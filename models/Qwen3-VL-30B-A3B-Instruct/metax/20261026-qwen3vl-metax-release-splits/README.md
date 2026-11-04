# 20261026-qwen3vl-metax-release-splits

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)

用户指定发布镜像tag202610191402（固定ID07cf737e）在mx-104独立容器 `qwen3vl-release-splits-mx104-20261026` 完成原始代码/default split0、prefix cache开启的完整评测：GPQA126/198=63.6364%，低于64分；ERQA163/400=40.75%，达到40分，0拒答。整体未满足GPQA阈值，无精度gate，无性能结论。见[完整精度实验](optimize/op-002-release-original-accuracy.md)。

原source容器 `qwen3vl-pr943-split1-mx104-20261023` 已恢复split1/prefixON，使用用户确认迁移的 `/data/models/Qwen3-VL-30B-A3B-Instruct`；当前源码/全部冻结env与argv（除授权路径变化）及graph16/C8/HTTP200均已复核，GPU4/5仅原服务占用。测试候选已停止，控制器退出，监控已删除。

此前[组件核验op-001](optimize/op-001-release-splits-audit.md)已证明原Plugin省略num_splits、native默认0，Python接口及native二进制与旧环境相同；24项参考和16capture/48replay通过，但同QKV的B1/B8在auto0下存在微小数值差异，fixed1对照逐位一致。这不等于kernel实现错误。

新旧split0的198条完整GPQA响应/逐题分数全部一致；这属于原始镜像同样存在低分的证据，根因尚未新增确认。权重配置/index/tokenizer/13分片名字大小与历史一致，实际safetensors头/index边界通过；无历史分片全字节SHA，不声称完整历史权重字节比对。所有原始证据留远端case，不复用旧gate。
