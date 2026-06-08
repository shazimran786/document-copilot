from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.documents import (
    fetch_chunks_by_ids,
    fetch_documents_by_ids,
    fetch_neighbor_chunks,
)
from app.retrieval.schemas import (
    ChunkHit,
    DocumentSummary,
    FusedChunkHit,
    NeighborChunk,
    RetrievalChannel,
    SourcePassage,
)


def _channel_map(
    semantic_hits: list[ChunkHit],
    fulltext_hits: list[ChunkHit],
) -> dict[str, list[RetrievalChannel]]:
    channels: dict[str, list[RetrievalChannel]] = {}

    for hit in semantic_hits:
        channels.setdefault(hit.stable_chunk_id, [])
        if RetrievalChannel.SEMANTIC not in channels[hit.stable_chunk_id]:
            channels[hit.stable_chunk_id].append(RetrievalChannel.SEMANTIC)

    for hit in fulltext_hits:
        channels.setdefault(hit.stable_chunk_id, [])
        if RetrievalChannel.FULLTEXT not in channels[hit.stable_chunk_id]:
            channels[hit.stable_chunk_id].append(RetrievalChannel.FULLTEXT)

    return channels


def assemble_passages(
    session: Session,
    fused_hits: list[FusedChunkHit],
    semantic_hits: list[ChunkHit],
    fulltext_hits: list[ChunkHit],
    *,
    neighbor_window: int,
) -> list[SourcePassage]:
    if not fused_hits:
        return []

    chunk_ids = [hit.chunk_id for hit in fused_hits]
    chunks_by_id = fetch_chunks_by_ids(session, chunk_ids)
    document_ids = list(
        {chunks_by_id[chunk_id].document_id for chunk_id in chunk_ids if chunk_id in chunks_by_id}
    )
    documents_by_id = fetch_documents_by_ids(session, document_ids)
    channels_by_stable_id = _channel_map(semantic_hits, fulltext_hits)

    passages: list[SourcePassage] = []
    for fused_hit in fused_hits:
        chunk = chunks_by_id.get(fused_hit.chunk_id)
        if chunk is None:
            continue

        document = documents_by_id.get(chunk.document_id)
        if document is None:
            continue

        neighbor_rows = fetch_neighbor_chunks(
            session,
            chunk.document_id,
            chunk.chunk_index,
            window=neighbor_window,
        )
        neighbors = [
            NeighborChunk(
                chunk_id=neighbor.id,
                stable_chunk_id=neighbor.stable_chunk_id,
                chunk_index=neighbor.chunk_index,
                chunk_text=neighbor.chunk_text,
                position="before" if neighbor.chunk_index < chunk.chunk_index else "after",
            )
            for neighbor in neighbor_rows
        ]

        passages.append(
            SourcePassage(
                chunk_id=chunk.id,
                stable_chunk_id=chunk.stable_chunk_id,
                document=DocumentSummary(
                    id=document.id,
                    ticker=document.ticker,
                    company_name=document.company_name,
                    filing_type=document.filing_type,
                    fiscal_year=document.fiscal_year,
                    accession_number=document.accession_number,
                    source_url=document.source_url,
                ),
                chunk_text=chunk.chunk_text,
                section_label=chunk.section_label,
                page_label=chunk.page_label,
                token_count=chunk.token_count,
                chunk_metadata=chunk.chunk_metadata,
                neighbors=neighbors,
                fused_score=fused_hit.fused_score,
                channels=channels_by_stable_id.get(chunk.stable_chunk_id, []),
            )
        )

    return passages
