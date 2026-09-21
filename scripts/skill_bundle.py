#!/usr/bin/env python3
"""Inspect portable Skill identity; never execute a Skill or choose its operation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

IGNORED = {'.git', '__pycache__', '.pytest_cache', '.DS_Store'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def inspect_bundle(directory):
    root = Path(directory).resolve()
    if not (root / 'SKILL.md').is_file():
        raise ValueError(f'missing SKILL.md: {root}')
    files = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or path.suffix == '.pyc':
            continue
        if path.is_symlink():
            raise ValueError(f'Skill must be self-contained; symlink: {relative}')
        if path.is_file():
            files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    interface = None
    if (root / 'interface.json').is_file():
        interface = json.loads((root / 'interface.json').read_text())
        if not isinstance(interface, dict) or type(interface.get('schema_version')) is not int or interface['schema_version'] != 1:
            raise ValueError('unsupported interface schema')
        for key in ('capability_id', 'interface_version', 'result_contract'):
            if not isinstance(interface.get(key), str) or not interface[key].strip():
                raise ValueError(f'missing interface {key}')
        selector = interface.get('selector')
        choices = interface.get('operations')
        if selector not in ('mode', 'operation') or not isinstance(choices, list) or not choices:
            raise ValueError('interface requires explicit selector and operations')
        if any(not isinstance(x, str) or not x for x in choices) or len(set(choices)) != len(choices):
            raise ValueError('invalid/duplicate operations')
        resources = interface.get('resources', [])
        if not isinstance(resources, list) or any(not isinstance(x, str) for x in resources):
            raise ValueError('resources must be a list of relative file names')
        for name in resources:
            if name not in files:
                raise ValueError(f'missing interface resource: {name}')
    return {'schema_version': 1, 'bundle_sha256': digest(files),
            'files': files, 'interface': interface}


def validate_selection(bundle, selected, expected_id=None):
    interface = bundle.get('interface')
    if not interface:
        raise ValueError('machine-readable interface missing; cannot validate invocation')
    if expected_id and interface['capability_id'] != expected_id:
        raise ValueError('capability identity mismatch')
    if selected not in interface['operations']:
        raise ValueError(f"explicit {interface['selector']} required; accepted: {interface['operations']}")


def verify_bundle(directory, receipt):
    actual = inspect_bundle(directory)
    if actual != receipt:
        raise ValueError('Skill content/interface changed; revalidate the binding')
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['inspect', 'verify'])
    parser.add_argument('--skill-dir', required=True, type=Path)
    parser.add_argument('--selection')
    parser.add_argument('--capability-id')
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    try:
        bundle = inspect_bundle(args.skill_dir)
        if args.operation == 'verify':
            if not args.receipt:
                raise ValueError('--receipt required')
            verify_bundle(args.skill_dir, json.loads(args.receipt.read_text()))
        if args.selection is not None or args.capability_id is not None:
            validate_selection(bundle, args.selection, args.capability_id)
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(json.dumps({'status': 'incomplete', 'reason': str(exc)}, ensure_ascii=False))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
