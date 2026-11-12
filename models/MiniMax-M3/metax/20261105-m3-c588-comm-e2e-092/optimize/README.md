# 20261105-m3-c588-comm-e2e-092 / optimize

<!-- e2e:summary:start -->

- 案例：20261105-m3-c588-comm-e2e-092
- 当前状态：64k-regression-investigated
- 当前候选：comm-e2e-001
- 下一步：64K同条件短探针及多rank trace拆分通信贡献，再单独评估通道4→8、buffer1MiB。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| comm-e2e-001 | reverted | 32K target, 1K guard | [comm-e2e-001.md](comm-e2e-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p32768-d1024-c64-n128 | baseline | total_token_throughput | 2292.189 | tok/s | targeted-performance-only |
| p1024-d1024-c64-n128 | baseline | total_token_throughput | 1245.4342 | tok/s | targeted-performance-only |
| p32768-d1024-c64-n128 | candidate | total_token_throughput | 2506.2856 | tok/s | targeted-performance-only |
| p1024-d1024-c64-n128 | candidate | total_token_throughput | 1575.7647 | tok/s | targeted-performance-only |
| p32768-d1024-c64-n128 | revert | total_token_throughput | 2301.5203 | tok/s | targeted-performance-only |
| p1024-d1024-c64-n128 | revert | total_token_throughput | 1342.1067 | tok/s | targeted-performance-only |

<!-- e2e:summary:end -->
