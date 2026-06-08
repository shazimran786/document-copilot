from __future__ import annotations

import asyncio
import json

from app.chat.streaming import (
    AI_UI_MESSAGE_STREAM_HEADER,
    STREAM_HEADERS,
    build_stub_reply,
    format_sse_event,
    split_text_deltas,
    stub_stream_events,
)


def test_format_sse_event_json() -> None:
    rendered = format_sse_event({"type": "finish"})
    assert rendered == 'data: {"type":"finish"}\n\n'


def test_format_sse_event_done_marker() -> None:
    assert format_sse_event("[DONE]") == "data: [DONE]\n\n"


def test_build_stub_reply_includes_user_text() -> None:
    reply = build_stub_reply("AWS margin?")
    assert "AWS margin?" in reply
    assert "stub" in reply.lower()


def test_split_text_deltas_preserves_spaces() -> None:
    assert split_text_deltas("hello world") == ["hello", " world"]


def test_stub_stream_events_order() -> None:
    async def collect() -> list[str]:
        events: list[str] = []
        async for event in stub_stream_events("hello world", chunk_delay_seconds=0):
            events.append(event)
        return events

    events = asyncio.run(collect())

    payloads = []
    for event in events:
        assert event.startswith("data: ")
        body = event.removeprefix("data: ").strip()
        if body == "[DONE]":
            payloads.append("[DONE]")
        else:
            payloads.append(json.loads(body))

    assert payloads[0]["type"] == "start"
    assert "messageId" in payloads[0]
    assert payloads[1]["type"] == "text-start"
    assert any(item.get("type") == "text-delta" for item in payloads if isinstance(item, dict))
    assert payloads[-2]["type"] == "finish"
    assert payloads[-1] == "[DONE]"


def test_stream_headers_include_ai_sdk_marker() -> None:
    assert STREAM_HEADERS[AI_UI_MESSAGE_STREAM_HEADER] == "v1"
