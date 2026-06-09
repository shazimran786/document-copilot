from __future__ import annotations

import re
from uuid import UUID

from app.assistant.outputs import GroundedAnswer
from app.retrieval.schemas import SourcePassage

_EXCERPT_PREFIX_MIN_LENGTH = 15
_EXCERPT_PREFIX_MAX_LENGTH = 50


class GroundingValidationError(Exception):
    """Raised when an assistant answer violates the grounding contract."""


def _normalize_text_for_grounding(text: str) -> str:
    """Normalize text for substring checks (tables, whitespace, case, punctuation)."""
    without_pipes = text.replace("|", " ")
    without_punctuation = re.sub(r"[^\w\s]", " ", without_pipes)
    return re.sub(r"\s+", " ", without_punctuation).strip().lower()


def _stable_chunk_ids_compatible(citation_stable: str, passage_stable: str) -> bool:
    if citation_stable == passage_stable:
        return True
    return passage_stable.startswith(f"{citation_stable}:")


def _words_grounded_in_order(excerpt: str, passage_text: str) -> bool:
    """Fallback: most excerpt words appear in the same order in the passage."""
    excerpt_words = [
        word
        for word in _normalize_text_for_grounding(excerpt).split()
        if len(word) > 2
    ]
    if len(excerpt_words) < 4:
        return False

    passage_words = _normalize_text_for_grounding(passage_text).split()
    passage_index = 0
    matched = 0
    for word in excerpt_words:
        while passage_index < len(passage_words):
            if passage_words[passage_index] == word:
                matched += 1
                passage_index += 1
                break
            passage_index += 1

    required = max(4, int(len(excerpt_words) * 0.75))
    return matched >= required


def _excerpt_is_grounded(excerpt: str, passage_text: str) -> bool:
    normalized_excerpt = _normalize_text_for_grounding(excerpt)
    normalized_passage = _normalize_text_for_grounding(passage_text)
    if not normalized_excerpt:
        return False
    if normalized_excerpt in normalized_passage:
        return True

    prefix_len = min(_EXCERPT_PREFIX_MAX_LENGTH, len(normalized_excerpt))
    if prefix_len >= _EXCERPT_PREFIX_MIN_LENGTH:
        if normalized_excerpt[:prefix_len] in normalized_passage:
            return True

    return _words_grounded_in_order(excerpt, passage_text)


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

            if not _stable_chunk_ids_compatible(
                citation.stable_chunk_id,
                passage.stable_chunk_id,
            ):
                raise GroundingValidationError(
                    f"Citation stable_chunk_id {citation.stable_chunk_id!r} "
                    f"does not match passage {passage.stable_chunk_id!r}."
                )

            if not _excerpt_is_grounded(citation.excerpt, passage.chunk_text):
                raise GroundingValidationError(
                    f"Citation excerpt for {citation.stable_chunk_id} "
                    "is not grounded in the passage text."
                )
