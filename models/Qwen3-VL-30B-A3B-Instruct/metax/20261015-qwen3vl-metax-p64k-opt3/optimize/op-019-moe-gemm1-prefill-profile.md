# op019：大 M GEMM1 与 opt4 对照

原生 targeted/performance_only 结果 **passed**。精确 P65536/D1024/C64/N128 输出吞吐 B/C/R **71.944/76.840/72.080 token/s**，C/B **+6.805%**，B/R 漂移 **+0.189%**。保留 **candidate**；当前 qwen3vl-p64k-opt-20261015 /8111 /API1095129。

## 用户范围与实现

用户要求保持当前小M优化、采样回退、gems-opt及GEMM2，先数值和graph，再完整P64端到端。只改Plugin根MoE JSON `vllm_fl/configs/moe/metax/E=128,N=384,device_name=metax.json`，M4096..8192为BM128/BN128/BK64/group1/warp8/stage1；旧表M4096为warp4/group1，M8192为warp4/group8。M4095/8193边界保护最近M；现有小M G1、全部GEMM2和其他M不变。G2整文件f392cfb568239f036bcc0ce16eadf5a6fa0b3ffbfb549310a916b248b3bfc7ca逐byte保持，没有库/worker/vLLM/环境开关改动，没有关闭FlagGems。

实际MetaX C550每rank w1=(128,768,2048)、w2=(128,2048,384)、topk8、BF16/TP2；硬件helper64KiB，旧/current有效PAIR_GATE_UP_DOT均False。中间M旧BM64与G2共享alignment不兼容，本轮不改变BM或另建对齐链路。适用范围沿原E/N/device配置匹配；同键其他模型/芯片/FP32未测。

## 正确性与生产graph

CPU真实选择器M0..65536×3种config dtype共589833项通过：所有G2、小M、范围外G1一致且BM共享对齐一致。40组BF16/FP16完整MoE前后逐bit一致；8数学参考最大绝对差0.001540660858，符合BF16 atol.004/rtol.016、FP16 atol.0005/rtol.003；18capture/36replay通过。

每个B/C/R及最终保留实例均做双worker真实M64/M8192的G1/G2命中、生产capture与各16replay、17smoke/C8及8192token输入探针；观察hook恢复后才测性能。KV容量562992，prefixcacheoff，argv与模型运行关键环境沿冻结基线；临时观察路径按实例分开，所有观察hook在测量前恢复。最小回归通过不代表GPQA；正式GPQA继续按用户要求暂缓。

合成路由完整MoE graph交错8blocks/10replay：M4096 3.833190→2.445030ms，M7393 5.969600→3.841485ms，M8192 6.755494→4.275482ms；M64/4095/8193为配置不变sentinel。微测不作为模型收益。

## 测量前冻结与端到端

当前op018保留组合是新P64场景入口baseline；没有将先前P4收益作为P64基线。每角色同一新graph服务先原生P64/C8/N8 1warm+2诊断轮、三轮TPSspread<=8%准入；随后完整原目标P65536/D1024/C64/N128 1声明预热+2测量全部保留。目标每轮timeout3600s，C8每轮600s。seed42、temperature.7、ignoreEOS、range0、finitebatch；原生维护版runner和比较器，未修改公共测量代码。

准入仅作准备，结果不冒充C64/N128：

- baseline: TPS [71.20491337173193, 71.27735832557089, 71.63903865040197], spread 0.609%.
- candidate: TPS [75.7750062891102, 75.80073275508875, 76.5432275362794], spread 1.013%.
- revert: TPS [70.69103821335149, 71.65072349489728, 71.68710390234133], spread 1.390%.

阈值在流量前冻结：TPS>=2%，P99TTFT/TPOT/ITL回退<=10%，测量轮间及B/R漂移<=8%，原始每轮128全成功且精确tokens。所有通过准入后的测量轮保留，没有事后删慢轮。

| 角色 | 两轮测量TPS | 中位数TPS | 轮间跨度/中位数 |
|---|---|---:|---:|
| baseline | 71.920, 71.967 | 71.944 | 0.065% |
| candidate | 76.813, 76.866 | 76.840 | 0.069% |
| revert | 72.052, 72.108 | 72.080 | 0.077% |

| 客户端指标ms | baseline | candidate | revert | C/B变化 |
|---|---:|---:|---:|---:|
| p99_ttft_ms | 862766.166 | 805797.562 | 860649.309 | -6.603% |
| p99_tpot_ms | 101.858 | 95.622 | 101.651 | -6.122% |
| p99_itl_ms | 1656.995 | 1545.773 | 1653.753 | -6.712% |

表中P99为原生比较器对各轮/进程P99的中位数，不是合并请求总体P99。TTFT/TPOT/ITL含网络、队列、调度及Mixed阶段干扰，不当作纯设备时间。完整目标计数增量包含1warm+2测量及客户端每轮探针，不推断单轮抢占；精确完成数/长度以原生JSON为准。

## 保留、回退和限制

当前保留candidate。回退本点只恢复外部baseline-gemm1.json到同一个Plugin根JSON，重启本任务独立服务并核验参数/graph/C8；不回退op018小M或op017 G2，不使用历史PID。镜像谱系和规范化挂载重新核验通过，最终仅上述根JSON允许变化；保护源8000四源码未变。

只证明当前组合下的P64增量结果；不把P4单点收益相加、不宣称完整opt4或四场景/正式模型精度验收。pr_readiness=experimental：标准配置数据，依赖现有阶段loader，无新增库代码；其他平台/匹配模型和正式GPQA未测。planning-op019-largeM-result-20261018已更新，继续优化应先看本组合P64阶段和真实shape证据，本轮不继续改其他配置。

完整远端根：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`；最终results/op019-final.json，性能results/op019-comparison.json和results/performance/op019-{baseline,candidate,revert}-01/run-record.json，准入同目录*-admission/run-record.json，数值results/op019-numerics.json，微测results/op019-microtiming.json，计数results/op019-*-target-counters.json。当前manifest：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/manifests/op019-retained-service.json`；准确SHA见state.yml。
