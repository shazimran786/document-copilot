from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.retrieval.schemas import DocumentSummary, SourcePassage

__all__ = [
    "Citation",
    "DocumentSummary",
    "GroundedAnswer",
    "SourcePassage",
]


class Citation(BaseModel):
    chunk_id: UUID
    stable_chunk_id: str
    claim_index: int = Field(ge=0)
    excerpt: str = Field(min_length=1)


class GroundedAnswer(BaseModel):
    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    insufficient_evidence: bool = False
