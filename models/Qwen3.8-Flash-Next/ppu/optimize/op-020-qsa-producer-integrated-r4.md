# op-020: producer-integrated QSA R4 single-graph gate

## Scope and frozen boundary

- Classification: `operator/improve`.
- Current status: `rows64 and real-P4K rows4096 Prefill/Mixed single-graph
  correctness gates passed; standalone complete-transaction timing is next`.
- The captured transaction contains an in-graph phase advance, Q staging,
  the real `qsa_select_paged_tokens` producer, current generic sparse
  attention, and the op-019 R4 clear/build/grouped-attention/fallback path.
- Exactly one graph is captured. Three consecutive replays have no external
  input writes and must produce A/B/A. Two independent captures, static
  selected replay, and performance timing before correctness completion are
  forbidden.

The frozen design is recorded in
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op020-qsa-producer-integrated-r4-captured-transaction-design.md`.
The executed script SHA-256 is
`ef28b47f96fbe733bf4dd56e5e91aa06e667886569163423350c9b5189936176`;
the imported op-019 candidate SHA-256 is
`d20e5c8df2f306043b2d7d13b0e1964b4e7ea61e8d058a3d73fadba553674fee`.

## Capture-semantics calibration

The first run stopped before replay at the intended capture-semantics guard:

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op020-qsa-producer-integrated-r4-rows64-20260920T171532Z-2356688`

It proved that this PPU records the graph without executing the transaction:
after seeding phase B, capture left `phase=B, phase_used=A`. The blocked result
was retained; no replay or performance result was inferred. The script was
then changed only to seed phase A and require capture to leave it unchanged,
so graph-internal phase flips generate A/B/A during the three actual replays.
This is a backend-semantics correction, not a relaxed gate.

## Passed rows64 gate

The passing evidence is:

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op020-qsa-producer-integrated-r4-rows64-20260920T171728Z-2395070`

- `result.json` SHA-256:
  `ad3ca56643311ffb85e314db2dc39a143d5f122eeb934d5ea895fa0eecd632bd`.
- `snapshots.pt` SHA-256:
  `634a3db1b34f205e4740c3ec91580a7689829e9348a292a015d8a9002c1a262f`.
- One graph was captured and replayed exactly three times in A/B/A order;
  `external_phase_updates_during_replay=false` and
  `two_graph_fallback_used=false`.
- All 64 selected rows changed between A and B; 130,944 selected cells and all
  16 complete membership groups changed.
- A1 and A2 selected, full membership, group metadata, generic output, and
  candidate output returned exactly to their A evidence. B matched its eager
  oracle with distinct selected, membership, and outputs.
- All 139,264 membership cells and 17 group slots were compared with the CPU
  structural reference on each snapshot. Duplicate rows were zero, selected
  values stayed in the 8192-token direct-address domain, and every row/head
  write marker was one.
- Candidate versus generic maximum absolute error was `0.0009765625` for both
  A and B; mean absolute error was about `3.65e-05`/`3.69e-05`, within the
  frozen `atol=rtol=0.05` boundary.

## Passed real-P4K rows4096 gate and boundary-race repair

The final correctness harness is
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op020-qsa-producer-integrated-r4-rows4096.py`,
SHA-256 `13bf633180074fb578bc99897ab645b922fc5e63efccb0ae585417b78aa08fd5`.
It consumes the immutable op021 Prefill/Mixed manifests, replays the real
producer, reconstructs every membership cell on CPU, checks sampled FP32
attention, and runs one internally advancing A/B/A graph without replay-time
external writes.

The first Mixed attempt exposed a real prototype defect rather than a reason
to relax the numerical gate. Its request starts are `[0, 1, 4096]`: the
one-row request-0 tail group wrote rows 0--3 while request 1 wrote rows 1--4.
Rows 1--3 therefore had two candidate writers. Two diagnostic runs observed
283 and 69 differing BF16 output elements, respectively, with maximum error
`0.0078125`; selected, full membership/metadata, and generic output remained
bit-exact. The existing write marker could not detect the race because both
writers stored the value one.

The standalone op019 prototype was repaired by requiring every attention
lane and source row to belong to the base row's request, and by applying the
same lane-valid mask to score computation. The fixed prototype SHA-256 is
`7a2dd94e2918a2cf88be803235a62d9362d9a71bb6da13a49cc9d0dd7fc36acc`.
No installed FlagGems file or retained service was modified.

The fixed evidence is:

- Prefill:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op020-qsa-producer-integrated-r4-rows4096-prefill-20260920T183652Z-4001203`,
  `result.json` SHA-256
  `0fbb863e7dfcfd984412a28d76511f1d629b12b52b4b51afb4fbaae12cf93df3`.
- Mixed:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op020-qsa-producer-integrated-r4-rows4096-mixed-20260920T183619Z-3989727`,
  `result.json` SHA-256
  `a7a0dcea5d44f209add02350ccb6c577a98e21644af1f4743d00099e25471fdd`.
- Prefill/Mixed shape similarity exactly recovered the frozen R4 values:
  `rho=0.695121889/0.694797948`, union max/p99/p90/p50
  `3460/3292/3036/2052` and `3400/3292/3056/2048`.
- Real producer A reproduced captured selected tensors exactly. Prefill has
  1024 eligible groups and no fallback; Mixed has 1023 eligible groups and
  four fallback rows at the request boundary.
- Eager and graph candidate outputs match generic within `0.05/0.05`;
  maximum absolute error is `0.0078125` for Prefill and `0.015625` for Mixed.
  Sampled FP32 reference checks pass.
- A1 and A2 selected, complete membership/metadata, generic output, and fixed
  candidate output are bit-exact for both phases. A/B changes 2045 selected
  rows and 512/513 membership groups.
- Both runners found PPU0 free before and after. Port 8030 remained healthy
  and live `/workspace/FlagGems/src/flag_gems/fused/qsa.py` remained
  `e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`.

## Decision and next gate

The rows64 and both real-P4K rows4096 correctness gates pass. No timing has yet
been executed and no speedup is claimed. The next authorized step is a new,
separate standalone experiment that measures Prefill and Mixed rows4096
complete `select+sparse` transactions in eager and graph modes against the
frozen 8% threshold. A result below 8% in either required phase/mode stops the
candidate before installed-source or service integration.

Formal acceptance remains blocked by inherited GPQA `170/198 = 85.86% < 88%`.
