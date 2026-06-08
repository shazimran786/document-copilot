from __future__ import annotations

import pytest

from app.retrieval.schemas import RetrievalFilters, RetrievalQuery


def test_retrieval_query_requires_non_empty_text() -> None:
    with pytest.raises(ValueError):
        RetrievalQuery(text="")


def test_retrieval_filters_default_to_unrestricted_search() -> None:
    query = RetrievalQuery(text="AWS operating margin")
    assert query.filters.tickers is None
    assert query.filters.fiscal_years is None
    assert query.filters.filing_types is None


def test_retrieval_query_accepts_optional_filters() -> None:
    query = RetrievalQuery(
        text="NVIDIA data center demand",
        filters=RetrievalFilters(tickers=["NVDA"], fiscal_years=[2024]),
    )
    assert query.filters.tickers == ["NVDA"]
    assert query.filters.fiscal_years == [2024]
