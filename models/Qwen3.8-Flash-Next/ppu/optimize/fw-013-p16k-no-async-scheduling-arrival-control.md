# fw-013: P16K no-async-scheduling arrival control

## Goal and status

- Classification: `framework`.
- Status: `incomplete_identity_contract`.
- Mechanism: compare the current asynchronous scheduler with the existing `--no-async-scheduling` control to test whether rank0 host/output work causes graph-enqueue skew and collective waiting.
- Workload: exact P16384/D128/C64/N64, fresh sequential A/B/R, three warmup plus three measured rounds, no profiler.

prof007 reports identical total AllReduce call counts on all ranks but rank0 total collective activity of 5.684s versus 13.544s for ranks1-7 median. This difference is an arrival-wait upper bound, not additive communication work. Historical same-clock events show rank0 graph enqueue lag near 14.12ms for 4096-token steps and 9.66ms for Decode steps, with other-rank graph duration increasing by the same amount before returns realign. Prior instrumentation had more than 0.5% observer effect and a strict causal lower bound of zero, so it cannot authorize code changes.

## Frozen experiment

- A/R: current async scheduling.
- B: only `--no-async-scheduling` changes.
- Same 8-card group, service port and source identity for all roles; no concurrent benchmark on the other group.
- A/R output drift at most 1%.
- B relative to A/R midpoint must improve output throughput, total-token throughput and duration by at least 1%.
- Median/P99 TTFT, TPOT, ITL and E2E may not regress more than 5%; zero failures, consistent outputs, all FULL graph keys and at least two changed-input replays are required.
- A B warmup regression over 5%, graph fallback/recapture, source drift, request failure or invalid comparison stops the experiment.

If B improves collective balance but exact end-to-end gain remains below 1%, the apparent wait is treated as overlap transfer and this direction is permanently closed. A separate lightweight timestamp probe is optional only after the no-profiler result; its instrumentation-versus-plain duration difference must be at most 0.5%.

## Stopped result

Service83 A completed 3+3 with measured output-throughput median 52.341 tok/s and zero failures. Service84 B passed readiness, graph and source gates, but its actual raw argv placed `--no-async-scheduling` before the `--compilation-config` pair while the frozen prototype placed it after that pair. This produced a different exact argv path layout even though the semantic launch variable was unchanged.

The identity hard gate stopped the experiment before any B benchmark request. The contract was not edited; B was precisely stopped and R was not launched. The A result is standalone environment evidence only and is not used to compute a gain. A new fw014 experiment must pre-freeze order-insensitive canonical launch identity and rerun all roles from fresh services.
