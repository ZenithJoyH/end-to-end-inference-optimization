#!/usr/bin/env python3
"""Correlate frozen acc-010 evaluator responses with proxy completion lines."""

from datetime import datetime
import json
from pathlib import Path
import re


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)
RECOVERED = ROOT / "diagnostics/accdiag-008-current-output-replay-20260924/formal-http-recovered"
FORMAL = ROOT / "evaluation/formal-run.log"
PROXY = ROOT / "evaluation/proxy.log"
OUT = RECOVERED / "route-match.json"
EVAL_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}):(\d{2}:\d{2}:\d{2}) INFO .*"
    r"get generate_until response, use ([0-9.]+)s"
)
PROXY_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) INFO "
    r"complete backend=([01]) status=(\d+) elapsed=([0-9.]+)"
)


index = json.loads((RECOVERED / "index.json").read_text(encoding="utf-8"))
records = index["records"]
if len(records) != 198 or len({r["doc_id"] for r in records}) != 198:
    raise RuntimeError("invalid recovered formal index")

eval_lines = FORMAL.read_text(encoding="utf-8", errors="replace").splitlines()
proxy_lines = PROXY.read_text(encoding="utf-8", errors="replace").splitlines()
proxy_responses = []
for line_no, line in enumerate(proxy_lines, 1):
    match = PROXY_RE.search(line)
    if match is None:
        continue
    stamp, backend, status, elapsed = match.groups()
    proxy_responses.append(
        {
            "line": line_no,
            "time": datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S,%f"),
            "backend": int(backend),
            "status": int(status),
            "elapsed": float(elapsed),
        }
    )

matches = []
used_proxy_lines = set()
errors = []
pending = []


def add_match(item, proxy, method):
    record = item["record"]
    eval_time = item["eval_time"]
    eval_elapsed = item["eval_elapsed"]
    if proxy["line"] in used_proxy_lines:
        raise RuntimeError(f"proxy line reused: {proxy['line']}")
    used_proxy_lines.add(proxy["line"])
    matches.append(
        {
            "doc_id": record["doc_id"],
            "backend": proxy["backend"],
            "port": (8000, 8010)[proxy["backend"]],
            "proxy_log_line": proxy["line"],
            "eval_log_line": record["response_log_line"],
            "elapsed_difference_seconds": round(proxy["elapsed"] - eval_elapsed, 3),
            "completion_time_offset_seconds": round((proxy["time"] - eval_time).total_seconds(), 3),
            "matching_method": method,
            "strict_correct": record["strict_correct"],
            "finish_reason": record["finish_reason"],
            "completion_tokens": record["completion_tokens"],
        }
    )


for record in records:
    line_no = record["response_log_line"]
    line = eval_lines[line_no - 1]
    parsed = EVAL_RE.search(line)
    if parsed is None:
        errors.append({"doc_id": record["doc_id"], "reason": "eval-line-unparsed", "line": line_no})
        continue
    date, clock, elapsed_text = parsed.groups()
    eval_time = datetime.strptime(f"{date} {clock}", "%Y-%m-%d %H:%M:%S")
    eval_elapsed = float(elapsed_text)
    candidates = [
        p
        for p in proxy_responses
        if p["status"] == 200
        and abs((p["time"] - eval_time).total_seconds()) <= 2.0
        and abs(p["elapsed"] - eval_elapsed) <= 0.1
    ]
    if not candidates:
        errors.append(
            {
                "doc_id": record["doc_id"],
                "reason": "no-proxy-candidate",
                "eval_line": line_no,
                "eval_elapsed": eval_elapsed,
            }
        )
        continue
    pending.append(
        {
            "record": record,
            "eval_time": eval_time,
            "eval_elapsed": eval_elapsed,
            "candidates": candidates,
        }
    )

while pending:
    resolved = []
    for item in pending:
        available = [p for p in item["candidates"] if p["line"] not in used_proxy_lines]
        if len(available) == 1:
            add_match(item, available[0], "unique-timestamp-elapsed")
            resolved.append(item)
    for item in resolved:
        pending.remove(item)
    if not resolved:
        break

# The remaining two formal responses may finish in the same second and have
# near-identical durations. Resolve only complete same-candidate groups by
# their independent evaluator/proxy completion order; otherwise fail closed.
while pending:
    item = pending[0]
    available = sorted(
        [p for p in item["candidates"] if p["line"] not in used_proxy_lines],
        key=lambda p: p["line"],
    )
    key = {p["line"] for p in available}
    group = [
        x
        for x in pending
        if {p["line"] for p in x["candidates"] if p["line"] not in used_proxy_lines}
        == key
    ]
    if not key or len(group) != len(key):
        errors.append(
            {
                "reason": "ambiguous-proxy-group",
                "docs": [x["record"]["doc_id"] for x in group],
                "proxy_lines": sorted(key),
            }
        )
        break
    group.sort(key=lambda x: x["record"]["response_log_line"])
    for x, p in zip(group, available):
        if not 0 <= x["eval_elapsed"] - p["elapsed"] <= 0.1:
            errors.append(
                {
                    "reason": "chronological-pair-latency-invalid",
                    "doc_id": x["record"]["doc_id"],
                    "proxy_line": p["line"],
                }
            )
            break
        add_match(x, p, "chronological-tie-with-latency-check")
    for x in group:
        pending.remove(x)

if errors or len(matches) != 198:
    print(json.dumps({"matched": len(matches), "errors": errors[:30]}, ensure_ascii=False))
    raise RuntimeError("cannot establish full one-to-one formal route mapping")

summary = {}
for backend in (0, 1):
    subset = [m for m in matches if m["backend"] == backend]
    summary[str(backend)] = {
        "port": (8000, 8010)[backend],
        "unique_docs": len(subset),
        "strict_correct": sum(m["strict_correct"] for m in subset),
        "length_caps": sum(m["finish_reason"] == "length" for m in subset),
        "completed_wrong": sum(
            not m["strict_correct"] and m["finish_reason"] == "stop" for m in subset
        ),
    }
if sum(v["unique_docs"] for v in summary.values()) != 198:
    raise RuntimeError("backend counts do not cover 198 docs")
if sum(v["strict_correct"] for v in summary.values()) != 174:
    raise RuntimeError("backend correctness does not match frozen score")

result = {
    "formal_log": str(FORMAL),
    "proxy_log": str(PROXY),
    "backend_mapping": {"0": 8000, "1": 8010},
    "matching_tolerances": {"completion_time_seconds": 2.0, "elapsed_seconds": 0.1},
    "matching_methods": dict((method, sum(m["matching_method"] == method for m in matches)) for method in {m["matching_method"] for m in matches}),
    "summary": summary,
    "matches": sorted(matches, key=lambda m: m["doc_id"]),
}
with OUT.open("x", encoding="utf-8") as handle:
    handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(
    json.dumps(
        {
            "matched": len(matches),
            "summary": summary,
            "doc168": next(m for m in matches if m["doc_id"] == 168),
            "out": str(OUT),
        },
        ensure_ascii=False,
    )
)
