from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from supabase import Client

from ingest.models import ChunkRecord, DocumentMetadata

CHUNK_BATCH_SIZE = 25
MAX_RETRIES = 5

T = TypeVar("T")


def _execute_with_retry(operation: Callable[[], T]) -> T:
    delay_seconds = 1.0
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 — retry transient Supabase/HTTP failures
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(delay_seconds)
            delay_seconds *= 2
    raise RuntimeError("Unreachable: retry loop exhausted.") from last_error


def upsert_document(client: Client, metadata: DocumentMetadata) -> uuid.UUID:
    payload = {
        "ticker": metadata.ticker,
        "company_name": metadata.company_name,
        "filing_type": metadata.filing_type,
        "fiscal_year": metadata.fiscal_year,
        "accession_number": metadata.accession_number,
        "source_url": metadata.source_url,
        "markdown_content": metadata.markdown_content,
    }

    existing = _execute_with_retry(
        lambda: client.table("source_documents")
        .select("id")
        .eq("accession_number", metadata.accession_number)
        .limit(1)
        .execute()
    )
    if existing.data:
        document_id = uuid.UUID(str(existing.data[0]["id"]))
        _execute_with_retry(
            lambda: client.table("source_documents")
            .update(payload)
            .eq("id", str(document_id))
            .execute()
        )
        return document_id

    document_id = uuid.uuid4()
    _execute_with_retry(
        lambda: client.table("source_documents")
        .insert({**payload, "id": str(document_id)})
        .execute()
    )
    return document_id


def replace_document_chunks(
    client: Client,
    document_id: uuid.UUID,
    chunks: list[ChunkRecord],
) -> int:
    _execute_with_retry(
        lambda: client.table("document_chunks")
        .delete()
        .eq("document_id", str(document_id))
        .execute()
    )
    if not chunks:
        return 0

    rows = [_chunk_row(document_id, chunk) for chunk in chunks]
    written = 0
    for start in range(0, len(rows), CHUNK_BATCH_SIZE):
        batch = rows[start : start + CHUNK_BATCH_SIZE]
        _execute_with_retry(
            lambda batch=batch: client.table("document_chunks").insert(batch).execute()
        )
        written += len(batch)
    return written


def _chunk_row(document_id: uuid.UUID, chunk: ChunkRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "document_id": str(document_id),
        "stable_chunk_id": chunk.stable_chunk_id,
        "chunk_index": chunk.chunk_index,
        "chunk_text": chunk.chunk_text,
        "page_label": chunk.page_label,
        "section_label": chunk.section_label,
        "token_count": chunk.token_count,
        "chunk_metadata": chunk.chunk_metadata,
    }
    if chunk.embedding is not None:
        row["embedding"] = chunk.embedding
    return row
