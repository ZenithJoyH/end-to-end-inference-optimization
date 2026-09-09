#!/usr/bin/env python3
"""Compare Docker-compatible inspect mount manifests; never create/change containers."""
import argparse
import json
from pathlib import Path


def inspect_object(path):
    value = json.loads(Path(path).read_text())
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, dict) or not isinstance(value.get('Mounts'), list):
        raise ValueError('Expected exactly one container inspect with Mounts')
    return value


def normalize(value):
    result = []
    destinations = set()
    declared = {}
    for options in value.get('HostConfig', {}).get('Mounts') or []:
        if not isinstance(options, dict):
            raise ValueError('declared mount must be an object')
        target = options.get('Target')
        if not isinstance(target, str) or not target or target in declared:
            raise ValueError('missing or duplicate declared mount target')
        declared[target] = options
    for mount in value['Mounts']:
        if not isinstance(mount, dict):
            raise ValueError('mount must be an object')
        kind = mount.get('Type')
        destination = mount.get('Destination')
        if not isinstance(kind, str) or not kind or not isinstance(destination, str) or not destination.startswith('/'):
            raise ValueError('mount type/absolute destination is missing')
        if destination in destinations:
            raise ValueError('duplicate mount destination')
        destinations.add(destination)
        if kind not in ('bind', 'volume'):
            # tmpfs and other mounts affect execution too. Preserve all exposed
            # fields rather than silently ignore an unfamiliar runtime type.
            result.append({'other_mount': mount, 'DeclaredOptions': declared.get(destination, {})})
            continue
        if type(mount.get('RW')) is not bool or not isinstance(mount.get('Source'), str) or not mount['Source']:
            raise ValueError('mount source/access mode is missing')
        mode = mount.get('Mode', '')
        if not isinstance(mode, str):
            raise ValueError('mount Mode must be a string')
        modes = set(filter(None, mode.split(',')))
        if ('ro' in modes and mount['RW']) or ('rw' in modes and not mount['RW']):
            raise ValueError('mount Mode disagrees with effective RW')
        # Docker's -v and --mount can spell effective rw differently. RW is
        # authoritative; retain SELinux and other non-redundant mode options.
        modes -= {'rw', 'ro'}
        options = declared.get(destination, {})
        known_fields = {'Type', 'Source', 'Destination', 'RW', 'Propagation', 'Name', 'Driver', 'Mode'}
        declared_fields = {'Target', 'Source', 'Type', 'ReadOnly', 'BindOptions', 'VolumeOptions'}
        result.append({'Type': kind, 'Source': mount['Source'], 'Destination': destination,
                       'RW': mount['RW'], 'Propagation': mount.get('Propagation', ''),
                       'Name': mount.get('Name'), 'Driver': mount.get('Driver'),
                       'Mode': sorted(modes),
                       'BindOptions': options.get('BindOptions', {}),
                       'VolumeOptions': options.get('VolumeOptions', {}),
                       'ExtraDeclaredOptions': {key: val for key, val in options.items() if key not in declared_fields},
                       'ExtraRuntimeFields': {key: val for key, val in mount.items() if key not in known_fields}})
    if set(declared) - destinations:
        raise ValueError('declared mount target is absent from effective Mounts')
    return sorted(result, key=lambda item: json.dumps(item, sort_keys=True))


def compare(source, target):
    left, right = normalize(source), normalize(target)
    return {'schema_version': 1, 'mount_parity': 'passed' if left == right else 'failed',
            'source_mounts': left, 'optimization_mounts': right,
            'missing_or_changed': [m for m in left if m not in right],
            'extra_or_changed': [m for m in right if m not in left],
            'image_lineage': 'unverified',
            'note': 'Mount equality does not prove image lineage or source isolation. File binds are also compared.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-inspect', required=True, type=Path)
    parser.add_argument('--optimization-inspect', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        report = compare(inspect_object(args.source_inspect), inspect_object(args.optimization_inspect))
        with args.output.open('x') as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
    print('mount_parity=' + report['mount_parity'])
    if report['mount_parity'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
