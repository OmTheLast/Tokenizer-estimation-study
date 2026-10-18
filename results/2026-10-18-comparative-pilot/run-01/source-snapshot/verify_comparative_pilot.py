"""Separate arithmetic verification; does not import the analysis or NumPy."""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def verify_summary(record, pairs):
    ratios = sorted(Fraction(a, b) for a, b in pairs)
    n = len(ratios)

    def quantile(p):
        position = (n - 1) * p
        low = position.numerator // position.denominator
        high = min(low + 1, n - 1)
        return float(ratios[low] + (position - low) * (ratios[high] - ratios[low]))

    values = {"n": n, "geometric_mean_ratio": math.exp(math.fsum(math.log(float(v)) for v in ratios) / n),
              "median_ratio": quantile(Fraction(1, 2)), "p10_ratio": quantile(Fraction(1, 10)),
              "p90_ratio": quantile(Fraction(9, 10)), "min_ratio": float(ratios[0]), "max_ratio": float(ratios[-1]),
              "fraction_less": sum(v < 1 for v in ratios) / n, "fraction_equal": sum(v == 1 for v in ratios) / n,
              "fraction_more": sum(v > 1 for v in ratios) / n}
    for key, expected in values.items():
        assert math.isclose(record[key], expected, rel_tol=1e-12, abs_tol=1e-12), (key, record, expected)


def main(run, inventory_dir):
    output = run / "independent-validation.json"
    if output.exists():
        raise FileExistsError(output)
    plan = json.loads((ROOT / "config/comparative-pilot-v1.json").read_text())
    source = ROOT / plan["input"]
    assert digest(source) == plan["input_sha256"]
    pilot = json.loads((ROOT / plan["pilot_config"]).read_text())
    selection_path = ROOT / "config/flores-pilot-sample.json"
    selection = json.loads(selection_path.read_text())
    assert selection["plan_sha256"] == digest(ROOT / plan["pilot_config"])
    ids = sorted(selection["ids_in_selection_order"])
    models = plan["models"]
    languages = [item["code"] for item in pilot["languages"]]
    rows = pq.read_table(source).to_pylist()
    table = {(r["model_key"], r["language"], r["sentence_id"]): r for r in rows}
    assert len(table) == len(rows) == 9000
    expected_keys = {(m, l, s) for m in models for l in languages for s in ids}
    assert set(table) == expected_keys
    assert all(r["token_count"] > 0 for r in rows)
    count = lambda m, l, s: table[m,l,s]["token_count"]
    for l in languages:
        for s in ids:
            assert len({table[m,l,s]["text_sha256"] for m in models}) == 1
    cube = json.loads((run / "count-data.json").read_text())
    assert cube["models"] == models and cube["languages"] == languages and cube["aligned_sentence_ids"] == ids
    for mi,m in enumerate(models):
        for li,l in enumerate(languages):
            assert cube["content_counts"][mi][li] == [count(m,l,s) for s in ids]
    results = json.loads((run / "comparisons.json").read_text())
    paired = results["paired_tokenizers"]
    translations = results["aligned_translations"]
    assert len(paired) == 475 and len(translations) == 90
    assert {(r["numerator"],r["denominator"],r["language"]) for r in paired} == {(a,b,l) for a in models for b in models for l in languages+["ALL"]}
    assert {(r["tokenizer"],r["numerator_language"]) for r in translations} == {(m,l) for m in models for l in languages}
    for r in paired:
        langs = languages if r["language"] == "ALL" else [r["language"]]
        verify_summary(r, [(count(r["numerator"],l,s),count(r["denominator"],l,s)) for l in langs for s in ids])
    for r in translations:
        assert r["denominator_language"] == "eng_Latn"
        verify_summary(r, [(count(r["tokenizer"],r["numerator_language"],s),count(r["tokenizer"],"eng_Latn",s)) for s in ids])
    inventory = json.loads((inventory_dir / "inventory.json").read_text())
    verified_files = 0
    for r in inventory["records"]:
        lock_path = ROOT/r["lock_file"]
        assert digest(lock_path) == plan["tokenizer_locks"][lock_path.name]
        lock = json.loads(lock_path.read_text())
        cache = ROOT/lock["cache_directory"]
        assert r["assets_verified"] == [{k:a[k] for k in ("filename","sha256","bytes","url")} for a in lock["assets"]]
        for asset in lock["assets"]:
            assert digest(cache/asset["filename"]) == asset["sha256"]
            assert (cache/asset["filename"]).stat().st_size == asset["bytes"]
            verified_files += 1
        raw = json.loads((cache/"tokenizer.json").read_text())
        config = json.loads((cache/"tokenizer_config.json").read_text())
        assert raw["model"]["type"] == r["algorithm_type"]
        assert r["model_key"] == lock["model_key"] and r["revision"] == lock["revision"] and r["repository"] == lock["repository"]
        assert all(table[r["model_key"],l,s]["tokenizer_revision"] == r["revision"] for l in languages for s in ids)
        vocab = raw["model"]["vocab"]
        vocabulary = set(vocab) if isinstance(vocab,dict) else {v[0] for v in vocab}
        added = raw.get("added_tokens",[])
        assert r["base_vocab_entries"] == len(vocab)
        assert r["effective_vocab_entries"] == len(vocabulary | {v["content"] for v in added})
        assert r["added_token_records"] == len(added)
        assert r["added_strings_already_in_base"] == sum(v["content"] in vocabulary for v in added)
        assert r["added_token_records_marked_special"] == sum(v["special"] for v in added)
        assert r["merge_rules"] == len(raw["model"].get("merges",[]))
        assert r["chat_template_present"] == bool(config.get("chat_template"))
        assert not r["pilot_add_special_tokens"]
        for k,v in r["wrapper_settings"].items():
            assert config[k] == v
        for component, expected in r["component_fingerprints"].items():
            value = raw["model"].get(component) if component in ("vocab","merges") else raw.get(component)
            assert canonical_hash(value) == expected
        pipeline={k:raw.get(k) for k in ("model","added_tokens","normalizer","pre_tokenizer","post_processor","decoder","truncation","padding")}
        assert canonical_hash(pipeline)==r["pipeline_fingerprint"]
    for pair in inventory["pair_checks"]:
        a=next(r for r in inventory["records"] if r["model_key"]==pair["a"])
        b=next(r for r in inventory["records"] if r["model_key"]==pair["b"])
        assert pair["same_pipeline_fingerprint"] == (a["pipeline_fingerprint"]==b["pipeline_fingerprint"])
        assert pair["equal_components"] == [k for k,v in a["component_fingerprints"].items() if v==b["component_fingerprints"][k]]
    result={"status":"passed","summary_groups_verified":565,"summary_values_verified":5650,"published_counts_verified":9000,
            "frozen_selection_and_complete_pairing_verified":True,"inventory_asset_files_verified":verified_files,
            "inventory_profiles_verified":5,"inventory_pair_checks_verified":10,
            "arithmetic":"Python math.fsum/log and Fraction-based quantiles; no analysis imports or NumPy.",
            "input_sha256":digest(source),"selection_sha256":digest(selection_path),"verifier_sha256":digest(Path(__file__)),
            "compared_result_sha256":{p.name:digest(p) for p in [run/"comparisons.json",run/"count-data.json",inventory_dir/"inventory.json"]},
            "limits":"Verifies saved counts, grouping, arithmetic and asset metadata. Does not re-tokenize source text, validate lineage or establish population generalization."}
    output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--run",required=True)
    parser.add_argument("--inventory",required=True)
    args=parser.parse_args()
    run=(ROOT/args.run).resolve()
    inventory=(ROOT/args.inventory).resolve()
    if not run.is_relative_to(ROOT/"results") or not inventory.is_relative_to(ROOT/"results"):
        parser.error("Paths must be inside results/")
    main(run,inventory)
