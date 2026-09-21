#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op021-qsa-producer-fixture-capture.sh prefill|mixed PORT OUTPUT_DIR}
port=${2:?missing isolated eager service port}
output_dir=${3:?missing unique output directory}
case "${phase}" in prefill|mixed) ;; *) echo "invalid phase" >&2; exit 2 ;; esac
test "${port}" = 8031
test -d "${output_dir}"
test -s "${output_dir}/arm.json"
sample_id=op021-p4k-${phase}-producer-001
test ! -e "${output_dir}/${sample_id}"

# Refuse a non-eager or non-isolated endpoint.  The lifecycle wrapper must have
# recorded the exact root process before invoking this request runner.
python3 - "${port}" <<'PY'
import os, sys
port = sys.argv[1]
matches = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if "serve" in argv and "--port" in argv and argv[argv.index("--port") + 1] == port:
        matches.append(argv)
if len(matches) != 1 or "--enforce-eager" not in matches[0]:
    raise SystemExit("expected exactly one isolated --enforce-eager service on port 8031")
PY
curl -fsS "http://127.0.0.1:${port}/health" > "${output_dir}/health.before.json"

if [[ "${phase}" == prefill ]]; then
  output=1 concurrency=1 requests=1
else
  output=128 concurrency=2 requests=2
fi

# Random dataset only.  Do not use --save-detailed: no prompt/token ids are
# persisted by this runner, and capture-run timings are explicitly invalid.
docker exec -i qwen3.8-flash-opt-candidate-20260919 bash -s -- \
  "${port}" "${output}" "${concurrency}" "${requests}" <<'BENCH'
set -euo pipefail
port=$1 output=$2 concurrency=$3 requests=$4
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}
exec vllm bench serve --backend vllm \
  --model /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --served-model-name Qwen3.8-Flash-Next \
  --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --host 127.0.0.1 --port "${port}" --endpoint /v1/completions \
  --dataset-name random --seed 42 --temperature 0 --random-range-ratio 0 \
  --random-input-len 4096 --random-output-len "${output}" \
  --max-concurrency "${concurrency}" --num-prompts "${requests}" \
  --request-rate inf --burstiness 1 --ignore-eos
BENCH

test -s "${output_dir}/${sample_id}/manifest.json"
test -s "${output_dir}/${sample_id}/index_q.bfloat16.bin"
test -s "${output_dir}/${sample_id}/compressed_k.bfloat16.bin"
test -s "${output_dir}/${sample_id}/compressed_page_table.int32.bin"
test -s "${output_dir}/${sample_id}/selected.int32.bin"
test ! -e "${output_dir}/arm.json"
printf '%s\n' "diagnostic-only: capture timing is invalid"
