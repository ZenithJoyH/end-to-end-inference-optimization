# op-012: M64 GEMM1 + SiLU fusion

- Direction: `operator/improve`; replace the retained GEMM1 BF16 store,
  separate `silu_and_mul`, and second BF16 store with FlagGems
  `FUSE_SILU=True` while leaving alignment, GEMM2, routing, and `moe_sum`
  unchanged.
- Scope: isolated PPU0, exact retained M64 BF16 shapes and configs, complete
  GEMM1 + activation + GEMM2 + reduction transaction.
- Correctness: the frozen BF16 allclose contract passed at every checked
  boundary; final max absolute error was `3.092e-7`, relative L2 was
  `0.004517`, and cosine similarity was `0.9999898`. Both variants captured
  and replayed graphs twice with per-variant eager/replay bitwise stability.
- Performance: median complete transaction regressed from `0.578570ms` to
  `0.620141ms` (`0.932966x`, `-7.185%` improvement). GEMM1+activation caused
  the regression; GEMM2+reduction stayed unchanged.
- Decision: rejected before service integration. Do not try
  `PAIR_GATE_UP_DOT` or adjacent fusion/tile/stage/warp scans under this
  mechanism.
- Evidence:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op012-m64-gemm1-silu-fusion-001/result.json`
  (SHA-256
  `bfac4e8a84540576bdf22378f284c81446e852ff5330e087d9ce0241615b7bfd`).
- Rollback: no source patch was applied and no service used this candidate.
