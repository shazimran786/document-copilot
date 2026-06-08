from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        ser_json_by_alias=True,
    )


class ThreadResponse(ApiModel):
    id: UUID
    title: str
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class CreateThreadRequest(ApiModel):
    title: str | None = None


class MessageResponse(ApiModel):
    id: UUID
    thread_id: UUID = Field(alias="threadId")
    role: Literal["user", "assistant"]
    content_text: str = Field(alias="contentText")
    sequence_number: int = Field(alias="sequenceNumber")
    created_at: datetime = Field(alias="createdAt")
    message_json: dict[str, Any] = Field(default_factory=dict, alias="messageJson")


class MessagesListResponse(ApiModel):
    messages: list[dict[str, Any]]


class ChatStreamRequest(ApiModel):
    thread_id: UUID = Field(alias="threadId")
    messages: list[dict[str, Any]]
