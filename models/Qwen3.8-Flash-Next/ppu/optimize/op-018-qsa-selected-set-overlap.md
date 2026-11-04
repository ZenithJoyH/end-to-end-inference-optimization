# op-018: P4K QSA selected-set overlap telemetry

## Contract

- Classification: `operator/improve`, bounded diagnostic only.
- Status: `complete`; the 12% design gate passed, and no source delta is retained.
- Service isolation: retain service50 on PPU8-15/8030 unchanged; use only PPU0-7 and
  port 8031 in the existing isolated optimization container.
- Workloads: P4096/D1/C1/N1 Prefill and P4096/D128/C2/N2 Mixed.  The latter is
  valid only when the instrumented QSA call contains at least two request runs.
- Metric: for an eligible same-request consecutive-row group, `a` is the sum of
  per-row expanded selected-set cardinalities and `u` is the union cardinality.
  `rho_R=sum(a-u)/sum_all_eligible_rows_cardinality`, with incomplete tails kept
  in the denominator and assigned zero saving.
- Decision gate: the same `R` in `2,4,8,16` must have `rho_R >= 0.12` in both
  Prefill and Mixed before a union/mask kernel microbenchmark may be designed.
- Timing boundary: telemetry synchronizes rank0 and sorts diagnostic tensors.
  Client latency and throughput are invalid and must never be used as a gain.

## Correctness and lifecycle gates

The patch is guarded by the exact current `qsa.py` SHA-256
`e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`.
It observes the final expanded `[rows,2051]` selected-token tensor without
mutating it, keeps large tensors on device, and copies only 18 integer counters
to the host.  Telemetry is eager-only and fails closed during graph capture.

Before each armed sample, one deterministic unarmed completion is saved.  After
the one-shot artifact is written, the same completion is repeated and its
normalized response is compared.  Each diagnostic service is stopped using
PID, start ticks, and exact argv.  Finally the source backup is restored, the
helper is removed, the original SHA is rechecked, PPU0-7 must be free, and
service50 must remain healthy.

## Result

Both samples were valid and the same `R` passed the frozen gate in Prefill and
Mixed.  Mixed contained exactly two request runs, rather than a relabeled pure
Prefill call.  The before/after deterministic short completion records were
identical for each valid service instance.

| R | Prefill rho | Prefill coverage | Mixed rho | Mixed coverage | Decision |
|---:|---:|---:|---:|---:|---|
| 2 | 44.0555% | 100.0000% | 44.0526% | 99.9349% | pass |
| 4 | 69.5122% | 100.0000% | 69.4798% | 99.8697% | pass |
| 8 | 83.8933% | 100.0000% | 83.7094% | 99.7395% | pass |
| 16 | 91.7276% | 100.0000% | 91.2856% | 99.4791% | pass |

This is a K/V-read reuse upper bound, not a kernel speedup.  Union generation,
membership masking, row-specific softmax state, layout, and graph costs remain
unmeasured.  The result authorizes only a complete-transaction standalone
microbenchmark, whose frozen gate remains at least 8% on production rows4096.

## Evidence

- Source/patch manifest:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/patches/op018-qsa-overlap-telemetry-001/patch-manifest.json`
- Prefill artifact:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op018-qsa-overlap-prefill-003/op018-p4k-prefill-001.rank0.json`,
  SHA-256 `95ffc65c56cf554afff9c1d52ebb31fa396ade4f72e728d8857424c064a1d017`.
- Mixed artifact:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op018-qsa-overlap-mixed-001/op018-p4k-mixed-001.rank0.json`,
  SHA-256 `43a0564b644f28f6525c4fdb09b12c91ea9ced70dda3ccc1798a717a1c002886`.
- Summary:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op018-qsa-overlap-summary-001.json`,
  SHA-256 `fa68ef87513d228ee6db2456ad211baca492da2e1c516c85dd6a7b25e259958c`.

Two invalid attempts are retained rather than overwritten:

- `op018-qsa-overlap-prefill-001`: Host lacked the `vllm` CLI; no request was sent.
- `op018-qsa-overlap-prefill-002`: client used the model path instead of the
  served model name and received HTTP 404; the request failed before telemetry.

The third Prefill attempt corrected both harness issues.  After the Mixed sample,
the diagnostic service was identity-stopped, PPU0-7 returned to 1 MiB/0%, the
helper was removed, `qsa.py` returned exactly to
`e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`,
and retained service50 on 8030 remained healthy.

The full insertion, eligibility, artifact, and stop rules are frozen in
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op018-qsa-selected-set-overlap-plan.md`.
