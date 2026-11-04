# 20261026-qwen3vl-opt12-c64-default-accuracy / optimize

<!-- e2e:summary:start -->

- 案例：20261026-qwen3vl-opt12-c64-default-accuracy
- 当前状态：completed-both-accuracy-passed-user-service-retained
- 当前候选：User-started opt12 on9999/GPU0,1/prefixON;PR638+decode1+canonicalFGV+gemsopt/MoE
- 下一步：No pending model work;both full datasets once passed;CPU-only collector recovery verified;stop monitor;no performance claim or automatic rerun

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-001-opt12-c64-default | Both requested full datasets passed once;collector failure preserved andCPUrecoveryresolved;user service originalPID/source/models200 retained;no performance or PR638 single-variable attribution | GPQA198-C64-and-ERQA400-C64-server-default-sampling | [acc-001-opt12-c64-default.md](acc-001-opt12-c64-default.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa198-c64-model-defaults | candidate | strict_match_accuracy | 65.15151515151516 | percent | full198 questions;129correct;threshold64;measured instance only |
| erqa400-c64-model-defaults | candidate | native_accuracy | 42.21 | percent | full400 questions;168correct/398scored;2native timeout rejects;threshold40 |
| erqa400-c64-model-defaults | candidate | all400_accuracy_timeout_incorrect | 42.0 | percent | full400 questions;168correct;2timeouts incorrect;conservative supplementary denominator |

<!-- e2e:summary:end -->
