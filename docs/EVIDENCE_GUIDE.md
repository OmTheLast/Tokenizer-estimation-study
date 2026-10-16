# Reading our research evidence

Updated 2026-10-16. Our question is whether a cheap token-count estimate can help
with browser context budgeting. Graphs make measurements easier to understand;
the saved data, methods and checks are the evidence behind them. A graph does
not establish that the estimator is safe for browser use.

## 1. Do token counts differ across languages and tokenizers?

[Original tokens-per-character heatmap](../results/2026-10-15-phase1-pilot/run-02/tokens-per-character.png)

This compares measured content tokens relative to text length. It shows that
one universal conversion factor is a poor description of these samples. It
cannot tell us which model is more intelligent, or which tokenizer is faster.
The exact measurement definitions and values are in the
[pilot report](../results/2026-10-15-phase1-pilot/run-02/REPORT.md).

## 2. How far off are the two existing prediction methods?

![Typical and large errors](../results/2026-10-16-pilot-figures/run-02/01-error-comparison.png)

Smaller bars mean smaller errors. The **median** is the middle error after
sorting the errors from smallest to largest. The **95th percentile** marks the
level below which roughly 95% of these errors fall; some errors are larger.
For Qwen, the median falls from 47.6% with the old rule to 8.7% with LocalMind.
Yet LocalMind's 95th-percentile error is 33.9%. A good typical result can hide
large mistakes. Absolute error measures distance from the actual count in either
direction: guessing 80 or 120 when the answer is 100 both gives 20% error.

This is a comparison of two already-existing, unchanged methods on the same
texts. It is not an improvement caused by a new method we trained. The old rule
uses JavaScript UTF-16 length units divided by 3.5, not words divided by 3.5.

## 3. Where do we predict too few tokens?

![Undercount frequency by language](../results/2026-10-16-pilot-figures/run-02/02-undercount-by-language.png)

Each cell covers 100 texts. A value of 99 means 99 predictions were more than
20% too low. For example, LocalMind with LFM undercounts 99 of 100 Korean texts
by this amount. That is a reason to investigate, even though LFM's overall
median error is small. Both panels use the same color scale. The 20% cutoff
helps describe errors; it is not an agreed safe margin for deployment.

Show exceptions too: Qwen/Russian has more such undercounts with LocalMind
(13%) than with the old rule (3%). Better overall results do not mean every
language or every error measure improves.

## 4. What happens to individual predictions?

![Predicted versus actual counts](../results/2026-10-16-pilot-figures/run-02/03-predicted-versus-actual.png)

One dot is one text measured by that tokenizer. Dots on the dashed line are
correct; below it means too few predicted tokens, above it means too many.
All 9,000 measurements are included, although dots can overlap. Axis ranges
differ between panels, so do not compare apparent dot distances across panels.
The broad language colors help locate patterns, but do not prove their cause.

## What these figures cannot establish

The pilot uses 100 aligned sentence IDs, their translations in 18 language
varieties, and five tokenizer profiles: 1,800 texts and 9,000 measurements.
These are related translations and repeated measurements, not 9,000 independent
examples. The data cover FLORES+ dev sentences, not arbitrary browser pages,
code or full chat prompts. Models themselves were not run. MiniCPM uses its HF
JSON tokenizer; browser/GGUF equivalence remains unverified. FLORES+ remains
evaluation-only and devtest remains unaccessed. No fitting took place.

The pilot helped us propose a follow-up, so it is not an untouched final exam
for that proposal. The [v2 design](CJK_EXPERIMENT_V2.md) specifies a bounded
comparison on separate data; its results do not exist yet.

## Traceability and reproduction

- [Numeric plot data](../results/2026-10-16-pilot-figures/run-02/plot-data.json): summaries, heatmap values and count pairs, without raw source text or token sequences.
- [Validation](../results/2026-10-16-pilot-figures/run-02/validation.json): input/script hashes, versions, checks and visual review.
- [Plotting script](../scripts/plot_pilot_evidence.py): checks 20 summary values and 180 heatmap values against saved diagnostics, then plots all 9,000 count pairs.
- [Detailed diagnostics](../results/2026-10-15-pilot-diagnostics/run-02/REPORT.md) and its independent validation retain the underlying numerical analysis.
- PNG, SVG and PDF versions share each figure's filename in `results/2026-10-16-pilot-figures/run-02/`.

With the project's pinned environment and locally regenerated pilot Parquet:

```sh
.venv/bin/python scripts/plot_pilot_evidence.py --output results/2026-10-16-pilot-figures/run-03
```

Use a new output directory each time. The script refuses to overwrite earlier
runs. Run-01 is preserved; run-02 fixes a caption overlap and clarifies a title.
Their numeric plot data are identical. Restricted raw data and the local Parquet
are not included in the public repository; see the pilot reproduction notes.

## Progress is recorded as completed work

| Research step | Status | Evidence or next action |
| --- | --- | --- |
| Reproduce actual tokenizer counts and estimator | Complete for our five profiles | [Phase 0](PHASE0_RESULTS.md) |
| Measure multilingual pilot | Complete | 9,000 verified measurements |
| Analyze prediction errors | Complete | Saved diagnostics and figures above |
| Check candidate practice/exam data | Audit complete; preparation unfinished | [Audit report](../results/2026-10-16-cjk-preflight/audit-02/REPORT.md) |
| Specify one-weight versus three-weight comparison | v2 recorded before fitting | [Focused design](CJK_EXPERIMENT_V2.md) |
| Resolve narrow source-use question; freeze cleaned splits | Pending | Missing article IDs are a limitation, not an automatic stop |
| Fit candidate weights and evaluate unseen exam errors | Not started | Requires prepared data and authorization |
| Measure browser speed, memory and full-prompt budgeting | Not started | Separate planned study stage |

We do not assign a made-up completion percentage. The [dated history](STUDY_HISTORY.md)
and Git commits record decisions, failures and finished milestones. Future result
figures should answer a stated question, label units and sample counts, show
unfavorable outcomes, and link to their inputs and code. We will add improvement
and browser-performance graphs only when those measurements actually exist.
