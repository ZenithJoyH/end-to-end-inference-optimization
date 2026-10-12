#!/usr/bin/env python3
"""Replay one frozen GPQA prompt against the current PPU service, preserving raw output."""

import argparse
import glob
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)
OUT_ROOT = ROOT / "diagnostics/accdiag-008-current-output-replay-20260924"


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--doc-id", type=int, required=True)
parser.add_argument("--port", type=int, choices=(8000, 8010), required=True)
parser.add_argument("--label", type=str, default="exact-r1")
parser.add_argument("--max-tokens", type=int, default=60000)
args = parser.parse_args()
if re.fullmatch(r"[a-z0-9-]{1,40}", args.label) is None:
    raise RuntimeError("label must be lowercase hyphenated text")
if not 1 <= args.max_tokens <= 60000:
    raise RuntimeError("diagnostic max-tokens must be within the frozen 60K budget")

paths = glob.glob(
    str(ROOT / "results/**/samples_gpqa_diamond_generative_cot_*.jsonl"),
    recursive=True,
)
if len(paths) != 1:
    raise RuntimeError(f"expected one frozen sample file, got {paths}")
matches = [
    row
    for line in open(paths[0], encoding="utf-8")
    if (row := json.loads(line)).get("filter") == "strict-match"
    and row.get("doc_id") == args.doc_id
]
if len(matches) != 1:
    raise RuntimeError(f"expected one strict-match row for {args.doc_id}")
row = matches[0]
packed = row["arguments"]["gen_args_0"]
generation = packed["arg_1"]
if generation.get("max_gen_toks") != 60000:
    raise RuntimeError("frozen max generation changed")
payload = {
    "model": "Qwen3.8-Flash-Next",
    "messages": json.loads(packed["arg_0"][0]),
    "temperature": generation["temperature"],
    "top_p": generation["top_p"],
    "top_k": generation["top_k"],
    "min_p": generation["min_p"],
    "presence_penalty": generation["presence_penalty"],
    "repetition_penalty": generation["repetition_penalty"],
    "max_completion_tokens": args.max_tokens,
    "stop": (generation["until"] + ["<|endoftext|>"])[:4],
    "seed": 1234,
}
base = f"http://127.0.0.1:{args.port}"
with urllib.request.urlopen(base + "/health", timeout=5) as response:
    if response.status != 200:
        raise RuntimeError(f"unhealthy endpoint: {response.status}")
with urllib.request.urlopen(base + "/v1/models", timeout=5) as response:
    ids = [item.get("id") for item in json.load(response).get("data", [])]
if payload["model"] not in ids:
    raise RuntimeError(f"model identity mismatch: {ids}")

out = OUT_ROOT / f"doc{args.doc_id}-port{args.port}-{args.label}"
out.mkdir(parents=True, exist_ok=False)
(out / "request.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
request = urllib.request.Request(
    base + "/v1/chat/completions",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
started = time.monotonic()
try:
    with urllib.request.urlopen(request, timeout=7200) as response:
        body = json.load(response)
        status = response.status
    (out / "response.json").write_text(
        json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    choice = body["choices"][0]
    message = choice["message"]
    content = message.get("content") or ""
    reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
    markers = re.findall(r"the best answer is\s*\(?([ABCD])\)?", content, re.I)
    summary = {
        "doc_id": args.doc_id,
        "port": args.port,
        "stage_label": args.label,
        "requested_max_tokens": args.max_tokens,
        "prompt_hash": row["prompt_hash"],
        "target": row["target"],
        "formal_answer": row["filtered_resps"][0],
        "request_sha256": sha(json.dumps(payload, sort_keys=True, ensure_ascii=False)),
        "http_status": status,
        "finish_reason": choice.get("finish_reason"),
        "usage": body.get("usage"),
        "content_chars": len(content),
        "reasoning_chars": len(reasoning),
        "final_markers": markers,
        "content_sha256": sha(content),
        "reasoning_sha256": sha(reasoning),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
except Exception as exc:
    summary = {
        "doc_id": args.doc_id,
        "port": args.port,
        "stage_label": args.label,
        "requested_max_tokens": args.max_tokens,
        "request_sha256": sha(json.dumps(payload, sort_keys=True, ensure_ascii=False)),
        "error": f"{type(exc).__name__}: {exc}",
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
(out / "summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
