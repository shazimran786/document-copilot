from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentMetadata:
    ticker: str
    company_name: str
    filing_type: str
    fiscal_year: int
    accession_number: str
    source_url: str
    markdown_content: str
    markdown_path: str


@dataclass
class ChunkRecord:
    stable_chunk_id: str
    chunk_index: int
    chunk_text: str
    section_label: str | None
    page_label: str | None
    token_count: int
    chunk_metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
