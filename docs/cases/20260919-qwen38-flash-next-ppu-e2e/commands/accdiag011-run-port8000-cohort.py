#!/usr/bin/env python3
"""One bounded, scheduled GPQA cohort replay on the existing port-8000 service."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import glob
import hashlib
import json
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.request


ROOT = Path(
    "/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/"
    "accuracy/acc-010-full-gpqa-dual-user-services-20260923"
)
DIAG = ROOT / "diagnostics/accdiag-011-port8000-sustained-cohort-20260924"
PLAN = DIAG / "cohort-plan.json"
RUN = DIAG / "run-001"
CONTAINER = "qwen3.8-flash-opt-candidate-20260919"
MODEL_FILE = "/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/models/qwen3_8_flash_next.py"
GRAPH_FILE = "/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/compilation/graph.py"
EXPECTED = {
    "plan_sha256": "521b508af7246fe563748190a7b45deeae88c2787bce9c040889eb85ccb7c9b2",
    "model_sha256": "3ae84180f7b5f4d70886c98f1d1afcf2255f8f7223a110397ec4894cf81a9a59",
    "graph_sha256": "ba78ed0a736bb21a4f2c307fc9775f15e3742b94533eff333b0c364eb8213fc2",
    "port8000_pid": 531902,
}
URL = "http://127.0.0.1:8000"
STATUS_LOCK = threading.Lock()
STATUS = {"phase": "prepared", "dispatched": [], "completed": [], "errors": [],
          "target_dispatched": False, "target_completed": False}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_status():
    with STATUS_LOCK:
        snapshot = dict(STATUS)
        snapshot["updated_at_utc"] = now()
        temporary = RUN / "progress.json.tmp"
        temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(RUN / "progress.json")


def execute(argv):
    return subprocess.check_output(argv, text=True, stderr=subprocess.PIPE).strip()


def get_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} from {url}")
        return json.load(response)


def metric_counts(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=8) as response:
        text = response.read().decode("utf-8", errors="replace")
    found = {}
    for name in ("vllm:num_requests_running", "vllm:num_requests_waiting"):
        rows = [line for line in text.splitlines() if line.startswith(name + "{")]
        if len(rows) != 1:
            raise RuntimeError(f"missing/ambiguous {name} on {port}: {len(rows)}")
        found[name] = float(rows[0].rsplit(" ", 1)[1])
    return found


def current_service_pid():
    text = execute(["docker", "exec", CONTAINER, "ps", "-eo", "pid,args"])
    found = []
    for line in text.splitlines():
        if "vllm serve" in line and "--port 8000" in line and "/mnt/cpfs/models/Qwen3.8-Flash-Next" in line:
            found.append(int(line.strip().split(None, 1)[0]))
    if len(found) != 1:
        raise RuntimeError(f"port8000 service process count={len(found)}")
    return found[0]


def preflight():
    if sha_bytes(PLAN.read_bytes()) != EXPECTED["plan_sha256"]:
        raise RuntimeError("cohort plan changed")
    ids = [item.get("id") for item in get_json(URL + "/v1/models").get("data", [])]
    if "Qwen3.8-Flash-Next" not in ids:
        raise RuntimeError(f"model identity mismatch: {ids}")
    for port in (8000, 8010):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"port {port} unhealthy")
        if any(value != 0 for value in metric_counts(port).values()):
            raise RuntimeError(f"port {port} not idle")
    if current_service_pid() != EXPECTED["port8000_pid"]:
        raise RuntimeError("port8000 process changed")
    for path, key in ((MODEL_FILE, "model_sha256"), (GRAPH_FILE, "graph_sha256")):
        line = execute(["docker", "exec", CONTAINER, "sha256sum", path])
        if line.split()[0] != EXPECTED[key]:
            raise RuntimeError(f"source changed: {path}")
    evaluator = execute(["docker", "top", "qwen38-eval-e2e-20260919"])
    if "formal_accuracy.py" in evaluator or "llmrun.py" in evaluator:
        raise RuntimeError("formal evaluator is active")
    processes = execute(["ps", "-eo", "args"])
    if any("dual-service-proxy.py" in line and "python" in line for line in processes.splitlines()):
        raise RuntimeError("formal dual-service proxy is active")
    return {"checked_at_utc": now(), "port8000_pid": EXPECTED["port8000_pid"],
            "model_sha256": EXPECTED["model_sha256"], "graph_sha256": EXPECTED["graph_sha256"],
            "served_model": "Qwen3.8-Flash-Next", "idle_ports": [8000, 8010]}


def build_manifest():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    peers = plan["peers_by_overlap"]
    active = sorted(
        [x for x in peers if x["start_offset_seconds"] <= 0 < x["end_offset_seconds"]],
        key=lambda x: (x["start_offset_seconds"], x["doc_id"]),
    )
    later = sorted([x for x in peers if x["start_offset_seconds"] > 0],
                   key=lambda x: (x["start_offset_seconds"], x["doc_id"]))[:2]
    if len(active) != 29 or [x["doc_id"] for x in later] != [170, 172]:
        raise RuntimeError("frozen overlapping cohort changed")
    selection = active + [{"doc_id": 168, "start_offset_seconds": 0.0}] + later
    if len(selection) != 32 or len({x["doc_id"] for x in selection}) != 32:
        raise RuntimeError("invalid cohort selection")
    sample_paths = glob.glob(str(ROOT / "results/**/samples_gpqa_diamond_generative_cot_*.jsonl"), recursive=True)
    if len(sample_paths) != 1:
        raise RuntimeError(f"expected one formal sample file, got {sample_paths}")
    selected_ids = {x["doc_id"] for x in selection}
    samples = {}
    with open(sample_paths[0], encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("filter") == "strict-match" and row.get("doc_id") in selected_ids:
                if row["doc_id"] in samples:
                    raise RuntimeError(f"duplicate strict sample {row['doc_id']}")
                samples[row["doc_id"]] = row
    if set(samples) != selected_ids:
        raise RuntimeError(f"missing samples {selected_ids - set(samples)}")
    earliest = min(x["start_offset_seconds"] for x in selection)
    requests = []
    for item in selection:
        doc_id = item["doc_id"]
        row = samples[doc_id]
        packed = row["arguments"]["gen_args_0"]
        generation = packed["arg_1"]
        if generation["max_gen_toks"] != 60000:
            raise RuntimeError(f"doc {doc_id} max_gen_toks changed")
        payload = {
            "model": "Qwen3.8-Flash-Next",
            "messages": json.loads(packed["arg_0"][0]),
            "temperature": generation["temperature"],
            "top_p": generation["top_p"],
            "top_k": generation["top_k"],
            "min_p": generation["min_p"],
            "presence_penalty": generation["presence_penalty"],
            "repetition_penalty": generation["repetition_penalty"],
            "max_completion_tokens": 60000,
            "stop": (generation["until"] + ["<|endoftext|>"])[:4],
            "seed": 1234,
        }
        packed_json = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        requests.append({"doc_id": doc_id, "formal_start_offset_seconds": item["start_offset_seconds"],
                         "scheduled_seconds": round(item["start_offset_seconds"] - earliest, 3),
                         "prompt_hash": row["prompt_hash"], "payload_sha256": sha_bytes(packed_json),
                         "payload": payload})
    requests.sort(key=lambda x: (x["scheduled_seconds"], x["doc_id"]))
    return {"selection_rule": "all 29 backend0 peers active at formal doc168 start, plus two earliest later arrivals (170,172)",
            "not_exact_formal_load": "Only 31 of 44 overlapping peers; HTTP schedule is a proxy, not internal scheduler batches; original 8000 process was restarted",
            "plan_sha256": EXPECTED["plan_sha256"], "sample_file": sample_paths[0],
            "sample_file_sha256": sha_bytes(Path(sample_paths[0]).read_bytes()),
            "target_doc_id": 168, "target_schedule_seconds": next(x["scheduled_seconds"] for x in requests if x["doc_id"] == 168),
            "requests": requests}


def send(item, origin):
    doc_id = item["doc_id"]
    deadline = origin + item["scheduled_seconds"]
    remaining = deadline - time.monotonic()
    if remaining > 0:
        time.sleep(remaining)
    if doc_id == 168 and current_service_pid() != EXPECTED["port8000_pid"]:
        raise RuntimeError(f"port8000 process changed before doc {doc_id} dispatch")
    request_path = RUN / f"doc{doc_id}-request.json"
    write_new(request_path, item["payload"])
    with STATUS_LOCK:
        STATUS["dispatched"].append(doc_id)
        if doc_id == 168:
            STATUS["target_dispatched"] = True
            STATUS["target_dispatched_at_utc"] = now()
    write_status()
    start = time.monotonic()
    start_utc = now()
    request = urllib.request.Request(
        URL + "/v1/chat/completions",
        data=json.dumps(item["payload"], ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10800) as response:
            body = json.load(response)
            code = response.status
        write_new(RUN / f"doc{doc_id}-response.json", body)
        choice = body["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""
        reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
        result = {"doc_id": doc_id, "status": code, "start_utc": start_utc, "end_utc": now(),
                  "elapsed_seconds": round(time.monotonic() - start, 3),
                  "finish_reason": choice.get("finish_reason"), "usage": body.get("usage"),
                  "content_sha256": sha_bytes(content.encode("utf-8")),
                  "reasoning_sha256": sha_bytes(reasoning.encode("utf-8")),
                  "content_chars": len(content), "reasoning_chars": len(reasoning)}
    except Exception as exc:
        result = {"doc_id": doc_id, "start_utc": start_utc, "end_utc": now(),
                  "elapsed_seconds": round(time.monotonic() - start, 3),
                  "error": f"{type(exc).__name__}: {exc}"}
    write_new(RUN / f"doc{doc_id}-result.json", result)
    with STATUS_LOCK:
        STATUS["completed"].append(doc_id)
        if "error" in result:
            STATUS["errors"].append(result)
        if doc_id == 168:
            STATUS["target_completed"] = True
            STATUS["target_result"] = result
    write_status()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def monitor(stop_event, origin):
    path = RUN / "metrics.ndjson"
    with path.open("x", encoding="utf-8") as handle:
        while not stop_event.is_set():
            row = {"utc": now(), "seconds_from_start": round(time.monotonic() - origin, 3)}
            try:
                row.update(metric_counts(8000))
                row["service_pid_unchanged"] = current_service_pid() == EXPECTED["port8000_pid"]
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            stop_event.wait(30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("plan", "run"))
    args = parser.parse_args()
    manifest = build_manifest()
    summary = {"selection_rule": manifest["selection_rule"],
               "target_schedule_seconds": manifest["target_schedule_seconds"],
               "selected_docs": [x["doc_id"] for x in manifest["requests"]],
               "request_count": len(manifest["requests"]),
               "sample_file_sha256": manifest["sample_file_sha256"]}
    if args.mode == "plan":
        print(json.dumps(summary, ensure_ascii=False))
        return
    preflight_result = preflight()
    RUN.mkdir(exist_ok=False)
    write_new(RUN / "manifest.json", manifest)
    write_new(RUN / "preflight.json", preflight_result)
    STATUS["phase"] = "running"
    write_status()
    print(json.dumps({"started_at_utc": now(), "run_dir": str(RUN), **summary}, ensure_ascii=False), flush=True)
    origin = time.monotonic()
    stop_event = threading.Event()
    watcher = threading.Thread(target=monitor, args=(stop_event, origin), daemon=True)
    watcher.start()
    try:
        with ThreadPoolExecutor(max_workers=len(manifest["requests"])) as pool:
            futures = [pool.submit(send, item, origin) for item in manifest["requests"]]
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        write_new(RUN / "results.json", {"finished_at_utc": now(), "results": results})
        with STATUS_LOCK:
            STATUS["phase"] = "completed"
        write_status()
    except Exception as exc:
        with STATUS_LOCK:
            STATUS["phase"] = "failed"
            STATUS["fatal_error"] = f"{type(exc).__name__}: {exc}"
        write_status()
        raise
    finally:
        stop_event.set()
        watcher.join(timeout=40)


if __name__ == "__main__":
    main()
