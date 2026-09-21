#!/usr/bin/env bash
set -euo pipefail

run_id=${1:?usage: lifecycle-prof006a-host-gap.sh UNIQUE_RUN_ID [preflight|run|resume] [CONTROL_DIAGNOSTIC]}
phase=${2:-run}
control_diag_override=${3:-}
case "${run_id}" in *[!A-Za-z0-9._-]*|'') echo "invalid run id" >&2; exit 2 ;; esac
case "${phase}" in preflight|run|resume) ;; *) echo "invalid phase" >&2; exit 2 ;; esac

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
source_root=/workspace/vllm-plugin-FL-qwen38-adaptation
plugin_root=/opt/qwen38-prof006a-${run_id}
commands=${case_root}/commands/prof006a
runner=${commands}/run-prof006a-host-gap-diagnostic-v2.sh
analyzer=${commands}/analyze-prof006a-host-gap-v2.py
profile_root=${case_root}/profiling/prof006a/${run_id}
transition_root=${case_root}/transitions/${run_id}
active_identity=${transition_root}/active-service.json
installed=0
service_stopped=1

source_files=(
  vllm_fl/__init__.py
  vllm_fl/worker/worker.py
  vllm_fl/worker/model_runner.py
)
source_shas=(
  2a7e903978b57aa8ff82a1e4c0785e2b1c8a51a2c7de8664ed8055b063516ff4
  a8de1780d1b41bf4889c26f3d593e6ec54e91a5f61996ce64b4d79f2a97efa24
  2df8aa58559ae7f9a3576ebcd234b42c864f5054fdff8897110dd60b26cb8bc0
)

export PROF006A_PLUGIN_ROOT=${plugin_root}
export PROF006A_PORT=8031

container_cmd() {
  docker exec -i -e PYTHONDONTWRITEBYTECODE=1 "${container}" "$@"
}

assert_source_shas() {
  local index actual
  for index in "${!source_files[@]}"; do
    actual=$(container_cmd sha256sum "${source_root}/${source_files[$index]}" | awk '{print $1}')
    test "${actual}" = "${source_shas[$index]}"
  done
}

assert_cards_free() {
  python3 - <<'PY'
import json, os
busy=[]
for entry in os.listdir('/proc'):
    if not entry.isdigit():
        continue
    try:
        argv=[x.decode(errors='replace') for x in open(f'/proc/{entry}/cmdline','rb').read().split(b'\0') if x]
        env=dict(x.split(b'=',1) for x in open(f'/proc/{entry}/environ','rb').read().split(b'\0') if b'=' in x)
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if not any(word in ' '.join(argv).lower() for word in ('vllm','enginecore','worker')):
        continue
    visible=env.get(b'CUDA_VISIBLE_DEVICES',b'').decode(errors='replace')
    try:
        cards={int(x) for x in visible.split(',') if x}
    except ValueError:
        continue
    if cards & set(range(8)):
        busy.append({'pid':int(entry),'visible':visible,'argv':argv})
if busy:
    print(json.dumps(busy,indent=2))
    raise SystemExit('PPU0-7 assigned to a vLLM process')
PY
}

snapshot_service() {
  local port=$1 output=$2
  container_cmd python3 - "${port}" "${output}" <<'PY'
import json, os, sys
port=sys.argv[1]; output=sys.argv[2]; found=[]
for entry in os.listdir('/proc'):
    if not entry.isdigit(): continue
    try:
        argv=[x.decode(errors='replace') for x in open(f'/proc/{entry}/cmdline','rb').read().split(b'\0') if x]
        raw=open(f'/proc/{entry}/stat',encoding='utf-8').read()
        env=dict(x.split(b'=',1) for x in open(f'/proc/{entry}/environ','rb').read().split(b'\0') if b'=' in x)
    except (FileNotFoundError, PermissionError, ProcessLookupError): continue
    if ('serve' in argv and '--port' in argv and argv[argv.index('--port')+1]==port
            and '/mnt/cpfs/models/Qwen3.8-Flash-Next' in argv):
        found.append({'pid':int(entry),'start_ticks':int(raw[raw.rfind(')')+2:].split()[19]),
                      'argv':argv,'pythonpath':env.get(b'PYTHONPATH',b'').decode(),
                      'arm':env.get(b'VLLM_FL_PROF006A_ARM',b'').decode(),
                      'probe_dir':env.get(b'VLLM_FL_PROF006A_DIR',b'').decode()})
if len(found)!=1: raise SystemExit(f'expected one service on {port}, got {len(found)}')
tmp=output+f'.tmp.{os.getpid()}'
open(tmp,'x',encoding='utf-8').write(json.dumps(found[0],indent=2,sort_keys=True)+'\n')
os.replace(tmp,output)
PY
}

stop_active_service() {
  if [[ "${service_stopped}" -eq 1 ]]; then return 0; fi
  container_cmd python3 - "${active_identity}" <<'PY'
import json, os, signal, sys
record=json.load(open(sys.argv[1],encoding='utf-8')); pid=record['pid']
try:
    raw=open(f'/proc/{pid}/stat',encoding='utf-8').read()
    argv=[x.decode(errors='replace') for x in open(f'/proc/{pid}/cmdline','rb').read().split(b'\0') if x]
except FileNotFoundError: raise SystemExit(0)
if int(raw[raw.rfind(')')+2:].split()[19])!=record['start_ticks'] or argv!=record['argv']:
    raise SystemExit('service PID identity changed; refusing signal')
os.kill(pid,signal.SIGTERM)
PY
  for _ in $(seq 1 150); do
    if ! ss -ltnH 'sport = :8031' | grep -q .; then break; fi
    sleep 2
  done
  if ss -ltnH 'sport = :8031' | grep -q .; then return 1; fi
  for _ in $(seq 1 60); do
    if assert_cards_free >/dev/null 2>&1; then service_stopped=1; return 0; fi
    sleep 2
  done
  return 1
}

validate_registrations() {
  local arm=$1 probe_dir=$2
  container_cmd python3 - "${arm}" "${probe_dir}" "${plugin_root}/vllm_fl/prof006a.py" <<'PY'
import json, sys
from pathlib import Path
arm, root, expected_source=sys.argv[1],Path(sys.argv[2]),sys.argv[3]
rows=[json.loads(p.read_text()) for p in sorted(root.glob('*.registration.json'))]
roles={row.get('role') for row in rows}
expected={'engine',*(f'worker-rank{i}' for i in range(8))}
if len(rows)!=9 or roles!=expected: raise SystemExit(f'registration mismatch: {sorted(roles)}')
if any(row.get('arm')!=arm or row.get('source_path')!=expected_source for row in rows):
    raise SystemExit('arm or private import path mismatch')
print(json.dumps({'roles':sorted(roles),'source_path':expected_source},sort_keys=True))
PY
}

launch_arm() {
  local arm=$1 arm_root=${profile_root}/$1 probe_dir=${profile_root}/$1/probe
  test ! -e "${arm_root}"
  mkdir -p "${probe_dir}"
  rm -f "${active_identity}"
  local -a probe_env=()
  if [[ "${arm}" != control ]]; then
    probe_env=(
      -e "VLLM_FL_PROF006A_ARM=${arm}"
      -e "VLLM_FL_PROF006A_DIR=${probe_dir}"
      -e VLLM_FL_PROF006A_CAPACITY=1024
    )
  fi
  docker exec -d \
    -e CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
    -e VLLM_WORKER_MULTIPROC_METHOD=spawn -e VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
    -e GLOO_SOCKET_IFNAME=eth0 -e NCCL_IB_HCA=fic2_soe_bond -e NCCL_IB_GID_INDEX=1 \
    -e NCCL_IB_ADDR_FAMILY=6 -e NCCL_SOCKET_IFNAME=bond -e NCCL_SOCKET_FAMILY=AF_INET6 \
    -e VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_,mm,mm_out \
    -e VLLM_TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01 \
    -e VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448 \
    -e PYTHONDONTWRITEBYTECODE=1 -e "PYTHONPATH=${plugin_root}" \
    "${probe_env[@]}" \
    -w "${case_root}" "${container}" bash -lc "source /usr/local/PPU_SDK/envsetup.sh; export PATH=/usr/lib64/openmpi/bin:\${PATH}; export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}; exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next --served-model-name Qwen3.8-Flash-Next --host 0.0.0.0 --port 8031 --tensor-parallel-size 8 --pipeline-parallel-size 1 --dtype bfloat16 --language-model-only --max-model-len 80000 --max-num-seqs 64 --max-num-batched-tokens 4096 --gpu-memory-utilization 0.90 --disable-custom-all-reduce --reasoning-parser qwen3 --no-enable-prefix-caching --compilation-config '{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\"}' >'${arm_root}/service-8031.live.log' 2>&1"
  service_stopped=0
  for _ in $(seq 1 120); do
    if snapshot_service 8031 "${active_identity}" >/dev/null 2>&1; then break; fi
    sleep 2
  done
  test -s "${active_identity}"
  container_cmd python3 - "${active_identity}" "${plugin_root}" "${arm}" "${probe_dir}" <<'PY'
import json,sys
x=json.load(open(sys.argv[1])); expected_arm='' if sys.argv[3]=='control' else sys.argv[3]
if x['pythonpath'].split(':')[0]!=sys.argv[2] or x['arm']!=expected_arm:
    raise SystemExit('service environment identity mismatch')
if expected_arm and x['probe_dir']!=sys.argv[4]: raise SystemExit('probe directory mismatch')
PY
  for _ in $(seq 1 180); do
    if curl -fsS http://127.0.0.1:8031/health >"${arm_root}/health.ready.json"; then break; fi
    sleep 5
  done
  test -f "${arm_root}/health.ready.json"
  if [[ "${arm}" != control ]]; then validate_registrations "${arm}" "${probe_dir}" >"${arm_root}/registrations.validated.json"; fi
  ppu-smi >"${arm_root}/ppu-smi.ready.txt" 2>&1
}

run_control() {
  local arm_root=${profile_root}/control client_root=${profile_root}/control/client benchmark=${case_root}/commands/performance/vllm_profile.py
  mkdir "${client_root}"
  container_cmd python3 "${benchmark}" --model Qwen3.8-Flash-Next --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next --host 127.0.0.1 --port 8031 --endpoint /v1/completions --case 4096,128,64,64 --runs 1 --warmup-rounds 0 --no-profile --seed 42 --timeout 1800 --output-dir "${client_root}/warmup"
  container_cmd python3 "${benchmark}" --model Qwen3.8-Flash-Next --tokenizer /mnt/cpfs/models/Qwen3.8-Flash-Next --host 127.0.0.1 --port 8031 --endpoint /v1/completions --case 4096,128,64,64 --runs 3 --warmup-rounds 0 --no-profile --seed 42 --timeout 1800 --output-dir "${client_root}/measured"
  find "${client_root}/measured" -type f -name diagnostic.json -print | sort >"${arm_root}/measured-diagnostic-path.txt"
  test "$(wc -l <"${arm_root}/measured-diagnostic-path.txt")" -eq 1
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  set +e
  stop_active_service; local stop_rc=$?
  if [[ "${installed}" -eq 1 ]]; then
    bash "${runner}" revert; local revert_rc=$?
  else
    local revert_rc=0
  fi
  assert_source_shas; local source_rc=$?
  curl -fsS http://127.0.0.1:8030/health >"${transition_root}/retained-health.final.json"; local health_rc=$?
  snapshot_service 8030 "${transition_root}/retained-service.final.json"; local identity_rc=$?
  if [[ "${identity_rc}" -eq 0 ]]; then cmp -s "${transition_root}/retained-service.before.json" "${transition_root}/retained-service.final.json"; identity_rc=$?; fi
  assert_cards_free; local cards_rc=$?
  {
    echo "initial_status=${status}"
    echo "service_stop_status=${stop_rc}"
    echo "private_source_revert_status=${revert_rc}"
    echo "original_source_status=${source_rc}"
    echo "retained_health_status=${health_rc}"
    echo "retained_identity_status=${identity_rc}"
    echo "ppu0_7_release_status=${cards_rc}"
    echo "private_copy_retained=${plugin_root}"
  } >"${transition_root}/cleanup-receipt.txt"
  if ((stop_rc||revert_rc||source_rc||health_rc||identity_rc||cards_rc)); then status=1; fi
  exit "${status}"
}

test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
for asset in "${runner}" "${analyzer}" "${commands}/prof006a_probe.py" "${commands}/prof006a-plugin.patch"; do test -s "${asset}"; done
if [[ "${phase}" = resume ]]; then
  case "${control_diag_override}" in "${case_root}"/profiling/prof006a/*/control/client/measured/*/diagnostic.json) ;; *) echo "unsafe control diagnostic" >&2; exit 2 ;; esac
  test -s "${control_diag_override}"
fi
test ! -e "${profile_root}"
test ! -e "${transition_root}"
mkdir -p "${profile_root}" "${transition_root}"
trap cleanup EXIT INT TERM

curl -fsS http://127.0.0.1:8030/health >"${transition_root}/retained-health.before.json"
snapshot_service 8030 "${transition_root}/retained-service.before.json"
if ss -ltnH 'sport = :8031' | grep -q .; then exit 3; fi
assert_cards_free
assert_source_shas
docker inspect "${container}" >"${transition_root}/container-inspect.json"
python3 - "${transition_root}/container-inspect.json" "${plugin_root}" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))[0]; candidate=sys.argv[2].rstrip('/')
for mount in x.get('Mounts',[]):
    destination=mount['Destination'].rstrip('/') or '/'
    if candidate==destination or candidate.startswith(destination+'/'):
        raise SystemExit(f'private copy would be under mount {destination}')
PY
container_cmd test ! -e "${plugin_root}"
container_cmd cp -a "${source_root}" "${plugin_root}"
container_cmd touch "${plugin_root}/.prof006a-experiment-${run_id}"
assert_source_shas
for index in "${!source_files[@]}"; do
  test "$(container_cmd sha256sum "${plugin_root}/${source_files[$index]}" | awk '{print $1}')" = "${source_shas[$index]}"
done
sha256sum "${runner}" "${analyzer}" "${commands}/prof006a_probe.py" "${commands}/prof006a-plugin.patch" >"${transition_root}/assets.sha256"
bash "${runner}" preflight >"${transition_root}/preflight.stdout"
if [[ "${phase}" = preflight ]]; then
  echo "preflight_passed" >"${transition_root}/preflight.receipt"
  exit 0
fi
bash "${runner}" install >"${transition_root}/install.stdout"
installed=1
container_cmd sha256sum "${plugin_root}/vllm_fl/prof006a.py" $(printf "${plugin_root}/%s " "${source_files[@]}") >"${transition_root}/private-source.patched.sha256"

if [[ "${phase}" = resume ]]; then arms=(event event_host); else arms=(control event event_host); fi
for arm in "${arms[@]}"; do
  launch_arm "${arm}"
  if [[ "${arm}" = control ]]; then
    run_control >"${profile_root}/${arm}/client.stdout" 2>"${profile_root}/${arm}/client.stderr"
  else
    PROF006A_RUN_ROOT="${profile_root}/${arm}" bash "${runner}" run "${arm}" "${arm}" >"${profile_root}/${arm}/client.stdout" 2>"${profile_root}/${arm}/client.stderr"
  fi
  sleep 2
  stop_active_service
  curl -fsS http://127.0.0.1:8030/health >"${profile_root}/${arm}/retained-health.after.json"
  assert_cards_free
done

if [[ "${phase}" = resume ]]; then control_diag=${control_diag_override}; else control_diag=$(cat "${profile_root}/control/measured-diagnostic-path.txt"); fi
event_diag=$(cat "${profile_root}/event/measured-diagnostic-path.txt")
host_diag=$(cat "${profile_root}/event_host/measured-diagnostic-path.txt")
set +e
python3 "${analyzer}" --control-diagnostic "${control_diag}" --event-probe "${profile_root}/event/probe" --event-diagnostic "${event_diag}" --event-host-probe "${profile_root}/event_host/probe" --event-host-diagnostic "${host_diag}" --output "${profile_root}/analysis.json" >"${profile_root}/analysis.stdout" 2>"${profile_root}/analysis.stderr"
analysis_rc=$?
set -e
case "${analysis_rc}" in 0|3) ;; *) exit "${analysis_rc}" ;; esac
echo "${analysis_rc}" >"${profile_root}/analysis.exit-code"
bash "${runner}" revert >"${transition_root}/revert.stdout"
installed=0
assert_source_shas
curl -fsS http://127.0.0.1:8030/health >"${transition_root}/retained-health.after.json"
assert_cards_free
sha256sum "${profile_root}/analysis.json" "${transition_root}/cleanup-receipt.txt" 2>/dev/null || true
