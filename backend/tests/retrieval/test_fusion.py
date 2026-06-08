from __future__ import annotations

from uuid import uuid4

from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.schemas import ChunkHit, RetrievalChannel


def _hit(
    stable_chunk_id: str,
    *,
    rank: int,
    channel: RetrievalChannel,
) -> ChunkHit:
    return ChunkHit(
        chunk_id=uuid4(),
        stable_chunk_id=stable_chunk_id,
        document_id=uuid4(),
        rank=rank,
        score=1.0 / rank,
        channel=channel,
    )


def test_reciprocal_rank_fusion_prefers_chunks_in_both_lists() -> None:
    semantic = [
        _hit("chunk-a", rank=1, channel=RetrievalChannel.SEMANTIC),
        _hit("chunk-b", rank=2, channel=RetrievalChannel.SEMANTIC),
    ]
    fulltext = [
        _hit("chunk-b", rank=1, channel=RetrievalChannel.FULLTEXT),
        _hit("chunk-c", rank=2, channel=RetrievalChannel.FULLTEXT),
    ]

    fused = reciprocal_rank_fusion([semantic, fulltext], k=60)

    assert [hit.stable_chunk_id for hit in fused[:3]] == ["chunk-b", "chunk-a", "chunk-c"]
    assert fused[0].semantic_rank == 2
    assert fused[0].fulltext_rank == 1


def test_reciprocal_rank_fusion_uses_rank_not_score() -> None:
    semantic = [_hit("only-semantic", rank=5, channel=RetrievalChannel.SEMANTIC)]
    fulltext = [_hit("only-fulltext", rank=1, channel=RetrievalChannel.FULLTEXT)]

    fused = reciprocal_rank_fusion([semantic, fulltext], k=60)

    assert fused[0].stable_chunk_id == "only-fulltext"
    assert fused[1].stable_chunk_id == "only-semantic"


def test_reciprocal_rank_fusion_returns_empty_for_empty_input() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
