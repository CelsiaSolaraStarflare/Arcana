"""Utilities for discovering indexed documents without relying on FiberDBMS.

The agent mode in the chatbot needs to present users with a list of documents
that can be summarised. Previously the only way to discover the available
files was to query ``FiberDBMS`` which couples the UI to the database layer.
This module provides a lightweight catalogue built directly from the cached
files on disk so that other components can browse and resolve documents
without touching the database implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from arcana.core.config import CACHE_DIR, SUPPORTED_FILE_TYPES


@dataclass(frozen=True)
class DocumentRecord:
    """Metadata about an indexed document available to the agent."""

    name: str
    path: Path


class DocumentCatalog:
    """Catalogue of files stored in the cache directory.

    The catalogue scans ``CACHE_DIR`` (or a caller supplied directory) and
    stores both the full relative path as well as the basename for each file so
    that callers can resolve documents even when only the filename is known.
    The catalogue purposefully avoids touching ``FiberDBMS`` so it can be used
    in contexts where the database layer is not available or should not be
    accessed directly.
    """

    def __init__(
        self,
        cache_dir: Path | str = CACHE_DIR,
        *,
        allowed_extensions: Optional[Iterable[str]] = None,
        exclude_subdirs: Optional[Sequence[str]] = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        extensions = allowed_extensions or SUPPORTED_FILE_TYPES
        self.allowed_extensions = {f".{ext.lower().lstrip('.')}" for ext in extensions}
        self.exclude_subdirs = {Path(subdir).parts[0] for subdir in (exclude_subdirs or [])}
        self._by_name: Dict[str, DocumentRecord] = {}
        self._by_basename: Dict[str, List[DocumentRecord]] = {}
        self.refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Rescan the cache directory and rebuild the catalogue."""

        self._by_name.clear()
        self._by_basename.clear()

        if not self.cache_dir.exists():
            return

        for path in self.cache_dir.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() and path.suffix.lower() not in self.allowed_extensions:
                continue

            try:
                relative = path.relative_to(self.cache_dir)
            except ValueError:
                # The file is outside of the cache directory; skip it.
                continue

            if relative.parts and relative.parts[0] in self.exclude_subdirs:
                continue

            relative_name = relative.as_posix()
            record = DocumentRecord(name=relative_name, path=path)
            self._by_name[relative_name] = record
            self._by_basename.setdefault(path.name.lower(), []).append(record)

    def list_names(self) -> List[str]:
        """Return all known document names sorted for display."""

        return sorted(self._by_name.keys(), key=str.lower)

    def find(self, file_name: str, *, refresh_on_miss: bool = True) -> Optional[DocumentRecord]:
        """Locate a document by name or basename.

        ``file_name`` can be an absolute path, a relative path within the cache
        directory, or just the basename of the file. When ``refresh_on_miss`` is
        true (the default) the catalogue will perform a one-time refresh if the
        first lookup fails in case new files were added since the last scan.
        """

        if not file_name:
            return None

        candidate = Path(file_name)
        if candidate.is_absolute() and candidate.exists():
            return DocumentRecord(name=candidate.name, path=candidate)

        normalised = self._normalise(candidate)
        record = self._by_name.get(normalised)
        if record:
            return record

        basename_matches = self._by_basename.get(candidate.name.lower())
        if basename_matches:
            if len(basename_matches) == 1:
                return basename_matches[0]
            # Prefer the shortest relative path to reduce ambiguity for users.
            return min(basename_matches, key=lambda rec: len(rec.name))

        if refresh_on_miss:
            self.refresh()
            return self.find(file_name, refresh_on_miss=False)

        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise(path: Path) -> str:
        """Return a normalised posix-style representation of ``path``."""

        return path.as_posix().lstrip("./")


__all__ = ["DocumentCatalog", "DocumentRecord"]
