#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-20260919
expected_container_id=2eafbddebde1b14c691173de29d1965bc48064829a86ee4150056ef1fc5297f7
perf_dir=${case_root}/commands/performance
manifest=${case_root}/manifests/baseline-maxseq64-bt4096-moe-bm16-op006-revert-service-25.json
plan=${case_root}/commands/167-perf-p4k-mixed-entry-plan-revert8020.json
contract=${perf_dir}/perf-p4k-mixed-comparison.json
output_root=${case_root}/performance
run_id=p4k-qsa-static-bound8448-revert-02
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
assert manifest["launch_config"]["max_num_batched_tokens"] == 4096
assert manifest["launch_config"]["enable_prefix_caching"] is False
assert manifest["launch_config"]["moe_tuned_config_folder"].endswith(
    "/configs/moe-bm16-decode-only-01"
)
assert manifest["performance_context"]["device_ids"] == [str(i) for i in range(8)]
assert manifest["base_url"] == "http://127.0.0.1:8020/v1/completions"
PY
python3 "${perf_dir}/verify-live-service-manifest.py" "${manifest}" "${container}" 8020 64
docker exec "${container}" curl -fsS http://127.0.0.1:8020/health >/dev/null

bash "${case_root}/commands/165-run-graph-replay-smoke-general.sh" \
  p4k-op006-revert-graph-03 "${manifest}" 64 \
  "${case_root}/smoke/moe-bm16-restored-graph-02/canonical.json" \
  "${container}" 8020

docker exec "${container}" \
  python3 "${perf_dir}/vllm_perf.py" \
  --config "${plan}" \
  --comparison-contract "${contract}" \
  --service-manifest "${manifest}" \
  --role revert \
  --run-id "${run_id}" \
  --scope performance_only \
  --output-dir "${output_root}" \
  --dry-run > "${dry_run}"

docker exec "${container}" \
  python3 "${perf_dir}/vllm_perf.py" \
  --config "${plan}" \
  --comparison-contract "${contract}" \
  --service-manifest "${manifest}" \
  --role revert \
  --run-id "${run_id}" \
  --scope performance_only \
  --output-dir "${output_root}" \
  2>&1 | tee "${console}"
