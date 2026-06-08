from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user, get_user_scoped_supabase
from app.assistant.outputs import GroundedAnswer
from app.chat.orchestrator import TurnResult
from app.chat.schemas import MessageResponse, ThreadResponse
from app import api as api_pkg
from app.main import app
from tests.conftest import TEST_USER


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    app.dependency_overrides[get_user_scoped_supabase] = lambda: MagicMock()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_threads_requires_auth() -> None:
    with TestClient(app) as client:
        response = client.get("/chat/threads")
    assert response.status_code == 401


def test_get_threads_returns_threads(
    authed_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    thread_response: ThreadResponse,
) -> None:
    monkeypatch.setattr(api_pkg.chat, "list_threads", lambda client: [thread_response])
    response = authed_client.get(
        "/chat/threads",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["id"] == str(thread_response.id)
    assert payload[0]["createdAt"]


def test_get_thread_messages_404_when_missing(
    authed_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread_id = uuid4()
    monkeypatch.setattr(api_pkg.chat, "get_thread", lambda client, tid: None)
    response = authed_client.get(
        f"/chat/threads/{thread_id}/messages",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 404


def test_get_thread_messages_ordered(
    authed_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    thread_response: ThreadResponse,
) -> None:
    thread_id = thread_response.id
    now = datetime.now(UTC)
    messages = [
        MessageResponse(
            id=uuid4(),
            thread_id=thread_id,
            role="user",
            content_text="First",
            sequence_number=0,
            created_at=now,
            message_json={"id": "u1", "role": "user", "parts": [{"type": "text", "text": "First"}]},
        ),
        MessageResponse(
            id=uuid4(),
            thread_id=thread_id,
            role="assistant",
            content_text="Second",
            sequence_number=1,
            created_at=now,
            message_json={
                "id": "a1",
                "role": "assistant",
                "parts": [{"type": "text", "text": "Second"}],
            },
        ),
    ]

    monkeypatch.setattr(api_pkg.chat, "get_thread", lambda client, tid: thread_response)
    monkeypatch.setattr(api_pkg.chat, "list_messages", lambda client, tid: messages)

    response = authed_client.get(
        f"/chat/threads/{thread_id}/messages",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    payload = response.json()["messages"]
    assert payload[0]["parts"][0]["text"] == "First"
    assert payload[1]["parts"][0]["text"] == "Second"


def test_post_stream_unknown_thread_404(
    authed_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    thread_id = uuid4()
    monkeypatch.setattr(api_pkg.chat, "get_thread", lambda client, tid: None)

    response = authed_client.post(
        "/chat/stream",
        headers={"Authorization": "Bearer test-token"},
        json={
            "threadId": str(thread_id),
            "messages": [
                {
                    "id": "u1",
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello"}],
                }
            ],
        },
    )
    assert response.status_code == 404


def test_post_stream_returns_ai_sdk_sse(
    authed_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    thread_response: ThreadResponse,
) -> None:
    inserted: list[tuple[str, int]] = []

    def fake_insert_message(
        client,
        thread_id,
        role,
        content_text,
        message_json,
        sequence_number,
        message_id=None,
    ):
        inserted.append((role, sequence_number))
        return MessageResponse(
            id=message_id or uuid4(),
            thread_id=thread_id,
            role=role,
            content_text=content_text,
            sequence_number=sequence_number,
            created_at=datetime.now(UTC),
            message_json=message_json,
        )

    async def fake_stream_agent_turn(**kwargs):
        from app.chat.messages import new_message_id
        from app.chat.streaming import format_sse_event

        message_id = new_message_id()
        text_id = "text_test"
        yield format_sse_event({"type": "start", "messageId": message_id})
        yield format_sse_event({"type": "text-start", "id": text_id})
        yield format_sse_event({"type": "text-delta", "id": text_id, "delta": "Hello"})
        yield format_sse_event({"type": "text-end", "id": text_id})
        yield format_sse_event({"type": "finish"})
        yield format_sse_event("[DONE]")
        if kwargs.get("on_complete") is not None:
            kwargs["on_complete"](
                TurnResult(
                    answer=GroundedAnswer(
                        answer="Hello",
                        citations=[],
                        insufficient_evidence=True,
                    ),
                    passages={},
                    message_id=message_id,
                    message_uuid=uuid4(),
                )
            )

    monkeypatch.setattr(api_pkg.chat, "get_thread", lambda client, tid: thread_response)
    monkeypatch.setattr(api_pkg.chat, "next_sequence_number", lambda client, tid: 0)
    monkeypatch.setattr(api_pkg.chat, "insert_message", fake_insert_message)
    monkeypatch.setattr(api_pkg.chat, "insert_citations", lambda *args, **kwargs: None)
    monkeypatch.setattr(api_pkg.chat, "maybe_set_thread_title", lambda *args, **kwargs: None)
    monkeypatch.setattr(api_pkg.chat, "touch_thread", lambda client, tid: None)
    monkeypatch.setattr(api_pkg.chat, "stream_agent_turn", fake_stream_agent_turn)

    with authed_client.stream(
        "POST",
        "/chat/stream",
        headers={"Authorization": "Bearer test-token"},
        json={
            "threadId": str(thread_response.id),
            "messages": [
                {
                    "id": "u1",
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello"}],
                }
            ],
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers.get("x-vercel-ai-ui-message-stream") == "v1"
        body = "".join(response.iter_text())

    assert '"type":"start"' in body or '"type": "start"' in body
    assert "[DONE]" in body
    assert inserted[0] == ("user", 0)
    assert inserted[1] == ("assistant", 1)
