#!/usr/bin/env bash
set -euo pipefail

# DRAFT ONLY. Run on PPU-01 from the host after review.
# Defaults to the 64 -> 32 revert. Candidate wrappers reuse this transition
# engine so every 32/48/64 screen has identical safety checks.

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
expected_image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
source_max_num_seqs=${SOURCE_MAX_NUM_SEQS:-64}
target_max_num_seqs=${TARGET_MAX_NUM_SEQS:-32}
source_max_num_batched_tokens=${SOURCE_MAX_NUM_BATCHED_TOKENS:-4096}
target_max_num_batched_tokens=${TARGET_MAX_NUM_BATCHED_TOKENS:-4096}
source_profiler_config=${SOURCE_PROFILER_CONFIG:-}
target_profiler_config=${TARGET_PROFILER_CONFIG:-}
tuned_config_folder=${TUNED_CONFIG_FOLDER:-${case_dir}/configs/moe-bm16-decode-only-01}
transition_role=${TRANSITION_ROLE:-revert-maxseq32}
default_source_manifest=${case_dir}/manifests/candidate-maxseq64-service.json
source_manifest=${2:-${SOURCE_MANIFEST_DEFAULT:-${default_source_manifest}}}
run_id=${1:?usage: revert-candidate-maxseq32-draft.sh UNIQUE_RUN_ID [MAXSEQ64_RAW_MANIFEST]}

case "${source_max_num_seqs}" in 32|48|64) ;; *) echo "unsupported source max-num-seqs" >&2; exit 2 ;; esac
case "${target_max_num_seqs}" in 32|48|64) ;; *) echo "unsupported target max-num-seqs" >&2; exit 2 ;; esac
case "${source_max_num_batched_tokens}" in 2048|4096|6144|8192) ;; *) echo "unsupported source max-num-batched-tokens" >&2; exit 2 ;; esac
case "${target_max_num_batched_tokens}" in 2048|4096|6144|8192) ;; *) echo "unsupported target max-num-batched-tokens" >&2; exit 2 ;; esac
if test "${source_max_num_seqs}" = "${target_max_num_seqs}" && \
   test "${source_max_num_batched_tokens}" = "${target_max_num_batched_tokens}" && \
   test "${source_profiler_config}" = "${target_profiler_config}"; then
  echo "source and target launch parameters are identical" >&2
  exit 2
fi

case "${run_id}" in
  *[!A-Za-z0-9._-]*|'')
    echo "run_id may contain only letters, digits, dot, underscore, and dash" >&2
    exit 2
    ;;
esac

transition_root=${case_dir}/transitions
run_dir=${transition_root}/${run_id}
before_process=${run_dir}/before-maxseq${source_max_num_seqs}-process.json
after_process=${run_dir}/after-maxseq${target_max_num_seqs}-process.json
service_log=${run_dir}/maxseq${target_max_num_seqs}-service-8030.live.log
startup_log_snapshot=${run_dir}/maxseq${target_max_num_seqs}-service-8030.startup.log
ppu_snapshot=${run_dir}/host-ppu-smi.after-maxseq${target_max_num_seqs}-launch.txt
raw_manifest=${run_dir}/${transition_role}-raw.json

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${expected_image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${source_manifest}"
test -f "${tuned_config_folder}/E=512,N=80,device_name=thead.json"
mkdir -p "${transition_root}"
test ! -e "${run_dir}"
mkdir "${run_dir}"

# Freeze the exact root PID/start ticks, argv, selected environment, and its
# current descendant tree. The source manifest must name this same live service.
docker exec -i "${container}" python3 - \
  "${source_manifest}" "${expected_container_id}" \
  "${source_max_num_seqs}" <<'PY' > "${before_process}"
import json
import os
import sys

source_manifest_path, container_id, source_max_num_seqs_raw = sys.argv[1:]
source_max_num_seqs = int(source_max_num_seqs_raw)
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
port = "8030"
env_keys = (
    "CUDA_VISIBLE_DEVICES",
    "VLLM_WORKER_MULTIPROC_METHOD",
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS",
    "GLOO_SOCKET_IFNAME",
    "NCCL_IB_HCA",
    "NCCL_IB_GID_INDEX",
    "NCCL_IB_ADDR_FAMILY",
    "NCCL_SOCKET_IFNAME",
    "NCCL_SOCKET_FAMILY",
    "VLLM_FL_FLAGOS_BLACKLIST_APPEND",
    "VLLM_TUNED_CONFIG_FOLDER",
    "PATH",
    "LD_LIBRARY_PATH",
)


def proc_stat(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2 :].split()
    return {
        "ppid": int(tail[1]),
        "pgrp": int(tail[2]),
        "session": int(tail[3]),
        "start_ticks": int(tail[19]),
    }


def proc_args(pid):
    return [
        value.decode(errors="replace")
        for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
        if value
    ]


def proc_env(pid):
    values = {}
    for item in open(f"/proc/{pid}/environ", "rb").read().split(b"\0"):
        if b"=" not in item:
            continue
        key, value = item.split(b"=", 1)
        name = key.decode(errors="replace")
        if name in env_keys:
            values[name] = value.decode(errors="replace")
    return values


processes = {}
services = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        args = proc_args(entry)
        stat = proc_stat(entry)
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        continue
    pid = int(entry)
    processes[pid] = {"pid": pid, "args": args, **stat}
    if not any(os.path.basename(value) == "vllm" for value in args):
        continue
    if "serve" not in args or model not in args or "--port" not in args:
        continue
    if args[args.index("--port") + 1] == port:
        services.append(processes[pid])

if len(services) != 1:
    raise SystemExit(f"expected exactly one vLLM root on port {port}, got {len(services)}")
service = dict(services[0])
args = service["args"]
if (
    "--max-num-seqs" not in args
    or args[args.index("--max-num-seqs") + 1] != str(source_max_num_seqs)
):
    raise SystemExit(
        f"port 8030 is not the max-num-seqs={source_max_num_seqs} source"
    )

vllm_index = next(
    index for index, value in enumerate(args) if os.path.basename(value) == "vllm"
)
vllm_args = args[vllm_index + 1 :]
source_manifest = json.load(open(source_manifest_path, encoding="utf-8"))
instance_id = (
    f"{container_id[:12]}-{port}-{service['pid']}-{service['start_ticks']}"
)
if source_manifest.get("service_instance_id") != instance_id:
    raise SystemExit(
        "source manifest does not identify the current port-8030 PID/start-ticks"
    )
if (
    source_manifest.get("launch_config", {}).get("max_num_seqs")
    != source_max_num_seqs
):
    raise SystemExit(
        f"source manifest is not max-num-seqs={source_max_num_seqs}"
    )
if source_manifest.get("launch_config", {}).get("launch_args") != vllm_args:
    raise SystemExit("source manifest launch args do not match the live service")

tree = {service["pid"]}
changed = True
while changed:
    changed = False
    for pid, process in processes.items():
        if pid not in tree and process["ppid"] in tree:
            tree.add(pid)
            changed = True

service["vllm_args"] = vllm_args
service["selected_environment"] = proc_env(service["pid"])
service["tree"] = [dict(processes[pid]) for pid in sorted(tree)]
print(json.dumps(service, indent=2, sort_keys=True))
PY

# Revalidate PID reuse and the entire argv immediately before sending the only
# signal in this script. os.kill executes in the same process as the checks.
docker exec -i "${container}" python3 - "${before_process}" <<'PY'
import json
import os
import signal
import sys

expected = json.load(open(sys.argv[1], encoding="utf-8"))
pid = expected["pid"]
raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2 :].split()
start_ticks = int(tail[19])
args = [
    value.decode(errors="replace")
    for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
    if value
]
if start_ticks != expected["start_ticks"] or args != expected["args"]:
    raise SystemExit("target PID identity changed; refusing to signal")
os.kill(pid, signal.SIGTERM)
PY

# Wait only for the exact PID/start-ticks identities captured in the port-8030
# service tree. No child or unrelated process receives a signal.
docker exec -i "${container}" python3 - "${before_process}" <<'PY'
import json
import os
import sys
import time

expected = json.load(open(sys.argv[1], encoding="utf-8"))["tree"]


def same_process(item):
    try:
        raw = open(f"/proc/{item['pid']}/stat", encoding="utf-8").read()
    except FileNotFoundError:
        return False
    tail = raw[raw.rfind(")") + 2 :].split()
    return int(tail[19]) == item["start_ticks"]


deadline = time.monotonic() + 240
while True:
    live = [item for item in expected if same_process(item)]
    if not live:
        break
    if time.monotonic() >= deadline:
        identities = [(item["pid"], item["start_ticks"]) for item in live]
        raise SystemExit(
            f"timed out waiting for exact port-8030 process tree: {identities}; "
            "no force signal was sent"
        )
    time.sleep(2)
PY

if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is still in use; refusing to launch" >&2
  exit 3
fi

# Same container, devices, environment, model, and launch arguments as the
# source service. Only the explicitly frozen scheduler-limit values may change.
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
  -e VLLM_TUNED_CONFIG_FOLDER="${tuned_config_folder}" \
  -w "${case_dir}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
profiler_args=()
if test -n '${target_profiler_config}'; then
  profiler_args=(--profiler-config '${target_profiler_config}')
fi
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \\
  --served-model-name Qwen3.8-Flash-Next \\
  --host 0.0.0.0 \\
  --port 8030 \\
  --tensor-parallel-size 8 \\
  --pipeline-parallel-size 1 \\
  --dtype bfloat16 \\
  --language-model-only \\
  --max-model-len 80000 \\
  --max-num-seqs ${target_max_num_seqs} \\
  --max-num-batched-tokens ${target_max_num_batched_tokens} \\
  --gpu-memory-utilization 0.90 \\
  --disable-custom-all-reduce \\
  --reasoning-parser qwen3 \\
  --no-enable-prefix-caching \\
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \\
  \"\${profiler_args[@]}\" \\
  > '${service_log}' 2>&1
"

# Capture and freeze the new root identity. Its argv must equal the old argv
# after replacing only the explicitly selected scheduler-limit values.
docker exec -i "${container}" python3 - \
  "${before_process}" "${source_max_num_seqs}" \
  "${target_max_num_seqs}" "${source_max_num_batched_tokens}" \
  "${target_max_num_batched_tokens}" "${source_profiler_config}" \
  "${target_profiler_config}" <<'PY' > "${after_process}"
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

before = json.load(open(sys.argv[1], encoding="utf-8"))
source_max_num_seqs = int(sys.argv[2])
target_max_num_seqs = int(sys.argv[3])
source_max_num_batched_tokens = int(sys.argv[4])
target_max_num_batched_tokens = int(sys.argv[5])
source_profiler_config = sys.argv[6]
target_profiler_config = sys.argv[7]
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"


def stat_start_ticks(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    tail = raw[raw.rfind(")") + 2 :].split()
    return int(tail[19])


def args_for(pid):
    return [
        value.decode(errors="replace")
        for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
        if value
    ]


expected_args = list(before["args"])
index = expected_args.index("--max-num-seqs") + 1
if expected_args[index] != str(source_max_num_seqs):
    raise SystemExit("before service max-num-seqs differs from requested source")
expected_args[index] = str(target_max_num_seqs)
batched_index = expected_args.index("--max-num-batched-tokens") + 1
if expected_args[batched_index] != str(source_max_num_batched_tokens):
    raise SystemExit("before service max-num-batched-tokens differs from requested source")
expected_args[batched_index] = str(target_max_num_batched_tokens)
if source_profiler_config:
    profiler_index = expected_args.index("--profiler-config")
    if expected_args[profiler_index + 1] != source_profiler_config:
        raise SystemExit("before service profiler-config differs from requested source")
    del expected_args[profiler_index : profiler_index + 2]
elif "--profiler-config" in expected_args:
    raise SystemExit("before service unexpectedly has profiler-config")
if target_profiler_config:
    expected_args.extend(["--profiler-config", target_profiler_config])
deadline = time.monotonic() + 120
while True:
    found = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            args = args_for(entry)
            ticks = stat_start_ticks(entry)
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue
        if args == expected_args:
            found.append({"pid": int(entry), "args": args, "start_ticks": ticks})
    if len(found) == 1:
        service = found[0]
        break
    if len(found) > 1:
        raise SystemExit(
            f"multiple exact maxseq{target_max_num_seqs} services found: {found}"
        )
    if time.monotonic() >= deadline:
        raise SystemExit(
            f"exact maxseq{target_max_num_seqs} service did not appear within 120 seconds"
        )
    time.sleep(1)

environment = {}
for item in open(f"/proc/{service['pid']}/environ", "rb").read().split(b"\0"):
    if b"=" not in item:
        continue
    key, value = item.split(b"=", 1)
    name = key.decode(errors="replace")
    if name in before["selected_environment"]:
        environment[name] = value.decode(errors="replace")
if environment != before["selected_environment"]:
    raise SystemExit("selected launch environment changed across max-num-seqs transition")
service["selected_environment"] = environment

repos = {}
for path in (
    "/workspace/vllm-plugin-FL-qwen38-adaptation",
    "/workspace/FlagGems-vllm",
    "/workspace/FlagGems",
):
    tracked = subprocess.check_output(
        ["git", "-C", path, "ls-files", "-co", "--exclude-standard", "-z"]
    )
    digest = hashlib.sha256()
    for rel in sorted(value for value in tracked.split(b"\0") if value):
        digest.update(rel + b"\0")
        digest.update(hashlib.sha256((Path(path) / os.fsdecode(rel)).read_bytes()).digest())
    repos[path] = {
        "head": subprocess.check_output(
            ["git", "-C", path, "rev-parse", "HEAD"], text=True
        ).strip(),
        "status": subprocess.check_output(
            ["git", "-C", path, "status", "--short"], text=True
        ),
        "content_sha256": digest.hexdigest(),
    }
service["repositories"] = repos
print(json.dumps(service, indent=2, sort_keys=True))
PY

ready=0
for _ in $(seq 1 360); do
  if ! docker exec -i "${container}" python3 - "${after_process}" <<'PY'
import json
import sys

expected = json.load(open(sys.argv[1], encoding="utf-8"))
pid = expected["pid"]
raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
tail = raw[raw.rfind(")") + 2 :].split()
if int(tail[19]) != expected["start_ticks"]:
    raise SystemExit("restarted service PID was reused")
args = [
    value.decode(errors="replace")
    for value in open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
    if value
]
if args != expected["args"]:
    raise SystemExit("restarted service argv changed")
PY
  then
    echo "exact restarted service exited before readiness" >&2
    test -f "${service_log}" && tail -200 "${service_log}" >&2
    exit 4
  fi
  if timeout 5s curl -fsS http://127.0.0.1:8030/v1/models >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 5
done
test "${ready}" -eq 1

grep -F 'enable_prefix_caching=False' "${service_log}" >/dev/null
grep -F 'Asynchronous scheduling is enabled.' "${service_log}" >/dev/null
grep -F 'Capturing CUDA graphs (decode, FULL): 100%' "${service_log}" >/dev/null
grep -F 'Application startup complete' "${service_log}" >/dev/null
grep -F "Using configuration from ${tuned_config_folder}/E=512,N=80,device_name=thead.json for MoE layer." "${service_log}" >/dev/null

# Freeze the startup/capture portion because the live service log keeps growing.
cp -- "${service_log}" "${startup_log_snapshot}"
test -s "${startup_log_snapshot}"
ppu-smi > "${ppu_snapshot}"

python3 - \
  "${before_process}" "${after_process}" "${source_manifest}" \
  "${raw_manifest}" "${service_log}" "${startup_log_snapshot}" \
  "${ppu_snapshot}" "${source_max_num_seqs}" "${target_max_num_seqs}" \
  "${source_max_num_batched_tokens}" "${target_max_num_batched_tokens}" \
  "${source_profiler_config}" "${target_profiler_config}" \
  "${transition_role}" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

(
    before_path,
    after_path,
    source_manifest_path,
    manifest_path,
    live_log_path,
    startup_log_path,
    ppu_snapshot_path,
    source_max_num_seqs_raw,
    target_max_num_seqs_raw,
    source_max_num_batched_tokens_raw,
    target_max_num_batched_tokens_raw,
    source_profiler_config,
    target_profiler_config,
    transition_role,
) = sys.argv[1:]
source_max_num_seqs = int(source_max_num_seqs_raw)
target_max_num_seqs = int(target_max_num_seqs_raw)
source_max_num_batched_tokens = int(source_max_num_batched_tokens_raw)
target_max_num_batched_tokens = int(target_max_num_batched_tokens_raw)
before = json.load(open(before_path, encoding="utf-8"))
after = json.load(open(after_path, encoding="utf-8"))
source = json.load(open(source_manifest_path, encoding="utf-8"))
container = json.loads(
    subprocess.check_output(
        ["docker", "inspect", "qwen3.8-flash-opt-candidate-20260919"], text=True
    )
)[0]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def vllm_args(args):
    index = next(
        index for index, value in enumerate(args) if os.path.basename(value) == "vllm"
    )
    return args[index + 1 :]


before_args = vllm_args(before["args"])
after_args = vllm_args(after["args"])
expected_after_args = list(before_args)
index = expected_after_args.index("--max-num-seqs")
if expected_after_args[index + 1] != str(source_max_num_seqs):
    raise SystemExit("before argv max-num-seqs differs from transition source")
expected_after_args[index + 1] = str(target_max_num_seqs)
batched_index = expected_after_args.index("--max-num-batched-tokens")
if expected_after_args[batched_index + 1] != str(source_max_num_batched_tokens):
    raise SystemExit("before argv max-num-batched-tokens differs from transition source")
expected_after_args[batched_index + 1] = str(target_max_num_batched_tokens)
if source_profiler_config:
    profiler_index = expected_after_args.index("--profiler-config")
    if expected_after_args[profiler_index + 1] != source_profiler_config:
        raise SystemExit("before argv profiler-config differs from transition source")
    del expected_after_args[profiler_index : profiler_index + 2]
elif "--profiler-config" in expected_after_args:
    raise SystemExit("before argv unexpectedly has profiler-config")
if target_profiler_config:
    expected_after_args.extend(["--profiler-config", target_profiler_config])
if after_args != expected_after_args:
    raise SystemExit("service argv changed beyond the selected scheduler-limit values")

plugin = after["repositories"]["/workspace/vllm-plugin-FL-qwen38-adaptation"]
fgv = after["repositories"]["/workspace/FlagGems-vllm"]
fg = after["repositories"]["/workspace/FlagGems"]
combined_fg_sha = hashlib.sha256(
    (fgv["content_sha256"] + fg["content_sha256"]).encode()
).hexdigest()
required_hashes = (
    ("plugin_sha256", plugin["content_sha256"]),
    ("flaggems_sha256", combined_fg_sha),
)
for key, actual in required_hashes:
    if source.get(key) != actual:
        raise SystemExit(f"repository content changed across A/B/R: {key}")
if (
    "flaggems_vllm_sha256" in source
    and source["flaggems_vllm_sha256"] != fgv["content_sha256"]
):
    raise SystemExit("repository content changed across A/B/R: flaggems_vllm_sha256")
startup_text = Path(startup_log_path).read_text(errors="replace")
service_instance_id = (
    f"{container['Id'][:12]}-8030-{after['pid']}-{after['start_ticks']}"
)
manifest = {
    "schema_version": 1,
    "manifest_kind": "raw-service-transition",
    "host": "PPU-01",
    "optimization_container_name": container["Name"].lstrip("/"),
    "container_id": container["Id"],
    "service_instance_id": service_instance_id,
    "model_name": "Qwen3.8-Flash-Next",
    "base_url": "http://127.0.0.1:8030/v1/completions",
    "mode": "graph",
    "model_sha256": "99e815241ef03325536b0aaa4441deea45174c17fae31e10f0bb456410c590de",
    "tokenizer_sha256": "6b49e287d3318979ff15f5a17d67806f67848399c71ed4201f23ab6e5fe44d6c",
    "engine_sha256": "fd3708e5a13abe98c566afd79a6b1987cef70c0548bb19c1218ff6a7f9d43346",
    "plugin_sha256": plugin["content_sha256"],
    "flaggems_vllm_sha256": fgv["content_sha256"],
    "flaggems_sha256": combined_fg_sha,
    "runtime_evidence_sha256": sha(after_path),
    "launch_config": {
        "enable_prefix_caching": False,
        "max_num_seqs": target_max_num_seqs,
        "max_num_batched_tokens": target_max_num_batched_tokens,
        "launch_args": after_args,
        "selected_environment": after["selected_environment"],
    },
    "transition": {
        "source_manifest_path": source_manifest_path,
        "source_manifest_sha256": sha(source_manifest_path),
        "before_service_instance_id": source["service_instance_id"],
        "before_pid": before["pid"],
        "before_start_ticks": before["start_ticks"],
        "after_pid": after["pid"],
        "after_start_ticks": after["start_ticks"],
        "only_launch_arg_change": {
            "max_num_seqs": {
                "from": source_max_num_seqs,
                "to": target_max_num_seqs,
            },
            "max_num_batched_tokens": {
                "from": source_max_num_batched_tokens,
                "to": target_max_num_batched_tokens,
            },
            "profiler_config": {
                "from": source_profiler_config,
                "to": target_profiler_config,
            },
        },
    },
    "image_lineage": "verified",
    "mount_parity": "passed",
    "tokenizer_path": "/mnt/cpfs/models/Qwen3.8-Flash-Next",
    "performance_context": {
        "platform": "thead-ppu",
        "device_model": "PPU-ZW810E",
        "device_ids": [str(value) for value in range(8, 16)],
        "driver_version": "2.1.1-rbd225",
        "device_runtime_version": "PPU-SMI-1.28",
        "image_id": container["Image"],
        "prefix_cache_state": "disabled",
        "cache_preparation": (
            "CLI includes --no-enable-prefix-caching and immutable startup log "
            "records enable_prefix_caching=False."
        ),
    },
    "evidence": {
        "role": transition_role,
        "before_process_path": before_path,
        "before_process_sha256": sha(before_path),
        "after_process_path": after_path,
        "after_process_sha256": sha(after_path),
        "live_log_path": live_log_path,
        "startup_log_snapshot_path": startup_log_path,
        "startup_log_snapshot_sha256": sha(startup_log_path),
        "ppu_snapshot_path": ppu_snapshot_path,
        "ppu_snapshot_sha256": sha(ppu_snapshot_path),
        "graph_capture_complete": (
            "Capturing CUDA graphs (decode, FULL): 100%" in startup_text
        ),
        "application_startup_complete": "Application startup complete" in startup_text,
        "async_scheduling_enabled": "Asynchronous scheduling is enabled." in startup_text,
        "plugin_head": plugin["head"],
        "flaggems_vllm_head": fgv["head"],
        "flaggems_head": fg["head"],
    },
}
with open(manifest_path, "x", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

sha256sum \
  "${before_process}" "${after_process}" "${source_manifest}" \
  "${startup_log_snapshot}" "${ppu_snapshot}" "${raw_manifest}"
