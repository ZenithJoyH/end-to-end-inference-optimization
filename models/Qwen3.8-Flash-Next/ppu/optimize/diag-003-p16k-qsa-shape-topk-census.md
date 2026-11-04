# diag-003: P16K QSA shape and TopK census

Status: `complete_no_go`. This non-performance diagnostic ran on PPU0–7/8031 using an isolated private source copy and Triton cache.

Collect CPU-available logical metadata for bounded real P16384/D128/C64/N64 execution: phase/marker, layer, graph key, rows, actual tokens, maximum sequence length, score columns, page-table width, page size, rows per chunk, request-run count and visible-width distribution. Correlate existing profiler kernel names and counts for score, every TopK stage, expand and sparse consumers; if trace names cannot bind a component, record the gap instead of guessing.

Instrumentation must not copy large tensors to host, synchronize the device, change selected outputs or participate in a performance claim. Use a bounded preallocated record path and flush only after the request. Prove the service imports the private copies and reproduces the frozen Plugin/FlagGems-vllm/FlagGems baseline before the instrumentation diff. Validate layer/call accounting, request success, graph replay and unchanged fixed replay outputs.

This diagnostic may run concurrently with diag004; all wall and device timing from that window is invalid. Its result must be a shape/component census and a conservative headroom bound only.

## Result

The fixed replay passed 24/24 and exactly matched the retained service50 canonical output. P16384/D128/C64/N64 then completed 64/64 requests with zero failures. All eight TP ranks recorded 22,668 bounded records with zero drops: 15,732 builder, 3,468 select and 3,468 sparse records. The cross-rank canonical census was identical.

Across the 12 QSA layers, select and sparse consumers paired strictly one-to-one within every layer lifecycle. There were 3,060 target pairs: 3,048 main-graph calls with `q=[4096,4,128]` and 12 tail calls with `q=[1968,4,128]`. Score width was 4096 for the first 12 calls and 4128 thereafter; chunk count was always one. The effective width was already 4096/4128, so the 8448 static cap was not active and a 4352 cap would not reduce this target workload.

Using the exact rank0 `prof-007` marker-wall denominators, cumulative device activity for `score + QSA TopK + expand` was:

| Phase | Marker wall | Selection-chain activity | Loose elimination upper bound |
|---|---:|---:|---:|
| Prefill | 0.600843 s | 0.011977 s | 1.993% |
| Decode | 139.054060 s | 8.070025 s | 5.804% |
| Mixed | 41.191392 s | 2.672370 s | 6.488% |

These cumulative device activities may overlap and are not additive speedups. Even the deliberately loose assumption that the whole selection chain becomes free remains below the frozen 8% complete-QSA gate in every phase. Including the sparse consumer raises the loose activity envelope to about 21.4%/22.2%/24.2%, but the previously tested direct-address and sparse transaction mechanisms failed, and this census found no new credible complete-transaction mechanism. Decision: `no_go_no_credible_ge_8pct_complete_qsa_transaction_candidate`.

Evidence root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/diag-003-p16k-qsa-shape-topk-census/diag003-20260921T152300Z-01`. Final receipt SHA-256: `ced131498de10d81ae0253b6747ec47b0c10198bc84245ff0e5fa03d28e63bba`; aggregate SHA-256: `aad3b1f0ec4af3978a64b34d1facbe4e921248895227784f17221bd41235de39`; shape summary SHA-256: `57049ead62cddbdcfd6c3281020084aa3c6719801ac50a868f5045fd5e3463e7`.

The frozen 8031 process tree was precisely stopped, PPU0–7 were released, the private source/cache was verified deleted, and the shared-source fingerprint remained unchanged.
