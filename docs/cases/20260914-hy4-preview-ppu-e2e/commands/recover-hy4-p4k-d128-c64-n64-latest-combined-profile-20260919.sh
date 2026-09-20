#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
profile_id=p4k-d128-c64-n64-latest-combined-reprofile-20260919-13
profile_root="${case_dir}/profiling/${profile_id}"
trace_dir="${profile_root}/traces"
result_dir="${case_dir}/results/profiling/${profile_id}"
commands_dir="${case_dir}/commands"

test "$(find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' | wc -l)" -eq 16
for rank in $(seq 0 15); do
  test "$(find "${trace_dir}" -maxdepth 1 -type f -name "*_rank${rank}.*.json.gz" | wc -l)" -eq 1
done

find "${trace_dir}" -maxdepth 1 -type f -printf '%P %s %T@\n' | sort >"${profile_root}/trace-inventory-after-1.txt"
sleep 10
find "${trace_dir}" -maxdepth 1 -type f -printf '%P %s %T@\n' | sort >"${profile_root}/trace-inventory-after-2.txt"
cmp "${profile_root}/trace-inventory-after-1.txt" "${profile_root}/trace-inventory-after-2.txt"
find "${trace_dir}" -maxdepth 1 -type f -name '*.json.gz' -print0 | sort -z | xargs -0 sha256sum >"${profile_root}/trace-inventory-after.sha256"

sampled_json="${result_dir}/phase-analysis-sampled.json"
cpu_json="${result_dir}/phase-analysis-rank0-cpu.json"
indexer_json="${result_dir}/indexer-breakdown-rank0.json"
indexer_md="${result_dir}/indexer-breakdown-rank0.md"
rank0_trace="$(find "${trace_dir}" -maxdepth 1 -type f -name '*_rank0.*.json.gz' -print -quit)"
test -n "${rank0_trace}"

python3 "${commands_dir}/analyze-hy4-profile-sampled-phases-20260915.py" \
  --trace-dir "${trace_dir}" --output "${sampled_json}" --top 120 --analyzed-ranks 0,1,15
python3 "${commands_dir}/analyze_hy4_indexer_breakdown_v2.py" \
  "${rank0_trace}" "${indexer_json}" "${indexer_md}"
python3 "${commands_dir}/analyze-hy4-profile-rank0-cpu-phases-20260915.py" \
  --trace-dir "${trace_dir}" --output "${cpu_json}" --top 120 --analyzed-ranks 0

test -s "${sampled_json}"
test -s "${cpu_json}"
test -s "${indexer_json}"
test -s "${indexer_md}"
python3 - "${result_dir}/analysis-status.json" <<'PY'
import json
import sys
from datetime import datetime, timezone

output = sys.argv[1]
payload = {
    "status": "complete_with_client_stop_profile_timeout",
    "trace_files": 16,
    "trace_export_stable": True,
    "deeply_analyzed_ranks": [0, 1, 15],
    "indexer_rank": 0,
    "service_stopped": True,
    "port_8010_released": True,
    "profiler_on_timing_claim": "diagnostic_only",
    "completed_at": datetime.now(timezone.utc).isoformat(),
}
with open(output, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

echo "PASS: ${profile_id} stable traces recovered and analyzed"
