# Qwen3-VL / MetaX：发布镜像splits与完整精度核验

mx-104使用用户指定release镜像唯一已有tag202610191402，固定ID07cf737e，挂载与source模板一致，不导入旧仓库补丁。原Plugin省略num_splits，native默认0；原生24项参考/16capture/48replay通过，auto0同QKV跨batch存在微小数值差异，fixed1对照逐位一致，不能据此断言kernel计算错误。

按用户要求，保持原始代码/defaultsplit0/prefixON、此前相同参数，完整GPQA198和ERQA400各一次：GPQA126/198=63.6364%<64（有效失败、无gate），ERQA163/400=40.75%>=40（0拒答、通过）。新旧split0的198完整GPQA响应与逐题分数全一致，低分在原始发布镜像亦出现；并非单变量根因已确认，不叠加性能优化。

原source split1/prefixON已恢复，当前graph16/C8/source/全部冻结env+argv/HTTP200/GPU4,5归属复核passed，模型路径按人类确认改为/data/models；候选停止，控制器退出，监控删除。无性能测量，不转移旧gate给恢复实例。

[模型与详细实验记录](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261026-qwen3vl-metax-release-splits/README.md)。远端case `/public-flash/jinghao/qwen3-VL/20261026-qwen3vl-metax-release-splits`；最终证据/恢复审计SHA481e394a301832fe73c78ae5d91afeb50bbeb9e9572a65126644367903942606。权重历史仅配置/index/tokenizer哈希与分片名大小对齐，无旧分片全字节SHA。
