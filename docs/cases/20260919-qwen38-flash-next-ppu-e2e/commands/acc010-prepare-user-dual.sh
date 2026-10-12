#!/usr/bin/env bash
set -euo pipefail

root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
old_case=${root}/accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922
case_dir=${root}/accuracy/acc-010-full-gpqa-dual-user-services-20260923
model_container=qwen3.8-flash-opt-candidate-20260919
eval_container=qwen38-eval-e2e-20260919

test ! -e "${case_dir}"
test "$(docker inspect --format '{{.State.Running}}' "${model_container}")" = true
test "$(docker inspect --format '{{.State.Running}}' "${eval_container}")" = true
mkdir -p "${case_dir}/commands" "${case_dir}/evaluation" "${case_dir}/evidence" \
  "${case_dir}/services" "${case_dir}/results"
cp -a "${old_case}/bundle" "${case_dir}/bundle"
cp "${old_case}/commands/dual-service-proxy.py" "${case_dir}/commands/dual-service-proxy.py"
docker inspect "${eval_container}" > "${case_dir}/evidence/evaluator.inspect.json"
docker inspect "${model_container}" > "${case_dir}/evidence/model-container.inspect.json"

if ss -ltn | grep -qE ':8041[[:space:]]'; then
  echo 'port 8041 is already occupied' >&2
  exit 3
fi
if docker exec "${eval_container}" sh -lc "ps -eo args | grep -E 'formal_accuracy|llmrun|lm_eval|dual-service-proxy' | grep -v grep"; then
  echo 'an evaluator process is already running' >&2
  exit 4
fi

curl -fsS --max-time 10 http://127.0.0.1:8000/v1/models > "${case_dir}/services/models-8000.json"
curl -fsS --max-time 10 http://127.0.0.1:8010/v1/models > "${case_dir}/services/models-8010.json"

docker exec -i "${model_container}" python3 - "${case_dir}/services/services-runtime.json" <<'PY'
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
    want_devices = '8,9,10,11,12,13,14,15' if replica['port'] == 8000 else '0,1,2,3,4,5,6,7'
    if env['CUDA_VISIBLE_DEVICES'] != want_devices:
        raise SystemExit('device binding mismatch')
    if env['VLLM_FL_QSA_STATIC_SCORE_COLUMNS'] is not None:
        raise SystemExit('QSA static bound unexpectedly present')
    argv = replica['argv']
    def arg(name):
        return argv[argv.index(name) + 1]
    if arg('--max-num-seqs') != '32' or arg('--max-num-batched-tokens') != '4096':
        raise SystemExit('launch shape mismatch')
with open(output, 'w') as f:
    json.dump({'schema_version': 1, 'replicas': found}, f, indent=2, sort_keys=True)
    f.write('\n')
PY

docker exec "${model_container}" python3 "${root}/commands/op023_source_fingerprint.py" \
  --output "${case_dir}/evidence/source.ready.json"

python3 - "${old_case}/services/service-manifest.prototype.json" \
  "${case_dir}/services/services-runtime.json" "${case_dir}/evidence/source.ready.json" \
  "${case_dir}/services/service-manifest.prototype.json" <<'PY'
import json, sys
from pathlib import Path

source, runtime_path, fingerprint_path, output = sys.argv[1:]
manifest = json.load(open(source))
runtime = json.load(open(runtime_path))
fingerprint = json.load(open(fingerprint_path))
repos = fingerprint['repositories']
manifest['service_instance_id'] = 'pending-proxy-runtime'
manifest['runtime_evidence_sha256'] = '0' * 64
manifest['plugin_sha256'] = repos['/workspace/vllm-plugin-FL-qwen38-adaptation']['content_sha256']
manifest['flaggems_vllm_sha256'] = repos['/workspace/FlagGems-vllm']['content_sha256']
manifest['flaggems_sha256'] = repos['/workspace/FlagGems']['content_sha256']
manifest['launch_config']['async_scheduling'] = True
manifest['launch_config']['enable_prefix_caching'] = False
manifest['launch_config']['max_num_seqs'] = 32
manifest['launch_config']['max_num_batched_tokens'] = 4096
manifest['launch_config']['qsa_static_score_columns'] = None
manifest['launch_config']['replicas'] = runtime['replicas']
manifest['launch_config']['shared_args'] = [
    'serve', '/mnt/cpfs/models/Qwen3.8-Flash-Next', '--served-model-name', 'Qwen3.8-Flash-Next',
    '--host', '0.0.0.0', '--tensor-parallel-size', '8', '--pipeline-parallel-size', '1',
    '--dtype', 'bfloat16', '--language-model-only', '--max-model-len', '80000',
    '--max-num-seqs', '32', '--max-num-batched-tokens', '4096',
    '--gpu-memory-utilization', '0.90', '--disable-custom-all-reduce',
    '--reasoning-parser', 'qwen3', '--compilation-config', '{"cudagraph_mode":"FULL_AND_PIECEWISE"}'
]
manifest['performance_context']['cache_preparation'] = (
    'Two user-started TP8 graph replicas; QSA static score bound absent; prefix caching disabled.'
)
Path(output).write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
PY

python3 - "${old_case}/evaluation/llm-config.json" "${case_dir}/evaluation/llm-config.json" "${case_dir}" <<'PY'
import json, sys
from pathlib import Path

source, output, case_dir = sys.argv[1:]
cfg = json.load(open(source))
cfg['eval_model'] = 'Qwen3.8-Flash-Next-user-dual-maxseq32-20260923'
cfg['output_root'] = case_dir + '/results'
cfg['cache_root'] = '/tmp/qwen38-acc010-full-gpqa-cache-20260923'
cfg['run_id'] = 'acc010-full-gpqa-dual-user-services-20260923'
Path(output).write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
PY

repo=${case_dir}/bundle/repo
eval_dir=${case_dir}/evaluation
docker exec "${eval_container}" python3 "${repo}/evaluation/accuracy/formal_accuracy.py" \
  --config "${eval_dir}/llm-config.json" \
  --evaluation-inspect "${case_dir}/evidence/evaluator.inspect.json" \
  --capture-provenance "${eval_dir}/task-provenance-1.json" \
  > "${eval_dir}/provenance-1.log" 2>&1
docker exec "${eval_container}" python3 "${repo}/evaluation/accuracy/formal_accuracy.py" \
  --config "${eval_dir}/llm-config.json" \
  --evaluation-inspect "${case_dir}/evidence/evaluator.inspect.json" \
  --capture-provenance "${eval_dir}/task-provenance-2.json" \
  > "${eval_dir}/provenance-2.log" 2>&1
cmp "${eval_dir}/task-provenance-1.json" "${eval_dir}/task-provenance-2.json"

python3 - "${eval_dir}/task-provenance-1.json" "${eval_dir}/contract.json" <<'PY'
import hashlib, json, sys
from pathlib import Path

provenance_path = Path(sys.argv[1])
contract_path = Path(sys.argv[2])
provenance = json.loads(provenance_path.read_text())
payload = {
    'schema_version': 3,
    'task': 'gpqa_diamond_generative_cot',
    'metric': 'exact_match,strict-match',
    'expected_samples': 198,
    'expected_doc_ids': list(range(198)),
    'dataset_revision': provenance['dataset_revision'],
    'task_provenance': {
        'path': str(provenance_path),
        'sha256': hashlib.sha256(provenance_path.read_bytes()).hexdigest(),
    },
    'threshold': 0.88,
}
contract_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
PY

sha256sum "${eval_dir}/llm-config.json" "${eval_dir}/task-provenance-1.json" \
  "${eval_dir}/task-provenance-2.json" "${eval_dir}/contract.json" \
  "${case_dir}/evidence/evaluator.inspect.json" "${case_dir}/services/services-runtime.json" \
  "${case_dir}/services/service-manifest.prototype.json" > "${eval_dir}/prepared.SHA256SUMS"
date -Iseconds > "${eval_dir}/PREPARED"
