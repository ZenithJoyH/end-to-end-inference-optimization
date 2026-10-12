# 20261012 Qwen3.6-27B / MetaX Flash Attention

目标为mx-59上的用户源容器qwen3.6-27B、权重/public-flash/models/Qwen3.6-27B。执行SOP0.40；范围diagnostic；候选正式精度failed（77.27%<80%），端到端性能incomplete。

用户授权远端目录：/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/。本地[基线](../../../models/Qwen3.6-27B/metax/baseline/README.md)、[优化总览](../../../models/Qwen3.6-27B/metax/optimize/README.md)、[单点实验](../../../models/Qwen3.6-27B/metax/optimize/op-001-metax-gqa-decode-scheduler.md)、[最终验收](../../../models/Qwen3.6-27B/metax/acceptance/README.md)为状态入口。

历史加入attention_backend后P4K/P16K/P64K吞吐退化43.62%/53.57%/72.77%，三轮中位数观察。当前代码路径已核验：Plugin AttentionFLBackend→flaggems_vllm.ops.attention→flash_api→MetaX scheduler。TP2每rank Q12/KV2/D256，16个full-attention层；48个linear-attention层不属于本Flash Attention改动。

独立优化容器从含用户未提交源码的适配状态快照复刻；Python源码指纹一致，mount_parity通过。源服务保留，使用空闲2/3卡产生新的可比基线，不能与历史0/1卡直接归因。

发现packed GQA6因query行数>4落入legacy；M16 SplitKV调度候选又暴露B1非连续输出stride误用于连续partial缓冲的问题。修复后78项原数值/graph测试通过，B64 KV1K/4K/16K完整算子调用约3.715/4.780/5.187×。证据等级reproduced仅限同进程算子A/B/revert；尚无端到端净收益结论。

下一步与完整原始证据在模型state.yml和远端case目录。未修改源服务、权重、tokenizer或vLLM；未提交、推送或创建PR。

当前原实现同契约GPQA精度二分在独立容器准备/执行；完整候选198题有效，未签发gate。长KV8项通过，附加M16严格容差失败的9组代表性输出与原实现bitwise相等，失败证据保留。端到端性能例外待用户明确答复；不可从算子收益宣称最终优化完成。
