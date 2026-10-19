# Study milestones

| Date | Completed work | Evidence |
| --- | --- | --- |
| 2026-09-30 | Initial estimation study design | [Original plan](../references/tokenizer-study-plan-v2.md) |
| 2026-10-04 | LocalMind fixture baseline reproduced | [Phase-0 reproduction](REPRODUCING_PHASE0.md) |
| 2026-10-07 | Five tokenizer profiles verified; estimator port and special-token diagnostics completed | [Phase-0 results](PHASE0_RESULTS.md) |
| 2026-10-15 | Multilingual pilot: 9,000 measurements; error analysis completed | [Pilot](../results/2026-10-15-phase1-pilot/run-02/REPORT.md) |
| 2026-10-16 | Error-analysis figures and candidate fitting-data audit completed; fitting deferred | [Evidence guide](EVIDENCE_GUIDE.md) · [Audit](../results/2026-10-16-cjk-preflight/audit-02/REPORT.md) |
| 2026-10-18 | Scope expanded to comparative tokenizer behavior; configuration inventory and direct comparisons completed | [Comparative report](../results/2026-10-18-comparative-pilot/run-01/REPORT.md) |
| 2026-10-18 | Controlled text-type experiment added one Unigram profile; 1,128 encoding comparisons verified | [Text-type report](../results/2026-10-18-text-types/analysis-02/REPORT.md) |
| 2026-10-19 | Published technical corpus frozen: 100 samples, ten source/language groups, all quotas filled | [Collection report](../results/2026-10-19-published-corpus/REPORT.md) |
| 2026-10-19 | Published-text experiment: 840 encoding comparisons, 1,146 checked summaries, three graphs | [Results](../results/2026-10-19-published-experiment/REPORT.md) |

## Current findings

Counts vary across tokenizer configurations, languages and text types. JSON
formatting costs vary by profile and source; low counts do not guarantee exact
text reconstruction. All comparisons concern the pinned assets and sampled inputs.
They do not measure model-answer quality or establish causal algorithm effects.

## Remaining questions

Browser startup, memory, counting latency and complete-prompt budgeting remain
unmeasured. A browser benchmark is proposed; broader source and tokenizer coverage
would be needed for general conclusions. Coefficient fitting remains deferred.

Reports preserve failed checks, corrections, versions, source limitations and
reproduction commands. Frozen numeric results and experiment records are retained.

## DeepSeek extension — 2026-10-19

[Protocol](DEEPSEEK_EXTENSION_V1.md) specified before measurement. Official V3
and R1 assets share their BPE core but differ in two added-token entries and chat
templates. Both configurations will be measured on the existing frozen corpus;
separate marker probes test the known differences. No additional source sampling.
