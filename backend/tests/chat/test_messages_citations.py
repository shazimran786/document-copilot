from __future__ import annotations

from uuid import uuid4

from app.assistant.outputs import Citation
from app.chat.messages import build_assistant_ui_message, build_citation_db_metadata
from app.retrieval.schemas import DocumentSummary, SourcePassage


def test_build_assistant_ui_message_includes_citation_metadata() -> None:
    chunk_id = uuid4()
    document_id = uuid4()
    passage = SourcePassage(
        chunk_id=chunk_id,
        stable_chunk_id="acc:1",
        document=DocumentSummary(
            id=document_id,
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            filing_type="10-K",
            fiscal_year=2024,
            accession_number="0001045810-24-000123",
            source_url="https://www.sec.gov/example",
        ),
        chunk_text="Data Center demand increased during the year.",
        section_label="Item 1",
        page_label=None,
        token_count=80,
        chunk_metadata={},
        fused_score=0.02,
    )
    citation = Citation(
        chunk_id=chunk_id,
        stable_chunk_id="acc:1",
        claim_index=0,
        excerpt="Data Center demand increased",
    )

    message = build_assistant_ui_message(
        "msg_test",
        "Data Center demand increased.",
        citations=[citation],
        passages={chunk_id: passage},
    )

    assert message["metadata"]["citations"][0]["ticker"] == "NVDA"
    assert message["metadata"]["citations"][0]["stableChunkId"] == "acc:1"


def test_build_citation_db_metadata_uses_snake_case() -> None:
    chunk_id = uuid4()
    document_id = uuid4()
    passage = SourcePassage(
        chunk_id=chunk_id,
        stable_chunk_id="acc:1",
        document=DocumentSummary(
            id=document_id,
            ticker="MSFT",
            company_name="Microsoft Corporation",
            filing_type="10-K",
            fiscal_year=2024,
            accession_number="0000950170-24-000123",
            source_url="https://www.sec.gov/example",
        ),
        chunk_text="Azure revenue grew.",
        section_label="Item 7",
        page_label=None,
        token_count=50,
        chunk_metadata={},
        fused_score=0.01,
    )
    citation = Citation(
        chunk_id=chunk_id,
        stable_chunk_id="acc:1",
        claim_index=0,
        excerpt="Azure revenue grew",
    )

    metadata = build_citation_db_metadata(citation, passage)
    assert metadata["stable_chunk_id"] == "acc:1"
    assert metadata["company_name"] == "Microsoft Corporation"
