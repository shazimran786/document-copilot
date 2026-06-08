from __future__ import annotations

from uuid import uuid4

import pytest

from app.assistant.outputs import Citation, GroundedAnswer


def test_grounded_answer_requires_answer_text() -> None:
    with pytest.raises(ValueError):
        GroundedAnswer(answer="", citations=[])


def test_citation_requires_excerpt() -> None:
    with pytest.raises(ValueError):
        Citation(
            chunk_id=uuid4(),
            stable_chunk_id="acc:1",
            claim_index=0,
            excerpt="",
        )
