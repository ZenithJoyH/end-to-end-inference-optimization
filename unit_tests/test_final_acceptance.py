"""Synthetic native receipts exercise project acceptance without a model service."""
import copy
import json
from pathlib import Path
import unittest

import test_performance_comparison as fixtures
import test_acceptance as accuracy_fixture
import final_acceptance as final

native = fixtures.compare


class FinalAcceptanceTests(unittest.TestCase):
    def setUp(self):
        f = fixtures.ComparisonTest()
        f.setUp()
        self.addCleanup(f.doCleanups)
        self.f = f
        plan = copy.deepcopy(f.plan)
        plan['cases'] = [dict(id=name, input_tokens=p, output_tokens=d, concurrency=c, requests=n,
                              load_mode='finite_batch', stage='mixed', request_rate=None, burstiness=1)
                         for name, (p, d, c, n) in native.REQUIRED_SCENARIOS.items()]
        first = native.read_json(f.paths[0])
        baseline = native.service_identity(native.read_json(first['artifacts']['service']['path']))
        f.contract.update(scope='formal', project_scope=dict(lifecycle='final-all-targets', case_id='case-a',
            baseline_id='anchor-a', baseline_kind='anchor', scenario_ids=list(native.REQUIRED_SCENARIOS),
            baseline_identity_sha256=native.identity_digest(baseline)))
        f.contract['guardrails'].append(dict(metric='p99_tpot_ms', direction='lower', max_regression=0.1))
        contract_ref = f.save(f.contract_path, f.contract)
        for path in f.paths:
            record = native.read_json(path)
            record['artifacts']['comparison_contract'] = contract_ref
            record['artifacts']['plan'] = f.save(Path(record['artifacts']['plan']['path']), plan)
            rows = []
            for case in plan['cases']:
                for old in record['rounds']:
                    row = copy.deepcopy(old)
                    i = row['round_id']
                    row['case_id'] = case['id']
                    row['seed'] = fixtures.performance_plan.round_seed(42, case, i)
                    raw = native.read_json(old['raw_result']['path'])
                    n, p, d = case['requests'], case['input_tokens'], case['output_tokens']
                    raw.update(num_prompts=n, completed=n, max_concurrency=case['concurrency'],
                               input_lens=[p] * n, output_lens=[d] * n, errors=[''] * n,
                               total_input_tokens=p*n, total_output_tokens=d*n)
                    for metric, count in [('request_throughput', n), ('request_goodput', n),
                                          ('output_throughput', d*n), ('total_token_throughput', (p+d)*n)]:
                        raw[metric] = count/raw['duration']
                    raw_path = (path.parent / f'{case["id"]}-{i}.json').resolve()
                    row['raw_result'] = f.save(raw_path, raw)
                    validation = native.read_json(old['validation']['path'])
                    stdout = (f"Successful requests: {n}\nBenchmark duration (s): {raw['duration']:.2f}\n"
                              f"Total input tokens: {p*n}\nTotal generated tokens: {d*n}\n")
                    validation.update(command=fixtures.performance_plan.build_round_command(plan, case, row['seed'], raw_path),
                                      stdout_metrics=fixtures.vllm_perf.extract_metrics(stdout),
                                      output=f.save(raw_path.with_suffix('.output.json'), dict(stdout=stdout, stderr='')))
                    row['validation'] = f.save(raw_path.with_suffix('.validation.json'), validation)
                    rows.append(row)
            record['rounds'] = rows
            if record['role'] == 'candidate':
                accuracy = accuracy_fixture.GateTest()
                accuracy.setUp()
                self.addCleanup(accuracy.doCleanups)
                accuracy.service = native.read_json(record['artifacts']['service']['path'])
                accuracy.save('service', accuracy.service)
                accuracy_record = native.read_json(accuracy.record)
                accuracy_record['artifacts']['service'] = accuracy.refs['service']
                f.save(accuracy.record, accuracy_record)
                accuracy_fixture.gate.issue_gate(accuracy.record, accuracy.output)
                record['artifacts']['accuracy_gate'] = native.artifact(accuracy.output)
                record['scope'] = 'formal_candidate'
            f.save(path, record)
        candidate_ref = native.artifact(f.paths[2])
        phases = {name: {phase: dict(run_record=candidate_ref, case_id=name, method='client-proxy',
                                    residual_costs='includes queue, scheduling and network')
                         for phase in ('prefill', 'decode')} for name in native.REQUIRED_SCENARIOS}
        self.manifest = dict(schema_version=1, contract=contract_ref,
                             run_records=[native.artifact(p) for p in f.paths], phase_evidence=phases)
        self.path = f.root / 'final-manifest.json'

    def result(self):
        self.f.save(self.path, self.manifest)
        return final.validate(self.path)

    def test_four_scenario_native_receipts_pass_final_acceptance(self):
        result = self.result()
        self.assertEqual(result['status'], 'passed', result)
        self.assertTrue(result['final_acceptance'])

    def test_journal_acceptance_binds_case_and_service_identity(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
        import project_gates
        self.f.save(self.path, self.manifest)
        record = native.read_json(self.f.paths[0])
        service = native.read_json(record['artifacts']['service']['path'])
        scope = dict(model=service['model_name'], host=service['host'], case_id='case-a', baseline_id='anchor-a')
        root = Path(__file__).resolve().parents[1]
        check = dict(kind='acceptance', manifest=str(self.path))
        self.assertEqual(project_gates.run_check(root, check, scope)['status'], 'passed')
        with self.assertRaises(ValueError):
            project_gates.run_check(root, check, dict(scope, case_id='different-case'))

    def test_missing_phase_and_modified_raw_evidence_cannot_pass(self):
        first = next(iter(native.REQUIRED_SCENARIOS))
        del self.manifest['phase_evidence'][first]['decode']
        self.assertEqual(self.result()['status'], 'incomplete')
        record = native.read_json(self.f.paths[2])
        Path(record['rounds'][0]['raw_result']['path']).write_text('{}')
        self.assertEqual(self.result()['status'], 'incomplete')

    def test_final_scope_cannot_omit_targets_or_use_entry_baseline(self):
        scope = self.f.contract['project_scope']
        for changed in (dict(scope, scenario_ids=scope['scenario_ids'][:1]),
                        dict(scope, baseline_kind='scenario-entry')):
            with self.assertRaises(ValueError): native.validate_project_scope(changed)
        intermediate = dict(scope, lifecycle='intermediate-single-target', baseline_kind='scenario-entry',
                            scenario_ids=scope['scenario_ids'][:1])
        native.validate_project_scope(intermediate)

    def test_mislabeled_reduced_workload_is_rejected(self):
        plan = native.performance_plan.load_plan(native.read_json(self.f.paths[0])['artifacts']['plan']['path'])
        plan['cases'][0]['requests'] = 8
        with self.assertRaisesRegex(ValueError, 'shortened'):
            native.check_project_plan(plan, self.f.contract['project_scope'])


if __name__ == '__main__': unittest.main()
