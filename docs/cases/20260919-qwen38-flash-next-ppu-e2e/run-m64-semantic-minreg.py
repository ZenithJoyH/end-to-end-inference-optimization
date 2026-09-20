#!/usr/bin/env python3
import concurrent.futures
import hashlib
import json
import os
import re
import threading
import time
import urllib.request
from pathlib import Path

CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
RUN_DIR = CASE_ROOT / "accuracy/m64-semantic-minreg-02"
CONTRACT = CASE_ROOT / "commands/accuracy/m64-semantic-minreg-contract.json"
SERVICES = {
    "revert": {
        "url": "http://127.0.0.1:8020/v1/completions",
        "metrics": "http://127.0.0.1:8020/metrics",
        "manifest": CASE_ROOT / "manifests/baseline-maxseq64-bt4096-m64-minreg-revert-service-11.json",
    },
    "candidate": {
        "url": "http://127.0.0.1:8030/v1/completions",
        "metrics": "http://127.0.0.1:8030/metrics",
        "manifest": CASE_ROOT / "manifests/candidate-maxseq64-bt4096-moe-bm16-service-comparison-10.json",
    },
}
FINAL_RE = re.compile(r"FINAL\s*[:=]\s*(-?\d+)", re.IGNORECASE)


def get_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def post_json(url, payload):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, sort_keys=True).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=1800) as response:
        return json.load(response)


def sample_running(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        text = response.read().decode(errors="replace")
    values = []
    for line in text.splitlines():
        if line.startswith("#") or "num_requests_running" not in line:
            continue
        match = re.search(r"\s([0-9]+(?:\.[0-9]+)?)$", line)
        if match:
            values.append(float(match.group(1)))
    return max(values, default=0.0)


def case(index):
    left = index * 17 + 113
    right = index * 29 + 71
    expected = left + right
    return {
        "index": index,
        "expected": expected,
        "payload": {
            "model": "Qwen3.8-Flash-Next",
            "prompt": (
                f"Compute {left} + {right}. Your response must end with exactly "
                f"FINAL={expected}. Do not use FINAL for any other number."
            ),
            "max_tokens": 128,
            "temperature": 0,
            "top_p": 1,
            "seed": 1234 + index,
            "ignore_eos": True,
        },
    }


def normalize(index, expected, payload):
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise RuntimeError(f"case {index}: invalid choices")
    choice = choices[0]
    text = choice.get("text")
    if not isinstance(text, str) or not text:
        raise RuntimeError(f"case {index}: empty completion")
    matches = FINAL_RE.findall(text)
    parsed = int(matches[-1]) if matches else None
    return {
        "index": index,
        "expected": expected,
        "parsed": parsed,
        "correct": parsed == expected,
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": payload.get("usage", {}).get("completion_tokens"),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "text": text,
    }


def run_service_wave(service_name, wave_kind, wave_index, barrier, count):
    service = SERVICES[service_name]
    cases = [case(index) for index in range(count)]
    barrier.wait()
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
        futures = {
            pool.submit(post_json, service["url"], item["payload"]): item
            for item in cases
        }
        rows = [None] * count
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            rows[item["index"]] = normalize(
                item["index"], item["expected"], future.result()
            )
    elapsed = time.monotonic() - started
    score = sum(row["correct"] for row in rows) / len(rows)
    print(
        f"service={service_name} kind={wave_kind} wave={wave_index} "
        f"correct={sum(row['correct'] for row in rows)}/{len(rows)} "
        f"score={score:.6f} elapsed={elapsed:.3f}",
        flush=True,
    )
    return rows, elapsed, score


def run_wave(kind, index, count, max_running):
    barrier = threading.Barrier(len(SERVICES) + 1)
    stop_monitor = threading.Event()

    def monitor():
        while not stop_monitor.is_set():
            for name, service in SERVICES.items():
                try:
                    max_running[name] = max(max_running[name], sample_running(service["metrics"]))
                except Exception:
                    pass
            stop_monitor.wait(0.05)

    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SERVICES)) as pool:
        futures = {
            name: pool.submit(run_service_wave, name, kind, index, barrier, count)
            for name in SERVICES
        }
        barrier.wait()
        result = {name: future.result() for name, future in futures.items()}
    stop_monitor.set()
    monitor_thread.join(timeout=5)
    return result


def main():
    if RUN_DIR.exists():
        raise SystemExit(f"refusing to reuse {RUN_DIR}")
    RUN_DIR.mkdir(parents=True)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    manifests = {}
    for name, service in SERVICES.items():
        manifests[name] = json.loads(service["manifest"].read_text(encoding="utf-8"))
        get_json(service["url"].rsplit("/v1/completions", 1)[0] + "/v1/models")

    process = {
        "pid": os.getpid(),
        "started_at_unix": time.time(),
        "experiment_id": contract["experiment_id"],
        "mode": contract["mode"],
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "service_instance_ids": {
            name: manifest["service_instance_id"] for name, manifest in manifests.items()
        },
    }
    (RUN_DIR / "process.json").write_text(
        json.dumps(process, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    workload = contract["workload"]
    count = workload["requests_per_service_per_wave"]
    max_running = {name: 0.0 for name in SERVICES}
    warmup = []
    measured = []
    for wave in range(1, workload["warmup_waves"] + 1):
        warmup.append(run_wave("warmup", wave, count, max_running))
    for wave in range(1, workload["measured_waves"] + 1):
        measured.append(run_wave("measured", wave, count, max_running))

    scores = {
        name: [wave[name][2] for wave in measured]
        for name in SERVICES
    }
    threshold = contract["threshold"]
    per_wave_pass = all(
        score >= threshold for values in scores.values() for score in values
    )
    candidate_not_worse = sum(scores["candidate"]) >= sum(scores["revert"])
    concurrency_pass = all(value >= count for value in max_running.values())
    passed = per_wave_pass and candidate_not_worse and concurrency_pass
    result = {
        "schema_version": 1,
        "experiment_id": contract["experiment_id"],
        "mode": contract["mode"],
        "contract_sha256": process["contract_sha256"],
        "service_instance_ids": process["service_instance_ids"],
        "threshold": threshold,
        "scores": scores,
        "candidate_not_worse": candidate_not_worse,
        "max_observed_running_requests": max_running,
        "per_wave_threshold_pass": per_wave_pass,
        "concurrency_pass": concurrency_pass,
        "warmup_elapsed_seconds": {
            name: [wave[name][1] for wave in warmup] for name in SERVICES
        },
        "measured_elapsed_seconds": {
            name: [wave[name][1] for wave in measured] for name in SERVICES
        },
        "measured_outputs": {
            name: [wave[name][0] for wave in measured] for name in SERVICES
        },
        "passed": passed,
        "evidence_boundary": contract["evidence_boundary"],
    }
    (RUN_DIR / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in result.items() if key != "measured_outputs"}, sort_keys=True), flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
