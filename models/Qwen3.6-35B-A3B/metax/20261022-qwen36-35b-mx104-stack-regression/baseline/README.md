# 20261022-qwen36-35b-mx104-stack-regression / baseline

<!-- e2e:summary:start -->

- 案例：20261022-qwen36-35b-mx104-stack-regression
- 当前状态：historical_baseline_preserved_current_shortlist_NV_reference_passed
- 当前候选：release02-editable-sampler-fixed
- 下一步：Historical baselineC32160/candidate147 and incomplete performance remain unchanged. Separate current combined stack shortlist+MoE/GDN/FlagTree/Gems independently passed one original-native C64/full198158/198>=predeclared NV77.53 reference; no oldC32 causal resolution or new formal performance claim. See optimize/sampler-shortlist-001.md and acceptance current_formal_result. Task complete/monitor deleted; no automatic work.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1500.2496605103297 | token/s | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1941.0504114348441 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3740.857904739678 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 40.68825538566619 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 42.11236411701972 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_itl_ms | 40.68825552905164 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 40.25421550497413 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_e2el_ms | 43565.13567097136 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 45333.94738264382 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |

<!-- e2e:summary:end -->

完整精度结果：基线160/198（80.81%），候选147/198（74.24%），候选低13题/6.5657个百分点，未达到冻结门槛，未签发gate。按精度诊断Skill保留失败证据并进行同请求B/A/B对照，根因未定；正式性能保持阻塞。性能原基线11轮全部保留，P4K预热不稳、P1K部分延迟波动，整体incomplete。安装一致性与FGV实际内核覆盖分别记录，未宣布最终验收。详见[state.yml](state.yml)及[完整实验](../optimize/regression-001.md)。

<!-- baseline-record-review:start -->
## 正式目标覆盖与历史测量

本节是记录审查：原测量状态与角色保持不变，不是新评测回执。`incomplete` 表示此表未闭合正式基线证据；历史、缩减或有观察器的结果须按原范围解释。

| 正式目标 | 正式基线证据状态 | 已记录指标数 | 边界 |
|---|---|---:|---|
| p1024-d1024-c64-n128 | incomplete | 9 | 已列出原始观测；是否满足正式基线契约仍以原回执和稳态/身份条件为准。 |
| p4096-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p16384-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |
| p32768-d1024-c64-n128 | incomplete | 0 | 本阶段没有可归属到此正式场景的汇总数值；不推断从未运行。 |

数值见上方由 `state.yml/metrics` 生成的指标表；每条新增指标保留 source_pointer，外部原件按原 evidence 查阅。
<!-- baseline-record-review:end -->
