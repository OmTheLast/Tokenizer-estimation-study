# Tokenizer estimation study

Study owner: Om. Repository: https://github.com/OmTheLast/Tokenizer-estimation-study

Research question: how accurately and cheaply can a browser estimate multilingual
token usage for a particular model, while limiting context overflows and unnecessary
history removal?

An estimator predicts a count; it does not replace the tokenizer that produces
model input IDs. Browser performance benefits are hypotheses to measure.

Read the [research protocol](docs/RESEARCH_PROTOCOL.md) for the questions,
evaluation rules, limitations and review gates. The specified
analysis of the frozen pilot is now complete; estimator weights remain unchanged.

## Current status

Start with the [readable study history and learning notes](docs/STUDY_HISTORY.md)
for what we did, what the results mean, and the next planned experiment.

**Phase 1 pilot completed (2026-10-15):** 100 aligned dev sentence IDs across
18 language varieties and five tokenizers produced 9,000 verified measurements.
Official dataset access succeeded. Median absolute prediction errors range from
3.28% to 11.11% across tokenizers, but worst underestimates range from 47.06% to
57.69%. These estimates are not reliable hard context-budget limits.
Read the [pilot report](results/2026-10-15-phase1-pilot/run-02/REPORT.md) and
[saved terminal output](results/2026-10-15-phase1-pilot/run-02/terminal-output.txt).
FLORES+ remains evaluation-only; weights were unchanged and devtest unaccessed.
Broader phase-1 coverage and browser testing remain unfinished.

**Error analysis completed (2026-10-15):** all 90 tokenizer-language cells and
360 fixed length-band cells were analyzed for both unchanged estimators.
LocalMind has lower median absolute error in 89/90 cells, but substantial
undercounts remain concentrated in specific tokenizer-language combinations.
See the [diagnostics](results/2026-10-15-pilot-diagnostics/run-02/REPORT.md).
The next step is review and a justified follow-up, not fitting on FLORES+.

**Controlled follow-up designed (2026-10-16):** compare newly fitted pooled
and separate Han/kana/Hangul coefficients on the same independent development
text. The [experiment design](docs/CJK_EXPERIMENT_V1.md) specifies controls,
data candidates, leakage checks and decision rules. Data preflight and immutable
split manifests are pending; no fitting or new test scoring has occurred.

### What the experiment compares

We varied **both the tokenizer and the language**. For each of 100 sentence IDs,
we selected its translations in 18 language varieties and measured every text
with all five tokenizer profiles: **100 × 18 × 5 = 9,000 comparisons**.
The models themselves were not run; their tokenizer assets produced the actual
content-token counts. The unchanged LocalMind formula supplied predictions.

| Tokenizer | Texts measured | Median absolute prediction error | Largest underestimate |
| --- | ---: | ---: | ---: |
| Qwen | 1,800 | 8.70% | 48.28% |
| Bonsai | 1,800 | 4.35% | 47.06% |
| LFM | 1,800 | 3.28% | 52.27% |
| Gemma | 1,800 | 11.11% | 48.72% |
| MiniCPM* | 1,800 | 3.49% | 57.69% |

*MiniCPM uses its first-party Hugging Face JSON tokenizer. Equivalence with the
GGUF/browser runtime has not been established.*

The median describes the middle absolute error, not a maximum error guarantee.
For example, MiniCPM predicted 11 tokens for one Cantonese sample whose actual
count was 26. Comparing token counts does not compare model intelligence.

Next: review errors by language and script, then choose broader phase-1 tests.
Code, JSON, webpages, complete chat formatting and browser performance still
need separate evaluation. FLORES+ will not be used for fitting or calibration.

**Phase 0 checks are now ready for review:** all 190 fresh JS/Python token-ID
sequences agree, and the Python estimator matches the original JS predictions.
We found and diagnosed 76 reference-count discrepancies: every LFM and MiniCPM
saved count includes one extra token relative to content-only encoding. Enabling
special tokens reproduces all 190 saved counts with our pinned setup. Historical
cause remains an inference because the original generator/version is unavailable.

Read the [phase-0 findings](docs/PHASE0_RESULTS.md) and
[reproduction instructions](docs/REPRODUCING_PHASE0.md). No new weights were fitted.

On 2026-10-04, the unchanged LocalMind fixture test at commit
`b39f0bc145a0c0926ba22247ee31cd369e0445b6` passed under Node v25.2.1:
38 samples across 5 tokenizer profiles, worst error -16% / +23%, versus -89%
worst error for the old heuristic. This reproduces the stored-fixture check;
independent regeneration was still pending at that point. The observed
2 ms timing is a single Node run, not a browser benchmark.

Output and provenance: `results/2026-10-04-localmind-baseline/`.

On 2026-10-07, fresh Qwen counts matched all 38 saved counts in both JavaScript
and Python; token-ID sequences also matched for all 38 samples. The unchanged
Qwen estimator's worst errors were -16.22% / +22.86%, with median absolute error
3.11%. These are existing fixtures, not held-out results. Historical tokenizer
revision provenance remains incomplete; our run pins its assets and libraries.

- [Generated Qwen report](results/2026-10-07-qwen-verification/run-01/REPORT.md)
- [Reproduction instructions](docs/REPRODUCING_QWEN.md)
- [Per-sample CSV](results/2026-10-07-qwen-verification/run-01/comparison.csv)

- Original supplied plan: `references/tokenizer-study-plan-v2.md`.
- Initial methodological review: `recovery/rounds/2026-09-30-01-review.json`.
- Recovery checkpoint: `recovery/CURRENT.json`.

## First milestone: reproduce the baseline

1. Resolve LocalMind commit `b39f0bc` to its full SHA. Record the source revision,
   applicable licence, environment and checksums. Keep fetched third-party source
   in the ignored `external/` directory.
2. Inspect its token-count implementation, fixture file and test script. Record
   what each fixture count represents and which tokenizer revision produced it.
3. Run its existing Node test and preserve the command, output and exit code.
   Distinguish the 38-fixture test from the reported 42-sample fitting corpus and
   held-out results. Report discrepancies rather than changing the target.
4. Port the estimator to Python. Compare every fixture estimate with JavaScript,
   including rounding and Unicode handling. JavaScript string length and Python
   string length use different units for some characters.
5. Obtain the exact tokenizer assets at recorded revisions where possible and
   independently regenerate content-token counts in JS and Python. A comparison
   with stored fixture numbers alone is not fresh tokenizer parity verification.
   Record unavailable revisions or gated assets as limitations.
6. Save a machine-generated per-fixture comparison and a short reproduction
   report. This milestone is complete when differences are absent or explained,
   with commands that someone else can rerun.

## Subsequent milestones

| Milestone | Output |
| --- | --- |
| Pilot ground truth | Counts for a small set of distinct tokenizer families across English, Indic, CJK, mixed scripts and code; pinned assets and data provenance |
| Browser feasibility | Exact worker counting, estimator and hybrid comparison; latency, memory, startup and worker communication costs |
| Wider evaluation | Frozen train/calibration/test splits, tokenizer-family holdouts, error tables and fully formatted chat-budget simulations |
| Reporting and packaging | Reproducible figures, limitations, paper draft and measured package size |

Review phases 0 and 1 before proceeding further, as requested in the supplied
plan. The full study is not assumed to fit a two-week pilot schedule.

## Working rules

- Preserve small, understandable commits and dated recovery logs. Every result
  must come from a saved script; keep failures alongside successes.
- Commit source, configuration, provenance and compact results. Keep credentials,
  caches, environments, model weights and large generated datasets out of Git.
- Use the existing configured Git identity; never invent authorship details.
- Om owns research decisions and interpretation. Record AI assistance honestly;
  AI-generated code or analysis should be reviewed and understood by Om.
- Split fitting, margin calibration and final testing. Never tune on final tests.
- Evaluate overflow frequency and severity, retained history, and runtime cost.
  Content-token accuracy alone does not establish safe chat budgeting.
- Use complete serialized prompts and reserve response tokens in downstream tests.
- Retain source-specific licences and attribution; a code licence does not
  automatically cover third-party text, tokenizer files or derived datasets.

AI assistance to date: Codex reviewed the supplied plan, inspected primary sources,
and prepared this repository scaffold and recovery logs. On 2026-10-04, Codex
executed the unchanged upstream fixture test and recorded its output and source
provenance. Follow-up discussion with Om covered the results and estimation
method. On 2026-10-06, Codex documented that discussion in the study history.
On 2026-10-07, Codex wrote and executed the Qwen verification scripts and recorded
the result. In a second round that day, Codex completed the other four profiles,
ported the estimator to Python, and diagnosed a special-token discrepancy in the
original references. On 2026-10-10, Codex prepared the multilingual pipeline;
on 2026-10-15 it ran and verified the FLORES+ pilot and prepared this progress
update at Om's request. Broader evaluation and browser tests remain unfinished.
