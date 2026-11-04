# 20261022-thinking-gpqa-metax103 / optimize

<!-- e2e:summary:start -->

- 案例：20261022-thinking-gpqa-metax103
- 当前状态：fw006_paused_by_user_manual_performance
- 当前候选：mx59-acc003-5ea09be+fw-001+op-001+op-002+fw-003+op-004+op-005+op-006+fw-004+fw-005-native-p2p+cleanup003+op007
- 下一步：User manually tests; no automatic restart, benchmark, profiling or changes until explicit resume

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| fw-005 | retain_native_TP_P2P_compute_stream_lifetime_fix | p16384-d1024-c64-n128 | [fw-005.md](fw-005.md) |
| fw-004 | retain_installation_no_new_stability_or_performance_claim_incident_open | native-plugin-initialization | [fw-004.md](fw-004.md) |
| env-001 | migration_passed | migration | [env-001.md](env-001.md) |
| acc-001 | 170/198 normalized extraction accepted; original strict receipt retained | gpqa-diamond-198-thinking | [acc-001.md](acc-001.md) |
| audit-001 | retain_current_code_no_new_changes | current-code-performance-audit | [audit-001.md](audit-001.md) |
| perf-001 | incomplete | four-scenario-current-baseline | [perf-001.md](perf-001.md) |
| fw-001 | retained | p16384-d1024-c64-n128 | [fw-001.md](fw-001.md) |
| op-001 | retained | p32768-d1024-c64-n128 | [op-001.md](op-001.md) |
| fw-002 | Retain op002 stability repair; original reference has no admitted measured rounds after3bounded warmup attempts; do not claim equivalence or whole-stack speedup. | p32768-d1024-c64-n128 | [fw-002.md](fw-002.md) |
| op-002 | targeted_performance_passed | p32768-d1024-c64-n128 | [op-002.md](op-002.md) |
| fw-003 | retained: native compilation/fusion restored; fresh GPQA169/198 passed80%; all3fullP32 passed, noerrors/JIT; original-image formal baseline still incomplete | p32768-d1024-c64-n128 | [fw-003.md](fw-003.md) |
| op-003 | Deferred, not applied: isolated GPU metadata fix validated; prefer complete native compile restoration first | p32768-d1024-c64-n128 | [op-003.md](op-003.md) |
| op-004 | retained: MetaX native FP32 GEMM removes weight materialization/generic MM; GPQA172/198; all3fullP32 valid and frozen spread passed. Third round has7other new kernels: fully precompiled steady-state coverage remains incomplete, not original-image equivalence. | p32768-d1024-c64-n128 | [op-004.md](op-004.md) |
| op-005 | retained_for_original7_shape_JIT_fix; frozen5pct throughput/TPOT thresholds passed narrowly, third-round slowdown remains and full precompiled coverage incomplete | p32768-d1024-c64-n128 | [op-005.md](op-005.md) |
| op-006 | retained: NT Default log-M selector and bounded cache preparation; all3 P32 within frozen5% throughput/TPOT variability, zero NT JIT/cache writes. Residual index/mHC JIT2 in third; full-chain zero-JIT and final4scenario acceptance incomplete | p32768-d1024-c64-n128 | [op-006.md](op-006.md) |
| op-007 | delete RMS patch and install_rms call; keep native compiler selection | ["p1024-d1024-c64-n128", "p32768-d1024-c64-n128"] | [op-007.md](op-007.md) |
| cleanup-004 | 13 effective settings in start-model.sh;38 obsolete/unnecessary settings removed;8 platform defaults kept | service-configuration | [cleanup-004.md](cleanup-004.md) |
| cleanup-005 | retain_slim_runtime_keep_original_backup | container-footprint | [cleanup-005.md](cleanup-005.md) |
| cleanup-006 | retain_seven_exports_removed_default_yaml | launch-configuration | [cleanup-006.md](cleanup-006.md) |
| cleanup-007 | retain_three_exports_removed | launch-configuration | [cleanup-007.md](cleanup-007.md) |
| fw-006 | paused; no fw006 fix installed; preserve all negative and incomplete evidence | p32768-d1024-c64-n128 | [fw-006.md](fw-006.md) |
| accuracy-20261029 | User-requested accuracy complete; no source/service modifications; no claim that original64K OOM fixed | — | [accuracy-20261029.md](accuracy-20261029.md) |
| cleanup-008 | Portable image retained; original service healthy and original container/volume/code/script preserved. User can use local image directly. | — | [cleanup-008.md](cleanup-008.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa-diamond-198-thinking | original_formal | exact_match,strict-match | 0.7727272727272727 | fraction | Historical frozen strict result; current acceptance uses user-confirmed170/198 |
| gpqa-diamond-198-thinking | user_accepted | bold_removed_exact_match | 0.8585858585858586 | fraction | Same198 outputs; bold normalization explicitly accepted by user2026-10-22 |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | request_throughput | 0.6272371133550654 | request/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | output_throughput | 642.290804075587 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | total_token_throughput | 1284.581608151174 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_ttft_ms | 6682.626925641671 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_ttft_ms | 4032.0440884679556 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_ttft_ms | 17145.268865209073 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_ttft_ms | 18101.15803470835 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_tpot_ms | 92.98437484808893 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_tpot_ms | 94.94581030734531 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_tpot_ms | 97.37471533567806 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_tpot_ms | 98.1835796869745 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_itl_ms | 92.98437502106184 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_itl_ms | 81.99385646730661 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_itl_ms | 87.17956515029073 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_itl_ms | 784.322493933141 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | mean_e2el_ms | 101747.69324024965 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | median_e2el_ms | 101535.81806458533 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p95_e2el_ms | 114334.88282561302 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | p99_e2el_ms | 115847.7112262696 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p1024-d1024-c64-n128 | diagnostic_current_baseline | benchmark_duration | 204.06955722905695 | s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | request_throughput | 0.4276101819376811 | request/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | output_throughput | 437.8728263041854 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | total_token_throughput | 2189.364131520927 | token/s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_ttft_ms | 19049.124712357298 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_ttft_ms | 4365.717804990709 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_ttft_ms | 59620.5686694011 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_ttft_ms | 64984.39759889618 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_tpot_ms | 126.36681695622123 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_tpot_ms | 139.49585494604455 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_tpot_ms | 140.727292735745 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_tpot_ms | 142.10201382147238 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_itl_ms | 126.36681714909456 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_itl_ms | 83.01894180476665 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_itl_ms | 88.37300669401883 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_itl_ms | 1020.1140977256 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | mean_e2el_ms | 148586.3469212054 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | median_e2el_ms | 147306.15263525397 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p95_e2el_ms | 203199.22011969608 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | p99_e2el_ms | 208355.3481924348 | ms | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p4096-d1024-c64-n128 | diagnostic_current_baseline | benchmark_duration | 299.3380546271801 | s | recovery-v2; all3 measured median; completed; no A/B or speedup claim |
| p16384-d1024-c64-n128 | fw001_only_baseline | request_throughput | 0.18714453515933124 | request/s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | output_throughput | 191.6360040031552 | token/s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | total_token_throughput | 3257.812068053638 | token/s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_ttft_ms | 70752.14057367702 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_ttft_ms | 9754.533527418971 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_ttft_ms | 236470.8114918321 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_ttft_ms | 257340.93551166359 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_tpot_ms | 260.9264776931275 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_tpot_ms | 315.95076265620145 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_tpot_ms | 318.2095663559205 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_tpot_ms | 318.6691467407162 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_itl_ms | 260.9264778820036 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_itl_ms | 90.66702611744404 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_itl_ms | 988.6310052126646 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_itl_ms | 1472.7796279452741 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | mean_e2el_ms | 337507.6729493594 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | median_e2el_ms | 332586.70236263424 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p95_e2el_ms | 560984.7536621615 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | p99_e2el_ms | 581777.4182157033 | ms | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p16384-d1024-c64-n128 | fw001_only_baseline | benchmark_duration | 683.9633328914642 | s | all3 measured per-metric median after declared fresh warmups; exact D1024/C64/N128; prefix disabled; source/service not pooled |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | request_throughput | 0.10694989016939468 | request/s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | output_throughput | 109.51668753346016 | token/s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | total_token_throughput | 3614.0506886041853 | token/s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_ttft_ms | 140343.06927179568 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_ttft_ms | 15989.924564026296 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_ttft_ms | 473795.3542062081 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_ttft_ms | 516671.1899105273 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_tpot_ms | 439.0424904395456 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_tpot_ms | 551.376257097223 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_tpot_ms | 555.4177873228055 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_tpot_ms | 556.1495798993 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_itl_ms | 439.042490628877 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_itl_ms | 96.24035842716694 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_itl_ms | 1345.595386531204 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_itl_ms | 1537.668632157147 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | mean_e2el_ms | 589336.1018699215 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | median_e2el_ms | 579107.886461541 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p95_e2el_ms | 1041540.157169476 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | p99_e2el_ms | 1082963.0328418317 | ms | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_native_valid_unstable | benchmark_duration | 1196.822173424065 | s | All3 native-valid measured rounds retained; descriptive per-metric median, spread12.913% fails10%; not a steady-state acceptance |
| p32768-d1024-c64-n128 | fw001_op001_op002_targeted_stable | output_throughput | 110.50963681370723 | token/s | Three complete measurements;prefixoff;spread1.0385%;noOOM/illegal;not4scenario/fullaccuracy acceptance |
| p32768-d1024-c64-n128 | fw001_op001_op002_targeted_stable | total_token_throughput | 3646.818014852339 | token/s | Three complete measurements;prefixoff;spread1.0385%;noOOM/illegal;not4scenario/fullaccuracy acceptance |
| p32768-d1024-c64-n128 | fw001_op001_op002_targeted_stable | mean_ttft_ms | 138314.7367331112 | ms | Three complete measurements;prefixoff;spread1.0385%;noOOM/illegal;not4scenario/fullaccuracy acceptance |
| p32768-d1024-c64-n128 | fw001_op001_op002_targeted_stable | mean_tpot_ms | 434.97776354902675 | ms | Three complete measurements;prefixoff;spread1.0385%;noOOM/illegal;not4scenario/fullaccuracy acceptance |
| p32768-d1024-c64-n128 | fw001_op001_op002_targeted_stable | benchmark_duration | 1186.0685074999928 | s | Three complete measurements;prefixoff;spread1.0385%;noOOM/illegal;not4scenario/fullaccuracy acceptance |
| p32768-d1024-c64-n128 | fw003_targeted_candidate | output_throughput | 180.18700832177245 | token/s | All3 full P32; prefixOFF; spread0.3096%; fresh GPQA; noOOM/illegal/JIT; not original-image equivalence or four-scenario acceptance |
| p32768-d1024-c64-n128 | fw003_targeted_candidate | mean_ttft_ms | 77629.29589567648 | ms | All3 full P32; prefixOFF; spread0.3096%; fresh GPQA; noOOM/illegal/JIT; not original-image equivalence or four-scenario acceptance |
| p32768-d1024-c64-n128 | fw003_targeted_candidate | mean_tpot_ms | 270.8332816872491 | ms | All3 full P32; prefixOFF; spread0.3096%; fresh GPQA; noOOM/illegal/JIT; not original-image equivalence or four-scenario acceptance |
| p32768-d1024-c64-n128 | fw003_targeted_candidate | mean_itl_ms | 270.83328188165865 | ms | All3 full P32; prefixOFF; spread0.3096%; fresh GPQA; noOOM/illegal/JIT; not original-image equivalence or four-scenario acceptance |
| gpqa-diamond-198-thinking | fw003_new_formal | exact_match,strict-match | 0.8535353535353535 | fraction | New198 samples, native official extractor frozen before generation; >=80%; same final service; historical170/198 not rewritten |
| p32768-d1024-c64-n128 | op004_targeted_native_gemm | output_throughput | 203.7078055255895 | token/s | All3 P32 measures retained; spread5.3714% passes10%; third newJIT7, fullyprecompiled coverage incomplete; noOOM/illegal; historical-only comparison |
| p32768-d1024-c64-n128 | op004_targeted_native_gemm | mean_ttft_ms | 74792.5618991867 | ms | All3 P32 measures retained; spread5.3714% passes10%; third newJIT7, fullyprecompiled coverage incomplete; noOOM/illegal; historical-only comparison |
| p32768-d1024-c64-n128 | op004_targeted_native_gemm | mean_tpot_ms | 237.17020581955651 | ms | All3 P32 measures retained; spread5.3714% passes10%; third newJIT7, fullyprecompiled coverage incomplete; noOOM/illegal; historical-only comparison |
| p32768-d1024-c64-n128 | op004_targeted_native_gemm | mean_itl_ms | 237.17020603526058 | ms | All3 P32 measures retained; spread5.3714% passes10%; third newJIT7, fullyprecompiled coverage incomplete; noOOM/illegal; historical-only comparison |
| p32768-d1024-c64-n128 | op004_targeted_native_gemm | benchmark_duration | 643.4314073622227 | s | All3 P32 measures retained; spread5.3714% passes10%; third newJIT7, fullyprecompiled coverage incomplete; noOOM/illegal; historical-only comparison |
| gpqa-diamond-198-thinking | op004_new_formal | exact_match,strict-match | 0.8686868686868687 | fraction | Fresh198 unique docs, official native metric frozen before generation, same no-profiler service, prefixOFF, threshold80% |
| p32768-d1024-c64-n128 | op005_targeted_dynamic_bounds | output_throughput | 201.38683862368526 | token/s | All3 retained; original7JIT0/0/0; otherJIT3/0/3; scalar spread<=5% narrowly, residual third slowdown; no fully-precompiled or B/C/R claim |
| p32768-d1024-c64-n128 | op005_targeted_dynamic_bounds | total_token_throughput | 6645.765674581614 | token/s | All3 retained; original7JIT0/0/0; otherJIT3/0/3; scalar spread<=5% narrowly, residual third slowdown; no fully-precompiled or B/C/R claim |
| p32768-d1024-c64-n128 | op005_targeted_dynamic_bounds | mean_ttft_ms | 75058.77038012841 | ms | All3 retained; original7JIT0/0/0; otherJIT3/0/3; scalar spread<=5% narrowly, residual third slowdown; no fully-precompiled or B/C/R claim |
| p32768-d1024-c64-n128 | op005_targeted_dynamic_bounds | mean_tpot_ms | 240.162927605986 | ms | All3 retained; original7JIT0/0/0; otherJIT3/0/3; scalar spread<=5% narrowly, residual third slowdown; no fully-precompiled or B/C/R claim |
| p32768-d1024-c64-n128 | op005_targeted_dynamic_bounds | mean_itl_ms | 240.1629278033686 | ms | All3 retained; original7JIT0/0/0; otherJIT3/0/3; scalar spread<=5% narrowly, residual third slowdown; no fully-precompiled or B/C/R claim |
| p32768-d1024-c64-n128 | op005_targeted_dynamic_bounds | benchmark_duration | 650.8469018917531 | s | All3 retained; original7JIT0/0/0; otherJIT3/0/3; scalar spread<=5% narrowly, residual third slowdown; no fully-precompiled or B/C/R claim |
| gpqa-diamond-198-thinking | op005_new_formal | exact_match,strict-match | 0.8585858585858586 | fraction | Fresh198 unique native samples, threshold80%, thinking, same prefixOFF no-profiler service |
| p1024-d1024-c64-n128 | op007_baseline | output_throughput | 1165.699267388531 | token/s | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_baseline | median_ttft_ms | 2483.1678913906217 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_baseline | median_tpot_ms | 52.41749899958935 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_candidate | output_throughput | 1165.9228599071143 | token/s | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_candidate | median_ttft_ms | 2432.1382911875844 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_candidate | median_tpot_ms | 52.123190196939284 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_revert | output_throughput | 1166.05953186565 | token/s | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_revert | median_ttft_ms | 2393.4347787871957 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p1024-d1024-c64-n128 | op007_revert | median_tpot_ms | 52.22937855541794 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_baseline | output_throughput | 208.21942525451536 | token/s | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_baseline | median_ttft_ms | 8502.754754386842 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_baseline | median_tpot_ms | 289.2051145529059 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_candidate | output_throughput | 206.52401241346823 | token/s | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_candidate | median_ttft_ms | 8788.02511189133 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_candidate | median_tpot_ms | 292.4257150631787 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_revert | output_throughput | 209.7111851587376 | token/s | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_revert | median_ttft_ms | 8538.084036670625 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| p32768-d1024-c64-n128 | op007_revert | median_tpot_ms | 287.6127848915122 | ms | performance03: median of all3 steady measurements; prefixOFF; B/C/R targeted passed; not4scenarioacceptance |
| gpqa-diamond-198-thinking | op007_candidate_accuracy03 | exact_match,strict-match | 0.8737373737373737 | fraction | Full198unique docs; C64/defaultsampling; thinkingON/prefixOFF;80%gate; not rebound to delivered prefixON source |

<!-- e2e:summary:end -->

## op-005 阶段历史结果与边界

[op-005](op-005.md) 已修复量化/padding等原7项的token边界特化与launch key，共6个FG/FGV生产文件。新完整thinking GPQA **170/198＝85.86%**通过80%阈值。同一服务、无profiler、prefix cache关闭，使用用户原始run_once完成三轮P32768/D1024/C64/N128。

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新增编译（总/原7项） |
|---|---:|---:|---:|---:|
| 1 | 201.3868 | 75.0588 | 240.1629 | 3/0 |
| 2 | 203.7935 | 74.4507 | 237.1143 | 0/0 |
| 3 | 194.3892 | 77.8273 | 249.0065 | 3/0 |

384/384成功，无OOM、非法访存或抢占。吞吐spread **4.6697%**、TPOTspread **4.9518%**勉强满足冻结5%阈值；**第三轮下降仍在，不能宣称根因完全解决或全链路零JIT**。第一轮另3项来自BF16 NT GEMM/index/mHC heads，第三轮3项均为NT GEMM；原目标7项均未复发。全部轮次保留，没有挑选或重跑替换慢轮。

中位吞吐201.3868tok/s为本组合P32 targeted观察。原镜像208.91仍仅预热参考，没有正式稳定对照或新独立B/C/R；本组合四场景最终验收未完成。下一步首查NT实际输入布局、选参和请求期benchmark/cache miss，不能盲目去掉有效EVEN/tile条件。


历史85.86%精度经用户确认通过，该分数属于原attempt01。性能修复前的代码审计覆盖39个生产文件和19个配套文件，详见[audit-001](audit-001.md)。主要机制为Attention减少padding/寄存器压力、Indexer分页与query分片、MCTlass/原生MoE工作区、mHC融合及局部mask/量化。原生gather已接管FGV同名路径；MoE调参部分字段及RMS hook不能算已确认收益。该审计阶段没有新增源码修改；当时的诊断性性能结果见下方perf-001摘要。

<!-- perf-001:final:start -->

perf-001历史快照时间：2026-10-23 00:23:00（Asia/Shanghai）。该阶段诊断性基线：P1K 642.29 token/s、P4K 437.87 token/s；P16K首次预热MCCL OOM，P32K未执行，四场景整体incomplete。

| 场景（D1024/C64/N128） | 状态 | 输出吞吐(token/s) | 总token吞吐(token/s) | mean TTFT(ms) | mean TPOT(ms) | mean ITL(ms) | mean E2EL(ms) | 批次耗时(s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1K | completed | 642.29 | 1,284.58 | 6,682.63 | 92.98 | 92.98 | 101,747.69 | 204.07 |
| P4K | completed | 437.87 | 2,189.36 | 19,049.12 | 126.37 | 126.37 | 148,586.35 | 299.34 |
| P16K | failed_oom_incomplete | — | — | — | — | — | — | — |
| P32K | not_run_incomplete | — | — | — | — | — | — | — |

历史170/198＝85.86%由用户确认精度通过，仍属于原attempt01与同一批198份输出；原strict153/198＝77.27%及其证据完整保留。恢复实例仅有新10/10最小回归和graph验证，没有新的完整GPQA分数或正式精度gate。

这是已保留组合代码的scenario-entry诊断性当前基线。没有未优化anchor、candidate/revert A/B或单优化消融，没有设定性能SLO/通过阈值，不声称加速倍数或完整正式性能验收通过。生产源码、权重、tokenizer均未新增修改。

逐轮指标、预热和波动见[baseline](../baseline/README.md)；完整实验说明见[perf-001](perf-001.md)。

<!-- perf-001:final:end -->

<!-- long-context-repair:start -->

## fw001/op001 阶段历史结果

| 输入 | 源码 | 输出吞吐(token/s) | mean TTFT(s) | mean TPOT(ms) | mean E2EL(s) | 整批耗时(s) |
|---|---|---:|---:|---:|---:|---:|
| p16384 | fw001_only_baseline | 191.64 | 70.752 | 260.926 | 337.508 | 683.963 |
| p32768 | fw001_op001_baseline | 109.52 | 140.343 | 439.042 | 589.336 | 1196.822 |

D1024/C64/N128、finite-batch、固定random长度、temperature0、ignore_eos；使用用户指定vllm_perf.py原run_once，prefix cache关闭。P16固定4预热+3测量；P32原4轮预热未稳态（零测量）全部保留，冻结恢复契约后再运行全新3轮预热（全部3轮spread≤5%）+3轮测量（要求spread≤10%，实际12.913%，未通过）。全部测量逐指标取描述性中位数，不丢第三轮；32K稳态性能结论为incomplete。TTFT/TPOT/ITL是含排队与调度的客户端代理。16K属于fw001-only，32K属于fw001+op001；没有同源码四目标正式验收或A/B加速结论。

32K每轮128/128成功，新恢复6轮合计768请求，无非法地址、OOM或服务ERROR；最终服务健康空闲。详细修复与逐轮值见[op-001](op-001.md)和[fw-001](fw-001.md)。32K结果：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/indexer-gather-oob-001/performance-recovery01/summary.json`，SHA `851fd8ff600e3fb412af18298f409352527c5d01670f117ec1c21373eeae805d`。

review-001：保留fw001→op001。故障已从MCCL延迟分配OOM定位到独立gather寻址错误并修复；尚无新组合的P16或四目标A/B数据，未把不同版本吞吐拼成组合加速。后续优化方向仅作延期记录，不在本次任务额外启动。

<!-- long-context-repair:end -->

第三轮吞吐95.540431 token/s、mean TPOT521.789389ms，较前两轮慢。三轮spread12.913%未达≤10%门槛，稳态性能状态为incomplete；所有轮次保留，未丢弃或重跑替换第三轮。

当前继续：[fw-002](fw-002.md) 已定位动态 copy 编译机制，[op-002](op-002.md) 的 MetaX top-k wrapper 最小修复及 10/10 模型回归通过，关闭 prefix cache 的两轮预热＋三轮测量已完成。三轮输出吞吐111.63/110.48/110.51 tok/s，TTFT136.85/138.31/138.74s，TPOT430.96/435.50/434.98ms，spread1.04%；无非法访存/OOM，测量轮新增编译均为0。原镜像同客户端对照已结束：三组预热均未通过5%稳态准入，保留incomplete，无正式一致性结论。

review-002（2026-10-23）：当前依赖顺序为 fw-001 → op-001 → op-002。op-002 独立算子实验及最小模型回归通过，首次完整 P32 预热 109.637 output tok/s、141.580 s TTFT、436.786 ms TPOT，新增 copy 编译 0；预热不能计为测量。三轮稳态结果现已通过；原镜像对照因三组预热不稳而incomplete，当前服务恢复后的18/18回归与graph核验通过。暂停扩展新优化方向；历史 GPQA 属于先前源码，当前没有新的全量 GPQA 分数或四目标组合验收。


<!-- op-002:final:start -->

当前P32布局修复的三轮中位吞吐为110.51tok/s，meanTTFT138.315s、meanTPOT434.978ms，spread1.04%，384/384成功，无新增编译、OOM或非法访存。原始镜像六轮完整预热均成功，但三组均未通过5%准入，对照incomplete，不能宣布性能一致或给出正式倍率。详见[op-002](op-002.md)和[fw-002](fw-002.md)。修复服务已恢复，18/18最小回归、7/7 graph capture、C1/C8多次replay及8个worker审计通过，prefix cache持续关闭。

<!-- op-002:final:end -->


<!-- op-004:final:start -->

## op-004 阶段历史结果

[op-004](op-004.md) 已将FP32输出GEMM从通用FG加转置复制切换到MetaX native NT路径，仅改两处Plugin生产文件。完整thinking GPQA **172/198＝86.87%**通过80%阈值；同实例、无profiler、prefix cache关闭完成三轮P32768/D1024/C64/N128。

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新增编译 |
|---|---:|---:|---:|---:|
| 1 | 204.2301 | 74.7926 | 236.0981 | 0 |
| 2 | 203.7078 | 74.5396 | 237.1702 | 0 |
| 3 | 193.2881 | 82.5454 | 246.3033 | 7 |

384/384成功，无OOM、非法访存或抢占；中位吞吐203.7078tok/s，较fw003同场景历史值180.1870观察提升13.05%。三轮spread5.3714%在冻结10%范围内，但第三轮仍有7个量化/padding/KV/MoE初始化新编译，完全预编译稳态覆盖未闭合；没有丢掉第三轮。原镜像208.91仅预热观察，不能宣布正式一致。TTFT/TPOT含排队、网络及调度。未做本组合四场景最终验收。

先前fw003恢复原生编译/融合的三轮180.2787/180.1870/179.7209及169/198精度均保留于[fw-003](fw-003.md)。当前运行的私有源码及回退、精度/性能原始证据由[op-004](op-004.md)和[结构化记录](state.yml)索引。

<!-- op-004:final:end -->

- [op-005](op-005.md)：尾部量化/padding等7项JIT收敛；内核227项与模型18项回归passed，新完整GPQA170/198通过，三轮P32完成；原7JIT0，当时第三轮NT JIT与下降仍开放；后续[op-006](op-006.md)已验证并修复NT搜索/JIT，残余index/mHC2。

<!-- op006-final -->

[op-006](op-006.md) 已复现并修复请求期 BF16 NT 选参：仅增加1个FG生产文件改动，Default log-M分桶并在请求前准备完整已验证形状范围，保留实际M/EVEN掩码与精确BenchmarkCache。新thinking GPQA **169/198=85.35%**通过80%阈值（op005为170/198，少1题）。

同一新实例、原始用户run_once、无profiler、prefix cache关闭，W3后保留全部三轮P32768/D1024/C64/N128：

| 轮次 | 输出吞吐(tok/s) | mean TTFT(s) | mean TPOT(ms) | 新编译（总/NT） |
|---|---:|---:|---:|---:|
| 1 | 203.3665 | 75.0368 | 237.2020 | 0/0 |
| 2 | 203.5084 | 74.9309 | 237.0885 | 0/0 |
| 3 | 201.2218 | 75.5128 | 239.9502 | 2/0 |

384/384成功，0 OOM/非法访存/抢占。吞吐spread **1.1244%**、TPOTspread **1.2064%**，均通过冻结5%阈值；三轮NT ConfigCache与BenchmarkCache均未变化。第三轮仍有index/mHC两项非NT编译，**不宣称全链路零JIT或旧31秒下降全部归因已闭合**。

中位吞吐203.3665tok/s；原镜像208.91仍仅预热参考，尚无正式稳定对照或新独立B/C/R；本组合四场景最终验收未完成。这是op006历史服务状态；fw004验证服务已结束，容器保持运行，prefixOFF。

## 补充优化点与评测记录索引

以下为同目录已有记录；结论范围以各点文档和 `state.yml` 为准。

- [cleanup-001](cleanup-001.md)
- [cleanup-002](cleanup-002.md)
- [cleanup-003](cleanup-003.md)
