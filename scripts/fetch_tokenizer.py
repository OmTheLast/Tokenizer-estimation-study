"""Fetch only locked tokenizer assets; validate cached and downloaded bytes."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "config/qwen-tokenizer.lock.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_assets():
    lock = json.loads(LOCK.read_text())
    directory = ROOT / lock["cache_directory"]
    directory.mkdir(parents=True, exist_ok=True)
    for asset in lock["assets"]:
        target = directory / asset["filename"]
        if not target.exists():
            partial = target.with_suffix(".download")
            subprocess.run([
                "curl", "--fail", "--silent", "--show-error", "--location",
                "--retry", "2", "--max-time", "120", "--output", str(partial),
                asset["url"],
            ], check=True)
            if sha256(partial) != asset["sha256"]:
                raise ValueError(f"Downloaded checksum mismatch: {asset['filename']}")
            partial.replace(target)
        if sha256(target) != asset["sha256"]:
            raise ValueError(f"Cached checksum mismatch: {target}")
    return lock, directory


if __name__ == "__main__":
    lock, directory = fetch_assets()
    print(f"Verified {len(lock['assets'])} assets at {lock['revision']}")
