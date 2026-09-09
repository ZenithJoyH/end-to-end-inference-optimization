"""Regression cases for false success, workload drift and misleading trace sums."""
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
sys.path.insert(0, str(ROOT / 'evaluation/performance'))
import sglang_perf
import vllm_profile
import trace_to_summary


class ProfilingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def args(self, extra=()):
        return vllm_profile.parse_args(['--model', 'test', '--tokenizer', 'tok',
            '--case', '10,10,2,2', '--runs', '3', '--warmup-rounds', '1',
            '--output-dir', str(self.root), *extra])

    def report(self):
        return json.loads(next(self.root.rglob('diagnostic.json')).read_text())

    def test_failed_warmup_stops_and_has_no_success_summary(self):
        bad = {'valid': False, 'returncode': 7, 'p99_ttft_ms': float('nan')}
        with patch.object(vllm_profile.vllm_perf, 'run_once', return_value=bad) as run, contextlib.redirect_stdout(io.StringIO()):
            code = vllm_profile.run_diagnostic(self.args(['--no-profile']))
        self.assertEqual(code, 1)
        run.assert_called_once()
        report = self.report()
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['summaries'], [])
        self.assertEqual(report['rounds'][0]['metrics']['p99_ttft_ms'], {'invalid_number': 'nan'})

    def test_profile_without_new_trace_is_incomplete(self):
        traces = self.root / 'traces'
        traces.mkdir()
        (traces / 'old.json').write_text('{"traceEvents": []}')
        with patch.object(vllm_profile.vllm_perf, 'run_once', return_value={'valid': True}), contextlib.redirect_stdout(io.StringIO()):
            code = vllm_profile.run_diagnostic(self.args(['--profile-dir', str(traces)]))
        self.assertEqual(code, 2)
        self.assertEqual(self.report()['status'], 'incomplete')
        self.assertFalse(self.report()['rounds'][-1]['traces'])

    def test_benchmark_json_and_partial_export_cannot_prove_profile_capture(self):
        traces = self.root / 'traces'
        traces.mkdir()
        before = vllm_profile.trace_snapshot(traces)
        (traces / 'native.json').write_text('{"completed": 2}')
        (traces / 'partial.json').write_text('{"traceEvents": [')
        self.assertEqual(vllm_profile.new_trace_artifacts(before, vllm_profile.trace_snapshot(traces)), [])

    def test_profiled_and_unprofiled_measurements_are_not_averaged_together(self):
        traces = self.root / 'traces'
        traces.mkdir()
        def run(case, run_id, output_dir, command, **kwargs):
            if '--profile' in command:
                (traces / 'worker.pt.trace.json').write_text('{"traceEvents": [{"ph":"X","name":"op","cat":"kernel","dur":1}]}')
            return {'valid': True, 'output_throughput': 10 if '--profile' in command else 100}
        args = self.args(['--profile-dir', str(traces)])
        with patch.object(vllm_profile.vllm_perf, 'run_once', side_effect=run), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vllm_profile.run_diagnostic(args), 0)
        values = {row['profile_requested']: row['metrics']['output_throughput'] for row in self.report()['summaries']}
        self.assertEqual(values, {False: 100, True: 10})
        self.assertTrue(self.report()['rounds'][-1]['traces'][0]['sha256'])

    def test_exception_produces_failed_evidence(self):
        with patch.object(vllm_profile.vllm_perf, 'run_once', side_effect=OSError('launch failed')), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vllm_profile.run_diagnostic(self.args(['--no-profile'])), 1)
        self.assertIn('launch failed', self.report()['errors'][0])

    def test_dry_run_sends_no_request_or_creates_output(self):
        with patch.object(vllm_profile.vllm_perf, 'run_once') as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vllm_profile.run_diagnostic(self.args(['--no-profile', '--dry-run'])), 0)
        run.assert_not_called()
        self.assertFalse(list(self.root.iterdir()))

    def test_invalid_profile_arguments_rejected(self):
        for extra in ([], ['--no-profile', '--warmup-rounds', '3'], ['--no-profile', '--case', '10,1,2,2']):
            with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.args(extra)


class SGLangTest(unittest.TestCase):
    def raw(self):
        result = dict(backend='sglang', dataset_name='random', random_input_len=10, random_output_len=10,
                      random_range_ratio=0.0, max_concurrency=2, request_rate=float('inf'),
                      completed=2, duration=1.0, total_input_tokens=20, total_output_tokens=20,
                      input_lens=[10,10], output_lens=[10,10], errors=['',''],
                      request_throughput=2., output_throughput=20., total_throughput=40.)
        result.update({key: 1.0 for key in sglang_perf.vllm_perf.REQUIRED_PERFORMANCE_METRICS if key.endswith('_ms')})
        result.update({f'{stat}_e2e_latency_ms': 5. for stat in ('mean', 'median', 'p99')})
        return result

    def stdout(self):
        return 'Successful requests: 2\nBenchmark duration (s): 1.00\nTotal input tokens: 20\nTotal generated tokens: 20\n'

    def test_native_schema_rejects_wrong_count_workload_and_metrics(self):
        _, report = sglang_perf.validate_result((10,10,2,2), self.raw(), self.stdout())
        self.assertFalse(report['errors'])
        for key, value in [('completed', 1), ('input_lens', [10]), ('max_concurrency', None),
                           ('request_rate', 2), ('p99_ttft_ms', float('nan')), ('output_throughput', 200)]:
            raw = self.raw()
            raw[key] = value
            with self.subTest(key=key):
                _, report = sglang_perf.validate_result((10,10,2,2), raw, self.stdout())
                self.assertTrue(report['errors'])

    def test_run_retains_native_output_and_nonzero_exit_cannot_pass(self):
        for code in (0, 7):
            with tempfile.TemporaryDirectory() as directory:
                def launch(cmd, **kwargs):
                    Path(cmd[cmd.index('--output-file')+1]).write_text(json.dumps(self.raw())+'\n')
                    return subprocess.CompletedProcess(cmd, code, self.stdout(), '')
                with patch.object(sglang_perf.subprocess, 'run', side_effect=launch), contextlib.redirect_stdout(io.StringIO()):
                    metrics = sglang_perf.run_once((10,10,2,2), 1, directory, ['python', '--seed', '42'])
                self.assertEqual(metrics['valid'], code == 0)
                self.assertEqual(len(list(Path(directory).glob('*.validation.json'))), 1)

    def test_timeout_keeps_output_and_failed_record(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(sglang_perf.subprocess, 'run',
                side_effect=subprocess.TimeoutExpired(['python'], 1, output=b'partial')), contextlib.redirect_stdout(io.StringIO()):
            metrics = sglang_perf.run_once((10,10,2,2), 1, directory, ['python'], timeout_s=1)
            self.assertFalse(metrics['valid'])
            self.assertEqual(metrics['returncode'], 124)
            report = json.loads(next(Path(directory).glob('*.validation.json')).read_text())
            self.assertEqual(report['stdout'], 'partial')

    def test_concurrency_and_arrival_rate_are_distinct(self):
        args = vllm_profile.parse_args(['--model','m','--tokenizer','t','--no-profile'], engine='sglang')
        command = sglang_perf.build_round_command((10,10,2,2), 1, sglang_perf.build_common_args(args), '/tmp/native.jsonl')
        self.assertEqual(command[command.index('--max-concurrency')+1], '2')
        self.assertEqual(command[command.index('--request-rate')+1], 'inf')
        self.assertEqual(command[command.index('--random-range-ratio')+1], '0')
        self.assertNotIn('--dataset-path', command)
        self.assertEqual(command[0], sys.executable)


class TraceTest(unittest.TestCase):
    def test_runtime_and_stream_metadata_do_not_count_as_device_time(self):
        events = [{'ph':'X','name':'cudaLaunchKernel','cat':'cuda_runtime','args':{'stream':7},'dur':10},
                  {'ph':'X','name':'matmul','cat':'kernel','dur':5},
                  {'ph':'X','name':'enqueue','cat':'vendor_unknown','args':{'stream':7},'dur':4}]
        cpu, device, unknown = trace_to_summary.aggregate_events(events)
        self.assertEqual(cpu['cudaLaunchKernel']['total_us'], 10)
        self.assertEqual(set(device), {'matmul'})
        self.assertEqual(set(unknown), {'enqueue'})

    def test_invalid_or_empty_trace_cannot_produce_success_report(self):
        for duration in (float('nan'), float('inf'), -1, '5', None):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                trace_to_summary.aggregate_events([{'ph':'X','name':'op','dur':duration}])
        with self.assertRaises(ValueError):
            trace_to_summary.aggregate_events([])

    def test_trace_summary_does_not_overwrite_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'trace.json'
            path.write_text(json.dumps([{'ph':'X','name':'op','cat':'kernel','dur':5}]))
            output = Path(directory)/'summary.txt'
            output.write_text('old report')
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(FileExistsError):
                trace_to_summary.process_trace_file(str(path), str(output))
            self.assertEqual(output.read_text(), 'old report')

    def test_directory_failure_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'bad.json').write_text('{}')
            with patch.object(sys, 'argv', ['trace_to_summary.py', directory]), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                trace_to_summary.main()
            self.assertEqual(raised.exception.code, 1)


class LegacyImportTest(unittest.TestCase):
    def test_legacy_import_does_not_mutate_or_require_real_stdout(self):
        spec = importlib.util.spec_from_file_location('legacy_import_check', ROOT/'evaluation/performance/all_perf.py')
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            spec.loader.exec_module(module)


if __name__ == '__main__':
    unittest.main()
