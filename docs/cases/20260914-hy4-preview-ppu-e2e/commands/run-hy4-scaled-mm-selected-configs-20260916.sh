#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e
container=hy4-opt-20260914
run_id=scaled-mm-selected-configs-20260916-01
result_dir="${case_root}/results/operators/${run_id}"

test ! -e "${result_dir}"
mkdir -p "${result_dir}"
if ss -ltn | grep -q ':8010 '; then
  echo 'refusing to inspect while port 8010 is listening' >&2
  exit 1
fi

docker exec "${container}" python \
  "${case_root}/commands/inspect-hy4-scaled-mm-selected-configs-20260916.py" \
  >"${result_dir}/inspect.stdout" \
  2>"${result_dir}/inspect.stderr"
grep '^SUMMARY=' "${result_dir}/inspect.stdout" \
  | sed 's/^SUMMARY=//' \
  >"${result_dir}/summary.json"
python3 -m json.tool "${result_dir}/summary.json" >/dev/null
sha256sum "${result_dir}/summary.json" >"${result_dir}/summary.json.sha256"
