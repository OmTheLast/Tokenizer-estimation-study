# Frozen-pilot error analysis

Exploratory diagnostics of 9,000 measurements from 100 aligned sentence IDs, 18 language varieties and five tokenizer profiles. Both estimators remain unchanged. No model inference, fitting, new data access or devtest access occurred.

Every rate uses all rows in the stated cell. Shortfall means max(actual − predicted, 0), including zeros. The 20% cutoff is descriptive, not a safety target. Quantiles use linear interpolation. Empty cells have null metrics.

## Overall results

| Tokenizer | Estimator | N | Undercount | Under by >20% | Median abs. error | P95 abs. error | Mean shortfall (tokens) | Max shortfall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Bonsai | localmind | 1800 | 50.11% | 13.67% | 4.35% | 30.61% | 3.11 | 36 |
| Bonsai | legacy_utf16_div_3_5 | 1800 | 93.67% | 88.78% | 69.90% | 84.93% | 83.64 | 437 |
| Gemma | localmind | 1800 | 55.56% | 17.44% | 11.11% | 33.33% | 3.27 | 32 |
| Gemma | legacy_utf16_div_3_5 | 1800 | 71.94% | 53.00% | 31.11% | 63.16% | 12.81 | 101 |
| LFM | localmind | 1800 | 36.67% | 12.94% | 3.28% | 41.47% | 2.86 | 38 |
| LFM | legacy_utf16_div_3_5 | 1800 | 93.78% | 90.33% | 76.92% | 89.13% | 150.21 | 712 |
| MiniCPM* | localmind | 1800 | 47.39% | 12.56% | 3.49% | 36.36% | 3.08 | 46 |
| MiniCPM* | legacy_utf16_div_3_5 | 1800 | 92.28% | 89.44% | 69.23% | 89.13% | 121.81 | 601 |
| Qwen | localmind | 1800 | 57.17% | 14.61% | 8.70% | 33.90% | 3.60 | 28 |
| Qwen | legacy_utf16_div_3_5 | 1800 | 88.17% | 83.56% | 47.62% | 64.77% | 26.42 | 125 |

## Where the older heuristic does better

Counts below compare all 90 cells separately for each metric, on the same texts. A method can win on one metric and lose on another; lower undercount alone can result from excessive overestimation.

| Metric | LocalMind lower | Equal | Legacy lower |
| --- | ---: | ---: | ---: |
| median_absolute_percent_error | 89 | 0 | 1 |
| p95_absolute_percent_error | 89 | 0 | 1 |
| under_by_more_than_20_percent_fraction | 77 | 3 | 10 |
| mean_absolute_token_error | 89 | 0 | 1 |

Cells where legacy has lower median absolute error:

- MiniCPM* / rus_Cyrl: LocalMind 11.63%, legacy 9.65%.

Paired signed-error differences are directional, not generic better/worse scores. A more negative signed error means more underestimation. Lower undercount rates must be read alongside absolute error and overestimation.


## All tokenizer-language cells

Each cell contains 100 texts. Percentages below summarize its unchanged LocalMind predictions. JSON includes every metric for both estimators and paired differences.

| Tokenizer | Language | Undercount | Under by >20% | Median abs. error | P95 abs. error | Mean token shortfall | Legacy median abs. error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Bonsai | arb_Arab | 69% | 11% | 9.23% | 23.89% | 3.90 | 23.61% |
| Bonsai | ben_Beng | 31% | 0% | 2.44% | 6.29% | 1.07 | 73.19% |
| Bonsai | cmn_Hans | 49% | 12% | 11.11% | 26.70% | 2.58 | 52.33% |
| Bonsai | cmn_Hant | 90% | 45% | 17.82% | 36.18% | 6.30 | 62.07% |
| Bonsai | eng_Latn | 29% | 2% | 7.98% | 31.82% | 0.80 | 42.30% |
| Bonsai | guj_Gujr | 51% | 0% | 1.77% | 4.75% | 2.16 | 80.30% |
| Bonsai | hin_Deva | 42% | 0% | 2.19% | 6.73% | 1.73 | 68.86% |
| Bonsai | jpn_Jpan | 68% | 13% | 9.45% | 28.25% | 3.39 | 56.25% |
| Bonsai | kan_Knda | 21% | 0% | 2.34% | 5.96% | 0.95 | 79.17% |
| Bonsai | kor_Hang | 100% | 68% | 23.96% | 34.82% | 10.80 | 58.14% |
| Bonsai | mal_Mlym | 16% | 0% | 3.81% | 9.54% | 0.73 | 78.42% |
| Bonsai | mar_Deva | 28% | 0% | 2.38% | 6.36% | 0.69 | 70.04% |
| Bonsai | ory_Orya | 22% | 0% | 2.28% | 5.03% | 0.93 | 85.48% |
| Bonsai | pan_Guru | 85% | 0% | 2.47% | 6.54% | 5.07 | 80.79% |
| Bonsai | rus_Cyrl | 65% | 10% | 10.17% | 25.03% | 3.84 | 16.47% |
| Bonsai | tam_Taml | 5% | 0% | 4.27% | 8.79% | 0.14 | 73.66% |
| Bonsai | tel_Telu | 31% | 0% | 1.59% | 4.59% | 0.89 | 80.27% |
| Bonsai | yue_Hant | 100% | 85% | 27.78% | 39.48% | 9.97 | 66.67% |
| Gemma | arb_Arab | 47% | 0% | 7.95% | 20.06% | 1.72 | 14.14% |
| Gemma | ben_Beng | 54% | 9% | 7.77% | 25.08% | 2.19 | 16.84% |
| Gemma | cmn_Hans | 85% | 29% | 15.11% | 29.22% | 4.24 | 55.90% |
| Gemma | cmn_Hant | 94% | 58% | 21.95% | 35.36% | 6.38 | 60.92% |
| Gemma | eng_Latn | 23% | 1% | 9.09% | 31.59% | 0.58 | 45.45% |
| Gemma | guj_Gujr | 47% | 2% | 7.89% | 24.36% | 2.29 | 26.57% |
| Gemma | hin_Deva | 37% | 1% | 8.45% | 23.83% | 1.23 | 11.03% |
| Gemma | jpn_Jpan | 59% | 7% | 9.23% | 27.32% | 2.13 | 48.33% |
| Gemma | kan_Knda | 74% | 13% | 10.30% | 25.04% | 5.18 | 23.67% |
| Gemma | kor_Hang | 100% | 95% | 33.33% | 41.47% | 12.20 | 48.39% |
| Gemma | mal_Mlym | 41% | 3% | 9.00% | 21.69% | 2.28 | 11.58% |
| Gemma | mar_Deva | 52% | 7% | 8.09% | 25.05% | 2.02 | 9.76% |
| Gemma | ory_Orya | 0% | 0% | 14.93% | 23.34% | 0.00 | 58.74% |
| Gemma | pan_Guru | 26% | 0% | 4.93% | 16.76% | 0.72 | 47.52% |
| Gemma | rus_Cyrl | 63% | 12% | 9.38% | 25.62% | 3.11 | 13.68% |
| Gemma | tam_Taml | 46% | 2% | 8.25% | 26.94% | 2.00 | 14.01% |
| Gemma | tel_Telu | 55% | 9% | 7.69% | 23.86% | 3.14 | 20.31% |
| Gemma | yue_Hant | 97% | 66% | 26.09% | 36.90% | 7.52 | 62.33% |
| LFM | arb_Arab | 37% | 1% | 4.94% | 14.94% | 1.43 | 35.20% |
| LFM | ben_Beng | 38% | 0% | 1.31% | 3.37% | 1.46 | 85.71% |
| LFM | cmn_Hans | 42% | 10% | 14.29% | 41.48% | 2.08 | 64.29% |
| LFM | cmn_Hant | 87% | 56% | 23.54% | 46.66% | 8.89 | 72.38% |
| LFM | eng_Latn | 22% | 1% | 9.09% | 31.32% | 0.45 | 40.31% |
| LFM | guj_Gujr | 11% | 0% | 0.31% | 0.79% | 0.18 | 88.30% |
| LFM | hin_Deva | 53% | 0% | 2.23% | 8.88% | 2.70 | 76.72% |
| LFM | jpn_Jpan | 14% | 0% | 14.29% | 47.27% | 0.46 | 55.26% |
| LFM | kan_Knda | 63% | 0% | 0.75% | 2.86% | 1.82 | 88.89% |
| LFM | kor_Hang | 100% | 99% | 42.48% | 48.66% | 18.65 | 58.33% |
| LFM | mal_Mlym | 12% | 0% | 0.25% | 1.79% | 0.16 | 89.18% |
| LFM | mar_Deva | 7% | 0% | 5.56% | 11.24% | 0.29 | 76.63% |
| LFM | ory_Orya | 7% | 0% | 0.35% | 3.15% | 0.10 | 88.63% |
| LFM | pan_Guru | 4% | 0% | 0.63% | 2.45% | 0.05 | 87.93% |
| LFM | rus_Cyrl | 29% | 0% | 9.20% | 29.67% | 0.70 | 12.70% |
| LFM | tam_Taml | 0% | 0% | 4.02% | 6.01% | 0.00 | 86.45% |
| LFM | tel_Telu | 43% | 0% | 0.32% | 2.10% | 0.69 | 88.76% |
| LFM | yue_Hant | 91% | 66% | 27.06% | 43.85% | 11.37 | 73.96% |
| MiniCPM* | arb_Arab | 45% | 0% | 2.83% | 10.30% | 2.36 | 68.47% |
| MiniCPM* | ben_Beng | 87% | 0% | 2.19% | 4.64% | 4.72 | 82.25% |
| MiniCPM* | cmn_Hans | 45% | 7% | 11.11% | 24.42% | 1.92 | 47.83% |
| MiniCPM* | cmn_Hant | 100% | 89% | 30.86% | 43.62% | 10.47 | 65.00% |
| MiniCPM* | eng_Latn | 9% | 0% | 13.71% | 36.59% | 0.19 | 45.31% |
| MiniCPM* | guj_Gujr | 6% | 0% | 1.22% | 2.30% | 0.08 | 89.01% |
| MiniCPM* | hin_Deva | 65% | 0% | 4.05% | 10.98% | 3.80 | 63.25% |
| MiniCPM* | jpn_Jpan | 63% | 9% | 9.23% | 25.96% | 3.08 | 53.85% |
| MiniCPM* | kan_Knda | 21% | 0% | 2.82% | 8.41% | 0.94 | 76.97% |
| MiniCPM* | kor_Hang | 83% | 11% | 11.53% | 22.59% | 4.23 | 51.93% |
| MiniCPM* | mal_Mlym | 47% | 0% | 1.35% | 3.25% | 2.52 | 86.56% |
| MiniCPM* | mar_Deva | 11% | 0% | 4.39% | 12.66% | 0.28 | 62.50% |
| MiniCPM* | ory_Orya | 37% | 0% | 0.52% | 1.61% | 0.97 | 89.15% |
| MiniCPM* | pan_Guru | 40% | 0% | 0.41% | 1.11% | 0.71 | 88.75% |
| MiniCPM* | rus_Cyrl | 66% | 11% | 11.63% | 25.11% | 3.87 | 9.65% |
| MiniCPM* | tam_Taml | 1% | 0% | 2.94% | 5.50% | 0.02 | 83.25% |
| MiniCPM* | tel_Telu | 27% | 0% | 0.70% | 1.57% | 0.54 | 84.33% |
| MiniCPM* | yue_Hant | 100% | 99% | 39.01% | 48.90% | 14.80 | 69.34% |
| Qwen | arb_Arab | 65% | 10% | 10.64% | 27.32% | 3.36 | 11.11% |
| Qwen | ben_Beng | 36% | 3% | 8.73% | 21.13% | 1.82 | 36.84% |
| Qwen | cmn_Hans | 49% | 8% | 10.53% | 30.44% | 1.83 | 47.37% |
| Qwen | cmn_Hant | 81% | 37% | 17.39% | 37.95% | 4.67 | 55.56% |
| Qwen | eng_Latn | 32% | 2% | 7.14% | 31.59% | 0.87 | 42.30% |
| Qwen | guj_Gujr | 79% | 0% | 5.87% | 14.36% | 4.91 | 56.95% |
| Qwen | hin_Deva | 37% | 0% | 6.37% | 18.77% | 1.45 | 30.99% |
| Qwen | jpn_Jpan | 58% | 9% | 9.09% | 28.15% | 2.17 | 45.83% |
| Qwen | kan_Knda | 84% | 2% | 7.98% | 17.67% | 6.90 | 53.64% |
| Qwen | kor_Hang | 100% | 93% | 31.79% | 42.86% | 10.89 | 42.86% |
| Qwen | mal_Mlym | 28% | 0% | 5.74% | 18.28% | 1.25 | 48.26% |
| Qwen | mar_Deva | 82% | 5% | 7.35% | 20.03% | 5.08 | 39.38% |
| Qwen | ory_Orya | 2% | 0% | 13.01% | 25.04% | 0.02 | 63.32% |
| Qwen | pan_Guru | 42% | 0% | 2.25% | 8.39% | 1.48 | 63.41% |
| Qwen | rus_Cyrl | 59% | 13% | 12.75% | 28.59% | 3.69 | 14.04% |
| Qwen | tam_Taml | 47% | 1% | 5.26% | 17.30% | 2.44 | 37.35% |
| Qwen | tel_Telu | 49% | 0% | 4.75% | 16.47% | 2.64 | 51.83% |
| Qwen | yue_Hant | 99% | 80% | 29.06% | 44.44% | 9.26 | 62.50% |

## Language groups

| Tokenizer | Group | Languages | N | LocalMind under by >20% | Legacy under by >20% |
| --- | --- | ---: | ---: | ---: | ---: |
| Bonsai | CJK | 5 | 500 | 44.60% | 100.00% |
| Bonsai | Indian | 10 | 1000 | 0.00% | 100.00% |
| Bonsai | Other | 3 | 300 | 7.67% | 32.67% |
| Gemma | CJK | 5 | 500 | 51.00% | 100.00% |
| Gemma | Indian | 10 | 1000 | 4.60% | 42.20% |
| Gemma | Other | 3 | 300 | 4.33% | 10.67% |
| LFM | CJK | 5 | 500 | 46.20% | 100.00% |
| LFM | Indian | 10 | 1000 | 0.00% | 100.00% |
| LFM | Other | 3 | 300 | 0.67% | 42.00% |
| MiniCPM* | CJK | 5 | 500 | 43.00% | 100.00% |
| MiniCPM* | Indian | 10 | 1000 | 0.00% | 100.00% |
| MiniCPM* | Other | 3 | 300 | 3.67% | 36.67% |
| Qwen | CJK | 5 | 500 | 45.40% | 100.00% |
| Qwen | Indian | 10 | 1000 | 1.10% | 99.10% |
| Qwen | Other | 3 | 300 | 8.33% | 4.33% |

## Largest LocalMind misses

One example per ranking and tokenizer is shown; diagnostics.json preserves the planned top five for each estimator. Source text and token sequences are not included.

| Tokenizer | Ranking | Language | ID | Predicted | Actual | Signed error | Missing tokens |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| Bonsai | largest_percentage_undercounts | cmn_Hant | 131 | 18 | 34 | -47.06% | 16 |
| Bonsai | largest_token_shortfalls | kor_Hang | 49 | 58 | 94 | -38.30% | 36 |
| Gemma | largest_percentage_undercounts | kor_Hang | 891 | 20 | 39 | -48.72% | 19 |
| Gemma | largest_token_shortfalls | tel_Telu | 484 | 97 | 129 | -24.81% | 32 |
| LFM | largest_percentage_undercounts | kor_Hang | 891 | 21 | 44 | -52.27% | 23 |
| LFM | largest_token_shortfalls | kor_Hang | 49 | 44 | 82 | -46.34% | 38 |
| MiniCPM* | largest_percentage_undercounts | yue_Hant | 843 | 11 | 26 | -57.69% | 15 |
| MiniCPM* | largest_token_shortfalls | yue_Hant | 215 | 52 | 98 | -46.94% | 46 |
| Qwen | largest_percentage_undercounts | yue_Hant | 370 | 15 | 29 | -48.28% | 14 |
| Qwen | largest_token_shortfalls | kan_Knda | 374 | 92 | 120 | -23.33% | 28 |

## Length and script diagnostics

diagnostics.json contains all 360 tokenizer-language-length cells, including empty cells, for the fixed Unicode-character bands [0,50), [50,100), [100,200), and [200,infinity). It also contains script feature totals divided by total Unicode characters for all 90 cells, and numeric features for selected outliers. Extra script diagnostics overlap the baseline classes and must not be summed as disjoint categories.

Compare lengths within a language and tokenizer before interpreting pooled patterns. Text length, script and content vary together; descriptive differences do not prove a causal effect. No new classifier, coefficient or safety margin was fitted.

## Interpretation limits

These repeated measurements are not 9,000 independent examples. No significance tests or confidence intervals are reported. The pilot summaries were inspected before the diagnostic plan was specified. Any hypotheses prompted by these results need independent tests. The shared CJK weight is a possible mechanism, not an established explanation.

Small median errors do not bound individual undercounts. A large percentage error and a large absolute token shortfall need not select the same example. Count errors alone do not measure browser speed, model quality, or actual context-overflow frequency.

*MiniCPM uses its HF JSON tokenizer; GGUF/browser equivalence remains unverified. Upstream fitting/training overlap is unknown. Raw FLORES+ data remain local and evaluation-only. No final devtest data were read.

Reproduce from the project root: `.venv/bin/python scripts/analyze_pilot_errors.py --output results/pilot-diagnostics-new`. This requires the existing local pilot Parquet. Inputs, specification, source hashes and runtime versions are in validation.json.

All fixed length-band results: [LENGTH_REPORT.md](LENGTH_REPORT.md).

## Script composition across the five CJK varieties

The same texts have the same character composition across tokenizers, so composition is shown once. Shares use totals over each variety’s 100 texts; categories shown here overlap and are not a partition.

| Variety | Han | Kana | Hangul syllables | CJK punctuation | Baseline other class |
| --- | ---: | ---: | ---: | ---: | ---: |
| cmn_Hans | 81.06% | 0.00% | 0.00% | 2.92% | 7.70% |
| cmn_Hant | 85.52% | 0.03% | 0.00% | 3.47% | 7.53% |
| jpn_Jpan | 31.71% | 58.57% | 0.00% | 5.32% | 5.83% |
| kor_Hang | 0.03% | 0.00% | 70.36% | 0.00% | 0.03% |
| yue_Hant | 85.56% | 0.00% | 0.00% | 3.36% | 7.42% |

These different script mixtures are collapsed into one baseline CJK weight (plus other character classes). This motivates a controlled follow-up using separate development data; it does not establish that splitting the class would resolve the observed errors.
