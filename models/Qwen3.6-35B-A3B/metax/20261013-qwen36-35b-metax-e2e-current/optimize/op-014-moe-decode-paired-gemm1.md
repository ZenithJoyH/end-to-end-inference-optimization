# Decode MoE GEMM1 paired gate/up

Stable experiment: `op-014-moe-decode-paired-gemm1`, operator/improve, parent `p1024-d1024-c64-n128`. Planned private single-variable experiment; production service/source/env unchanged. Exact script19 FlagGems scope retained; public fused_experts and no callerworkspace retained.

Evidence: prof003 actual TP0/1 traces 95e63f92…/d5d62de1…; 14 C64 decode steps each, matched CPU/GPU External id, one graph each, input ids [64,1], recurrent packed GDN30/step and no chunk GDN. MoE80 GEMMs/step. Baseline remains 1132.9415 tok/s median, .021576% spread, fullGPQA164/198. Trace activity is not critical path or E2E gain. First 24 captured main-batch steps include filling transients; no claim that all Prefill/Mixed shapes or whole-run steady state were captured.

Current chain: TritonExpertsFL -> flaggems_vllm public fused_experts_impl -> MetaX backend 75f34372… -> no_tle alignment -> fused GEMM1 -> GEMM2 -> reduction. GEMM1 real stage shape [64,2048] x [256,512,2048] -> [64,8,256], BF16, E256/TopK8. Current MetaX TP2 default BM16/BN64/BK64, warps4/stages2, GEMM1 sequential gate/up. Observed grids1088/8704 agree with EM4352, Nout256/2048 and BM16/BN64. Embedded config resolution must be verified in private process before timing, not inferred solely from defaults.

Hypothesis: existing `_metax_pair_fused_moe_kernel` can combine gate/up projection for exact M64, reusing A. Counterhypothesis: doubled accumulator/register/spill cancels benefit. Change only pair flag at existing MetaX invoke boundary, with BF16, exact A/B/C shapes, FUSE_SILU, no bias/scales/quantization/sorted-token guard. Keep grid/tile/GEMM2, public API and allocations. Reuse existing implementation, no new kernel or dispatch framework; no global autotune/NVIDIA changes. No other-platform hardware claim.

## Project truth table (before code)

| Field | Frozen value |
| --- | --- |
| Current op | flaggems_vllm.fused_experts_impl, existing Triton GEMM1 + SiLU/Up |
| Editable | ROOT/private/op014-pair-gemm1-20261016/fused_moe_candidate.py only |
| Read-only | all production repos, vLLM, model/tokenizer, original tests/benchmark |
| Build | Python AST/compile then private import; no install |
| Validation | same-input current/candidate BF16 complete output; rtol/atol .02, exact fallback cases; finite/zero/repeat, balanced/uniform/hot8 routing |
| Benchmark | native FlagGems-vllm Benchmark API, same-data currentFG vs candidateFG; operator/kernel then graph when independently available; latency ms, lower better |
| Active set | target M64/E256/H2048/I256/K8 BF16, routing balanced/uniform/hot8; M1/8/63/65 fallback sentinels; FP16 metadata guard preserved |
| Aggregation | 3 independent timing groups, median; every row retained, no min/best selection |
| Timeout | numeric max180s; nativebench max300s; no repeated constrained Stream creation |
| Profiler | existing prof003 only; no new capture planned |
| Autotune | no-autotune exemption: single existing boolean route on MetaX, preserve native tile config; no NVIDIA kernel or tune table changes |
| Fallback | existing same MetaX FG path; no added torch/vendor compute fallback |

## Alignment contract

| Field | Frozen value |
| --- | --- |
| Reference | current target MetaX fused_experts_impl, source75f34372… and current original repo benchmark; reference-only torch tests |
| Inputs | BF16 contiguous M64 H2048, w1 [256,512,2048], w2 [256,2048,256], unique per-token expert8 IDs, normalized FP32 weights; valid supported indices |
| Output | BF16 [64,2048], out-of-place public semantic; no callerworkspace |
| Dtype/promotion | only BF16 target; preserve existing FP32 accumulation and BF16 rounding points, FP16/FP32 unchanged |
| Edge semantics | zero, signed values, repeated call, routing skew; NaN/Inf behavior remains unknown until explicit classification check; not a promotion proof |
| Autograd | forward inference only, no backward claim |
| Unsupported | all non-target shapes/dtypes/quantized/EP/bias/fusion-disabled use exact existing path; no new unsupported inputs accepted |
| Torch use | only test input/reference/assertion; production delta metadata/boolean only |

## Path table

| Path | Gate | Method | Tests/perf | Risk |
| --- | --- | --- | --- | --- |
| Fast candidate | exact BF16 M64 GEMM1, fused SiLU, no bias/scale, sorted tokens | existing MetaX pair kernel | complete output + 3 route nativebench + graph>=2 | register/spill, rounding |
| General/fallback | every other valid original input | unchanged original MetaX kernel | M1/8/63/65 and dtype static sentinel | no changed coverage |
| Empty/invalid | original contract | unchanged original behavior | metadata gate test, no invented support |
| External | none added | all FG kept | no native bypass |

Repo AGENTS/workflow read. workflow.md currently carries unrelated conv1d task template; user current MoE scope takes precedence. Referenced optimization.md/deep_opt.md absent at repo root; no new kernel design or deep-optimization loop assumed. Existing kernel selection experiment only. Before any changed-kernel implementation, resolve methodology gap. Existing allocation/compute code preserved; no unrelated cleanup.

Promotion: exact numerical/boundaries first, complete-MoE median current/candidate>=1.05 and every frozen route>=.95, then >=2 graph replay and standard native benchmark, then new full198 precision and identical no-profiler P1K baseline/candidate/revert (>=3% throughput, opposite-stage guards). Current source gate does not apply to candidate. Graph with new Stream is known unsafe under resident model resource pressure; do not retry it or stop/restart service under expired authorizations. A new interruption would require a concrete prepared plan and separate user authorization. Failure preserves evidence and rejects candidate, no production deployment.

Rollback: private process exits and original production source SHA remains unchanged; all dirty/source snapshots preserved. No commit/push/reload.

Before execution: ROOT/commands/prepare-op014-private-pair-20261016.py SHA 3ef8597a2e4b57dd4a7503d8d8686077e9c31de665c3c5268a16fa7a6b4a27e2 freezes source/config/dirty snapshots and exact private pair flag; CPU source-only preparation.

Preparation v1 syntax error in nested quoting occurred before any execution: zero source changes/GPU work. Preserved original failed script; v2 prepare-op014-private-pair-v2-20261016.py SHA ca379ba859075c01906dc17320a8807623a93909ddf72204ca3d6dd8167d311d passed outer and embedded Python AST parse before execution.

V2 CPU preflight confirmed both GPUs only current workers, ~2987MiB free each, APIidle; private parent directory absent, mkdir stopped before any source snapshot/candidate file or GPU work. V3 prepare-op014-private-pair-v3-20261016.py SHA 95c47cf7514cf7fb72040af2cd8b961c7212ddf4e09153a5582dfbc2a1a3d1b0 creates only missing case-private parent and refuses existing experiment dir; parsed inner/outer before run. No numerical result yet.

Numerical executable saved beforeupload: ROOT/commands/test-op014-pair-numeric-20261016.py SHA 70a6e49f6207e01f6f2ec2c4939612732f472f6e274f0a9a3ba078f947be65ec. One private physicalGPU6/defaultstream process; no CUDA Stream/graph; exact same current publicFG backend reference and actual17ATenFG scope; eight frozen cases,180s budget and exclusive result.

Before execution: ROOT/commands/run-op014-private-numeric-20261016.py SHA 8c567000f7e0de0d374959bfc7e70408a27a2bda4b9a1d8fc8f3c8afa2be8deb rechecks source12355/fullenv/model/service/gate/APIidle/GPU6owner, exactprivatePID/birth bounded180s; postsource/idle verification. Privatefile c85ec4a3…, plan042d438b…; no installedsourcechange.

Numerics complete:8cases passed current reference tolerance .02, targetmaxabs .015625/RMSE~.00145–.00152, zero/fallbackbitwise, actual4paired hits. NumericSHAe69651ea…; source/currentinstance unchanged. Beforebenchmark: nativeharness adapter ROOT/commands/test_op014_native_benchmark_20261016.py SHA 5b535d56b3ff770953d0db87fba5e4beb1be6558252b30210129eb80c5ba9d83; launcher run-op014-native-benchmark-20261016.py SHA e24dcf0e6393ce0750e7d650c8dc35971776e1eb23a8743cde01b95385eaaecd. Original Benchmark.run/get_latency preserved; samecurrentFG/candidateFG inputs,3groups(seed42..44),7routing/fallbackcases/mode,20mswarm/100msmeasure, modeskernel/operator, primarykernel wholeMoE median>=1.05/allrows>=.95,300s/mode. NewStream/graph notattempted. All42expectedrows retained.

Nativebenchmark v1 pytest CLI stopped beforecollection: --metrics is append/singlearg, not nargs; error file latency notfound,0tests/0timings, nativeJSON{}. Supervisor80752284… and failedCLI/XML kept. New v2 run-op014-native-benchmark-v2-20261016.py SHA 889e957b3d8f00e77e64d71fde801556a76ff659a46b26b34629dbc5fb71473d repeats --metrics flags only; identical frozen workloads/thresholds and new exclusive v2plan/results/logs. Added nativecollect-only gate3tests before GPUtiming. This repairs tool interface, not retesting failedmeasurements.

## 2026-10-16 review027 — rejected, production unchanged

Native benchmark v2 completed: kernel/operator each3pytest passed,21 valid rows each, all42 rows retained. V1 CLI failure was0tests/0timing (`--metrics` is append notnargs), preserved, not performance failure reclassification. V2 used exact same data/matrix/timing gates plus collect-only3tests; no benchmark logic copied. Native column “Torch” is currentFG reference and “Gems” privateFG, not torch-vs-Gems.

| Full MoE routing M64 | Kernel current/private median ms | Median current/private speedup | Operator speedup |
| --- | --- | --- | --- |
| uniform | .504832 / .606208 | .832770× | .843555× |
| balanced | .585984 / .670976 | .872998× | .888153× |
| hot8 | .276864 / .275328 | 1.005579× | 1.004297× |

Primary nine target-row median .872998× misses >=1.05; every-row >=.95 guard also fails. M1 operator sentinel one .946505× row is retained; medians near1 do not erase it. Candidate rejected/not deployed. No graph or new GPQA needed for rejected candidate. Current source12355/env/model/precise service continue unchanged and APIidle. Private source and failed/successful utility artifacts preserved, no installed rollback necessary because production never changed. Resource/spill explanation remains hypothesis: CPU cached-artifact filter returned0matching records, no proof of register/spill cost. Do not assert driver/LLVM root cause or run another GPUtest solelytojustify rejection.

Evidence relative ROOT: native kernel8d4add1d5b797f9bf44417ce4e79e8578bcfa0bcfccf96e8adba4bdb6df7ae8c/operator73a055baebdb274f776af2f03cd03f948a6ab99e14c50d645f495b5205994474; XML760c487b…/49f2adc6…; results/op014-native-benchmark-supervisor-v2-20261016.json SHA4f6410fc525453b745e9e9d19199b7bfd92cc7d1ff9159236b9b4565e6bc8172; results/op014-native-v2-analysis-20261016.json SHA4cb7d6b9afa25155abcb110fc72f0269d17b8c1bb5946aeb3e704af62ea54a76. Numericale69651ea… remains minimalonly, notmodelprecision.
