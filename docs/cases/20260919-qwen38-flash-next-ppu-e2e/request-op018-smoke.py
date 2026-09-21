#!/usr/bin/env python3
"""Save one deterministic unarmed completion for op-018 correctness checks."""

import argparse
import json
import urllib.request


parser = argparse.ArgumentParser()
parser.add_argument("output")
parser.add_argument("--port", type=int, default=8031)
args = parser.parse_args()
payload = {
    "model": "Qwen3.8-Flash-Next",
    "prompt": "Reply with exactly: OP018_OK",
    "temperature": 0,
    "max_tokens": 8,
    "seed": 42,
}
request = urllib.request.Request(
    f"http://127.0.0.1:{args.port}/v1/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=600) as response:
    raw = json.load(response)
record = {
    "request": payload,
    "text": raw["choices"][0]["text"],
    "finish_reason": raw["choices"][0]["finish_reason"],
    "completion_tokens": raw["usage"]["completion_tokens"],
}
with open(args.output, "x", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2, sort_keys=True)
    handle.write("\n")
print(json.dumps(record, sort_keys=True))
