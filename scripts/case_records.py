#!/usr/bin/env python3
"""Case-scoped local records, compact views and portable backups; no remote IO."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import zipfile

import yaml

STAGES = ('baseline', 'optimize', 'acceptance')
IDENTITY_FIELDS = ('case_id', 'model', 'platform', 'host', 'baseline_id', 'topology')
START, END = '<!-- e2e:summary:start -->', '<!-- e2e:summary:end -->'


class UniqueLoader(yaml.SafeLoader):
    pass


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f'duplicate YAML key: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def load(path):
    value = yaml.load(Path(path).read_text(), Loader=UniqueLoader)
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int:
        raise ValueError('state requires a mapping and integer schema_version')
    if value['schema_version'] == 4:
        identity = value.get('identity', {})
        if not isinstance(identity, dict) or any(not isinstance(identity.get(k), str) or not identity[k].strip()
                                                for k in IDENTITY_FIELDS):
            raise ValueError('schema 4 requires case/model/platform/host/baseline/topology identity')
        if value.get('stage') not in STAGES or not isinstance(value.get('current'), dict):
            raise ValueError('schema 4 requires stage and current mapping')
        if not isinstance(value.get('experiments'), list):
            raise ValueError('schema 4 requires experiments list')
        ids = set()
        for row in value['experiments']:
            if not isinstance(row, dict):
                raise ValueError('experiment rows must be mappings')
            identifier = row.get('experiment_id')
            if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
                raise ValueError('experiment IDs must be nonempty and unique')
            ids.add(identifier)
        if not isinstance(value.get('metrics', []), list):
            raise ValueError('metrics must be a list')
        for row in value.get('metrics', []):
            fields = ('scenario_id', 'role', 'metric', 'unit', 'scope')
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in fields):
                raise ValueError('metric rows require scenario, role, metric, unit and scope')
            number = row.get('value')
            if 'value' not in row or (number is not None and
                    (type(number) not in (int, float) or not math.isfinite(number))):
                raise ValueError('metric value must be finite or explicitly null')
    return value


def init_case(directory, identity):
    directory = Path(directory)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', identity['case_id']):
        raise ValueError('case-id must be a safe directory identifier')
    if directory.name != identity['case_id']:
        raise ValueError('root directory basename must equal case-id')
    if any(not isinstance(identity.get(k), str) or not identity[k].strip() for k in IDENTITY_FIELDS):
        raise ValueError('all identity fields are required, including explicit topology')
    directory.mkdir(parents=True, exist_ok=False)
    for stage in STAGES:
        folder = directory / stage
        folder.mkdir()
        value = {'schema_version': 4, 'identity': identity, 'stage': stage,
                 'current': {'status': 'not_run', 'candidate': None, 'next_action': None},
                 'experiments': [], 'metrics': []}
        (folder / 'state.yml').write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False))
        (folder / 'README.md').write_text(f'# {identity["case_id"]} / {stage}\n\n{START}\n{END}\n')
        render(folder / 'state.yml', folder / 'README.md')
    (directory / 'README.md').write_text('# ' + identity['case_id'] + '\n\n' + '\n'.join(
        f'- [{s}]({s}/README.md)' for s in STAGES) + '\n')


def summary(path):
    state = load(path)
    if state['schema_version'] == 4:
        identity, current = state['identity'], state['current']
        warnings = []
    else:
        # Expose ambiguity instead of silently merging legacy TP/Host cases.
        identity = {k: state.get(k) for k in IDENTITY_FIELDS}
        current = {k: state.get(k) for k in ('status', 'current_target_scenario_id', 'current_candidate', 'next_action')}
        warnings = ['legacy record: verify the selected case before changing or resuming it']
        if state.get('active_case_id') not in (None, state.get('case_id')):
            warnings.append(f"case_id={state.get('case_id')} differs from active_case_id={state['active_case_id']}")
    return {'identity': identity, 'stage': state.get('stage'), 'current': current,
            'experiment_count': len(state.get('experiments', [])), 'warnings': warnings}


def cell(value):
    if value is None:
        return '—'
    if not isinstance(value, (str, int, float, bool)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    return str(value).replace('|', '\\|').replace('\n', ' ')


def render(state_path, output):
    state = load(state_path)
    if state['schema_version'] != 4:
        raise ValueError('legacy records are summary-only; migrate explicitly before rendering')
    view = summary(state_path)
    lines = [START, '', f"- 案例：{cell(view['identity']['case_id'])}",
             f"- 当前状态：{cell(view['current'].get('status'))}",
             f"- 当前候选：{cell(view['current'].get('candidate'))}",
             f"- 下一步：{cell(view['current'].get('next_action'))}", '',
             '| 实验 | 状态/决定 | 场景 | 文档 |', '|---|---|---|---|']
    for row in state['experiments']:
        name = row.get('document')
        if not isinstance(name, str) or Path(name).name != name or not name.endswith('.md'):
            raise ValueError('experiment document must be a direct Markdown filename')
        lines.append('| ' + ' | '.join(cell(v) for v in
            (row.get('experiment_id'), row.get('decision', row.get('status')), row.get('scenario_id'))) +
            f' | [{cell(name)}]({name}) |')
    lines += ['', '| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |', '|---|---|---|---|---|---|']
    for row in state.get('metrics', []):
        if any(k not in row for k in ('scenario_id', 'role', 'metric', 'value', 'unit', 'scope')):
            raise ValueError('metric rows require scenario/role/metric/value/unit/scope')
        lines.append('| ' + ' | '.join(cell(row[k]) for k in
                     ('scenario_id', 'role', 'metric', 'value', 'unit', 'scope')) + ' |')
    lines += ['', END]
    output = Path(output)
    text = output.read_text() if output.exists() else START + '\n' + END + '\n'
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) >= text.index(END):
        raise ValueError('README needs exactly one ordered managed summary block; human prose is never replaced')
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    output.write_text(before + '\n'.join(lines) + after)


def export_records(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not root.is_dir() or output.is_relative_to(root):
        raise ValueError('choose an existing records root and an output outside that root')
    files = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError(f'records backup refuses symlinks: {p}')
        if p.is_file() and p.suffix in ('.md', '.yml', '.yaml'):
            data = p.read_bytes()
            files[p.relative_to(root).as_posix()] = data
    if not files:
        raise ValueError('no Markdown/YAML records to export')
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr('records/' + name, data)
        archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return {'archive': str(output), 'files': len(files), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def restore_records(archive_path, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('restore requires a new directory; merge into active cases only after review')
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > 100 * 1024 * 1024:
            raise ValueError('duplicate entries or record backup larger than 100 MiB')
        manifest = json.loads(archive.read('manifest.json'))
        if not isinstance(manifest, dict) or not manifest:
            raise ValueError('missing record manifest')
        if set(names) != {'manifest.json', *('records/' + name for name in manifest)}:
            raise ValueError('archive entries differ from manifest')
        contents = {}
        for name, digest in manifest.items():
            path = PurePosixPath(name)
            if (path.is_absolute() or name != path.as_posix() or '..' in path.parts or '\\' in name
                    or path.suffix not in ('.md', '.yml', '.yaml')):
                raise ValueError('unsafe or non-record archive entry')
            data = archive.read('records/' + name)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f'backup checksum mismatch: {name}')
            contents[name] = data
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return {'destination': str(destination), 'files': len(contents)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='operation', required=True)
    init = commands.add_parser('init', help='create a new case; existing records are never migrated implicitly')
    init.add_argument('--root', required=True, type=Path)
    for name in IDENTITY_FIELDS:
        init.add_argument('--' + name.replace('_', '-'), required=True)
    for operation in ('summary', 'render'):
        sub = commands.add_parser(operation)
        sub.add_argument('--state', required=True, type=Path)
        if operation == 'render': sub.add_argument('--output', required=True, type=Path)
    export = commands.add_parser('export')
    export.add_argument('--root', required=True, type=Path)
    export.add_argument('--output', required=True, type=Path)
    restore = commands.add_parser('restore')
    restore.add_argument('--archive', required=True, type=Path)
    restore.add_argument('--destination', required=True, type=Path)
    args = p.parse_args()
    try:
        if args.operation == 'init':
            init_case(args.root, {k: getattr(args, k) for k in IDENTITY_FIELDS})
            result = {'created': str(args.root)}
        elif args.operation == 'summary': result = summary(args.state)
        elif args.operation == 'render':
            render(args.state, args.output)
            result = {'updated': str(args.output)}
        elif args.operation == 'export': result = export_records(args.root, args.output)
        else: result = restore_records(args.archive, args.destination)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    except (OSError, ValueError, KeyError, yaml.YAMLError, zipfile.BadZipFile) as exc:
        p.exit(2, f'incomplete: {exc}\n')


if __name__ == '__main__': main()
