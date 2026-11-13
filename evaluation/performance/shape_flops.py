#!/usr/bin/env python3
"""Estimate algorithmic FLOPs from explicit per-rank operator shapes, offline.

This is a diagnostic sidecar, not a model simulator or hardware counter. It does
not infer TP/EP partitioning, hardware peaks, HBM traffic, or model-level MFU.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


MAX_COUNT = int(sys.float_info.max)
FLOAT_DTYPES = {"fp64", "float64", "fp32", "float32", "tf32", "bf16", "bfloat16",
                "fp16", "float16", "fp8", "float8_e4m3fn", "float8_e5m2", "fp4"}


def _object(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    extra = set(value) - set(allowed)
    if extra:
        raise ValueError(f"{label} has unknown fields: {', '.join(sorted(extra))}")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _integer(value, label, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    if value > MAX_COUNT:
        raise ValueError(f"{label} exceeds the supported finite count range")
    return value


def _count(value, label):
    if value > MAX_COUNT:
        raise ValueError(f"{label} count overflow: exceeds finite report arithmetic range")
    return value


def _product(values, label):
    result = 1
    for value in values:
        result = _count(result * value, label)
    return result


def _json_values(value):
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        for child in value.values():
            _json_values(child)
    elif isinstance(value, list):
        for child in value:
            _json_values(child)
    elif type(value) is float and not math.isfinite(value):
        raise ValueError("non-finite values are not allowed")
    elif value is not None and type(value) not in (str, int, float, bool):
        raise ValueError("spec must contain JSON values only")


def _scope(raw, label):
    _object(raw, {"phase", "rank", "dtype", "scenario_id", "service_id"}, label)
    phase = raw.get("phase")
    if phase not in ("prefill", "decode", "mixed", "unknown"):
        raise ValueError(f"{label}.phase must be prefill, decode, mixed or unknown")
    rank = raw.get("rank")
    if type(rank) is int:
        rank = str(_integer(rank, f"{label}.rank", 0))
    else:
        _text(rank, f"{label}.rank")
    dtype = _text(raw.get("dtype"), f"{label}.dtype")
    result = dict(raw, rank=rank, dtype=dtype, phase=phase)
    for field in ("scenario_id", "service_id"):
        if field in raw:
            _text(raw[field], f"{label}.{field}")
    return result


def gemm_flops(shape, calls, label):
    _object(shape, {"batch", "m", "n", "k"}, label)
    dims = {key: _integer(shape.get(key), f"{label}.{key}") for key in ("batch", "m", "n", "k")}
    count = _product([2, dims["batch"], dims["m"], dims["n"], dims["k"], calls], label)
    return count, {"formula": "2 * batch * M * N * K * calls", "dimensions": dims}, ["bias, epilogue and quantization work"]


def attention_flops(shape, calls, label):
    if not isinstance(shape, dict):
        raise ValueError(f"{label} must be an object")
    pattern = _text(shape.get("pattern"), f"{label}.pattern")
    if pattern not in ("dense", "causal"):
        return None, {"pattern": pattern}, ["unsupported attention requires explicit decomposed operator shapes"]
    _object(shape, {"pattern", "batch", "query_tokens", "key_tokens", "query_heads", "head_dim",
                    "value_head_dim", "prefix_tokens", "kv_heads"}, label)
    dims = {key: _integer(shape.get(key), f"{label}.{key}")
            for key in ("batch", "query_tokens", "key_tokens", "query_heads", "head_dim", "value_head_dim")}
    if "kv_heads" in shape:
        kv_heads = _integer(shape["kv_heads"], f"{label}.kv_heads")
        if kv_heads > dims["query_heads"] or dims["query_heads"] % kv_heads:
            raise ValueError(f"{label}: query_heads must be a positive multiple of kv_heads")
        dims["kv_heads"] = kv_heads
    query, keys = dims["query_tokens"], dims["key_tokens"]
    if pattern == "causal":
        prefix = _integer(shape.get("prefix_tokens"), f"{label}.prefix_tokens", 0)
        if keys != prefix + query:
            raise ValueError(f"{label}: causal key_tokens must equal prefix_tokens + query_tokens")
        pairs = _count(query * prefix + query * (query + 1) // 2, label)
        dims["prefix_tokens"] = prefix
    else:
        if "prefix_tokens" in shape:
            raise ValueError(f"{label}: prefix_tokens is only defined for causal self-attention")
        pairs = _product([query, keys], label)
    qk = _product([2, dims["batch"], dims["query_heads"], pairs, dims["head_dim"], calls], label)
    av = _product([2, dims["batch"], dims["query_heads"], pairs, dims["value_head_dim"], calls], label)
    return _count(qk + av, label), {"pattern": pattern, "dimensions": dims, "query_key_pairs_per_head": pairs,
                                   "qk_F_algo": qk, "av_F_algo": av}, ["softmax, scaling, masking implementation, RoPE, indexing and KV movement"]


def moe_projection_flops(shape, calls, label):
    _object(shape, {"tokens_per_expert", "projections"}, label)
    tokens = shape.get("tokens_per_expert")
    if not isinstance(tokens, list) or not tokens:
        raise ValueError(f"{label}.tokens_per_expert must be a non-empty array")
    tokens = [_integer(item, f"{label}.tokens_per_expert[{index}]", 0) for index, item in enumerate(tokens)]
    projections = shape.get("projections")
    if not isinstance(projections, list) or not projections:
        raise ValueError(f"{label}.projections must be a non-empty array")
    breakdown, seen = [], set()
    for index, projection in enumerate(projections):
        where = f"{label}.projections[{index}]"
        _object(projection, {"name", "in_features", "out_features"}, where)
        name = _text(projection.get("name"), f"{where}.name")
        if name in seen:
            raise ValueError(f"{label}: duplicate projection name {name}")
        seen.add(name)
        before = _integer(projection.get("in_features"), f"{where}.in_features")
        after = _integer(projection.get("out_features"), f"{where}.out_features")
        per_expert = [_product([2, count, before, after, calls], where) for count in tokens]
        total = _count(sum(per_expert), where)
        breakdown.append(dict(projection, per_expert_F_algo=per_expert, F_algo=total))
    return _count(sum(item["F_algo"] for item in breakdown), label), {
        "tokens_per_expert": tokens, "projections": breakdown}, ["router, activation, gating multiplication, packing, communication and padded execution work"]


def analyze_spec(spec):
    _json_values(spec)
    _object(spec, {"schema_version", "operations", "aggregations"}, "spec")
    if type(spec.get("schema_version")) is not int or spec["schema_version"] != 1:
        raise ValueError("spec.schema_version must be 1")
    operations = spec.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("spec.operations must be a non-empty array")
    output, by_id, gaps = [], {}, []
    for index, operation in enumerate(operations):
        label = f"operations[{index}]"
        _object(operation, {"id", "kind", "scope", "calls", "source", "shape_evidence", "shape"}, label)
        op_id = _text(operation.get("id"), f"{label}.id")
        if op_id in by_id:
            raise ValueError(f"duplicate operation id {op_id}")
        kind = _text(operation.get("kind"), f"{label}.kind")
        scope = _scope(operation.get("scope"), f"{label}.scope")
        calls = _integer(operation.get("calls", 1), f"{label}.calls")
        source = _text(operation.get("source"), f"{label}.source")
        evidence = operation.get("shape_evidence")
        if evidence not in ("measured", "estimated"):
            raise ValueError(f"{label}.shape_evidence must be measured or estimated")
        shape = operation.get("shape")
        if not isinstance(shape, dict):
            raise ValueError(f"{label}.shape must be an object")
        operation_gaps = []
        if kind == "gemm":
            count, details, excluded = gemm_flops(shape, calls, f"{label}.shape")
        elif kind == "attention":
            count, details, excluded = attention_flops(shape, calls, f"{label}.shape")
        elif kind == "moe_projections":
            count, details, excluded = moe_projection_flops(shape, calls, f"{label}.shape")
        else:
            count, details, excluded = None, {}, [f"unsupported operator kind {kind}"]
        if count is None:
            operation_gaps.extend(excluded)
        if scope["phase"] == "unknown" or scope["rank"] == "unknown":
            operation_gaps.append("phase/rank attribution is unknown")
        if scope["dtype"].lower() not in FLOAT_DTYPES:
            count = None
            details = {}
            operation_gaps.append("dtype lacks a supported floating-point counting convention; integer/mixed work requires decomposition")
        result = {"id": op_id, "kind": kind, "scope": scope, "calls": calls, "source": source,
                  "shape_evidence": evidence, "shape": shape, "F_algo": count, "F_algo_evidence": "estimated",
                  "F_exec": None, "HBM_bytes": None, "details": details, "excluded_work": excluded,
                  "status": "incomplete" if operation_gaps else "complete", "gaps": operation_gaps}
        output.append(result)
        by_id[op_id] = result
        gaps.extend(f"{op_id}: {gap}" for gap in operation_gaps)
    aggregations = spec.get("aggregations", [])
    if not isinstance(aggregations, list):
        raise ValueError("spec.aggregations must be an array")
    totals, seen_groups = [], set()
    for index, aggregation in enumerate(aggregations):
        label = f"aggregations[{index}]"
        _object(aggregation, {"id", "operation_ids"}, label)
        group_id = _text(aggregation.get("id"), f"{label}.id")
        if group_id in seen_groups:
            raise ValueError(f"duplicate aggregation id {group_id}")
        seen_groups.add(group_id)
        members = aggregation.get("operation_ids")
        if not isinstance(members, list) or not members or any(not isinstance(item, str) for item in members):
            raise ValueError(f"{label}.operation_ids must be a non-empty string array")
        if len(set(members)) != len(members) or any(item not in by_id for item in members):
            raise ValueError(f"{label}: duplicate or unknown operation id")
        selected = [by_id[item] for item in members]
        scope = selected[0]["scope"]
        if any(item["scope"] != scope for item in selected):
            raise ValueError(f"{label}: only operations with exactly matching phase/rank/dtype/scope may be aggregated")
        complete = all(item["status"] == "complete" for item in selected)
        known_counts = [item["F_algo"] for item in selected if item["F_algo"] is not None]
        scope_known = scope["phase"] != "unknown" and scope["rank"] != "unknown"
        known = _count(sum(known_counts), label) if known_counts and scope_known else None
        totals.append({"id": group_id, "operation_ids": members, "scope": scope, "F_algo": known if complete else None,
                       "known_F_algo": known, "F_algo_evidence": "estimated", "F_exec": None, "HBM_bytes": None,
                       "status": "complete" if complete else "incomplete"})
    return {"schema_version": 1, "tool": "shape_flops", "diagnostic": True,
            "status": "incomplete" if gaps else "complete", "operations": output, "aggregations": totals, "gaps": gaps,
            "assumptions": ["One multiply-add is counted as two algorithmic FLOPs.",
                            "Shapes and expert token counts are explicit per-rank caller inputs; no TP/EP division is inferred.",
                            "calls multiplies the supplied representative shape; varying shapes must be separate operations.",
                            "Explicit aggregations declare non-duplicated computation; overlapping descriptions must not be summed."],
            "limits": ["F_algo is a shape-based estimate, including when shape evidence is measured.",
                       "F_exec, HBM traffic, counter coverage, hardware efficiency and model-level MFU remain unknown.",
                       "Only listed matrix/projection work is counted; this is not complete model or service work.",
                       "No runtime identity, dispatch, correctness, performance gain or native gate is certified."]}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Spec example:
 {"schema_version":1,"operations":[{"id":"projection","kind":"gemm",
   "scope":{"phase":"prefill","rank":0,"dtype":"bf16"},"calls":1,
   "source":"verified per-rank shape","shape_evidence":"measured",
   "shape":{"batch":1,"m":1024,"n":4096,"k":4096}}]}
Attention shape: pattern=dense|causal, batch, query_tokens, key_tokens,
query_heads, head_dim, value_head_dim; causal requires prefix_tokens and K=prefix+Q.
MoE shape: tokens_per_expert=[...], projections=[{name,in_features,out_features}].
Explicit totals: aggregations=[{id,operation_ids:[...]}]; scope must match exactly.
Unsupported kinds, sparse/MLA/hybrid attention and integer/mixed counting stay
incomplete; decompose them into explicit supported operations when justified.
Exit 0: diagnostic produced (inspect status/gaps); exit 2: invalid input/output.''')
    parser.add_argument("--spec", type=Path, required=True, help="Explicit operator-shape JSON")
    parser.add_argument("--output", type=Path, help="Write a new JSON file; otherwise use stdout")
    args = parser.parse_args(argv)
    try:
        if args.output is not None and args.output.resolve() == args.spec.resolve():
            raise ValueError("output must not overwrite the input spec")
        if args.output is not None and args.output.exists():
            raise ValueError("output already exists; choose a new diagnostic artifact path")
        data = args.spec.read_bytes()
        spec = json.loads(data, object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number: {value}")))
        report = analyze_spec(spec)
        report["source"] = {"path": str(args.spec.resolve()), "sha256": hashlib.sha256(data).hexdigest()}
        text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output is None:
            sys.stdout.write(text)
        else:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(text)
    except (ValueError, OSError, OverflowError, UnicodeError) as exc:
        print(f"shape_flops: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
