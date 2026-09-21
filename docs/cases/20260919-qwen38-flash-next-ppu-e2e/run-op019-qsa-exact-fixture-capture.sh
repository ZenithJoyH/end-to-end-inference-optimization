#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op019-qsa-exact-fixture-capture.sh prefill|mixed PORT OUTPUT_DIR}
port=${2:?missing diagnostic service port}
output_dir=${3:?missing unique output directory}
case "${phase}" in prefill|mixed) ;; *) echo "invalid phase" >&2; exit 2 ;; esac
case "${port}" in 8031) ;; *) echo "unexpected diagnostic port" >&2; exit 2 ;; esac
test -d "${output_dir}"
test -s "${output_dir}/arm.json"
sample_id=op019-p4k-${phase}-fixture-001
test ! -e "${output_dir}/${sample_id}"

if [[ "${phase}" == prefill ]]; then
  input=4096 output=1 concurrency=1 requests=1
else
  input=4096 output=128 concurrency=2 requests=2
fi

curl -fsS "http://127.0.0.1:${port}/health" > "${output_dir}/health.before.json"
find "${output_dir}" -maxdepth 2 -type f -printf '%P %s %TY-%Tm-%TdT%TH:%TM:%TS\n' \
  | sort > "${output_dir}/inventory.before.txt"

set +e
docker exec -i qwen3.8-flash-opt-candidate-20260919 bash -s -- \
  "${port}" "${input}" "${output}" "${concurrency}" "${requests}" "${output_dir}" \
  > "${output_dir}/client.stdout" 2> "${output_dir}/client.stderr" <<'BENCH'
set -euo pipefail
port=$1 input=$2 output=$3 concurrency=$4 requests=$5 output_dir=$6
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:${LD_LIBRARY_PATH:-}
exec vllm bench serve --backend vllm \
  --model /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --served-model-name Qwen3.8-Flash-Next \
  --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --host 127.0.0.1 --port "${port}" --endpoint /v1/completions \
  --dataset-name random --seed 42 --temperature 0 --random-range-ratio 0 \
  --random-input-len "${input}" --random-output-len "${output}" \
  --max-concurrency "${concurrency}" --num-prompts "${requests}" \
  --request-rate inf --burstiness 1 --ignore-eos \
  --save-result --save-detailed --result-dir "${output_dir}" \
  --result-filename native-client.json
BENCH
client_rc=$?
set -e

find "${output_dir}" -maxdepth 2 -type f -printf '%P %s %TY-%Tm-%TdT%TH:%TM:%TS\n' \
  | sort > "${output_dir}/inventory.after.txt"
test "${client_rc}" -eq 0
test -s "${output_dir}/native-client.json"
test -s "${output_dir}/${sample_id}/manifest.json"
test -s "${output_dir}/${sample_id}/selected.int32.bin"
test ! -e "${output_dir}/arm.json"
printf '%s\n' "diagnostic-only: fixture capture synchronizes and copies selected indices; client timing is invalid"
