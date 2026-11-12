# Qwen3.6-35B：C588双die与C550双卡的收益差异

2026-11-04；policy0.44；diagnostic/observation。用户要求解释单die计算、显存带宽及同卡互连优势为何没有转化为明显端到端收益。当前只读复核指定历史CSV、项目模型/路径记录和两端硬件/配置，不启动服务、压测、profiler，不分配GPU或改源码。正式精度/性能验收不适用，算子/通信因果归因尚待证据。

范围：C588-5 `/data/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-opt4`，对照C550104 `/public-flash/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-retest`。本地C550数据按用户指定 `/Users/baai/Downloads/benchmark_results/qwen36-35b`；4K维持用户指定Run3，其余SUMMARY，C588使用指定SUMMARY，不把当前不同服务当历史绑定身份。

来源：[跨模型总览](../20261104-metax-models-c588-c550-overview/README.md)、[104 retest只读诊断](../../../models/Qwen3.6-35B-A3B/metax/20261022-qwen36-35b-mx104-stack-regression/optimize/perf-retest-20261103-001.md)、[模型结构/源码审计](../20261022-qwen36-35b-mx104-code-audit/README.md)。计算与读取工具临时目录/private/tmp/qwen35-c588-c550-analysis-20261104；原始CSV与日志保留用户位置。远端仅执行只读代码，未创建远端工作目录或模型产物。

## 结论与证据边界

已确认的现象是：C588平均TTFT较低，但五个长度下中位ITL均高3.39%–6.14%；P1K/P4K/P16K平均TPOT也较高。当前负载中，首token之前的收益没有成为持续的生成速度收益，端到端总吞吐落在C550的-3.22%至+1.54%。不能据此判断C588硬件没有优势，也不能宣布CPU、MCCL或某个算子已经构成主要根因。

优先需要验证的机制是小shape MoE/GDN与生成循环的执行效率，以及小消息集合通信的延迟和rank到达差异。原因：模型不是大矩阵吞吐测试；C550两卡已走MetaXLink；两端历史日志均显示custom all-reduce因缺少库而禁用。两端KV容量相同，未发现MiniMax式的容量落差。尚无同配置Qwen多rank设备trace或实际消息大小的通信A/B，因此下面的机制候选不标为因果confirmed。

## 历史性能重算

统一P1024/4096/16384/32768/65536、D1024、C64、N128，所选记录128请求成功且输入输出token数匹配。总吞吐单位tok/s。变化均为 `C588/C550-1`。CSV的SUMMARY是既有runner计分结果，不追认为预冻结稳态准入或正式验收。4K按用户指令选C550 Run3，不使用原4812.15的SUMMARY。

| 输入 | C550总吞吐 | C588总吞吐 | C588变化 | 平均TTFT秒 C550/C588 | 平均TPOT毫秒 C550/C588 | 中位ITL毫秒 C550/C588 |
|---|---:|---:|---:|---:|---:|---:|
| 1K | 3095.10 | 3037.22 | -1.87% | 2.009/1.894 | 39.39/40.27 | 37.42/38.75 |
| 4K | 6271.68 | 6069.86 | -3.22% | 4.598/4.344 | 46.35/48.30 | 38.04/39.78 |
| 16K | 10776.42 | 10656.35 | -1.11% | 17.064/16.389 | 83.44/85.17 | 43.03/45.67 |
| 32K | 10952.51 | 11111.39 | +1.45% | 61.901/60.746 | 120.23/118.23 | 49.00/50.66 |
| 64K | 9464.27 | 9609.97 | +1.54% | 237.977/233.817 | 154.74/152.38 | 44.96/46.84 |

TTFT、TPOT、ITL均为客户端代理，包含网络、排队、调度及Mixed阶段干扰，不能当纯设备Prefill/Decode耗时。32K/64K平均TPOT和P99 ITL较低，而中位ITL仍较高，说明分布和混合执行干扰存在差异，不能称为普通Decode步普遍更快。

以16K说明抵消的量级：TTFT减少0.67568秒；TPOT增加1.73毫秒，1023个生成间隔约增加1.76979秒；按固定输出长度估算，单请求平均完成延迟约增加1.09411秒。该估算使用CSV四舍五入后的均值，**不是完整批次耗时分解**，不能用它精确分摊总吞吐的因果贡献。

历史稳定性限制：C550 1K计分两轮3018.43/3171.76，约4.95%波动，超过两机SUMMARY差1.87%；4K计分两轮3352.62/6271.68，差异很大。保留用户选轮口径，但不把该口径直接升级为稳态硬件结论。

## 硬件、拓扑与软件事实

| 项目 | C550104 | C588-5 | 可作出的判断 |
|---|---|---|---|
| Qwen部署 | 单机两张C550，GPU4/5、TP2 | 单模组两个die，逻辑设备2/3、TP2 | 都是两个rank和两个逻辑设备，不能将整块双die卡的规格直接当每rank增幅 |
| 显存 | 64GB/卡，两卡128GB | 128GB/模组，双die各约64GB | 本模型使用的总显存容量接近 |
| 当前mx-smi芯片/显存类型 | MXC500、HBM2e | MXC500、HBM2e | 驱动报告同系列；不证明核心数、位宽或峰值相同 |
| 当前XCORE/MC时钟快照 | 1371/1800 MHz | 使用模组对应两die为1416/1800 MHz | XCORE快照差3.28%；不是历史满载频率，更不是算力或带宽比 |
| 拓扑 | GPU4↔5显示MX，NUMA1 | 物理板卡拓扑显示MX | C550已用MetaXLink；C588的物理板卡topo不能替代逻辑die内部链路测量 |
| 历史KV cache | 1,786,116 tokens | 1,786,116 tokens | 未发现跨机KV预算落差；长输入仍可能都受容量限制 |
| 历史集合通信日志 | nccl==2.16.5，custom allreduce缺库禁用 | nccl==2.16.5，custom allreduce缺库禁用 | 不是C588独有的缺库问题；日志通过pynccl打印，不能靠类名推断具体协议、链路利用率和独立耗时 |
| Host CPU/NUMA背景 | Xeon8460Y+，80核、2NUMA | Hygon7493，112核、8NUMA | 多个Host变量不一致，尚非仅换GPU的硬件A/B |

官方产品页同样将[C550](https://www.metax-tech.com/en/goods/prod.html?cid=107&id=35)和[C588](https://www.metax-tech.com/en/goods/prod.html?cid=107&id=67)的MetaXLink描述为8卡全互连最高896GB/s。该数字不是TP2点对点有效带宽，也不是C588内部die链路的延迟或带宽证据。官方这两页未给出可用于本对比的完整单die计算单元、位宽及统一精度峰值，不能推定单die性能有数倍差距。

本轮未核实到计算单元数量和显存总线位宽。SDK头文件注明多数MC runtime调用会隐式初始化，因此未调用mcInit、mcDeviceGetAttribute、torch或其他会创建GPU上下文的接口。sysfs只读检查没有返回相应核心/位宽字段。对“C588每die更快多少”保持未知，不把相同HBM类型/时钟当成相同有效带宽的证明。

历史两端主要配置均为BF16、TP2、MBT8192、maxseq64、util0.9、prefix关闭、FULL_DECODE_ONLY/capture64。C588镜像引用public release，104当前为inner release，同tag后缀但image ID不同；本轮没有完成两端所有运行文件的逐项一致性证明。104当前service.log已是11月4日opt5，不用于绑定11月3日retest CSV；C550通信/KV事实专门回读11月3日冻结service.log。

## 为什么更高的规格可能没有转化为收益

### 小shape计算与有效显存带宽

两端模型config SHA256均为 `93a4693fa9d8392fbfccd4b3c9873f4bfdcb14fdede978b123d07d19675efe99`。模型hidden2048、40层，其中30层linear/GDN、10层full attention；256专家、top8、MoE intermediate512，TP2时每rank中间维256。vocab248320。

在Decode batch64且路由均匀这一**说明性假设**下，每专家平均只有 `64*8/256=2` 个token；真实路由/步batch尚未采样。小M、窄中间维的专家GEMM、路由/重排、GDN递推等路径不能用大矩阵峰值TFLOPS推算。更高标称HBM带宽也只有在实际HBM传输占主导、访问模式及并行度能利用带宽时才转化为收益；本轮没有带宽计数器，不宣布内存已饱和或不是瓶颈。

### 通信延迟与消息大小

同模组双die仍有两个rank、两个逻辑设备以及跨rank同步，并不自动变为单设备执行。C550已走高速MetaXLink，两端custom all-reduce又都未生效，不能按“C550跨卡慢、C588同卡消除通信”推断。

仅以BF16 hidden2048的完整激活作为例子，B1–64消息体约4KiB–256KiB；这**不是从trace读出的实际集合通信大小**。该量级可能更敏感于launch/同步/协议延迟和另一rank何时到达，而非大消息峰值带宽。需按真实调用测延迟和关键路径，不能把通信kernel全部持续时间都当物理链路传输。若仅假设通信占关键路径10%，通信时间减半也只对应 `1/(0.9+0.1/2)=1.0526` 倍端到端；占比及加速均为举例，不是本模型测量值。

### CPU与设备空隙

已有同C588 P16K/D1/C1/N32的CPU活动记录中，Qwen35两rank约38.56%/37.16%，DeepSeek约74.24%/77.74%。它们只说明两个模型Host活动不同，不能从CPU利用率证明CPU型号解释当前Qwen差异，也不能证明GPU已经吃满。需要区分主线程执行、调度等待、rank偏斜和GPU上相邻kernel间空隙；DeepSeek的PMU结论不外推Qwen。

## 后续最小证伪路径

本轮只读诊断结束，不自动占用两机资源。若获得后续采集窗口，先冻结两端源/独立诊断容器的软件身份和shape，统一预热后开展：

1. **Decode专用多rank trace**：以相同活跃batch及上下文分布，记录每步关键路径、MoE/GDN/full attention/采样、设备空隙、collective开始与两rank到达时间。再看Prefill和Mixed；不能只加各rank各stream耗时。
2. **真实小消息集合通信**：对实际Qwen消息列表测TP2延迟分布，另测大消息仅作为带宽上界；区分C588内部die对和C5504/5，不拿8卡聚合带宽换算。
3. **实际shape算子**：对trace命中的MoE/GDN路径确认impl与调参配置，再做原shape对照；不以通用大GEMM结果代替。
4. **CPU假说**：仅当trace存在可归因Host空隙或rank发射偏斜，再设计绑核/NUMA等单变量验证，避免先凭CPU品牌下结论。所有候选收益回到无profiler相同Mixed workload测量。

## 复核与产物

- 当前连接按项目inventory与connectivity-check核验；只读对象为mx-104与mxC588-5，未访问103、101/102，未影响其他服务。
- C588历史启动脚本SHA256 `68deafdc54f83ba64ed824485af806c089936788723614628b10d847d83f4c73`；service.log读取前2MiB（实际全文件）SHA256 `9ba20bdaad3f27eab35e75533088726787d596e798c30430ad1f03bfdb0df4fd`。
- C550冻结服务日志 `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/performance-diagnosis/retest-20261103-001/service.log`，361578 bytes、SHA256 `b83d77c4eb55676cfeb9835151be5890257d99c697e119ea2de6292bd94b10eb`。包含11月3日10:36的pynccl/custom allreduce日志和10:37的KV容量。
- C588 CSV只读快照 `/private/tmp/metax-cross-model-20261104/c588-5.json`；源CSV路径及各自SHA随快照保留。计算入口读取五个指定C550 CSV和五个指定C588 SUMMARY，4K遵守用户指定Run3，未修改任一源CSV。
- 重算产物 `/private/tmp/qwen35-c588-c550-analysis-20261104/computed-comparison.json`，SHA256 `c38d04f1842e920a0aa65adcb8fc2eb22094b7a048d056d2e954463debfd7a02`，含十个源CSV身份、选轮、全部指标、相对变化与延迟示例。
- 现场检查命令保存于上述临时目录的 `read_facts.py`、`read_topology.py`、`read_sysfs.py`、`read_historical_comm.py` 等，仅通过Ansible inline执行只读Python；未生成远端脚本或大体积原始产物。

状态：只读分析完成；阶段差异已复核，具体算子/通信/CPU贡献尚未做因果验证。无新性能、GPU profiling、正式精度或验收结果。
