# All-profile reference verification and Python estimator port

Completed 190/190 sample/profile comparisons. Saved counts match both fresh implementations in 114 cases; full JS/Python token IDs match in 190. Python estimates match original JS estimates in 190 cases.

| Profile | Saved = JS | Saved = Python | IDs match | Estimator matches | Worst under | Worst over | Median absolute error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen35-4b | 38/38 | 38/38 | 38/38 | 38/38 | -16.22% | +22.86% | 3.11% |
| bonsai-ternary-4b | 38/38 | 38/38 | 38/38 | 38/38 | -11.48% | +10.61% | 2.14% |
| lfm2-1.2b | 0/38 | 0/38 | 38/38 | 38/38 | -10.96% | +15.00% | 1.81% |
| gemma4-e2b | 38/38 | 38/38 | 38/38 | 38/38 | -16.28% | +20.83% | 4.74% |
| minicpm5-2b-gguf | 0/38 | 0/38 | 38/38 | 38/38 | -12.50% | +15.91% | 2.00% |

Errors above use the fresh Python tokenizer as reference. Inspect disagreements before interpreting metrics where implementations differ.

Python estimator parity also checked 380 fixture/alias combinations, 1230 edge combinations, and 109 class boundaries: 0 mismatches.

## Limits

Existing fixtures only; no fitting or held-out evaluation. Historical fixture asset/library versions were not recorded. Our runs pin their own assets and versions. MiniCPM uses the first-party parent JSON tokenizer, not the GGUF/wllama runtime. No browser benchmark, chat template or output allowance was tested.

See comparison.csv for every row, disagreements.json for mismatches, per-profile directories for both ID sequences, and run.json for provenance.
