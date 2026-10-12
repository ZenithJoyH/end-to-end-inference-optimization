#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
run_root="$case_root/accuracy/fw006-formal-gpqa-c64-threshold88"
workspace="$case_root/commands/formal-eval-workspace"
config="$run_root/config.json"
runtime="$run_root/service-runtime.json"
service="$run_root/service-manifest.json"
inspect="$run_root/evaluator.inspect.json"
provenance="$run_root/task-provenance.json"
contract="$run_root/contract.json"
startup="$case_root/logs/fw006-targeted-reflection-retained-server.log"

test ! -e "$run_root"
mkdir -p "$run_root" "$run_root/native" "$run_root/control"
cp "$case_root/commands/accuracy/minimax-m3-fw006-formal-c64-threshold88.json" "$config"
docker inspect minimax-m3-eval-e2e-20260921 > "$inspect"
docker exec minimaxM3-opt-20260921 python3 \
  "$case_root/commands/performance/capture-baseline-service.py" > "$runtime"
python3 "$case_root/commands/accuracy/build-fw006-formal-service-manifest.py" \
  "$runtime" "$startup" "$service"
docker exec minimax-m3-eval-e2e-20260921 python3 \
  "$workspace/evaluation/accuracy/formal_accuracy.py" \
  --config "$config" \
  --evaluation-inspect "$inspect" \
  --capture-provenance "$provenance" \
  > "$run_root/provenance.log" 2>&1
python3 "$case_root/commands/accuracy/freeze-fw006-formal-contract.py" \
  "$provenance" "$contract"
docker exec minimax-m3-eval-e2e-20260921 python3 \
  "$workspace/evaluation/accuracy/formal_accuracy.py" \
  --config "$config" \
  --contract "$contract" \
  --service-manifest "$service" \
  --evaluation-inspect "$inspect" \
  --preflight-only \
  > "$run_root/preflight.log" 2>&1
sha256sum "$config" "$runtime" "$service" "$inspect" "$provenance" "$contract" \
  > "$run_root/SHA256SUMS.preflight"
