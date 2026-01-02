"""Lightweight web search helpers using Brave's Search API."""

from __future__ import annotations

import os
import re
from typing import Iterable, List, Optional

import requests


_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Arcana/1.0 (+https://example.com)",
}

_DEFAULT_API_KEY = "BSAU1UTC37OH1-kTszK9FYoKVi8haW7" #uwu


def _normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query or "").strip()


def _dedupe_results(items: Iterable[dict]) -> List[dict]:
    seen = set()
    unique: List[dict] = []
    for item in items:
        link = (item.get("link") or "").strip()
        if not link or link in seen:
            continue
        seen.add(link)
        unique.append(item)
    return unique


def search_brave_api(
    query: str,
    max_results: int = 5,
    timeout: int = 10,
    api_key: Optional[str] = None,
) -> List[dict]:
    """Fetch supplemental search results from Brave's Search API."""

    normalized = _normalize_query(query)
    if not normalized:
        return []

    token = api_key or os.environ.get("BRAVE_SEARCH_API_KEY") or _DEFAULT_API_KEY
    if not token:
        return []

    headers = dict(_DEFAULT_HEADERS)
    headers["X-Subscription-Token"] = token

    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": normalized, "count": max_results},
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
    except Exception:
        return []

    try:
        payload = response.json()
    except ValueError:
        return []

    results: List[dict] = []
    for item in (payload.get("web", {}) or {}).get("results", []) or []:
        title = (item.get("title") or "").strip()
        link = (item.get("url") or "").strip()
        description = (item.get("description") or "").strip()
        if title and link:
            results.append({"title": title, "link": link, "snippet": description})
        if len(results) >= max_results:
            break

    return _dedupe_results(results)


def search_web(query: str, max_results: int = 5, timeout: int = 10) -> List[dict]:
    """Public wrapper for supplemental web search."""

    return search_brave_api(query=query, max_results=max_results, timeout=timeout)
