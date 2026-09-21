#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
port=8031
label=${1:?usage: run-op014-service51-smoke.sh LABEL [EXPECTED_PLUGIN_FILE_SHA]}
payload=${case_root}/commands/performance/graph-replay-smoke-payload.json
baseline=${case_root}/smoke/post-prof005-native-service50-graph-01/canonical.json
output_dir=${case_root}/smoke/${label}
expected_plugin_file_sha=${2:-c1062b5810a1bcfec7cfca7f61e11a0ffd08700cee2b3f6472b7086d195a87e7}

test ! -e "${output_dir}"
test -f "${payload}"
test -f "${baseline}"
mkdir -p "${output_dir}"

docker exec -i "${container}" python3 - "${container_id}" "${port}" \
  "${expected_plugin_file_sha}" <<'PY' > "${output_dir}/service-instance.json"
import hashlib
import json
import os
import sys

container_id, port, expected_sha = sys.argv[1:]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
source = "/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/models/qwen3_8_flash_next.py"
actual_sha = hashlib.sha256(open(source, "rb").read()).hexdigest()
if actual_sha != expected_sha:
    raise SystemExit("Plugin source SHA differs from op014 candidate")
services = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [item.decode(errors="replace") for item in open(
            f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if item]
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
        tail = raw[raw.rfind(")") + 2:].split()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if "serve" not in argv or model not in argv or "--port" not in argv:
        continue
    if argv[argv.index("--port") + 1] != port:
        continue
    env = {}
    for item in open(f"/proc/{entry}/environ", "rb").read().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            env[key.decode(errors="replace")] = value.decode(errors="replace")
    services.append({
        "pid": int(entry),
        "start_ticks": int(tail[19]),
        "argv": argv,
        "selected_environment": {key: env.get(key) for key in (
            "CUDA_VISIBLE_DEVICES",
            "VLLM_FL_FLAGOS_BLACKLIST_APPEND",
            "VLLM_FL_QSA_STATIC_SCORE_COLUMNS",
            "VLLM_TUNED_CONFIG_FOLDER",
        )},
    })
if len(services) != 1:
    raise SystemExit(f"expected one service on port {port}, got {len(services)}")
service = services[0]
expected_env = {
    "CUDA_VISIBLE_DEVICES": "0,1,2,3,4,5,6,7",
    "VLLM_FL_FLAGOS_BLACKLIST_APPEND": "_conv_depthwise2d,index,normal_,mm,mm_out",
    "VLLM_FL_QSA_STATIC_SCORE_COLUMNS": "8448",
    "VLLM_TUNED_CONFIG_FOLDER": (
        "/mnt/nfs/users/jinghao/qwen3.8-flash/"
        "20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-only-01"
    ),
}
if service["selected_environment"] != expected_env:
    raise SystemExit("candidate environment drift")
service["service_instance_id"] = (
    f"{container_id[:12]}-{port}-{service['pid']}-{service['start_ticks']}"
)
service["plugin_file_sha256"] = actual_sha
print(json.dumps(service, indent=2, sort_keys=True))
PY

curl -fsS "http://127.0.0.1:${port}/health" >/dev/null
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

python3 - "${output_dir}" "${baseline}" <<'PY'
import json
import sys
from pathlib import Path

output_dir = Path(sys.argv[1])
baseline_path = Path(sys.argv[2])
rows = []
for path in sorted(output_dir.glob("wave-*-request-*.json")):
    payload = json.loads(path.read_text(encoding="utf-8"))
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise SystemExit(f"invalid choices: {path}")
    choice = choices[0]
    text = choice.get("text")
    if not isinstance(text, str) or not text:
        raise SystemExit(f"empty completion: {path}")
    rows.append({
        "text": text,
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": payload.get("usage", {}).get("completion_tokens"),
    })
if len(rows) != 24 or any(row != rows[0] for row in rows[1:]):
    raise SystemExit("candidate graph replays are not deterministic")
canonical = {"schema_version": 1, "requests": len(rows), "response": rows[0]}
baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
if canonical != baseline:
    raise SystemExit("op014 canonical differs from service50 baseline")
path = output_dir / "canonical.json"
path.write_text(json.dumps(canonical, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(path)
PY

sha256sum "${payload}" "${baseline}" "${output_dir}/service-instance.json" \
  "${output_dir}/canonical.json"
