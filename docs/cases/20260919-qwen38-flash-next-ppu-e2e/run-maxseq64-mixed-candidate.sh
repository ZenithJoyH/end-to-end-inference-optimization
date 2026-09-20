#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
plan=${case_root}/commands/performance/perf-mixed-p1k-plan-v2.json
contract=${case_root}/commands/performance/perf-maxseq-mixed-comparison.json
service_manifest=${case_root}/manifests/candidate-maxseq64-service-comparison.json
run_id=${1:-maxseq64-mixed-candidate-01}
output_root=${case_root}/performance

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test -f "${plan}"
test -f "${contract}"
test -f "${service_manifest}"
test ! -e "${output_root}/${run_id}"
test ! -e "${output_root}/${run_id}.console.log"

python3 - "${service_manifest}" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
assert manifest["launch_config"]["max_num_seqs"] == 64
assert manifest["launch_config"]["enable_prefix_caching"] is False
assert manifest["performance_context"]["prefix_cache_state"] == "disabled"
assert manifest["performance_context"]["device_ids"] == [str(i) for i in range(8, 16)]
assert manifest["base_url"] == "http://127.0.0.1:8030/v1/completions"
PY

docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null
python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${service_manifest}" "${container}" 8030 64

docker exec "${container}" \
  python3 "${case_root}/commands/performance/vllm_perf.py" \
  --config "${plan}" \
  --comparison-contract "${contract}" \
  --service-manifest "${service_manifest}" \
  --role candidate \
  --run-id "${run_id}" \
  --scope performance_only \
  --output-dir "${output_root}" \
  2>&1 | tee "${output_root}/${run_id}.console.log"
