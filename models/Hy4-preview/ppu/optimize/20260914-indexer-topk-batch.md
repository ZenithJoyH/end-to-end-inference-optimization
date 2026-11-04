# 20260914-indexer-topk-batch：Indexer 分块 Top-K

- experiment-id：`20260914-indexer-topk-batch`
- 分类：`operator/improve`
- 状态：`retained`
- 目标场景：`P4096/D32/C8/N8`；`P4096/D4/C1/N1` 仅用于 profiling

## Status

`retained at P4K scout milestone; automated comparison metadata incomplete`

## Frozen scope

- Model/platform/host: Hy4-preview / PPU / PPU-07.
- Stage and workload: P4K prefill only; the frozen service workload remains
  `P4096/D32/C8/N8`, with `P4096/D4/C1/N1` used only for bounded profiling.
- Service baseline: `max_num_batched_tokens=2048`, TP16, BF16,
  `FULL_DECODE_ONLY`, prefix caching disabled.
- Primary metric and keep threshold: output-token throughput, at least `+5%`
  versus the frozen P4K baseline under the maintained comparison contract.

## Evidence and hypothesis

The incomplete-but-usable 16-rank trace captured 42 calls per representative
rank to `vllm::hyv4_bf16_sparse_attn_indexer`. Rank 0/1/15 each emitted about
86,000 calls to `aten::index`, `aten::nonzero`, and `aten::index_put_` and about
86,000 device `gatherTopK` launches. The indexer annotation accumulated about
143 seconds on each rank across a roughly 145-second profiled timeline, while
the sparse MLA device kernel accumulated about 1.23 seconds. These inclusive
durations overlap and are not added as critical-path time, but the identical
counts and timeline coverage make the per-row reference Top-K path the first
operator candidate.

Hypothesis: the current prefill fallback performs one Top-K workflow per query
row. Replacing only that fallback with an equivalent batched/fused row-wise
implementation can remove tens of thousands of framework calls and launches
without changing indexer scores, `topk`, sparse-MLA layout, model weights, or
service configuration.

## Gates before an end-to-end candidate

1. Resolve the live model-to-Plugin-to-implementation call chain and capture
   the exact source revision/worktree state.
2. Preserve the reference path and use capability/shape guards rather than
   model name or host identity.
3. Compare exact indices and values, including tie behavior if required by the
   caller, over representative, boundary, and non-aligned shapes.
4. Prove the target implementation is hit; test eager plus graph capture and
   at least two replays where the path is graph eligible.
5. Run the same no-profiler P4K baseline/candidate/revert measurement. Reject
   if output-token throughput improves by less than 5%, correctness fails, or
   the fallback/graph path regresses.

Raw profiling evidence remains under:

`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/profiling/p4k-prefill-capture-01/`

## Existing-provider probe

The first probe attempt did not execute because the PPU SDK setup script reads
an optional positional argument and is incompatible with `set -u`. The service
restore attempt failed for the same reason. The failed result/service
directories were retained; the launcher was corrected to match the existing
successful service scripts and the baseline service was restored in a new
directory with stable identity matching the frozen revert manifest.

The corrected single-device probe then compared the existing Plugin reference
adapter with the current FlagGems provider for one row, FP32 logits, INT32
indices and `top_k=2048`:

| valid length | reference median | FlagGems median | correctness | result |
|---:|---:|---:|---|---|
| 4096 | 0.1251 ms | 0.0780 ms | selected value set exact; indices in range | pass |
| 2048 | 0.1092 ms | 0.0653 ms | selected value set exact; indices in range | pass |
| 1024 | 0.1005 ms | 0.0630 ms | selected value set exact; invalid tail remains `-1` | pass |
| 1 | n/a | n/a | PPU Triton compilation failed in `_top_k_per_row_job` | fail |

The provider reports `HAS_TLE=false`. The length-1 failure proves the current
provider cannot be made the unconditional backend for the live P4K path, whose
first query row has one valid key. The approximately 1.6x–1.7x single-call
improvement also leaves the outer 2048-row Python loop intact, so a guarded
provider-only change is no longer the first candidate. The next falsification
experiment batches adjacent query rows for both score construction and Top-K,
with the current row loop as the correctness oracle.

## Blocked-indexer probe

A single-device prototype reproduced the two C1 P4K prefill chunks with
`q=[2048,32,128]`, BF16 keys/queries/weights, `top_k=2048`, and monotonically
growing causal key ranges. It compared the existing row loop with blocks of
adjacent query rows. Selected index sets were exactly equal for every one of
the 4096 query rows at every tested block size.

| chunk | key range | row reference | block 8 | block 32 | block 128 |
|---|---:|---:|---:|---:|---:|
| first | 1…2048 | 159.40 ms | 41.31 ms (3.86x) | 10.78 ms (14.79x) | 3.82 ms (41.76x) |
| second | 2049…4096 | 203.49 ms | 42.23 ms (4.82x) | 13.76 ms (14.79x) | 6.98 ms (29.17x) |

This microbenchmark excludes request scheduling, KV gather, other layers,
communication and service overhead. It only promotes block size 128 to the
first end-to-end candidate; it does not establish an end-to-end speedup.

### Plugin design ownership

The change belongs to `operator/improve` in the Hy4 model shim. The dispatch
adapter receives already-completed logits for one call and therefore cannot
batch the much larger per-row score construction. The model shim owns the
request-local ranges and sequence boundaries needed to batch adjacent rows
without changing sparse-attention semantics. The candidate will retain the
existing `_select_topk` row implementation as the reference/fallback, use a
bounded constant query block, avoid model-path/host guards, and leave the
shared `top_k_per_row` dispatch and all other models/platforms unchanged.

The first falsification tests are non-zero ranges, multiple request boundaries,
empty/short ranges, exact selected-index sets, and a target-hardware service
smoke. Prefill is outside the current `FULL_DECODE_ONLY` captured region;
decode graph behavior must remain unchanged and will be checked by the same
graph service startup and request guard.

## Candidate implementation and validation

The retained Plugin candidate replaces the per-query-row prefill indexer score
construction and Top-K loop with request-bounded blocks of 128 rows. It keeps
the original single-row implementation as fallback and does not change service
configuration, model weights, tokenizer, decode attention, or shared dispatch
selection. The patch SHA256 is
`97d5d5bb3ede4229ed465635d5352ca582caa696993c492a1ddd07253af6a24e` and the
loaded `hy_v4.py` SHA256 is
`e0f45312dacfb3ea64b3a6c2b77d730145ffeac0599dc3bb179d06b6bb53650e`.

- Python compilation passed and the four targeted Hy4 unit tests passed.
- The candidate service and final retained service each passed the fixed chat
  smoke+C8 guard, 9/9 requests. This is a minimal service regression guard, not
  a formal model-accuracy gate.
- The final service completed `FULL_DECODE_ONLY` graph capture with eager
  disabled. Nine successful multi-token requests after capture generated 521
  completion tokens, providing execution evidence for more than two replays;
  this vLLM/PPU build does not expose a direct replay counter.

The no-profiler P4K scout used frozen `P4096/D32/C8/N8`, one warmup and two
measured rounds. Every measured round completed 8/8 requests, 32,768 input
tokens and 256 output tokens with no failures.

| metric | baseline median | candidate median | revert median | candidate vs baseline |
|---|---:|---:|---:|---:|
| output throughput | 0.331103 tok/s | 6.876431 tok/s | 0.333439 tok/s | 20.768x |
| total-token throughput | 42.7123 tok/s | 887.0596 tok/s | 43.0136 tok/s | 20.768x |
| P99 TTFT | 764,650.1 ms | 31,980.0 ms | 759,244.3 ms | -95.82% |
| P99 TPOT | 21,425.5 ms | 986.0 ms | 21,290.3 ms | -95.40% |
| P99 ITL | 48,217.9 ms | 2,142.2 ms | 48,138.0 ms | -95.56% |

Candidate output-throughput spread was 0.047%; revert spread was 0.872%. The
revert drift from the original baseline was +0.705%, within the frozen 15%
limit. The A/B/R data therefore supports retaining this candidate for the
measured scout workload and exceeds the pre-recorded +5% threshold.

The maintained comparison utility returned `incomplete`, not `failed`, because
the reused comparison JSON still declared the prior experiment's
`max_num_batched_tokens=2048 -> 4096` variable paths. The code candidate had no
launch-argument difference, so it reported
`undeclared changes or no changed variable: []`. Original run records were not
rewritten after measurement. This metadata defect limits the result to a
milestone retention decision rather than formal performance acceptance.

Raw evidence is under
`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/`,
including `results/performance/candidate-indexer-block128-p4k-scout-01`,
`results/performance/revert-indexer-block128-p4k-scout-01`, and
`results/retained-indexer-block128-sanity`. The final retained service manifest
is `manifests/retained-service-indexer-block128.json`.
