#!/usr/bin/env bash
set -euo pipefail
role=${1:?usage: op010-collect-performance2-identity.sh baseline|candidate|revert}
case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
control=${case_dir}/commands/performance
runtime=${case_dir}/results/op010-perf2-${role}-runtime.json
manifest=${case_dir}/results/op010-perf2-${role}-performance-manifest.json
log=${case_dir}/logs/op010-perf2-${role}-131k-server.log
case "${role}" in
  candidate) variant=op010 ;;
  baseline|revert) variant=original ;;
  *) exit 2 ;;
esac
test ! -e "${runtime}"
test ! -e "${manifest}"
test -f "${log}"
test "$(sha256sum "${control}/build-op010-service-manifest.py" | cut -d ' ' -f 1)" = cb3b97a9fc2284eb062c927e28b629923256c780b433699f89a20c32acea3228
docker exec minimaxM3-opt-20260921 python3 "${control}/capture-baseline-service.py" > "${runtime}"
python3 "${control}/build-op010-service-manifest.py" \
  "${role}" "${runtime}" "${log}" "${manifest}" "${variant}"
docker exec minimaxM3-opt-20260921 python3 \
  "${control}/verify-live-baseline-service.py" "${manifest}"
sha256sum "${runtime}" "${manifest}"
