#!/usr/bin/env bash
set -euo pipefail

label=${1:?usage: run-fw006-milestone.sh LABEL}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
root=${case_dir}/performance/fw006-${label}
runner=${case_dir}/commands/performance/vllm_profile.py
container=minimaxM3-opt-20260921

test -f "${runner}"
test ! -e "${root}"
mkdir -p "${root}/client"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
docker exec "${container}" pgrep -af \
  '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)' \
  > "${root}/service-argv.txt"
docker exec "${container}" bash -lc \
  'cd /workspace/FlagGems && git rev-parse HEAD && git status --short && git diff -- src/flag_gems/utils/models/sql.py' \
  > "${root}/flaggems-state.txt"

docker exec "${container}" python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,256,64,128 --runs 3 --warmup-rounds 0 --no-profile \
  --timeout 1800 --output-dir "${root}/client" --dry-run > "${root}/dry-run.json"

docker exec "${container}" python3 "${runner}" \
  --model MiniMax-M3 --tokenizer /mnt/cpfs/models/MiniMax-M3 \
  --host 127.0.0.1 --port 8023 --endpoint /v1/completions \
  --case 1024,256,64,128 --runs 3 --warmup-rounds 0 --no-profile \
  --timeout 1800 --output-dir "${root}/client" > "${root}/benchmark.console.log" 2>&1

diagnostic=$(find "${root}/client/MiniMax-M3" -type f -name diagnostic.json -print -quit)
test -n "${diagnostic}"
python3 "${case_dir}/commands/performance/summarize-request-waves.py" \
  "$(dirname "${diagnostic}")" 'p1024-d256-c64-r?-????????.json' \
  > "${root}/request-wave-summary.json"
sha256sum "${root}/dry-run.json" "${root}/benchmark.console.log" \
  "${root}/request-wave-summary.json" "${root}/service-argv.txt" \
  "${root}/flaggems-state.txt" > "${root}/SHA256SUMS.control"
