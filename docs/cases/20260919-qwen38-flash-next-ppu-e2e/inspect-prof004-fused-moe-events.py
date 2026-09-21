#!/usr/bin/env python3
import gzip
import json
from collections import Counter
from pathlib import Path

trace_dir = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-004-p4k-post-op008/traces")
trace = next(trace_dir.glob("dp0_pp0_tp0_*rank0.*.pt.trace.json.gz"))
with gzip.open(trace, "rt", encoding="utf-8") as handle:
    document = json.load(handle)
events = [event for event in document["traceEvents"] if event.get("name") == "fused_moe_kernel"]
arg_keys = Counter()
for event in events:
    arg_keys.update(event.get("args", {}).keys())
output = {
    "trace": str(trace),
    "event_count": len(events),
    "argument_keys": dict(arg_keys),
    "first_events": events[:8],
}
output_path = trace_dir.parent / "summaries/fused-moe-event-samples.json"
output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
print(output_path)
print(json.dumps(output, indent=2, sort_keys=True)[:30000])
