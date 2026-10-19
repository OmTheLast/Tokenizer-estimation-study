# Study history and learning notes

For Om. Written with Codex assistance; last updated 2026-10-10.
This is our readable internal research record. The JSON files in `recovery/`
preserve execution details and restart instructions. Add dated entries here as
work progresses; preserve earlier findings and explicitly document corrections.

## Where we are now

We have checked **all 190 sample/profile combinations** using actual tokenizers
in JavaScript and Python, and ported the original estimator to Python. The real
tokenizer ID sequences agree across implementations in all 190 cases. The Python
port also matches the original estimates in every case. No weights were fitted.

We discovered that 76 LFM/MiniCPM saved reference counts are one token higher
than content-only counts. A special-token diagnostic explains the difference.
Read the [phase-0 findings](PHASE0_RESULTS.md) and
[reproduction instructions](REPRODUCING_PHASE0.md).

The [phase-1 pilot pipeline](PHASE1_PILOT.md) is now implemented and smoke-tested.
Its real dataset run is pending FLORES+ access: the configured account received
HTTP 403. No new multilingual results have been produced yet. Browser benchmarks
remain future work.

## What we are trying to find out

Can a small, fast estimator predict how many tokens a model will use, across
languages and text types, accurately enough to help manage browser chat history?

The initial character heuristic was `ceil(text.length / 3.5)`: roughly 3.5
characters per token, not 3.5 words. In JavaScript, `.length` measures UTF-16 code
units, which differ from Unicode code points for some characters.

A tokenizer converts text into token IDs. Its count is our reference for that
specific tokenizer revision and configuration. An estimator predicts only the
number of tokens. It does not produce those IDs or increase the context window.
Conventional token-based inference still needs the actual tokenizer.

LocalMind already has the tokenizer in a worker, according to the inspected
implementation. Its main-thread budgeting helper uses an estimate. Whether this
offers useful browser speed or memory savings must be measured against exact
counting through the existing worker.

## How the existing prediction was made

LocalMind's prior work collected sample text, measured counts with actual
tokenizers, and fitted weights to approximate those counts. Its estimator groups
characters into script/symbol classes and uses weights specific to a tokenizer
profile. It sums each class count multiplied by its weight and rounds up.

For illustration only, suppose the weights were 0.2 for Latin characters and 1.5
for Tamil characters. Text containing 100 Latin characters and 20 Tamil characters
would get this estimate:

```text
100 × 0.2 + 20 × 1.5 = 50 estimated tokens
```

If a real tokenizer returned 55 tokens, the signed relative error would be:

```text
error (%) = 100 × (estimated count − actual count) / actual count
          = 100 × (50 − 55) / 55
          ≈ −9.1%
```

These numbers are invented to explain the calculation; they are not experiment
results. Negative error means undercounting; positive error means overcounting.
Relative error needs separate handling when the actual count is zero.

## 2026-09-30 — Scope review and repository setup

Om supplied the [study plan](../references/tokenizer-study-plan-v2.md) and chose
[Tokenizer-estimation-study](https://github.com/OmTheLast/Tokenizer-estimation-study)
as the GitHub destination. Codex reviewed the plan and prepared the local project,
remote configuration, README, exclusions and recovery records.

The review recommended measuring exact worker counting as a baseline, holding out
tokenizer families, separating fitting/calibration/testing, and testing real chat
budgets including formatting and response allowance. These remain proposed study
design improvements, not experimentally demonstrated results.

The project is independent of the workspace's JEE and history-model projects.

## 2026-10-04 — Existing fixture test reproduced

Codex cloned LocalMind into the ignored `external/LocalMind/` directory and ran
the unchanged test at commit `b39f0bc145a0c0926ba22247ee31cd369e0445b6`, using Node
`v25.2.1`. The upstream checkout was clean before and after the run.

Exact saved terminal output:

```text
$ node scripts/test-token-count.mjs
LocalMind token counting: ok — 38 samples x 5 tokenizers, worst -16% (mixed-code-ta-b/gemma4-e2b) / +23% (mixed-hi-en-a/qwen35-4b), old guess worst -89%, 2 ms for 267880 chars

Exit code: 0
```

- [Full terminal output](../results/2026-10-04-localmind-baseline/terminal-output.txt)
- [Runtime, source hashes and limitations](../results/2026-10-04-localmind-baseline/run.json)

The test made 190 sample/profile comparisons and all assertions passed. The
displayed worst-case errors reproduce the reported rounded -16% / +23% baseline.
The old character heuristic's worst undercount was -89% on this fixture set.
These extrema can come from different samples; they are not paired measurements
of a single sentence. They are also not average errors.

An undercount can admit more history than the budget permits. An overcount can
discard history that would fit. An error of -16% remains relevant near a hard
context limit, even though it is much smaller than -89%.

### What this run does not establish

- The test reads saved reference counts. It did not execute real tokenizers.
- The fixture header says counts and weights were fitted together. Passing these
  fixtures does not establish accuracy on unseen text.
- The 2 ms measurement is one Node run, not a browser performance benchmark.
- The synthetic history test multiplies saved sentence counts rather than
  tokenizing the complete joined history, including its separators and template.
- The source contains references to a 42-sample fitting corpus, while this test
  uses 38 fixtures. Do not combine their results or the plan's held-out results.

## 2026-10-06 — Clarification and next experiment

Om asked whether we now use a real tokenizer to see how far the prediction is off.
**Yes: that is the next planned check.** It also verifies that the saved reference
counts used in the first test are reproducible.

For each sample, we will compare three values:

| Value | Where it comes from | Purpose |
| --- | --- | --- |
| Saved reference count | LocalMind's fixture file | The result we are trying to reproduce |
| Fresh reference count | Our run of the actual tokenizer | Independently regenerate the count |
| Existing estimate | LocalMind's unchanged estimator | Measure prediction error against the fresh count |

The procedure is to identify and pin the tokenizer assets and library version,
run the same text with special tokens excluded to match the fixture setup, and
save a row-by-row comparison. We need tokenizer assets, not model weights.
If the historical tokenizer revision is unavailable or unrecorded, document that
limitation rather than claiming an exact historical reproduction. Investigate
differences before attributing them to estimator quality or incorrect fixtures.

Keep the estimator's weights unchanged during verification. Start with Qwen and
then expand to the other profiles. The Python estimator port and JS/Python
tokenizer agreement checks also remain part of phase 0.

After reference verification, evaluate fixed estimates on text not used for
fitting. This is the generalization test. Use separate calibration data for safety
margins, and keep the final test data untouched by fitting decisions.

## 2026-10-07 — Fresh Qwen counts verified

Om authorized the next experiment. Codex identified the tokenizer repository from
LocalMind's Qwen model mapping, pinned and downloaded its tokenizer assets, wrote
the verification scripts, and ran the unchanged estimator alongside fresh JS and
Python tokenization. No weights were fitted or changed.

The tokenizer assets came from `onnx-community/Qwen3.5-4B-ONNX-OPT` at revision
`57b13b4dce7be073be0df3eaf1c842a6bbb2e0a7`. We used JS library version 0.2.0 and
Python tokenizers 0.23.2. Files, versions, checksums and outputs are recorded in
the [run metadata](../results/2026-10-07-qwen-verification/run-01/run.json).

All **38 saved counts = 38 fresh JS counts = 38 fresh Python counts**. Both
implementations also produced exactly the same token IDs for every sample.
That provides stronger evidence than count agreement alone.

The unchanged estimator was still approximate:

| Sample | Actual tokens | Estimated tokens | Signed error |
| --- | ---: | ---: | ---: |
| English prose `en-prose-a` | 84 | 84 | 0.00% |
| Marathi `mr-a` | 111 | 93 | -16.22% |
| Mixed Hindi-English `mixed-hi-en-a` | 35 | 43 | +22.86% |

Across these 38 Qwen examples, the median absolute error was **3.11%**. There
were 13 undercounts, 7 exact predictions and 18 overcounts; 37/38 estimates were
within +/-20%. The Marathi and mixed Hindi-English rows show Qwen's worst under-
and overestimates. These are Qwen-only figures, not results for all five profiles.

This answers our immediate question: the saved Qwen reference counts are
reproducible with the pinned tokenizer setup, and prediction errors remain after
checking against fresh actual counts. It does not establish accuracy on new text.

Historical provenance remains limited: the original fixture file does not name
its exact tokenizer revision or library version. The pinned HF revision predates
the original measurement, but matching counts do not prove that the exact same
files were originally used. We keep that caveat alongside the successful result.

During setup, system Python's metadata download hit a local certificate-validation
error. A retry with curl and normal TLS verification succeeded. This did not
affect the tokenizer comparison. All new outputs are local and have not been
committed or pushed. Scripts and result tables were produced with Codex assistance.

## 2026-10-07 — Remaining profiles, Python port and reference correction

Om authorized the remaining four profiles and estimator port. All sources were
accessible anonymously. We pinned tokenizer assets, reused the locked libraries,
and left the original fixtures and weights untouched. MiniCPM uses the parent
first-party HF JSON tokenizer; this does not verify its deployed GGUF runtime.

The content-only run completed all 190 comparisons. Both fresh tokenizer
implementations agreed on every complete ID sequence, but only 114 saved counts
matched content-only encoding. The other 76, all LFM/MiniCPM samples, were exactly
one token higher. The run correctly exited 2 and remains preserved as a failed
saved-reference contract check.

We investigated rather than adjusting the data to pass. Special-enabled encoding
adds exactly `<|startoftext|>` (ID 1) for LFM or `<s>` (ID 0) for MiniCPM, with all
remaining IDs unchanged. All 190 saved counts match special-enabled encoding.
For the other three profiles, enabling special tokens adds nothing in the tested
JSON tokenizer setup. This statement does not cover their full chat templates.

The fixture header spells the option `addSpecialTokens: false`, while our installed
JS library expects `add_special_tokens: false`. The diagnostic showed that the
camelCase spelling behaves like the default and leaves specials enabled. That is
a demonstrated mechanism consistent with the old data, not proof of the original
author's exact call: the generator and historical library version are unavailable.

**Correction to our earlier assumption:** the original saved counts cannot all
be described as content-only. The first Qwen result remains valid; the discrepancy
was invisible there because its tested JSON tokenizer adds no special prefix.
Future ground-truth tables will use explicit content-only counts and track special
tokens separately. We did not silently subtract one from or overwrite old fixtures.

The Python estimator port matches all 190 main comparisons. Additional checks
covered 380 fixture/alias combinations, 1,230 edge combinations and 109 character
class boundaries with zero mismatches, including null/empty inputs, emoji,
combining marks, unknown-model fallback and surrogate handling. We preserved the
original addition order and rounding, rather than changing the fitted method.

The [generated phase-0 review](PHASE0_RESULTS.md) contains per-profile prediction
errors, evidence links, limits and next steps. Phase 0 is ready for review with
the reference discrepancy documented. Next is phase 1's multilingual ground-truth
table and frozen data splits; new estimator fitting and held-out evaluation follow
later. No model training, commit or push occurred in this round.

## 2026-10-10 — Multilingual pilot prepared; dataset access pending

Om asked to start observing tokenizer behavior on broader text. We chose a pilot
of 100 aligned dev sentence IDs across 18 language varieties and the existing
five tokenizers (9,000 intended measurement rows). The same sentence IDs across
translations help control differences in subject matter. IDs will be selected
with a fixed hash rule before observing token counts, then frozen locally.

The official FLORES+ repository is gated. An existing local Hugging Face credential
was available, but an authorized download attempt for its English dev file at
revision `e707e62e762a9e2faca3933aa315f4665cc3cd8f` returned HTTP 403. We asked Om
to review/accept the access conditions with that account. No raw FLORES+ text
was obtained and no mirror bypass was attempted. Credential values were neither
printed nor saved to project logs.

We also corrected a proposed use in the original study plan: the current FLORES+
card specifies evaluation use and says not to use it for training. This pilot
will assess the frozen estimator, not fit or calibrate weights on FLORES+.
Future fitting needs a separate source of text. The final devtest split remains
unaccessed; raw evaluation text and token IDs will not be included in published
project artifacts.

While access was pending, Codex implemented a pinned download and sampling path,
a measurement pipeline, Parquet output, special-token accounting, Unicode and
pre-tokenizer diagnostics, Indian/CJK/other group summaries, a heat map and
largest-gap report. Completed per-model output shards can be resumed only when
checksums and source/configuration/code fingerprints agree.

Infrastructure validation used the **old LocalMind fixtures only**: all 190 fresh
counts and unchanged estimates matched phase 0; class totals and Parquet round-trip
checks passed. A second invocation successfully reused the five saved shards.
Three separate input tests passed, covering Unicode measurement, parallel ID
selection and frozen-input protection, and sanitized access-error messages.
The smoke figure was visually inspected and is labelled as a smoke test.

These checks add no new generalization evidence. The real data loader, full
18-language figure and empirical results still require an authorized FLORES+
download. See [the pilot notes and exact commands](PHASE1_PILOT.md) and the
[smoke validation record](../results/2026-10-10-phase1-smoke/run-01/validation.json).
No weights were fitted and no commit, push or model training occurred.

## 2026-10-15 — FLORES+ conditions remembered

Om shared the access form and asked whether to agree and to remember its terms.
The two commitments are no re-hosting where web crawlers can collect FLORES+,
and keeping evaluation contents out of training data. Acceptance also shares
the account email and username with the authors. Our evaluation-only plan
excludes FLORES+ from training, fitting and calibration and keeps raw text and
reconstructable token sequences out of public artifacts. Full upstream
training/fitting provenance remains unknown; absence of prior exposure is not
verified. The exact displayed conditions are saved in [the pilot notes](PHASE1_PILOT.md)
and handling rules are included in project instructions.

Access acceptance remains unconfirmed. This round changed documentation only;
no terms were accepted, data downloaded, measurements run, training started,
commits made or files pushed.

## 2026-10-15 — First real multilingual pilot completed

Om asked to start after discussing the LocalMind character-weight formula.
Run-01 could not resolve Hugging Face from the restricted network environment.
Run-02 used authorized network access; official authenticated downloads succeeded
for all 18 dev files. The script froze the file hashes and 100 shared sentence
IDs before measuring. It completed 9,000 rows with exit code 0.

The unchanged estimator's median absolute errors were Qwen 8.70%, Bonsai 4.35%,
LFM 3.28%, Gemma 11.11%, and MiniCPM 3.49%. Small median errors conceal large
individual misses: worst underestimates range from 47.06% to 57.69%. For example,
MiniCPM's estimator predicted 11 tokens for Cantonese dev ID 843, but the real
HF JSON tokenizer produced 26 content tokens (57.69% under). No source text is
reproduced here. MiniCPM's GGUF/browser runtime equivalence is still unverified.

CJK group median absolute errors range from 18.18% to 25.00%, versus 0.75% to
8.76% for the ten-language Indian group. These are descriptive results for this
sample, not proof of the cause or universal language-level guarantees. The pilot
supports investigating errors by language and script before relying on estimates
for context budgeting. It does not establish model quality or browser performance.

Validation confirmed 9,000 unique rows, 1,800 texts, zero exact overlaps with the
38 published fixtures, unchanged weights, matching character-class totals and
Parquet round-trip fidelity. Independent checks verified all source/configuration
hashes, five shard checksums and every prediction-error calculation. The figure
was visually inspected. Full upstream fitting/training overlap remains unknown.

Read the [pilot report](../results/2026-10-15-phase1-pilot/run-02/REPORT.md) and
[actual terminal output](../results/2026-10-15-phase1-pilot/run-02/terminal-output.txt).
No fitting, model inference, devtest access, commit or push occurred. Next: review
these findings together before choosing the next phase-1 extension.

## 2026-10-15 — GitHub progress published

Om asked whether the experiment varied models or languages and requested a
GitHub progress update. It varied both tokenizer profiles and language varieties:
100 aligned IDs × 18 language varieties × 5 tokenizers = 9,000 comparisons.
No model inference was performed. The README now explains this design, shows
the per-tokenizer results and identifies remaining work.

The destination repository had no remote branches when checked. This is the
first publication of the local study source, documentation and compact results.
Raw FLORES+ files, numeric Parquet tables, environments, downloaded tokenizer
assets and third-party checkouts remain excluded. Study commit `e1da27de4fbcefe25a3e426d03a80279c3b86450` was pushed to `main`, and
GitHub returned the same SHA during verification. Source, documentation and compact
results are now on GitHub; excluded local data and caches are not backed up there.

## 2026-10-15 — Research protocol and next-analysis specification

Om asked to approach the work methodically as research. Codex recorded
[protocol v1](RESEARCH_PROTOCOL.md), separating descriptive tokenizer differences,
estimator accuracy, asset-derived estimation and browser budgeting/performance.
The document preserves the original research questions but supersedes the
proposal's FLORES dev-fitting suggestion with evaluation-only usage.

This protocol was written after the pilot summaries were inspected. It is not a
preregistration of those results. The pilot has 9,000 repeated measurements from
100 aligned sentence IDs; it does not have 9,000 independent examples. Maximum
observed errors are not universal bounds, and tokenizer counts do not measure
model intelligence. No novelty claim is established; literature review remains.

The [next-analysis specification](../config/pilot-diagnostics-v1.json) pins the
existing Parquet hash, all 90 tokenizer-language cells, paired baseline metrics,
fixed length bands and deterministic outlier selection. It requires reporting
both percentage errors and token shortfalls, including failures. This detailed
analysis has not yet been run. No new measurements, data downloads or fitting
occurred in this round. Product acceptance thresholds and independent final-test
design remain future decisions, before the relevant experiments.

## 2026-10-15 — Prespecified pilot diagnostics completed

Om approved the structured error analysis. The analysis used only the frozen
9,000-row Parquet and both saved prediction columns. It computed all 90
language/tokenizer cells, five tokenizer summaries, 15 group summaries, and
360 fixed length-band cells (70 empty). Empty cells have null metrics.
No fitting, new measurements, data downloads, devtest access or model inference
occurred. All original weights and the input Parquet hash remain unchanged.

LocalMind has lower median absolute error in 89/90 cells. The exception is
MiniCPM/Russian; better typical error does not imply every error metric improves.
The language-specific undercount patterns include:

- lfm2-1.2b, kor_Hang: 99/100 texts underestimated by more than 20%.
- minicpm5-2b-gguf, kor_Hang: 11/100 texts underestimated by more than 20%.
- minicpm5-2b-gguf, yue_Hant: 99/100 texts underestimated by more than 20%.

These are exploratory observations from 100 aligned IDs, not population
probabilities or independent samples across all 9,000 rows. The report includes
both percentage and absolute token shortfalls, both estimators, all cells,
script composition and fixed length bands. Shared CJK weighting remains a
candidate explanation, not an established cause. Browser overflow was not tested.

Four hand-calculated unit tests cover strict threshold boundaries, quantiles,
empty cells, band edges, deterministic outliers and paired differences. An
independent verifier using Python arithmetic/sorting checked every metric and
paired difference in all 470 groups, all 20 outlier rankings using exact rational
ordering, and all 90 script composition summaries. No significance tests or
uncertainty intervals were computed.

Run-01 is preserved. Run-02 adds readable length-band and composition tables;
the numeric diagnostics are byte-identical between runs. The frozen plan's
broad wording about signed-error differences is clarified in the report:
more-negative signed error means more underestimation, not generic improvement.

Read the [diagnostic report](../results/2026-10-15-pilot-diagnostics/run-02/REPORT.md)
and [all length bands](../results/2026-10-15-pilot-diagnostics/run-02/LENGTH_REPORT.md).
Commands: `.venv/bin/python scripts/analyze_pilot_errors.py --output results/diagnostics-new`
and `.venv/bin/python scripts/verify_pilot_diagnostics.py --output results/diagnostics-new`.

Next: review these findings and the remaining phase-0 limits with Om before
selecting a bounded phase-1 extension or controlled follow-up. New protocol and
diagnostics are saved locally; the earlier pilot publication remains on GitHub.

## 2026-10-16 — Standing Git milestone policy and next research decision

Om requested that meaningful progress be committed and pushed without repeated
reminders. This preference is saved in workspace memory and this project's
instructions. The completed research protocol, diagnostic specification, analysis
scripts/tests and numeric reports were published as the next milestone.
Restricted raw data and ignored caches stay local; only pushed files are
preserved remotely. The remote branch was verified at commit `bf281f1796507316949e0d5f46cecc84c819bf9c`.

The proposed next step is to specify a controlled follow-up for the shared CJK
weight, using separate, licensed development and evaluation texts. Compare a
single CJK coefficient with Han/kana/Hangul coefficients while keeping other
features, samples, objective and fitting procedure fixed. Any fitted coefficients
must come from separate development data, never FLORES+. Freeze the hypothesis,
splits, baselines and success criteria before fitting. Test on an untouched
split and report changes in absolute error, undercount severity and overcounting.
This is a proposed experiment, not a result or an authorized fitting run. It may
show the shared class is insufficient, or that splitting it adds little benefit.
Review the existing phase-0/phase-1 evidence and select that bounded design with
Om before executing later-stage fitting.

## 2026-10-16 — Controlled CJK experiment design recorded

Om approved writing the next experiment's design, explicitly before fitting.
The [design](CJK_EXPERIMENT_V1.md) and [versioned configuration](../config/cjk-experiment-v1.json)
compare a refitted shared coefficient with three refitted script coefficients
on identical development data. The old frozen formula and simple heuristic are
additional baselines. Non-CJK weights, Unicode coverage, rounding and tokenizer
assets stay fixed. The split is exactly Han/kana/Hangul within the old CJK class;
it does not introduce Cantonese-specific weights or move punctuation/Jamo out
of other. Splitting may therefore leave important errors unresolved.

Official Universal Dependencies documentation was checked for Chinese GSD,
Japanese GSD, Korean GSD, Chinese GSDSimp and Cantonese HK. Candidate roles and
source links are saved; all five pages list CC BY-SA 4.0. No dataset files were
downloaded, licences at pinned revisions audited, or corpus counts promised.
Traditional/simplified Chinese versions share source material and must remain
aligned across splits. Cantonese is secondary transfer evaluation, not fitting.

The plan sets an equal-language nonnegative relative least-squares objective,
paired group-bootstrap analysis, a primary error metric and prospective practical
and tradeoff flags. These study criteria are not browser safety thresholds.
Preflight must establish licensed snapshots, document groups, deduplication,
feasible train/test sizes and script coverage. Failed requirements trigger a
dated design amendment, not an ad-hoc relaxation after scoring.

This round made no new empirical findings and fitted no coefficients. The next
milestone is data preflight and frozen manifests, followed by review and explicit
fit authorization. The design was pushed under Om's standing milestone policy; commit
`76e93dbe774ab3619913deb1f39045461737d079` was verified on GitHub main.

## 2026-10-16 — Plain-language teaching preference

Om requested high-school English and gradual vocabulary-building throughout
the study. This is saved in workspace memory and project instructions. Future
explanations should start with purpose and a small example, introducing only
one or two new terms at a time. Distinguish measured findings from proposed
explanations; preserve technical details in the research documents.

The current experiment can be explained as comparing one shared multiplier
with three separate multipliers, using the same practice texts and then new
exam texts. A multiplier is a weight; choosing it from practice examples is
fitting. Updating the shared multiplier is also necessary for a fair comparison,
so improvement cannot be attributed merely to newer practice data. The data
checks and fitting have not started. No research result or experiment scope
changed during this teaching-preference round.

## 2026-10-16 — Practice/exam data audit completed; candidates not approved

Om authorized checking the practice and exam texts and asked for explanations
along the way. Codex pinned five official UD repositories by commit and fetched
21 files, including README/licence files and the requested splits. Raw data stay
in ignored `.cache/cjk_ud/`. Original # text fields were used; test text was read
only by preparation checks, without showing examples or computing token counts,
predictions or errors. No weights were fitted.

The audit parsed 20,940 sentences with no
missing text fields. It checked normalized exact matches and the specified
character-5-gram near-duplicate rule against candidate data, all cached FLORES+
dev text and the 38 original fixtures. It found no external overlap under these
rules; that does not prove all possible semantic overlap is absent.

In Korean, the priority rule flags 133 practice rows and 30 development rows
because matching families occur in a later split. Further within-split copies
are recorded separately. The 500 simplified Chinese test sentences align with
the 500 traditional Chinese test IDs, so conversion families are kept together.
Script feature coverage and rank pass the stated checks on provisionally eligible
practice rows; eligibility is not an approval to fit.

The primary candidates fail the document-provenance requirement: Chinese and
Korean lack original-document IDs, and Japanese newdoc IDs repeat sentence IDs.
They cannot establish separation of articles or satisfy the verified-source-group
floor. Cantonese has four source ranges documented in its README and remains
secondary-only. We did not pretend that duplicate components were source articles.

A second issue emerged in the pinned GSD READMEs: the CC BY-SA annotation label
is distinguished from the underlying text, over which Google disclaims ownership.
Our earlier metadata-level selection did not resolve this. The experiment's
clear text-provenance/licensing requirement is therefore not cleared. This is
a source-audit limitation, not a conclusion that all research use is prohibited.

Four tests check original-text extraction, document metadata handling, duplicate
rules and group construction. An independent verifier checked all 20,940 row
hashes/counts, all 21 file hashes, 742 reported duplicate/parallel edges, and
known-group split dispositions. It does not independently prove exhaustive
near-match discovery or recover undocumented article relationships. Audit-01 is
preserved; audit-02 has identical findings and a reusable output-path command.

See the [report](../results/2026-10-16-cjk-preflight/audit-02/REPORT.md),
[source locks](../results/2026-10-16-cjk-preflight/acquisition/sources.json), and
[verification](../results/2026-10-16-cjk-preflight/audit-02/independent-validation.json).
The row-level provisional manifests are local-only and explicitly not approved
training/test manifests. The frozen experiment design was not weakened to pass.
Next: recover source mappings and clarify text provenance or choose replacements,
then record an amendment before fitting. This completed audit is a research
milestone, including its negative outcome, and was published under the
standing Git policy. Commit `025f616d001a4188dcf19b1b26154eb3d12f27f4` was verified on GitHub main.

## Current completion checklist

- [x] Preserve the supplied plan and review notes.
- [x] Set up the local repository and GitHub remote.
- [x] Run the unchanged LocalMind fixture test and save its output.
- [x] Explain the result, estimation method and evidence limits with Om.
- [x] Save this readable history.
- [x] Pin Qwen tokenizer assets and document historical provenance uncertainty.
- [x] Compare 38 fresh Qwen counts with saved counts and estimates; check JS/Python token IDs.
- [x] Verify the remaining four profiles; preserve and explain the special-token discrepancy.
- [x] Port the estimator to Python and establish JS/Python agreement.
- [x] Prepare a pinned phase-1 pilot design and smoke-test the measurement pipeline.
- [x] Obtain authorized FLORES+ dataset access and run the actual multilingual pilot.
- [ ] Test unseen text and benchmark browser alternatives.

Earlier setup and experiment rounds were saved locally without commits or
pushes. The 2026-10-15 publication round records the first GitHub update;
ignored local caches and data are not included in that publication.

## 2026-10-16 — Focus the experiment and make its evidence visible

Om asked us to avoid unnecessary detours and treat the project as a research
study with graphs and a clear progress record. We recorded a versioned v2
amendment before candidate token counts, fitting or exam-error scoring. Missing
article IDs become a limitation for this bounded sentence-level comparison;
we keep duplicate/known-family separation and avoid independence or significance
claims. Source-text use documentation and a cleaned v2 manifest remain pending.
The earlier v1 design and audit are preserved as historical records.

Added three scientific figures from the already verified pilot: typical/large
errors for both existing methods, undercount frequency for all tokenizer-language
cells, and predicted-versus-actual count plots. Recomputed 20 summary values and
180 heatmap values against the saved diagnostics; plotted all 9,000 pairs. These
are new presentations of existing evidence, not new fitting results. Run-01 was
retained; run-02 fixes caption spacing and a title with identical numeric data.
All three final PNGs were visually inspected. PNG/SVG/PDF exports, numeric plot
data, script snapshots and checksums are saved.

The new [evidence guide](EVIDENCE_GUIDE.md) explains each graph in plain language
and records progress without inventing a completion percentage. Next: complete
the narrow source-use check, then prepare the cleaned v2 split manifest. No
training, candidate scoring, FLORES+ devtest access or browser trial occurred.

Publication: milestone `457bfec3b9891dbb141ff81c0ebb4616441f7281` was pushed
and verified on GitHub main. Raw data and ignored local artifacts remain excluded.

## 2026-10-17 — Proposed broader tokenizer-behavior study

Om clarified an interest in observing how tokenization changes across tokenizers,
families and circumstances, with comparative graphs. The written umbrella goal
currently emphasizes browser token-count estimation; it is narrower than this
proposed direction. Prior results remain useful descriptive pilot evidence.

Proposed working title: **Comparative Tokenizer Study: Languages, Text Types,
and Context Budgets**. Proposed main question: how do tokenizer choices affect
text splitting, token counts and context use across languages and text types?
Estimation accuracy becomes one sub-question. Browser runtime remains a later
measured application; model answer quality is outside this current scope.
This is a proposal for discussion, not an approved new protocol or a claim that
the original study was designed this way. The GitHub repository was not renamed.

Proposed order:
1. Inventory the five pinned tokenizer assets: revision, algorithm, vocabulary
   size, normalization/pre-tokenization, special-token settings and asset
   identity/lineage where verifiable. Distinguish model names, tokenizer families
   and language families; do not infer family membership from branding alone.
2. Specify a small descriptive comparison using existing pilot counts: paired
   counts on identical text within each language and aligned translations for
   cross-language comparisons. Plot language-by-tokenizer patterns and pairwise
   count ratios with distributions, denominators and clear ratio direction.
   Translation comparisons preserve approximate meaning, not identical text
   length; character/byte ratios answer different questions and need labels.
3. Add a bounded set of text types (prose, code, JSON/HTML, mixed-language text)
   only after specifying sampling and metrics. Use shareable examples for visible
   token-boundary illustrations; do not expose restricted FLORES+ text.
4. Compare existing estimator errors and later measure browser runtime and
   serialized context budgets as separate outcomes.

Keep early claims about the tokenizer versions actually measured. A family-wide
claim needs justified family definitions and adequate representatives; one
example per family cannot establish a universal pattern. Token-count differences
do not establish model intelligence or prove which tokenizer design feature
caused the difference. Choose questions before graphs, retain unfavorable results,
and avoid expanding every possible combination at once.

Recommendation: prioritize the inventory and comparison specification before
the proposed CJK coefficient-fitting experiment. That experiment remains saved
and unstarted; it need not drive a descriptive study. Its source-use issue is
not a blocker to analyzing already-authorized pilot measurements. No new data,
fitting, scoring or graph generation occurred in this discussion.

## 2026-10-18 — Comparative scope adopted; inventory and direct comparisons completed

Om approved the proposed broader study and asked that the work be preserved on
GitHub. The public title is now **Comparative Tokenizer Study: Languages, Text
Types, and Context Budgets**. The existing repository URL is unchanged. The new
[comparative protocol](COMPARATIVE_STUDY_V2.md) records this amendment and makes
estimation a sub-question. The CJK fitting design is deferred and remains unstarted.
Prior protocols, outputs and limitations remain available.

Before this new analysis ran, we wrote `config/comparative-pilot-v1.json`, defining
pairing, ratios, summaries and figures. This is exploratory analysis of already
inspected pilot data, not a prospective preregistration or an independent new test.

The inventory verified 11 cached asset files against five existing locks. All
five tokenizer JSON models report BPE. Base vocabulary sizes are Qwen 248,044,
Bonsai 151,643, LFM 64,400, Gemma 262,144 and MiniCPM 130,072. All five serialized
pipeline fingerprints differ. We recorded processing stages, special-token
settings, component hashes and source revisions. These are five configurations,
not five established lineages, and the sample has no cross-algorithm coverage.
Runtime vocabulary counts agree with independently counted base/added unions.

Using the existing 9,000 content-token counts, we verified same-text pairing,
frozen sentence selection, complete model/language coverage and source revisions.
We computed 475 ordered-tokenizer-pair summaries (including self-comparisons and
pooled results) and 90 aligned-language/English summaries. Three scientific figures
show pooled pairwise ratios, language-specific ratios/spreads against Qwen, and
aligned translations relative to English. All have PNG/SVG/PDF exports.

A separate verifier using Python math and rational-number quantiles checked all
5,650 summary values, all 9,000 published counts and the inventory. The three
PNGs were inspected visually. Scripts, numeric count data, source snapshots,
version records and checksums are saved. No restricted text or token sequences
are published. No new text encoding, model run, coefficient fitting, devtest
access or browser trial occurred.

For example, LFM/Gemma geometric mean per-text ratios are 1.022 on English,
8.261 on Tamil and 1.220 on Korean (100 texts each). These descriptive ratios
show that the difference varies across language samples; they do not establish
a cause or model-quality ranking. The geometric mean differs from earlier
ratios of total token counts. English and Qwen are fixed references, not quality
standards. Percentile lines show sample spread, not confidence intervals.

Read the [inventory](../results/2026-10-18-comparative-pilot/inventory-01/REPORT.md),
[comparison report](../results/2026-10-18-comparative-pilot/run-01/REPORT.md), and
[evidence guide](EVIDENCE_GUIDE.md). Next: specify a small text-type expansion and
additional algorithm-class coverage, with sampling and metrics fixed before
collection. The deferred fitting-data permission question does not block this work.

Publication: commit `8722dc3e2ba5d9eaf82274cec97be7df8b9d51e8` was pushed and
verified on GitHub main. Code, permitted numeric evidence, figures and research
records are included; ignored local inputs are not off-device backups.

## 2026-10-18 — Text types and a Unigram profile measured

Om authorized the next text-type/non-BPE comparison, requested explanations as
work progressed and asked for GitHub publication. We specified a controlled
synthetic study before encoding: 12 original record scenarios × three message
conditions (English, English+Hindi, English+Tamil) × five representations
(prose, Python literal assignment, compact JSON, pretty JSON, HTML). Eight
separate probes cover whitespace, accents, emoji and rare characters. These
are Codex-authored examples with shared templates and unvalidated translations,
not natural-workload sampling. Original fixtures are public; no FLORES data used.

Selected FacebookAI/xlm-roberta-base at
`e73636d4f797dec63c3081bb6ed5c7b0bb3f2089` before measurements. Its legacy JSON
omits model.type; the first inspection raised KeyError. The pinned runtime
loads it as Unigram with 250,002 base vocabulary entries. Original asset bytes
were preserved. A hashed runtime serialization supplies explicit fields; all
188 original-versus-serialized Python ID sequences agree. The JS implementation
also successfully loaded the original source, so no conversion was needed there.
No model weights were downloaded. Sources, asset hashes and selection rationale
are recorded in the new lock. A single encoder-model tokenizer is a descriptive
reference, not a controlled BPE-versus-Unigram experiment or chat-model comparison.

Plan, corpus, renderer and source lock were committed and pushed as
`d88eda415da60fbaaf198e5cb3a47e4af8ad4423` before workload encoding; its remote SHA
was verified. Six profiles produced 1,080 primary rows and 48 diagnostic rows.
Per-profile outputs were saved incrementally. Python/JS ID-sequence hashes agree
on all 1,128 inputs. Independent verification recomputed row metadata/special
counts and all 6,552 numeric summary values in 738 groups; all 14 source asset
files passed their pinned hashes.

The first plotting run failed on a Matplotlib keyword-argument requirement. Its
script, error and numeric summaries are preserved in analysis-01. Analysis-02
has identical numbers and the completed three figures in PNG/SVG/PDF; all PNGs
were visually inspected. The verifier was subsequently made reproducible without
requiring a failed attempt in a fresh run; the first successful audit and its
source remain preserved, and the final verifier was rerun.

Observed geometric mean pretty/compact English JSON ratios: Qwen 1.928, Gemma
1.962, XLM-R 1.003. XLM-R's relative count versus Qwen is about 0.86 on English
prose but 1.56 on compact JSON. Its decoded strings differ for all 144 primary
non-compact-JSON inputs (mostly layout whitespace), while all 36 compact JSON
inputs match exactly. All five BPE profiles reconstruct every primary input
exactly. No primary inputs produced unknown IDs; XLM-R produced unknown IDs
on two diagnostic probes. Some BPE profiles normalize the decomposed-accent
probe. These observations are sample-specific and do not establish universal
losslessness, semantic damage, model intelligence or algorithm superiority.

See [text-type results](../results/2026-10-18-text-types/analysis-02/REPORT.md),
[readable token examples](../results/2026-10-18-text-types/TOKEN_EXAMPLES.md), and
[verification](../results/2026-10-18-text-types/verification.json). Next: specify
varied natural workloads and additional tokenizer representatives before broader
claims. No fitting, model inference, browser trial or FLORES+ devtest access occurred.

Publication: results commit `fb7aeb7871965cabb080a7f9c547f0985f811ebe` was
pushed and verified on GitHub main. Original fixtures, permitted results,
figures, scripts and logs are included; downloaded tokenizer assets stay local.

## 2026-10-18 — Published-text sources and sampling rules fixed

Om requested source selection and sampling rules, simple explanations during work,
and GitHub publication. This round completes the design, not the collection or
tokenizer experiment. Seven repositories are pinned for 100 target original inputs:
20 each of English documentation, code, JSON package files, HTML examples and
Hindi/Tamil–English documentation. The same six existing profiles will be used.

Sources are CPython, Node.js, npm CLI, VS Code, MDN dom-examples, MDN learning-area
and Microsoft ML for Beginners. The latter publishes automatic translations; we
explicitly label this and do not call them human conversation. Learn X in Y Minutes
was considered but had only four Hindi and four Tamil documents at the inspected
revision. MDN's two repositories share one publisher. The study therefore samples
technical materials, not a representative cross-section of all browser content.

The metadata-only audit contains 2,129 path candidates, with no claim of content
eligibility. Source/license hashes and commit-to-tree links were checked. A fixed
hash order, source/language quotas, one sample per file, duplicate filtering and
one language per translated lesson prevent discretionary selection based on token
counts. Original formatting is preserved. The next collection step must record
paragraph byte boundaries, eligibility reviews, file terms and shortfalls before
encoding. Whole files and passages have different length limits; categories are
not treated as matched representations of identical content. JSON compact/pretty
variants supply the separate controlled formatting comparison.

An initial Python HTTPS attempt failed certificate verification. We used curl
with TLS verification enabled instead. The first commit-addressed tree response
reported the requested commit SHA rather than the actual tree SHA; a consistency
assertion caught this. We fetched all inventories again by their actual tree SHAs
and verified them against commit metadata. No failed evidence was accepted.

See the [plain-language plan](PUBLISHED_TEXT_SAMPLING_V1.md) and
[source audit](../results/2026-10-18-source-design/REPORT.md). There are no new token
counts or result graphs in this round. Next: implement collection and review,
freeze the selected sample manifest, then measure. No fitting, inference, browser
trial, model-weight download or FLORES+ devtest access occurred. Codex prepared
the plan, metadata script and documentation; Om remains the study owner.

Publication: source-design commit `f96e07509d91d6669b49fb91cb7d04e20be9f344` was pushed and
verified on GitHub main. Included files preserve the design, inventory and checks;
ignored caches are not backed up by this push.

## 2026-10-19 — Published samples collected, reviewed and frozen

Om authorized collection and checks under the saved sampling rules and requested
simple progress explanations and a GitHub push. We now have 100 original inputs:
20 English documentation paragraphs, 20 code files, 20 JSON manifests, 20 HTML
examples and 20 Hindi/Tamil–English passages. Each of ten strata contributed ten.
There are 100 distinct files and 20 distinct translated lesson families.

The collector preserves exact UTF-8 bytes, verifies Git blob identities and stores
raw files locally. Its maximal-paragraph extractor tracks code fences and RST
blocks; conservative implementation refinements are recorded separately without
rewriting the earlier protocol. A six-test boundary check passed before downloads;
the final eight-test check adds URL-screening coverage. No selected source program
was executed. No tokenizer was loaded or run.

Provisional collection was followed by saved Codex review labels. Review removed
an image-caption block, translation disclaimers, URL-only English-letter matches,
proper-name-only passages, and an actual unit test under an idle_test directory.
Generated encoding files were excluded automatically. Replacements followed the
original hash order and within-source quotas. Earlier provisional outputs remain
as history; they are not the frozen sample set. The final selector encountered
129 paths and wrote 775 file/paragraph decisions, including 100 selections.

The selected npm workspace manifests use their nearer ISC licenses, not just the
repository root Artistic-2.0 license. Twenty-one distinct source-notice files were
recorded and hashed. Codex inspected source headers and selected text; this is
AI-assisted review, not human approval or a translation-quality certification.
Raw source/notice text stays ignored and local; public artifacts contain hashes,
paths, byte boundaries, decisions and reproduction scripts.

Independent calculations verified bytes, paragraph boundaries, JSON, lengths,
script thresholds, notices and all 4,950 sample pairs. The greatest character
5-gram similarity was 0.815, below the fixed 0.90 cutoff. An offline replay matched
both manifest and decisions byte-for-byte. The length graph shows the expected
imbalance between short paragraphs and whole files; it is not a token-count graph.
English passages span 200–489 code points, while code files span 793–10,543.

A preview command initially sliced through a UTF-8 character; the preview was
fixed to decode before shortening. Original inputs were unaffected. Matplotlib
used a temporary font cache because the default cache was not writable; plotting
completed and the saved PNG was visually inspected. No collection/verification
run failed. The report records shared templates, automatic translations, placeholder
HTML and tool-maintained JSON fields as limitations.

Read the [collection report and graph](../results/2026-10-19-published-corpus/REPORT.md)
and [frozen corpus lock](../config/published-text-corpus-v1.lock.json). Next: verify
the exact-value JSON formatting variants, then measure the same six profiles.
No fitting, model inference, browser trial or FLORES+ devtest access occurred.

Publication: collection commit `4c532e4df5c5727f955c95816724ef4e2a27ac10` was pushed and
verified on GitHub main. Public scripts, sample metadata, review/check records and
figures are included; ignored local source text is not covered by this backup.

## 2026-10-19 — Published-text experiment preparation

Om authorized the experiment. Verified the frozen corpus hashes and reconstructed
100 original inputs unchanged. Prepared 40 JSON variants using exact Decimal
parsing and a shared compact/pretty serializer, preserving numeric sign, precision,
object/array order and data. All 20 source JSON equivalence checks and three focused
serializer tests passed. Prepared text is ignored/local; public input metadata
contains only IDs, categories, hashes and lengths.

The [experiment protocol](PUBLISHED_TEXT_EXPERIMENT_V1.md) fixes grouped metrics,
all-pair ratios, unknown-free sensitivity summaries, exact reconstruction checks
and graphs before encoding. Six pinned profiles will produce 840 rows. Preparation
and measurement scripts are being published before the run; no new counts yet.

## 2026-10-19 — Published-text experiment completed

The pre-encoding plan and input metadata were pushed and verified at
`b7c8b09deda75b475f973d8b98bccd06e07ad634`. We then measured all six pinned profiles
on 100 originals and 40 exact-value JSON variants. All 840 Python/JS complete
ID-sequence hashes and counts match. An independent arithmetic implementation
checked 1,146 summary groups, 10,698 values and 3,720 individual ratios; metadata,
asset hashes and JSON value/whitespace equality also passed.

Plain-language findings: counts depend on the text and tokenizer. Relative to
Qwen, LFM averages 3.33 times as many tokens on our mixed-script documentation,
while Gemma averages 0.69 times. Indenting the same JSON data adds about 61% for
Qwen and 56% for Gemma. XLM-R adds about 0.46%, but changes the original layout.
Its 100 original reconstruction mismatches comprise 99 whitespace-only cases
and one case also losing an initial byte-order mark. All 20 compact JSON inputs
reconstruct exactly with XLM-R; all 140 inputs do so with each BPE profile.
No unknown-token IDs occurred. None of this measures model intelligence.

Three graphs retain individual dots, source/language separation and reconstruction
checks. Analysis-02 improves count-axis labels and a title; all numeric files are
byte-identical to analysis-01. Both exports and the first script snapshot remain
saved. Codex visually reviewed the final PNGs. The extra BOM diagnostic was saved
as a reproducible script and checked against the original diagnostic record.

Read the [report](../results/2026-10-19-published-experiment/REPORT.md). This bounded
experiment is complete. Broader sources/additional algorithm representatives and
browser speed/memory measurement remain future design choices. No fitting,
model inference, training or FLORES+ access occurred. Public artifacts contain
numeric evidence, hashes, methods and plots; raw source text and token sequences
remain local and ignored. Publication receipt is recorded after the push.
