# op-021: real P4K QSA producer fixture capture

## Purpose and boundary

op-020 passed its synthetic rows64 single-graph A/B/A gate, but rows4096 must
use a real producer input.  op-021 is a diagnostic-only acquisition step.  It
captures exactly one rank0 `qsa_select_paged_tokens` call from a synthetic P4K
request served by an isolated `--enforce-eager` service on PPU0-7.  It does not
time a candidate, alter the retained port-8030 service, or authorize op-020
performance timing.

The fixture contains raw `index_q`, a compacted compressed-K cache, a densely
remapped compressed page table, `token_to_req`, `query_positions`,
`sequence_lengths`, and the producer's exact `selected`.  It contains no prompt
text, token ids, model weights, main K/V, or business request.  Raw tensors live
only below the user-specified case root on PPU-01 and are never copied into this
repository.

## Bounded page compaction

The production compressed-cache ABI observed on the isolated service is BF16
`[109617,1600,1,128]`.  The width 1600 is not the raw 16-token CacheConfig
default divided by compression ratio 4: vLLM first unifies the hybrid
Mamba/attention page sizes, and the QSA backend then exposes that enlarged
compressed storage page directly to the kernel.  The service log records this
page-unification path, and the live QSA kernel uses `k_cache.shape[1]` for both
logical-page division and page offset.  The one-shot arm therefore freezes
compression ratio 4 and effective kernel page width 1600.  The helper does not
copy the 109617-page cache or stale/unreachable pages.  For active request ids
it examines only the page-table prefix required by the **actual
`static_score_columns` argument received by this call** (rounded up by the
1600-row effective page size), takes the sorted unique nonnegative physical
page ids, gathers those K pages, and rewrites their ids densely.  It does not
assume the retained 8448 cap: an eager P4K caller may pass a tighter safe bound,
and that captured value becomes part of the fixture ABI.  The compact table
preserves original request ids and is `-1` everywhere else.

This is replay-equivalent because QSA dereferences K only through that table,
and the score-width prefix is unchanged.  Hard checks reject out-of-range page
ids, more than 1250 referenced pages, a non-BF16/non-production shape, a byte
total over 64 MiB, or an output other than `[4096,2051]`.  The selected tensor
is about 33.6 MiB and dominates the bounded fixture; each reachable cache page
adds about 0.39 MiB.  The exact total is recorded from the captured page set
instead of multiplying by the full allocator capacity.

The gather is intentionally page-wise: each selected one-page narrow view is
copied to host immediately and the compact cache is concatenated on CPU.  The
active FlagGems `index_select(dim=0)` path first materializes the entire
roughly 41.8-GiB source cache, so it is prohibited for this bounded diagnostic
even when only one page is requested.

## One-shot protocol

1. Copy the helper, arm, prepare, request, revert and verifier files under
   `<case-root>/commands/op021/`, then invoke the single entry point
   `lifecycle-op021-qsa-producer-fixture.sh` with phase, unique run id, exact
   unpatched qsa.py SHA and its container path.  The lifecycle registers its
   cleanup trap **before** creating the arm or changing shared source.
2. The lifecycle creates a fresh single-use arm/output directory, then runs
   `prepare-op021-qsa-producer-fixture.py`.  The preparer writes a durable exact
   rollback manifest before either live path changes and refuses unknown
   source, non-unique anchors, an existing helper or artifact directory.  Its
   revert accepts only the four exact before/patched and helper-present/absent
   intermediate states, so interruption between atomic replacements is safe.
3. Before launch the lifecycle requires PPU0-7 to have no
   vLLM/worker process assignment, port 8031 to be unused, port 8030 to be
   healthy, and the optimization container/image identity to match the
   recorded case.  It launches only the isolated eager service with the
   existing op-010/op-008/M64-BM16 environment plus:

   ```text
   VLLM_FL_QSA_PRODUCER_CAPTURE=1
   VLLM_FL_QSA_PRODUCER_RANK=0
   VLLM_FL_QSA_PRODUCER_ARM_FILE=<fresh-output>/arm.json
   VLLM_FL_QSA_PRODUCER_OUTPUT_DIR=<fresh-output>
   VLLM_FL_QSA_PRODUCER_CASE_ROOT=/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e
   ```

4. Record the exact service root PID/start ticks/argv, then invoke
   `run-op021-qsa-producer-fixture-capture.sh`.  It uses only vLLM's seeded
   random dataset and deliberately omits detailed request persistence.  The
   helper atomically renames the arm to a rank/PID claim before any capture;
   only the first eligible rows4096 call can write a fresh temporary directory,
   which is atomically renamed after all raw files, manifest and SHA256SUMS are
   durable.
5. Stop only that recorded service root after rechecking PID/start ticks/argv.
   If startup fails before the identity file is written, cleanup performs a
   read-only scan and records the unique `serve --port 8031 --enforce-eager`
   process before stopping it.  Zero matches is already stopped; multiple
   matches are a hard error and are never blindly killed.
   Wait for port 8031 to close and for PPU0-7 processes to disappear.  Verify
   port 8030 health again.  Save before/ready/after PPU snapshots and the exact
   service identity under the case root.  The lifecycle script owns this
   guarded launch/request/stop sequence and writes evidence into a unique
   transition directory.
6. Run `revert-op021-qsa-producer-fixture.sh`.  It restores only if qsa.py and
   the helper still equal their patched SHAs, then requires the restored SHA to
   equal the original.  The lifecycle script's cleanup trap performs steps 5--6
   on every exit; no wildcard kill, source reset, or directory cleanup is
   allowed.  After stop/revert the lifecycle performs integrity plus real
   producer replay on PPU0, then its final receipt rechecks port-8030 health,
   original qsa.py SHA and PPU0-7 release.

Prefill and Mixed require separate isolated-service runs and fresh output dirs;
"one-shot" means one capture per arm, not combining two phases into one mutable
artifact.

## Verification and op-020 handoff

First run `verify-op021-qsa-producer-fixture.py --integrity-only` to check every
size/SHA/shape, dense-table bounds, page-id ordering, byte total and metadata.
Then run it inside the same image/revision with PPU0 free and without a service;
the verifier loads raw tensors, calls the real retained
`qsa_select_paged_tokens` with the manifest's captured
`static_score_columns`, and requires an exact
cell-for-cell selected match.  This is the proof that page slicing/remapping is
lossless.  Record verifier, qsa.py, helper, arm, patch manifest and fixture
manifest SHAs.

Only after replay passes may op-020 consume the fixture.  op-020 still must run
rows4096 Prefill/Mixed eager correctness, op-019 shape-similarity windows, full
membership reconstruction, and single-graph A/B/A before any timing.  Capture
client latency is invalid because the helper synchronizes and performs large
D2H writes.  No source/service/performance claim follows from op-021 alone.
