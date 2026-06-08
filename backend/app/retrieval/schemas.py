from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetrievalChannel(str, Enum):
    SEMANTIC = "semantic"
    FULLTEXT = "fulltext"


class RetrievalFilters(BaseModel):
    tickers: list[str] | None = None
    fiscal_years: list[int] | None = None
    filing_types: list[str] | None = None


class RetrievalQuery(BaseModel):
    text: str = Field(min_length=1)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class ChunkHit(BaseModel):
    chunk_id: UUID
    stable_chunk_id: str
    document_id: UUID
    rank: int = Field(ge=1)
    score: float
    channel: RetrievalChannel


class FusedChunkHit(BaseModel):
    chunk_id: UUID
    stable_chunk_id: str
    fused_score: float
    semantic_rank: int | None = None
    fulltext_rank: int | None = None


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticker: str
    company_name: str
    filing_type: str
    fiscal_year: int
    accession_number: str
    source_url: str


class NeighborChunk(BaseModel):
    chunk_id: UUID
    stable_chunk_id: str
    chunk_index: int
    chunk_text: str
    position: Literal["before", "after"]


class SourcePassage(BaseModel):
    chunk_id: UUID
    stable_chunk_id: str
    document: DocumentSummary
    chunk_text: str
    section_label: str | None
    page_label: str | None
    token_count: int
    chunk_metadata: dict[str, Any]
    neighbors: list[NeighborChunk] = Field(default_factory=list)
    fused_score: float
    channels: list[RetrievalChannel] = Field(default_factory=list)


class RetrievalResult(BaseModel):
    query: RetrievalQuery
    passages: list[SourcePassage]
    fused_hits: list[FusedChunkHit]
    semantic_candidates: int
    fulltext_candidates: int
