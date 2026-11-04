# diag-003: Manual whitelist/blacklist throughput gap

2026-10-25 read-only diagnosis requested by user. Preserve ongoing manual benchmark and original verify. No source/config/environment change, signals, model request or new test. Current focus is Total tok/s, TPOT deferred. Method: checkpoint review of existing manual CSV plus live process/socket/log/source facts; not formal acceptance.

## Measured observations

Directories are under /public-flash/jinghao/qwen3.6-27B/test/perf_test/benchmark_results/. Whitelist group qwen36-27b-new-retry-retry has5 complete scenarios, filename timestamp20261024_154424. Intended blacklist group qwen36-27b-new-retry-retry-retry has filename timestamp20261025_100035; P1K/P4K complete at review and P16K client still running. Do not treat partial/absent scenes as results.

| P/D/C/N | Whitelist Total tok/s | Second group Total tok/s | Change |
|---|---:|---:|---:|
|1024/1024/64/128|1760.54|1187.34|-32.56%|
|4096/1024/64/128|2895.47|1811.30|-37.44%|

Each completed scene has3 successful128-request rows with fixed exact token totals. SUMMARY averages Run2/3; both second-group steady rows are similarly slow, so the gap is not solely the slow Run1. File SHA, complete paths and exact values are in state.manual_list_gap_diagnosis. The P4K CSV was still growing at first read; preserve its observed first SHA as a partial snapshot, not the final-file SHA. No native run-record/gate is fabricated.

## Confirmed execution mismatch

Two independent API launches in B claim port9998 and same served name. Actual listening socket inode1895575028 is owned only by API171330; its parent/group differs from API171400. API171400 initial env contains BLACKLIST=exponential_,index_select,mm,max, but it has no listening socket on9998. API171330 has neither list in its initial env. Source default use_flaggems() is true and current metax.yaml exclusion lists are empty. No debugger or worker injection was used.

Both service stdout/stderr point to /public-flash/jinghao/qwen3.6-27B/service-new.log, so logs are interleaved; bind by PID rather than filename. Line392 starts API171330. All878 POST /v1/completions entries seen during review carry API171330 (first lines396-398 and recent1599-1607). Thus the active endpoint handled benchmark traffic, not the API carrying the intended blacklist.

Active chain:171330 -> Engine171672 -> TP workers172208/172209. Other chain:171400 -> Engine171941 -> workers172418/172419. Active worker startup/capture logs330-337 explicitly show FlagGems mm metax_nt and metax_splitk_two_step_partial; lines926+ show FlagGems _metax/ops/index_select.py during requests. These should not be attributed to a clean intended blacklist experiment. Exact per-kernel contribution has not been measured.

MetaX read-only process observation: first TP workers occupy about61328/61756MiB onGPU2/3; second workers only2MiB each. Do not claim two full replicas are competing or that GPU memory contention alone caused32-37%. Host PID mapping was independently checked via NSpid.

## What the configuration switch changes

Plugin worker.py246-273 uses only_enable(include=...) for whitelist and enable(unused=...) for blacklist.27 allowed functions versus everything except4 is a broad replacement expansion, not a four-function subtraction. Plugin dispatch/backends/flaggems/register_ops.py384 also filters fused logical ops via use_flaggems_op, so silu_and_mul/rms_norm/rotary_embedding availability can change too. The two environment lists cannot both be nonempty (utils.py128-132 raises ValueError); explicitly unset the opposite one before launching. Changing a shell export cannot rewrite already-running workers or captured graphs.

Current user dirty metax.yaml also removes masked_fill/masked_fill_ from both FlagOS and OOT exclusions. This is recorded but not reverted. Its historical timing versus the whitelist measurement is unknown. Source/launch identity across old manual runs is not fully bound. Existing unknown-vLLM-env warnings do not by themselves prove Plugin envs are ignored; the Plugin reads them in its own code.

## Conclusion and next discriminating step

The direct confirmed issue is endpoint/config mismatch: the second group is being served by a different launch than the one supplied the intended blacklist. At least Gems mm/index_select remain active; it cannot yet prove that the requested blacklist is intrinsically32-37% slower. No profiler or new benchmark was run, so do not name a single operator as the proven root cause.

After the user ends/completes the current client, first retain results, ensure only the intended service owns9998 and GPU2/3, unset the opposite list, start with fixed common launch settings, verify listener-to-worker identity and actual registration, and rerun a small same-workload comparison. Only then bisect the expanded operator set if a gap persists. No automatic stop/cleanup/restart or repeat measurement was authorized or performed in this analysis.

## Latest corrected service and persistent P1K gap (2026-10-25)

The previous mismatch is historical. Fresh verification: API247744 owns port9998/socket1897513676 and has BLACKLIST=exponential_,index_select,mm,max with no whitelist; Engine248015 and TP workers248282/248283 are its current chain. Latest 20261025_110346 P1K CSV SHA8e4c2549fe3e29356efc082bd95afd559107774de26f02e102c6039ebf92347f has128 successful requests each run and total throughput1141.64/1185.78/1185.82 tok/s. SUMMARY1185.80 versus previously read whitelist1760.54 is -32.65%. Run2/3 agreement does not support a purely first-run warmup explanation. The historical whitelist file was not present in the latest inventory; retain the prior SHA-bound read, not a claim of fresh access.

A concrete dispatch boundary was found: FlagGems src/flag_gems/runtime/op_registrar.py186-193 filters by exact implementation __name__. __init__.py1446 registers mm->mm, while1447 registers mm.out->mm_out. Therefore blacklisting mm does not exclude mm_out; max likewise does not exclude max_dim. The whitelist does not enable these matrix variants. Other matrix/fused functions also expand under blacklist selection. MetaX linear has its own kernel; it was not shown to call mm internally.

Current workers log FlagGems MM metax_nt at service-new.log323/324 and metax_splitk_two_step_partial during FULL graph capture329/330. This proves Gems MM variants still enter this service initialization/capture, but not the precise calling overload or their share of P1K wall time. Existing Inductor cache contains extern_kernels.mm(...,out=...) examples, but these were not bound to the active instance and are not used as current-call proof. Operator-once logs provide presence only, not hotness or timing.

Next discriminating test: retain current configuration and add only mm_out to blacklist for a new P1K comparison, with fresh listener/registration verification. This is a recommendation only: no source/env change, restart, request, benchmark or profiling was executed. Do not attribute the entire32.65% to mm_out before the single-variable result.

## Blacklist6: partial recovery and next discriminating path

2026-10-25 user supplied qwen36-27b-new-retry-retry-retry-retry after adding mm_out and max_dim. Read-only checkpoint analysis of existing CSV, current source/log/process facts; performance automation remains paused.

| P/D/C/N | Valid blacklist4 Total tok/s | Blacklist6 Total tok/s | Improvement | Historical whitelist Total tok/s | Remaining difference |
|---|---:|---:|---:|---:|---:|
|1024/1024/64/128|1185.80|1368.89|+15.44%|1760.54|-22.25%|
|4096/1024/64/128|1837.64|2439.36|+32.74%|2895.47|-15.75%|

Both completed new scenes have3 successful128-request rows with expected exact token counts. P1K runs1303.83/1369.11/1368.67; P4K2426.54/2439.22/2439.50. Existing script SUMMARY averages Run2/3; no rounds discarded by this review. New files timestamp20261025_150446: P1K SHA98a55efea84215f5aac646398180cc8bb7aa816eea979f3dfeb670c15bffcb85, P4K SHA70e10eab7ee1536aabafacb7a239a737d81b93008d3c9adf0dd20b0aca36f752. Prior valid-blacklist4 P4K final CSV SHA2cdbded9a1334f766f294b8cf755f90216ab23b77362669e7d26f55fc3c06bb5. P16K client was still running at inspection; no result invented. Prior blacklist4 P32K/P64K CSVs now contain failed rows, not throughput results.

Current API262845 owns9998 socket1898432685 with BLACKLIST=exponential_,index_select,mm,max,mm_out,max_dim and no whitelist; Engine263115 workers263382/263383. New startup/graph capture log does not contain earlier FlagTune flaggems/mm entries. Rank0 worker owns the oplist file; identical SHA across restarts can result from deterministic once-per-location logging. It is neither a call counter nor timing/proof of steady-workload hotspot. Original verify untouched.

New model path is /data/Qwen3.6-27B, earlier /public-flash/models/Qwen3.6-27B. config.json byte SHA differs but parsed JSON is equal; tokenizer config, weight index and generation config SHA equal. Full weights not reread. Stack revisions unchanged from prior review; no new source modifications. This is observational manual comparison, lacking current whitelist reversion and formal service-bound independent repeats. Joint mm_out/max_dim change cannot isolate either contribution.

### First remaining hypothesis: independent linear implementation

FlagGems __init__.py1349 still registers linear; blacklist6 allows it and whitelist27 does not. vLLM logits_processor.py89-96 invokes lm_head.quant_method.apply; vocab_parallel_embedding.py67-75 dispatches unquantized GEMM; layers/utils.py309-315 chooses default on this platform, whose92-98 calls torch.nn.functional.linear. MetaX FlagGems linear.py143-214 runs an independent linear_kernel, so excluding mm/mm_out is not equivalent to excluding linear. Logits projection repeats for output tokens with hidden5120/vocab248320, TP2 per-rank output dimension124160, batch<=64. This establishes a concrete eligible high-frequency path, not its live implementation timing or the cause of all remaining22.25%. Recommendation: add only linear to existing blacklist6 for a same-P1K test. No such test executed.

### Second hypothesis: small-batch sampling tail

Current service log329 confirms temperature1/top_k20/top_p0.95 from generation_config.json; manual bench supplies no overrides. topk_topp_sampler.py245-255 uses dedicated Triton masking when batch>=8, and PyTorch sorting below8 (279,299). sort/sort_stable/scatter_ and other extra registrations differ from whitelist, but full C64 steady sampling must not be mislabeled as PyTorch sort. Tail batch sizes/timing remain unmeasured; sorting is a secondary candidate, not a proven root cause. Preserve generation parameters in comparisons; temperature0/top_p1 would change workload semantics. Do not blindly disable RMSNorm: current graph uses vllm_ir.rms_norm/native and no live Plugin rms_norm dispatch is demonstrated.

Prefill proxy: mean TTFT falls P1K9545.90->5163.22ms and P4K26802.83->14531.83ms, including scheduler/queue costs. Decode: repeated logits/sampling source paths identified; user defers TPOT and no pure device phase timing exists. Mixed: total throughput table above is the observed end-to-end result. No profiler, new model request, env/source edit or service action was performed.

## Blacklist7: linear exclusion not supported as primary cause (2026-10-26)

User supplied the five-retry directory, timestamp20261025_193026. Read-only checkpoint of existing manual CSVs and current service/source/cache evidence, not a new measurement or formal acceptance. All five scenes have3 successful128-request rows with fixed expected token counts; SUMMARY retains the original script Run2/3 average.

| Input | Blacklist6 Total tok/s | Blacklist7 Total tok/s | Change |
|---|---:|---:|---:|
|1K|1368.89|1371.26|+0.173%|
|4K|2439.36|2439.48|+0.005%|
|16K|3372.70|3370.85|-0.055%|
|32K|3421.47|3428.17|+0.196%|
|64K|3406.77|3415.98|+0.270%|

Blacklist7 = exponential_,index_select,mm,max,mm_out,max_dim,linear. Current API285453 owns9998 socket1898798527, workers285990/285991. Launch keeps TP2/GPU2,3/BF16/P8192budget/C64/FULL_DECODE_ONLY/maxcapture64/prefixcacheoff. Model /data/Qwen3.6-27B and default temperature1/top_k20/top_p0.95 remain. Stack revisions unchanged, no new changes by agent. P1K1371.26 remains22.11% below historical whitelist1760.54; P4K2439.48 remains15.75% below2895.47. Original whitelist artifacts remain unavailable for a fresh reread; previous SHA-bound observation is retained, not treated as current control. Exact new filenames and SHA are in state.manual_list_gap_diagnosis.blacklist7_review.

This result downgrades the previous linear-first hypothesis: observed changes across five scenes are within -0.055..+0.270%, with no material recovery. It does not prove no linear call executes, but there is no evidence to keep treating it as the primary cause.

A stronger current execution-path fact is now available: current service log304 directly loads graphs from compile cache4dec565ac5/rank_0_0/backbone. Read-only byte-string inspection of its artifacts subgraph0/1/2/3/64 finds generated extern_kernels.mm(...,out=...) associated with source linear nodes and no linear_kernel/flag_gems strings in these artifacts. Thus at least these compiled model-body linear nodes have been lowered to mm-out calls; they cannot be assumed to execute the standalone FlagGems Linear kernel. This is bound current-cache evidence, unlike the earlier unbound generic Inductor examples. It is not a device trace or exhaustive proof of all live calls. FLAGOS_BLACKLIST is absent from the displayed cache env factors; reuse is observed but does not establish a cache correctness bug. Future configuration comparisons should keep distinct compilation-cache directories without deleting old material.

Before the first128 completion responses, service log samples433..439 show prompt throughput0,64 running requests and generation767.8..780.8 tok/s. There are sustained full-batch Decode periods; current evidence is insufficient to attribute the whole residual gap to sort in the batch<8 tail. Once-only operator logging still supplies presence, not steady-state timings.

Next discriminating work should stop blind one-name-at-a-time blacklist expansion. After explicit user resume, first verify that the original whitelist recovers throughput on the current stack under otherwise equal settings, then use native two-rank P1K capture/analyze on whitelist versus blacklist7. Separate graph body, logits/sampling, host/dispatch, communication and tail; retain the same sampling semantics. Existing low-overhead evidence cannot name the remaining kernel/root cause. No profiler was started, no model requests sent, no service/env/source/cache modified. Automatic regression remains paused.

## Current whitelist recovery and corrected MetaX sampling path (2026-10-26)

Current qwen36-27b-white-list contains only completed P1K CSV20261026_094528 (SHAa12a1ab5a983b77428f78d917ea13326de000f00613255ddab9487223b72ef9e). Runs1738.10/1766.42/1767.56 Total tok/s, SUMMARY1766.99. Blacklist7 P1K1371.26 is22.40% lower. Both have3x128successful requests, each131072input/131072output tokens. Makespan148.36s white versus191.17s black (+42.81s); mean TTFT5099.58 versus5166.18ms, so the dominant observation is sustained-generation/mixed makespan, not a large first-token delay. These client metrics do not isolate GPU phases. No new workload was sent.

Current white listener API307160/9998, workers307699/307700, whitelist27 and no blacklist. Launch/model/TP2/GPU2,3/graph/prefixcacheoff/defaulttemperature1/top_k20/top_p0.95 match the previous checked black configuration. Revisions unchanged. Both load compile cache4dec565ac5/rank_0_0/backbone; shared compiled body does not imply all runtime operators or sampling kernels identical. Current client source SHAe342ce5a32ea1e89b08ac3ae23a782f4ec2db76ba96900ad892dacc27e2f8f38 differs from prior black client SHAda320b269a7b233b75b3bd02b2c509938fdf1e98c81b72bb720419749ca5321f; current command still3runs/SKIP_FIRST1/random/ignoreEOS/same lengths,C,N/no sampling overrides. Old exact source was not saved for diff, so do not upgrade this manual evidence to formal frozen comparison.

White first-scene prompt0/Running64 generation samples1030.2..1043.2 tok/s; prior black equivalent samples767.8..780.8. This supports a persistent full-batch effect, with10s log-window limitations; it is not device timing or a per-kernel counter.

### Explicit correction of earlier analysis

The previous statement that batch>=8 uses the vLLM Triton top-k/top-p branch was incorrect for this container: it missed the platform override. platform.py180 and vendor/metax/__init__.py13 import MetaX patches, patches/__init__.py22 imports patches/topk_topp_sampler.py, and line36 replaces apply_top_k_top_p with _apply_top_k_top_p_no_triton. Lines27-32 force apply_top_k_top_p_pytorch whenever k/p present. Therefore C64 also executes full-vocabulary PyTorch sorting; sorting is not restricted to a small-batch tail. Earlier statements above are retained as superseded hypotheses, not current conclusions.

Verified source chain:

```text
MetaX _apply_top_k_top_p_no_triton
 -> apply_top_k_top_p_pytorch
 -> logits.sort(dim=-1)        # full vocabulary, before top-k mask
 -> softmax / cumsum(out=...) / scatter_
```

Blacklist7 permits FlagGems sort and sort_stable; __init__.py1793/1794 registers both ATen variants. The whitelist does not include either. Black once-log has GEMS SORT, SORT.STABLE, CLONE, SCATTER_, CUMSUM_OUT; current rank0-owned white once-log lacks these. Logs are presence only, including warmup. FlagGems sort.py377-400 routes to radix_sort with4 bits/pass; FP32 logits therefore require8 sweeps. radix_sort258-340 also clones values, materializes int64 indices, allocates double buffers and clears status per sweep. Each full C64 sampling step covers64x248320=15,892,480 values. This makes full-vocab radix sorting and its associated copying/reordering a concrete mechanism matching persistent generation overhead, rather than an arbitrary next operator guess. Device costs and exact22.40% contribution remain unmeasured. Source SHA values are pinned in state.white_retest_review.

Next discriminating experiment: keep blacklist7 and add only sort,sort_stable as one semantic operator family; rerun just P1K at identical temperature/top_k/top_p, without requiring the long five-scene suite. If recovery is partial, separately inspect cumsum_out/scatter_ in this same sampling chain. A native two-rank trace can quantify time by sampling/model/communication/host, but was not captured in this review. No service/env/source/cache modification, no restart or benchmark; automatic regression remains paused.
