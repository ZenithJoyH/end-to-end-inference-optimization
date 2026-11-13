"""Capacity arithmetic and trust boundaries; no model, network, or device use."""

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
SCRIPT = ROOT / "evaluation/performance/capacity_analysis.py"
SPEC = importlib.util.spec_from_file_location("capacity_analysis", SCRIPT)
CAPACITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CAPACITY)


def quantity(value, unit="GiB", evidence="measured"):
    return {"value": value, "unit": unit, "evidence": evidence, "source": "synthetic fixture"}


def snapshot():
    return {"schema_version": 1, "context": {"case_id": "synthetic"}, "ranks": [{
        "rank": 0, "memory_accounting": "disjoint",
        "memory": {"total": quantity(80), "weights": quantity(30), "kv": quantity(35),
                   "graph": quantity(5), "workspace": quantity(2), "other": quantity(3), "free": quantity(5)},
        "kv": {"layout": "hybrid", "groups_complete": True, "request_scope": "full_decode_lifecycle",
               "source": "verified synthetic allocation contract", "equivalent_tokens": 95082,
               "groups": [{"id": "full", "free_blocks": 100, "request_blocks": 9,
                           "allocation_alignment_blocks": 4},
                          {"id": "sliding", "free_blocks": 20, "request_blocks": 4}]}}]}


class CapacityArithmeticTest(unittest.TestCase):
    def test_disjoint_memory_and_group_alignment(self):
        result = CAPACITY.analyze_snapshot(snapshot())
        rank = result["ranks"][0]
        self.assertEqual(result["status"], "complete")
        self.assertEqual(rank["memory"]["known_components_bytes"], 75 * 1024**3)
        self.assertEqual(rank["memory"]["unexplained_bytes"], 0)
        self.assertEqual(rank["kv"]["groups"][0]["aligned_request_blocks"], 12)
        self.assertEqual(rank["kv"]["groups"][0]["homogeneous_requests_upper_bound"], 8)
        self.assertEqual(rank["kv"]["homogeneous_full_decode_residency_upper_bound"], 5)

    def test_units_and_estimated_quantities_are_retained(self):
        raw = snapshot()
        memory = raw["ranks"][0]["memory"]
        memory["total"] = quantity(80000, "MB")
        memory["weights"] = quantity(30000, "MB", "estimated")
        memory["kv"] = quantity(35000, "MB")
        memory["graph"] = quantity(5000, "MB")
        memory["workspace"] = quantity(2000, "MB")
        memory["other"] = quantity(3000, "MB")
        memory["free"] = quantity(5000, "MB")
        result = CAPACITY.analyze_snapshot(raw)["ranks"][0]["memory"]
        self.assertEqual(result["quantities"]["total"]["bytes"], 80_000_000_000)
        self.assertEqual(result["evidence"], "estimated")

    def test_memory_unknown_is_not_zero_and_overlap_is_not_summed(self):
        raw = snapshot()
        del raw["ranks"][0]["memory"]["graph"]
        result = CAPACITY.analyze_snapshot(raw)
        self.assertEqual(result["status"], "incomplete")
        memory = result["ranks"][0]["memory"]
        self.assertIsNone(memory["quantities"]["graph"])
        self.assertTrue(memory["unexplained_includes_missing_categories"])
        self.assertEqual(memory["unexplained_bytes"], 5 * 1024**3)
        raw["ranks"][0]["memory_accounting"] = "unspecified"
        result = CAPACITY.analyze_snapshot(raw)["ranks"][0]["memory"]
        self.assertIsNone(result["known_components_bytes"])
        self.assertIsNone(result["unexplained_bytes"])

    def test_zero_capacity_is_known_not_missing(self):
        raw = snapshot()
        raw["ranks"][0]["kv"]["groups"][0]["free_blocks"] = 0
        result = CAPACITY.analyze_snapshot(raw)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["ranks"][0]["kv"]["homogeneous_full_decode_residency_upper_bound"], 0)

    def test_hybrid_equivalent_tokens_never_become_a_pool(self):
        raw = snapshot()
        kv = raw["ranks"][0]["kv"]
        kv["groups"] = [{"id": "full", "free_blocks": 100, "request_tokens": 1024,
                         "block_size_tokens": 16, "token_mapping": "dense_tokens"}]
        result = CAPACITY.analyze_snapshot(raw)
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["ranks"][0]["kv"]["homogeneous_full_decode_residency_upper_bound"])
        self.assertEqual(result["ranks"][0]["kv"]["equivalent_tokens"], 95082)
        self.assertTrue(any("explicit per-group" in gap for gap in result["gaps"]))

    def test_explicit_dense_paging_rounds_tokens_then_block_alignment(self):
        raw = snapshot()
        kv = raw["ranks"][0]["kv"]
        kv["layout"] = "paged"
        kv["groups"] = [{"id": "full", "free_blocks": 100, "request_tokens": 17,
                         "block_size_tokens": 16, "token_mapping": "dense_tokens",
                         "allocation_alignment_blocks": 4}]
        result = CAPACITY.analyze_snapshot(raw)["ranks"][0]["kv"]
        self.assertEqual(result["groups"][0]["required_blocks"], 2)
        self.assertEqual(result["groups"][0]["aligned_request_blocks"], 4)
        self.assertEqual(result["homogeneous_full_decode_residency_upper_bound"], 25)

    def test_prompt_scope_and_missing_groups_do_not_claim_full_residency(self):
        for edit in (lambda kv: kv.update(request_scope="prompt_only"),
                     lambda kv: kv.update(groups_complete=False),
                     lambda kv: kv["groups"][0].pop("request_blocks")):
            raw = snapshot()
            edit(raw["ranks"][0]["kv"])
            result = CAPACITY.analyze_snapshot(raw)
            self.assertEqual(result["status"], "incomplete")
            self.assertIsNone(result["ranks"][0]["kv"]["homogeneous_full_decode_residency_upper_bound"])

    def test_ranks_are_independent_and_dp_not_silently_added(self):
        raw = snapshot()
        second = copy.deepcopy(raw["ranks"][0])
        second["rank"] = 1
        second["kv"]["groups"][1]["free_blocks"] = 4
        raw["ranks"].append(second)
        result = CAPACITY.analyze_snapshot(raw)
        self.assertEqual([rank["kv"]["homogeneous_full_decode_residency_upper_bound"] for rank in result["ranks"]], [5, 1])
        self.assertNotIn("service_concurrency", result)

    def test_non_allocating_group_does_not_limit_another_group(self):
        raw = snapshot()
        kv = raw["ranks"][0]["kv"]
        kv["groups"][0]["request_blocks"] = 0
        result = CAPACITY.analyze_snapshot(raw)["ranks"][0]["kv"]
        self.assertTrue(result["groups"][0]["non_constraining"])
        self.assertEqual(result["homogeneous_full_decode_residency_upper_bound"], 5)
        kv["groups"][1]["request_blocks"] = 0
        result = CAPACITY.analyze_snapshot(raw)
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["ranks"][0]["kv"]["homogeneous_full_decode_residency_upper_bound"])

    def test_invalid_or_contradictory_input_is_rejected(self):
        edits = [
            lambda p: p.update(schema_version=True),
            lambda p: p["ranks"].append(copy.deepcopy(p["ranks"][0])),
            lambda p: p["ranks"][0]["memory"]["total"].update(value=float("inf")),
            lambda p: p["ranks"][0]["memory"]["kv"].update(value=True),
            lambda p: p["ranks"][0]["memory"]["weights"].update(value=10**1000),
            lambda p: p["ranks"][0]["memory"]["total"].update(unit="G"),
            lambda p: p["ranks"][0]["memory"]["graph"].update(value=-1),
            lambda p: p["ranks"][0]["memory"].update(allocated=quantity(1)),
            lambda p: p["ranks"][0]["memory"]["other"].update(value=4),
            lambda p: p["ranks"][0]["kv"].update(groups_complete=1),
            lambda p: p["ranks"][0]["kv"]["groups"].append(copy.deepcopy(p["ranks"][0]["kv"]["groups"][0])),
            lambda p: p["ranks"][0]["kv"]["groups"][0].update(request_tokens=1024),
            lambda p: p["ranks"][0]["kv"]["groups"][0].update(total_blocks=20),
            lambda p: p["ranks"][0]["kv"]["groups"][0].update(allocation_alignment_blocks=0),
            lambda p: p["ranks"][0]["kv"]["groups"][0].update(free_blocks=False),
        ]
        for edit in edits:
            raw = snapshot()
            edit(raw)
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                CAPACITY.analyze_snapshot(raw)


class CapacityCliTest(unittest.TestCase):
    def test_report_source_digest_and_no_input_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "snapshot.json"
            target = Path(directory) / "report.json"
            source.write_text(json.dumps(snapshot()), encoding="utf-8")
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT), "--snapshot", str(source), "--output", str(target)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(target.read_text())
            self.assertEqual(report["source"]["sha256"], hashlib.sha256(before).hexdigest())
            self.assertTrue(report["diagnostic"])
            self.assertEqual(source.read_bytes(), before)
            for output in (source, target):
                result = subprocess.run([sys.executable, str(SCRIPT), "--snapshot", str(source), "--output", str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(source.read_bytes(), before)

    def test_invalid_json_is_not_a_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            target = Path(directory) / "report.json"
            for text in ('{"schema_version":1,"schema_version":1}', '{"schema_version":NaN}', '{"ranks":[]}', '{'):
                source.write_text(text)
                result = subprocess.run([sys.executable, str(SCRIPT), "--snapshot", str(source), "--output", str(target)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(target.exists())
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
