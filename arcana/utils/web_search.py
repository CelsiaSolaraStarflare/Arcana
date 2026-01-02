"""Web search placeholder helpers (disabled)."""

from __future__ import annotations

from typing import List


def search_web(query: str, max_results: int = 5, timeout: int = 10) -> List[dict]:
    """Return no results because web search is disabled."""

    return []
