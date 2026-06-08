from __future__ import annotations

from uuid import uuid4

import pytest

from app.assistant.outputs import Citation, GroundedAnswer
from app.grounding.validator import GroundingValidationError, GroundingValidator
from app.retrieval.schemas import DocumentSummary, SourcePassage


def _passage(chunk_id, stable_chunk_id: str, text: str) -> SourcePassage:
    document_id = uuid4()
    return SourcePassage(
        chunk_id=chunk_id,
        stable_chunk_id=stable_chunk_id,
        document=DocumentSummary(
            id=document_id,
            ticker="AMZN",
            company_name="Amazon.com, Inc.",
            filing_type="10-K",
            fiscal_year=2024,
            accession_number="0001018724-24-000123",
            source_url="https://www.sec.gov/example",
        ),
        chunk_text=text,
        section_label="Item 7",
        page_label=None,
        token_count=100,
        chunk_metadata={},
        fused_score=0.03,
    )


def test_validator_accepts_grounded_citations() -> None:
    chunk_id = uuid4()
    passage = _passage(chunk_id, "acc:1", "AWS operating margin expanded during the year.")
    answer = GroundedAnswer(
        answer="AWS operating margin expanded.",
        citations=[
            Citation(
                chunk_id=chunk_id,
                stable_chunk_id="acc:1",
                claim_index=0,
                excerpt="AWS operating margin expanded",
            )
        ],
    )

    GroundingValidator().validate(answer, {chunk_id: passage})


def test_validator_rejects_unknown_chunk_id() -> None:
    chunk_id = uuid4()
    other_id = uuid4()
    passage = _passage(chunk_id, "acc:1", "AWS operating margin expanded.")
    answer = GroundedAnswer(
        answer="AWS operating margin expanded.",
        citations=[
            Citation(
                chunk_id=other_id,
                stable_chunk_id="acc:1",
                claim_index=0,
                excerpt="AWS operating margin expanded",
            )
        ],
    )

    with pytest.raises(GroundingValidationError, match="not retrieved"):
        GroundingValidator().validate(answer, {chunk_id: passage})


def test_validator_rejects_ungrounded_excerpt() -> None:
    chunk_id = uuid4()
    passage = _passage(chunk_id, "acc:1", "AWS operating margin expanded.")
    answer = GroundedAnswer(
        answer="Revenue grew sharply.",
        citations=[
            Citation(
                chunk_id=chunk_id,
                stable_chunk_id="acc:1",
                claim_index=0,
                excerpt="Revenue grew sharply",
            )
        ],
    )

    with pytest.raises(GroundingValidationError, match="not grounded"):
        GroundingValidator().validate(answer, {chunk_id: passage})


def test_validator_allows_insufficient_evidence_without_citations() -> None:
    answer = GroundedAnswer(
        answer="The corpus does not contain enough evidence.",
        citations=[],
        insufficient_evidence=True,
    )
    GroundingValidator().validate(answer, {})


def test_validator_rejects_citations_with_insufficient_evidence() -> None:
    chunk_id = uuid4()
    passage = _passage(chunk_id, "acc:1", "AWS operating margin expanded.")
    answer = GroundedAnswer(
        answer="Not enough evidence.",
        citations=[
            Citation(
                chunk_id=chunk_id,
                stable_chunk_id="acc:1",
                claim_index=0,
                excerpt="AWS operating margin expanded",
            )
        ],
        insufficient_evidence=True,
    )

    with pytest.raises(GroundingValidationError, match="must not include citations"):
        GroundingValidator().validate(answer, {chunk_id: passage})
