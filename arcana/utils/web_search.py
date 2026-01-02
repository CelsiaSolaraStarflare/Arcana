"""Lightweight web search helpers using Brave's Search API. uwu"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List, Optional

import requests


_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Arcana/1.0 (+https://example.com)",
}


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


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    try:
        content = dotenv_path.read_text(encoding="utf-8")
    except OSError:
        return

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_api_key() -> Optional[str]:
    token = os.environ.get("BRAVE_SEARCH_API_KEY")
    if token:
        return token

    project_root = Path(__file__).resolve().parents[2]
    _load_dotenv(project_root / ".env")
    token = os.environ.get("BRAVE_SEARCH_API_KEY")
    if token:
        return token

    try:
        import streamlit as st
    except Exception:
        return None

    secrets = getattr(st, "secrets", None)
    if secrets:
        return secrets.get("BRAVE_SEARCH_API_KEY")

    return None


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

    token = api_key or _get_api_key()
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
