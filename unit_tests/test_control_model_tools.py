"""Local rejection-path tests for control and case tools; no remote/device use."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / 'models/XingChen4-29B-A4B/ppu/optimize/tools'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOUNTS = load('mount_guard_extra', ROOT / 'scripts/verify-container-mounts.py')
TARGETS = load('target_guard_extra', ROOT / 'scripts/check-targets.py')
SANITY = load('case_sanity', TOOL_DIR / 'sanity.py')
SUMMARY = load('legacy_summary', TOOL_DIR / 'collect_perf_summary.py')
LAUNCH = load('case_launch', TOOL_DIR / 'launch_service.py')


class MountAndTargetTest(unittest.TestCase):
    def source(self):
        return {'Mounts': [{'Type': 'bind', 'Source': '/src', 'Destination': '/dst', 'RW': True,
                            'Mode': 'rw', 'Propagation': 'rprivate'}]}

    def test_equivalent_mode_spelling_preserves_parity(self):
        source = self.source()
        target = copy.deepcopy(source)
        target['Mounts'][0]['Mode'] = ''
        target['HostConfig'] = {'Mounts': None}
        self.assertEqual(MOUNTS.compare(source, target)['mount_parity'], 'passed')
        target['Mounts'][0]['Mode'] = 'z'
        self.assertEqual(MOUNTS.compare(source, target)['mount_parity'], 'failed')

    def test_unknown_effective_and_declared_mount_options_are_not_ignored(self):
        source = self.source()
        target = copy.deepcopy(source)
        target['Mounts'][0]['RuntimeOption'] = 'changed'
        self.assertEqual(MOUNTS.compare(source, target)['mount_parity'], 'failed')
        target = copy.deepcopy(source)
        target['HostConfig'] = {'Mounts': [{'Target': '/dst', 'Consistency': 'cached'}]}
        self.assertEqual(MOUNTS.compare(source, target)['mount_parity'], 'failed')

    def test_duplicate_or_missing_effective_mounts_and_conflicting_rw_fail(self):
        for alter in (
            lambda v: v['Mounts'].append({'Type': 'tmpfs', 'Destination': '/dst'}),
            lambda v: v.update(HostConfig={'Mounts': [{'Target': '/absent'}]}),
            lambda v: v.update(HostConfig={'Mounts': [{'Target': '/dst'}, {'Target': '/dst'}]}),
            lambda v: v['Mounts'][0].update(Mode='ro'),
            lambda v: v['Mounts'][0].pop('Destination'),
        ):
            value = self.source()
            alter(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                MOUNTS.normalize(value)

    def test_host_group_name_collision_is_not_an_explicit_host_limit(self):
        inventory = {'_meta': {'hostvars': {'host-a': {}, 'host-b': {}}}, 'host-a': {'hosts': ['host-b']}}
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            TARGETS.resolve_targets('host-a', inventory)

    @unittest.skipUnless((ROOT / '.venv/bin/python').exists(), 'control runtime not bootstrapped')
    def test_bastion_error_on_stderr_is_rejected_by_real_playbook_expressions(self):
        program = '''
from pathlib import Path
from types import SimpleNamespace
import yaml
from jinja2 import Environment
env = Environment()
for name in ('connectivity-check', 'health-check'):
    play = yaml.safe_load((Path('playbooks') / (name + '.yml')).read_text())[0]
    task = next(t for t in play['tasks'] if 'failed_when' in t)
    expression = env.compile_expression(task['failed_when'])
    assert not expression(hostname_result=SimpleNamespace(rc=0, stdout='host-a', stderr=''))
    for error in ('MATCH ASSET FAILED', '未发现匹配的资产'):
        assert expression(hostname_result=SimpleNamespace(rc=0, stdout='banner', stderr=error))
play = yaml.safe_load(Path('playbooks/accelerator-check.yml').read_text())[0]
checks = play['tasks'][-1]['ansible.builtin.assert']['that']
for error in ('MATCH ASSET FAILED', '未发现匹配的资产'):
    result = SimpleNamespace(rc=0, stdout='banner', stderr=error)
    assert not all(env.compile_expression(check)(accelerator_result=result) for check in checks)
'''
        result = subprocess.run([str(ROOT / '.venv/bin/python'), '-c', program], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class SanityTest(unittest.TestCase):
    def test_fixed_answers_reject_substrings_denials_and_repetition(self):
        for content, expected in [('21', '2'), ('12', '2'), ('.2', '2'), ('2 2 2', '2'), ('不是北京，是上海', '北京'), ('北京北京', '北京')]:
            with self.subTest(content=content):
                self.assertFalse(SANITY.answer_matches(content, expected))
        for content, expected in [('2', '2'), ('2.0', '2'), ('**21**。', '21'), ('北京。', '北京'), ('猫', '猫')]:
            with self.subTest(content=content):
                self.assertTrue(SANITY.answer_matches(content, expected))

    def test_base_and_endpoint_forms_do_not_duplicate_v1(self):
        for url in ('http://localhost:8000', 'http://localhost:8000/v1/', 'http://localhost:8000/v1/chat/completions'):
            self.assertEqual(SANITY.endpoint(url), 'http://localhost:8000/v1/chat/completions')
        with self.assertRaises(ValueError):
            SANITY.endpoint('http://localhost:8000/other')

    def test_existing_output_fails_before_requests(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'sanity.json'
            output.write_text('previous')
            with patch.object(SANITY.urllib.request, 'urlopen') as request, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                SANITY.main(['--base-url', 'http://localhost:8000', '--model', 'test', '--output', str(output)])
            request.assert_not_called()
            self.assertEqual(output.read_text(), 'previous')


class LegacySummaryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.validate = SUMMARY.load_validator()
        self.rounds = []
        for run in (1, 2, 3):
            raw = {'num_prompts': 2, 'completed': 2, 'failed': 0, 'errors': ['', ''], 'output_lens': [10, 10],
                   'duration': 2, 'total_input_tokens': 20, 'total_output_tokens': 20,
                   'request_throughput': 1, 'output_throughput': 10, 'total_token_throughput': 20,
                   'mean_ttft_ms': 2, 'p99_ttft_ms': 3, 'p99_tpot_ms': 4, 'p99_e2el_ms': 40}
            (self.root / f'p10-d10-c2-r{run}.json').write_text(json.dumps(raw))
            self.rounds.append({'run': run, 'case': [10, 10, 2, 2], 'metrics': {
                'successful_requests': 2, 'benchmark_duration': 2, 'total_input_tokens': 20, 'total_output_tokens': 20}})
        self.write_rounds()

    def write_rounds(self):
        (self.root / 'all-rounds.json').write_text(json.dumps(self.rounds))

    def test_complete_legacy_summary_keeps_numbers_but_not_formal_status(self):
        result = SUMMARY.collect(self.root, self.validate)
        self.assertEqual(result['steady']['output_throughput']['median_of_rounds'], 10)
        self.assertEqual(result['scope'], 'historical_performance_only')
        self.assertEqual(result['warmup_stability'], 'not_established_by_fixed_rounds')

    def test_mixed_workloads_are_not_labeled_as_first_case(self):
        self.rounds[1]['case'] = [20, 10, 2, 2]
        self.write_rounds()
        with self.assertRaisesRegex(ValueError, 'same workload'):
            SUMMARY.collect(self.root, self.validate)

    def test_nonfinite_or_inconsistent_throughput_cannot_enter_summary(self):
        path = self.root / 'p10-d10-c2-r2.json'
        original = json.loads(path.read_text())
        for value in (float('nan'), 100):
            path.write_text(json.dumps(dict(original, output_throughput=value)))
            with self.subTest(value=value), self.assertRaises(ValueError):
                SUMMARY.collect(self.root, self.validate)


class LaunchTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.env = {'MODEL_PATH': str(self.root), 'MODEL_NAME': 'test-model', 'PORT': '18000', 'DEVICE_IDS': '0',
                    'TP_SIZE': '1', 'ARTIFACT_ROOT': str(self.root / 'artifacts'), 'SERVICE_LABEL': 'test'}
        self.config = LAUNCH.settings(self.env)

    def test_invalid_port_devices_and_resources_fail(self):
        for update in ({'PORT': '65536'}, {'DEVICE_IDS': '0,0'}, {'MEMORY_UTILIZATION': 'nan'},
                       {'STARTUP_TIMEOUT': 'inf'}, {'TP_SIZE': '2'},
                       {'MAX_NUM_BATCHED_TOKENS': '0'}, {'PREFIX_CACHING': 'maybe'}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                LAUNCH.settings(dict(self.env, **update))

    def test_python_installation_and_module_style_do_not_hide_existing_service(self):
        processes = '\n'.join(['12 /opt/venv/bin/python -m vllm.entrypoints.openai.api_server',
                               '13 /usr/bin/python /opt/venv/bin/vllm serve model',
                               '14 /opt/venv/bin/vllm bench serve --model model', '15 python launch_service.py'])
        self.assertEqual(LAUNCH.serving_processes(processes), [12, 13])
        with patch.object(LAUNCH.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, processes, '')), \
                patch.object(LAUNCH.subprocess, 'Popen') as child, self.assertRaisesRegex(ValueError, 'already exists'):
            LAUNCH.launch(self.config, self.env)
        child.assert_not_called()

    def test_immediately_failed_child_does_not_set_current_service(self):
        child = Mock(pid=123, returncode=7)
        child.poll.return_value = 7
        with patch.object(LAUNCH.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')), \
                patch.object(LAUNCH.socket, 'socket'), patch.object(LAUNCH.subprocess, 'Popen', return_value=child), \
                self.assertRaisesRegex(RuntimeError, 'exited with status 7'):
            LAUNCH.launch(self.config, self.env)
        self.assertFalse((self.config['root'] / 'current-service').exists())
        self.assertEqual((self.config['root'] / 'test.pid').read_text().strip(), '123')

    def test_ready_child_gets_explicit_comparable_cache_settings(self):
        child = Mock(pid=123, returncode=None)
        with patch.object(LAUNCH.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')), \
                patch.object(LAUNCH.socket, 'socket'), patch.object(LAUNCH.subprocess, 'Popen', return_value=child) as create, \
                patch.object(LAUNCH, 'wait_ready'), contextlib.redirect_stdout(io.StringIO()):
            LAUNCH.launch(self.config, self.env)
        command = create.call_args.args[0]
        self.assertEqual(command[command.index('--max-num-batched-tokens') + 1], '8192')
        self.assertIn('--enable-prefix-caching', command)
        self.assertEqual((self.config['root'] / 'current-service').read_text().strip(), 'test')

    def test_readiness_requires_health_and_the_requested_model(self):
        child = Mock(pid=123, returncode=None)
        child.poll.return_value = None
        health = io.StringIO(''); health.status = 200
        models = io.StringIO(json.dumps({'data': [{'id': 'test-model'}]}))
        with patch.object(LAUNCH.urllib.request, 'urlopen', side_effect=[contextlib.closing(health), contextlib.closing(models)]) as request:
            LAUNCH.wait_ready(child, 18000, 'test-model', 1)
        self.assertEqual([call.args[0] for call in request.call_args_list], ['http://127.0.0.1:18000/health', 'http://127.0.0.1:18000/v1/models'])
        wrong = io.StringIO(json.dumps({'data': [{'id': 'wrong-model'}]}))
        health = io.StringIO(''); health.status = 200
        with patch.object(LAUNCH.urllib.request, 'urlopen', side_effect=[contextlib.closing(health), contextlib.closing(wrong)]), \
                patch.object(LAUNCH.time, 'monotonic', side_effect=[0, 0.1, 0.9, 1.1]), patch.object(LAUNCH.time, 'sleep'), \
                self.assertRaisesRegex(RuntimeError, 'requested model is not listed'):
            LAUNCH.wait_ready(child, 18000, 'test-model', 1)


if __name__ == '__main__':
    unittest.main()
