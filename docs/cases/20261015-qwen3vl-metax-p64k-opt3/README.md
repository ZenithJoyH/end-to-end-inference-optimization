# Qwen3-VL / MetaX / P64K opt3

2026-10-19 [pr029 收敛与正式评审](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/pr-029-moe-scope-cleanup.md)：PR943 Ready/head090ef1d；现有stage入口+完整shape/dtype/C550边界+正确pair内存估算，marker1处。55GPU/37参考/23capture+46replay、TP2双worker各>=16replay和11HTTP/C8、两套MetaX CI通过。8111/opt9已按原配置恢复，原运行源码/采样/gems-opt未回写。无新E2E/正式精度结论。

op024: [inline MoE tuning](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-024-moe-inline-config.md) saved; external JSON/helper and Plugin assets removed;393240CPU selector comparisons exact, kernels unchanged; no service restart.

Read-only [native GEMM2 feasibility](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/diag-023-native-moe-gemm2-feasibility.md): feasible via a scoped Plugin runtime adapter; no implementation/restart; current candidate unchanged.

op022: [direct FlagGems sampling adapter](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-022-sampling-direct-adapter.md) saved; sampling dispatch removed,18CPU routing checks passed; all other configs/libraries unchanged; no service restart.

op021: [sampling FlagGems dispatch](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-021-sampling-flaggems-dispatch.md) saved;20CPU contract checks passed, MoE/gems-opt/libraries unchanged; user restart and production graph/HTTP validation pending.

op020: [sampling integration](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-020-sampling-reconnect.md) ready in isolated8111; numeric/graph/actualHTTP library route passed, current worker shapes warmed; MoE/GEMM2/gems-opt/start script unchanged. E2E pending user, GPQA deferred.

2026-10-18当前：[op019大M G1对照](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-019-moe-gemm1-prefill-profile.md)：精确P64 B/C/R 71.944/76.840/72.080TPS，C/B+6.81%，漂移+0.19%，native passed，保留candidate。小M/G2/采样/gems-opt保持，数值/graph通过，正式精度及四场景验收未完成。

2026-10-17当前：[op018 GEMM1限域对照](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-018-moe-gemm1-decode-profile.md)：P4K B/C/R 899.66/940.41/898.50TPS，C/B+4.53%，漂移-0.13%，原生passed，保留candidate。G2固定、采样参考和gems-opt不变；数值/graph通过，P64/正式精度未验收。

2026-10-17当前：[op017完整G2参数对照](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/op-017-moe-gemm2-decode-profile.md)：P4K同配置B/C/R为865.38/898.64/871.04TPS（C/B+3.84%，漂移+0.65%），原生比较passed。28数值/8数学参考/独立及双worker生产graph/C8通过，保留candidate，8111/API995053。仅G2JSON变化，采样参考、gems-opt与其他配置保持；正式精度/P64/完整opt4恢复未验收。

2026-10-17最新：[diag016 opt7只读诊断](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/optimize/diag-016-opt7-stage1-gap.md)：P4K SUMMARY867.38TPS，比opt6低3.69%、比opt4低11.98%。当前源码/两份JSON与stage1交付一致，但只恢复stage，旧tile/warp/group及GEMM1/Prefill未恢复；实际新增范围M49..64，不能覆盖历史P64K/M8。P16仅两轮、P64未出结果；外部完整GEMM2对照JSON已准备未应用，用户测试和生产配置保持。

2026-10-17最新：op015 GEMM2 stage1配置已在独立容器8111生效：保持共享PR595表、GEMM1、采样回退、gems-opt/sort与其他配置，只在可选gemm2/阶段表调整M8..64（实际差异M49..64）。28组完整MoE数值与6组数学参考、独立graph和生产双worker各16replay、17个smoke/C8通过。当前API 932846，源8000不变。端到端收益未测，正式精度暂缓。

此前diag014分析（性能因果贡献仍待独立对照）：
2026-10-17最新：diag014 opt4→opt6差距分析：P4K原SUMMARY985.46→900.65TPS（−8.61%），P16K354.60→331.49（−6.52%）。旧精确M/GEMM2 stage1覆盖已被PR595完整最近M/双GEMM表替代，M64当前stage3且tile/group/warps改变；kernel计算体保持，完整因果贡献待MoE-only对照。当前用户opt6/8111/KV562992正在跑P64；本轮只读，未改源码、配置或重启。旧0.90审计对应09:37另一批数据，不能用于现在11:33的opt4。正式精度暂缓。

此前记录：
2026-10-17最新：diag013采样波动定位与对照：旧慢轮多出的121.28秒中，119.60秒与新M采样kernel编译重合；完整shape预热后P4K B参考/C库/R参考中位数为902.409/962.603/902.131 token/s，库相对参考+6.67%，原生比较passed，三组均无新增采样编译。保留同一R参考服务8111，MoE JSON/gems-opt/sort等配置不变，源码及源8000保护通过。正式精度暂缓，P16K/P64K未重测。

此前 op012 记录（已由本次新对照补充，原 incomplete 证据保持）：
2026-10-17最新：op012采样回退验证已按要求保留原参考调用，MoE JSON/gems-opt/sort不变。P4K两测量轮：库调用956.276/963.126，回退897.552/905.534；重新接入库后508.761/961.307出现明显波动，原生B/C/R比较判为incomplete，不能确认性能恢复。9项参数/mask回归及服务graph/双worker replay和源码保护通过；独立采样graph超时未确认，8111就绪，当前清单`manifests/op012-retained-service.json`。P16K/P64K未重测，精度暂缓。

此前记录：
最新maint011：完整审查tracked/untracked差异，只保留7个必要源码文件，集中JSON设备解析及路径缓存，删除重复入口代码和两个未用kernel参数。根init为HEAD，kernel计算体不变。133项外部pytest、MoE28组逐bit/数学参考/graph、9边界和服务17请求/双worker各16replay通过；8111就绪，当前清单maint011-service.json。Plugin/JSON/gems-opt/sort和源容器私有源码保持，无新正式精度或吞吐结论。public-flash共享副本已由用户主动清理（2026-10-16确认），无需恢复；任务未向该路径写入或恢复。详见模型记录中的maint011。

此前maint010：实际导入私有副本根目录新增`__all__`项已撤销，根文件恢复HEAD，ops/backend导出及Plugin显式导入保留。该步骤未重启8111，未回写共享副本。

最新maint009：库内新增采样`test_top_k_top_p.py`及`test_top_k_top_p_perf.py`已备份删除，运行代码和导出声明保持，显式导入/8111同进程就绪通过，无重启。下述库测试数字属于文件删除前的历史验证；当前资产清单见maint009、运行实现仍见op008。

当前Plugin保持`024plugin-opt/08da21cb3960`和PR595 JSON，独立MoE加载器/gems-opt/sort保留；库内新增MoE测试已全部备份删除。MetaX采样patch已按现有flag/policy接入库API，unsupported metadata走原参考，运行错误透出。49项原库、17项路由、47项实际hook数值/graph、9项边界通过；两worker启动预热确认库采样命中，服务capture/各16次replay及k20/p.8的smoke/C8通过。当前独立容器opt4/8111、memory0.91、KV562992，源8000未回写。下述性能为历史结果，当前完整吞吐未重测；详见模型记录maint007/op008。

同设备原 P65536/D1024/C64/N128 B/C/R 通过：68.772→76.279→68.657 token/s，+10.92%；唯一改动 gpu_memory_utilization0.90→0.91，maxseq64/graph64不变。完整预热+测量两轮抢占36/0/36。

保留全部FlagGems路径，PR595配置按原生最近M规则对两个GEMM生效。vLLM源码未改；验证期间外部FlagGems更新导致首轮身份检查失败，用户确认后保留新版重启重验，四仓库指纹稳定。独立容器qwen3vl-p64k-opt-20261015/GPU0,1/8111已留候选，源8000/GPU4,5未操作；来源、挂载、健康/graph、稳定身份及源保护复查通过。

cap8/graph8仅+0.3369%已回退；C8 milestone+13.6714%只作晋级依据，不与原目标相加。原目标是每role一测量轮的有限performance_only确认，正式精度按用户要求暂缓，不宣称长期稳定或四场景最终验收。

[模型及详细证据](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261015-qwen3vl-metax-p64k-opt3/README.md)。远端案例：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。
