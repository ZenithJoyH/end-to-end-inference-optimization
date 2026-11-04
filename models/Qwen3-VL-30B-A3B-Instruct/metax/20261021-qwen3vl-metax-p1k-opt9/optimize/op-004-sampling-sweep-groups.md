# op-004 Sampling radix digit groups

Planned before implementation. One variable: process all16bins per CTA instead of8bins/twoCTA groups, retain8passes and all masks. Independent external candidate from original; op003 is not combined. Static logical input loads halve; actual bandwidth and runtime unknown. Expected counter-risk: larger sequential bin loop/register pressure and decoupled-lookback progress. Timeout or numerical/graph failure stops promotion.

| Project truth | Frozen choice |
|---|---|
| Editable | Independent container private FlagGems-vllm MetaX top_k_top_p.py, _guarded_sweep TILE_R and launch digit groups only |
| Read-only | vLLM, Plugin, FlagGems, MoE, test oracle and benchmark workload after freeze |
| Build | Triton JIT; no C++ build |
| Validation | External standalone original/candidate bitwise masks, sorted values incl NaN, ties, signed zero; device graph changed-input replay twice; TP2 smoke/C8 |
| Benchmark | Original vs candidate vs revert full sampling GPU event median, interleaved; then maintained no-profiler E2E runner |
| Active set | FP32 contiguous M1,8,32,64; V nonaligned and151936; exact BF16, fractional(.7), mixed blocks; k int32/int64; p FP32 |
| Aggregation | Per-shape medians; no geometric average disguising regressions; target full E2E process/round medians |
| Timeouts | operator validation300s per stage, E2E900s/round, controlled service startup1800s |
| Profiler | Torch profiler in isolated service, ranks0/1; inactive for performance |
| Autotune | Exempt: fixed MetaX TILE_R8vs16 with all16digits processed; CUDA/NVIDIA unchanged; MetaX-only device guard; NVIDIA unmodified |
| Fallback | Existing unsupported NotImplementedError and Plugin original fallback unchanged; no torch compute fallback |

| Alignment contract | Choice |
|---|---|
| Reference | Current exact runtime FV operator and vLLM ee0da84 apply_top_k_top_p_pytorch |
| Input | FP32 contiguous rank2 cuda, 0<=M<=64,1<=V<=262144; optional contiguous k int32/int64[M],1..V; p FP32[M],0..1 |
| Output | Same storage/in-place logits, FP32, masks -inf; preserve kept bits/tie policy |
| Dtype/promotion | No change; BF16 used only for exact representability guard/count path; FP32 radix for nonexact values |
| Semantics | Preserve NaN/Inf/signed-zero/ties by original output oracle (no assertion that all such logits are model-valid); no RNG |
| Autograd | Inference forward-only unchanged |
| Unsupported | Existing metadata/layout/size cases unchanged |
| Torch usage | Test/reference/allocation only, no added production torch compute |

| Path | Trigger | Implementation/config | Risk/check |
|---|---|---|---|
| early return | Empty M or no filters | Unchanged | Alias/zero tests |
| exact BF16 | Every CTA bad==0 | Unchanged exact-count path | Exact full-sort/mask parity |
| fractional/general | Any bad>0 CTA | Same4bit radix,8passes; TILE_R16vs8 and grid1vs2 | Mixed CTAs/global batch fallback/graph changed inputs |
| unsupported | Existing metadata checks | Existing Plugin fallback unchanged | Boundary rejection |


Same external validation coverage and B/C/R measurement contract as op003 except specific hypothesis. Minimum operator gain5% before promotion unless live trace justifies; E2E2%, guards10%, spread/drift8%. Target P1024/D1024/C64/N128,3warm+2measure, steady only. Full GPQA deferred by user. No source edit until external validation and baseline trace.

Results: not_run.

35 data/shape groups,105 filter comparisons,4graphcaptures16changed-input replays bitwise passed. M64fractional7.5374→7.5105ms (~0.36%), M1fractional0.9057→1.1241ms (24.1%slower). Rejected, no repository edit. Reduced logical reads do not yield runtime gain: bin-loop/register/occupancy effects remain competing explanations, no hardware-counter attribution claimed.
