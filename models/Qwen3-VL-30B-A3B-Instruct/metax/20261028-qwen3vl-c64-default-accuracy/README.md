# opt14 C64 默认采样精度结果

2026-10-28已完成用户要求的GPQA和ERQA，各完整一次、64并发。保持mx-104用户服务qwen3vl-opt14/8030、GPU0,1/TP2、prefixON、模型默认T.7/P.8/K20/repetition1，FLA回退PR638/default split0，无服务重启或源码变更。

| 数据集 | 正确/总数 | 分数 | 阈值 | 结论 |
|---|---:|---:|---:|---|
| GPQA strict-match | 118/198 | 59.60 | 64 | 未通过，无gate |
| ERQA native及全400计错 | 181/400 | 45.25 | 40 | 通过，0原生拒答 |

原生覆盖/分数、数据与评分源码、全部实际默认采样请求及源前后身份均独立核验。用户原模型仍运行、models200；唯一评测控制器和自有adapter已退出，半小时监控已删除。整体正式精度未通过，GPQA原因未确认，不自动重跑或叠加优化。

[评测与诊断记录](optimize/acc-001-opt14-c64-default.md) · [结构化状态](optimize/state.yml) · [验收视图](acceptance/README.md)

远端：/public-flash/jinghao/qwen3-VL/20261028-qwen3vl-c64-default-accuracy。当前source未绑定可用GPQA gate，无本轮性能结论。
