# Project Design — FinTag: Distilling a Frontier LLM for SEC 8-K Event Extraction

> Status: **DRAFT for review.** This is a design doc, not a commitment. The
> point is to argue over specifics. Anything here can change.

## 1. One-line pitch

Turn a frontier LLM's ability to read SEC 8-K filings into a small, fine-tuned,
**self-hosted model that does the same structured event extraction at ~1% of the
cost and a fraction of the latency** — with a reproducible eval harness that
proves the tradeoff instead of asserting it.

## 2. Why this project (the hiring signal)

An "AI engineer who can call an API" is a commodity. This project demonstrates
the things that are not:

- **Data engineering:** ingesting and parsing real, messy filings at scale.
- **Supervision design:** using a frontier LLM as a labeler, and knowing when
  that's valid vs when it launders the teacher's bias.
- **Model building:** fine-tuning + distillation, not prompting.
- **Production economics:** quantization, serving, and a measured
  accuracy / $-per-1k-docs / latency Pareto frontier.
- **Evaluation rigor:** an objective ground-truth slice + a validated
  LLM-as-judge slice, with confidence intervals.

Resume line target: *"Distilled a frontier LLM into a fine-tuned, quantized
model serving 8-K event extraction at 98% of teacher quality for ~1% of the cost
and ~30 ms p50; reproducible eval harness with CI."*

## 3. The task, precisely

Input: one 8-K filing (HTML/text) from SEC EDGAR.
Output: a typed JSON record:

```json
{
  "item_codes": ["5.02"],                 // classification — HAS free labels
  "event_type": "executive_departure",    // normalized taxonomy
  "entities": {"person": "Jane Doe", "role": "CFO"},
  "key_figures": [],                       // e.g. severance, deal size
  "effective_date": "2025-03-01",
  "materiality_summary": "CFO Jane Doe resigned effective 2025-03-01..."
}
```

Two sub-tasks with *different* eval stories:

| Sub-task | Ground truth | How we eval |
| --- | --- | --- |
| **Item-code classification** | The codes the filer actually tagged (free, in the EDGAR index) | Macro-F1 vs true codes — fully objective |
| **Structured extraction** | No free labels | Gold hand-labeled set (n≈100) + LLM-as-judge validated against that gold set |

The classification labels keep us honest: if the distilled model's *classification*
collapses, the eval catches it without any subjective judgment.

## 4. Architecture / pipeline

```
EDGAR bulk index ──> ingest ──> parse/clean ──> dataset (parquet)
                                                   │
                        ┌──────────────────────────┤
                        ▼                           ▼
              teacher = frontier LLM        gold set (hand-labeled, n≈100)
              (silver labels @ scale)               │
                        │                            │
                        ▼                            ▼
              student training set ──> fine-tune ──> eval harness
              (ModernBERT for cls;        + distill   (F1 / judge / CIs)
               small decoder for          (LoRA)            │
               extraction)                                  ▼
                        └────────────> quantize ──> serve (vLLM/ONNX)
                                                      │
                                                      ▼
                                       cost/latency/throughput benchmark
                                       (student vs teacher API)
```

## 5. Modeling plan

- **Classification (item codes):** start with a fine-tuned encoder
  (ModernBERT / DeBERTa-v3). Strong baseline, cheap, fast. This alone answers
  "why not just train a classifier?" — we *do*, and we measure where it's not
  enough.
- **Extraction (structured fields):** distill frontier-LLM outputs into a small
  instruction model (Qwen2.5-1.5B / Llama-3.2-1B/3B) via LoRA. Structured output
  enforced with a JSON schema / constrained decoding.
- **Baselines we must beat (or honestly report losing to):**
  1. Zero-shot frontier LLM (the teacher / upper bound on quality, upper bound on cost).
  2. Zero-shot small open model (lower bound — shows the lift from fine-tuning).
  3. Rules/regex for the easy item codes (shows where ML actually earns its keep).

## 6. Evaluation (the centerpiece, not an afterthought)

- **Splits:** time-based train/val/test (train on older filings, test on newer)
  to avoid temporal leakage — a deliberate, defensible choice.
- **Metrics:** macro-F1 (classification); field-level precision/recall + a
  rubric LLM-judge score (extraction); **cost per 1k filings**; **p50/p95
  latency**; **throughput (docs/s)**.
- **Judge validation:** before trusting the LLM-as-judge, measure its agreement
  (Cohen's κ) with the human gold set. Report it. An unvalidated judge is vibes.
- **Reporting:** a single Pareto plot — quality vs $/1k vs latency — for every
  model variant. That plot is the project.

## 7. Serving & ops

- Package the student behind a small FastAPI service; containerized.
- Quantize (int8/4-bit) and report the quality/latency delta from quantization.
- Batch inference path for the bulk EDGAR backfill.
- Minimal observability: request logging, latency histograms, and a simple
  **drift check** (input-distribution + score monitoring) — because filings
  change over time and that's a real-world failure mode worth showing.

## 8. Scope control (so it actually ships)

**MVP (weekend 1–2):** EDGAR ingest for one or two item codes (e.g. 5.02, 2.02),
teacher labels, ModernBERT classifier, objective F1 eval, README with the Pareto
plot for {teacher, zero-shot small, fine-tuned small}. **This alone is a
portfolio-worthy project.**

**v1 (weekend 3–4):** add structured extraction + distillation, gold set +
validated judge, quantization, served API, cost/latency benchmark.

**Explicit non-goals:** price prediction, trading signals, "alpha" of any kind,
real-time streaming, multi-tenant infra. We are not building a hedge fund.

## 9. Risks & honest unknowns

- **EDGAR parsing is tedious** (HTML soup, amendments, exhibits). Mitigation:
  CFPB complaint dataset is a drop-in swap with cleaner labels if parsing eats
  too much time.
- **Teacher bias laundering:** distilling the LLM means inheriting its mistakes.
  Mitigation: the gold set is human-labeled and the classification slice uses
  real filer codes, so we can detect teacher error.
- **Compute:** LoRA on a 1–3B model needs a GPU. Mitigation: Colab/runpod for
  training; the encoder baseline trains on CPU/modest GPU.

## 10. Repo strategy (open question for you)

Two choices, your call:
- **New repo** (`fintag/`), clean history, link the old NLP homework as the
  "before." Best for portfolio optics.
- **Evolve this repo**, keeping the before/after diff visible in one place.

## 11. Open decisions I need from you

1. 8-K (richer finance story, messier data) vs CFPB complaints (cleaner data,
   faster to MVP)?
2. Do you have GPU access (Colab Pro / a cloud budget), or should the plan stay
   encoder-only + API-teacher so it runs on modest hardware?
3. New repo or evolve this one?
