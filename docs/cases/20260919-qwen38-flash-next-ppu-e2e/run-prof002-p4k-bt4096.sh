#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
manifest=${case_root}/transitions/prof-002-p4k-bt4096-service-16/prof-002-p4k-bt4096-service-16-raw.json
profile_root=${case_root}/profiling/prof-002-p4k-bt4096-mixed-tail
trace_dir=${profile_root}/traces
output_dir=${profile_root}/client
mode=${1:?usage: run-prof002-p4k-bt4096.sh dry-run|capture}

test -f "${manifest}"
test -d "${trace_dir}"
python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${manifest}" "${container}" 8030 64 \
  > "${profile_root}/live-service-instance.${mode}.txt"
docker exec "${container}" curl -fsS http://127.0.0.1:8030/health >/dev/null

common=(
  python3 "${case_root}/commands/performance/vllm_profile.py"
  --model Qwen3.8-Flash-Next
  --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next
  --host 127.0.0.1
  --port 8030
  --endpoint /v1/completions
  --case 4096,128,64,64
  --runs 2
  --warmup-rounds 1
  --profile-runs last
  --timeout 1800
  --profile-dir "${trace_dir}"
  --output-dir "${output_dir}"
)

case "${mode}" in
  dry-run)
    test ! -e "${profile_root}/dry-run.json"
    docker exec "${container}" "${common[@]}" --dry-run > "${profile_root}/dry-run.json"
    ;;
  capture)
    test -f "${profile_root}/dry-run.json"
    test ! -e "${output_dir}"
    docker exec "${container}" "${common[@]}" 2>&1 | tee "${profile_root}/capture.console.log"
    ;;
  *)
    echo "mode must be dry-run or capture" >&2
    exit 2
    ;;
esac
