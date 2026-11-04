# op-003 Sampling guard count skip

Status: planned before implementation. Target P1024/D1024/C64/N128, steady output throughput. Scope performance_only, GPQA explicitly deferred by user. Preserve source container, gems-opt, Plugin sampling integration, MoE and blacklist.

Hypothesis: if a CTA contains a value not exactly BF16, global invalid selects independent FP32 radix output, making that CTA BF16 count updates irrelevant. Update invalid only for nonzero bad, count only for bad==0. No host sync, dtype/output/RNG changes. Live cost to be confirmed before promotion.

| Project truth | Frozen choice |
|---|---|
| Editable | Independent container private FlagGems-vllm MetaX top_k_top_p.py, _count_bf16 only |
| Read-only | vLLM, Plugin, FlagGems, MoE, test oracle and benchmark workload after freeze |
| Build | Triton JIT; no C++ build |
| Validation | External standalone original/candidate bitwise masks, sorted values incl NaN, ties, signed zero; device graph changed-input replay twice; TP2 smoke/C8 |
| Benchmark | Original vs candidate vs revert full sampling GPU event median, interleaved; then maintained no-profiler E2E runner |
| Active set | FP32 contiguous M1,8,32,64; V nonaligned and151936; exact BF16, fractional(.7), mixed blocks; k int32/int64; p FP32 |
| Aggregation | Per-shape medians; no geometric average disguising regressions; target full E2E process/round medians |
| Timeouts | operator validation300s per stage, E2E900s/round, controlled service startup1800s |
| Profiler | Torch profiler in isolated service, ranks0/1; inactive for performance |
| Autotune | Exempt: no tile/warp/stage change; MetaX-only device guard; NVIDIA unmodified |
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
| exact BF16 | Every CTA bad==0 | Same histogram counts, no invalid zero atomics | Exact full-sort/mask parity |
| fractional/general | Any bad>0 CTA | Same invalid nonzero, skip only local unused counts; FP32 radix unchanged | Mixed CTAs/global batch fallback/graph changed inputs |
| unsupported | Existing metadata checks | Existing Plugin fallback unchanged | Boundary rejection |

Contract frozen before causal baseline: guard-count-comparison.json, minimum throughput gain2%, guard regressions<=10%, spread/drift<=8%,2measured rounds after3declared warmups stable within8%. Full operator micro gain>=5% supports E2E promotion; otherwise reconsider based on live trace. Milestone P1024/D256/C64/N128 has separate same-config baseline; parent target remains D1024. Prefill/decode probes retain own baseline. No first measured round discarded.

Results: not_run.

External numerical35groups ×3filtermodes and4captures/16changed-input replays passed bitwise. M64fractional7.5267→7.3047ms, revert7.5346ms; about3%microgain, below5%promotionthreshold. No repository source edit or E2E run. Leave source original; evaluate independent sweep candidate.
