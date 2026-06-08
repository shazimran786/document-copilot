from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.retrieval.schemas import ChunkHit, FusedChunkHit, RetrievalChannel


@dataclass
class _FusionAccumulator:
    chunk_id: UUID
    stable_chunk_id: str
    fused_score: float = 0.0
    semantic_rank: int | None = None
    fulltext_rank: int | None = None


def reciprocal_rank_fusion(
    rankings: list[list[ChunkHit]],
    *,
    k: int = 60,
) -> list[FusedChunkHit]:
    accumulators: dict[str, _FusionAccumulator] = {}

    for ranking in rankings:
        for hit in ranking:
            entry = accumulators.get(hit.stable_chunk_id)
            if entry is None:
                entry = _FusionAccumulator(
                    chunk_id=hit.chunk_id,
                    stable_chunk_id=hit.stable_chunk_id,
                )
                accumulators[hit.stable_chunk_id] = entry

            entry.fused_score += 1.0 / (k + hit.rank)
            if hit.channel == RetrievalChannel.SEMANTIC:
                entry.semantic_rank = hit.rank
            elif hit.channel == RetrievalChannel.FULLTEXT:
                entry.fulltext_rank = hit.rank

    sorted_entries = sorted(
        accumulators.values(),
        key=lambda entry: (
            -entry.fused_score,
            entry.semantic_rank if entry.semantic_rank is not None else 10_000,
            entry.fulltext_rank if entry.fulltext_rank is not None else 10_000,
        ),
    )

    return [
        FusedChunkHit(
            chunk_id=entry.chunk_id,
            stable_chunk_id=entry.stable_chunk_id,
            fused_score=entry.fused_score,
            semantic_rank=entry.semantic_rank,
            fulltext_rank=entry.fulltext_rank,
        )
        for entry in sorted_entries
    ]
