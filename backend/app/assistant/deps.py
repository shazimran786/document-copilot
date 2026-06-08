from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import SourcePassage

SessionFactory = Callable[[], AbstractContextManager[Session]]


@dataclass
class DocumentAgentDeps:
    user_id: str
    thread_id: str
    retriever: DocumentRetriever
    session_factory: SessionFactory
    retrieved_passages: dict[UUID, SourcePassage] = field(default_factory=dict)
