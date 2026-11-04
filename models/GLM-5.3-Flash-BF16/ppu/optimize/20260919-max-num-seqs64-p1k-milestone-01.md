# 20260919-max-num-seqs64-p1k-milestone-01 提高并发序列上限

- 状态：`retained_by_user_objective`
- 分类：`framework`
- 目标场景：P1024/D1024/C64/N128
- 目标阶段：Mixed / Decode
- 依赖：vLLM scheduler 与 Decode graph

## 优化方向与瓶颈依据

用户将总输出吞吐设为主指标，允许以单请求 TPOT 为代价扩大 Decode batch。测试
`max_num_seqs=32 -> 64`。

## 优化内容与适用边界

仅改变 `max_num_seqs`，其余保留配置和 workload 不变。该变化把主要 Decode graph
从 cached32 改为 cached64，因此后续算子必须按 M64 重新分析。

## 正确性与路径命中

3 预热 + 3 measured 全部完成，768/768 请求成功，measured 吞吐离散 0.775%；
graph 服务健康。

## 性能效果

| 配置 | 输出吞吐 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| max32 reference | 1013.657 tok/s | 35.190 s | 31.281 ms |
| max64 candidate | 1277.797 tok/s | 6.918 s | 49.251 ms |

吞吐 +26.058%，TTFT 改善 80.342%，TPOT 回退 57.450%。按原综合延迟守护曾被
拒绝；用户随后明确吞吐为主指标并接受该取舍，因此最终保留。

## 决定、风险与回退

当前启动脚本固定 max64。风险是单请求 TPOT 增加；回退只需改回 max32，但会改变
Decode live M 和后续 exact-M64 优化的适用性。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p1024-d1024-c64-n128/candidates/max-num-seqs64-01`

