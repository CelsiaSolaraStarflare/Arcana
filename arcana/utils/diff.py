"""Utilities for rendering HTML diffs between text variants."""

from __future__ import annotations

import difflib
import html


def generate_inline_diff_html(original_text: str, edited_text: str) -> str:
    """Return HTML that shows inline differences between original and edited text.

    Added words are highlighted in green, deleted words are shown with a red
    strikethrough.
    """

    original_words = original_text.split()
    edited_words = edited_text.split()

    matcher = difflib.SequenceMatcher(None, original_words, edited_words)

    html_chunks: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            html_chunks.extend(html.escape(w) for w in original_words[i1:i2])
        elif tag == "delete":
            html_chunks.extend(
                "<span style='background-color:#ffe6e6;color:#000!important;text-decoration:line-through;'>-"
                f"{html.escape(w)}</span>"
                for w in original_words[i1:i2]
            )
        elif tag == "insert":
            html_chunks.extend(
                "<span style='background-color:#e6ffe6;color:#000!important;'>+"
                f"{html.escape(w)}</span>"
                for w in edited_words[j1:j2]
            )
        elif tag == "replace":
            html_chunks.extend(
                "<span style='background-color:#ffe6e6;color:#000!important;text-decoration:line-through;'>-"
                f"{html.escape(w)}</span>"
                for w in original_words[i1:i2]
            )
            html_chunks.extend(
                "<span style='background-color:#e6ffe6;color:#000!important;'>+"
                f"{html.escape(w)}</span>"
                for w in edited_words[j1:j2]
            )

    html_output = " ".join(html_chunks)
    return f"<div style='line-height:1.6; word-wrap:break-word;'>{html_output}</div>"


def generate_version_diff_html(current_text: str, version_text: str) -> str:
    """Generate HTML diff showing changes from ``version_text`` to ``current_text``."""

    current_words = current_text.split()
    version_words = version_text.split()

    matcher = difflib.SequenceMatcher(None, version_words, current_words)

    html_chunks: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            html_chunks.extend(html.escape(w) for w in version_words[i1:i2])
        elif tag == "delete":
            html_chunks.extend(
                "<span style='background-color:#ffe6e6;color:#000!important;text-decoration:line-through;'>-"
                f"{html.escape(w)}</span>"
                for w in version_words[i1:i2]
            )
        elif tag == "insert":
            html_chunks.extend(
                "<span style='background-color:#e6ffe6;color:#000!important;'>+"
                f"{html.escape(w)}</span>"
                for w in current_words[j1:j2]
            )
        elif tag == "replace":
            html_chunks.extend(
                "<span style='background-color:#ffe6e6;color:#000!important;text-decoration:line-through;'>-"
                f"{html.escape(w)}</span>"
                for w in version_words[i1:i2]
            )
            html_chunks.extend(
                "<span style='background-color:#e6ffe6;color:#000!important;'>+"
                f"{html.escape(w)}</span>"
                for w in current_words[j1:j2]
            )

    html_output = " ".join(html_chunks)
    return (
        "<div style='line-height:1.6; word-wrap:break-word; font-size:0.9em; padding:10px;"
        " border:1px solid #ddd; border-radius:5px; margin:5px 0;'>"
        f"{html_output}</div>"
    )

