# 性能优化案例索引

本目录保存已经实际执行的端到端推理优化案例。案例可以成功、失败、回退或被阻塞，但必须有真实目标、环境和证据。

## 索引

| 案例 ID | 模型 | 平台/硬件 | 引擎 | Workload | 瓶颈 | 主要改动 | 结果 | 证据等级 |
|---|---|---|---|---|---|---|---|---|
| [20260903-imported-deepseek-v4-flash-w8a8](20260903-imported-deepseek-v4-flash-w8a8/README.md) | DeepSeek-V4-Flash W8A8 | 8× MetaX C550 | vLLM 0.20.2 + Plugin-FL + FlagGems | P1K/P4K, D1K, C64 | Indexer、Sparse MLA、cache copy、调度 | graph-safe/fusion/shape specialization | 原文最终组合显著提升；本项目未复测 | `observation` |
| [20260903-imported-glm-5-2-w8a8](20260903-imported-glm-5-2-w8a8/README.md) | GLM-5.2 W8A8 | TP16 MetaX | vLLM + Plugin-FL + FlagGems/MCTlass | P1K/P4K | Indexer、MoE、Sparse MLA、采样、KV 抢占 | 分阶段 backend、精确算法、head packing、调度 | 原文持续演进；本项目未复测 | `observation` |
| [20260903-imported-qwen3-6-moe](20260903-imported-qwen3-6-moe/README.md) | Qwen3.6-35B-A3B MoE BF16 | Hygon BW gfx936 | vLLM + Plugin-FL + FlagGems/ROCm | P1K/D256/C64 | MoE、DeltaRule、通信 | MoE 分阶段配置与 grouped-GEMM 原型 | 无最终 E2E 验收 | `observation` |

以上为用户历史案例的资料导入，不等同于当前项目重新执行。原始性能数字与结论需回到各案例的环境和版本解释。

## 命名

案例目录使用：

```text
YYYYMMDD-<model>-<platform>-<short-objective>
```

目录中的 `README.md` 从 [TEMPLATE.md](TEMPLATE.md) 初始化。配置、命令、补丁和小型结果摘要放在同一案例目录；大体积原始结果只记录外部路径和校验信息。

## 检索标签

案例至少填写以下标签，便于后续复用：

- 模型结构：dense、MoE、MLA、GQA/MQA、mHC、multimodal 等。
- 阶段：cold-start、prefill、decode、mixed。
- 层级：request、scheduler、framework、memory、communication、operator。
- 平台、设备型号、设备数量和是否跨机。
- 引擎、Plugin、backend、dtype、量化和 graph/eager。
- 目标：TTFT、TPOT、ITL、throughput、memory、stability、cost。

## 纳入标准

- 必须来自实际执行或可复现失败。
- 必须记录 baseline、变量、验证和结论。
- 推测可以记录，但不能伪装为验证事实。
- 失败案例不删除；说明失败机制和后续是否值得重试。
- 同一案例的多个实验保留独立编号，不能只留下最优结果。
