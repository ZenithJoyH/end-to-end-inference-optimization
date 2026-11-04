# pr-002 Refresh PR943 on latest upstream

User explicitly authorizes updating existing upstream PR943. Expected fork/main head090ef1d; retain history and normally merge upstream rather than force rewrite. Freeze current remote heads before editing. Reuse independent qwen3vl-pr977-20261022 private source; original production qwen3vl-p64k-opt-20261015 and its GPU6/7 service remain untouched.

Preserve latest977 Qwen3.6 E256 TP2 configuration, optional out/workspace support and all existing kernels. Port only943 narrow C550 E128 stage-aware measured profile, actual per-device shared-memory generic guard, dtype/batch-invariant/quantization exclusions and one marker compatibility line. No sampling/Plugin/gems-opt changes or new library test/perf/JSON files.

Validation scope: accuracy minimal-regression. Reuse original numerical tolerances, independently check FP32 mathematical reference, BF16/FP16 shape and M boundaries, nonmatching/FP32 and actual64KiB generic fallback; capture plus two changed-input/routing replays. Preserve existing upstream target configurations for E256/E512 by host oracle and focused GPU sentinels including supplied/aliased workspace. Validate target CI style and marker requirements on final diff. Publish only after exact-candidate tests, with a checked expected-head lease; update PR body around final implementation and limits. Full GPQA/ERQA and fresh E2E are not part of this PR maintenance; historical validations are not relabeled as current results.

## Contract and repository protocol review

This is maintenance of the existing MoE PR, not the stale conv1d task in the repository workflow template. The user explicitly requests retaining the tuned inline MetaX implementation while refreshing upstream. No new Triton kernel, NVIDIA tuning, export, registration, external dependency, benchmark or test file is introduced. Thus new-op integration/autotune and deep optimization are not triggered. optimization.md/deep_opt.md are absent at this revision; no missing skill blocks this scoped maintenance.

| Project fact | Scope |
|---|---|
| Editable | Private PR copy, MetaX fused_moe.py and existing one-line marker |
| Read-only | Production/Plugin/vLLM/FlagGems, original JSON oracle, upstream baseline |
| Build | Python-only; AST, syntax, whitespace, pinned Black/isort/flake8 |
| Numerical validation | Independent FP32 reference; BF16 .004/.016, FP16 .0005/.003, FP32 .0001/.001; no relaxation |
| Active set | Original55cases, E128 M0..8193, fallback/E64;8extra E128/E256 workspace cases |
| Benchmark/profiler | Not_run; no fresh speedup claim; actual dispatch and compiled resource evidence used |
| Timeout | GPU1800s, compatibility1200s, service readiness1200s, HTTP240s |
| Autotune | Existing inline measured C550 profile retained; no NVIDIA/kernel tuning changes |

| API contract | Scope |
|---|---|
| API | Existing fused_experts_impl, same latest-upstream public signature including out/workspace13/workspace2 |
| Math | Routed full forward, gate/up SiLU then down projection and weighted sum |
| Dtypes/layout | Current FP16/BF16 contiguous inference; FP32 fallback references; existing unsupported layouts rejected |
| Output/alias | Shape/dtype retained, original inplace; newest workspace alias/chunk policy unchanged |
| Accumulation | Existing kernels unchanged; reference casts activation intermediate to input dtype |
| Boundaries | Empty/singleton/nonaligned/nearest-M boundaries, two changed-input/routing graph replays |
| Unsupported | No new quantized, NaN/Inf, integer/complex, training/backward promises |
| Torch use | New production code reads cached per-device metadata only; test reference math remains external |

| Path | Implementation and evidence |
|---|---|
| Early/error | Existing empty/contiguous rejection unchanged |
| Measured E128 | Same C550/H2048/I384/topk8 half profile and dtype/block/batch-invariant exclusions |
| Upstream E256/E512 | Original specialized branches unchanged;992config comparisons and E256 GPU/workspace sentinels |
| Generic | Original non-Torch kernels, actual-device cap, paired/regular footprint and FP32 bytes |
| Unsupported | Existing behavior unchanged; no silent Torch fallback |

Fresh results so far:262160historical JSON comparisons,17negative gates,896shared-memory checks;55GPU cases/37references/23captures/46replays;8additional workspace cases/32references/8captures/16replays. Five Triton kernels and public arguments are AST-identical to latest upstream. All fixed-version style checks and the current marker checker pass. TP2 graph service validation remains pending; none of the earlier standalone results substitutes for it.

## Final publication

PR943 is updated and remains open, non-draft and mergeable. New head [316f03691271397f7f7d4c7eb3681f6c4dda6fb1](https://github.com/ZenithJoyH/FlagGems-vllm/commit/316f03691271397f7f7d4c7eb3681f6c4dda6fb1), parents090ef1d and latest upstreambad340d. This is a normal fast-forward of the fork main ref, force=false, expected-head090ef1d; no history rewrite. GitHub comparison confirms latest upstream is the merge base, behind_by0, and only2files/66additions/5deletions in the PR. The uploaded blobs match exactly the validated operator/test Git blob IDs. PR body now describes this latest implementation and fresh validation, rather than treating old results as current.

Final checks:55core GPU cases/37references/23captures/46replays;8E128/E256 workspace GPU cases/32references/8captures/16replays. Total63GPU cases,69math references,31standalone captures and62changed-input/routing replays. Host262160JSON comparisons,17exclusions,896memory checks,992upstream specialized-config checks passed.25existing tests collected; the marker-related test function passed10cases. Fixed-version Black/isort/flake8 and marker checks pass.

TP2 FULL_AND_PIECEWISE/max64 model service passed: both workers17376/17377 loaded operator749e81..., actualM64GEMM1/2stage3/1, capture and>=16delegated replays each during startup/smoke;11HTTP requests includingC8 passed. The dedicated18977service was then stopped using exact PID/start identity. Model runtime used a separate copy retaining the preexisting local sampler exports; these sampling files are excluded from the published PR tree. The MoE bytes were identical in PR and model runtime.

Fresh GitHub workflows for this exact head both completed successfully: [basic ci39734385734](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/39734385734) and [rule-check39734385003](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/39734385003). Style/target selection, MetaX MACA3.7.2.0 and3.8.1.0 job conclusions and multi-backend summary are success; NVIDIA job skipped. Important coverage boundary: both MetaX jobs' Run backend tests steps were skipped by the workflow, while Test alpha ops succeeded. Do not label that as full hardware test coverage; the dedicated local numerical/graph proof above is separate.

Publication receipt commands/pr002-refresh943/publication.json SHA47efa8a248db8e8384b7399165a1da6211405107f156fecccc3e173029f799c9. Exact-candidate gate commands/pr002-refresh943/publish-ready.json SHAc9d05ca75a15ef7b8cfa13a50acf8d72da46b0513b01cf2301cd6fb98f2060d4. Both under /public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-pr977; all native checks/SHA paths are linked from state.yml. Original production four repositories, model/tokenizer and9999readiness verified unchanged. No production backwrite, fresh GPQA/ERQA or E2E performance claim; pr_readiness=ready_for_review within the tested scope.

## 后续全量模型精度

用户选择最新PR943独立环境并开启prefix cache后，[acc-003](acc-003-pr943-gpqa-erqa.md)完整评测为GPQA123/198=62.12（阈值64，失败）、ERQA164/400=41.00（阈值40，通过）。数据/源码/实例及原生评分证据有效；这不覆盖或撤销本点原有算子数值/graph/CI通过，但当前模型组合不能签发通过gate。GPQA根因未隔离，不能直接归因本MoE补丁；生产未回写。

后续[diag-004受控诊断](diag-004-gpqa-controlled.md)：同卡四轮旧125/124、新128/125，未复现新版稳定下降；实际固定输入MoE在11种M下逐位一致，6次capture/12次replay通过。当前完整模型acc003失败仍保留，不以诊断较高分晋级，也未修改PR。

后续[diag-005固定前缀定位](diag-005-fixed-prefix-logits.md)已将独立运行副本同步PR943 a1570df，并在完整Q/K/V相同、同实例探针中性及忠实重放下定位首层MACA native kvcache自动路径的batch数值差异；组件固定split1消除差异，服务未应用该参数，其他配置及9999未动。原正式GPQA失败不覆盖，无新score/gate/E2E。
