from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.database.documents import ChunkRow, DocumentRow
from app.retrieval.assembly import assemble_passages
from app.retrieval.schemas import ChunkHit, FusedChunkHit, RetrievalChannel


def test_assemble_passages_builds_neighbors_and_channels() -> None:
    chunk_id = uuid4()
    document_id = uuid4()
    before_id = uuid4()
    after_id = uuid4()

    fused_hits = [
        FusedChunkHit(
            chunk_id=chunk_id,
            stable_chunk_id="acc:1",
            fused_score=0.03,
            semantic_rank=1,
            fulltext_rank=2,
        )
    ]
    semantic_hits = [
        ChunkHit(
            chunk_id=chunk_id,
            stable_chunk_id="acc:1",
            document_id=document_id,
            rank=1,
            score=0.9,
            channel=RetrievalChannel.SEMANTIC,
        )
    ]
    fulltext_hits = [
        ChunkHit(
            chunk_id=chunk_id,
            stable_chunk_id="acc:1",
            document_id=document_id,
            rank=2,
            score=0.4,
            channel=RetrievalChannel.FULLTEXT,
        )
    ]

    chunk_row = ChunkRow(
        id=chunk_id,
        document_id=document_id,
        stable_chunk_id="acc:1",
        chunk_index=3,
        chunk_text="Center chunk text",
        page_label=None,
        section_label="Item 7",
        token_count=120,
        chunk_metadata={"ticker": "AMZN"},
    )
    document_row = DocumentRow(
        id=document_id,
        ticker="AMZN",
        company_name="Amazon.com, Inc.",
        filing_type="10-K",
        fiscal_year=2024,
        accession_number="0001018724-24-000123",
        source_url="https://www.sec.gov/example",
    )
    neighbor_rows = [
        ChunkRow(
            id=before_id,
            document_id=document_id,
            stable_chunk_id="acc:0",
            chunk_index=2,
            chunk_text="Before chunk",
            page_label=None,
            section_label="Item 7",
            token_count=80,
            chunk_metadata={},
        ),
        ChunkRow(
            id=after_id,
            document_id=document_id,
            stable_chunk_id="acc:2",
            chunk_index=4,
            chunk_text="After chunk",
            page_label=None,
            section_label="Item 7",
            token_count=90,
            chunk_metadata={},
        ),
    ]

    session = MagicMock()
    with (
        patch(
            "app.retrieval.assembly.fetch_chunks_by_ids",
            return_value={chunk_id: chunk_row},
        ),
        patch(
            "app.retrieval.assembly.fetch_documents_by_ids",
            return_value={document_id: document_row},
        ),
        patch(
            "app.retrieval.assembly.fetch_neighbor_chunks",
            return_value=neighbor_rows,
        ),
    ):
        passages = assemble_passages(
            session,
            fused_hits,
            semantic_hits,
            fulltext_hits,
            neighbor_window=1,
        )

    assert len(passages) == 1
    passage = passages[0]
    assert passage.document.ticker == "AMZN"
    assert passage.channels == [
        RetrievalChannel.SEMANTIC,
        RetrievalChannel.FULLTEXT,
    ]
    assert [neighbor.position for neighbor in passage.neighbors] == ["before", "after"]
    assert passage.fused_score == 0.03


def test_assemble_passages_returns_empty_for_no_fused_hits() -> None:
    session = MagicMock()
    assert assemble_passages(session, [], [], [], neighbor_window=1) == []
