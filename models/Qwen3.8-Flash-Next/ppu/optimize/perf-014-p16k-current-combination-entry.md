# perf-014: P16K current-combination scenario entry

## Direction and status

- Mode: `inference-performance-evaluation/baseline`.
- Status: `complete`.
- Parent target: `p16384-d1024-c64-n128`.
- Baseline kind: `scenario-entry`.
- Parent candidate: `maxseq64-bt4096 + M64 BM16 + op008 runtime QSA bound capped8448 + op010 native mm/mm_out`.
- Conclusion boundary: the older op008 P16K checkpoint predates op010 and is historical parent evidence, not a same-configuration current baseline.

## Frozen phase workloads

| Phase | Workload | Purpose |
|---|---|---|
| Prefill | P16384/D1/C32/N64 | Prompt-processing and TTFT/input-token view; Decode residual is one generated token plus scheduling overhead |
| Decode | P16384/D1024/C32/N64 | Long autoregressive/KV view at lower concurrency; still includes prompt admission and client-visible scheduling/network costs |
| Mixed | P16384/D1024/C64/N128 | Parent target end-to-end interference and guard view |

Each phase uses the maintained runner, prefix cache disabled, exact current service identity, three warmup rounds and three measured rounds, seed/workload settings matching the previous P16K contract, unique run IDs, and separate external output directories. The main metrics are phase-appropriate token throughput and duration; TTFT, TPOT, ITL, E2E, failures and warmup stability are guards where available.

## Gates and stop rules

The entry is complete only if all requested rounds finish with zero request failures, required finite metrics, stable warmup, exact service/source identity, graph path evidence and disabled prefix cache. Stop and preserve `incomplete` evidence on unsupported context, OOM, graph/service failure, request failure, identity drift, warmup instability or diagnostic-budget expiry. A shortened workload, if required, receives a new milestone ID and a same-workload baseline; it cannot be renamed as the formal P16K target.

No source or service change belongs to this experiment. After the three phase views are valid, compare their hotspot signals with `prof-003`. If op010 may have moved the order and low-overhead evidence cannot isolate the next bottleneck, run bounded `prof-007` reprofile before implementing a new candidate.

## Deferred P4K direction recorded

The remaining P4K QSA frontier is exact cross-row K/V reuse without the rejected direct-address clear/build workspace. Any future implementation must reduce repeated K/V or softmax work, preserve request boundaries and graph behavior, include construction/fallback in the complete transaction, and prove at least 8% real-shape transaction gain before service integration. It is not part of perf-014.

## Existing evidence

- Prior P16K op008 checkpoint: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-op008-full-checkpoint-summary-01.json`.
- Prior P16K profiler: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-003-p16k-post-qsa-bound`.
- Current retained combination identity and planning review: `models/Qwen3.8-Flash-Next/ppu/optimize/state.yml`, `plan-026-20260921-user-redirect-p16k-reentry`.

## Prefill result

The current-combination Prefill view completed on live service `9b65cc77d73c-8030-2655295-260762280` with the frozen P16384/D1/C32/N64 plan. All three warmup and three measured rounds completed 64/64 requests with zero failures. Warmup total-token-throughput relative spread was 0.1050%, passing the 10% stability gate.

Measured medians from rounds 4–6 are 7699.05 tok/s total-token throughput, 136.20s benchmark duration, 68053.67ms median TTFT, 51644.28ms mean TTFT, and 68125.38ms P99 TTFT. This is the current-combination scenario-entry result, not a causal op010 gain: the older op008 checkpoint was recorded on a different service/time and remains historical parent evidence.

- Run record: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-current-op010-prefill-baseline-01/run-record.json`.
- Run-record SHA-256: `d2b505bdf0a799b6caac704d077e3420dd78a4692fe5a0a882b15f4941fa016d`.
- Service after the run: HTTP 200, zero running requests, zero waiting requests.

## Invalid Decode attempt preserved

The first Decode attempt is not accepted as baseline evidence. Its third warmup round overlapped op-023 service58 traffic on PPU0–7 and slowed from about 312.8s to 336.9s while P99 ITL rose from about 586.7ms to 1352.3ms. Measured round 4 then began during exact service58 cleanup. The attempt was interrupted by stopping only the verified benchmark client tree; service50 remained healthy. Its directory was archived as `p16k-current-op010-decode-baseline-01.invalid-shared-host-interference-20260921` and must not enter any median or comparison.

- Archive receipt: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/p16k-current-op010-decode-invalid-shared-host-interference-20260921.txt`, SHA-256 `cd6ca70a080085a2c359efe1c4b55a911d7fe74d7ed612fbec90fcdd10cb5474`.
- Exact client-stop receipt: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/transitions/p16k-current-op010-decode-client-stop-20260921.txt`, SHA-256 `cb250d0e1b5a9bc610de898c4ed56fa8a20172e72883381e9ba6da3ef8da1c3f`.

## Decode result

After keeping port 8031 and PPU0–7 silent, the clean P16384/D1024/C32/N64 rerun completed all three warmup and three measured rounds with 64/64 successful requests per round and zero failures. Warmup rounds 2–3 had total-token throughput 3567.16/3549.87 tok/s, a relative spread of about 0.49%.

Measured rounds 4–6 had durations 311.61/311.95/312.01s and total-token throughput 3575.35/3571.39/3570.76 tok/s. Their medians are 311.95s duration, 3571.39 tok/s total throughput, and 210.085 tok/s derived output throughput (`65536 / duration`). Median guards are 4020.71ms TTFT, 143.61ms TPOT and 86.30ms ITL; P99 guards are 71190.81ms TTFT, 144.92ms TPOT and 583.55ms ITL. Measured total-throughput spread is 0.1285%.

- Run record: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-current-op010-decode-baseline-01/run-record.json`.
- Run-record SHA-256: `244d983b3faa931038819ae1e0a1277570f24b119747100edd62a556ca3a6465`.
- Validator note: its `output_throughput` field is null for these runs; the exact output count and duration are present, so output throughput is reproducibly derived as `65536 / benchmark_duration`.

## Mixed result

P16384/D1024/C64/N128 completed all three warmup and three measured rounds with 128/128 successful requests per round and zero failures. Warmup rounds 2–3 had total-token throughput 4794.34/4782.88 tok/s, a relative spread of about 0.24%.

Measured rounds 4–6 had durations 465.76/464.75/465.69s and total-token throughput 4784.01/4794.51/4784.79 tok/s. Their medians are 465.69s duration, 4784.79 tok/s total throughput and 281.458 tok/s derived output throughput (`131072 / duration`). Median guards are 5278.39ms TTFT, 211.37ms TPOT and 92.91ms ITL; P99 guards are 144849.11ms TTFT, 213.71ms TPOT and 596.88ms ITL. Measured total-throughput spread is 0.2194%.

- Run record: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/performance/p16k-current-op010-mixed-baseline-01/run-record.json`.
- Run-record SHA-256: `3317fa718b91d17de6e0c28f637fbef2c33f54a6fa11575ce2face5155030f73`.
- Service after the run: HTTP 200, zero running requests, zero waiting requests.
- Conclusion boundary: perf-014 is the current-combination scenario-entry baseline. It does not by itself attribute the improvement over the older op008 checkpoint to op010, because that comparison is not a fresh A/B/R.
