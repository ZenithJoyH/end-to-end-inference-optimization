#!/usr/bin/env python3
"""Offline per-rank memory accounting and explicit paged-KV residency estimates.

This diagnostic reads a supplied snapshot, never contacts a service, and never
converts equivalent KV tokens into concurrency. Run --help for the input schema.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


UNITS = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3,
         "KB": 1000, "MB": 1000**2, "GB": 1000**3}
COMPONENTS = ("weights", "kv", "graph", "workspace", "other")
MEMORY_FIELDS = ("total",) + COMPONENTS + ("free",)


def _object(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    extra = set(value) - set(allowed)
    if extra:
        raise ValueError(f"{label} has unknown fields: {', '.join(sorted(extra))}")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _quantity(value, label):
    if value is None:
        return None
    _object(value, {"value", "unit", "evidence", "source"}, label)
    number = value.get("value")
    try:
        valid_number = type(number) in (int, float) and math.isfinite(number) and number >= 0
    except OverflowError:
        valid_number = False
    if not valid_number:
        raise ValueError(f"{label}.value must be finite and non-negative")
    unit = value.get("unit")
    if unit not in UNITS:
        raise ValueError(f"{label}.unit must be one of {', '.join(UNITS)}")
    if value.get("evidence") not in ("measured", "estimated"):
        raise ValueError(f"{label}.evidence must be measured or estimated")
    _text(value.get("source"), f"{label}.source")
    size = number * UNITS[unit]
    if not math.isfinite(size):
        raise ValueError(f"{label} byte conversion overflowed")
    return dict(value, bytes=size)


def _safe_sum(values, label):
    try:
        result = math.fsum(values)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{label} overflowed") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} overflowed")
    return result


def analyze_memory(raw, accounting, label):
    """Account only explicitly disjoint categories; unknown values stay null."""
    _object(raw, MEMORY_FIELDS, label)
    if accounting not in ("disjoint", "unspecified"):
        raise ValueError(f"{label} accounting must be disjoint or unspecified")
    quantities = {name: _quantity(raw.get(name), f"{label}.{name}") for name in MEMORY_FIELDS}
    known = {name: item["bytes"] for name, item in quantities.items() if item is not None}
    missing = [name for name in MEMORY_FIELDS if quantities[name] is None]
    gaps = [f"{label}.{name} is unknown" for name in missing]
    result = {"accounting": accounting, "quantities": quantities,
              "known_components_bytes": None, "unexplained_bytes": None,
              "unexplained_includes_missing_categories": bool(set(missing) & set(COMPONENTS)),
              "evidence": ("unknown" if not known else
                           "estimated" if any(item and item["evidence"] == "estimated"
                                              for item in quantities.values()) else "measured")}
    if accounting != "disjoint":
        gaps.append(f"{label}: disjoint accounting not declared; categories are not summed")
        return result, gaps
    components = _safe_sum((known.get(name, 0) for name in COMPONENTS), label)
    result["known_components_bytes"] = components
    # Free memory is deliberately outside the components, not another allocation.
    accounted = _safe_sum((components, known.get("free", 0)), label)
    if "total" in known:
        if accounted > known["total"]:
            raise ValueError(f"{label}: disjoint components plus free exceed total memory")
        if "free" in known:
            result["unexplained_bytes"] = max(0, known["total"] - accounted)
        if result["unexplained_bytes"] and not result["unexplained_includes_missing_categories"]:
            gaps.append(f"{label}: residual memory is not classified")
    return result, gaps


def analyze_kv(raw, label):
    """Calculate limits from supplied allocation groups, never a generic KV formula."""
    _object(raw, {"layout", "equivalent_tokens", "groups_complete", "request_scope", "groups", "source"}, label)
    layout = raw.get("layout", "unknown")
    if layout not in ("paged", "hybrid", "mla", "unknown"):
        raise ValueError(f"{label}.layout must be paged, hybrid, mla or unknown")
    complete = raw.get("groups_complete", False)
    if type(complete) is not bool:
        raise ValueError(f"{label}.groups_complete must be a boolean")
    scope = raw.get("request_scope", "unspecified")
    if scope not in ("full_decode_lifecycle", "prompt_only", "unspecified"):
        raise ValueError(f"{label}.request_scope is invalid")
    equivalent_tokens = raw.get("equivalent_tokens")
    if equivalent_tokens is not None:
        _integer(equivalent_tokens, f"{label}.equivalent_tokens")
    if "source" in raw:
        _text(raw["source"], f"{label}.source")
    groups = raw.get("groups", [])
    if not isinstance(groups, list):
        raise ValueError(f"{label}.groups must be an array")
    gaps, limits, seen, output = [], [], set(), []
    for index, group in enumerate(groups):
        place = f"{label}.groups[{index}]"
        _object(group, {"id", "free_blocks", "total_blocks", "request_blocks", "request_tokens",
                        "block_size_tokens", "token_mapping", "allocation_alignment_blocks", "source"}, place)
        group_id = _text(group.get("id"), f"{place}.id")
        if group_id in seen:
            raise ValueError(f"{label} has duplicate group id {group_id}")
        seen.add(group_id)
        free = _integer(group.get("free_blocks"), f"{place}.free_blocks")
        if "total_blocks" in group:
            total = _integer(group["total_blocks"], f"{place}.total_blocks")
            if free > total:
                raise ValueError(f"{place}: free_blocks exceed total_blocks")
        if "source" in group:
            _text(group["source"], f"{place}.source")
        alignment = _integer(group.get("allocation_alignment_blocks", 1), f"{place}.allocation_alignment_blocks", 1)
        if "token_mapping" in group and group["token_mapping"] != "dense_tokens":
            raise ValueError(f"{place}.token_mapping only supports explicitly verified dense_tokens")
        if "block_size_tokens" in group:
            _integer(group["block_size_tokens"], f"{place}.block_size_tokens", 1)
        if "request_blocks" in group and "request_tokens" in group:
            raise ValueError(f"{place}: provide request_blocks or request_tokens, not both")
        required, method = None, None
        if "request_blocks" in group:
            required = _integer(group["request_blocks"], f"{place}.request_blocks")
            method = "explicit_per_group_blocks"
        elif "request_tokens" in group:
            tokens = _integer(group["request_tokens"], f"{place}.request_tokens")
            if layout != "paged":
                gaps.append(f"{place}: {layout} layout requires explicit per-group request_blocks")
            elif group.get("token_mapping") != "dense_tokens" or "block_size_tokens" not in group:
                gaps.append(f"{place}: token-to-block mapping is not explicitly established")
            else:
                block_size = group["block_size_tokens"]
                required = (tokens + block_size - 1) // block_size
                method = "explicit_dense_token_mapping"
        else:
            gaps.append(f"{place}: per-request allocation is unknown")
        aligned = None if required is None else ((required + alignment - 1) // alignment) * alignment
        upper = free // aligned if aligned else None
        if upper is not None:
            limits.append(upper)
        output.append(dict(group, required_blocks=required, aligned_request_blocks=aligned,
                           allocation_method=method, homogeneous_requests_upper_bound=upper,
                           non_constraining=aligned == 0))
    if not groups:
        gaps.append(f"{label}: no KV groups supplied; equivalent tokens are not a token pool")
    if not complete:
        gaps.append(f"{label}: complete allocation-group coverage is not established")
    if scope != "full_decode_lifecycle":
        gaps.append(f"{label}: allocation does not cover the complete Decode lifecycle")
    if groups and not limits and not any(item["required_blocks"] is None for item in output):
        gaps.append(f"{label}: supplied groups impose no finite per-request limit")
    # Missing groups may impose a lower limit: even a complete subset is only a
    # supplied-group bound, not a complete residency estimate.
    supplied_bound = min(limits) if limits else None
    all_known = bool(groups) and all(item["required_blocks"] is not None for item in output)
    bound = supplied_bound if complete and all_known and scope == "full_decode_lifecycle" else None
    return {"layout": layout, "equivalent_tokens": equivalent_tokens,
            "equivalent_tokens_interpretation": "reported_equivalent_capacity_only",
            "groups_complete": complete, "request_scope": scope, "groups": output,
            "supplied_groups_upper_bound": supplied_bound,
            "homogeneous_full_decode_residency_upper_bound": bound,
            "evidence": "estimated",
            "source": raw.get("source")}, gaps


def analyze_snapshot(snapshot):
    _object(snapshot, {"schema_version", "context", "ranks"}, "snapshot")
    if type(snapshot.get("schema_version")) is not int or snapshot["schema_version"] != 1:
        raise ValueError("snapshot.schema_version must be 1")
    context = snapshot.get("context", {})
    if not isinstance(context, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                            for key, value in context.items()):
        raise ValueError("snapshot.context must map strings to strings")
    ranks = snapshot.get("ranks")
    if not isinstance(ranks, list) or not ranks:
        raise ValueError("snapshot.ranks must be a non-empty array")
    output, gaps, seen = [], [], set()
    for index, rank in enumerate(ranks):
        label = f"ranks[{index}]"
        _object(rank, {"rank", "memory_accounting", "memory", "kv"}, label)
        rank_id = rank.get("rank")
        if type(rank_id) is int:
            _integer(rank_id, f"{label}.rank")
            rank_id = str(rank_id)
        else:
            _text(rank_id, f"{label}.rank")
        if rank_id in seen:
            raise ValueError(f"duplicate rank {rank_id}")
        seen.add(rank_id)
        if "memory" not in rank and "kv" not in rank:
            raise ValueError(f"{label} must contain memory and/or kv")
        result = {"rank": rank_id, "memory": None, "kv": None}
        if "memory" in rank:
            result["memory"], local_gaps = analyze_memory(rank["memory"], rank.get("memory_accounting", "unspecified"), f"{label}.memory")
            gaps.extend(local_gaps)
        elif "memory_accounting" in rank:
            raise ValueError(f"{label}.memory_accounting has no memory object")
        if "kv" in rank:
            result["kv"], local_gaps = analyze_kv(rank["kv"], f"{label}.kv")
            gaps.extend(local_gaps)
        output.append(result)
    return {"schema_version": 1, "tool": "capacity_analysis", "diagnostic": True,
            "status": "incomplete" if gaps else "complete", "context": context,
            "ranks": output, "gaps": gaps,
            "assumptions": [
                "Memory categories are summed only when explicitly declared disjoint.",
                "KV bounds assume independent identical incremental allocations and the supplied free-block snapshot.",
                "Only declared block alignment is modeled; sharing, eviction and future scheduler behavior are not simulated.",
                "Full Decode residency requires caller-supplied peak allocation across the entire output lifetime."],
            "limits": ["Diagnostic arithmetic only; no runtime identity, allocation-path or evidence validity is certified.",
                       "A KV residency upper bound is not actual running concurrency, throughput, goodput or an SLO guarantee.",
                       "Ranks are kept separate; their capacities are not added or minimized without replica/topology semantics."]}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_snapshot(path):
    data = Path(path).read_bytes()
    snapshot = json.loads(data, object_pairs_hook=_pairs,
                          parse_constant=lambda item: (_ for _ in ()).throw(ValueError(f"non-finite JSON number: {item}")))
    return snapshot, {"path": str(Path(path).resolve()), "sha256": hashlib.sha256(data).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Snapshot schema (quantities may be null):
  {"schema_version":1,"context":{"model":"example"},"ranks":[
    {"rank":0,"memory_accounting":"disjoint","memory":{
      "total":{"value":80,"unit":"GiB","evidence":"measured","source":"device snapshot"}},
     "kv":{"layout":"hybrid","groups_complete":true,
       "request_scope":"full_decode_lifecycle",
       "groups":[{"id":"group0","free_blocks":100,"request_blocks":8,
                   "allocation_alignment_blocks":2}]}}]}
Memory keys: total, weights, kv, graph, workspace, other, free.
Units: B/KiB/MiB/GiB (binary), KB/MB/GB (decimal). Evidence: measured|estimated.
KV groups may use request_tokens + block_size_tokens + token_mapping=dense_tokens
only for an explicitly verified paged layout. Hybrid/MLA require request_blocks.
request_scope must cover peak allocation over the full Decode lifetime for a full
residency estimate. Missing input remains unknown, never zero. No network or GPU use.
Exit 0: diagnostic produced (inspect status/gaps); exit 2: invalid input or output.''')
    parser.add_argument("--snapshot", type=Path, required=True, help="Explicit per-rank JSON snapshot")
    parser.add_argument("--output", type=Path, help="Write a new JSON file; otherwise print to stdout")
    args = parser.parse_args(argv)
    try:
        if args.output is not None and args.output.resolve() == args.snapshot.resolve():
            raise ValueError("output must not overwrite the input snapshot")
        if args.output is not None and args.output.exists():
            raise ValueError("output already exists; choose a new diagnostic artifact path")
        snapshot, source = read_snapshot(args.snapshot)
        report = analyze_snapshot(snapshot)
        report["source"] = source
        text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output is None:
            sys.stdout.write(text)
        else:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(text)
    except (ValueError, OSError, OverflowError, UnicodeError) as exc:
        print(f"capacity_analysis: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
