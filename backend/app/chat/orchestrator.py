from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.assistant.agent import build_user_prompt, document_agent
from app.chat.messages import split_text_deltas
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.database.engine import session_scope
from app.grounding.validator import GroundingValidationError, GroundingValidator
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import RetrievalQuery, SourcePassage

logger = logging.getLogger(__name__)

GROUNDING_FALLBACK_MESSAGE = (
    "I could not verify citations for this answer against the retrieved filings. "
    "Please try rephrasing your question or ask for a narrower topic."
)


@dataclass(frozen=True)
class TurnResult:
    answer: GroundedAnswer
    passages: dict[UUID, SourcePassage]
    message_id: str
    message_uuid: UUID
    validation_failed: bool = False


def _seed_passages(retrieval_passages: list[SourcePassage]) -> dict[UUID, SourcePassage]:
    return {passage.chunk_id: passage for passage in retrieval_passages}


def _normalize_agent_answer(answer: GroundedAnswer) -> GroundedAnswer:
    """Fix common model mistakes before grounding validation."""
    if answer.insufficient_evidence and answer.citations:
        logger.info(
            "Dropping %d citation(s) from insufficient_evidence answer",
            len(answer.citations),
        )
        return answer.model_copy(update={"citations": []})
    return answer


async def stream_turn(
    *,
    user_text: str,
    thread_id: UUID,
    user_id: str,
    retriever: DocumentRetriever,
    validator: GroundingValidator,
    message_id: str | None = None,
) -> AsyncIterator[str | TurnResult]:
    message_uuid = uuid4()
    wire_message_id = message_id or f"msg_{message_uuid.hex}"

    retrieval = retriever.search(RetrievalQuery(text=user_text))
    retrieved_passages = _seed_passages(retrieval.passages)

    deps = DocumentAgentDeps(
        user_id=user_id,
        thread_id=str(thread_id),
        retriever=retriever,
        session_factory=session_scope,
        retrieved_passages=retrieved_passages,
    )

    prompt = build_user_prompt(user_text, retrieval.passages)
    grounded_answer: GroundedAnswer | None = None

    try:
        run_result = await document_agent.run(prompt, deps=deps)
        grounded_answer = run_result.output
        for delta in split_text_deltas(grounded_answer.answer):
            yield delta
    except Exception:
        logger.exception("Agent run failed for thread %s", thread_id)
        raise

    assert grounded_answer is not None
    grounded_answer = _normalize_agent_answer(grounded_answer)

    try:
        validator.validate(grounded_answer, deps.retrieved_passages)
    except GroundingValidationError:
        logger.warning(
            "Grounding validation failed for thread %s",
            thread_id,
            exc_info=True,
        )
        yield TurnResult(
            answer=GroundedAnswer(
                answer=GROUNDING_FALLBACK_MESSAGE,
                citations=[],
                insufficient_evidence=True,
            ),
            passages=deps.retrieved_passages,
            message_id=wire_message_id,
            message_uuid=message_uuid,
            validation_failed=True,
        )
        return

    yield TurnResult(
        answer=grounded_answer,
        passages=deps.retrieved_passages,
        message_id=wire_message_id,
        message_uuid=message_uuid,
    )
