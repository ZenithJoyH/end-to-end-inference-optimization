#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
script=${case_root}/commands/150-qsa-static-bound-universal-microbench.py
result_root=${case_root}/microbench/qsa-static-bound-universal-004
output=${result_root}/result.json
console=${result_root}/console.log

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${script}"
test ! -e "${result_root}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "candidate service must be stopped before isolated microbenchmark" >&2
  exit 3
fi
mkdir "${result_root}"
docker exec "${container}" git -C /workspace/FlagGems status --short > "${result_root}/flaggems-status.before.txt"
test ! -s "${result_root}/flaggems-status.before.txt"
docker cp "${script}" "${container}:/tmp/qsa-static-bound-universal-microbench.py"
ppu-smi > "${result_root}/ppu-smi.before.txt"
docker exec \
  -e CUDA_VISIBLE_DEVICES=8 \
  -w /workspace/FlagGems \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
python3 /tmp/qsa-static-bound-universal-microbench.py \
  --warmup 5 --repeat 20 --output '${output}'
" > "${console}" 2>&1
ppu-smi > "${result_root}/ppu-smi.after.txt"
docker exec "${container}" git -C /workspace/FlagGems status --short > "${result_root}/flaggems-status.after.txt"
test ! -s "${result_root}/flaggems-status.after.txt"
python3 -m json.tool "${output}"
sha256sum "${script}" "${output}" "${console}" \
  "${result_root}/flaggems-status.before.txt" \
  "${result_root}/flaggems-status.after.txt"
