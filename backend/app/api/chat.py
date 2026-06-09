from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, get_user_scoped_supabase
from app.chat.messages import (
    build_citation_db_metadata,
    extract_latest_user_text,
    get_latest_user_message,
    to_ui_message,
)
from app.chat.orchestrator import TurnResult
from app.chat.schemas import (
    ChatStreamRequest,
    CreateThreadRequest,
    MessagesListResponse,
    ThreadResponse,
)
from app.chat.streaming import (
    SSE_MEDIA_TYPE,
    STREAM_HEADERS,
    assistant_message_json,
    stream_agent_turn,
)
from app.database.chats import (
    ChatPersistenceError,
    CitationRecord,
    create_thread,
    get_thread,
    insert_citations,
    insert_message,
    list_messages,
    list_threads,
    maybe_set_thread_title,
    next_sequence_number,
    touch_thread,
)
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever

logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache
def get_document_retriever() -> DocumentRetriever:
    return DocumentRetriever()


@lru_cache
def get_grounding_validator() -> GroundingValidator:
    return GroundingValidator()


def _chat_persistence_http_error(exc: ChatPersistenceError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc),
    )


def _thread_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Chat thread not found.",
    )


def _persist_turn_result(
    client: Client,
    thread_id: UUID,
    turn_result: TurnResult,
    assistant_sequence: int,
) -> None:
    if turn_result.validation_failed:
        insert_message(
            client,
            thread_id,
            "assistant",
            turn_result.answer.answer,
            assistant_message_json(
                turn_result.message_id,
                turn_result.answer.answer,
                turn_result=turn_result,
            ),
            assistant_sequence,
            message_id=turn_result.message_uuid,
        )
        touch_thread(client, thread_id)
        return

    insert_message(
        client,
        thread_id,
        "assistant",
        turn_result.answer.answer,
        assistant_message_json(
            turn_result.message_id,
            turn_result.answer.answer,
            turn_result=turn_result,
        ),
        assistant_sequence,
        message_id=turn_result.message_uuid,
    )
    insert_citations(
        client,
        turn_result.message_uuid,
        [
            CitationRecord(
                chunk_id=citation.chunk_id,
                claim_index=citation.claim_index,
                excerpt=citation.excerpt,
                citation_metadata=build_citation_db_metadata(
                    citation,
                    turn_result.passages[citation.chunk_id],
                ),
            )
            for citation in turn_result.answer.citations
        ],
    )
    touch_thread(client, thread_id)


@router.get("/threads", response_model=list[ThreadResponse])
def get_threads(
    client: Annotated[Client, Depends(get_user_scoped_supabase)],
) -> list[ThreadResponse]:
    try:
        return list_threads(client)
    except ChatPersistenceError as exc:
        raise _chat_persistence_http_error(exc) from exc


@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
def post_thread(
    body: CreateThreadRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[Client, Depends(get_user_scoped_supabase)],
) -> ThreadResponse:
    try:
        return create_thread(client, current_user.id, body.title)
    except ChatPersistenceError as exc:
        raise _chat_persistence_http_error(exc) from exc


@router.get("/threads/{thread_id}/messages", response_model=MessagesListResponse)
def get_thread_messages(
    thread_id: UUID,
    client: Annotated[Client, Depends(get_user_scoped_supabase)],
) -> MessagesListResponse:
    try:
        thread = get_thread(client, thread_id)
        if thread is None:
            raise _thread_not_found()
        messages = list_messages(client, thread_id)
    except ChatPersistenceError as exc:
        raise _chat_persistence_http_error(exc) from exc

    return MessagesListResponse(
        messages=[to_ui_message(message) for message in messages],
    )


@router.post("/stream")
async def post_chat_stream(
    body: ChatStreamRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[Client, Depends(get_user_scoped_supabase)],
    retriever: Annotated[DocumentRetriever, Depends(get_document_retriever)],
    validator: Annotated[GroundingValidator, Depends(get_grounding_validator)],
) -> StreamingResponse:
    try:
        thread = get_thread(client, body.thread_id)
        if thread is None:
            raise _thread_not_found()

        user_text = extract_latest_user_text(body.messages)
        user_message = get_latest_user_message(body.messages)
        user_sequence = next_sequence_number(client, body.thread_id)

        insert_message(
            client,
            body.thread_id,
            "user",
            user_text,
            user_message,
            user_sequence,
        )
        maybe_set_thread_title(client, body.thread_id, user_text)

        assistant_sequence = user_sequence + 1
        persisted = False

        def persist_assistant_message(turn_result: TurnResult) -> None:
            nonlocal persisted
            if persisted:
                return
            try:
                _persist_turn_result(
                    client,
                    body.thread_id,
                    turn_result,
                    assistant_sequence,
                )
                persisted = True
            except ChatPersistenceError:
                logger.exception("Failed to persist assistant message")

        async def event_generator():
            try:
                async for event in stream_agent_turn(
                    user_text=user_text,
                    thread_id=body.thread_id,
                    user_id=current_user.id,
                    retriever=retriever,
                    validator=validator,
                    on_complete=persist_assistant_message,
                ):
                    yield event
            except ChatPersistenceError:
                logger.exception("Failed while streaming agent chat response")
                raise
            except Exception:
                logger.exception("Agent chat stream failed")
                raise

        return StreamingResponse(
            event_generator(),
            media_type=SSE_MEDIA_TYPE,
            headers=STREAM_HEADERS,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ChatPersistenceError as exc:
        raise _chat_persistence_http_error(exc) from exc
