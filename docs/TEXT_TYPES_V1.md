# Text types and a Unigram tokenizer: controlled pilot v1

Specified 2026-10-18 before encoding this workload. Om authorized the next
text-type/non-BPE comparison and GitHub publication. This is a new, deliberately
small synthetic experiment, not a representative sample of browser traffic.
Codex authors the examples and code; this is disclosed rather than presented as
human-collected or independently translated data.

## Questions

1. For identical text, how do the five existing BPE profiles and one multilingual
   Unigram profile differ in count across representations and language mixtures?
2. Within each tokenizer, how does rendering the same record as prose, a Python
   literal assignment, compact JSON, pretty JSON or HTML change its count?
3. Does a low count coincide with unknown tokens or changes to the decoded text?

The added profile is `FacebookAI/xlm-roberta-base`, selected for its multilingual
coverage and accessible tokenizer JSON, not its performance on these examples.
Its legacy JSON omits `model.type`; the pinned runtime must load it as Unigram.
Preserve original bytes and hash a runtime-serialized copy with explicit type
for JS compatibility, then verify identical IDs on the full corpus. Pin its revision,
asset hashes and runtime. It is an encoder-model tokenizer, not a chat model.
Algorithm, vocabulary, training data and normalization all differ together, so
this is a comparison of six concrete profiles, not a causal BPE-versus-Unigram test.

Sources: [model card](https://huggingface.co/FacebookAI/xlm-roberta-base),
[tokenizer model API](https://huggingface.co/docs/tokenizers/v0.20.3/en/api/models),
[SentencePiece project](https://github.com/google/sentencepiece).
SentencePiece is a toolkit supporting more than one method; do not use the name
as a synonym for Unigram. The new source lock records the exact acquired revision.

## Workload, fixed before counts

Author 12 original record scenarios, with 1, 3 or 6 items (four scenarios each).
Each record has an English batch name, a boolean active flag, and items containing
an ID, quantity and short message. Author English/Hindi/Tamil versions of the
messages, keeping IDs, quantities and English structural labels fixed.

Cross every scenario with three content conditions: English messages,
English structure + Hindi messages, English structure + Tamil messages. Cross
each of these 36 records with five deterministic renderers:

- English-scaffold prose listing every record field.
- Python literal assignment (valid syntax, no execution).
- Compact JSON with literal Unicode, not ASCII escaping.
- Pretty JSON with literal Unicode and two-space indentation.
- HTML table with escaped values and fixed markup.

This yields **12 × 3 × 5 = 180 inputs**, each evaluated by six tokenizers:
**1,080 primary measurements**. The 12 scenarios and shared templates are the
underlying blocks, not 180 unrelated observations. Hindi/Tamil messages are
illustrative authored translations, not native-speaker-validated parallel data.
These are mixed-language records, not pure Hindi/Tamil documents. Sizes are
item-count tiers, not fixed character lengths, and are not independently randomized.
Python coverage is literal assignments, not general software. HTML is one template,
not real webpages. Prose/HTML/Python add different scaffolding; only compact versus
pretty JSON provides a narrow whitespace-formatting contrast with identical data.

Freeze generated fixtures, source records, renderer and analysis specification
by hash before encoding; make a Git checkpoint. Do not edit examples after seeing
counts. Check JSON and Python renderers recover the source record, verify HTML
field values through parsing, and check each input's text hash and unique ID.

## Separate diagnostic probes

Eight original probes cover ASCII, repeated whitespace, composed/decomposed
accents, emoji, rare characters, code indentation and a literal SentencePiece
space marker. They are **not pooled into primary results**. Their purpose is to
expose coverage/normalization behavior, not estimate its population frequency.
Save token pieces, IDs, decoded text and normalization for these shareable probes,
and for scenario 01 prose/compact JSON in all three conditions, selected in advance.

## Measurement and summaries

Use the pinned Python `tokenizers` runtime, deterministic encoding, no added
special tokens, no truncation/padding and no model calls. Save per-input content
counts, special-enabled counts/deltas separately, character/UTF-8 lengths,
unknown-token counts, normalized-text equality and exact decoded-text equality.
A decoding mismatch may reflect intentional normalization, whitespace handling or
unknown substitution; it is not automatically evidence of lost semantic meaning.
For code and exact text reconstruction, changes can nevertheless matter.
Counts can exceed a model's allowed input length because we deliberately disable
truncation; this is counting, not successful model inference.

Report all 90 model × condition × format cells (12 inputs each): count median,
10th/90th percentiles, tokens per 100 Unicode code points, unknown-input rate,
normalization-change rate and exact decode-mismatch rate. Use linear quantiles.
For every ordered model pair and each of the 15 workload cells, report geometric
mean/median/p10/p90 per-input ratios, plus unknown-free pair count and its geometric
mean (null if empty). A lower count is not a compression win if coverage differs.

Within each model and condition, pair every format to the prose representation
of the same scenario. Separately pair pretty/compact JSON. These are descriptive
ratios of the saved templates, not isolated causal effects of a general text type.
No confidence intervals, significance tests, global winner or model-quality claim.
No ranking of BPE and Unigram as whole families from one Unigram representative.

Figures: (1) six-profile count ratios relative to fixed Qwen, separated by content
condition and format; (2) within-profile format/prose ratios with a separate
pretty/compact JSON panel; (3) exact reconstruction mismatch rates, accompanied by
unknown-token rates in the numeric report. Label observed changes, denominators,
limitations and logarithmic color scales. Retain all cells, not just favorable ones.

## Validation, publication and continuation

Independently encode all inputs in a second tokenizer implementation where
supported, compare full ID sequences, and disclose any incompatibility rather
than silently substituting. Verify summary arithmetic separately. Include all
failed checks, source snapshots and hashes. Original fixtures are public project
artifacts; FLORES+ and the candidate CJK datasets are not accessed in this round.
Publish scripts, original examples, numeric results, figures and recovery records.
Keep downloaded third-party tokenizer files in ignored caches. No model weights,
paid API calls, coefficient fitting or FLORES+ devtest access.

The next study after this controlled pilot should sample varied natural workloads
and additional representatives; these templates alone cannot support broad claims.
