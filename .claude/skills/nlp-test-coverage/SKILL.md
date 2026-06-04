---
name: nlp-test-coverage
description: >-
  Add or improve automated tests for this NLP notebook project. Use when the
  user wants to test, refactor for testability, raise coverage, set up pytest,
  or fix the notebook's known bugs. Encodes the P0-P4 plan from
  TEST_COVERAGE_ANALYSIS.md: extract notebook cells into pure functions, then
  write deterministic tests that need no out-of-order cell execution.
---

# NLP Test Coverage

This project is a single Jupyter notebook (`NLP AI Application.ipynb`) with no
tests. The goal of this skill is to move it from **0% / untestable** to a
measured, regression-protected baseline.

## When to use
- "add tests", "improve coverage", "set up pytest", "make this testable"
- "fix the notebook bug" (the two NameErrors below)
- "refactor the notebook into functions"

## Background you must load first
Read `TEST_COVERAGE_ANALYSIS.md` at the repo root. It contains the full
findings. The two **known bugs** to fix while extracting code:
- Notebook cell 24 uses `f_dist` but the variable is `f_dst` -> NameError.
- Notebook cell 32 uses `np_hyp` but the list is `a_hyp` -> NameError.

## Workflow

1. **Extract pure functions** into `nlp_app/analysis.py`. Each function takes
   data in and returns data out — no `print`, no `nltk.download`, no global
   mutable state. Target signatures (see `references/function-contracts.md`):
   - `top_long_words(words, min_len=8, n=10)`  ("longer than 7" == len >= 8;
     apply `.isalpha()` so punctuation tokens are excluded)
   - `modal_frequency_gap(words, modals)`  (relative freq max - min; guard
     divide-by-zero on empty input)
   - `text_with_extreme_gap(words_by_file, modals)`  (returns max & min file)
   - `synonym_counts(words)` / `hyponym_counts(words)`  (WordNet-backed)

2. **Write tests** in `tests/test_analysis.py`. Start from
   `templates/test_analysis.py`. Cover, in priority order:
   - **P0** regression: synonym/hyponym pipelines run without NameError.
   - **P1** pure logic with hand-built token lists (no downloads): length
     filter, punctuation exclusion, top-n cap, divide-by-zero on `[]`.
   - **P2** WordNet fixtures: `synonym_counts(["car"])` includes `automobile`;
     `hyponym_counts(["color"])` is non-empty. Mark with
     `@pytest.mark.wordnet` and skip cleanly if the corpus is missing.

3. **Notebook smoke test (P3)**: add `nbmake` and run
   `pytest --nbmake "NLP AI Application.ipynb"` so cells must pass top-to-bottom
   on a clean kernel.

4. **Wire up tooling**: `pytest`, `pytest-cov`, `nbmake`. Add a GitHub Actions
   workflow (`references/ci-workflow.yml`) that installs deps, pre-downloads
   `gutenberg inaugural wordnet`, and runs `pytest --cov=nlp_app`.

5. **Update the notebook** to import from `nlp_app.analysis` instead of
   inlining logic, so the notebook and tests share one source of truth.

## Guardrails
- Keep network/download calls out of the importable module and out of P0/P1
  tests — those must run offline.
- Don't change analytical results the assignment depends on; only fix the two
  bugs and the missing `.isalpha()` filter, and note any behavior change.
- Set an initial coverage floor (e.g. 70% of `nlp_app`) and raise over time.
