# Reproducing the Qwen count verification

This experiment checks LocalMind's 38 saved Qwen counts and unchanged estimates
against fresh JavaScript and Python tokenization of the same fixture text.
No model weights, model inference, estimator fitting or chat templates are used.

## Recorded result

The [generated report](../results/2026-10-07-qwen-verification/run-01/REPORT.md)
contains the per-sample table. All 38 saved counts matched both fresh counts;
all 38 JS/Python token-ID sequences matched exactly. This validates this fixture
set under the pinned configuration, not unseen-text generalization.

## Pinned inputs

- LocalMind commit: `b39f0bc145a0c0926ba22247ee31cd369e0445b6`.
- Tokenizer repository: `onnx-community/Qwen3.5-4B-ONNX-OPT`, from LocalMind's
  `qwen35-4b` model mapping.
- Hugging Face revision: `57b13b4dce7be073be0df3eaf1c842a6bbb2e0a7`.
- JavaScript: `@huggingface/tokenizers` 0.2.0; dependencies in `package-lock.json`.
- Python: `tokenizers` 0.23.2; environment in `requirements.lock.txt`.
- Observed runtimes: Node v25.2.1 and Python 3.13.11 on macOS arm64.
- Asset hashes and URLs: [tokenizer lock](../config/qwen-tokenizer.lock.json).
- LocalMind file hashes: [baseline provenance](../results/2026-10-04-localmind-baseline/run.json).

The fixture file identifies the library and measurement date, but not its library
version or exact Hugging Face revision. The available HF revision predates that
date. Count agreement establishes reproduction on these samples; it does not
prove byte-identical historical assets. HF metadata and commit-history snapshots
are preserved alongside the run directory.

## Setup and execution

Run these commands from the `tokenizer-study/` project root. The recorded machine
already has the LocalMind checkout and environments; cloning and environment
creation are only needed on a fresh checkout.

```bash
mkdir -p external
git clone https://github.com/NakliTechie/LocalMind.git external/LocalMind
git -C external/LocalMind checkout --detach b39f0bc145a0c0926ba22247ee31cd369e0445b6
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm ci --ignore-scripts --no-audit --no-fund
```

One command runs the verification after setup:

```bash
.venv/bin/python scripts/verify_qwen.py --output results/qwen-reproduction-02
```

Use a new output directory for every run. The script refuses to overwrite an
existing run. It downloads missing locked tokenizer assets with curl, verifies
checksums, validates the upstream source, runs the two tokenizer implementations,
compares complete ID sequences, and saves a report and terminal output. Assets
are cached in `.cache/` and excluded from Git. No Hugging Face credentials were
required for this run.

Both libraries receive `add_special_tokens=False` (JavaScript spelling:
`add_special_tokens: false`). We do not strip tokens from the input text. The
tokenizer has no configured padding, truncation or nonzero BPE dropout; the
verification checks those assumptions. The original fixture comment uses the
spelling `addSpecialTokens`; our installed JS API uses the snake-case option.

An exit code of 0 means the saved counts, fresh counts and ID comparisons agree.
It does **not** mean predictions are exact: the estimator errors are measured
and reported separately. Exit code 2 means a reference/count/ID disagreement;
exit code 1 means execution failed. Failed runs are preserved for investigation.

## Output files

| File | Contents |
| --- | --- |
| `REPORT.md` | Readable, generated summary and full comparison table |
| `comparison.csv` / `comparison.json` | Saved count, both fresh counts, estimate, old estimate, errors and text measurements |
| `javascript.json` | Fixture text, JS token IDs, estimates and Node/library versions |
| `python-ids.json` | Independently encoded Python token IDs |
| `summary.json` | Metrics and any reference disagreements |
| `run.json` | Asset pins, runtime versions, dependency versions and script/config hashes |
| `terminal-output.txt` / `javascript-stderr.txt` | Captured execution output |
| `status.json` | Start/end status and exit code |

Fixture text is attributed under the original MIT licence in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The HF conversion repository
does not provide an explicit licence file in its listed assets; we record that
gap and do not redistribute its tokenizer files in this repository.

The initial metadata-fetch attempt with system Python failed local certificate
validation. The retry used curl with TLS verification enabled and succeeded.
No verification bypass was used. Our saved fetch script uses curl for the same
reason. No random sampling occurs in this experiment.
