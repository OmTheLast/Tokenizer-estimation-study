"""Run all five tokenizer checks plus independent Python estimator parity.

Requires the locked JS/Python dependencies and the pinned LocalMind checkout.
Writes a new result directory and preserves partial failures for investigation.
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
from fetch_tokenizer import ROOT, sha256
from localmind_estimator import LocalMindEstimator, token_class_index

LOCKS = ["qwen-tokenizer.lock.json", "bonsai-ternary-4b-tokenizer.lock.json",
         "lfm2-1.2b-tokenizer.lock.json", "gemma4-e2b-tokenizer.lock.json",
         "minicpm5-2b-gguf-tokenizer.lock.json"]


def save(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n")
    temp.replace(path)


def node_json(script, args, output):
    with output.open("w") as stream, output.with_suffix(".stderr.txt").open("w") as errors:
        subprocess.run(["node", str(ROOT / "scripts" / script), *args], cwd=ROOT,
                       stdout=stream, stderr=errors, check=True)
    return json.loads(output.read_text())


def fetch_locked(lock):
    directory = ROOT / lock["cache_directory"]
    directory.mkdir(parents=True, exist_ok=True)
    for asset in lock["assets"]:
        target = directory / asset["filename"]
        if not target.exists():
            temp = target.with_suffix(".download")
            subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "120", "-o", str(temp), asset["url"]], check=True)
            if sha256(temp) != asset["sha256"]:
                raise ValueError(f"Download checksum mismatch: {target}")
            temp.replace(target)
        if sha256(target) != asset["sha256"]:
            raise ValueError(f"Cache checksum mismatch: {target}")
    return directory


def stats(rows):
    errors = [r["error_percent_python_reference"] for r in rows]
    return {"samples": len(rows), "min_error_percent": min(errors), "max_error_percent": max(errors),
            "median_absolute_error_percent": statistics.median(abs(e) for e in errors),
            "within_20_percent_count": sum(abs(e) <= 20 for e in errors)}


def run(out, log):
    if tokenizers.__version__ != "0.23.2":
        raise ValueError("Expected Python tokenizers 0.23.2")
    cases = node_json("export_estimator_cases.mjs", [], out / "estimator-cases.json")
    profile_path = ROOT / "config/localmind-profiles.json"
    if profile_path.exists() and json.loads(profile_path.read_text()) != cases["profiles"]:
        raise ValueError("Extracted profiles differ from existing frozen profiles")
    save(profile_path, cases["profiles"])
    estimator = LocalMindEstimator()
    parity = {"fixture_checks": 0, "edge_checks": 0, "classification_checks": 0, "mismatches": []}
    for group, key in [(cases["fixtures"], "fixture_checks"), (cases["edge_cases"], "edge_checks")]:
        for sample in group:
            for model, expected in sample["estimates"].items():
                actual = estimator.count_tokens(sample["text"], model)
                parity[key] += 1
                if actual != expected:
                    parity["mismatches"].append({"sample": sample["name"], "model": model, "js": expected, "python": actual})
    for case in cases["classification"]:
        parity["classification_checks"] += 1
        actual = token_class_index(case["code_point"])
        if actual != case["class_index"]:
            parity["mismatches"].append({**case, "python_class_index": actual})
    # Exercise explicitly represented pairs as well as Python's single astral character.
    for model in [*cases["profiles"]["model_profiles"], "unknown-model"]:
        parity["edge_checks"] += 1
        if estimator.count_tokens("\ud83d\ude42", model) != estimator.count_tokens("🙂", model):
            parity["mismatches"].append({"sample": "explicit-python-surrogate-pair", "model": model})
    save(out / "estimator-parity.json", parity)
    log(f"Python estimator parity: {parity['fixture_checks']} fixture/alias checks, {parity['edge_checks']} edge checks, {parity['classification_checks']} class checks; {len(parity['mismatches'])} mismatches")
    all_rows, profiles, failures = [], {}, {}
    for filename in LOCKS:
        lock_path = ROOT / "config" / filename
        lock = json.loads(lock_path.read_text())
        key = lock["model_key"]
        directory = out / key
        directory.mkdir()
        try:
            assets = fetch_locked(lock)
            js = node_json("count_profile.mjs", [str(lock_path)], directory / "javascript.json")
            if js["js_tokenizers_version"] != "0.2.0":
                raise ValueError("Expected JS tokenizers 0.2.0")
            native = tokenizers.Tokenizer.from_file(str(assets / "tokenizer.json"))
            native.no_padding()
            native.no_truncation()
            rows, encoded = [], []
            for sample in js["rows"]:
                ids = native.encode(sample["text"], add_special_tokens=False).ids
                actual = len(ids)
                if actual == 0:
                    raise ValueError(f"Unexpected empty tokens: {sample['name']}")
                python_estimate = estimator.count_tokens(sample["text"], key)
                row = {"model_key": key, **{k: v for k, v in sample.items() if k not in {"text", "js_ids"}}}
                row.update(python_count=actual, python_estimate=python_estimate,
                           ids_equal=ids == sample["js_ids"], estimator_equal=python_estimate == sample["estimate"],
                           saved_js_match=sample["saved_count"] == sample["js_count"],
                           saved_python_match=sample["saved_count"] == actual,
                           error_percent_python_reference=100 * (sample["estimate"] - actual) / actual,
                           error_percent_js_reference=100 * (sample["estimate"] - sample["js_count"]) / sample["js_count"])
                rows.append(row)
                encoded.append({"name": sample["name"], "ids": ids})
            del native
            save(directory / "python-ids.json", encoded)
            save(directory / "comparison.json", rows)
            save(directory / "source-lock.json", lock)
            all_rows.extend(rows)
            result = {**stats(rows), "saved_js_matches": sum(r["saved_js_match"] for r in rows),
                      "saved_python_matches": sum(r["saved_python_match"] for r in rows),
                      "id_matches": sum(r["ids_equal"] for r in rows),
                      "estimator_matches": sum(r["estimator_equal"] for r in rows)}
            profiles[key] = result
            log(f"{key}: saved=JS {result['saved_js_matches']}/38; saved=Python {result['saved_python_matches']}/38; IDs {result['id_matches']}/38; estimator {result['estimator_matches']}/38; error {result['min_error_percent']:+.2f}% to {result['max_error_percent']:+.2f}%")
        except Exception:
            failures[key] = traceback.format_exc()
            (directory / "failure.txt").write_text(failures[key])
            log(f"{key}: FAILED — see {key}/failure.txt")
        save(out / "progress.json", {"completed_profiles": profiles, "failures": failures})

    if all_rows:
        with (out / "comparison.csv").open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(all_rows[0]))
            writer.writeheader()
            writer.writerows(all_rows)
    disagreements = [r for r in all_rows if not all(r[k] for k in ["ids_equal", "estimator_equal", "saved_js_match", "saved_python_match"])]
    save(out / "disagreements.json", disagreements)
    summary = {"profiles": profiles, "rows": len(all_rows), "expected_rows": 190,
               "saved_js_python_matches": sum(r['saved_js_match'] and r['saved_python_match'] for r in all_rows),
               "id_matches": sum(r["ids_equal"] for r in all_rows),
               "estimator_matches": sum(r["estimator_equal"] for r in all_rows),
               "estimator_parity": parity, "disagreement_rows": len(disagreements), "failures": failures}
    save(out / "summary.json", summary)
    files = ["scripts/verify_all_profiles.py", "scripts/count_profile.mjs", "scripts/localmind_source.mjs",
             "scripts/export_estimator_cases.mjs", "scripts/localmind_estimator.py", "scripts/fetch_tokenizer.py",
             "config/localmind-profiles.json", "package-lock.json", "requirements.lock.txt"] + [f"config/{n}" for n in LOCKS]
    save(out / "run.json", {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
         "localmind_commit": cases["localmind_commit"], "python_version": platform.python_version(),
         "python_tokenizers_version": tokenizers.__version__, "node_version": subprocess.check_output(["node", "--version"], text=True).strip(),
         "js_tokenizers_version": json.loads((ROOT / "node_modules/@huggingface/tokenizers/package.json").read_text())["version"],
         "platform": platform.platform(), "add_special_tokens": False, "truncation": False, "padding": False,
         "script_and_config_sha256": {name: sha256(ROOT / name) for name in files}})
    lines = ["# All-profile reference verification and Python estimator port", "",
             f"Completed {len(all_rows)}/190 sample/profile comparisons. Saved counts match both fresh implementations in {summary['saved_js_python_matches']} cases; full JS/Python token IDs match in {summary['id_matches']}. Python estimates match original JS estimates in {summary['estimator_matches']} cases.", "",
             "| Profile | Saved = JS | Saved = Python | IDs match | Estimator matches | Worst under | Worst over | Median absolute error |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key, s in profiles.items():
        lines.append(f"| {key} | {s['saved_js_matches']}/38 | {s['saved_python_matches']}/38 | {s['id_matches']}/38 | {s['estimator_matches']}/38 | {s['min_error_percent']:+.2f}% | {s['max_error_percent']:+.2f}% | {s['median_absolute_error_percent']:.2f}% |")
    lines.extend(["", "Errors above use the fresh Python tokenizer as reference. Inspect disagreements before interpreting metrics where implementations differ.", "",
                  f"Python estimator parity also checked {parity['fixture_checks']} fixture/alias combinations, {parity['edge_checks']} edge combinations, and {parity['classification_checks']} class boundaries: {len(parity['mismatches'])} mismatches.", "",
                  "## Limits", "", "Existing fixtures only; no fitting or held-out evaluation. Historical fixture asset/library versions were not recorded. Our runs pin their own assets and versions. MiniCPM uses the first-party parent JSON tokenizer, not the GGUF/wllama runtime. No browser benchmark, chat template or output allowance was tested.", "",
                  "See comparison.csv for every row, disagreements.json for mismatches, per-profile directories for both ID sequences, and run.json for provenance.", ""])
    if failures:
        lines.extend(["## Execution failures", "", *[f"- {key}: see `{key}/failure.txt`." for key in failures], ""])
    (out / "REPORT.md").write_text("\n".join(lines))
    log(f"Total: {summary['saved_js_python_matches']}/190 saved-count matches; {summary['id_matches']}/190 ID matches; {summary['estimator_matches']}/190 estimator matches")
    return 0 if len(all_rows) == 190 and not failures and not disagreements and not parity["mismatches"] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "results"):
        parser.error("Output must be inside results/")
    out.mkdir(parents=True, exist_ok=False)
    state = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(), "command": sys.argv}
    save(out / "status.json", state)
    with (out / "terminal-output.txt").open("w", buffering=1) as stream:
        def log(message):
            print(message, flush=True)
            print(message, file=stream, flush=True)
        try:
            code = run(out, log)
        except Exception:
            log(traceback.format_exc())
            code = 1
        log(f"Exit code: {code}")
    state.update(status="passed" if code == 0 else "failed", exit_code=code,
                 completed_utc=datetime.now(timezone.utc).isoformat())
    save(out / "status.json", state)
    return code


if __name__ == "__main__":
    sys.exit(main())
