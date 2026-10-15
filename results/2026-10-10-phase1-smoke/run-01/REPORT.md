# Pipeline smoke test — not a multilingual pilot result

This run uses existing LocalMind fixtures only to verify the pipeline. It adds no unseen-text evidence.

Numeric measurement rows: **190**. Raw texts and token IDs are excluded from the result table.

![Tokens per character](tokens-per-character.png)

Each cell is the sum of content tokens divided by the sum of Unicode code points. It is not a word count or a measure of model quality. Comparisons within a language use identical text.

| Tokenizer | Median absolute prediction error | Worst under | Worst over | Within ±20% |
| --- | ---: | ---: | ---: | ---: |
| Qwen | 3.11% | -16.22% | +22.86% | 37/38 |
| Bonsai | 2.14% | -11.48% | +10.61% | 38/38 |
| LFM | 1.81% | -10.96% | +15.00% | 38/38 |
| Gemma | 4.74% | -16.28% | +20.83% | 37/38 |
| MiniCPM* | 2.00% | -12.50% | +15.91% | 38/38 |

## Indian, CJK and other groups

| Tokenizer | Group | Rows | Median absolute error | Within ±20% |
| --- | --- | ---: | ---: | ---: |
| Qwen | Smoke only | 38 | 3.11% | 37/38 |
| Bonsai | Smoke only | 38 | 2.14% | 38/38 |
| LFM | Smoke only | 38 | 1.81% | 38/38 |
| Gemma | Smoke only | 38 | 4.74% | 37/38 |
| MiniCPM* | Smoke only | 38 | 2.00% | 38/38 |

## Largest tokenizer gaps within a language

Ratio of the largest total token count to the smallest total count on that language’s same selected sentences. This compares tokenizers, not translations of different lengths.

| Language | Most tokens | Fewest tokens | Ratio |
| --- | --- | --- | ---: |
| Existing fixtures | LFM | Gemma | 3.50× |

## Limits

The original LocalMind fitting corpus is not fully available, so absence of overlap with all its training examples cannot be proven. We check overlap with its 38 published fixtures. Model-training exposure to FLORES is not assessed. The dataset is evaluation-only; any new estimator must be fitted on separate text.

No model inference, new fitting, full chat templates, context-overflow simulation or browser benchmark was run. The pre-token count is a diagnostic of the tokenizer’s pre-tokenizer applied after its normalizer; added-token extraction is not emulated at that stage. Content-token counts use the full tokenizer with added special tokens disabled.

The pilot is smaller than the planned full study (20+ tokenizers and broader language coverage). See run.json, validation.json, summary.json and the local ground-truth.parquet. Downloaded text remains in the ignored cache; FLORES+ attribution and use conditions are in docs/PHASE1_PILOT.md.
