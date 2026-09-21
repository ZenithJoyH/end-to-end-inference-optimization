#!/usr/bin/env bash
set -euo pipefail

label=${1:?usage: run-fw008-service57-smoke.sh LABEL EXPECTED_COMMON_SLOT_SHA}
expected_sha=${2:?missing expected common-slot SHA}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
source=/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/worker/common_slot_mapping.py
payload=${case_root}/commands/performance/graph-replay-smoke-payload.json
baseline=${case_root}/smoke/post-prof005-native-service50-graph-01/canonical.json
output_dir=${case_root}/smoke/${label}
test ! -e "${output_dir}"
mkdir "${output_dir}"

ready=0
for _ in $(seq 1 360); do
  if timeout 5s curl -fsS http://127.0.0.1:8031/v1/models >/dev/null 2>&1; then ready=1; break; fi
  sleep 5
done
test "${ready}" -eq 1

docker exec -i "${container}" python3 - "${container_id}" "${expected_sha}" "${source}" <<'PY' > "${output_dir}/service-instance.json"
import hashlib, json, os, sys
container_id, expected_sha, source = sys.argv[1:]
actual = hashlib.sha256(open(source, "rb").read()).hexdigest()
if actual != expected_sha:
    raise SystemExit("common-slot source SHA mismatch")
found=[]
for entry in os.listdir("/proc"):
    if not entry.isdigit(): continue
    try:
        argv=[x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline","rb").read().split(b"\0") if x]
        raw=open(f"/proc/{entry}/stat",encoding="utf-8").read()
    except (FileNotFoundError,PermissionError,ProcessLookupError): continue
    if "serve" not in argv or "--port" not in argv or argv[argv.index("--port")+1] != "8031": continue
    env={}
    for item in open(f"/proc/{entry}/environ","rb").read().split(b"\0"):
        if b"=" in item:
            key,value=item.split(b"=",1); env[key.decode(errors="replace")]=value.decode(errors="replace")
    found.append({"pid":int(entry),"start_ticks":int(raw[raw.rfind(")")+2:].split()[19]),"argv":argv,
                  "selected_environment":{key:env.get(key) for key in (
                      "CUDA_VISIBLE_DEVICES","VLLM_FL_FLAGOS_BLACKLIST_APPEND",
                      "VLLM_FL_QSA_STATIC_SCORE_COLUMNS","VLLM_TUNED_CONFIG_FOLDER",
                      "VLLM_FL_SKIP_COMMON_SLOT_HOST_SYNC")}})
if len(found) != 1: raise SystemExit(f"expected one service, got {len(found)}")
service=found[0]
if service["selected_environment"]["VLLM_FL_SKIP_COMMON_SLOT_HOST_SYNC"] != "1":
    raise SystemExit("candidate opt-out environment missing")
service["service_instance_id"]=f"{container_id[:12]}-8031-{service['pid']}-{service['start_ticks']}"
service["plugin_file_sha256"]=actual
print(json.dumps(service,indent=2,sort_keys=True))
PY

for wave in 1 2 3; do
  pids=()
  for request in 1 2 3 4 5 6 7 8; do
    curl -fsS http://127.0.0.1:8031/v1/completions -H 'Content-Type: application/json' \
      --data-binary "@${payload}" > "${output_dir}/wave-${wave}-request-${request}.json" &
    pids+=("$!")
  done
  for pid in "${pids[@]}"; do wait "${pid}"; done
done

python3 - "${output_dir}" "${baseline}" <<'PY'
import json, sys
from pathlib import Path
root=Path(sys.argv[1]); baseline=json.loads(Path(sys.argv[2]).read_text())
rows=[]
for path in sorted(root.glob("wave-*-request-*.json")):
    data=json.loads(path.read_text()); choices=data.get("choices")
    if not isinstance(choices,list) or len(choices)!=1 or not choices[0].get("text"):
        raise SystemExit(f"invalid response {path}")
    rows.append({"text":choices[0]["text"],"finish_reason":choices[0].get("finish_reason"),
                 "completion_tokens":data.get("usage",{}).get("completion_tokens")})
if len(rows)!=24 or any(row!=rows[0] for row in rows[1:]):
    raise SystemExit("candidate graph replays are not deterministic")
canonical={"schema_version":1,"requests":len(rows),"response":rows[0]}
if canonical!=baseline: raise SystemExit("fw008 canonical differs from retained service50")
(root/"canonical.json").write_text(json.dumps(canonical,indent=2,sort_keys=True)+"\n")
PY
sha256sum "${payload}" "${baseline}" "${output_dir}/service-instance.json" "${output_dir}/canonical.json"
