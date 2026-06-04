"""Test suite for nlp_app.analysis.

P0 = regression for the two known NameError bugs (cells 24 and 32).
P1 = pure logic, offline (no corpus downloads).
P2 = WordNet-backed, deterministic; skipped if the corpus is unavailable.
"""
import pytest

from nlp_app import analysis

MODALS = analysis.MODALS


# ---------------------------------------------------------------- P1: pure logic
def test_top_long_words_filters_by_length():
    words = ["nation", "freedom", "responsibility", "the", "government"]
    result = dict(analysis.top_long_words(words, min_len=8))
    assert "responsibility" in result
    assert "government" in result
    assert "freedom" not in result  # len 7, "longer than 7" excludes it
    assert "the" not in result


def test_top_long_words_excludes_punctuation_tokens():
    # Locks down the .isalpha() gap noted in TEST_COVERAGE_ANALYSIS.md.
    words = ["----------", "fellow--citizens", "responsibility"]
    result = [w for w, _ in analysis.top_long_words(words, min_len=8)]
    assert "----------" not in result
    assert "fellow--citizens" not in result
    assert result == ["responsibility"]


def test_top_long_words_is_case_insensitive_and_counts():
    words = ["Responsibility", "responsibility", "RESPONSIBILITY"]
    assert analysis.top_long_words(words, min_len=8) == [("responsibility", 3)]


def test_top_long_words_caps_at_n():
    words = [f"longword{i:03d}" for i in range(50)]
    assert len(analysis.top_long_words(words, min_len=4, n=10)) <= 10


def test_top_long_words_returns_fewer_than_n_when_few_qualify():
    assert analysis.top_long_words(["responsibility", "the"], n=10) == [
        ("responsibility", 1)
    ]


def test_modal_relative_frequencies_basic():
    rel = analysis.modal_relative_frequencies(["can", "can", "will"], ["can", "will"])
    assert rel["can"] == pytest.approx(2 / 3)
    assert rel["will"] == pytest.approx(1 / 3)


def test_modal_relative_frequencies_empty_is_zero():
    rel = analysis.modal_relative_frequencies([], MODALS)
    assert set(rel.values()) == {0.0}


def test_modal_frequency_gap_basic():
    gap = analysis.modal_frequency_gap(["can", "can", "will"], ["can", "will"])
    assert gap == pytest.approx(1 / 3)  # 2/3 - 1/3


def test_modal_frequency_gap_empty_is_zero():
    assert analysis.modal_frequency_gap([], MODALS) == 0.0


def test_modal_frequency_gap_ignores_non_alpha_in_total():
    # "123" is not alphabetic, so the denominator is 2 (can, will), gap = 0.
    gap = analysis.modal_frequency_gap(["can", "will", "123"], ["can", "will"])
    assert gap == pytest.approx(0.0)


def test_text_with_extreme_gap_picks_max_and_min():
    words_by_file = {
        "all_can.txt": ["can", "can", "can"],   # gap = 1.0 over {can, will}
        "balanced.txt": ["can", "will"],         # gap = 0.0
    }
    max_file, min_file = analysis.text_with_extreme_gap(
        words_by_file, ["can", "will"]
    )
    assert max_file == "all_can.txt"
    assert min_file == "balanced.txt"


def test_text_with_extreme_gap_empty_raises():
    with pytest.raises(ValueError):
        analysis.text_with_extreme_gap({}, MODALS)


# ------------------------------------------------- P0/P2: WordNet-backed pipelines
wordnet = pytest.mark.wordnet


@wordnet
def test_synonym_counts_runs_and_finds_known_synonym(wordnet_lemmas):
    # P0: this pipeline must not raise NameError (regression for cell 24).
    counts = dict(analysis.synonym_counts(["car"]))
    assert counts["car"] > 0
    assert "automobile" in wordnet_lemmas("car")


@wordnet
def test_synonym_counts_empty_word_is_zero():
    assert analysis.synonym_counts(["zzzznotaword"]) == [("zzzznotaword", 0)]


@wordnet
def test_hyponym_counts_runs_and_is_nonempty():
    # P0: regression for cell 32.
    counts = dict(analysis.hyponym_counts(["color"]))
    assert counts["color"] > 0
