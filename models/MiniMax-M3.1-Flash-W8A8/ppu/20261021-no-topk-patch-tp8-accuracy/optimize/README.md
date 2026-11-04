# 20261021-no-topk-patch-tp8-accuracy / optimize

<!-- e2e:summary:start -->

- 案例：20261021-no-topk-patch-tp8-accuracy
- 当前状态：all_three_native_completed_verified
- 当前候选：user-removed-topk-patch
- 下一步：await user direction; model service retained; no automatic optimization/performance

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-001 | accuracy-evaluation-completed; no performance decision | — | [acc-001.md](acc-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa_diamond_generative_cot | candidate | exact_match,strict-match | 0.8636363636363636 | fraction | fresh_full_native_198_current_no_topk_patch_TP8_first8 |
| math_500 | candidate | exact_match,none | 0.94 | fraction | fresh_full_native_500_current_no_topk_patch_TP8_first8 |
| erqa | candidate | accuracy | 0.6625 | fraction | fresh_full_native_400_current_no_topk_patch_TP8_first8 |

<!-- e2e:summary:end -->
