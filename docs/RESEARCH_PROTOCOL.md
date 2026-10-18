# Research protocol: tokenizer-count estimation

**Historical umbrella scope:** the [comparative protocol v2](COMPARATIVE_STUDY_V2.md)
is the active direction approved on 2026-10-18. This document preserves the
original design; its completed diagnostic analysis remains valid evidence.

Version 1, recorded 2026-10-15, after the first pilot results were inspected.
Owner: Om. Prepared with Codex assistance. This is a working research protocol,
not a retrospective preregistration or a claim of novelty.

## Question and intended use

Can a small, inexpensive estimator predict token counts across languages and
tokenizers well enough to help a browser manage its context budget?

Accuracy, runtime cost and context-budget reliability are separate outcomes.
An estimator that predicts counts does not produce the token IDs needed by a
model. We must compare its practical benefit against exact tokenizer counting
in a worker before recommending a browser implementation.

| Question | Evidence needed | Current position |
| --- | --- | --- |
| RQ1: How do counts vary across tokenizers and language varieties? | Paired counts on identical text within each variety | First descriptive pilot complete |
| RQ2: How accurate are count estimators, particularly when they undercount? | Errors by tokenizer, language, length and text type; independent evaluation | Existing formula evaluated on one pilot; detailed diagnosis next |
| RQ3: Can a profile be inferred from tokenizer assets without fitting on target text? | A defined method and held-out tokenizer families | Not started |
| RQ4: Does estimation improve browser budgeting and performance? | Complete serialized prompts, output reserve, overflow and retention metrics, browser measurements | Not started |

## What our evidence currently supports

Phase 0 verified JS/Python token-ID agreement on 38 existing fixtures across
five profiles, ported the unchanged estimator, and explained special-token
reference discrepancies. Those fixtures are continuity checks, not independent
test data. MiniCPM's HF JSON tokenizer is not verified against its GGUF runtime.

The FLORES+ pilot measured 100 aligned sentence IDs × 18 language varieties ×
five tokenizer profiles. Its 9,000 rows are repeated measurements of related
material, **not 9,000 independent examples**. Each tokenizer-language cell has
100 observations. Translations help match meaning but do not control character
length, writing conventions or all translation effects.

The observed errors justify further investigation. They do not establish a
universal worst-error bound, model intelligence, a causal explanation for
language differences, or browser latency/memory benefits. Historical overlap
with unpublished estimator fitting data and upstream tokenizer training is
unknown. The pilot is exploratory, not a clean final test of future methods.

## Measurement contract

- Ground truth for the current pilot is the pinned tokenizer's content-token
  count with added special tokens disabled. Preserve separate special-enabled
  counts. Do not confuse these with full serialized chat counts.
- Compare two frozen predictions on each identical row: LocalMind's per-script,
  per-tokenizer weights, and `ceil(UTF-16 units / 3.5)`. This is characters in the
  historical JavaScript sense, not 3.5 words per token.
- Let actual count be T and prediction P. Signed percentage error is
  `100 * (P - T) / T`; negative means undercount. Also report errors in tokens,
  since a large percentage on a short text can represent few missing tokens.
- Report all 90 tokenizer-language cells. Summary groups supplement those cells;
  they must not hide a weak language. State group sizes and aggregation rules.
- Pin data, sampling, tokenizer assets, libraries, formulas and analysis code.
  Preserve old outputs. Corrections create a new version with an explanation.

## Next analysis: diagnosis of the frozen pilot

The versioned specification is [pilot-diagnostics-v1.json](../config/pilot-diagnostics-v1.json).
It is written before this detailed analysis, but after pilot summaries were seen.
Results remain exploratory. No new data, tokenizer downloads, model inference,
weight fitting, margin selection or devtest access is needed.

For both estimators, calculate per-cell and per-tokenizer undercount rate,
rate of underestimation greater than 20%, median and 95th-percentile absolute
percentage error, signed 5th/95th percentiles, maximum under/over error,
fraction within ±20%, and token shortfalls. The 20% threshold is a descriptive
continuity metric from the original plan, not an accepted product safety target.

Compare the two estimators on the same rows. Report all cells, including ones
where the older heuristic does better. Examine fixed Unicode-length bands and
existing script features; report sample sizes and empty cells. Do not search
for thresholds that make the estimator appear better.

Select the five largest percentage undercounts and five largest absolute token
shortfalls per tokenizer, using deterministic ties. Save IDs and numeric
features only. Any local text inspection must be labelled qualitative and must
not reproduce FLORES+ text publicly. Treat potential explanations, such as the
shared CJK weight, as hypotheses requiring separate controlled tests.

If uncertainty intervals are reported, resample aligned sentence IDs as blocks,
keeping every translation and tokenizer measurement together. Paired estimator
differences must use the same resampled blocks. Such intervals describe sampling
variability under this corpus design, not generalization to arbitrary browser
text. Do not treat exploratory cell comparisons as confirmatory significance
tests or claim a population guarantee from the worst observed sample.

## Stages and review gates

| Stage | Deliverable | Condition before advancing |
| --- | --- | --- |
| 0. Reproduction | Saved parity checks and discrepancy explanation | Review phase-0 evidence and limitations |
| 1. Describe and diagnose | Pilot diagnostics, coverage gaps, literature/evidence map | Review phases 0 and 1 with Om; choose bounded expansion |
| 2. Design improvements | Candidate methods and separate fitting/calibration/evaluation manifests | Explicitly authorize fitting; freeze split and comparison rules first |
| 3. Independent evaluation | Results on previously uninspected data and held-out families/languages | Freeze candidates before opening final evaluation; report failures |
| 4. Browser evaluation | Exact-worker, estimator and hybrid comparisons | Define product thresholds and hardware/browser workload before measurement |
| 5. Reporting | Reproducible write-up with limitations and attribution | Audit claims, sources, licensing and AI disclosure before submission/release |

Phase 1's pilot is complete; the broader phase is not. Adding 20+ tokenizers is
not automatically the next best step. First diagnose the existing five and use
the result to justify the coverage we add. A literature review must verify
primary sources and distinguish existing work from our contribution; citations
and novelty suggestions in the original proposal are leads, not verified claims.

## Data separation and future methods

FLORES+ is evaluation-only: no training, fitting or calibration on any split.
The original proposal's dev-fitting suggestion is superseded. Never re-host
its text or reconstructable token sequences where crawlers can collect them.
Current `devtest` remains unaccessed. No authorization to open it is implied here.

For future improvements, use separately licensed development and calibration
data. Reserve final evaluation before model selection. Keep near-duplicates,
translations of the same source, and fragments of the same document together
across splits. Group byte-identical or closely related tokenizer assets into
families before any held-out-tokenizer experiment. Record the grouping rule.

Once results influence a candidate design, do not call that corpus an untouched
final test for that design. Amendments and failed attempts remain in the log.
Negative findings are valid outcomes; do not change success criteria afterwards.

## Browser decision and evidence requirements

Before a browser trial, specify representative text types, input lengths,
languages, devices, browsers and warm/cold runs. Measure latency distributions,
startup/download cost, memory and worker communication for exact counting,
estimation and a clearly specified hybrid policy.

Tokenize each complete serialized prompt, including messages, templates, system
instructions and tools; reserve output capacity. Do not add isolated sentence
counts and assume they equal the joined prompt's count. Compare budget overflow
frequency/severity and retained context against an exact-count policy. Report
both unnecessary trimming and unused capacity with explicit denominators.

Acceptable overflow, latency, memory and retained-context thresholds are product
decisions still to be set with Om before that trial. Until then we can report
tradeoffs, but cannot declare an estimator deployment-ready. No training run,
package release or external submission is authorized by this protocol.

## Research record

Every substantive round records question, plan, inputs, versions, command,
outputs, checks, interpretation, limitations and exact next action. Scripts
generate numerical claims. Recovery checkpoints are local records; only files
actually pushed are on GitHub. Preserve attribution to LocalMind and disclose
Codex's coding, analysis and documentation assistance.

Evidence: [study history](STUDY_HISTORY.md), [phase 0](PHASE0_RESULTS.md),
[pilot notes](PHASE1_PILOT.md), and [saved pilot report](../results/2026-10-15-phase1-pilot/run-02/REPORT.md).

## Focused exploratory amendment — 2026-10-16

For the bounded CJK comparison, [v2](CJK_EXPERIMENT_V2.md) supersedes the
requirement to establish every original-document group before proceeding.
Keep known families together; report unknown article relationships as a
limitation. This trial will report descriptive fixed-test-set differences,
without bootstrap intervals or significance claims. The general stronger-study
requirements above remain relevant to later generalization claims. The separate
source-text use question remains pending. No fitting has occurred.

The [evidence guide](EVIDENCE_GUIDE.md) maps saved plots to their questions,
measurements and limitations, and lists completed and unstarted stages.
