#!/usr/bin/env python3
"""Correlate fw-003 per-request ITL gaps with low-overhead host/PPU samples."""

from collections import defaultdict
from datetime import datetime, timedelta
import glob
import json
from pathlib import Path
import statistics
import sys
import re


root = Path(sys.argv[1]).resolve()
raw_paths = sorted(
    path for path in glob.glob(str(root / "client/MiniMax-M3/diagnostic-*" / "p1024-d256-c64-r*.json"))
    if re.fullmatch(r"p1024-d256-c64-r\d+-[0-9a-f]+\.json", Path(path).name)
)
if len(raw_paths) != 3:
    raise SystemExit(f"expected three raw rounds, got {len(raw_paths)}")
diagnostic_paths = list((root / "client/MiniMax-M3").glob("diagnostic-*/diagnostic.json"))
if len(diagnostic_paths) != 1:
    raise SystemExit(f"expected one diagnostic report, got {len(diagnostic_paths)}")
diagnostic = json.loads(diagnostic_paths[0].read_text(encoding="utf-8"))
profile_by_run = {row["run_id"]: row["profile_requested"] for row in diagnostic["rounds"]}

ppu_by_time = defaultdict(list)
with (root / "timelines/ppu.csv").open(encoding="utf-8") as stream:
    for line in stream:
        parts = [item.strip() for item in line.split(",")]
        if len(parts) != 8:
            continue
        try:
            stamp = datetime.strptime(parts[0], "%Y/%m/%d %H:%M:%S.%f").replace(microsecond=0)
            index = int(parts[1])
            util = float(parts[2])
            memory_util = float(parts[3])
            memory_used = float(parts[4])
            power = float(parts[5])
        except ValueError:
            continue
        ppu_by_time[stamp].append(
            {"index": index, "util": util, "memory_util": memory_util,
             "memory_used_mib": memory_used, "power_w": power}
        )

ppu_samples = []
for stamp, devices in sorted(ppu_by_time.items()):
    if len(devices) != 16:
        continue
    ppu_samples.append(
        {"time": stamp, "device_count": len(devices),
         "util_mean": statistics.mean(row["util"] for row in devices),
         "util_min": min(row["util"] for row in devices),
         "util_max": max(row["util"] for row in devices),
         "power_mean_w": statistics.mean(row["power_w"] for row in devices)}
    )

vmstat = []
with (root / "timelines/vmstat.txt").open(encoding="utf-8") as stream:
    for line in stream:
        parts = line.split()
        if len(parts) != 19 or not parts[0].isdigit():
            continue
        try:
            stamp = datetime.strptime(" ".join(parts[-2:]), "%Y-%m-%d %H:%M:%S")
            vmstat.append({"time": stamp, "r": int(parts[0]), "b": int(parts[1]),
                           "cpu_user": int(parts[12]), "cpu_system": int(parts[13]),
                           "cpu_idle": int(parts[14]), "cpu_iowait": int(parts[15])})
        except ValueError:
            continue


def summarize_samples(rows):
    if not rows:
        return {"samples": 0}
    return {
        "samples": len(rows),
        "ppu_util_mean": statistics.mean(row["util_mean"] for row in rows),
        "ppu_util_min_across_devices": min(row["util_min"] for row in rows),
        "ppu_util_max_across_devices": max(row["util_max"] for row in rows),
        "ppu_all_device_zero_samples": sum(row["util_max"] == 0 for row in rows),
        "ppu_power_mean_w": statistics.mean(row["power_mean_w"] for row in rows),
    }


result = {
    "schema_version": 1,
    "method": {
        "round_start": "for unprofiled rounds only, raw result date minus duration; approximate to about one second because date has second precision and is recorded at result save",
        "profiled_round_wall_time": "not correlated because the result is saved after synchronous multi-rank trace export",
        "token_gap": "(start_times - round minimum start_time) + ttft + cumulative preceding ITLs",
        "ppu_sampling": "16-device means from ppu-smi at two-second intervals",
        "slow_threshold_s": 5.0,
    },
    "rounds": [],
}

for path_text in raw_paths:
    path = Path(path_text)
    raw = json.loads(path.read_text(encoding="utf-8"))
    run_match = re.search(r"-r(\d+)-", path.name)
    if not run_match or int(run_match.group(1)) not in profile_by_run:
        raise SystemExit(f"cannot map raw round to diagnostic: {path.name}")
    run_id = int(run_match.group(1))
    profile_requested = profile_by_run[run_id]
    result_end = datetime.strptime(raw["date"], "%Y%m%d-%H%M%S")
    start = result_end - timedelta(seconds=raw["duration"])
    request_clock_origin = min(raw["start_times"])
    round_ppu = [] if profile_requested else [row for row in ppu_samples if start <= row["time"] <= result_end]
    round_vm = [] if profile_requested else [row for row in vmstat if start <= row["time"] <= result_end]
    gaps = []
    for request_id, (request_start, ttft, itls) in enumerate(
            zip(raw["start_times"], raw["ttfts"], raw["itls"])):
        cursor = start + timedelta(seconds=request_start - request_clock_origin + ttft)
        for token_index, gap_s in enumerate(itls):
            gap_end = cursor + timedelta(seconds=gap_s)
            if gap_s >= 5.0:
                matched_ppu = [] if profile_requested else [row for row in ppu_samples if cursor <= row["time"] <= gap_end]
                matched_vm = [] if profile_requested else [row for row in vmstat if cursor <= row["time"] <= gap_end]
                entry = {
                    "request_id": request_id,
                    "token_index": token_index,
                    "gap_s": gap_s,
                    "approx_start": cursor.isoformat(),
                    "approx_end": gap_end.isoformat(),
                    "ppu": summarize_samples(matched_ppu),
                    "host": {"samples": len(matched_vm)},
                }
                if matched_vm:
                    entry["host"].update(
                        {"cpu_idle_mean": statistics.mean(row["cpu_idle"] for row in matched_vm),
                         "cpu_iowait_max": max(row["cpu_iowait"] for row in matched_vm),
                         "run_queue_max": max(row["r"] for row in matched_vm),
                         "blocked_max": max(row["b"] for row in matched_vm)}
                    )
                gaps.append(entry)
            cursor = gap_end
    gaps.sort(key=lambda row: row["gap_s"], reverse=True)
    round_entry = {
        "file": path.name,
        "run_id": run_id,
        "profile_requested": profile_requested,
        "wall_alignment_valid": not profile_requested,
        "approx_start": start.isoformat(),
        "result_date": result_end.isoformat(),
        "duration_s": raw["duration"],
        "output_throughput": raw["output_throughput"],
        "p99_itl_ms": raw["p99_itl_ms"],
        "slow_gap_count": len(gaps),
        "max_gap_s": max((row["gap_s"] for row in gaps), default=max(max(values) if values else 0 for values in raw["itls"])),
        "round_ppu": summarize_samples(round_ppu) if not profile_requested else {
            "status": "not_correlated",
            "reason": "profile trace export delays result-save wall time",
        },
        "slow_gaps": gaps,
    }
    if round_vm:
        round_entry["round_host"] = {
            "samples": len(round_vm),
            "cpu_idle_mean": statistics.mean(row["cpu_idle"] for row in round_vm),
            "cpu_iowait_max": max(row["cpu_iowait"] for row in round_vm),
            "run_queue_max": max(row["r"] for row in round_vm),
            "blocked_max": max(row["b"] for row in round_vm),
        }
    result["rounds"].append(round_entry)

json.dump(result, sys.stdout, indent=2, sort_keys=True)
sys.stdout.write("\n")
