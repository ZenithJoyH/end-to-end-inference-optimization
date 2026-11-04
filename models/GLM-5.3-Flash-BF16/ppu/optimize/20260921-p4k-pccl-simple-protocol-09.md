# 20260921-p4k-pccl-simple-protocol-09 P4K collective 协议筛选

- 状态：`rejected`
- 分类：`framework`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed；Decode 作为守护项
- 当前保留组合：`max_num_seqs=64`、`max_num_batched_tokens=16384`

## 优化方向与瓶颈依据

P4K 的 16-rank profile 中，ring all-reduce 占 Prefill 设备活动 11.603%，占
Mixed 设备活动 6.003%。CPU 标记表明每个完整模型 step 有 91 次 all-reduce；
实际 BF16/TP16 payload 为：

| 阶段 | 张量 shape | 单次 payload | trace 调用数 |
|---|---:|---:|---:|
| Decode 守护项 | `(64,4096)` | 524,288 B | 102 |
| Prefill | `(4096,4096)` | 33,554,432 B | 91 |
| Mixed 尾批 | `(12769,4096)` | 104,603,648 B | 91 |
| Mixed 主批 | `(16384,4096)` | 134,217,728 B | 1365（15×91） |

现有 Decode 实验只证明 256 KiB 上强制 Ring/Tree 均显著慢于自动选择，不能外推到
P4K 的 32–128 MiB 大 payload。当前 trace 的大 payload 命中
`pcclKernel_AllReduce_RING_LL`，因此本实验只改变协议为 `Simple`，不强制算法。

## 冻结实验契约

使用容器 SDK 自带 `all_reduce_perf`，world size 16、BF16、单卡单 rank，分别对四个
精确 payload 比较：

- 基线：不设置 `NCCL_PROTO`，不设置 `NCCL_ALGO`；
- 候选：只设置 `NCCL_PROTO=Simple`，保持算法自动选择；
- 每个角色使用 3 个全新进程，`warmup=20`，`iters=50`；
- 同时记录 out-of-place 与 in-place 时间、`#wrong`、越界和退出码；
- 运行前确认模型服务停止且 16 卡没有目标模型进程。

## 晋级与停止条件

- 大 payload 的逐 shape 中位数至少提升 8%，且结果方向一致；
- 512 KiB Decode 守护项退化不得超过 10%；
- 全部进程退出 0，`#wrong=0`，无 OOB；
- 任一正确性失败、主 payload 无收益或收益明显被 Decode 退化抵消时停止，不启动模型服务；
- 通过以上筛选后才进入 graph/服务端 P4K 同配置 A/B/R，服务端最终仍以总输出吞吐为主指标。

## 性能与正确性结果

宿主机非交互首轮因没有加载容器 SDK 动态库而 24/24 以 rc=127 结束；该轮未执行
任何 collective，作为无效环境尝试保留在 `results/`，不计入性能结论。随后在目标
优化容器内以完全相同契约写入 `results-container-01/`，结果如下：

| payload | auto OOP 中位数 | Simple OOP 中位数 | auto/Simple | 结论 |
|---:|---:|---:|---:|---|
| 512 KiB | 77.27 μs | 255.8 μs | 0.3021× | Simple 慢 231.0% |
| 32 MiB | 297.8 μs | 399.7 μs | 0.7451× | Simple 慢 34.2% |
| 99.76 MiB | 735.2 μs | 1105.1 μs | 0.6653× | Simple 慢 50.3% |
| 128 MiB | 908.1 μs | 1422.9 μs | 0.6382× | Simple 慢 56.7% |

in-place 方向一致，auto/Simple 分别为 0.2999×、0.7343×、0.6600×、
0.6370×。有效轮 24/24 退出 0，所有 out-of-place/in-place `#wrong=0`，全部
OOB=0。

## 决定、风险与回退

候选在所有 P4K 精确 payload 上都显著退化，并严重破坏 Decode 守护项，故在算子
筛选层停止，不进入 graph 或服务 A/B/R。保留 PCCL 自动协议选择，不修改启动脚本、
服务环境或三个源码仓库；模型服务仍停止。

## 外部证据

- 根目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/collectives/pccl-simple-protocol-09/`
- 有效汇总 SHA-256：`057e3d05ec5d7a9c88398010d5f7e9e21b418f6350dc9dfe773c78226de40fb5`
- 有效执行脚本 SHA-256：`70dfd0a268c7cae987497f78ce02f89a0c611efbcb27c63148d29b8fff0c6d09`
- 契约 SHA-256：`69ab304950359bce7fef2c14a08095eac6bb577e2d3a81dffadc98e73946c6bc`
