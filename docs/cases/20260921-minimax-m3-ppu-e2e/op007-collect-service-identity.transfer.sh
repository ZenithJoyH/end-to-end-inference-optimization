#!/usr/bin/env bash
set -euo pipefail

role=${1:?usage: op007-collect-service-identity.sh baseline|candidate|revert EXPECTED_MOE_SHA256}
expected_moe=${2:?missing EXPECTED_MOE_SHA256}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
control=${case_dir}/commands/performance
runtime=${case_dir}/results/op007-${role}-runtime.json
manifest=${case_dir}/results/op007-${role}-performance-manifest.json
log=${case_dir}/logs/op007-${role}-comparison-131k-server.log

case "${role}" in
  baseline|candidate|revert) ;;
  *) echo "invalid role: ${role}" >&2; exit 2 ;;
esac
test ! -e "${runtime}"
test ! -e "${manifest}"
test -f "${log}"
docker exec minimaxM3-opt-20260921 python3 "${control}/capture-baseline-service.py" > "${runtime}"
python3 "${control}/build-op007-comparison-manifest.py" \
  "${role}" "${runtime}" "${log}" "${manifest}" "${expected_moe}"
docker exec minimaxM3-opt-20260921 python3 \
  "${control}/verify-live-baseline-service.py" "${manifest}"
sha256sum "${runtime}" "${manifest}"
