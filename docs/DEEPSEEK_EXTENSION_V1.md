# DeepSeek tokenizer extension v1

Specified 2026-10-19 before encoding. Add the official full-model DeepSeek-V3
and DeepSeek-R1 tokenizer configurations to the published technical-text study.
These are named releases, not a claim to cover every current DeepSeek release.
Distilled Qwen/Llama models are excluded from this extension.

## Identity and inputs

Pinned revisions and asset hashes are recorded in the two tokenizer locks.
The configurations share their BPE model, normalizer, pre-tokenizer, decoder and
post-processor. Added-token entries differ at IDs 128798 and 128799; R1 uses
`<think>` and `</think>`. Chat templates also differ. Preserve separate profiles,
but do not count them as independent algorithm families. No model weights or
repository code are needed.

Use all 140 previously frozen inputs: 100 originals and 40 exact-value JSON
variants. Do not replace samples or revise eligibility after seeing counts.
Reuse the previous six profiles' 840 verified rows unchanged; add 280 new rows
and independently check the combined 1,120-row evidence. The corpus has already
been inspected, so this is exploratory replication, not unseen final evaluation.

Four separately labeled synthetic diagnostic inputs cover plain text, each
reasoning marker and markers embedded in text. They are probes of known asset
differences, not representative data; exclude their eight measurements from
corpus summaries and plots.

## Measurements and comparisons

Retain the previous definitions: content-only counts, separate special-token
counts, unknown IDs, normalization, exact reconstruction, hashes and no truncation.
Verify all new encodings in Python tokenizers 0.23.2 and JS tokenizers 0.2.0.
Recheck combined metadata and arithmetic independently; saved earlier JS encodings
are reused with pinned hashes. Report whether V3/R1 sequences match on each input.
Do not infer global equivalence from agreement on these samples.

Summarize all eight profiles by category, source/language stratum and occupied
length band, with all ordered tokenizer-pair ratios and paired pretty/compact JSON
ratios. Preserve geometric means, medians, p10/p90, extrema, unknown-free results,
per-input dots and exact denominators. Regenerate the three comparison graphs.
Do not pool tokenizer profiles into a family-level average. Link the earlier report
rather than replacing it. Freeze protocol/configuration/scripts before encoding.

## Interpretation

Model parameter count is not a tokenizer method. Larger models may share a
vocabulary and splitting pipeline. Tokenizer file size is descriptive here, not
measured browser download time or memory use. Full chat formatting, inference,
API behavior and browser benchmarking remain outside this extension. The technical
source, automatic translation, shared-template and MiniCPM equivalence limitations
from the earlier study still apply. No fitting or FLORES+ access is involved.

Only compact metadata, scripts, counts, hashes and figures are published.
Tokenizer assets, source notices and the original third-party corpus stay local.
Official sources: [V3](https://huggingface.co/deepseek-ai/DeepSeek-V3) and
[R1](https://huggingface.co/deepseek-ai/DeepSeek-R1); immutable asset URLs are in
`config/deepseek-v3-tokenizer.lock.json` and `config/deepseek-r1-tokenizer.lock.json`.
