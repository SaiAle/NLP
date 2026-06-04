"""Starter test suite for nlp_app.analysis.

P0 = regression for the two known NameError bugs.
P1 = pure logic, offline (no corpus downloads).
P2 = WordNet-backed, deterministic; skipped if the corpus is unavailable.
"""
import pytest

from nlp_app import analysis

MODALS = ["can", "could", "may", "might", "would", "will", "shall"]


# ---------------------------------------------------------------- P1: pure logic
def test_top_long_words_filters_by_length():
    words = ["nation", "freedom", "responsibility", "the", "government"]
    result = dict(analysis.top_long_words(words, min_len=8))
    assert "responsibility" in result
    assert "government" in result
    assert "freedom" not in result  # len 7, "longer than 7" excludes it
    assert "the" not in result


def test_top_long_words_excludes_punctuation_tokens():
    words = ["----------", "fellow-citizens", "responsibility"]
    result = [w for w, _ in analysis.top_long_words(words, min_len=8)]
    assert "----------" not in result  # not isalpha


def test_top_long_words_caps_at_n():
    words = [f"word{i:05d}" for i in range(50)]
    assert len(analysis.top_long_words(words, min_len=4, n=10)) <= 10


def test_modal_frequency_gap_basic():
    gap = analysis.modal_frequency_gap(["can", "can", "will"], ["can", "will"])
    assert gap == pytest.approx(1 / 3)  # 2/3 - 1/3


def test_modal_frequency_gap_empty_is_zero():
    assert analysis.modal_frequency_gap([], MODALS) == 0.0


# ------------------------------------------------- P0/P2: WordNet-backed pipelines
wordnet = pytest.mark.wordnet


@wordnet
def test_synonym_counts_runs_and_finds_known_synonym():
    # P0: this pipeline must not raise NameError (regression for cell 24).
    counts = dict(analysis.synonym_counts(["car"]))
    assert counts["car"] > 0


@wordnet
def test_hyponym_counts_runs_and_is_nonempty():
    # P0: regression for cell 32.
    counts = dict(analysis.hyponym_counts(["color"]))
    assert counts["color"] > 0
