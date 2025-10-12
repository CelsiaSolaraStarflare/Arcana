"""Helpers for managing reusable style guides."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

from arcana.core.config import DATA_DIR

STYLE_GUIDES_DIR = DATA_DIR / "style_guides"
_ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown"}


def ensure_style_guide_dir() -> Path:
    """Ensure the style guides directory exists and return its path."""

    STYLE_GUIDES_DIR.mkdir(parents=True, exist_ok=True)
    return STYLE_GUIDES_DIR


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\- ]+", "", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned


def list_style_guides() -> List[str]:
    """Return the available style guide names (without extensions)."""

    ensure_style_guide_dir()
    guides = []
    for path in STYLE_GUIDES_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in _ALLOWED_EXTENSIONS:
            guides.append(path.stem)
    return sorted(set(guides))


def _resolve_style_guide_path(name: str) -> Path:
    ensure_style_guide_dir()
    sanitized = _sanitize_filename(name)
    if not sanitized:
        raise ValueError("Style guide name must contain alphanumeric characters.")

    for extension in _ALLOWED_EXTENSIONS:
        candidate = STYLE_GUIDES_DIR / f"{sanitized}{extension}"
        if candidate.exists():
            return candidate

    # Default to markdown extension when creating a new file
    return STYLE_GUIDES_DIR / f"{sanitized}.md"


def load_style_guide(name: str) -> str:
    """Load the text content of the specified style guide."""

    path = _resolve_style_guide_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Style guide '{name}' was not found.")
    return path.read_text(encoding="utf-8")


def save_style_guide(name: str, content: str) -> Path:
    """Create or overwrite a style guide with the supplied content."""

    if not content.strip():
        raise ValueError("Style guide content cannot be empty.")

    path = _resolve_style_guide_path(name)
    ensure_style_guide_dir()
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path


def save_uploaded_style_guide(filename: str, data: bytes) -> Path:
    """Persist an uploaded style guide file."""

    if not data:
        raise ValueError("Uploaded file has no content.")

    base = Path(filename).stem
    sanitized = _sanitize_filename(base) or "style_guide"
    extension = Path(filename).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        extension = ".md"

    ensure_style_guide_dir()
    target = STYLE_GUIDES_DIR / f"{sanitized}{extension}"
    counter = 1
    while target.exists() and target.read_bytes() != data:
        target = STYLE_GUIDES_DIR / f"{sanitized}_{counter}{extension}"
        counter += 1

    target.write_bytes(data)
    return target


def get_style_guide_rules(names: Iterable[str]) -> str:
    """Concatenate the content of the selected style guides."""

    rules: List[str] = []
    for name in names:
        try:
            rules.append(load_style_guide(name).strip())
        except FileNotFoundError:
            continue
    return "\n\n".join(rule for rule in rules if rule)
