"""Offline discovery preserves provenance and cannot upgrade metadata into proof."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/upstream_pr_query.py'
SPEC = importlib.util.spec_from_file_location('upstream_pr_query', SCRIPT)
QUERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUERY)


class UpstreamPrQueryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index, cls.source = QUERY.load_index(QUERY.DEFAULT_INDEX)

    def result(self, index=None, **filters):
        return QUERY.query_index(self.index if index is None else index, self.source, **filters)

    def changed(self, mutate):
        index = copy.deepcopy(self.index)
        mutate(index['entries'][0])
        return index

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True, timeout=10)

    def test_seed_is_a_small_valid_discovery_inventory(self):
        self.assertGreaterEqual(len(self.index['entries']), 4)
        self.assertLessEqual(len(self.index['entries']), 6)
        for entry in self.index['entries']:
            self.assertTrue(entry['metadata_verified'])
            self.assertEqual(entry['review']['level'], 'discovery')
            self.assertEqual(entry['applicability']['current_dispatch'], 'unknown')
        self.assertTrue(any(not entry['pr']['merged'] for entry in self.index['entries']))
        self.assertTrue(any(card['kind'] == 'local_record'
                            for entry in self.index['entries'] for card in entry['source_cards']))

    def test_provenance_hash_is_the_selected_index_bytes(self):
        self.assertEqual(self.source['sha256'], hashlib.sha256(QUERY.DEFAULT_INDEX.read_bytes()).hexdigest())
        output = self.result()
        self.assertEqual(output['source_index'], self.source)
        self.assertEqual(output['claim_scope'], QUERY.CLAIM_SCOPE)

    def test_filters_are_case_insensitive_and_combined_with_and(self):
        result = self.result(framework='VLLM', model='DEEPSEEK', operator='indexer_topk',
                             keywords=['graph persistent'], review_level='discovery')
        self.assertEqual([entry['pr']['number'] for entry in result['entries']], [37421])
        self.assertEqual(self.result(framework='vllm', model='Qwen3-Next',
                                     operator='mla_attention')['status'], 'no_matches')
        self.assertEqual(self.result(framework='vll')['total_matches'], 0)

    def test_chinese_keyword_and_duplicate_terms_are_supported(self):
        result = self.result(keywords=['融合', '融合'])
        self.assertEqual([entry['pr']['number'] for entry in result['entries']], [21116])
        self.assertEqual(result['query']['keywords'], ['融合'])

    def test_deterministic_order_and_limit_preserve_total_matches(self):
        reversed_index = copy.deepcopy(self.index)
        reversed_index['entries'].reverse()
        self.assertEqual(self.result(limit=2), self.result(reversed_index, limit=2))
        result = self.result(limit=2)
        self.assertEqual(result['total_matches'], len(self.index['entries']))
        self.assertEqual(result['returned'], 2)
        self.assertTrue(result['truncated'])

    def test_no_matches_and_empty_inventory_are_explicit(self):
        result = self.result(keywords=['unknown-model-never-present'])
        self.assertEqual((result['status'], result['total_matches'], result['entries']),
                         ('no_matches', 0, []))
        empty = copy.deepcopy(self.index)
        empty['entries'] = []
        self.assertEqual(self.result(empty)['status'], 'no_matches')

    def test_url_must_be_exact_pull_request_not_issue_or_different_repository(self):
        for url in ('https://github.com/vllm-project/vllm/issues/21116',
                    'https://github.com/other/repo/pull/21116',
                    'https://example.com/vllm-project/vllm/pull/21116'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.result(self.changed(lambda entry: entry['pr'].update(url=url)))

    def test_commit_and_date_validation_rejects_ambiguous_or_contradictory_facts(self):
        changes = [lambda entry: entry['pr'].update(head_commit='070dfa4'),
                   lambda entry: entry['pr'].update(merge_commit='x' * 40),
                   lambda entry: entry.update(metadata_audited_on='2026-02-30'),
                   lambda entry: entry.update(metadata_audited_on='2020-01-01'),
                   lambda entry: entry['pr'].update(created_on='2026-12-01'),
                   lambda entry: entry['pr'].update(merged=False),
                   lambda entry: entry['pr'].update(state='open'),
                   lambda entry: entry['pr'].update(number=True)]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.result(self.changed(change))

    def test_metadata_verification_is_bound_to_head_and_does_not_promote_review(self):
        self.assertEqual(self.result(review_level='diff_reviewed')['total_matches'], 0)
        for change in (lambda entry: entry['source_cards'][1].update(revision='f' * 40),
                       lambda entry: entry.update(metadata_verified=1),
                       lambda entry: entry.update(metadata_audited_on=None),
                       lambda entry: entry['source_cards'][1].update(audited_on='2026-11-12')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.result(self.changed(change))

    def test_review_upgrade_requires_its_own_dated_evidence(self):
        for level in ('diff_reviewed', 'target_reproduced'):
            with self.subTest(level=level), self.assertRaises(ValueError):
                self.result(self.changed(lambda entry: entry['review'].update(level=level)))
        for field, value in (('diff_reviewed_on', '2026-11-13'),
                             ('target_reproduced_on', '2026-11-13'),
                             ('diff_evidence', ['metadata']), ('target_scope', 'a fake claim')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.result(self.changed(lambda entry: entry['review'].update({field: value})))

    def reviewed_fixture(self):
        index = copy.deepcopy(self.index)
        entry = index['entries'][0]
        entry['source_cards'].append({
            'id': 'diff-test-fixture', 'kind': 'upstream_diff', 'location': entry['pr']['url'] + '/files',
            'revision': entry['pr']['head_commit'], 'audited_on': '2026-11-13',
            'note': 'Synthetic unit-test evidence only; not a real review.'})
        entry['review'].update(level='diff_reviewed', diff_reviewed_on='2026-11-13',
                               diff_evidence=['diff-test-fixture'])
        return index

    def test_diff_review_and_target_reproduction_remain_distinct(self):
        index = self.reviewed_fixture()
        self.assertEqual(self.result(index, review_level='diff_reviewed')['total_matches'], 1)
        self.assertEqual(self.result(index, review_level='target_reproduced')['total_matches'], 0)
        entry = index['entries'][0]
        entry['source_cards'].append({
            'id': 'target-test-fixture', 'kind': 'target_evidence',
            'location': 'https://github.com/example/repo/blob/' + 'a' * 40 + '/test-only.json',
            'revision': entry['pr']['head_commit'], 'audited_on': '2026-11-13',
            'note': 'Synthetic unit-test fixture; no hardware measurement was performed.'})
        entry['review'].update(level='target_reproduced', target_reproduced_on='2026-11-13',
                               target_scope='Synthetic unit-test target, no production claim',
                               target_evidence=['target-test-fixture'])
        self.assertEqual(self.result(index, review_level='target_reproduced')['total_matches'], 1)
        self.assertEqual(entry['applicability']['current_dispatch'], 'unknown')
        entry['review']['target_scope'] = None
        with self.assertRaises(ValueError):
            self.result(index)

    def test_current_dispatch_cannot_be_certified_from_a_historical_index(self):
        with self.assertRaises(ValueError):
            self.result(self.changed(lambda entry: entry['applicability'].update(current_dispatch='hit')))

    def test_source_locators_never_escape_or_trigger_source_reads(self):
        for location in ('../outside.txt', '/etc/passwd', 'docs/../../outside.txt',
                         'docs\\outside.txt', 'file:///etc/passwd'):
            index = self.changed(lambda entry: entry['source_cards'][0].update(
                kind='local_record', location=location, revision=None))
            with self.subTest(location=location), self.assertRaises(ValueError):
                self.result(index)
        with tempfile.TemporaryDirectory() as directory:
            selected = Path(directory) / 'selected.json'
            selected.write_text(json.dumps(self.index), encoding='utf-8')
            original = Path.read_bytes
            reads = []

            def read_only_selected(path):
                reads.append(path)
                self.assertEqual(path, selected.resolve())
                return original(path)

            with mock.patch.object(Path, 'read_bytes', read_only_selected):
                index, source = QUERY.load_index(selected)
                self.assertEqual(QUERY.query_index(index, source)['status'], 'matched')
            self.assertEqual(reads, [selected.resolve()])

    def test_duplicate_ids_prs_and_unknown_fields_are_rejected(self):
        for changes in ({'id': self.index['entries'][1]['id']}, {'command': 'never execute me'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.result(self.changed(lambda entry: entry.update(changes)))
        index = copy.deepcopy(self.index)
        duplicate = copy.deepcopy(index['entries'][0])
        duplicate['id'] = 'different-id-same-pr'
        index['entries'].append(duplicate)
        with self.assertRaises(ValueError):
            self.result(index)

    def test_bad_source_kinds_and_control_characters_fail_closed(self):
        for change in (lambda entry: entry['source_cards'][0].update(kind=[]),
                       lambda entry: entry['source_cards'][0].update(location='https://example.com/x'),
                       lambda entry: entry.update(summary='bad\x1b[31m'),
                       lambda entry: entry['review'].update(diff_evidence=['missing'])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.result(self.changed(change))

    def test_cli_text_json_help_and_empty_results(self):
        result = self.run_cli('--framework', 'vllm', '--model', 'DeepSeek', '--operator',
                              'indexer_topk', 'graph', 'persistent', '--format', 'json')
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed['entries'][0]['pr']['number'], 37421)
        text = self.run_cli('--model', 'Qwen3-Next')
        self.assertEqual(text.returncode, 0, text.stderr)
        for marker in ('SHA256:', 'Review: discovery', 'Current dispatch: unknown', 'Source [metadata/'):
            self.assertIn(marker, text.stdout)
        empty = self.run_cli('--model', 'not-a-model', '--format', 'json')
        self.assertEqual(empty.returncode, 0)
        self.assertEqual(json.loads(empty.stdout)['status'], 'no_matches')
        help_result = self.run_cli('--help')
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('never opened or executed', help_result.stdout)

    def test_cli_rejects_invalid_json_indexes_without_a_success_result(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            for content in ('{"schema_version":1,"schema_version":1}', '{"value":NaN}', '[]'):
                path.write_text(content, encoding='utf-8')
                result = self.run_cli('--index', path, '--format', 'json')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')

    def test_invalid_limits_and_review_filters_are_errors(self):
        for limit in (0, -1, 1001, True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.result(limit=limit)
        self.assertEqual(self.run_cli('--review-level', 'verified').returncode, 2)
        self.assertEqual(self.run_cli('--index', '/path/that/does/not/exist').returncode, 2)


if __name__ == '__main__':
    unittest.main()
