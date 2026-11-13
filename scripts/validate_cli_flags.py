#!/usr/bin/env python3
"""Compare saved argv tokens with saved help declarations, without execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


OPTION = re.compile(r'(--\[no-\][A-Za-z][A-Za-z0-9_.-]*|--?[A-Za-z][A-Za-z0-9_.-]*)(?![A-Za-z0-9_.-])')
NEGATIVE_NUMBER = re.compile(r'-(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?')
ANSI_COLOR = re.compile(r'\x1b\[[0-9;]*m')
BOUNDARY = 'flag recognition only; no parameter-value, runtime, plugin, readiness or acceptance verification'
EXAMPLE = {
    'schema_version': 1,
    'argv': ['vllm', 'serve', 'model-id', '--dtype', 'bfloat16', '--no-enable-prefix-caching'],
    'command_scope': {'executable': 'vllm', 'subcommands': ['serve']},
    'help_scope': {'executable': 'vllm', 'subcommands': ['serve']},
    'positional_indices': [2],
}


def _text(value, label):
    if (not isinstance(value, str) or not value or '\x00' in value
            or any(ord(char) < 32 and char not in '\n\t' for char in value)):
        raise ValueError(f'{label} must be a nonempty string without unsafe control characters')


def _scope(value, label):
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != {'executable', 'subcommands'}:
        raise ValueError(f'{label} requires executable and subcommands')
    _text(value['executable'], label + '.executable')
    if not isinstance(value['subcommands'], list):
        raise ValueError(f'{label}.subcommands must be an explicit list')
    for token in value['subcommands']:
        _text(token, label + '.subcommands')
        if token.startswith('-'):
            raise ValueError('subcommand declarations cannot be option tokens')


def normalize_spec(value):
    """An argv array is accepted, but cannot establish a help/subcommand scope."""
    if isinstance(value, list):
        value = {'schema_version': 1, 'argv': value}
    if not isinstance(value, dict) or set(value) - {
        'schema_version', 'argv', 'command_scope', 'help_scope', 'positional_indices'
    } or not {'schema_version', 'argv'} <= set(value):
        raise ValueError('expected an argv array or schema 1 argv object; shell strings are not accepted')
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValueError('schema_version must be integer 1')
    argv = value['argv']
    if not isinstance(argv, list) or not argv:
        raise ValueError('argv must be a nonempty JSON string array, not a shell command')
    for token in argv:
        # Empty strings are legitimate argument values, but never an executable.
        if not isinstance(token, str) or '\x00' in token:
            raise ValueError('argv elements must be strings without NUL')
    _text(argv[0], 'argv executable')
    if argv[0].startswith('-'):
        raise ValueError('argv[0] must explicitly identify an executable')
    result = {**value, 'command_scope': value.get('command_scope'),
              'help_scope': value.get('help_scope'),
              'positional_indices': value.get('positional_indices', [])}
    for name in ('command_scope', 'help_scope'):
        _scope(result[name], name)
    positions = result['positional_indices']
    if (not isinstance(positions, list)
            or any(type(index) is not int or not 1 <= index < len(argv) for index in positions)
            or len(set(positions)) != len(positions)):
        raise ValueError('positional_indices must be unique argument indices, excluding executable')
    return result


def help_options(text):
    """Read only option declaration lines; never grep flags from body/examples.

    Declaration aliases must precede prose. Comma/slash/pipe separators and an
    optional uppercase metavar are accepted. Explicit --[no-]name declares both
    forms; no other negations, prefixes, short clusters or abbreviations expand.
    """
    definitions = {}
    skip_section = False
    for line_no, line in enumerate(text.splitlines(), 1):
        line = ANSI_COLOR.sub('', line).strip()
        if not line.startswith('-') and (line.endswith(':') or line.casefold().startswith('usage:')):
            skip_section = bool(re.search(r'\b(?:examples?|usage|notes?|description|warnings?)\b', line.casefold()))
        if skip_section:
            continue
        if not line.startswith('-'):
            continue
        header = re.split(r'\s{2,}', line, maxsplit=1)[0]
        first = OPTION.match(header)
        if not first:
            continue
        suffix = header[first.end():]
        if suffix and not re.match(r'^(?:\s*[,/|]|=|\s+(?:[A-Z][A-Z0-9_]*(?:\b|$)|[\[{<]))', suffix):
            # A sentence such as "--bad is unsupported" is not a declaration.
            continue
        remaining = header
        while True:
            match = OPTION.match(remaining)
            if not match:
                break
            option = match.group(1)
            names = [option]
            if option.startswith('--[no-]'):
                stem = option[len('--[no-]'):]
                names = ['--' + stem, '--no-' + stem]
            for name in names:
                definitions.setdefault(name, []).append(line_no)
            remaining = remaining[match.end():]
            # Stop at value choices or arbitrary text rather than finding flags
            # mentioned inside metavar descriptions or unsupported examples.
            remaining = re.sub(r'^\s+[A-Z][A-Z0-9_]*(?=\s*[,/|])', '', remaining)
            separator = re.match(r'^\s*[,/|]\s*', remaining)
            if not separator:
                break
            remaining = remaining[separator.end():]
    return {name: sorted(set(lines)) for name, lines in sorted(definitions.items())}


def analyze(spec, help_text):
    spec = normalize_spec(spec)
    if not isinstance(help_text, str):
        raise ValueError('help text must be UTF-8 text')
    argv = spec['argv']
    command_scope, help_scope = spec['command_scope'], spec['help_scope']
    gaps = []
    prefix_matches = None
    scope_matches = None
    prefix_count = 1
    if command_scope is None or help_scope is None:
        gaps.append('command_scope/help_scope missing; subcommand and help identity are unknown')
    if command_scope is not None:
        prefix = [command_scope['executable'], *command_scope['subcommands']]
        prefix_matches = argv[:len(prefix)] == prefix
        if prefix_matches:
            prefix_count = len(prefix)
        else:
            gaps.append('declared command scope does not match the exact argv prefix')
    if command_scope is not None and help_scope is not None:
        scope_matches = command_scope == help_scope
        if not scope_matches:
            gaps.append('command_scope and help_scope differ; help cannot establish flags for this subcommand')
    definitions = help_options(help_text)
    if not definitions:
        gaps.append('no supported option declaration lines were recognized in the saved help')
    positions = set(spec['positional_indices'])
    if any(index < prefix_count for index in positions):
        raise ValueError('a declared positional overlaps the executable/subcommand prefix')
    recognized, unknown, non_options, literals = [], [], [], []
    terminated = False
    terminator = None
    for index in range(prefix_count, len(argv)):
        token = argv[index]
        if terminated:
            literals.append({'index': index, 'token': token,
                             'declared_positional': index in positions})
            continue
        if token == '--':
            if index in positions:
                raise ValueError('the -- terminator cannot be declared as a positional')
            terminated, terminator = True, index
            continue
        is_option = token.startswith('-') and token != '-' and not NEGATIVE_NUMBER.fullmatch(token)
        if index in positions:
            if is_option:
                raise ValueError('a positional beginning with - requires an explicit -- terminator')
            non_options.append({'index': index, 'token': token, 'role': 'caller_declared_positional'})
        elif is_option:
            name, separator, value = token.partition('=')
            item = {'index': index, 'token': token, 'flag': name,
                    'inline_value': value if separator else None}
            if name in definitions:
                recognized.append({**item, 'help_lines': definitions[name]})
            else:
                unknown.append({**item, 'reason': 'no exact declaration; aliases, negations and short clusters are not inferred'})
        else:
            non_options.append({'index': index, 'token': token,
                                'role': 'unclassified_value_or_positional'})
    if unknown:
        gaps.append('one or more option-looking tokens have no exact saved-help declaration')
    return {
        'schema_version': 1, 'status': 'incomplete' if gaps else 'flags_recognized',
        'claim_scope': BOUNDARY, 'argv': argv, 'executable': argv[0],
        'scope': {'command': command_scope, 'help': help_scope,
                  'command_prefix_matches': prefix_matches, 'declared_scopes_match': scope_matches,
                  'binding': 'caller_declared_only; help origin and runtime identity not independently verified'},
        'supported_flags': sorted(definitions), 'recognized_flags': recognized,
        'unknown_flags': unknown, 'non_option_tokens': non_options,
        'end_of_options_index': terminator, 'literal_tokens_after_terminator': literals,
        'gaps': gaps,
        'unchecked': ['parameter arity and values, including separate boolean values',
                      'whether unclassified bare tokens are values or further positionals/subcommands',
                      'plugin or dynamically registered options absent from this help snapshot',
                      'snapshot origin, installed revision, runtime behavior and service readiness'],
        'parsing_policy': 'Check each option-looking token independently; never consume its successor. Negative decimal/exponent numbers and a lone - are non-options. -- ends checking. No shell parsing, expansion, short clustering or implicit --no-* aliases.',
    }


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f'duplicate JSON key: {key}')
        value[key] = item
    return value


def _constant(value):
    raise ValueError(f'non-finite JSON: {value}')


def _read(path):
    selected = Path(path).resolve(strict=True)
    if not selected.is_file() or selected.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('input must be a regular file no larger than 8 MiB')
    raw = selected.read_bytes()
    return raw.decode('utf-8'), {'path': str(selected), 'sha256': hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Offline exact flag recognition from explicit argv JSON and saved help. Never executes commands or captures help.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Minimal scoped argv object:\n' + json.dumps(EXAMPLE, indent=2)
               + '\nScope is caller-declared only. Input errors exit 2; inspect JSON status for incomplete. --output creates a new file and refuses overwrite.')
    parser.add_argument('--argv-json', required=True, type=Path, help='Saved argv array or schema 1 object')
    parser.add_argument('--help-text', required=True, type=Path, help='Previously captured UTF-8 help; never recaptured')
    parser.add_argument('--output', type=Path, help='New diagnostic JSON path; default stdout')
    args = parser.parse_args(argv)
    try:
        argv_text, argv_source = _read(args.argv_json)
        help_text, help_source = _read(args.help_text)
        value = json.loads(argv_text, object_pairs_hook=_object, parse_constant=_constant)
        result = analyze(value, help_text)
        result['sources'] = {'argv_json': argv_source, 'help_text': help_source}
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            if args.output.resolve() in (Path(argv_source['path']), Path(help_source['path'])):
                raise ValueError('output cannot replace either input')
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(output)
        else:
            print(output, end='')
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    sys.exit(main())
