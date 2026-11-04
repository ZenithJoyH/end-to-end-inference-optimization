# op-015 QSA sparse GQA group-3 literal-four-lane probe

## Decision

`stopped_before_service_implementation` / `no_go_production_rows4096_regression`.

The candidate is correct and graph-safe, but it fails the pre-frozen production-shape
performance gate. No FlagGems or service source was modified.

## Hypothesis and contract

- Live path: Plugin QSA dispatch to
  `flag_gems.fused.qsa._qsa_sparse_paged_gqa_kernel`.
- Live contract: BF16 query `[rows, 3, 256]`, BF16 K/V
  `[blocks, 16, 1, 256]`, int32 logical indices `[rows, 2051]`, one KV head.
- Current wrapper: `GROUP_SIZE=3` is promoted to `BLOCK_M=16`.
- Candidate: a standalone Triton kernel using literal `tl.arange(0, 4)` with lane
  3 masked; `BLOCK_M` is absent from the candidate signature.
- Gate: exact/within-BF16-tolerance output, invalid request output exactly zero,
  graph capture plus two identical replays, and both eager and graph median gain
  `>=8%` for valid `rows=4096`.

## Evidence

- Smoke:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op015-qsa-sparse-group3-literal4-smoke-001/result.json`
- Full result:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op015-qsa-sparse-group3-literal4-001/result.json`
- Full result SHA-256:
  `01b45cef75c2bc81bf26a8166e23d82f20e4d77d6155712e6f5634bfb7f92709`
- Script SHA-256:
  `a8044c561928297ca3a9c90bfe94f90caa7a6addfb050864ddb69b637524e255`
- Device isolation: released PPU0 only; retained service50 stayed unchanged on
  PPU8-15 and port 8030.

Five timing samples were collected after five warmups; each sample averaged 20
transactions. The candidate matched the current generic kernel exactly for the
tested outputs, passed sampled FP32 reference checks, covered valid and
invalid/non-contiguous-page inputs, and passed graph capture plus two replays.

| Rows | Mode | Eager gain | Graph gain | Decision |
|---:|---|---:|---:|---|
| 1 | valid | +5.988% | +5.439% | diagnostic only |
| 1 | invalid/non-contiguous | +6.981% | +6.558% | diagnostic only |
| 64 | valid | +21.305% | +21.659% | small-shape positive |
| 64 | invalid/non-contiguous | +20.859% | +21.474% | small-shape positive |
| 4096 | valid | **-4.549%** | **-4.563%** | stop condition triggered |
| 4096 | invalid/non-contiguous | -3.866% | -3.798% | confirms large-shape regression |

For valid rows4096, the current graph median was `9.494234 ms` and the literal-four
candidate was `9.948200 ms`. The large-shape regression agrees with the earlier
parameterized BLOCK_M4 warning and outweighs the rows64 improvement for the current
P4K Mixed target.

## Boundary and rollback

This is operator microbenchmark evidence, not end-to-end performance evidence. It
does not establish that all future QSA optimization is unprofitable; it falsifies
the specific strategy of reducing the logical query-head tile from 16 to literal
4 while preserving the existing online-softmax/dot organization.

No runtime source delta was applied, so rollback is not required. The retained
service identity and Plugin/common-slot hashes remain unchanged. Formal acceptance
is still blocked by inherited GPQA `170/198 = 85.86%`, below the frozen 88% gate.

## Next direction

Proceed to a no-profiler TP8 collective causal probe using the live message-size
sequence and only already-supported collective paths. Require bit-exact output,
graph capture plus two replays, no rank outlier, `>=8%` weighted transaction gain,
and a credible `>=1%` P4K Mixed contribution before service integration.
