from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from ingest.chunking import chunk_markdown
from ingest.embeddings import embed_texts
from ingest.metadata import load_document_from_manifest_entry, load_manifest
from ingest.persist import replace_document_chunks, upsert_document

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "data" / "downloads" / "manifest.json"
DEFAULT_DOWNLOADS = REPO_ROOT / "data" / "downloads"
DEFAULT_MARKDOWN = REPO_ROOT / "data" / "markdown"


@dataclass
class IngestSummary:
    documents_processed: int = 0
    documents_failed: int = 0
    chunks_written: int = 0
    embeddings_created: int = 0


def ingest_filing(
    manifest_entry: dict,
    *,
    downloads_root: Path,
    markdown_root: Path,
    dry_run: bool = False,
    documents_only: bool = False,
    skip_embeddings: bool = False,
    client=None,
) -> tuple[int, int]:
    metadata = load_document_from_manifest_entry(
        manifest_entry,
        downloads_root=downloads_root,
        markdown_root=markdown_root,
    )
    chunks = chunk_markdown(metadata, metadata.markdown_content)

    if dry_run:
        print(
            f"  dry-run: {metadata.accession_number} "
            f"({metadata.ticker} FY{metadata.fiscal_year}) "
            f"-> {len(chunks)} chunks"
        )
        return 0, 0

    if client is None:
        from app.database.supabase import get_service_role_client

        client = get_service_role_client()

    document_id = upsert_document(client, metadata)
    print(
        f"  document {metadata.accession_number} "
        f"({metadata.ticker} FY{metadata.fiscal_year}) id={document_id}"
    )

    if documents_only:
        return 0, 0

    if not skip_embeddings and chunks:
        embeddings = embed_texts([chunk.chunk_text for chunk in chunks])
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk.embedding = embedding

    chunks_written = replace_document_chunks(client, document_id, chunks)
    embeddings_created = sum(1 for chunk in chunks if chunk.embedding is not None)
    print(f"  wrote {chunks_written} chunks ({embeddings_created} embedded)")
    return chunks_written, embeddings_created


def run_ingest(
    *,
    manifest_path: Path,
    downloads_root: Path,
    markdown_root: Path,
    ticker: str | None = None,
    dry_run: bool = False,
    documents_only: bool = False,
    skip_embeddings: bool = False,
) -> IngestSummary:
    manifest = load_manifest(manifest_path)
    filings = manifest.get("filings", [])
    if ticker:
        prefix = ticker.upper()
        filings = [entry for entry in filings if str(entry.get("ticker", "")).upper() == prefix]

    if not filings:
        raise ValueError("No manifest filings matched the ingest filters.")

    summary = IngestSummary()
    client = None
    if not dry_run:
        from app.database.supabase import get_service_role_client

        client = get_service_role_client()

    print(f"Ingesting {len(filings)} filing(s) from {manifest_path}")

    for index, entry in enumerate(filings, start=1):
        accession = entry.get("accession_number", "?")
        print(f"[{index}/{len(filings)}] {accession}")
        try:
            chunks_written, embeddings_created = ingest_filing(
                entry,
                downloads_root=downloads_root,
                markdown_root=markdown_root,
                dry_run=dry_run,
                documents_only=documents_only,
                skip_embeddings=skip_embeddings,
                client=client,
            )
        except Exception as exc:  # noqa: BLE001 — batch summary; fail fast per filing
            summary.documents_failed += 1
            print(f"  failed: {exc}", file=sys.stderr)
            raise

        summary.documents_processed += 1
        summary.chunks_written += chunks_written
        summary.embeddings_created += embeddings_created

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest SEC Markdown corpus into Supabase source_documents + document_chunks.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to manifest.json (default: data/downloads/manifest.json)",
    )
    parser.add_argument(
        "--downloads-root",
        type=Path,
        default=DEFAULT_DOWNLOADS,
        help="Root of downloaded HTML files",
    )
    parser.add_argument(
        "--markdown-root",
        type=Path,
        default=DEFAULT_MARKDOWN,
        help="Root of converted Markdown files",
    )
    parser.add_argument("--ticker", help="Only ingest one ticker (e.g. AAPL)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only; no Supabase or OpenAI calls",
    )
    parser.add_argument(
        "--documents-only",
        action="store_true",
        help="Upsert source_documents only; skip chunks and embeddings",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Write chunks without OpenAI embeddings (for testing persist path)",
    )
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"Manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    try:
        summary = run_ingest(
            manifest_path=args.manifest,
            downloads_root=args.downloads_root,
            markdown_root=args.markdown_root,
            ticker=args.ticker,
            dry_run=args.dry_run,
            documents_only=args.documents_only,
            skip_embeddings=args.skip_embeddings,
        )
    except Exception as exc:  # noqa: BLE001 — CLI exit code
        print(f"Ingest failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Done: "
        f"{summary.documents_processed} document(s), "
        f"{summary.chunks_written} chunk(s), "
        f"{summary.embeddings_created} embedding(s), "
        f"{summary.documents_failed} failed."
    )
    return 0 if summary.documents_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
