# fw-014: P16K no-async-scheduling repaired contract

## Goal and status

- Classification: `framework`.
- Status: `complete_valid_failed`.
- Goal: rerun the fw013 current/no-async/current control with an identity representation that treats equivalent CLI argument order as non-semantic while retaining raw argv for audit.
- Workload and performance gates are unchanged: P16384/D128/C64/N64, fresh sequential A/B/R, three warmup plus three measured rounds, output/total/duration at least 1% versus the A/R midpoint, A/R drift at most 1%, and every median/P99 latency guard within 5%.

fw013 stopped before candidate traffic because the prototype placed `--no-async-scheduling` after `--compilation-config` while the live launcher placed it before that pair. The semantic configuration was the same, but the frozen exact-path identity contract did not permit order variation. The fw013 contract is immutable, its A role is not reused, and no fw013 B/R performance conclusion exists.

## Repaired identity gate

- Preserve raw argv and its SHA in a role sidecar.
- Parse supported boolean flags and key/value options into one deterministic canonical object before comparator identity is built.
- Require A/R canonical `async_scheduling=true` and B `false`; all other canonical options, environment, container, source and workload fields must match.
- Before service launch, prove a prototype B and a simulated live B with the two observed raw orders canonicalize identically. A-to-B canonical diff must be only `/launch_config/async_scheduling`; A-to-R must be empty.
- Repeat the same canonical comparison against every actual live manifest before benchmark. Any additional diff stops the experiment; do not repair after measurement.

All graph, replay, request, output, QSA/source and host-quiescence gates from fw013 remain binding. Retained 8030 stays stopped and PPU8–15 stays idle during each performance role. Finish with all 16 cards released.

## Result

The canonical identity repair worked: prototype and live B raw argv orders normalized identically; A-to-B canonical diff was only `/launch_config/async_scheduling`, and A-to-R was empty. All services passed source, QSA, graph, replay, fallback and host-quiescence gates. Every measured round completed 64/64 requests with zero failures.

| Role | Output tok/s | Total tok/s | Duration (s) |
|---|---:|---:|---:|
| A, current async | 52.612 | 6786.956 | 155.706 |
| B, no async | 50.169 | 6471.846 | 163.287 |
| R, current async | 52.405 | 6760.226 | 156.321 |

The A/R midpoint was 52.508 output tok/s, 6773.591 total tok/s and 156.014s. A/R output drift was 0.3946%. B regressed output and total throughput by 4.4547% and made duration 4.6620% worse. All median/P99 TTFT, TPOT, ITL and E2E regressions remained under the 5% guard but were consistently 4.06%–4.69%, so no secondary metric rescues the candidate.

Changed-input graph replay matched. Cross-role canonical hashes of the measured generated text did not match despite fixed seeds; this additional hard failure is preserved, but the performance no-go is already decisive. Comparator SHA-256 is `86a96ba1fa200cadcb9f13aa7571704a010b99b03f90271d2953bb2218dc25b4`; final decision SHA-256 is `71b3d117719149313a44d0ae62e3e5577187aba7e2d52e4a9b215fa69eb639af`.

Decision: reject `--no-async-scheduling`, retain the current async path, and do not implement an arrival-alignment change from this evidence. Service86/87/88 were precisely stopped; 8030 and 8031 remain closed, all 16 cards are free, the candidate container remains running, and source/QSA identity is unchanged.
