# 20260915-post-combination-reprofile：P4K 热点迁移核验

- experiment-id：`20260915-post-combination-reprofile`
- 分类：`operator/diagnostic`
- 状态：`completed`
- 场景：`P4096/D128/C8/N8`

## 结果

16/16 rank trace 有效。`mm_kernel_general` 降为 0；Indexer
`cudaMemcpyAsync` wait 在 Prefill/Mixed/Decode 下降 `98.9%–99.9%`，证明
mm_out 路由和 metadata 优化真实命中。Split-K stage1/stage2 在 Decode 各命中
28,885 次；热点迁移到 SQ2048 generic sparse MLA，触发 BK32 实验。

## 决策与边界

该文档是多优化点的命中和热点迁移证据，不作为新的独立收益点，也不累计
profiler-on 时间。

