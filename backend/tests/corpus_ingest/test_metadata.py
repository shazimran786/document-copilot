from __future__ import annotations

from pathlib import Path

import pytest

from ingest.metadata import (
    build_document_metadata,
    company_name_for_ticker,
    fiscal_year_from_manifest,
    markdown_path_for,
)

SAMPLE_ENTRY = {
    "ticker": "AAPL",
    "form": "10-K",
    "filing_date": "2024-11-01",
    "report_date": "2024-09-28",
    "accession_number": "0000320193-24-000123",
    "source_url": "https://www.sec.gov/example",
    "local_path": "2024\\aapl_10-k_2024-11-01_0000320193-24-000123.htm",
}


def test_markdown_path_for_normalizes_windows_separators(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    markdown = tmp_path / "markdown"
    path = markdown_path_for(
        SAMPLE_ENTRY,
        downloads_root=downloads,
        markdown_root=markdown,
    )
    assert path == markdown / "2024" / "aapl_10-k_2024-11-01_0000320193-24-000123.md"


def test_fiscal_year_from_report_date() -> None:
    assert fiscal_year_from_manifest(SAMPLE_ENTRY) == 2024


def test_company_name_for_ticker() -> None:
    assert company_name_for_ticker("aapl") == "Apple Inc."


def test_build_document_metadata() -> None:
    metadata = build_document_metadata(
        SAMPLE_ENTRY,
        "# Item 1. Business\n\nApple builds products.",
        markdown_path=Path("dummy.md"),
    )
    assert metadata.ticker == "AAPL"
    assert metadata.company_name == "Apple Inc."
    assert metadata.filing_type == "10-K"
    assert metadata.fiscal_year == 2024
    assert metadata.accession_number == "0000320193-24-000123"


def test_build_document_metadata_rejects_empty_markdown() -> None:
    with pytest.raises(ValueError, match="Empty Markdown"):
        build_document_metadata(
            SAMPLE_ENTRY,
            "   \n  ",
            markdown_path=Path("dummy.md"),
        )
