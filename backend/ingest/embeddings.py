from __future__ import annotations

import time

from openai import OpenAI, RateLimitError

from app.config import settings

DEFAULT_BATCH_SIZE = 64
MAX_RETRIES = 5


def embed_texts(
    texts: list[str],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    client: OpenAI | None = None,
) -> list[list[float]]:
    if not texts:
        return []

    openai_client = client or OpenAI(api_key=settings.openai_api_key)
    embeddings: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        embeddings.extend(_embed_batch_with_retry(openai_client, batch))

    return embeddings


def _embed_batch_with_retry(client: OpenAI, batch: list[str]) -> list[list[float]]:
    delay_seconds = 1.0
    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(
                input=batch,
                model=settings.openai_embedding_model,
                dimensions=settings.openai_embedding_dimensions,
            )
            return [item.embedding for item in response.data]
        except RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(delay_seconds)
            delay_seconds *= 2
    raise RuntimeError("Unreachable: embed retry loop exhausted.")
