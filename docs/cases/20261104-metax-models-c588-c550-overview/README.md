# C588 与 C550 跨模型端到端性能对比及瓶颈分析

交付：按用户批注修订[飞书文档](https://jwolpxeehx.feishu.cn/docx/DuwsdmPo7oi979xodNac0OVknab)：以C550为基线重算C588变化，移除16K专属总览，开头精简为显卡使用和环境差异；随后按用户指定，将Qwen35的C550 4K展示口径改为Run3，吞吐、TTFT、TPOT及相对变化同步更新；再按用户提示只读核对C588-5，将Qwen3-VL的1K/4K更新为`20261104_144806`批次SUMMARY。此前整稿HTML SHA256为`42052bc93a7f31665f1d8a41ec4f278dcc15aace3850882de9816d690293bad8`，不代表本次局部编辑后的云端正文；原始CSV未修改。

更新日期：2026-11-04。以 C550 为基线，对比五个模型在 C588 上的端到端性能，并分析 DeepSeek 与 MiniMax-M3 的瓶颈。

## 一、各模型 C588 / C550 性能对比

### 1.1 显卡使用情况

DeepSeek 与三个 Qwen 模型使用 C588-5，MiniMax-M3 使用 C588-6；C550 的 MiniMax-M3 使用 mx-101、mx-102 双机，其余模型为单机。

| 模型 | C550（基线） | C588 |
| --- | --- | --- |
| DeepSeek | 8卡/TP8 | 4卡8die/TP8 |
| Qwen3.6-27B | 2卡/TP2 | 1卡2die/TP2 |
| Qwen3.6-35B | 2卡/TP2 | 1卡2die/TP2 |
| Qwen3-VL | 2卡/TP2 | 1卡2die/TP2 |
| MiniMax-M3 | 双机16卡/TP16 | 8卡16die/TP16 |

C550 每卡 64 GiB；C588 每卡 128 GiB、包含两个逻辑 die。推理每个 rank 使用一个逻辑设备，按 die 计算两端每 rank 显存均约 64 GiB。

### 1.2 测试环境的主要区别

| 项目 | C550 | C588 |
| --- | --- | --- |
| CPU型号 | Xeon 8460Y+ | Hygon 7493 |
| 物理核/NUMA | 80核/2NUMA | 112核/8NUMA |
| GPU驱动 | 3.8.1 | 3.9.61 |
| Mini显存比例 | 0.96 | 0.92 |
| Mini上下文上限 | 131072 | 70000 |
| Mini KV容量 | 155136 token | 95082 token |

CPU 核数/NUMA 按单台机器计算。MiniMax 的 C588 显存比例受 OOM 限制；单机/双机拓扑及显存预算差异在第三章展开。软件分组为：DeepSeek、MiniMax、Qwen3-VL 使用 vLLM0.24，Qwen27/35 使用 vLLM0.20.2；历史版本绑定与证据见后文。

统一输入 1K/4K/16K/32K/64K、输出 1K、并发上限 64、128 请求。总吞吐单位 tok/s。C588 相对变化 =（C588 吞吐 / C550 吞吐 − 1）×100%，正值表示提高，负值表示降低。

### 1.3 DeepSeek-V4-Flash W8A8：五场景完整结果

| 输入 | C550吞吐 | C588吞吐 | C588变化 |
| --- | --- | --- | --- |
| 1K | 2169.62 | 2012.88 | 降低 7.22% |
| 4K | 3861.31 | 3405.93 | 降低 11.79% |
| 16K | 6117.00 | 4791.32 | 降低 21.67% |
| 32K | 6791.77 | 5484.40 | 降低 19.25% |
| 64K | 6920.01 | 5869.80 | 降低 15.18% |

延迟表每格依次为 C550 / C588；TTFT 单位秒，TPOT 单位毫秒。

| 输入 | TTFT秒 550/588 | TPOTms 550/588 |
| --- | --- | --- |
| 1K | 3.77/4.91 | 55.23/58.71 |
| 4K | 9.60/12.54 | 73.05/81.25 |
| 16K | 36.14/49.31 | 140.52/176.84 |
| 32K | 71.60/94.13 | 236.69/288.65 |
| 64K | 235.40/281.98 | 346.48/406.04 |

以 C550 为基线，C588 五场景总吞吐低 7.22%–21.67%，mean TTFT/TPOT 整体更高。本批 16K 原始值为 C550 6117.00、C588 4791.32；第二章另列后续诊断批次，避免混用。

### 1.4 Qwen3.6-27B：五场景完整结果

| 输入 | C550吞吐 | C588吞吐 | C588变化 |
| --- | --- | --- | --- |
| 1K | 1943.70 | 1987.91 | 提高 2.27% |
| 4K | 3089.56 | 3247.06 | 提高 5.10% |
| 16K | 3694.79 | 3902.14 | 提高 5.61% |
| 32K | 3600.33 | 3804.52 | 提高 5.67% |
| 64K | 3495.44 | 3655.63 | 提高 4.58% |

延迟表每格依次为 C550 / C588；TTFT 单位秒，TPOT 单位毫秒。

| 输入 | TTFT秒 550/588 | TPOTms 550/588 |
| --- | --- | --- |
| 1K | 5.11/5.13 | 60.84/59.32 |
| 4K | 14.43/13.53 | 89.26/85.10 |
| 16K | 104.10/97.66 | 175.03/166.18 |
| 32K | 318.76/300.37 | 195.00/184.61 |
| 64K | 786.55/751.17 | 214.62/205.48 |

以 C550 为基线，C588 五场景总吞吐高 2.27%–5.67%。该模型没有新增根因诊断，不将这几百分点归给 CPU 或 GPU 的单独贡献。

### 1.5 Qwen3.6-35B-A3B：五场景完整结果

| 输入 | C550吞吐 | C588吞吐 | C588变化 |
| --- | --- | --- | --- |
| 1K | 3095.10 | 3037.22 | 降低 1.87% |
| 4K * | 6271.68 | 6069.86 | 降低 3.22% |
| 16K | 10776.42 | 10656.35 | 降低 1.11% |
| 32K | 10952.51 | 11111.39 | 提高 1.45% |
| 64K | 9464.27 | 9609.97 | 提高 1.54% |

延迟表每格依次为 C550 / C588；TTFT 单位秒，TPOT 单位毫秒。

| 输入 | TTFT秒 550/588 | TPOTms 550/588 |
| --- | --- | --- |
| 1K | 2.01/1.89 | 39.39/40.27 |
| 4K | 4.60/4.34 | 46.35/48.30 |
| 16K | 17.06/16.39 | 83.44/85.17 |
| 32K | 61.90/60.75 | 120.23/118.23 |
| 64K | 237.98/233.82 | 154.74/152.38 |

* 4K 的 C550 按用户指定采用 Run3：6271.68 tok/s、104.50 秒，TTFT/TPOT 同步采用该轮；C588 保留原 SUMMARY。因此该行 C588 吞吐降低 3.22%，五场景相对变化为−3.22%至+1.54%。

### 1.6 Qwen3-VL-30B-A3B：五场景完整结果

| 输入 | C550吞吐 | C588吞吐 | C588变化 |
| --- | --- | --- | --- |
| 1K | 3181.19 | 3053.06 | 降低 4.03% |
| 4K | 5621.01 | 5675.85 | 提高 0.98% |
| 16K | 6499.96 | 6734.07 | 提高 3.60% |
| 32K | 6013.93 | 6169.49 | 提高 2.59% |
| 64K | 5136.02 | 5286.82 | 提高 2.94% |

延迟表每格依次为 C550 / C588；TTFT 单位秒，TPOT 单位毫秒。

| 输入 | TTFT秒 550/588 | TPOTms 550/588 |
| --- | --- | --- |
| 1K | 1.63/1.48 | 38.63/40.47 |
| 4K | 4.74/3.86 | 52.14/52.43 |
| 16K | 73.66/70.01 | 77.93/75.94 |
| 32K | 215.25/208.52 | 82.00/80.50 |
| 64K | 568.93/552.25 | 89.18/87.03 |

C588 的1K/4K采用11月4日14:48批次的 SUMMARY，16K/32K/64K保留原批次。更新后，1K吞吐低4.03%，4K高0.98%，五场景差异为−4.03%至+3.60%。

### 1.7 MiniMax-M3 BF16：五场景完整结果

| 输入 | C550吞吐 | C588吞吐 | C588变化 |
| --- | --- | --- | --- |
| 1K | 1041.13 | 1000.70 | 降低 3.88% |
| 4K | 1577.11 | 1357.74 | 降低 13.91% |
| 16K | 2025.56 | 1941.83 | 降低 4.13% |
| 32K | 2445.62 | 1996.66 | 降低 18.36% |
| 64K | 2497.82 | 2050.63 | 降低 17.90% |

延迟表每格依次为 C550 / C588；TTFT 单位秒，TPOT 单位毫秒。

| 输入 | TTFT秒 550/588 | TPOTms 550/588 |
| --- | --- | --- |
| 1K | 3.49/5.11 | 119.50/103.66 |
| 4K | 78.27/121.10 | 101.89/71.81 |
| 16K | 358.86/396.90 | 68.75/41.43 |
| 32K | 630.36/790.80 | 48.75/30.11 |
| 64K | 1251.0/1539.5 | 42.54/25.64 |

以 C550 为基线，C588 在1K/16K总吞吐低约4%，4K低13.91%，32K/64K低18.36%/17.90%；但全部场景的TPOT都更低。第三章分析显存预算、实际并发与单请求延迟的取舍。

### 1.8 结果说明

除 Qwen35 的 C550 4K 按用户指定采用 Run3 外，其他数据沿用原 CSV SUMMARY，原始各轮记录完整保留。Qwen3-VL 的C588 1K/4K已更新为11月4日复测结果；C588-5历史测试时间范围重叠，GPU die 分开但主机资源共享。这批结果用于比较实际部署表现，不能视为仅更换 CPU 的实验。

## 二、DeepSeek 在 C588 上性能较低的原因

### 2.1 结论：主机供给侧关键路径，rank0 日志放大不均衡

现有证据最支持：当前 DeepSeek prefill/mixed 路径有密集的 Python 包装、Tensor 元数据、dispatch 与 kernel launch；C588 执行相关 CPU 热点的效率较低，使 GPU 执行出现更多空隙，并让其他 TP rank 在 collective 中等待。rank0 专有的 oplist 日志对象处理是已经通过单变量 E2E 验证的放大因素。主要 GPU 计算整体变慢或 MCCL 链路本身变慢，不是匹配 trace 的主要增量来源。

模型环境核验与复验已确认相同发布镜像（tag 202610291849，digest 70c61a83528977a4de8070a9a9bc20ea702ab08abaea52e8a894ea25688e6562）、vLLM0.24 / Torch2.10+metax3.8.2.2 / MACA3.8.2。两端模型 config/tokenizer/权重索引一致，未全量哈希权重分片；驱动、CPU、内核与内存系统仍不同。TP8、MBT4096、seq64、FP8 KV/block256、maxlen66560、显存比例0.85、FULL_DECODE_ONLY、prefix cache关闭。

### 2.2 全 rank trace：设备空隙增加，计算 kernel 接近

这是迁移前 C588-5 / mx-103 的历史 trace；不是 mx-104 新采的 trace。每端 8 rank 均覆盖，每份 8 个 step，匹配中间 6 个长输入 step，每步 4483 个 kernel。下表为 rank0 平均 ms/step。

| 指标 | C550/103 | C588-5 |
| --- | --- | --- |
| GPU执行跨度 | 616.949 | 809.030 |
| 计算区间并集 | 386.602 | 381.365 |
| MCCL区间并集 | 87.458 | 74.550 |
| 无kernel区间 | 142.889 | 353.115 |

主要计算 kernel 的数量和时间接近，增加集中在设备执行空隙。C588 rank1–7 的 MCCL 区间约 379–400 ms/step，103 为 192–199 ms/step，但 rank0 MCCL 合计没有更慢，符合其他 rank 等待较慢 rank 推进。MCCL kernel 时间包含等待，不能直接解释为链路传输时间。空隙也不等于纯 CPU self time；Torch profiler 有扰动，不能把这些时间差直接折算为无 profiler E2E 收益。

### 2.3 rank0 的已验证放大因素：oplist

安装 Plugin 强制 should_record=(rank==0)，向 FlagGems 传 record=True、once=True。once 在 logging handler 中过滤，虽避免重复写文件，后续每次调用仍会先查找调用位置、创建 LogRecord。主要额外成本是主机对象与调用栈处理，不能简单称为大量磁盘写日志。Qwen 也启用 rank0 记录，不能据是否开启解释模型差异。

后续按用户要求迁至 mx-104，采用相同 P16K/D1K/C64/N128，原配置与仅关闭 oplist 的单变量无 profiler E2E，3轮跳过首轮；所有计分轮128成功、0失败。与主表的历史批次分开：

| 配置 | C550/104 | C588 | C588变化 |
| --- | --- | --- | --- |
| 原配置 | 6141.91 | 5361.61 | 降低 12.70% |
| 关闭oplist | 6175.19 | 5554.25 | 降低 10.06% |

以 C550 为基线，原配置 C588 吞吐低12.70%；双方关闭oplist后，C588仍低10.06%。关闭日志相对本机原配置的收益为C588提高3.59%、104提高0.54%，只能解释部分差距。历史主表的21.67%与独立复验的12.70%来自不同批次，不能混用，也不能相减作为精确贡献。诊断后已恢复原源码和启动配置。

### 2.4 CPU-only PMU：相关热点每周期效率存在直接差异

C588-5 / mx-104 的后续实验屏蔽 GPU，核对 CUDA 未初始化、设备数0、GPU FD为空；Python/torch CPU相关库、脚本与原生探针 ELF 的 SHA 一致。每端3个固定核心，每项7次；PMU用户态 cycles/instructions 无复用、无核心迁移。它直接测 CPU 路径，不是 GPU wrapper 计时。

| CPU-only路径 | 104 μs/次 | C588 μs/次 |
| --- | --- | --- |
| 禁用日志检查 | 0.119 | 0.160 |
| once 日志记录 | 4.385 | 5.638 |
| CPU Tensor 创建 | 1.981 | 3.090 |
| CPU Tensor view | 2.947 | 4.443 |
| Python 小对象 | 0.205 | 0.308 |

以Tensor view为例，按C550/C588顺序：每次指令数21128/21069，周期数8223/13767，IPC2.57/1.53；C588线程CPU时间高50.8%，对应频率约2.79/3.10GHz。调度等待和系统CPU时间远小于差距，因此该热点不是C588低频或明显排队造成。公共整数依赖链和部分小工作集C588反而更快，不能推广为所有CPU计算都慢。

这实锤了相关 Python/Tensor 元数据路径在两 CPU 平台上的执行效率不同；仍未在同 GPU/驱动/内核下只替换 CPU，因此不能宣称某个 CPU 型号单独造成了全部端到端差距。内核、安全缓解机制、内存系统和驱动等影响尚未完全拆开。

### 2.5 为什么 Qwen35 长输入差距较小；哪些解释未被证实

C588 上同口径 P16K/D1/C1/N32 短负载中，DeepSeek rank0/1 主线程 CPU 约74.24%/77.74%，Qwen35约38.56%/37.16%，没有重叠压测。结合调用栈和 GPU 时序，符合 DeepSeek 主机开销更易落在关键路径、Qwen35 有较大 CPU 余量的机制；CPU利用率本身不是瓶颈证明。Qwen仍无同口径GPU trace，不能逐kernel定性全部瓶颈。

DeepSeek 的 silu_and_mul_with_clamp 实际落入 forward_native，展开为 slice/clamp/sigmoid/mul/add，现场 VLLM_FL_USE_FLAGGEMS_VLLM 未设置；Qwen 的普通 silu_and_mul 接入融合实现。不能以 default.flagos 日志证明目标融合 kernel 已命中，也不能直接打开全局变量就宣称收益。Qwen35为BF16/TP2/MBT8192/vLLM0.20.2/MACA3.7，DeepSeek为W8A8/TP8/MBT4096/vLLM0.24/MACA3.8.2；两者都是FULL_DECODE_ONLY，不是“Qwen全prefill图而DeepSeek没有”的对照。

NUMA绑定使小 prefill 探针吞吐提高11.95%，但完整16K E2E下降1.10%；不能将完整差距主要归结为未绑NUMA。关闭异步调度只有小探针提高7.61%，未完成高并发E2E验证。rank0额外输出职责/GIL也未证明是唯一原因。深入证据集中在长输入 prefill 与 mixed，纯 Decode 的独立跨机归因仍待补。

## 三、MiniMax-M3 在 C588 上总吞吐较低的原因

### 3.1 结论：初始显存开销与 KV/实际并发约束更直接

MiniMax 的直接证据链是：C588 初始化后的显存占用更高，0.96存在OOM/显存门禁约束，只能采用较低预算；由此可分配KV字节数更少，实际Running更低，长输入排队增加。它与C588单请求TPOT更低、总吞吐更低同时出现相吻合。KV预算原因已有逐rank日志和实际代码支撑；对端到端吞吐的贡献尚未用相同KV预算的A/B全部量化，不能直接套用DeepSeek的CPU结论。

两端均TP16/BF16权重、BF16 KV/index KV、MBT8192、seq64、block128、prefix和async关闭、breakable FULL_AND_PIECEWISE。主要Plugin/FlagGems-vllm/FlagGems revision和策略、模型元数据已核对一致，但镜像仓库/image ID、设备、驱动和单机/双机拓扑不同；未证明全部底层二进制与权重分片逐字节一致。

### 3.2 逐 rank 显存账：0.92 是 OOM 约束

用户已说明 C588 先前设0.96会OOM。本轮不复现OOM，只核验成功启动时两端各16rank的M3_MEMORY_BUDGET。单位GiB，每个逻辑设备/rank：

| 项目 | C550双机 | C588-6 |
| --- | --- | --- |
| 可见总显存 | 63.59 | 63.59 |
| 初始可用 | 61.98–62.01 | 59.49 |
| 初始已占用 | 1.59–1.61 | 4.11 |
| 申请预算 | 61.05（0.96） | 58.51（0.92） |
| 模型权重 | 50.41 | 50.41 |
| 激活峰值 | 3.98 | 2.73 |
| 非Torch增量 | 0.09–0.12 | 1.35 |
| KV字节预算 | 6.55–6.57 | 4.01–4.02 |
| graph estimate 字段 | 0 | 0 |

实际 Plugin init_device 在通信初始化之后、权重加载之前取init_snapshot，再计算requested_memory=total×利用率，free<requested时直接报错。C588若在相同初始状态使用0.96，需要61.05GiB，比59.48654GiB可用量多1.56346GiB；当前可用/总量仅约0.935415。因此0.96不能直接照搬；该比值不是可稳定运行的推荐上限，graph/临时峰值还需余量。约4.11GiB也不是启动服务前的空卡占用。

预算公式为：requested_memory−权重−激活峰值−非Torch增量−已应用graph estimate。权重两端相同；C588非Torch增量多约1.24GiB，激活峰值少约1.25GiB，两项基本抵消。0.04×63.59375=2.54375GiB，而最小KV字节预算实差约2.53441GiB，说明KV预算差的主要数值项就是受限后较低的利用率参数。不能把初始占用再重复从该公式扣一次；graph estimate=0也不意味着实际graph显存为零。

### 3.3 KV 容量、Running 与吞吐/延迟的取舍

日志KV容量为C550 155,136 token、C588 95,082 token，C588相对低38.71%；max-model-len分别为131072/70000。按客户端轮次边界对齐历史服务采样、排除初始60秒并仅统计Running>0，两计分轮中位数如下：

| 输入 | C550 R2/R3 | C588 R2/R3 |
| --- | --- | --- |
| 1K | R2=64,R3=64 | R2=49,R3=49 |
| 4K | R2=31,R3=31 | R2=19,R3=19 |
| 16K | R2=9,R3=9 | R2=5,R3=5 |
| 32K | R2=4,R3=4 | R2=2,R3=2 |
| 64K | R2=2,R3=2 | R2=1,R3=1 |

Running是引擎已运行请求数，不是每个GPU step的精确batch；窗口包含边界/收尾残余，不能替代profiler。16K C588 224个活跃采样中203次为5；64K 818个全部为1，C550大多为2。客户端C64不意味着实际并发一致。长输入KV使用率不到100%仍可能无法接纳下一条请求，因为剩余块不足。

16K下，TTFT为C550 358.86秒、C588 396.90秒，TPOT为68.75/41.43ms，C588 TPOT低39.74%。32K/64K的C588 Running约为C550一半，总吞吐分别低18.36%/17.90%。这支持小并行负载降低单请求TPOT、同时增加排队并限制总吞吐的机制，不能称为同batch GPU decode算子快40%。

### 3.4 通信显存是否更大：候选明确，尚未拆分

通信值得重点查，但尚未单独实锤：初始快照在通信初始化后，已初始化的通信资源可能计入约4.11GiB；后续1.35GiB非Torch增量也可能包含延迟通信分配、运行时与vendor workspace。不能将任一项全算成MCCL，也不能把两个时点的统计当成同一个分量重复相加。

C550策略显式配置NCCL/MCCL BUFFSIZE=1MiB、MIN/MAX_NCHANNELS=4、MAX_P2P_NCHANNELS=4；C588成功启动的rank0 after_capture effective_env没有NCCL_/MCCL_项。单机16 local rank与双机每机8 local rank的peer/IPC映射、默认选路、驱动/运行时都可能影响占用。没有各communicator实际分配字节证据，不能仅从环境变量或non-Torch总量算出纯通信占用。

C550在4K/16K/32K的轮内P99 ITL平均约1062.95/1096.43/1074.14ms，C588为471.70/46.62/34.38ms；提示需要检查mixed干扰、调度与collective等待，但约1秒尾部不能证明RDMA慢。这是轮内P99的平均，不是合并样本P99。MiniMax没有同口径多rank trace/CPU-only实验，不能把C588-5/104的DeepSeek PMU结果直接套到C588-6/101+102。

## 四、结论强度、后续验证与证据入口

| 模型 | 已验证的关键事实 | 仍未完成的归因 |
| --- | --- | --- |
| DeepSeek | 主机空隙；日志单变量收益；CPU热点IPC差异 | CPU SKU唯一贡献；纯Decode；全历史差距分解 |
| MiniMax-M3 | 初始占用更高；0.96门禁不足；KV与Running较少 | 纯MCCL分配；KV对E2E贡献；同batch计算/通信 |
| Qwen系列 | Qwen35长输入接近；Qwen3-VL更新后五场景吞吐差异在约±4%以内 | 旧批次Qwen3-VL 1K/4K异常的原因尚未归因，不能据旧结果判定硬件差距 |

后续优先级：DeepSeek减少重复日志/元数据/dispatch/launch并逐项验证实际融合路径；MiniMax先在隔离环境建立相同maxlen等条件的新基线，再仅降低C550的KV budget到C588可运行水平验证容量贡献，避免直接提高C588到0.96；通信显存则用新进程在绑定设备后、分布式初始化后、首个collective后分别记录free/allocated/reserved。以上均为待执行方案，不是已完成优化。

性能/精度边界：本轮没有新benchmark或正式精度gate；历史CSV与定位实验不是最终四场景优化验收。MiniMax的C550历史日志在压测结束之后另有worker死亡/EngineDeadError，不能据成功轮数声明长期稳定性。之前DeepSeek诊断已恢复原配置，本轮没有改动任何服务或103。

### 4.1 原始数据与实验来源

C550：/Users/baai/Downloads/benchmark_results/{deepseek-v4-flash-w8a8-int8,qwen36-27b,qwen36-35b,qwen3vl,minimax-m3}。C588：前述各工作根下test/perf_test/benchmark_results；分别使用deepseek-v4-flash-w8a8-int8、qwen36-27b-black-list、qwen36-35b-opt4、qwen3vl、minimax-m3目录。补充：Qwen3-VL 的 C588 1K/4K 更新为20261104_144806批次，下表保留原批次记录。

| 模型 | C550 CSV批次 | C588 CSV批次 |
| --- | --- | --- |
| DeepSeek | 20261028_223915 | 20261103_105152 |
| Qwen27 | 20261028_111052 | 20261103_103536 |
| Qwen35 | 20261103_103903 | 20261103_103056 |
| Qwen3-VL | 20261029_103926 | 20261103_105910 |
| MiniMax | 20261029_070842 | 20261103_093147 |

DeepSeek：C588根/data/jinghao/deepseek，104根/public-flash/jinghao/deepseekV4。早期C588/103的04-runs/profile16k-20261103-01保存8rank trace；C588/104的04-runs/cpu-ab16k-<Host>-20261103-01保存日志/NUMA/E2E，04-runs/cpu-proof-<Host>-20261104-01保存GPU-off PMU窗口与软件哈希。早期trace的103仅作为历史证据引用，本轮未连接该机。

DeepSeek详细实验记录为“新模型适配”项目models/DeepSeek-V4-Flash/metax/frameworks/vllm-plugin-fl/adaptation下014、015、016三份文档。本轮只读导入相关事实，没有修改上游。MiniMax证据为两端service日志的M3_MEMORY_BUDGET、KV/Running及原launcher；C550为service101.log/service102.log。

本地完整新稿与50个CSV的SHA/路径索引位于当前“端到端推理优化”项目docs/cases/20261104-metax-models-c588-c550-overview/README.md；MiniMax逐rank预算细节另见docs/cases/20261104-minimax-m3-metax-cross-topology/README.md。旧飞书正文已在本地外部临时产物中备份，新稿按本轮明确的数据源重组。

## 本地补充：Qwen35 C550 4K 单轮展示修订

2026-11-04，用户在吞吐表和延迟表的两条批注中均指定“4K数据以6271那轮为准”。只修改该行展示和相关说明，保留其他行及C588的SUMMARY口径。源文件为`/Users/baai/Downloads/benchmark_results/qwen36-35b/qwen36-35b-retest_4096in_1024out_c64_n128_20261103_103903.csv`；原始文件SHA见下方索引。

采用`Run3(SUCCESS)`：128请求成功，总吞吐6271.68 tok/s、耗时104.50秒、mean TTFT 4598.17 ms（表中4.60秒）、mean TPOT 46.35 ms。C588保持6069.86 tok/s、4.34秒、48.30 ms；相对吞吐变化按`(6069.86/6271.68-1)*100`计算为−3.2179575%，展示为降低3.22%。此前C550的SUMMARY为4812.15 tok/s、18.32秒、55.13 ms，原始Run2/Run3及SUMMARY均未改写；该展示例外不构成新增稳态验证。

云端仅局部修改两张表的四个单元格、Qwen35取值说明及1.8结果说明，保留用户现有排版。本轮没有新benchmark、远端操作或服务变更。

## 本地补充：Qwen3-VL C588 1K/4K 复测更新

2026-11-04，用户指出Qwen3-VL在C588的1K/4K已有更新。本轮通过项目inventory限定`mxC588-5`，非交互认证失败后使用`ANSIBLE_ASK_PASS=true ./scripts/connectivity-check --limit mxC588-5`完成连接验证（实际hostname为`pm-6ae4`），再经项目Ansible入口只读列出并读取指定模型目录的CSV。没有启动压测、修改远端文件、连接103或变更推理服务。

新批次为`20261104_144806`，工作负载仍为P1024或P4096/D1024/C64/N128。两文件各含3轮SUCCESS及SUMMARY，各轮128请求完成，输入/输出token总量与场景一致；SUMMARY与Run2/Run3的算术均值相符（容许CSV保留两位小数的舍入）。1K计分轮吞吐为3087.16/3018.96 tok/s，4K为5637.80/5713.90 tok/s，轮间差/均值约2.23%/1.34%。本次仅核验历史结果文件，未建立新服务身份或正式稳态准入证据，不能独立归因旧批次异常。

| 输入 | 新C588总吞吐 tok/s | Mean TTFT ms | Mean TPOT ms | 相对C550总吞吐 |
| --- | --- | --- | --- | --- |
| 1K | 3053.06 | 1478.49 | 40.47 | −4.027738%，展示降低4.03% |
| 4K | 5675.85 | 3863.60 | 52.43 | +0.975625%，展示提高0.98% |

C550基线及16K/32K/64K保持原数据。C588旧1K/4K总吞吐2091.98/4566.01 tok/s、TTFT 3.18/4.15秒、TPOT 50.16/61.27ms及对应文件仍保留为历史证据。云端已同步两张表、移除旧4K星号，并更新1.6、1.8、第四章结论和4.1来源说明；保留用户现有排版。

新文件均在`/data/jinghao/qwen3vl/test/perf_test/benchmark_results/qwen3vl/`：

| 输入 | 文件 | 原始字节SHA256 |
| --- | --- | --- |
| 1K | `qwen3vl_1024in_1024out_c64_n128_20261104_144806.csv` | `840b66b3ae9c7636bf9aacd86dd72880e88d2e553d7c43b448541501ad2fade1` |
| 4K | `qwen3vl_4096in_1024out_c64_n128_20261104_144806.csv` | `ce2be6d1e14e57a0385ed8fad530c2a46d60108ab1f5778bd5549b02c152d927` |

外部本地证据目录：`/private/tmp/metax-cross-model-20261104/qwen3vl-1k4k-update/`，包含远端原始CSV的字节一致副本（CRLF换行、SHA256匹配）、`c588-updated.json`及`comparison-update.json`。下方旧逐文件索引保留初稿来源，新1K/4K展示以本节为准。

## 本地补充：逐文件证据索引

本表只保存路径和校验信息，原始CSV/日志留在用户指定位置。

### DeepSeek-V4-Flash W8A8

| 输入 | C588 CSV / SHA256 | C550 CSV / SHA256 |
|---|---|---|
| 1K | `/data/jinghao/deepseek/test/perf_test/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_1024in_1024out_c64_n128_20261103_105152.csv`；`197bf95f2ff5570b0f2f2365bac9c34bc3398818b1c95f47f3883f62f6a79b39` | `/Users/baai/Downloads/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_1024in_1024out_c64_n128_20261028_223915.csv`；`db148585e94269d04f2b4a11f0436479c6b0d70d0a081273bfa4500167983b78` |
| 4K | `/data/jinghao/deepseek/test/perf_test/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_4096in_1024out_c64_n128_20261103_105152.csv`；`fe12941701ffae42196200d425de008c1a8402628ccb06bed36096ca3dde8009` | `/Users/baai/Downloads/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_4096in_1024out_c64_n128_20261028_223915.csv`；`17f3b0f1fc7cb616008bcbebeb463f6b9e36c60c489dde350c7cf4f61511dbf7` |
| 16K | `/data/jinghao/deepseek/test/perf_test/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_16384in_1024out_c64_n128_20261103_105152.csv`；`40ab84e121e98ac08ca37a1b3351cf68cbe8aaf64151df8bed0e9334fa4dcb0e` | `/Users/baai/Downloads/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_16384in_1024out_c64_n128_20261028_223915.csv`；`2edd34f4eef8f181a6e2dcc776799d9f569ef44ae9c15d8661aedef341598f6c` |
| 32K | `/data/jinghao/deepseek/test/perf_test/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_32768in_1024out_c64_n128_20261103_105152.csv`；`a080916230dc22975bfd57afe6a51a8c8097ebb9e78bcb37cd6977de4acd1453` | `/Users/baai/Downloads/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_32768in_1024out_c64_n128_20261028_223915.csv`；`69aace099121757b045563dedb622ef06703cf29ff1fd2b21b2ca2c30f9efb6e` |
| 64K | `/data/jinghao/deepseek/test/perf_test/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_65536in_1024out_c64_n128_20261103_105152.csv`；`0b0cd3efcda2c1f755ef5d74330c69f247f9779ad0a1c72186c0657ac1552129` | `/Users/baai/Downloads/benchmark_results/deepseek-v4-flash-w8a8-int8/deepseek-v4-flash-w8a8-int8_65536in_1024out_c64_n128_20261028_223915.csv`；`921c66ac060507c994c14a70d9343a46424a774f37ec83681571ed509853ab49` |

### Qwen3.6-27B

| 输入 | C588 CSV / SHA256 | C550 CSV / SHA256 |
|---|---|---|
| 1K | `/data/jinghao/qwen3.6-27B/test/perf_test/benchmark_results/qwen36-27b-black-list/qwen36-27b-black-list_1024in_1024out_c64_n128_20261103_103536.csv`；`d84e72f69972c172cbc818ecb474da44acd0c580010c19267f01f80cc0b1ac5c` | `/Users/baai/Downloads/benchmark_results/qwen36-27b/qwen36-27b-black-list_1024in_1024out_c64_n128_20261028_111052.csv`；`099fc303411b2d6bb4615cbab505ce58bb490331838b51ca527c9a56a189968d` |
| 4K | `/data/jinghao/qwen3.6-27B/test/perf_test/benchmark_results/qwen36-27b-black-list/qwen36-27b-black-list_4096in_1024out_c64_n128_20261103_103536.csv`；`5acdd0a60a1eb95df541a93af1ce95d1a982b9e0eb8e744ebbb44b270a8af18b` | `/Users/baai/Downloads/benchmark_results/qwen36-27b/qwen36-27b-black-list_4096in_1024out_c64_n128_20261028_111052.csv`；`b8f256bf63cfcd07e0d53be74d348b45f2f45ff84a53f2a5540568a2698ba501` |
| 16K | `/data/jinghao/qwen3.6-27B/test/perf_test/benchmark_results/qwen36-27b-black-list/qwen36-27b-black-list_16384in_1024out_c64_n128_20261103_103536.csv`；`85e4607f9a0430bdfb8626b0e9d5ef7c2f08814fa4ae849574bd8bfc1c700e99` | `/Users/baai/Downloads/benchmark_results/qwen36-27b/qwen36-27b-black-list_16384in_1024out_c64_n128_20261028_111052.csv`；`f14b6262a0d420bbdfb531727a8ae9c92a81f8dec2026177e3796736dc7e704f` |
| 32K | `/data/jinghao/qwen3.6-27B/test/perf_test/benchmark_results/qwen36-27b-black-list/qwen36-27b-black-list_32768in_1024out_c64_n128_20261103_103536.csv`；`98e5392b191ec09ea0fc5f655e912095d91bdec93b9254a8e8710176bee5ee07` | `/Users/baai/Downloads/benchmark_results/qwen36-27b/qwen36-27b-black-list_32768in_1024out_c64_n128_20261028_111052.csv`；`167c70e7b587f105bab6d3f53498d0a570b794f89adaa938b2c2824938a697a7` |
| 64K | `/data/jinghao/qwen3.6-27B/test/perf_test/benchmark_results/qwen36-27b-black-list/qwen36-27b-black-list_65536in_1024out_c64_n128_20261103_103536.csv`；`4428a66b68e5122c129ee4a8a54f0c18e4b1b23e8d50ff75c1ffc5939a1884e5` | `/Users/baai/Downloads/benchmark_results/qwen36-27b/qwen36-27b-black-list_65536in_1024out_c64_n128_20261028_111052.csv`；`49645a13f28031afda4b99f8801a3c5eff732d099e14c5167a674732e9212e78` |

### Qwen3.6-35B-A3B

| 输入 | C588 CSV / SHA256 | C550 CSV / SHA256 |
|---|---|---|
| 1K | `/data/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-opt4/qwen36-35b-opt4_1024in_1024out_c64_n128_20261103_103056.csv`；`d8eed6fcde886c2c89e734e1a69526f2c335041cf941f3fb20a320f40dde2226` | `/Users/baai/Downloads/benchmark_results/qwen36-35b/qwen36-35b-retest_1024in_1024out_c64_n128_20261103_103903.csv`；`4bf0d983da5cbf08ccdce270d9fba515a7160aeec766dc7241923293a1f8995b` |
| 4K | `/data/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-opt4/qwen36-35b-opt4_4096in_1024out_c64_n128_20261103_103056.csv`；`a86db850d450f6f61e765ea8151589dcd419852b1462c57833f8a804075f2139` | `/Users/baai/Downloads/benchmark_results/qwen36-35b/qwen36-35b-retest_4096in_1024out_c64_n128_20261103_103903.csv`；`2a7250e735d221f1ee287f83ed0490a27a8a3dd6034fb7464c1e2d9a6fd034d6` |
| 16K | `/data/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-opt4/qwen36-35b-opt4_16384in_1024out_c64_n128_20261103_103056.csv`；`ae457a77c187f138f2bbdd8a839f09d30bdd315da91e111868304ceeb4832894` | `/Users/baai/Downloads/benchmark_results/qwen36-35b/qwen36-35b-retest_16384in_1024out_c64_n128_20261103_103903.csv`；`e458056153ec2fdf35d17f9eb760a2f87702e1e89692bf7079268df54d36bdc7` |
| 32K | `/data/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-opt4/qwen36-35b-opt4_32768in_1024out_c64_n128_20261103_103056.csv`；`e45cc68d302cdae10b4cce522dfaad98bfa2fb122d61ae536364c4a26fd8755a` | `/Users/baai/Downloads/benchmark_results/qwen36-35b/qwen36-35b-retest_32768in_1024out_c64_n128_20261103_103903.csv`；`0092d0b52f7e7953782ed9414ffcf7b3a483092b48b67fc614a60a4ff9c081c0` |
| 64K | `/data/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35b-opt4/qwen36-35b-opt4_65536in_1024out_c64_n128_20261103_103056.csv`；`017cab5205eb7e576bebf7043442932936b82cd5c512927c5842b6e840fd47e6` | `/Users/baai/Downloads/benchmark_results/qwen36-35b/qwen36-35b-retest_65536in_1024out_c64_n128_20261103_103903.csv`；`7368f3cbf5aba85e7328e448f6fd633471552f057ae2b46176df04a51c28b2de` |

### Qwen3-VL-30B-A3B

| 输入 | C588 CSV / SHA256 | C550 CSV / SHA256 |
|---|---|---|
| 1K | `/data/jinghao/qwen3vl/test/perf_test/benchmark_results/qwen3vl/qwen3vl_1024in_1024out_c64_n128_20261103_105910.csv`；`9f69a5830d57ce0bc0d0ca34177d55c24eb570088e15e2a46a0443e46e58a024` | `/Users/baai/Downloads/benchmark_results/qwen3vl/qwen3vl-opt15_1024in_1024out_c64_n128_20261029_103926.csv`；`974c1a0c1f74d545633363d061ab98dff7e0147d078fee8014104c235e7c9f5f` |
| 4K | `/data/jinghao/qwen3vl/test/perf_test/benchmark_results/qwen3vl/qwen3vl_4096in_1024out_c64_n128_20261103_105910.csv`；`eddb006aab29db831c1b0ce5be859c39f589db6070426ef4bf5043266306d874` | `/Users/baai/Downloads/benchmark_results/qwen3vl/qwen3vl-opt15_4096in_1024out_c64_n128_20261029_103926.csv`；`f042e02e4a3885b75684a786fdd84121001f4e3997deb2d0ecda003a687150e5` |
| 16K | `/data/jinghao/qwen3vl/test/perf_test/benchmark_results/qwen3vl/qwen3vl_16384in_1024out_c64_n128_20261103_105910.csv`；`24d474624963f337688e68145d2fb2d9ee0e15f0f7c91d1f638bb961cde235fd` | `/Users/baai/Downloads/benchmark_results/qwen3vl/qwen3vl-opt15_16384in_1024out_c64_n128_20261029_103926.csv`；`30821997b3f1bbc9a2fd5c53e012a5f58be22ec834caa59e5a02c7effaad972c` |
| 32K | `/data/jinghao/qwen3vl/test/perf_test/benchmark_results/qwen3vl/qwen3vl_32768in_1024out_c64_n128_20261103_105910.csv`；`16a3d3b57bb9aa1dd55b8aeba049205251c69ebe95e78ae7a1818a6bde9643e4` | `/Users/baai/Downloads/benchmark_results/qwen3vl/qwen3vl-opt15_32768in_1024out_c64_n128_20261029_103926.csv`；`2f019ca774e7babf3153322383affb2b888e04d61ea6316ccb6761ec1ba66f31` |
| 64K | `/data/jinghao/qwen3vl/test/perf_test/benchmark_results/qwen3vl/qwen3vl_65536in_1024out_c64_n128_20261103_105910.csv`；`0d7bd803271fa3c68258ff48bf50de487f503488ece34232e23d2685f93bdcb9` | `/Users/baai/Downloads/benchmark_results/qwen3vl/qwen3vl-opt15_65536in_1024out_c64_n128_20261029_103926.csv`；`c6f9983a25e57ac84e4130c4b367f124d43614e4a1c680694c746c9304660a9c` |

### MiniMax-M3 BF16

| 输入 | C588 CSV / SHA256 | C550 CSV / SHA256 |
|---|---|---|
| 1K | `/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3/minimax-m3_1024in_1024out_c64_n128_20261103_093147.csv`；`a78b0da51064b800c93d2938bdb907b435b709cc823848a40e07efdf614f8fe0` | `/Users/baai/Downloads/benchmark_results/minimax-m3/minimax-m3_1024in_1024out_c64_n128_20261029_070842.csv`；`68e60768549fe6e1984e0cb955fbabc5cb15b737ac85a99b46f292688f0fe8fa` |
| 4K | `/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3/minimax-m3_4096in_1024out_c64_n128_20261103_093147.csv`；`086e8ddd4b2ea221bbdae82376e984fcebaf7c12072eb3f54ceba7cb334be452` | `/Users/baai/Downloads/benchmark_results/minimax-m3/minimax-m3_4096in_1024out_c64_n128_20261029_070842.csv`；`4d56afdc790e624d9db1260111b17b1870bb6d0106e1c992abf8e1b7db011374` |
| 16K | `/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3/minimax-m3_16384in_1024out_c64_n128_20261103_093147.csv`；`ad7243ba1628bc675527027eb4db87ed009b534a5085cafe809563129aa78dfd` | `/Users/baai/Downloads/benchmark_results/minimax-m3/minimax-m3_16384in_1024out_c64_n128_20261029_070842.csv`；`28a89b4b226946381aec8825ed2d45582c33cbde4d39edb9c6556c31a3ddbd4d` |
| 32K | `/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3/minimax-m3_32768in_1024out_c64_n128_20261103_093147.csv`；`6c3e2f09ae5f564851288f049ef798ee9b419074c25193cfe758095ee9001227` | `/Users/baai/Downloads/benchmark_results/minimax-m3/minimax-m3_32768in_1024out_c64_n128_20261029_070842.csv`；`daaa6e857ab85ddc8ab70e11ab062b6cb1f1f6efba0062a8fbb8c7f132b00382` |
| 64K | `/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3/minimax-m3_65536in_1024out_c64_n128_20261103_093147.csv`；`829d2c896bafe82ab7f5f04b368e6915b5db735ce5bc7c01222a07773fa95051` | `/Users/baai/Downloads/benchmark_results/minimax-m3/minimax-m3_65536in_1024out_c64_n128_20261029_070842.csv`；`270ee59944959dfc9063ebaf112f63fedc3d4ae54e87c3636abf0114e8fcaefe` |

## 本地执行与边界记录

acceptance_scope=diagnostic；新测试=not_run；历史CSV验证=passed（仅结构/计数/原汇总算术）；正式稳态性能与精度验收=incomplete。已保存各源目录的计分规则，C55025个下载文件均与共享目录SHA匹配；不以验证通过代表硬件因果归因。

连接采用项目inventory及精确Host connectivity-check。C588-5/6非交互检查认证失败，随后沿用已授权交互认证核对实际hostname和目标路径；没有把普通SSH退出码当作控制面检查通过。C550共享目录通过mx-104只读核对，没有访问mx-103。为使用控制面，仅在inventory补登既有别名mxC588-5；未保存连接凭据。

本轮没有创建/启动/停止/重启容器，没有提交或推送。原始解析/计算、原飞书剪贴板备份、新稿HTML保存在/private/tmp/metax-cross-model-20261104；大型原始产物不纳入仓库。

2026-11-04只读导入的DeepSeek事实来源为`/Users/baai/Documents/ChatGPT/新模型适配/models/DeepSeek-V4-Flash/metax/frameworks/vllm-plugin-fl/adaptation/`：014文档SHA256为`adca9938f9a438dffa05d6ac0ef09b6f10149b8bdcc583e06726afdb7d3ba173`，015为`872e84b171914c8aa9d77332036978233a429cc9b4b96d5392efb842341e390f`，016为`a7da295e54c56b00e81b2016509d9dd99ba3630d1e6898d2bd4c454e8ebe4a9c`。本案例已保存必要事实快照，不依赖上游持续同步；未修改上游。




本次仅修订文档表达；C550基线百分比全部由原始SUMMARY重新计算，未连接远端或运行新测试。飞书Running表采用R2/R3标签文本以避免日期转换。

批注修订核验：全文回读已确认无“16K场景总览”、保留四个主章节与18个数据表；25组吞吐按C550基线重新计算，延迟与诊断表也改为先列C550。已目视核验显卡/TP使用、CPU/NUMA/驱动与Mini显存预算差异、DeepSeek五场景新百分比；页面显示“已经保存到云端”。外部修订稿、正文备份、验证记录与截图位于`/private/tmp/metax-cross-model-20261104/revision-c550-baseline/`。
