# Comparative Tokenizer Study

A study of how token counts vary across tokenizer configurations, languages and
text types—and what that means for managing context in browser applications.

## Latest results

[DeepSeek extension: report and updated graphs](results/2026-10-19-deepseek-extension/REPORT.md)

Eight tokenizer configurations now cover the same 100 published samples and 40
paired JSON variants. **1,120 encodings** agree between Python and JavaScript:
280 new DeepSeek measurements and 840 unchanged earlier results.

- DeepSeek V3 and R1 match on all 140 corpus inputs and reconstruct them exactly.
  Their shared BPE core does not make their added tokens or chat templates identical.
- Relative to Qwen, both use about **9.5% fewer tokens on HTML** and **24.4% more
  on mixed-script documentation**. English documentation counts are nearly equal.
- JSON indentation adds about **35.2%** for DeepSeek, compared with about **61%**
  for Qwen and **56%** for Gemma in these samples.

These are sample-specific tokenizer results, not model-quality scores. Technical
sources, shared templates and automatic translations limit generalization. One
Unigram profile cannot establish an algorithm-wide effect.

## Experiments

| Experiment | Scope | Evidence |
| --- | --- | --- |
| Tokenizer and estimator reproduction | 38 fixtures × five profiles; special-token diagnostics | [Results](docs/PHASE0_RESULTS.md) · [Reproduce](docs/REPRODUCING_PHASE0.md) |
| Multilingual pilot | 100 aligned IDs × 18 language varieties × five profiles | [Report](results/2026-10-15-phase1-pilot/run-02/REPORT.md) |
| Direct tokenizer comparisons | Same-input counts, language differences and configuration inventory | [Report](results/2026-10-18-comparative-pilot/run-01/REPORT.md) |
| Controlled text types | 180 synthetic inputs, eight probes, six profiles | [Report](results/2026-10-18-text-types/analysis-02/REPORT.md) |
| Published technical text | Initial six-profile comparison | [Collection](results/2026-10-19-published-corpus/REPORT.md) · [Results](results/2026-10-19-published-experiment/REPORT.md) |
| DeepSeek extension | V3/R1 added; eight configurations, same corpus | [Results](results/2026-10-19-deepseek-extension/REPORT.md) |

## Browser question

An estimator predicts a count; a tokenizer produces the IDs used by a model.
Browser feasibility remains unmeasured. The proposed next stage compares exact
counting, estimates and a combined approach for startup cost, memory, latency
and complete-prompt context budgets, with capacity reserved for responses.
No estimator coefficients have been fitted in this study.

## Methods and reproduction

- [Study protocol](docs/COMPARATIVE_STUDY_V2.md)
- [Evidence guide](docs/EVIDENCE_GUIDE.md) and [milestone history](docs/STUDY_HISTORY.md)
- [Latest verification](results/2026-10-19-deepseek-extension/verification.json)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

Each report links to its configuration, scripts, checks and numeric plot inputs.
Tokenizer revisions and runtime versions are pinned. MiniCPM uses its Hugging Face
JSON asset; GGUF/browser-runtime equivalence remains unverified. Counts reported
without special tokens do not represent a complete chat prompt.

Raw third-party text, tokenizer assets and reconstructable token sequences are
excluded from Git. FLORES+ is evaluation-only and is not re-hosted. Reproduction
requires the pinned local inputs and applicable source access. Frozen experiment
records retain their original hashes and provenance.
