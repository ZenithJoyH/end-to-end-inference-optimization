# GDN 优化地图

证据范围：MetaX C550、Qwen3.6-27B、TP2、FG-vLLM29e80363+私有补丁，Prefill H8/HV24/K128/V128/BF16、FP32 g/state、V-major，附加96/80及64/64。其他backend/dtype/hardware未实测。

| 信号/匹配键 | 机制及首个实验 | 通过/停止条件 | 已知边界 |
|---|---|---|---|
| 导出同名、state shape相同但输出大幅不一致 | 从实际函数对象解析runtime/generic ABI；非零非对称、K!=V检查布局，先修adapter | 不以全零state或shape相等证明ABI；未确认导出时不启用 | MetaX V-major与generic K-major区别，不能直接套跨平台转置 |
| BF16输入、FP32 finalstate局部超原容差 | 固定量化后输入：FP64递推↔等价块公式，逐阶段模拟舍入；用完整入口捕获中间量 | 原参考/容差不变，全部state元素检查；未复现stock的独立stage直调不得当修复证据 | .002/.02是本案例冻结门槛，不是所有上游实现共同标准 |
| 小矩阵通过但长状态失败 | 多chunk/慢衰减/非零state，用相同FP32 oracle；消融WY与状态投影/创新量舍入 | 少量shape通过不得晋级；保留257token g=-.001/-.01失败回归与两次changed-input graph | 加权RHS-only在本例仍失败，完整FP32链通过；与模型实际gate分布关系未知 |
| FP32链满足数值但预期更慢 | 先冻结全FG Prefill/Decode/Mixed正确基线，再验证补偿BF16、FP32部分累积或tiling | 数值/graph+实际双rankFG命中和C8通过后，性能独立测量；不缩白名单、不切native获益 | OP009缩减P1K Prefill证实完整FP32链−8.30%吞吐/+9.00%TTFT（回退漂移<1%）；Decode/Mixed不稳未归因。自动调优编译成本非稳态收益，有限配置不证明最快 |

下一次首个证伪实验：固定同一慢衰减/空段输入，对正确FP32链与精度补偿候选检查state元素和两次变化输入graph，失败即停，避免先投入完整模型性能。若通过，再证明实际模型路径并按三阶段同契约baseline/candidate/revert验证。正式GPQA gate必须独立取得。

OP009新增检查：稳态准入通过后仍检查全部测量轮spread，原BF16回退50.7%输出散差不能以三轮中位隐去；共同波动先查shape/编译/主机/调度覆盖再改kernel。不得用warmup填补失败角色或把TTFT/TPOT代理当纯GDN设备时间。

OP010限域观察（未晋级）：在原FP32链的BF16K=V128/BT64/H8/HV24/C550路径，WY报告256regs/thread/48KBshared，Prefill GPU活动约5.39%；可先试保持FP32/IEEE64-token归约的输出列并行tile，而不改状态递推或累积精度。必须验证原9矩阵/18变化输入graph、完整调用微测、同契约三阶段和原FP32回退；本例共享NFS写满在基线Decode0轮中断，尚无候选收益。GPU活动百分比/静态资源估计不等于criticalpath或spill证据。

若graph前停在torch.cuda.Stream创建，先查进程栈/活动GPU上下文与精确进程归属，区分僵尸PID与活动模型，保留不完整结果；不能用first-call数值pass替代graph，不能据此指认operator缺陷。测量前另核验输出空间；进度JSON原地truncate可能在ENOSPC时损失最后状态，恢复应以原生日志/已存record/精确进程核验，不把空JSON当running或重发相同任务。

2026-10-15 OP010恢复补充（仅micro，E2E待定）：空闲本caseGPU后同9/18数值/graph完整通过，Stream创建等待消失，尚未定位driver根因。保留FP32/IEEE的WY tile32列并行初版WY快38.35%，N8完整调用仅快1.84%，拒绝安装；输出列tile在gridx紧邻的第二版，同形状独立三role微测WY快43.64%、完整调用快13.77%，全部complete输出/state与原版bitwise相等。完整调用baseline/revert微测漂移+3.85%仍保留，不能把两次不同时间微测的差归为严格单变量E2E收益。实际模型双rank命中、全21FG、三phase同契约及原FP32回退仍为后续门禁。grid-order选择应由完整调用验证，不能只按WY耗时或静态occupancy选择。

OP010终态更新（2026-10-15）：新WY实际两rank资源92regs/24KiB、4warps实际256threads；原数值9/18通过，N8完整调用−13.77%只转为Prefill名义+2.361%。87轮完整但三阶段比较均incomplete：PF回退meanTTFT1.010247%、D回退P99ITL2.415935%>1%；Mixed基线实测spread26.781%，原代码回退TPS也+16.705%。因此先定位Mixed完整执行/shape与运行环境差异，不能把它的candidate+18.489%当真实E2E增益。固定末3warm通过不保证后续measured稳态；不删慢轮、不事后替换baseline、不放宽冻结阈值。原FP32/full21保留，候选代码撤回但保存，详见案例主记录；跨平台/shape和数值根因仍未知。


2026-10-16 packed decode补充：在目标服务编译IR中核验dtype、索引类型、QKV rowpitch和SSM pool rowpitch，再建立微测。C550实例如BF16bias/I32index/QKV8192/state401408；padding可能容纳Z/卷积状态，必须保留而非contiguous重排。proxy同shape微测会改变编译/访存，BV32W4的完整调用收益由proxy13.46%变为真实ABI8.29%；15case原容差/变化输入graph通过不等于模型精度或E2E通过。按trace correlation分离steady B64 graph，不能把带prefill的decode窗口全部kernel比例当纯decode占比；packed20.1% work也不等于E2E20.1%。先用独立三阶段与回退判断有效收益，拒绝继续凭spill/寄存器单指标搜索；详见新case证据卡。

当前20FG OP002真实ABI终态：独立三阶段模型Decode输出+1.3902%、Mixed+1.3316%，均未达冻结2%；数值/graph、延迟5%守护、全轮spread10%与回退漂移1%通过，候选仍撤回。真实8.29%完整调用提升不能直接按kernelwork比例推出达标收益；下一步优先补完整Mixed两cohort与CPU/device重叠证据，停止本轮tile/warp搜索。原代码/服务恢复，不改写微测或正式精度门槛。


2026-10-16 当前20FG FP32 JIT补充（`observation`，同C550/FG-vLLM de2298b+私有FP32链，不能外推所有GDN）：Decode专项吞吐暖轮稳定但首个measured TTFT突升时，先用单调时钟还原首token/ITL/cohort并核验新编译缓存；检查已prune为单一FP32配置的H kernel是否仍将不参与数学的N/skew分桶作为constexpr。9个不同cache目录的source与binary完全相同是冗余特化证据，未必是设备kernel计算变慢。本例r7新compile区间与2.203s输出停顿重叠、基线meanTTFTspread13.445%，历史无ranktrace，不能精确分摊全部延迟。

首个验证应限私有副本：只在FP32固定配置成立的边界规范化无用key，检查key-only变化是否还产生不同compile variant；保持数学/FP32、原数值矩阵和变化输入graph、全20FG命中/C8，再在新冻结且所有角色一致的key覆盖/延迟准入下做PF/D/M B/C/R。没有该验证时仅标候选，不能声称已修复；保留旧measured慢轮与10%spread/1%回退/5%guard，超预算保持incomplete。不要把此规则用于仍需不同N/skew调参的BF16路径。

同轮metadata hoist虽然实际消除逐层同步，Mixed仅+0.2646%<2%，已撤回。下一次不要仅按累计D2H等待或消除copy数量推断收益，先量化可消除的criticalpath与现有模型代价；full修复在所有角色共同启用，其微测收益不能和metadata观察值相加。
