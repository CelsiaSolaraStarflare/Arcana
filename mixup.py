"""Utility functions for Arcana Mixup.

This module provides a lightweight import path for tests that expect
functions such as :func:`parse_markdown_content_to_word` and
:func:`parse_markdown_to_word_runs` to live in a top-level ``mixup``
module.  The actual implementations live in
``arcana.pages.mixup`` where the Streamlit page is defined.  To keep
test dependencies minimal, we re-export the required helpers here.
"""

from arcana.pages.mixup import (
    parse_markdown_content_to_word,
    parse_mixed_formatting_to_runs,
    get_page_count_instructions,
    get_markdown_formatting_instructions,
)

# Backwards compatibility: older code and tests expect this name.
# The new implementation is ``parse_mixed_formatting_to_runs`` which
# supports additional formatting features.  Alias it for callers.
parse_markdown_to_word_runs = parse_mixed_formatting_to_runs

__all__ = [
    "parse_markdown_content_to_word",
    "parse_markdown_to_word_runs",
    "get_page_count_instructions",
    "get_markdown_formatting_instructions",
]
