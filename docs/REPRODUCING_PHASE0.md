# Reproducing all-profile verification and the Python port

Use the existing Node and Python setup described in
[REPRODUCING_QWEN.md](REPRODUCING_QWEN.md). The same dependency locks apply.
Run from the project root; use new output directories to preserve earlier runs.

```bash
.venv/bin/python scripts/verify_all_profiles.py --output results/phase0-reproduction-02
.venv/bin/python scripts/diagnose_special_tokens.py --output results/specials-reproduction-02
```

The first command is expected to exit **2** with the current frozen fixtures:
76 LFM/MiniCPM saved reference counts differ from explicitly content-only counts.
This is a preserved reference discrepancy, not an execution crash or a Python
port failure. Run the diagnostic as a separate command even when the first exits
2. The diagnostic is expected to exit **0** and show that special-enabled counts
reproduce all saved values. Do not change the fixtures merely to make the first
command pass.

Both scripts download only missing, checksum-locked assets; no model weights are
needed. Source revisions, library versions, counts and complete token-ID sequences
are recorded. `scripts/pin_remaining_tokenizers.py` was used to establish the
additional locks; regular reproduction uses those saved locks directly.

## Tokenizer sources

| Profile | Repository | Revision |
| --- | --- | --- |
| Qwen | onnx-community/Qwen3.5-4B-ONNX-OPT | 57b13b4dce7be073be0df3eaf1c842a6bbb2e0a7 |
| Bonsai | onnx-community/Ternary-Bonsai-4B-ONNX | 9d085aaf786063cadb648fff1725c2c36fd28ade |
| LFM | LiquidAI/LFM2.5-1.2B-Instruct-ONNX | 10f72e70abf67ac0fd7ebf15bc5854726891d864 |
| Gemma | onnx-community/gemma-4-E2B-it-ONNX | 9f4bef82ea6e296bc69f8a2f5939f73af81b07a6 |
| MiniCPM | openbmb/MiniCPM5-2B | 12a3808a956f869c767195e9266b59c4d21d92e2 |

All were fetched anonymously. LocalMind's MiniCPM entry points to GGUF files;
the first-party parent JSON tokenizer is used here to check the JSON-based fixture
claim. The chosen MiniCPM revision is the latest one listed before 2026-09-24,
not its newer main revision. These choices are independent of observed counts.
No exact historical HF or tokenizer-library revision is recorded in the fixtures.

See the individual `config/*-tokenizer.lock.json` files for checksums, provenance
and model-card licence metadata. Assets are cached locally and excluded from
Git. The LFM licence text is also preserved in that asset cache.

## Using the Python estimator

From the project root:

```python
from scripts.localmind_estimator import LocalMindEstimator

estimator = LocalMindEstimator()
prediction = estimator.count_tokens("Hello, world!", "qwen35-4b")
print(prediction)
```

`config/localmind-profiles.json` contains unchanged values extracted from pinned
LocalMind source, not newly fitted weights. An unknown model key uses the original
unknown profile. Strings and `None` are supported. Arbitrary Python object
coercion is intentionally unsupported.

The port uses explicit left-to-right floating-point addition because a different
summation algorithm can alter a value just around a final rounding boundary. It
also handles explicit UTF-16 surrogate pairs consistently with JavaScript.

## Records and interpretation

- The original [content-only run](../results/2026-10-07-all-profiles/run-01/REPORT.md)
  contains all comparisons, including failures of the saved-count contract.
- The [diagnostic report](../results/2026-10-07-all-profiles/special-token-diagnostic-01/REPORT.md)
  separates verified special-token behavior from the inferred historical cause.
- The [phase-0 review](PHASE0_RESULTS.md) combines both findings.

Rebuild that review from the preserved original summaries with:

```bash
.venv/bin/python scripts/write_phase0_report.py
```

All scripts were authored with Codex assistance. LocalMind-derived code, profiles
and fixture texts retain attribution in `THIRD_PARTY_NOTICES.md`. The upstream
source and previous Qwen outputs were not changed.
