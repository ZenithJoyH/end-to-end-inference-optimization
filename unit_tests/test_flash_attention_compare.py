"""CPU-only contract checks; these do not claim hardware performance coverage."""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'benchmarks/flash_attention_compare.py'
spec = importlib.util.spec_from_file_location('flash_attention_compare', SCRIPT)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class FlashAttentionCompareTests(unittest.TestCase):
    def cli(self, *arguments):
        return subprocess.run([sys.executable, '-P', str(SCRIPT), *map(str, arguments)],
                              capture_output=True, text=True)

    def test_exact_original_catalog(self):
        catalog = bench.cases()
        self.assertEqual(len(catalog), 18)
        self.assertEqual(len({case['id'] for case in catalog}), 18)
        decode = {(len(case['ql']), tuple(set(case['kl']))) for case in catalog if case['stage'] == 'decode'}
        self.assertEqual(decode, {(batch, (kv,)) for batch in [1, 8, 32, 64] for kv in [1024, 2048, 4096]})
        self.assertEqual(catalog[0]['ql'], [17, 5])
        self.assertEqual(catalog[-1]['kl'], [1009, 1021])

    def test_list_needs_no_candidate_or_torch(self):
        result = self.cli('--list')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)), 18)
        probe = subprocess.run([sys.executable, '-P', '-c',
                                f"import runpy,sys; runpy.run_path({str(SCRIPT)!r}); assert 'torch' not in sys.modules"],
                               capture_output=True, text=True)
        self.assertEqual(probe.returncode, 0, probe.stderr)

    def test_dry_run_does_not_execute_candidate_or_create_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.py'
            marker = root / 'executed'
            candidate.write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
            output = root / 'results'
            result = self.cli('--candidate', candidate, '--output-dir', output,
                              '--case', 'decode-b64-k1024', '--dry-run')
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads(result.stdout)
            self.assertEqual(config['candidate_sha256'], bench.file_sha256(candidate))
            self.assertEqual(config['cases'][0]['id'], 'decode-b64-k1024')
            self.assertEqual(config['rounds'], 9)
            self.assertFalse(marker.exists())
            self.assertFalse(output.exists())

    def test_source_mismatch_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'candidate.py'
            source.write_text('raise RuntimeError("must never execute")\n')
            result = self.cli('--candidate', source, '--expected-sha256', '0' * 64, '--dry-run')
            self.assertEqual(result.returncode, 1)
            self.assertIn('SHA256 mismatch', result.stderr)

    def test_existing_run_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'candidate.py'
            source.write_text('raise RuntimeError("must never execute")\n')
            old = root / 'old'
            old.mkdir()
            evidence = old / 'result.json'
            evidence.write_text('unique evidence')
            result = self.cli('--candidate', source, '--output-dir', root, '--run-id', 'old')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(evidence.read_text(), 'unique evidence')
            self.assertEqual(list(old.iterdir()), [evidence])

    def test_bad_case_timeout_and_path_are_rejected(self):
        for options in [
            ['--cases', 'decode-b1-k1024,decode-b1-k1024'],
            ['--case', 'not-a-case'], ['--run-id', '../outside'],
            ['--timeout', 'nan'], ['--total-budget', 'inf'],
            ['--q-heads', '15'],
        ]:
            with self.subTest(options=options):
                result = self.cli('--candidate', 'unused.py', *options)
                self.assertEqual(result.returncode, 2)

    def test_failed_and_incomplete_cases_remain_in_summary(self):
        failed = bench.summarize({'case_id': 'failed-shape', 'status': 'failed', 'error': 'bad numerics'})
        incomplete = bench.summarize({'case_id': 'slow-shape', 'status': 'incomplete-timeout'})
        self.assertIsNone(failed['native_us'])
        self.assertEqual(bench.result_exit_code([incomplete]), 2)
        self.assertEqual(bench.result_exit_code([failed, incomplete]), 1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bench.save_summary(root, [failed, incomplete])
            self.assertEqual(len(json.loads((root / 'summary.json').read_text())), 2)
            with (root / 'summary.csv').open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row['status'] for row in rows], ['failed', 'incomplete-timeout'])
            self.assertEqual(rows[0]['native_us'], '')

    def test_slower_candidate_is_successful_measurement(self):
        result = {'case': {'id': 'x', 'stage': 'decode', 'ql': [1], 'kl': [1024]},
                  'status': 'complete', 'summary': {
                      'native': {'median_us': 10}, 'candidate': {'median_us': 20},
                      'speedup': 0.5, 'native_before_after_drift': 0.001}}
        row = bench.summarize(result)
        self.assertEqual(row['candidate_over_native'], 2)
        self.assertEqual(bench.result_exit_code([row]), 0)

    def test_exhausted_budget_keeps_case_without_running_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'candidate.py'
            source.write_text('raise RuntimeError("must never execute")\n')
            result = self.cli('--candidate', source, '--output-dir', root, '--run-id', 'budget',
                              '--case', 'decode-b1-k1024', '--total-budget', '1e-300')
            self.assertEqual(result.returncode, 2, result.stderr)
            rows = json.loads((root / 'budget/summary.json').read_text())
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['case_id'], 'decode-b1-k1024')
            self.assertEqual(rows[0]['status'], 'incomplete-total-budget')


if __name__ == '__main__':
    unittest.main()
