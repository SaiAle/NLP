# Test Coverage Analysis & Proposed Improvements

_Analysis date: 2026-06-04_
_Subject: `NLP AI Application.ipynb`_

## 1. Summary

| Metric | Value |
| --- | --- |
| Test files | 0 |
| Test framework configured | None |
| CI / automated checks | None |
| Functions / importable units | 0 |
| Estimated line coverage | **0%** |

The repository contains a single Jupyter notebook with 16 code cells. All logic
runs at the top level of a cell, mutating shared global variables and relying on
downloaded NLTK corpora. There is currently **nothing that can be imported and
exercised by a test runner**, so the practical coverage is 0%.

## 2. Why this matters: bugs already present

Two defects exist in the current notebook that a single round of unit tests
would have caught. Both only stay hidden because notebook cells can be run out
of order and stale globals persist between runs.

1. **Cell 24** — `for i in f_dist.most_common(10):` references `f_dist`, but the
   frequency distribution defined in cell 20 is named `f_dst`. This raises
   `NameError` on a clean run.
2. **Cell 32** — `e_1.append(np_hyp[i][0])` references `np_hyp`, but the list
   built in cell 30 is named `a_hyp`. This also raises `NameError` on a clean
   run.
3. **Cell 13** *(found later by the notebook smoke test)* — the
   `for m in modals:` concordance loop is mis-indented one level too shallow, so
   it runs for **every** gutenberg file while `moby` is only assigned for files
   in `mst_used_text`. On a clean kernel the first file isn't a match, so `moby`
   is undefined when the loop uses it → `NameError`. Same "stale global hides
   the error" class as the other two; nesting the loop inside the `if` fixes it.

There are also correctness/robustness concerns worth pinning down with tests:

- **Cell 20** filters long words with `len(w) > 7` but does **not** apply
  `.isalpha()`, so punctuation-bearing tokens can leak into the "top 10 words".
  Compare with cell 10, which *does* filter `.isalpha()`. The inconsistency is
  exactly the kind of thing a test should lock down.
- **Synonym counting (cell 24)** sums `len(j.lemma_names())` across every synset,
  which double-counts the headword itself and counts the same lemma across
  multiple senses. Whether that is the intended definition of "number of
  synonyms" should be encoded in an assertion.
- **Modal frequency gap (cell 10)** divides modal counts by the total alphabetic
  token count. Division-by-zero, empty texts, and case-normalization are all
  untested edge cases.

## 3. Root cause: the code is not testable yet

The single biggest improvement to "test coverage" is to make the code
**testable at all**. Right now logic is inseparable from:

- I/O and downloads (`nltk.download(...)`),
- global mutable state (`list_1`, `e_1`, `e_2`, `d`, ...),
- print-based output instead of returned values.

**Recommendation:** extract the pure logic into small functions in a module
(e.g. `nlp_app/analysis.py`) and have the notebook import and call them. Each
function takes data in and returns data out, with no printing and no downloads.

Suggested function boundaries:

```python
def modal_relative_frequencies(words, modals): ...      # cell 7 / 10
def modal_frequency_gap(words, modals): ...             # cell 10
def text_with_max_gap(corpus_words_by_file, modals): ...# cell 11 / 13
def top_long_words(words, min_len=8, n=10): ...         # cell 20  (longer than 7 => >= 8)
def synonym_counts(words): ...                          # cell 24 / 26
def hyponym_counts(words): ...                          # cell 30 / 32
```

## 4. Proposed test areas (priority order)

### P0 — Regression tests for the two known bugs
Add tests that run the synonym and hyponym pipelines end-to-end on a tiny fixed
word list and assert they return a result without `NameError`. These fail today
and pass once the variable-name bugs are fixed.

### P1 — Pure-logic unit tests (no corpus download required)
Feed hand-built token lists into the extracted functions and assert exact
outputs. Examples:

- `top_long_words(["nation", "freedom", "responsibility", "the"], min_len=8)`
  returns only words of length >= 8, correctly ranked, and **excludes
  punctuation tokens** (locks down the `.isalpha()` gap).
- `modal_frequency_gap(["can","can","will"], ["can","will","shall"])`
  returns the expected max-minus-min relative frequency.
- `modal_frequency_gap([], modals)` handles the empty-text / divide-by-zero case
  gracefully instead of crashing.
- `top_long_words(words, n=10)` returns at most 10 items even when fewer than 10
  qualify.

### P2 — WordNet-backed tests (deterministic fixtures)
WordNet is stable, so tests can assert on well-known words:

- `synonym_counts(["car"])` returns a count > 0 and includes `automobile` among
  the lemma names.
- `hyponym_counts(["color"])` returns hyponyms such as `red`/`blue`.
- Document and assert the chosen counting convention (does "synonyms" include
  the headword? are duplicates across senses collapsed?).

### P3 — Notebook execution smoke test
Add a CI job that executes the whole notebook top-to-bottom on a clean kernel
(`jupyter nbconvert --to notebook --execute` or `nbmake`/`pytest --nbmake`).
This guarantees cells run **in order on a fresh state** and would have caught
both `NameError`s automatically.

### P4 — Data-contract / shape tests
Assert the resulting DataFrames (`df_freq`, `df_sn`, `df_hy`) have the expected
columns and exactly 10 rows, so downstream formatting changes can't silently
break the output.

## 5. Suggested tooling

- **pytest** as the runner.
- **pytest-cov** to start measuring real coverage once functions exist.
- **nbmake** (or `nbconvert --execute`) for the notebook smoke test.
- A minimal **GitHub Actions** workflow that installs `nltk`, pre-downloads the
  required corpora (`gutenberg`, `inaugural`, `wordnet`), and runs `pytest`.

## 6. Suggested first milestone

1. Extract the six functions above into `nlp_app/analysis.py` (fixing the two
   bugs in the process).
2. Add `tests/test_analysis.py` covering P0 + P1 (no network needed).
3. Add the notebook smoke test (P3) and a CI workflow.
4. Turn on `pytest-cov` and set an initial coverage floor (e.g. 70% of the new
   module), raising it over time.

This moves the project from **0% / untestable** to a measurable baseline and
prevents the class of "stale global / out-of-order cell" bug that currently
hides real errors.

## 7. Status — implemented

This milestone has now been implemented on this branch:

- `nlp_app/analysis.py` extracts the six pure functions (no I/O, no downloads,
  no globals). The `.isalpha()` filter is now applied to `top_long_words`, and
  empty-input divide-by-zero is guarded.
- `tests/test_analysis.py` + `tests/conftest.py` provide 15 tests (P0 + P1 + P2).
  P2 WordNet tests skip cleanly when the corpus is absent. Measured coverage of
  `nlp_app` is **~98%**.
- All **three** bugs above are fixed in the notebook with a minimal 6-line diff.
- `.github/workflows/tests.yml` runs pytest with coverage (floor 70%) and the
  `nbmake` notebook smoke test — the latter is what surfaced bug #3.
- `pyproject.toml` declares the package, deps, and the `wordnet` marker.
