"""Manual smoke test for hybrid retrieval against the live Supabase corpus."""

from __future__ import annotations

import sys

from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import RetrievalQuery

SMOKE_QUERIES = [
    "AWS operating margin",
    "NVIDIA data center demand",
    "Azure AI infrastructure capacity",
    "Apple Services revenue mix",
    "generative AI improved margins",
]


def main() -> int:
    retriever = DocumentRetriever()
    failures = 0

    for query_text in SMOKE_QUERIES:
        print(f"\n=== Query: {query_text!r} ===")
        result = retriever.search(RetrievalQuery(text=query_text))
        print(
            f"semantic={result.semantic_candidates} "
            f"fulltext={result.fulltext_candidates} "
            f"fused={len(result.fused_hits)} "
            f"passages={len(result.passages)}"
        )

        if not result.passages:
            print("  (no passages returned)")
            if query_text != "generative AI improved margins":
                failures += 1
            continue

        for index, passage in enumerate(result.passages[:3], start=1):
            preview = passage.chunk_text.replace("\n", " ")[:120]
            channels = ", ".join(channel.value for channel in passage.channels)
            print(
                f"  {index}. [{passage.document.ticker} {passage.document.fiscal_year}] "
                f"score={passage.fused_score:.4f} channels={channels}"
            )
            print(f"     {preview}...")

    if failures:
        print(f"\nSmoke retrieval finished with {failures} unexpected empty result(s).")
        return 1

    print("\nSmoke retrieval finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
