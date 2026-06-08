from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from postgrest.exceptions import APIError
from supabase import Client

from app.chat.schemas import MessageResponse, ThreadResponse

logger = logging.getLogger(__name__)

DEFAULT_THREAD_TITLE = "New chat"
MAX_THREAD_TITLE_LENGTH = 60


class ChatPersistenceError(Exception):
    """Raised when Supabase chat persistence fails."""


def _raise_for_response_error(response: Any, action: str) -> None:
    error = getattr(response, "error", None)
    if error is None or error is False:
        return
    logger.exception("Supabase %s failed: %s", action, error)
    if isinstance(error, BaseException):
        raise ChatPersistenceError(f"Failed to {action}.") from error
    raise ChatPersistenceError(f"Failed to {action}.")


def _parse_thread(row: dict[str, Any]) -> ThreadResponse:
    return ThreadResponse.model_validate(row)


def _parse_message(row: dict[str, Any]) -> MessageResponse:
    return MessageResponse.model_validate(row)


def list_threads(client: Client) -> list[ThreadResponse]:
    response = (
        client.table("chat_threads")
        .select("*")
        .order("updated_at", desc=True)
        .execute()
    )
    _raise_for_response_error(response, "list chat threads")
    return [_parse_thread(row) for row in response.data or []]


def create_thread(
    client: Client,
    user_id: str,
    title: str | None = None,
) -> ThreadResponse:
    payload = {
        "id": str(uuid4()),
        "user_id": user_id,
        "title": title or DEFAULT_THREAD_TITLE,
    }
    response = client.table("chat_threads").insert(payload).execute()
    _raise_for_response_error(response, "create chat thread")
    if not response.data:
        raise ChatPersistenceError("Failed to create chat thread.")
    return _parse_thread(response.data[0])


def get_thread(client: Client, thread_id: UUID) -> ThreadResponse | None:
    response = (
        client.table("chat_threads")
        .select("*")
        .eq("id", str(thread_id))
        .maybe_single()
        .execute()
    )
    _raise_for_response_error(response, "get chat thread")
    if not response.data:
        return None
    return _parse_thread(response.data)


def list_messages(client: Client, thread_id: UUID) -> list[MessageResponse]:
    response = (
        client.table("chat_messages")
        .select("*")
        .eq("thread_id", str(thread_id))
        .order("sequence_number")
        .execute()
    )
    _raise_for_response_error(response, "list chat messages")
    return [_parse_message(row) for row in response.data or []]


def next_sequence_number(client: Client, thread_id: UUID) -> int:
    response = (
        client.table("chat_messages")
        .select("sequence_number")
        .eq("thread_id", str(thread_id))
        .order("sequence_number", desc=True)
        .limit(1)
        .execute()
    )
    _raise_for_response_error(response, "read next sequence number")
    rows = response.data or []
    if not rows:
        return 0
    return int(rows[0]["sequence_number"]) + 1


def insert_message(
    client: Client,
    thread_id: UUID,
    role: Literal["user", "assistant"],
    content_text: str,
    message_json: dict[str, Any],
    sequence_number: int,
) -> MessageResponse:
    payload = {
        "id": str(uuid4()),
        "thread_id": str(thread_id),
        "role": role,
        "content_text": content_text,
        "message_json": message_json,
        "sequence_number": sequence_number,
    }
    try:
        response = client.table("chat_messages").insert(payload).execute()
    except APIError as exc:
        logger.exception("Supabase insert chat message failed")
        raise ChatPersistenceError("Failed to insert chat message.") from exc
    _raise_for_response_error(response, "insert chat message")
    if not response.data:
        raise ChatPersistenceError("Failed to insert chat message.")
    return _parse_message(response.data[0])


def touch_thread(client: Client, thread_id: UUID) -> None:
    payload = {"updated_at": datetime.now(UTC).isoformat()}
    response = (
        client.table("chat_threads")
        .update(payload)
        .eq("id", str(thread_id))
        .execute()
    )
    _raise_for_response_error(response, "update chat thread")


def maybe_set_thread_title(
    client: Client,
    thread_id: UUID,
    first_user_text: str,
) -> None:
    thread = get_thread(client, thread_id)
    if thread is None or thread.title != DEFAULT_THREAD_TITLE:
        return

    normalized = " ".join(first_user_text.split())
    if not normalized:
        return

    title = normalized[:MAX_THREAD_TITLE_LENGTH].strip()
    if len(normalized) > MAX_THREAD_TITLE_LENGTH:
        title = f"{title.rstrip()}..."

    response = (
        client.table("chat_threads")
        .update({"title": title})
        .eq("id", str(thread_id))
        .execute()
    )
    _raise_for_response_error(response, "set chat thread title")
