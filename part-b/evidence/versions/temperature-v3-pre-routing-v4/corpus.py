"""The frozen source corpus. This module never reads generated test labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from taxonomy import CATEGORIES

ROOT = Path(__file__).resolve().parent

def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_corpus(root=ROOT):
    data = Path(root) / "data"
    manifest = json.loads((data / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        if sha256(data / name) != expected:
            raise ValueError(f"Frozen corpus changed: {name}")
    development = read_jsonl(data / "development.jsonl")
    review = read_jsonl(data / "review_reports.jsonl")
    if len(development) != 300 or len(review) != 60:
        raise ValueError("Expected 300 development and 60 review reports.")
    records = development + review
    if len({r["id"] for r in records}) != 360 or len({r["text"] for r in records}) != 360:
        raise ValueError("Report IDs and exact report texts must be unique.")
    train = [r for r in development if r["split"] == "train"]
    validation = [r for r in development if r["split"] == "validation"]
    if len(train) != 240 or len(validation) != 60:
        raise ValueError("Expected a 240/60 development split.")
    if {r["family"] for r in train} & {r["family"] for r in validation}:
        raise ValueError("A scenario family crossed training and development.")
    if any(r["category"] not in CATEGORIES or type(r["urgent"]) is not bool or
           type(r["clarification"]) is not bool for r in development):
        raise ValueError("Invalid development labels.")
    if any(set(r) != {"id", "text", "channel"} for r in review):
        raise ValueError("The blind review corpus must not contain labels or predictions.")
    return development, review, manifest

if __name__ == "__main__":
    development, review, _ = load_corpus()
    print(f"Corpus verified: {len(development)} development + {len(review)} blind review reports.")
