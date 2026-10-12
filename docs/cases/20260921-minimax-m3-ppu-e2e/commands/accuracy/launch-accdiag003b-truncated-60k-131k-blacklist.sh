#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
experiment_id=accdiag-003b-gpqa-truncated-60k-131k-blacklist
root=${case_dir}/accuracy/${experiment_id}
source_root=${case_dir}/accuracy/accdist-001-gpqa-c64-multiseed3
runner=${case_dir}/commands/run-accdiag003-truncated-60k.py
service_log=${case_dir}/logs/op003-thead-yaml-entrypoint-131k-server.log
container=minimaxM3-opt-20260921

test ! -e "${root}"
test -f "${source_root}/aggregate-result.json"
test -x "${runner}"
curl -fsS --max-time 5 http://127.0.0.1:8023/health >/dev/null
mapfile -t service_pids < <(docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)')
test "${#service_pids[@]}" -eq 1
service_argv=$(docker exec "${container}" ps -o args= -p "${service_pids[0]}")
grep -F -- '--max-model-len 131072' <<<"${service_argv}" >/dev/null
grep -F -- '--max-num-seqs 32' <<<"${service_argv}" >/dev/null
grep -F -- '--no-enable-prefix-caching' <<<"${service_argv}" >/dev/null
grep -F 'Capturing CUDA graphs (decode, FULL): 100%' "${service_log}" >/dev/null
grep -F 'Application startup complete' "${service_log}" >/dev/null
test "$(grep -Ec 'illegal memory|Engine core initialization failed|cudnn_convolution.py|flag_gems/ops/conv3d.py' "${service_log}" || true)" -eq 0
docker exec "${container}" grep -F -- '- conv3d' /workspace/vllm-plugin-FL/vllm_fl/dispatch/config/thead.yaml >/dev/null
docker exec "${container}" grep -F -- '- cudnn_convolution' /workspace/vllm-plugin-FL/vllm_fl/dispatch/config/thead.yaml >/dev/null

mkdir -p "${root}/control"
cp "${runner}" "${root}/control/"
date --iso-8601=seconds > "${root}/launched-at.txt"
printf '%s\n' 'minimax-m3-accdiag003-truncated-60k' > "${root}/heartbeat-automation-id.txt"
printf '%s\n' "${service_argv}" > "${root}/service-argv.txt"
docker inspect "${container}" > "${root}/container.inspect.json"
docker top "${container}" -eo pid,ppid,etimes,stat,cmd > "${root}/processes.preflight.txt"
docker exec "${container}" git -C /workspace/vllm-plugin-FL diff -- vllm_fl/dispatch/config/thead.yaml \
  > "${root}/plugin-thead-blacklist.diff"
sha256sum \
  "${root}/control/$(basename "${runner}")" \
  "${source_root}/aggregate-result.json" \
  "${service_log}" \
  "${root}/plugin-thead-blacklist.diff" \
  > "${root}/SHA256SUMS.preflight"

nohup python3 "${runner}" \
  --experiment-id "${experiment_id}" \
  --aggregate "${source_root}/aggregate-result.json" \
  --output-root "${root}" \
  --base-url http://127.0.0.1:8023/v1/chat/completions \
  --max-tokens 60000 \
  --server-max-model-len 131072 \
  --concurrency 64 \
  > "${root}/runner.log" 2>&1 &
pid=$!
printf '%s\n' "${pid}" > "${root}/runner.pid"
sleep 3
kill -0 "${pid}"
test -f "${root}/manifest.json"
test -f "${root}/progress.json"
printf 'launched pid=%s root=%s\n' "${pid}" "${root}"
