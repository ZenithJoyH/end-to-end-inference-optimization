#!/usr/bin/env bash
set -euo pipefail

expected_qsa_sha=${1:?usage: preflight-op021-qsa-producer-prepare-copy.sh EXPECTED_QSA_SHA RUN_ID}
run_id=${2:?missing unique run id}
[[ "${expected_qsa_sha}" =~ ^[0-9a-f]{64}$ ]]
case "${run_id}" in *[!A-Za-z0-9._-]*|'') exit 2 ;; esac

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
commands=${case_root}/commands/op021
live_qsa=/workspace/FlagGems/src/flag_gems/fused/qsa.py
root=${case_root}/transitions/${run_id}
copy_dir=${root}/flag_gems/fused
copy_qsa=${copy_dir}/qsa.py
artifact=${root}/patch-artifact
manifest=${artifact}/patch-manifest.json

test ! -e "${root}"
mkdir -p "${copy_dir}"
docker exec -i "${container}" python3 - "${live_qsa}" "${expected_qsa_sha}" "${copy_qsa}" <<'PY'
import hashlib
import shutil
import sys

source, expected, target = sys.argv[1:]
actual = hashlib.sha256(open(source, "rb").read()).hexdigest()
if actual != expected:
    raise SystemExit(f"live qsa SHA mismatch: {actual} != {expected}")
shutil.copy2(source, target)
PY

docker exec -i "${container}" python3 \
  "${commands}/prepare-op021-qsa-producer-fixture.py" \
  --qsa "${copy_qsa}" \
  --helper "${commands}/op021-qsa-producer-fixture-helper.py" \
  --artifact-dir "${artifact}" \
  --expected-sha256 "${expected_qsa_sha}" \
  > "${root}/prepare.stdout"
test -s "${manifest}"

docker exec -i "${container}" python3 - "${copy_qsa}" <<'PY' > "${root}/patched-syntax.txt"
import sys
path = sys.argv[1]
compile(open(path, encoding="utf-8").read(), path, "exec")
print("patched-syntax-ok")
PY

docker exec -i "${container}" bash \
  "${commands}/revert-op021-qsa-producer-fixture.sh" "${manifest}" \
  > "${root}/revert.stdout"
actual=$(sha256sum "${copy_qsa}" | awk '{print $1}')
test "${actual}" = "${expected_qsa_sha}"
test ! -e "${copy_dir}/qsa_producer_fixture_capture.py"
sha256sum "${manifest}" "${copy_qsa}" > "${root}/SHA256SUMS"
printf '%s\n' "${root}"
