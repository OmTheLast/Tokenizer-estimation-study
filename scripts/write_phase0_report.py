"""Generate the readable phase-0 review from preserved machine-generated results."""
import json
from fetch_tokenizer import ROOT

base = ROOT / "results/2026-10-07-all-profiles"
main = json.loads((base / "run-01/summary.json").read_text())
diagnostic = json.loads((base / "special-token-diagnostic-01/summary.json").read_text())
parity = main["estimator_parity"]
special_matches = sum(s["saved_matches_true"] for s in diagnostic.values())
if main["rows"] != 190 or main["failures"] or parity["mismatches"] or special_matches != 190:
    raise ValueError("Expected complete, diagnosed phase-0 results")
names = {"qwen35-4b": "Qwen", "bonsai-ternary-4b": "Bonsai", "lfm2-1.2b": "LFM",
         "gemma4-e2b": "Gemma", "minicpm5-2b-gguf": "MiniCPM (HF JSON)"}
lines = [
    "# Phase 0: verified tokenizers, Python port, and a reference-count discrepancy",
    "", "Recorded 2026-10-07.", "",
    f"We completed {main['rows']} fresh tokenizer comparisons across five profiles and ported the unchanged estimator to Python. JavaScript and Python produced identical token-ID sequences in all {main['id_matches']} comparisons, and the Python estimator matched all {main['estimator_matches']} original JavaScript predictions.", "",
    f"The saved fixture counts did not all mean what their comment said: {main['saved_js_python_matches']} matched content-only counts, while {main['disagreement_rows']} were one token higher. The separate diagnostic reproduced all {special_matches} saved counts with special tokens enabled.", "",
    "## What we found", "",
    "| Profile | Saved = fresh content-only | Saved = special-enabled | Extra token when specials enabled |",
    "| --- | ---: | ---: | --- |",
]
for key, s in main["profiles"].items():
    d = diagnostic[key]
    prefix = ", ".join(f"`{p['token']}` (ID {p['id']})" for p in d["prefix"]) or "none"
    lines.append(f"| {names[key]} | {s['saved_python_matches']}/{s['samples']} | {d['saved_matches_true']}/{d['samples']} | {prefix} |")
lines.extend([
    "", "For LFM and MiniCPM, the special-enabled sequence is exactly the beginning-of-sequence token followed by the content-only sequence, for every fixture. This is not a disagreement between the JS and Python tokenizers.", "",
    "The original fixture header says `addSpecialTokens: false`. The installed JS library (0.2.0) instead expects `add_special_tokens: false`. We deliberately tested both spellings: the camelCase spelling behaves like the default and like specials enabled on every example. This reproduces a plausible cause of the extra token, but the original generator and library version were not recorded, so its exact historical cause remains an inference.", "",
    "The original fixtures and estimator weights remain unchanged. The initial content-only verification still has exit code 2 and its mismatch rows are preserved. The follow-up diagnostic has exit code 0 because it explains the discrepancy; it does not retroactively make the content-only comparison pass.", "",
    "## Prediction errors against fresh content-only counts", "",
    "A negative error is an underestimate; a positive error is an overestimate. Median absolute error describes the typical error magnitude without cancellation between signs. These are familiar fixtures, not held-out test results.", "",
    "| Profile | Worst under | Worst over | Median absolute error | Within +/-20% |",
    "| --- | ---: | ---: | ---: | ---: |",
])
for key, s in main["profiles"].items():
    lines.append(f"| {names[key]} | {s['min_error_percent']:+.2f}% | {s['max_error_percent']:+.2f}% | {s['median_absolute_error_percent']:.2f}% | {s['within_20_percent_count']}/{s['samples']} |")
lines.extend([
    "", "## Python estimator port", "",
    "The port reads the original weights and model-to-profile mapping extracted from the hash-verified LocalMind source. It preserves Unicode classification, unknown-model fallback, per-character addition order and final rounding. No weights were fitted. The research interface supports strings and None; it deliberately does not reproduce JavaScript's arbitrary object-to-string coercion.", "",
    f"Checks: {parity['fixture_checks']} fixture/alias combinations, {parity['edge_checks']} edge combinations and {parity['classification_checks']} class-boundary cases, with {len(parity['mismatches'])} mismatches. Cases include empty/null input, emoji, combining marks, surrogate pairs, lone surrogates, boundary characters, repeated strings and unknown-model fallback.", "",
    "## Limits and next action", "",
    "- Original HF revisions and tokenizer-library versions were not recorded. We pin available revisions that predate the fixture measurement and preserve asset hashes; matching results do not prove historical byte identity.",
    "- MiniCPM verification uses the first-party parent HF JSON tokenizer. LocalMind uses a GGUF runtime, whose tokenizer equivalence has not been tested here.",
    "- This checks raw content, with explicit special-token settings. Complete chat formatting, response reservations and browser performance remain outside this experiment.",
    "- Phase 0's reproduction and port checks are ready for review, with the discrepancy documented. Next is phase 1: collect pinned multilingual ground-truth counts with an explicit content-only contract and separate special-token accounting. Freeze dataset splits before any new fitting. The broader unseen-text estimator evaluation comes afterward.", "",
    "## Evidence", "",
    "- [All-profile terminal output](../results/2026-10-07-all-profiles/run-01/terminal-output.txt)",
    "- [All 190 rows](../results/2026-10-07-all-profiles/run-01/comparison.csv)",
    "- [The 76 original reference disagreements](../results/2026-10-07-all-profiles/run-01/disagreements.json)",
    "- [Special-token diagnostic](../results/2026-10-07-all-profiles/special-token-diagnostic-01/REPORT.md)",
    "- [Python estimator parity](../results/2026-10-07-all-profiles/run-01/estimator-parity.json)",
    "- [How to reproduce and use the Python port](REPRODUCING_PHASE0.md)", "",
    "Generated by `scripts/write_phase0_report.py` from the preserved result summaries. No model training or publication occurred in this round.", "",
])
target = ROOT / "docs/PHASE0_RESULTS.md"
target.write_text("\n".join(lines))
print(target.relative_to(ROOT))
