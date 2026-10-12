#!/usr/bin/env python3
"""Bounded exact-field C8/C32 short GPQA replay; not a scored evaluation."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import glob
import hashlib
import json
from pathlib import Path
import threading
import time
import urllib.request


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)
OUT_ROOTS = {
    "accdiag008": ROOT / "diagnostics/accdiag-008-current-output-replay-20260924",
    "accdiag009": ROOT / "diagnostics/accdiag-009-sustained-peer-overlap-20260924",
}
DOC_IDS_BY_CONCURRENCY = {
    1: (168,),
    8: tuple(range(7)) + (168,),
    32: tuple(range(31)) + (168,),
}


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def send(doc_id, row, barrier, base, out, logprobs, target_full, peer_max_tokens):
    packed = row["arguments"]["gen_args_0"]
    generation = packed["arg_1"]
    if generation["max_gen_toks"] != 60000:
        raise RuntimeError(f"doc {doc_id}: frozen max generation changed")
    payload = {
        "model": "Qwen3.8-Flash-Next",
        "messages": json.loads(packed["arg_0"][0]),
        "temperature": generation["temperature"],
        "top_p": generation["top_p"],
        "top_k": generation["top_k"],
        "min_p": generation["min_p"],
        "presence_penalty": generation["presence_penalty"],
        "repetition_penalty": generation["repetition_penalty"],
        "max_completion_tokens": 60000 if target_full and doc_id == 168 else peer_max_tokens,
        "stop": (generation["until"] + ["<|endoftext|>"])[:4],
        "seed": 1234,
    }
    if logprobs:
        payload.update({"logprobs": True, "top_logprobs": 5})
    doc_dir = out / f"doc{doc_id}"
    doc_dir.mkdir()
    (doc_dir / "request.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    req = urllib.request.Request(
        base + "/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    barrier.wait(timeout=30)
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=7200 if target_full and doc_id == 168 else 180) as response:
            body = json.load(response)
            status = response.status
        (doc_dir / "response.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        choice = body["choices"][0]
        message = choice["message"]
        reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
        content = message.get("content") or ""
        result = {
            "doc_id": doc_id,
            "prompt_hash": row["prompt_hash"],
            "request_sha256": sha(json.dumps(payload, ensure_ascii=False, sort_keys=True)),
            "http_status": status,
            "finish_reason": choice.get("finish_reason"),
            "usage": body.get("usage"),
            "reasoning_chars": len(reasoning),
            "reasoning_sha256": sha(reasoning),
            "reasoning_prefix": reasoning[:160],
            "content_chars": len(content),
            "content_sha256": sha(content),
            "elapsed_seconds": round(time.monotonic() - start, 3),
        }
    except Exception as exc:
        result = {
            "doc_id": doc_id,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.monotonic() - start, 3),
        }
    (doc_dir / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, choices=(8000, 8010), required=True)
    parser.add_argument("--wave", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--concurrency", type=int, choices=(1, 8, 32), default=8)
    parser.add_argument("--logprobs", action="store_true")
    parser.add_argument("--target-full", action="store_true")
    parser.add_argument("--peer-max-tokens", type=int, choices=(64, 128, 256), default=64)
    parser.add_argument("--case", choices=tuple(OUT_ROOTS), default="accdiag008")
    args = parser.parse_args()
    if args.target_full and (args.concurrency != 8 or args.logprobs):
        raise RuntimeError("target-full is restricted to C8 without logprobs")
    if args.peer_max_tokens != 64 and not args.target_full:
        raise RuntimeError("extended peers require target-full")
    if args.case == "accdiag009" and (not args.target_full or args.peer_max_tokens != 128):
        raise RuntimeError("accdiag009 is restricted to the frozen C8/peer128 design")
    doc_ids = DOC_IDS_BY_CONCURRENCY[args.concurrency]
    paths = glob.glob(
        str(ROOT / "results/**/samples_gpqa_diamond_generative_cot_*.jsonl"),
        recursive=True,
    )
    if len(paths) != 1:
        raise RuntimeError(f"expected one frozen sample file: {paths}")
    rows = {}
    with open(paths[0], encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("filter") == "strict-match" and row.get("doc_id") in doc_ids:
                if row["doc_id"] in rows:
                    raise RuntimeError("duplicate strict-match row")
                rows[row["doc_id"]] = row
    if set(rows) != set(doc_ids):
        raise RuntimeError(f"missing frozen docs: {set(doc_ids) - set(rows)}")
    base = f"http://127.0.0.1:{args.port}"
    with urllib.request.urlopen(base + "/health", timeout=5) as response:
        if response.status != 200:
            raise RuntimeError("service unhealthy")
    with urllib.request.urlopen(base + "/v1/models", timeout=5) as response:
        ids = [item.get("id") for item in json.load(response).get("data", [])]
    if "Qwen3.8-Flash-Next" not in ids:
        raise RuntimeError(f"model identity mismatch: {ids}")
    qualifier = (f"-targetfull-peer{args.peer_max_tokens}-exact" if args.target_full else ("-lp5" if args.logprobs else "-exact"))
    out = OUT_ROOTS[args.case] / f"c{args.concurrency}-short{qualifier}-port{args.port}-wave{args.wave}"
    out.mkdir(parents=True, exist_ok=False)
    barrier = threading.Barrier(len(doc_ids))
    with ThreadPoolExecutor(max_workers=len(doc_ids)) as pool:
        futures = [pool.submit(send, doc_id, rows[doc_id], barrier, base, out, args.logprobs, args.target_full, args.peer_max_tokens) for doc_id in doc_ids]
        results = [future.result() for future in futures]
    summary = {"port": args.port, "wave": args.wave, "target_max_completion_tokens": 60000 if args.target_full else args.peer_max_tokens, "peer_max_completion_tokens": args.peer_max_tokens, "concurrency": len(doc_ids), "logprobs": args.logprobs, "target_full": args.target_full, "results": results}
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
