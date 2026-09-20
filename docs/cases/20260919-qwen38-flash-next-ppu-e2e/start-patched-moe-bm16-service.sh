#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
expected_container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
source_manifest=${case_root}/transitions/p4k-maxbt6144-failed-restored4096-service-15/p4k-maxbt6144-failed-restored4096-service-15-raw.json
config_dir=${case_root}/configs/moe-bm16-decode-only-01
service_label=${1:-post-prof002-restored-bt4096-service-18}
manifest_name=${2:-candidate-maxseq64-bt4096-moe-bm16-post-prof002-service-18.json}
long_prefill_threshold=${3:-0}
source_candidate=${4:-0}
qsa_static_score_columns=${5:-0}
case "${long_prefill_threshold}" in
  0) long_prefill_cli= ;;
  2048) long_prefill_cli="--long-prefill-token-threshold 2048" ;;
  *) echo "unsupported long Prefill threshold" >&2; exit 2 ;;
esac
case "${source_candidate}" in 0|1|2) ;; *) echo "invalid source candidate flag" >&2; exit 2;; esac
case "${qsa_static_score_columns}" in
  0|8448) ;;
  *) echo "unsupported QSA static score width" >&2; exit 2 ;;
esac
run_dir=${case_root}/transitions/${service_label}
service_log=${run_dir}/${service_label}-8030.live.log
startup_log=${run_dir}/${service_label}-8030.startup.log
after_process=${run_dir}/after-process.json
manifest=${case_root}/manifests/${manifest_name}

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${expected_container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test -f "${source_manifest}"
test -f "${config_dir}/E=512,N=80,device_name=thead.json"
if test "${source_candidate}" -eq 1; then
  expected_patch=${case_root}/patches/op-005-qsa-row-range-topk-05/applied.patch
  test -f "${expected_patch}"
  live_diff_sha=$(docker exec "${container}" git -C /workspace/FlagGems diff -- src/flag_gems/fused/qsa.py | sha256sum | awk '{print $1}')
  test "${live_diff_sha}" = "$(sha256sum "${expected_patch}" | awk '{print $1}')"
  test "$(docker exec "${container}" git -C /workspace/FlagGems status --short)" = ' M src/flag_gems/fused/qsa.py'
fi
if test "${source_candidate}" -eq 2; then
  patch_dir=${case_root}/patches/op-006-qsa-static-bound-08
  fg_expected=${patch_dir}/flaggems.applied.patch
  plugin_expected=${patch_dir}/plugin.applied.patch
  test -f "${fg_expected}"
  test -f "${plugin_expected}"
  fg_live_sha=$(docker exec "${container}" git -C /workspace/FlagGems diff -- src/flag_gems/fused/qsa.py | sha256sum | awk '{print $1}')
  plugin_live_sha=$(docker exec "${container}" git -C /workspace/vllm-plugin-FL-qwen38-adaptation diff -- vllm_fl/models/qwen3_8_flash_next.py | sha256sum | awk '{print $1}')
  test "${fg_live_sha}" = "$(sha256sum "${fg_expected}" | awk '{print $1}')"
  test "${plugin_live_sha}" = "$(sha256sum "${plugin_expected}" | awk '{print $1}')"
  test "$(docker exec "${container}" git -C /workspace/FlagGems status --short)" = ' M src/flag_gems/fused/qsa.py'
  docker exec "${container}" git -C /workspace/vllm-plugin-FL-qwen38-adaptation status --short | grep -F ' M vllm_fl/models/qwen3_8_flash_next.py' >/dev/null
  test "${qsa_static_score_columns}" -eq 8448
fi
test ! -e "${run_dir}"
test ! -e "${manifest}"
if ss -ltnH 'sport = :8030' | grep -q .; then
  echo "port 8030 is already in use" >&2
  exit 3
fi
mkdir "${run_dir}"

qsa_env_args=()
if test "${qsa_static_score_columns}" -ne 0; then
  qsa_env_args=(-e "VLLM_FL_QSA_STATIC_SCORE_COLUMNS=${qsa_static_score_columns}")
fi

docker exec -i -e VLLM_TUNED_CONFIG_FOLDER="${config_dir}" "${container}" bash -lc '
set -e
source /usr/local/PPU_SDK/envsetup.sh
python3 - <<"PY"
from vllm.model_executor.layers.fused_moe.fused_moe import (
    get_default_config,
    get_moe_configs,
    try_get_optimal_moe_config,
)

get_moe_configs.cache_clear()
candidate_64 = try_get_optimal_moe_config((512, 160, 2560), (512, 2560, 80), 10, None, 64)
assert candidate_64["BLOCK_SIZE_M"] == 16, candidate_64
for tokens in (1, 32, 63, 65, 96, 4096):
    candidate = try_get_optimal_moe_config((512, 160, 2560), (512, 2560, 80), 10, None, tokens)
    baseline = get_default_config(tokens, 512, 80, 2560, 10, None, None)
    assert candidate == baseline, (tokens, candidate, baseline)
print("Post-prof002 max-batched-tokens 4096 plus decode-only MoE tuned-config guard passed")
PY
' > "${run_dir}/config-guard.txt" 2>&1

docker exec -d \
  "${qsa_env_args[@]}" \
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
  -e VLLM_TUNED_CONFIG_FOLDER="${config_dir}" \
  -w "${case_root}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \
  --served-model-name Qwen3.8-Flash-Next \
  --host 0.0.0.0 \
  --port 8030 \
  --tensor-parallel-size 8 \
  --pipeline-parallel-size 1 \
  --dtype bfloat16 \
  --language-model-only \
  --max-model-len 80000 \
  --max-num-seqs 64 \
  --max-num-batched-tokens 4096 \
  ${long_prefill_cli} \
  --gpu-memory-utilization 0.90 \
  --disable-custom-all-reduce \
  --reasoning-parser qwen3 \
  --no-enable-prefix-caching \
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \
  > '${service_log}' 2>&1
"

docker exec -i "${container}" python3 - "${after_process}" "${long_prefill_threshold}" "${qsa_static_score_columns}" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

output = sys.argv[1]
long_prefill_threshold = int(sys.argv[2])
qsa_static_score_columns = int(sys.argv[3])
model = "/mnt/cpfs/models/Qwen3.8-Flash-Next"
expected_launch = [
    "serve", model, "--served-model-name", "Qwen3.8-Flash-Next",
    "--host", "0.0.0.0", "--port", "8030", "--tensor-parallel-size", "8",
    "--pipeline-parallel-size", "1", "--dtype", "bfloat16",
    "--language-model-only", "--max-model-len", "80000", "--max-num-seqs", "64",
    "--max-num-batched-tokens", "4096",
]
if long_prefill_threshold:
    expected_launch.extend(
        ["--long-prefill-token-threshold", str(long_prefill_threshold)]
    )
expected_launch.extend([
    "--gpu-memory-utilization", "0.90",
    "--disable-custom-all-reduce", "--reasoning-parser", "qwen3",
    "--no-enable-prefix-caching", "--compilation-config",
    '{"cudagraph_mode":"FULL_AND_PIECEWISE"}',
])
env_keys = (
    "CUDA_VISIBLE_DEVICES", "VLLM_WORKER_MULTIPROC_METHOD",
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS", "GLOO_SOCKET_IFNAME", "NCCL_IB_HCA",
    "NCCL_IB_GID_INDEX", "NCCL_IB_ADDR_FAMILY", "NCCL_SOCKET_IFNAME",
    "NCCL_SOCKET_FAMILY", "VLLM_FL_FLAGOS_BLACKLIST_APPEND",
    "VLLM_TUNED_CONFIG_FOLDER", "VLLM_FL_QSA_STATIC_SCORE_COLUMNS",
)


def proc_args(pid):
    return [value.decode(errors="replace") for value in open(
        f"/proc/{pid}/cmdline", "rb").read().split(b"\0") if value]


def start_ticks(pid):
    raw = open(f"/proc/{pid}/stat", encoding="utf-8").read()
    return int(raw[raw.rfind(")") + 2 :].split()[19])


deadline = time.monotonic() + 120
while True:
    matches = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            argv = proc_args(entry)
            ticks = start_ticks(entry)
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue
        if not any(os.path.basename(value) == "vllm" for value in argv):
            continue
        index = next((i for i, value in enumerate(argv) if os.path.basename(value) == "vllm"), None)
        if index is not None and argv[index + 1 :] == expected_launch:
            matches.append({"pid": int(entry), "args": argv, "start_ticks": ticks})
    if len(matches) == 1:
        service = matches[0]
        break
    if len(matches) > 1:
        raise SystemExit(f"multiple exact services found: {matches}")
    if time.monotonic() >= deadline:
        raise SystemExit("exact patched service did not appear")
    time.sleep(1)

environment = {}
for item in open(f"/proc/{service['pid']}/environ", "rb").read().split(b"\0"):
    if b"=" not in item:
        continue
    key, value = item.split(b"=", 1)
    name = key.decode(errors="replace")
    if name in env_keys:
        environment[name] = value.decode(errors="replace")
service["selected_environment"] = environment
service["launch_args"] = expected_launch
expected_qsa = str(qsa_static_score_columns) if qsa_static_score_columns else None
if environment.get("VLLM_FL_QSA_STATIC_SCORE_COLUMNS") != expected_qsa:
    raise SystemExit("QSA static score environment does not match requested value")

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
        "head": subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip(),
        "status": subprocess.check_output(["git", "-C", path, "status", "--short"], text=True),
        "content_sha256": digest.hexdigest(),
    }
service["repositories"] = repos
Path(output).write_text(json.dumps(service, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

ready=0
for _ in $(seq 1 360); do
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
grep -F "Using configuration from ${config_dir}/E=512,N=80,device_name=thead.json for MoE layer." "${service_log}" >/dev/null
cp -- "${service_log}" "${startup_log}"

python3 - "${source_manifest}" "${after_process}" "${startup_log}" "${manifest}" "${service_label}" "${long_prefill_threshold}" "${source_candidate}" "${qsa_static_score_columns}" <<'PY'
import hashlib
import json
import subprocess
import sys
from pathlib import Path

source_path, process_path, startup_path, output_path, service_label, long_prefill_threshold, source_candidate, qsa_static_score_columns = sys.argv[1:]
source_candidate = int(source_candidate)
qsa_static_score_columns = int(qsa_static_score_columns)
source = json.load(open(source_path, encoding="utf-8"))
process = json.load(open(process_path, encoding="utf-8"))
container = json.loads(subprocess.check_output(
    ["docker", "inspect", "qwen3.8-flash-opt-candidate-20260919"], text=True))[0]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


plugin = process["repositories"]["/workspace/vllm-plugin-FL-qwen38-adaptation"]
fgv = process["repositories"]["/workspace/FlagGems-vllm"]
fg = process["repositories"]["/workspace/FlagGems"]
combined_fg_sha = hashlib.sha256((fgv["content_sha256"] + fg["content_sha256"]).encode()).hexdigest()
if source.get("flaggems_vllm_sha256") not in (None, fgv["content_sha256"]):
    raise SystemExit("FlagGems-vllm content changed unexpectedly")
if source_candidate == 0 and source["flaggems_sha256"] != combined_fg_sha:
    raise SystemExit("FlagGems content changed unexpectedly")
if source_candidate in (1, 2) and fg["status"] != " M src/flag_gems/fused/qsa.py\n":
    raise SystemExit(f"unexpected FlagGems candidate status: {fg['status']!r}")
if source_candidate == 2 and " M vllm_fl/models/qwen3_8_flash_next.py\n" not in plugin["status"]:
    raise SystemExit(f"QSA Plugin candidate is not present: {plugin['status']!r}")
instance_id = f"{container['Id'][:12]}-8030-{process['pid']}-{process['start_ticks']}"
manifest = {
    key: source[key]
    for key in (
        "host", "optimization_container_name", "model_name", "base_url", "mode",
        "model_sha256", "tokenizer_sha256", "engine_sha256", "image_lineage",
        "mount_parity", "tokenizer_path", "performance_context",
    )
}
manifest.update({
    "schema_version": 1,
    "service_instance_id": instance_id,
    "plugin_sha256": plugin["content_sha256"],
    "flaggems_vllm_sha256": fgv["content_sha256"],
    "flaggems_sha256": combined_fg_sha,
    "runtime_evidence_sha256": sha(process_path),
    "launch_config": {
        "enable_prefix_caching": False,
        "max_num_seqs": 64,
        "max_num_batched_tokens": 4096,
        "long_prefill_token_threshold": int(long_prefill_threshold),
        "qsa_static_score_columns": qsa_static_score_columns or None,
        "launch_args": process["launch_args"],
    },
    "evidence": {
        "role": service_label,
        "source_candidate": source_candidate,
        "source_candidate_patches": (
            ["/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op-005-qsa-row-range-topk-05/applied.patch"]
            if source_candidate == 1
            else [
                "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op-006-qsa-static-bound-08/flaggems.applied.patch",
                "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op-006-qsa-static-bound-08/plugin.applied.patch",
            ]
            if source_candidate == 2
            else []
        ),
        "process_path": process_path,
        "startup_log_path": startup_path,
        "startup_log_sha256": sha(startup_path),
        "plugin_head": plugin["head"],
        "plugin_status": plugin["status"],
    },
})
Path(output_path).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

python3 "${case_root}/commands/performance/verify-live-service-manifest.py" \
  "${manifest}" "${container}" 8030 64
sha256sum "${run_dir}/config-guard.txt" "${after_process}" "${startup_log}" "${manifest}"
