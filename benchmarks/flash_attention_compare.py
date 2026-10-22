#!/usr/bin/env python3
"""Compare a candidate run() varlen Attention API with installed native flash_attn.

Run inside the target PyTorch/FlashAttention environment. No model/service changes.
The default catalog and measurement procedure reproduce the 18-shape MetaX test:
Q16/KV2/D128, BF16, page16, 9 graph timing rounds (native/candidate/native).
Native prefill uses flash_attn_varlen_func; native decode uses with_kvcache.
Candidate Split-KV merge is included. Metadata, compilation, capture, allocator
and host enqueue time are excluded; results are not end-to-end model throughput.
"""
import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import pathlib
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import traceback
import uuid


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cases():
    a=[{'id':'sentinel-ragged','stage':'prefill','ql':[17,5],'kl':[113,57],'oracle':True}]
    for b in [1,8,32,64]:
        for k in [1024,2048,4096]:
            a.append({'id':f'decode-b{b}-k{k}','stage':'decode','ql':[1]*b,'kl':[k]*b})
    for b,q in [(1,1024),(8,1024),(1,4096),(2,4096)]:
        a.append({'id':f'prefill-b{b}-q{q}','stage':'prefill','ql':[q]*b,'kl':[q]*b})
    a.append({'id':'prefill-ragged','stage':'prefill','ql':[1009,257],'kl':[1009,1021]})
    return a

def write_json(p,x):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False));tmp.replace(p)


def run(args):
    import torch, triton
    from flash_attn import flash_attn_varlen_func, flash_attn_with_kvcache
    c=next(c for c in cases() if c['id']==args.case)
    spec=importlib.util.spec_from_file_location('attention_compare_candidate',args.candidate)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    torch.set_grad_enabled(False);torch.manual_seed(args.seed+next(i for i,x in enumerate(cases()) if x['id']==args.case))
    torch.cuda.set_device(0)
    prop=torch.cuda.get_device_properties(0)
    ident={'torch':torch.__version__,'triton':triton.__version__,'device_name':prop.name,'sms':prop.multi_processor_count,'physical_gpu':os.environ.get('CUDA_VISIBLE_DEVICES'),'main_sha256':hashlib.sha256(pathlib.Path(args.candidate).read_bytes()).hexdigest(),'native_module':flash_attn_varlen_func.__module__}
    if args.expected_sha256 and ident['main_sha256'] != args.expected_sha256:
        raise ValueError('Candidate SHA256 differs from the frozen source')
    native_path = pathlib.Path(sys.modules[flash_attn_varlen_func.__module__].__file__)
    ident['native_interface'] = str(native_path)
    ident['native_interface_sha256'] = file_sha256(native_path)
    ident['benchmark_sha256'] = file_sha256(pathlib.Path(__file__))
    b=len(c['ql']);hq=args.q_heads;hk=args.kv_heads;d=args.head_dim;page=args.page_size;maxq=max(c['ql']);maxk=max(c['kl']);total=sum(c['ql']);pages=math.ceil(maxk/page)
    q=torch.randn((total,hq,d),device='cuda',dtype=getattr(torch, args.dtype))
    k=torch.randn((b*pages,page,hk,d),device='cuda',dtype=getattr(torch, args.dtype))
    v=torch.randn_like(k)
    bt=torch.randperm(b*pages,device='cuda',dtype=torch.int64).to(torch.int32).reshape(b,pages)
    cuq=torch.tensor([0]+list(__import__('itertools').accumulate(c['ql'])),device='cuda',dtype=torch.int32)
    cuk=torch.tensor([0]+list(__import__('itertools').accumulate(c['kl'])),device='cuda',dtype=torch.int32)
    used=torch.tensor(c['kl'],device='cuda',dtype=torch.int32)
    scale=d**-0.5
    def candidate():
        return mod.run(q,k,v,maxq,cuq,maxk,seqused_k=used,block_table=bt,causal=True,softmax_scale=scale)
    def native():
        if c['stage']=='decode':
            return flash_attn_with_kvcache(q.reshape(b,1,hq,d),k,v,cache_seqlens=used,block_table=bt,softmax_scale=scale,causal=True).reshape(total,hq,d)
        return flash_attn_varlen_func(q,k,v,cuq,cuk,maxq,maxk,softmax_scale=scale,causal=True,block_table=bt)
    def error(a,z):
        a=a.float();z=z.float();delta=a-z
        out={'max_abs':delta.abs().max().item(),'relative_l2':(torch.linalg.vector_norm(delta)/(torch.linalg.vector_norm(z)+1e-12)).item(),'finite':bool(torch.isfinite(a).all().item() and torch.isfinite(z).all().item())}
        torch.testing.assert_close(a,z,atol=0.03,rtol=0.03)
        assert out['finite'] and out['relative_l2']<=0.01,out
        return out
    start=time.perf_counter();n=native();a=candidate();torch.cuda.synchronize()
    numerical={'native_vs_candidate':error(a,n)}
    if c.get('oracle'):
        refs=[];off=0
        for bi,(ql,kl) in enumerate(zip(c['ql'],c['kl'])):
            keys=k[bt[bi].long()].reshape(-1,hk,d)[:kl].float().repeat_interleave(hq//hk,dim=1).transpose(0,1)
            vals=v[bt[bi].long()].reshape(-1,hk,d)[:kl].float().repeat_interleave(hq//hk,dim=1).transpose(0,1)
            qq=q[off:off+ql].float().transpose(0,1)
            scores=(qq@keys.transpose(1,2))*scale
            mask=torch.arange(kl,device='cuda')[None,:]<=torch.arange(ql,device='cuda')[:,None]+kl-ql
            refs.append((torch.softmax(scores.masked_fill(~mask,float('-inf')),dim=-1)@vals).transpose(0,1));off+=ql
        ref=torch.cat(refs)
        numerical['native_vs_fp32']=error(n,ref);numerical['candidate_vs_fp32']=error(a,ref)
    print(json.dumps({'case':c['id'],'event':'numerical_pass','error':numerical,'initialization_s':time.perf_counter()-start}),flush=True)
    inner=32 if c['stage']=='decode' else 4
    graphs={};outputs={}
    for name,fn in [('native',native),('candidate',candidate)]:
        for _ in range(args.warmup):fn()
        torch.cuda.synchronize()
        stream=torch.cuda.Stream();stream.wait_stream(torch.cuda.current_stream())
        g=torch.cuda.CUDAGraph()
        with torch.cuda.graph(g,stream=stream):
            for _ in range(inner):out=fn()
        torch.cuda.current_stream().wait_stream(stream);torch.cuda.synchronize()
        graphs[name]=g;outputs[name]=out
    changed=[]
    for repeat in range(2):
        q.copy_(torch.randn_like(q))
        graphs['native'].replay();graphs['candidate'].replay();torch.cuda.synchronize()
        changed.append(error(outputs['candidate'],outputs['native']))
    def timing(name,replays):
        s=torch.cuda.Event(enable_timing=True);e=torch.cuda.Event(enable_timing=True)
        s.record()
        for _ in range(replays):graphs[name].replay()
        e.record();e.synchronize()
        return s.elapsed_time(e)*1000/(inner*replays)
    calibration={name:timing(name,2) for name in graphs}
    replays=max(1,min(32,math.ceil(10000/(min(calibration.values())*inner))))
    warm=[];admitted=False
    for i in range(12):
        warm.append({name:timing(name,replays) for name in graphs})
        if i>=4 and all(max(w[name] for w in warm[-3:])/min(w[name] for w in warm[-3:])-1<=0.08 for name in graphs):admitted=True;break
    result={'case':c,'identity':ident,'tensor':{'q':list(q.shape),'q_stride':list(q.stride()),'k':list(k.shape),'k_stride':list(k.stride()),'page_size':page,'page_table':'random-permutation-disjoint-pages','scale':scale},'numerical':numerical,'changed_input_graph_replays':changed,'timing_contract':{'unit':'us_per_API','mode':'graph-complete-API-device-time','inner':inner,'replays':replays,'rounds':args.rounds,'order':'native,candidate,native','excluded':'JIT/capture/metadata/host-allocator/KV-append/network/TP'},'warmup_windows':warm,'steady_admitted':admitted,'rounds':[]}
    if not admitted:
        result['status']='incomplete-warmup';write_json(args.output,result);return
    for r in range(args.rounds):
        result['rounds'].append({'round':r,'native_before_us':timing('native',replays),'candidate_us':timing('candidate',replays),'native_after_us':timing('native',replays)})
    def quant(vals,p):
        x=sorted(vals);pos=(len(x)-1)*p;lo=math.floor(pos);hi=math.ceil(pos)
        return x[lo]+(x[hi]-x[lo])*(pos-lo)
    before=[r['native_before_us'] for r in result['rounds']];after=[r['native_after_us'] for r in result['rounds']];cand=[r['candidate_us'] for r in result['rounds']]
    nvals=[(a+b)/2 for a,b in zip(before,after)]
    def stats(xs):return {'median_us':statistics.median(xs),'p90_us':quant(xs,.9),'min_us':min(xs),'max_us':max(xs),'spread':max(xs)/min(xs)-1}
    result['summary']={'native':stats(nvals),'candidate':stats(cand),'native_before':stats(before),'native_after':stats(after),'speedup':statistics.median(nvals)/statistics.median(cand),'native_before_after_drift':abs(statistics.median(after)/statistics.median(before)-1)}
    su=result['summary'];result['status']='complete' if max(su['native']['spread'],su['native_before']['spread'],su['native_after']['spread'],su['candidate']['spread'],su['native_before_after_drift'])<=0.08 else 'incomplete-spread-or-drift'
    if all(hasattr(mod, name) for name in ['_choose_splits', '_group_tile', '_BLOCK_M']):
        bm=mod._BLOCK_M
        result['candidate_auto_splits']=mod._choose_splits(maxq,maxk,bm//mod._group_tile(hq//hk,bm),b,hk,total,hq,d,prop.multi_processor_count)
    write_json(args.output,result)
    print(json.dumps({'case':c['id'],'status':result['status'],'summary':su}),flush=True)



def summarize(result):
    """Keep every case, including failed/incomplete ones, in the public summary."""
    case = result.get('case', {})
    row = {
        'case_id': case.get('id', result.get('case_id')),
        'stage': case.get('stage'),
        'batch': len(case.get('ql', [])),
        'query_lengths': case.get('ql'),
        'kv_lengths': case.get('kl'),
        'status': result['status'],
        'native_us': None,
        'candidate_us': None,
        'candidate_over_native': None,
        'candidate_splits': result.get('candidate_auto_splits'),
        'error': result.get('error'),
    }
    if result.get('summary'):
        summary = result['summary']
        row.update(
            native_us=summary['native']['median_us'],
            candidate_us=summary['candidate']['median_us'],
            candidate_over_native=1 / summary['speedup'],
            native_drift=summary['native_before_after_drift'],
        )
    return row


def result_exit_code(rows):
    if any(row['status'] == 'failed' for row in rows):
        return 1
    if any(row['status'] != 'complete' for row in rows):
        return 2
    return 0


def save_summary(root, rows):
    write_json(root / 'summary.json', rows)
    fields = [
        'case_id', 'stage', 'batch', 'query_lengths', 'kv_lengths', 'status',
        'native_us', 'candidate_us', 'candidate_over_native',
        'candidate_splits', 'native_drift', 'error',
    ]
    temporary = root / 'summary.csv.tmp'
    with temporary.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})
    temporary.replace(root / 'summary.csv')


def stop_worker(process):
    """Only stop the process group created by this benchmark invocation."""
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def run_suite(args, selected):
    source = Path(args.candidate).resolve(strict=True)
    source_hash = file_sha256(source)
    if args.expected_sha256 and source_hash != args.expected_sha256:
        raise ValueError(f'Candidate SHA256 mismatch: expected {args.expected_sha256}, got {source_hash}')
    configuration = {
        'candidate_source': str(source),
        'candidate_sha256': source_hash,
        'benchmark_sha256': file_sha256(__file__),
        'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
        'cases': selected,
        'q_heads': args.q_heads, 'kv_heads': args.kv_heads,
        'head_dim': args.head_dim, 'page_size': args.page_size, 'dtype': args.dtype,
        'seed': args.seed, 'rounds': args.rounds, 'warmup_calls': args.warmup,
        'inner_calls': {'decode': 32, 'prefill': 4},
        'steady_state': {'minimum_windows': 5, 'maximum_windows': 12, 'last_windows': 3, 'max_spread': 0.08},
        'correctness': {'atol': 0.03, 'rtol': 0.03, 'max_relative_l2': 0.01, 'changed_input_replays': 2},
        'calibration': {'target_us': 10000, 'min_replays': 1, 'max_replays': 32},
        'case_timeout_seconds': args.timeout,
        'total_budget_seconds': args.total_budget,
        'timing': 'graph full-API device time; native/candidate/native; retain all admitted rounds',
        'excluded': 'JIT/capture/metadata/host-allocator/KV-append/output-copy-to-service/TP/network',
    }
    if args.dry_run:
        print(json.dumps(configuration, indent=2))
        return 0
    # A fresh child directory prevents overwriting any prior run or evidence.
    run_id = args.run_id or time.strftime('fa-compare-%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8]
    root = Path(args.output_dir).resolve() / run_id
    root.mkdir(parents=True, exist_ok=False)
    frozen = root / 'sources'
    frozen.mkdir()
    candidate = frozen / 'candidate.py'
    candidate.write_bytes(source.read_bytes())
    if file_sha256(candidate) != source_hash:
        raise ValueError('Candidate changed while creating the frozen copy')
    benchmark = frozen / 'flash_attention_compare.py'
    benchmark.write_bytes(Path(__file__).read_bytes())
    cache = Path(tempfile.gettempdir()) / 'flash-attention-compare' / run_id / 'triton'
    environment = dict(os.environ, TRITON_CACHE_DIR=str(cache), PYTHONNOUSERSITE='1')
    configuration.update(run_id=run_id, output_directory=str(root), triton_cache=str(cache))
    write_json(root / 'config.json', configuration)
    print(f'Results: {root}', flush=True)
    print('case                            native_us  candidate_us  candidate/native  status', flush=True)
    rows = []
    started = time.monotonic()
    try:
        for case in selected:
            remaining = args.total_budget - (time.monotonic() - started)
            output = root / (case['id'] + '.json')
            if remaining <= 0:
                result = {'case': case, 'status': 'incomplete-total-budget'}
                write_json(output, result)
            else:
                command = [
                    sys.executable, '-P', str(benchmark), '--worker', '--case', case['id'],
                    '--candidate', str(candidate), '--expected-sha256', source_hash,
                    '--output', str(output), '--seed', str(args.seed),
                    '--q-heads', str(args.q_heads), '--kv-heads', str(args.kv_heads),
                    '--head-dim', str(args.head_dim), '--page-size', str(args.page_size),
                    '--dtype', args.dtype, '--rounds', str(args.rounds), '--warmup', str(args.warmup),
                ]
                write_json(root / (case['id'] + '.command.json'), command)
                print(f"Running {case['id']} ...", flush=True)
                with (root / (case['id'] + '.log')).open('w') as log:
                    process = subprocess.Popen(command, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    timed_out = False
                    try:
                        process.wait(timeout=min(args.timeout, remaining))
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        stop_worker(process)
                    except BaseException:
                        stop_worker(process)
                        raise
                if timed_out:
                    result = {'case': case, 'status': 'incomplete-timeout', 'error': 'Own worker exceeded the frozen timeout'}
                    # Preserve a worker-produced result if timeout happened during teardown.
                    if output.exists():
                        result['partial_result'] = json.loads(output.read_text())
                    write_json(output, result)
                elif output.exists():
                    result = json.loads(output.read_text())
                    if process.returncode and result.get('status') == 'complete':
                        result.update(status='failed', error=f'Worker exited {process.returncode} after writing results')
                        write_json(output, result)
                else:
                    result = {'case': case, 'status': 'failed', 'error': f'Worker exited {process.returncode} without a result; see log'}
                    write_json(output, result)
            result.setdefault('case', case)
            row = summarize(result)
            rows.append(row)
            save_summary(root, rows)
            if row['native_us'] is None:
                print(f"{case['id']:<31} {'-':>9} {'-':>13} {'-':>17}  {row['status']}", flush=True)
            else:
                print(f"{case['id']:<31} {row['native_us']:9.3f} {row['candidate_us']:13.3f} {row['candidate_over_native']:16.3f}x  {row['status']}", flush=True)
    except BaseException:
        save_summary(root, rows)
        raise
    exit_code = result_exit_code(rows)
    write_json(root / 'run.json', {
        'status': 'complete' if exit_code == 0 else 'failed' if exit_code == 1 else 'incomplete',
        'exit_code': exit_code, 'elapsed_seconds': time.monotonic() - started,
        'selected_cases': len(selected), 'completed_cases': sum(row['status'] == 'complete' for row in rows),
        'configuration_sha256': file_sha256(root / 'config.json'),
        'summary_sha256': file_sha256(root / 'summary.json'),
        'candidate_source_unchanged': file_sha256(source) == source_hash,
        'meaning': 'Comparison completed; exit zero does not mean the candidate is faster or model accuracy passed',
    })
    print(f"Finished: {len(rows)} cases, exit={exit_code}; {root / 'summary.csv'}", flush=True)
    return exit_code


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--candidate', help='Python file exporting the candidate run() API')
    p.add_argument('--expected-sha256', help='Optional exact candidate source hash; reject a different version')
    p.add_argument('--output-dir', default='./flash-attention-results', help='Parent of a new per-run output directory')
    p.add_argument('--run-id', help='Fresh child directory name; existing directories are rejected')
    p.add_argument('--case', help='Run one catalog case (same seed as the full catalog)')
    p.add_argument('--cases', help='Comma-separated catalog IDs; default: all 18')
    p.add_argument('--list', action='store_true', help='List the full catalog without importing torch or using GPU')
    p.add_argument('--dry-run', action='store_true', help='Print the frozen configuration without executing candidate code or GPU work')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--q-heads', type=int, default=16)
    p.add_argument('--kv-heads', type=int, default=2)
    p.add_argument('--head-dim', type=int, default=128)
    p.add_argument('--page-size', type=int, default=16)
    p.add_argument('--dtype', choices=['bfloat16', 'float16'], default='bfloat16')
    p.add_argument('--rounds', type=int, default=9)
    p.add_argument('--warmup', type=int, default=20)
    p.add_argument('--timeout', type=float, default=180, help='Maximum seconds for one worker')
    p.add_argument('--total-budget', type=float, default=900)
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--output', help=argparse.SUPPRESS)
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if args.list:
        print(json.dumps(cases(), indent=2))
        return 0
    if not args.candidate:
        p.error('--candidate is required except for --list')
    if min(args.q_heads, args.kv_heads, args.head_dim, args.page_size, args.rounds, args.warmup) <= 0:
        p.error('shape, rounds and warmup parameters must be positive')
    if args.q_heads % args.kv_heads:
        p.error('--q-heads must be divisible by --kv-heads')
    if not all(math.isfinite(value) and value > 0 for value in [args.timeout, args.total_budget]):
        p.error('timeouts must be finite and positive')
    if args.case and args.cases:
        p.error('use either --case or --cases')
    if args.run_id and (Path(args.run_id).name != args.run_id or args.run_id in ['.', '..']):
        p.error('--run-id must be a single directory name')
    ids = [args.case] if args.case else args.cases.split(',') if args.cases else [c['id'] for c in cases()]
    ids = [value.strip() for value in ids]
    catalog = {case['id']: case for case in cases()}
    if len(ids) != len(set(ids)) or any(value not in catalog for value in ids):
        p.error('case IDs must be distinct members of --list')
    if args.worker:
        if not args.case or not args.output:
            p.error('internal worker requires --case and --output')
        try:
            run(args)
            result = json.loads(Path(args.output).read_text())
            return result_exit_code([result])
        except Exception as exc:
            detail = {'case_id': args.case, 'status': 'failed', 'error': str(exc), 'traceback': traceback.format_exc()}
            write_json(args.output, detail)
            print(json.dumps(detail), flush=True)
            return 1
    try:
        return run_suite(args, [catalog[value] for value in ids])
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
