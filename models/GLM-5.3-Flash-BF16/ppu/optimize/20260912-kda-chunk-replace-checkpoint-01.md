# 20260912-kda-chunk-replace-checkpoint-01 Chunk KDA vendor 路由

- 状态：`retained`
- 分类：`operator/replace`
- 目标场景：长 Prefill 与 Mixed
- 目标阶段：Prefill / Mixed
- 依赖：FlagGems-vllm Chunk KDA、Plugin shape guard

## 优化方向与瓶颈依据

长输入下 Chunk KDA 是显著热点。目标是对 `max_query_len >= 512` 的支持范围使用
vendor 实现，同时保持短 query 和不支持 shape 的 fallback。

## 优化内容与适用边界

Plugin 依据 query length 和能力路由 `chunk_kda_with_safe_gate`；实现后来迁入
FlagGems-vllm，Plugin 只保留集成层。其他 shape 继续使用原路径。

## 正确性与路径命中

三个诊断 workload 全部完成，vendor 路径命中；graph 服务正常。该结果未替代最终
四场景验收。

## 性能效果

| Workload | Baseline | Candidate | 吞吐变化 |
|---|---:|---:|---:|
| P4096/D128/C32 | 181.555 tok/s | 224.851 tok/s | +23.847% |
| P1024/D512/C32 | 697.965 tok/s | 703.518 tok/s | +0.796% |
| P4096/D512/C8 | 219.862 tok/s | 235.379 tok/s | +7.057% |

## 决定、风险与回退

决定保留。收益强依赖 Prefill 长度；回退为取消 shape 路由并恢复原 KDA。Plugin
提交 `ef19fd9` 与迁移提交 `11b2285` 已推送。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/kda-chunk-replace/checkpoint-01`
- comparison SHA-256：`d9d6a3703c95fba70872a3b0587bfd72003a64afbc6ef7398f20cfc6636f6d05`

