#!/usr/bin/env python3
"""Issue/check a formal accuracy gate bound to files and a service manifest."""
import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from sample_validation import task_filters, validate_sample_file
from verify_accuracy import load_task_metrics, metric_value

TASK = "gpqa_diamond_generative_cot"
RUNNER_SHA256 = "82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e"
EVAL_IMAGE = "harbor.baai.ac.cn/flageval/flageval-llmeval:v1"


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def content_sha256(value):
    """Canonical JSON content identity, also used for raw/processed GPQA docs."""
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def model_args_values(cfg):
    """The exact model_args supplied by the unchanged original runner."""
    return {"model": cfg["model_name"], "base_url": cfg["base_url"],
            "num_concurrent": cfg["num_concurrent"], "timeout": cfg["timeout"],
            "max_retries": cfg["api_max_retries"]}


def model_args_text(cfg):
    return ",".join(f"{key}={value}" for key, value in model_args_values(cfg).items())


def artifact(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha256(path)}


def checked_artifact(ref):
    if not isinstance(ref, dict) or sha256(ref["path"]) != ref["sha256"]:
        raise ValueError("artifact content changed or reference is invalid")
    return Path(ref["path"])


def write_new(path, value):
    # Serialize before creating anything. Publish a complete sibling file with
    # link(), whose no-clobber behavior also protects concurrent issuers. A
    # failed serialization/write/publish must not leave a partial final artifact.
    contents = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path = Path(path)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}.", suffix=".tmp") as handle:
        handle.write(contents)
        handle.flush()
        os.fsync(handle.fileno())
        os.link(handle.name, path)


def require_text(payload, keys):
    for key in keys:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip() or value.lower() in ("unknown", "todo", "model_name"):
            raise ValueError(f"missing/unknown identity: {key}")


def validate_service(service, *, formal=True):
    """Validate measured identity; formal accuracy also pins graph/chat mode.

    Performance research can explicitly opt out of those two accuracy-specific
    constraints while retaining the original service mode and all identity
    evidence. Formal gate callers use the strict default.
    """
    require_text(service, ("host", "optimization_container_name", "service_instance_id", "model_name", "base_url", "tokenizer_path"))
    for key in ("model_sha256", "tokenizer_sha256", "engine_sha256", "plugin_sha256", "flaggems_sha256", "runtime_evidence_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", service.get(key, "")):
            raise ValueError(f"{key} must be a measured SHA-256")
    allowed_modes = ("graph",) if formal else ("eager", "graph")
    if service.get("mode") not in allowed_modes:
        raise ValueError("formal service must have graph mode" if formal else "service mode must be eager or graph")
    if not isinstance(service.get("launch_config"), dict) or not service["launch_config"]:
        raise ValueError("service must have explicit launch_config")
    if service.get("image_lineage") != "verified" or service.get("mount_parity") != "passed":
        raise ValueError("service image lineage/mount parity gate has not passed")
    url = urlsplit(service["base_url"])
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("base_url must be an HTTP(S) endpoint without credentials/query/fragment")
    allowed_endpoints = ("/v1/chat/completions",) if formal else ("/v1/completions", "/v1/chat/completions")
    if url.path not in allowed_endpoints:
        raise ValueError("formal accuracy endpoint must be /v1/chat/completions" if formal
                         else "service endpoint must be /v1/completions or /v1/chat/completions")


def validate_contract(contract):
    if contract.get("schema_version") != 2 or contract.get("task") != TASK:
        raise ValueError("contract must be schema 2 with collected task provenance, full GPQA Diamond")
    if contract.get("expected_samples") != 198 or contract.get("expected_doc_ids") != list(range(198)):
        raise ValueError("contract must freeze all GPQA doc IDs 0..197")
    require_text(contract, ("metric", "dataset_revision"))
    provenance = read_json(checked_artifact(contract.get("task_provenance")))
    validate_provenance(provenance)
    if contract["dataset_revision"] != provenance["dataset_revision"]:
        raise ValueError("contract dataset_revision differs from the collected dataset content")
    if contract.get("minimum") is None and contract.get("baseline") is None:
        raise ValueError("freeze a minimum or a trusted baseline artifact before running")
    for key in ("minimum", "max_regression"):
        value = contract.get(key, 0 if key == "max_regression" else None)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value)):
            raise ValueError(f"{key} must be finite")
    if contract.get("max_regression", 0) < 0:
        raise ValueError("max_regression must be nonnegative")
    if contract.get("baseline") is not None:
        checked_artifact(contract["baseline"])


def validate_provenance(provenance, cfg=None):
    if (provenance.get("schema_version") != 1
            or provenance.get("adapter") != "lm-eval-configurable-task-v1"
            or provenance.get("task") != TASK):
        raise ValueError("unsupported/missing collected task provenance")
    for key in ("raw_doc_sha256", "eval_doc_sha256"):
        hashes = provenance.get(key)
        if not isinstance(hashes, list) or len(hashes) != 198 or any(
                not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes):
            raise ValueError(f"provenance requires 198 measured {key} entries")
    revision = "content-sha256:" + content_sha256(provenance["raw_doc_sha256"])
    if provenance.get("dataset_revision") != revision:
        raise ValueError("dataset revision does not match raw document fingerprints")
    task_config = provenance.get("task_config")
    if not isinstance(task_config, dict) or task_config.get("task") != TASK:
        raise ValueError("resolved task configuration is missing")
    if task_config.get("output_type") != "generate_until":
        raise ValueError("formal task must use generate_until")
    task_filters(task_config)
    if not isinstance(provenance.get("generation_overrides"), dict):
        raise ValueError("parsed generation overrides are missing")
    sources = provenance.get("sources")
    if not isinstance(sources, dict) or not sources.get("lm_eval"):
        raise ValueError("evaluator source evidence is missing")
    for source in sources.values():
        if not isinstance(source, dict) or not re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")):
            raise ValueError("invalid evaluator/task source fingerprint")
    require_text(provenance, ("lm_eval_version", "datasets_version", "dataset_path", "dataset_name", "dataset_split"))
    if cfg is not None:
        for key in ("dataset_path", "dataset_name", "dataset_split", "seed", "gen_kwargs", "include_path"):
            if provenance.get(key) != cfg.get(key, "" if key == "include_path" else None):
                raise ValueError(f"case config differs from collected task provenance: {key}")
        if task_config.get("dataset_path") != cfg["dataset_path"] or task_config.get("dataset_name") != cfg["dataset_name"]:
            raise ValueError("actual lm-eval task dataset differs from case config")
        split = task_config.get("test_split") or task_config.get("validation_split")
        if split != cfg["dataset_split"]:
            raise ValueError("actual lm-eval evaluation split differs from case config")


def verify_result_provenance(result_path, samples_path, cfg, provenance):
    """Validate the native v0.4.9-style lm-eval metadata; unknown schemas fail closed.

    Schema source: EleutherAI/lm-evaluation-harness v0.4.9 evaluator.py,
    simple_evaluate/evaluate. No dependency on lm_eval is needed to consume a gate.
    """
    payload = read_json(result_path)
    metadata = payload.get("config")
    if not isinstance(metadata, dict) or metadata.get("model") != cfg["model_type"]:
        raise ValueError("results metadata has a missing/different model backend")
    expected_args = model_args_values(cfg)
    model_args = metadata.get("model_args")
    expected_string = model_args_text(cfg)
    if model_args != expected_args and model_args != expected_string:
        raise ValueError("results model/endpoint/request configuration differs from the frozen run")
    for key in ("random_seed", "numpy_seed", "torch_seed", "fewshot_seed"):
        if type(metadata.get(key)) is not int or metadata[key] != cfg["seed"]:
            raise ValueError(f"results seed differs or is missing: {key}")
    if "limit" not in metadata or metadata["limit"] is not None:
        raise ValueError("results must report a full evaluation with limit=null")
    if metadata.get("gen_kwargs") != provenance["generation_overrides"]:
        raise ValueError("results generation overrides differ from the frozen run")
    safe = lambda value: re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "run"
    cache = Path(cfg["cache_root"]) / safe(cfg["eval_model"]) / safe(cfg["run_id"]) / TASK / "responses.sqlite"
    if metadata.get("use_cache") != str(cache):
        raise ValueError("results do not belong to this run's response-cache namespace")
    if payload.get("configs", {}).get(TASK) != provenance["task_config"]:
        raise ValueError("results task configuration differs from the resolved frozen task")
    count = payload.get("n-samples", {}).get(TASK, {})
    if any(type(count.get(key)) is not int or count[key] != 198 for key in ("original", "effective")):
        raise ValueError("results do not report 198 original and effective samples")
    # lm-eval logs the actual processed doc per sample. Bind each ID to content,
    # not just to 0..197, which could name 198 entirely different questions.
    for line in Path(samples_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        sample = json.loads(line)
        doc_id = int(sample["doc_id"])
        if "doc" not in sample or content_sha256(sample["doc"]) != provenance["eval_doc_sha256"][doc_id]:
            raise ValueError(f"sample {doc_id} differs from the frozen processed evaluation document")


def validate_config_integers(cfg):
    """Reject lossy int() coercion by the fixed original runner before loading it."""
    if not isinstance(cfg, dict):
        raise ValueError("case config must be a JSON object")
    minimums = {
        "limit": 0, "expected_samples": 1, "seed": 0,
        "num_concurrent": 1, "timeout": 1, "api_max_retries": 0,
        "eval_max_retries": 0, "retry_delay": 0,
        "service_poll_interval": 1, "service_wait_timeout": 0,
        "progress_score_interval": 0, "progress_score_poll_seconds": 1,
    }
    for key, minimum in minimums.items():
        if key in cfg and (type(cfg[key]) is not int or cfg[key] < minimum):
            raise ValueError(f"{key} must be an integer >= {minimum}")


def validate_config(cfg, service):
    validate_config_integers(cfg)
    if cfg.get("tasks") != [TASK] or cfg.get("limit") != 0 or cfg.get("expected_samples") != 198:
        raise ValueError("formal config requires full GPQA: limit=0, expected_samples=198")
    if cfg.get("allow_timeouts") is not False:
        raise ValueError("formal config must explicitly set allow_timeouts=false")
    if cfg.get("model_name") != service["model_name"] or cfg.get("base_url") != service["base_url"]:
        raise ValueError("config model/endpoint does not match service manifest")
    if any("," in cfg[key] for key in ("model_name", "base_url")):
        raise ValueError("model/endpoint cannot contain commas in the original runner's model_args format")
    if cfg.get("dataset_name") != "gpqa_diamond" or cfg.get("dataset_split") != "train" or not cfg.get("dataset_path"):
        raise ValueError("explicit GPQA dataset configuration is required")
    if cfg.get("model_type") != "openai-chat-completions" or cfg.get("apply_chat_template") is not True:
        raise ValueError("formal workflow requires chat completions and chat template")
    if not isinstance(cfg.get("gen_kwargs"), str) or not cfg["gen_kwargs"].strip():
        raise ValueError("freeze generation parameters explicitly")
    if type(cfg.get("seed")) is not int or cfg["seed"] < 0:
        raise ValueError("freeze a nonnegative integer lm-eval seed")


def score_check(result, contract):
    value = metric_value(load_task_metrics(result, contract["task"]), contract["metric"])
    minimum = contract.get("minimum")
    if minimum is not None and value < minimum:
        raise ValueError("candidate score is below the frozen minimum")
    if contract.get("baseline"):
        baseline = checked_artifact(contract["baseline"])
        baseline_value = metric_value(load_task_metrics(baseline, contract["task"]), contract["metric"])
        if value < baseline_value - contract.get("max_regression", 0):
            raise ValueError("candidate score regressed beyond the frozen allowance")
    return value


def inspect_evaluator(path):
    value = read_json(path)
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, dict) or value.get("Config", {}).get("Image") != EVAL_IMAGE:
        raise ValueError("evaluation container image reference does not match the required image")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value.get("Image", "")):
        raise ValueError("evaluation container image ID is missing")
    return value


def verify_run(record_path):
    return verify_run_record(read_json(record_path))


def verify_run_record(record):
    """Check all evidence before a wrapper publishes a completed run record."""
    if record.get("schema_version") != 2 or record.get("status") != "evaluated" or record.get("process_succeeded") is not True:
        raise ValueError("run is not complete")
    refs = record["artifacts"]
    paths = {key: checked_artifact(refs[key]) for key in (
        "contract", "config", "service", "runner", "results", "samples", "evaluation_inspect", "task_provenance"
    )}
    if refs["runner"]["sha256"] != RUNNER_SHA256:
        raise ValueError("run did not use the original formal runner baseline")
    service = read_json(paths["service"])
    contract = read_json(paths["contract"])
    validate_service(service)
    validate_contract(contract)
    cfg = read_json(paths["config"])
    validate_config(cfg, service)
    if refs["task_provenance"]["sha256"] != contract["task_provenance"]["sha256"]:
        raise ValueError("run task provenance differs from the frozen contract")
    provenance = read_json(paths["task_provenance"])
    validate_provenance(provenance, cfg)
    inspect_evaluator(paths["evaluation_inspect"])
    validate_sample_file(paths["samples"], 198, contract["expected_doc_ids"],
                         expected_filters=task_filters(provenance["task_config"]))
    verify_result_provenance(paths["results"], paths["samples"], cfg, provenance)
    score = score_check(paths["results"], contract)
    return record, service, score


def issue_gate(record_path, health_path, output):
    record, service, score = verify_run(record_path)
    health = read_json(health_path)
    if health.get("samples_sha256") != record["artifacts"]["samples"]["sha256"]:
        raise ValueError("health review is for a different samples file")
    # lm-eval samples do not always preserve finish_reason/token counts. Do not
    # claim truncation/repetition checks based on their absence.
    for key in ("empty_outputs", "truncation", "abnormal_repetition", "garbled_output", "timeouts"):
        if health.get(key) != "passed":
            raise ValueError(f"output health review is incomplete: {key}")
    require_text(health, ("reviewer", "method"))
    gate = {"schema_version": 2, "passed": True, "score": score,
            "service_sha256": record["artifacts"]["service"]["sha256"],
            "run_record": artifact(record_path), "health_review": artifact(health_path)}
    write_new(output, gate)
    return gate


def check_gate(gate_path, service_path, model=None, host=None, port=None, tokenizer=None):
    gate = read_json(gate_path)
    if gate.get("schema_version") != 2 or gate.get("passed") is not True:
        raise ValueError("not a formal acceptance record")
    if sha256(service_path) != gate.get("service_sha256"):
        raise ValueError("current service manifest differs from the evaluated service")
    record_path = checked_artifact(gate["run_record"])
    health_path = checked_artifact(gate["health_review"])
    record, service, score = verify_run(record_path)
    health = read_json(health_path)
    if record["artifacts"]["service"]["sha256"] != gate["service_sha256"] or score != gate.get("score"):
        raise ValueError("gate does not match its run record")
    if health.get("samples_sha256") != record["artifacts"]["samples"]["sha256"]:
        raise ValueError("health review samples changed")
    for key in ("empty_outputs", "truncation", "abnormal_repetition", "garbled_output", "timeouts"):
        if health.get(key) != "passed":
            raise ValueError("output health review did not pass")
    require_text(health, ("reviewer", "method"))
    url = urlsplit(service["base_url"])
    if tokenizer is not None and tokenizer != service["tokenizer_path"]:
        raise ValueError("benchmark tokenizer differs from accepted tokenizer path")
    if model is not None and model != service["model_name"]:
        raise ValueError("benchmark model differs from accepted model")
    if host is not None and host != url.hostname:
        raise ValueError("benchmark host differs from accepted endpoint")
    if port is not None and port != (url.port or (443 if url.scheme == "https" else 80)):
        raise ValueError("benchmark port differs from accepted endpoint")
    return gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    issue = commands.add_parser("issue")
    issue.add_argument("--run-record", required=True, type=Path)
    issue.add_argument("--health-review", required=True, type=Path)
    issue.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check")
    check.add_argument("--gate", required=True, type=Path)
    check.add_argument("--service-manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "issue":
            issue_gate(args.run_record, args.health_review, args.output)
        else:
            check_gate(args.gate, args.service_manifest)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print("PASS: formal accuracy acceptance verified")


if __name__ == "__main__":
    main()
