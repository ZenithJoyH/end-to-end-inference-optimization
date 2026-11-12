# 20261105-c588-numa-launch / optimize

<!-- e2e:summary:start -->

- 案例：20261105-c588-numa-launch
- 当前状态：superseded_by_topology_change
- 当前候选：—
- 下一步：See separate 20261105-c588-tp8-eight-cards case; former rollback refuses later script SHA

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| numa-launch-001 | superseded | manual-e2e-retest | [numa-launch-001.md](numa-launch-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

已交付按设备拓扑绑定 NUMA 的启动脚本，当前服务未重启。CPU-only 绑定和原参数保持验证通过，端到端收益待用户复测。

| ID | 方向/阶段 | 主要变量 | 性能效果 | 正确性 | 决定 |
|---|---|---|---|---|---|
| [numa-launch-001](numa-launch-001.md) | framework；Prefill/Decode/Mixed | CPU/内存 NUMA 绑定 | 未测 | CPU-only 路径通过；模型未测 | incomplete，交付待复测 |
