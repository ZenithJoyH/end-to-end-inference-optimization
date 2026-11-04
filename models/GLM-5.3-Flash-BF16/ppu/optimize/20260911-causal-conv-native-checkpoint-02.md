# 20260911-causal-conv-native-checkpoint-02 Causal Conv 路由

- 状态：`retained`
- 分类：`operator/replace`
- 目标场景：Prefill/Mixed 多长度 workload
- 目标阶段：Prefill / Mixed
- 依赖：FlagGems-vllm causal-conv、Plugin shape 路由

## 优化方向与瓶颈依据

长 Prefill 下 causal-conv 的实现选择会影响端到端吞吐。目标是使用 thead 自适应
实现，并对不匹配 shape 保留原路径。

## 优化内容与适用边界

Plugin 对支持的长 Prefill shape 路由至 FlagGems-vllm causal-conv；实现后来从
Plugin 迁入 FlagGems-vllm，Plugin 只保留延迟导入与 dispatch。

## 正确性与路径命中

三个 workload 的候选请求均成功完成，路径命中与 fallback 已验证。该点不修改模型
语义；正式四场景精度/性能验收仍未完成。

## 性能效果

| Workload | Baseline | Candidate | 吞吐变化 |
|---|---:|---:|---:|
| P4096/D128/C32 | 157.442 tok/s | 181.045 tok/s | +14.991% |
| P1024/D512/C32 | 691.814 tok/s | 693.833 tok/s | +0.292% |
| P4096/D512/C8 | 207.609 tok/s | 219.260 tok/s | +5.612% |

## 决定、风险与回退

决定保留。收益随 prompt/输出组合变化，不能外推为固定比例。回退为禁用该 shape
路由并使用原 causal-conv；相关 Plugin 提交 `062c06f` 与迁移提交 `c8ce8b7` 已推送。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/causal-conv-native/checkpoint-02`
- comparison SHA-256：`7309338153a0e3e390e0d55a8d818106118e23e7831ddbe268415c9df082e510`

