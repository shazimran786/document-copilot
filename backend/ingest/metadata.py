from __future__ import annotations

import json
from pathlib import Path

from ingest.models import DocumentMetadata

COMPANY_NAMES: dict[str, str] = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
}


def markdown_path_for(
    manifest_entry: dict,
    *,
    downloads_root: Path,
    markdown_root: Path,
) -> Path:
    rel = Path(str(manifest_entry["local_path"]).replace("\\", "/"))
    return markdown_root / rel.with_suffix(".md")


def fiscal_year_from_manifest(manifest_entry: dict) -> int:
    report_date = manifest_entry.get("report_date") or manifest_entry.get("filing_date")
    if not report_date:
        raise ValueError(
            f"Missing report_date/filing_date for accession "
            f"{manifest_entry.get('accession_number')!r}."
        )
    return int(str(report_date)[:4])


def company_name_for_ticker(ticker: str) -> str:
    name = COMPANY_NAMES.get(ticker.upper())
    if not name:
        raise ValueError(f"No company name mapping for ticker {ticker!r}.")
    return name


def load_manifest(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def build_document_metadata(
    manifest_entry: dict,
    markdown: str,
    *,
    markdown_path: Path,
) -> DocumentMetadata:
    ticker = str(manifest_entry["ticker"]).upper()
    markdown_stripped = markdown.strip()
    if not markdown_stripped:
        raise ValueError(
            f"Empty Markdown for accession {manifest_entry['accession_number']!r} "
            f"at {markdown_path}."
        )

    return DocumentMetadata(
        ticker=ticker,
        company_name=company_name_for_ticker(ticker),
        filing_type=str(manifest_entry["form"]),
        fiscal_year=fiscal_year_from_manifest(manifest_entry),
        accession_number=str(manifest_entry["accession_number"]),
        source_url=str(manifest_entry["source_url"]),
        markdown_content=markdown,
        markdown_path=str(markdown_path),
    )


def load_document_from_manifest_entry(
    manifest_entry: dict,
    *,
    downloads_root: Path,
    markdown_root: Path,
) -> DocumentMetadata:
    md_path = markdown_path_for(
        manifest_entry,
        downloads_root=downloads_root,
        markdown_root=markdown_root,
    )
    if not md_path.is_file():
        raise FileNotFoundError(
            f"Missing Markdown file {md_path}. "
            "Run: cd backend && uv run python ../data/convert_to_markdown.py"
        )
    markdown = md_path.read_text(encoding="utf-8")
    return build_document_metadata(
        manifest_entry,
        markdown,
        markdown_path=md_path,
    )
