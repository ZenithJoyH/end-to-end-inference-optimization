# op012: M64 GEMM1 + SiLU fusion sentinel

Status: `stopped_gate` / rejected. The experiment used only PPU0 in the
baseline container and did not modify source or start a service.

## Scope and implementation

- Container: `qwen3.8-flash-opt-20260919`
- Container ID:
  `2eafbddebde1b14c691173de29d1965bc48064829a86ee4150056ef1fc5297f7`
- Device: physical PPU0 through `CUDA_VISIBLE_DEVICES=0`
- FlagGems revision:
  `2b1e5cfdbd22d453933b2c6589a29daf31315ccd`
- Kernel:
  `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py:fused_moe_kernel`
- Exact BF16 shapes: hidden `[64,2560]`, W1 `[512,160,2560]`, W2
  `[512,2560,80]`, E512, top-k 10.
- Shared config: BM16, BN64, BK128, GROUP1, four warps, three stages.
- Shared downstream path: GEMM2 followed by `moe_sum`.
- Single variable: current GEMM1 plus separate `silu_and_mul` versus GEMM1
  with `FUSE_SILU=True`. `PAIR_GATE_UP_DOT` remained false.

The current Plugin baseline has two BF16 stores/rounding boundaries around the
activation: GEMM1 accumulates in FP32 and stores BF16 gate/up, then the
pointwise kernel converts gate to FP32, evaluates SiLU, and stores activated
BF16. The FlagGems fusion branch evaluates SiLU from the FP32 GEMM accumulators
and performs only the final activated BF16 store. Candidate-versus-baseline
bitwise equality was therefore not required; the frozen contract required
finite BF16 values and elementwise `allclose(atol=0.02, rtol=0.02)` at the
activated, routed GEMM2, and final reduced outputs.

## Correctness and graph result

All numerical and graph gates passed:

| tensor | max abs | relative L2 | cosine | bitwise-equal fraction |
|---|---:|---:|---:|---:|
| activated BF16 | 7.629e-06 | 0.003260 | 0.9999948 | 0.65258 |
| routed GEMM2 BF16 | 2.384e-07 | 0.003917 | 0.9999923 | 0.41943 |
| reduced final BF16 | 3.092e-07 | 0.004517 | 0.9999898 | 0.37003 |

Baseline and fusion each captured successfully and replayed twice. Captured
and replayed output was bitwise equal to its own eager reference, and the two
replays were bitwise stable.

## Performance result

Measurement used 20 warmups, 100 timed iterations, and three alternating
rounds. Values below are medians.

| transaction | baseline | fused | conclusion |
|---|---:|---:|---|
| GEMM1 + activation | 0.193026 ms | 0.234435 ms | fused 21.46% slower |
| GEMM2 + sum | 0.385648 ms | 0.385778 ms | effectively unchanged |
| complete transaction | 0.578570 ms | 0.620141 ms | fused 7.19% slower |

Complete-transaction speedup was `0.932966x`, below the frozen `1.08x`
promotion threshold and in the wrong direction. Run-to-run CV was below 0.14%
for all stage measurements and below 0.06% for both complete transactions.

Although the fusion reduces the expected GEMM1 grid from 1560 to 1040 and
removes one launch/intermediate store, the current non-paired fusion kernel
executes gate and up projections sequentially in one program. On this exact
PPU M64 shape, that implementation cost dominates the saved work. This is an
experimental observation; no hardware-counter claim is made.

## Stop conclusion

Reject this FlagGems `FUSE_SILU=True`, `PAIR_GATE_UP_DOT=False` path for the
current M64 candidate. Do not integrate it into the Plugin or service. Per the
pre-frozen rule, do not continue with `PAIR_GATE_UP_DOT`, tile, stage, warp, or
other fusion variants under op012; each would be a new multi-variable/kernel
hypothesis.

PPU0 returned to 9 MiB and 0% utilization after the process exited. The
baseline container still had no `vllm serve` process, and the post-run source
status matched the pre-run status.

## Artifacts

Remote root:

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op012-m64-gemm1-silu-fusion-001`

Key SHA-256 values:

- `benchmark.py`:
  `026601ba4695ff0468dd730ec91242024c16b8206816f3319ff97ab2fa344bd5`
- `result.json`:
  `bfac4e8a84540576bdf22378f284c81446e852ff5330e087d9ce0241615b7bfd`
- `console.log`:
  `ac30b59540b752847612ebe990a3da906f06c6c1c4f74b52a3d144deb008ba06`
- `status.txt`:
  `e4bcb46f2eb0b4b96f70e909e085558df1dee918f40a5fc55f4cf9e6dc8cc3c8`

Local reproducibility files:

- `op012-m64-gemm1-silu-fusion-microbench.py`
- `run-op012-m64-gemm1-silu-fusion.sh`

Knowledge delta: for Qwen3.8-Flash-Next BF16, PPU, exact M64/E512/top-k10 and
the retained BM16 config, the already-present non-paired FlagGems GEMM1+SiLU
fusion is numerically compatible and graph-safe, but is decisively slower than
the current separate GEMM1 and activation path.
