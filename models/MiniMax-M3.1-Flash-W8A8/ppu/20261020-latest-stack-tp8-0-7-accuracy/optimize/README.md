<!-- e2e:summary:start -->

- 案例：20261020-latest-stack-tp8-0-7-accuracy
- 当前状态：all_three_native_completed_verified
- 当前候选：minimaxM3.1-opt-latest-20261020
- 下一步：await user direction; monitor paused; model service retained; no automatic optimization/performance

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-001 | all_three_native_completed_verified | — | [acc-001.md](acc-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa_diamond_generative_cot | candidate | exact_match,strict-match | 0.8383838383838383 | fraction | formal198_unique_current_latest_first8 |
| math_500 | candidate | exact_match,none | 0.94 | fraction | native500_unique_score_only_current_latest_first8 |
| erqa | candidate | accuracy | 0.61 | fraction | native400_unique_score_only_current_latest_first8 |

<!-- e2e:summary:end -->
