"""CPU-only negative cases for the documented lm-eval v0.4.9 result schema.

Synthetic docs/values test the adapter and rejection behavior, not compatibility
with the target flageval image. That image still needs an integration preflight.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/accuracy"))
import acceptance as gate
import formal_accuracy
from sample_validation import task_filters, validate_sample_file


def example_docs():
    return [{"question": f"synthetic question {i}", "answer": "A"} for i in range(198)]


def make_provenance(cfg):
    hashes = [gate.content_sha256(doc) for doc in example_docs()]
    return {
        "schema_version": 1, "adapter": "lm-eval-configurable-task-v1", "task": gate.TASK,
        "dataset_revision": "content-sha256:" + gate.content_sha256(hashes),
        "raw_doc_sha256": hashes, "eval_doc_sha256": hashes,
        "task_config": {"task": gate.TASK, "dataset_path": cfg["dataset_path"],
                        "dataset_name": cfg["dataset_name"], "test_split": cfg["dataset_split"],
                        "output_type": "generate_until", "num_fewshot": 0,
                        "metadata": gate.model_args_values(cfg),
                        "generation_kwargs": {"temperature": 0}},
        "generation_overrides": {"temperature": 0},
        "sources": {"lm_eval": {"path": "/synthetic/lm_eval", "sha256": "a" * 64}},
        "lm_eval_version": "0.4.9", "datasets_version": "synthetic-version",
        **{key: cfg.get(key, "" if key == "include_path" else None) for key in (
            "dataset_path", "dataset_name", "dataset_split", "seed", "gen_kwargs", "include_path")},
    }


def result_payload(cfg, provenance, score=0.6):
    # Matches actual evaluator.py simple_evaluate/evaluate metadata keys.
    args = {"model": cfg["model_name"], "base_url": cfg["base_url"],
            "num_concurrent": cfg["num_concurrent"], "timeout": cfg["timeout"],
            "max_retries": cfg["api_max_retries"]}
    cache = Path(cfg["cache_root"]) / cfg["eval_model"] / cfg["run_id"] / gate.TASK / "responses.sqlite"
    return {"results": {gate.TASK: {"score": score}},
            "config": {"model": cfg["model_type"],
                       "model_args": ",".join(f"{key}={value}" for key, value in args.items()),
                       "limit": None, "use_cache": str(cache), "gen_kwargs": {"temperature": 0},
                       **{key: cfg["seed"] for key in ("random_seed", "numpy_seed", "torch_seed", "fewshot_seed")}},
            "configs": {gate.TASK: copy.deepcopy(provenance["task_config"])},
            "n-samples": {gate.TASK: {"original": 198, "effective": 198}}}


class ProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = dict(model_name="model-a", model_type="openai-chat-completions",
                        base_url="http://127.0.0.1:8000/v1/chat/completions", num_concurrent=1,
                        timeout=60, api_max_retries=0, seed=42, gen_kwargs="temperature=0",
                        dataset_path="Idavidrein/gpqa", dataset_name="gpqa_diamond",
                        dataset_split="train", include_path="", cache_root=str(self.root),
                        eval_model="case", run_id="run-a")
        self.provenance = make_provenance(self.cfg)
        self.result = self.root / "results.json"
        self.samples = self.root / "samples.jsonl"
        self.samples.write_text("".join(json.dumps({"doc_id": i, "doc": doc, "resps": [["answer"]], "filter": "none"}) + "\n"
                                       for i, doc in enumerate(example_docs())))

    def verify(self, payload):
        self.result.write_text(json.dumps(payload))
        gate.verify_result_provenance(self.result, self.samples, self.cfg, self.provenance)

    def test_matching_native_metadata_and_documents(self):
        self.verify(result_payload(self.cfg, self.provenance))

    def test_result_identity_count_and_task_mismatches_fail(self):
        valid = result_payload(self.cfg, self.provenance)
        for category in ("missing_metadata", "model", "endpoint", "count", "task", "seed", "cache", "generation"):
            payload = copy.deepcopy(valid)
            if category == "missing_metadata":
                payload.pop("config")
            elif category in ("model", "endpoint"):
                replacement = "model=WRONG" if category == "model" else "base_url=http://other:9000/v1/chat/completions"
                payload["config"]["model_args"] = replacement
            elif category == "count":
                payload["n-samples"][gate.TASK]["effective"] = 1
            elif category == "task":
                payload["configs"][gate.TASK]["dataset_path"] = "different/dataset"
            elif category == "seed":
                payload["config"]["fewshot_seed"] = 99
            elif category == "cache":
                payload["config"]["use_cache"] = "/another-run/responses.sqlite"
            else:
                payload["config"]["gen_kwargs"] = {"temperature": 1}
            with self.subTest(category=category), self.assertRaises(ValueError):
                self.verify(payload)

    def test_same_ids_with_different_documents_or_no_doc_fail(self):
        for remove in (False, True):
            rows = [json.loads(line) for line in self.samples.read_text().splitlines()]
            if remove:
                rows[0].pop("doc")
            else:
                rows[0]["doc"] = {"question": "a different question", "answer": "A"}
            self.samples.write_text("".join(json.dumps(row) + "\n" for row in rows))
            with self.subTest(remove=remove), self.assertRaises(ValueError):
                self.verify(result_payload(self.cfg, self.provenance))

    def test_contract_cannot_freeze_an_unmeasured_revision_or_legacy_schema(self):
        path = self.root / "provenance.json"
        path.write_text(json.dumps(self.provenance))
        contract = dict(schema_version=2, task=gate.TASK, expected_samples=198,
                        expected_doc_ids=list(range(198)), minimum=0.5, metric="score",
                        dataset_revision=self.provenance["dataset_revision"], task_provenance=gate.artifact(path))
        gate.validate_contract(contract)
        for changes in ({"dataset_revision": "unverified-revision"}, {"task_provenance": None}, {"schema_version": 1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                gate.validate_contract(dict(contract, **changes))

    def test_resolved_task_path_cannot_be_silently_remapped(self):
        for key, value in (("dataset_path", "mirror/gpqa"), ("dataset_split", "validation"), ("seed", 99)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                gate.validate_provenance(self.provenance, dict(self.cfg, **{key: value}))

    def test_model_args_delimiter_cannot_change_the_actual_target(self):
        cfg = dict(self.cfg, model_name="model-a,base_url=http://other:9000/v1/chat/completions",
                   tasks=[gate.TASK], limit=0, expected_samples=198, allow_timeouts=False, apply_chat_template=True)
        with self.assertRaisesRegex(ValueError, "commas"):
            gate.validate_config(cfg, {"model_name": cfg["model_name"], "base_url": cfg["base_url"]})

    def test_multi_filter_completeness_and_raw_consistency(self):
        names = ["metric-a", "metric-b"]
        rows = [dict(row, filter=name) for row in map(json.loads, self.samples.read_text().splitlines()) for name in names]
        def check(values):
            self.samples.write_text("".join(json.dumps(row) + "\n" for row in values))
            return validate_sample_file(self.samples, 198, range(198), expected_filters=names)
        self.assertEqual(check(rows)["unique_samples"], 198)
        changed = copy.deepcopy(rows)
        changed[1]["doc"] = {"question": "different"}
        unknown = copy.deepcopy(rows)
        unknown[1]["filter"] = "undeclared"
        for invalid in (rows[:-1], rows + [rows[0]], changed, unknown):
            with self.subTest(rows=len(invalid)), self.assertRaises(ValueError):
                check(invalid)
        with self.assertRaises(ValueError):
            validate_sample_file(self.samples, 198, range(198))  # unchanged strict default
        for definitions in ([], [None], [{"name": "same"}, {"name": "same"}]):
            with self.assertRaises(ValueError):
                task_filters({"filter_list": definitions})

    def test_missing_required_task_does_not_select_a_similar_task(self):
        manager = type("Manager", (), {"all_tasks": ["gpqa_diamond_cot_zeroshot"]})()
        with patch.object(formal_accuracy, "model_args_text", return_value="model=model-a"):
            with self.assertRaisesRegex(ValueError, "not registered"):
                formal_accuracy.resolve_task(self.cfg, lambda **kw: manager,
                                              lambda *args: self.fail("must not load a substitute task"),
                                              object, lambda value: {"model": "model-a"})

    def test_snapshot_distinguishes_raw_rows_and_processed_eval_docs(self):
        class Task:
            def __init__(self):
                self.config = copy.deepcopy(self_outer.provenance["task_config"])
                self.dataset = {"train": example_docs()}
                self.eval_docs = [dict(doc, rendered="processed") for doc in example_docs()]
            def get_config(self, key):
                return self.config.get(key)
            def set_config(self, key, value, update=False):
                self.config[key] = dict(self.config.get(key, {}), **value) if update else value
            def set_fewshot_seed(self, seed):
                self.seed = seed
            def dump_config(self):
                return self.config
        self_outer = self
        task = Task()
        snapshot = formal_accuracy.task_snapshot(task, self.cfg, {"temperature": 0},
                                                self.provenance["sources"],
                                                {key: self.provenance[key] for key in ("lm_eval_version", "datasets_version")})
        self.assertNotEqual(snapshot["raw_doc_sha256"], snapshot["eval_doc_sha256"])
        task.config["dataset_path"] = "mirror/gpqa"
        with self.assertRaisesRegex(ValueError, "no automatic remapping"):
            formal_accuracy.task_snapshot(task, self.cfg, {"temperature": 0}, snapshot["sources"],
                                          {key: snapshot[key] for key in ("lm_eval_version", "datasets_version")})

    def test_capture_mode_does_not_probe_or_run_model(self):
        runner = formal_accuracy.load_runner()
        cfg = dict(self.cfg, eval_model="case", tasks=[gate.TASK], limit=0, expected_samples=198,
                   allow_timeouts=False, apply_chat_template=True)
        config = self.root / "case.json"
        config.write_text(json.dumps(cfg))
        evaluator = self.root / "inspect.json"
        evaluator.write_text(json.dumps({"Config": {"Image": gate.EVAL_IMAGE}, "Image": "sha256:" + "b" * 64}))
        output = self.root / "provenance.json"
        args = type("Args", (), dict(config=config, evaluation_inspect=evaluator, capture_provenance=output))()
        with patch.object(formal_accuracy, "load_runner", return_value=runner), \
             patch.object(formal_accuracy, "collect_provenance", return_value=self.provenance), \
             patch.object(runner, "probe_service") as probe, patch.object(runner, "run_task") as run, \
             patch.object(runner, "configure_environment"), contextlib.redirect_stdout(io.StringIO()):
            formal_accuracy.run(args)
        probe.assert_not_called()
        run.assert_not_called()
        self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
