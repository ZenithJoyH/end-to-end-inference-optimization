#!/usr/bin/env bash
set -euo pipefail

phase=${1:?usage: lifecycle-op021-qsa-producer-fixture.sh prefill|mixed RUN_ID EXPECTED_QSA_SHA QSA_PATH}
run_id=${2:?missing unique run id}
expected_qsa_sha=${3:?missing exact unpatched qsa.py SHA256}
qsa_path=${4:?missing qsa.py path inside the container}
case "${phase}" in prefill|mixed) ;; *) exit 2 ;; esac
case "${run_id}" in *[!A-Za-z0-9._-]*|'') exit 2 ;; esac
[[ "${expected_qsa_sha}" =~ ^[0-9a-f]{64}$ ]]
case "${qsa_path}" in /*/flag_gems/fused/qsa.py) ;; *) exit 2 ;; esac

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
container_id=9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4
image_id=sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6
commands=${case_root}/commands/op021
arm=${commands}/arm-op021-qsa-producer-fixture.py
prepare=${commands}/prepare-op021-qsa-producer-fixture.py
helper=${commands}/op021-qsa-producer-fixture-helper.py
request=${commands}/run-op021-qsa-producer-fixture-capture.sh
revert=${commands}/revert-op021-qsa-producer-fixture.sh
verify=${commands}/verify-op021-qsa-producer-fixture.py
run_dir=${case_root}/transitions/${run_id}
output_dir=${case_root}/profiling/${run_id}
patch_dir=${run_dir}/patch-artifact
patch_manifest=${patch_dir}/patch-manifest.json
identity=${run_dir}/service-process.json
fixture=${output_dir}/op021-p4k-${phase}-producer-001
service_stopped=0
source_restored=0

for path in "${arm}" "${prepare}" "${helper}" "${request}" "${revert}" "${verify}"; do test -s "${path}"; done
test "$(docker inspect --format '{{.Id}}' "${container}")" = "${container_id}"
test "$(docker inspect --format '{{.Image}}' "${container}")" = "${image_id}"
test "$(docker inspect --format '{{.State.Running}}' "${container}")" = true
test ! -e "${run_dir}"
test ! -e "${output_dir}"
mkdir -p "${case_root}/transitions" "${case_root}/profiling"
mkdir "${run_dir}"

assert_cards_free() {
  python3 - <<'PY'
import json, os, sys
busy=[]
for e in os.listdir('/proc'):
    if not e.isdigit(): continue
    try:
        argv=[x.decode(errors='replace') for x in open(f'/proc/{e}/cmdline','rb').read().split(b'\0') if x]
        env=dict(x.split(b'=',1) for x in open(f'/proc/{e}/environ','rb').read().split(b'\0') if b'=' in x)
    except (FileNotFoundError,PermissionError,ProcessLookupError): continue
    if not any(x in ' '.join(argv).lower() for x in ('vllm','enginecore','worker')): continue
    visible=env.get(b'CUDA_VISIBLE_DEVICES',b'').decode(errors='replace')
    try: cards={int(x) for x in visible.split(',') if x}
    except ValueError: continue
    if cards & set(range(8)): busy.append({'pid':int(e),'visible':visible,'argv':argv})
if busy:
    print(json.dumps(busy,indent=2),file=sys.stderr)
    raise SystemExit('PPU0-7 assigned to a vLLM process')
PY
}

discover_identity() {
  docker exec -i "${container}" python3 - "${identity}" <<'PY'
import json, os, sys
path=sys.argv[1]; found=[]
for e in os.listdir('/proc'):
    if not e.isdigit(): continue
    try:
        argv=[x.decode(errors='replace') for x in open(f'/proc/{e}/cmdline','rb').read().split(b'\0') if x]
        raw=open(f'/proc/{e}/stat',encoding='utf-8').read(); tail=raw[raw.rfind(')')+2:].split()
    except (FileNotFoundError,PermissionError,ProcessLookupError): continue
    if 'serve' in argv and '--port' in argv and argv[argv.index('--port')+1]=='8031' and '--enforce-eager' in argv:
        found.append({'pid':int(e),'start_ticks':int(tail[19]),'argv':argv})
if not found: raise SystemExit(4)
if len(found)!=1: raise SystemExit(f'ambiguous port-8031 services: {len(found)}')
tmp=path+f'.tmp.pid{os.getpid()}'
open(tmp,'x',encoding='utf-8').write(json.dumps(found[0],indent=2,sort_keys=True)+'\n')
os.replace(tmp,path)
PY
}

stop_service() {
  if [[ ! -s "${identity}" ]]; then
    set +e
    discover_identity
    rc=$?
    set -e
    if [[ "${rc}" -eq 4 ]]; then service_stopped=1; return 0; fi
    if [[ "${rc}" -ne 0 ]]; then echo "ambiguous 8031 service; refusing blind kill" >&2; return 1; fi
  fi
  docker exec -i "${container}" python3 - "${identity}" <<'PY'
import json, os, signal, sys
x=json.load(open(sys.argv[1],encoding='utf-8')); pid=x['pid']
try:
    raw=open(f'/proc/{pid}/stat',encoding='utf-8').read(); tail=raw[raw.rfind(')')+2:].split()
    argv=[z.decode(errors='replace') for z in open(f'/proc/{pid}/cmdline','rb').read().split(b'\0') if z]
except FileNotFoundError: raise SystemExit(0)
if int(tail[19])!=x['start_ticks'] or argv!=x['argv']: raise SystemExit('changed PID identity')
os.kill(pid,signal.SIGTERM)
PY
  for _ in $(seq 1 150); do
    if ! ss -ltnH 'sport = :8031' | grep -q .; then break; fi
    sleep 2
  done
  if ss -ltnH 'sport = :8031' | grep -q .; then return 1; fi
  # The API socket can close before TP workers have exited.  Do not mark the
  # service stopped or start single-card replay until PPU0-7 are process-free.
  for _ in $(seq 1 60); do
    if assert_cards_free >/dev/null 2>&1; then service_stopped=1; return 0; fi
    sleep 2
  done
  ppu-smi >"${run_dir}/host-ppu-smi.stop-timeout.txt" 2>&1
  echo "PPU0-7 workers remain 120 seconds after port 8031 closed" >&2
  return 1
}

restore_source() {
  if [[ ! -s "${patch_manifest}" ]]; then source_restored=1; return 0; fi
  docker exec -i "${container}" bash "${revert}" "${patch_manifest}" >"${run_dir}/revert.stdout" 2>"${run_dir}/revert.stderr"
  docker exec -i "${container}" python3 - "${qsa_path}" "${expected_qsa_sha}" <<'PY'
import hashlib, sys
actual=hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()
raise SystemExit(0 if actual==sys.argv[2] else 1)
PY
  source_restored=1
}

cleanup() {
  status=$?
  trap - EXIT INT TERM
  set +e
  if [[ "${service_stopped}" -ne 1 ]]; then stop_service; stop_rc=$?; else stop_rc=0; fi
  if [[ "${source_restored}" -ne 1 ]]; then restore_source; revert_rc=$?; else revert_rc=0; fi
  curl -fsS http://127.0.0.1:8030/health >"${run_dir}/retained-health.final.json"; health_rc=$?
  docker exec -i "${container}" python3 - "${qsa_path}" "${expected_qsa_sha}" <<'PY' >"${run_dir}/qsa-sha.final.txt"
import hashlib, sys
actual=hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()
print(actual)
raise SystemExit(0 if actual==sys.argv[2] else 1)
PY
  sha_rc=$?
  ppu-smi >"${run_dir}/host-ppu-smi.final.txt" 2>&1
  assert_cards_free; free_rc=$?
  {
    echo "initial_status=${status}"
    echo "service_stop_status=${stop_rc}"
    echo "source_revert_status=${revert_rc}"
    echo "retained_health_status=${health_rc}"
    echo "qsa_sha_status=${sha_rc}"
    echo "ppu0_7_release_status=${free_rc}"
  } >"${run_dir}/cleanup-receipt.txt"
  if ((stop_rc||revert_rc||health_rc||sha_rc||free_rc)); then status=1; fi
  exit "${status}"
}

# Recovery owns every subsequent exit before arm creation or source mutation.
trap cleanup EXIT INT TERM
curl -fsS http://127.0.0.1:8030/health >"${run_dir}/retained-health.before.json"
if ss -ltnH 'sport = :8031' | grep -q .; then exit 3; fi
assert_cards_free
ppu-smi >"${run_dir}/host-ppu-smi.before.txt"
python3 "${arm}" "${phase}" "${output_dir}" --expected-qsa-sha256 "${expected_qsa_sha}"
docker exec -i "${container}" python3 "${prepare}" --qsa "${qsa_path}" --helper "${helper}" --artifact-dir "${patch_dir}" --expected-sha256 "${expected_qsa_sha}" >"${run_dir}/prepare.stdout"
test -s "${patch_manifest}"

docker exec -d \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn -e VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS=1800 \
  -e GLOO_SOCKET_IFNAME=eth0 -e NCCL_IB_HCA=fic2_soe_bond -e NCCL_IB_GID_INDEX=1 \
  -e NCCL_IB_ADDR_FAMILY=6 -e NCCL_SOCKET_IFNAME=bond -e NCCL_SOCKET_FAMILY=AF_INET6 \
  -e VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_,mm,mm_out \
  -e VLLM_TUNED_CONFIG_FOLDER=${case_root}/configs/moe-bm16-decode-only-01 \
  -e VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448 \
  -e VLLM_FL_QSA_PRODUCER_CAPTURE=1 -e VLLM_FL_QSA_PRODUCER_RANK=0 \
  -e VLLM_FL_QSA_PRODUCER_ARM_FILE=${output_dir}/arm.json \
  -e VLLM_FL_QSA_PRODUCER_OUTPUT_DIR=${output_dir} \
  -e VLLM_FL_QSA_PRODUCER_CASE_ROOT=${case_root} \
  -w "${case_root}" "${container}" bash -lc "source /usr/local/PPU_SDK/envsetup.sh; export PATH=/usr/lib64/openmpi/bin:\${PATH}; export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}; exec vllm serve /mnt/cpfs/models/Qwen3.8-Flash-Next --served-model-name Qwen3.8-Flash-Next --host 0.0.0.0 --port 8031 --tensor-parallel-size 8 --pipeline-parallel-size 1 --dtype bfloat16 --language-model-only --max-model-len 80000 --max-num-seqs 64 --max-num-batched-tokens 4096 --gpu-memory-utilization 0.90 --disable-custom-all-reduce --reasoning-parser qwen3 --no-enable-prefix-caching --enforce-eager >'${run_dir}/service-8031.live.log' 2>&1"

for _ in $(seq 1 60); do if discover_identity; then break; fi; sleep 2; done
test -s "${identity}"
for _ in $(seq 1 180); do if curl -fsS http://127.0.0.1:8031/health >"${run_dir}/health.ready.json"; then break; fi; sleep 5; done
# The vLLM health endpoint intentionally returns an empty 200 response, so the
# curl exit status and file existence are the readiness evidence; nonzero size
# is not required.
test -f "${run_dir}/health.ready.json"
ppu-smi >"${run_dir}/host-ppu-smi.ready.txt"
bash "${request}" "${phase}" 8031 "${output_dir}" >"${run_dir}/capture.stdout" 2>"${run_dir}/capture.stderr"
test -s "${fixture}/manifest.json"

stop_service
restore_source
assert_cards_free
docker exec -i -e CUDA_VISIBLE_DEVICES=0 -w "${case_root}" "${container}" bash -lc "source /usr/local/PPU_SDK/envsetup.sh; export PATH=/usr/lib64/openmpi/bin:\${PATH}; export LD_LIBRARY_PATH=/usr/lib64/libibverbs:/usr/lib64/openmpi/lib:\${LD_LIBRARY_PATH:-}; python3 '${verify}' '${fixture}' --output '${run_dir}/verification.json'" >"${run_dir}/verification.stdout" 2>"${run_dir}/verification.stderr"
python3 - "${run_dir}/verification.json" <<'PY'
import json, sys
x=json.load(open(sys.argv[1],encoding='utf-8'))
assert x['integrity']=='passed' and x['producer_replay']=='passed' and x['selected_exact_match'] is True
PY
curl -fsS http://127.0.0.1:8030/health >"${run_dir}/retained-health.after-replay.json"
ppu-smi >"${run_dir}/host-ppu-smi.after-replay.txt"
assert_cards_free
sha256sum "${patch_manifest}" "${fixture}/manifest.json" "${run_dir}/verification.json" >"${run_dir}/SHA256SUMS"
