# /// script
# requires-python = ">=3.12"
# ///
"""Convert SEC filing HTML under data/downloads/ to Markdown via Docling.

Output mirrors the downloads folder layout under data/markdown/:
  downloads/2024/aapl_10-k_....htm  ->  markdown/2024/aapl_10-k_....md

Requires docling (installed in backend dev deps). Run:

  cd backend && uv run python ../data/convert_to_markdown.py
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from docling.document_converter import DocumentConverter

DOWNLOADS_DIR = Path(__file__).resolve().parent / "downloads"
MARKDOWN_DIR = Path(__file__).resolve().parent / "markdown"
HTML_SUFFIXES = {".html", ".htm"}


def find_html_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in HTML_SUFFIXES
    )


def output_path_for(html_path: Path) -> Path:
    relative = html_path.relative_to(DOWNLOADS_DIR)
    return MARKDOWN_DIR / relative.with_suffix(".md")


def convert_file(converter: DocumentConverter, html_path: Path) -> Path:
    output_path = output_path_for(html_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = converter.convert(str(html_path))
    markdown = result.document.export_to_markdown()
    if not markdown.strip():
        raise ValueError("Docling produced empty Markdown.")

    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert HTML filings in data/downloads/ to Markdown via Docling.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reconvert even when the .md file already exists.",
    )
    parser.add_argument(
        "--ticker",
        help="Only convert files whose name starts with this ticker (case-insensitive).",
    )
    args = parser.parse_args()

    html_files = find_html_files(DOWNLOADS_DIR)
    if args.ticker:
        prefix = args.ticker.lower() + "_"
        html_files = [path for path in html_files if path.name.lower().startswith(prefix)]

    if not html_files:
        print(f"No HTML files found under {DOWNLOADS_DIR}", file=sys.stderr)
        return 1

    converter = DocumentConverter()
    converted = 0
    skipped = 0
    failures: list[tuple[Path, str]] = []

    print(f"Found {len(html_files)} HTML file(s). Output root: {MARKDOWN_DIR}")

    for index, html_path in enumerate(html_files, start=1):
        output_path = output_path_for(html_path)
        if (
            not args.force
            and output_path.exists()
            and output_path.stat().st_mtime >= html_path.stat().st_mtime
        ):
            skipped += 1
            print(f"[{index}/{len(html_files)}] skip {html_path.relative_to(DOWNLOADS_DIR)}")
            continue

        started = time.perf_counter()
        label = html_path.relative_to(DOWNLOADS_DIR)
        print(f"[{index}/{len(html_files)}] converting {label} ...", flush=True)
        try:
            convert_file(converter, html_path)
        except Exception as exc:  # noqa: BLE001 — collect per-file failures for batch summary
            failures.append((html_path, str(exc)))
            print(f"  failed: {exc}", file=sys.stderr)
            continue

        elapsed = time.perf_counter() - started
        converted += 1
        print(f"  wrote {output_path.relative_to(MARKDOWN_DIR)} ({elapsed:.1f}s)")

    print(
        f"Done: {converted} converted, {skipped} skipped, {len(failures)} failed.",
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
