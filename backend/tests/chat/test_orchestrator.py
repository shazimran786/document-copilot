from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.assistant.outputs import Citation, GroundedAnswer
from app.chat.orchestrator import stream_turn
from app.grounding.validator import GroundingValidator
from app.retrieval.schemas import DocumentSummary, RetrievalQuery, RetrievalResult, SourcePassage


def _passage() -> SourcePassage:
    chunk_id = uuid4()
    return SourcePassage(
        chunk_id=chunk_id,
        stable_chunk_id="acc:1",
        document=DocumentSummary(
            id=uuid4(),
            ticker="AMZN",
            company_name="Amazon.com, Inc.",
            filing_type="10-K",
            fiscal_year=2024,
            accession_number="0001018724-24-000123",
            source_url="https://www.sec.gov/example",
        ),
        chunk_text="AWS operating margin expanded during the year.",
        section_label="Item 7",
        page_label=None,
        token_count=100,
        chunk_metadata={},
        fused_score=0.03,
    )


def test_stream_turn_returns_validated_result() -> None:
    asyncio.run(_test_stream_turn_returns_validated_result())


async def _test_stream_turn_returns_validated_result() -> None:
    passage = _passage()
    grounded = GroundedAnswer(
        answer="AWS operating margin expanded.",
        citations=[
            Citation(
                chunk_id=passage.chunk_id,
                stable_chunk_id=passage.stable_chunk_id,
                claim_index=0,
                excerpt="AWS operating margin expanded",
            )
        ],
    )
    retriever = MagicMock()
    retriever.search.return_value = RetrievalResult(
        query=RetrievalQuery(text="AWS operating margin"),
        passages=[passage],
        fused_hits=[],
        semantic_candidates=1,
        fulltext_candidates=1,
    )

    run_result = MagicMock()
    run_result.output = grounded

    with patch(
        "app.chat.orchestrator.document_agent.run",
        AsyncMock(return_value=run_result),
    ):
        items: list[object] = []
        async for item in stream_turn(
            user_text="AWS operating margin",
            thread_id=uuid4(),
            user_id="user-1",
            retriever=retriever,
            validator=GroundingValidator(),
        ):
            items.append(item)

    assert "".join(str(item) for item in items[:-1]) == grounded.answer
    result = items[-1]
    assert result.answer.answer == grounded.answer
    assert result.validation_failed is False
