import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ControlTest(unittest.TestCase):
    def test_aliases_only(self):
        guard = load('target_guard', 'scripts/check-targets.py')
        inventory = {'_meta': {'hostvars': {'host-a': {}, 'host-b': {}}}, 'managed': {'hosts': ['host-a', 'host-b']}}
        self.assertEqual(guard.resolve_targets('host-a,host-b', inventory), ['host-a', 'host-b'])
        for value in ('', 'managed', 'all', '*', 'host-*', '@hosts', 'host-a,host-a', 'host-a,missing'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                guard.resolve_targets(value, inventory)

    def test_missing_limit_rejected_before_subprocess(self):
        guard = load('target_guard2', 'scripts/check-targets.py')
        with patch.object(sys, 'argv', ['check-targets.py', 'health-check']), patch.object(guard.subprocess, 'run') as run, \
             contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            guard.main()
        run.assert_not_called()


class PerformanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_nonzero_exit_cannot_pass_with_success_count(self):
        for name in ('vllm_perf', 'sglang_perf'):
            m = load(name, f'evaluation/performance/{name}.py')
            output = 'Successful requests: 2\nBenchmark duration (s): 1\nTotal generated tokens: 20\n'
            with self.subTest(name=name), patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 7, output, 'late failure')), contextlib.redirect_stdout(io.StringIO()):
                args = [(10, 10, 2, 2), 1, self.tmp.name]
                args.append(['vllm'] if name == 'vllm_perf' else ['python3', '-m', 'sglang.bench_serving'])
                result = m.run_once(*args)
                self.assertFalse(result['valid'])
                self.assertEqual(result['returncode'], 7)

    def test_failed_warmup_or_measured_round_prevents_summary(self):
        for name in ('vllm_perf', 'sglang_perf'):
            m = load(name, f'evaluation/performance/{name}.py')
            valid = {'successful_requests': 2, 'valid': True, 'returncode': 0}
            for failure_index in (0, 1, 2):
                runs = [dict(valid) for _ in range(3)]
                runs[failure_index]['valid'] = False
                args = [(10, 10, 2, 2), str(Path(self.tmp.name) / 'case.csv'), self.tmp.name]
                if name == 'vllm_perf':
                    args.append([])
                with self.subTest(name=name, failure_index=failure_index), patch.object(m, 'run_once', side_effect=runs):
                    summary, failed = m.run_test_case(*args)
                    self.assertTrue(failed)
                    self.assertIsNone(summary)
            with self.assertRaises(ValueError):
                m.average_metrics([{'valid': False}])

    def test_main_exits_nonzero_on_exception_or_failed_case(self):
        m = load('vllm_main_test', 'evaluation/performance/vllm_perf.py')
        for outcome in (RuntimeError('broken CLI'), (None, True)):
            with self.subTest(outcome=outcome), patch.object(sys, 'argv', ['vllm_perf.py', '--model', 'test', '--tokenizer', 'test', '--output-dir', self.tmp.name]), \
                 patch.object(m, 'DEFAULT_TEST_CASES', [(10, 10, 2, 2)]), \
                 patch.object(m, 'run_test_case', side_effect=outcome if isinstance(outcome, Exception) else None, return_value=outcome), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                m.main()
            self.assertEqual(raised.exception.code, 1)

    def test_complete_rounds_keep_successful_summary(self):
        m = load('vllm_success_test', 'evaluation/performance/vllm_perf.py')
        runs = [{'valid': True, 'returncode': 0, 'successful_requests': 2, 'output_throughput': n} for n in (1, 20, 30)]
        with patch.object(m, 'run_once', side_effect=runs):
            summary, failed = m.run_test_case((10, 10, 2, 2), str(Path(self.tmp.name) / 'ok.csv'), self.tmp.name, [])
        self.assertFalse(failed)
        self.assertEqual(summary['Output tok/s'], 25)
        partial = m.average_metrics([{'valid': True, 'p99_ttft_ms': 3}, {'valid': True, 'p99_ttft_ms': None}])
        self.assertIsNone(partial['p99_ttft_ms'])


class MountParityTest(unittest.TestCase):
    def test_mount_reorder_preserves_parity_but_shared_path_changes_fail(self):
        import copy
        m = load('mount_checker', 'scripts/verify-container-mounts.py')
        source = {'Mounts': [{'Type': 'bind', 'Source': '/shared', 'Destination': '/workspace', 'RW': True, 'Propagation': 'rprivate'},
                             {'Type': 'volume', 'Source': '/vol/data', 'Destination': '/data', 'Name': 'data', 'RW': True}],
                  'HostConfig': {'Mounts': [{'Target': '/data', 'VolumeOptions': {'Subpath': 'a'}}]}}
        target = copy.deepcopy(source)
        target['Mounts'].reverse()
        self.assertEqual(m.compare(source, target)['mount_parity'], 'passed')
        for key, value in [('Source', '/copy'), ('RW', False), ('Propagation', 'rshared')]:
            target = copy.deepcopy(source)
            target['Mounts'][0][key] = value
            with self.subTest(key=key):
                self.assertEqual(m.compare(source, target)['mount_parity'], 'failed')
        target = copy.deepcopy(source)
        target['HostConfig']['Mounts'][0]['VolumeOptions']['Subpath'] = 'b'
        report = m.compare(source, target)
        self.assertEqual(report['mount_parity'], 'failed')
        self.assertEqual(report['image_lineage'], 'unverified')


class NativePerformanceTest(unittest.TestCase):
    def test_native_counts_and_exit_code_are_both_required(self):
        import json
        m = load('native_perf', 'evaluation/performance/vllm_perf.py')
        with tempfile.TemporaryDirectory() as directory:
            for code, count, expected in ((0, 20, True), (0, 19, False), (7, 20, False)):
                def benchmark(cmd, **kwargs):
                    path = Path(cmd[cmd.index('--result-dir') + 1]) / cmd[cmd.index('--result-filename') + 1]
                    raw = {'num_prompts': 2, 'completed': 2, 'failed': 0, 'duration': 1.0,
                           'total_input_tokens': 20, 'total_output_tokens': count,
                           'errors': ['', ''], 'output_lens': [10, 10],
                           'request_throughput': 2.0, 'output_throughput': 20.0,
                           'total_token_throughput': 40.0}
                    raw.update({key: 1.0 for key in m.REQUIRED_PERFORMANCE_METRICS if key.endswith('_ms')})
                    path.write_text(json.dumps(raw))
                    return subprocess.CompletedProcess(cmd, code, 'Successful requests: 2\nBenchmark duration (s): 1\nTotal input tokens: 20\nTotal generated tokens: 20\n', '')
                with self.subTest(code=code, count=count), patch.object(m.subprocess, 'run', side_effect=benchmark), contextlib.redirect_stdout(io.StringIO()):
                    metrics = m.run_once((10, 10, 2, 2), 1, directory, ['vllm', '--seed', '42'])
                self.assertEqual(metrics['valid'], expected)

    def test_reference_average_does_not_drop_missing_rounds(self):
        m = load('legacy_all_perf', 'evaluation/performance/all_perf.py')
        good = {'Successful requests': 2}
        self.assertIsNone(m.compute_average([good, good, None, good, good]))
        self.assertIsNone(m.compute_average([None, good, good, good, good]))
        self.assertIsNotNone(m.compute_average([good] * 5))


if __name__ == '__main__':
    unittest.main()
