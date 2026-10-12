#!/usr/bin/env python3
"""Recover exact acc-010 per-doc HTTP responses from its immutable formal log."""

import ast
import glob
import hashlib
import json
from pathlib import Path


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)
LOG = ROOT / "evaluation/formal-run.log"
OUT = ROOT / "diagnostics/accdiag-008-current-output-replay-20260924/formal-http-recovered"


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


paths = glob.glob(
    str(ROOT / "results/**/samples_gpqa_diamond_generative_cot_*.jsonl"),
    recursive=True,
)
if len(paths) != 1:
    raise RuntimeError(f"expected exactly one formal samples file: {paths}")
samples = {}
prompt_to_id = {}
for line in open(paths[0], encoding="utf-8"):
    row = json.loads(line)
    if row.get("filter") != "strict-match":
        continue
    doc_id = row["doc_id"]
    prompt = row["arguments"]["gen_args_0"]["arg_0"][0]
    if doc_id in samples or prompt in prompt_to_id:
        raise RuntimeError(f"duplicate strict sample or prompt: {doc_id}")
    samples[doc_id] = row
    prompt_to_id[prompt] = doc_id
if len(samples) != 198:
    raise RuntimeError(f"expected 198 strict samples, found {len(samples)}")

records = {}
wrong_responses = {}
pending = None
sent_count = 0
response_count = 0
for line_number, line in enumerate(LOG.open(encoding="utf-8", errors="replace"), 1):
    if "sent generate_until request, messages=" in line:
        if pending is not None:
            raise RuntimeError(f"unpaired sent request at line {line_number}")
        start = line.index("JsonChatStr(prompt=") + len("JsonChatStr(prompt=")
        end = line.index(")], gen_kwargs=", start)
        prompt = ast.literal_eval(line[start:end])
        if prompt not in prompt_to_id:
            raise RuntimeError(f"unmatched prompt at line {line_number}")
        pending = (prompt_to_id[prompt], line_number)
        sent_count += 1
    elif "get generate_until response" in line:
        if pending is None:
            raise RuntimeError(f"unpaired response at line {line_number}")
        doc_id, request_line = pending
        pending = None
        if doc_id in records:
            raise RuntimeError(f"duplicate response for {doc_id}")
        body = ast.literal_eval(line.split("output=", 1)[1])
        choice = body["choices"][0]
        message = choice["message"]
        usage = body.get("usage") or {}
        sample = samples[doc_id]
        if usage.get("completion_tokens") != (sample.get("usage") or {}).get(
            "completion_tokens"
        ):
            raise RuntimeError(f"usage mismatch for {doc_id}")
        content = message.get("content") or ""
        reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
        if not sample.get("timeout") and content != sample["resps"][0][0]:
            raise RuntimeError(f"content mismatch for {doc_id}")
        records[doc_id] = {
            "doc_id": doc_id,
            "request_log_line": request_line,
            "response_log_line": line_number,
            "response_id": body.get("id"),
            "prompt_hash": sample["prompt_hash"],
            "target": sample["target"],
            "strict_answer": sample["filtered_resps"][0],
            "strict_correct": bool(sample["exact_match"]),
            "timeout_flag": bool(sample.get("timeout")),
            "finish_reason": choice.get("finish_reason"),
            "completion_tokens": usage.get("completion_tokens"),
            "content_chars": len(content),
            "reasoning_chars": len(reasoning),
            "content_sha256": digest(content),
            "reasoning_sha256": digest(reasoning),
        }
        if not sample["exact_match"]:
            wrong_responses[doc_id] = body
        response_count += 1
if pending is not None or sent_count != 198 or response_count != 198 or len(records) != 198:
    raise RuntimeError(
        f"invalid matching: pending={pending}, sent={sent_count}, "
        f"responses={response_count}, unique={len(records)}"
    )

OUT.mkdir(parents=True, exist_ok=False)
(OUT / "wrong").mkdir()
for doc_id, body in wrong_responses.items():
    (OUT / "wrong" / f"doc{doc_id}.json").write_text(
        json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
summary = {
    "formal_log": str(LOG),
    "samples": paths[0],
    "strict_samples": len(samples),
    "paired_requests": sent_count,
    "paired_responses": response_count,
    "wrong_raw_responses": len(wrong_responses),
    "wrong_ids": sorted(wrong_responses),
    "records": [records[doc_id] for doc_id in sorted(records)],
}
(OUT / "index.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {
            "strict_samples": len(samples),
            "paired_requests": sent_count,
            "paired_responses": response_count,
            "wrong_raw_responses": len(wrong_responses),
            "wrong_ids": sorted(wrong_responses),
            "out": str(OUT),
        },
        ensure_ascii=False,
    )
)
