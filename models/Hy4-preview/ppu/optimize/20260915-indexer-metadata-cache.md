# 20260915-indexer-metadata-cache：Indexer host metadata 缓存

- experiment-id：`20260915-indexer-metadata-cache`
- 分类：`framework`
- 状态：`retained_then_superseded_by_builder_shim`

## 方向与改动

将 `cu_seq_lens/cu_seqlen_ks/cu_seqlen_ke` 首次转为 host list 后缓存到同一
execution chunk，并用 `bisect_right` 在 host 侧派生 sequence id，使约 21 层
共享 metadata，保留旧路径作为兼容 fallback。

## 效果与正确性

21 层隔离复现的 `cudaMemcpyAsync` 从 `105` 降至 `3`（`-97.14%`），host
elapsed 从 `131.14 ms` 降至 `2.48 ms`；序列映射与原 `searchsorted` 一致，
Plugin 聚焦测试 `5/5` 通过。

## 决策与边界

当时保留，后续 metadata-builder shim 直接复用 vLLM CPU metadata，进一步
消除了目标路径 DtoH。隔离时间不作为端到端收益。

