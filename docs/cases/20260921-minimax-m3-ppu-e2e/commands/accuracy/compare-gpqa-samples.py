#!/usr/bin/env python3
"""Compare two lm-eval GPQA sample files by doc_id and filter."""

import argparse
import hashlib
import json
from pathlib import Path


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def load(path):
    rows = [json.loads(line) for line in Path(path).open(encoding="utf-8") if line.strip()]
    keyed = {(int(row["doc_id"]), row["filter"]): row for row in rows}
    if len(keyed) != len(rows):
        raise ValueError(f"duplicate doc/filter rows in {path}")
    return rows, keyed


def raw_text(row):
    resps = row.get("resps") or []
    if len(resps) == 1 and isinstance(resps[0], list) and len(resps[0]) == 1:
        return str(resps[0][0])
    return json.dumps(resps, ensure_ascii=False, sort_keys=True)


def extracted(row):
    values = row.get("filtered_resps") or []
    return values[0] if len(values) == 1 else values


def compact(row):
    usage = row.get("usage") or {}
    text = raw_text(row)
    completion_tokens = usage.get("completion_tokens")
    return {
        "correct": float(row.get("exact_match", 0.0)) == 1.0,
        "extracted": extracted(row),
        "target": row.get("target"),
        "completion_tokens": completion_tokens,
        "truncated_30000": isinstance(completion_tokens, int) and completion_tokens >= 30000,
        "timeout": bool(row.get("timeout")) or "<TIMEOUT>" in text,
        "response_chars": len(text),
        "response_sha256": sha256_text(text),
        "prompt_hash": row.get("prompt_hash"),
        "doc_hash": row.get("doc_hash"),
        "target_hash": row.get("target_hash"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("old")
    parser.add_argument("new")
    parser.add_argument("output")
    args = parser.parse_args()
    old_rows, old = load(args.old)
    new_rows, new = load(args.new)
    if set(old) != set(new):
        raise ValueError("old/new doc/filter coverage differs")

    details = []
    for doc_id in range(198):
        old_row = old[(doc_id, "strict-match")]
        new_row = new[(doc_id, "strict-match")]
        old_c = compact(old_row)
        new_c = compact(new_row)
        details.append({
            "doc_id": doc_id,
            "old": old_c,
            "new": new_c,
            "status": (
                "regressed" if old_c["correct"] and not new_c["correct"] else
                "improved" if not old_c["correct"] and new_c["correct"] else
                "both_correct" if old_c["correct"] else "both_wrong"
            ),
            "same_extracted": old_c["extracted"] == new_c["extracted"],
            "same_response": old_c["response_sha256"] == new_c["response_sha256"],
        })

    counts = {name: sum(item["status"] == name for item in details) for name in
              ("regressed", "improved", "both_correct", "both_wrong")}
    payload = {
        "schema_version": 1,
        "old_samples": str(Path(args.old).resolve()),
        "new_samples": str(Path(args.new).resolve()),
        "row_counts": {"old": len(old_rows), "new": len(new_rows)},
        "coverage": {"unique_doc_ids": 198, "filters": ["flexible-extract", "strict-match"]},
        "provenance_equal": {
            key: all(old[(doc, "strict-match")].get(key) == new[(doc, "strict-match")].get(key)
                     for doc in range(198))
            for key in ("prompt_hash", "doc_hash", "target_hash")
        },
        "strict_counts": counts,
        "old_strict_correct": sum(item["old"]["correct"] for item in details),
        "new_strict_correct": sum(item["new"]["correct"] for item in details),
        "same_extracted_count": sum(item["same_extracted"] for item in details),
        "same_response_count": sum(item["same_response"] for item in details),
        "old_truncated_30000": [item["doc_id"] for item in details if item["old"]["truncated_30000"]],
        "new_truncated_30000": [item["doc_id"] for item in details if item["new"]["truncated_30000"]],
        "regressed_doc_ids": [item["doc_id"] for item in details if item["status"] == "regressed"],
        "improved_doc_ids": [item["doc_id"] for item in details if item["status"] == "improved"],
        "both_wrong_doc_ids": [item["doc_id"] for item in details if item["status"] == "both_wrong"],
        "details": details,
    }
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
