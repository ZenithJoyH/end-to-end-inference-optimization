"""CPU evidence tests for an explicitly authorized, frozen GPQA replay protocol."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/accuracy"))
import acceptance as gate
import formal_accuracy


class ReferenceProtocolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.parameters = {"temperature": 0.9, "seed": 123, "max_tokens": 65536}
        self.docs = [{"index": i, "prompt": f"question {i}", "gold": "A",
                      "request": {"model": "synthetic-model", "messages": [{"role": "user", "content": str(i)}],
                                  **self.parameters}} for i in range(198)]
        (self.root / "requests.jsonl").write_text("".join(json.dumps(d) + "\n" for d in self.docs))
        (self.root / "parameters.json").write_text(json.dumps(self.parameters))
        (self.root / "task.py").write_text("class ReferenceTask:\n    def __init__(self):\n        pass\n")
        (self.root / "manifest.json").write_text(json.dumps({
            "task": "frozen_gpqa_reference", "reference_sha256": "a" * 64,
            "files": {name: gate.sha256(self.root / name) for name in
                      ("requests.jsonl", "parameters.json", "task.py")}}))
        self.reference = {"task": "frozen_gpqa_reference", "authorization": "User selected the existing reference protocol",
                          **{key: gate.artifact(self.root / name) for key, name in
                             [("manifest", "manifest.json"), ("requests", "requests.jsonl"),
                              ("parameters", "parameters.json"), ("implementation", "task.py")]}}
        self.cfg = dict(reference_protocol=self.reference, tasks=[self.reference["task"]],
                        model_name="synthetic-model", base_url="http://localhost:8000/v1/chat/completions",
                        limit=0, expected_samples=198, allow_timeouts=True, dataset_path="json",
                        dataset_name=None, dataset_split="test", model_type="local-chat-completions",
                        gen_kwargs="", seed=123, apply_chat_template=True, include_path=str(self.root))
        self.cfg.update(num_concurrent=8, timeout=600, api_max_retries=0)

    def validate(self, cfg=None):
        cfg = cfg or self.cfg
        gate.validate_config(cfg, {key: cfg[key] for key in ("model_name", "base_url")})

    def test_default_and_complete_reference_are_distinct(self):
        self.assertEqual(gate.bound_task({}), gate.TASK)
        self.assertEqual(gate.bound_task(self.cfg), "frozen_gpqa_reference")
        self.validate()
        without_binding = dict(self.cfg)
        without_binding.pop("reference_protocol")
        with self.assertRaises(ValueError):
            self.validate(without_binding)

    def test_name_or_authorization_alone_cannot_enable_a_custom_task(self):
        for changes in ({"authorization": ""}, {"task": gate.TASK}, {"implementation": None}):
            cfg = copy.deepcopy(self.cfg)
            cfg["reference_protocol"].update(changes)
            with self.subTest(changes=changes), self.assertRaises((ValueError, TypeError)):
                self.validate(cfg)

    def test_resource_tampering_rejected_even_after_updating_its_direct_hash(self):
        for name in ("requests.jsonl", "parameters.json", "task.py"):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.validate()
            cfg = copy.deepcopy(self.cfg)
            key = {"requests.jsonl": "requests", "parameters.json": "parameters", "task.py": "implementation"}[name]
            cfg["reference_protocol"][key] = gate.artifact(path)
            with self.subTest(rehashed=name), self.assertRaises(ValueError):
                self.validate(cfg)
            path.write_bytes(original)

    def test_full_collection_and_request_owned_generation_cannot_be_overridden(self):
        for key, value in (("limit", 10), ("expected_samples", 197), ("seed", 999),
                           ("gen_kwargs", "temperature=0"), ("model_type", "openai-chat-completions"),
                           ("dataset_split", "train"), ("include_path", "/different"),
                           ("model_name", "another-model")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(dict(self.cfg, **{key: value}))

    def test_a_repacked_subset_or_changed_request_is_not_the_original_protocol(self):
        for docs in (self.docs[:-1], self.docs + [self.docs[0]],
                     [dict(self.docs[0], index=99), *self.docs[1:]],
                     [dict(self.docs[0], request=dict(self.docs[0]["request"], seed=999)), *self.docs[1:]]):
            path = self.root / "requests.jsonl"
            path.write_text("".join(json.dumps(d) + "\n" for d in docs))
            manifest = gate.read_json(self.root / "manifest.json")
            manifest["files"]["requests.jsonl"] = gate.sha256(path)
            (self.root / "manifest.json").write_text(json.dumps(manifest))
            cfg = copy.deepcopy(self.cfg)
            cfg["reference_protocol"]["manifest"] = gate.artifact(self.root / "manifest.json")
            cfg["reference_protocol"]["requests"] = gate.artifact(path)
            with self.subTest(count=len(docs)), self.assertRaises(ValueError):
                self.validate(cfg)

    def test_custom_class_must_come_from_the_exact_frozen_source(self):
        spec = importlib.util.spec_from_file_location("synthetic_reference_task", self.root / "task.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(module)
        manager = type("Manager", (), {"all_tasks": [self.reference["task"]]})()
        task = module.ReferenceTask()
        load = lambda names, manager: {self.reference["task"]: task}
        actual = formal_accuracy.resolve_task(self.cfg, lambda **kw: manager, load, object, lambda text: {})
        self.assertIs(actual, task)
        sys.modules.pop(spec.name)
        self.assertIs(formal_accuracy.resolve_task(self.cfg, lambda **kw: manager, load, object, lambda text: {}), task)
        with self.assertRaisesRegex(ValueError, "frozen implementation"):
            formal_accuracy.resolve_task(self.cfg, lambda **kw: manager,
                                         lambda *args: {self.reference["task"]: self}, object, lambda text: {})

    def test_actual_request_construction_preserves_messages_and_all_parameters(self):
        class Task:
            change = None
            def construct_requests(inner, doc, ctx, **kwargs):
                request = copy.deepcopy(doc["request"])
                request.pop("model")
                messages = request.pop("messages")
                request["until"] = []
                if inner.change == "message":
                    messages[0]["content"] = "different question"
                elif inner.change == "generation":
                    request["temperature"] = 0
                elif inner.change == "stop":
                    request["until"] = ["Answer:"]
                return SimpleNamespace(arguments=(SimpleNamespace(prompt=json.dumps(messages)), request))
        task = Task()
        hashes = formal_accuracy.reference_request_fingerprints(task, self.docs, self.reference["task"])
        self.assertEqual(hashes, [gate.content_sha256(doc["request"]) for doc in self.docs])
        for change in ("message", "generation", "stop"):
            task.change = change
            with self.subTest(change=change), self.assertRaises(ValueError):
                formal_accuracy.reference_request_fingerprints(task, self.docs, self.reference["task"])

    def test_reference_gate_uses_native_evidence_and_rejects_later_protocol_drift(self):
        def write(name, value):
            path = self.root / name
            path.write_text(json.dumps(value))
            return gate.artifact(path)
        cfg = dict(self.cfg, cache_root=str(self.root / "cache"), eval_model="case", run_id="run-a")
        task_name = self.reference["task"]
        hashes = [gate.content_sha256(doc) for doc in self.docs]
        task_config = dict(task=task_name, output_type="generate_until", dataset_path="json", dataset_name=None,
                           test_split="test", dataset_kwargs={"data_files": {"test": self.reference["requests"]["path"]}})
        provenance = dict(schema_version=1, adapter="lm-eval-configurable-task-v1", task=task_name,
                          reference_protocol=self.reference, raw_doc_sha256=hashes, eval_doc_sha256=hashes,
                          reference_request_sha256=[gate.content_sha256(d["request"]) for d in self.docs],
                          dataset_revision="content-sha256:" + gate.content_sha256(hashes), task_config=task_config,
                          generation_overrides={}, sources={"lm_eval": {"sha256": "b" * 64}},
                          lm_eval_version="synthetic", datasets_version="synthetic",
                          **{k: cfg[k] for k in ("dataset_path", "dataset_name", "dataset_split", "seed", "gen_kwargs", "include_path")})
        provenance_ref = write("provenance.json", provenance)
        contract = dict(schema_version=3, task=task_name, reference_protocol=self.reference, metric="exact_match,none",
                        threshold=0.9, expected_samples=198, expected_doc_ids=list(range(198)),
                        dataset_revision=provenance["dataset_revision"], task_provenance=provenance_ref)
        service = dict(host="synthetic-host", optimization_container_name="synthetic-container", service_instance_id="instance",
                       model_name=cfg["model_name"], base_url=cfg["base_url"], tokenizer_path="/synthetic/tokenizer", mode="graph",
                       image_lineage="verified", mount_parity="passed", launch_config={"enable_prefix_caching": False},
                       flaggems_vllm_installed=True,
                       **{key: "a" * 64 for key in ("model_sha256", "tokenizer_sha256", "engine_sha256", "plugin_sha256",
                                                   "flaggems_sha256", "flaggems_vllm_sha256", "runtime_evidence_sha256")})
        result = {"results": {task_name: {"exact_match,none": 1.0}}, "configs": {task_name: task_config},
                  "n-samples": {task_name: {"original": 198, "effective": 198}},
                  "config": dict(model=cfg["model_type"], model_args=gate.model_args_text(cfg), limit=None, gen_kwargs={},
                                 use_cache=str(Path(cfg["cache_root"]) / cfg["eval_model"] / cfg["run_id"] / task_name / "responses.sqlite"),
                                 **{key: cfg["seed"] for key in ("random_seed", "numpy_seed", "torch_seed", "fewshot_seed")})}
        samples = self.root / "samples.jsonl"
        samples.write_text("".join(json.dumps({"doc_id": i, "doc": d, "resps": [["Answer: A"]], "filter": "none"}) + "\n"
                                   for i, d in enumerate(self.docs)))
        refs = {"contract": write("contract.json", contract), "config": write("config.json", cfg),
                "service": write("service.json", service), "task_provenance": provenance_ref,
                "runner": gate.artifact(ROOT / "test/Accuracy_test/llmrun.py"), "results": write("results.json", result),
                "samples": gate.artifact(samples),
                "evaluation_inspect": write("inspect.json", {"Config": {"Image": gate.EVAL_IMAGE}, "Image": "sha256:" + "c" * 64})}
        record_ref = write("run.json", dict(schema_version=2, status="evaluated", process_succeeded=True, artifacts=refs))
        output = self.root / "gate.json"
        gate.issue_gate(record_ref["path"], output)
        self.assertEqual(gate.check_gate(output, refs["service"]["path"])["score"], 1.0)
        (self.root / "parameters.json").write_text(json.dumps(dict(self.parameters, seed=999)))
        with self.assertRaises(ValueError):
            gate.check_gate(output, refs["service"]["path"])


if __name__ == "__main__":
    unittest.main()
