# 20260919-indexer-runtime-reprofile：Indexer 新路径运行时核验

- experiment-id：`20260919-indexer-runtime-reprofile`
- 分类：`operator/diagnostic`
- 状态：`completed`
- 场景：`P4096/D16/C16/N16`

## 结果

16/16 rank trace 和 16/16 请求有效。rank0 Indexer wall 在 Prefill/Mixed/
Decode-labeled 分别下降 `4.68%/28.54%/36.37%`；本体下降
`25.55%/36.75%`，旧翻译链和整缓存转换链均消失。相同 profiler-enabled
次轮 output throughput 提升 `5.22%`，只作诊断信号。

## 决策与边界

确认三个 Indexer 数据流候选真实命中并保留。profiler-on 时间不作为正式收益，
也不创建每个 trace 的独立文档。

