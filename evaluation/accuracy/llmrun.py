#!/usr/bin/env python3
"""Run reproducible lm-eval API accuracy jobs in flageval_llmeval."""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sample_validation import validate_sample_file


def log(level: str, message: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] [{level:<5}] {message}", flush=True)


def fail(message: str, code: int = 1) -> None:
    log("ERROR", message)
    raise SystemExit(code)


def resolve_path(value: str, config_dir: Path) -> str:
    if not value:
        return ""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = config_dir / path
    return str(path.resolve())


def load_config(config_path: Path) -> Dict:
    if not config_path.is_file():
        fail(f"Configuration file does not exist: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        cfg = json.load(handle)

    defaults = {
        "model_type": "openai-chat-completions",
        "base_url": "http://127.0.0.1:8010/v1/chat/completions",
        "tasks": ["gpqa_diamond_generative_cot"],
        "limit": 0,
        "num_concurrent": 1,
        "timeout": 3600,
        "api_max_retries": 3,
        "eval_max_retries": 0,
        "retry_delay": 60,
        "gen_kwargs": "",
        "apply_chat_template": True,
        "include_path": "",
        "output_root": "./outputs",
        "cache_root": "/tmp/lm_eval_cache",
        "run_id": "auto",
        "offline": True,
        "hf_datasets_cache": "/root/.cache/huggingface/datasets",
        "dataset_path": "",
        "dataset_name": "",
        "dataset_split": "train",
        "expected_samples": 0,
        "allow_timeouts": False,
        "wait_for_service": False,
        "service_poll_interval": 1800,
        "service_wait_timeout": 0,
        "progress_score_interval": 10,
        "progress_score_poll_seconds": 5,
    }
    for key, value in defaults.items():
        cfg.setdefault(key, value)

    for key in ("eval_model", "model_name", "base_url"):
        if not cfg.get(key):
            fail(f"Missing required configuration key: {key}")

    tasks = cfg.get("tasks", cfg.get("task"))
    if isinstance(tasks, str):
        tasks = [tasks]
    if not tasks or not all(isinstance(task, str) and task for task in tasks):
        fail("tasks must be a non-empty string or list of strings")
    cfg["tasks"] = tasks

    config_dir = config_path.parent.resolve()
    cfg["output_root"] = resolve_path(cfg["output_root"], config_dir)
    cfg["cache_root"] = resolve_path(cfg["cache_root"], config_dir)
    cfg["include_path"] = resolve_path(cfg["include_path"], config_dir)

    for key in (
        "limit",
        "num_concurrent",
        "timeout",
        "api_max_retries",
        "eval_max_retries",
        "retry_delay",
        "expected_samples",
        "service_poll_interval",
        "service_wait_timeout",
        "progress_score_interval",
        "progress_score_poll_seconds",
    ):
        try:
            cfg[key] = int(cfg[key])
        except (TypeError, ValueError):
            fail(f"{key} must be an integer")

    if cfg["limit"] < 0:
        fail("limit must be >= 0")
    if cfg["num_concurrent"] < 1:
        fail("num_concurrent must be >= 1")
    if cfg["timeout"] < 1:
        fail("timeout must be >= 1")
    if cfg["service_poll_interval"] < 1:
        fail("service_poll_interval must be >= 1")
    if cfg["service_wait_timeout"] < 0:
        fail("service_wait_timeout must be >= 0")
    if cfg["progress_score_interval"] < 0 or cfg["progress_score_poll_seconds"] < 1:
        fail("progress_score_interval must be >= 0 and progress_score_poll_seconds must be >= 1")
    return cfg


def configure_environment(cfg: Dict) -> None:
    os.environ.setdefault("OPENAI_API_KEY", "EMPTY")
    os.environ["HF_DATASETS_CACHE"] = cfg["hf_datasets_cache"]
    if cfg["offline"]:
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"


def models_url(base_url: str) -> str:
    replaced = re.sub(r"/v1/.*$", "/v1/models", base_url.rstrip("/"))
    if replaced == base_url.rstrip("/"):
        return base_url.rstrip("/") + "/v1/models"
    return replaced


def probe_service(cfg: Dict, timeout: int = 10) -> Tuple[bool, str]:
    url = models_url(cfg["base_url"])
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        model_ids = [item.get("id") for item in body.get("data", [])]
        if cfg["model_name"] not in model_ids:
            return False, f"HTTP 200, but {cfg['model_name']!r} is not in {model_ids}"
        return True, f"HTTP 200, models={model_ids}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code} from {url}"
    except Exception as exc:  # noqa: BLE001 - preflight should report all failures
        return False, f"{type(exc).__name__}: {exc}"


def wait_for_service(cfg: Dict) -> None:
    started = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        healthy, detail = probe_service(cfg)
        if healthy:
            log("INFO", f"Model service ready after {attempt} probe(s): {detail}")
            return
        if not cfg.get("wait_for_service", False):
            fail(f"Model service is not ready: {detail}")

        elapsed = int(time.monotonic() - started)
        wait_timeout = cfg["service_wait_timeout"]
        if wait_timeout and elapsed >= wait_timeout:
            fail(
                f"Model service did not become ready within {wait_timeout} seconds; "
                f"last probe: {detail}"
            )
        interval = cfg["service_poll_interval"]
        if wait_timeout:
            interval = min(interval, max(1, wait_timeout - elapsed))
        next_probe = datetime.fromtimestamp(time.time() + interval).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        log(
            "WAIT",
            f"Service not ready (probe {attempt}: {detail}); "
            f"next probe in {interval}s at {next_probe}",
        )
        time.sleep(interval)


def verify_dataset(cfg: Dict) -> None:
    dataset_path = cfg.get("dataset_path")
    dataset_name = cfg.get("dataset_name")
    expected = cfg.get("expected_samples", 0)
    if not dataset_path:
        return
    try:
        from datasets import load_dataset

        dataset = load_dataset(
            dataset_path,
            dataset_name or None,
            split=cfg["dataset_split"],
            cache_dir=cfg["hf_datasets_cache"],
        )
    except Exception as exc:  # noqa: BLE001 - surface dataset/cache failures
        fail(f"Dataset preflight failed for {dataset_path}/{dataset_name}: {exc}")
    actual = len(dataset)
    if expected and actual != expected:
        fail(f"Dataset sample count mismatch: expected {expected}, found {actual}")
    log("INFO", f"Dataset ready: {dataset_path}/{dataset_name}, split={cfg['dataset_split']}, samples={actual}")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "run"


def create_run_dir(cfg: Dict) -> Path:
    run_id = cfg.get("run_id", "auto")
    if not run_id or run_id == "auto":
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(cfg["output_root"]) / safe_name(cfg["eval_model"]) / safe_name(run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    with (run_dir / "effective_config.json").open("w", encoding="utf-8") as handle:
        json.dump(cfg, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return run_dir


def build_command(cfg: Dict, task: str, task_dir: Path) -> List[str]:
    # SQLite WAL/locking is unreliable on shared NFS mounts. Keep response
    # cache local to the evaluation container while results remain on NFS.
    cache_dir = (
        Path(cfg["cache_root"])
        / safe_name(cfg["eval_model"])
        / task_dir.parent.name
        / safe_name(task)
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "responses.sqlite"
    model_args = ",".join(
        [
            f"model={cfg['model_name']}",
            f"base_url={cfg['base_url']}",
            f"num_concurrent={cfg['num_concurrent']}",
            f"timeout={cfg['timeout']}",
            f"max_retries={cfg['api_max_retries']}",
        ]
    )
    command = [
        "lm_eval",
        "--tasks",
        task,
        "--output_path",
        str(task_dir),
        "--model",
        cfg["model_type"],
        "--model_args",
        model_args,
        "--use_cache",
        str(cache_file),
        "--log_samples",
        "--verbosity",
        "INFO",
    ]
    if cfg.get("gen_kwargs"):
        command.extend(["--gen_kwargs", cfg["gen_kwargs"]])
    if cfg.get("apply_chat_template"):
        command.append("--apply_chat_template")
    if cfg["limit"] > 0:
        command.extend(["--limit", str(cfg["limit"])])
    if cfg.get("include_path"):
        include_path = Path(cfg["include_path"])
        if not include_path.is_dir():
            fail(f"include_path is not a directory: {include_path}")
        command.extend(["--include_path", str(include_path)])
    return command


def run_streaming(
    command: List[str],
    log_file: Path,
    sidecar_command: Optional[List[str]] = None,
) -> int:
    log("INFO", "Command: " + " ".join(command))
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] command={' '.join(command)}\n")
        handle.flush()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        sidecar = None
        if sidecar_command:
            sidecar = subprocess.Popen(sidecar_command + ["--pid", str(process.pid)])
        try:
            assert process.stdout is not None
            for line in process.stdout:
                handle.write(line)
                handle.flush()
                print(line, end="", flush=True)
            return_code = process.wait()
        except KeyboardInterrupt:
            os.killpg(process.pid, signal.SIGINT)
            return_code = process.wait()
        finally:
            if sidecar is not None:
                try:
                    sidecar.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    sidecar.terminate()
                    sidecar.wait(timeout=5)
        return return_code


def newest_result(task_dir: Path) -> Optional[Path]:
    files = list(task_dir.rglob("results_*.json"))
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def newest_samples(task: str, task_dir: Path) -> Optional[Path]:
    files = list(task_dir.rglob(f"samples_{task}_*.jsonl"))
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def validate_samples(cfg: Dict, task: str, task_dir: Path) -> bool:
    samples_file = newest_samples(task, task_dir)
    if samples_file is None:
        log("ERROR", f"No samples JSONL was found for {task} under {task_dir}")
        return False
    expected = cfg["limit"] if cfg["limit"] > 0 else cfg.get("expected_samples", 0)
    try:
        summary = validate_sample_file(
            samples_file, expected, cfg.get("expected_doc_ids"),
            allow_timeouts=cfg.get("allow_timeouts", False),
        )
    except (ValueError, OSError, TypeError) as exc:
        log("ERROR", str(exc))
        return False
    log("INFO", f"Validated samples: {summary}")
    return True


def report_result(cfg: Dict, task: str, task_dir: Path) -> bool:
    result_file = newest_result(task_dir)
    if result_file is None:
        log("ERROR", f"lm-eval exited successfully but no results JSON was found under {task_dir}")
        return False
    with result_file.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    metrics = result.get("results", {}).get(task)
    if not metrics:
        log("ERROR", f"No metrics for task {task} in {result_file}")
        return False
    log("INFO", f"Result file: {result_file}")
    for key, value in metrics.items():
        if isinstance(value, (int, float, str, bool)) or value is None:
            log("RESULT", f"{task}: {key}={value}")
    return validate_samples(cfg, task, task_dir)


def run_task(cfg: Dict, task: str, run_dir: Path) -> bool:
    task_dir = run_dir / safe_name(task)
    task_dir.mkdir(parents=True, exist_ok=False)
    command = build_command(cfg, task, task_dir)
    log_file = task_dir / "lm_eval.log"
    score_command = None
    score_interval = cfg.get("progress_score_interval", 0)
    score_helper = Path(__file__).resolve().with_name("score_progress.py")
    if score_interval and task == "gpqa_diamond_generative_cot":
        if not score_helper.is_file():
            log("WARN", f"Interim score helper not found: {score_helper}")
        else:
            cache_base = Path(command[command.index("--use_cache") + 1])
            score_command = [
                sys.executable,
                str(score_helper),
                "--config",
                str(run_dir / "effective_config.json"),
                "--cache-db",
                str(cache_base) + "_rank0.db",
                "--interval",
                str(score_interval),
                "--poll-seconds",
                str(cfg["progress_score_poll_seconds"]),
                "--output",
                str(task_dir / "progress_score.log"),
            ]

    attempts = cfg["eval_max_retries"] + 1
    for attempt in range(1, attempts + 1):
        log("STEP", f"Starting {task}, attempt {attempt}/{attempts}")
        return_code = run_streaming(command, log_file, score_command)
        if return_code == 0:
            if report_result(cfg, task, task_dir):
                return True
            log("ERROR", "lm_eval returned 0, but result validation failed")
        elif return_code < 0:
            log("ERROR", f"lm_eval was terminated by signal {-return_code}")
        else:
            log("ERROR", f"lm_eval exited with code {return_code}")
        if attempt >= attempts:
            return False
        healthy, detail = probe_service(cfg)
        log("WARN", f"Retry preflight: service_healthy={healthy}, detail={detail}")
        log(
            "WARN",
            f"Retrying in {cfg['retry_delay']} seconds; completed responses remain "
            "in the container-local SQLite cache",
        )
        time.sleep(cfg["retry_delay"])
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", default="llm_config.json")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate service, model id, and offline dataset without starting lm-eval",
    )
    args = parser.parse_args()
    config_path = Path(args.config).expanduser().resolve()
    cfg = load_config(config_path)
    configure_environment(cfg)

    if shutil.which("lm_eval") is None:
        fail("lm_eval is not available on PATH")
    verify_dataset(cfg)

    log("INFO", f"Tasks={cfg['tasks']}, limit={cfg['limit'] or 'full'}, concurrency={cfg['num_concurrent']}")
    if args.preflight_only:
        healthy, detail = probe_service(cfg)
        if not healthy:
            fail(f"Model service is not ready: {detail}")
        log("INFO", f"Model service ready: {detail}")
        log("INFO", "Preflight completed; lm-eval was not started")
        return
    wait_for_service(cfg)
    run_dir = create_run_dir(cfg)
    log("INFO", f"Run directory: {run_dir}")

    failed = [task for task in cfg["tasks"] if not run_task(cfg, task, run_dir)]
    if failed:
        fail("Failed tasks: " + ", ".join(failed))
    log("INFO", "All tasks completed successfully")


if __name__ == "__main__":
    main()
