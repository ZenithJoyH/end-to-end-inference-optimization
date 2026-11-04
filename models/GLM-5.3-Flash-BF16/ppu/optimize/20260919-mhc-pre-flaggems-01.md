# 20260919-mhc-pre-flaggems-01 mHC pre backend 替换

- 状态：`reverted`
- 分类：`operator/replace`
- 目标场景：P1024/D1024/C64/N128
- 目标阶段：Decode
- 依赖：FlagGems mHC pre 与 thead blacklist

## 优化方向与瓶颈依据

post-small-M profile 中 mHC pre 是 Decode 后续热点，尝试从 reference/native 路径
切换到 FlagGems 实现。

## 优化内容与适用边界

临时从 `mhc_pre_with_norm` 黑名单释放，使 PPU BF16 `hc_mult=4/hidden=4096`
的 live shape 命中 FlagGems；其他配置不变。

## 正确性与路径命中

M=1/8/16/24/32/1024 均通过 eager、数值、graph capture 与两次 replay；16/16 rank
确认服务命中 `default.flagos`，候选完成 3+3 测量。

## 性能效果

算子中位加速 5.528×，但端到端：

| 角色 | 输出吞吐 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 1011.860 tok/s | 35.323 s | 31.376 ms |
| candidate | 1005.918 tok/s | 36.796 s | 31.948 ms |
| revert | 1013.657 tok/s | 35.190 s | 31.281 ms |

吞吐 -0.587%，TTFT/TPOT 分别回退 4.171%/1.821%。

## 决定、风险与回退

决定回退并恢复 `mhc_pre_with_norm` 黑名单。该反例说明 isolated kernel event
收益不能替代 graph 服务复测。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/mhc-analysis/pre-reference-vs-flaggems-01`
- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p1024-d1024-c64-n128/candidates/mhc-pre-flaggems-01`

