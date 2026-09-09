#!/usr/bin/env python3
"""Run the original formal runner with explicit configuration and frozen evidence."""
import argparse
import importlib.metadata
import importlib.util
import inspect
import json
import random
import sys
import uuid
from pathlib import Path

from acceptance import (
    TASK, RUNNER_SHA256, artifact, checked_artifact, content_sha256, inspect_evaluator,
    model_args_text, read_json, sha256,
    validate_config, validate_config_integers, validate_contract, validate_provenance,
    validate_service, verify_run_record, write_new,
)
from sample_validation import task_filters, validate_sample_file

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "test/Accuracy_test/llmrun.py"


def load_runner():
    if sha256(RUNNER) != RUNNER_SHA256:
        raise ValueError("formal runner hash differs from the imported baseline")
    spec = importlib.util.spec_from_file_location("original_formal_runner", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def source_tree(path):
    """Fingerprint source/task resources, excluding bytecode and VCS metadata."""
    path = Path(path).resolve()
    files = [path] if path.is_file() else sorted(path.rglob("*"))
    entries = {}
    for item in files:
        if not item.is_file() or any(part in ("__pycache__", ".git") for part in item.relative_to(path.parent if path.is_file() else path).parts):
            continue
        if item.suffix in (".pyc", ".pyo"):
            continue
        name = item.name if path.is_file() else str(item.relative_to(path))
        entries[name] = sha256(item)
    if not entries:
        raise ValueError(f"no evaluator/task source files found at {path}")
    return {"path": str(path), "sha256": content_sha256(entries)}


def task_snapshot(task, cfg, generation_overrides, sources, versions):
    """Collect raw split and processed eval docs, without building model requests.

    The adapter follows TaskManager/ConfigurableTask and evaluator overrides in
    lm-evaluation-harness v0.4.9. Unsupported custom classes/schemas must not pass
    merely because they expose a task name or a manually supplied revision.
    """
    if task.get_config("output_type") != "generate_until":
        raise ValueError("unsupported task output type; expected generate_until")
    task.set_config(key="generation_kwargs", value=generation_overrides, update=True)
    if task.get_config("num_fewshot") is None:
        task.set_config(key="num_fewshot", value=0)
    task.set_fewshot_seed(seed=cfg["seed"])
    task_config = task.dump_config()
    # Native results dump this exact configuration, including function source.
    # Opaque object reprs containing addresses cannot be compared across runs.
    serialized = json.dumps(task_config, sort_keys=True, ensure_ascii=False, allow_nan=False)
    if " at 0x" in serialized:
        raise ValueError("task configuration contains an unstable callable/object representation")
    task_config = json.loads(serialized)
    split = task_config.get("test_split") or task_config.get("validation_split")
    if (task_config.get("dataset_path") != cfg["dataset_path"]
            or task_config.get("dataset_name") != cfg["dataset_name"]
            or split != cfg["dataset_split"]):
        raise ValueError("resolved lm-eval task dataset path/name/split differs from case config; no automatic remapping")
    raw_docs = list(task.dataset[split])
    eval_docs = list(task.eval_docs)
    if len(raw_docs) != 198 or len(eval_docs) != 198:
        raise ValueError("resolved raw split and processed eval_docs must both contain 198 documents")
    raw_hashes = [content_sha256(doc) for doc in raw_docs]
    snapshot = {
        "schema_version": 1, "adapter": "lm-eval-configurable-task-v1", "task": TASK,
        "dataset_revision": "content-sha256:" + content_sha256(raw_hashes),
        "raw_doc_sha256": raw_hashes,
        "eval_doc_sha256": [content_sha256(doc) for doc in eval_docs],
        "task_config": task_config, "generation_overrides": generation_overrides,
        "sources": sources, **versions,
        **{key: cfg.get(key, "" if key == "include_path" else None) for key in (
            "dataset_path", "dataset_name", "dataset_split", "seed", "gen_kwargs", "include_path")},
    }
    validate_provenance(snapshot, cfg)
    return snapshot


def resolve_task(cfg, task_manager, get_task_dict, configurable_task, parse_args):
    """Use the same TaskManager inputs as the fixed lm-eval CLI.

    v0.4.9 __main__.cli_evaluate merges parsed model_args into task metadata.
    Omitting that merge produces a different config (and can change custom
    dataset loading), even when model/endpoint are checked separately.
    """
    manager = task_manager(include_path=cfg.get("include_path") or None,
                           metadata=parse_args(model_args_text(cfg)))
    if TASK not in manager.all_tasks:
        raise ValueError(f"required task {TASK!r} is not registered; use the verified evaluation image/task definitions, not a similarly named substitute")
    tasks = get_task_dict([TASK], manager)
    if set(tasks) != {TASK} or type(tasks[TASK]) is not configurable_task:
        raise ValueError("unsupported task class/group; provenance adapter supports one ConfigurableTask")
    return tasks[TASK]


def collect_provenance(cfg):
    # These imports and task loading happen in the evaluation environment only.
    # They do not instantiate an LM, probe its endpoint or request generations.
    try:
        import lm_eval
        import numpy as np
        import torch
        from lm_eval.api.task import ConfigurableTask
        from lm_eval.tasks import TaskManager, get_task_dict
        from lm_eval.utils import simple_parse_args_string
        random.seed(cfg["seed"])
        np.random.seed(cfg["seed"])
        torch.manual_seed(cfg["seed"])
        task = resolve_task(cfg, TaskManager, get_task_dict, ConfigurableTask, simple_parse_args_string)
        sources = {"lm_eval": source_tree(Path(lm_eval.__file__).parent)}
        if cfg.get("include_path"):
            sources["include_path"] = source_tree(cfg["include_path"])
        # Include custom callable modules outside the lm_eval/include trees.
        def collect_callables(value):
            if isinstance(value, dict):
                for item in value.values():
                    collect_callables(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    collect_callables(item)
            elif callable(value):
                source = inspect.getsourcefile(value)
                if not source:
                    raise ValueError("task callable has no inspectable source")
                sources[str(Path(source).resolve())] = source_tree(source)
        collect_callables(vars(task.config))
        versions = {"lm_eval_version": importlib.metadata.version("lm_eval"),
                    "datasets_version": importlib.metadata.version("datasets")}
        return task_snapshot(task, cfg, simple_parse_args_string(cfg["gen_kwargs"]), sources, versions)
    except (ImportError, AttributeError, TypeError, KeyError) as exc:
        raise ValueError(f"unsupported evaluation environment/task provenance API: {exc}") from exc


def run(args):
    runner = load_runner()
    # The baseline loader uses int(), which silently turns a fractional limit
    # such as 0.9 into the full-evaluation sentinel 0 and accepts bool as int.
    # Check the user's values before that normalization or any external work.
    validate_config_integers(read_json(args.config.resolve()))
    cfg = runner.load_config(args.config.resolve())
    inspect_evaluator(args.evaluation_inspect)
    validate_config(cfg, {"model_name": cfg["model_name"], "base_url": cfg["base_url"]})
    runner.configure_environment(cfg)
    provenance = collect_provenance(cfg)
    if getattr(args, "capture_provenance", None):
        write_new(args.capture_provenance, provenance)
        print(f"Task/data provenance collected without model requests: {args.capture_provenance}")
        print(f"dataset_revision={provenance['dataset_revision']}")
        print(f"task_provenance={json.dumps(artifact(args.capture_provenance))}")
        return
    service = read_json(args.service_manifest)
    contract = read_json(args.contract)
    validate_service(service)
    validate_contract(contract)
    validate_config(cfg, service)
    provenance_path = checked_artifact(contract["task_provenance"])
    if provenance != read_json(provenance_path):
        raise ValueError("current evaluator/task/dataset differs from the pre-frozen provenance")
    if args.config.resolve() == (RUNNER.parent / "llm_config.json").resolve():
        raise ValueError("use a case-specific config, not the imported example")
    frozen = {name: artifact(path) for name, path in (
        ("contract", args.contract), ("service", args.service_manifest),
        ("runner", RUNNER), ("evaluation_inspect", args.evaluation_inspect),
        ("task_provenance", provenance_path)
    )}
    healthy, detail = runner.probe_service(cfg)
    if not healthy:
        raise ValueError(f"model service preflight failed: {detail}")
    if args.preflight_only:
        print("Preflight passed; no evaluation was started")
        return

    # Always use a fresh response cache namespace; original retry behavior within
    # this run remains intact. A new service/candidate must start a new run.
    cfg["run_id"] = uuid.uuid4().hex
    run_dir = runner.create_run_dir(cfg)
    frozen["config"] = artifact(run_dir / "effective_config.json")
    write_new(run_dir / "frozen-inputs.json", frozen)
    original_build = runner.build_command

    def build_command(config, task, task_dir):
        command = original_build(config, task, task_dir)
        # Use the interpreter whose evaluator/task sources were collected,
        # not a potentially different `lm_eval` console script on PATH.
        if command[0] != "lm_eval":
            raise ValueError("unexpected original runner executable")
        return [sys.executable, "-m", "lm_eval", *command[1:], "--seed", str(config["seed"])]

    def validate_samples(config, task, task_dir):
        samples = runner.newest_samples(task, task_dir)
        try:
            if samples is None:
                raise ValueError("samples file is missing")
            validate_sample_file(samples, 198, contract["expected_doc_ids"],
                                 expected_filters=task_filters(provenance["task_config"]))
            return True
        except (ValueError, OSError, TypeError) as exc:
            runner.log("ERROR", str(exc))
            return False

    # Keep the imported model API, task and generation implementation unchanged.
    # Pin the interpreter/seed and strengthen provenance/acceptance checks.
    runner.build_command = build_command
    runner.validate_samples = validate_samples
    succeeded = runner.run_task(cfg, TASK, run_dir)
    if collect_provenance(cfg) != provenance:
        raise ValueError("evaluator/task/dataset changed during evaluation")
    for ref in frozen.values():
        checked_artifact(ref)
    if not succeeded:
        raise ValueError(f"formal process/result validation failed; artifacts: {run_dir}")
    task_dir = run_dir / TASK
    results = list(task_dir.rglob("results_*.json"))
    samples = list(task_dir.rglob(f"samples_{TASK}_*.jsonl"))
    if len(results) != 1 or len(samples) != 1:
        raise ValueError("ambiguous output pair; start a new run rather than choosing the best result")
    frozen.update(results=artifact(results[0]), samples=artifact(samples[0]))
    record_path = run_dir / "run-record.json"
    record = {"schema_version": 2, "status": "evaluated",
              "process_succeeded": True, "artifacts": frozen}
    verify_run_record(record)
    write_new(record_path, record)
    write_new(run_dir / "health-review.template.json", {
        "samples_sha256": frozen["samples"]["sha256"], "reviewer": "", "method": "",
        "empty_outputs": "pending", "truncation": "pending",
        "abnormal_repetition": "pending", "garbled_output": "pending", "timeouts": "pending",
    })
    print(f"Score and sample structure passed: {record_path}")
    print("Complete the output health review, then use acceptance.py issue; formal acceptance remains pending.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--service-manifest", type=Path)
    parser.add_argument("--evaluation-inspect", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--capture-provenance", type=Path,
                        help="Collect actual evaluator/task/data evidence only; no model requests. Freeze this artifact in the contract.")
    args = parser.parse_args()
    if args.capture_provenance:
        if args.preflight_only or args.contract or args.service_manifest:
            parser.error("--capture-provenance is separate from service preflight/evaluation")
    elif not args.contract or not args.service_manifest:
        parser.error("evaluation/preflight requires --contract and --service-manifest")
    try:
        run(args)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
