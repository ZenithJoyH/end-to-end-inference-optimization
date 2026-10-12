#!/usr/bin/env bash
set -uo pipefail

case_dir=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/accuracy/acc-011-full-gpqa-dual-cachefix-20260924
repo=${case_dir}/bundle/repo
prepared_dir=${case_dir}/evaluation
eval_dir=${prepared_dir}/run-003

test -f "${prepared_dir}/PREPARED" || exit 120
mkdir "${eval_dir}" || exit 119
test ! -e "${eval_dir}/STARTED" || exit 121
date -Iseconds > "${eval_dir}/STARTED"
printf '%s\n' "$$" > "${eval_dir}/runner.pid"

proxy_pid=''
cleanup() {
  rc=$?
  if [[ -n "${proxy_pid}" ]] && kill -0 "${proxy_pid}" 2>/dev/null; then
    kill "${proxy_pid}" 2>/dev/null || true
    wait "${proxy_pid}" 2>/dev/null || true
  fi
  printf '%s\n' "${rc}" > "${eval_dir}/exit.code"
  date -Iseconds > "${eval_dir}/FINISHED"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python3 "${case_dir}/commands/dual-service-proxy.py" > "${eval_dir}/proxy.log" 2>&1 &
proxy_pid=$!
printf '%s\n' "${proxy_pid}" > "${eval_dir}/proxy.pid"
for _ in $(seq 1 60); do
  if curl -fsS --max-time 5 http://127.0.0.1:8041/v1/models >/dev/null 2>&1; then break; fi
  sleep 2
done
curl -fsS --max-time 10 http://127.0.0.1:8041/v1/models > "${eval_dir}/proxy-models.json" || exit 122

smoke='{"model":"Qwen3.8-Flash-Next","messages":[{"role":"user","content":"Reply with A."}],"temperature":1.0,"top_p":0.95,"top_k":20,"min_p":0.0,"presence_penalty":0.0,"repetition_penalty":1.0,"max_tokens":2}'
for port in 8000 8010; do
  curl -fsS --max-time 300 -H 'Content-Type: application/json' -d "${smoke}" \
    "http://127.0.0.1:${port}/v1/chat/completions" > "${eval_dir}/smoke-${port}.json" || exit 123
done

python3 - "${proxy_pid}" "${case_dir}" <<'PY'
import hashlib, json, sys, time
from pathlib import Path

proxy_pid, case_dir = sys.argv[1:]
case = Path(case_dir)
services = json.loads((case / 'services/services-runtime.json').read_text())
host_preflight = case / 'services/host-preflight-run003.json'
receipt = json.loads(host_preflight.read_text())
if time.time() - receipt['checked_epoch'] > receipt['freshness_requirement_seconds']:
    raise RuntimeError('host-side service identity evidence expired')
for replica in services['replicas']:
    if not any(x['port'] == replica['port'] and x['pid'] == replica['pid'] and
               x['start_ticks'] == replica['start_ticks'] for x in receipt['replicas']):
        raise RuntimeError(f"service {replica['port']} host identity mismatch")
stat = Path(f'/proc/{proxy_pid}/stat').read_text()
proxy_start = int(stat[stat.rfind(')') + 2:].split()[19])
runtime = {
    'schema_version': 1,
    'logical_endpoint': 'http://127.0.0.1:8041/v1/chat/completions',
    'proxy': {'pid': int(proxy_pid), 'start_ticks': proxy_start,
              'sha256': hashlib.sha256((case/'commands/dual-service-proxy.py').read_bytes()).hexdigest()},
    'host_preflight_sha256': hashlib.sha256(host_preflight.read_bytes()).hexdigest(),
    'replicas': services['replicas'],
    'sampling': {'temperature': 1.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
                 'presence_penalty': 0.0, 'repetition_penalty': 1.0, 'api_seed': 1234},
}
runtime_path = case / 'evidence/runtime-evidence.json'
runtime_path.write_text(json.dumps(runtime, indent=2, sort_keys=True) + '\n')
prototype = json.loads((case / 'services/service-manifest.prototype.json').read_text())
prototype['flaggems_vllm_installed'] = True
prototype['base_url'] = runtime['logical_endpoint']
prototype['service_instance_id'] = 'dual-' + '-'.join(
    f"{r['port']}-{r['pid']}-{r['start_ticks']}" for r in services['replicas']) + f"-proxy-{proxy_pid}-{proxy_start}"
prototype['runtime_evidence_sha256'] = hashlib.sha256(runtime_path.read_bytes()).hexdigest()
(case / 'services/service-manifest.json').write_text(json.dumps(prototype, indent=2, sort_keys=True) + '\n')
PY

python3 "${repo}/evaluation/accuracy/formal_accuracy.py" \
  --config "${prepared_dir}/llm-config.json" \
  --contract "${prepared_dir}/contract.json" \
  --service-manifest "${case_dir}/services/service-manifest.json" \
  --evaluation-inspect "${case_dir}/evidence/evaluator.inspect.json" \
  --preflight-only > "${eval_dir}/preflight.log" 2>&1 || exit 124

date -Iseconds > "${eval_dir}/FORMAL_STARTED"
python3 "${repo}/evaluation/accuracy/formal_accuracy.py" \
  --config "${prepared_dir}/llm-config.json" \
  --contract "${prepared_dir}/contract.json" \
  --service-manifest "${case_dir}/services/service-manifest.json" \
  --evaluation-inspect "${case_dir}/evidence/evaluator.inspect.json" \
  > "${eval_dir}/formal-run.log" 2>&1
rc=$?

result=$(find "${case_dir}/results" -type f -name 'results_*.json' -print | sort | tail -n 1)
if [[ -n "${result}" ]]; then
  python3 "${repo}/evaluation/accuracy/verify_accuracy.py" "${result}" \
    --task gpqa_diamond_generative_cot --metric 'exact_match,strict-match' --threshold 0.88 \
    > "${eval_dir}/score-verdict.log" 2>&1 || true
  printf '%s\n' "${result}" > "${eval_dir}/result.path"
fi
exit "${rc}"
