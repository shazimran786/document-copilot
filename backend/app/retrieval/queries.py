from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.retrieval.schemas import ChunkHit, RetrievalChannel, RetrievalFilters


def _format_embedding(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


def _build_filter_sql(filters: RetrievalFilters) -> tuple[str, dict[str, object]]:
    clauses: list[str] = []
    params: dict[str, object] = {}

    if filters.tickers:
        clauses.append("sd.ticker = ANY(CAST(:tickers AS text[]))")
        params["tickers"] = filters.tickers

    if filters.fiscal_years:
        clauses.append("sd.fiscal_year = ANY(CAST(:fiscal_years AS int[]))")
        params["fiscal_years"] = filters.fiscal_years

    if filters.filing_types:
        clauses.append("sd.filing_type = ANY(CAST(:filing_types AS text[]))")
        params["filing_types"] = filters.filing_types

    if not clauses:
        return "", params

    return " AND " + " AND ".join(clauses), params


def _rows_to_hits(
    rows: list[dict[str, object]],
    *,
    channel: RetrievalChannel,
) -> list[ChunkHit]:
    hits: list[ChunkHit] = []
    for rank, row in enumerate(rows, start=1):
        hits.append(
            ChunkHit(
                chunk_id=UUID(str(row["chunk_id"])),
                stable_chunk_id=str(row["stable_chunk_id"]),
                document_id=UUID(str(row["document_id"])),
                rank=rank,
                score=float(row["score"]),
                channel=channel,
            )
        )
    return hits


def semantic_search(
    session: Session,
    embedding: list[float],
    filters: RetrievalFilters,
    *,
    top_k: int,
) -> list[ChunkHit]:
    filter_sql, filter_params = _build_filter_sql(filters)
    result = session.execute(
        text(
            f"""
            SELECT
                dc.id AS chunk_id,
                dc.stable_chunk_id,
                dc.document_id,
                1 - (dc.embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM document_chunks dc
            JOIN source_documents sd ON sd.id = dc.document_id
            WHERE dc.embedding IS NOT NULL
            {filter_sql}
            ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """
        ),
        {
            "query_embedding": _format_embedding(embedding),
            "top_k": top_k,
            **filter_params,
        },
    )
    return _rows_to_hits(list(result.mappings()), channel=RetrievalChannel.SEMANTIC)


def fulltext_search(
    session: Session,
    query_text: str,
    filters: RetrievalFilters,
    *,
    top_k: int,
) -> list[ChunkHit]:
    filter_sql, filter_params = _build_filter_sql(filters)
    result = session.execute(
        text(
            f"""
            SELECT
                dc.id AS chunk_id,
                dc.stable_chunk_id,
                dc.document_id,
                ts_rank_cd(
                    dc.search_vector,
                    websearch_to_tsquery('english', :query_text)
                ) AS score
            FROM document_chunks dc
            JOIN source_documents sd ON sd.id = dc.document_id
            WHERE dc.search_vector @@ websearch_to_tsquery('english', :query_text)
            {filter_sql}
            ORDER BY score DESC
            LIMIT :top_k
            """
        ),
        {
            "query_text": query_text,
            "top_k": top_k,
            **filter_params,
        },
    )
    return _rows_to_hits(list(result.mappings()), channel=RetrievalChannel.FULLTEXT)
