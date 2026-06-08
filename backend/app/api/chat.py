from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, get_user_scoped_supabase
from app.chat.messages import (
    extract_latest_user_text,
    get_latest_user_message,
    new_message_id,
    to_ui_message,
)
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
    build_stub_reply,
    stream_stub_turn,
)
from app.database.chats import (
    ChatPersistenceError,
    create_thread,
    get_thread,
    insert_message,
    list_messages,
    list_threads,
    maybe_set_thread_title,
    next_sequence_number,
    touch_thread,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
    client: Annotated[Client, Depends(get_user_scoped_supabase)],
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

        stub_text = build_stub_reply(user_text)
        assistant_id = new_message_id()
        assistant_sequence = user_sequence + 1
        persisted = False

        def persist_assistant_message() -> None:
            nonlocal persisted
            if persisted:
                return
            try:
                insert_message(
                    client,
                    body.thread_id,
                    "assistant",
                    stub_text,
                    assistant_message_json(assistant_id, stub_text),
                    assistant_sequence,
                )
                touch_thread(client, body.thread_id)
                persisted = True
            except ChatPersistenceError:
                logger.exception("Failed to persist stub assistant message")

        async def event_generator():
            try:
                async for event in stream_stub_turn(
                    stub_text,
                    on_complete=persist_assistant_message,
                ):
                    yield event
            except ChatPersistenceError:
                logger.exception("Failed while streaming stub chat response")
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
