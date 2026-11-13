"""Explicit-shape arithmetic and attribution boundaries, without any device use."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evaluation/performance/shape_flops.py"
SPEC = importlib.util.spec_from_file_location("shape_flops", SCRIPT)
FLOPS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FLOPS)


def operation(kind="gemm"):
    shapes = {
        "gemm": {"batch": 2, "m": 3, "n": 4, "k": 5},
        "attention": {"pattern": "causal", "batch": 2, "query_tokens": 3, "key_tokens": 8,
                      "prefix_tokens": 5, "query_heads": 4, "kv_heads": 2, "head_dim": 8, "value_head_dim": 16},
        "moe_projections": {"tokens_per_expert": [0, 3, 17], "projections": [
            {"name": "gate", "in_features": 8, "out_features": 16},
            {"name": "up", "in_features": 8, "out_features": 16},
            {"name": "down", "in_features": 16, "out_features": 8}]}}
    return {"id": kind, "kind": kind, "scope": {"phase": "prefill", "rank": 0, "dtype": "bf16"},
            "calls": 1, "source": "synthetic explicit per-rank shape", "shape_evidence": "measured",
            "shape": copy.deepcopy(shapes[kind])}


def spec(kind="gemm"):
    return {"schema_version": 1, "operations": [operation(kind)]}


class ShapeArithmeticTest(unittest.TestCase):
    def test_batched_gemm_and_calls(self):
        raw = spec()
        raw["operations"][0]["calls"] = 7
        result = FLOPS.analyze_spec(raw)
        self.assertEqual(result["operations"][0]["F_algo"], 2 * 2 * 3 * 4 * 5 * 7)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["aggregations"], [])
        self.assertIsNone(result["operations"][0]["F_exec"])
        self.assertIsNone(result["operations"][0]["HBM_bytes"])

    def test_causal_prefix_counts_valid_pairs_and_distinct_value_dimension(self):
        raw = spec("attention")
        raw["operations"][0]["calls"] = 2
        result = FLOPS.analyze_spec(raw)["operations"][0]
        self.assertEqual(result["details"]["query_key_pairs_per_head"], 21)
        self.assertEqual(result["F_algo"], 16128)
        self.assertEqual(result["F_algo"], result["details"]["qk_F_algo"] + result["details"]["av_F_algo"])
        raw["operations"][0]["shape"].update(query_tokens=1, key_tokens=6)
        self.assertEqual(FLOPS.analyze_spec(raw)["operations"][0]["details"]["query_key_pairs_per_head"], 6)

    def test_dense_attention_counts_rectangle(self):
        raw = spec("attention")
        raw["operations"][0]["shape"]["pattern"] = "dense"
        del raw["operations"][0]["shape"]["prefix_tokens"]
        result = FLOPS.analyze_spec(raw)["operations"][0]
        self.assertEqual(result["details"]["query_key_pairs_per_head"], 24)
        self.assertEqual(result["F_algo"], 9216)

    def test_moe_uses_actual_unbalanced_experts_and_projection_list(self):
        raw = spec("moe_projections")
        raw["operations"][0]["calls"] = 2
        result = FLOPS.analyze_spec(raw)["operations"][0]
        self.assertEqual(result["F_algo"], 30720)
        self.assertEqual(result["details"]["projections"][0]["per_expert_F_algo"], [0, 1536, 8704])
        raw["operations"][0]["shape"]["tokens_per_expert"] = [0, 0, 0]
        result = FLOPS.analyze_spec(raw)["operations"][0]
        self.assertEqual(result["F_algo"], 0)
        self.assertEqual(result["status"], "complete")

    def test_only_explicit_matching_scope_operations_are_aggregated(self):
        raw = spec()
        raw["operations"].append(operation("attention"))
        self.assertEqual(FLOPS.analyze_spec(raw)["aggregations"], [])
        raw["aggregations"] = [{"id": "listed-only", "operation_ids": ["gemm", "attention"]}]
        result = FLOPS.analyze_spec(raw)["aggregations"][0]
        self.assertEqual(result["F_algo"], 240 + 8064)
        for field, value in (("rank", 1), ("phase", "decode"), ("dtype", "fp16"), ("scenario_id", "different")):
            other = copy.deepcopy(raw)
            other["operations"][1]["scope"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "matching"):
                FLOPS.analyze_spec(other)

    def test_multiple_ranks_are_preserved_without_model_total(self):
        raw = spec()
        other = operation()
        other.update(id="other-rank")
        other["scope"]["rank"] = 1
        raw["operations"].append(other)
        result = FLOPS.analyze_spec(raw)
        self.assertEqual([item["scope"]["rank"] for item in result["operations"]], ["0", "1"])
        self.assertEqual(result["aggregations"], [])
        self.assertNotIn("MFU", result)
        self.assertNotIn("model_F_algo", result)

    def test_unsupported_attention_or_operator_stays_unknown(self):
        for pattern in ("sparse", "mla", "hybrid"):
            raw = spec("attention")
            raw["operations"][0]["shape"] = {"pattern": pattern}
            result = FLOPS.analyze_spec(raw)
            self.assertEqual(result["status"], "incomplete")
            self.assertIsNone(result["operations"][0]["F_algo"])
        raw = spec()
        raw["operations"][0]["kind"] = "mystery_kernel"
        raw["aggregations"] = [{"id": "unknown", "operation_ids": ["gemm"]}]
        result = FLOPS.analyze_spec(raw)
        self.assertIsNone(result["aggregations"][0]["F_algo"])
        self.assertIsNone(result["aggregations"][0]["known_F_algo"])

    def test_integer_work_and_unknown_scope_do_not_gain_floating_totals(self):
        raw = spec("moe_projections")
        raw["operations"][0]["scope"]["dtype"] = "int8"
        result = FLOPS.analyze_spec(raw)["operations"][0]
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["F_algo"])
        self.assertEqual(result["details"], {})
        raw = spec()
        raw["operations"][0]["scope"]["rank"] = "unknown"
        raw["aggregations"] = [{"id": "unattributed", "operation_ids": ["gemm"]}]
        result = FLOPS.analyze_spec(raw)
        self.assertIsNone(result["aggregations"][0]["F_algo"])
        self.assertIsNone(result["aggregations"][0]["known_F_algo"])

    def test_invalid_shapes_and_aggregation_contracts_are_rejected(self):
        edits = [
            lambda p: p.update(schema_version=True),
            lambda p: p["operations"][0]["shape"].update(m=True),
            lambda p: p["operations"][0]["shape"].update(k=0),
            lambda p: p["operations"][0]["shape"].update(n=float("inf")),
            lambda p: p["operations"][0]["shape"].update(m=10**200, n=10**200),
            lambda p: p["operations"][0].update(calls=False),
            lambda p: p["operations"][0].update(shape_evidence="hardware_counter"),
            lambda p: p["operations"].append(copy.deepcopy(p["operations"][0])),
            lambda p: p.update(aggregations=[{"id": "bad", "operation_ids": ["absent"]}]),
            lambda p: p.update(aggregations=[{"id": "bad", "operation_ids": ["gemm", "gemm"]}]),
        ]
        for edit in edits:
            raw = spec()
            edit(raw)
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                FLOPS.analyze_spec(raw)
        for edit in (lambda shape: shape.update(key_tokens=9),
                     lambda shape: shape.update(prefix_tokens=-1),
                     lambda shape: shape.update(kv_heads=3)):
            raw = spec("attention")
            edit(raw["operations"][0]["shape"])
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                FLOPS.analyze_spec(raw)
        raw = spec("moe_projections")
        raw["operations"][0]["shape"]["tokens_per_expert"] = [1.5]
        with self.assertRaises(ValueError):
            FLOPS.analyze_spec(raw)


class ShapeCliTest(unittest.TestCase):
    def test_source_digest_new_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "shapes.json"
            target = Path(directory) / "report.json"
            source.write_text(json.dumps(spec("attention")), encoding="utf-8")
            before = source.read_bytes()
            command = [sys.executable, str(SCRIPT), "--spec", str(source)]
            result = subprocess.run(command + ["--output", str(target)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(target.read_text())
            self.assertEqual(report["source"]["sha256"], hashlib.sha256(before).hexdigest())
            self.assertEqual(report["operations"][0]["F_algo"], 8064)
            self.assertTrue(report["diagnostic"])
            for output in (source, target):
                result = subprocess.run(command + ["--output", str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(source.read_bytes(), before)

    def test_bad_json_never_creates_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            target = Path(directory) / "report.json"
            for text in ('{"schema_version":1,"schema_version":1}', '{"value":NaN}', '{"value":1e400}', '{'):
                source.write_text(text)
                result = subprocess.run([sys.executable, str(SCRIPT), "--spec", str(source), "--output", str(target)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
