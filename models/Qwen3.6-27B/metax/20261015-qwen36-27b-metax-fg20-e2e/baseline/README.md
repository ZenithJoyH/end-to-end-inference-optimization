# 原20项FlagGems基线

这些是原代码下已经保存的诊断milestone结果，parent为P1024/D1024/C64/N128，不能充当本轮OP003新基线或四场景验收。完整身份、原始runrecord与SHA见[state.yml](state.yml)。

| 原始阶段milestone | 吞吐 | 延迟代理 |
|---|---:|---:|
| Prefill P1024/D1/C64/N128 | total5693.825 token/s | meanTTFT8990.596ms |
| Decode P1024/D512/C64/N64 | output950.095 token/s | meanTPOT53.819ms |
| Mixed P1024/D256/C64/N128 | output704.178 token/s | meanTPOT68.211ms / p99ITL1485.689ms |

后续FW002r3新baseline PF/D各3measured有效（total5641.706/output940.144）；Mixed8warm/0measured，末3spread10.803%>10而失败，全部保留，无候选/回退对照。新双rank完整trace已复现FG full新小整数N在线调优造成约1.5秒preprocess，forward仍约1.5秒，具体见[FW002](../optimize/framework-002-mixed-batch-overlap.md)。

FW002r4新基线与回退已完成（共同OP003 full修复，独立18012，数据归optimize而非替换上表原代码基线）。PF total5694.1523→candidate5727.1996→revert5686.6342；D output940.8560→943.2032→939.4023；Mixed output700.4087→702.2617→698.3162 tok/s。Mixed元数据候选仅+0.2646%<2%，Decode因基线TTFTspread13.4452%保持incomplete；B/R各指标<1%，全部87轮保留。原四仓与原full/Plugin均已恢复，源18002精确954040/1792130229.17 ready/full20/.002/.02不变。详情与Decode重复JIT诊断见[FW002](../optimize/framework-002-mixed-batch-overlap.md)。

| 四个正式目标 | 状态 |
|---|---|
| P1024/D1024/C64/N128 | not_run |
| P4096/D1024/C64/N128 | not_run |
| P16384/D1024/C64/N128 | not_run |
| P32768/D1024/C64/N128 | not_run |

<!-- record-metrics:start -->
## 已记录指标（按 state.yml 展示）

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1-c64-n128-prefill | baseline | total_token_throughput | 5693.82512484262 | token/s | diagnostic milestone, parent p1024-d1024-c64-n128 |
| p1024-d1-c64-n128-prefill | baseline | mean_ttft | 8990.595569630386 | ms | diagnostic milestone, parent p1024-d1024-c64-n128 |
| p1024-d512-c64-n64-decode | baseline | output_throughput | 950.0954693293319 | token/s | diagnostic milestone, parent p1024-d1024-c64-n128 |
| p1024-d512-c64-n64-decode | baseline | mean_tpot | 53.81912709069242 | ms | diagnostic milestone, parent p1024-d1024-c64-n128 |
| p1024-d256-c64-n128-mixed | baseline | output_throughput | 704.1775316779153 | token/s | diagnostic milestone, parent p1024-d1024-c64-n128 |
| p1024-d256-c64-n128-mixed | baseline | mean_tpot | 68.21058591657693 | ms | diagnostic milestone, parent p1024-d1024-c64-n128 |
| p1024-d256-c64-n128-mixed | baseline | p99_itl | 1485.6886451225728 | ms | diagnostic milestone, parent p1024-d1024-c64-n128 |
<!-- record-metrics:end -->

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

| 场景 / 角色 | 已记录性能数值（附单位） | 证据范围 / 原字段 |
|---|---|---|
| p1024-d1-c64-n128-prefill / baseline | total_token_throughput = 5693.82512484262 token/s；mean_ttft = 8990.595569630386 ms | diagnostic milestone, parent p1024-d1024-c64-n128；`/metrics` |
| p1024-d512-c64-n64-decode / baseline | output_throughput = 950.0954693293319 token/s；mean_tpot = 53.81912709069242 ms | diagnostic milestone, parent p1024-d1024-c64-n128；`/metrics` |
| p1024-d256-c64-n128-mixed / baseline | output_throughput = 704.1775316779153 token/s；mean_tpot = 68.21058591657693 ms；p99_itl = 1485.6886451225728 ms | diagnostic milestone, parent p1024-d1024-c64-n128；`/metrics` |
<!-- baseline-record-review:end -->
