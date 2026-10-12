#!/usr/bin/env python3
"""Recover HTTP-level formal overlap for doc 168; never infer vLLM batches."""

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)
PROXY = ROOT / "evaluation/proxy.log"
ROUTES = (
    ROOT
    / "diagnostics/accdiag-008-current-output-replay-20260924/"
    "formal-http-recovered/route-match.json"
)
OUT = (
    ROOT
    / "diagnostics/accdiag-011-port8000-sustained-cohort-20260924/"
    "cohort-plan.json"
)
LINE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) INFO "
    r"complete backend=([01]) status=(\d+) elapsed=([0-9.]+)"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


routes = json.loads(ROUTES.read_text(encoding="utf-8"))
matches = routes["matches"]
if len(matches) != 198 or len({m["doc_id"] for m in matches}) != 198:
    raise RuntimeError("route-match lacks 198 unique docs")

proxy_by_line = {}
for line_no, text in enumerate(PROXY.open(encoding="utf-8", errors="replace"), 1):
    match = LINE.search(text)
    if match is None:
        continue
    stamp, backend, status, elapsed = match.groups()
    proxy_by_line[line_no] = {
        "end": datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S,%f"),
        "backend": int(backend),
        "status": int(status),
        "elapsed": float(elapsed),
    }

intervals = []
for match in matches:
    proxy = proxy_by_line.get(match["proxy_log_line"])
    if proxy is None or proxy["backend"] != match["backend"] or proxy["status"] != 200:
        raise RuntimeError(f"proxy/route mismatch for doc {match['doc_id']}")
    end = proxy["end"]
    start = end - timedelta(seconds=proxy["elapsed"])
    intervals.append({"doc_id": match["doc_id"], "backend": match["backend"],
                      "start": start, "end": end, "elapsed_seconds": proxy["elapsed"],
                      "completion_tokens": match["completion_tokens"],
                      "finish_reason": match["finish_reason"],
                      "strict_correct": match["strict_correct"]})

target = next(x for x in intervals if x["doc_id"] == 168)
if target["backend"] != 0:
    raise RuntimeError("formal doc168 was not on backend0")
peers = []
for item in intervals:
    if item["backend"] != 0 or item["doc_id"] == 168:
        continue
    overlap = max(0.0, (min(item["end"], target["end"]) -
                        max(item["start"], target["start"])).total_seconds())
    if overlap <= 0:
        continue
    peers.append({
        "doc_id": item["doc_id"],
        "start_offset_seconds": round((item["start"] - target["start"]).total_seconds(), 3),
        "end_offset_seconds": round((item["end"] - target["start"]).total_seconds(), 3),
        "overlap_seconds": round(overlap, 3),
        "completion_tokens": item["completion_tokens"],
        "finish_reason": item["finish_reason"],
        "strict_correct": item["strict_correct"],
    })
peers.sort(key=lambda x: (-x["overlap_seconds"], x["doc_id"]))
active_at_start = sum(x["start_offset_seconds"] <= 0 < x["end_offset_seconds"] for x in peers)
events = [(0.0, 1), (target["elapsed_seconds"], -1)]
for peer in peers:
    events.extend(((max(0.0, peer["start_offset_seconds"]), 1),
                   (min(target["elapsed_seconds"], peer["end_offset_seconds"]), -1)))
events.sort(key=lambda pair: (pair[0], pair[1]))
running = 0
max_overlap = 0
for _, change in events:
    running += change
    max_overlap = max(running, max_overlap)

result = {
    "source_sha256": {"proxy_log": digest(PROXY), "route_match": digest(ROUTES)},
    "scope": "HTTP request intervals reconstructed from proxy completion and elapsed; not internal scheduler cohorts",
    "target": {"doc_id": 168, "backend": 0, "port": 8000,
               "formal_start": target["start"].isoformat(),
               "formal_end": target["end"].isoformat(),
               "elapsed_seconds": target["elapsed_seconds"],
               "completion_tokens": target["completion_tokens"],
               "finish_reason": target["finish_reason"]},
    "overlapping_peer_count": len(peers),
    "active_peer_count_at_target_start": active_at_start,
    "peak_http_inflight_in_target_interval": max_overlap,
    "peers_by_overlap": peers,
}
OUT.parent.mkdir(parents=True, exist_ok=False)
with OUT.open("x", encoding="utf-8") as handle:
    handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"out": str(OUT), "target": result["target"],
                  "overlapping_peer_count": len(peers),
                  "active_peer_count_at_target_start": active_at_start,
                  "peak_http_inflight_in_target_interval": max_overlap,
                  "top_peers": peers[:40]}, ensure_ascii=False))
