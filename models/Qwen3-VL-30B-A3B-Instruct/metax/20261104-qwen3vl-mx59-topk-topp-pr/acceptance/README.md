# 交付范围

[PR #1069](https://github.com/flagos-ai/FlagGems-vllm/pull/1069)单行性能优化已验证并更新，head ce0fedd。91设备测试、18次变化输入graph replay通过，20组对原PR位级一致；8个组件benchmark测项均超过0.9x Torch参考线，M1改善2.27–4.94x。

保持Draft待review；没有新模型精度或E2E验收。已按用户授权同步mx-59/qwen3vl，目标容器91项组件测试、20组位级对照和18算子+18实际调用graph replay通过，其他配置保持。当前无模型服务，不将组件结果称为模型验收。见[部署记录](../optimize/deploy-004-container-sync.md)及[优化记录](../optimize/op-002-single-batch-sort.md)。

前轮[MoE同步](../optimize/sync-006-moe-main.md)仅保留主线MetaX文件，通用INT8大stride失败已回滚。后续[fix-007](../optimize/fix-007-int8-large-stride.md)已修复该组件阻塞：通用MoE为main208ab加仅三个量化kernel的寻址归并补丁，62项MoE测试/42次变化输入graph回放，以及实际MetaX/PR1069护栏通过，独立最终审计通过。PR1069、111项真实配置和启动脚本保持；pytest报告的更新单独归档。当前容器仍不是整个仓库精确main，也没有新模型精度、全模型graph或E2E验收结论。
