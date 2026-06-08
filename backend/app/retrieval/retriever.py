from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.database.engine import session_scope
from app.retrieval.assembly import assemble_passages
from app.retrieval.embed import embed_query
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import fulltext_search, semantic_search
from app.retrieval.schemas import RetrievalQuery, RetrievalResult

SessionFactory = Callable[[], AbstractContextManager[Session]]


class DocumentRetriever:
    def __init__(
        self,
        session_factory: SessionFactory | None = None,
        app_settings: Settings | None = None,
        openai_client: OpenAI | None = None,
    ) -> None:
        self._session_factory: SessionFactory = session_factory or session_scope
        self._settings = app_settings or settings
        self._openai_client = openai_client

    def search(self, query: RetrievalQuery) -> RetrievalResult:
        embedding = embed_query(query.text, client=self._openai_client)

        with self._session_factory() as session:
            semantic_hits = semantic_search(
                session,
                embedding,
                query.filters,
                top_k=self._settings.retrieval_semantic_top_k,
            )
            fulltext_hits = fulltext_search(
                session,
                query.text,
                query.filters,
                top_k=self._settings.retrieval_fulltext_top_k,
            )
            fused_hits = reciprocal_rank_fusion(
                [semantic_hits, fulltext_hits],
                k=self._settings.retrieval_rrf_k,
            )[: self._settings.retrieval_fusion_top_k]
            passages = assemble_passages(
                session,
                fused_hits,
                semantic_hits,
                fulltext_hits,
                neighbor_window=self._settings.retrieval_neighbor_window,
            )

        return RetrievalResult(
            query=query,
            passages=passages,
            fused_hits=fused_hits,
            semantic_candidates=len(semantic_hits),
            fulltext_candidates=len(fulltext_hits),
        )
