"""Offline trace diagnostics: clipping, identity, anchors and evidence safety."""

import contextlib
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation" / "performance"))
import trace_analysis


def kernel(name="op", start=0, duration=10, *, pid=10, device=0, rank=0, stream=1, category="kernel", **extra):
    args = {"device": device, "rank": rank, **extra}
    if stream is not None:
        args["stream"] = stream
    return {"ph": "X", "cat": category, "name": name, "pid": pid,
            "tid": 900, "ts": start, "dur": duration, "args": args}


class TraceAnalysisTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.trace = self.root / "trace.json"
        self.annotations = self.root / "annotations.json"
        self.output = self.root / "diagnostic.json"

    def write_trace(self, events, *, compressed=False):
        raw = json.dumps({"traceEvents": events}).encode()
        if compressed:
            self.trace = self.root / "trace.json.gz"
            self.trace.write_bytes(gzip.compress(raw))
        else:
            self.trace.write_bytes(raw)
        return hashlib.sha256(self.trace.read_bytes()).hexdigest()

    def spec(self, **extra):
        return {"schema_version": 1, "trace_sha256": hashlib.sha256(self.trace.read_bytes()).hexdigest(), **extra}

    def analyze(self, spec=None, **kwargs):
        if spec is None:
            return trace_analysis.analyze(self.trace, **kwargs)
        self.annotations.write_text(json.dumps(spec))
        return trace_analysis.analyze(self.trace, self.annotations, **kwargs)

    def range(self, identifier, kind, start, end, parent=None, label=None, **extra):
        result = {"id": identifier, "kind": kind, "label": label or ("decode" if kind == "phase" else identifier),
                  "pid": 10, "device": 0, "start_us": start, "end_us": end, "evidence": "verified synthetic boundary", **extra}
        if parent is not None:
            result["parent_id"] = parent
        return result

    def test_rank_device_groups_and_cross_stream_tail_remain_separate(self):
        self.write_trace([kernel("long", 0, 20), kernel("short", 5, 2, stream=2),
                          kernel("other-rank", 0, 100, pid=20, rank=1),
                          kernel("other-device", 0, 200, device=1)])
        report = self.analyze()
        self.assertEqual(len(report["groups"]), 3)
        stats = report["groups"][0]["statistics"]
        self.assertEqual(stats["sum_duration_us"], 22)
        self.assertEqual(stats["busy_union_us"], 20)
        self.assertEqual(stats["wall_end_us"], 20)
        self.assertEqual(stats["wall_us"], 20)
        self.assertEqual(stats["cross_stream_overlap_us"], 2)
        self.assertEqual(stats["exclusive_us"], 18)
        self.assertTrue(report["diagnostic_only"])
        self.assertFalse(report["formal_gate"])
        self.assertEqual(report["groups"][0]["phases"][0]["label"], "unknown")
        self.assertIsNone(report["events"][0]["attribution"]["phase_id"])

    def test_overlap_is_temporal_and_source_is_not_inferred_from_name(self):
        self.write_trace([kernel("known_model_gemm", 0, 10), kernel("quant", 2, 3, stream=2), kernel("next", 12, 1)])
        report = self.analyze()
        views = report["groups"][0]["views"]
        self.assertTrue(all(row["source"] == "unknown" for row in views["kernel_source"]))
        by_name = {row["kernel"]: row for row in views["overlap_candidates"]}
        self.assertEqual(by_name["known_model_gemm"]["time_overlapped_with_other_stream_us"], 3)
        self.assertEqual(by_name["known_model_gemm"]["event_exclusive_duration_us"], 7)
        self.assertTrue(all(row["dependency"] == "unknown" and row["removable_latency_us"] is None for row in by_name.values()))
        fusion = views["fusion_candidates"]
        self.assertEqual(fusion[0]["event_indices"], [0, 2])
        self.assertEqual(fusion[0]["fusion_legality"], "unknown")

    def test_crossing_phase_events_are_clipped_and_whole_ownership_unknown(self):
        self.write_trace([kernel("tail", 0, 20)])
        spec = self.spec(ranges=[self.range("p0", "phase", 0, 10, label="prefill"),
                                 self.range("p1", "phase", 10, 20)])
        report = self.analyze(spec)
        phases = report["groups"][0]["phases"]
        self.assertEqual([p["statistics"]["sum_duration_us"] for p in phases], [10, 10])
        self.assertEqual(sum(p["statistics"]["sum_duration_us"] for p in phases), 20)
        self.assertTrue(all(p["event_segments"][0]["clipped"] for p in phases))
        self.assertIsNone(report["events"][0]["attribution"]["phase_id"])
        self.assertEqual(report["events"][0]["crossing_range_ids"], ["p0", "p1"])

    def test_unknown_remainder_does_not_count_known_phase_as_idle(self):
        self.write_trace([kernel("full", 0, 20)])
        report = self.analyze(self.spec(ranges=[self.range("p", "phase", 5, 15)]))
        phases = report["groups"][0]["phases"]
        unknown = next(p for p in phases if p["label"] == "unknown")
        self.assertEqual(unknown["scope_windows_us"], [(0.0, 5.0), (15.0, 20.0)])
        self.assertEqual(unknown["statistics"]["window_us"], 10)
        self.assertEqual(unknown["statistics"]["busy_union_us"], 10)
        self.assertEqual(unknown["statistics"]["idle_gaps_us"], 0)
        self.assertEqual(unknown["forwards"][0]["statistics"]["idle_gaps_us"], 0)

    def test_unknown_scope_does_not_invent_adjacency_across_excluded_phase(self):
        self.write_trace([kernel("before", 0, 2), kernel("inside", 4, 2), kernel("after", 8, 2)])
        report = self.analyze(self.spec(ranges=[self.range("p", "phase", 3, 7)]))
        unknown = next(p for p in report["groups"][0]["phases"] if p["label"] == "unknown")
        self.assertEqual(unknown["views"]["fusion_candidates"], [])

    def test_verified_anchor_layers_with_partial_kernel_tail(self):
        self.write_trace([{"ph": "M", "name": "process_name", "args": {"name": "worker"}},
                          kernel("anchor", 0, 1), kernel("long", 2, 12, stream=2), kernel("anchor", 10, 1)])
        spec = self.spec(ranges=[self.range("p", "phase", 0, 14), self.range("f", "forward", 0, 14, "p")],
                         anchors=[{"id": "a", "parent_id": "f", "verified": True,
                                   "event_indices": [1, 3], "labels": ["L0", "L1"], "evidence": "verified per-layer cadence"}])
        report = self.analyze(spec)
        layers = report["groups"][0]["phases"][0]["forwards"][0]["layers"]
        self.assertEqual([x["label"] for x in layers], ["L0", "L1"])
        self.assertEqual(layers[0]["statistics"]["wall_end_us"], 10)
        self.assertEqual(layers[1]["statistics"]["wall_end_us"], 14)
        self.assertEqual(layers[0]["event_segments"][1]["event_index"], 2)
        self.assertTrue(layers[0]["event_segments"][1]["clipped"])
        self.assertEqual(report["events"][1]["event_index"], 2)
        self.assertIsNone(report["events"][1]["attribution"]["layer_id"])
        self.assertEqual(report["events"][1]["attribution"]["forward_id"], "f")
        nav = trace_analysis.navigation_trace(report)
        self.assertEqual([e["name"] for e in nav["traceEvents"] if e["ph"] == "X"], ["decode", "f", "L0", "L1"])
        self.assertTrue(all(e["cat"] == "verified_navigation_interval" for e in nav["traceEvents"] if e["ph"] == "X"))

    def test_anchor_first_layer_is_not_guessed_from_parent_start(self):
        self.write_trace([kernel("leading", 0, 1), kernel("anchor", 2, 1), kernel("tail", 4, 2)])
        spec = self.spec(ranges=[self.range("p", "phase", 0, 6), self.range("f", "forward", 0, 6, "p")],
                         anchors=[{"id": "a", "parent_id": "f", "verified": True,
                                   "event_indices": [1], "labels": ["L8"], "evidence": "pipeline stage starts at layer 8"}])
        report = self.analyze(spec)
        layers = report["groups"][0]["phases"][0]["forwards"][0]["layers"]
        self.assertEqual(layers[0]["label"], "L8")
        self.assertEqual(layers[1]["label"], "unknown")
        self.assertIsNone(report["events"][0]["attribution"]["layer_id"])

    def test_navigation_serialization_uses_numeric_distinct_ids_and_names(self):
        self.write_trace([kernel("rank0", 0, 10), kernel("rank1", 0, 10, pid=20, rank=1)])
        report = self.analyze(self.spec(ranges=[self.range("p0", "phase", 0, 10),
                                               self.range("p1", "phase", 0, 10, pid=20)]))
        events = json.loads(json.dumps(trace_analysis.navigation_trace(report)))["traceEvents"]
        self.assertTrue(all(type(event["pid"]) is int and type(event["tid"]) is int for event in events))
        slices = [event for event in events if event["ph"] == "X"]
        self.assertEqual(len({event["pid"] for event in slices}), 2)
        self.assertEqual(len({event["tid"] for event in slices}), 2)
        self.assertEqual([event["args"]["original_rank"] for event in slices], ["0", "1"])
        processes = [event for event in events if event["name"] == "process_name"]
        threads = [event for event in events if event["name"] == "thread_name"]
        self.assertEqual(len(processes), 2)
        self.assertEqual(len(threads), 2)
        for event in slices:
            self.assertTrue(any(meta["pid"] == event["pid"] and meta["tid"] == event["tid"] for meta in threads))
            self.assertTrue(any(meta["pid"] == event["pid"] and "navigation only" in meta["args"]["name"] for meta in processes))

    def test_source_map_and_trace_args_have_explicit_provenance(self):
        self.write_trace([kernel("a", source="trace.py:12"), kernel("b", 12, 1)])
        report = self.analyze(self.spec(source_map=[{"event_index": 1, "source": "model.py:forward", "evidence": "separate matching mapping trace"}]))
        self.assertEqual(report["events"][0]["source_basis"], "trace_args")
        self.assertEqual(report["events"][1]["source_basis"], "explicit_mapping")
        self.assertEqual(report["events"][1]["source_evidence"], "separate matching mapping trace")

    def test_unknown_stream_does_not_publish_exact_exclusivity(self):
        self.write_trace([kernel("a", 0, 10), kernel("missing", 2, 3, stream=None)])
        report = self.analyze()
        stats = report["groups"][0]["statistics"]
        self.assertEqual(stats["busy_union_us"], 10)
        self.assertIsNone(stats["cross_stream_overlap_us"])
        self.assertIsNone(stats["exclusive_us"])
        self.assertTrue(all(x["event_exclusive_duration_us"] is None for x in report["groups"][0]["views"]["overlap_candidates"]))

    def test_vendor_category_requires_explicit_mapping_and_cpu_stays_host(self):
        self.write_trace([kernel("vendor", category="vendor_kernel"),
                          kernel("cudaLaunchKernel", category="cuda_runtime")])
        report = self.analyze()
        self.assertEqual(report["groups"], [])
        self.assertEqual(report["unclassified_event_indices"], [0])
        report = self.analyze(device_categories=trace_analysis.DEVICE_CATEGORIES | {"vendor_kernel"})
        self.assertEqual(len(report["groups"]), 1)
        self.assertEqual(report["groups"][0]["event_indices"], [0])
        with self.assertRaises(ValueError):
            self.analyze(device_categories={"cuda_runtime"})

    def test_rank_binding_is_validated_and_unknown_identity_retained(self):
        event = kernel()
        del event["args"]["rank"]
        self.write_trace([event])
        self.assertEqual(self.analyze()["groups"][0]["rank"], "unknown")
        spec = self.spec(rank_bindings=[{"pid": 10, "device": 0, "rank": 8, "evidence": "worker manifest"}])
        self.assertEqual(self.analyze(spec)["groups"][0]["rank"], "8")
        self.write_trace([kernel()])
        spec["trace_sha256"] = hashlib.sha256(self.trace.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.analyze(spec)

    def test_ambiguous_group_selector_and_conflicting_rank_are_rejected(self):
        self.write_trace([kernel(rank=0), kernel("other", rank=1)])
        with self.assertRaises(ValueError):
            self.analyze(self.spec(ranges=[self.range("p", "phase", 0, 10)]))
        self.write_trace([kernel(global_rank=5)])
        with self.assertRaises(ValueError):
            self.analyze()

    def test_sha_mismatch_and_duplicate_json_fields_fail_closed(self):
        self.write_trace([kernel()])
        with self.assertRaises(ValueError):
            self.analyze({"schema_version": 1, "trace_sha256": "0" * 64})
        self.annotations.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(ValueError):
            trace_analysis.analyze(self.trace, self.annotations)

    def test_invalid_durations_timestamps_and_trace_structures_rejected(self):
        for field, value in [("dur", -1), ("dur", float("nan")), ("dur", True), ("dur", "1"),
                             ("ts", float("inf")), ("ts", None), ("args", [])]:
            event = kernel()
            event[field] = value
            self.write_trace([event])
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.analyze()
        for data in ({}, {"traceEvents": [1]}, [], {"traceEvents": [kernel(duration=0)]}):
            self.trace.write_text(json.dumps(data))
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.analyze()

    def test_invalid_overlapping_ranges_and_unknown_fields_rejected(self):
        self.write_trace([kernel(duration=20)])
        cases = [
            [self.range("p", "phase", -1, 10)],
            [self.range("p", "phase", 0, 21)],
            [self.range("p", "phase", 10, 10)],
            [self.range("p", "phase", 0, 10), self.range("q", "phase", 9, 20)],
            [self.range("p", "phase", 0, 10), self.range("p", "phase", 10, 20)],
            [self.range("p", "phase", 0, 10), self.range("f", "forward", 0, 12, "p")],
            [self.range("f", "forward", 0, 10, "absent")],
            [self.range("p", "phase", 0, 10, unexpected=True)],
        ]
        for ranges in cases:
            with self.subTest(ranges=ranges), self.assertRaises(ValueError):
                self.analyze(self.spec(ranges=ranges))

    def test_invalid_duplicate_wrong_group_and_unverified_anchors_rejected(self):
        self.write_trace([kernel("anchor", 0, 1), kernel("anchor", 10, 1), kernel("end", 15, 5),
                          kernel("other", 0, 20, pid=20, rank=1)])
        good = {"id": "a", "parent_id": "f", "verified": True, "event_indices": [0, 1],
                "labels": ["L0", "L1"], "evidence": "verified once per layer"}
        updates = [{"verified": False}, {"event_indices": [0, 0]}, {"event_indices": [1, 0]},
                   {"event_indices": [0, 8]}, {"event_indices": [0, 3]}, {"labels": ["L0", "L0"]},
                   {"labels": ["L0"]}, {"parent_id": "p"}, {"evidence": ""}]
        for update in updates:
            spec = self.spec(ranges=[self.range("p", "phase", 0, 20), self.range("f", "forward", 0, 20, "p")],
                             anchors=[{**good, **update}])
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.analyze(spec)

    def test_duplicate_anchor_block_and_explicit_layer_conflict_rejected(self):
        self.write_trace([kernel("anchor", 0, 1), kernel("tail", 9, 1)])
        anchor = {"id": "a", "parent_id": "f", "verified": True, "event_indices": [0],
                  "labels": ["L0"], "evidence": "verified"}
        ranges = [self.range("p", "phase", 0, 10), self.range("f", "forward", 0, 10, "p")]
        for anchors, extra in [([anchor, {**anchor, "id": "b"}], []),
                               ([anchor], [self.range("l", "layer", 0, 10, "f")])]:
            with self.subTest(anchors=anchors), self.assertRaises(ValueError):
                self.analyze(self.spec(ranges=ranges + extra, anchors=anchors))

    def test_indistinguishable_device_events_rejected(self):
        self.write_trace([kernel(), kernel()])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.analyze()

    def test_idle_gaps_and_zero_duration_events(self):
        self.write_trace([kernel("a", 0, 2), kernel("zero", 3, 0), kernel("b", 5, 2)])
        report = self.analyze()
        stats = report["groups"][0]["statistics"]
        self.assertEqual(stats["idle_gaps_us"], 3)
        self.assertEqual(stats["idle_gap_ranges_us"], [(2.0, 5.0)])
        self.assertEqual(report["zero_duration_event_indices"], [1])

    def test_gzip_sha_binds_exact_original_bytes(self):
        expected = self.write_trace([kernel()], compressed=True)
        report = self.analyze()
        self.assertEqual(report["source"]["sha256"], expected)
        self.assertNotEqual(expected, hashlib.sha256(gzip.decompress(self.trace.read_bytes())).hexdigest())

    def test_outputs_never_overwrite_inputs_existing_files_or_each_other(self):
        self.write_trace([kernel()])
        report = self.analyze()
        original = self.trace.read_bytes()
        for output, perfetto in [(self.trace, None), (self.output, self.output), (self.output, self.trace)]:
            with self.subTest(output=output), self.assertRaises(ValueError):
                trace_analysis.write_outputs(report, output, perfetto)
        self.output.write_text("existing")
        with self.assertRaises(FileExistsError):
            trace_analysis.write_outputs(report, self.output)
        self.assertEqual(self.output.read_text(), "existing")
        self.assertEqual(self.trace.read_bytes(), original)
        alias = self.root / "alias.json"
        alias.symlink_to(self.trace)
        with self.assertRaises(ValueError):
            trace_analysis.write_outputs(report, alias)

    def test_output_reservation_failure_removes_only_new_partial_result(self):
        self.write_trace([kernel()])
        report = self.analyze()
        missing_parent = self.root / "not-created" / "nav.json"
        with self.assertRaises(FileNotFoundError):
            trace_analysis.write_outputs(report, self.output, missing_parent)
        self.assertFalse(self.output.exists())
        self.assertTrue(self.trace.exists())

    def test_cli_valid_gzip_navigation_and_invalid_trace_no_output(self):
        self.write_trace([kernel()])
        self.annotations.write_text(json.dumps(self.spec(ranges=[self.range("p", "phase", 0, 10)])))
        nav = self.root / "navigation.json.gz"
        command = [sys.executable, str(ROOT / "evaluation/performance/trace_analysis.py"), "--trace", str(self.trace),
                   "--annotations", str(self.annotations), "--output", str(self.output), "--perfetto-output", str(nav)]
        run = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(self.output.read_text())["diagnostic_only"])
        self.assertEqual(len(json.loads(gzip.decompress(nav.read_bytes()))["traceEvents"]), 3)
        bad_output = self.root / "bad-output.json"
        self.write_trace([kernel(duration=-1)])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(trace_analysis.main(["--trace", str(self.trace), "--output", str(bad_output)]), 1)
        self.assertFalse(bad_output.exists())


if __name__ == "__main__":
    unittest.main()
