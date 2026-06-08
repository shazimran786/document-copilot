from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.retrieval.schemas import DocumentSummary, SourcePassage


@dataclass(frozen=True)
class ChunkRow:
    id: UUID
    document_id: UUID
    stable_chunk_id: str
    chunk_index: int
    chunk_text: str
    page_label: str | None
    section_label: str | None
    token_count: int
    chunk_metadata: dict[str, Any]


@dataclass(frozen=True)
class DocumentRow:
    id: UUID
    ticker: str
    company_name: str
    filing_type: str
    fiscal_year: int
    accession_number: str
    source_url: str


def _row_to_chunk(row: object) -> ChunkRow:
    mapping = row  # sqlalchemy RowMapping
    return ChunkRow(
        id=UUID(str(mapping["id"])),
        document_id=UUID(str(mapping["document_id"])),
        stable_chunk_id=mapping["stable_chunk_id"],
        chunk_index=mapping["chunk_index"],
        chunk_text=mapping["chunk_text"],
        page_label=mapping["page_label"],
        section_label=mapping["section_label"],
        token_count=mapping["token_count"],
        chunk_metadata=dict(mapping["chunk_metadata"] or {}),
    )


def fetch_chunk_by_id(session: Session, chunk_id: UUID) -> ChunkRow | None:
    rows = fetch_chunks_by_ids(session, [chunk_id])
    return rows.get(chunk_id)


def fetch_chunk_by_stable_id(session: Session, stable_chunk_id: str) -> ChunkRow | None:
    result = session.execute(
        text(
            """
            SELECT
                id,
                document_id,
                stable_chunk_id,
                chunk_index,
                chunk_text,
                page_label,
                section_label,
                token_count,
                chunk_metadata
            FROM document_chunks
            WHERE stable_chunk_id = :stable_chunk_id
            """
        ),
        {"stable_chunk_id": stable_chunk_id},
    )
    row = result.mappings().first()
    if row is None:
        return None
    return _row_to_chunk(row)


def chunk_row_to_source_passage(session: Session, chunk_row: ChunkRow) -> SourcePassage:
    documents = fetch_documents_by_ids(session, [chunk_row.document_id])
    document = documents[chunk_row.document_id]
    return SourcePassage(
        chunk_id=chunk_row.id,
        stable_chunk_id=chunk_row.stable_chunk_id,
        document=DocumentSummary(
            id=document.id,
            ticker=document.ticker,
            company_name=document.company_name,
            filing_type=document.filing_type,
            fiscal_year=document.fiscal_year,
            accession_number=document.accession_number,
            source_url=document.source_url,
        ),
        chunk_text=chunk_row.chunk_text,
        section_label=chunk_row.section_label,
        page_label=chunk_row.page_label,
        token_count=chunk_row.token_count,
        chunk_metadata=chunk_row.chunk_metadata,
        neighbors=[],
        fused_score=0.0,
        channels=[],
    )


def fetch_chunks_by_ids(session: Session, chunk_ids: list[UUID]) -> dict[UUID, ChunkRow]:
    if not chunk_ids:
        return {}

    result = session.execute(
        text(
            """
            SELECT
                id,
                document_id,
                stable_chunk_id,
                chunk_index,
                chunk_text,
                page_label,
                section_label,
                token_count,
                chunk_metadata
            FROM document_chunks
            WHERE id = ANY(CAST(:chunk_ids AS uuid[]))
            """
        ),
        {"chunk_ids": [str(chunk_id) for chunk_id in chunk_ids]},
    )

    rows: dict[UUID, ChunkRow] = {}
    for row in result.mappings():
        chunk = _row_to_chunk(row)
        rows[chunk.id] = chunk
    return rows


def fetch_documents_by_ids(
    session: Session, document_ids: list[UUID]
) -> dict[UUID, DocumentRow]:
    if not document_ids:
        return {}

    result = session.execute(
        text(
            """
            SELECT
                id,
                ticker,
                company_name,
                filing_type,
                fiscal_year,
                accession_number,
                source_url
            FROM source_documents
            WHERE id = ANY(CAST(:document_ids AS uuid[]))
            """
        ),
        {"document_ids": [str(document_id) for document_id in document_ids]},
    )

    rows: dict[UUID, DocumentRow] = {}
    for row in result.mappings():
        document_id = UUID(str(row["id"]))
        rows[document_id] = DocumentRow(
            id=document_id,
            ticker=row["ticker"],
            company_name=row["company_name"],
            filing_type=row["filing_type"],
            fiscal_year=row["fiscal_year"],
            accession_number=row["accession_number"],
            source_url=row["source_url"],
        )
    return rows


def fetch_neighbor_chunks(
    session: Session,
    document_id: UUID,
    chunk_index: int,
    *,
    window: int,
) -> list[ChunkRow]:
    if window <= 0:
        return []

    result = session.execute(
        text(
            """
            SELECT
                id,
                document_id,
                stable_chunk_id,
                chunk_index,
                chunk_text,
                page_label,
                section_label,
                token_count,
                chunk_metadata
            FROM document_chunks
            WHERE document_id = :document_id
              AND chunk_index BETWEEN :min_index AND :max_index
              AND chunk_index <> :chunk_index
            ORDER BY chunk_index
            """
        ),
        {
            "document_id": str(document_id),
            "chunk_index": chunk_index,
            "min_index": chunk_index - window,
            "max_index": chunk_index + window,
        },
    )

    return [_row_to_chunk(row) for row in result.mappings()]
