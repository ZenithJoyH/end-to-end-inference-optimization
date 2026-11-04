# fw-010 TP8 RING/two-shot AllReduce causal control

## Status

`stopped_before_service_implementation` / `no_go_simple_protocol_regression`.

## Runtime identity and hypothesis

- Retained service: service50, PPU8-15, port 8030, healthy.
- Service launch has `--disable-custom-all-reduce`.
- Service log proves `backend=nccl`, vLLM `pynccl.py`, `nccl==2.27.3`, and
  `PCCL version 2.1.0-11-accl-p` with network plugin `accl-lite`.
- Prof005 no-stack evidence: Mixed RING AllReduce activity median `3.968s`
  in `40.143524s` marker wall; Decode two-shot activity median `1.742s`.
- Hypothesis: the already-supported `NCCL_PROTO=Simple` path can improve the
  weighted live TP8 transaction by at least 8% without rank outliers and can
  credibly expose at least 1% P4K Mixed wall gain.

The standalone probe does not reproduce vLLM wrapper overhead. It isolates the
same PCCL interface, topology, dtype, message sizes, and 96 reductions per model
step without profiler overhead.

## Frozen transaction contract

- TP8, BF16, hidden size 2560.
- 48 layers x attention-output and MoE/MLP-output reduction = 96 calls/chain.
- Production shapes: `[64,2560]` (320 KiB/call, Decode two-shot) and
  `[4096,2560]` (20 MiB/call, Mixed/Prefill RING).
- `[1,2560]` is a correctness boundary only and is excluded from the weighted
  performance gate.
- Baseline: PCCL defaults with `NCCL_ALGO` and `NCCL_PROTO` unset.
- Candidate: only `NCCL_PROTO=Simple`; `NCCL_ALGO` remains unset.
- Per arm: graph capture, two changed-input bit-exact replays, three warmups,
  seven measured chain replays, all-rank latency distribution.

## Pre-frozen gate

Advance to an isolated service candidate only if all conditions pass:

1. capture and both changed-input replays are bit-exact on every rank;
2. weighted production transaction gain is at least 8%;
3. for each production shape, max rank median / rank-median is at most 1.10;
4. applying the large-message gain to `3.968 / 40.143524` predicts at least 1%
   Mixed wall gain.

Stop without service/source modification on any correctness/graph/hang/rank
failure, a weighted gain below 8%, or predicted Mixed gain below 1%.

## Evidence locations

- Plan:
  `docs/cases/20260919-qwen38-flash-next-ppu-e2e/fw010-tp8-collective-microbench-plan.md`
- Script:
  `docs/cases/20260919-qwen38-flash-next-ppu-e2e/fw010-tp8-collective-microbench.py`
- Planned remote root:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/fw010-tp8-collective-002`

The preserved first smoke under `fw010-tp8-collective-001/smoke-default` is an
invalid harness attempt: PCCL recorded collectives during capture but did not
update the buffers until replay, so the harness incorrectly asserted capture-time
output on every rank. Revision 002 adds eager lazy-path initialization and checks
the first explicit graph replay plus two changed-input replays.

## Result and decision

Both arms passed eager initialization, first explicit graph replay, two
changed-input bit-exact replays, seven measured full-chain replays, and the
`max-rank / rank-median <= 1.10` guard. The formal transaction results are:

| Rows | Default 96-call chain | Simple 96-call chain | Gain `(default/Simple)-1` | Max-rank ratio, default/Simple |
|---:|---:|---:|---:|---:|
| 1 | 571.820 us | 3714.800 us | -84.607% | 1.00150 / 1.00061 |
| 64 | 1449.580 us | 4285.800 us | **-66.177%** | 1.00054 / 1.00073 |
| 4096 | 18776.340 us | 25087.420 us | **-25.156%** | 1.00015 / 1.00025 |

The candidate increases rows4096 wall time by 33.612%. Even the deliberately
optimistic projection using the profiler-on `3.968 / 40.143524` activity ratio
is negative (`-2.487%` Mixed wall), rather than the required `+1%`.

- Default result SHA-256:
  `423fab8f05b097a745acc0dbde76050fbbd2e02d0ae29794a8fea77a98550b34`
- Simple result SHA-256:
  `efbefb3275becac3c7d0a00b5bf2ed71cc6d2a78691d9af0e1b704c621899a22`
- Executed script SHA-256:
  `d2d19b07b8556851c7df1924a1eb3a0eb0926dd64f4022aa37196a657fdc5a1f`

The supported Simple protocol is therefore rejected without service integration.
Default PCCL selection remains unchanged. The result also shows that the profiler
rank spread was not reproduced in the no-profiler transaction: every measured
max-rank ratio was within 0.16% of the rank median.

Formal acceptance remains blocked by inherited GPQA `170/198 = 85.86%`, below
the frozen 88% accuracy gate.
