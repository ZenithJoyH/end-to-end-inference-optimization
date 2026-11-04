# 20260919-max-batched-tokens-sweep：稳态 token-budget 扫描

- experiment-id：`20260919-max-batched-tokens-sweep`
- 分类：`framework`
- 状态：`rejected_keep_2048`
- 场景：`P4096/D128/C64/N64`

## 方向与结果

相对 2048，2304/2560/3072 的 output throughput 提升
`3.66%/5.30%/5.07%`，但 P99 ITL 回退 `5.89%/10.56%/23.20%`；4096 吞吐
仅 `+2.05%`，P99 ITL 回退 `47.97%`。

## 决策

没有候选同时满足 `>=3%` 吞吐与 `<=5%` P99 ITL 回退，启动配置保持 2048。
这只证明当前场景的已测集合，不宣称 2048 是全局最优。

