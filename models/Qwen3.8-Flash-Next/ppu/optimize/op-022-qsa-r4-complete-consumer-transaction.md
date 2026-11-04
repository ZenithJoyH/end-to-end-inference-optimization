# op-022: QSA R4 complete consumer transaction timing

## Direction and boundary

- Classification: `operator/improve`.
- Status: `no_go_prefill_complete_transaction_regression`.
- Parent scenario: P4K Prefill/Mixed operator milestone for
  `p4096-d1024-c64-n128`.
- Baseline: currently imported FlagGems
  `qsa_sparse_paged_attention` consumer.
- Candidate: boundary-fixed R4 output clear, workspace clear, direct-address
  membership build, grouped attention, and per-row fallback. The complete
  candidate transaction must stay inside every timed invocation.
- Candidate prototype SHA-256:
  `7a2dd94e2918a2cf88be803235a62d9362d9a71bb6da13a49cc9d0dd7fc36acc`.

This is a standalone consumer-only operator microbenchmark. The immutable
selected tensors come from the verified op021 real-P4K producer fixtures, but
producer execution is common and is not timed here. Main-attention Q/K/V is
deterministic synthetic BF16 data. A passing result can authorize an isolated
service milestone only; it is not end-to-end performance, accumulated service
gain, or formal acceptance.

## Frozen inputs

- Prefill manifest SHA-256:
  `e9765fa23ae19d487c9c7773c3f0b5ea65e5870012eb6ab4cacf7be9efcaeabd`.
- Mixed manifest SHA-256:
  `4d066545ab78ea30d340ce9a76db0325dfd4acee15b14c46fd719790779a037e`.
- Shape: query `[4096,3,256]`, logical selected `[4096,2051]`, BF16
  main K/V `[512,16,1,256]`, token domain 8192.
- Prefill has one request run, 1024 full R4 groups, no fallback and
  `rho=0.695121889`.
- Mixed has request lengths `[1,4095]`, 1023 full R4 groups, four fallback
  rows and `rho=0.694797948`.

## Correctness and graph gate

Before timing each phase independently:

1. Verify the fixture manifest and every raw file, the timing script,
   correctness harness, fixed prototype, live imported baseline source, PPU0
   isolation, retained 8030 health, and live installed `qsa.py` identity.
2. Require selected SHA to remain unchanged; compare generic and candidate at
   `atol=rtol=0.05`, check sampled FP32 attention, reconstruct complete
   membership/group-base/overflow on CPU, and prove every row/head writer.
3. Capture a static generic graph and a static complete-candidate graph.
   Replay each at least three times without external input updates; each arm
   must match its eager oracle and be bit-exact across same-arm replays.
4. Repeat correctness and immutable-input checks after timing.

Any correctness, graph, integrity, isolation, OOM, device, or hang failure
stops the experiment and cannot be converted into a performance result.

## Frozen timing contract

- Prefill and Mixed run in separate fresh processes on released PPU0.
- Eager and graph are measured separately.
- Each mode performs five untimed warmups.
- One event interval contains five complete invocations of one arm.
- Collect at least seven paired samples; even samples use
  baseline-to-candidate order and odd samples reverse the order.
- Preserve every raw observation. If either arm has `MAD/median > 3%` after
  seven samples, extend both arms to eleven samples. If either remains above
  3%, mark that mode invalid and do not promote.
- Report raw milliseconds, order, per-pair and median gains, median, p25, p75,
  MAD, MAD/median, min, max, repeat and sample count.
- Gain is `(baseline_median / candidate_median - 1) * 100`.

Prefill eager, Prefill graph, Mixed eager, and Mixed graph must each be valid
and at least 8% faster. The minimum of the four gains is the promotion value;
no averaging may hide a failed arm.

## Decision

Prefill ran first and stopped the candidate under the frozen rule; Mixed was
not run because no four-way promotion remained possible.

Evidence root:

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op022-qsa-r4-complete-consumer-timing-prefill-20260920T185150Z-105188`

- `result.json` SHA-256:
  `1ea0cdd4106c33f28851d5d00906ecf19d4511f31512f84566e81fb032e088a6`.
- Script SHA-256:
  `6a26a2615199917a87efffcdacc21970493d0adcbc6b850e0d844828c9e17e88`.
- Every fixture/source SHA, full structure, sampled FP32, eager numerical,
  static graph and post-timing guard passed. Baseline and candidate graph
  outputs were bit-exact across three replays, and candidate membership was
  bit-exact across replays.
- Eager generic/candidate medians were `9.950968/14.746951 ms`, so the
  candidate regressed `32.5219%` by the frozen gain formula. MAD/median was
  `0.0746%/0.7262%`.
- Graph generic/candidate medians were `9.941424/14.667456 ms`, so the
  candidate regressed `32.2212%`. MAD/median was
  `0.0979%/0.2595%`.
- Seven order-balanced samples were sufficient because all four arm/mode
  stability ratios were below 3%; no samples were discarded.
- The candidate paid `33,644,552` bytes of workspace plus output clear,
  membership build and grouped/fallback execution on every call. The result
  proves only that the complete combination is slower; it does not isolate
  one subcomponent as the sole cause.
- PPU0 was free before and after, port 8030 stayed healthy, and live
  `qsa.py` remained
  `e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`.

Decision: `no_go`. Do not run Mixed, install the prototype, or start a service
candidate. Installed FlagGems, Plugin, and retained service source remain
unchanged. Formal accuracy remains blocked by inherited GPQA
`170/198 = 85.86% < 88%`, and P32K remains deferred-too-slow under the
user-approved P4K-first policy.
