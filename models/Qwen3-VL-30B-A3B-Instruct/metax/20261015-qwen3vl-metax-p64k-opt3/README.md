# Qwen3-VL / MetaX / P64K优化（opt3起点）

2026-10-22后续：[PR943最新上游刷新](../20261022-qwen3vl-metax-pr977/optimize/pr-002-refresh943-upstream977.md)已发布316f036，保留保护及调优、兼容977；新63GPU/TP2graph与CI通过。以下090ef1d记录为10月19日历史验证，不作新head证据。

2026-10-19：[PR943 收敛与正式评审](optimize/pr-029-moe-scope-cleanup.md)已完成，提交090ef1d。复用现有分阶段配置入口，限定C550/完整shape/半精度并排除量化键，修正shared-memory估算；marker只留1处兼容标记。55GPU用例/37参考/23capture+46replay、TP2双worker各>=16replay/11HTTP含C8及两套MetaX CI通过。8111/opt9已按原配置和源码状态恢复；原服务源码未回写，采样/gems-opt/其他配置不变。无新吞吐或完整精度结论。

op024: [inline MoE tuning](optimize/op-024-moe-inline-config.md) saved; external JSON/helper and Plugin assets removed;393240CPU selector comparisons exact, kernels unchanged; no service restart.

Read-only [native GEMM2 feasibility](optimize/diag-023-native-moe-gemm2-feasibility.md): feasible via a scoped Plugin runtime adapter; no implementation/restart; current candidate unchanged.

op022: [direct FlagGems sampling adapter](optimize/op-022-sampling-direct-adapter.md) saved; sampling dispatch removed,18CPU routing checks passed; all other configs/libraries unchanged; no service restart.

op021: [sampling FlagGems dispatch](optimize/op-021-sampling-flaggems-dispatch.md) saved;20CPU contract checks passed, MoE/gems-opt/libraries unchanged; user restart and production graph/HTTP validation pending.

op020: [sampling integration](optimize/op-020-sampling-reconnect.md) ready in isolated8111; numeric/graph/actualHTTP library route passed, current worker shapes warmed; MoE/GEMM2/gems-opt/start script unchanged. E2E pending user, GPQA deferred.

2026-10-18当前：[op019大M G1对照](optimize/op-019-moe-gemm1-prefill-profile.md)：精确P64 B/C/R 71.944/76.840/72.080TPS，C/B+6.81%，漂移+0.19%，native passed，保留candidate。小M/G2/采样/gems-opt保持，数值/graph通过，正式精度及四场景验收未完成。

2026-10-17当前：[op018 GEMM1限域对照](optimize/op-018-moe-gemm1-decode-profile.md)：P4K B/C/R 899.66/940.41/898.50TPS，C/B+4.53%，漂移-0.13%，原生passed，保留candidate。G2固定、采样参考和gems-opt不变；数值/graph通过，P64/正式精度未验收。

2026-10-17当前：[op017完整G2参数对照](optimize/op-017-moe-gemm2-decode-profile.md)：P4K同配置B/C/R为865.38/898.64/871.04TPS（C/B+3.84%，漂移+0.65%），原生比较passed。28数值/8数学参考/独立及双worker生产graph/C8通过，保留candidate，8111/API995053。仅G2JSON变化，采样参考、gems-opt与其他配置保持；正式精度/P64/完整opt4恢复未验收。

2026-10-17最新：[diag016 opt7只读诊断](optimize/diag-016-opt7-stage1-gap.md)：P4K SUMMARY867.38TPS，比opt6低3.69%、比opt4低11.98%。当前源码/两份JSON与stage1交付一致，但只恢复stage，旧tile/warp/group及GEMM1/Prefill未恢复；实际新增范围M49..64，不能覆盖历史P64K/M8。P16仅两轮、P64未出结果；外部完整GEMM2对照JSON已准备未应用，用户测试和生产配置保持。

2026-10-17最新：[op015 GEMM2 stage1配置](optimize/op-015-moe-gemm2-stage1-json.md)已在独立容器8111生效：保持共享PR595表、GEMM1、采样回退、gems-opt/sort与其他配置，只在可选gemm2/阶段表调整M8..64（实际差异M49..64）。28组完整MoE数值与6组数学参考、独立graph和生产双worker各16replay、17个smoke/C8通过。当前API 932846，源8000不变。端到端收益未测，正式精度暂缓。

此前diag014分析（性能因果贡献仍待独立对照）：
2026-10-17最新：[diag014 opt4→opt6差距分析](optimize/diag-014-opt4-opt6-gap.md)：P4K原SUMMARY985.46→900.65TPS（−8.61%），P16K354.60→331.49（−6.52%）。旧精确M/GEMM2 stage1覆盖已被PR595完整最近M/双GEMM表替代，M64当前stage3且tile/group/warps改变；kernel计算体保持，完整因果贡献待MoE-only对照。当前用户opt6/8111/KV562992正在跑P64；本轮只读，未改源码、配置或重启。旧0.90审计对应09:37另一批数据，不能用于现在11:33的opt4。正式精度暂缓。

此前记录：
2026-10-17最新：[diag013采样波动定位与对照](optimize/diag-013-sampling-variance.md)：旧慢轮多出的121.28秒中，119.60秒与新M采样kernel编译重合；完整shape预热后P4K B参考/C库/R参考中位数为902.409/962.603/902.131 token/s，库相对参考+6.67%，原生比较passed，三组均无新增采样编译。保留同一R参考服务8111，MoE JSON/gems-opt/sort等配置不变，源码及源8000保护通过。正式精度暂缓，P16K/P64K未重测。

此前 op012 记录（已由本次新对照补充，原 incomplete 证据保持）：
2026-10-17最新：[op012采样回退验证](optimize/op-012-sampling-call-rollback.md)已按要求保留原参考调用，MoE JSON/gems-opt/sort不变。P4K两测量轮：库调用956.276/963.126，回退897.552/905.534；重新接入库后508.761/961.307出现明显波动，原生B/C/R比较判为incomplete，不能确认性能恢复。9项参数/mask回归及服务graph/双worker replay和源码保护通过；独立采样graph超时未确认，8111就绪，当前清单`manifests/op012-retained-service.json`。P16K/P64K未重测，精度暂缓。

此前记录：
2026-10-16最新交付：[maint011完整审查及收敛](optimize/maint-011-flaggems-vllm-convergence.md)已完成。实际导入的私有FlagGems-vllm相对HEAD保留7个必要源码文件，集中JSON设备解析/文件缓存，去掉重复入口代码及两个未使用kernel参数；根init保持HEAD，MoE/采样计算体未变。133项外部pytest、28组MoE逐bit与数学参考/graph、9边界以及TP2服务17请求/双worker各16replay通过，8111就绪。Plugin、MoE JSON、gems-opt/sort和源容器私有源码保持；当前清单`manifests/maint011-service.json`。共享`/public-flash/jinghao/qwen3-VL/FlagGems-vllm`已由用户主动清理（2026-10-16确认），无需恢复；本次只写独立容器`/workspace/FlagGems-vllm`六个文件。无新正式精度或吞吐结果。

以下为此前步骤及其历史证据：[新增MoE测试已删除](optimize/maint-007-remove-added-moe-tests.md)，[Plugin采样已接入库API](optimize/op-008-plugin-topk-topp-integration.md)。独立容器`qwen3vl-p64k-opt-20261015`复用MetaX patch和已有flag/policy调用FlagGems-vllm top-k/top-p，unsupported metadata保留原参考，编译/运行错误透出。op008时49项原库测试、17项路由、47项实际hook数值/graph、9项边界和TP2服务回归通过，两个worker启动预热均确认库采样命中。原argv/memory0.91/maxseq64/graph64保持，实际KV562992。

[独立MoE JSON加载器](optimize/op-006-independent-moe-json-loader.md)、Plugin内PR595 JSON/目录变量、`024plugin-opt/08da21cb3960`、`gems-opt/c3c5f5ab2`及sort int32均保持。原22项MoE配置测试已按用户要求移除，历史验证和外部证据保留，不重新添加MoE测试。

随后[maint009](optimize/maint-009-remove-sampling-test-perf.md)按用户要求删除库内新增采样test/perf两文件；原`__all__`及其新增API条目保留，运行代码未变。显式导入和同一8111进程readiness通过，无重启。该步骤资产清单为`manifests/maint009-service.json`，运行实现仍为op008；前述49项库测试为删除前历史验证。

此前[maint010](optimize/maint-010-root-export-cleanup.md)撤销实际导入副本根目录`__all__`中的新增API项，根文件已恢复HEAD；ops/backend绑定保留，Plugin显式导入仍正常，该步骤未重启8111。用户所指public-flash是另一副本，该步骤未回写。当时清单为`manifests/maint010-service.json`。

此前完成[MoE配置迁入Plugin及环境变量入口](optimize/op-003-moe-config-plugin.md)和[Plugin分支切换](optimize/maint-004-plugin-024plugin-opt.md)，其57项精确M/GEMM2配置已被PR595完整表替代。Plugin MoE测试按用户要求保持删除。以下吞吐数字属于配置迁移前源码身份，新身份未重测完整P64K；该步骤的8111服务身份记录在`manifests/op008-service.json`，源8000服务未回写。

同设备原 P65536/D1024/C64/N128 B/C/R 通过：68.772→76.279→68.657 token/s，+10.92%；唯一改动 gpu_memory_utilization0.90→0.91，maxseq64/graph64不变。完整预热+测量两轮抢占36/0/36。

全部FlagGems选择保持；本轮改Plugin/FlagGems-vllm配置入口、JSON和启动脚本export，vLLM源码未改。验证期间检测到用户更新FlagGems，按其确认保留新版本并重启重验；新一轮四仓库指纹稳定。候选保留于独立容器qwen3vl-p64k-opt-20261015、GPU0/1、8111，源8000/GPU4,5未修改或重启。当前配置数值与覆盖范围有意变化，不能复用历史性能收益结论。

此前 fw002 的历史测量是targeted/performance_only：每role一个完整测量轮及一个完整预热轮，另有重复C8生命周期验证；不宣称长期方差、正式精度或原四场景最终验收。用户已明确暂缓GPQA。

[瓶颈诊断](optimize/diag-001-p64k-phase-kv.md)、[已回退的并发限制](optimize/fw-001-p64k-admission.md)、[保留候选与原生证据](optimize/fw-002-p64k-kv-budget.md)。远端案例：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)
