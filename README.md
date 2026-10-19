# Comparative Tokenizer Study

A study of how token counts vary across tokenizer configurations, languages and
text types—and what that means for managing context in browser applications.

## Latest results

[Published-text experiment: report and graphs](results/2026-10-19-published-experiment/REPORT.md)

Six tokenizer profiles measured 100 published technical samples plus 40 paired
JSON variants. All **840 encodings** agree between Python and JavaScript.

- Indented JSON uses about **61% more tokens with Qwen** and **56% more with Gemma**
  than compact JSON containing the same data.
- On mixed-script documentation, LFM averages **3.33× Qwen's count** and Gemma **0.69×**.
- XLM-R's JSON formatting overhead is about **0.46%**, but it changes whitespace.
  The five BPE profiles reconstruct all 140 inputs exactly.

These are sample-specific tokenizer results, not model-quality scores. The corpus
contains technical sources, shared templates and automatic translations; it is
not representative browser traffic. One Unigram profile cannot establish an
algorithm-wide effect.

## Experiments

| Experiment | Scope | Evidence |
| --- | --- | --- |
| Tokenizer and estimator reproduction | 38 fixtures × five profiles; special-token diagnostics | [Results](docs/PHASE0_RESULTS.md) · [Reproduce](docs/REPRODUCING_PHASE0.md) |
| Multilingual pilot | 100 aligned IDs × 18 language varieties × five profiles | [Report](results/2026-10-15-phase1-pilot/run-02/REPORT.md) |
| Direct tokenizer comparisons | Same-input counts, language differences and configuration inventory | [Report](results/2026-10-18-comparative-pilot/run-01/REPORT.md) |
| Controlled text types | 180 synthetic inputs, eight probes, six profiles | [Report](results/2026-10-18-text-types/analysis-02/REPORT.md) |
| Published technical text | 100 originals, 40 JSON variants, six profiles | [Collection](results/2026-10-19-published-corpus/REPORT.md) · [Results](results/2026-10-19-published-experiment/REPORT.md) |

## Browser question

An estimator predicts a count; a tokenizer produces the IDs used by a model.
Browser feasibility remains unmeasured. The proposed next stage compares exact
counting, estimates and a combined approach for startup cost, memory, latency
and complete-prompt context budgets, with capacity reserved for responses.
No estimator coefficients have been fitted in this study.

## Methods and reproduction

- [Study protocol](docs/COMPARATIVE_STUDY_V2.md)
- [Evidence guide](docs/EVIDENCE_GUIDE.md) and [milestone history](docs/STUDY_HISTORY.md)
- [Latest verification](results/2026-10-19-published-experiment/verification.json)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

Each report links to its configuration, scripts, checks and numeric plot inputs.
Tokenizer revisions and runtime versions are pinned. MiniCPM uses its Hugging Face
JSON asset; GGUF/browser-runtime equivalence remains unverified. Counts reported
without special tokens do not represent a complete chat prompt.

Raw third-party text, tokenizer assets and reconstructable token sequences are
excluded from Git. FLORES+ is evaluation-only and is not re-hosted. Reproduction
requires the pinned local inputs and applicable source access. Frozen experiment
records retain their original hashes and provenance.
