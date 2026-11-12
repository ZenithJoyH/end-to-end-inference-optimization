# 20261105-c588-numa-launch / baseline

<!-- e2e:summary:start -->

- 案例：20261105-c588-numa-launch
- 当前状态：configuration_recorded_only
- 当前候选：—
- 下一步：User restarts target service and runs E2E measurements

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

本轮只核验原启动配置，不运行模型；Prefill、Decode、Mixed 指标均未知。独立优化容器及镜像/挂载门禁不适用于这次仅修改用户指定脚本的任务，不能复用为后续正式测试已通过的门禁。

| 正式目标场景 | 状态 | 吞吐/TTFT/TPOT/E2E |
|---|---|---|
| p1024-d1024-c64-n128 | not_run | — |
| p4096-d1024-c64-n128 | not_run | — |
| p16384-d1024-c64-n128 | not_run | — |
| p32768-d1024-c64-n128 | not_run | — |
