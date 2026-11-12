# op-008-threshold-prefix: PR1069 review performance validation

2026-11-06. User asks to validate the review finding in the actual MetaX environment. Diagnostic component experiment; no production/PR change, no model requests or E2E claim.

Baseline PR head `ce0feddceb0d74a031081e57ce9ff9d24fef3b84`. Candidate computes each row's integer total_less and exclusive equal-count prefix once, then reads scalar statistics in each mask CTA. Sorting, floating-point filtering, tie rules, API and RNG semantics are unchanged. Forced prefix at all p shapes exposes extra-launch regressions instead of choosing a favorable shape guard after seeing data. Reuses existing installed Triton scan capability; no compiler upgrade/TLE assumption.

Source qwen3vl remains running on GPU0/1. New private clone on currently idle GPU6, fresh no-pause effective snapshot and exact mount/import/source/model parity required. Source code is private /workspace; clone modification only. Finally restores clone baseline, stops only own clone and verifies original source PID/ticks/code/argv/env/models200.

Read local operator standard/key-operator-analysis and performance evaluation skill. Pure operator microbenchmark uses upstream Benchmark.get_latency, not the model E2E runner. Applicable A1-A4/B1/B3/C/D/E/F requirements: actual public entry/new-kernel launch proof; out-of-place input preservation; independent unchanged upstream Torch/FP64 oracle; changed-input graph/sentinel checks; no RNG/CPU numerical fallback; full benchmark raw rounds. No new precision gate or claimed model benefit.

Frozen matrix: B1/B8/B64 x V4096/151936/262144 x BF16-grid/arbitrary FP32 x k20+p.8/p-only.8. Full filtering API and counts/prefix/mask stage (common output clone); KERNEL and upstream CUDAGRAPH timing if supported. Warm20 calls, upstream20ms, 3 stable admission windows within10% max8; 5 measured B/C/R cycles, all retained, 5% baseline/revert drift attribution guard. Incomplete admission/drift results kept, never cherry-picked.

Correctness: baseline/candidate bitwise, independent CPU int64 prefix oracle, unchanged inherited unit reference/tolerance, six graph captures x three changed-input replays, sentinel/input/RNG checks. Any invalidity stops; no new optimization or retry of model workload.

Remote root: `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/op008-threshold-prefix-20261106`. Commands and SHA frozen in contract.json before remote execution. Raw tensors/logs/rounds stay remote.

Status: prepared, not measured yet.

- `control.py`: `b7cfb42c7b468d10553f8f2afe07809bc9d542a26712e3008c078931e090aaf7`
- `backend-baseline.py`: `0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4`
- `mounts.py`: `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`
- `component.py`: `bcd892de2627e01353678bf3ed235ae8d43287986dc956a496e5a4737e9591c6`
- `identity.py`: `f50f65e0a8ecf09ed55d57e7831ffcd76efc7b26ad9a1c8ff2ce4de497de2edd`
- `backend-candidate.py`: `e5cf41b4bfdf0e011ae0f3189aa28fe8fbcaa308952280032f27cb2703facf28`

Remote upload/unique launch: `/tmp/qwen3vl-pr1069-prefix-20261106/upload.py` SHA256 `743fcc10c9cd65eb8e5b48749419d66fcdd9661e4ff377f6e8e031d01ce4985f`. Creates only declared new root, immutable command copies, single detached controller and manifest.

Tool incident: first controller945133 exited before any snapshot/clone/GPU launch because image PATH does not resolve python. Read-only check confirms /opt/conda/bin/python. Use explicit absolute interpreter in immutable v2 scripts; prior evidence retained. New execution root `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/op008-threshold-prefix-20261106/v2`.
- `control.py`: `0e3f1157ccb442498be1e292980144be038d84d605e1002e5dcdc907b4aee567`
- `backend-baseline.py`: `0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4`
- `mounts.py`: `32adacf39859e88ad6e2dad04ada248a00b636c795fed67d34328f5264bec3e3`
- `component.py`: `ecc8facb0eceb78cc2c457088b1e0cbfbe55d4d9077e260e6c4c8c22d37e2028`
- `identity.py`: `f50f65e0a8ecf09ed55d57e7831ffcd76efc7b26ad9a1c8ff2ce4de497de2edd`
- `backend-candidate.py`: `e5cf41b4bfdf0e011ae0f3189aa28fe8fbcaa308952280032f27cb2703facf28`
- upload.py: `efbbe1a41d22a9912257fc7ec92eb5b19b5aceeb739be93e6cd2bd7f6552a723`

Actual C550 correctness42/CPUintegeroracle/6graph18changed-input replay passed; inherited91tests passed. V2 stopped its private clone and source-preserved passed. Tool incident before0timing: benchmark provenance import missed repo path; no numerical failure. V3 continuation uses same immutable clone/image/candidate and existing verification; explicitly sets repo import path for benchmark tools, fresh source/clone/resource guard. Prior failure retained. No new snapshot or repeated GPU correctness needed.
- `component_v3.py`: `8588c0dfaf1436b8be9387dbb15bb3eff6744d35573bc97e3c7d0a30e4887264`
- `benchmark_control_v3.py`: `d85c28a5134e6ef435e09ed6b08b47d20ced8543a6fcb6f613708545b9203115`
- `upload_v3.py`: `bcf41a92c709fd9f24ee5175bf6c017427bb1be720962b0dc19fd6844ea0468c`

Independent read-only/CPU final audit staged before execution: `commands/independent_audit.py` SHA256 `edc0676eedccabe21eda25fbfbb980d2695ed1b54704da68b710e5a376d82293`; verifies all36 shapes/all5rounds/admission/B-R drift/42case/91tests/18replays/source identity/privateclone stopped. No GPU/model requests.

Final audit additionally independently rereads current source full identity and modelsHTTP200, no GPU work. Final pre-execution script SHA256 `c2bc59f9da0ab277ada2cb49873b04b68a48d3731b1a3adad821c15fcc3d20c1`.

Audit upload command SHA256 `63c5b4b5c0443ea68c6d51af9aaa6824c5e38a733280d0eeb5de4e47267e2710`. Uploads only a new immutable CPU audit command; no execution until current controller completes.

## Actual results and decision

Completed on mx-59 physical GPU6, MetaX C550, Torch2.8.0+metax3.7.0.7, actual Triton3.6.0. Effective snapshot18128d0b315822e3d0c5efa6d8fc8b67721af3a56456a8e6c369c2fc5c143268; exact mount/import/source/model parity passed. PCI0000:ca:00.0 / actual hostPID970931 matched docker top to mx-smi GPU6; no inference requests. Original qwen3vl opt17/8030 remains PID346908/ticks681351047, code/argv/env/model/tokenizer/config unchanged, models200. Private clone baseline restored and stopped; no production/PR update.

- 42 B/C bitwise cases, five CPUint64 prefix-oracle shapes, inherited91 tests, six extra graph captures x3 changed-input replays all passed. Input/output aliasing and defaultRNG preserved. Candidate modifies integer statistics only; independent inherited floating-point tolerances unchanged.
- Full36-row matrix x3 methods all admitted/comparable; five fixed B/C/R cycles each, all raw rounds retained. Maximum B/R drift: normal2.8544%, counts/mask1.1628%, graph0.3078%, all within frozen5% guard.
- B64 BF16-grid k20/p.8 V151936: counts/prefix/mask with common clone0.464000→0.392448ms (15.42% lower); normal fullAPI1.763328→1.691392ms (4.08% lower); graph1.705637→1.638590ms (3.93% lower).
- B64/V262144 same inputs: stage0.769280→0.637184ms (17.17% lower); normal2.934400→2.801792ms (4.52% lower); graph2.850440→2.747166ms (3.62% lower).
- Counterexamples retained: B1/V4096 normal+2.29%; B8/V151936 BF16-grid normal+8.16% while graph-1.57%; B64/V4096 normal+10.54%. Arbitrary FP32 B64 large-vocab fullAPI improves only1.03%/1.30%, despite stage15.49%/18.44% improvement.
- Therefore reviewer identified a real avoidable statistics cost. Forced prefix at all p shapes is not a uniform performance win. Additional launch and two workspace allocations are explicit source differences; normal-vs-graph observations motivate focused host/launch analysis, but this run did not profile or isolate each cost. Do not treat graph timing as proof the model sampler runs inside its model graph. Preserve small-shape original path; shape-scoped integration would require a separate frozen implementation/verification, not deployed here.
- Stats-only logical reads at B64/V262144 originally512MiB, candidate about1.25MiB including prefix writes/mask scalar reads. These are logical operation counts, not measured HBM traffic. Cache reuse and remaining sorting/clone/softmax/cumsum limit complete-interface benefit. No profiler/HBM measurement, model throughput or E2E result/gate claimed. No SOP change justified by this component-only experiment.

### Complete normalized comparison

Normal: upstream Benchmark.get_latency KERNEL mode; graph: upstream CUDAGRAPH mode; stage: counts+optionalprefix+mask with common output clone, sort/threshold precomputed and workspaces preallocated. Negative change means lower latency. Normal latency is a GPU-event benchmark with normal submissions, not a pure CPU wall-time measurement. BF16-grid input is FP32 tensor whose values are exactly BF16-representable; FP32 uses arbitrary values. both=k20/p.8, p=p-only.8. k-only path unchanged and correctness-covered.

| Input | M | V | Filter | Baseline normal ms | Candidate normal ms | Normal change | Graph change | Stage change |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| BF16-grid | 1 | 4096 | both | 0.122880 | 0.125696 | +2.29% | +2.09% | +12.50% |
| BF16-grid | 1 | 4096 | p | 0.119808 | 0.122368 | +2.14% | +2.05% | +15.00% |
| BF16-grid | 1 | 151936 | both | 0.284928 | 0.288256 | +1.17% | +0.31% | +9.62% |
| BF16-grid | 1 | 151936 | p | 0.271872 | 0.273152 | +0.47% | +0.37% | +4.73% |
| BF16-grid | 1 | 262144 | both | 0.362496 | 0.361984 | -0.14% | -0.13% | +0.00% |
| BF16-grid | 1 | 262144 | p | 0.354048 | 0.353536 | -0.14% | -0.18% | +0.53% |
| BF16-grid | 8 | 4096 | both | 0.557824 | 0.605696 | +8.58% | +1.80% | +10.53% |
| BF16-grid | 8 | 4096 | p | 0.469248 | 0.519936 | +10.80% | +1.63% | +10.64% |
| BF16-grid | 8 | 151936 | both | 0.600704 | 0.649728 | +8.16% | -1.57% | -5.14% |
| BF16-grid | 8 | 151936 | p | 0.556032 | 0.609280 | +9.58% | -1.78% | -4.55% |
| BF16-grid | 8 | 262144 | both | 0.598784 | 0.582656 | -2.69% | -2.42% | -10.86% |
| BF16-grid | 8 | 262144 | p | 0.554368 | 0.540672 | -2.47% | -1.73% | -10.46% |
| BF16-grid | 64 | 4096 | both | 0.538112 | 0.594816 | +10.54% | +1.00% | +4.97% |
| BF16-grid | 64 | 4096 | p | 0.497152 | 0.541952 | +9.01% | +0.83% | +5.06% |
| BF16-grid | 64 | 151936 | both | 1.763328 | 1.691392 | -4.08% | -3.93% | -15.42% |
| BF16-grid | 64 | 151936 | p | 1.617664 | 1.551360 | -4.10% | -3.88% | -14.93% |
| BF16-grid | 64 | 262144 | both | 2.934400 | 2.801792 | -4.52% | -3.62% | -17.17% |
| BF16-grid | 64 | 262144 | p | 2.679552 | 2.557056 | -4.57% | -3.81% | -16.26% |
| FP32 | 1 | 4096 | both | 0.120320 | 0.122880 | +2.13% | +2.05% | +11.63% |
| FP32 | 1 | 4096 | p | 0.115456 | 0.118016 | +2.22% | +2.00% | +10.47% |
| FP32 | 1 | 151936 | both | 0.278528 | 0.280320 | +0.64% | +0.32% | +5.41% |
| FP32 | 1 | 151936 | p | 0.271616 | 0.273664 | +0.75% | +0.36% | +5.44% |
| FP32 | 1 | 262144 | both | 0.361984 | 0.362112 | +0.04% | -0.40% | +0.52% |
| FP32 | 1 | 262144 | p | 0.353792 | 0.353536 | -0.07% | +0.47% | +0.00% |
| FP32 | 8 | 4096 | both | 0.507392 | 0.557312 | +9.84% | +0.50% | +11.46% |
| FP32 | 8 | 4096 | p | 0.491008 | 0.551424 | +12.30% | +0.56% | +9.47% |
| FP32 | 8 | 151936 | both | 1.171456 | 1.165312 | -0.52% | -0.49% | -5.28% |
| FP32 | 8 | 151936 | p | 1.148928 | 1.144576 | -0.38% | -0.60% | -4.66% |
| FP32 | 8 | 262144 | both | 1.808896 | 1.793536 | -0.85% | -0.40% | -11.33% |
| FP32 | 8 | 262144 | p | 1.774592 | 1.761536 | -0.74% | -0.56% | -9.19% |
| FP32 | 64 | 4096 | both | 0.509184 | 0.513280 | +0.80% | +0.27% | +6.56% |
| FP32 | 64 | 4096 | p | 0.501632 | 0.505728 | +0.82% | +0.24% | +4.97% |
| FP32 | 64 | 151936 | both | 6.535168 | 6.467840 | -1.03% | -0.98% | -15.49% |
| FP32 | 64 | 151936 | p | 6.389248 | 6.321664 | -1.06% | -1.01% | -15.43% |
| FP32 | 64 | 262144 | both | 10.977152 | 10.834176 | -1.30% | -0.94% | -18.44% |
| FP32 | 64 | 262144 | p | 10.718464 | 10.588032 | -1.22% | -0.91% | -16.54% |

### Evidence and incidents

Remote `op008-threshold-prefix-20261106/v2/results/benchmark.json`, `component-correctness.json`, `performance-completed-v3.json`, `runtime-mapping-v3.json`, `source-preserved-v3.json`, `independent-final-audit.json`, plus logs/pytest.log and manifests/upstream-benchmark-v3.json. Raw rounds/logs remain remote. Independent CPU audit recomputed all medians, admission/drift guards, complete36-row coverage, same-source identity/models200 and privateclone stopped. V1 interpreter PATH lookup and v2 missing benchmark import path are resolved tool incidents, retained as original failure.json files; no mathematical failure, no model requests/retries and no result overwritten. V3 only continued previously unstarted timing of the same verified candidate.

- `results/benchmark.json`: `11ef212c39b477337b78f7eabed8f1da1bb170cd66e98e3633929cd04f01d481`
- `results/component-correctness.json`: `665d744e66b2ef8933877c0dd7a5dbfd72bd2cbef835bdc06ee685c4870180e0`
- `results/performance-completed-v3.json`: `97700aac3e83c4760c6353ab5487ed4504275ea4c17bed426840c04d938367a8`
- `results/source-preserved-v3.json`: `08c0787a434a3c5e38822d243f63b1e5d4265dcb71a0b3f6ef87a3a5f0ffe589`
- `results/runtime-mapping-v3.json`: `4f17418cee0bf55f90d52849897c7a721b56f8df7f62a9bbc599e04ebfa5b077`
- `logs/pytest.log`: `c9dc3cb0eda486b31af9e9e0f6f07b05b3489bbcee81cdb1164dfb73dda5fb35`
- `manifests/upstream-benchmark-v3.json`: `4fadfcdcda0b70ad476473d754231893fa063821f8caa2590a653d74964877b4`
- independent-final-audit.json: `69bc81daee787a292ba240fa9508f2d37055a16a99aa6e61b5597bcd861dd578`
