# MiniMax-M3：通信显存与KV容量机制诊断

2026-11-04。C588-6为单机16die，C550为mx-101+102双机各8卡，均TP16。本记录承接[历史性能比较](../20261104-minimax-m3-metax-cross-topology/README.md)，分开通信显存探针、历史调度观察与已完成的同机KV因果实验。不是正式精度/性能验收。

## 当前结论

1. **通信路径的显存占用已通过独立探针确认。** C588默认配置在通信前基础占用之外新增约3.916GiB/die；4 collective通道、1MiB缓冲策略为1.359GiB/die，少2.557GiB/die。这里包含MCCL及连接/peer/driver资源，不是单个buffer的容量，也不包含完整模型的graph显存。
2. **较小KV预算的直接计算原因已核对。** 两端权重均约50.409GiB/rank；C588使用0.92、C550使用0.96导致申请预算少2.544GiB，其余activation/non-Torch差异基本抵消，最终KV字节预算少2.534GiB。
3. **容量影响长输入并发的机制有较强证据。** 历史32K/64K的Running分别为C550 4/2、C588 2/1；源码默认在接纳新请求前检查完整输入所需KV页，而非只检查首个prefill chunk。因此KV使用率70%左右，也可能没有足够空闲页接纳下一条长请求。
4. **同机可逆对照已证实KV会显著限制32K吞吐。** C550仅将KV blocks1212降到743，总吞吐2604.33→1757.69 tok/s（-32.51%），Running众数4→2；恢复1212后回到2600.78 tok/s，漂移仅-0.14%。短输入哨兵变化+1.27%。这支持KV是C588长输入性能差的重要机制，但仍未量化历史N128跨硬件差距的精确贡献，不能概括为所有长度都由KV主导。
5. **2026-11-05 只读再归因进一步确认多套通信资源与实际策略差异。** C588 探针先创建/预热 TP、EP 两套 PyNccl/MCCL，再因 MetaX 普通 all_reduce 路由补丁惰性创建 PyTorch 通信器。限制策略仍实际采用 16 P2P 通道、1MiB chunk，而 C550 原模型日志为 4 P2P 通道、128KiB chunk。当前两端 libmccl 与 libmcruntime 字节一致；不能用库版本差异解释，也不能将剩余差额单独归给驱动或拓扑。详见第5节。

C588源服务已在通信探针后恢复原18050配置。C550三角色验证完成后，101/102诊断服务与两个收尾观察器均退出；逐台新核验16张GPU无进程、18150关闭，容器保留，无自动重启。

## 1. 通信显存：分清基础占用和后续延迟分配

在独立优化容器 `e2e-m3-comm-c5886-20261104` 中复用实际 `init_worker_distributed_environment` 和MCCL路径。每策略3组全新进程、每组16rank，所有rank均完成collective端点数值校验。没有加载权重或capture模型graph。各采样在同步、张量释放、GC和empty_cache后进行，最终torch allocated/reserved均为0。

单位GiB/die；表中每个策略48个rank样本取中位数。基础值包含已有设备基础占用和当前进程context，不等同纯context开销。

| 阶段 | 默认通信策略 | 4 collective通道/1MiB策略 |
|---|---:|---:|
| 通信前基础总占用 | 1.504692 | 1.504681 |
| 分布式初始化后总占用 | 4.110428 | 2.407070 |
| 初始化新增 | 2.605730 | 0.902395 |
| 大尺寸TP collective并释放张量后总占用 | 5.420860 | 2.863869 |
| 相对通信前的完整路径新增 | 3.916161 | 1.359184 |

默认策略完整路径增量min/max为3.916130/3.916180GiB；销毁通信组释放约3.886936GiB/die。这提供了通信生命周期与显存变化的直接证据。实际库为 `libmccl.so` 的MCCLLibrary，位于Plugin MetaX pynccl_vllm024 backend。

原生日志确认默认为32 coll/32 p2p通道；限额策略实际为4 coll/**16 p2p**通道。虽然MAX_P2P_NCHANNELS=4被读取，实际P2P仍为16，不能按环境值假定只有4条连接。

默认策略在初始化后又增加约1.310417GiB：首个TP collective约0.684959、大payload约0.625458。这个量级与真实模型历史profile期non-Torch增加1.351–1.353GiB一致；但合成探针和完整模型不是同一运行，不据此宣称精确归因比例。

省下的2.556992GiB中，约1.703358发生在init_snapshot之前、约0.853634发生在之后。前者影响启动空闲显存门禁，后者才进入当前的profile增量扣减。因此**不能在固定0.92的旧KV预算上，直接加回全部2.557GiB**。4通道策略也尚未经过模型吞吐、graph或精度验证，不是已保留优化。

## 2. 为什么0.96启动受限、KV预算少

实际Plugin在通信初始化后采init_snapshot，要求 `free_memory >= total_memory × gpu_memory_utilization`。历史C588单die可见总量63.59375GiB、初始空闲59.48654GiB；0.96要求61.05GiB，差约1.56346GiB，无法通过这一启动门禁。这不是“未对齐参数”，而是0.96在该初始状态不可行；也不是对用户当时OOM栈的重新复现，不能将0.92说成唯一可行值。

实际预算为：

`KV = requested_memory − weights − peak_activation − post-init non-Torch increase − applied graph estimate`

按每端最小KV预算对应的限制项，C550减C588，单位GiB/rank：

| 预算差分项 | 对C550更多KV的贡献 |
|---|---:|
| requested_memory：0.96 vs0.92 | +2.543750000 |
| 权重相同 | 0 |
| C550 activation peak更大 | −1.246410370 |
| C588 post-init non-Torch增加更大 | +1.237068176 |
| 合计 | +2.534407806 |
| 实测KV字节预算差 | +2.534407806 |

两端最小KV预算分别6.548958/4.014550GiB，差分完全对账。显存比例仅差4个百分点，却对应原C588 KV预算约63%的大小，原因是权重已占掉绝大部分显存，KV使用的是较小的剩余空间。

限额通信探针的初始空闲约61.18668GiB，使0.96初始门禁仅剩约0.13668GiB余量；**这不证明完整模型0.96能稳定启动或运行**。后续临时峰值、graph和allocator仍须真实服务验证；graph estimate字段为0也不代表实际graph占用为0。

## 3. 历史吞吐与调度：以C550为基线

统一P1K/4K/16K/32K/64K，D1024/C64/N128，历史两计分轮SUMMARY。总吞吐单位tok/s；Running列是引擎请求数中位数，不是精确每step GPU batch。TTFT/TPOT均为客户端代理，包含排队和mixed干扰，不能作为纯设备prefill/decode时间。

| 输入 | C550总吞吐 | C588总吞吐 | C588相对C550 | Running，550/588 | mean TTFT秒，550/588 | mean TPOT毫秒，550/588 |
|---|---:|---:|---:|---|---|---|
| 1K | 1041.13 | 1000.70 | -3.88% | 64 / 49 | 3.49 / 5.11 | 119.50 / 103.66 |
| 4K | 1577.11 | 1357.74 | -13.91% | 31 / 19 | 78.27 / 121.10 | 101.89 / 71.81 |
| 16K | 2025.56 | 1941.83 | -4.13% | 9 / 5 | 358.86 / 396.90 | 68.75 / 41.43 |
| 32K | 2445.62 | 1996.66 | -18.36% | 4 / 2 | 630.36 / 790.80 | 48.75 / 30.11 |
| 64K | 2497.82 | 2050.63 | -17.90% | 2 / 1 | 1250.96 / 1539.49 | 42.54 / 25.64 |

32K的C588有418/432个活跃采样Running=2，C550有325/353个为4；64K的C588有818/818个为1，C550有642/680个为2。因此并发差不是单个瞬间。C588 32K/64K最大KV使用率71.2%/70.1%，仍存在大量Waiting；C550相应为87.2%/85.9%。

当前源码 `SchedulerConfig.scheduler_reserve_full_isl` 默认True，实际启动未显式覆盖该项。Scheduler将此开关传入 `KVCacheManager.allocate_slots(full_sequence_must_fit=...)`；该函数先按整段输入计算各KV组所需页，与free blocks比较，放不下则返回None，Scheduler停止接纳该请求。块分配还要考虑组/块对齐，不能只看平均百分比。这里是源码默认＋实际启动配置的核对，没有读取live Python scheduler对象。

还需收紧一个解释：`GPU KV cache size`在当前源码中定义为 `int(max_concurrency × max_model_len)`，max_concurrency按不同KV组的page需求计算。因此95,082/155,136是分组感知的等效token容量，**不能把它们无条件当连续token池并用除法精确预测每步并发**。后续A/B须保留实际KV groups/blocks和Running数据；单纯相同kv字节也须验证产生了何种实际容量。

Prefill/排队：C588 TTFT较高与接纳较少、等待较久一致，未证明prefill kernel本身较慢。Decode：C588 TPOT更低，但batch也较小，不能称为同batch硬件加速。Mixed：C550更高并发提高总吞吐，同时TPOT/尾延迟可能较高。16K的Running差较大而总吞吐仅低4.13%，已经说明容量比例不能直接换算为吞吐比例，不能对所有场景用一个“主因”比例概括。

## 4. 同一C550机器上，只改KV容量的可逆对照

在mx-101+102双机TP16上使用独立容器，CPU/GPU/驱动、模型/源码、graph、通信均固定。三角色稳定身份经比较器复核，唯一差异为`/launch_config/num_gpu_blocks_override`。baseline1212 blocks → small-KV743 → revert1212，实际等效容量155100→95082→155100 tokens。maxlen统一70000，BF16 KV/index、MBT8192、seq64、四通道1MiB/IB、prefix off不变；这是新受控基线，不能与历史C550 maxlen131072的吞吐拼接。

本次模式targeted、scope performance_only。为尽快归还资源，在任何测量前冻结长输入P32768/D1024/C64/N4、短输入哨兵P1024/D128/C64/N32，分别映射原P32K/P1K目标。每角色独立服务、每场景3预热/2计分，末2预热跨度≤5%、计分波动≤10%、baseline/revert漂移≤5%。没有删除慢计分轮，两个原生比较均passed。

| 指标 | C550大KV基线 | 同一C550小KV | 恢复大KV |
|---|---:|---:|---:|
| 32K总吞吐，tok/s | 2604.33 | 1757.69 | 2600.78 |
| 32K输出吞吐，tok/s | 78.92 | 53.26 | 78.81 |
| 32K完整批次，秒 | 51.90 | 76.90 | 51.97 |
| 32K mean TTFT，秒 | 12.062 | 26.151 | 12.018 |
| 32K mean TPOT，毫秒 | 38.763 | 31.878 | 38.878 |
| 32K活跃采样Running众数 | 4 | 2 | 4 |
| 1K/D128哨兵总吞吐，tok/s | 2995.90 | 3033.89 | 3010.93 |

小KV的32K吞吐下降32.51%，恢复大KV与原基线只差-0.1365%；短输入哨兵变化+1.2680%、恢复漂移+0.5015%。长输入计分窗口Running=4占基线37/50、恢复37/51个活跃采样；小KV Running=2占67/75，未观察到Running>2。三角色长短场景计分累计抢占均0，因此这里主要表现为接纳/驻留并发受限，没有看到靠抢占/重算反复腾挪KV的证据。

Prefill/排队代理：TTFT从12.06增加到26.15秒，支持接纳不足造成后续请求等待；不能据此说prefill kernel变慢。Decode代理：TPOT从38.76降低到31.88毫秒，但Running减半，较小batch每步更快仍无法弥补并行请求减少。Mixed：完整批次51.90增加到76.90秒，总吞吐下降，短输入基本不变且恢复大KV后回升，形成容量影响吞吐的直接因果证据。

结论范围：已实锤KV容量可造成这类长输入吞吐下降，无需更换CPU或GPU就能复现；它是解释C588长输入较慢的重要机制。**32.51%属于本N4受控场景，不能直接抵扣历史N128下C588低18.36%的差距，也不证明所有长度的主要原因相同。** 若要量化历史差距的精确贡献，仍需匹配N128场景及C588当前基线。

三角色各17条固定算术C1/两批C8检查通过，PIECEWISE/FULL原生capture完成；没有项目GPQA10题完整baseline-sanity或正式精度gate，也未单独采集replay计数，因此不是正式精度/性能验收。4通道策略在C588仍只验证了通信显存，不能直接当成已通过完整模型吞吐和精度的优化。

计分采样按原生结果date结束时间减duration对齐（结束时间1秒舍入、2秒采样），避开共享FS mtime约229–230秒偏移。当前C550驱动101=3.3.12、102=3.8.1，在三角色间固定；未修改驱动或任何推理源码。

## 证据与当前状态

独立模型记录：[C588通信/分析](../../../models/MiniMax-M3/metax/20261104-comm-kv-c5886/optimize/README.md)、[C550容量实验](../../../models/MiniMax-M3/metax/20261104-kv-c550101102/optimize/README.md)。两案例的image_lineage和mount_parity均通过，C550101曾出现的首次挂载不一致已作废并重建，未用于测试。

C588远端case `/data/jinghao/minimaxM3/20261104-comm-kv-c5886`：通信rank JSONL和日志在results/与logs/；精确通信汇总SHA `da6f955b6a534d73758cd179a9f824b0f7b3d7d938e71e99930a5fc5999c78bb`。本次只读源码摘录、历史JSON输入与计算结果在 `results/analysis-20261104/`，最终analysis SHA `83093787a4507ab4197f8c757ae54ddb1d7d27654e4a6fe994ca4a0b400504d4`，归档清单保存逐文件SHA。

实际worker.py SHA `bdbec6c8204f05d861f3edcc5ef21bb87ee5cbfce943bc756bf13206834064de`；kv_cache_utils.py `3ca561818019cef84c43c6d3839627145fd049f9479d40fc733ae142d6d71df3`；scheduler.py `df78076164fe02a63876d7690cefac810f1ba4d8fb58afc15e786c1608064090`；kv_cache_manager.py `2e91e77f84dfd9d4bed79f50392be72559207f54e845a3d3402baf88dc529320`。源服务恢复回执和C550最终停止回执在两案例state.yml中。C550原始run-record位于`/public-flash/jinghao/minimaxM3/20261104-kv-c550101102/performance/quick02-<baseline|candidate|revert>-<long|short>-v5/`。聚合`results/quick02-results-summary.json` SHA `4f2b3b564578339ad885fca8b7f530d65fb8c32e5d13d7e322c51dd607fb9fc8`；两个comparison SHA分别`e3bd59be54d32cfdb0d373624d29a7537ecbe7bce24c86e337ee419bc9e482b7`、`c3f98d5cb2af5a572e8563cc846cf69c33800413e3010836fae342a09b9a8bf0`。最终释放新核验回执为`manifests/quick02-final-release-mx-101.json`与`mx-102.json`，SHA分别`60d30d5292f0e8f3d42f1ad4c75e705bbd1fb593fb6ff29ac9351fb681930420`、`ccd6d0291ee57508b54c4069873ee80630ad6f1fde3ef11d7a9ee3372772aadc`。

结论边界：通信显存机制已测得；KV预算差已对账；同C550硬件上容量导致32K并发与吞吐下降的效应已可逆验证。历史N128精确贡献、同batch计算/通信耗时、C588完整模型限通信通道后的效果及正式验收仍未完成。C550服务和后台观察器均已退出。

飞书[定位文档3.5](https://jwolpxeehx.feishu.cn/docx/DuwsdmPo7oi979xodNac0OVknab#TABCdyU3QoDIMWxkx9acLWmQnzb)已同步更新3.1总论、3.4通信实测和3.5容量对照；界面已显示保存到云端，表格与正文已可见核验。

## 5. 2026-11-05：为什么 C588 通信显存更多

本次为只读再分析，没有运行新通信探针、修改生产环境或重启服务。重新读取既有 6 组探针的全部 96 rank JSONL、原生日志，以及 C550 原服务两节点日志、启动脚本和当前源容器文件。C550102 源容器已停止，使用 docker cp 流式读取指纹，未启动它。

### 实际生效的通信策略与资源规模

| 项目 | C550 原测试 | C588 默认探针 | C588 限额探针 |
|---|---:|---:|---:|
| 节点/本地 rank | 2×8 | 1×16 | 1×16 |
| collective 通道 | 4 | 32 | 4 |
| P2P 通道 | 4 | 32 | 16 |
| P2P 通道/peer | 1 | 4 | 4 |
| P2P chunk | 128KiB | 1MiB | 1MiB |
| BUFFSIZE 配置 | 1MiB | 未显式设置 | 1MiB |
| 原生 Init COMPLETE 的 typical used/rank/comm | 8.085MiB | 686.338MiB | 430.050MiB |

最后一行是 MCCL 自己报告的初始化统计，不能与设备 free/total 的总占用重复相加。C550 原生 used=8,477,344B；C588 默认=719,677,056B、限额=450,940,256B（rank0 有少量额外开销）。C550 另外显式启用 tuning-ar512k.cfg；C588 探针基础通信环境仅 DEBUG=INFO，因此相同 BUFFSIZE/MAX_NCHANNELS 并不等于完整通信策略相同。

通道/缓冲策略的同机可控效应已由既有探针实测：3.916161→1.359184GiB/die，减少2.556992GiB、约65.29%。但该对照同时改了 collective 通道、BUFFSIZE、P2P cap，不能单独给每个变量分配收益。限额后实际 P2P 仍16通道，证明不能把环境 MAX_P2P_NCHANNELS=4 当实际4通道。单机16本地rank与双机每节点8本地rank下的连接/协议资源规模不同，是剩余差额的有依据解释；拓扑、tuning和驱动各自贡献仍未独立拆分。

[沐曦 MCCL 编程指南](https://developer.metax-tech.com/api/client/document/preview/467/C500_MCCLProgrammingGuide_CN.html) 4.2.1.6 说明 BUFFSIZE 控制 GPU 对之间 Simple 协议缓冲；4.2.2 说明 collective/P2P 通道等参数。其语义用于解释多通道/多连接开销，文档默认值不替代当前运行时测量，更不能直接用 NCCL 默认值推算 MCCL 分配。

### 框架为何同时保留三套通信资源

实际 MetaX `pynccl_wrapper.py:464–470` 为 TorchDynamo 可追踪性，将 CudaCommunicator.all_reduce 替换为 `dist.all_reduce(..., group=self.device_group)`。但原生 CudaCommunicator 构造仍为 TP/EP 各建立 PyNccl，`pynccl.py:135–145` 在构造时分别调用 CommInitRank 并 warmup 一次。

原始事件确认 TP、EP 均为16rank，PyNccl serial为0和1；默认策略各自构造含warmup的设备增量中位数为1.309414/1.298256GiB，单例 DCP/PCP/PP/DP 组没有可测增量。构造结束清理 PyTorch cache 后，合计通信新增约2.605730GiB。之后普通 TP all_reduce 走 PyTorch group；默认首轮原生日志有48个16rank初始化/通道事件，匹配每rank共3套原生通信器，且Python PyNccl构造只观察到2套。第三套在首次正常TP collective处惰性出现；大payload继续使资源实例化。

| 生命周期增量，GiB/die | C588 默认 | C588 限额 |
|---|---:|---:|
| 初始化结束的通信新增（TP+EP PyNccl，已清理Torch缓存） | 2.605730 | 0.902395 |
| 后续普通TP collective路径新增（含第三套及大payload资源） | 1.310417 | 0.456783 |
| 全路径新增 | 3.916161 | 1.359184 |

此为分阶段物理显存差分，不是allocator逐笔分配栈，因此不能将每字节全标成第三个communicator buffer。三套路径是当前共同框架设计，会累积各自资源；它不是C588特有的框架差异。TP/EP PyNccl 可能用于其他collective，未证明整体无用或可安全关闭。销毁组释放约3.887GiB/die，支持资源与通信生命周期相关，不是仅凭empty_cache后不下降就判泄漏。

### 二进制核对与尚未闭合的归因

当前 C588 源容器及两台 C550 源容器中的 libmccl.so SHA256 均为 `e6c7ab02b7d329a3e178aadf0e7d638cb7f36909cc22bbd18d25bdfd544057b6`，libmcruntime.so 均为 `f41fb86c7634c79b1c53910beb7beab540f345499659f462563b1db028291cb8`。两端原生日志均为 MCCL2.16.5。当前文件相同不倒推历史运行文件绝对相同，但没有“当前库版本不同”的证据。C550102 的 pynccl_wrapper.py SHA 与 C588 相同，为 `977a9c37e7bd1335301eda53dbe031f24c04d8e952a9917535bffb82e41d4491`。

目前可确定：空载每die预占不是主要解释；通信策略可控项贡献已实测，多套通信器累积开销已核验，P2P资源选择差异有日志证据。还不能唯一判定剩余430MiB/comm级初始化统计由MCCL某缓冲、peer/IPC映射、驱动或MCM专用通道各占多少。需要 ALLOC/调用栈或严格单变量探针才能继续拆分，不能用公开指南默认值乘通道数伪造精确分解。

新分析及完整只读摘录保存在 `/data/jinghao/minimaxM3/20261104-comm-kv-c5886/results/communication-causes-20261105/`，总论 `communication-causes-20261105.json` SHA256 `0c966993a6871d33e4a24cd0440ac2afc752203a553736ceeccbb242667b5d94`；归档命令 `commands/archive-communication-causes-20261105.py` SHA256 `c12e1b93845b3278e8081f6f76a040a84be9f06147741bdbf0a7f381965f95d0`。旧结果、源码和服务不变。

2026-11-05 按用户要求已汇总到[飞书定位文档](https://jwolpxeehx.feishu.cn/docx/DuwsdmPo7oi979xodNac0OVknab)新增“3.5 为什么 C588 的通信显存更多”。包含实际通道/P2P参数表、2.557GiB/die配置效应、三套通信器路径、0.96预算解释、二进制一致性及未闭合归因；新增内容仅使用机器型号。已通过页面正文和参数表核验，界面显示“已经保存到云端”。截图保存在 `/private/tmp/minimax-m3-comm-causes-feishu-20261105.jpg`。
