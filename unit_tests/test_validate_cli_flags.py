"""Saved-help checking is offline, scoped and never a service acceptance gate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/validate_cli_flags.py'
SPEC = importlib.util.spec_from_file_location('validate_cli_flags', SCRIPT)
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
HELP = '''usage: vllm serve [options]
Options:
  -h, --help            show help
  -tp TP, --tensor-parallel-size TP
  --dtype DTYPE         dtype selection
  --no-enable-prefix-caching
  --enabled             boolean flag
  --[no-]cache          explicit two-form spelling
  --mode {--not-a-flag,plain}  value choices are not options
  --sentence-only is unsupported in this version

Examples:
  vllm serve model --example-only
  unsupported --not-supported is absent
  Use --not-declared in a separate revision.
  --continuation-example  appears only in an example, not the option table
'''


def spec(*arguments):
    return {'schema_version': 1, 'argv': ['vllm', 'serve', 'model-id', *arguments],
            'command_scope': {'executable': 'vllm', 'subcommands': ['serve']},
            'help_scope': {'executable': 'vllm', 'subcommands': ['serve']},
            'positional_indices': [2]}


class ValidateCliFlagsTest(unittest.TestCase):
    def result(self, *arguments, help_text=HELP):
        return CLI.analyze(spec(*arguments), help_text)

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, arguments)],
                              capture_output=True, text=True, timeout=10)

    def test_known_flags_report_recognition_and_explicit_limits_only(self):
        result = self.result('--dtype', 'bfloat16', '--no-enable-prefix-caching')
        self.assertEqual(result['status'], 'flags_recognized')
        self.assertEqual([item['flag'] for item in result['recognized_flags']],
                         ['--dtype', '--no-enable-prefix-caching'])
        self.assertIn('no parameter-value', result['claim_scope'])
        self.assertIn('caller_declared_only', result['scope']['binding'])
        self.assertEqual(result['non_option_tokens'][-1]['role'], 'unclassified_value_or_positional')
        self.assertNotIn('passed', result.values())

    def test_unknown_option_and_implicit_negation_remain_incomplete(self):
        result = self.result('--dtype-extra=foo', '--enable-prefix-caching', '--no-enabled')
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual([item['flag'] for item in result['unknown_flags']],
                         ['--dtype-extra', '--enable-prefix-caching', '--no-enabled'])

    def test_help_prose_usage_examples_and_choices_do_not_declare_flags(self):
        options = CLI.help_options(HELP)
        for name in ('--example-only', '--not-supported', '--not-declared', '--not-a-flag',
                     '--sentence-only', '--continuation-example'):
            self.assertNotIn(name, options)
        result = self.result('--not-a-flag')
        self.assertEqual(result['status'], 'incomplete')

    def test_explicit_aliases_multi_character_short_names_and_equals(self):
        result = self.result('-tp=8', '--tensor-parallel-size', '8', '--dtype=bfloat16', '-h')
        self.assertEqual(result['status'], 'flags_recognized')
        self.assertEqual(result['recognized_flags'][0]['inline_value'], '8')
        self.assertEqual(result['recognized_flags'][2]['inline_value'], 'bfloat16')
        self.assertEqual(result['recognized_flags'][0]['help_lines'],
                         result['recognized_flags'][1]['help_lines'])
        for token in ('-tp8', '-htp', '--dt'):
            with self.subTest(token=token):
                self.assertEqual(self.result(token)['status'], 'incomplete')

    def test_boolean_values_do_not_consume_or_hide_the_next_option(self):
        result = self.result('--enabled', 'false', '--unknown')
        self.assertEqual(result['unknown_flags'][0]['index'], 5)
        self.assertEqual(result['non_option_tokens'][-1]['token'], 'false')
        adjacent = self.result('--enabled', '--dtype', 'bfloat16')
        self.assertEqual([item['flag'] for item in adjacent['recognized_flags']], ['--enabled', '--dtype'])

    def test_negative_decimal_and_exponent_values_are_not_options(self):
        result = self.result('--dtype', '-1', '-0.5', '-.5', '-1e-3', '-2E+4', '-')
        self.assertEqual(result['status'], 'flags_recognized')
        self.assertEqual(len(result['recognized_flags']), 1)
        self.assertEqual([item['token'] for item in result['non_option_tokens'][1:]],
                         ['-1', '-0.5', '-.5', '-1e-3', '-2E+4', '-'])

    def test_double_dash_makes_all_successor_tokens_literal(self):
        result = self.result('--enabled', '--', '--unknown', '-tp8')
        self.assertEqual(result['status'], 'flags_recognized')
        self.assertEqual(result['unknown_flags'], [])
        self.assertEqual(result['end_of_options_index'], 4)
        self.assertEqual([item['token'] for item in result['literal_tokens_after_terminator']],
                         ['--unknown', '-tp8'])

    def test_explicit_boolean_optional_notation_expands_only_its_own_two_forms(self):
        self.assertEqual(self.result('--cache', '--no-cache')['status'], 'flags_recognized')
        self.assertEqual(self.result('--no-dtype')['status'], 'incomplete')

    def test_subcommand_and_executable_scopes_cannot_be_cross_applied(self):
        for field, value in (('subcommands', ['bench', 'serve']), ('executable', '/other/vllm')):
            command = spec('--dtype', 'bfloat16')
            command['help_scope'][field] = value
            with self.subTest(field=field):
                result = CLI.analyze(command, HELP)
                self.assertEqual(result['status'], 'incomplete')
                self.assertFalse(result['scope']['declared_scopes_match'])
        command = spec('--enabled')
        command['command_scope']['subcommands'] = ['bench', 'serve']
        self.assertFalse(CLI.analyze(command, HELP)['scope']['command_prefix_matches'])

    def test_plain_argv_array_is_supported_but_does_not_establish_scope(self):
        result = CLI.analyze(['vllm', 'serve', 'model', '--dtype', 'bfloat16'], HELP)
        self.assertEqual(result['status'], 'incomplete')
        self.assertIsNone(result['scope']['declared_scopes_match'])

    def test_invalid_structures_strings_and_positional_conflicts_are_rejected(self):
        bad = ['vllm serve model --dtype bf16', {'schema_version': 1, 'argv': 'vllm --help'},
               [], [7], {'schema_version': True, 'argv': ['vllm']},
               {**spec(), 'extra_command': 'do not run'},
               {**spec('--enabled'), 'positional_indices': [3]},
               {**spec(), 'positional_indices': [0]},
               {**spec(), 'positional_indices': [True]},
               {**spec(), 'positional_indices': [2, 2]},
               {**spec(), 'positional_indices': [1]}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                CLI.analyze(value, HELP)

    def test_literal_positional_after_terminator_can_start_with_dash(self):
        command = spec('--', '--literal')
        command['positional_indices'] = [2, 4]
        result = CLI.analyze(command, HELP)
        self.assertTrue(result['literal_tokens_after_terminator'][0]['declared_positional'])

    def test_no_option_definitions_returns_incomplete(self):
        self.assertEqual(self.result(help_text='Usage: program [flags]\nSee another document.')['status'], 'incomplete')
        self.assertEqual(self.result('--dynamic-flag', help_text='Plugin options are added dynamically.')['status'], 'incomplete')

    def test_cli_sources_hashes_new_output_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            argv_path, help_path, output_path = [directory / name for name in ('argv.json', 'help.txt', 'result.json')]
            argv_path.write_text(json.dumps(spec('--dtype=bf16')), encoding='utf-8')
            help_path.write_text(HELP, encoding='utf-8')
            result = self.run_cli('--argv-json', argv_path, '--help-text', help_path, '--output', output_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            report = json.loads(output_path.read_text())
            self.assertEqual(report['sources']['argv_json']['sha256'], hashlib.sha256(argv_path.read_bytes()).hexdigest())
            self.assertEqual(report['sources']['help_text']['sha256'], hashlib.sha256(help_path.read_bytes()).hexdigest())
            before = {path: path.read_bytes() for path in (argv_path, help_path, output_path)}
            for path in (argv_path, help_path, output_path):
                failed = self.run_cli('--argv-json', argv_path, '--help-text', help_path, '--output', path)
                self.assertEqual(failed.returncode, 2)
                self.assertEqual(path.read_bytes(), before[path])

    def test_cli_incomplete_has_explicit_status_and_does_not_execute_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            argv_path, help_path = directory / 'argv.json', directory / 'help.txt'
            marker = directory / 'must-not-exist'
            # A shell-shaped argument is still inert JSON; no subprocess shell is used.
            command = spec('--unknown', f'$(touch {marker})')
            command['argv'][0] = '/nonexistent/executable'
            command['command_scope']['executable'] = '/nonexistent/executable'
            command['help_scope']['executable'] = '/nonexistent/executable'
            argv_path.write_text(json.dumps(command), encoding='utf-8')
            help_path.write_text(HELP, encoding='utf-8')
            result = self.run_cli('--argv-json', argv_path, '--help-text', help_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'incomplete')
            self.assertFalse(marker.exists())

    def test_cli_duplicate_keys_and_nonfinite_inputs_fail_without_report(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            argv_path, help_path = directory / 'argv.json', directory / 'help.txt'
            help_path.write_text(HELP, encoding='utf-8')
            for content in ('{"argv":[],"argv":[]}', '{"argv":NaN}', '"vllm serve --help"'):
                argv_path.write_text(content, encoding='utf-8')
                result = self.run_cli('--argv-json', argv_path, '--help-text', help_path)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')

    def test_help_includes_complete_minimal_scoped_object(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('"command_scope"', result.stdout)
        self.assertIn('"positional_indices"', result.stdout)
        self.assertIn('Never executes commands', result.stdout)


if __name__ == '__main__':
    unittest.main()
