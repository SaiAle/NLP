"""Pure, importable NLP analysis functions extracted from
``NLP AI Application.ipynb``.

Each function takes data in and returns data out. There is no printing, no
``nltk.download`` and no shared global state, so the logic can be exercised by
a test runner. The notebook imports these helpers instead of inlining the
logic, keeping the notebook and the tests on a single source of truth.

WordNet-backed helpers (:func:`synonym_counts`, :func:`hyponym_counts`) require
the ``wordnet`` corpus to be available, but they do not download it themselves;
callers (the notebook, or a CI step) are responsible for ensuring the corpus is
present.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Sequence, Tuple

# The set of English modal verbs used throughout the notebook.
MODALS: List[str] = ["can", "could", "may", "might", "would", "will", "shall"]


def top_long_words(
    words: Sequence[str], min_len: int = 8, n: int = 10
) -> List[Tuple[str, int]]:
    """Return the ``n`` most common alphabetic words of length ``>= min_len``.

    The notebook's original cell filtered on ``len(w) > 7`` (i.e. length >= 8)
    but did **not** apply ``.isalpha()``, so punctuation-bearing tokens could
    leak into the "top 10". We add the ``.isalpha()`` filter here for
    consistency with the modal-frequency cell; see TEST_COVERAGE_ANALYSIS.md.
    """
    tokens = [w.lower() for w in words if w.isalpha() and len(w) >= min_len]
    return Counter(tokens).most_common(n)


def modal_relative_frequencies(
    words: Sequence[str], modals: Sequence[str] = MODALS
) -> Dict[str, float]:
    """Map each modal to its frequency relative to the alphabetic token count.

    Returns ``0.0`` for every modal when there are no alphabetic tokens, so the
    caller never divides by zero.
    """
    tokens = [w.lower() for w in words if w.isalpha()]
    total = len(tokens)
    counts = Counter(tokens)
    if total == 0:
        return {m: 0.0 for m in modals}
    return {m: counts[m] / total for m in modals}


def modal_frequency_gap(
    words: Sequence[str], modals: Sequence[str] = MODALS
) -> float:
    """Spread (max - min) of the modal relative frequencies for one text.

    Guards the empty-text / divide-by-zero case by returning ``0.0``.
    """
    rel = modal_relative_frequencies(words, modals)
    if not rel:
        return 0.0
    values = rel.values()
    return max(values) - min(values)


def text_with_extreme_gap(
    words_by_file: Dict[str, Sequence[str]], modals: Sequence[str] = MODALS
) -> Tuple[str, str]:
    """Return ``(max_fileid, min_fileid)`` by modal frequency gap.

    Mirrors notebook cells 11/13: the file with the largest modal-frequency
    spread and the one with the smallest.
    """
    if not words_by_file:
        raise ValueError("words_by_file must not be empty")
    gaps = {fid: modal_frequency_gap(words, modals) for fid, words in words_by_file.items()}
    max_file = max(gaps, key=gaps.get)
    min_file = min(gaps, key=gaps.get)
    return max_file, min_file


def synonym_counts(words: Sequence[str]) -> List[Tuple[str, int]]:
    """For each word, total ``len(lemma_names())`` across all of its synsets.

    This is the notebook's convention (cell 24): it counts the headword and
    repeats lemmas that appear across multiple senses. The original cell raised
    ``NameError`` because it iterated over ``f_dist`` instead of the supplied
    word list; taking ``words`` as a parameter fixes that.
    """
    from nltk.corpus import wordnet as wn

    result: List[Tuple[str, int]] = []
    for word in words:
        count = sum(len(syn.lemma_names()) for syn in wn.synsets(word))
        result.append((word, count))
    return result


def hyponym_counts(words: Sequence[str]) -> List[Tuple[str, int]]:
    """For each word, total ``len(hyponyms())`` across all of its synsets.

    Mirrors notebook cell 30. The companion cell 32 raised ``NameError`` by
    referencing ``np_hyp`` instead of the list it built; returning the counts
    directly removes the stale-global dependency.
    """
    from nltk.corpus import wordnet as wn

    result: List[Tuple[str, int]] = []
    for word in words:
        count = sum(len(syn.hyponyms()) for syn in wn.synsets(word))
        result.append((word, count))
    return result
