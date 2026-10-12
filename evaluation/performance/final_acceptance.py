#!/usr/bin/env python3
"""Revalidate project acceptance scope and phase evidence; never launch workloads."""
import argparse
import json
from pathlib import Path

import compare_performance as native


def validate_phase(phase, target, evidence, candidate_identity):
    native.fields(evidence, ("run_record", "case_id", "method", "residual_costs"),
                  ("run_record", "case_id", "method", "residual_costs"), "phase evidence")
    if evidence["method"] not in ("client-proxy", "isolated-probe"):
        raise ValueError("phase method must be client-proxy or isolated-probe")
    if not isinstance(evidence["residual_costs"], str) or not evidence["residual_costs"].strip():
        raise ValueError("record residual scheduling/network/cross-phase costs")
    path = native.checked(evidence["run_record"])
    record = native.read_json(path)
    contract_ref = record["artifacts"]["comparison_contract"]
    contract = native.validate_contract(native.read_json(native.checked(contract_ref)))
    run = native.check_run(path, contract_ref, contract)
    if run["role"] != "candidate" or run["identity"] != candidate_identity:
        raise ValueError("phase evidence must belong to the same final candidate identity")
    case = next((c for c in run["plan"]["cases"] if c["id"] == evidence["case_id"]), None)
    if case is None:
        raise ValueError("phase evidence case is missing")
    if evidence["method"] == "client-proxy":
        if case != target:
            raise ValueError("client proxies must come from the exact parent mixed workload")
    elif case["stage"] != phase or case["input_tokens"] != target["input_tokens"]:
        raise ValueError("isolated probe must match phase and parent input length")
    metrics = run["plan"]["measurement"]["required_metrics"]
    tokens = ("_ttft_",) if phase == "prefill" else ("_tpot_", "_itl_")
    if not any(any(token in metric for token in tokens) for metric in metrics):
        raise ValueError(f"{phase} evidence lacks stage proxy latency metrics")
    return run["evidence_refs"]


def validate(manifest_path):
    report = {"schema_version": 1, "status": "incomplete", "issues": [],
              "claim_scope": "project-scoped finite-batch acceptance; no sustained capacity claim"}
    try:
        manifest_ref = native.artifact(manifest_path)
        manifest = native.read_json(manifest_path)
        native.fields(manifest, ("schema_version", "contract", "run_records", "phase_evidence"),
                      ("schema_version", "contract", "run_records", "phase_evidence"), "acceptance manifest")
        if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
            raise ValueError("unsupported project acceptance schema")
        contract_path = native.checked(manifest["contract"])
        contract = native.validate_contract(native.read_json(contract_path))
        scope = contract.get("project_scope")
        if scope is None:
            raise ValueError("legacy comparisons have no frozen project lifecycle; bounded comparison only")
        report["project_scope"] = scope
        paths = [native.checked(ref) for ref in manifest["run_records"]]
        comparison = native.compare(contract_path, paths)
        report["comparison"] = comparison
        if comparison["status"] != "passed":
            report.update(status=comparison["status"], issues=comparison["issues"])
            return report
        runs = [native.check_run(p, manifest["contract"], contract) for p in paths]
        candidate = next(r for r in runs if r["role"] == "candidate")
        phases = manifest["phase_evidence"]
        if not isinstance(phases, dict) or set(phases) != set(scope["scenario_ids"]):
            raise ValueError("phase evidence must cover every target in the frozen scope")
        guards = [contract["primary"]["metric"], *(g["metric"] for g in contract["guardrails"])]
        if not any('_ttft_' in m for m in guards) or not any('_tpot_' in m or '_itl_' in m for m in guards):
            raise ValueError("project acceptance requires prefill and decode latency guards")
        refs = [manifest_ref, manifest["contract"], *manifest["run_records"]]
        for target in candidate["plan"]["cases"]:
            pair = phases[target["id"]]
            if not isinstance(pair, dict) or set(pair) != {"prefill", "decode"}:
                raise ValueError("each mixed target needs prefill and decode evidence")
            for phase, evidence in pair.items():
                refs += validate_phase(phase, target, evidence, candidate["identity"])
        for run in runs:
            refs += run["evidence_refs"]
        for ref in refs:
            native.checked(ref)
        report.update(status="passed", manifest=manifest_ref,
                      final_acceptance=scope["lifecycle"] == "final-all-targets")
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        report["issues"].append(str(exc))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='operation', required=True)
    check = commands.add_parser('check', help='revalidate existing native measurements, including manually launched runs')
    check.add_argument('--manifest', required=True, type=Path)
    check.add_argument('--output', required=True, type=Path)
    prepare = commands.add_parser('prepare', help='freeze project scope before measurement; produces no acceptance result')
    for name in ('contract', 'baseline-service', 'output'):
        prepare.add_argument('--' + name, required=True, type=Path)
    for name in ('case-id', 'baseline-id'):
        prepare.add_argument('--' + name, required=True)
    prepare.add_argument('--lifecycle', required=True, choices=['intermediate-single-target', 'final-all-targets'])
    prepare.add_argument('--baseline-kind', required=True, choices=['anchor', 'scenario-entry'])
    prepare.add_argument('--scenario-id', action='append')
    args = p.parse_args()
    if args.operation == 'prepare':
        result = native.read_json(args.contract)
        identity = native.service_identity(native.read_json(args.baseline_service), result)
        result.update(scope='formal', project_scope=dict(lifecycle=args.lifecycle, case_id=args.case_id,
            baseline_id=args.baseline_id, baseline_kind=args.baseline_kind,
            baseline_identity_sha256=native.identity_digest(identity),
            scenario_ids=args.scenario_id or (list(native.REQUIRED_SCENARIOS) if args.lifecycle == 'final-all-targets' else [])))
        native.validate_contract(result)
    else:
        result = validate(args.manifest)
    with args.output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(f"{result.get('status', 'prepared')}: {args.output}")
    return 0 if args.operation == 'prepare' or result['status'] == 'passed' else 2


if __name__ == '__main__': raise SystemExit(main())
