#!/usr/bin/env bash
set -euo pipefail

case_root=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
container=qwen3.8-flash-opt-candidate-20260919
instance=${case_root}/smoke/fw008-service57-graph-01/service-instance.json
patch=${case_root}/commands/patches/fw008-common-slot-host-sync-optout.patch
plugin_root=/workspace/vllm-plugin-FL-qwen38-adaptation
plugin_file=${plugin_root}/vllm_fl/worker/common_slot_mapping.py
candidate_sha=0b7f07ab3068197a2cb6219cdd2c0fd151dc0b39c408c71468315104a1fad85b
baseline_sha=811289ae9cbcf2869e506eeae7028818a07b65daf54b10d425c1c2baf60a64d6
receipt=${case_root}/transitions/stop-revert-fw008-service57-01

test -f "${instance}"
test ! -e "${receipt}"
test "$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')" = "${candidate_sha}"
mkdir "${receipt}"

docker exec -i "${container}" python3 - "${instance}" <<'PY' > "${receipt}/before.json"
import json, os, signal, sys, time
instance=json.load(open(sys.argv[1])); pid=int(instance["pid"]); expected=int(instance["start_ticks"])
def snapshot(value):
    raw=open(f"/proc/{value}/stat",encoding="utf-8").read(); fields=raw[raw.rfind(")")+2:].split()
    argv=[x.decode(errors="replace") for x in open(f"/proc/{value}/cmdline","rb").read().split(b"\0") if x]
    return {"pid":value,"ppid":int(fields[1]),"start_ticks":int(fields[19]),"argv":argv}
root=snapshot(pid)
if root["start_ticks"]!=expected or root["argv"]!=instance["argv"]: raise SystemExit("service57 identity changed")
processes={}
for entry in os.listdir("/proc"):
    if not entry.isdigit(): continue
    try: item=snapshot(int(entry))
    except (FileNotFoundError,PermissionError,ProcessLookupError,ValueError): continue
    processes[item["pid"]]=item
tree={pid}; changed=True
while changed:
    changed=False
    for child,item in processes.items():
        if child not in tree and item["ppid"] in tree: tree.add(child); changed=True
evidence={"service":root,"tree":[processes[x] for x in sorted(tree)]}
print(json.dumps(evidence,indent=2,sort_keys=True)); os.kill(pid,signal.SIGTERM)
deadline=time.monotonic()+240
while True:
    live=[]
    for item in evidence["tree"]:
        try: current=snapshot(item["pid"])
        except FileNotFoundError: continue
        if current["start_ticks"]==item["start_ticks"]: live.append(item["pid"])
    if not live: break
    if time.monotonic()>=deadline: raise SystemExit(f"service tree did not exit: {live}")
    time.sleep(1)
PY

if ss -ltnH 'sport = :8031' | grep -q .; then echo "port 8031 remains in use" >&2; exit 3; fi
docker exec "${container}" bash -lc "cd '${plugin_root}' && git apply -R --check '${patch}' && git apply -R '${patch}'"
test "$(docker exec "${container}" sha256sum "${plugin_file}" | awk '{print $1}')" = "${baseline_sha}"
docker exec "${container}" sha256sum "${plugin_file}" > "${receipt}/plugin-file.after.sha256"
ppu-smi > "${receipt}/host-ppu-smi.after.txt"
sha256sum "${instance}" "${patch}" "${receipt}/before.json" "${receipt}/plugin-file.after.sha256" "${receipt}/host-ppu-smi.after.txt"
