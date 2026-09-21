#!/usr/bin/env bash
set -euo pipefail

role=${1:?usage: run-op014-d128-role.sh baseline|candidate|revert RUN_ID SERVICE_INSTANCE EXPECTED_SHA}
run_id=${2:?missing RUN_ID}
service_instance=${3:?missing SERVICE_INSTANCE}
expected_sha=${4:?missing EXPECTED_SHA}
case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
control=${case_root}/commands/performance
runner=${control}/vllm_perf.py
plan=${control}/perf-op014-d128-same-device-plan.json
contract=${control}/perf-op014-d128-same-device-comparison.json
source_manifest=${case_root}/manifests/post-prof005-native-service50.json
manifest=${case_root}/manifests/${run_id}.json
runtime=${case_root}/runtime/${run_id}.json
output_root=${case_root}/performance

case "${role}" in baseline|candidate|revert) ;; *) echo "invalid role" >&2; exit 2;; esac
for path in "${runner}" "${plan}" "${contract}" "${source_manifest}" "${service_instance}"; do test -f "${path}"; done
for path in "${manifest}" "${runtime}" "${output_root}/${run_id}" "${output_root}/${run_id}.dry-run.json" "${output_root}/${run_id}.console.log"; do
  test ! -e "${path}" || { echo "refusing to overwrite ${path}" >&2; exit 2; }
done
curl -fsS http://127.0.0.1:8031/health >/dev/null

mkdir -p "${case_root}/runtime"
docker exec -i "${container}" python3 - "${expected_sha}" <<'PY' > "${runtime}"
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

expected_sha = sys.argv[1]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
plugin_file = Path(
    "/workspace/vllm-plugin-FL-qwen38-adaptation/"
    "vllm_fl/models/qwen3_8_flash_next.py"
)
plugin_file_sha = hashlib.sha256(plugin_file.read_bytes()).hexdigest()
if plugin_file_sha != expected_sha:
    raise SystemExit("Plugin source SHA differs from requested role")

services = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        argv = [item.decode(errors="replace") for item in open(
            f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if item]
        raw = open(f"/proc/{entry}/stat", encoding="utf-8").read()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if "serve" not in argv or model not in argv or "--port" not in argv:
        continue
    if argv[argv.index("--port") + 1] != "8031":
        continue
    services.append({
        "pid": int(entry),
        "argv": argv,
        "start_ticks": int(raw[raw.rfind(")") + 2:].split()[19]),
    })
if len(services) != 1:
    raise SystemExit(f"expected one service on port 8031, got {len(services)}")

repositories = {}
for repo in (
    "/workspace/vllm-plugin-FL-qwen38-adaptation",
    "/workspace/FlagGems-vllm",
    "/workspace/FlagGems",
):
    tracked = subprocess.check_output(
        ["git", "-C", repo, "ls-files", "-co", "--exclude-standard", "-z"]
    )
    digest = hashlib.sha256()
    for rel in sorted(item for item in tracked.split(b"\0") if item):
        digest.update(rel + b"\0")
        digest.update(hashlib.sha256((Path(repo) / os.fsdecode(rel)).read_bytes()).digest())
    repositories[repo] = {
        "head": subprocess.check_output(
            ["git", "-C", repo, "rev-parse", "HEAD"], text=True
        ).strip(),
        "status": subprocess.check_output(
            ["git", "-C", repo, "status", "--short"], text=True
        ),
        "content_sha256": digest.hexdigest(),
    }
print(json.dumps({
    "plugin_file_sha256": plugin_file_sha,
    "service": services[0],
    "repositories": repositories,
}, indent=2, sort_keys=True))
PY

python3 - "${source_manifest}" "${service_instance}" "${runtime}" "${manifest}" "${expected_sha}" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

source = json.load(open(sys.argv[1], encoding="utf-8"))
instance = json.load(open(sys.argv[2], encoding="utf-8"))
runtime_path = Path(sys.argv[3])
runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
expected_sha = sys.argv[5]
if instance.get("plugin_file_sha256") != expected_sha:
    raise SystemExit("service instance Plugin SHA differs from requested role")
if runtime.get("plugin_file_sha256") != expected_sha:
    raise SystemExit("runtime Plugin SHA differs from requested role")
argv = instance["argv"]
observed = runtime["service"]
if observed["argv"] != argv or observed["pid"] != instance["pid"] or observed["start_ticks"] != instance["start_ticks"]:
    raise SystemExit("runtime service differs from smoke service instance")
repos = runtime["repositories"]
plugin = repos["/workspace/vllm-plugin-FL-qwen38-adaptation"]["content_sha256"]
fgv = repos["/workspace/FlagGems-vllm"]["content_sha256"]
fg = repos["/workspace/FlagGems"]["content_sha256"]
source["base_url"] = "http://127.0.0.1:8031/v1/completions"
source["service_instance_id"] = instance["service_instance_id"]
source["plugin_sha256"] = plugin
source["flaggems_vllm_sha256"] = fgv
source["flaggems_sha256"] = hashlib.sha256((fgv + fg).encode()).hexdigest()
source["runtime_evidence_sha256"] = hashlib.sha256(runtime_path.read_bytes()).hexdigest()
source["launch_config"]["launch_args"] = argv[argv.index("serve"):]
source["launch_config"]["selected_environment"].update(instance["selected_environment"])
source["performance_context"]["device_ids"] = [str(value) for value in range(8)]
Path(sys.argv[4]).write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
python3 "${control}/verify-live-service-manifest.py" "${manifest}" "${container}" 8031 64 >/dev/null

docker exec "${container}" python3 "${runner}" \
  --config "${plan}" --comparison-contract "${contract}" \
  --service-manifest "${manifest}" --role "${role}" \
  --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" \
  --dry-run > "${output_root}/${run_id}.dry-run.json"
docker exec "${container}" python3 "${runner}" \
  --config "${plan}" --comparison-contract "${contract}" \
  --service-manifest "${manifest}" --role "${role}" \
  --run-id "${run_id}" --scope performance_only --output-dir "${output_root}" \
  2>&1 | tee "${output_root}/${run_id}.console.log"
sha256sum "${plan}" "${contract}" "${runtime}" "${manifest}" "${output_root}/${run_id}/run-record.json"
