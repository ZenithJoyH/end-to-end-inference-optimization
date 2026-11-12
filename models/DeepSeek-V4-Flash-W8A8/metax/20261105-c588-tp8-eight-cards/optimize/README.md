# 20261105-c588-tp8-eight-cards / optimize

<!-- e2e:summary:start -->

- 案例：20261105-c588-tp8-eight-cards
- 当前状态：delivered_for_manual_retest
- 当前候选：numa-eight-cards-001
- 下一步：User frees selected dies, restarts using modified script, verifies runtime affinity and compares steady-state E2E

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| numa-eight-cards-001 | incomplete | manual-e2e-retest | [numa-eight-cards-001.md](numa-eight-cards-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

已完成 TP8 跨 8 张物理卡的脚本交付，当前服务未重启。

| 实验 | 方向/阶段 | 主要变量 | 性能效果 | 正确性 | 决定 |
|---|---|---|---|---|---|
| [numa-eight-cards-001](numa-eight-cards-001.md) | framework；Prefill/Decode/Mixed | 8 物理卡各 1 die，并绑定对应 NUMA | 未测 | 设备元数据、CPU-only 绑定及参数保持通过；模型未测 | incomplete，待用户复测 |
