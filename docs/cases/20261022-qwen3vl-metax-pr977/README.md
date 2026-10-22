# Qwen3-VL / MetaX：PR977 最新上游验证

冻结上游 main `bad340d`（含已合入的 #977），去掉本地 #943 MoE 改动后，当前 E128/H2048/I384/topk8 仍复现共享内存超限：BF16、FP16 的 M4096/M8192 均要求 98304 bytes，C550 上限 65536 bytes。

独立容器 `qwen3vl-pr977-20261022` 已通过镜像、挂载及原始源码一致性门禁。原版本和回退版本均通过 18/18 用例、14 次 capture、28 次变化输入 replay；最新上游通过 14/18，其余四项资源失败。候选 MoE 文件与上游原文一致。

本轮未推进端到端性能测试，也未回写或重启生产容器。原 `qwen3vl-p64k-opt-20261015` 的四仓库、模型、tokenizer、9999 服务保持不变，采样与 gems-opt 保留。

[Full record](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261022-qwen3vl-metax-pr977/optimize/op-001-upstream977-no943.md).
