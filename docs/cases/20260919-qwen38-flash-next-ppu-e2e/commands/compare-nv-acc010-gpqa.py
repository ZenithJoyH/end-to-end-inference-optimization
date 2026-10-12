#!/usr/bin/env python3
"""Read-only paired audit of user-provided NV and frozen PPU GPQA samples."""

import collections
import glob
import json
import re
import statistics
from pathlib import Path


NV_PATH = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/gpqa_nv.jsonl")
PPU_ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)


def load(path):
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    by_filter = collections.defaultdict(dict)
    for row in rows:
        filt = row.get("filter")
        doc_id = row.get("doc_id")
        if doc_id in by_filter[filt]:
            raise RuntimeError(f"duplicate {filt=} {doc_id=} in {path}")
        by_filter[filt][doc_id] = row
    return by_filter


def correct(row):
    return row.get("exact_match") == 1


def capped(row):
    return bool(row.get("timeout")) or (row.get("usage") or {}).get(
        "completion_tokens", 0
    ) >= 60000


def extracted(row):
    values = row.get("filtered_resps") or []
    return values[0] if values else None


def raw_response(row):
    values = row.get("resps") or []
    if not values:
        return ""
    value = values[0]
    if isinstance(value, list):
        value = value[0] if value else ""
    return value if isinstance(value, str) else str(value)


def length_stats(rows):
    values = [len(raw_response(row)) for row in rows]
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


paths = glob.glob(
    str(PPU_ROOT / "**/samples_gpqa_diamond_generative_cot_*.jsonl"),
    recursive=True,
)
if len(paths) != 1:
    raise RuntimeError(f"expected exactly one PPU sample file: {paths}")
ppu_path = Path(paths[0])
nv_all = load(NV_PATH)
ppu_all = load(ppu_path)
nv = nv_all["strict-match"]
ppu = ppu_all["strict-match"]
if set(nv) != set(ppu) or len(nv) != 198:
    raise RuntimeError(
        f"unpaired data: NV={len(nv)}, PPU={len(ppu)}, common={len(set(nv) & set(ppu))}"
    )
ids = sorted(nv, key=int)

groups = {
    "both_right": [i for i in ids if correct(nv[i]) and correct(ppu[i])],
    "nv_right_ppu_wrong": [i for i in ids if correct(nv[i]) and not correct(ppu[i])],
    "nv_wrong_ppu_right": [i for i in ids if not correct(nv[i]) and correct(ppu[i])],
    "both_wrong": [i for i in ids if not correct(nv[i]) and not correct(ppu[i])],
}
summary = {
    "nv_path": str(NV_PATH),
    "ppu_path": str(ppu_path),
    "filters": {
        "nv": {key: len(value) for key, value in nv_all.items()},
        "ppu": {key: len(value) for key, value in ppu_all.items()},
    },
    "nv_correct": sum(correct(nv[i]) for i in ids),
    "ppu_correct": sum(correct(ppu[i]) for i in ids),
    "same_hashes": {
        key: sum(nv[i].get(key) == ppu[i].get(key) for i in ids)
        for key in ("doc_hash", "prompt_hash", "target_hash")
    },
    "same_arguments": sum(nv[i].get("arguments") == ppu[i].get("arguments") for i in ids),
    "same_prompt_argument": sum(
        nv[i].get("arguments", {}).get("gen_args_0", {}).get("arg_0")
        == ppu[i].get("arguments", {}).get("gen_args_0", {}).get("arg_0")
        for i in ids
    ),
    "generation_arguments": {
        label: dict(
            collections.Counter(
                json.dumps(
                    row.get("arguments", {}).get("gen_args_0", {}).get("arg_1"),
                    sort_keys=True,
                )
                for row in samples.values()
            )
        )
        for label, samples in (("nv", nv), ("ppu", ppu))
    },
    "same_target": sum(nv[i].get("target") == ppu[i].get("target") for i in ids),
    "same_extracted": sum(extracted(nv[i]) == extracted(ppu[i]) for i in ids),
    "groups": groups,
    "nv_timeout_ids": [i for i in ids if capped(nv[i])],
    "ppu_cap_ids": [i for i in ids if capped(ppu[i])],
    "nv_response_chars": length_stats(nv.values()),
    "ppu_response_chars": length_stats(ppu.values()),
    "nv_wrong_response_chars": length_stats(
        [nv[i] for i in ids if not correct(nv[i])]
    ),
    "ppu_wrong_response_chars": length_stats(
        [ppu[i] for i in ids if not correct(ppu[i])]
    ),
}
print(json.dumps({"summary": summary}, ensure_ascii=False, sort_keys=True))
for group in ("nv_right_ppu_wrong", "nv_wrong_ppu_right", "both_wrong"):
    for i in groups[group]:
        nv_text = raw_response(nv[i])
        ppu_text = raw_response(ppu[i])
        print(
            json.dumps(
                {
                    "group": group,
                    "doc_id": i,
                    "target": nv[i].get("target"),
                    "nv_answer": extracted(nv[i]),
                    "ppu_answer": extracted(ppu[i]),
                    "nv_timeout": capped(nv[i]),
                    "ppu_cap": capped(ppu[i]),
                    "nv_response_chars": len(nv_text),
                    "ppu_response_chars": len(ppu_text),
                    "nv_final_markers": len(
                        re.findall(r"the best answer is\s*\(?[ABCD]\)?", nv_text, re.I)
                    ),
                    "ppu_final_markers": len(
                        re.findall(r"the best answer is\s*\(?[ABCD]\)?", ppu_text, re.I)
                    ),
                    "ppu_completion_tokens": (ppu[i].get("usage") or {}).get(
                        "completion_tokens"
                    ),
                    "subject": (nv[i].get("doc") or {}).get("Subdomain"),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
