import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'evaluation/accuracy'))
import acceptance as gate
from sample_validation import validate_sample_file
import formal_accuracy
from test_accuracy_provenance import example_docs, make_provenance, result_payload


class SamplesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'samples.jsonl'

    def write(self, rows):
        self.path.write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def test_valid_nested_responses_and_wrong_answer_filter(self):
        self.write([{'doc_id': 0, 'resps': [['reasoning and answer']], 'filtered_resps': ['']}])
        self.assertEqual(validate_sample_file(self.path, 1, [0])['unique_samples'], 1)

    def test_reject_invalid_samples(self):
        bad = [[], [{}], [{'doc_id': 0}], [{'doc_id': 0, 'resps': [[' ']]}],
               [{'doc_id': 0, 'resps': [['<TIMEOUT>']]}],
               [{'doc_id': 0, 'resps': [['answer']], 'finish_reason': 'length'}],
               [{'doc_id': 0, 'resps': [['answer']], 'truncated': True}],
               [{'doc_id': 0, 'resps': [['a']]}, {'doc_id': '0', 'resps': [['b']]}],
               [{'doc_id': 1, 'resps': [['answer']]}]]
        for rows in bad:
            with self.subTest(rows=rows):
                self.write(rows)
                with self.assertRaises(ValueError):
                    validate_sample_file(self.path, 1, [0])

    def test_output_health_is_nonblocking_when_used_as_an_observation(self):
        self.write([{'doc_id': 0, 'resps': [['answer']], 'finish_reason': 'length'}])
        summary = validate_sample_file(
            self.path, 1, [0], enforce_output_health=False)
        self.assertEqual(summary['truncations'], 1)

    def test_score_cli_rejects_nonfinite_thresholds(self):
        result = self.path.with_suffix('.json')
        result.write_text(json.dumps({'results': {'task': {'score': 0.1}}}))
        for args in (['--threshold', 'nan'], ['--threshold', 'inf']):
            with self.subTest(args=args):
                proc = subprocess.run([sys.executable, str(ROOT / 'evaluation/accuracy/verify_accuracy.py'),
                                       str(result), '--task', 'task', '--metric', 'score', *args], capture_output=True)
                self.assertNotEqual(proc.returncode, 0)

    def test_score_cli_accepts_equal_threshold(self):
        result = self.path.with_suffix('.json')
        result.write_text(json.dumps({'results': {'task': {'score': 0.5}}}))
        command = [sys.executable, str(ROOT / 'evaluation/accuracy/verify_accuracy.py'),
                   str(result), '--task', 'task', '--metric', 'score', '--threshold']
        self.assertEqual(subprocess.run([*command, '0.5'], capture_output=True).returncode, 0)
        self.assertNotEqual(subprocess.run([*command, '0.5001'], capture_output=True).returncode, 0)


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.service = dict(host='host-a', optimization_container_name='isolated', service_instance_id='boot-1',
                            model_name='model-a', base_url='http://127.0.0.1:8000/v1/chat/completions',
                            tokenizer_path='/tokenizer', mode='graph', launch_config={'tp': 4}, image_lineage='verified', mount_parity='passed')
        self.service.update({key: 'a' * 64 for key in ('model_sha256', 'tokenizer_sha256', 'engine_sha256', 'plugin_sha256', 'flaggems_sha256', 'runtime_evidence_sha256')})
        self.service.update(flaggems_vllm_installed=False, flaggems_vllm_sha256=None)
        self.service['performance_context'] = dict(platform='fixture', device_model='fixture',
            driver_version='fixture', device_runtime_version='fixture', image_id='fixture-image', device_ids=['0'])
        self.contract = dict(schema_version=3, task=gate.TASK, metric='score', threshold=0.5,
                             expected_samples=198, expected_doc_ids=list(range(198)))
        self.cfg = dict(tasks=[gate.TASK], limit=0, expected_samples=198, allow_timeouts=True,
                        model_name='model-a', base_url=self.service['base_url'], seed=42,
                        dataset_path='Idavidrein/gpqa', dataset_name='gpqa_diamond', dataset_split='train',
                        model_type='openai-chat-completions', apply_chat_template=True, gen_kwargs='temperature=0',
                        include_path='', num_concurrent=1, timeout=60, api_max_retries=0,
                        cache_root=str(self.root / 'cache'), eval_model='fixture', run_id='run-a')
        self.refs = {}
        self.provenance = make_provenance(self.cfg)
        self.save('task_provenance', self.provenance)
        self.contract.update(dataset_revision=self.provenance['dataset_revision'],
                             task_provenance=self.refs['task_provenance'])
        for name, obj in [('service', self.service), ('contract', self.contract), ('config', self.cfg),
                          ('evaluation_inspect', {'Config': {'Image': gate.EVAL_IMAGE}, 'Image': 'sha256:' + 'b' * 64}),
                          ('results', result_payload(self.cfg, self.provenance))]:
            self.save(name, obj)
        self.refs['runner'] = gate.artifact(formal_accuracy.RUNNER)
        samples = self.root / 'samples.jsonl'
        samples.write_text(''.join(json.dumps({'doc_id': i, 'doc': doc, 'resps': [['answer']], 'filter': 'none'}) + '\n'
                                   for i, doc in enumerate(example_docs())))
        self.refs['samples'] = gate.artifact(samples)
        self.record = self.root / 'run-record.json'
        gate.write_new(self.record, {'schema_version': 2, 'status': 'evaluated', 'process_succeeded': True, 'artifacts': self.refs})
        self.health = self.root / 'health.json'
        gate.write_new(self.health, dict(samples_sha256=self.refs['samples']['sha256'], reviewer='test', method='fixture',
                                        **{key: 'passed' for key in ('empty_outputs', 'truncation', 'abnormal_repetition', 'garbled_output', 'timeouts')}))
        self.output = self.root / 'gate.json'

    def save(self, name, obj):
        path = self.root / (name + '.json')
        path.write_text(json.dumps(obj))
        self.refs[name] = gate.artifact(path)

    def test_issue_check_and_changed_service_rejected(self):
        gate.issue_gate(self.record, self.output)
        gate.check_gate(self.output, self.root / 'service.json', 'model-a', '127.0.0.1', 8000)
        self.service['service_instance_id'] = 'boot-2'
        self.save('service', self.service)
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, self.root / 'service.json')

    def test_changed_result_or_different_endpoint_rejected(self):
        gate.issue_gate(self.record, self.output)
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, self.root / 'service.json', port=9000)
        self.save('results', {'results': {gate.TASK: {'score': 1.0}}})
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, self.root / 'service.json')

    def test_gate_accepts_score_equal_to_threshold(self):
        self.contract['threshold'] = 0.6
        self.save('contract', self.contract)
        record = gate.read_json(self.record)
        record['artifacts']['contract'] = self.refs['contract']
        self.record.write_text(json.dumps(record))
        issued = gate.issue_gate(self.record, self.output)
        self.assertEqual(issued['score'], issued['threshold'])
        gate.check_gate(self.output, self.root / 'service.json')

    def test_gate_accepts_timeout_when_score_meets_threshold(self):
        samples = self.root / 'samples.jsonl'
        rows = [json.loads(line) for line in samples.read_text().splitlines()]
        rows[0]['resps'] = [['<TIMEOUT>']]
        rows[0]['timeout'] = True
        samples.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        self.refs['samples'] = gate.artifact(samples)
        self.record.write_text(json.dumps({
            'schema_version': 2, 'status': 'evaluated',
            'process_succeeded': True, 'artifacts': self.refs,
        }))
        issued = gate.issue_gate(self.record, self.output)
        self.assertTrue(issued['passed'])
        gate.check_gate(self.output, self.root / 'service.json')

    def test_boolean_gate_rejected_and_health_observation_nonblocking(self):
        gate.write_new(self.output, {'passed': True})
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, self.root / 'service.json')
        health = gate.read_json(self.health)
        health['truncation'] = 'pending'
        self.health.write_text(json.dumps(health))
        diagnostic_gate = self.root / 'new.json'
        issued = gate.issue_gate(self.record, diagnostic_gate, self.health)
        self.assertIn('health_observation', issued)
        gate.check_gate(diagnostic_gate, self.root / 'service.json')

    def make_rebind(self):
        gate.issue_gate(self.record, self.output)
        current = dict(self.service, service_instance_id='boot-2')
        runtime = dict(service_instance_id='boot-2', graph_capture_completed=True, graph_replays=2,
                       stable_identity_sha256=gate.content_sha256(gate.stable_service_identity(current)))
        runtime_path = self.root / 'restart-runtime.json'
        runtime_path.write_text(json.dumps(runtime))
        current['runtime_evidence_sha256'] = gate.sha256(runtime_path)
        current_path = self.root / 'restarted-service.json'
        current_path.write_text(json.dumps(current))
        regression_path = self.root / 'restart-regression.json'
        regression_path.write_text(json.dumps(dict(status='passed', service_sha256=gate.sha256(current_path),
                                                   evidence=gate.artifact(runtime_path))))
        evidence = dict(schema_version=1, source_service=self.refs['service'], current_service=gate.artifact(current_path),
                        runtime_evidence=gate.artifact(runtime_path), minimal_regression=gate.artifact(regression_path))
        evidence_path = self.root / 'rebind-evidence.json'
        evidence_path.write_text(json.dumps(evidence))
        return current_path, evidence_path, self.root / 'rebound-gate.json'

    def test_rebind_is_explicit_and_rechecks_original_evidence(self):
        current, evidence, output = self.make_rebind()
        with self.assertRaises(ValueError):
            gate.check_gate(self.output, current)
        gate.rebind_gate(self.output, current, evidence, output)
        self.assertTrue(gate.check_gate(output, current)['evaluation_reused'])
        with self.assertRaises(ValueError):
            gate.check_gate(output, current, model='different')
        with self.assertRaises(ValueError):
            gate.rebind_gate(output, current, evidence, self.root / 'chain.json')
        runtime = self.root / 'restart-runtime.json'
        runtime.write_text('{}')
        with self.assertRaises(ValueError):
            gate.check_gate(output, current)

    def test_rebind_rejects_source_configuration_and_device_changes(self):
        current, evidence, output = self.make_rebind()
        original = gate.read_json(current)
        for key, value in [('plugin_sha256', 'b' * 64), ('flaggems_vllm_installed', True),
                           ('launch_config', {'tp': 8}), ('host', 'host-b'), ('base_url', 'http://localhost:9000/v1/chat/completions')]:
            changed = dict(original, **{key: value})
            current.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaises(ValueError):
                gate.rebind_gate(self.output, current, evidence, output)

    def test_rebind_requires_two_observed_replays_even_with_consistent_hashes(self):
        current, evidence, output = self.make_rebind()
        runtime_path = self.root / 'restart-runtime.json'
        runtime = gate.read_json(runtime_path)
        runtime['graph_replays'] = 1
        runtime_path.write_text(json.dumps(runtime))
        service = gate.read_json(current)
        service['runtime_evidence_sha256'] = gate.sha256(runtime_path)
        current.write_text(json.dumps(service))
        receipt = gate.read_json(evidence)
        receipt.update(current_service=gate.artifact(current), runtime_evidence=gate.artifact(runtime_path))
        evidence.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, 'two replays'):
            gate.rebind_gate(self.output, current, evidence, output)

    def test_flaggems_vllm_presence_cannot_be_assumed(self):
        for change in ({'flaggems_vllm_installed': None}, {'flaggems_vllm_installed': True},
                       {'flaggems_vllm_installed': True, 'flaggems_vllm_sha256': 'bad'},
                       {'flaggems_vllm_sha256': 'a' * 64}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                gate.validate_service(dict(self.service, **change))
        gate.validate_service(dict(self.service, flaggems_vllm_installed=True, flaggems_vllm_sha256='c' * 64))

    def test_formal_config_accepts_timeouts_but_rejects_invalid_config(self):
        gate.validate_config(self.cfg, self.service)
        for changes in ({'model_name': 'different'}, {'allow_timeouts': 'yes'}, {'limit': 1}, {'seed': None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                gate.validate_config(dict(self.cfg, **changes), self.service)

    def test_original_runner_unchanged(self):
        formal_accuracy.load_runner()

    def test_formal_gate_accepts_complete_multi_filter_native_samples(self):
        names = ['strict-match', 'flexible-extract']
        self.provenance['task_config']['filter_list'] = [{'name': name, 'filter': []} for name in names]
        self.save('task_provenance', self.provenance)
        self.contract['task_provenance'] = self.refs['task_provenance']
        self.save('contract', self.contract)
        self.save('results', result_payload(self.cfg, self.provenance))
        samples = self.root / 'samples.jsonl'
        rows = [dict(row, filter=name) for row in map(json.loads, samples.read_text().splitlines()) for name in names]
        samples.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        self.refs['samples'] = gate.artifact(samples)
        self.record.write_text(json.dumps({'schema_version': 2, 'status': 'evaluated', 'process_succeeded': True,
                                          'artifacts': self.refs}))
        gate.issue_gate(self.record, self.output)
        gate.check_gate(self.output, self.root / 'service.json')

    def test_wrapper_runs_original_and_records_evidence(self):
        # No API/GPU access: exercise wrapper orchestration with the original runner
        # module, substituting only external preflight and the expensive task.
        runner = formal_accuracy.load_runner()
        config = dict(self.cfg, eval_model='fixture', output_root=str(self.root / 'outputs'))
        self.save('input-config', config)
        def task(cfg, task, run_dir):
            command = runner.build_command(cfg, task, run_dir / task)
            self.assertEqual(command[-2:], ['--seed', '42'])
            self.assertEqual(command[:3], [sys.executable, '-m', 'lm_eval'])
            task_dir = run_dir / task
            task_dir.mkdir()
            (task_dir / 'results_fixture.json').write_text(json.dumps(result_payload(cfg, self.provenance)))
            (task_dir / f'samples_{task}_fixture.jsonl').write_text((self.root / 'samples.jsonl').read_text())
            return runner.validate_samples(cfg, task, task_dir)
        args = type('Args', (), dict(config=self.root / 'input-config.json', service_manifest=self.root / 'service.json',
                                    contract=self.root / 'contract.json', evaluation_inspect=self.root / 'evaluation_inspect.json', preflight_only=False))()
        with patch.object(formal_accuracy, 'load_runner', return_value=runner), \
             patch.object(formal_accuracy, 'collect_provenance', return_value=self.provenance), \
             patch.object(runner, 'probe_service', return_value=(True, 'ready')), patch.object(runner, 'configure_environment'), \
             patch.object(runner, 'run_task', side_effect=task), \
             contextlib.redirect_stdout(io.StringIO()):
            formal_accuracy.run(args)
        records = list((self.root / 'outputs').rglob('run-record.json'))
        self.assertEqual(len(records), 1)
        gate.verify_run(records[0])

    def test_finalize_existing_run_reuses_frozen_outputs_without_inference(self):
        run_dir = self.root / 'existing-run'
        task_dir = run_dir / gate.TASK
        task_dir.mkdir(parents=True)
        result = task_dir / 'results_existing.json'
        samples = task_dir / f'samples_{gate.TASK}_existing.jsonl'
        result.write_text((self.root / 'results.json').read_text())
        samples.write_text((self.root / 'samples.jsonl').read_text())
        gate.write_new(run_dir / 'frozen-inputs.json', {
            key: self.refs[key] for key in (
                'contract', 'service', 'runner', 'evaluation_inspect',
                'task_provenance', 'config')
        })
        record = formal_accuracy.finalize_existing_run(run_dir)
        gate.verify_run(record)
        with self.assertRaises(FileExistsError):
            formal_accuracy.finalize_existing_run(run_dir)


if __name__ == '__main__':
    unittest.main()
