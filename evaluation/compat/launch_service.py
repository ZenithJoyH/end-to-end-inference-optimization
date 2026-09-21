#!/usr/bin/env python3
# Compatibility-only: not the current container creation workflow.
"""Legacy isolated XingChen4 vLLM launcher with fail-closed preflight checks.

Retained for historical contract tests; new tasks use the repository control
plane and freshly generated service manifests.
"""

import math
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.request
import json


def _integer(env, name, default=None, minimum=1):
    value = env.get(name, default)
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return result


def _float(env, name, default, minimum=0, maximum=None):
    try:
        result = float(env.get(name, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result) or result <= minimum or (maximum is not None and result > maximum):
        raise ValueError(f"{name} is outside the supported range")
    return result


def _boolean(env, name, default):
    value = str(env.get(name, default)).strip().lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be a boolean")


def settings(env=None) -> dict:
    env = dict(os.environ if env is None else env)
    required = ("MODEL_PATH", "MODEL_NAME", "PORT", "DEVICE_IDS", "TP_SIZE", "ARTIFACT_ROOT", "SERVICE_LABEL")
    missing = [name for name in required if not str(env.get(name, "")).strip()]
    if missing:
        raise ValueError(f"missing settings: {', '.join(missing)}")

    model_path = Path(env["MODEL_PATH"])
    artifact_root = Path(env["ARTIFACT_ROOT"])
    if not model_path.is_absolute() or not artifact_root.is_absolute():
        raise ValueError("MODEL_PATH and ARTIFACT_ROOT must be absolute")
    label = env["SERVICE_LABEL"].strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", label):
        raise ValueError("SERVICE_LABEL is not a safe identifier")

    port = _integer(env, "PORT")
    if port > 65535:
        raise ValueError("PORT exceeds 65535")
    devices = [item.strip() for item in env["DEVICE_IDS"].split(",")]
    if not devices or any(not re.fullmatch(r"\d+", item) for item in devices) or len(set(devices)) != len(devices):
        raise ValueError("DEVICE_IDS must contain unique integer identifiers")
    tp_size = _integer(env, "TP_SIZE")
    if tp_size != len(devices):
        raise ValueError("TP_SIZE must equal the number of visible devices")

    return {
        "model_path": model_path,
        "model_name": env["MODEL_NAME"].strip(),
        "port": port,
        "devices": devices,
        "tp_size": tp_size,
        "root": artifact_root,
        "label": label,
        "max_model_len": _integer(env, "MAX_MODEL_LEN", "100000"),
        "max_num_batched_tokens": _integer(env, "MAX_NUM_BATCHED_TOKENS", "8192"),
        "memory_utilization": _float(env, "MEMORY_UTILIZATION", "0.8", maximum=1),
        "startup_timeout": _float(env, "STARTUP_TIMEOUT", "1800"),
        "prefix_caching": _boolean(env, "PREFIX_CACHING", "1"),
    }


def serving_processes(output: str) -> list[int]:
    result = []
    for line in output.splitlines():
        match = re.match(r"\s*(\d+)\s+(.*)\Z", line)
        if not match:
            continue
        pid, command = int(match.group(1)), match.group(2)
        if "vllm bench serve" in command:
            continue
        if re.search(r"(?:^|[/\s])vllm\s+serve(?:\s|$)", command) or "-m vllm.entrypoints.openai.api_server" in command:
            result.append(pid)
    return result


def wait_ready(child, port: int, model: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error = "service did not become ready"
    while True:
        child.poll()
        if child.returncode is not None:
            raise RuntimeError(f"service exited with status {child.returncode}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError("health endpoint is not ready")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=5) as response:
                payload = json.load(response)
            listed = [item.get("id") for item in payload.get("data", []) if isinstance(item, dict)]
            if model in listed:
                return
            last_error = "requested model is not listed"
        except Exception as exc:  # readiness polling records the last useful cause
            if not isinstance(exc, (StopIteration, IndexError)):
                last_error = str(exc) or type(exc).__name__
        if time.monotonic() >= deadline:
            raise RuntimeError(last_error)
        time.sleep(min(2, max(0, deadline - time.monotonic())))


def launch(config: dict, env=None):
    env = dict(os.environ if env is None else env)
    processes = subprocess.run(
        ["ps", "-eo", "pid=,args="], capture_output=True, text=True, check=False
    )
    active = serving_processes(processes.stdout)
    if active:
        raise ValueError(f"a vLLM service already exists: {active}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex(("127.0.0.1", config["port"])) == 0:
            raise ValueError(f"port {config['port']} is already in use")

    root = config["root"]
    root.mkdir(parents=True, exist_ok=True)
    pid_path = root / f"{config['label']}.pid"
    current_path = root / "current-service"
    if pid_path.exists() or current_path.exists():
        raise ValueError("service state already exists")

    command = [
        "vllm", "serve", str(config["model_path"]),
        "--served-model-name", config["model_name"],
        "--host", "0.0.0.0",
        "--port", str(config["port"]),
        "--trust-remote-code",
        "--tensor-parallel-size", str(config["tp_size"]),
        "--max-model-len", str(config["max_model_len"]),
        "--gpu-memory-utilization", str(config["memory_utilization"]),
        "--max-num-batched-tokens", str(config["max_num_batched_tokens"]),
        "--enable-prefix-caching" if config["prefix_caching"] else "--no-enable-prefix-caching",
    ]
    child_env = dict(env)
    child_env["CUDA_VISIBLE_DEVICES"] = ",".join(config["devices"])
    log_path = root / f"{config['label']}.log"
    with log_path.open("x", encoding="utf-8") as log:
        child = subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT, env=child_env, start_new_session=True
        )
    pid_path.write_text(f"{child.pid}\n", encoding="utf-8")
    child.poll()
    if child.returncode is not None:
        raise RuntimeError(f"service exited with status {child.returncode}")
    try:
        wait_ready(child, config["port"], config["model_name"], config["startup_timeout"])
    except Exception:
        if child.returncode is None:
            child.terminate()
        raise
    current_path.write_text(f"{config['label']}\n", encoding="utf-8")
    print(f"Ready: {config['model_name']} on 127.0.0.1:{config['port']}")
    return child


def main() -> int:
    launch(settings(), os.environ)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
