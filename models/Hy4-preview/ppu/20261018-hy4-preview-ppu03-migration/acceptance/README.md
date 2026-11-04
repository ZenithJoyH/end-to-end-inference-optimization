# HY4 / PPU-03：完整精度通过，性能未验收

完整198题GPQA C64已完成，strict-match **183/198=92.4242%**，高于预冻结87%阈值。原参数、官方原runner、独立UUID和数据指纹未改变；396样本行对应198题×2filters，每题strict/ flexible各一次。前后服务、完整四包/仓源码、131权重文件身份清单、tokenizer和启动配置一致，acceptance issue/check通过，42文件/28141872字节原生证据已SHA备份。heartbeat hy4-ppu-03已PAUSED。

当前结论见[acc006](../optimize/acc-006.md)。以下包含历史记录，当前状态以本节和原生gate为准。

<!-- e2e:summary:start -->

- 案例：20261018-hy4-preview-ppu03-migration
- 当前状态：env031_acc006_full198_accuracy_passed
- 当前候选：env031-FGV45e14232-original2048
- 下一步：User-requested accuracy complete; retain2048, no new performance/code changes; gate invalidated by identity/config change

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

env030已用一文件最小修复解决当前PPU上FULL_AND_PIECEWISE短输入答非所问：BF16 indexer缺失splitting_ops边界，捕获dummy metadata=None后replay跳过真实索引/cache写入。只在该indexer构造处幂等补边界，计算/dispatch不变。两个gems-opt、vLLM、权重和tokenizer均未改；未开始评测，旧acc005保持取消、heartbeat暂停。

见[env030验证](../optimize/env-030.md)。

2026-10-20 env031：已将原 hy4-preview 安装 FGV 更新到官方 main@45e14232，Plugin BF16 paged logits 改从 FGV 导入；FG3ba1d1d9不变。14项算子测试和4组各2次动态graph replay通过。当前 HY4 未重启，仍加载env030/旧FGV，新磁盘组合整模型回归和正式精度尚未执行。见[env031](../optimize/env-031.md)。
