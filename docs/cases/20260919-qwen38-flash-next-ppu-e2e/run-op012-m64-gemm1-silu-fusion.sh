#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
result_root=${case_root}/microbench/op012-m64-gemm1-silu-fusion-001
source_script=${case_root}/commands/op012-m64-gemm1-silu-fusion-microbench.py
container=qwen3.8-flash-opt-20260919
expected_container_id=2eafbddebde1b14c691173de29d1965bc48064829a86ee4150056ef1fc5297f7

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test -f "${source_script}"
test ! -e "${result_root}"
if docker exec "${container}" sh -lc "ps -ef | grep '[v]llm serve'"; then
  echo "baseline service is still live; refusing isolated microbenchmark" >&2
  exit 3
fi

mkdir -p "${result_root}"
cp "${source_script}" "${result_root}/benchmark.py"
ppu-smi > "${result_root}/ppu-smi.before.txt"

set +e
docker exec \
  -e CUDA_VISIBLE_DEVICES=0 \
  -w "${result_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${result_root}/benchmark.py' \
  --device 0 --seed 74284 --warmup 20 --repeat 100 --rounds 3 \
  --output '${result_root}/result.json'
" > "${result_root}/console.log" 2>&1
benchmark_rc=$?
set -e

ppu-smi > "${result_root}/ppu-smi.after.txt"
printf 'benchmark_rc=%s\n' "${benchmark_rc}" > "${result_root}/status.txt"

test -s "${result_root}/result.json"
python3 -c '
import json, sys
payload = json.load(open(sys.argv[1]))
allowed = {"passed", "stopped_gate", "stopped_correctness"}
if payload.get("status") not in allowed:
    raise SystemExit("invalid terminal status: %r" % (payload.get("status"),))
' "${result_root}/result.json"

sha256sum \
  "${result_root}/benchmark.py" \
  "${result_root}/result.json" \
  "${result_root}/console.log" \
  "${result_root}/status.txt" \
  "${result_root}/ppu-smi.before.txt" \
  "${result_root}/ppu-smi.after.txt" \
  > "${result_root}/SHA256SUMS"

cat "${result_root}/status.txt"
cat "${result_root}/SHA256SUMS"
