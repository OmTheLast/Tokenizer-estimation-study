"""Authorized, pinned FLORES+ dev access and text-independent pilot sampling.

No tokens, credentials or dataset text are printed. Access errors are explicit;
there are no mirror fallbacks or automatic acceptance of dataset conditions.
"""
import hashlib
import json
from pathlib import Path

from huggingface_hub import get_token, hf_hub_download
from fetch_tokenizer import ROOT, sha256
from verify_all_profiles import save

PLAN = ROOT / "config/phase1-pilot.json"


def freeze(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f"Refusing to replace frozen input: {path.name}")
    else:
        save(path, value)


def load_pilot(log=print):
    plan = json.loads(PLAN.read_text())
    if plan["split"] != "dev":
        raise ValueError("This pilot may read dev only")
    token = get_token()
    by_language, sources = {}, []
    for language in plan["languages"]:
        code = language["code"]
        filename = f"dev/{code}.jsonl"
        try:
            path = Path(hf_hub_download(
                repo_id=plan["dataset"], repo_type="dataset", filename=filename,
                revision=plan["revision"], local_dir=ROOT / ".cache/flores_plus" / plan["revision"],
                token=token if token else False,
            ))
        except Exception as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            raise RuntimeError(f"Dataset access failed for {filename}: {type(error).__name__}, HTTP {status}. Review FLORES+ conditions with the configured HF account; no fallback was used.") from None
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        mapped = {}
        for record in records:
            if record.get("split", "dev") != "dev":
                raise ValueError("Unexpected non-dev record")
            record_id = str(record["id"])
            if record_id in mapped:
                raise ValueError(f"Duplicate ID in {code}: {record_id}")
            if not isinstance(record["text"], str) or not record["text"].strip():
                raise ValueError(f"Empty or invalid text in {code}: {record_id}")
            mapped[record_id] = record
        by_language[code] = mapped
        sources.append({"language": code, "filename": filename, "sha256": sha256(path), "records": len(records)})
        log(f"Fetched {code}: {len(records)} dev records (text kept in ignored cache)")
    dataset_lock = {"dataset": plan["dataset"], "revision": plan["revision"], "split": "dev",
                    "licence": "CC-BY-SA-4.0", "use": "Evaluation only; no training; no public redistribution of raw text or token IDs", "files": sources}
    freeze(ROOT / "config/flores-pilot.lock.json", dataset_lock)
    common = set.intersection(*(set(records) for records in by_language.values()))
    if len(common) < plan["sample_count"]:
        raise ValueError("Insufficient common parallel sentence IDs")
    rank = lambda record_id: hashlib.sha256(f"{plan['selection_salt']}|{record_id}".encode()).hexdigest()
    ids = sorted(common, key=lambda i: (rank(i), i))[:plan["sample_count"]]
    selection = {"plan_sha256": sha256(PLAN), "dataset_lock_sha256": sha256(ROOT / "config/flores-pilot.lock.json"),
                 "common_ids_available": len(common), "ids_in_selection_order": ids,
                 "selection_salt": plan["selection_salt"], "policy": "Same IDs for every language; selected by hash before tokenization; devtest unaccessed. No fitting on these data."}
    freeze(ROOT / "config/flores-pilot-sample.json", selection)
    texts = [{"sentence_id": i, "language": lang["code"], "language_label": lang["label"], "group": lang["group"],
              "text": by_language[lang["code"]][i]["text"], "dataset": plan["dataset"],
              "dataset_revision": plan["revision"], "split": "dev", "domain": by_language[lang["code"]][i].get("domain", "unknown")}
             for lang in plan["languages"] for i in ids]
    return texts, {"plan": plan, "dataset_lock": dataset_lock, "selection": selection}
