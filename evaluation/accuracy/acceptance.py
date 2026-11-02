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

from sample_validation import iter_sample_records, task_filters, validate_sample_file
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


def bound_task(payload):
    """Keep the standard task default; an explicit reference binds all resources.

    This opt-in path replays a user-authorized, complete GPQA request protocol.
    A task name alone never enables custom task classes or a different dataset.
    """
    reference = payload.get("reference_protocol")
    if reference is None:
        return TASK
    required = {"task", "authorization", "manifest", "requests", "parameters", "implementation"}
    if not isinstance(reference, dict) or set(reference) != required:
        raise ValueError("reference protocol requires explicit authorization and four frozen resources")
    require_text(reference, ("task", "authorization"))
    name = reference["task"]
    if name == TASK or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name):
        raise ValueError("reference task must have a distinct explicit identifier")
    resources = {key: checked_artifact(reference[key]) for key in
                 ("manifest", "requests", "parameters", "implementation")}
    manifest = read_json(resources["manifest"])
    if manifest.get("task") != name or not re.fullmatch(r"[0-9a-f]{64}", manifest.get("reference_sha256", "")):
        raise ValueError("reference manifest does not identify the frozen task/source")
    parent = resources["manifest"].resolve().parent
    for key in ("requests", "parameters", "implementation"):
        path = resources[key].resolve()
        if path.parent != parent or manifest.get("files", {}).get(path.name) != reference[key]["sha256"]:
            raise ValueError("reference resource differs from its original protocol manifest")
    docs = [row for _, row in iter_sample_records(resources["requests"])]
    if (len(docs) != 198 or any(not isinstance(doc, dict) for doc in docs)
            or [doc.get("index") for doc in docs] != list(range(198))):
        raise ValueError("reference protocol must contain exactly the ordered 198 GPQA documents")
    parameters = read_json(resources["parameters"])
    for doc in docs:
        request = doc.get("request")
        if (doc.get("gold") not in ("A", "B", "C", "D") or not isinstance(request, dict)
                or not isinstance(request.get("model"), str) or not request["model"]
                or not isinstance(request.get("messages"), list) or not request["messages"]):
            raise ValueError("invalid frozen GPQA reference request/target")
        if {key: value for key, value in request.items() if key not in ("model", "messages")} != parameters:
            raise ValueError("reference request generation parameters differ from the frozen parameters")
    return name


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
        if not isinstance(service.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", service[key]):
            raise ValueError(f"{key} must be a measured SHA-256")
    installed = service.get("flaggems_vllm_installed")
    if type(installed) is not bool:
        raise ValueError("flaggems_vllm_installed must be an observed boolean (missing is not absent)")
    digest = service.get("flaggems_vllm_sha256")
    if installed:
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("installed FlagGems-vllm requires measured flaggems_vllm_sha256")
    elif digest is not None:
        raise ValueError("absent FlagGems-vllm must have null flaggems_vllm_sha256")
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
    if contract.get("schema_version") != 3 or contract.get("task") != bound_task(contract):
        raise ValueError("contract must be schema 3 with collected task provenance, full GPQA Diamond")
    if contract.get("expected_samples") != 198 or contract.get("expected_doc_ids") != list(range(198)):
        raise ValueError("contract must freeze all GPQA doc IDs 0..197")
    require_text(contract, ("metric", "dataset_revision"))
    provenance = read_json(checked_artifact(contract.get("task_provenance")))
    validate_provenance(provenance)
    if provenance.get("reference_protocol") != contract.get("reference_protocol"):
        raise ValueError("contract and task provenance bind different reference protocols")
    if contract["dataset_revision"] != provenance["dataset_revision"]:
        raise ValueError("contract dataset_revision differs from the collected dataset content")
    threshold = contract.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (float, int)) or not math.isfinite(threshold):
        raise ValueError("threshold must be a finite number frozen before running")
    if any(key in contract for key in ("minimum", "baseline", "max_regression")):
        raise ValueError("schema 3 accuracy contracts use only threshold; legacy score gates are not allowed")


def validate_provenance(provenance, cfg=None):
    task_name = bound_task(provenance)
    if (provenance.get("schema_version") != 1
            or provenance.get("adapter") != "lm-eval-configurable-task-v1"
            or provenance.get("task") != task_name):
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
    if not isinstance(task_config, dict) or task_config.get("task") != task_name:
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
    names = ("lm_eval_version", "datasets_version", "dataset_path", "dataset_split")
    require_text(provenance, names if provenance.get("reference_protocol") else (*names, "dataset_name"))
    if provenance.get("reference_protocol"):
        reference = provenance["reference_protocol"]
        docs = [doc for _, doc in iter_sample_records(checked_artifact(reference["requests"]))]
        if provenance["raw_doc_sha256"] != [content_sha256(doc) for doc in docs]:
            raise ValueError("resolved reference dataset differs from the frozen original requests")
        if provenance.get("reference_request_sha256") != [content_sha256(doc["request"]) for doc in docs]:
            raise ValueError("reference task request construction was not verified against all 198 frozen requests")
        if (task_config.get("dataset_path") != "json" or task_config.get("dataset_name") is not None
                or task_config.get("dataset_kwargs", {}).get("data_files", {}).get("test") != reference["requests"]["path"]):
            raise ValueError("reference task must load the exact frozen request file")
    if cfg is not None:
        if cfg.get("reference_protocol") != provenance.get("reference_protocol") or bound_task(cfg) != task_name:
            raise ValueError("config and provenance bind different task protocols")
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
    task_name = bound_task(cfg)
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
    # lm-eval serializes absent/empty CLI overrides as an explicit null.
    # Missing metadata is not evidence of that state; nonempty frozen overrides
    # must still compare exactly.
    actual_overrides = metadata.get("gen_kwargs")
    if ("gen_kwargs" in metadata and actual_overrides is None
            and cfg.get("gen_kwargs") == ""
            and provenance["generation_overrides"] == {}):
        actual_overrides = {}
    if ("gen_kwargs" not in metadata
            or actual_overrides != provenance["generation_overrides"]):
        raise ValueError("results generation overrides differ from the frozen run")
    safe = lambda value: re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "run"
    cache = Path(cfg["cache_root"]) / safe(cfg["eval_model"]) / safe(cfg["run_id"]) / task_name / "responses.sqlite"
    if metadata.get("use_cache") != str(cache):
        raise ValueError("results do not belong to this run's response-cache namespace")
    if payload.get("configs", {}).get(task_name) != provenance["task_config"]:
        raise ValueError("results task configuration differs from the resolved frozen task")
    count = payload.get("n-samples", {}).get(task_name, {})
    if any(type(count.get(key)) is not int or count[key] != 198 for key in ("original", "effective")):
        raise ValueError("results do not report 198 original and effective samples")
    # lm-eval logs the actual processed doc per sample. Bind each ID to content,
    # not just to 0..197, which could name 198 entirely different questions.
    for _, sample in iter_sample_records(samples_path):
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
    task_name = bound_task(cfg)
    if cfg.get("tasks") != [task_name] or cfg.get("limit") != 0 or cfg.get("expected_samples") != 198:
        raise ValueError("formal config requires full GPQA: limit=0, expected_samples=198")
    if type(cfg.get("allow_timeouts")) is not bool:
        raise ValueError("allow_timeouts must be a boolean compatibility field")
    if cfg.get("model_name") != service["model_name"] or cfg.get("base_url") != service["base_url"]:
        raise ValueError("config model/endpoint does not match service manifest")
    if any("," in cfg[key] for key in ("model_name", "base_url")):
        raise ValueError("model/endpoint cannot contain commas in the original runner's model_args format")
    if cfg.get("reference_protocol"):
        reference = cfg["reference_protocol"]
        parameters = read_json(checked_artifact(reference["parameters"]))
        docs = [doc for _, doc in iter_sample_records(checked_artifact(reference["requests"]))]
        if (cfg.get("dataset_path") != "json" or cfg.get("dataset_name") is not None
                or cfg.get("dataset_split") != "test" or cfg.get("model_type") != "local-chat-completions"
                or cfg.get("gen_kwargs") != "" or cfg.get("seed") != parameters.get("seed")
                or cfg.get("apply_chat_template") is not True
                or Path(cfg.get("include_path", "")).resolve() != Path(reference["manifest"]["path"]).resolve().parent
                or any(doc["request"]["model"] != cfg["model_name"] for doc in docs)):
            raise ValueError("reference config must preserve the frozen model, dataset, seed and request-owned generation")
    else:
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
    if value < contract["threshold"]:
        raise ValueError("candidate score is below the frozen threshold")
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
    if cfg.get("reference_protocol") != contract.get("reference_protocol"):
        raise ValueError("run configuration differs from the contracted reference protocol")
    if refs["task_provenance"]["sha256"] != contract["task_provenance"]["sha256"]:
        raise ValueError("run task provenance differs from the frozen contract")
    provenance = read_json(paths["task_provenance"])
    validate_provenance(provenance, cfg)
    inspect_evaluator(paths["evaluation_inspect"])
    validate_sample_file(paths["samples"], 198, contract["expected_doc_ids"],
                         expected_filters=task_filters(provenance["task_config"]),
                         enforce_output_health=False)
    verify_result_provenance(paths["results"], paths["samples"], cfg, provenance)
    score = score_check(paths["results"], contract)
    return record, service, score


def issue_gate(record_path, output, health_path=None):
    record, service, score = verify_run(record_path)
    gate = {"schema_version": 3, "passed": True, "score": score,
            "threshold": read_json(checked_artifact(record["artifacts"]["contract"]))["threshold"],
            "criterion": "score_greater_than_or_equal_to_threshold",
            "service_sha256": record["artifacts"]["service"]["sha256"],
            "run_record": artifact(record_path)}
    if health_path is not None:
        gate["health_observation"] = artifact(health_path)
    write_new(output, gate)
    return gate


def stable_service_identity(service):
    """Only process-instance evidence may change; even endpoint changes fail closed."""
    validate_service(service)
    context = service.get("performance_context", {})
    require_text(context, ("platform", "device_model", "driver_version", "device_runtime_version", "image_id"))
    devices = context.get("device_ids")
    if (not isinstance(devices, list) or not devices or any(not isinstance(d, str) or not d for d in devices)
            or len(set(devices)) != len(devices)):
        raise ValueError("gate rebind requires observed device topology")
    if "api_pid" in service and (type(service["api_pid"]) is not int or service["api_pid"] <= 0):
        raise ValueError("api_pid must be a positive observed integer")
    if "runtime_evidence_files" in service:
        files = service["runtime_evidence_files"]
        if (not isinstance(files, dict) or not files
                or any(not isinstance(path, str) or not path or not isinstance(digest, str)
                       or not re.fullmatch(r"[0-9a-f]{64}", digest)
                       for path, digest in files.items())):
            raise ValueError("runtime_evidence_files requires a nonempty path/SHA-256 mapping")
        if service["runtime_evidence_sha256"] not in files.values():
            raise ValueError("runtime evidence mapping does not bind the service runtime SHA")
        # Evidence locations and API PID change on restart, but the evidence is
        # still consumed. Rehash both old and current manifests' references
        # before omitting these volatile fields from their stable identities.
        for path, digest in files.items():
            checked_artifact({"path": path, "sha256": digest})
    return {k: v for k, v in service.items() if k not in (
        "service_instance_id", "runtime_evidence_sha256", "api_pid", "runtime_evidence_files")}


def verify_rebind(source_gate_path, service_path, evidence_path):
    source = read_json(source_gate_path)
    if source.get("schema_version") != 3:
        raise ValueError("rebind must reference an original evaluated gate, not another rebind")
    record = read_json(checked_artifact(source["run_record"]))
    old_path = checked_artifact(record["artifacts"]["service"])
    check_gate(source_gate_path, old_path)
    old, current = read_json(old_path), read_json(service_path)
    identity = stable_service_identity(current)
    if identity != stable_service_identity(old):
        raise ValueError("rebind changes source/configuration/environment; a new formal evaluation is required")
    if current["service_instance_id"] == old["service_instance_id"]:
        raise ValueError("rebind requires a fresh service instance")
    evidence = read_json(evidence_path)
    if (evidence.get("schema_version") != 1 or evidence.get("source_service") != artifact(old_path)
            or evidence.get("current_service") != artifact(service_path)):
        raise ValueError("rebind evidence must bind both exact service manifests")
    runtime_path = checked_artifact(evidence["runtime_evidence"])
    if (sha256(runtime_path) != current["runtime_evidence_sha256"]
            or current["runtime_evidence_sha256"] == old["runtime_evidence_sha256"]):
        raise ValueError("rebind requires new SHA-bound runtime evidence")
    runtime = read_json(runtime_path)
    if (runtime.get("service_instance_id") != current["service_instance_id"]
            or runtime.get("stable_identity_sha256") != content_sha256(identity)
            or runtime.get("graph_capture_completed") is not True
            or type(runtime.get("graph_replays")) is not int or runtime["graph_replays"] < 2):
        raise ValueError("rebind runtime evidence lacks identity/capture/two replays")
    regression = read_json(checked_artifact(evidence["minimal_regression"]))
    if (regression.get("service_sha256") != sha256(service_path)
            or regression.get("status") != "passed"):
        raise ValueError("rebind requires passed minimal regression for the new instance")
    checked_artifact(regression["evidence"])
    return source


def rebind_gate(source_gate_path, service_path, evidence_path, output):
    refs = [artifact(path) for path in (source_gate_path, service_path, evidence_path)]
    source = verify_rebind(source_gate_path, service_path, evidence_path)
    for ref in refs:
        checked_artifact(ref)
    result = {"schema_version": 4, "kind": "accuracy_gate_rebind", "passed": True,
              "source_gate": refs[0], "rebind_evidence": refs[2],
              "service_sha256": refs[1]["sha256"], "score": source["score"],
              "threshold": source["threshold"], "criterion": source["criterion"],
              "evaluation_reused": True}
    write_new(output, result)
    return result


def tuning_cache_identity(service):
    """Only the observed FlagGems cache bytes are mutable, not its URL/policy."""
    identity = stable_service_identity(service)
    identity['service_instance_id'] = service['service_instance_id']
    launch = dict(identity['launch_config'])
    digest = launch.pop('flaggems_db_sha256', None)
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise ValueError('cache update requires an observed FlagGems DB SHA')
    if not isinstance(launch.get('environment'), dict):
        raise ValueError('cache update requires the observed cache URL environment')
    require_text(launch['environment'], ('FLAGGEMS_DB_URL',))
    identity['launch_config'] = launch
    return identity


def verify_cache_update(source_gate_path, service_path, evidence_path):
    """Explicit same-instance cache evolution; original verdict stays immutable."""
    source = read_json(source_gate_path)
    if source.get('schema_version') != 3:
        raise ValueError('cache update requires an original evaluated gate, not a chained binding')
    record = read_json(checked_artifact(source['run_record']))
    old_path = checked_artifact(record['artifacts']['service'])
    check_gate(source_gate_path, old_path)
    old, current = read_json(old_path), read_json(service_path)
    if tuning_cache_identity(old) != tuning_cache_identity(current):
        raise ValueError('cache update changes stable identity or service instance')
    evidence = read_json(evidence_path)
    if evidence.get('schema_version') != 1 or evidence.get('kind') != 'flaggems_tuning_cache_update':
        raise ValueError('missing explicit tuning cache update evidence')
    require_text(evidence, ('authorization',))
    if (evidence.get('source_service') != artifact(old_path)
            or evidence.get('current_service') != artifact(service_path)):
        raise ValueError('cache evidence must bind both exact manifests')
    before_runtime = checked_artifact(evidence['before_runtime'])
    current_runtime = checked_artifact(evidence['current_runtime'])
    if (sha256(before_runtime) != old['runtime_evidence_sha256']
            or sha256(current_runtime) != current['runtime_evidence_sha256']):
        raise ValueError('cache evidence runtime does not match the manifests')
    audit = read_json(checked_artifact(evidence['cache_audit']))
    expected = {
        'status': 'passed', 'kind': 'flaggems_autotune_cache',
        'service_instance_id': current['service_instance_id'],
        'cache_url': current['launch_config']['environment']['FLAGGEMS_DB_URL'],
        'before_sha256': old['launch_config']['flaggems_db_sha256'],
        'after_sha256': current['launch_config']['flaggems_db_sha256'],
        'stable_identity_sha256': content_sha256(tuning_cache_identity(current)),
        'cache_tables_only': True,
        'manual_reset_copy_or_policy_override': False,
    }
    if any(type(audit.get(k)) is not type(v) or audit[k] != v for k, v in expected.items()):
        raise ValueError('cache audit does not prove this exact observed transition')
    # The audit producer inspects the live service and actual cache schema/writer;
    # the verifier binds that evidence, rather than claiming hashes prove causality.
    checked_artifact(audit['inspection'])
    return source


def cache_update_gate(source_gate_path, service_path, evidence_path, output):
    refs = [artifact(p) for p in (source_gate_path, service_path, evidence_path)]
    source = verify_cache_update(source_gate_path, service_path, evidence_path)
    for ref in refs:
        checked_artifact(ref)
    result = {'schema_version': 5, 'kind': 'accuracy_gate_tuning_cache_update',
              'passed': True, 'source_gate': refs[0], 'cache_update_evidence': refs[2],
              'service_sha256': refs[1]['sha256'], 'evaluation_reused': True,
              **{k: source[k] for k in ('score', 'threshold', 'criterion')}}
    write_new(output, result)
    return result


def cache_restart_identity(service):
    """Restart identity with only the audited tuning DB bytes omitted."""
    identity = tuning_cache_identity(service)
    identity.pop('service_instance_id')
    return identity


def verify_cache_rebind(source_gate_path, service_path, evidence_path):
    """Explicit restart plus cache evolution; never chain or relax code/config."""
    source = read_json(source_gate_path)
    if source.get('schema_version') != 3:
        raise ValueError('cache rebind requires the original evaluated gate')
    record = read_json(checked_artifact(source['run_record']))
    old_path = checked_artifact(record['artifacts']['service'])
    check_gate(source_gate_path, old_path)
    old, current = read_json(old_path), read_json(service_path)
    identity = cache_restart_identity(current)
    if identity != cache_restart_identity(old):
        raise ValueError('cache rebind changes source/configuration/environment')
    if current['service_instance_id'] == old['service_instance_id']:
        raise ValueError('cache rebind requires a fresh instance; use cache-update otherwise')
    evidence = read_json(evidence_path)
    if (evidence.get('schema_version') != 1 or evidence.get('kind') != 'flaggems_cache_restart'
            or evidence.get('source_service') != artifact(old_path)
            or evidence.get('current_service') != artifact(service_path)):
        raise ValueError('cache rebind requires exact original/current manifests')
    require_text(evidence, ('authorization',))
    before = checked_artifact(evidence['before_runtime'])
    runtime_path = checked_artifact(evidence['current_runtime'])
    if (sha256(before) != old['runtime_evidence_sha256']
            or sha256(runtime_path) != current['runtime_evidence_sha256']
            or current['runtime_evidence_sha256'] == old['runtime_evidence_sha256']):
        raise ValueError('cache rebind runtime hashes differ from manifests')
    runtime = read_json(runtime_path)
    if (runtime.get('service_instance_id') != current['service_instance_id']
            or runtime.get('stable_identity_sha256') != content_sha256(identity)
            or runtime.get('graph_capture_completed') is not True
            or type(runtime.get('graph_replays')) is not int or runtime['graph_replays'] < 2):
        raise ValueError('cache rebind needs current identity/capture/two replays')
    # Recheck the raw observations supporting the producer's capture assertion.
    observations = read_json(checked_artifact(runtime['observations']))
    refs = observations.get('artifacts')
    if not isinstance(refs, list) or not refs:
        raise ValueError('cache rebind observations require raw evidence references')
    for ref in refs:
        checked_artifact(ref)
    regression = read_json(checked_artifact(evidence['minimal_regression']))
    if regression.get('status') != 'passed' or regression.get('service_sha256') != sha256(service_path):
        raise ValueError('cache rebind requires current passed minimal regression')
    checked_artifact(regression['evidence'])
    audit = read_json(checked_artifact(evidence['cache_audit']))
    expected = dict(status='passed', kind='flaggems_autotune_cache_restart',
        source_service_instance_id=old['service_instance_id'],
        service_instance_id=current['service_instance_id'],
        cache_url=current['launch_config']['environment']['FLAGGEMS_DB_URL'],
        before_sha256=old['launch_config']['flaggems_db_sha256'],
        after_sha256=current['launch_config']['flaggems_db_sha256'],
        stable_identity_sha256=content_sha256(identity), cache_tables_only=True,
        manual_reset_copy_or_policy_override=False)
    if any(type(audit.get(k)) is not type(v) or audit[k] != v for k, v in expected.items()):
        raise ValueError('cache rebind audit does not bind the observed transition')
    checked_artifact(audit['inspection'])
    # Missing historical DB bytes are an explicit provenance gap, not an
    # invented row-level equivalence proof. This receipt only reuses accuracy;
    # it never establishes performance cache comparability.
    if audit.get('historical_row_delta_available') is True:
        checked_artifact(audit['historical_row_delta'])
    elif audit.get('historical_row_delta_available') is False:
        require_text(audit, ('history_gap',))
    else:
        raise ValueError('cache rebind must disclose historical row-delta availability')
    return source


def cache_rebind_gate(source_gate_path, service_path, evidence_path, output):
    refs = [artifact(p) for p in (source_gate_path, service_path, evidence_path)]
    source = verify_cache_rebind(source_gate_path, service_path, evidence_path)
    for ref in refs:
        checked_artifact(ref)
    result = dict(schema_version=6, kind='accuracy_gate_cache_restart', passed=True,
        source_gate=refs[0], cache_rebind_evidence=refs[2], service_sha256=refs[1]['sha256'],
        evaluation_reused=True, **{k: source[k] for k in ('score', 'threshold', 'criterion')})
    write_new(output, result)
    return result


def check_gate(gate_path, service_path, model=None, host=None, port=None, tokenizer=None):
    gate = read_json(gate_path)
    if gate.get('schema_version') == 6:
        if (gate.get('kind') != 'accuracy_gate_cache_restart' or gate.get('passed') is not True
                or gate.get('evaluation_reused') is not True or gate.get('service_sha256') != sha256(service_path)):
            raise ValueError('invalid cache restart gate or changed current manifest')
        source = verify_cache_rebind(checked_artifact(gate['source_gate']), service_path,
                                    checked_artifact(gate['cache_rebind_evidence']))
        if any(gate.get(k) != source[k] for k in ('score', 'threshold', 'criterion')):
            raise ValueError('cache rebind changed the evaluated verdict')
        check_target(read_json(service_path), model, host, port, tokenizer)
        return gate
    if gate.get('schema_version') == 5:
        if (gate.get('kind') != 'accuracy_gate_tuning_cache_update' or gate.get('passed') is not True
                or gate.get('evaluation_reused') is not True or gate.get('service_sha256') != sha256(service_path)):
            raise ValueError('invalid cache update gate or changed current manifest')
        source = verify_cache_update(checked_artifact(gate['source_gate']), service_path,
                                     checked_artifact(gate['cache_update_evidence']))
        if any(gate.get(k) != source[k] for k in ('score', 'threshold', 'criterion')):
            raise ValueError('cache update changed the evaluated verdict')
        check_target(read_json(service_path), model, host, port, tokenizer)
        return gate
    if gate.get("schema_version") == 4:
        if (gate.get("kind") != "accuracy_gate_rebind" or gate.get("passed") is not True
                or gate.get("evaluation_reused") is not True or gate.get("service_sha256") != sha256(service_path)):
            raise ValueError("invalid rebind gate or changed current service")
        source = verify_rebind(checked_artifact(gate["source_gate"]), service_path,
                               checked_artifact(gate["rebind_evidence"]))
        if any(gate.get(k) != source[k] for k in ("score", "threshold", "criterion")):
            raise ValueError("rebind changed the evaluated verdict")
        service = read_json(service_path)
        check_target(service, model, host, port, tokenizer)
        return gate
    if gate.get("schema_version") != 3 or gate.get("passed") is not True:
        raise ValueError("not a formal acceptance record")
    if sha256(service_path) != gate.get("service_sha256"):
        raise ValueError("current service manifest differs from the evaluated service")
    record_path = checked_artifact(gate["run_record"])
    record, service, score = verify_run(record_path)
    contract = read_json(checked_artifact(record["artifacts"]["contract"]))
    if (record["artifacts"]["service"]["sha256"] != gate["service_sha256"]
            or score != gate.get("score") or contract["threshold"] != gate.get("threshold")
            or gate.get("criterion") != "score_greater_than_or_equal_to_threshold"):
        raise ValueError("gate does not match its run record")
    if "health_observation" in gate:
        checked_artifact(gate["health_observation"])
    check_target(service, model, host, port, tokenizer)
    return gate


def check_target(service, model=None, host=None, port=None, tokenizer=None):
    url = urlsplit(service["base_url"])
    if tokenizer is not None and tokenizer != service["tokenizer_path"]:
        raise ValueError("benchmark tokenizer differs from accepted tokenizer path")
    if model is not None and model != service["model_name"]:
        raise ValueError("benchmark model differs from accepted model")
    if host is not None and host != url.hostname:
        raise ValueError("benchmark host differs from accepted endpoint")
    if port is not None and port != (url.port or (443 if url.scheme == "https" else 80)):
        raise ValueError("benchmark port differs from accepted endpoint")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    issue = commands.add_parser("issue")
    issue.add_argument("--run-record", required=True, type=Path)
    issue.add_argument("--health-observation", type=Path,
                       help="optional diagnostic observation; never changes the threshold verdict")
    issue.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check")
    check.add_argument("--gate", required=True, type=Path)
    check.add_argument("--service-manifest", required=True, type=Path)
    rebind = commands.add_parser("rebind", help="reuse an evaluated gate only after verified identical-service restart")
    rebind.add_argument("--source-gate", required=True, type=Path)
    rebind.add_argument("--service-manifest", required=True, type=Path)
    rebind.add_argument("--evidence", required=True, type=Path)
    rebind.add_argument("--output", required=True, type=Path)
    cache = commands.add_parser('cache-update', help='explicit same-instance FlagGems tuning cache transition')
    cache.add_argument('--source-gate', required=True, type=Path)
    cache.add_argument('--service-manifest', required=True, type=Path)
    cache.add_argument('--evidence', required=True, type=Path)
    cache.add_argument('--output', required=True, type=Path)
    restart_cache = commands.add_parser('cache-rebind', help='explicit audited restart plus normal tuning-cache writes')
    for name in ('source-gate', 'service-manifest', 'evidence', 'output'):
        restart_cache.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "issue":
            issue_gate(args.run_record, args.output, args.health_observation)
        elif args.command == "rebind":
            rebind_gate(args.source_gate, args.service_manifest, args.evidence, args.output)
        elif args.command == 'cache-update':
            cache_update_gate(args.source_gate, args.service_manifest, args.evidence, args.output)
        elif args.command == 'cache-rebind':
            cache_rebind_gate(args.source_gate, args.service_manifest, args.evidence, args.output)
        else:
            check_gate(args.gate, args.service_manifest)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")
    print("PASS: formal accuracy acceptance verified")


if __name__ == "__main__":
    main()
