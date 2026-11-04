# 20260917-indexer-prefix-translate：消除 nonzero 同步链

- experiment-id：`20260917-indexer-prefix-translate`
- 分类：`operator/improve`
- 状态：`retained`
- 证据场景：`P4096/D128/C64/N64`

## 方向与改动

原单行布尔索引回写触发 `nonzero -> long to -> cudaStreamSynchronize`。在已
证明有效前缀长度等于 `selection_limit` 的分支中，改为
`indices[:selection_limit].add_(offset)` 并保留 `-1` tail。

## 效果与正确性

count 0/1/17/1024/2048 逐元素一致，graph replay 和 Plugin `14/14` 通过。
42 次链路微基准 `2.842 -> 0.360 ms`（`7.90x`），绝对节省约 `2.48 ms`。

## 决策与边界

低风险保留。trace 中 `2.489 s` 同步包含等待前置异步工作，不能将其视为可直接
回收的端到端时间。

