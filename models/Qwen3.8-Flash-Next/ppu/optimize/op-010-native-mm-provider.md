# op-010: platform-native `mm/mm_out` provider

- Direction: `operator/replace`; exclude Python function names `mm` and
  `mm_out` from FlagGems so the T-Head platform-native implementation handles
  the service's `aten::mm`/`aten::mm.out` calls.
- Dependencies: retained maxseq64/batched4096, exact M64 BM16 MoE config, and
  op008 runtime QSA bound capped at 8448.
- P4096/D128 evidence: correctly bound same-container baseline/candidate/revert
  comparison passed at +3.188% output throughput; all P99 TTFT/TPOT/ITL/E2E
  guards improved. Comparison SHA-256
  `dd7bcb48837797d96e914afa6f9929b0119bb339886e9ba540187a5cadb2d2db`.
- P4096/D1024 checkpoint: candidate versus the earlier exact-workload op008
  reference improved output and total-token throughput 2.849%, duration 2.770%,
  and every median/P99 latency metric; three measured rounds had 0.711% output
  spread. Screen SHA-256
  `2b783f6acc629accd3cbace3e0e2ade3f6cdf1f0c936a67372d751a570247e36`.
- Correctness/path: full graph capture and two replays passed; runtime enabled-op
  evidence proved that `mm_out`, not ATen schema spelling `mm.out`, is the
  effective FlagGems exclusion key.
- Exact P4096/D1024 A/B/R: maintained comparator `passed` with no issues;
  output/total throughput improved 3.4168% and P99 TTFT/TPOT/ITL/E2E improved
  3.2163%/3.4655%/2.9641%/3.3005%. Comparator SHA-256 is
  `dac9c81c3537e3eb45a8a4fab33182274e01017d36b15e4f969c1d4f6979a6e4`.
- Current decision: retained performance-only. Service48 is the restored native
  provider state and passed readiness, full graph capture, and canonical
  replay.
- Rollback: restore blacklist `_conv_depthwise2d,index,normal_` in the exact
  candidate container, preserving op008 and the M64 tuned config.
- Formal boundary: inherited GPQA remains 170/198 (85.86%), below the frozen
  88% gate; no formal acceptance claim is made.
