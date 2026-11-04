# 20260913-max-batched-tokens-24576 中间 token-budget

- 状态：`failed`
- 分类：`framework`
- 目标场景：多 workload，`max_num_seqs=32`
- 目标阶段：Prefill / Mixed
- 依赖：vLLM scheduler

## 优化方向与瓶颈依据

在 16384 与 32768 之间测试 24576，判断能否避免 32768 的稳定性和长输出回退。

## 优化内容与适用边界

单变量把 `max_num_batched_tokens` 调整为 24576；其他服务参数不变。

## 正确性与路径命中

两个 workload 完成可用对照，请求正常返回。

## 性能效果

P4096/D128/C32 从 234.463 提升至 236.515 tok/s（+0.875%）；
P1024/D512/C32 从 723.850 降至 719.229 tok/s（-0.638%）。

## 决定、风险与回退

长输出 workload 回退且另一场景收益不足，决定拒绝并恢复 16384。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/max-batched-tokens-24576`
- comparison SHA-256：`05b6c72d3a43bc7140793c8c95345c83a20fa509e939a50cfd9b5b0c8b70d251`

