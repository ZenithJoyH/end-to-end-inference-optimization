# 20260912-max-batched-tokens-16384 提高批处理 token 上限

- 状态：`retained`
- 分类：`framework`
- 目标场景：多种有限批 workload
- 目标阶段：Prefill / Mixed
- 依赖：vLLM scheduler

## 优化方向与瓶颈依据

原批处理 token 上限限制 Prefill admission 和混合批组织。目标是在不改变请求语义的
前提下扩大每轮可调度 token 数。

## 优化内容与适用边界

将 `max_num_batched_tokens` 固定为 16384；其他并发、graph 与模型参数保持不变。

## 正确性与路径命中

三个诊断 workload 均成功完成，服务和 graph 正常。前缀缓存保持关闭。

## 性能效果

| Workload | Baseline | Candidate | 吞吐变化 |
|---|---:|---:|---:|
| P4096/D128/C32 | 225.340 tok/s | 234.156 tok/s | +3.912% |
| P1024/D512/C32 | 703.680 tok/s | 711.567 tok/s | +1.121% |
| P4096/D512/C8 | 236.130 tok/s | 239.548 tok/s | +1.447% |

## 决定、风险与回退

决定保留，并写入当前启动脚本。更大的 24576/32768 在长输出或稳定性上失败；回退
为恢复旧 token 上限。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/max-batched-tokens-16384`
- comparison SHA-256：`530d585cba8ef94cb04903ceb395d29efde537eef1d8097e1e2eb1a42c16d6cc`

