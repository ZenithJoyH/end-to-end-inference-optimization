#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
script=${case_root}/commands/245-general-mm-out-provider-microbench.py
result_root=${case_root}/microbench/general-mm-out-provider-002

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test -f "${script}"
test ! -e "${result_root}"
curl -fsS http://127.0.0.1:8030/v1/models >/dev/null

python3 - <<'PY'
import urllib.request

text = urllib.request.urlopen("http://127.0.0.1:8030/metrics", timeout=10).read().decode()
values = {}
required = {"vllm:num_requests_running", "vllm:num_requests_waiting"}
for line in text.splitlines():
    if line.startswith("vllm:") and not line.startswith("#"):
        name, value = line.split()[:2]
        base = name.split("{", 1)[0]
        if base in required:
            values[base] = float(value)
if set(values) != required:
    raise SystemExit(f"missing service idle metrics: {values}")
if any(value != 0 for value in values.values()):
    raise SystemExit(f"candidate service is not idle: {values}")
PY

mkdir -p "${case_root}/microbench"
ppu-smi > "${case_root}/microbench/ppu-smi.before-general-mm-out-provider-002.txt"

docker exec \
  -e CUDA_VISIBLE_DEVICES=15 \
  -w "${case_root}" \
  "${container}" \
  bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
python3 '${script}' \
  --warmup 10 --repeat 200 --rounds 3 --device 0 \
  --output '${result_root}/result.json'
" > "${case_root}/microbench/general-mm-out-provider-002.console.log" 2>&1

ppu-smi > "${case_root}/microbench/ppu-smi.after-general-mm-out-provider-002.txt"
sha256sum \
  "${script}" "${result_root}/result.json" \
  "${case_root}/microbench/general-mm-out-provider-002.console.log"
