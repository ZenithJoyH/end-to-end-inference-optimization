# op-021: real P4K QSA producer fixtures

## Decision

`passed_diagnostic_prerequisite_only`.  Real rows4096 Prefill and Mixed QSA
producer inputs were captured from fixed synthetic requests on an isolated
eager service using PPU0-7/port8031.  Both compact fixtures reproduce the live
producer's `selected` tensor exactly with the restored retained pre-capture
QSA path.  The
capture synchronizes and copies tensors to host, so all capture-run timing is
invalid and no speedup or service candidate is claimed.

The retained service process and configuration on PPU8-15/port8030 were not
restarted or reloaded.  The shared `qsa.py` was temporarily instrumented for
each isolated capture and then exactly restored.  Each successful lifecycle
stopped its exact isolated process and restored
`qsa.py` to SHA-256
`e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`,
verified port8030 health, and released PPU0-7 to 1 MiB / 0% utilization.

## Frozen fixtures

Prefill:

- Root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op021-qsa-producer-prefill-005/op021-p4k-prefill-producer-001`
- Manifest SHA-256:
  `e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd`.
- Verification SHA-256:
  `a823eddde28b1f548a66ed234ac98ed72e4f1378297f53b11841541717e82334`.
- Shape/phase: `rows=actual_rows=4096`, `request_runs=1`,
  `selected=[4096,2051]`, `static_score_columns=1024`.
- Cache: production view `[109617,1600,1,128]`; one reachable page was
  compacted to `[1,1600,1,128]`.
- Raw bytes: `38,256,652`; every file and manifest passed `SHA256SUMS`.

Mixed:

- Root: `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op021-qsa-producer-mixed-001/op021-p4k-mixed-producer-001`
- Manifest SHA-256:
  `4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e`.
- Verification SHA-256:
  `40183d854603724880e3304444716e904290834dea0058e2aa66ad9255763abc`.
- Shape/phase: `rows=actual_rows=4096`, `request_runs=2`,
  `selected=[4096,2051]`, `static_score_columns=1056`.
- Cache: two reachable pages compacted to `[2,1600,1,128]`.
- Raw bytes: `38,666,264`; every file and manifest passed `SHA256SUMS`.

Both verifiers report `integrity=passed`, `producer_replay=passed`, and
`selected_exact_match=true`.  Neither fixture contains prompt text, token IDs,
model weights, main K/V, or business traffic.  It contains synthetic-request
activations and remains only in the user-specified remote case directory.
The capture-time manifest records the temporary instrumented `qsa.py` SHA-256
`8bbe4847d8db234cf3d1eae6d491f770bfad5d9848a074c6358152ebcc74b32a`;
the post-capture producer replay runs only after restoring the retained
pre-capture SHA-256 `e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`.

## ABI correction and bounded acquisition

The live cache width is 1600, not the initial raw estimate 16 or the raw
default-block estimate 4.  vLLM unifies this hybrid Mamba/attention model's KV
page sizes; the QSA kernel then uses `k_cache.shape[1]` as its effective page
size.  The capture therefore freezes compression ratio 4 and page size 1600,
uses the actual runtime score width, and remaps only pages reachable through
the active request rows and exact table prefix.

FlagGems `index_select(dim=0)` was unsuitable because it first materialized
the complete 41.82-GiB cache and OOMed.  The accepted helper copies each
already-bounded one-page narrow view to CPU and concatenates there.  The final
helper SHA-256 is
`cdfd3d2990b6539c14733b06b312f4bf41dc73e2e30b5b42dc94eea31abdf7a3`;
the final arm SHA-256 is
`93e027e8b372f8977bbbc668455eb92c397cf86384e7e98416881274d6afdd64`.

## Failed attempts retained as evidence

- `prefill-001`: readiness incorrectly required a nonempty `/health` body;
  vLLM intentionally returns empty HTTP 200.  Cleanup passed.
- `prefill-002`: rejected an assumed `[blocks,16,1,128]` cache shape.  Cleanup
  passed.
- `prefill-003`: source-derived raw page width 4 did not account for hybrid
  page unification; runtime reported `[109617,1600,1,128]`.  Cleanup passed.
- `prefill-004`: runtime ABI gate passed, but FlagGems `index_select` tried to
  allocate 41.82 GiB and OOMed before fixture creation.  Cleanup passed.
- Three prepare/revert preflights on copies passed before the final live run.

These failed runs produced no promotable fixture or timing result and made no
persistent source/service change.

## Next hard gate

Use the two frozen manifest SHAs as explicit inputs to op-020 rows4096.  Before
any timing, Prefill and Mixed must separately pass fixture integrity,
shape-similarity checks, eager generic/candidate correctness, complete R4
membership reconstruction, and one captured graph replaying A/B/A with
graph-internal phase changes and no external replay-time writes.  Performance
timing remains forbidden until both phase fixtures pass.

Formal acceptance remains blocked by inherited GPQA `170/198 = 85.86% < 88%`.
