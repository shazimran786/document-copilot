from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user, get_user_scoped_supabase
from app.main import app

TEST_USER = CurrentUser(
    id="5c42f900-3d23-4509-8980-31e17e8c6351",
    email="test@example.com",
    access_token="test-token",
)


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    app.dependency_overrides[get_user_scoped_supabase] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def thread_id() -> UUID:
    return uuid4()


@pytest.fixture
def thread_response(thread_id: UUID):
    from app.chat.schemas import ThreadResponse

    now = datetime.now(UTC)
    return ThreadResponse(
        id=thread_id,
        title="New chat",
        created_at=now,
        updated_at=now,
    )
