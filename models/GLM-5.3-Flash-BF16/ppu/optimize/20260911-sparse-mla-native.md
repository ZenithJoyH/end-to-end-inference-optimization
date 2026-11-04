# 20260911-sparse-mla-native vendor Sparse MLA 路由

- 状态：`retained`
- 分类：`operator/replace`
- 目标场景：长 Prefill 与 Mixed
- 目标阶段：Prefill / Mixed
- 依赖：Plugin capability fallback、vendor sparse attention

## 优化方向与瓶颈依据

稀疏 MLA 是长输入阶段热点。目标是优先命中平台 vendor 实现，同时对 RoPE0、
head size 512 等能力边界保留兼容 fallback。

## 优化内容与适用边界

Plugin 根据真实能力选择 vendor sparse attention；不支持的 shape/layout 回退原路径，
不通过模型路径或 served name 做选择。

## 正确性与路径命中

三个诊断 workload 均成功完成，后续 graph 服务继续使用该路由。正式精度 gate 未因
该改动下降；完整四场景验收尚未执行。

## 性能效果

| Workload | Baseline | Candidate | 吞吐变化 |
|---|---:|---:|---:|
| P4096/D128/C32 | 153.240 tok/s | 157.447 tok/s | +2.746% |
| P1024/D512/C32 | 680.440 tok/s | 692.800 tok/s | +1.816% |
| P4096/D512/C8 | 200.130 tok/s | 209.817 tok/s | +4.840% |

以上为诊断场景单点结果，不等同于最终四场景累计收益。

## 决定、风险与回退

决定保留。风险集中在未覆盖 shape 与 vendor 能力边界；回退为 Plugin 恢复原 sparse
MLA 路径。相关 Plugin 提交 `dbb0e67` 已推送。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/sparse-mla-native`

