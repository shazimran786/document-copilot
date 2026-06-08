from __future__ import annotations

from ingest.chunking import chunk_markdown, estimate_tokens
from ingest.models import DocumentMetadata

METADATA = DocumentMetadata(
    ticker="AAPL",
    company_name="Apple Inc.",
    filing_type="10-K",
    fiscal_year=2024,
    accession_number="0000320193-24-000123",
    source_url="https://www.sec.gov/example",
    markdown_content="",
    markdown_path="2024/aapl.md",
)


def test_estimate_tokens() -> None:
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100


def test_chunk_markdown_splits_on_item_headings() -> None:
    markdown = (
        "Item 1. Business\n\n"
        + ("Apple designs consumer electronics and services worldwide. " * 20)
        + "\n\nItem 7. Management's Discussion and Analysis\n\n"
        + ("Net sales increased during the fiscal year across all segments. " * 20)
    )
    chunks = chunk_markdown(METADATA, markdown)
    assert len(chunks) >= 2
    assert chunks[0].stable_chunk_id == "0000320193-24-000123:0"
    assert chunks[1].stable_chunk_id == "0000320193-24-000123:1"
    assert any("Business" in (chunk.section_label or "") for chunk in chunks)
    assert all(chunk.chunk_metadata["accession_number"] == METADATA.accession_number for chunk in chunks)


def test_chunk_markdown_splits_long_sections() -> None:
    body = "word " * 5000
    markdown = f"Item 1. Business\n\n{body}"
    chunks = chunk_markdown(METADATA, markdown)
    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
    assert all(chunk.token_count <= 800 for chunk in chunks)


def test_chunk_markdown_is_stable() -> None:
    markdown = "Item 1. Business\n\n" + ("Apple designs consumer electronics. " * 25)
    first = chunk_markdown(METADATA, markdown)
    second = chunk_markdown(METADATA, markdown)
    assert [chunk.stable_chunk_id for chunk in first] == [
        chunk.stable_chunk_id for chunk in second
    ]
    assert first
