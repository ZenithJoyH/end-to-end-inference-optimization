#!/usr/bin/env bash
set -euo pipefail

role=${1:?usage: op005-switch-linear-source.sh baseline|candidate|revert}
case "${role}" in
  baseline|candidate|revert) ;;
  *) echo "invalid comparison role: ${role}" >&2; exit 2 ;;
esac

case_dir=/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e
container=minimaxM3-opt-20260921
source_file=/workspace/FlagGems/src/flag_gems/ops/linear.py
original_sha=4d46bae0804ac32b698582d010d5f0e02d3570c6703efff9d1d666e2bf43fd94
candidate_sha=40468058e6e664448573e10663b89b5aa467b052a0b2c56191243760c5c99bef
if [[ "${role}" == candidate ]]; then
  expected_before=${original_sha}
  expected_after=${candidate_sha}
  replacement=${case_dir}/patches/op005-linear-candidate.py
else
  expected_before=${candidate_sha}
  expected_after=${original_sha}
  replacement=${case_dir}/patches/op005-linear-original.py
fi
transition=${case_dir}/transitions/op005-switch-to-${role}

test "$(docker inspect -f '{{.Id}}' "${container}" | cut -c1-12)" = bd37abcbf719
test ! -e "${transition}"
test "$(sha256sum "${replacement}" | cut -d ' ' -f 1)" = "${expected_after}"
if docker exec "${container}" pgrep -f '^python -m vllm.entrypoints.openai.api_server .* --port 8023( |$)'; then
  echo 'refusing to switch while port-8023 model process is active' >&2; exit 3
fi
if ss -lntp | grep -q ':8023 '; then
  echo 'refusing to switch while port 8023 has a listener' >&2; exit 3
fi
if ps -eo args | grep -q '[l]lmrun.py.*minimax-m3-op005-minimal-regression'; then
  echo 'refusing to switch while op005 accuracy evaluator is active' >&2; exit 3
fi
if [[ -n "$(ppu-smi --query-compute-apps=pid --format=csv,noheader,nounits)" ]]; then
  echo 'refusing to switch while PPU compute processes remain' >&2; exit 3
fi
before=$(docker exec "${container}" sha256sum "${source_file}" | cut -d ' ' -f 1)
test "${before}" = "${expected_before}"
mkdir "${transition}"
printf '%s\n' "${before}" > "${transition}/linear.before.sha256"
docker cp "${replacement}" "${container}:${source_file}"
after=$(docker exec "${container}" sha256sum "${source_file}" | cut -d ' ' -f 1)
test "${after}" = "${expected_after}"
printf '%s\n' "${after}" > "${transition}/linear.after.sha256"
docker exec "${container}" sh -lc \
  "cd /workspace/FlagGems && git diff --check -- src/flag_gems/ops/linear.py && python3 -c 'import ast; from pathlib import Path; ast.parse(Path(\"src/flag_gems/ops/linear.py\").read_text())' && git status --short" \
  > "${transition}/source-check.txt"
sha256sum "${replacement}" "${transition}/linear.before.sha256" \
  "${transition}/linear.after.sha256" "${transition}/source-check.txt" \
  > "${transition}/SHA256SUMS"
