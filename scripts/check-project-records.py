#!/usr/bin/env python3
"""Validate local record links and prevent new process-artifact sprawl; no remote IO."""
import argparse
import json
from pathlib import Path
import re

import yaml


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_state(path):
    value = yaml.load(path.read_text(), Loader=UniqueLoader)
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int:
        raise ValueError('state requires an integer schema_version and mapping')
    return value


def point_links(state):
    """Normalize existing schemas without rewriting historical facts."""
    links = {}
    for name in state.get('point_documents', []):
        links[Path(name).stem] = name
    ids = set()
    for row in state.get('experiments', []):
        identifier = row.get('experiment_id')
        if not isinstance(identifier, str) or identifier in ids:
            raise ValueError(f'missing/duplicate experiment ID: {identifier}')
        ids.add(identifier)
        if identifier.startswith(('op-', 'fw-')) or row.get('document'):
            links[identifier] = row.get('document', identifier + '.md')
    return links


def process_files(root, public_scripts=()):
    found = set()
    for base in ('models', 'docs/cases'):
        for path in (root / base).rglob('*'):
            # Existing history is user-owned and explicitly outside this migration.
            if not path.is_file() or 'history' in path.parts or '__pycache__' in path.parts:
                continue
            if path.suffix != '.md' and not (base == 'models' and path.name == 'state.yml'):
                found.add(path.relative_to(root).as_posix())
    allowed = set(public_scripts)
    for path in (root / 'scripts').rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in allowed:
            found.add(relative)
    return found


def check(root):
    errors, warnings = [], []
    for path in sorted((root / 'models').glob('*/*/*/state.yml')):
        try:
            state = load_state(path)
            readme = path.with_name('README.md')
            if not readme.is_file():
                raise ValueError('missing stage README.md')
            if path.parent.name != 'optimize':
                continue
            text = readme.read_text()
            for identifier, name in point_links(state).items():
                if not isinstance(name, str) or Path(name).name != name or not name.endswith('.md'):
                    raise ValueError(f'{identifier}: document must be a direct Markdown filename')
                if not (path.parent / name).is_file():
                    errors.append(f'{path}: {identifier} missing {name}')
                elif not re.search(r'\]\((?:\./)?' + re.escape(name) + r'(?:#[^)]*)?\)', text):
                    errors.append(f'{readme}: missing point link {name}')
        except (ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
            errors.append(f'{path}: {exc}')
    for name in ('inference-accuracy-evaluation', 'inference-performance-evaluation',
                 'inference-accuracy-diagnosis', 'inference-profiling', 'inference-optimization-planning',
                 'key-operator-analysis'):
        entry = root / 'skills' / name / 'SKILL.md'
        if not entry.is_file():
            errors.append(f'missing local Skill: {entry}')
            continue
        for ref in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', entry.read_text()):
            if '://' not in ref and not ref.startswith('#') and not (entry.parent / ref).exists():
                errors.append(f'{entry}: broken local reference {ref}')
    inventory = root / 'docs/process-artifact-inventory.json'
    legacy = json.loads(inventory.read_text()) if inventory.exists() else {'files': {}}
    public_scripts = legacy.get('public_script_files', [])
    if (not isinstance(public_scripts, list) or len(set(public_scripts)) != len(public_scripts)
            or any(not isinstance(path, str) or not path.startswith('scripts/') for path in public_scripts)):
        errors.append('process artifact inventory has invalid public_script_files')
        public_scripts = []
    for path in public_scripts:
        if not (root / path).is_file():
            errors.append(f'public script inventory points to a missing file: {path}')
    old_history = set(legacy.get('legacy_history_roots', []))
    for path in (root / 'models').rglob('history'):
        if path.is_dir() and path.relative_to(root).as_posix() not in old_history:
            errors.append(f'new history directory is not allowed: {path.relative_to(root)}')
    present = process_files(root, public_scripts)
    for path in sorted(present - set(legacy['files'])):
        errors.append(f'new process artifact outside external case directory: {path}')
    if present & set(legacy['files']):
        warnings.append(f'{len(present & set(legacy["files"]))} existing process artifacts await verified migration; not deleted or accepted as permanent knowledge')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors, warnings = check(args.root.resolve())
    for message in warnings:
        print('WARN:', message)
    for message in errors:
        print('FAIL:', message)
    if errors:
        raise SystemExit(1)
    print('Project record/Skill links checked; historical pending migration is reported separately.')


if __name__ == '__main__':
    main()
