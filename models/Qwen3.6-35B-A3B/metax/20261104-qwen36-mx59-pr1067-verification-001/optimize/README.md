# 20261104-qwen36-mx59-pr1067-verification-001 / optimize

<!-- e2e:summary:start -->

- 案例：20261104-qwen36-mx59-pr1067-verification-001
- 当前状态：completed_numerical_pass_performance_regressions_PR_remains_draft
- 当前候选：PR1067@fb7c9f9461e5b88b64617eb996db42636ddfc423
- 下一步：No automatic retuning or full model evaluation. Proposed defaults are not recommended; tests and negative results are published.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| pr1067-hardware-001 | verified_numerical_pass_performance_regressions_draft | MoE-BF16-E256-H2048-I256-topk8-M64-M8192 | [pr1067-hardware-001.md](pr1067-hardware-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| full-MoE-bfloat16-M63-uniform | main | graph_latency_median | 0.49867744052533025 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M63-uniform | candidate | graph_latency_median | 0.49868278114163145 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M63-uniform | revert | graph_latency_median | 0.49858290019788243 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M64-uniform | main | graph_latency_median | 0.49049208115558235 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M64-uniform | candidate | graph_latency_median | 0.49477066596349084 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M64-uniform | revert | graph_latency_median | 0.4897227773861009 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M65-uniform | main | graph_latency_median | 0.4844852369658801 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M65-uniform | candidate | graph_latency_median | 0.4842713546752929 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M65-uniform | revert | graph_latency_median | 0.4844483444371175 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8191-uniform | main | graph_latency_median | 2.3353843688964844 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8191-uniform | candidate | graph_latency_median | 2.3243885948544456 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8191-uniform | revert | graph_latency_median | 2.3626301175072077 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8192-uniform | main | graph_latency_median | 2.33432996840704 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8192-uniform | candidate | graph_latency_median | 2.348221006847563 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8192-uniform | revert | graph_latency_median | 2.3714437938871837 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8193-uniform | main | graph_latency_median | 2.4392960197047184 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8193-uniform | candidate | graph_latency_median | 2.4414316478528475 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8193-uniform | revert | graph_latency_median | 2.5073350270589194 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M64-concentrated | main | graph_latency_median | 0.1024392266427317 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M64-concentrated | candidate | graph_latency_median | 0.11200101791866242 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M64-concentrated | revert | graph_latency_median | 0.10175120739536431 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8192-concentrated | main | graph_latency_median | 1.7703634670802526 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8192-concentrated | candidate | graph_latency_median | 1.770832626907914 | ms | operator_only_BR_guard_passed |
| full-MoE-bfloat16-M8192-concentrated | revert | graph_latency_median | 1.76987886428833 | ms | operator_only_BR_guard_passed |
| full-MoE-float16-M64-uniform | main | graph_latency_median | 0.48985862731933594 | ms | operator_only_BR_guard_passed |
| full-MoE-float16-M64-uniform | candidate | graph_latency_median | 0.48937795600112605 | ms | operator_only_BR_guard_passed |
| full-MoE-float16-M64-uniform | revert | graph_latency_median | 0.48948518025506405 | ms | operator_only_BR_guard_passed |
| full-MoE-float16-M8192-uniform | main | graph_latency_median | 2.3815744400024412 | ms | operator_only_BR_guard_passed |
| full-MoE-float16-M8192-uniform | candidate | graph_latency_median | 2.3791679382324222 | ms | operator_only_BR_guard_passed |
| full-MoE-float16-M8192-uniform | revert | graph_latency_median | 2.4393081665039062 | ms | operator_only_BR_guard_passed |
| nonfast-gemm1-BF16-M64 | main | graph_latency_median | 0.3082941140338873 | ms | operator_only_BR_guard_passed |
| nonfast-gemm1-BF16-M64 | candidate | graph_latency_median | 0.31604197118189425 | ms | operator_only_BR_guard_passed |
| nonfast-gemm1-BF16-M64 | revert | graph_latency_median | 0.30784665144883194 | ms | operator_only_BR_guard_passed |
| nonfast-gemm2-BF16-M64 | main | graph_latency_median | 0.15913061261570494 | ms | operator_only_BR_guard_passed |
| nonfast-gemm2-BF16-M64 | candidate | graph_latency_median | 0.1595927720824724 | ms | operator_only_BR_guard_passed |
| nonfast-gemm2-BF16-M64 | revert | graph_latency_median | 0.15925035550612812 | ms | operator_only_BR_guard_passed |
| nonfast-gemm1-BF16-M8192 | main | graph_latency_median | 1.4320564831004423 | ms | operator_only_BR_guard_passed |
| nonfast-gemm1-BF16-M8192 | candidate | graph_latency_median | 1.6321791966756185 | ms | operator_only_BR_guard_passed |
| nonfast-gemm1-BF16-M8192 | revert | graph_latency_median | 1.4324442358577953 | ms | operator_only_BR_guard_passed |
| nonfast-gemm2-BF16-M8192 | main | graph_latency_median | 0.9852851104736329 | ms | incomplete_BR_drift_exceeds_3percent |
| nonfast-gemm2-BF16-M8192 | candidate | graph_latency_median | 1.0186346769332886 | ms | incomplete_BR_drift_exceeds_3percent |
| nonfast-gemm2-BF16-M8192 | revert | graph_latency_median | 1.043066552344789 | ms | incomplete_BR_drift_exceeds_3percent |

<!-- e2e:summary:end -->
