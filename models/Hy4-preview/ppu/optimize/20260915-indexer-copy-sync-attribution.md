# 20260915-indexer-copy-sync-attribution：Indexer 复制与同步拆分

- experiment-id：`20260915-indexer-copy-sync-attribution`
- 分类：`operator/diagnostic`
- 状态：`completed`
- 证据场景：`P4096/D128/C8/N8` profile

## 方向与结果

按互斥区间拆开 Indexer 本体、copy wrapper、`cudaMemcpyAsync` host wait、
显式同步和 device memcpy，避免重复累计 `to -> _to_copy -> copy_` 嵌套。
Mixed/Decode 中 host wait 分别占 Indexer wall 的 `43.34%/55.13%`，实际
device memcpy 仅 `6.650/14.828 ms`。

典型 `int32[2]` DtoH 只有 8 bytes、device 约 `0.6 us`，但 host API 阻塞
`50.412 ms`，根因指向 `.tolist()` 触发 stream drain，而非带宽不足。

## 决策与边界

诊断完成并转入 metadata cache/builder shim 实验。CPU wait 与异步 device work
可能重叠，不能把 inclusive 时间直接作为端到端可回收量。

