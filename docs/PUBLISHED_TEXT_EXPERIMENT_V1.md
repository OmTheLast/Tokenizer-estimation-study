# Published-text tokenizer experiment v1

Authorized 2026-10-19, following the frozen 100-sample corpus. Parent rules:
[sampling plan](PUBLISHED_TEXT_SAMPLING_V1.md) and [collection record](PUBLISHED_TEXT_COLLECTION_V1.md).
Do not change selected text or review labels in response to token counts.

## Inputs and measurement

Reconstruct all 100 original samples from verified file hashes/byte ranges. For
the 20 JSON files, parse numbers directly as exact Decimal values, reject duplicate
keys/nonstandard constants, and preserve object insertion order and array order.
Produce compact and two-space-indented forms with literal Unicode and no final
newline. Both forms use the same scalar serialization. Verify recursive ordered
values including numeric sign/precision/exponent before encoding. Tests cover huge
integers, long decimals, negative zero, nested structures, escapes and invalid data.
Only pretty/compact isolates whitespace; comparing either with the original can
also change numeric spelling and character escaping.

This gives 140 inputs (100 originals + 40 derived forms) × six profiles = **840
measurement rows**. Variants are paired repeated measurements, not new documents.
Use the six exact tokenizer locks from `config/text-types-v1.json`, Python
`tokenizers==0.23.2` and JS `@huggingface/tokenizers==0.2.0`. Verify assets before
loading. Disable truncation/padding; reject stochastic dropout. Primary counts
exclude special tokens; save counts with configured special tokens separately.
Also save unknown-ID counts, normalized length/change, exact decoded-string match,
decoded-string hash and full ID-sequence hash. Never publish raw/normalized/decoded
text or token sequences. Confirm original/serialized XLM-R Python parity as before.
Also record whether decoded text equals the input after removing all Unicode
whitespace from both. This distinguishes whitespace-only differences from other
changes; it is not a test of semantic equivalence or executable-code correctness.

Public preparation metadata and this plan are committed before encoding. Private
prepared text stays under ignored `data/processed/`. Save resumable per-profile
Python shards and separate JS encodings. On resume, require identical script,
input and configuration hashes. Keep earlier attempts rather than overwrite them.

## Comparisons fixed before results

For **originals**, summarize five categories, all ten source/language strata and
each occupied category × fixed length-band cell (200–999, 1,000–3,999, 4,000–12,000).
Do not fill empty length cells or pool a web-wide leaderboard. For JSON variants,
also report each format in the combined 20-file group and each 10-file source.

Each cell saves sample count, median/p10/p90 token count, median tokens per 100
code points, unknown-input count/rate, normalization-change count/rate and exact
decode mismatch count/rate. Preserve all 36 ordered tokenizer-pair summaries per
original cell and all per-input ratios. Qwen is a fixed reference, not a quality
standard. Ratio summaries: n, geometric mean, median, p10/p90, min/max, plus n and
geometric mean after excluding inputs with unknown IDs in either profile. Show
both full and unknown-free summaries; do not remove unknowns silently.

JSON pretty/compact comparisons use the same sample IDs and tokenizer, combined
and split by source. Percentiles use linear interpolation and describe sample
spread, not confidence intervals. Related files/templates are not independent
population draws. Source, subject, length, language and format remain intertwined.

Graphs: per-input original count ratios to Qwen with source/language colors;
paired JSON formatting ratios with source colors; exact reconstruction and
unknown-input rates with denominators. Link to the existing sample-length graph.
Keep numeric plot inputs and PNG/SVG/PDF exports with readable captions.

## Verification and interpretation

Compare full ID-sequence hashes and counts for all 840 inputs across Python/JS.
Recompute per-row metadata in Python; independently recompute summary arithmetic
using a separate implementation. Verify group membership/coverage and every
summary value; inspect figures before publication. Hash all relevant artifacts.

This measures tokenizer behavior, not model intelligence, browser performance,
full chat overhead or an isolated BPE-versus-Unigram effect. XLM-R is an encoder
tokenizer; MiniCPM uses the pinned HF JSON with no proven GGUF-runtime equivalence.
Sources are technical convenience samples; mixed passages are automatic
translations. No estimator fitting, model inference, FLORES+ access or paid
service calls are involved.
