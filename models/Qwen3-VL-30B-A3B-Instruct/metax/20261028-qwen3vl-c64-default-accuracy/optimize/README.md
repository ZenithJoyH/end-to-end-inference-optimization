# 20261028-qwen3vl-c64-default-accuracy / optimize

<!-- e2e:summary:start -->

- 案例：20261028-qwen3vl-c64-default-accuracy
- 当前状态：completed;accuracy-failed-GPQA;ERQA-passed
- 当前候选：qwen3vl-opt14:1597993:1146418910
- 下一步：User-requested evaluation finished;keep model running. GPQA cause remains unconfirmed;no automatic rerun/new optimization.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-001-opt14-c64-default | GPQA-failed;ERQA-passed;no-formal-accuracy-gate | GPQA198-C64;ERQA400-C64 | [acc-001-opt14-c64-default.md](acc-001-opt14-c64-default.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| GPQA198-C64-model-defaults | current-opt14 | strict-match | 59.59595959595959 | percent | 198unique;118correct;threshold64;valid failure |
| ERQA400-C64-model-defaults | current-opt14 | native-accuracy | 45.25 | percent | 181/400,0native rejects;threshold40;passed |
| ERQA400-C64-model-defaults | current-opt14 | all400-accuracy | 45.25 | percent | 181/400,all questions counted;passed |

<!-- e2e:summary:end -->
