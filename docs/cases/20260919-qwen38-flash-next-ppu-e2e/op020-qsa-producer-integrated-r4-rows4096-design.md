# op-020 rows4096 real-producer consumer correctness gate

## Scope

This is the correctness-only bridge from the two verified op021 P4K producer
fixtures to the op019 R4 direct-membership consumer prototype. Prefill and
Mixed are separate runs and separate results. The gate does not time kernels,
patch source, restart a service, or authorize promotion.

Frozen fixtures:

- Prefill:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op021-qsa-producer-prefill-005/op021-p4k-prefill-producer-001`,
  manifest SHA-256
  `e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd`.
  It has rows/actual_rows 4096, one request run, producer page size 1600,
  static score width 1024 and one compact K page.
- Mixed:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op021-qsa-producer-mixed-001/op021-p4k-mixed-producer-001`,
  manifest SHA-256
  `4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e`.
  It has rows/actual_rows 4096, two request runs, producer page size 1600,
  static score width 1056 and two compact K pages.

The script validates the manifest SHA, schema fields, all raw file SHA/size,
the exact SHA256SUMS coverage, dtype/shape, compact table bounds, active request
runs, `[4096,2051]` selected output and the 1600-wide producer cache ABI. It
then requires real producer replay A to equal the captured selected tensor
cell-for-cell.

## Consumer boundary

The producer fixture does not include main-attention K/V. The consumer check
therefore uses deterministic BF16 synthetic main Q/K/V and the already audited
op019 standalone ABI: main K/V pages are 16 tokens and cover the complete
8192-token direct-address domain. This 16-token page is not presented as the
production producer page; the result records both values explicitly.

Original request ids are retained for producer replay. For the consumer only,
contiguous request runs are remapped to `[0, request_runs)` and
`query_start_loc` is derived from exact row boundaries. This satisfies the
op019 group-id proof without changing row order, positions, selected values or
request segmentation.

For eager A and B the gate compares current generic sparse output with the R4
candidate at `atol=rtol=0.05`, checks sampled FP32 attention, asserts every
row/head writer, and reconstructs the entire int32 membership tensor,
group-base map and overflow vector on CPU. Duplicate selected entries or a
selected token outside the 8192 domain stop the experiment.

## Shape-similarity gate

Only real fixture A is used for representativeness. R4 `rho` must remain within
3 percentage points of op019 and union max/p99/p90/p50 must each remain within
5 percent:

| phase | rho | max | p99 | p90 | p50 |
|---|---:|---:|---:|---:|---:|
| Prefill | 0.695122 | 3460 | 3292 | 3036 | 2052 |
| Mixed | 0.694798 | 3400 | 3292 | 3056 | 2048 |

A failure is a fixture-shape blocker, not a performance result.

## Single-graph dynamic proof

Exactly one graph contains:

```text
internal phase_used copy + phase flip
  -> stage real A or sign-inverted real-query B
  -> real qsa_select_paged_tokens
  -> current generic sparse consumer
  -> op019 clear + full membership build + R4 consumer/fallback
```

The rows64 calibration proved that this PPU records capture without executing
the transaction. The script therefore seeds phase A before capture and requires
capture to leave phase A unchanged. It then performs three consecutive replays
without any phase or tensor write between them. The graph-internal phase kernel
must produce A/B/A. Each replay is compared with its eager oracle; A1 and A2
must be bit-exact for selected, complete membership/metadata and both outputs.

The B query is the sign inversion of the captured real query. It preserves the
captured magnitude/layout while providing a deterministic dynamic producer
control. At least 25 percent of selected rows, eight membership groups and the
generic output must change from A.

## Run and stopping rules

After uploading the script and runner under the case command directories, run
Prefill and Mixed independently:

```bash
run-op020-qsa-producer-integrated-r4-rows4096.sh \
  prefill <script-sha256> <op019-script-sha256>
run-op020-qsa-producer-integrated-r4-rows4096.sh \
  mixed <script-sha256> <op019-script-sha256>
```

Any integrity, producer-exactness, shape-similarity, eager, FP32, full
membership, capture or A/B/A failure stops before timing. Even if both runs
pass, they only authorize designing a separate full-transaction timing
experiment. Formal acceptance remains blocked by inherited GPQA
`170/198 = 85.86% < 88%`.
