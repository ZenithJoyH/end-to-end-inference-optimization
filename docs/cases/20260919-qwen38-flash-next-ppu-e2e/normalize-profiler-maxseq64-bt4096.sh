#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
transition_id=prof-001-maxseq64-bt4096-service-01
source_manifest=${case_root}/transitions/${transition_id}/profiler-maxseq64-bt4096-raw.json
destination=${case_root}/manifests/profiler-maxseq64-bt4096-service-comparison.json

test -f "${source_manifest}"
test ! -e "${destination}"
python3 "${case_root}/commands/performance/normalize-maxseq-service-manifest.py" \
  "${source_manifest}" \
  "${destination}" \
  64 \
  4096
python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${destination}" qwen3.8-flash-opt-candidate-20260919 8030 64
python3 - "${destination}" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
args = manifest["launch_config"]["launch_args"]
assert args.count("--profiler-config") == 1
config = json.loads(args[args.index("--profiler-config") + 1])
assert config["profiler"] == "torch"
assert config["torch_profiler_with_stack"] is True
assert config["torch_profiler_record_shapes"] is True
assert config["torch_profiler_dir"].endswith("/profiling/prof-001-maxseq64-bt4096-mixed-capture/traces")
PY
sha256sum "${source_manifest}" "${destination}"
