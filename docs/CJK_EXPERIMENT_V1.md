# Controlled CJK experiment — design v1

Recorded 2026-10-16 after exploratory FLORES+ diagnostics. Owner: Om; design
prepared with Codex assistance. **Design only: no data files acquired, no weights
fitted, no new tokenizer measurements.** Source documentation was inspected.
The machine-readable companion is [cjk-experiment-v1.json](../config/cjk-experiment-v1.json).
Dataset revisions, split manifests and implementation versions must be locked
in a preflight record before this design becomes executable.

## Question and hypothesis

Does separating LocalMind's existing CJK character class into Han, kana and
Hangul improve predictions on independent text, beyond merely refitting the
existing single CJK coefficient on that same development text?

We hypothesize a reduction in mean absolute percentage error on held-out text.
This is motivated by the inspected pilot, not a hypothesis registered before
those results. A negative or mixed result is valid. The experiment assesses
this estimator representation within chosen corpora; it cannot establish a
universal causal explanation of tokenization differences.

Han is shared by Mandarin, Cantonese and Japanese. Splitting by script does
not give Cantonese its own weight and may not resolve its errors. CJK punctuation,
Hangul Jamo, supplementary Han and normalization are deliberately not changed
here: testing several changes together would obscure the comparison.

## Four arms, five existing tokenizer profiles

| Arm | CJK coefficients | Other coefficients | Purpose |
| --- | --- | --- | --- |
| Legacy | None; ceil(UTF-16 units / 3.5) | Not applicable | Historical simple baseline |
| Frozen LocalMind | Original single weight | Original weights | Continuity with the pilot |
| Refit pooled | Fit one shared CJK weight | Original weights, frozen | Matched control for refitting |
| Refit split | Fit Han, kana, Hangul weights | Same original weights, frozen | Test of splitting the class |

The primary comparison is **refit split versus refit pooled**, per tokenizer.
Both receive identical development rows, ground truth, sample weights and
fitting objective. Same tokenizer assets and content-only counting contract as
the pilot. No model inference, intercept, language-specific routing, safety
margin, tokenizer-derived extra features or fitting of the other 14 classes.
MiniCPM continues to mean the first-party HF JSON tokenizer, not verified GGUF.

Define the three buckets as an exact partition of the existing CJK class:

- Han: U+3400–U+4DBF and U+4E00–U+9FFF.
- Kana bucket: U+3040–U+30FF, including any non-letter characters already in it.
- Hangul syllable bucket: U+AC00–U+D7AF.

These are historical block-based buckets, not a complete Unicode script
classifier. No new code points move out of `other`. Verify for every input that
Han + kana + Hangul equals the old CJK count. Tying all three new weights to the
old value must reproduce original predictions, including left-to-right binary64
addition and ceiling. Do not silently replace this with a reordered dot product
at inference. Preserve original text; no Unicode normalization before counting.

## Candidate data and roles

Official treebank pages checked on 2026-10-16 list CC BY-SA 4.0 for each candidate.
This is source selection evidence, not a completed licence/revision audit. At
preflight save each repository's LICENSE, README, immutable commit, file hashes
and attribution. No source text will be committed in this experiment.

| Variety | Candidate | Role |
| --- | --- | --- |
| Traditional Chinese | [UD Chinese GSD](https://universaldependencies.org/treebanks/zh_gsd/index.html) | Primary development and held-out test |
| Japanese | [UD Japanese GSD](https://universaldependencies.org/treebanks/ja_gsd/index.html) | Primary development and held-out test |
| Korean | [UD Korean GSD](https://universaldependencies.org/treebanks/ko_gsd/index.html) | Primary development and held-out test |
| Simplified Chinese | [UD Chinese GSDSimp](https://universaldependencies.org/treebanks/zh_gsdsimp/index.html) | Secondary test on corresponding held-out Chinese source IDs only |
| Cantonese | [UD Cantonese HK](https://universaldependencies.org/treebanks/yue_hk/index.html) | Secondary transfer evaluation only, never fitted |

GSD and GSDSimp are paired versions of the same Chinese source material; do not
count them as independent languages/examples or train on one version of a test
sentence. Cantonese-HK contains dialogue from a small number of films and a
legislative proceeding. Its genre and limited source diversity constrain transfer
claims. It is not a matched translation of the other primary corpora.

This bounded design uses three primary language varieties rather than fitting
on all five pilot varieties. It specifically tests script separation and then
checks transfer to simplified Chinese and Cantonese. It does not claim broad
coverage of browser text or unseen tokenizer families.

## Preflight and separation of data

Use upstream train for fitting, dev only for implementation/debug checks, and
test for the final comparison. Never promote official test content into fitting.
Do not tune objectives, bins, stopping rules or thresholds on dev results. A
methodological change after looking at dev requires a dated amendment; test
results remain sealed until all candidates and code are frozen.

Use the original sentence from the CoNLL-U `# text` field. Missing/empty text is
excluded and counted; do not join UD word tokens with artificial spaces. Keep
all remaining rows, including code switching and unusual characters. No error-
based exclusion and no capping sample counts after seeing tokenizer outcomes.

Before fitting, an automated preparation pass may read test text solely to
validate schema, construct groups, hash and detect leakage. It must not print
test examples or expose token counts/predictions/error summaries. Thus the test
is uninspected for model development, not literally unread by preparation code.

Group sentences by original document/article/film and known translation or
conversion family. Use the most restrictive split if a group crosses upstream
splits: test > dev > train, removing its earlier-split members from use rather
than moving test into training. Within a split, retain one canonical sentence
per exact normalized-text duplicate and report removals. Dedup normalization is
NFC plus collapsed whitespace, only for matching; the measured input is unchanged.
Connect near-duplicates with character 5-gram Jaccard >=0.9 for texts at least
20 code points long; shorter texts use exact matching only. Connected components
are additional leakage groups, not proof that all semantic overlap is absent.
Apply the same family mapping to GSD and GSDSimp, not just text matching.

Exclude matches against all already-cached FLORES+ dev texts and the 38 published
LocalMind fixtures using these rules. Do not access FLORES+ devtest. Record
remaining uncertainty about unpublished fitting data and upstream tokenizer
training exposure. FLORES+ cannot be used to fit, calibrate, choose models or
set this experiment's acceptance thresholds.

Minimum preflight requirements per primary variety: 500 eligible train sentences,
100 test sentences, and 20 identifiable source/duplicate groups in each of train
and test. Each split feature must occur in at least 100 development sentences
and the split design matrix must have rank three. These are feasibility floors,
not a statistical power guarantee. Audit document identity; if it cannot be
recovered or these minima fail, publish the deficiency and amend the data plan
before fitting. Do not silently treat each sentence as an independent document.
Dataset acquisition, exact counts and compliance with these requirements remain
pending; the candidate list is not an execution-ready dataset lock.

## Fitting contract (future, requires explicit authorization)

Fit separately for each of the five tokenizer profiles. For sentence i, let T_i
be its measured content-token count, O_i the contribution of the frozen non-CJK
weights, and X_i the one or three CJK counts. Solve nonnegative least squares:

`min over w >= 0: (1/3) * sum_language mean_i_in_language ((O_i + X_i w - T_i) / T_i)^2`

This weights the three development languages equally regardless of corpus size.
Use the continuous prediction during fitting, and the common ceiling rule at
inference. There is no intercept, regularizer, ceiling-aware tuning or parameter
search. T_i must be positive; a zero count is a pipeline error requiring review.

There are at most three parameters: enumerate active subsets, solve weighted
least squares for each subset in binary64, retain feasible solutions, and select
the minimum objective. Ties within 1e-12 absolute objective select minimum L2 norm,
then lexicographic weights. Tiny negatives in [-1e-12,0) may be clamped to zero;
larger negatives are infeasible. Check KKT conditions to a documented tolerance,
report objective/residual/rank/condition diagnostics, and fail visibly if solving
is unreliable. Pin libraries and full numeric tolerances in the implementation
lock before fitting; no solver retries selected by test performance.

## Metrics and decision rule

Primary outcome: for each tokenizer, calculate mean absolute percentage error
within each of the three primary test varieties and average the three values.
Then equally average the five tokenizer results. Define delta = split minus
pooled, in percentage points. Report per-language and per-tokenizer results as
well as this macro average; do not pool all rows as independent observations.

Primary hypothesis is supported on this corpus only if the upper endpoint of
the paired 95% bootstrap interval for delta is below zero. Otherwise record
inconclusive or adverse evidence according to the interval and point estimate.
A secondary practical-relevance flag requires at least a 10% relative decrease
in the primary macro metric. If pooled error is zero, relative improvement is
undefined and cannot pass this flag. The 10% value is a prospective study
convention, not a learned threshold or browser deployment requirement.

Bootstrap 2,000 replicates, NumPy PCG64 seed 20261016, percentile interval using
linear quantiles. Resample held-out document/duplicate groups with replacement
within each primary language; keep every row, both arms, and all five tokenizers
for a sampled group together. If group membership spans primary languages, use
connected groups and jointly resample that linked stratum. Report a descriptive
sensitivity analysis if small/unequal clusters make intervals unstable. Do not
substitute independent-row resampling or add post-hoc significance claims.

For all four arms, report median/P95 absolute percentage error, undercount rate,
rate of undercount >20%, rate of overcount >20%, mean/max token shortfall and
signed error quantiles. All rates use every row in the cell, with strict >20%
cutoffs; quantiles use linear interpolation. Show fixed Unicode-length bands
[0,50), [50,100), [100,200), [200,infinity), including empty cells.

Report every cell's split-minus-pooled change in under/overcount >20% rates,
flagging any increase greater than 5 percentage points as a descriptive tradeoff.
These flags cannot overturn or conceal the primary finding. No global success
claim implies that every tokenizer benefits. The two secondary varieties do not
enter the primary statistic or candidate selection. No multiplicity-unadjusted
claims of significance for the 15 individual primary cells.

## Interpretation and next actions

- Split beats pooled: evidence that extra script coefficients help in this setting;
  not proof of a complete mechanism or a safe context-budget policy.
- Pooled beats frozen, split adds little: refitting explains the main improvement.
- Split improves development but not held-out performance: report overfitting or
  transfer limitations as possibilities, not a single established explanation.
- Neither works well: investigate other-class coverage, punctuation, context and
  tokenization structure in a separately specified follow-up; do not modify this
  test until it gives a desired result.

Next milestone is **data preflight and an immutable split manifest**, followed
by review with Om and explicit authorization before fitting. This design-only
approval does not initiate coefficient fitting, model training or test scoring.
After that review, implement parity/solver checks on synthetic inputs, freeze
code and environment, fit once, freeze coefficients, score the final test once,
and publish all outcomes. A defect discovered afterwards needs a correction log
and an explicit statement that the original test has now been exposed.

Required outputs: source/attribution lock, exclusions and group/split audit,
feature-parity tests, fitting/solver logs, frozen coefficients, all-cell metrics,
paired bootstrap output, limitations and recovery records. Raw text remains in
ignored local storage; no package or browser deployment is part of this trial.
