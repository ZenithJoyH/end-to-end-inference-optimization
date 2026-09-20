#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
perf_dir=${case_root}/commands/performance
manifest=${case_root}/manifests/candidate-maxseq64-bt8192-moe-bm16-service-screen-12.json
plan=${perf_dir}/perf-p4k-mixed-entry-plan.json
contract=${perf_dir}/perf-p4k-mixed-comparison.json
output_root=${case_root}/performance
run_id=p4k-maxbt8192-mixed-candidate-01
dry_run=${output_root}/${run_id}.dry-run.json
console=${output_root}/${run_id}.console.log

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test ! -e "${output_root}/${run_id}"
test ! -e "${dry_run}"
test ! -e "${console}"
python3 - "${manifest}" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
assert manifest["launch_config"]["max_num_seqs"] == 64
assert manifest["launch_config"]["max_num_batched_tokens"] == 8192
assert manifest["launch_config"]["enable_prefix_caching"] is False
assert manifest["performance_context"]["device_ids"] == [str(i) for i in range(8, 16)]
assert manifest["base_url"] == "http://127.0.0.1:8030/v1/completions"
PY
python3 "${perf_dir}/verify-live-service-manifest.py" "${manifest}" "${container}" 8030 64
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null

bash "${case_root}/commands/27-run-graph-replay-smoke.sh" \
  p4k-maxbt8192-graph-01 "${manifest}" 64 \
  "${case_root}/smoke/moe-bm16-restored-graph-02/canonical.json"

docker exec "${container}" \
  python3 "${perf_dir}/vllm_perf.py" \
  --config "${plan}" \
  --comparison-contract "${contract}" \
  --service-manifest "${manifest}" \
  --role candidate \
  --run-id "${run_id}" \
  --scope performance_only \
  --output-dir "${output_root}" \
  --dry-run > "${dry_run}"

docker exec "${container}" \
  python3 "${perf_dir}/vllm_perf.py" \
  --config "${plan}" \
  --comparison-contract "${contract}" \
  --service-manifest "${manifest}" \
  --role candidate \
  --run-id "${run_id}" \
  --scope performance_only \
  --output-dir "${output_root}" \
  2>&1 | tee "${console}"
