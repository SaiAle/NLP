# Function contracts for `nlp_app/analysis.py`

These are the pure functions extracted from the notebook. No printing, no
downloads, no global state — data in, data out.

## `top_long_words(words, min_len=8, n=10)`
- Lowercase each token, keep only `w.isalpha()` and `len(w) >= min_len`.
- "longer than 7 characters" means length >= 8, so default `min_len=8`.
- Return a list of `(word, count)` tuples for the `n` most common, most-frequent
  first. Returns fewer than `n` if fewer qualify.

## `modal_frequency_gap(words, modals)`
- Lowercase + `.isalpha()` filter the words; let `t` be that token count.
- If `t == 0`, return `0.0` (do not divide by zero).
- For each modal compute `count(modal) / t`; return `max(rel) - min(rel)`.

## `text_with_extreme_gap(words_by_file, modals)`
- Input: dict `{fileid: list_of_words}`.
- Compute `modal_frequency_gap` per file.
- Return `(max_fileid, min_fileid)`.

## `synonym_counts(words)`
- For each word, sum `len(syn.lemma_names())` over `wn.synsets(word)`.
- Return list of `(word, count)`. Document that this counts the headword and
  repeats lemmas across senses — that is the assignment's convention.

## `hyponym_counts(words)`
- For each word, sum `len(syn.hyponyms())` over `wn.synsets(word)`.
- Return list of `(word, count)`.
