#!/usr/bin/env python3
"""Recheck frozen vLLM run evidence and decide a bounded performance comparison.

This consumes artifacts; it never starts/stops a service. A passed comparison
applies to the measured workloads, not to sustained production capacity.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import statistics
import sys
from urllib.parse import urlsplit

import performance_plan
import vllm_perf


ROLES = ("baseline", "candidate", "revert")
VOLATILE_SERVICE_FIELDS = {"service_instance_id", "runtime_evidence_sha256", "base_url"}
VARIABLE_ROOTS = {"plugin_sha256", "flaggems_sha256", "launch_config", "mode"}
CACHE_VARIABLE_PATHS = {"/performance_context/prefix_cache_state", "/performance_context/cache_preparation"}


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError(f"nonfinite JSON number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=nonfinite)


def artifact(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "sha256": digest.hexdigest()}


def checked(ref):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        raise ValueError("missing artifact path/SHA")
    if artifact(ref["path"]) != ref:
        raise ValueError(f"artifact missing, relocated or changed: {ref.get('path')}")
    return Path(ref["path"])


def number(value, label, minimum=0, maximum=None):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= minimum
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{label} must be a finite number >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return value


def fields(value, allowed, required, label):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        raise ValueError(f"{label}: missing or unknown fields")


def validate_contract(value):
    fields(value, ("schema_version", "scope", "hypothesis", "variable_paths", "primary",
                   "guardrails", "repeats", "slo_min_attainment"),
           ("schema_version", "scope", "hypothesis", "variable_paths", "primary", "guardrails", "repeats"), "contract")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["scope"] not in ("formal", "performance_only"):
        raise ValueError("comparison requires schema 1 and an explicit acceptance scope")
    if not isinstance(value["hypothesis"], str) or not value["hypothesis"].strip():
        raise ValueError("describe the one primary optimization hypothesis")
    paths = value["variable_paths"]
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths):
        raise ValueError("variable_paths must identify concrete service manifest fields")
    if len(set(paths)) != len(paths):
        raise ValueError("duplicate variable paths")
    for path in paths:
        parts = path.split("/")[1:]
        if not path.startswith("/") or not parts or any(not p or p in ("*", ".", "..") or "~" in p for p in parts):
            raise ValueError("use concrete JSON pointer paths; wildcard/escape paths are unsupported")
        if path not in CACHE_VARIABLE_PATHS and (parts[0] not in VARIABLE_ROOTS or (parts[0] == "launch_config" and len(parts) < 2)):
            raise ValueError("variable must be Plugin/FlagGems content, execution mode or a specific launch setting")
    primary = value["primary"]
    fields(primary, ("metric", "direction", "min_improvement"), ("metric", "direction", "min_improvement"), "primary")
    validate_metric(primary)
    number(primary["min_improvement"], "min_improvement", maximum=1)
    if not isinstance(value["guardrails"], list):
        raise ValueError("guardrails must be an explicit list")
    names = set()
    for guard in value["guardrails"]:
        fields(guard, ("metric", "direction", "max_regression", "minimum", "maximum"),
               ("metric", "direction", "max_regression"), "guardrail")
        validate_metric(guard)
        if guard["metric"] in names:
            raise ValueError("duplicate guardrail")
        names.add(guard["metric"])
        number(guard["max_regression"], "max_regression", maximum=1)
        for key in ("minimum", "maximum"):
            if key in guard:
                number(guard[key], key)
        if guard.get("minimum", 0) > guard.get("maximum", math.inf):
            raise ValueError("guardrail minimum exceeds maximum")
    repeats = value["repeats"]
    fields(repeats, ("min_processes", "min_measured_rounds", "max_relative_spread", "max_baseline_drift"),
           ("min_processes", "min_measured_rounds", "max_relative_spread", "max_baseline_drift"), "repeats")
    for key in ("min_processes", "min_measured_rounds"):
        if type(repeats[key]) is not int or repeats[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    for key in ("max_relative_spread", "max_baseline_drift"):
        number(repeats[key], key, maximum=1)
    if "slo_min_attainment" in value:
        number(value["slo_min_attainment"], "slo_min_attainment", maximum=1)
    return value


def validate_metric(spec):
    if spec.get("metric") not in vllm_perf.SUPPORTED_PERFORMANCE_METRICS:
        raise ValueError("unsupported decision metric")
    if spec.get("direction") not in ("higher", "lower"):
        raise ValueError("metric direction must be higher or lower")


def service_identity(service):
    # These are observed manifests, not an automatic remote attestation.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "accuracy"))
    from acceptance import validate_service
    # Identity/lineage applies to both modes and completion endpoints; formal
    # candidate admission separately retains its graph/chat gate.
    validate_service(service, formal=False)
    context = service.get("performance_context")
    if not isinstance(context, dict):
        raise ValueError("service is missing measured performance_context")
    for key in ("platform", "device_model", "driver_version", "device_runtime_version", "image_id", "cache_preparation"):
        if not isinstance(context.get(key), str) or not context[key].strip() or context[key].lower() in ("unknown", "todo"):
            raise ValueError(f"performance_context missing: {key}")
    devices = context.get("device_ids")
    if (not isinstance(devices, list) or not devices or any(not isinstance(d, str) or not d for d in devices)
            or len(set(devices)) != len(devices)):
        raise ValueError("performance_context requires explicit unique device identifiers")
    if context.get("prefix_cache_state") not in ("cold", "warm", "mixed", "disabled"):
        raise ValueError("prefix cache state is not established")
    return {key: val for key, val in service.items() if key not in VOLATILE_SERVICE_FIELDS}


def diff_paths(left, right, prefix=""):
    if isinstance(left, dict) and isinstance(right, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            path = prefix + "/" + key
            result.extend([path] if key not in left or key not in right else diff_paths(left[key], right[key], path))
        return result
    return [] if left == right and type(left) is type(right) else [prefix]


def relative_spread(values):
    center = number(statistics.median(values), "median")
    if center == 0:
        return 0.0 if all(v == 0 for v in values) else math.inf
    return (max(values) - min(values)) / abs(center)


def check_run(path, contract_ref, contract):
    evidence_refs = [artifact(path)]
    def verified(ref):
        result = checked(ref)
        evidence_refs.append(ref)
        return result
    record = read_json(path)
    if (not isinstance(record, dict) or type(record.get("schema_version")) is not int
            or record.get("schema_version") != 1 or record.get("kind") != "performance_run" or record.get("role") not in ROLES):
        raise ValueError("unsupported performance run record")
    if record.get("status") != "complete":
        raise ValueError("run is incomplete or failed")
    if record.get("inputs_verified_before") is not True or record.get("inputs_verified_after") is not True:
        raise ValueError("run did not verify frozen inputs before and after measurement")
    refs = record["artifacts"]
    if not isinstance(refs, dict):
        raise ValueError("run artifacts must be an object")
    if not isinstance(refs.get("comparison_contract"), dict) or refs["comparison_contract"].get("sha256") != contract_ref["sha256"]:
        raise ValueError("run did not freeze this comparison contract before measurement")
    verified(refs["comparison_contract"])
    plan = performance_plan.load_plan(verified(refs["plan"]))
    service = read_json(verified(refs["service"]))
    performance_plan._check_service(service, plan["target"])
    identity = service_identity(service)
    target, url = plan["target"], urlsplit(service["base_url"])
    if (target["model"] != service["model_name"] or target["tokenizer"] != service["tokenizer_path"]
            or target["host"] != url.hostname or target["port"] != (url.port or (443 if url.scheme == "https" else 80))):
        raise ValueError("benchmark target differs from observed service")
    if contract["scope"] == "formal" and record["role"] == "candidate":
        if record.get("scope") != "formal_candidate":
            raise ValueError("formal comparison requires formally admitted candidate runs")
        from acceptance import check_gate
        gate_path = verified(refs["accuracy_gate"])
        check_gate(gate_path, verified(refs["service"]), model=target["model"], host=target["host"],
                   port=target["port"], tokenizer=target["tokenizer"])
    elif record.get("scope") not in ("diagnostic", "performance_only", "formal_candidate"):
        raise ValueError("unknown run scope")
    client = read_json(verified(refs["client"]))
    if (not isinstance(client, dict) or type(client.get("schema_version")) is not int or client.get("schema_version") != 1
            or any(not isinstance(client.get(key), str) or not client[key] for key in ("version", "executable", "executable_sha256"))
            or not isinstance(client.get("required_flags"), list) or not isinstance(client.get("supported_flags"), list)
            or any(not isinstance(flag, str) for flag in client["required_flags"] + client["supported_flags"])
            or not set(client["required_flags"]).issubset(client["supported_flags"])):
        raise ValueError("benchmark client identity is missing")
    if not Path(client["executable"]).is_absolute() or not re.fullmatch(r"[0-9a-f]{64}", client["executable_sha256"]):
        raise ValueError("benchmark client executable fingerprint is invalid")
    probes = read_json(verified(refs["client_probes"]))
    if not isinstance(probes, dict):
        raise ValueError("client probe evidence must be an object")
    for name in ("version", "help", "runtime"):
        probe = probes.get(name)
        if (not isinstance(probe, dict) or not isinstance(probe.get("output"), str)
                or type(probe.get("returncode")) is not int or probe["returncode"] != 0
                or hashlib.sha256(probe["output"].encode()).hexdigest() != probe.get("output_sha256")):
            raise ValueError(f"invalid client {name} probe evidence")
    for name, suffix in (("version", ["--version"]), ("help", ["bench", "serve", "--help=all"])):
        if probes[name].get("command") != [client["executable"], *suffix]:
            raise ValueError(f"client {name} probe used a different executable")
    versions = re.findall(r"(?m)^\s*v?(\d+\.\d+\.\d+[^\s]*)\s*$", probes["version"]["output"])
    supported = sorted(set(re.findall(r"--[a-z][a-z0-9-]*", probes["help"]["output"])))
    if not versions or versions[-1] != client["version"] or supported != client["supported_flags"]:
        raise ValueError("client identity disagrees with its version/help probe evidence")
    runtime = performance_plan.runtime_from_probe(probes["runtime"])
    if (runtime != client.get("runtime") or runtime["vllm_version"] != client["version"]
            or probes["runtime"].get("command") != [runtime["python_invocation"], "-c", performance_plan.RUNTIME_PROBE, runtime["python_invocation"]]):
        raise ValueError("client runtime identity disagrees with source probe evidence")
    measurement = plan["measurement"]
    needed = {contract["primary"]["metric"], *(g["metric"] for g in contract["guardrails"])}
    if needed - set(measurement["required_metrics"]):
        raise ValueError("decision metrics were not frozen as required metrics in the benchmark plan")
    if "slo_min_attainment" in contract and not measurement.get("slo"):
        raise ValueError("SLO attainment requested without pre-frozen latency thresholds")
    repeats = contract["repeats"]
    if measurement["measured_rounds"] < repeats["min_measured_rounds"]:
        raise ValueError("too few measured rounds")
    total = measurement["warmup_rounds"] + measurement["measured_rounds"]
    rounds = record.get("rounds")
    if not isinstance(rounds, list) or len(rounds) != len(plan["cases"]) * total:
        raise ValueError("missing or extra rounds")
    expected = [(case, i) for case in plan["cases"] for i in range(1, total + 1)]
    collected = {case["id"]: {"warmup": [], "measured": []} for case in plan["cases"]}
    required_flags = set()
    for row, (case, index) in zip(rounds, expected):
        if not isinstance(row, dict) or type(row.get("round_id")) is not int or type(row.get("seed")) is not int:
            raise ValueError("invalid round identity")
        phase = "warmup" if index <= measurement["warmup_rounds"] else "measured"
        seed = plan["generation"]["seed"] + case["input_tokens"] * 10 + case["concurrency"] * 1000 + index
        if (row.get("case_id"), row.get("round_id"), row.get("phase"), row.get("seed")) != (case["id"], index, phase, seed):
            raise ValueError("round order, role, count or seed mismatch")
        raw_path, validation_path = verified(row["raw_result"]), verified(row["validation"])
        raw, validation = read_json(raw_path), read_json(validation_path)
        if not isinstance(raw, dict) or not isinstance(validation, dict):
            raise ValueError("native result/validation must be objects")
        command = performance_plan.build_round_command(plan, case, seed, raw_path)
        required_flags.update(arg for arg in command if arg.startswith("--"))
        if (validation.get("command") != command or type(row.get("returncode")) is not int or row["returncode"] != 0
                or type(validation.get("returncode")) is not int or validation["returncode"] != 0):
            raise ValueError("executed command/exit status differs from the frozen workload")
        if validation.get("valid") is not True or validation.get("errors") != [] or validation.get("raw_error") is not None:
            raise ValueError("round was not admitted by the native result validator")
        output = read_json(verified(validation["output"]))
        if (not isinstance(output, dict) or not isinstance(output.get("stdout"), str)
                or vllm_perf.extract_metrics(output["stdout"]) != validation["stdout_metrics"]):
            raise ValueError("parsed stdout evidence differs from the preserved client output")
        matrix = (case["input_tokens"], case["output_tokens"], case["concurrency"], case["requests"])
        metrics, diagnostics = vllm_perf.validate_native_result(
            matrix, raw, validation["stdout_metrics"], required_metrics=measurement["required_metrics"],
            ignore_eos=plan["generation"]["ignore_eos"], slo=measurement.get("slo"))
        diagnostics["errors"].extend(performance_plan.validate_native_configuration(plan, case, raw))
        if diagnostics["errors"]:
            raise ValueError("native result failed revalidation: " + "; ".join(diagnostics["errors"]))
        if measurement.get("slo"):
            goodput = number(raw.get("request_goodput"), "native request_goodput")
            good_count = goodput * raw["duration"]
            if good_count > case["requests"] + 1e-6 or abs(good_count - round(good_count)) > 1e-5:
                raise ValueError("goodput does not encode a valid successful request count")
            metrics["request_goodput"] = goodput
            metrics["slo_attainment"] = round(good_count) / case["requests"]
        collected[case["id"]][phase].append(metrics)
    if sorted(required_flags) != client["required_flags"] or required_flags - set(supported):
        raise ValueError("benchmark client capabilities do not match the frozen commands")
    warmup = measurement.get("warmup_stability")
    for case_id, phases in collected.items():
        if warmup:
            values = [m[warmup["metric"]] for m in phases["warmup"]][-warmup["window"]:]
            if performance_plan._warmup_check(values, warmup)["status"] != "passed":
                raise ValueError(f"{case_id}: warmup did not satisfy the frozen stability rule")
        elif contract["scope"] == "formal":
            raise ValueError("formal automatic comparison requires an explicit warmup stability check")
    for ref in evidence_refs:
        checked(ref)
    return {"record": evidence_refs[0], "evidence_refs": evidence_refs, "role": record["role"], "run_id": record["run_id"],
            "service_instance_id": service["service_instance_id"], "identity": identity,
            "plan": plan, "client": client, "cases": collected,
            "measurement_paths": [row[key]["path"] for row in rounds for key in ("raw_result", "validation")]}


def compare(contract_path, record_paths):
    report = {"schema_version": 1, "status": "incomplete", "scope": None, "issues": [], "cases": {},
              "aggregation": "median of per-process round medians; each round and process spread retained",
              "claim_scope": "measured workloads only; no sustained-capacity or long-term-stability claim"}
    try:
        contract_ref = artifact(contract_path)
        contract = validate_contract(read_json(contract_path))
        report.update(scope=contract["scope"], contract=contract_ref)
        runs = [check_run(path, contract_ref, contract) for path in record_paths]
        if len({r["record"]["sha256"] for r in runs}) != len(runs) or len({r["run_id"] for r in runs}) != len(runs):
            raise ValueError("duplicate run records or run IDs")
        measurement_paths = [path for run in runs for path in run["measurement_paths"]]
        if len(set(measurement_paths)) != len(measurement_paths):
            raise ValueError("a physical measurement artifact was reused across rounds or roles")
        by_role = {role: [r for r in runs if r["role"] == role] for role in ROLES}
        for role, selected in by_role.items():
            if len(selected) < contract["repeats"]["min_processes"]:
                raise ValueError(f"{role}: insufficient independent process runs")
            if len({r["service_instance_id"] for r in selected}) != len(selected):
                raise ValueError(f"{role}: same service process counted as independent repeats")
        baseline = by_role["baseline"][0]
        baseline_plan = json.loads(json.dumps(baseline["plan"]))
        for key in ("host", "port"):
            baseline_plan["target"].pop(key)
        candidate_identity = by_role["candidate"][0]["identity"]
        changed = diff_paths(baseline["identity"], candidate_identity)
        if not changed or any(not any(p == v or p.startswith(v + "/") for v in contract["variable_paths"]) for p in changed):
            raise ValueError(f"undeclared changes or no changed variable: {changed}")
        report["changed_paths"] = changed
        for run in runs:
            plan = json.loads(json.dumps(run["plan"]))
            for key in ("host", "port"):
                plan["target"].pop(key)
            if plan != baseline_plan or run["client"] != baseline["client"]:
                raise ValueError("workload/measurement plan or benchmark client drift")
            expected_identity = candidate_identity if run["role"] == "candidate" else baseline["identity"]
            if run["identity"] != expected_identity:
                raise ValueError(f"{run['role']}: service/environment drift beyond declared changes")
        report["runs"] = [r["record"] for r in runs]
        incomplete, failed = [], []
        for case in baseline["plan"]["cases"]:
            case_id = case["id"]
            detail = {"metrics": {}, "slo": {}, "load_mode": case["load_mode"]}
            specs = [contract["primary"], *contract["guardrails"]]
            for spec in specs:
                metric = spec["metric"]
                roles = {}
                for role, selected in by_role.items():
                    process_values = []
                    round_values = []
                    for run in selected:
                        values = [number(m.get(metric), metric) for m in run["cases"][case_id]["measured"]]
                        round_values.append(values)
                        process_values.append(statistics.median(values))
                        if relative_spread(values) > contract["repeats"]["max_relative_spread"]:
                            incomplete.append(f"{case_id}/{role}/{metric}: excessive within-process spread")
                    spread = relative_spread(process_values)
                    if spread > contract["repeats"]["max_relative_spread"]:
                        incomplete.append(f"{case_id}/{role}/{metric}: excessive between-process spread")
                    roles[role] = {"value": statistics.median(process_values), "round_values": round_values,
                                   "process_values": process_values, "relative_spread": spread if math.isfinite(spread) else None}
                base, candidate, revert = [roles[r]["value"] for r in ROLES]
                if base <= 0:
                    incomplete.append(f"{case_id}/{metric}: zero baseline cannot support a relative comparison")
                    continue
                improvement = (candidate - base) / base * (1 if spec["direction"] == "higher" else -1)
                if not math.isfinite(improvement):
                    raise ValueError(f"{case_id}/{metric}: relative improvement is not finite")
                detail["metrics"][metric] = {**roles, "relative_improvement": improvement}
                if abs(revert - base) / base > contract["repeats"]["max_baseline_drift"]:
                    incomplete.append(f"{case_id}/{metric}: baseline/revert drift")
                if spec is contract["primary"] and improvement < spec["min_improvement"]:
                    failed.append(f"{case_id}/{metric}: primary improvement below threshold")
                if spec is not contract["primary"]:
                    if improvement < -spec["max_regression"]:
                        failed.append(f"{case_id}/{metric}: guardrail regression")
                    # Absolute constraints apply to every measured candidate round,
                    # not just to the median of several good/bad runs.
                    for values in roles["candidate"]["round_values"]:
                        if any(v < spec.get("minimum", 0) or v > spec.get("maximum", math.inf) for v in values):
                            failed.append(f"{case_id}/{metric}: absolute guardrail breached")
                            break
            if "slo_min_attainment" in contract:
                for role, selected in by_role.items():
                    detail["slo"][role] = [m["slo_attainment"] for r in selected for m in r["cases"][case_id]["measured"]]
                if any(v < contract["slo_min_attainment"] for v in detail["slo"]["candidate"]):
                    failed.append(f"{case_id}: candidate SLO attainment below threshold")
            report["cases"][case_id] = detail
        report["issues"] = incomplete + failed
        for ref in [contract_ref, *(ref for run in runs for ref in run["evidence_refs"])]:
            checked(ref)
        report["status"] = "incomplete" if incomplete else "failed" if failed else "passed"
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        report["issues"].append(str(exc))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--run-record", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.contract, args.run_record)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"{report['status']}: {args.output}")
    raise SystemExit({"passed": 0, "failed": 1, "incomplete": 2}[report["status"]])


if __name__ == "__main__":
    main()
