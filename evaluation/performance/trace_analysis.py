#!/usr/bin/env python3
"""Offline trace diagnostics; never a performance/accuracy gate or a collector.

Example annotation schema (times are original Chrome-trace microseconds):
  {"schema_version": 1, "trace_sha256": "<64 hex digits>",
   "rank_bindings": [{"pid": 10, "device": 0, "rank": 0,
                      "evidence": "worker manifest"}],
   "ranges": [
     {"id": "p0", "kind": "phase", "label": "decode", "pid": 10,
      "device": 0, "start_us": 100, "end_us": 150, "evidence": "step marker"},
     {"id": "f0", "kind": "forward", "label": "target-0", "parent_id": "p0",
      "pid": 10, "device": 0, "start_us": 100, "end_us": 150,
      "evidence": "verified complete target forward"}],
   "anchors": [{"id": "a0", "parent_id": "f0", "verified": true,
                "event_indices": [0, 3], "labels": ["L0", "L1"],
                "evidence": "source and trace verified once per layer"}],
   "source_map": [{"event_index": 0, "source": "model.py:forward",
                   "evidence": "mapping trace matched shape and backend"}]}

An anchor identifies a start, not exclusive kernel ownership. Its last interval
ends at the explicitly verified forward boundary. A crossing event is clipped
for interval statistics and retains unknown whole-event ownership. No stage,
first layer, layer count, data dependency, or critical path is guessed.
"""

from __future__ import annotations

import argparse
import bisect
from collections import defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from trace_to_summary import CPU_CATEGORIES, DEVICE_CATEGORIES, categorize_event


SCHEMA_VERSION = 1
UNKNOWN = "unknown"
LIMITS = [
    "Diagnostic sidecar only; no formal gate, utilization, or end-to-end speedup.",
    "Time overlap does not establish independent dataflow, removable latency, or a critical path.",
    "Explicit windows and verified anchor intervals guide navigation; they do not prove exclusive layer ownership.",
    "Unobserved workers, dropped trace records, and unknown device categories require separate evidence.",
    "Only positive-duration complete (X) events are analyzed; gaps refer to the selected observed activity set, not all device work.",
]


def _number(value, label, *, nonnegative=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if nonnegative and value < 0:
        raise ValueError(f"{label} must be nonnegative")
    return float(value)


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _identity(value, label):
    if type(value) not in (int, str) or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{label} must be an integer or nonempty string")
    return str(value)


def _index(value, length, label):
    if type(value) is not int or not 0 <= value < length:
        raise ValueError(f"{label} must be an existing original event index")
    return value


def _keys(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    extra = set(value) - set(allowed)
    if extra:
        raise ValueError(f"{label} has unknown fields: {sorted(extra)}")


def _list(value, label):
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def read_json(path):
    raw = Path(path).read_bytes()
    decoded = gzip.decompress(raw) if str(path).endswith(".gz") else raw
    return json.loads(decoded.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant), hashlib.sha256(raw).hexdigest()


def _normal_identity(event, args, index):
    pid = _identity(event.get("pid", UNKNOWN), f"event {index} pid")
    device = _identity(args.get("device", UNKNOWN), f"event {index} device")
    rank = _identity(args.get("rank", args.get("global_rank", UNKNOWN)), f"event {index} rank")
    if "rank" in args and "global_rank" in args:
        if _identity(args["rank"], "rank") != _identity(args["global_rank"], "global_rank"):
            raise ValueError(f"event {index} has conflicting rank/global_rank")
    return pid, device, rank


def load_events(raw_events, device_categories):
    if not isinstance(raw_events, list) or any(not isinstance(e, dict) for e in raw_events):
        raise ValueError("traceEvents must be an array of event objects")
    rows = []
    zero_indices = []
    for index, event in enumerate(raw_events):
        if event.get("ph") != "X":
            continue
        name = _text(event.get("name"), f"event {index} name")
        start = _number(event.get("ts"), f"event {index} timestamp")
        duration = _number(event.get("dur"), f"event {index} duration", nonnegative=True)
        end = _number(start + duration, f"event {index} end")
        args = event.get("args", {})
        if not isinstance(args, dict):
            raise ValueError(f"event {index} args must be an object")
        category = event.get("cat", "")
        if not isinstance(category, str):
            raise ValueError(f"event {index} category must be a string")
        if duration == 0:
            zero_indices.append(index)
            continue
        kind = categorize_event(event, device_categories)
        pid, device, rank = _normal_identity(event, args, index)
        stream = args.get("stream", UNKNOWN)
        stream = _identity(stream, f"event {index} stream")
        source = next((args[key] for key in ("source", "source_file", "Call stack")
                       if isinstance(args.get(key), str) and args[key].strip()), None)
        rows.append({"event_index": index, "name": name, "category": category,
                     "activity": kind, "pid": pid, "device": device, "rank": rank,
                     "stream": stream, "start_us": start, "end_us": end,
                     "duration_us": duration, "source": source or UNKNOWN,
                     "source_basis": "trace_args" if source else UNKNOWN,
                     "source_evidence": None})
    if not rows:
        raise ValueError("trace has no positive-duration complete events")
    return rows, zero_indices


def merged(intervals):
    result = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if result and start <= result[-1][1]:
            result[-1][1] = max(end, result[-1][1])
        else:
            result.append([start, end])
    return result


def _length(intervals):
    return math.fsum(end - start for start, end in intervals)


def subtract_interval(start, end, intervals):
    cursor = start
    for lower, upper in intervals:
        if upper <= cursor:
            continue
        if lower >= end:
            break
        if lower > cursor:
            yield cursor, min(lower, end)
        cursor = max(cursor, upper)
        if cursor >= end:
            break
    if cursor < end:
        yield cursor, end


def _interval_index(intervals):
    intervals = merged(intervals)
    prefix = [0.0]
    for start, end in intervals:
        prefix.append(prefix[-1] + end - start)
    return [p[0] for p in intervals], [p[1] for p in intervals], prefix


def _overlap_length(start, end, index):
    starts, ends, prefix = index

    def before(time):
        count = bisect.bisect_right(ends, time)
        partial = max(0.0, time - starts[count]) if count < len(starts) else 0.0
        return prefix[count] + partial
    return before(end) - before(start)


def interval_stats(segments, window, scope_windows=None):
    """Union over observed intervals; a stream is counted once per time slice."""
    busy = merged((s["start_us"], s["end_us"]) for s in segments)
    by_stream = defaultdict(list)
    for segment in segments:
        if segment["row"]["stream"] != UNKNOWN:
            by_stream[segment["row"]["stream"]].append((segment["start_us"], segment["end_us"]))
    changes = defaultdict(list)
    for stream, intervals in by_stream.items():
        for start, end in merged(intervals):
            changes[start].append((stream, 1))
            changes[end].append((stream, -1))
    active = set()
    previous = None
    overlap = []
    exclusive = defaultdict(list)
    for time, updates in sorted(changes.items()):
        if previous is not None and time > previous:
            if len(active) >= 2:
                overlap.append([previous, time])
            elif len(active) == 1:
                exclusive[next(iter(active))].append([previous, time])
        for stream, delta in updates:
            if delta == -1:
                active.discard(stream)
        for stream, delta in updates:
            if delta == 1:
                active.add(stream)
        previous = time
    all_streams_known = all(s["row"]["stream"] != UNKNOWN for s in segments)
    wall_start = min((s["start_us"] for s in segments), default=None)
    wall_end = max((s["end_us"] for s in segments), default=None)
    scope_windows = scope_windows if scope_windows is not None else [window]
    idle = [gap for start, end in scope_windows for gap in subtract_interval(start, end, busy)]
    stats = {"event_count": len({s["row"]["event_index"] for s in segments}),
             "segment_count": len(segments),
             "sum_duration_us": math.fsum(s["end_us"] - s["start_us"] for s in segments),
             "busy_union_us": _length(busy), "wall_start_us": wall_start,
             "wall_end_us": wall_end, "wall_us": wall_end - wall_start if wall_start is not None else 0.0,
             "window_us": _length(scope_windows), "idle_gaps_us": _length(idle),
             "idle_gap_ranges_us": idle, "stream_coverage": "complete" if all_streams_known else "incomplete",
             "cross_stream_overlap_us": _length(overlap) if all_streams_known else None,
             "known_stream_overlap_lower_bound_us": _length(overlap),
             "exclusive_us": math.fsum(_length(v) for v in exclusive.values()) if all_streams_known else None}
    if not all(math.isfinite(v) for v in stats.values() if type(v) in (int, float)):
        raise ValueError("statistics overflow; no finite diagnostic can be written")
    return stats, exclusive


def _clip(segments, start, end):
    result = []
    for segment in segments:
        lower, upper = max(segment["start_us"], start), min(segment["end_us"], end)
        if upper > lower:
            result.append({"row": segment["row"], "start_us": lower, "end_us": upper})
    return result


def _remaining(segments, children):
    windows = merged((r["start_us"], r["end_us"]) for r in children)
    return [{"row": segment["row"], "start_us": start, "end_us": end}
            for segment in segments
            for start, end in subtract_interval(segment["start_us"], segment["end_us"], windows)]


def _segment_json(segment, origin):
    row = segment["row"]
    return {"event_index": row["event_index"], "start_us": segment["start_us"],
            "end_us": segment["end_us"], "duration_us": segment["end_us"] - segment["start_us"],
            "relative_start_s": (segment["start_us"] - origin) / 1e6,
            "relative_end_s": (segment["end_us"] - origin) / 1e6,
            "clipped": segment["start_us"] != row["start_us"] or segment["end_us"] != row["end_us"]}


def views(segments, stats, exclusive):
    exclusive_indices = {stream: _interval_index(intervals) for stream, intervals in exclusive.items()}
    empty_index = ([], [], [0.0])
    buckets = defaultdict(list)
    for segment in segments:
        row = segment["row"]
        buckets[(row["name"], row["source"], row["source_basis"])].append(segment)
    kernel_rows, overlap_rows = [], []
    for (name, source, basis), items in sorted(buckets.items()):
        duration = math.fsum(s["end_us"] - s["start_us"] for s in items)
        event_ids = sorted({s["row"]["event_index"] for s in items})
        kernel_rows.append({"kernel": name, "source": source, "source_basis": basis,
                            "event_indices": event_ids, "sum_duration_us": duration,
                            "call_count": len(event_ids)})
        known_overlap = math.fsum(
            s["end_us"] - s["start_us"] - _overlap_length(s["start_us"], s["end_us"], exclusive_indices.get(s["row"]["stream"], empty_index))
            for s in items if s["row"]["stream"] != UNKNOWN)
        complete = stats["stream_coverage"] == "complete"
        overlap_rows.append({"kernel": name, "event_indices": event_ids, "sum_duration_us": duration,
                             "time_overlapped_with_other_stream_us": max(0.0, known_overlap) if complete else None,
                             "known_overlap_lower_bound_us": max(0.0, known_overlap),
                             "event_exclusive_duration_us": max(0.0, duration - known_overlap) if complete else None,
                             "dependency": UNKNOWN, "removable_latency_us": None,
                             "interpretation": "temporal observation; scheduling candidate only"})
    fusion = []
    by_stream = defaultdict(list)
    for segment in segments:
        if segment["row"]["stream"] != UNKNOWN:
            by_stream[segment["row"]["stream"]].append(segment)
    for stream, items in sorted(by_stream.items()):
        items.sort(key=lambda s: (s["start_us"], s["end_us"], s["row"]["event_index"]))
        for left, right in zip(items, items[1:]):
            if left["row"]["event_index"] == right["row"]["event_index"]:
                continue
            if left["end_us"] > right["start_us"]:
                continue
            if right["row"].get("previous_same_stream_event_index") != left["row"]["event_index"]:
                continue
            if any(s["start_us"] != s["row"]["start_us"] or s["end_us"] != s["row"]["end_us"] for s in (left, right)):
                continue
            fusion.append({"event_indices": [left["row"]["event_index"], right["row"]["event_index"]],
                           "kernels": [left["row"]["name"], right["row"]["name"]],
                           "sources": [left["row"]["source"], right["row"]["source"]],
                           "stream": stream, "gap_us": right["start_us"] - left["end_us"],
                           "basis": "adjacent observed device events on the same stream",
                           "dependency": UNKNOWN, "fusion_legality": UNKNOWN,
                           "next_check": "verify producer/consumer, dtype/layout, side effects, graph buffers and end-to-end effect"})
    return {"kernel_source": kernel_rows, "overlap_candidates": overlap_rows, "fusion_candidates": fusion}


def _match_group(spec, groups, label):
    pid, device = _identity(spec.get("pid"), label + " pid"), _identity(spec.get("device"), label + " device")
    rank = _identity(spec["rank"], label + " rank") if "rank" in spec else None
    matches = [key for key in groups if key[0] == pid and key[1] == device and (rank is None or key[2] == rank)]
    if len(matches) != 1:
        raise ValueError(f"{label} must select exactly one existing pid/device/rank group")
    return matches[0]


def parse_annotations(spec, trace_sha, rows, raw_count):
    _keys(spec, {"schema_version", "trace_sha256", "rank_bindings", "ranges", "anchors", "source_map"}, "annotations")
    if type(spec.get("schema_version")) is not int or spec["schema_version"] != SCHEMA_VERSION:
        raise ValueError("annotations schema_version must be 1")
    if spec.get("trace_sha256") != trace_sha:
        raise ValueError("annotations trace_sha256 does not match exact input bytes")
    bindings = {}
    for binding in _list(spec.get("rank_bindings", []), "rank_bindings"):
        _keys(binding, {"pid", "device", "rank", "evidence"}, "rank binding")
        key = (_identity(binding.get("pid"), "binding pid"), _identity(binding.get("device"), "binding device"))
        if key in bindings:
            raise ValueError("duplicate/ambiguous rank binding")
        _text(binding.get("evidence"), "binding evidence")
        bindings[key] = _identity(binding.get("rank"), "binding rank")
    used_bindings = set()
    for row in rows:
        if row["activity"] != "device":
            continue
        key = row["pid"], row["device"]
        if key in bindings:
            if row["rank"] not in (UNKNOWN, bindings[key]):
                raise ValueError(f"rank binding conflicts with event {row['event_index']}")
            row["rank"] = bindings[key]
            used_bindings.add(key)
    if used_bindings != set(bindings):
        raise ValueError("rank binding selects no device events")
    groups = defaultdict(list)
    device_by_index = {}
    for row in rows:
        if row["activity"] == "device":
            groups[(row["pid"], row["device"], row["rank"])].append(row)
            device_by_index[row["event_index"]] = row
    ranges, ids = [], {}
    for item in _list(spec.get("ranges", []), "ranges"):
        _keys(item, {"id", "kind", "label", "parent_id", "pid", "device", "rank", "start_us", "end_us", "evidence"}, "range")
        item = dict(item)
        item["id"] = _text(item.get("id"), "range id")
        if item["id"] in ids or item["id"].startswith("__"):
            raise ValueError("duplicate or reserved range id")
        if item.get("kind") not in ("phase", "forward", "layer"):
            raise ValueError("range kind must be phase, forward or layer")
        _text(item.get("label"), "range label")
        if item["kind"] == "phase" and item["label"] not in ("prefill", "decode", "mixed"):
            raise ValueError("phase label must be prefill, decode or mixed")
        _text(item.get("evidence"), "range evidence")
        if "parent_id" in item:
            _text(item["parent_id"], "range parent_id")
        item["group_key"] = _match_group(item, groups, "range")
        item["start_us"] = _number(item.get("start_us"), "range start_us")
        item["end_us"] = _number(item.get("end_us"), "range end_us")
        if item["end_us"] <= item["start_us"]:
            raise ValueError("range end must be greater than start")
        group = groups[item["group_key"]]
        if item["start_us"] < min(r["start_us"] for r in group) or item["end_us"] > max(r["end_us"] for r in group):
            raise ValueError("range is outside observed device-group bounds")
        ids[item["id"]] = item
        ranges.append(item)
    for item in ranges:
        expected_parent = {"phase": None, "forward": "phase", "layer": "forward"}[item["kind"]]
        parent = ids.get(item.get("parent_id"))
        if expected_parent is None:
            if "parent_id" in item:
                raise ValueError("phase range cannot have parent_id")
        elif (not parent or parent["kind"] != expected_parent or parent["group_key"] != item["group_key"]
              or item["start_us"] < parent["start_us"] or item["end_us"] > parent["end_us"]):
            raise ValueError("range has absent/incompatible parent or crosses parent bounds")
    anchor_ids, anchor_parents = set(), set()
    for anchor in _list(spec.get("anchors", []), "anchors"):
        _keys(anchor, {"id", "parent_id", "verified", "event_indices", "labels", "evidence"}, "anchor")
        anchor_id = _text(anchor.get("id"), "anchor id")
        if anchor_id in anchor_ids or anchor_id in ids or anchor_id.startswith("__"):
            raise ValueError("duplicate or reserved anchor id")
        anchor_ids.add(anchor_id)
        if anchor.get("verified") is not True:
            raise ValueError("anchors require verified=true and source/trace evidence")
        _text(anchor.get("evidence"), "anchor evidence")
        parent = ids.get(_text(anchor.get("parent_id"), "anchor parent_id"))
        if not parent or parent["kind"] != "forward":
            raise ValueError("anchor parent must be an explicit forward range")
        if parent["id"] in anchor_parents or any(r.get("parent_id") == parent["id"] for r in ranges):
            raise ValueError("anchor parent already has layer ranges/anchors")
        anchor_parents.add(parent["id"])
        indices = _list(anchor.get("event_indices"), "anchor event_indices")
        labels = _list(anchor.get("labels"), "anchor labels")
        for label in labels:
            _text(label, "anchor layer label")
        if not indices or len(indices) != len(labels) or len(set(labels)) != len(labels):
            raise ValueError("anchor indices and unique labels must have equal positive length")
        selected = []
        seen = set()
        for index, label in zip(indices, labels):
            _index(index, raw_count, "anchor index")
            _text(label, "anchor layer label")
            row = device_by_index.get(index)
            if index in seen or row is None or (row["pid"], row["device"], row["rank"]) != parent["group_key"]:
                raise ValueError("duplicate anchor or anchor outside the selected device group")
            seen.add(index)
            if not parent["start_us"] <= row["start_us"] < row["end_us"] <= parent["end_us"]:
                raise ValueError("anchor event crosses forward bounds")
            selected.append(row)
        starts = [r["start_us"] for r in selected]
        if starts != sorted(set(starts)):
            raise ValueError("anchors must have strictly increasing timestamps")
        for offset, (row, label) in enumerate(zip(selected, labels)):
            item = {"id": f"{anchor_id}:{offset}", "kind": "layer", "label": label,
                    "parent_id": parent["id"], "group_key": parent["group_key"],
                    "start_us": row["start_us"],
                    "end_us": starts[offset + 1] if offset + 1 < len(starts) else parent["end_us"],
                    "evidence": anchor["evidence"], "boundary_method": "verified_anchor_interval",
                    "anchor_event_index": row["event_index"]}
            if item["id"] in ids:
                raise ValueError("generated anchor id conflicts with explicit range")
            ids[item["id"]] = item
            ranges.append(item)
    sibling_sets = defaultdict(list)
    for item in ranges:
        sibling_sets[(item["group_key"], item["kind"], item.get("parent_id"))].append(item)
    for siblings in sibling_sets.values():
        siblings.sort(key=lambda r: r["start_us"])
        for left, right in zip(siblings, siblings[1:]):
            if left["end_us"] > right["start_us"]:
                raise ValueError("sibling ranges overlap: ambiguous phase/forward/layer boundaries")
    mapped_indices = set()
    for mapping in _list(spec.get("source_map", []), "source_map"):
        _keys(mapping, {"event_index", "source", "evidence"}, "source mapping")
        index = _index(mapping.get("event_index"), raw_count, "source event_index")
        if index in mapped_indices or index not in device_by_index:
            raise ValueError("source mapping duplicates an event or selects no positive device event")
        mapped_indices.add(index)
        row = device_by_index[index]
        row["source"] = _text(mapping.get("source"), "mapped source")
        row["source_basis"] = "explicit_mapping"
        row["source_evidence"] = _text(mapping.get("evidence"), "source evidence")
    return ranges


def _node(identifier, kind, label, window, segments, ranges, origin, evidence=None, method=None, scope_windows=None):
    scope_windows = scope_windows if scope_windows is not None else [window]
    stats, exclusive = interval_stats(segments, window, scope_windows)
    node = {"id": identifier, "kind": kind, "label": label,
            "bounds": {"start_us": window[0], "end_us": window[1],
                       "relative_start_s": (window[0] - origin) / 1e6,
                       "relative_end_s": (window[1] - origin) / 1e6},
            "boundary_evidence": evidence, "boundary_method": method or ("explicit_range" if evidence else UNKNOWN),
            "scope_windows_us": scope_windows,
            "event_indices": sorted({s["row"]["event_index"] for s in segments}),
            "event_segments": [_segment_json(s, origin) for s in segments], "statistics": stats,
            "views": views(segments, stats, exclusive)}
    next_kind = {"group": "phase", "phase": "forward", "forward": "layer"}.get(kind)
    if next_kind:
        children = [r for r in ranges if r["kind"] == next_kind and r.get("parent_id") == (None if kind == "group" else identifier)]
        child_nodes = [_node(r["id"], next_kind, r["label"], (r["start_us"], r["end_us"]),
                             _clip(segments, r["start_us"], r["end_us"]), ranges, origin,
                             r["evidence"], r.get("boundary_method")) for r in sorted(children, key=lambda r: r["start_us"])]
        remaining = _remaining(segments, children)
        if remaining or not children:
            child_windows = merged((r["start_us"], r["end_us"]) for r in children)
            unknown_windows = [gap for start, end in scope_windows for gap in subtract_interval(start, end, child_windows)]
            child_nodes.append(_node(f"__{identifier}:{next_kind}:unknown", next_kind, UNKNOWN,
                                     window, remaining, [], origin, scope_windows=unknown_windows))
        node[{"phase": "phases", "forward": "forwards", "layer": "layers"}[next_kind]] = child_nodes
    return node


def analyze(trace_path, annotations_path=None, device_categories=DEVICE_CATEGORIES):
    device_categories = set(device_categories)
    if device_categories & CPU_CATEGORIES:
        raise ValueError("known CPU categories cannot be reclassified as device execution")
    if any(not isinstance(c, str) or not c.strip() or "," in c for c in device_categories):
        raise ValueError("device categories must be nonempty individual category tokens")
    data, trace_sha = read_json(trace_path)
    raw_events = data.get("traceEvents") if isinstance(data, dict) else data
    rows, zero = load_events(raw_events, device_categories)
    spec, annotation_sha = read_json(annotations_path) if annotations_path else ({"schema_version": 1, "trace_sha256": trace_sha}, None)
    ranges = parse_annotations(spec, trace_sha, rows, len(raw_events))
    origin = min(r["start_us"] for r in rows)
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        if row["activity"] != "device":
            continue
        key = row["pid"], row["device"], row["rank"]
        identity = (*key, row["stream"], row["name"], row["category"], row["start_us"], row["end_us"])
        if identity in seen:
            raise ValueError("duplicate indistinguishable device events; resolve the capture ambiguity first")
        seen.add(identity)
        groups[key].append(row)
    nodes = []
    gaps = []
    if not groups:
        gaps.append("no verified device-category events; configure verified vendor categories if appropriate")
    for number, (key, group_rows) in enumerate(sorted(groups.items())):
        group_id = f"g{number}"
        selected_ranges = [r for r in ranges if r["group_key"] == key]
        previous_by_stream = {}
        for row in sorted(group_rows, key=lambda r: (r["start_us"], r["end_us"], r["event_index"])):
            if row["stream"] != UNKNOWN:
                row["previous_same_stream_event_index"] = previous_by_stream.get(row["stream"])
                previous_by_stream[row["stream"]] = row["event_index"]
        segments = [{"row": row, "start_us": row["start_us"], "end_us": row["end_us"]} for row in group_rows]
        window = min(r["start_us"] for r in group_rows), max(r["end_us"] for r in group_rows)
        node = _node(group_id, "group", f"pid={key[0]} device={key[1]} rank={key[2]}", window,
                     segments, selected_ranges, origin)
        node.update({"pid": key[0], "device": key[1], "rank": key[2]})
        node["gaps"] = []
        if UNKNOWN in key:
            node["gaps"].append("pid/device/rank identity is incomplete; no worker-coverage claim")
        if any(r["stream"] == UNKNOWN for r in group_rows):
            node["gaps"].append("unknown stream identity; exact overlap/exclusive statistics unavailable")
        if not any(r["kind"] == "phase" for r in selected_ranges):
            node["gaps"].append("phase boundaries unavailable; all phase attribution remains unknown")
        range_indices = {}
        for kind in ("phase", "forward", "layer"):
            items = sorted((r for r in selected_ranges if r["kind"] == kind), key=lambda r: r["start_us"])
            range_indices[kind] = items, [r["start_us"] for r in items], [r["end_us"] for r in items]
        for row in group_rows:
            attribution = {}
            intersecting = []
            for kind in ("phase", "forward", "layer"):
                items, starts, ends = range_indices[kind]
                intersections = items[bisect.bisect_right(ends, row["start_us"]):bisect.bisect_left(starts, row["end_us"])]
                candidates = [r for r in intersections if r["start_us"] <= row["start_us"] and row["end_us"] <= r["end_us"]]
                attribution[kind + "_id"] = candidates[0]["id"] if len(candidates) == 1 else None
                for item in intersections:
                    if not item["start_us"] <= row["start_us"] <= row["end_us"] <= item["end_us"]:
                        intersecting.append(item["id"])
            row["attribution"] = attribution
            row["crossing_range_ids"] = intersecting
            row["group_id"] = group_id
        node["crossing_event_indices"] = [r["event_index"] for r in group_rows if r["crossing_range_ids"]]
        if node["crossing_event_indices"]:
            node["gaps"].append("events cross verified boundaries; window segments are clipped, whole-event ownership may remain unknown")
        for kind in ("phase", "forward", "layer"):
            if any(r["attribution"][kind + "_id"] is None for r in group_rows):
                node["gaps"].append(f"some whole-event {kind} attribution is unknown")
        gaps.extend(f"{group_id}: {gap}" for gap in node["gaps"])
        nodes.append(node)
    unknown = [r["event_index"] for r in rows if r["activity"] == "unclassified"]
    if unknown:
        gaps.append("unclassified complete events retained; inspect categories before reclassification")
    return {"schema_version": SCHEMA_VERSION, "tool": "trace_analysis", "diagnostic_only": True,
            "formal_gate": False, "status": "incomplete" if gaps else "diagnostic",
            "source": {"path": str(Path(trace_path).resolve()), "sha256": trace_sha,
                       "raw_event_count": len(raw_events)},
            "annotations": {"path": str(Path(annotations_path).resolve()) if annotations_path else None,
                            "sha256": annotation_sha, "verification": "caller-supplied boundary evidence; not a native gate"},
            "time_unit": "us", "navigation_origin_us": origin,
            "device_categories": sorted(device_categories), "groups": nodes,
            "events": rows, "zero_duration_event_indices": zero,
            "unclassified_event_indices": unknown, "gaps": gaps, "conclusion_boundaries": LIMITS}


def navigation_trace(report):
    events = []
    for group_index, group in enumerate(report["groups"]):
        # Numeric synthetic IDs also work with older Chrome-JSON importers.
        # Give each group globally distinct thread IDs, not just distinct pids.
        pid = 1_000_000 + group_index
        tids = {kind: 2_000_000 + 3 * group_index + offset
                for offset, kind in enumerate(("phase", "forward", "layer"))}
        original_identity = {"group_id": group["id"], "original_pid": group["pid"],
                             "original_device": group["device"], "original_rank": group["rank"]}
        events.append({"ph": "M", "name": "process_name", "pid": pid, "tid": pid,
                       "args": {"name": group["label"] + " (navigation only)", **original_identity}})
        named_kinds = set()

        def visit(node):
            if node["boundary_evidence"]:
                tid = tids[node["kind"]]
                if node["kind"] not in named_kinds:
                    events.append({"ph": "M", "name": "thread_name", "pid": pid, "tid": tid,
                                   "args": {"name": node["kind"] + " intervals (navigation only)", **original_identity}})
                    named_kinds.add(node["kind"])
                events.append({"ph": "X", "cat": "verified_navigation_interval", "name": node["label"],
                               "pid": pid, "tid": tid, "ts": node["bounds"]["start_us"],
                               "dur": node["bounds"]["end_us"] - node["bounds"]["start_us"],
                               "args": {"navigation_only": True, "boundary_evidence": node["boundary_evidence"],
                                        **original_identity,
                                        "source_sha256": report["source"]["sha256"], "range_id": node["id"],
                                        "original_event_indices": node["event_indices"],
                                        "boundary_method": node["boundary_method"]}})
            for key in ("phases", "forwards", "layers"):
                for child in node.get(key, []):
                    visit(child)
        visit(group)
    return {"traceEvents": events, "displayTimeUnit": "ms", "diagnostic_only": True,
            "source_sha256": report["source"]["sha256"],
            "notice": "Separate verified-window navigation trace; original trace is unchanged. Not kernel ownership or measured critical path."}


def write_outputs(report, output_path, perfetto_path=None, annotations_path=None):
    paths = [Path(output_path)] + ([Path(perfetto_path)] if perfetto_path else [])
    protected = {Path(report["source"]["path"]).resolve()}
    if annotations_path:
        protected.add(Path(annotations_path).resolve())
    resolved = [p.resolve() for p in paths]
    if len(set(resolved)) != len(paths) or any(p in protected for p in resolved):
        raise ValueError("outputs must be distinct from input trace, annotations and each other")
    if any(os.path.lexists(p) for p in paths):
        raise FileExistsError("output already exists; evidence is never overwritten")
    payloads = [json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8") + b"\n"]
    if perfetto_path:
        navigation = json.dumps(navigation_trace(report), ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8") + b"\n"
        payloads.append(gzip.compress(navigation, mtime=0) if str(perfetto_path).endswith(".gz") else navigation)
    opened = []
    try:
        for path in paths:
            opened.append((path, path.open("xb")))
        for (_, handle), payload in zip(opened, payloads):
            handle.write(payload)
            handle.flush()
        for _, handle in opened:
            handle.close()
    except BaseException:
        for path, handle in opened:
            handle.close()
            path.unlink()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trace", required=True, help="Explicit Chrome trace JSON or JSON.gz file; no directory discovery or capture")
    parser.add_argument("--annotations", help="Optional SHA-bound v1 boundary/anchor/source mapping JSON")
    parser.add_argument("--output", required=True, help="New diagnostic JSON path; existing files are refused")
    parser.add_argument("--perfetto-output", help="Optional new standalone verified-window navigation trace (.json or .json.gz)")
    parser.add_argument("--device-category", action="append", default=[], help="Additional independently verified vendor device category (repeatable)")
    args = parser.parse_args(argv)
    try:
        report = analyze(args.trace, args.annotations, DEVICE_CATEGORIES | set(args.device_category))
        write_outputs(report, args.output, args.perfetto_output, args.annotations)
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
        print(f"trace analysis failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "diagnostic_only": True,
                      "output": str(Path(args.output).resolve()), "groups": len(report["groups"]),
                      "gaps": report["gaps"]}, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
