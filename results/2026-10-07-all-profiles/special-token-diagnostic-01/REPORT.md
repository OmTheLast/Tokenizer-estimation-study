# Special-token discrepancy diagnosis

All 190 saved counts match fresh special-enabled counts in JS and Python under the pinned setup. Content-only counts differ by one token for all LFM and MiniCPM fixtures.

| Profile | Saved = content only | Saved = special enabled | Added prefix |
| --- | ---: | ---: | --- |
| qwen35-4b | 38/38 | 38/38 | none |
| bonsai-ternary-4b | 38/38 | 38/38 | none |
| lfm2-1.2b | 0/38 | 38/38 | `<|startoftext|>` (ID 1) |
| gemma4-e2b | 38/38 | 38/38 | none |
| minicpm5-2b-gguf | 0/38 | 38/38 | `<s>` (ID 0) |

The JS library's documented option is `add_special_tokens: false`. Passing `addSpecialTokens: false`, the spelling written in the fixture header, behaves exactly like the default and like `add_special_tokens: true` on every sample in this experiment.

For LFM, enabling specials prepends `<|startoftext|>` (ID 1); for MiniCPM, it prepends `<s>` (ID 0). All remaining IDs are identical to the content-only encoding. JS and Python agree on both modes for all 190 comparisons.

This reproduces a plausible mechanism for the extra token. It does not prove the original author's exact call or library version. Preserve the upstream fixtures and label their saved counts as special-enabled-compatible; use explicit content-only counts for the study. No estimator weights were changed.

The original all-profile run correctly exits 2 because the stated content-only reference contract failed in 76 rows. A successful diagnostic does not erase that failure or change the content-only benchmark.
