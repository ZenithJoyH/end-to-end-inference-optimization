#!/usr/bin/env python3
"""Read-only, bounded views of acc010 incorrect completed GPQA samples."""

import argparse
import glob
import json
from pathlib import Path

ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/accuracy"
)
RUNS = {
    "009": "acc-009-full-gpqa-dual-qsa-unbounded-20260922",
    "010": "acc-010-full-gpqa-dual-user-services-20260923",
}


def load(which):
    files = glob.glob(str(ROOT / RUNS[which] / "results/**/samples_*.jsonl"), recursive=True)
    if len(files) != 1:
        raise RuntimeError((which, files))
    return {
        r["doc_id"]: r
        for r in map(json.loads, open(files[0], encoding="utf-8"))
        if r["filter"] == "strict-match"
    }


def shorten(text, first=500, last=2500):
    if not isinstance(text, str):
        return text
    if len(text) <= first + last:
        return text
    return text[:first] + f"\n... [omitted {len(text) - first - last} chars] ...\n" + text[-last:]


parser = argparse.ArgumentParser()
parser.add_argument("ids", nargs="+", type=int)
args = parser.parse_args()
old, current = load("009"), load("010")
for doc_id in args.ids:
    row, previous = current[doc_id], old[doc_id]
    doc = row["doc"]
    output = {
        "doc_id": doc_id,
        "domain": doc["High-level domain"],
        "subdomain": doc["Subdomain"],
        "question": doc["Question"],
        "choices": doc["choices"],
        "target": row["target"],
        "gold_explanation": shorten(doc.get("Explanation"), first=0, last=4500),
        "current_answer": row["filtered_resps"],
        "current_completion_tokens": (row.get("usage") or {}).get("completion_tokens"),
        "current_content": shorten(row["resps"][0][0], first=1000, last=5000),
        "previous_answer": previous["filtered_resps"],
        "previous_correct": bool(previous["exact_match"]),
        "previous_completion_tokens": (previous.get("usage") or {}).get("completion_tokens"),
    }
    print(json.dumps(output, ensure_ascii=False))
