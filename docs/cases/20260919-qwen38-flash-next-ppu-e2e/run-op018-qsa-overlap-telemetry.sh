#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: run-op018-qsa-overlap-telemetry.sh prefill|mixed PORT OUTPUT_DIR}
port=${2:?missing diagnostic service port}
output_dir=${3:?missing unique output directory}
case "${phase}" in prefill|mixed) ;; *) exit 2 ;; esac
case "${port}" in 8020|8031) ;; *) echo "unexpected diagnostic port" >&2; exit 2 ;; esac
test ! -e "${output_dir}"
mkdir -p "${output_dir}"
arm=${output_dir}/arm.json
sample_id=op018-p4k-${phase}-001

if [[ "${phase}" == prefill ]]; then
  input=4096 output=1 concurrency=1 requests=1 min_runs=1 max_runs=1
else
  # One finite-batch client invocation with two requests: request 1 enters
  # decode before request 2 is admitted, producing a real new+cached step.
  input=4096 output=128 concurrency=2 requests=2 min_runs=2 max_runs=64
fi

python3 - "${arm}" "${sample_id}" "${phase}" "${min_runs}" "${max_runs}" <<'PY'
import json, sys
path, sample, phase, minimum, maximum = sys.argv[1:]
json.dump({"sample_id": sample, "expected_phase": phase,
           "min_request_runs": int(minimum), "max_request_runs": int(maximum)},
          open(path, "w", encoding="utf-8"), indent=2, sort_keys=True)
PY

curl -fsS "http://127.0.0.1:${port}/health" > "${output_dir}/health.json"
find "${output_dir}" -maxdepth 1 -type f -printf '%f %s %TY-%Tm-%TdT%TH:%TM:%TS\n' \
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

find "${output_dir}" -maxdepth 1 -type f -printf '%f %s %TY-%Tm-%TdT%TH:%TM:%TS\n' \
  | sort > "${output_dir}/inventory.after.txt"
result=${output_dir}/${sample_id}.rank0.json
test "${client_rc}" -eq 0
test -s "${result}"
python3 - "${result}" "${phase}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["observed_phase"] == sys.argv[2]
assert data["rows"] >= 4096
assert data["large_host_tensor_copy"] is False
assert all(data["group_rows"][r]["coverage"] is not None for r in ("2", "4", "8", "16"))
PY
sha256sum "${result}" "${output_dir}/native-client.json" > "${output_dir}/SHA256SUMS"
printf '%s\n' "diagnostic-only: client timing is invalid because telemetry synchronizes rank0"
