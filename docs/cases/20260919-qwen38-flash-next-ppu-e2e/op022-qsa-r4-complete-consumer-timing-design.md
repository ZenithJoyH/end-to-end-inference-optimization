# op022: QSA R4 complete-consumer timing

## Frozen scope

op022 is an isolated rows4096 consumer microbenchmark. It imports the hardened
op020 fixture/correctness implementation at SHA-256
`13bf633180074fb578bc99897ab645b922fc5e63efccb0ae585417b78aa08fd5`
and the request-boundary-fixed op019 R4 implementation at SHA-256
`7a2dd94e2918a2cf88be803235a62d9362d9a71bb6da13a49cc9d0dd7fc36acc`.
Any dependency drift is a blocker.

The runner consumes immutable remote uploads named
`op020-qsa-producer-integrated-r4-rows4096-diag-v2.py` and
`op019-qsa-r4-direct-membership-microbench-boundary-fix-v3.py`. The harness
also resolves the actually imported generic QSA source, requires SHA-256
`e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`,
and records its resolved path and hash.

Prefill and Mixed run in separate processes using their immutable verified
op021 fixtures. The producer is excluded from both arms:

```text
baseline:  current generic qsa_sparse_paged_attention
candidate: output clear + complete workspace clear + membership build
           + boundary-fixed R4 attention/exact fallback
```

The comparison therefore measures only the consumer replacement. It is not an
endpoint result and does not include TopK or producer cost.

## Correctness before timing

Before creating events, each phase must pass:

1. fixture manifest/raw SHA, rows4096, selected `[4096,2051]`, phase and shape
   similarity checks inherited from op020;
2. selected immutability and exact match with the captured fixture;
3. eager candidate versus generic at `atol=rtol=0.05`, sampled FP32 reference,
   complete membership/group-base/overflow reconstruction, all writer markers,
   and CPU row ownership exactly once;
4. one static graph for baseline and one static graph for candidate, with three
   untimed replays per arm; no input update occurs after capture; each arm is
   bit-exact across replays and candidate workspace is rebuilt exactly;
5. a final output/workspace/selected guard after all timing.

The two timing graphs are independent comparison arms, not the rejected dual
graph A/B dynamic-input scheme. Their inputs and addresses remain fixed.

## Timing and statistics

Eager and graph are measured separately. For each mode:

- five untimed paired warmups;
- each event contains five calls/replays of one arm;
- seven paired samples with alternating arm order;
- if either arm has `MAD/median > 3%`, extend to eleven samples without
  deleting any value;
- if either arm still exceeds 3%, the measurement is invalid and cannot pass;
- retain every raw sample, order, paired gain, median, p25/p75, MAD,
  MAD/median, min and max.

The frozen gain is:

```text
gain = baseline_median / candidate_median - 1
```

Prefill-eager, Prefill-graph, Mixed-eager and Mixed-graph must each be at least
8%. A single phase records only its phase gate; a later aggregator must require
all four and use their minimum. No single run can promote the candidate.

## Safety and result boundary

The runner creates a unique result directory, verifies PPU0 is free before and
after, checks retained port 8030 health before and after, and requires live
`qsa.py` SHA-256
`e18fbb229d9c4a5c2b06a6858ae4679596e1a6f971a4ff8878acbbc4f469db23`.
It refuses fixture/dependency drift, has a 30-minute timeout, writes structured
blocked/failed results where possible, and never overwrites an artifact.

Profiler time, capture, compilation, warmup, D2H copies, hashes, fixture load,
correctness references and device-health checks are outside event intervals.
No service or source is modified. Passing all four microbenchmark gates only
permits an isolated P4K service milestone; it does not establish endpoint
speedup or formal acceptance.
