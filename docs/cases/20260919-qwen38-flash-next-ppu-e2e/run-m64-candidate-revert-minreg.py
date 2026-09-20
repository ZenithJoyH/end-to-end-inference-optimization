#!/usr/bin/env python3
import concurrent.futures
import json
import os
import re
import threading
import time
import urllib.request
from pathlib import Path

CASE_ROOT = Path("/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e")
RUN_DIR = CASE_ROOT / "accuracy/m64-candidate-revert-minreg-01"
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
REQUESTS = 64
WAVES = 2
MAX_TOKENS = 128


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
        if line.startswith("#"):
            continue
        if "num_requests_running" not in line:
            continue
        match = re.search(r"\s([0-9]+(?:\.[0-9]+)?)$", line)
        if match:
            values.append(float(match.group(1)))
    return max(values, default=0.0)


def normalize(payload):
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise RuntimeError(f"invalid choices: {payload}")
    choice = choices[0]
    text = choice.get("text")
    if not isinstance(text, str) or not text:
        raise RuntimeError(f"empty completion: {payload}")
    usage = payload.get("usage", {})
    return {
        "text": text,
        "finish_reason": choice.get("finish_reason"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def make_payload(index):
    return {
        "model": "Qwen3.8-Flash-Next",
        "prompt": (
            "You are checking deterministic numerical consistency. "
            f"Case {index:02d}: compute {index + 17} + {index * 3 + 11}, "
            "then explain the arithmetic in one concise sentence."
        ),
        "max_tokens": MAX_TOKENS,
        "temperature": 0,
        "top_p": 1,
        "seed": 1234 + index,
        "ignore_eos": True,
    }


def run_service_wave(service_name, wave, start):
    service = SERVICES[service_name]
    start.wait()
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=REQUESTS) as pool:
        futures = {
            pool.submit(post_json, service["url"], make_payload(index)): index
            for index in range(REQUESTS)
        }
        rows = [None] * REQUESTS
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            rows[index] = normalize(future.result())
    elapsed = time.monotonic() - started
    print(f"service={service_name} wave={wave} requests={len(rows)} elapsed={elapsed:.3f}", flush=True)
    return rows, elapsed


def main():
    if RUN_DIR.exists():
        raise SystemExit(f"refusing to reuse {RUN_DIR}")
    RUN_DIR.mkdir(parents=True)
    manifests = {}
    for name, service in SERVICES.items():
        manifests[name] = json.loads(service["manifest"].read_text(encoding="utf-8"))
        get_json(service["url"].rsplit("/v1/completions", 1)[0] + "/v1/models")

    process = {
        "pid": os.getpid(),
        "started_at_unix": time.time(),
        "mode": "minimal-regression",
        "experiment_id": "acc-002-m64-candidate-revert-minimal-regression",
        "requests_per_service_per_wave": REQUESTS,
        "waves": WAVES,
        "max_tokens": MAX_TOKENS,
        "service_instance_ids": {
            name: manifest["service_instance_id"] for name, manifest in manifests.items()
        },
    }
    (RUN_DIR / "process.json").write_text(
        json.dumps(process, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    all_rows = {name: [] for name in SERVICES}
    elapsed = {name: [] for name in SERVICES}
    max_running = {name: 0.0 for name in SERVICES}
    for wave in range(1, WAVES + 1):
        start = threading.Barrier(len(SERVICES) + 1)
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
                name: pool.submit(run_service_wave, name, wave, start)
                for name in SERVICES
            }
            start.wait()
            for name, future in futures.items():
                rows, duration = future.result()
                all_rows[name].append(rows)
                elapsed[name].append(duration)
        stop_monitor.set()
        monitor_thread.join(timeout=5)

    stable = {
        name: all_rows[name][0] == all_rows[name][1]
        for name in SERVICES
    }
    cross_equal = all_rows["candidate"][0] == all_rows["revert"][0]
    mismatches = [
        index for index in range(REQUESTS)
        if all_rows["candidate"][0][index] != all_rows["revert"][0][index]
    ]
    result = {
        "schema_version": 1,
        "experiment_id": "acc-002-m64-candidate-revert-minimal-regression",
        "mode": "minimal-regression",
        "criterion": "two stable waves per service and byte-identical normalized outputs across candidate and revert",
        "requests_per_service_per_wave": REQUESTS,
        "waves": WAVES,
        "request_parameters": {
            "temperature": 0,
            "top_p": 1,
            "seed": "1234 + case_index",
            "ignore_eos": True,
            "max_tokens": MAX_TOKENS,
        },
        "service_instance_ids": process["service_instance_ids"],
        "stable_replay": stable,
        "cross_service_equal": cross_equal,
        "mismatch_indices": mismatches,
        "max_observed_running_requests": max_running,
        "elapsed_seconds": elapsed,
        "outputs": all_rows,
        "passed": all(stable.values()) and cross_equal and all(
            value >= REQUESTS for value in max_running.values()
        ),
    }
    (RUN_DIR / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in result.items() if key != "outputs"}, sort_keys=True), flush=True)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
