#!/usr/bin/env python3
"""Read-only per-document audit for the three full GPQA runs."""

import collections
import ast
import glob
import json
import re
from pathlib import Path

ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/"
    "20260919-qwen38-flash-next-ppu-e2e/accuracy"
)
CASES = {
    name: next(ROOT.glob(pattern))
    for name, pattern in {
        "acc008": "acc-008-full-gpqa-dual-service-current-candidate-20260922",
        "acc009": "acc-009-full-gpqa-dual-qsa-unbounded-20260922",
        "acc010": "acc-010-full-gpqa-dual-user-services-20260923",
    }.items()
}


def load(name):
    case = CASES[name]
    files = glob.glob(str(case / "results/**/samples_*.jsonl"), recursive=True)
    if len(files) != 1:
        raise RuntimeError((name, files))
    rows = [json.loads(line) for line in open(files[0], encoding="utf-8")]
    strict = {r["doc_id"]: r for r in rows if r["filter"] == "strict-match"}
    if len(strict) != 198:
        raise RuntimeError((name, len(strict)))
    return strict


runs = {name: load(name) for name in CASES}
ids = set(range(198))
for name, rows in runs.items():
    if set(rows) != ids:
        raise RuntimeError((name, sorted(ids - set(rows))))


def correct(row):
    return bool(row.get("exact_match"))


def caps(rows):
    return {
        doc_id
        for doc_id, row in rows.items()
        if (row.get("usage") or {}).get("completion_tokens", 0) >= 60000
    }


for name, rows in runs.items():
    cap = caps(rows)
    timeout = {doc_id for doc_id, row in rows.items() if row.get("timeout")}
    wrong = {doc_id for doc_id, row in rows.items() if not correct(row)}
    missing = {
        doc_id
        for doc_id, row in rows.items()
        if str(row.get("filtered_resps")) == "['[invalid]']"
    }
    print(name, json.dumps({
        "correct": sum(correct(row) for row in rows.values()),
        "wrong_count": len(wrong),
        "caps": sorted(cap),
        "timeout": sorted(timeout),
        "invalid": sorted(missing),
        "wrong_without_cap": sorted(wrong - cap),
    }, sort_keys=True))

print("provenance", json.dumps({
    "acc008_acc009_same_prompt_hash": sum(
        runs["acc008"][i]["prompt_hash"] == runs["acc009"][i]["prompt_hash"]
        for i in ids
    ),
    "acc009_acc010_same_prompt_hash": sum(
        runs["acc009"][i]["prompt_hash"] == runs["acc010"][i]["prompt_hash"]
        for i in ids
    ),
    "acc009_acc010_same_target_hash": sum(
        runs["acc009"][i]["target_hash"] == runs["acc010"][i]["target_hash"]
        for i in ids
    ),
}, sort_keys=True))

for older, newer in (("acc008", "acc009"), ("acc009", "acc010")):
    a, b = runs[older], runs[newer]
    gained = sorted(i for i in ids if not correct(a[i]) and correct(b[i]))
    lost = sorted(i for i in ids if correct(a[i]) and not correct(b[i]))
    common_wrong = sorted(i for i in ids if not correct(a[i]) and not correct(b[i]))
    common_caps = sorted(caps(a) & caps(b))
    print(older + "_to_" + newer, json.dumps({
        "gained": gained,
        "lost": lost,
        "common_wrong": common_wrong,
        "common_caps": common_caps,
        "new_caps": sorted(caps(b) - caps(a)),
        "resolved_caps": sorted(caps(a) - caps(b)),
    }, sort_keys=True))

rows = runs["acc010"]
print("acc010_wrong_detail")
for doc_id in sorted(i for i in ids if not correct(rows[i])):
    row = rows[doc_id]
    old = runs["acc009"][doc_id]
    print(json.dumps({
        "doc_id": doc_id,
        "acc009_correct": correct(old),
        "acc009_cap": doc_id in caps(runs["acc009"]),
        "acc010_timeout": bool(row.get("timeout")),
        "acc010_tokens": (row.get("usage") or {}).get("completion_tokens"),
        "target": row.get("target"),
        "filtered": row.get("filtered_resps"),
    }, ensure_ascii=False, sort_keys=True))

log_path = CASES["acc010"] / "evaluation" / "formal-run.log"
length_responses = []
stop_responses = 0
for line in open(log_path, encoding="utf-8", errors="replace"):
    if "get generate_until response" not in line or "output=" not in line:
        continue
    try:
        response = ast.literal_eval(line.split("output=", 1)[1])
    except (SyntaxError, ValueError):
        continue
    choice = response["choices"][0]
    if choice.get("finish_reason") == "stop":
        stop_responses += 1
    if choice.get("finish_reason") != "length":
        continue
    reasoning = choice["message"].get("reasoning") or ""
    markers = list(re.finditer(r"the best answer is\s*([ABCD])", reasoning, re.I))
    length_responses.append({
        "completion_tokens": response.get("usage", {}).get("completion_tokens"),
        "content_is_null": choice["message"].get("content") is None,
        "reasoning_chars": len(reasoning),
        "final_answer_markers_inside_reasoning": len(markers),
        "last_answer_marker_position_fraction": (
            round(markers[-1].start() / len(reasoning), 3) if markers and reasoning else None
        ),
        "last_180_reasoning_chars": reasoning[-180:].replace("\n", " "),
    })
print("raw_response_summary", json.dumps({
    "stop_responses": stop_responses,
    "length_responses": length_responses,
}, ensure_ascii=False, sort_keys=True))

wrong_noncap = [r for r in rows.values() if not correct(r) and not r.get("timeout")]
extraction_audit = []
for row in wrong_noncap:
    content = row["resps"][0][0]
    markers = re.findall(r"the best answer is\s*([ABCD])", content, re.I)
    extraction_audit.append({
        "doc_id": row["doc_id"],
        "strict_extracted": row["filtered_resps"][0],
        "last_explicit_final": markers[-1].upper() if markers else None,
        "explicit_final_count": len(markers),
    })
print("wrong_noncap_extraction_audit", json.dumps(extraction_audit, sort_keys=True))
