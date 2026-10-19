# Comparative Tokenizer Study: Languages, Text Types, and Context Budgets

Version 2, recorded 2026-10-18.
This supersedes the umbrella priority in the [earlier protocol](RESEARCH_PROTOCOL.md),
which remains the historical record. It does not retrospectively redesign the
completed pilot. The first comparative analysis is exploratory: its input data
and earlier summaries have already been inspected.

## Main question

How do different tokenizers split text, how do their token counts vary across
languages and text types, and what do those differences mean for context use?

An estimator predicts a count. A tokenizer produces the actual token sequence.
Estimation is now one sub-question; improving an estimator is not a prerequisite
to learning about tokenizer behavior. Model answer quality is outside this scope.

## Questions and order

| Priority | Question | Evidence |
| --- | --- | --- |
| 1 | What tokenizer configurations are we actually comparing? | Verified assets, vocabulary counts, algorithm and processing stages; explicit identity grouping |
| 2 | How do counts differ on identical text? | Paired counts and ratio distributions for every tokenizer pair and language |
| 3 | How do counts differ across languages? | Aligned translations within each tokenizer, with length/translation limitations |
| 4 | How does text type change behavior? | Prospectively sampled prose, code, JSON/HTML and mixed-language cases; shareable token-boundary examples |
| 5 | How reliable are inexpensive count estimates? | Existing errors; optional separately authorized fitting experiment |
| 6 | What is useful in a browser? | Measured startup, memory, latency and complete-prompt context budgets |

This round covers priorities 1–3 using the existing five profiles and numeric
FLORES+ dev pilot. Priorities 4–6 are future work. No new data acquisition,
coefficient fitting, model inference or FLORES+ devtest access is part of this round.
The [CJK fitting design](CJK_EXPERIMENT_V2.md) is deferred, preserved and unstarted.
Its unresolved source-use question is separate from this authorized pilot analysis.

## What “family” means here

Keep model branding, algorithm class, exact tokenizer identity and historical
lineage separate. Inspect actual assets rather than infer behavior from a name.
Record full-file hashes and canonical fingerprints for the model/vocabulary,
merges, normalizer, pre-tokenizer, decoder, post-processor and added-token rules.
Identical core vocabularies or algorithms alone do not establish identical
behavior. Exact fingerprints establish equality of those serialized components,
not an exhaustive proof of semantic equivalence under every runtime.

Initial labels are individual pinned profiles and their inspected algorithm
classes. Do not assert genealogical families without evidence of lineage, or
claim an algorithm-class effect from one or a few differently configured assets.
If every profile uses the same algorithm class, explicitly report the coverage
gap; adding representatives of another class requires a subsequent sampling plan.
No family-level causal claim or clustering inferred from these five results.

## First comparative analysis, specified before execution

The machine-readable specification is
[comparative-pilot-v1.json](../config/comparative-pilot-v1.json).
Use only content-token counts (special-token insertion disabled), retain all
100 aligned IDs × 18 varieties × 5 profiles, and verify complete matching and
text hashes within each language/ID. Verify source revisions and numeric input hash.

For each ordered tokenizer pair A/B, compute per-text count ratios. Summarize
all 18 language cells (100 ratios each) and the balanced pooled sample (1,800):
geometric mean, median, 10th/90th percentiles, minimum/maximum and fractions where
A has fewer/equal/more tokens. Also retain paired counts for graph reproduction.
The geometric mean is exp(mean(log(A/B))); it averages multiplicative differences
and reverses exactly when A/B is changed to B/A (up to floating-point precision).
It is not the ratio of summed counts. Quantiles use linear interpolation.

Separately, within each tokenizer, pair each language with English by aligned ID.
Report the same summaries for language/English. English is a reference, not a
quality standard; translated text is not identical text. Figures:

1. All ordered tokenizer-pair geometric means, row count divided by column count.
2. Per-language ratios relative to Qwen, with median and 10th–90th percentile
   intervals for the other four profiles. Qwen is an arbitrary fixed reference,
   not a winner selected after analysis. All pairs remain in the numeric report.
3. Language/English geometric mean count ratios within each tokenizer.

Percentile intervals describe variation among measured ratios, not uncertainty
in a population mean. No independent-row significance tests or confidence intervals.
These are 100 related sets of translations, repeatedly measured by five tokenizers.
Full results retain unfavorable comparisons. Do not infer intelligence, causes,
or universal efficiency rankings. Smaller counts alone do not prove better models.
Raw counts across translations reflect length, writing and translation choices.

## Research record and next stage

Save scripts, configuration, numeric summaries, labeled PNG/SVG/PDF figures,
input/output hashes, independent verification and readable interpretations.
Publish compact permitted evidence on the existing GitHub repository; keep raw
FLORES+ text, token sequences, caches and third-party assets out of public commits.
The public study title changes; the existing repository URL remains stable.

After this round, specify a small text-type expansion and the algorithm-class
coverage we need. Define sampling and metrics before collecting it. Token-boundary
illustrations should use original or otherwise shareable examples. Later browser
experiments must measure actual serialized prompts and reserve response capacity;
sentence-level count ratios alone do not establish useful context capacity.

## Text-type extension — 2026-10-18

[Text types v1](TEXT_TYPES_V1.md) freezes 180 original primary inputs and eight
separate probes, measured with the five existing BPE profiles and a pinned
XLM-RoBERTa Unigram profile. This is a controlled synthetic extension, not a
representative corpus or an isolated causal algorithm comparison. The design
and fixtures were pushed before encoding.

[Results](../results/2026-10-18-text-types/analysis-02/REPORT.md) include counts,
unknown-token checks, exact reconstruction and three scientific figures. The
new Unigram asset's legacy schema and source-preserving compatibility checks
are documented. The CJK coefficient experiment remains deferred. Next specify
varied natural workloads and additional profiles before broad generalization.
