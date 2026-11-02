# MiniMax Flash1019 移除 top-k patch 精度复测

已完成：PPU-07最新容器、TP8物理0–7、Flash1019、FlagTree0.7.1.dev1+ppu3.6。用户移除top-k patch后，设备与模型回归通过；单次完整串行三项精度已独立核验。

| 数据集 | 正确/全量 | 分数 |
|---|---:|---:|
| GPQA Diamond | 171/198 | 86.36%（通过81%） |
| Math500 | 470/500 | 94.00% |
| ERQA | 265/400 | 66.25% |

GPQA原生gate复验PASS；Math500/ERQA无指定阈值，仅报告得分。ERQA400个item/evaluated ID均匹配冻结集合；NUL-only0、原始空响应0、30000触顶9。监控已PAUSED，模型服务保留，无性能或新优化，不把单次采样差异解释为单一改动因果。

[结构化状态](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-no-topk-patch-tp8-accuracy/optimize/state.yml) · [实验说明](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261021-no-topk-patch-tp8-accuracy/optimize/acc-001.md)

远端：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-no-topk-patch-tp8-accuracy`；原生路径/SHA见结构化状态。保留全部旧案例和旧分数，未改无关服务。
