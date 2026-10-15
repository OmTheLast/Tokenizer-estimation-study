"""Compare frozen estimates, saved counts, and fresh JS/Python token IDs.

Run from any directory with the project's pinned Python environment.
Results are written to a NEW output directory; earlier runs are never replaced.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import traceback

import tokenizers
from fetch_tokenizer import ROOT, LOCK, fetch_assets, sha256


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def evaluate(out, log):
    lock, directory = fetch_assets()
    expected_python = "0.23.2"
    if tokenizers.__version__ != expected_python:
        raise ValueError(f"Expected tokenizers {expected_python}, got {tokenizers.__version__}")
    with (out / "javascript.json").open("w") as output, (out / "javascript-stderr.txt").open("w") as errors:
        subprocess.run(["node", str(ROOT / "scripts/count_qwen.mjs")], cwd=ROOT,
                       stdout=output, stderr=errors, check=True)
    js = json.loads((out / "javascript.json").read_text())
    if js["js_tokenizers_version"] != "0.2.0":
        raise ValueError("Unexpected JavaScript tokenizer version")
    tokenizer = tokenizers.Tokenizer.from_file(str(directory / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    rows, python_ids = [], []
    for sample in js["rows"]:
        ids = tokenizer.encode(sample["text"], add_special_tokens=False).ids
        actual = len(ids)
        if actual == 0:
            raise ValueError(f"Unexpected empty encoding for {sample['name']}")
        row = {key: value for key, value in sample.items() if key not in {"text", "js_ids"}}
        row.update(
            python_count=actual,
            saved_minus_python=sample["saved_count"] - actual,
            js_minus_python=sample["js_count"] - actual,
            ids_equal=ids == sample["js_ids"],
            error_percent=100 * (sample["estimate"] - actual) / actual,
            old_error_percent=100 * (sample["old_estimate"] - actual) / actual,
        )
        rows.append(row)
        python_ids.append({"name": sample["name"], "ids": ids})
    save_json(out / "python-ids.json", python_ids)
    save_json(out / "comparison.json", rows)
    with (out / "comparison.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def metrics(field):
        errors = [r[field] for r in rows]
        return {
            "minimum_error_percent": min(errors),
            "minimum_error_sample": min(rows, key=lambda r: r[field])["name"],
            "maximum_error_percent": max(errors),
            "maximum_error_sample": max(rows, key=lambda r: r[field])["name"],
            "median_absolute_error_percent": statistics.median(abs(e) for e in errors),
            "mean_absolute_error_percent": statistics.mean(abs(e) for e in errors),
            "within_20_percent_count": sum(abs(e) <= 20 for e in errors),
            "undercount_count": sum(e < 0 for e in errors),
            "overcount_count": sum(e > 0 for e in errors),
            "exact_count": sum(e == 0 for e in errors),
        }

    n = len(rows)
    saved_matches = sum(r["saved_count"] == r["python_count"] == r["js_count"] for r in rows)
    id_matches = sum(r["ids_equal"] for r in rows)
    summary = {
        "samples": n, "saved_js_python_count_matches": saved_matches,
        "js_python_token_id_matches": id_matches,
        "estimator": metrics("error_percent"), "old_heuristic": metrics("old_error_percent"),
        "reference_disagreements": [r for r in rows if r["saved_minus_python"] or r["js_minus_python"] or not r["ids_equal"]],
        "scope": "Qwen content counts on existing LocalMind fixtures; no new fitting or held-out evaluation.",
        "historical_provenance": lock["historical_provenance"],
    }
    save_json(out / "summary.json", summary)
    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_lock": lock, "localmind_commit": js["localmind_commit"],
        "python_version": platform.python_version(), "python_tokenizers_version": tokenizers.__version__,
        "node_version": js["node_version"], "js_tokenizers_version": js["js_tokenizers_version"],
        "platform": platform.platform(), "add_special_tokens": False,
        "truncation": False, "padding": False, "chat_template_applied": False,
        "python_dependencies": subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines(),
        "script_and_config_sha256": {name: sha256(ROOT / name) for name in [
            "scripts/fetch_tokenizer.py", "scripts/count_qwen.mjs", "scripts/verify_qwen.py",
            "config/qwen-tokenizer.lock.json", "package-lock.json", "requirements.lock.txt",
        ]},
    }
    save_json(out / "run.json", metadata)
    e = summary["estimator"]
    log(f"Qwen verification: {n} fixtures")
    log(f"Saved counts = fresh JS counts = fresh Python counts: {saved_matches}/{n}")
    log(f"JS and Python token IDs identical: {id_matches}/{n}")
    log(f"Estimator worst under: {e['minimum_error_percent']:.2f}% ({e['minimum_error_sample']})")
    log(f"Estimator worst over: +{e['maximum_error_percent']:.2f}% ({e['maximum_error_sample']})")
    log(f"Estimator median absolute error: {e['median_absolute_error_percent']:.2f}%")
    log(f"Within +/-20%: {e['within_20_percent_count']}/{n}")
    log(f"Undercount / exact / overcount: {e['undercount_count']} / {e['exact_count']} / {e['overcount_count']}")
    log("Sample                              Saved    JS    Python  Estimate  Error")
    for row in rows:
        log(f"{row['name']:<35} {row['saved_count']:>5} {row['js_count']:>5} {row['python_count']:>7} {row['estimate']:>9} {row['error_percent']:>+7.2f}%")

    lines = ["# Qwen reference-count verification", "", summary["scope"], "",
             f"Saved and fresh counts match: **{saved_matches}/{n}**. JS/Python token-ID sequences match: **{id_matches}/{n}**.", "",
             f"Estimator errors range from {e['minimum_error_percent']:.2f}% to +{e['maximum_error_percent']:.2f}%; median absolute error is {e['median_absolute_error_percent']:.2f}%.", "",
             "| Sample | Saved | Fresh JS | Fresh Python | Estimate | Error |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(f"| {row['name']} | {row['saved_count']} | {row['js_count']} | {row['python_count']} | {row['estimate']} | {row['error_percent']:+.2f}% |")
    lines.extend(["", "## Reproducibility and limits", "", f"Tokenizer: `{lock['repository']}` at `{lock['revision']}`.", "",
                  lock["historical_provenance"], "", "Content only, with added special tokens disabled, no truncation, no padding and no chat template. Weights are unchanged. These are familiar fixtures, not held-out examples. No browser speed or memory conclusion follows from this check.", "",
                  "Generated by `scripts/verify_qwen.py`; see `run.json`, `summary.json`, `comparison.csv`, `javascript.json` and `python-ids.json` beside this file.", ""])
    (out / "REPORT.md").write_text("\n".join(lines))
    return 0 if saved_matches == n and id_matches == n else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New results directory, relative to project root")
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "results"):
        parser.error("Output must be inside this project's results directory")
    out.mkdir(parents=True, exist_ok=False)
    state = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(), "command": sys.argv}
    save_json(out / "status.json", state)
    with (out / "terminal-output.txt").open("w", buffering=1) as stream:
        def log(message):
            print(message, flush=True)
            print(message, file=stream, flush=True)
        try:
            code = evaluate(out, log)
        except Exception:
            log(traceback.format_exc())
            code = 1
        log(f"Exit code: {code}")
    state.update(status="passed" if code == 0 else "failed", exit_code=code,
                 completed_utc=datetime.now(timezone.utc).isoformat())
    save_json(out / "status.json", state)
    return code


if __name__ == "__main__":
    sys.exit(main())
