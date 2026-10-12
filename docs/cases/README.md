# 性能优化案例索引

本目录保存已经实际执行的端到端推理优化案例。案例可以成功、失败、回退或被阻塞，但必须有真实目标、环境和证据。

## 索引

| 案例 ID | 模型 | 平台/硬件 | 引擎 | Workload | 瓶颈 | 主要改动 | 结果 | 证据等级 |
|---|---|---|---|---|---|---|---|---|
| [20261012-qwen36-27b-metax-flash-attention](20261012-qwen36-27b-metax-flash-attention/README.md) | Qwen3.6-27B BF16 GQA/linear hybrid | TP2 MetaX C550 / mx-59 | vLLM0.20.2 + Plugin + FlagGems-vllm | P1K→P4K→P16K→P32K，D1K/C64/N128；Decode算子诊断 | packed GQA6 Decode落入legacy | MetaX受保护SplitKV调度及partial独立strides | [当前状态](../../models/Qwen3.6-27B/metax/optimize/README.md)；未部署、未验收 | 算子A/B/revert reproduced；模型GPQA77.27%低于80%，精度定位中；端到端收益未知 |
| [20261010-minimax-m31-w8a8-ppu-tp8-e2e](20261010-minimax-m31-w8a8-ppu-tp8-e2e/README.md) | MiniMax-M3.1 W8A8 | TP8 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | PPU BF16 M8 A矩阵加载K地址缺位已确认 | 私有Plugin head tile16修复；用户TP8配置与原11exports不变 | [当前状态](../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md) | 完整198通过85.86%；P1K基线1968.23TPS；完整机制A/B/A验证；FW004已回退，性能未验收 |
| [20261008-minimax-m31-w8a8-ppu-e2e](20261008-minimax-m31-w8a8-ppu-e2e/README.md) | MiniMax-M3.1 W8A8 | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | C64超capture32回退NONE；动态shape编译关联慢预热 | capture64历史GPQA84.85%；Mixed图16rank/105+2及新GPQA85.86%通过 | [当前状态](../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md) | 旧P1K单实例10.510×，缺独立重复/回退；新组合收益未知，四场景未验收 |
| [20260921-minimax-m3-ppu-e2e](20260921-minimax-m3-ppu-e2e/README.md) | MiniMax-M3 BF16 MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P1K→P4K→P16K→P32K，D1K/C64/N128 | 待 Prefill/Decode/Mixed 定位 | 独立优化容器→框架工作点→算子 A/B | 环境门禁已过；待授权释放源服务的 16 张 PPU | `observation` |
| [20260919-qwen38-flash-next-ppu-e2e](20260919-qwen38-flash-next-ppu-e2e/README.md) | Qwen3.8-Flash-Next | PPU-ZW810E / PPU-01 | 版本见模型运行记录 | P1K→P4K→P16K→P32K，D1K/C64/N128 | QSA、MoE、GEMM、阶段干扰 | 调度、score 上界、算子 provider | 活跃；[当前状态与单点结果](../../models/Qwen3.8-Flash-Next/ppu/optimize/README.md)，历史 acc-011 精度通过但服务重启后待复测，op027 性能里程碑通过未部署 | 见各实验 |
| [20260914-hy4-preview-ppu-e2e](20260914-hy4-preview-ppu-e2e/README.md) | Hy4-preview W8A8 linear/MoE | TP16 PPU-ZW810E / PPU-07 | vLLM 0.24.0 + Plugin + FlagGems | P4096/D1024/C64/N128；缩减 profiling | sparse MLA、fused MoE、scaled MM、Indexer 同步与冷启动 | Plugin/FlagGems 算子与数据流特化，native router MM | 最新稳态 278.14 output tok/s；较前 checkpoint +22.10%；正式 A/B/revert 待补 | `reproduced` |
| [20260911-glm53-flash-ppu-e2e](20260911-glm53-flash-ppu-e2e/README.md) | GLM-5.3-Flash-BF16 | TP16 PPU-ZW810E / PPU-13 | vLLM 0.24.0 + Plugin + FlagGems | 正式矩阵与缩减探针见模型记录 | MoE、MLA、mHC、调度 | 框架与算子多轮优化 | 活跃；[当前状态与单点结果](../../models/GLM-5.3-Flash-BF16/ppu/optimize/README.md) | 见各实验 |
| [20260904-xingchen4-ppu-isolated-e2e](20260904-xingchen4-ppu-isolated-e2e/README.md) | XingChen4-29B-A4B BF16 | TP4 PPU-ZW810E / PPU-01 | vLLM 0.24.0 + Plugin + FlagGems | P1K/D1K/C64；P4K/D256/C64；P16K/D256/C32，各三轮 | MLA decode约60.6% GPU kernel时间 | operator/improve：H8的head tile64→16，限shape、可回退 | 保留：输出/总吞吐约+95.5%/+73.2%/+31.9%；GPQA按用户指示暂缓 | `reproduced` |
| [20260903-imported-deepseek-v4-flash-w8a8](20260903-imported-deepseek-v4-flash-w8a8/README.md) | DeepSeek-V4-Flash W8A8 | 8× MetaX C550 | vLLM 0.20.2 + Plugin-FL + FlagGems | P1K/P4K, D1K, C64 | Indexer、Sparse MLA、cache copy、调度 | graph-safe/fusion/shape specialization | 原文最终组合显著提升；本项目未复测 | `observation` |
| [20260903-imported-glm-5-2-w8a8](20260903-imported-glm-5-2-w8a8/README.md) | GLM-5.2 W8A8 | TP16 MetaX | vLLM + Plugin-FL + FlagGems/MCTlass | P1K/P4K | Indexer、MoE、Sparse MLA、采样、KV 抢占 | 分阶段 backend、精确算法、head packing、调度 | 原文持续演进；本项目未复测 | `observation` |
| [20260903-imported-qwen3-6-moe](20260903-imported-qwen3-6-moe/README.md) | Qwen3.6-35B-A3B MoE BF16 | Hygon BW gfx936 | vLLM + Plugin-FL + FlagGems/ROCm | P1K/D256/C64 | MoE、DeltaRule、通信 | MoE 分阶段配置与 grouped-GEMM 原型 | 无最终 E2E 验收 | `observation` |

20260904 XingChen4案例为本项目实际执行；其他标记imported的条目为用户历史案例资料导入，不等同于当前项目重新执行。原始性能数字与结论需回到各案例的环境和版本解释。

## 命名

案例目录使用：

```text
YYYYMMDD-<model>-<platform>-<short-objective>
```

目录中的 `README.md` 从 [TEMPLATE.md](TEMPLATE.md) 初始化。模型/平台 `optimize/` 只保存
`state.yml`、多轮 README 和单点 Markdown；案例目录只保留少量可复用结论与链接。
执行配置、命令、补丁和逐轮原始结果保存在外部 case 目录，记录绝对路径与 SHA。
活跃案例的过程文件必须先核验外部副本及引用再移除，不能因精简而丢失唯一证据。
索引不复制活跃案例的瞬时进度，以模型 `state.yml` 和 README 为当前事实入口。

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
