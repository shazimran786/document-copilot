"""Smoke test for the grounded agent against the live corpus."""

from __future__ import annotations

import asyncio
import sys

from app.chat.orchestrator import stream_turn
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever

SMOKE_QUERIES = [
    "For Amazon, what did the filing say about AWS operating margin?",
    "How did NVIDIA describe Data Center demand drivers?",
    "Do the filings prove that generative AI improved margins for any company?",
]


async def _run_query(query: str) -> int:
    retriever = DocumentRetriever()
    validator = GroundingValidator()
    print(f"\n=== Query: {query!r} ===")

    deltas: list[str] = []
    turn_result = None
    async for item in stream_turn(
        user_text=query,
        thread_id=__import__("uuid").uuid4(),
        user_id="smoke-user",
        retriever=retriever,
        validator=validator,
    ):
        if isinstance(item, str):
            deltas.append(item)
        else:
            turn_result = item

    if turn_result is None:
        print("  (no turn result)")
        return 1

    print(f"  validation_failed={turn_result.validation_failed}")
    print(f"  insufficient_evidence={turn_result.answer.insufficient_evidence}")
    print(f"  citations={len(turn_result.answer.citations)}")
    print(f"  answer_preview={turn_result.answer.answer[:240]}...")
    return 0


async def main() -> int:
    failures = 0
    for query in SMOKE_QUERIES:
        try:
            failures += await _run_query(query)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            failures += 1

    if failures:
        print(f"\nAgent smoke finished with {failures} failure(s).")
        return 1

    print("\nAgent smoke finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
