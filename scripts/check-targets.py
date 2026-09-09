#!/usr/bin/env python3
"""Run one built-in read-only check against explicit inventory aliases, serially."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def resolve_targets(limit, inventory):
    aliases = limit.split(',')
    known = set(inventory.get('_meta', {}).get('hostvars', {}))
    for group in inventory.values():
        if isinstance(group, dict):
            known.update(group.get('hosts', []))
    if not aliases or len(set(aliases)) != len(aliases):
        raise ValueError('Provide distinct explicit host aliases')
    for alias in aliases:
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', alias) or alias not in known:
            raise ValueError(f'Not an explicit inventory host alias: {alias!r}')
        if alias in inventory:
            raise ValueError(f'Host alias also names an inventory group; --limit would be ambiguous: {alias!r}')
    return aliases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('check', choices=('connectivity-check', 'health-check', 'accelerator-check'))
    parser.add_argument('--limit', required=True, help='Explicit Host alias; comma-separated aliases run serially')
    parser.add_argument('--check', dest='check_mode', action='store_true')
    parser.add_argument('--diff', action='store_true')
    parser.add_argument('--list-hosts', action='store_true', help='Resolve only; no remote connection')
    parser.add_argument('-v', action='count', default=0)
    parser.add_argument('-e', '--extra-vars', action='append', default=[], choices=(
        'show_processes=true', 'show_processes=false', 'full_output=true', 'full_output=false'))
    args = parser.parse_args()
    env = dict(os.environ, ANSIBLE_HOME=str(ROOT / '.ansible'), ANSIBLE_CONFIG=str(ROOT / 'ansible.cfg'))
    try:
        result = subprocess.run([str(ROOT / '.venv/bin/ansible-inventory'), '-i', str(ROOT / 'inventory/hosts.yml'), '--list'],
                                cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        aliases = resolve_targets(args.limit, json.loads(result.stdout))
        print('Resolved targets: ' + ', '.join(aliases), flush=True)
        if args.list_hosts:
            return
        extra = []
        if args.check_mode:
            extra.append('--check')
        if args.diff:
            extra.append('--diff')
        if args.v:
            extra.append('-' + 'v' * args.v)
        for value in args.extra_vars:
            extra.extend(['-e', value])
        for alias in aliases:
            subprocess.run([str(ROOT / 'scripts/playbook'), f'playbooks/{args.check}.yml',
                            '-i', str(ROOT / 'inventory/hosts.yml'), '--limit', alias, *extra],
                           cwd=ROOT, env=env, check=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    main()
