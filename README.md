# Comparative Tokenizer Study: Languages, Text Types, and Context Budgets

Study owner: Om. Repository: https://github.com/OmTheLast/Tokenizer-estimation-study

Research question: how do different tokenizers split text, how do token counts
vary across languages and text types, and what do these differences mean for
context use? Token-count estimation is one part of this broader study.

Om approved this direction on 2026-10-18. The repository URL remains unchanged
to preserve existing links; prior results retain their original scope and dates.

An estimator predicts a count; it does not replace the tokenizer that produces
model input IDs. Browser performance benefits are hypotheses to measure.

Read the [comparative study protocol](docs/COMPARATIVE_STUDY_V2.md) for the
current questions, comparison rules and limitations. The [earlier protocol](docs/RESEARCH_PROTOCOL.md)
preserves the estimation-focused history. No estimator weights have been fitted.

## Current status

Start with the [readable study history and learning notes](docs/STUDY_HISTORY.md)
for what we did, what the results mean, and the next planned experiment.
The [evidence guide](docs/EVIDENCE_GUIDE.md) explains our graphs and current progress.

**Published-text experiment completed and independently checked (2026-10-19):**
Six pinned tokenizer profiles measured 100 frozen source samples plus 40 paired
JSON variants: **840 measurements**, with complete Python/JS encoding agreement.
On these JSON files, indentation uses about 61% more tokens with Qwen and 56%
more with Gemma. XLM-R's near-constant count accompanies whitespace changes.
Relative counts vary markedly on mixed-script documentation. These are tokenizer
measurements, not model-quality scores or browser-performance results.

- [Plain-English results and three graphs](results/2026-10-19-published-experiment/REPORT.md)
- [Independent checks](results/2026-10-19-published-experiment/verification.json)
- [Frozen experiment plan](docs/PUBLISHED_TEXT_EXPERIMENT_V1.md)

**Published-text corpus collected and checked (2026-10-19):** 100 samples, 20 each
of English documentation, code, JSON, HTML and mixed-script documentation. All ten
source/language quotas are filled. Original-byte checks, strict JSON checks and
all 4,950 duplicate comparisons passed; offline replay reproduced the sample list
and decision log exactly. Codex reviewed the selected text and source notices.

- [Readable collection report and sample-length graph](results/2026-10-19-published-corpus/REPORT.md)
- [Final sample manifest](results/2026-10-19-published-corpus/collection-final/manifest.json)
- [Frozen corpus lock](config/published-text-corpus-v1.lock.json) and [verification](results/2026-10-19-published-corpus/validation.json)

The collection milestone preceded the completed measurements above. Raw source
text stays local; public metadata records how to reproduce it. Technical source
bias, automatic translations and shared templates remain limitations.

**Published-text sampling design completed (2026-10-18):** selected seven pinned
repositories and fixed selection rules for 100 target inputs: 20 each of English
documentation passages, code, JSON, HTML and mixed-script documentation. Microsoft
Hindi/Tamil passages are published automatic translations; the scope is technical
material, not a representative sample of the web. Read the [simple explanation
and sampling plan](docs/PUBLISHED_TEXT_SAMPLING_V1.md), [source lock](config/published-text-sources-v1.json)
and [metadata audit](results/2026-10-18-source-design/REPORT.md).
At that design milestone only metadata and root terms had been inspected.
Collection, file-specific checks and the bounded measurements are now completed above.

**Text-type comparison completed (2026-10-18):** five BPE profiles plus the
multilingual XLM-RoBERTa Unigram profile measured 180 original inputs across
prose, Python literal assignments, compact/pretty JSON and HTML, with English,
English+Hindi and English+Tamil conditions. Eight separate diagnostic probes
check normalization and unknown characters. The corpus and plan were committed
and pushed before encoding.

- [Text-type results and three graphs](results/2026-10-18-text-types/analysis-02/REPORT.md)
- [Readable token/reconstruction examples](results/2026-10-18-text-types/TOKEN_EXAMPLES.md)
- [Original public fixtures](data/fixtures/text-types-v1.json) and [study design](docs/TEXT_TYPES_V1.md)
- [Independent verification](results/2026-10-18-text-types/verification.json)

All 1,128 Python/JS token-ID sequence hashes agree, and a separate arithmetic
check verifies 738 summary groups. Pretty English JSON costs about 1.93× compact
JSON with Qwen and 1.96× with Gemma on these templates. XLM-R is near 1.00×, but
it removes decoded layout whitespace. Its relative count versus Qwen also changes
from 0.86× on English prose to 1.56× on compact JSON. These are geometric means
of 12 paired ratios, not universal rules or a BPE-versus-Unigram ranking.

This is a small authored fixture study, not sampled natural browser traffic.
No primary input produced unknown tokens; two XLM-R diagnostic probes did.
The source plan above specifies the next published-text follow-up. Broader
tokenizer representation remains future work. No fitting or browser trial has started.

**Comparative milestone completed (2026-10-18):** inspected the five pinned
tokenizer profiles and compared their actual counts on the existing pilot.
All five assets use **BPE**, with five distinct serialized processing pipelines;
this is not yet a comparison across algorithm classes or proven historical families.
Base vocabulary sizes range from 64,400 to 262,144 entries.

- [Tokenizer fact sheets and sources](results/2026-10-18-comparative-pilot/inventory-01/REPORT.md)
- [Direct comparisons and three new graphs](results/2026-10-18-comparative-pilot/run-01/REPORT.md)
- [Independent verification](results/2026-10-18-comparative-pilot/run-01/independent-validation.json)

On identical English texts, the geometric mean LFM/Gemma count ratio is 1.022;
on identical Tamil texts, it is 8.261. These are averages of per-text ratios,
not model-quality scores or ratios of total tokens. All 565 summaries, including
self-comparisons and aligned-language comparisons, are saved and independently
checked. No new text was tokenized, no fitting occurred, and devtest stayed untouched.

The controlled text-type expansion above now adds a Unigram profile. The CJK
coefficient-fitting design is deferred; its data-use question does not block
this descriptive study.

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
The broader comparative follow-up is now completed above; FLORES+ stays evaluation-only.

**Deferred estimation experiment, designed 2026-10-16:** compare newly fitted pooled
and separate Han/kana/Hangul coefficients on the same independent development
text. The [preserved v2 design](docs/CJK_EXPERIMENT_V2.md) specifies a bounded exploratory
comparison. The original v1 audit is preserved; missing article IDs are now a
stated limitation rather than an automatic stop. Source-use documentation and
approved cleaned split manifests remain pending. No fitting or new test scoring has occurred.

**Candidate-data audit completed (2026-10-16): not ready for fitting.**
We checked 20,940 sentences at pinned source revisions. The audit found duplicate
families across Korean splits, unverified original-document boundaries in all
three primary candidates, and source-text licensing caveats in GSD documentation.
Read the [data-check report](results/2026-10-16-cjk-preflight/audit-02/REPORT.md).
No weights were fitted or test predictions scored. If this deferred fitting experiment resumes, resolve the narrow source-text use
question and freeze cleaned splits under its v2 design. It is not the current priority.

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

Language/script error analysis and the first direct count comparisons are complete.
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
