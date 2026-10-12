#!/usr/bin/env python3
"""Read-only repetition audit of recovered formal GPQA wrong responses."""

import json
from pathlib import Path
import re


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923/diagnostics/"
    "accdiag-008-current-output-replay-20260924/formal-http-recovered"
)


def novelty(words, width=8):
    if len(words) < width:
        return 1.0
    grams = [tuple(words[i : i + width]) for i in range(len(words) - width + 1)]
    return round(len(set(grams)) / len(grams), 4)


index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
records = {item["doc_id"]: item for item in index["records"]}
if len(records) != 198 or len(index["wrong_ids"]) != 24:
    raise RuntimeError("formal recovery is incomplete")

rows = []
for doc_id in index["wrong_ids"]:
    body = json.loads((ROOT / "wrong" / f"doc{doc_id}.json").read_text(encoding="utf-8"))
    choice = body["choices"][0]
    message = choice["message"]
    reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
    words = re.findall(r"\S+", reasoning)
    tail = words[-5000:]
    head = words[:5000]
    markers = re.findall(r"the best answer is\s*\(?([ABCD])\)?", reasoning, re.I)
    rows.append(
        {
            "doc_id": doc_id,
            "finish_reason": choice.get("finish_reason"),
            "completion_tokens": body["usage"]["completion_tokens"],
            "reasoning_words": len(words),
            "head_8gram_novelty": novelty(head),
            "tail_8gram_novelty": novelty(tail),
            "reasoning_answer_markers": markers,
            "final_content_present": bool(message.get("content")),
        }
    )

print(json.dumps(rows, ensure_ascii=False, sort_keys=True))
