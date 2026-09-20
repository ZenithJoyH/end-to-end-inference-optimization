#!/usr/bin/env bash
set -euo pipefail

run_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01
native_run=${run_root}/runs/hy4-preview-formal-gate-f7d1aaa-a26a902-20260918/004dd92608e94977b18ed9567f88338b
bundle=${run_root}/bundle/evaluation/accuracy
backup=${run_root}/validation-repair-original
staging=${run_root}/validation-repair-staging

test ! -e "${native_run}/run-record.json"
test ! -e "${run_root}/accuracy-gate.json"
mkdir -p "${backup}"
for name in sample_validation.py acceptance.py formal_accuracy.py; do
  test -s "${staging}/${name}"
  if [[ ! -e "${backup}/${name}" ]]; then
    cp "${bundle}/${name}" "${backup}/${name}"
  else
    test -s "${backup}/${name}"
  fi
  cp "${staging}/${name}" "${bundle}/${name}"
done

docker exec flageval_llmeval-jinghao python \
  "${bundle}/formal_accuracy.py" --finalize-run "${native_run}"
docker exec flageval_llmeval-jinghao python \
  "${bundle}/acceptance.py" issue \
  --run-record "${native_run}/run-record.json" \
  --output "${run_root}/accuracy-gate.json"
docker exec flageval_llmeval-jinghao python \
  "${bundle}/acceptance.py" check \
  --gate "${run_root}/accuracy-gate.json" \
  --service-manifest "${run_root}/service-manifest.json"

sha256sum \
  "${native_run}/run-record.json" \
  "${run_root}/accuracy-gate.json" \
  "${bundle}/sample_validation.py" \
  "${bundle}/acceptance.py" \
  "${bundle}/formal_accuracy.py" \
  >"${run_root}/gate-artifacts.sha256"
