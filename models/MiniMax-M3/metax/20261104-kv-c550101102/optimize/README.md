# 20261104-kv-c550101102 / optimize

<!-- e2e:summary:start -->

- 案例：20261104-kv-c550101102
- 当前状态：diagnostic_complete_services_released
- 当前候选：—
- 下一步：同机KV容量因果效应已验证；101/102服务与观察器均退出。后续历史N128贡献或C588模型级通信优化另需资源窗口。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| kv-001 | diagnostic hypothesis supported; low-KV not retained | — | [kv-001.md](kv-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p32768-d1024-c64-n4-kv-diagnostic | baseline | total_token_throughput | 2604.3343241474836 | tok/s | targeted finite-batch diagnostic only |
| p32768-d1024-c64-n4-kv-diagnostic | candidate | total_token_throughput | 1757.6888985455944 | tok/s | targeted finite-batch diagnostic only |
| p32768-d1024-c64-n4-kv-diagnostic | revert | total_token_throughput | 2600.779066390259 | tok/s | targeted finite-batch diagnostic only |
| p1024-d128-c64-n32-kv-sentinel | baseline | total_token_throughput | 2995.9015506430505 | tok/s | targeted finite-batch diagnostic only |
| p1024-d128-c64-n32-kv-sentinel | candidate | total_token_throughput | 3033.8889986439594 | tok/s | targeted finite-batch diagnostic only |
| p1024-d128-c64-n32-kv-sentinel | revert | total_token_throughput | 3010.9262954123915 | tok/s | targeted finite-batch diagnostic only |

<!-- e2e:summary:end -->
