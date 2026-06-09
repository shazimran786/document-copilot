from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.assistant.outputs import Citation
from app.chat.schemas import MessageResponse
from app.retrieval.schemas import SourcePassage


def extract_latest_user_text(messages: list[dict[str, Any]]) -> str:
    """Return text from the last user message in AI SDK wire format."""
    for message in reversed(messages):
        if message.get("role") != "user":
            continue

        parts = message.get("parts")
        if isinstance(parts, list):
            chunks: list[str] = []
            for part in parts:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text" and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
            if chunks:
                return "".join(chunks).strip()

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    raise ValueError("No user message text found in request.")


def get_latest_user_message(messages: list[dict[str, Any]]) -> dict[str, Any]:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message
    raise ValueError("No user message found in request.")


def to_ui_message(row: MessageResponse) -> dict[str, Any]:
    if row.message_json:
        return row.message_json

    return {
        "id": str(row.id),
        "role": row.role,
        "parts": [{"type": "text", "text": row.content_text}],
    }


def build_citation_db_metadata(
    citation: Citation,
    passage: SourcePassage,
) -> dict[str, Any]:
    return {
        "stable_chunk_id": citation.stable_chunk_id,
        "ticker": passage.document.ticker,
        "company_name": passage.document.company_name,
        "filing_type": passage.document.filing_type,
        "fiscal_year": passage.document.fiscal_year,
        "section_label": passage.section_label,
        "page_label": passage.page_label,
        "source_url": passage.document.source_url,
        "accession_number": passage.document.accession_number,
    }


def build_citation_ui_metadata(
    citation: Citation,
    passage: SourcePassage,
) -> dict[str, Any]:
    return {
        "chunkId": str(citation.chunk_id),
        "stableChunkId": citation.stable_chunk_id,
        "claimIndex": citation.claim_index,
        "excerpt": citation.excerpt,
        "passageText": passage.chunk_text,
        "ticker": passage.document.ticker,
        "companyName": passage.document.company_name,
        "filingType": passage.document.filing_type,
        "fiscalYear": passage.document.fiscal_year,
        "sectionLabel": passage.section_label,
        "pageLabel": passage.page_label,
        "sourceUrl": passage.document.source_url,
        "accessionNumber": passage.document.accession_number,
    }


def build_assistant_ui_message(
    message_id: str,
    text: str,
    *,
    citations: list[Citation] | None = None,
    passages: dict[UUID, SourcePassage] | None = None,
    insufficient_evidence: bool = False,
    validation_failed: bool = False,
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "id": message_id,
        "role": "assistant",
        "parts": [{"type": "text", "text": text}],
    }

    citation_payload: list[dict[str, Any]] = []
    if citations and passages:
        citation_payload = [
            build_citation_ui_metadata(
                citation,
                passages[citation.chunk_id],
            )
            for citation in citations
            if citation.chunk_id in passages
        ]

    if citation_payload or insufficient_evidence or validation_failed:
        message["metadata"] = {
            "citations": citation_payload,
            "insufficientEvidence": insufficient_evidence,
            "validationFailed": validation_failed,
        }

    return message


def new_message_id() -> str:
    return f"msg_{uuid4().hex}"


def split_text_deltas(text: str) -> list[str]:
    words = text.split(" ")
    if not words:
        return [""]

    deltas: list[str] = []
    for index, word in enumerate(words):
        if index == 0:
            deltas.append(word)
        else:
            deltas.append(f" {word}")
    return deltas
