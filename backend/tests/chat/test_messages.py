from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.chat.messages import (
    build_assistant_ui_message,
    extract_latest_user_text,
    to_ui_message,
)
from app.chat.schemas import MessageResponse


def test_extract_latest_user_text_from_parts() -> None:
    messages = [
        {
            "id": "u1",
            "role": "user",
            "parts": [{"type": "text", "text": "What was AWS margin?"}],
        }
    ]
    assert extract_latest_user_text(messages) == "What was AWS margin?"


def test_extract_latest_user_text_uses_last_user_message() -> None:
    messages = [
        {
            "id": "u1",
            "role": "user",
            "parts": [{"type": "text", "text": "First question"}],
        },
        {
            "id": "a1",
            "role": "assistant",
            "parts": [{"type": "text", "text": "Stub reply"}],
        },
        {
            "id": "u2",
            "role": "user",
            "parts": [{"type": "text", "text": "Second question"}],
        },
    ]
    assert extract_latest_user_text(messages) == "Second question"


def test_extract_latest_user_text_supports_legacy_content_field() -> None:
    messages = [{"id": "u1", "role": "user", "content": "Legacy content"}]
    assert extract_latest_user_text(messages) == "Legacy content"


def test_extract_latest_user_text_raises_when_missing() -> None:
    with pytest.raises(ValueError, match="No user message text"):
        extract_latest_user_text([{"id": "a1", "role": "assistant", "parts": []}])


def test_to_ui_message_prefers_message_json() -> None:
    stored = {
        "id": "u1",
        "role": "user",
        "parts": [{"type": "text", "text": "Stored json"}],
    }
    row = MessageResponse(
        id=uuid4(),
        thread_id=uuid4(),
        role="user",
        content_text="Stored json",
        sequence_number=0,
        created_at=datetime.now(UTC),
        message_json=stored,
    )
    assert to_ui_message(row) == stored


def test_build_assistant_ui_message_shape() -> None:
    payload = build_assistant_ui_message("msg_123", "Hello")
    assert payload["id"] == "msg_123"
    assert payload["role"] == "assistant"
    assert payload["parts"] == [{"type": "text", "text": "Hello"}]
