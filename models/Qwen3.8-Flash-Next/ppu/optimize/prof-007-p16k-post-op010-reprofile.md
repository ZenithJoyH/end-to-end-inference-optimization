# prof-007: post-op010 P16K phase re-profile

## Goal and status

- Classification: `profiling/diagnostic`.
- Status: `complete`.
- Target: refresh the Prefill, Decode, and Mixed hotspot order on the exact retained P16K combination after op010 and the valid op024 no-go.
- Workload: bounded P16384/D128/C64/N64, one no-profiler warmup plus one profiled measured round unless the profiling contract requires a smaller probe for trace-size safety.
- Boundary: profiler-on wall time is not a performance result and cannot be compared with perf014 as a speedup.

## Required evidence

- Run on an isolated fresh service using PPU0-7/8031; preserve and identity-guard the retained PPU8-15/8030 service.
- Freeze source fingerprint, container/image, launch arguments, graph mode, QSA bound 8448, M64 BM16, native mm/mm_out, maxseq64 and batched4096 before capture.
- Capture one async trace and all TP0-7 worker traces; require gzip integrity, parser readability, non-empty events and exact rank coverage.
- Segment using the source-proven marker semantics: `new>0,cached=0` Prefill, `new=0,cached>0` Decode, both non-zero Mixed. Do not infer phases from a fixed marker name.
- Report marker wall spans, device activity and invocation counts per rank for QSA MQA/sparse, fused MoE, native/general GEMM, AllReduce, synchronization, graph wrapper and identifiable host gaps. Overlapping activity must not be added into a speedup claim.
- Separate capture/export overhead and outside-window activity. Record any observer effect or missing coverage as incomplete.
- Stop only the frozen temporary service PID/start-ticks tree; restore 8031 idle and verify retained 8030 identity/health.

## Decision rule

The profile passes only as attribution evidence when every rank and phase is covered and integrity checks succeed. Rank the next one to three candidates by current phase weight, causal evidence, conservative end-to-end headroom, implementation cost and rollback risk. Rejected historical directions remain rejected unless the new trace proves a materially different production shape or mechanism.

## Capture and integrity

- Workload: P16384/D128/C64/N64; one no-profiler warmup and one profiled measured round. Both completed 64/64 requests with zero failures.
- Trace set: one async trace and TP0–7, all passing gzip, parser, non-empty event, exact-rank and phase-marker checks.
- Every rank produced 385 consistent phase markers; `phase-completeness=complete` and method consistency passed.
- Profiler observer effect was substantial: output throughput -14.0567% and duration +16.3558% versus warmup. These numbers are diagnostic overhead, not a performance regression or speedup claim.

## Current phase attribution

Times are cross-rank medians of profiler-on activity and may overlap. Percentages below use each phase's summed device activity only; they must not be added to sync, graph-wrapper or uncovered proxies.

| Phase | Marker span | Device activity | QSA sparse + MQA | Fused MoE | Native GEMM | AllReduce |
|---|---:|---:|---:|---:|---:|---:|
| Prefill | 600.857ms | 454.815ms | 125.089ms | 104.334ms | 89.110ms | 44.672ms |
| Mixed | 41.270s | 31.548s | 9.479s | 7.315s | 5.615s | 2.961s |
| Decode | 139.317s | 101.420s | 29.497s (29.1%) | 23.719s (23.4%) | 17.618s (17.4%) | 10.510s (10.4%) |

`mm_kernel_general` was absent in all phases, confirming the retained op010 native provider path. Device max/min rank spread was 1.0555/1.0747/1.0873 for Prefill/Mixed/Decode. QSA, MoE and native GEMM were nearly rank-balanced, while AllReduce and synchronization carried the main imbalance. Decode sync 50.404s, graph-wrapper 99.784s and device-uncovered proxy 37.897s overlap with kernel work and are not additive opportunity estimates.

Trace launch evidence proves QSA sparse grid `[4096,1,1]`, block128, 166 registers and 24704 shared bytes; QSA MQA grid `[4096,129,1]`, block128, 62 registers and 256 shared bytes. Dominant MoE launches used grids `[1656,1,1]` and `[16560,1,1]`, block256, 160 registers and 65536 shared bytes. The trace does not contain logical tensor dimensions, so no missing shape is inferred from these grids.

## Decision

The refreshed ordering supports two independent candidate audits: QSA sparse/MQA shape/tile work that does not repeat the rejected static-4352 cap, and fused-MoE Decode specialization that does not repeat failed M40/48/56/63 BM16, BN128, GEMM1+SiLU or split-K proposals. Native GEMM remains material enough to trigger only the pre-recorded op023 contract-repaired D128 rerun; the profile cannot isolate `mm_out`, so it does not authorize a D1024 expansion.

Evidence root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-007-p16k-post-op010-reprofile`. Final receipt SHA-256 is `6d4e27d16e30f6030fcbedeca74fe96f2890fc8743facc6dbab9105d6c3ede3d`; aggregate SHA-256 is `bde5cbf86eeef073cef0c7ccca9a69e94eb60889da795ff7259c01484fed465b`. Cleanup left 8031 and PPU0–7 empty and preserved the exact 8030 service at health 200.
