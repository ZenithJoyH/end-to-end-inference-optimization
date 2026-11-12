# 20261105-c588-numa-launch

已按用户要求修改 `/data/jinghao/deepseek/start-model.sh`，使用 native vLLM 按可见设备绑定 NUMA。CPU-only 绑定及参数保持验证通过；当前服务未重启，等待用户启动与端到端复测，无性能验收结论。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)

2026-11-05 更新：本轮脚本已被独立的 [8 物理卡 TP8 配置](../20261105-c588-tp8-eight-cards/README.md) 替代；旧参数及交付验证作为历史记录保留，不能代表当前脚本。
