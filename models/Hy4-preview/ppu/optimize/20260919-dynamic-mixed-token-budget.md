# 20260919-dynamic-mixed-token-budget：动态 Mixed token budget

- experiment-id：`20260919-dynamic-mixed-token-budget`
- 分类：`framework`
- 状态：`rejected_and_reverted`

## 方向与结果

尝试在 Plugin 中根据 Mixed 状态动态调整 token budget，但方案未进入 Hy4 实际
Scheduler 构造链，无法证明运行时命中。

## 决策

完整回退并通过语法和 diff 检查；不保留、不提交，也不产生性能结论。

