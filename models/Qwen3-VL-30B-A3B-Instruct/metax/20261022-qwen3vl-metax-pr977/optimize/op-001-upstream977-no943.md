# op-001 Upstream PR977 without local PR943 changes

User requests updating FlagGems-vllm and testing whether latest upstream replaces local943 shared-memory protection and tuning. Freeze main at bad340d, including merged977 eb04ad7. PR943 remains unmerged. PR977 targets Qwen3.6 E256; current Qwen3-VL uses E128,H2048,I384,topk8 and requires actual tests.

Source: qwen3vl-p64k-opt-20261015, mx-59, active GPU6/7, port9999. New isolated container: qwen3vl-pr977-20261022 on idle GPU0/1. User-provided remote root /public-flash/jinghao/qwen3-VL; resolved path, owner0, mode755, free6.43TB verified. New case directory20261022-qwen3vl-metax-pr977. Snapshot effective writable layer, preserve all mount mappings and verify exact content parity before changes.

Only update FlagGems-vllm. Preserve gems-opt, sampling/histogram, Plugin, vLLM and model/tokenizer. No FlagGems operator is disabled. Candidate MoE must be byte-identical to frozen upstream and contain no943 overlays. Changes first validated independently, with backups before any later production source update. Never restart original service as part of this test.

Accuracy mode minimal-regression: independent FP32 mathematical reference, BF16/FP16 tolerance inherited from prior validation, target shapes M0/1/8/64/65/257/1024/4096/8192, prioritize historical large-M resource failures. Graph capture followed by two changed-input/routing replays. Then actual TP2 graph service smoke/C8 and both-rank import evidence. Failure freezes promotion and retains logs.

Performance mode targeted, steady_state. Mixed target P1024/D1024/C64/N128; prefill sentinel P1024/D1/C64/N64; decode sentinel P1/D256/C64/N64. Client TTFT/TPOT are proxies and include residual scheduling/network cost. Original production GPU6/7 data is not a same-hardware baseline. New B/C/R all use GPU0/1, no prefix cache, same sampled generation .7/.8/20, three warmups and two measured rounds. Last-two warmup spread<=8%; preserve every admitted measurement. Main output throughput, secondary total throughput; significant benefit>=2%, latency regression<=10%, within-role spread and B/R drift<=8%. Stop if correctness, graph, resources or admission fails; never discard a slow admitted round.

This is a scoped diagnostic/performance_only comparison, not full four-scenario acceptance. Old opt10 GPQA/ERQA gates cannot bind new code. Frozen source/current configuration remains the rollback reference. Commands, native evidence and full logs stay remote.

## Final result

Pure frozen upstream main bad340d (includes977) does NOT replace the local943 resource fix for this model. Candidate MoE SHA1d56b618594aa319da73490e73eff83f1b2604deb2cd875eed19b77e92fc871e is byte-identical to upstream. Sampling941bdc... remains identical; only its two files and two existing export entries were retained outside MoE. Actual import: /workspace/FlagGems-vllm-upstream977/src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py.

| Role | GPU cases passed | Captures | Changed-input/routing replays | Result |
|---|---:|---:|---:|---|
| Current original | 18/18 | 14 | 28 | passed |
| Latest upstream without943 | 14/18 | 10 | 20 | failed at large M |
| Revert to original | 18/18 | 14 | 28 | passed |

Both BF16 and FP16 fail at M4096 and8192, GEMM1 with w1=(128,768,2048). Actual selected config: BM128/BN128/BK64/group1/warps8/stages4/PAIR_GATE_UP_DOT=true. Triton launch metadata raises OutOfResources: shared memory Required98304, hardware limit65536. This is an execution/resource regression, not an observed numerical mismatch. All four failures retain full traces and configs. Nonempty passing cases match independent FP32 reference with unchanged BF16 atol.004/rtol.016 and FP16 atol.0005/rtol.003; passing graphs have two changed-input/routing replays each.

Mechanism: current E128 misses upstream _is_qwen_tp2_moe_shape and _is_qwen_moe_shape. _generic_get_default_config still uses a200000-byte ceiling and minimum stages2, and chooses the paired fast path. PR977 fixes the E256 TP2 branch and adds optional workspaces; it does not bound this E128 generic path by the C55064KiB limit. No claim that PR977 introduced the bug: the latest snapshot still contains this missing protection. More detailed upstream commit bisection was unnecessary for the requested latest-only decision.

Stopped candidate promotion after the required minimal regression failure. No TP2 candidate service or end-to-end timings were run; P1K steady throughput, total throughput and Prefill/Decode/Mixed speedup are not_run, not zero and not inferred from local kernels. No FlagGems operators were disabled, no fallback or resource-fix overlay was added to upstream MoE, no model-score gate was claimed. Incident accdiag-001-upstream977-e128-smem records the failure and exact rollback.

Original qwen3vl-p64k-opt-20261015 service9999/qwen3vl-opt10 remains running unchanged onGPU6/7. Final audit verifies the same process argv, four repositories, model/tokenizer and /v1/models. No production library update or service restart was applied; retain the successfully evaluated original environment. Independent container and candidate clone remain for reproducibility.

Summary: /public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-pr977/results/summary.json, SHA542bfd1a531d8279061133cc0afdb7726b0c9b644c706d3a2e1fb1075c7b2a4a. Baseline/candidate/revert artifacts, gate, commands and hashes are in state.yml. Snapshot sha256:40cb617f8629a3829b3937a25c1d569d1a1ca0c91c40b6372fd3c1766fb77dd1; image_lineage verified and mount_parity passed.

Knowledge delta refined: a shape-specific upstream shared-memory fix does not prove protection of unmatched model geometries. First inspect whitelist membership and actual compiled metadata for the current E/N/K/topk; only then promote to graph service and E2E. No performance number or cross-model claim is justified here.
