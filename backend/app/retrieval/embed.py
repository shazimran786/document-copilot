from __future__ import annotations

from openai import OpenAI

from ingest.embeddings import embed_texts


def embed_query(text: str, *, client: OpenAI | None = None) -> list[float]:
    return embed_texts([text], client=client)[0]
