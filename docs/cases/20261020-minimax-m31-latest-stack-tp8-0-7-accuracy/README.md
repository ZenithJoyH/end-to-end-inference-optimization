# MiniMax-M3.1 Flash 最新栈 / PPU-07 前8卡全量精度

最新容器minimaxM3.1-opt-latest-20261020、review-001收敛代码、Flash1019权重，物理0–7/8045、TP8、prefixcache disabled。三项单次原生全量完成：GPQA166/198=83.84%（通过81%及原生gate）；Math500470/500=94.00%；ERQA244/400=61.00%。后两项没有指定阈值，只报告得分；不与旧preview/旧栈分数混用。

全量前56 INT8、9模型算子、34MoE融合、16视觉SDPA graph及105+2模型最小回归通过，FULL/PIECEWISE各7/7。终态按物理行与唯一doc_id核对198/500；Math500原生采样参数匹配冻结proof。ERQA实际400项与evaluated的400唯一ID完全匹配冻结dataset-proof，原生正确244和61%一致；NUL-only0、原始空响应0、30000触顶8。所有阶段和queue/advance退出码0，服务保留健康且空闲。

监控已PAUSED；无重跑、远端源码/服务改动、性能队列或自动优化恢复。原生gate/结果/样本/audit及SHA见[结构化事实](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-tp8-0-7-accuracy/optimize/state.yml)，方法、冻结契约、限制与终态见[精度实验](../../../models/MiniMax-M3.1-Flash-W8A8/ppu/20261020-latest-stack-tp8-0-7-accuracy/optimize/acc-001.md)。
