#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
control=${case_root}/commands/performance
runner=${control}/vllm_perf.py
plan50=${control}/perf-op014-screen-service50.json
plan51=${control}/perf-op014-screen-service51.json
manifest50=${case_root}/manifests/post-prof005-native-service50.json
instance51=${case_root}/smoke/op014-service51-graph-02/service-instance.json
manifest51=${case_root}/manifests/op014-service51.json
output_root=${case_root}/performance
run50=op014-screen-service50-baseline-01
run51=op014-screen-service51-candidate-01

for path in "${runner}" "${plan50}" "${plan51}" "${manifest50}" "${instance51}"; do
  test -f "${path}"
done
for path in "${manifest51}" "${output_root}/${run50}" "${output_root}/${run51}" \
  "${output_root}/${run50}.dry-run.json" "${output_root}/${run51}.dry-run.json" \
  "${output_root}/${run50}.console.log" "${output_root}/${run51}.console.log"; do
  test ! -e "${path}" || { echo "refusing to overwrite ${path}" >&2; exit 2; }
done

python3 "${control}/verify-live-service-manifest.py" "${manifest50}" \
  "${container}" 8030 64 >/dev/null
curl -fsS http://127.0.0.1:8030/health >/dev/null
curl -fsS http://127.0.0.1:8031/health >/dev/null

python3 - "${manifest50}" "${instance51}" "${manifest51}" <<'PY'
import json
import sys
from pathlib import Path

source = json.load(open(sys.argv[1], encoding="utf-8"))
instance = json.load(open(sys.argv[2], encoding="utf-8"))
argv = instance["argv"]
source["base_url"] = "http://127.0.0.1:8031/v1/completions"
source["service_instance_id"] = instance["service_instance_id"]
source["plugin_file_sha256"] = instance["plugin_file_sha256"]
source["launch_config"]["launch_args"] = argv[argv.index("serve"):]
source["launch_config"]["selected_environment"].update(
    instance["selected_environment"]
)
source["performance_context"]["device_ids"] = [str(value) for value in range(8)]
Path(sys.argv[3]).write_text(
    json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY
python3 "${control}/verify-live-service-manifest.py" "${manifest51}" \
  "${container}" 8031 64 >/dev/null

run_role() {
  local role=$1
  local plan=$2
  local manifest=$3
  local run_id=$4
  docker exec "${container}" python3 "${runner}" \
    --config "${plan}" --service-manifest "${manifest}" --role "${role}" \
    --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" \
    --dry-run > "${output_root}/${run_id}.dry-run.json"
  docker exec "${container}" python3 "${runner}" \
    --config "${plan}" --service-manifest "${manifest}" --role "${role}" \
    --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" \
    2>&1 | tee "${output_root}/${run_id}.console.log"
}

# Keep clients serial so shared host CPU/network activity does not overlap.
run_role baseline "${plan50}" "${manifest50}" "${run50}"
run_role candidate "${plan51}" "${manifest51}" "${run51}"

sha256sum "${plan50}" "${plan51}" "${manifest50}" "${manifest51}" \
  "${output_root}/${run50}/run-record.json" \
  "${output_root}/${run51}/run-record.json"
