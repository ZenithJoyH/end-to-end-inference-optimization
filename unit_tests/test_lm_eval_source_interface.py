"""Optional checks that execute unchanged method bodies from the official wheel.

Set E2E_LM_EVAL_WHEEL to the public lm_eval==0.4.9 wheel. No installation,
dataset download, torch import or model call occurs. These are fixed-source
interface checks with synthetic rows, not a full-package/image integration.
"""
import ast
import copy
import dataclasses
import hashlib
import inspect
import json
import logging
import os
from pathlib import Path
import random
import sys
import tempfile
import types
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation/accuracy"))
import acceptance as gate
import formal_accuracy
from sample_validation import validate_sample_file

WHEEL = os.environ.get("E2E_LM_EVAL_WHEEL")
WHEEL_SHA256 = "6be0bd9395fd08e71b876622c3f53db54345a74faf60c34bf617e74dde33ba8f"


@unittest.skipUnless(WHEEL, "set E2E_LM_EVAL_WHEEL for fixed upstream source-interface checks")
class UpstreamSourceInterfaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(WHEEL)
        if hashlib.sha256(path.read_bytes()).hexdigest() != WHEEL_SHA256:
            raise ValueError("expected the original public lm_eval==0.4.9 wheel")
        with zipfile.ZipFile(path) as wheel:
            cls.sources = {name: wheel.read(name).decode() for name in (
                "lm_eval/api/task.py", "lm_eval/tasks/__init__.py", "lm_eval/__main__.py",
                "lm_eval/utils.py", "lm_eval/evaluator.py")}
            cls.task_definitions = {name: wheel.read(name).decode() for name in wheel.namelist()
                                    if name.startswith("lm_eval/tasks/") and name.endswith((".yaml", ".yml", "_yaml"))}

    def setUp(self):
        self.module = types.ModuleType("e2e_fixed_source_interface")
        sys.modules[self.module.__name__] = self.module
        self.addCleanup(sys.modules.pop, self.module.__name__, None)
        self.ns = self.module.__dict__
        self.ns.update(dataclass=dataclasses.dataclass, asdict=dataclasses.asdict,
                       getsource=inspect.getsource, eval_logger=logging.getLogger("fixture"),
                       random=random, json=json, hashlib=hashlib)
        self.cfg = dict(model_name="model-a", base_url="http://127.0.0.1:8000/v1/chat/completions",
                        num_concurrent=1, timeout=60, api_max_retries=0, seed=42,
                        dataset_path="synthetic/gpqa", dataset_name="gpqa_diamond",
                        dataset_split="train", include_path="", gen_kwargs="temperature=0")

    def nodes(self, source, name):
        return [node for node in ast.walk(ast.parse(self.sources[source]))
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name]

    def execute(self, nodes):
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
        exec(compile(ast.fix_missing_locations(module), "<fixed-lm-eval-source>", "exec"), self.ns)

    def test_cli_metadata_matches_collected_task_configuration(self):
        self.execute(self.nodes("lm_eval/utils.py", "handle_arg_string") +
                     self.nodes("lm_eval/utils.py", "simple_parse_args_string") +
                     self.nodes("lm_eval/api/task.py", "TaskConfig"))
        task_class = self.nodes("lm_eval/api/task.py", "Task")[0]
        methods = [node for node in task_class.body if isinstance(node, ast.FunctionDef)
                   and node.name in ("get_config", "set_config", "set_fewshot_seed", "dump_config", "config")]
        shell = ast.ClassDef(name="SourceTask", bases=[], keywords=[], body=methods, decorator_list=[])
        self.execute([shell])
        SourceTask = self.ns["SourceTask"]
        # Only data acquisition/constructor dependencies are replaced; all
        # config mutation/serialization below is unchanged upstream code.
        def constructor(obj, config):
            obj._config = self.ns["TaskConfig"](**config)
            obj.dataset = {"train": [{"question": str(i)} for i in range(198)]}
            obj.eval_docs = obj.dataset["train"]
        SourceTask.__init__ = constructor
        self.ns["ConfigurableTask"] = SourceTask
        self.execute(self.nodes("lm_eval/tasks/__init__.py", "_load_task"))
        yaml_config = {"task": gate.TASK, "dataset_path": self.cfg["dataset_path"],
                       "dataset_name": "gpqa_diamond", "validation_split": "train",
                       "output_type": "generate_until", "metadata": {"version": 2.0},
                       "generation_kwargs": {"temperature": 0, "until": ["\n\n"]}}
        def manager_factory(include_path=None, metadata=None):
            manager = types.SimpleNamespace(all_tasks=[gate.TASK], metadata=metadata,
                                            _config_is_python_task=lambda _: False)
            self.ns["self"] = manager
            return manager
        def get_task_dict(names, manager):
            return self.ns["_load_task"](copy.deepcopy(yaml_config), names[0])
        task = formal_accuracy.resolve_task(self.cfg, manager_factory, get_task_dict,
                                            SourceTask, self.ns["simple_parse_args_string"])
        cli = ast.parse(self.sources["lm_eval/__main__.py"])
        metadata_assignment = next(node for node in ast.walk(cli) if isinstance(node, ast.Assign)
                                   and any(isinstance(target, ast.Name) and target.id == "metadata" for target in node.targets))
        self.ns["args"] = types.SimpleNamespace(model_args=gate.model_args_text(self.cfg), metadata={})
        self.execute([metadata_assignment])
        expected_metadata = {"version": 2.0, **self.ns["metadata"]}
        self.assertEqual(task.config.metadata, expected_metadata)
        snapshot = formal_accuracy.task_snapshot(task, self.cfg, {"temperature": 0},
                        {"lm_eval": {"path": "wheel", "sha256": WHEEL_SHA256}},
                        {"lm_eval_version": "0.4.9", "datasets_version": "not-imported"})
        self.assertEqual(snapshot["task_config"]["metadata"], expected_metadata)

    def test_native_evaluator_rows_allow_complete_consistent_filters_only(self):
        self.execute(self.nodes("lm_eval/utils.py", "hash_string"))
        tree = ast.parse(self.sources["lm_eval/evaluator.py"])
        sample_expr = next(node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                           and any(isinstance(target, ast.Name) and target.id == "example" for target in node.targets))
        code = compile(ast.Expression(sample_expr), "<native-evaluator-sample>", "eval")
        rows = []
        filters = ["strict-match", "flexible-extract"]
        for doc_id in range(198):
            doc = {"question": f"synthetic-{doc_id}"}
            request = types.SimpleNamespace(doc=doc, args=("prompt",), arguments=("prompt",),
                        resps=["answer"], filtered_resps={name: "A" for name in filters})
            for name in filters:
                scope = dict(self.ns, doc_id_true=doc_id, doc=doc, target="A", requests=[request],
                             filter_key=name, metrics={"exact_match": 1}, handle_non_serializable=str)
                rows.append(eval(code, scope))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "samples.jsonl"
            def check(values):
                path.write_text("".join(json.dumps(row) + "\n" for row in values))
                return validate_sample_file(path, 198, range(198), expected_filters=filters)
            self.assertEqual(check(rows)["unique_samples"], 198)
            bad_raw = copy.deepcopy(rows)
            bad_raw[1]["resps"] = [["different model output"]]
            for invalid in (rows[:-1], rows + [rows[0]], bad_raw):
                with self.assertRaises(ValueError):
                    check(invalid)

    def test_official_wheel_does_not_supply_the_project_custom_task(self):
        self.assertFalse(any(gate.TASK in text for text in self.task_definitions.values()))


if __name__ == "__main__":
    unittest.main()
