# op011: M64 fused-MoE GEMM2 `BLOCK_SIZE_N` falsification plan

Status: read-only analysis and local draft only. No remote source, container,
service, or accelerator workload was changed or run.

## Live identity and call path

- Candidate container: `qwen3.8-flash-opt-candidate-20260919`.
- Live service PID observed during the read-only check: `2636577`.
- Active config folder:
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-only-01`.
- Plugin source: `/workspace/vllm-plugin-FL-qwen38-adaptation`, revision
  `939600b323c02c21916f1f76bfb4cd8c2b02578d`.
- FlagGems source actually imported by the process:
  `/workspace/FlagGems/src/flag_gems`, revision
  `2b1e5cfdbd22d453933b2c6589a29daf31315ccd`.
- FlagGems-vllm revision was
  `5865ed53b183e6d3aff69ad1823622a11679d257`; it is not the fused-MoE
  implementation reached by this path.
- Existing dirty files were preserved. Plugin had unrelated Qwen/QSA/worker
  edits; FlagGems had only `src/flag_gems/fused/qsa.py` modified. The MoE files
  inspected here were not listed as modified.

The effective chain is:

1. `vllm_fl/ops/fused_moe/fused_moe.py:fused_experts_impl` calls vLLM's
   `try_get_optimal_moe_config` once.
2. The returned single `config` is passed to both GEMM1 and GEMM2 through the
   Plugin `CachedOp("invoke_fused_moe_triton_kernel")`.
3. The FlagGems backend imports
   `flag_gems.invoke_fused_moe_triton_kernel`.
4. FlagGems launches
   `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py:fused_moe_kernel`.

The Plugin currently executes three separate operations: GEMM1,
`_silu_and_mul`, and GEMM2. Although the current FlagGems kernel has an
optional `FUSE_SILU` mode, this Plugin wrapper does not pass that option; the
live M64 path is therefore not using the FlagGems GEMM1+SiLU fusion branch.

## Exact retained M64 configuration and shapes

The live `E=512,N=80,device_name=thead.json` entry for key `64` is:

```json
{
  "BLOCK_SIZE_K": 128,
  "BLOCK_SIZE_M": 16,
  "BLOCK_SIZE_N": 64,
  "GROUP_SIZE_M": 1,
  "SPLIT_K": 1,
  "num_stages": 3,
  "num_warps": 4
}
```

The rank-local BF16 shapes represented by the existing case and live model
code are:

| stage | A | B | logical output N | routed top-k |
|---|---:|---:|---:|---:|
| GEMM1 | `[64,2560]` | `[512,160,2560]` | 160 | 10 |
| activation | `[640,160]` | n/a | 80 | n/a |
| GEMM2 | `[640,80]` | `[512,2560,80]` | 2560 | 1 per routed row |

Both GEMMs therefore use `BM16/BN64/BK128/GROUP1/warps4/stages3` today.
GEMM1 has `K=2560`; GEMM2 has `K=80`. The same aligned token/expert mapping is
reused by both stages.

## prof004 evidence and stage attribution

Evidence source:

`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-004-p4k-post-op008/summaries/fused-moe-signatures-by-phase.json`

The M64 Decode graph signature is uniquely consistent with BM16 and the
FlagGems launch formula
`ceil(EM/BM) * ceil(actual_N/BN)`. Its two stage signatures are:

| stage | grid | block | registers/thread | shared memory | count | average | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| GEMM1 | 1560 | 128 | 108 | 40960 B | 3408 | 128.110 us | 436600.516 us |
| GEMM2 | 20800 | 128 | 108 | 40960 B | 3408 | 255.788 us | 871725.892 us |

Reasoning: `1560 / ceil(160/64) = 520` aligned M programs, while
`20800 / ceil(2560/64) = 520`. GEMM2 accounts for approximately 66.6% of the
two GEMM elapsed time and has 13.33 times as many programs as GEMM1. The
profile does not include Triton meta-parameters directly, so tile/stage/warp
values come from the exact live config and are cross-checked against the
observed block/shared-memory signature.

## One narrow hypothesis

Change only GEMM2 `BLOCK_SIZE_N` from 64 to 128 for the exact retained M64
BF16 shape. Keep GEMM1 and alignment unchanged, and keep GEMM2's
`BM16/BK128/GROUP1/warps4/stages3` unchanged.

Expected structural effect:

- GEMM2 `N=2560` is exactly divisible by 128.
- GEMM2 grid falls from `520 * 40 = 20800` to `520 * 20 = 10400` programs.
- GEMM1 stays at grid 1560 and cannot contaminate attribution.
- K reduction order, routed-weight application, output dtype/layout, and
  alignment remain unchanged, so bitwise BF16 equality is plausible and is a
  hard gate rather than an assumption.

This is preferred over a simultaneous BK/stage/warp scan because it changes
one compile-time field and directly targets the profiled dominant stage.

## Risks

- A `16x128` accumulator may increase register pressure enough to offset the
  halved grid. That is the main performance falsification risk.
- A new Triton specialization will compile once. Compile time must not enter
  timed samples; warmup is mandatory.
- Graph capture may expose an unsupported specialization or an autotune cache
  miss. Both variants must capture and replay twice after warmup.
- Synthetic random routing preserves the exact tensor schema and maximum
  aligned capacity but does not reproduce the production expert histogram.
  Passing the microbenchmark only permits a bounded service experiment; it is
  not an end-to-end result.
- The draft Plugin guard is deliberately exact and opt-in. It is suitable for
  falsification, not PR-ready design. A retained implementation should extend
  the tuned-config schema to distinguish GEMM1 and GEMM2 rather than preserve
  this exact-shape environment switch.

## First experiment and hard gates

Local draft:

`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op011-m64-gemm2-bn128-microbench.py`

It measures GEMM1, activation, GEMM2, the three-operation pair, and the full
transaction including `moe_sum`. It uses three alternating rounds with 20
warmups and 100 timed iterations per metric. It also checks both the routed
GEMM2 output and final reduced output.

Suggested isolated-container invocation after cards are available (not run by
this analysis):

```bash
python3 op011-m64-gemm2-bn128-microbench.py \
  --device 0 --warmup 20 --repeat 100 --rounds 3 \
  --output result.json
```

Promotion requires all of the following:

1. Candidate GEMM2 and final reduced BF16 outputs are bitwise equal to the
   retained BN64 reference.
2. Baseline and candidate each complete graph capture and two replays; every
   replay is bitwise equal to eager and to the other replay.
3. Median full transaction
   `GEMM1 + activation + GEMM2 + moe_sum` speedup is at least `1.08x`.
4. The JSON confirms the only changed field is
   `gemm2.BLOCK_SIZE_N`, with expected GEMM2 grids 20800 and 10400.

Stop immediately on any correctness or graph failure, or if the median full
transaction gain is below 8%. Do not scan other M keys, BK, stages, or warps
after a failed result under this hypothesis.

## Patch draft and validation

`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op011-m64-gemm2-bn128-draft.patch`

The patch is off by default. With `VLLM_FL_M64_GEMM2_BN128=1`, it changes only
GEMM2 after an exact BF16/shape/top-k/base-config/no-quant/no-bias guard;
otherwise it passes the original config unchanged. The local patch was piped
to the live candidate container only as stdin to:

```bash
git -C /workspace/vllm-plugin-FL-qwen38-adaptation apply --check -
```

The check passed. The patch was not applied.

## Read-only evidence commands

```bash
docker exec qwen3.8-flash-opt-candidate-20260919 python -c \
  'import importlib.util; print(importlib.util.find_spec("flag_gems").origin)'

docker exec qwen3.8-flash-opt-candidate-20260919 python -c \
  'import json; p="/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/configs/moe-bm16-decode-only-01/E=512,N=80,device_name=thead.json"; print(json.load(open(p))["64"])'

python3 -c \
  'import json; p="/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-004-p4k-post-op008/summaries/fused-moe-signatures-by-phase.json"; print(json.dumps(json.load(open(p)), indent=2))'
```
