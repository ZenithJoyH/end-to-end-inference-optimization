# Qwen3-VL / MetaX：PR977 最新上游验证

最新进展：[op-006](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/op-006-kvcache-split1-gpqa.md)已在独立`qwen3vl-pr977-20261022`的Plugin中固定kvcache `num_splits=1`，prefix cache开启，其余配置/采样/gems-opt/MoE不变。14项算子用例、12capture/48replay、两rank真实命中、服务capture+16replay与C8通过；原契约唯一一轮完整GPQA 131/198=66.16分，达到64分阈值。ERQA/性能未重测，生产9999未动，历史失败保留。

后续完整精度：此前PR943316f036独立环境（prefix cache开启）GPQA123/198=62.12<64，ERQA164/400=41.00>=40；完整证据有效，GPQA未达标，未回写生产或晋级性能。后续[同卡受控诊断](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/diag-004-gpqa-controlled.md)旧版125/124、新版128/125，未复现新版稳定退化；同seed并发全模型有波动，具体算子根因未隔离，原失败不覆盖。详见[acc-003](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/acc-003-pr943-gpqa-erqa.md)。

2026-10-22后续：[PR #943](https://github.com/flagos-ai/FlagGems-vllm/pull/943) 已基于最新上游刷新至 `316f036`，保留必需保护及调优，63项GPU用例、graph、TP2/C8与CI通过；两文件最小改动，正式待评审。生产未回写，未重测E2E。

冻结上游 main `bad340d`（含已合入的 #977），去掉本地 #943 MoE 改动后，当前 E128/H2048/I384/topk8 仍复现共享内存超限：BF16、FP16 的 M4096/M8192 均要求 98304 bytes，C550 上限 65536 bytes。

独立容器 `qwen3vl-pr977-20261022` 已通过镜像、挂载及原始源码一致性门禁。原版本和回退版本均通过 18/18 用例、14 次 capture、28 次变化输入 replay；最新上游通过 14/18，其余四项资源失败。候选 MoE 文件与上游原文一致。

本轮未推进端到端性能测试，也未回写或重启生产容器。原 `qwen3vl-p64k-opt-20261015` 的四仓库、模型、tokenizer、9999 服务保持不变，采样与 gems-opt 保留。

[Full record](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/op-001-upstream977-no943.md).
