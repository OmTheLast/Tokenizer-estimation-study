"""Inspect pinned local tokenizer assets without publishing vocabularies."""
import argparse
import hashlib
import json
from pathlib import Path

from tokenizers import Tokenizer
import tokenizers

ROOT = Path(__file__).resolve().parents[1]


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def compact(value):
    if isinstance(value, str) and len(value) > 500:
        return {"omitted_string_characters": len(value), "sha256": hashlib.sha256(value.encode()).hexdigest()}
    if isinstance(value, dict):
        return {k: compact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [compact(v) for v in value]
    return value


def stage_types(value):
    if value is None:
        return "None"
    children = value.get("normalizers", value.get("pretokenizers", value.get("decoders", value.get("processors", []))))
    if children:
        return value["type"] + "(" + ", ".join(stage_types(c) for c in children) + ")"
    return value.get("type", "Unspecified")


def main(output):
    plan_path = ROOT / "config/comparative-pilot-v1.json"
    plan = json.loads(plan_path.read_text())
    records = []
    for filename, expected in plan["tokenizer_locks"].items():
        lock_path = ROOT / "config" / filename
        assert file_sha(lock_path) == expected
        lock = json.loads(lock_path.read_text())
        cache = ROOT / lock["cache_directory"]
        checked = []
        for asset in lock["assets"]:
            path = cache / asset["filename"]
            assert file_sha(path) == asset["sha256"], path
            assert path.stat().st_size == asset["bytes"], path
            checked.append({k: asset[k] for k in ("filename", "sha256", "bytes", "url")})
        raw = json.loads((cache / "tokenizer.json").read_text())
        config = json.loads((cache / "tokenizer_config.json").read_text())
        model = raw["model"]
        vocab = model["vocab"]
        vocab_strings = set(vocab) if isinstance(vocab, dict) else {item[0] for item in vocab}
        added = raw.get("added_tokens", [])
        combined = vocab_strings | {item["content"] for item in added}
        runtime = Tokenizer.from_file(str(cache / "tokenizer.json"))
        assert runtime.get_vocab_size(with_added_tokens=False) == len(vocab)
        assert runtime.get_vocab_size(with_added_tokens=True) == len(combined)
        assert len(vocab_strings) == len(vocab)
        stages = ["normalizer", "pre_tokenizer", "post_processor", "decoder"]
        component_hashes = {k: fingerprint(raw.get(k)) for k in ["model", "added_tokens", *stages]}
        component_hashes["vocab"] = fingerprint(vocab)
        component_hashes["merges"] = fingerprint(model.get("merges"))
        pipeline = {k: raw.get(k) for k in ["model", "added_tokens", *stages, "truncation", "padding"]}
        records.append({
            "model_key": lock["model_key"], "repository": lock["repository"], "revision": lock["revision"],
            "lock_file": str(lock_path.relative_to(ROOT)), "assets_verified": checked,
            "algorithm_type": model["type"], "model_options": compact({k: v for k, v in model.items() if k not in ("vocab", "merges")}),
            "base_vocab_entries": len(vocab), "added_token_records": len(added),
            "added_token_records_marked_special": sum(a["special"] for a in added),
            "added_strings_already_in_base": sum(a["content"] in vocab_strings for a in added),
            "effective_vocab_entries": len(combined), "merge_rules": len(model.get("merges", [])),
            "stages": {k: {"types": stage_types(raw.get(k)), "configuration": compact(raw.get(k))} for k in stages},
            "wrapper_settings": {k: compact(config[k]) for k in ["tokenizer_class", "add_bos_token", "add_eos_token", "clean_up_tokenization_spaces", "split_special_tokens"] if k in config},
            "chat_template_present": bool(config.get("chat_template")),
            "pilot_add_special_tokens": lock["add_special_tokens"],
            "component_fingerprints": component_hashes, "pipeline_fingerprint": fingerprint(pipeline),
            "lineage_status": "Not established by this local asset inspection; repository identity is not a genealogical family assignment.",
        })
    records.sort(key=lambda r: plan["models"].index(r["model_key"]))
    pair_checks = []
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            pair_checks.append({"a": a["model_key"], "b": b["model_key"],
                                "same_algorithm_class": a["algorithm_type"] == b["algorithm_type"],
                                "same_pipeline_fingerprint": a["pipeline_fingerprint"] == b["pipeline_fingerprint"],
                                "equal_components": [k for k, v in a["component_fingerprints"].items() if v == b["component_fingerprints"][k]]})
    output.mkdir(parents=True, exist_ok=False)
    result = {"plan_sha256": file_sha(plan_path), "script_sha256": file_sha(Path(__file__)),
              "tokenizers_version": tokenizers.__version__, "records": records, "pair_checks": pair_checks,
              "checks": {"assets_verified": sum(len(r["assets_verified"]) for r in records), "runtime_vocab_checks": 10},
              "limitations": "Asset fingerprints describe serialized configuration, not lineage or runtime equivalence. Missing wrapper fields are unspecified, not false. Special-token settings do not describe full chat-template overhead."}
    (output / "inventory.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    report = ["# Inventory of the five pinned tokenizer profiles", "", "Generated from cached, hash-verified assets; no new tokenizer download or text encoding.", "",
              "| Profile | Algorithm in JSON | Base vocabulary | Effective vocabulary | Added records marked special | Merge rules |",
              "| --- | --- | ---: | ---: | ---: | ---: |"]
    for label, r in zip(plan["labels"], records):
        report.append(f"| {label} | {r['algorithm_type']} | {r['base_vocab_entries']:,} | {r['effective_vocab_entries']:,} | {r['added_token_records_marked_special']:,} | {r['merge_rules']:,} |")
    report += ["", "Base vocabulary counts entries in the tokenizer model. Effective vocabulary counts the union",
               "of base and added-token strings; an added record can refer to an existing base entry.",
               "Special-token records are not tokens automatically appended to every input.",
               "*MiniCPM is the pinned HF JSON asset; GGUF/browser equivalence is unverified.", "",
               "## Processing stages"]
    for label, r in zip(plan["labels"], records):
        report += ["", f"### {label}", "", f"Source: `{r['repository']}` at `{r['revision']}`.", ""]
        for a in r["assets_verified"]:
            report.append(f"- [{a['filename']}]({a['url']}): `{a['sha256']}`")
        report += ["", *[f"- {k}: {r['stages'][k]['types']}" for k in stages],
                   f"- Model options: `{json.dumps(r['model_options'], ensure_ascii=False)}`",
                   f"- Wrapper settings explicitly present: `{json.dumps(r['wrapper_settings'])}`",
                   f"- Chat template present: {r['chat_template_present']}; pilot inserts special tokens: {r['pilot_add_special_tokens']}."]
    classes = sorted({r["algorithm_type"] for r in records})
    report += ["", "## What can be called a family here?", "", f"Observed algorithm classes: {', '.join(classes)}.",
               f"Distinct serialized pipeline fingerprints: {len({r['pipeline_fingerprint'] for r in records})} of 5.",
               "These are separate profiles, not five proven historical families. Identical algorithm labels",
               "do not mean identical vocabulary, preprocessing or counts. The JSON report lists component",
               "equalities for all ten unordered pairs; matching null components are not lineage evidence.",
               "A cross-algorithm comparison needs additional representatives if only one class is present.", "",
               "## Verification and limits", "", f"Verified {result['checks']['assets_verified']} files against existing locks and checked base/effective vocabulary",
               "sizes against the pinned tokenizer runtime. Full configurations for processing stages (with",
               "very large strings represented by length and hash) and component fingerprints are in",
               "[inventory.json](inventory.json). Vocabularies and third-party asset files are not republished.",
               result["limitations"], ""]
    (output / "REPORT.md").write_text("\n".join(report))
    print(json.dumps({"algorithms": classes, "profiles": [{k: r[k] for k in ("model_key", "base_vocab_entries", "effective_vocab_entries")} for r in records], "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = (ROOT / args.output).resolve()
    if not destination.is_relative_to(ROOT / "results"):
        parser.error("Output must be inside results/")
    main(destination)
