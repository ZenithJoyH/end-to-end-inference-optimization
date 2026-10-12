#!/usr/bin/env bash
set -euo pipefail

root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
old_case=${root}/accuracy/acc-008-full-gpqa-dual-service-current-candidate-20260922
case_dir=${root}/accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
config_dir=${root}/configs/moe-bm16-decode-only-01
expected_source=${root}/fw-014-p16k-no-async-scheduling-repaired-contract/fresh-abr-service86-88/source-fingerprint.initial.json
commands=${root}/commands

test ! -e "${case_dir}"
test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
mkdir -p "${case_dir}/commands" "${case_dir}/evaluation" "${case_dir}/evidence" \
  "${case_dir}/services/service-a" "${case_dir}/services/service-b" "${case_dir}/results"
cp -a "${old_case}/bundle" "${case_dir}/bundle"
cp "${old_case}/evidence/evaluator.inspect.json" "${case_dir}/evidence/evaluator.inspect.json"
cp "${old_case}/evidence/skill-bundle.json" "${case_dir}/evidence/skill-bundle.json"
cp "${old_case}/commands/dual-service-proxy.py" "${case_dir}/commands/dual-service-proxy.py"

docker top "${container}" -eo pid,ppid,lstart,stat,args > "${case_dir}/evidence/processes.before-transition.txt"
ppu-smi > "${case_dir}/evidence/ppu-smi.before-transition.txt"

mapfile -t pid8000 < <(docker exec "${container}" pgrep -f '^/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next .*--port 8000 ')
mapfile -t pid8010 < <(docker exec "${container}" pgrep -f '^/usr/local/bin/python3.12 /usr/local/bin/vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next .*--port 8010 ')
test "${#pid8000[@]}" -eq 1
test "${#pid8010[@]}" -eq 1
docker exec "${container}" sh -c "tr '\0' '\n' < /proc/${pid8000[0]}/environ" > "${case_dir}/evidence/service-8000.before.env"
docker exec "${container}" sh -c "tr '\0' '\n' < /proc/${pid8010[0]}/environ" > "${case_dir}/evidence/service-8010.before.env"
if grep -q '^VLLM_FL_QSA_STATIC_SCORE_COLUMNS=' "${case_dir}/evidence/service-8000.before.env"; then
  echo 'port 8000 is not the verified unbounded control' >&2
  exit 3
fi
grep -Fx 'VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448' "${case_dir}/evidence/service-8010.before.env"
curl -fsS http://127.0.0.1:8000/v1/models > "${case_dir}/services/models-8000.json"

docker exec "${container}" kill -TERM "${pid8010[0]}"
for _ in $(seq 1 120); do
  if ! docker exec "${container}" test -d "/proc/${pid8010[0]}"; then break; fi
  sleep 1
done
test ! -d "/proc/${pid8010[0]}"

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
  -e VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_,mm,mm_out \
  -e VLLM_TUNED_CONFIG_FOLDER="${config_dir}" \
  -w "${root}" \
  "${container}" bash -lc "
set -e
source /usr/local/PPU_SDK/envsetup.sh
export PATH=/usr/lib64/openmpi/bin:\${PATH}
export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}
unset VLLM_FL_QSA_STATIC_SCORE_COLUMNS
exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next \\
  --served-model-name Qwen3.8-Flash-Next --host 0.0.0.0 --port 8010 \\
  --tensor-parallel-size 8 --pipeline-parallel-size 1 --dtype bfloat16 \\
  --language-model-only --max-model-len 80000 --max-num-seqs 64 \\
  --max-num-batched-tokens 4096 --gpu-memory-utilization 0.90 \\
  --disable-custom-all-reduce --reasoning-parser qwen3 \\
  --no-enable-prefix-caching \\
  --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' \\
  > '${case_dir}/services/service-b/service-8010.log' 2>&1
"

ready=0
for _ in $(seq 1 900); do
  if curl -fsS http://127.0.0.1:8010/v1/models > "${case_dir}/services/models-8010.json.tmp" 2>/dev/null; then
    mv "${case_dir}/services/models-8010.json.tmp" "${case_dir}/services/models-8010.json"
    ready=1
    break
  fi
  sleep 2
done
test "${ready}" -eq 1
grep -F 'enable_prefix_caching=False' "${case_dir}/services/service-b/service-8010.log" >/dev/null
grep -F 'Capturing CUDA graphs (decode, FULL): 100%' "${case_dir}/services/service-b/service-8010.log" >/dev/null
grep -F 'Application startup complete' "${case_dir}/services/service-b/service-8010.log" >/dev/null
grep -F 'Asynchronous scheduling is enabled.' "${case_dir}/services/service-b/service-8010.log" >/dev/null
grep -F 'Using configuration from' "${case_dir}/services/service-b/service-8010.log" >/dev/null

docker exec -i "${container}" python3 - "${case_dir}/services/services-runtime.json" <<'PY'
import json, os, sys
output = sys.argv[1]
found = []
for entry in os.listdir('/proc'):
    if not entry.isdigit():
        continue
    try:
        argv = [x.decode(errors='replace') for x in open(f'/proc/{entry}/cmdline','rb').read().split(b'\0') if x]
        raw = open(f'/proc/{entry}/stat', encoding='utf-8').read()
        env_raw = open(f'/proc/{entry}/environ','rb').read().split(b'\0')
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if 'serve' not in argv or '--port' not in argv:
        continue
    port = argv[argv.index('--port') + 1]
    if port not in ('8000', '8010') or '/mnt/cpfs/models/Qwen3.8-Flash-Next' not in argv:
        continue
    env = {}
    for item in env_raw:
        if b'=' in item:
            k, v = item.split(b'=', 1)
            env[k.decode(errors='replace')] = v.decode(errors='replace')
    keys = ('CUDA_VISIBLE_DEVICES','VLLM_WORKER_MULTIPROC_METHOD','VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS',
            'GLOO_SOCKET_IFNAME','NCCL_IB_HCA','NCCL_IB_GID_INDEX','NCCL_IB_ADDR_FAMILY',
            'NCCL_SOCKET_IFNAME','NCCL_SOCKET_FAMILY','VLLM_FL_FLAGOS_BLACKLIST_APPEND',
            'VLLM_TUNED_CONFIG_FOLDER','VLLM_FL_QSA_STATIC_SCORE_COLUMNS')
    found.append({'port': int(port), 'pid': int(entry),
                  'start_ticks': int(raw[raw.rfind(')')+2:].split()[19]),
                  'argv': argv, 'selected_environment': {k: env.get(k) for k in keys}})
if len(found) != 2 or {x['port'] for x in found} != {8000, 8010}:
    raise SystemExit(f'expected two service roots, found {found}')
found.sort(key=lambda x: x['port'])
for replica in found:
    env = replica['selected_environment']
    want_devices = '0,1,2,3,4,5,6,7' if replica['port'] == 8000 else '8,9,10,11,12,13,14,15'
    if env['CUDA_VISIBLE_DEVICES'] != want_devices:
        raise SystemExit('device binding mismatch')
    if env['VLLM_FL_FLAGOS_BLACKLIST_APPEND'] != '_conv_depthwise2d,index,normal_,mm,mm_out':
        raise SystemExit('provider config mismatch')
    if env['VLLM_FL_QSA_STATIC_SCORE_COLUMNS'] is not None:
        raise SystemExit('QSA static bound unexpectedly present')
    if '--no-enable-prefix-caching' not in replica['argv'] or '--no-async-scheduling' in replica['argv']:
        raise SystemExit('launch flag mismatch')
with open(output, 'w') as f:
    json.dump({'schema_version': 1, 'replicas': found}, f, indent=2, sort_keys=True)
    f.write('\n')
PY

docker exec "${container}" python3 "${commands}/op023_source_fingerprint.py" \
  --expected "${expected_source}" --output "${case_dir}/evidence/source.ready.json"
docker exec "${container}" python3 "${commands}/op023r_qsa_guard.py" \
  --output "${case_dir}/evidence/qsa.ready.json"

python3 - "${old_case}/services/service-manifest.prototype.json" \
  "${case_dir}/services/services-runtime.json" "${case_dir}/services/service-manifest.prototype.json" <<'PY'
import json, sys
from pathlib import Path
source, runtime_path, output = sys.argv[1:]
manifest = json.load(open(source))
manifest['service_instance_id'] = 'pending-proxy-runtime'
manifest['runtime_evidence_sha256'] = '0' * 64
manifest['launch_config']['qsa_static_score_columns'] = None
manifest['launch_config']['replicas'] = json.load(open(runtime_path))['replicas']
manifest['performance_context']['cache_preparation'] = 'Two TP8 graph replicas with QSA static score bound absent; prefix caching disabled.'
Path(output).write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
PY

python3 - "${old_case}/evaluation/llm-config.json" "${case_dir}/evaluation/llm-config.json" "${case_dir}" <<'PY'
import json, sys
from pathlib import Path
source, output, case_dir = sys.argv[1:]
cfg = json.load(open(source))
cfg['eval_model'] = 'Qwen3.8-Flash-Next-current-optimized-dual-qsa-unbounded-20260922'
cfg['output_root'] = case_dir + '/results'
cfg['cache_root'] = '/tmp/qwen38-acc009-full-gpqa-cache'
cfg['run_id'] = 'acc009-full-gpqa-dual-qsa-unbounded-20260922'
Path(output).write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
PY

docker top "${container}" -eo pid,ppid,lstart,stat,args > "${case_dir}/evidence/processes.ready.txt"
ppu-smi > "${case_dir}/evidence/ppu-smi.ready.txt"
sha256sum "${case_dir}/services/services-runtime.json" \
  "${case_dir}/services/service-manifest.prototype.json" \
  "${case_dir}/evidence/source.ready.json" "${case_dir}/evidence/qsa.ready.json" \
  "${case_dir}/evaluation/llm-config.json" > "${case_dir}/services/ready.SHA256SUMS"
date -Iseconds > "${case_dir}/services/READY"
