# 20260916-indexer-metadata-builder-shim：复用 vLLM CPU metadata

- experiment-id：`20260916-indexer-metadata-builder-shim`
- 分类：`framework`
- 状态：`retained`

## 方向与改动

Plugin 增加幂等 metadata-builder shim，直接从 vLLM 已有 CPU
`query_start_loc` 和 `seq_lens` 派生 Indexer host row ranges，旧 `.tolist()`
路径保留为兼容 fallback。

## 效果与正确性

重采样中 Indexer pageable DtoH 降为 0；Mixed `cudaMemcpyAsync` wait
`1774.774 -> 1.372 ms`（`-99.92%`），Decode `310.392 -> 4.120 ms`，Mixed
Indexer wall `-28.27%`。Plugin `8/8`、graph capture 和真实 replay 通过。

## 决策与边界

保留。profiler-on output throughput 仅作诊断，不记为正式收益。

