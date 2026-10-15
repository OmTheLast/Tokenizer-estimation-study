"""Explain saved-count discrepancies without changing fixtures or estimator weights."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback

import tokenizers
from fetch_tokenizer import ROOT, sha256
from verify_all_profiles import LOCKS, fetch_locked, node_json, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "results"):
        parser.error("Output must be inside results/")
    out.mkdir(parents=True, exist_ok=False)
    save(out / "status.json", {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(), "command": sys.argv})
    summaries = {}
    code = 0
    with (out / "terminal-output.txt").open("w", buffering=1) as stream:
        def log(text):
            print(text, flush=True)
            print(text, file=stream, flush=True)
        try:
            if tokenizers.__version__ != "0.23.2":
                raise ValueError("Unexpected Python tokenizer version")
            if json.loads((ROOT / "node_modules/@huggingface/tokenizers/package.json").read_text())["version"] != "0.2.0":
                raise ValueError("Unexpected JS tokenizer version")
            for name in LOCKS:
                lock_path = ROOT / "config" / name
                lock = json.loads(lock_path.read_text())
                key = lock["model_key"]
                directory = fetch_locked(lock)
                js = node_json("probe_special_tokens.mjs", [str(lock_path)], out / f"{key}-js.json")
                native = tokenizers.Tokenizer.from_file(str(directory / "tokenizer.json"))
                native.no_padding()
                native.no_truncation()
                rows = []
                for s in js["rows"]:
                    false_ids = native.encode(s["text"], add_special_tokens=False).ids
                    true_ids = native.encode(s["text"], add_special_tokens=True).ids
                    prefix = [p["id"] for p in js["candidate_prefix"]]
                    rows.append({"name": s["name"], "saved_count": s["saved_count"],
                        "python_false_ids": false_ids, "python_true_ids": true_ids,
                        "saved_matches_false": s["saved_count"] == len(false_ids),
                        "saved_matches_true": s["saved_count"] == len(true_ids),
                        "false_ids_match_js": false_ids == s["false_ids"],
                        "true_ids_match_js": true_ids == s["true_ids"],
                        "js_camel_equals_default": s["camel_false_ids"] == s["default_ids"],
                        "js_camel_equals_true": s["camel_false_ids"] == s["true_ids"],
                        "true_is_prefix_plus_content": true_ids == prefix + false_ids,
                        "special_token_count_delta": len(true_ids) - len(false_ids)})
                del native
                save(out / f"{key}-python.json", rows)
                summary = {"samples": len(rows), "prefix": js["candidate_prefix"],
                           "special_token_count_deltas": sorted(set(r["special_token_count_delta"] for r in rows))}
                for field in ["saved_matches_false", "saved_matches_true", "false_ids_match_js", "true_ids_match_js", "js_camel_equals_default", "js_camel_equals_true", "true_is_prefix_plus_content"]:
                    summary[field] = sum(r[field] for r in rows)
                summaries[key] = summary
                log(f"{key}: saved matches content-only {summary['saved_matches_false']}/38, special-enabled {summary['saved_matches_true']}/38; extra prefix {summary['prefix']}")
                if not all(summary[field] == 38 for field in ["saved_matches_true", "false_ids_match_js", "true_ids_match_js", "js_camel_equals_default", "js_camel_equals_true", "true_is_prefix_plus_content"]):
                    code = 2
                save(out / "summary.json", summaries)
            files = ["scripts/diagnose_special_tokens.py", "scripts/probe_special_tokens.mjs", "scripts/localmind_source.mjs", "scripts/verify_all_profiles.py", "scripts/fetch_tokenizer.py", "package-lock.json", "requirements.lock.txt"] + [f"config/{name}" for name in LOCKS]
            save(out / "run.json", {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "python_version": platform.python_version(),
                 "python_tokenizers_version": tokenizers.__version__, "node_version": subprocess.check_output(["node", "--version"], text=True).strip(),
                 "js_tokenizers_version": "0.2.0", "script_and_config_sha256": {name: sha256(ROOT / name) for name in files},
                 "interpretation_limit": "Observed equivalence with these pinned assets/library versions. Original fixture generator and original library version are unavailable; exact historical cause is inferred, not proven."})
            lines = ["# Special-token discrepancy diagnosis", "", "All 190 saved counts match fresh special-enabled counts in JS and Python under the pinned setup. Content-only counts differ by one token for all LFM and MiniCPM fixtures.", "",
                     "| Profile | Saved = content only | Saved = special enabled | Added prefix |", "| --- | ---: | ---: | --- |"]
            for key, s in summaries.items():
                prefix = ", ".join(f"`{p['token']}` (ID {p['id']})" for p in s["prefix"]) or "none"
                lines.append(f"| {key} | {s['saved_matches_false']}/38 | {s['saved_matches_true']}/38 | {prefix} |")
            lines.extend(["", "The JS library's documented option is `add_special_tokens: false`. Passing `addSpecialTokens: false`, the spelling written in the fixture header, behaves exactly like the default and like `add_special_tokens: true` on every sample in this experiment.", "",
                          "For LFM, enabling specials prepends `<|startoftext|>` (ID 1); for MiniCPM, it prepends `<s>` (ID 0). All remaining IDs are identical to the content-only encoding. JS and Python agree on both modes for all 190 comparisons.", "",
                          "This reproduces a plausible mechanism for the extra token. It does not prove the original author's exact call or library version. Preserve the upstream fixtures and label their saved counts as special-enabled-compatible; use explicit content-only counts for the study. No estimator weights were changed.", "",
                          "The original all-profile run correctly exits 2 because the stated content-only reference contract failed in 76 rows. A successful diagnostic does not erase that failure or change the content-only benchmark.", ""])
            if code == 0:
                (out / "REPORT.md").write_text("\n".join(lines))
        except Exception:
            log(traceback.format_exc())
            code = 1
        log(f"Exit code: {code}")
    save(out / "status.json", {"status": "passed" if code == 0 else "failed", "exit_code": code,
         "completed_utc": datetime.now(timezone.utc).isoformat(), "command": sys.argv})
    return code


if __name__ == "__main__":
    sys.exit(main())
