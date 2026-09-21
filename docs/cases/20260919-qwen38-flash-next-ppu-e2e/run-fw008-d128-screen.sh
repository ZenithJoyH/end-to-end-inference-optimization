#!/usr/bin/env bash
set -euo pipefail

run_id=${1:?usage: run-fw008-d128-screen.sh RUN_ID}
expected_sha=${2:?missing expected common-slot source SHA}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
control=${case_root}/commands/performance
runner=${control}/vllm_perf.py
plan=${control}/perf-fw008-d128-screen-plan.json
contract=${control}/perf-fw008-d128-screen-comparison.json
source_manifest=${case_root}/manifests/post-prof005-native-service50.json
service_instance=${case_root}/smoke/fw008-service57-graph-01/service-instance.json
runtime=${case_root}/runtime/${run_id}.json
manifest=${case_root}/manifests/${run_id}.json
output_root=${case_root}/performance
source=/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/worker/common_slot_mapping.py

for path in "${runner}" "${plan}" "${contract}" "${source_manifest}" "${service_instance}"; do test -f "${path}"; done
for path in "${runtime}" "${manifest}" "${output_root}/${run_id}" "${output_root}/${run_id}.dry-run.json" "${output_root}/${run_id}.console.log"; do
  test ! -e "${path}" || { echo "refusing to overwrite ${path}" >&2; exit 2; }
done
curl -fsS http://127.0.0.1:8031/health >/dev/null
mkdir -p "${case_root}/runtime"

docker exec -i "${container}" python3 - "${expected_sha}" "${source}" <<'PY' > "${runtime}"
import hashlib, json, os, subprocess, sys
from pathlib import Path
expected, source = sys.argv[1:]
actual=hashlib.sha256(Path(source).read_bytes()).hexdigest()
if actual != expected: raise SystemExit("common-slot source SHA mismatch")
services=[]
for entry in os.listdir("/proc"):
    if not entry.isdigit(): continue
    try:
        argv=[x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline","rb").read().split(b"\0") if x]
        raw=open(f"/proc/{entry}/stat",encoding="utf-8").read()
    except (FileNotFoundError,PermissionError,ProcessLookupError): continue
    if "serve" in argv and "--port" in argv and argv[argv.index("--port")+1] == "8031":
        services.append({"pid":int(entry),"argv":argv,"start_ticks":int(raw[raw.rfind(")")+2:].split()[19])})
if len(services)!=1: raise SystemExit(f"expected one service, got {len(services)}")
repos={}
for repo in ("/workspace/vllm-plugin-FL-qwen38-adaptation","/workspace/FlagGems-vllm","/workspace/FlagGems"):
    tracked=subprocess.check_output(["git","-C",repo,"ls-files","-co","--exclude-standard","-z"])
    digest=hashlib.sha256()
    for rel in sorted(x for x in tracked.split(b"\0") if x):
        digest.update(rel+b"\0"); digest.update(hashlib.sha256((Path(repo)/os.fsdecode(rel)).read_bytes()).digest())
    repos[repo]={"head":subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip(),
                 "status":subprocess.check_output(["git","-C",repo,"status","--short"],text=True),
                 "content_sha256":digest.hexdigest()}
print(json.dumps({"common_slot_sha256":actual,"service":services[0],"repositories":repos},indent=2,sort_keys=True))
PY

python3 - "${source_manifest}" "${service_instance}" "${runtime}" "${manifest}" <<'PY'
import hashlib, json, sys
from pathlib import Path
source=json.load(open(sys.argv[1])); instance=json.load(open(sys.argv[2])); runtime_path=Path(sys.argv[3]); runtime=json.loads(runtime_path.read_text())
if runtime["common_slot_sha256"] != instance["plugin_file_sha256"]: raise SystemExit("source identity mismatch")
observed=runtime["service"]
if any(observed[k]!=instance[k] for k in ("pid","start_ticks","argv")): raise SystemExit("service identity mismatch")
repos=runtime["repositories"]; plugin=repos["/workspace/vllm-plugin-FL-qwen38-adaptation"]["content_sha256"]
fgv=repos["/workspace/FlagGems-vllm"]["content_sha256"]; fg=repos["/workspace/FlagGems"]["content_sha256"]
source["base_url"]="http://127.0.0.1:8031/v1/completions"; source["service_instance_id"]=instance["service_instance_id"]
source["plugin_sha256"]=plugin; source["flaggems_vllm_sha256"]=fgv; source["flaggems_sha256"]=hashlib.sha256((fgv+fg).encode()).hexdigest()
source["runtime_evidence_sha256"]=hashlib.sha256(runtime_path.read_bytes()).hexdigest()
argv=instance["argv"]; source["launch_config"]["launch_args"]=argv[argv.index("serve"):]
source["launch_config"]["selected_environment"].update(instance["selected_environment"])
source["performance_context"]["device_ids"]=[str(i) for i in range(8)]
Path(sys.argv[4]).write_text(json.dumps(source,indent=2,sort_keys=True)+"\n")
PY

python3 "${control}/verify-live-service-manifest.py" "${manifest}" "${container}" 8031 64 >/dev/null
docker exec "${container}" python3 "${runner}" --config "${plan}" --comparison-contract "${contract}" \
  --service-manifest "${manifest}" --role candidate --run-id "${run_id}" --scope performance_only \
  --output-dir "${output_root}" --dry-run > "${output_root}/${run_id}.dry-run.json"
docker exec "${container}" python3 "${runner}" --config "${plan}" --comparison-contract "${contract}" \
  --service-manifest "${manifest}" --role candidate --run-id "${run_id}" --scope performance_only \
  --output-dir "${output_root}" 2>&1 | tee "${output_root}/${run_id}.console.log"
sha256sum "${plan}" "${contract}" "${runtime}" "${manifest}" "${output_root}/${run_id}/run-record.json"
