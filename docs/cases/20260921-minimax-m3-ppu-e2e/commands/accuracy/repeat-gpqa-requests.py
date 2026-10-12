#!/usr/bin/env python3
"""Repeat selected frozen GPQA requests against one service instance."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request


ANSWER_PATTERNS = (
    re.compile(r"best answer is\s*(?:\*\*)?\(?([ABCD])\)?", re.I),
    re.compile(r"answer is\s*(?:\*\*)?\(?([ABCD])\)?", re.I),
)


def extract_answer(text):
    for pattern in ANSWER_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            return matches[-1].upper()
    return "[invalid]"


def load_prompts(samples_path, doc_ids):
    rows = [json.loads(line) for line in Path(samples_path).open(encoding="utf-8") if line.strip()]
    selected = {}
    for row in rows:
        doc_id = int(row["doc_id"])
        if row["filter"] != "strict-match" or doc_id not in doc_ids:
            continue
        arg = row["arguments"]["gen_args_0"]["arg_0"][0]
        selected[doc_id] = {
            "messages": json.loads(arg),
            "target": row["target"],
            "frozen_prompt_hash": row["prompt_hash"],
        }
    if set(selected) != set(doc_ids):
        raise ValueError("missing requested doc_ids in samples")
    return selected


def request_once(base_url, doc_id, repeat, spec):
    payload = {
        "model": "MiniMax-M3",
        "messages": spec["messages"],
        "max_tokens": 30000,
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 20,
        "seed": 1234,
        "stop": ["</s>"],
    }
    body = json.dumps(payload).encode()
    started = time.time()
    request = urllib.request.Request(base_url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=7200) as response:
        result = json.load(response)
    text = result["choices"][0]["message"]["content"]
    usage = result.get("usage") or {}
    return {
        "doc_id": doc_id,
        "repeat": repeat,
        "elapsed_seconds": time.time() - started,
        "target": spec["target"],
        "frozen_prompt_hash": spec["frozen_prompt_hash"],
        "extracted": extract_answer(text),
        "finish_reason": result["choices"][0].get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
        "response_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "response": text,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8023/v1/chat/completions")
    parser.add_argument("--doc-ids", default="69,121,131")
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    doc_ids = [int(value) for value in args.doc_ids.split(",")]
    prompts = load_prompts(args.samples, doc_ids)
    futures = []
    rows = []
    with ThreadPoolExecutor(max_workers=len(doc_ids) * args.repeats) as pool:
        for doc_id in doc_ids:
            for repeat in range(args.repeats):
                futures.append(pool.submit(request_once, args.base_url, doc_id, repeat, prompts[doc_id]))
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: (row["doc_id"], row["repeat"]))
    summary = {
        str(doc_id): {
            "answers": [row["extracted"] for row in rows if row["doc_id"] == doc_id],
            "response_sha256": [row["response_sha256"] for row in rows if row["doc_id"] == doc_id],
            "completion_tokens": [row["completion_tokens"] for row in rows if row["doc_id"] == doc_id],
            "finish_reasons": [row["finish_reason"] for row in rows if row["doc_id"] == doc_id],
        }
        for doc_id in doc_ids
    }
    output.write_text(json.dumps({
        "schema_version": 1,
        "base_url": args.base_url,
        "service_request": {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 20,
            "seed": 1234,
            "max_tokens": 30000,
        },
        "summary": summary,
        "rows": rows,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
