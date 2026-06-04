"""Shared pytest fixtures and WordNet availability handling.

Tests marked ``@pytest.mark.wordnet`` are skipped cleanly when the WordNet
corpus is not installed, so the P0/P1 suite always runs offline while the
WordNet-backed tests only run when the corpus is present.
"""
import pytest


def _wordnet_available() -> bool:
    try:
        from nltk.corpus import wordnet as wn

        wn.synsets("car")  # forces the corpus to load
        return True
    except LookupError:
        return False
    except ImportError:
        return False


WORDNET_AVAILABLE = _wordnet_available()


def pytest_collection_modifyitems(config, items):
    skip_wordnet = pytest.mark.skip(reason="WordNet corpus not available")
    for item in items:
        if "wordnet" in item.keywords and not WORDNET_AVAILABLE:
            item.add_marker(skip_wordnet)


@pytest.fixture
def wordnet_lemmas():
    """Return a helper that lists all lemma names for a word (across synsets)."""
    from nltk.corpus import wordnet as wn

    def _lemmas(word):
        names = set()
        for syn in wn.synsets(word):
            names.update(syn.lemma_names())
        return names

    return _lemmas
