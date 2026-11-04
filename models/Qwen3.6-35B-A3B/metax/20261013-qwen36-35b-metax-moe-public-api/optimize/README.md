# 20261013-qwen36-35b-metax-moe-public-api / optimize

<!-- e2e:summary:start -->

- 案例：20261013-qwen36-35b-metax-moe-public-api
- 当前状态：retained
- 当前候选：op-002-moe-unified-call
- 下一步：端到端收益未证实；先冻结同配置 P4K A/B/A（双方保留 buffer），P1K 为哨兵，定位中途慢轮。当前源码仅保留为调用维护性重构。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-002-moe-unified-call | retained | p4096-d1024-c64-n128 | [op-002-moe-unified-call.md](op-002-moe-unified-call.md) |
| op-001-moe-public-api | superseded | p4096-d1024-c64-n128 | [op-001-moe-public-api.md](op-001-moe-public-api.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| moe-e256-h2048-n256-top8-m1 | baseline | operator_graph_latency | 0.03853598358810589 | ms | operator_only |
| moe-e256-h2048-n256-top8-m1 | candidate | operator_graph_latency | 0.03850566265629787 | ms | operator_only |
| moe-e256-h2048-n256-top8-m17 | baseline | operator_graph_latency | 0.2525932087617762 | ms | operator_only |
| moe-e256-h2048-n256-top8-m17 | candidate | operator_graph_latency | 0.25221826069390596 | ms | operator_only |
| moe-e256-h2048-n256-top8-m64 | baseline | operator_graph_latency | 0.4868115941318897 | ms | operator_only |
| moe-e256-h2048-n256-top8-m64 | candidate | operator_graph_latency | 0.4863590989157418 | ms | operator_only |
| moe-e256-h2048-n256-top8-m512 | baseline | operator_graph_latency | 0.6575337521315832 | ms | operator_only |
| moe-e256-h2048-n256-top8-m512 | candidate | operator_graph_latency | 0.6573786604295083 | ms | operator_only |
| moe-e256-h2048-n256-top8-m2048 | baseline | operator_graph_latency | 1.2695451819378398 | ms | operator_only |
| moe-e256-h2048-n256-top8-m2048 | candidate | operator_graph_latency | 1.2677724289791779 | ms | operator_only |
| moe-e256-h2048-n256-top8-m4096 | baseline | operator_graph_latency | 2.3448664347330728 | ms | operator_only |
| moe-e256-h2048-n256-top8-m4096 | candidate | operator_graph_latency | 2.343249245295449 | ms | operator_only |
| moe-e256-h2048-n256-top8-m8192 | baseline | operator_graph_latency | 5.364774703979492 | ms | operator_only |
| moe-e256-h2048-n256-top8-m8192 | candidate | operator_graph_latency | 5.371431662819603 | ms | operator_only |
| p1024-d1024-c64-n128 | baseline | output_throughput | 994.65 | token/s | user_csv_run2_run3_observation_uncontrolled |
| p1024-d1024-c64-n128 | baseline | batch_duration | 131.77 | s | user_csv_run2_run3_observation_uncontrolled |
| p4096-d1024-c64-n128 | baseline | output_throughput | 898.61 | token/s | user_csv_run2_run3_observation_uncontrolled |
| p4096-d1024-c64-n128 | baseline | batch_duration | 145.89 | s | user_csv_run2_run3_observation_uncontrolled |
| p1024-d1024-c64-n128 | candidate | output_throughput | 1140.97 | token/s | user_csv_run2_run3_observation_uncontrolled |
| p1024-d1024-c64-n128 | candidate | batch_duration | 114.88 | s | user_csv_run2_run3_observation_uncontrolled |
| p4096-d1024-c64-n128 | candidate | output_throughput | 719.87 | token/s | user_csv_run2_run3_observation_uncontrolled |
| p4096-d1024-c64-n128 | candidate | batch_duration | 196.59 | s | user_csv_run2_run3_observation_uncontrolled |

<!-- e2e:summary:end -->

用户补交端到端结果已在 [op-002 复盘](op-002-moe-unified-call.md) 和 `state.yml` 的 `planning_review` 中记录。P1K CSV SUMMARY 吞吐 +14.71%，P4K −19.89%；候选 P4K Run2 耗时 250.01s，对照 Run1 也有 289.95s 慢轮。全部逐轮结果均保留，稳态/回退证据不足，端到端收益与波动因果归属为 `incomplete`。

buffer 复用在本次重构之前已存在；25.79% 是移除既有复用的单 token 算子代价，不是重构带来的服务加速。当前 `retained` 表示代码仍在、算子回归通过；端到端性能晋级 pending。本轮只读检查和本地记录更新，没有修改远端代码、重启服务或运行新测试。
