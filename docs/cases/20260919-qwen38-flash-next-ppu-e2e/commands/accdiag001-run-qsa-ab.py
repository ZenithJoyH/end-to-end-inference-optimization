#!/usr/bin/env python3
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import re
import threading
import time
import urllib.request

SAMPLES = pathlib.Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/"
    "acc-008-full-gpqa-dual-service-current-candidate-20260922/results/"
    "Qwen3.8-Flash-Next-current-optimized-dual-full-gpqa-20260922/"
    "a8e7870e0dbe43fb854d042f0ed0e1ce/gpqa_diamond_generative_cot/"
    "Qwen3.8-Flash-Next/samples_gpqa_diamond_generative_cot_2026-09-22T04-13-39.526414.jsonl"
)
OUT = pathlib.Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/"
    "acc-008-full-gpqa-dual-service-current-candidate-20260922/diagnostics/"
    "accdiag-001-qsa-bound-long-gpqa-20260922/results"
)
DOC_IDS = [12, 15, 64, 121, 127]
ENDPOINTS = {
    "bound8448": "http://127.0.0.1:8010/v1/chat/completions",
    "unbounded": "http://127.0.0.1:8000/v1/chat/completions",
}
LOCK = threading.Lock()


def now():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def load_cases():
    cases = {}
    with SAMPLES.open() as f:
        for line in f:
            row = json.loads(line)
            if row.get("filter") != "strict-match" or row.get("doc_id") not in DOC_IDS:
                continue
            packed = row["arguments"]["gen_args_0"]
            messages = json.loads(packed["arg_0"][0])
            cases[row["doc_id"]] = {"messages": messages, "target": row["target"]}
    if sorted(cases) != DOC_IDS:
        raise RuntimeError(f"missing selected cases: got {sorted(cases)}")
    return cases


def extract_answer(text):
    if not text:
        return None
    matches = re.findall(r"The best answer is\s*([ABCD])", text, flags=re.I)
    return matches[-1].upper() if matches else None


def run_one(label, url, doc_id, case):
    payload = {
        "model": "Qwen3.8-Flash-Next",
        "messages": case["messages"],
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
        "max_tokens": 60000,
        "seed": 1234,
        "stream": False,
    }
    started = time.monotonic()
    result = {
        "label": label,
        "doc_id": doc_id,
        "target": case["target"],
        "started_at": now(),
        "request_sha256": hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
    }
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10800) as response:
            body = json.loads(response.read())
            result["http_status"] = response.status
        choice = body["choices"][0]
        message = choice.get("message") or {}
        content = message.get("content")
        reasoning = message.get("reasoning_content") or message.get("reasoning")
        usage = body.get("usage") or {}
        result.update(
            finish_reason=choice.get("finish_reason"),
            content=content,
            answer=extract_answer(content),
            correct=extract_answer(content) == case["target"],
            reasoning_chars=len(reasoning or ""),
            reasoning_sha256=(hashlib.sha256(reasoning.encode()).hexdigest() if reasoning else None),
            usage=usage,
            response_id=body.get("id"),
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    result["finished_at"] = now()
    with LOCK:
        path = OUT / f"{label}-doc{doc_id}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        tmp.replace(path)
        update_summary()
    return result


def update_summary():
    rows = []
    for path in sorted(OUT.glob("*-doc*.json")):
        rows.append(json.loads(path.read_text()))
    summary = {
        "updated_at": now(),
        "expected": len(DOC_IDS) * len(ENDPOINTS),
        "completed": len(rows),
        "rows": rows,
    }
    tmp = OUT / "summary.json.tmp"
    tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(OUT / "summary.json")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    (OUT / "RUNNING").write_text(now() + "\n")
    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for label, url in ENDPOINTS.items():
            for doc_id in DOC_IDS:
                jobs.append(pool.submit(run_one, label, url, doc_id, cases[doc_id]))
        for job in concurrent.futures.as_completed(jobs):
            job.result()
    (OUT / "COMPLETED").write_text(now() + "\n")
    (OUT / "RUNNING").unlink(missing_ok=True)
    update_summary()


if __name__ == "__main__":
    main()
