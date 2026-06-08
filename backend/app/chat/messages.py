from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.chat.schemas import MessageResponse


def extract_latest_user_text(messages: list[dict[str, Any]]) -> str:
    """Return text from the last user message in AI SDK wire format."""
    for message in reversed(messages):
        if message.get("role") != "user":
            continue

        parts = message.get("parts")
        if isinstance(parts, list):
            chunks: list[str] = []
            for part in parts:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text" and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
            if chunks:
                return "".join(chunks).strip()

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    raise ValueError("No user message text found in request.")


def get_latest_user_message(messages: list[dict[str, Any]]) -> dict[str, Any]:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message
    raise ValueError("No user message found in request.")


def to_ui_message(row: MessageResponse) -> dict[str, Any]:
    if row.message_json:
        return row.message_json

    return {
        "id": str(row.id),
        "role": row.role,
        "parts": [{"type": "text", "text": row.content_text}],
    }


def build_assistant_ui_message(message_id: str, text: str) -> dict[str, Any]:
    return {
        "id": message_id,
        "role": "assistant",
        "parts": [{"type": "text", "text": text}],
    }


def new_message_id() -> str:
    return f"msg_{uuid4().hex}"
