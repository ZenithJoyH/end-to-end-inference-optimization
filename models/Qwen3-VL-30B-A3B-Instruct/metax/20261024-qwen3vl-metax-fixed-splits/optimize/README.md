# 20261024-qwen3vl-metax-fixed-splits / optimize

<!-- e2e:summary:start -->

- 案例：20261024-qwen3vl-metax-fixed-splits
- 当前状态：split0-full-evaluation-completed-source1-restored
- 当前候选：Originalsplit1 retained;split0 GPQA126/198=63.6364<64 rejected;ERQA176/400=44>=40 passed
- 下一步：Requested finitevalidation complete;no active evaluation/diagnostic/performance controllers. No automaticrerun/newsplit or performance;keep originalsource1 and failedGPQA incident for any separately planned follow-up.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-001-fixed-kvcache-splits | Rejectcandidate16;no morefullrepeatseries;onlynecessarysameprefixnativeboundarydiagnosis | p1024-d1024-c64-n128 | [op-001-fixed-kvcache-splits.md](op-001-fixed-kvcache-splits.md) |
| op-002-auto-kvcache-formal | Rejectsplit0promotion;originalsplit1 restored and current graph16/C8/source/launchverified;no score gate transfer/no performance claim | accuracy-only-gpqa198-erqa400 | [op-002-auto-kvcache-formal.md](op-002-auto-kvcache-formal.md) |
| maint-003-zombie-cleanup | One-timecleanupcompleted;no model/container restart or source/config/precision/performance changes | maintenance-no-performance-measurement | [maint-003-zombie-cleanup.md](maint-003-zombie-cleanup.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->
