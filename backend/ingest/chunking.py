from __future__ import annotations

import hashlib
import re

from ingest.models import ChunkRecord, DocumentMetadata

MAX_CHUNK_TOKENS = 800
OVERLAP_TOKENS = 100
MIN_CHUNK_TOKENS = 50
MAX_SECTION_LABEL_LENGTH = 255

SECTION_HEADING_RE = re.compile(
    r"^(?:#{1,3}\s+.+|Item\s+\d+[A-Z]?\.?\s+.+)$",
    re.MULTILINE | re.IGNORECASE,
)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _split_into_sections(markdown: str) -> list[tuple[str | None, str]]:
    matches = list(SECTION_HEADING_RE.finditer(markdown))
    if not matches:
        body = markdown.strip()
        return [(None, body)] if body else []

    sections: list[tuple[str | None, str]] = []
    prefix = markdown[: matches[0].start()].strip()
    if prefix:
        sections.append((None, prefix))

    for index, match in enumerate(matches):
        label = match.group(0).strip()
        label = re.sub(r"^#+\s*", "", label)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        if body:
            sections.append((label, body))

    return sections


def _split_long_section(
    section_label: str | None,
    text: str,
    *,
    max_tokens: int,
    overlap_tokens: int,
) -> list[tuple[str | None, str]]:
    if estimate_tokens(text) <= max_tokens:
        return [(section_label, text)]

    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4
    parts: list[tuple[str | None, str]] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            break_at = text.rfind("\n\n", start, end)
            if break_at > start + max_chars // 2:
                end = break_at
        piece = text[start:end].strip()
        if piece:
            parts.append((section_label, piece))
        if end >= len(text):
            break
        start = max(start + 1, end - overlap_chars)
    return parts


def _normalize_section_label(label: str | None) -> str | None:
    if label is None:
        return None
    cleaned = label.strip()
    if not cleaned:
        return None
    if len(cleaned) <= MAX_SECTION_LABEL_LENGTH:
        return cleaned
    return cleaned[: MAX_SECTION_LABEL_LENGTH - 3] + "..."


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def chunk_markdown(metadata: DocumentMetadata, markdown: str) -> list[ChunkRecord]:
    sections = _split_into_sections(markdown)
    pieces: list[tuple[str | None, str]] = []
    for section_label, body in sections:
        pieces.extend(
            _split_long_section(
                section_label,
                body,
                max_tokens=MAX_CHUNK_TOKENS,
                overlap_tokens=OVERLAP_TOKENS,
            )
        )

    chunks: list[ChunkRecord] = []
    chunk_index = 0
    char_cursor = 0
    for section_label, text in pieces:
        token_count = estimate_tokens(text)
        if token_count < MIN_CHUNK_TOKENS:
            char_cursor += len(text)
            continue

        stable_chunk_id = f"{metadata.accession_number}:{chunk_index}"
        char_start = char_cursor
        char_end = char_start + len(text)
        char_cursor = char_end

        chunks.append(
            ChunkRecord(
                stable_chunk_id=stable_chunk_id,
                chunk_index=chunk_index,
                chunk_text=text,
                section_label=_normalize_section_label(section_label),
                page_label=None,
                token_count=token_count,
                chunk_metadata={
                    "ticker": metadata.ticker,
                    "company_name": metadata.company_name,
                    "filing_type": metadata.filing_type,
                    "fiscal_year": metadata.fiscal_year,
                    "accession_number": metadata.accession_number,
                    "source_url": metadata.source_url,
                    "char_start": char_start,
                    "char_end": char_end,
                    "content_hash": _content_hash(text),
                },
            )
        )
        chunk_index += 1

    return chunks
