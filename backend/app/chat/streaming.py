from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any
from uuid import uuid4

from app.chat.messages import build_assistant_ui_message, new_message_id

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


def split_text_deltas(text: str) -> list[str]:
    words = text.split(" ")
    if not words:
        return [""]

    deltas: list[str] = []
    for index, word in enumerate(words):
        if index == 0:
            deltas.append(word)
        else:
            deltas.append(f" {word}")
    return deltas


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


def assistant_message_json(message_id: str, text: str) -> dict[str, Any]:
    return build_assistant_ui_message(message_id, text)
