from __future__ import annotations

from pathlib import Path
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.config import settings
from app.database.documents import (
    chunk_row_to_source_passage,
    fetch_chunk_by_stable_id,
    fetch_neighbor_chunks,
)
from app.retrieval.schemas import RetrievalFilters, RetrievalQuery, SourcePassage

_INSTRUCTIONS_PATH = Path(__file__).parent / "instructions.md"
_PASSAGE_PREVIEW_CHARS = 600
_TOOL_PREVIEW_CHARS = 400


def load_instructions() -> str:
    return _INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def _register_passage(deps: DocumentAgentDeps, passage: SourcePassage) -> None:
    deps.retrieved_passages[passage.chunk_id] = passage


def _compact_passage(passage: SourcePassage, *, max_chars: int) -> dict[str, object]:
    preview = passage.chunk_text[:max_chars]
    if len(passage.chunk_text) > max_chars:
        preview += "..."
    return {
        "chunk_id": str(passage.chunk_id),
        "stable_chunk_id": passage.stable_chunk_id,
        "ticker": passage.document.ticker,
        "fiscal_year": passage.document.fiscal_year,
        "section_label": passage.section_label,
        "text": preview,
    }


def format_seed_passages(passages: list[SourcePassage]) -> str:
    if not passages:
        return "No passages were retrieved for this question."

    blocks: list[str] = []
    for index, passage in enumerate(passages, start=1):
        compact = _compact_passage(passage, max_chars=_PASSAGE_PREVIEW_CHARS)
        blocks.append(
            f"Passage {index}\n"
            f"- chunk_id: {compact['chunk_id']}\n"
            f"- stable_chunk_id: {compact['stable_chunk_id']}\n"
            f"- ticker: {compact['ticker']}\n"
            f"- fiscal_year: {compact['fiscal_year']}\n"
            f"- section: {compact['section_label']}\n"
            f"- text: {compact['text']}"
        )
    return "\n\n".join(blocks)


def build_user_prompt(user_text: str, passages: list[SourcePassage]) -> str:
    return (
        f"Analyst question:\n{user_text}\n\n"
        f"Retrieved passages:\n{format_seed_passages(passages)}"
    )


document_agent = Agent(
    OpenAIChatModel(
        settings.openai_chat_model,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    ),
    deps_type=DocumentAgentDeps,
    output_type=GroundedAnswer,
    system_prompt=load_instructions(),
    defer_model_check=True,
)


@document_agent.tool
def search_filings(
    ctx: RunContext[DocumentAgentDeps],
    query: str,
    tickers: list[str] | None = None,
    fiscal_years: list[int] | None = None,
) -> list[dict[str, object]]:
    """Search SEC filings for passages relevant to the query."""
    result = ctx.deps.retriever.search(
        RetrievalQuery(
            text=query,
            filters=RetrievalFilters(tickers=tickers, fiscal_years=fiscal_years),
        )
    )
    summaries: list[dict[str, object]] = []
    for passage in result.passages:
        _register_passage(ctx.deps, passage)
        summaries.append(_compact_passage(passage, max_chars=_TOOL_PREVIEW_CHARS))
    return summaries


@document_agent.tool
def read_chunk(
    ctx: RunContext[DocumentAgentDeps],
    stable_chunk_id: str,
) -> dict[str, object] | None:
    """Read a filing chunk by its stable_chunk_id."""
    with ctx.deps.session_factory() as session:
        chunk_row = fetch_chunk_by_stable_id(session, stable_chunk_id)
        if chunk_row is None:
            return None
        passage = chunk_row_to_source_passage(session, chunk_row)
    _register_passage(ctx.deps, passage)
    return _compact_passage(passage, max_chars=_TOOL_PREVIEW_CHARS)


@document_agent.tool
def read_surrounding_chunks(
    ctx: RunContext[DocumentAgentDeps],
    stable_chunk_id: str,
) -> list[dict[str, object]]:
    """Read neighboring chunks around a stable_chunk_id within the same filing."""
    with ctx.deps.session_factory() as session:
        chunk_row = fetch_chunk_by_stable_id(session, stable_chunk_id)
        if chunk_row is None:
            return []
        center = chunk_row_to_source_passage(session, chunk_row)
        _register_passage(ctx.deps, center)
        neighbor_rows = fetch_neighbor_chunks(
            session,
            chunk_row.document_id,
            chunk_row.chunk_index,
            window=1,
        )
        summaries = [_compact_passage(center, max_chars=_TOOL_PREVIEW_CHARS)]
        for neighbor_row in neighbor_rows:
            neighbor = chunk_row_to_source_passage(session, neighbor_row)
            _register_passage(ctx.deps, neighbor)
            summaries.append(_compact_passage(neighbor, max_chars=_TOOL_PREVIEW_CHARS))
    return summaries
