"""Frozen, finite vLLM serving experiments; no server lifecycle operations."""

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shlex
import shutil
from statistics import median
import subprocess
from urllib.parse import urlparse


def _native():
    spec = importlib.util.spec_from_file_location("plan_native_perf", Path(__file__).with_name("vllm_perf.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NATIVE = _native()
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite JSON value: {value}")))


def _object(value, allowed, required, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    if set(value) - set(allowed):
        raise ValueError(f"unknown {label} keys: {sorted(set(value) - set(allowed))}")
    if set(required) - set(value):
        raise ValueError(f"missing {label} keys: {sorted(set(required) - set(value))}")


def _number(value, label, minimum=0, integer=False, inclusive=False):
    if type(value) not in ((int,) if integer else (int, float)):
        raise ValueError(f"{label} must be {'an integer' if integer else 'a number'}")
    try:
        valid = math.isfinite(value) and (value >= minimum if inclusive else value > minimum)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{label} must be finite and {'>=' if inclusive else '>'} {minimum}")


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError(f"{label} must be nonempty text without control characters")


def _identifier(value, label):
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a safe 1-128 character identifier")


def normalize_plan(data):
    """Return the schema 1 effective plan; reject unsupported semantics early."""
    _object(data, ("schema_version", "target", "generation", "measurement", "cases"),
            ("schema_version", "target", "cases"), "plan")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported performance plan schema_version")
    target = dict(data["target"]) if isinstance(data["target"], dict) else data["target"]
    target_keys = ("model", "tokenizer", "host", "port", "endpoint")
    _object(target, (*target_keys, "trust_remote_code"), target_keys, "target")
    for key in ("model", "tokenizer", "host", "endpoint"):
        _text(target[key], f"target.{key}")
    if any(character in target["host"] for character in ("/", "@", "?", "#", " ", ":")):
        raise ValueError("target.host must be a plain hostname or IPv4 address (IPv6 is not supported by this runner)")
    _number(target["port"], "target.port", integer=True)
    if target["port"] > 65535:
        raise ValueError("target.port exceeds 65535")
    if target["endpoint"] != "/v1/completions":
        raise ValueError("this random generation backend supports only /v1/completions")
    target.setdefault("trust_remote_code", False)
    if type(target["trust_remote_code"]) is not bool:
        raise ValueError("target.trust_remote_code must be boolean")

    generation_defaults = {"seed": 42, "temperature": 0, "ignore_eos": True, "random_range_ratio": 0}
    generation = data.get("generation", {})
    _object(generation, generation_defaults, (), "generation")
    generation = {**generation_defaults, **generation}
    _number(generation["seed"], "generation.seed", integer=True, inclusive=True)
    _number(generation["temperature"], "generation.temperature", inclusive=True)
    if type(generation["ignore_eos"]) is not bool:
        raise ValueError("generation.ignore_eos must be boolean")
    if type(generation["random_range_ratio"]) not in (int, float) or generation["random_range_ratio"] != 0:
        raise ValueError("only random_range_ratio=0 is supported; token lengths must be controlled")

    measurement_defaults = {"warmup_rounds": 1, "measured_rounds": 3, "timeout_s": 3600,
                            "required_metrics": list(NATIVE.REQUIRED_PERFORMANCE_METRICS),
                            "slo": {}, "warmup_stability": None}
    measurement = data.get("measurement", {})
    _object(measurement, measurement_defaults, (), "measurement")
    measurement = {**measurement_defaults, **measurement}
    _number(measurement["warmup_rounds"], "measurement.warmup_rounds", integer=True)
    _number(measurement["measured_rounds"], "measurement.measured_rounds", integer=True)
    _number(measurement["timeout_s"], "measurement.timeout_s")
    required = measurement["required_metrics"]
    if (not isinstance(required, list) or not required or any(not isinstance(key, str) for key in required)
            or len(set(required)) != len(required) or set(required) - set(NATIVE.SUPPORTED_PERFORMANCE_METRICS)):
        raise ValueError("measurement.required_metrics must be a nonempty unique list of supported metric names")
    measurement["required_metrics"] = list(required)
    _object(measurement["slo"], ("ttft", "tpot", "e2el"), (), "measurement.slo")
    measurement["slo"] = dict(measurement["slo"])
    for key, value in measurement["slo"].items():
        _number(value, f"measurement.slo.{key}")
    if measurement["slo"]:
        if "request_goodput" not in required:
            measurement["required_metrics"].append("request_goodput")
    elif "request_goodput" in required:
        raise ValueError("request_goodput requires a nonempty measurement.slo")
    stability = measurement["warmup_stability"]
    if stability is not None:
        _object(stability, ("metric", "window", "max_relative_spread"),
                ("metric", "window", "max_relative_spread"), "measurement.warmup_stability")
        if stability["metric"] not in measurement["required_metrics"]:
            raise ValueError("warmup stability metric must appear in required_metrics")
        _number(stability["window"], "warmup_stability.window", minimum=2, inclusive=True, integer=True)
        if stability["window"] > measurement["warmup_rounds"]:
            raise ValueError("warmup stability window exceeds the fixed warmup budget")
        _number(stability["max_relative_spread"], "warmup_stability.max_relative_spread", inclusive=True)
        measurement["warmup_stability"] = dict(stability)

    if not isinstance(data["cases"], list) or not data["cases"]:
        raise ValueError("cases must be a nonempty list")
    cases, ids = [], set()
    for index, value in enumerate(data["cases"]):
        keys = ("id", "input_tokens", "output_tokens", "concurrency", "requests", "load_mode")
        _object(value, (*keys, "request_rate", "burstiness"), keys, f"cases[{index}]")
        case = {"request_rate": None, "burstiness": 1, **value}
        _identifier(case["id"], "case.id")
        if case["id"] in ids:
            raise ValueError(f"duplicate case id: {case['id']}")
        ids.add(case["id"])
        for key in ("input_tokens", "output_tokens", "concurrency", "requests"):
            _number(case[key], f"case.{key}", integer=True)
        if case["load_mode"] == "closed_loop":
            raise ValueError("closed_loop is unsupported: N finite requests at inf rate with a concurrency cap are a finite batch, not sustained closed-loop traffic")
        if case["load_mode"] not in ("finite_batch", "open_loop"):
            raise ValueError("case.load_mode must be finite_batch or open_loop")
        if case["load_mode"] == "finite_batch" and case["request_rate"] is not None:
            raise ValueError("finite_batch requires request_rate=null")
        if case["load_mode"] == "open_loop":
            _number(case["request_rate"], "open_loop.request_rate")
        _number(case["burstiness"], "case.burstiness")
        if case["output_tokens"] <= 1 and (any("_tpot_" in key or "_itl_" in key for key in required) or "tpot" in measurement["slo"]):
            raise ValueError("single-token output cannot require TPOT/ITL or a TPOT SLO")
        last_seed = round_seed(generation["seed"], case, measurement["warmup_rounds"] + measurement["measured_rounds"])
        if last_seed >= 2**32:
            raise ValueError("derived round seed exceeds the client's uint32 seed range")
        cases.append(case)
    return {"schema_version": 1, "target": target, "generation": generation,
            "measurement": measurement, "cases": cases}


def load_plan(path):
    return normalize_plan(read_json(path))


def round_seed(base_seed, case, round_id):
    return base_seed + case["input_tokens"] * 10 + case["concurrency"] * 1000 + round_id


def build_round_command(plan, case, seed, raw_path):
    target, generation, measurement = plan["target"], plan["generation"], plan["measurement"]
    cmd = ["vllm", "bench", "serve", "--backend", "vllm", "--model", target["model"],
           "--tokenizer", target["tokenizer"], "--host", target["host"], "--port", str(target["port"]),
           "--endpoint", target["endpoint"], "--dataset-name", "random", "--seed", str(seed),
           "--temperature", str(generation["temperature"]), "--random-range-ratio", "0",
           "--random-input-len", str(case["input_tokens"]), "--random-output-len", str(case["output_tokens"]),
           "--max-concurrency", str(case["concurrency"]), "--num-prompts", str(case["requests"]),
           "--request-rate", "inf" if case["load_mode"] == "finite_batch" else str(case["request_rate"]),
           "--burstiness", str(case["burstiness"]), "--save-result", "--save-detailed",
           "--result-dir", str(Path(raw_path).parent), "--result-filename", Path(raw_path).name]
    if generation["ignore_eos"]:
        cmd.append("--ignore-eos")
    if target["trust_remote_code"]:
        cmd.append("--trust-remote-code")
    # Ask the native client to calculate the requested summaries from its own
    # request observations; do not reconstruct TPOT/E2EL from streaming chunks.
    latency = [key for key in measurement["required_metrics"] if key.endswith("_ms")]
    names = sorted({key.split("_")[1] for key in latency})
    percentiles = sorted({int(key.split("_")[0][1:]) for key in latency if key.startswith("p")})
    if names:
        cmd += ["--percentile-metrics", ",".join(names), "--metric-percentiles", ",".join(map(str, percentiles or [99]))]
    if measurement["slo"]:
        cmd += ["--goodput", *(f"{key}:{value}" for key, value in sorted(measurement["slo"].items()))]
    return cmd


def validate_native_configuration(plan, case, raw):
    """Check metadata emitted by the v0.11/v0.12 generation result schemas.

    The native result does not attest the server's loaded weights or expose all
    sampling settings. Those remain bound by the service record and command.
    """
    expected = {"model_id": plan["target"]["model"], "tokenizer_id": plan["target"]["tokenizer"],
                "backend": "vllm", "max_concurrency": case["concurrency"],
                "request_rate": "inf" if case["load_mode"] == "finite_batch" else case["request_rate"],
                "burstiness": case["burstiness"]}
    errors = []
    for key, value in expected.items():
        actual = raw.get(key)
        valid_type = type(actual) in (int, float) if type(value) in (int, float) else type(actual) is str
        if key == "max_concurrency":
            valid_type = type(actual) is int
        if not valid_type or actual != value:
            errors.append(f"native {key} differs from frozen plan: expected {value!r}, got {actual!r}")
    lengths = raw.get("input_lens")
    if (not isinstance(lengths, list) or len(lengths) != case["requests"]
            or any(type(length) is not int or length != case["input_tokens"] for length in lengths)):
        errors.append("native input_lens differs from the fixed per-request input length")
    return errors


def artifact(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    return artifact(path)


def _check_refs(refs):
    for ref in refs:
        if artifact(ref["path"])["sha256"] != ref["sha256"]:
            raise ValueError(f"input/artifact SHA changed during run: {ref['path']}")


def _check_service(service, target):
    if not isinstance(service, dict):
        raise ValueError("service manifest must be an object")
    for key in ("model_name", "tokenizer_path", "service_instance_id", "base_url"):
        _text(service.get(key), f"service.{key}")
    url = urlparse(service["base_url"])
    if (url.scheme != "http" or url.username or url.password or url.query or url.fragment
            or url.hostname != target["host"] or (url.port or 80) != target["port"]
            or url.path not in ("/v1/completions", "/v1/chat/completions")):
        raise ValueError("service base_url must match the target HTTP origin and a supported completion endpoint")
    if service["model_name"] != target["model"] or service["tokenizer_path"] != target["tokenizer"]:
        raise ValueError("service model/tokenizer differs from performance target")


def _gate_check(gate_path, service_path, target):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "accuracy"))
    from acceptance import check_gate
    check_gate(gate_path, service_path, model=target["model"], host=target["host"],
               port=target["port"], tokenizer=target["tokenizer"])


# Execute in the console script's interpreter, not the controller's Python.
# Limit source identity to vLLM benchmark/CLI code; this is not an environment
# lockfile or an attestation of third-party dependencies and remote services.
RUNTIME_PROBE = '''import hashlib, importlib.metadata, importlib.util, json, pathlib, sys
spec = importlib.util.find_spec("vllm")
roots = list(spec.submodule_search_locations or []) if spec else []
if len(roots) != 1: raise RuntimeError("expected one installed vllm package root")
root = pathlib.Path(roots[0]).resolve()
files = set((root / "benchmarks").rglob("*.py")) | set((root / "entrypoints" / "cli").rglob("*.py"))
if not (root / "benchmarks" / "serve.py") in files: raise RuntimeError("vllm benchmark source is unavailable")
def ref(path):
    path = path.resolve()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
print(json.dumps({"python_invocation": sys.argv[1],
                  "python_executable": ref(pathlib.Path(sys.executable)), "python_version": " ".join(sys.version.split()),
                  "vllm_version": importlib.metadata.version("vllm"),
                  "source_files": [ref(p) for p in sorted(files)]}, sort_keys=True))
'''


def runtime_command(executable):
    with Path(executable).open("rb") as stream:
        line = stream.readline(4096).decode("utf-8").strip()
    if not line.startswith("#!"):
        raise ValueError("vllm launcher must be a Python console script to bind benchmark sources")
    parts = shlex.split(line[2:])
    if parts and Path(parts[0]).name == "env" and len(parts) == 2:
        interpreter = shutil.which(parts[1])
        parts = [interpreter] if interpreter else []
    if len(parts) != 1 or not re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", Path(parts[0]).name):
        raise ValueError("unsupported vllm launcher interpreter; use a direct Python console script")
    # Keep a virtualenv's symlink path: resolving it can switch sys.prefix and
    # load a different installation even when the interpreter bytes are equal.
    invocation = str(Path(parts[0]).absolute())
    return [invocation, "-c", RUNTIME_PROBE, invocation]


def _probe(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    output = result.stdout + "\n" + result.stderr
    return {"command": command, "returncode": result.returncode,
            "output_sha256": hashlib.sha256(output.encode()).hexdigest(), "output": output}


def runtime_from_probe(probe):
    # The isolated Python probe emits exactly one JSON object. Startup logs or
    # unsupported source layouts are explicit diagnostic failures.
    if type(probe.get("returncode")) is not int or probe["returncode"] != 0:
        raise ValueError("client runtime probe failed")
    value = json.loads(probe["output"])
    keys = ("python_invocation", "python_executable", "python_version", "vllm_version", "source_files")
    _object(value, keys, keys, "client.runtime")
    if not isinstance(value["python_invocation"], str) or not Path(value["python_invocation"]).is_absolute():
        raise ValueError("client runtime Python invocation must be absolute")
    for key in ("python_version", "vllm_version"):
        _text(value[key], f"client.runtime.{key}")
    files = value["source_files"]
    if not isinstance(files, list) or not files:
        raise ValueError("client runtime source fingerprints are missing")
    paths = []
    for ref in [value["python_executable"], *files]:
        _object(ref, ("path", "sha256"), ("path", "sha256"), "client runtime fingerprint")
        if (not isinstance(ref["path"], str) or not Path(ref["path"]).is_absolute()
                or not isinstance(ref["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"])):
            raise ValueError("invalid client runtime fingerprint")
        paths.append(ref["path"])
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate client runtime fingerprint")
    if not any(path.endswith("/benchmarks/serve.py") for path in paths):
        raise ValueError("client runtime lacks benchmark serve.py fingerprint")
    return value


def inspect_client(commands):
    executable = shutil.which("vllm")
    required = sorted({argument for command in commands for argument in command if argument.startswith("--")})
    report = {"schema_version": 1, "executable": executable, "executable_sha256": None, "version": None,
              "required_flags": required, "supported_flags": [], "probes": {}}
    errors = []
    if not executable:
        return report, ["vllm executable not found; no requests were sent"]
    try:
        report["executable_sha256"] = artifact(executable)["sha256"]
    except OSError as exc:
        return report, [f"cannot fingerprint vllm executable: {exc}"]
    try:
        runtime_probe = _probe(runtime_command(executable))
        report["probes"]["runtime"] = runtime_probe
        report["runtime"] = runtime_from_probe(runtime_probe)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        errors.append(f"cannot bind benchmark runtime sources: {exc}")
    for name, command in (("version", [executable, "--version"]),
                          ("help", [executable, "bench", "serve", "--help=all"])):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            output = result.stdout + "\n" + result.stderr
            report["probes"][name] = {"command": command, "returncode": result.returncode,
                                      "output_sha256": hashlib.sha256(output.encode()).hexdigest(), "output": output}
            if result.returncode != 0:
                errors.append(f"client {name} probe failed with status {result.returncode}")
            if name == "version":
                versions = re.findall(r"(?m)^\s*v?(\d+\.\d+\.\d+[^\s]*)\s*$", output)
                if versions:
                    report["version"] = versions[-1]
                else:
                    errors.append("client version probe did not report an identifiable version")
            else:
                report["supported_flags"] = sorted(set(re.findall(r"--[a-z][a-z0-9-]*", output)))
                # Help can contain timestamped import logs or generated default
                # request IDs. Its original text/SHA stays in probe evidence;
                # stable client identity compares executable/version/flags.
        except (OSError, subprocess.TimeoutExpired) as exc:
            report["probes"][name] = {"command": command, "returncode": None, "error": str(exc)}
            errors.append(f"client {name} probe failed: {exc}")
    missing = set(required) - set(report["supported_flags"])
    if missing:
        errors.append(f"client CLI lacks required capabilities: {sorted(missing)}")
    if report.get("runtime") and report["version"] != report["runtime"]["vllm_version"]:
        errors.append("client CLI version differs from its Python package version")
    return report, errors


def _warmup_check(values, config):
    if config is None:
        return {"status": "not_checked", "reason": "fixed warmup rounds do not establish steady state"}
    values = values[-config["window"]:]
    center = median(values)
    spread = (max(values) - min(values)) / center if center > 0 and math.isfinite(center) else None
    passed = spread is not None and math.isfinite(spread) and spread <= config["max_relative_spread"]
    return {"status": "passed" if passed else "failed", "metric": config["metric"],
            "values": values, "relative_spread": spread, "max_relative_spread": config["max_relative_spread"]}


def execute_plan(args):
    """Freeze inputs and persist all completed/failed rounds; return run-record path."""
    _identifier(args.run_id, "run_id")
    source_refs = {"plan": artifact(args.config), "service": artifact(args.service_manifest)}
    plan = load_plan(args.config)
    _check_service(read_json(args.service_manifest), plan["target"])
    scope = args.scope
    if args.accuracy_gate:
        if args.role != "candidate" or scope == "performance_only":
            raise ValueError("accuracy gate is only valid for a candidate and cannot be combined with performance_only")
        source_refs["accuracy_gate"] = artifact(args.accuracy_gate)
        _gate_check(args.accuracy_gate, args.service_manifest, plan["target"])
        scope = "formal_candidate"
    if args.comparison_contract:
        source_refs["comparison_contract"] = artifact(args.comparison_contract)
    _check_refs(source_refs.values())

    directory = Path(args.output_dir).resolve() / args.run_id
    commands = []
    for case in plan["cases"]:
        for round_id in range(1, plan["measurement"]["warmup_rounds"] + plan["measurement"]["measured_rounds"] + 1):
            seed = round_seed(plan["generation"]["seed"], case, round_id)
            commands.append({"case_id": case["id"], "round_id": round_id,
                             "phase": "warmup" if round_id <= plan["measurement"]["warmup_rounds"] else "measured",
                             "seed": seed, "command": build_round_command(plan, case, seed, directory / f"{case['id']}-r{round_id}.json")})
    if args.dry_run:
        print(json.dumps({"scope": scope, "effective_plan": plan, "input_artifacts": source_refs,
                          "run_record": str(directory / "run-record.json"), "commands": commands}, ensure_ascii=False, indent=2))
        return None
    directory.mkdir(parents=True, exist_ok=False)
    record = {"schema_version": 1, "kind": "performance_run", "role": args.role,
              "run_id": args.run_id, "status": "failed", "scope": scope,
              "artifacts": {}, "input_artifacts": source_refs, "rounds": [], "errors": [],
              "warmup_check": {}, "inputs_verified_before": True, "inputs_verified_after": False}
    record_path = directory / "run-record.json"
    all_refs = [*source_refs.values()]
    try:
        record["artifacts"]["plan"] = _write_new(directory / "effective-plan.json", plan)
        for name, ref in source_refs.items():
            if name == "plan":
                continue
            destination = directory / f"{name}.json"
            with destination.open("xb") as handle:
                handle.write(Path(ref["path"]).read_bytes())
            record["artifacts"][name] = artifact(destination)
            if record["artifacts"][name]["sha256"] != ref["sha256"]:
                raise ValueError(f"{name} input changed before snapshot")
        client, client_errors = inspect_client([entry["command"] for entry in commands])
        client = dict(client)
        record["artifacts"]["client_probes"] = _write_new(directory / "client-probes.json", client.pop("probes", {}))
        record["artifacts"]["client"] = _write_new(directory / "client.json", client)
        record["errors"].extend(client_errors)
        if client_errors:
            raise ValueError("client capability preflight failed; no requests were sent")
        all_refs = [*source_refs.values(), *record["artifacts"].values()]
        if client.get("executable_sha256"):
            all_refs.append({"path": client["executable"], "sha256": client["executable_sha256"]})
        if client.get("runtime"):
            all_refs.extend([client["runtime"]["python_executable"], *client["runtime"]["source_files"]])
        for case in plan["cases"]:
            warmup_values = []
            for entry in (item for item in commands if item["case_id"] == case["id"]):
                _check_refs(all_refs)
                command = entry["command"]
                if shutil.which("vllm") != client["executable"]:
                    raise ValueError("vllm executable changed after client preflight")
                if client.get("executable_sha256") and artifact(client["executable"])["sha256"] != client["executable_sha256"]:
                    raise ValueError("vllm executable contents changed after client preflight")
                raw_path = directory / command[command.index("--result-filename") + 1]
                if raw_path.exists():
                    raise ValueError(f"refusing to overwrite raw result: {raw_path}")
                stdout, stderr, returncode, execution_error = "", "", None, None
                try:
                    process = subprocess.run(command, capture_output=True, text=True, timeout=plan["measurement"]["timeout_s"])
                    stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
                except subprocess.TimeoutExpired as exc:
                    stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
                    stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr or ""
                    returncode, execution_error = 124, f"benchmark exceeded timeout_s={plan['measurement']['timeout_s']}"
                except OSError as exc:
                    returncode, execution_error = 127, str(exc)
                except KeyboardInterrupt:
                    returncode, execution_error = 130, "benchmark interrupted; partial pipe output unavailable"
                stdout_metrics = NATIVE.extract_metrics(stdout)
                raw_ref, raw, read_error = None, {}, None
                try:
                    raw_ref = artifact(raw_path)
                    raw = read_json(raw_path)
                    if not isinstance(raw, dict):
                        raise ValueError("native benchmark result is not an object")
                except (OSError, ValueError) as exc:
                    raw, read_error = {}, str(exc)
                metrics, validation = NATIVE.validate_native_result(
                    (case["input_tokens"], case["output_tokens"], case["concurrency"], case["requests"]), raw,
                    stdout_metrics, required_metrics=plan["measurement"]["required_metrics"],
                    ignore_eos=plan["generation"]["ignore_eos"], slo=plan["measurement"]["slo"])
                validation["errors"].extend(validate_native_configuration(plan, case, raw))
                validation.update({"command": command, "stdout_metrics": stdout_metrics,
                                   "returncode": returncode, "raw_result": str(raw_path), "raw_error": read_error})
                for error in (execution_error, read_error, f"benchmark exited with status {returncode}" if returncode != 0 else None):
                    if error:
                        validation["errors"].append(error)
                validation["valid"] = not validation["errors"]
                log_path = directory / f"{case['id']}-r{entry['round_id']}.output.json"
                validation["output"] = _write_new(log_path, {"stdout": stdout, "stderr": stderr})
                validation_ref = _write_new(raw_path.with_suffix(".validation.json"), validation)
                record["rounds"].append({key: entry[key] for key in ("case_id", "round_id", "phase", "seed")}
                                        | {"returncode": returncode, "raw_result": raw_ref, "validation": validation_ref})
                all_refs.extend(ref for ref in (raw_ref, validation_ref, validation["output"]) if ref is not None)
                if not validation["valid"]:
                    raise ValueError(f"case {case['id']} round {entry['round_id']} failed native validation")
                stability = plan["measurement"]["warmup_stability"]
                if entry["phase"] == "warmup" and stability:
                    warmup_values.append(metrics[stability["metric"]])
                if entry["round_id"] == plan["measurement"]["warmup_rounds"]:
                    check = _warmup_check(warmup_values, stability)
                    record["warmup_check"][case["id"]] = check
                    if check["status"] == "failed":
                        raise ValueError(f"case {case['id']} did not stabilize within the fixed warmup budget")
        _check_refs(all_refs)
        if client.get("runtime") and runtime_from_probe(_probe(runtime_command(client["executable"]))) != client["runtime"]:
            raise ValueError("benchmark runtime source set changed during the run")
        if args.accuracy_gate:
            _gate_check(args.accuracy_gate, args.service_manifest, plan["target"])
        record["inputs_verified_after"] = True
        record["status"] = "complete"
    except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        record["errors"].append(str(exc))
    finally:
        try:
            _check_refs([*all_refs, *record["artifacts"].values()])
            record["inputs_verified_after"] = True
        except (OSError, ValueError) as exc:
            record["status"] = "failed"
            record["inputs_verified_after"] = False
            record["errors"].append(str(exc))
        _write_new(record_path, record)
    return record_path
