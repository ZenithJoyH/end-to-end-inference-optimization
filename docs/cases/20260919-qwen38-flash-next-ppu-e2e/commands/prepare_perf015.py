#!/usr/bin/env python3
"""Freeze the live unbounded port-8000 identity and P16K phase plans for perf-015."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
EXPERIMENT = CASE_ROOT / "performance/perf-015-p16k-post-rb001-unbounded-entry-20260922"
CONTAINER = "qwen3.8-flash-opt-candidate-20260919"
PORT = 8000
SOURCE_MANIFEST = CASE_ROOT / "accuracy/acc-009-full-gpqa-dual-qsa-unbounded-20260922/services/service-manifest.json"
PERF_COMMANDS = CASE_ROOT / "commands/performance"

PROBE = r'''
import json, os, sys
model, port = sys.argv[1:]
found = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    try:
        args = [x.decode(errors="replace") for x in open(f"/proc/{entry}/cmdline", "rb").read().split(b"\0") if x]
        stat = open(f"/proc/{entry}/stat", encoding="utf-8").read().split()
        env = {x.decode(errors="replace").split("=", 1)[0]: x.decode(errors="replace").split("=", 1)[1]
               for x in open(f"/proc/{entry}/environ", "rb").read().split(b"\0") if b"=" in x}
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if not any(os.path.basename(x) == "vllm" for x in args):
        continue
    if "serve" not in args or model not in args or "--port" not in args:
        continue
    if args[args.index("--port") + 1] == port:
        found.append({"pid": int(entry), "start_ticks": stat[21], "args": args, "environment": env})
if len(found) != 1:
    raise SystemExit(f"expected one live service, got {len(found)}")
print(json.dumps(found[0], sort_keys=True))
'''


def encode_json(value: object) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = EXPERIMENT / "manifests/service-8000.json"
    evidence_path = EXPERIMENT / "evidence/runtime-8000.json"
    if manifest_path.exists() or evidence_path.exists():
        raise SystemExit("refusing to overwrite frozen perf-015 identity")

    source = json.loads(SOURCE_MANIFEST.read_text())
    container = json.loads(subprocess.check_output(["docker", "inspect", CONTAINER], text=True))[0]
    process = json.loads(subprocess.check_output([
        "docker", "exec", "-i", CONTAINER, "python3", "-c", PROBE,
        source["tokenizer_path"], str(PORT),
    ], text=True))
    live_args = process["args"][process["args"].index("serve"):]
    replica = next(item for item in source["launch_config"]["replicas"] if item["port"] == PORT)
    if live_args != replica["argv"][replica["argv"].index("serve"):]:
        raise SystemExit("live argv differs from acc-009 frozen identity")
    if process["environment"].get("VLLM_FL_QSA_STATIC_SCORE_COLUMNS") is not None:
        raise SystemExit("QSA static score bound is unexpectedly present")
    for key, expected in replica["selected_environment"].items():
        if process["environment"].get(key) != expected:
            raise SystemExit(f"environment drift for {key}")
    subprocess.check_call(["docker", "exec", CONTAINER, "curl", "-fsS", f"http://127.0.0.1:{PORT}/health"], stdout=subprocess.DEVNULL)
    subprocess.check_call(["docker", "exec", CONTAINER, "curl", "-fsS", "http://127.0.0.1:8010/health"], stdout=subprocess.DEVNULL)

    instance = f"{container['Id'][:12]}-{PORT}-{process['pid']}-{process['start_ticks']}"
    evidence = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "container_id": container["Id"],
        "container_name": CONTAINER,
        "health": {"8000": "passed", "8010_idle_control": "passed"},
        "process": process,
        "qsa_static_score_columns": None,
        "service_instance_id": instance,
    }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_bytes(encode_json(evidence))

    manifest = dict(source)
    manifest["base_url"] = f"http://127.0.0.1:{PORT}/v1/completions"
    manifest["service_instance_id"] = instance
    manifest["runtime_evidence_sha256"] = sha256(evidence_path)
    manifest["launch_config"] = {
        "async_scheduling": True,
        "enable_prefix_caching": False,
        "launch_args": live_args,
        "max_num_batched_tokens": 4096,
        "max_num_seqs": 64,
        "qsa_static_score_columns": None,
        "selected_environment": replica["selected_environment"],
    }
    manifest["performance_context"] = dict(source["performance_context"])
    manifest["performance_context"].update({
        "cache_preparation": "Post-acc009 live graph service; prefix cache disabled; QSA static score bound absent.",
        "device_ids": [str(i) for i in range(8)],
        "serving_replicas": 1,
        "idle_peer_service": "8010 on PPU8-15; no benchmark traffic permitted",
    })
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(encode_json(manifest))

    plan_dir = EXPERIMENT / "commands"
    plan_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for phase in ("prefill", "decode", "mixed"):
        plan = json.loads((PERF_COMMANDS / f"perf-p16k-{phase}-entry-plan.json").read_text())
        plan["target"]["port"] = PORT
        out = plan_dir / f"perf-p16k-{phase}-entry-plan.json"
        out.write_bytes(encode_json(plan))
        contract = PERF_COMMANDS / f"perf-p16k-{phase}-comparison.json"
        copied = plan_dir / contract.name
        copied.write_bytes(contract.read_bytes())
        files.extend([out, copied])

    receipt = {
        "schema_version": 1,
        "experiment_id": "perf-015-p16k-post-rb001-unbounded-entry",
        "mode": "baseline",
        "scope": "performance_only",
        "service_manifest": str(manifest_path),
        "service_manifest_sha256": sha256(manifest_path),
        "runtime_evidence": str(evidence_path),
        "runtime_evidence_sha256": sha256(evidence_path),
        "files": {str(path): sha256(path) for path in files},
    }
    (EXPERIMENT / "prepare-receipt.json").write_bytes(encode_json(receipt))
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
