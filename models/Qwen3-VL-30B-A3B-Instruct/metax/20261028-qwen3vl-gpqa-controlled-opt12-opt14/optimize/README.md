# 20261028-qwen3vl-gpqa-controlled-opt12-opt14 / optimize

<!-- e2e:summary:start -->

- 案例：20261028-qwen3vl-gpqa-controlled-opt12-opt14
- 当前状态：all experiments terminal;minimal batch-RNG firsttoken mechanism confirmed;source preserved
- 当前候选：original opt14 f81/paged/default0 retained;no test variant deployed
- 下一步：Report bounded mechanism;no pending execution or automatic further trials. Original fullGPQA score causality remains unresolved.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| diag-001-controlled-attention | version-associated reversible score gap;two factors remain unisolated | GPQA198-C64-defaults-B1-C1-R1 | [diag-001-controlled-attention.md](diag-001-controlled-attention.md) |
| diag-002-factorial-bridges | both bridges passed;no unique Prefill/split rootcause;all scores retained | GPQA198-C64-defaults-D1-E1-factorial | [diag-002-factorial-bridges.md](diag-002-factorial-bridges.md) |
| diag-003-parallel67-auxiliary | valid-score-failure;auxiliary cross-device not isolated hardware/rootcause | GPQA198-C64-defaults-E67-newGPU | [diag-003-parallel67-auxiliary.md](diag-003-parallel67-auxiliary.md) |
| diag-004-sampling-batch-minimal | diagnostic completed;formal score cause not established | sampler-fixed-probs-shape-row-history | [diag-004-sampling-batch-minimal.md](diag-004-sampling-batch-minimal.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| GPQA198-C64-defaults | B1-old-Attention | strict-match | 65.15151515151516 | percent | 129/198;threshold64;fresh controlled role;not restored source gate |
| GPQA198-C64-defaults | C1-current-Attention | strict-match | 60.1010101010101 | percent | 119/198;threshold64;valid failure,no gate |
| GPQA198-C64-defaults | R1-old-Attention | strict-match | 65.15151515151516 | percent | 129/198;threshold64;revert instance only |
| GPQA198-C64-defaults-D1-E1-factorial | D1 | strict-match | 64.14141414141415 | percent | 127/198;threshold64;only stopped measured instance gate |
| GPQA198-C64-defaults-D1-E1-factorial | E1 | strict-match | 65.15151515151516 | percent | 129/198;threshold64;only stopped measured instance gate |
| GPQA198-C64-defaults-E67-newGPU | E67 | strict-match | 61.61616161616162 | percent | 122/198;threshold64;valid failure,no gate;different GPU pair/host placement |

<!-- e2e:summary:end -->
