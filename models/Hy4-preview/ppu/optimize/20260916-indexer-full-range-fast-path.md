# 20260916-indexer-full-range-fast-path：full-range 连续索引快路径

- experiment-id：`20260916-indexer-full-range-fast-path`
- 分类：`operator/improve`
- 状态：`retained`
- profile 场景：`P4096/D64/C16/N16`

## 方向与改动

当每行有效 key 数不超过 `topk` 时，直接生成 request-relative 连续索引，
跳过 key gather、QK、ReLU、reduce 与 Top-K。

## 效果与正确性

算子对照 `8.462x–12.665x`，有效前缀逐元素一致，graph capture/replay 通过。
reprofile 中 rank0 各减少 5,376 次 BMM、ReLU、reduce 和 Prefill Top-K，
Indexer wall `16441.335 -> 11975.788 ms`（`-27.16%`）。

## 决策与边界

保留。wall time 是 profiler 归因，不等价于父场景端到端收益。

