from __future__ import annotations

import re
from uuid import UUID

from app.assistant.outputs import GroundedAnswer
from app.retrieval.schemas import SourcePassage


class GroundingValidationError(Exception):
    """Raised when an assistant answer violates the grounding contract."""


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


class GroundingValidator:
    def validate(
        self,
        answer: GroundedAnswer,
        allowed_passages: dict[UUID, SourcePassage],
    ) -> None:
        if answer.insufficient_evidence:
            if answer.citations:
                raise GroundingValidationError(
                    "insufficient_evidence answers must not include citations."
                )
            return

        if not answer.citations:
            raise GroundingValidationError(
                "Grounded answers must include at least one citation."
            )

        for citation in answer.citations:
            passage = allowed_passages.get(citation.chunk_id)
            if passage is None:
                raise GroundingValidationError(
                    f"Citation references chunk_id {citation.chunk_id} "
                    "that was not retrieved in this turn."
                )

            if citation.stable_chunk_id != passage.stable_chunk_id:
                raise GroundingValidationError(
                    f"Citation stable_chunk_id {citation.stable_chunk_id!r} "
                    f"does not match passage {passage.stable_chunk_id!r}."
                )

            normalized_excerpt = _normalize_text(citation.excerpt)
            normalized_passage = _normalize_text(passage.chunk_text)
            if normalized_excerpt not in normalized_passage:
                raise GroundingValidationError(
                    f"Citation excerpt for {citation.stable_chunk_id} "
                    "is not grounded in the passage text."
                )
