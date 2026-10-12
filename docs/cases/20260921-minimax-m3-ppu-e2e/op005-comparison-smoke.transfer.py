#!/usr/bin/env python3
"""Two short graph-service smoke requests for one op005 comparison role."""

import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen


if len(sys.argv) != 3 or sys.argv[1] not in ("baseline", "candidate", "revert"):
    raise SystemExit("usage: op005-comparison-smoke.py ROLE RESULTS_DIRECTORY")

role = sys.argv[1]
root = Path(sys.argv[2]).resolve()
request_body = json.dumps({
    "model": "MiniMax-M3",
    "messages": [{"role": "user", "content": "Say hello briefly."}],
    "temperature": 0,
    "max_tokens": 64,
}).encode()
output = root / f"op005-{role}-comparison-smoke.json"
if output.exists():
    raise SystemExit(f"refusing to overwrite {output}")

responses = []
for index in (1, 2):
    request = Request(
        "http://127.0.0.1:8023/v1/chat/completions",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise SystemExit(f"smoke {index}: HTTP {response.status}")
        raw = response.read()
    parsed = json.loads(raw)
    content = parsed["choices"][0]["message"]["content"]
    if not content:
        raise SystemExit(f"smoke {index}: empty output")
    responses.append({
        "index": index,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_chars": len(content),
        "completion_tokens": parsed["usage"]["completion_tokens"],
        "finish_reason": parsed["choices"][0]["finish_reason"],
    })

output.write_text(json.dumps({"role": role, "responses": responses}, indent=2) + "\n")
print(output)
print(json.dumps(responses))
