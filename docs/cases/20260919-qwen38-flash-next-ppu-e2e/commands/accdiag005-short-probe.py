#!/usr/bin/env python3
"""Same-card eager/graph short GPQA comparison with fixed prompts and seed."""

import argparse
import importlib.util
import json
import time
from pathlib import Path

BASE = Path('/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/commands')
spec = importlib.util.spec_from_file_location('short_probe', BASE / 'accdiag004-no-logprob-probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
ROOT = probe.CASE / 'diagnostics/accdiag-005-graph-eager-numerics-20260923'
DOC_IDS = (89, 140, 168)


def check(stage):
    original = json.loads((probe.PREV / 'preflight.json').read_text())
    receipt = json.loads((ROOT / f'stage-{stage}.json').read_text())
    probe.controller.check_8010(original)
    probe.controller.check_evaluator_idle()
    current = probe.controller.process_facts(8000)
    if current is None or current['start_ticks'] != receipt['service']['start_ticks']:
        raise RuntimeError(f'8000 identity no longer matches {stage}')
    if not probe.controller.port_ready(8000):
        raise RuntimeError('8000 unhealthy')
    probe.controller.check_8000_idle()
    return current['start_ticks'], probe.controller.process_facts(8010)['start_ticks']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=('eager', 'restored-graph'), required=True)
    args = parser.parse_args()
    identity = check(args.stage)
    cases = probe.prompts()
    out = ROOT / f'probe-{args.stage}'
    out.mkdir(exist_ok=False)
    rows = []
    for doc_id in DOC_IDS:
        payload = {'model': 'Qwen3.8-Flash-Next', 'messages': cases[doc_id]['messages'],
                   'temperature': 0.0, 'top_p': 0.95, 'top_k': 20, 'min_p': 0.0,
                   'presence_penalty': 0.0, 'repetition_penalty': 1.0,
                   'max_tokens': 64, 'seed': 1234, 'stream': False}
        for port in (8000, 8010):
            for repeat in (1, 2):
                if check(args.stage) != identity:
                    raise RuntimeError('service identity drifted')
                status, body, elapsed = probe.post(port, payload)
                choice = body['choices'][0]
                message = choice['message']
                text = (message.get('reasoning') or message.get('reasoning_content') or '') + '\0' + (message.get('content') or '')
                record = {'doc_id': doc_id, 'port': port, 'repeat': repeat,
                          'prompt_hash': cases[doc_id]['prompt_hash'],
                          'request_sha256': probe.sha(json.dumps(payload, ensure_ascii=False, sort_keys=True)),
                          'http_status': status, 'finish_reason': choice.get('finish_reason'),
                          'completion_tokens': body.get('usage', {}).get('completion_tokens'),
                          'reasoning': message.get('reasoning') or message.get('reasoning_content'),
                          'content': message.get('content'), 'text_sha256': probe.sha(text),
                          'elapsed_seconds': elapsed}
                (out / f'doc{doc_id}-port{port}-repeat{repeat}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
                rows.append(record)
    if check(args.stage) != identity:
        raise RuntimeError('service identity changed after probe')
    summary = []
    for doc_id in DOC_IDS:
        selected = {(r['port'], r['repeat']): r for r in rows if r['doc_id'] == doc_id}
        graph_8000 = json.loads((probe.ROOT / 'probe-ldpath-matched' / f'doc{doc_id}-port8000-repeat1.json').read_text())
        graph_8010 = json.loads((probe.ROOT / 'probe-ldpath-matched' / f'doc{doc_id}-port8010-repeat1.json').read_text())
        summary.append({'doc_id': doc_id,
                        'within_8000_identical': selected[(8000, 1)]['text_sha256'] == selected[(8000, 2)]['text_sha256'],
                        'within_8010_identical': selected[(8010, 1)]['text_sha256'] == selected[(8010, 2)]['text_sha256'],
                        '8000_same_as_matched_graph': selected[(8000, 1)]['text_sha256'] == graph_8000['text_sha256'],
                        '8000_matches_8010': selected[(8000, 1)]['text_sha256'] == selected[(8010, 1)]['text_sha256'],
                        '8010_same_as_before': selected[(8010, 1)]['text_sha256'] == graph_8010['text_sha256']})
    receipt = {'stage': args.stage, '8000_start_ticks': identity[0], '8010_start_ticks': identity[1],
               'completed_at_epoch': time.time(), 'rows': summary}
    (out / 'summary.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
