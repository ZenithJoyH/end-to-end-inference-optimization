# Qwen3-VL / MetaX / PR977 最新上游验证

最新进展：[op-006](optimize/op-006-kvcache-split1-gpqa.md)已在独立`qwen3vl-pr977-20261022`的Plugin中固定kvcache `num_splits=1`，prefix cache开启，其余配置/采样/gems-opt/MoE不变。14项算子用例、12capture/48replay、两rank真实命中、服务capture+16replay与C8通过；原契约唯一一轮完整GPQA 131/198=66.16分，达到64分阈值。ERQA/性能未重测，生产9999未动，历史失败保留。

此前PR943316f036独立环境的[完整精度评测](optimize/acc-003-pr943-gpqa-erqa.md)已完成（prefix cache开启）：GPQA123/198=62.12，低于64；ERQA164/400=41.00，通过40。证据有效，当前组合不能晋级。后续[受控诊断](optimize/diag-004-gpqa-controlled.md)四轮同卡旧版125/124、新版128/125，未复现新版稳定退化；同seed并发回答仍有波动，具体底层算子未隔离。原失败与原生产分数均保留。

2026-10-22后续：[PR #943](https://github.com/flagos-ai/FlagGems-vllm/pull/943) 已基于最新上游刷新至 `316f036`，保留必需保护及调优，63项GPU用例、graph、TP2/C8与CI通过；两文件最小改动，正式待评审。生产未回写，未重测E2E。

最新上游 `bad340d`（含 #977）尚不能替代本地 #943 的共享内存保护。BF16、FP16 的 M4096/M8192 均报要求 98304 bytes、硬件上限 65536 bytes。

| 版本 | GPU 用例通过 | capture / replay |
|---|---:|---:|
| 当前原版 | 18/18 | 14 / 28 |
| 最新上游、无本地943 | 14/18 | 10 / 20 |
| 回退原版 | 18/18 | 14 / 28 |

[实验、完整配置与原始证据](optimize/op-001-upstream977-no943.md)。候选在独立容器测试，未推进端到端性能比较；生产源码、服务、gems-opt 与采样配置均保持不变。
