"""Read-only adapters to this project's existing native evidence validators."""
import importlib.util
import json
from pathlib import Path
import sys


def validate_check(check):
    required = {'service': {'manifest'}, 'accuracy': {'manifest', 'gate'},
                'acceptance': {'manifest'},
                'performance': {'contract', 'plan', 'services', 'records'},
                'performance-run': {'contract', 'plan', 'services', 'records'}}
    if not isinstance(check, dict) or check.get('kind') not in required:
        raise ValueError('supported native gates: service, accuracy, performance-run, performance, acceptance')
    kind = check['kind']
    if set(check) != {'kind', *required[kind]}:
        raise ValueError(f'{kind}: missing/unknown gate arguments')
    for field in required[kind]:
        values = check[field] if field in ('records', 'services') else [check[field]]
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not Path(v).is_absolute() for v in values):
            raise ValueError(f'{field}: explicit absolute evidence paths required')
        if len(set(values)) != len(values):
            raise ValueError(f'{field}: duplicate paths are not allowed')


def source_files(root):
    return [p for folder in ('evaluation/accuracy', 'evaluation/performance', 'test/Accuracy_test', 'test/perf_test')
            for p in (root / folder).glob('*.py')] + [root / p for p in
            ('AGENTS.md', 'docs/skills-project-contract.md', 'docs/experiment-contract.md',
             'docs/performance-optimization-sop.md', 'docs/container-isolation.md',
             'docs/model-artifact-contract.md', 'docs/agent-execution.md',
             'evaluation/README.md', 'evaluation/accuracy/README.md',
             'evaluation/performance/README.md')]


def validate_plan(spec):
    if any(c['kind'] not in ('service', 'accuracy') for c in spec['before']):
        raise ValueError('before gates must validate the frozen current service or accuracy gate')
    if any(not isinstance(spec['scope'].get(k), str) or not spec['scope'][k] for k in ('model', 'host')):
        raise ValueError('scope requires exact model and host from service manifests')
    final_kinds = {c['kind'] for c in spec['after']}
    capability = spec['capability_id']
    if capability == 'e2e/performance':
        required = {'performance', 'acceptance'} if spec['selection'] == 'formal' else {'performance', 'performance-run'}
        if not final_kinds & required: raise ValueError('performance completion requires native performance evidence')
        if spec['selection'] == 'formal' and not any(c['kind'] == 'accuracy' for c in spec['before']):
            raise ValueError('formal performance requires an accuracy gate before measurement')
    elif capability == 'e2e/accuracy':
        if spec['selection'] not in ('formal-gate', 'gate-check'):
            raise ValueError('journal native accuracy adapter currently supports formal-gate/gate-check only')
        if 'accuracy' not in final_kinds: raise ValueError('accuracy completion requires the native accuracy gate')
    else:
        raise ValueError('unsupported project capability')
    if capability == 'e2e/performance' and spec['selection'] == 'formal':
        for c in spec['after']:
            if c['kind'] == 'performance' and json.loads(Path(c['contract']).read_text()).get('scope') != 'formal':
                raise ValueError('formal selection requires a native formal comparison contract')
    frozen = {str(Path(p).resolve()) for p in spec['context_files']}
    for c in spec['before'] + spec['after']:
        for key in ('manifest', 'contract', 'plan'):
            if key in c and str(Path(c[key]).resolve()) not in frozen:
                raise ValueError(f'freeze {key} in context_files')
        for value in c.get('services', []):
            if str(Path(value).resolve()) not in frozen:
                raise ValueError('freeze every expected service manifest in context_files')
    for c in spec['before']:
        if 'gate' in c and str(Path(c['gate']).resolve()) not in frozen:
            raise ValueError('freeze prerequisite accuracy gate in context_files')


def module(path, name):
    # These modules have adjacent imports; restore sys.path after loading.
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try: spec.loader.exec_module(value)
    finally: sys.path.pop(0)
    return value


def bind_service(service, scope):
    for key, native in (('model', 'model_name'), ('host', 'host')):
        if scope.get(key) != service.get(native):
            raise ValueError(f'journal scope and native service differ: {key}')


def bind_performance_inputs(validator, check, scope):
    """Bind native run outputs to this journal's frozen workload and instances."""
    expected_ref = validator.artifact(Path(check['plan']))
    expected_plan = validator.performance_plan.load_plan(Path(check['plan']))
    expected_services = {validator.artifact(Path(path))['sha256'] for path in check['services']}
    actual_services = set()
    for path in check['records']:
        record = validator.read_json(Path(path))
        plan_ref = record.get('artifacts', {}).get('plan')
        service_ref = record.get('artifacts', {}).get('service')
        plan_path = validator.checked(plan_ref)
        service_path = validator.checked(service_ref)
        if validator.performance_plan.load_plan(plan_path) != expected_plan:
            raise ValueError(f'run plan differs from the frozen journal plan: {path}')
        # The executor serializes a normalized plan (including defaults). Bind
        # original inputs separately; a formatting change is not workload drift.
        original = record.get('input_artifacts', {}).get('plan')
        if original is not None:
            original_path = validator.checked(original)
            if validator.performance_plan.load_plan(original_path) != expected_plan:
                raise ValueError(f'run input plan differs from the frozen journal plan: {path}')
        elif plan_ref['sha256'] != expected_ref['sha256']:
            raise ValueError('legacy run without input provenance requires the exact frozen plan snapshot')
        service = validator.read_json(service_path)
        bind_service(service, scope)
        actual_services.add(service_ref['sha256'])
    if actual_services != expected_services:
        raise ValueError('run service instances differ from the frozen expected service set')


def run_check(root, check, scope):
    validate_check(check)
    kind = check['kind']
    if kind == 'acceptance':
        validator = module(root / 'evaluation/performance/final_acceptance.py', '_step_final_acceptance')
        manifest = validator.native.read_json(check['manifest'])
        for ref in manifest['run_records']:
            record = validator.native.read_json(validator.native.checked(ref))
            service = validator.native.read_json(validator.native.checked(record['artifacts']['service']))
            bind_service(service, scope)
        result = validator.validate(Path(check['manifest']))
        project_scope = result.get('project_scope', {})
        if any(scope.get(k) != project_scope.get(k) for k in ('case_id', 'baseline_id')):
            raise ValueError('acceptance requires matching case_id/baseline_id in journal scope')
        return {'kind': kind, **result}
    if kind in ('service', 'accuracy'):
        validator = module(root / 'evaluation/accuracy/acceptance.py', '_step_accuracy')
        service = json.loads(Path(check['manifest']).read_text())
        bind_service(service, scope)
        if kind == 'service':
            validator.validate_service(service, formal=False)
        else:
            validator.check_gate(Path(check['gate']), Path(check['manifest']))
        return {'kind': kind, 'status': 'passed', 'validator': 'evaluation/accuracy/acceptance.py'}
    validator = module(root / 'evaluation/performance/compare_performance.py', '_step_performance')
    # The native validators prove each run. This additional binding proves that
    # those valid runs are the workload and service instances frozen by this step.
    bind_performance_inputs(validator, check, scope)
    if kind == 'performance-run':
        contract_path = Path(check['contract'])
        contract = validator.validate_contract(validator.read_json(contract_path))
        ref = validator.artifact(contract_path)
        for path in check['records']: validator.check_run(Path(path), ref, contract)
        return {'kind': kind, 'status': 'passed', 'boundary': 'individual native runs; no speedup or final acceptance claim'}
    return {'kind': kind, **validator.compare(Path(check['contract']), [Path(p) for p in check['records']])}


def output_files(root, spec):
    return [Path(p) for c in spec['after'] for p in
            (c['records'] if 'records' in c else [c['gate']] if 'gate' in c else [c['manifest']])]
