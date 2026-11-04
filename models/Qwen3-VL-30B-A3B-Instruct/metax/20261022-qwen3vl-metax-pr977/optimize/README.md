# 20261022-qwen3vl-metax-pr977 / optimize

<!-- e2e:summary:start -->

- 案例：20261022-qwen3vl-metax-pr977
- 当前状态：kvcache-split1-GPQA-passed
- 当前候选：PR943 a1570df MoE bbc2edded + Plugin MetaX kvcache num_splits=1; gems-opt/sampling/prefix cache and other launch settings preserved
- 下一步：User paused mx-59; migrate exact source container and related services to mx-104 under new host-specific case.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-001-upstream977-no943 | reject-pure-upstream-no943;preserve-production | p1024-d1024-c64-n128 | [op-001-upstream977-no943.md](op-001-upstream977-no943.md) |
| pr-002-refresh943-upstream977 | publish-tested-minimal-refresh;no-production-backwrite | pr943-upstream-refresh | [pr-002-refresh943-upstream977.md](pr-002-refresh943-upstream977.md) |
| acc-003-pr943-gpqa-erqa | retain-evidence;no-promotion | — | [acc-003-pr943-gpqa-erqa.md](acc-003-pr943-gpqa-erqa.md) |
| diag-004-gpqa-controlled | retain-unchanged-latest;no-accuracy-promotion | — | [diag-004-gpqa-controlled.md](diag-004-gpqa-controlled.md) |
| diag-005-fixed-prefix-logits | retain-requested-PR943-update;restore-original-config;no-split-fix-deployed | — | [diag-005-fixed-prefix-logits.md](diag-005-fixed-prefix-logits.md) |
| op-006-kvcache-split1-gpqa | retain-scoped-fix;performance-unmeasured | — | [op-006-kvcache-split1-gpqa.md](op-006-kvcache-split1-gpqa.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| operator-e128-h2048-i384-topk8 | baseline | GPU_cases_passed | 18 | cases | 18 numerical/resource cases; not E2E performance |
| operator-e128-h2048-i384-topk8 | candidate | GPU_cases_passed | 14 | cases | 18 numerical/resource cases; not E2E performance |
| operator-e128-h2048-i384-topk8 | revert | GPU_cases_passed | 18 | cases | 18 numerical/resource cases; not E2E performance |
| gpqa-diamond-198 | candidate | accuracy | 62.121212121212125 | percent | full 198; PR943 independent instance; prefix cache enabled |
| erqa-400 | candidate | accuracy | 41.0 | percent | full 400; PR943 independent instance; prefix cache enabled |
| gpqa-controlled-full198-c32-seed1234 | B1-new | accuracy | 64.64646464646465 | percent | Predeclared full-task diagnostic repeat; no passing acceptance gate |
| gpqa-controlled-full198-c32-seed1234 | A1-old | accuracy | 63.13131313131313 | percent | Predeclared full-task diagnostic repeat; no passing acceptance gate |
| gpqa-controlled-full198-c32-seed1234 | A2-old | accuracy | 62.62626262626263 | percent | Predeclared full-task diagnostic repeat; no passing acceptance gate |
| gpqa-controlled-full198-c32-seed1234 | B2-new | accuracy | 63.13131313131313 | percent | Predeclared full-task diagnostic repeat; no passing acceptance gate |

<!-- e2e:summary:end -->
