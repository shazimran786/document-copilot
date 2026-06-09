from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any
from uuid import UUID, uuid4

from app.chat.messages import (
    build_assistant_ui_message,
    new_message_id,
    split_text_deltas,
)
from app.chat.orchestrator import TurnResult, stream_turn
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever

AI_UI_MESSAGE_STREAM_HEADER = "x-vercel-ai-ui-message-stream"
AI_UI_MESSAGE_STREAM_VERSION = "v1"
SSE_MEDIA_TYPE = "text/event-stream"
STREAM_HEADERS = {
    AI_UI_MESSAGE_STREAM_HEADER: AI_UI_MESSAGE_STREAM_VERSION,
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}

STUB_REPLY_TEMPLATE = (
    'Document Copilot stub: ingestion and retrieval are not connected yet. '
    'Your question was: "{user_text}"'
)


def format_sse_event(payload: dict[str, Any] | str) -> str:
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


def build_stub_reply(user_text: str) -> str:
    return STUB_REPLY_TEMPLATE.format(user_text=user_text)


async def stub_stream_events(
    full_text: str,
    *,
    chunk_delay_seconds: float = 0.05,
) -> AsyncIterator[str]:
    message_id = new_message_id()
    text_id = f"text_{uuid4().hex}"

    yield format_sse_event({"type": "start", "messageId": message_id})
    yield format_sse_event({"type": "text-start", "id": text_id})

    for delta in split_text_deltas(full_text):
        yield format_sse_event({"type": "text-delta", "id": text_id, "delta": delta})
        if chunk_delay_seconds > 0:
            await asyncio.sleep(chunk_delay_seconds)

    yield format_sse_event({"type": "text-end", "id": text_id})
    yield format_sse_event({"type": "finish"})
    yield format_sse_event("[DONE]")


async def stream_stub_turn(
    full_text: str,
    *,
    on_complete: Callable[[], None] | None = None,
    chunk_delay_seconds: float = 0.05,
) -> AsyncIterator[str]:
    try:
        async for event in stub_stream_events(
            full_text,
            chunk_delay_seconds=chunk_delay_seconds,
        ):
            yield event
    finally:
        if on_complete is not None:
            on_complete()


def assistant_message_json(
    message_id: str,
    text: str,
    *,
    turn_result: TurnResult | None = None,
) -> dict[str, Any]:
    if turn_result is None:
        return build_assistant_ui_message(message_id, text)
    return build_assistant_ui_message(
        message_id,
        text,
        citations=turn_result.answer.citations,
        passages=turn_result.passages,
        insufficient_evidence=turn_result.answer.insufficient_evidence,
        validation_failed=turn_result.validation_failed,
    )


async def stream_agent_turn(
    *,
    user_text: str,
    thread_id: UUID,
    user_id: str,
    retriever: DocumentRetriever,
    validator: GroundingValidator,
    on_complete: Callable[[TurnResult], None] | None = None,
) -> AsyncIterator[str]:
    message_id = new_message_id()
    text_id = f"text_{uuid4().hex}"
    turn_result: TurnResult | None = None

    yield format_sse_event({"type": "start", "messageId": message_id})
    yield format_sse_event({"type": "text-start", "id": text_id})

    try:
        async for item in stream_turn(
            user_text=user_text,
            thread_id=thread_id,
            user_id=user_id,
            retriever=retriever,
            validator=validator,
            message_id=message_id,
        ):
            if isinstance(item, str):
                yield format_sse_event(
                    {"type": "text-delta", "id": text_id, "delta": item}
                )
            else:
                turn_result = item
    finally:
        if turn_result is not None and on_complete is not None:
            on_complete(turn_result)

    yield format_sse_event({"type": "text-end", "id": text_id})
    yield format_sse_event({"type": "finish"})
    yield format_sse_event("[DONE]")
