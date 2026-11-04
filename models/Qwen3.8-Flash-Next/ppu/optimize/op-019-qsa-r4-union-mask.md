# op-019: QSA R4 union/mask complete-transaction microbenchmark

## Frozen scope

- Classification: `operator/improve`.
- Status: `stopped before performance timing: rows4096 eager changed-input
  precondition invalid, so the graph dynamic-input gate was not reached`.
- Primary candidate: group four consecutive eligible rows from one request,
  build their exact selected-token union and per-row membership on device, then
  share each K/V load across 12 independent query-head softmax states.
- Baseline: current `qsa_sparse_paged_attention` on the exact same real selected
  fixture and synthetic BF16 Q/K/V.
- Performance gate: both Prefill and Mixed rows4096 valid fixtures must improve
  the complete `union/mask build + workspace clear + grouped sparse + fallback`
  transaction by at least 8% in eager and graph modes.  Kernel-only timing is
  diagnostic and cannot promote a candidate.

R4 is selected before implementation because op018 measured about 69.5% K/V
occurrence reuse in both phases, while 4 rows x 3 heads = 12 logical lanes still
fit the current physical `BLOCK_M=16`.  R2 would occupy the same BM16 with only
44% reuse and a larger minimum metadata transaction.  R8/R16 increase physical
M tiles, accumulator pressure, workspace, and compilation risk, so they are out
of this bounded experiment.

## Fixture prerequisite

The op018 counter summary cannot reconstruct membership or union capacity.
Before writing or timing a candidate, capture exact rank0 Prefill and Mixed
expanded selected tensors `[4096,2051]` plus request/position/length metadata in
raw little-endian files.  The fixture must:

1. reproduce every op018 R counter exactly;
2. prove per-row nonnegative selected entries have no duplicates, or preserve
   multiplicity in the candidate;
3. report per-group union max/percentiles and whether the last row is a union
   leader/subset superset;
4. remain diagnostic-only, use an isolated eager service, and be exactly
   reverted before microbenchmark execution.

The capture contains logical indices and scheduling metadata only; it excludes
prompt text, input token IDs, model weights, and K/V contents.  Raw fixtures
remain in the remote case artifact directory and are not committed.

The prerequisite is now complete. Both fixtures reproduce every op018 overlap
counter for R2/R4/R8/R16 exactly, and every valid selected row has zero
duplicate nonnegative entries. The exact artifact identities are:

- Prefill:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op019-qsa-exact-prefill-001/op019-p4k-prefill-fixture-001`,
  manifest SHA-256
  `480def84c7d2c17cb86fac9e2e340caa28806f89cd3bfe05ca7885e0378daf64`.
- Mixed:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op019-qsa-exact-mixed-001/op019-p4k-mixed-fixture-001`,
  manifest SHA-256
  `07fb120403a6af733417feb9db48af7fca8d0869b2ec18cbb1e9698c70455dd6`.

For R4, Prefill union sizes have max/p99/p90/p50
`3460/3292/3036/2052`; Mixed has `3400/3292/3056/2048`. The existing 8192
direct-address domain therefore has capacity with margin. Last-row leader
coverage is only about 82% in both phases, below the frozen 90% shortcut gate,
so the candidate must construct the exact union and cannot use a leader-only
approximation. Mixed covers 4088 of 4096 rows as full same-request groups; the
four-row tail/rejected path remains part of complete transaction timing.

The temporary capture patch was exactly reverted: `qsa.py` returned to
SHA-256 `e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`,
the helper was removed, PPU0-7 were released, and retained service50 remained
healthy. These results authorize only the standalone microbenchmark, not a
service or source integration.

## Correctness and graph gates

- Same-request, segment-aligned, consecutive logical positions only; tails and
  rejected groups use the current row path.
- Generic oracle plus sampled independent FP32 attention reference, with
  `atol=rtol=0.05`; invalid request outputs are exact zero.
- Valid and invalid/non-contiguous page modes, Prefill and Mixed fixtures,
  rows64 guard and rows4096 primary shape.
- Candidate graph includes builder, clear, grouped attention, and fallback;
  it must capture and replay A/B/A selected inputs to prove membership is
  recomputed, not cached.
- No host tensor-value read, dynamic allocation, or capture-time synchronization.

Detailed schema and fixture selection are frozen in
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op019-qsa-row-group-union-mask-microbench-design.md`;
the transaction model is in
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op018-qsa-union-mask-cost-model.md`.

## Standalone outcome

The R4 prototype compiled on PPU. In the final smoke, the initial rows4096
candidate-versus-generic, sampled FP32 reference, exact fixture structure,
request-bound, duplicate/overflow fallback, and complete device
`group_id -> base_row` bijection assertions did not fire before the later
eager changed-input precheck failed. Because that run exited without a
structured `result.json`, these are retained as passed preconditions rather
than a completed full correctness suite. An attempted debug
`tl.atomic_add` write counter produced false vector counts on this backend; it
was removed from the algorithm and replaced with the complete group-map proof
plus a coverage marker.

The final smoke stopped before graph validation. Its eager changed-input
precheck proved `selected_A != selected_B`, but the following rows4096 generic
outputs were identical, so it could not establish a trustworthy dynamic-input
control and did not enter the graph gate. Earlier standalone attempts using a
same-buffer copy, an in-place Triton transform, and a second rows4096 input
pointer were likewise inconclusive; they do not prove a specific PPU cache
bug. Setting every selected entry to `-1` did produce all-zero output. A
separate rows1/TOPK1 control using independent tensors proved only that the
current generic kernel consumes positive index values at that small shape:
token 0 output was exactly V0, token 2049 output was exactly V2049, the two
outputs differed, and `-1` produced exact zero. It does not validate rows4096
dynamic replacement or graph replay. Its result is:

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op019-qsa-positive-index-value-probe-001/result.json`

with SHA-256
`68430bd253bd91ee648de9ad6f36425d57eb3f2c5f45c6990b4105fdff69de61`.
The final stopped smoke is under
`microbench/op019-qsa-r4-direct-membership-smoke-20260920T165455Z-1947604`;
earlier compile and diagnostic attempts remain preserved rather than hidden.

Because the standalone harness could not establish the rows4096 eager
changed-input precondition, the graph gate was not reached. No eager or graph
performance number is promoted, the full suite was not run, and no
FlagGems/service integration was allowed. A future reopen should include the
real selected producer inside one captured transaction, or an equivalent
PPU-validated single-graph dynamic-input mechanism, and persist producer
selected, complete membership, generic output, and candidate output for the
same-graph A/B/A proof; it cannot weaken the gate to static replay or two
independent captures.

Cleanup passed at 2026-09-21 00:56 +08:00: PPU0-7 were at 1 MiB/0%, service50
on PPU8-15 returned healthy, and the live `qsa.py` SHA-256 remained
`e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`.
This proves that op-019 introduced no persistent source/service change; the
FlagGems workspace itself still contains the previously retained QSA diff and
is not globally clean.
