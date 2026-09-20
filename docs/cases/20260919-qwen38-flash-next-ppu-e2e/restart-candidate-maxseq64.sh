#!/usr/bin/env bash
set -euo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
expected_image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
manifest_dir=${case_dir}/manifests
log_dir=${case_dir}/logs
before_process=${manifest_dir}/candidate-before-maxseq64.json
after_process=${manifest_dir}/candidate-maxseq64-runtime.json
service_manifest=${manifest_dir}/candidate-maxseq64-service.json
service_log=${log_dir}/candidate-maxseq64-service-8030.log

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${expected_image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${before_process}"
test ! -e "${after_process}"
test ! -e "${service_manifest}"
test ! -e "${service_log}"

docker exec -i "${container}" python3 - <<'PY' > "${before_process}"
import json
import os

model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        args = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if not any(os.path.basename(x) == "vllm" for x in args) or "serve" not in args or model not in args:
        continue
    if "--port" not in args or args[args.index("--port") + 1] != "8030":
        continue
    found.append({"pid": int(entry), "args": args})
if len(found) != 1:
    raise SystemExit(f"Expected exactly one service on port 8030, got {len(found)}")
args = found[0]["args"]
if args[args.index("--max-num-seqs") + 1] != "32":
    raise SystemExit("Current service is not the frozen max-num-seqs=32 baseline")
print(json.dumps(found[0], indent=2, sort_keys=True))
PY

service_pid=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["pid"])' "${before_process}")
docker exec "${container}" kill -TERM "${service_pid}"

deadline=$((SECONDS + 240))
while docker exec "${container}" test -d "/proc/${service_pid}"; do
  if test "${SECONDS}" -ge "${deadline}"; then
    echo "Timed out waiting for candidate service shutdown; no force signal was sent." >&2
    exit 2
  fi
  sleep 2
done

for _ in $(seq 1 60); do
  if ! docker exec "${container}" bash -lc "ps -eo args | grep -E '(VLLM::EngineCore|VLLM::Worker_TP|vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next)' | grep -v grep" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if docker exec "${container}" bash -lc "ps -eo args | grep -E '(VLLM::EngineCore|VLLM::Worker_TP|vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next)' | grep -v grep" >/dev/null 2>&1; then
  echo "Candidate child processes remain; no force signal was sent." >&2
  exit 3
fi
if ss -ltn "sport = :8030" | tail -n +2 | grep -q .; then
  echo "Port 8030 is still in use." >&2
  exit 4
fi

docker exec -d \
  -e CUDA_VISIBLE_DEVICES=8,9,10,11,12,13,14,15 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
  -e GLOO_SOCKET_IFNAME=eth0 \
  -e NCCL_IB_HCA=fic2_soe_bond \
  -e NCCL_IB_GID_INDEX=1 \
  -e NCCL_IB_ADDR_FAMILY=6 \
  -e NCCL_SOCKET_IFNAME=bond \
  -e NCCL_SOCKET_FAMILY=AF_INET6 \
  -e VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_ \
  -w "${case_dir}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \\
  --served-model-name Qwen3.8-Flash-Next \\
  --host 0.0.0.0 \\
  --port 8030 \\
  --tensor-parallel-size 8 \\
  --pipeline-parallel-size 1 \\
  --dtype bfloat16 \\
  --language-model-only \\
  --max-model-len 80000 \\
  --max-num-seqs 64 \\
  --max-num-batched-tokens 4096 \\
  --gpu-memory-utilization 0.90 \\
  --disable-custom-all-reduce \\
  --reasoning-parser qwen3 \\
  --no-enable-prefix-caching \\
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \\
  > '${service_log}' 2>&1
"

ready=0
for _ in $(seq 1 360); do
  if timeout 5s curl -fsS http://127.0.0.1:8030/v1/models >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! docker exec "${container}" pgrep -f 'vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next' >/dev/null 2>&1; then
    echo "Candidate service exited before readiness." >&2
    tail -200 "${service_log}" >&2
    exit 5
  fi
  sleep 5
done
test "${ready}" -eq 1
grep -F 'enable_prefix_caching=False' "${service_log}" >/dev/null
grep -F 'Application startup complete' "${service_log}" >/dev/null

docker exec -i "${container}" python3 - <<'PY' > "${after_process}"
import hashlib
import json
import os
import subprocess
from pathlib import Path

model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
services = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        args = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if not any(os.path.basename(x) == "vllm" for x in args) or "serve" not in args or model not in args:
        continue
    if "--port" not in args or args[args.index("--port") + 1] != "8030":
        continue
    services.append({"pid": int(entry), "args": args, "proc_stat_start_ticks": open(f"/proc/{entry}/stat").read().split()[21]})
if len(services) != 1:
    raise SystemExit(f"Expected one restarted service, got {len(services)}")
repos = {}
for path in ("/workspace/vllm-plugin-FL-qwen38-adaptation", "/workspace/FlagGems-vllm", "/workspace/FlagGems"):
    tracked = subprocess.check_output(["git", "-C", path, "ls-files", "-co", "--exclude-standard", "-z"])
    digest = hashlib.sha256()
    for rel in sorted(x for x in tracked.split(b"\0") if x):
        digest.update(rel + b"\0")
        digest.update(hashlib.sha256((Path(path) / os.fsdecode(rel)).read_bytes()).digest())
    repos[path] = {
        "head": subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip(),
        "status": subprocess.check_output(["git", "-C", path, "status", "--short"], text=True),
        "content_sha256": digest.hexdigest(),
    }
print(json.dumps({"service": services[0], "repositories": repos}, indent=2, sort_keys=True))
PY

python3 - "${after_process}" "${service_manifest}" "${service_log}" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

runtime_path, manifest_path, log_path = sys.argv[1:]
runtime = json.load(open(runtime_path, encoding="utf-8"))
container = json.loads(subprocess.check_output(["docker", "inspect", "qwen3.8-flash-opt-candidate-20260919"], text=True))[0]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

repos = runtime["repositories"]
plugin = repos["/workspace/vllm-plugin-FL-qwen38-adaptation"]
fgv = repos["/workspace/FlagGems-vllm"]
fg = repos["/workspace/FlagGems"]
service = runtime["service"]
manifest = {
    "host": "PPU-01",
    "optimization_container_name": "qwen3.8-flash-opt-candidate-20260919",
    "service_instance_id": f"{container['Id'][:12]}-8030-{service['pid']}-{service['proc_stat_start_ticks']}",
    "model_name": "Qwen3.8-Flash-Next",
    "base_url": "http://127.0.0.1:8030/v1/completions",
    "mode": "graph",
    "model_sha256": "99e815241ef03325536b0aaa4441deea45174c17fae31e10f0bb456410c590de",
    "tokenizer_sha256": "6b49e287d3318979ff15f5a17d67806f67848399c71ed4201f23ab6e5fe44d6c",
    "engine_sha256": "fd3708e5a13abe98c566afd79a6b1987cef70c0548bb19c1218ff6a7f9d43346",
    "plugin_sha256": plugin["content_sha256"],
    "flaggems_vllm_sha256": fgv["content_sha256"],
    "flaggems_sha256": hashlib.sha256((fgv["content_sha256"] + fg["content_sha256"]).encode()).hexdigest(),
    "runtime_evidence_sha256": sha(runtime_path),
    "launch_config": {
        "enable_prefix_caching": False,
        "max_num_seqs": 64,
        "max_num_batched_tokens": 4096,
        "launch_args": service["args"][2:],
    },
    "image_lineage": "verified",
    "mount_parity": "passed",
    "tokenizer_path": "/mnt/cpfs/models/Qwen3.8-Flash-Next",
    "performance_context": {
        "platform": "thead-ppu",
        "device_model": "PPU-ZW810E",
        "device_ids": list(range(8, 16)),
        "driver_version": "2.1.1-rbd225",
        "device_runtime_version": "PPU-SMI-1.28",
        "image_id": container["Image"],
        "prefix_cache_state": "disabled",
        "cache_preparation": "CLI includes --no-enable-prefix-caching and startup log records enable_prefix_caching=False.",
    },
    "evidence": {
        "role": "candidate-maxseq64",
        "runtime_path": runtime_path,
        "runtime_sha256": sha(runtime_path),
        "log_path": log_path,
        "log_sha256": sha(log_path),
        "graph_capture_and_startup_observed": "Capturing CUDA graphs" in Path(log_path).read_text(errors="replace") and "Application startup complete" in Path(log_path).read_text(errors="replace"),
        "plugin_head": plugin["head"],
        "flaggems_vllm_head": fgv["head"],
        "flaggems_head": fg["head"],
    },
}
with open(manifest_path, "x", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

ppu-smi > "${manifest_dir}/host-ppu-smi.after-maxseq64-launch.txt"
sha256sum "${before_process}" "${after_process}" "${service_manifest}" "${service_log}"
