"""Utilities for computing readability and style metrics."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Dict, List

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_VOWEL_RE = re.compile(r"[aeiouy]+", re.I)
_PASSIVE_PATTERN = re.compile(
    r"\b(am|is|are|was|were|be|been|being)\s+(\w+ed|\w+en)\b",
    re.IGNORECASE,
)


@dataclass
class TextMetrics:
    """Container for readability and usage metrics."""

    word_count: int
    sentence_count: int
    avg_sentence_length: float
    flesch_reading_ease: float
    passive_voice_ratio: float
    passive_voice_count: int
    syllable_count: int

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "TextMetrics":
        return cls(**data)


def _split_sentences(text: str) -> List[str]:
    stripped = text.strip()
    if not stripped:
        return []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", stripped) if s.strip()]
    return sentences or [stripped]


def _estimate_syllables(word: str) -> int:
    cleaned = word.lower().strip()
    if not cleaned:
        return 0

    cleaned = re.sub(r"[^a-z]", "", cleaned)
    if not cleaned:
        return 0

    matches = list(_VOWEL_RE.finditer(cleaned))
    syllables = len(matches)

    if cleaned.endswith("e") and syllables > 1:
        syllables -= 1

    if not matches:
        syllables = 1

    return max(1, syllables)


def calculate_text_metrics(text: str) -> TextMetrics:
    """Calculate readability and style metrics for the supplied text."""

    sentences = _split_sentences(text)
    words = _WORD_RE.findall(text)

    sentence_count = len(sentences)
    word_count = len(words)
    syllable_count = sum(_estimate_syllables(word) for word in words)

    avg_sentence_length = word_count / sentence_count if sentence_count else 0.0
    avg_sentence_length = round(avg_sentence_length, 2)

    words_per_sentence = word_count / sentence_count if sentence_count else 0.0
    syllables_per_word = syllable_count / word_count if word_count else 0.0

    flesch = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    flesch = round(flesch, 2) if not math.isnan(flesch) else 0.0

    passive_sentences = 0
    for sentence in sentences:
        if _PASSIVE_PATTERN.search(sentence):
            passive_sentences += 1

    passive_ratio = (passive_sentences / sentence_count * 100) if sentence_count else 0.0
    passive_ratio = round(passive_ratio, 2)

    return TextMetrics(
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_length=avg_sentence_length,
        flesch_reading_ease=flesch,
        passive_voice_ratio=passive_ratio,
        passive_voice_count=passive_sentences,
        syllable_count=syllable_count,
    )
