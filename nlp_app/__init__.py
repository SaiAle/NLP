"""Importable NLP analysis helpers extracted from the project notebook."""

from .analysis import (
    MODALS,
    hyponym_counts,
    modal_frequency_gap,
    modal_relative_frequencies,
    synonym_counts,
    text_with_extreme_gap,
    top_long_words,
)

__all__ = [
    "MODALS",
    "hyponym_counts",
    "modal_frequency_gap",
    "modal_relative_frequencies",
    "synonym_counts",
    "text_with_extreme_gap",
    "top_long_words",
]
