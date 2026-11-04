# prof-006a: P4K device-idle / host-handoff causal proof

## Decision

`no_go_or_inconclusive`; do not implement `fw-012` from this evidence.

The frozen diagnostic workload was `P4096/D128/C64/N64`, three measured
rounds per arm, on isolated PPU0-7/port 8031.  The retained PPU8-15/8030
service stayed healthy and kept the same PID/start-ticks/argv throughout.
This is profiling evidence, not a formal performance result.

## Valid evidence

- no-probe control diagnostic SHA-256:
  `74c37aac5a39a119df9266874e5e83c0c5a608f3ad691c724eac47ce5f2f7a9c`
- event diagnostic SHA-256:
  `078331bd9d54c6d7dad56050f93cfa80c17dd09fedc0685a986c4ca2d3b2b301`
- event+host-ring diagnostic SHA-256:
  `043827bb49878388a99a4c01151b6913706841fdb5335541fd04c57ba622a9ad`
- final analysis:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof006a/prof006a-resume-v6-20260921T105000Z/analysis-v2.json`,
  SHA-256 `99f088f20693860a9175b19f65007902781b56dbb92c7844d2b1e7cbca563abf`.

All three arms completed 64/64 requests in all three measured rounds with
exact `262144` input and `8192` output tokens per round.  Event and
event+host arms each contain engine plus TP0-7 registrations loaded from the
private `/opt` Plugin copy, 579 actual model-forward steps, 63 Mixed steps per
round, no ring overflow, and identical `(new,cached,total_tokens)` sequences.
The event+host engine additionally recorded six `(0,0,0)` empty schedule
rows, exactly two after each round; they are preserved as context and excluded
only from worker-step alignment.

## Result

- no-probe/event/event+host median walls:
  `46.593398 / 46.111190 / 46.671939 s`.
- event versus control: `-1.0349%`; event+host versus event: `+1.2161%`.
  Both absolute perturbations exceed the frozen `0.5%` limit.
- all arm wall MAD/median ratios are below `0.16%`, so the arm-local samples
  are stable even though cross-service perturbation fails the bound.
- event-only common-rank inter-forward device idle is `7.6339%` of wall.
- causal Plugin preprocessing lower bound is exactly `0`: across all
  `3 x 63` Mixed steps, not one step had the previous forward-end event
  complete on all TP ranks at worker entry.
- schedule and dispatch-return medians (`6715.594 us` and `192.235 us`) are
  contextual only; no cross-process clock subtraction or speedup claim uses
  them.

The evidence therefore proves a repeatable common-rank device gap, but does
not prove that Plugin model preprocessing creates it or that removing a host
handoff can reclaim it.  The strict causal gate and both perturbation gates
fail, so a scheduler patch would be speculation.

## Diagnostic repairs and cleanup

The first drafts were stopped by their own validity gates: the current service
uses stock `Scheduler`, not `AsyncSchedulerFL`; worker device-event export is
unsafe from a background thread; and engine has legitimate zero-token empty
schedules.  The final valid capture used a stock-Scheduler Plugin shim and
`MultiprocExecutor.collective_rpc("prof006a_flush")` after measurement so each
worker exported on its normal RPC execution thread.  Failed drafts remain as
invalid evidence and are not mixed into the result.

The final cleanup receipt SHA-256 is
`fcd71400e477a074cb356d57ecf2002e8f5e54af77a9ae89872606cc03f8f315`.
Port 8031 closed, PPU0-7 were released, port 8030 remained healthy, and the
original Plugin files returned to SHA-256
`2a7e9039...` (`__init__.py`), `a8de1780...` (`worker.py`), and
`2df8aa58...` (`model_runner.py`, including the pre-existing retained blocking
Event diff).  No prof006a code is installed in the retained service.

Formal accuracy remains blocked by inherited GPQA `170/198 = 85.86% < 88%`.
