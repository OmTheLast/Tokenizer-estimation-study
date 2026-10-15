"""Download explicitly chosen revisions and record asset hashes (no model weights)."""
import json
from pathlib import Path
import subprocess
from fetch_tokenizer import ROOT, sha256

SOURCES = [
    ("bonsai-ternary-4b", "onnx-community/Ternary-Bonsai-4B-ONNX", "9d085aaf786063cadb648fff1725c2c36fd28ade", "No model card/licence file listed in conversion repository."),
    ("lfm2-1.2b", "LiquidAI/LFM2.5-1.2B-Instruct-ONNX", "10f72e70abf67ac0fd7ebf15bc5854726891d864", "Model card identifies LFM Open License v1.0; source LICENSE retained in cache."),
    ("gemma4-e2b", "onnx-community/gemma-4-E2B-it-ONNX", "9f4bef82ea6e296bc69f8a2f5939f73af81b07a6", "Conversion model card identifies apache-2.0 and links the Gemma 4 licence. Assets remain unredistributed in cache."),
    ("minicpm5-2b-gguf", "openbmb/MiniCPM5-2B", "12a3808a956f869c767195e9266b59c4d21d92e2", "First-party model card identifies apache-2.0. HF JSON tokenizer checked, not the GGUF runtime."),
]


def main():
    for key, repository, revision, licence in SOURCES:
        lock_path = ROOT / "config" / f"{key}-tokenizer.lock.json"
        cache = Path(".cache/tokenizers") / key / revision
        directory = ROOT / cache
        directory.mkdir(parents=True, exist_ok=True)
        assets = []
        names = ["tokenizer.json", "tokenizer_config.json"]
        if key == "lfm2-1.2b":
            names.append("LICENSE")
        for name in names:
            target = directory / name
            url = f"https://huggingface.co/{repository}/resolve/{revision}/{name}"
            if not target.exists():
                temp = target.with_suffix(".download")
                subprocess.run(["curl", "-fsSL", "--retry", "2", "--max-time", "120", "-o", str(temp), url], check=True)
                if name.endswith(".json"):
                    json.loads(temp.read_text())
                temp.replace(target)
            assets.append({"filename": name, "url": url, "sha256": sha256(target), "bytes": target.stat().st_size})
        note = "Repository mapped from pinned LocalMind registry; original fixture does not record the exact HF revision or tokenizer-library version. Selected revision predates the fixture measurement date; historical identity is unproven."
        if key == "minicpm5-2b-gguf":
            note = "LocalMind uses first-party openbmb/MiniCPM5-2B-GGUF, which has no tokenizer.json. This run uses the first-party parent MiniCPM5-2B JSON tokenizer at the latest recorded revision before 2026-09-24. It can reproduce the stated JSON-based fixtures but does not verify GGUF/wllama runtime equivalence. Original fixture HF revision/library version is unrecorded."
        lock = {"localmind_commit": "b39f0bc145a0c0926ba22247ee31cd369e0445b6", "model_key": key,
                "repository": repository, "revision": revision, "cache_directory": str(cache),
                "add_special_tokens": False, "assets": assets,
                "historical_provenance": note, "licence_note": licence}
        if lock_path.exists() and json.loads(lock_path.read_text()) != lock:
            raise ValueError(f"Refusing to change existing lock: {lock_path}")
        lock_path.write_text(json.dumps(lock, indent=2) + "\n")
        print(f"Pinned {key}: {revision} ({sum(a['bytes'] for a in assets)} bytes)", flush=True)


if __name__ == "__main__":
    main()
