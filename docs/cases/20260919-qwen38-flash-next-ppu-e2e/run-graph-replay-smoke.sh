#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
label=${1:?usage: run-graph-replay-smoke.sh LABEL SERVICE_MANIFEST MAX_NUM_SEQS [BASELINE_CANONICAL]}
service_manifest=${2:?missing service manifest}
max_num_seqs=${3:?missing max_num_seqs}
baseline_canonical=${4:-}
container=${5:-${container}}
port=${6:-8030}
payload=${case_root}/commands/performance/graph-replay-smoke-payload.json
output_dir=${case_root}/smoke/${label}

case "${max_num_seqs}" in
  32|48|64) ;;
  *) echo "max_num_seqs must be 32, 48, or 64" >&2; exit 2 ;;
esac
case "${port}" in 8020|8030) ;; *) echo "unexpected task service port" >&2; exit 2;; esac
test -f "${service_manifest}"
test -f "${payload}"
test ! -e "${output_dir}"
mkdir -p "${output_dir}"

python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${service_manifest}" "${container}" "${port}" "${max_num_seqs}" \
  > "${output_dir}/live-service-instance.txt"
docker exec "${container}" curl -fsS "http://127.0.0.1:${port}/health" >/dev/null

for wave in 1 2 3; do
  pids=()
  for request in 1 2 3 4 5 6 7 8; do
    curl -fsS "http://127.0.0.1:${port}/v1/completions" \
      -H 'Content-Type: application/json' \
      --data-binary "@${payload}" \
      > "${output_dir}/wave-${wave}-request-${request}.json" &
    pids+=("$!")
  done
  for pid in "${pids[@]}"; do
    wait "${pid}"
  done
done

python3 - "${output_dir}" "${baseline_canonical}" <<'PY'
import json
import sys
from pathlib import Path

output_dir = Path(sys.argv[1])
baseline_path = Path(sys.argv[2]) if sys.argv[2] else None
rows = []
for path in sorted(output_dir.glob("wave-*-request-*.json")):
    payload = json.loads(path.read_text(encoding="utf-8"))
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise SystemExit(f"invalid choices in {path}")
    choice = choices[0]
    text = choice.get("text")
    if not isinstance(text, str) or not text:
        raise SystemExit(f"empty completion in {path}")
    rows.append({
        "text": text,
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": payload.get("usage", {}).get("completion_tokens"),
    })
if len(rows) != 24:
    raise SystemExit(f"expected 24 responses, got {len(rows)}")
if any(row != rows[0] for row in rows[1:]):
    raise SystemExit("same-shape deterministic graph replays produced different outputs")
canonical = {"schema_version": 1, "requests": len(rows), "response": rows[0]}
canonical_path = output_dir / "canonical.json"
canonical_path.write_text(json.dumps(canonical, indent=2, sort_keys=True) + "\n", encoding="utf-8")
if baseline_path is not None:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if canonical != baseline:
        raise SystemExit("candidate graph replay output differs from max-num-seqs=32 baseline")
print(canonical_path)
PY

sha256sum "${payload}" "${service_manifest}" "${output_dir}/canonical.json"
