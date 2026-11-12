# fgv-moe-main-config-001 主线TP2配置定向迁入

状态：已在59完成同镜像验证并原子写入用户指定的qwen36-35b。用户将自行跑端到端性能，本任务不启动模型或全量评测。

## 优化方向与依据

PR1067实测证明旧设置不优于当前主线；用户明确选择“沐曦59的qwen36-35b”，104完全不改。最新主线016dac84的MoE文件仍为此前59验证的9de7b6eb。

## 优化内容与适用边界

原文件c4673aea，候选22670fd3。复制主线_is_qwen_tp2_moe_shape/_qwen_tp2_config两helper，限C550、E256/H2048/I256/topk8、FP16/BF16、无block/INT8/批次不变开关，embedded配置优先级不变；非目标退回原局部配置。增加一个可选内部INT8 guard参数传递避免把量化误当普通half。

旧消费者不能识别主线UNFUSE_SILU，因此同步最小host消费：取出标记、验证与共享alignment相同BLOCK_M，并走已有独立激活路径。其余Triton kernel、所有module globals、公共算子API、路由/归约/缓存实现、GDN/采样及其他库保持不变；不整仓升级，不改启动脚本和推理参数。

## 正确性与命中

262152组目标配置与固定主线逐字典相等，1720组非目标/量化/block/device/batch-invariant保持旧值，embedded优先及copy通过，0GPU CPU配置证明不替代硬件。初版AST审阅因添加函数导致匿名节点序号位移而误报，未产出/执行候选；改用命名函数和非函数节点序列比对后确认仅三个host函数变化，全部kernel与globals不变。

计划59同镜像新独立容器、私有FGV副本，仅候选文件变化，25项公开API独立FP32数值和每项两次变化输入Graph，包括全部主线配置分段边界、均匀/集中和FP16哨兵。通过后再归档59目标容器保护清单和旧字节，CAS SHA原子写入，仅此文件允许变化。用户服务保持未启动，实际模型精度/端到端收益待用户新测，不复用旧gate。

## 性能与交付

不新跑性能。只准备用户指定环境以便其自行测量。失败按精确源SHA回退，保留错误和独立原始产物；不对用户其他容器、GPU任务或共享启动脚本操作。

## 外部证据

59应用及兼容性统一ROOT：/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001。
待归档59：/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001。

## 同镜像兼容性实测与应用前记录

已归档并执行verify-ported-gpu-002.py（92d4621c），新专用容器与用户目标的两项bind mount逐项相同，私有FGV副本；25数值测试和50次变化输入Graph全部通过，模型请求0，专用容器已停止。准备执行唯一apply-main-config-host-001.py（e950332d）/apply-in-container-001.py（9fa307da），精确59目标ID及旧SHA保护；备份旧字节并比对FGV/Plugin/Gems/vLLM全部源码，只有目标MoE文件允许变化。

## 最终交付与边界

应用原生exit0，公开API实际加载目标文件，C550实际selector在BF16/FP16、GEMM1/2、fast/nonfast共72组与主线helper相符，目标没有embedded配置覆盖。6559文件的前后SHA/权限/owner清单仅目标MoE文件变化，其余6558保持；目标源码新SHA22670fd313b0d6a30cfc019924be6a941427e5809ea0306fcac762f0d12e20d1。25个GPU测试58.26秒完成，50次变化输入Graph均通过；这是算子兼容性，不是完整模型精度或TP2服务验收。

原生应用command SHA34866a8fb0fb3189496af9f591ee0e3269fa60b7b06c55fdc404cea492a19b52；application.json SHA087f3076a2e78f07134f4149733ece6029d266fabe30f20891a1df6add386338；实际公开导入与配置证明SHAe4126bd229a40cffca4620aeb834382cfd878b9cee8062a5e7685f89f7012e6c。完整证据位于ROOT/application-001/{application.json,final-verification.json,actual-import-config-proof.json,protected-before.json,protected-after.json}。

可回退旧字节：ROOT/application-001/fused_moe.before.py（c4673aea）。回退前须精确确认同容器、无服务或另获服务操作授权，且当前目标仍为22670fd3；只恢复该文件，不覆盖其他代码。当前用户容器保持bash空闲，验证容器已停止，无模型请求/启动/重启；启动脚本未改。用户用原启动方式新启动即加载新配置，端到端收益和完整模型精度待新测，无新gate。主线helper按原AST移植，旧kernel及module globals不动；此最小旧路径兼容保留而非整仓目录/API迁移。

## 用户 opt5 端到端结果接续审阅（执行前）

用户提供opt5与retest两组性能，明确retest的P16K为测试问题并排除。仅只读消费已有结果，主指标稳态总TPS；保留所有轮次与原SUMMARY，不新增benchmark、profiler、模型/管理请求或服务/源码操作。核对实际长度/请求/采样/运行身份及Host，阶段指标仅作客户端代理。历史跨Host或稳态不足不能当主线配置单变量因果收益。新唯一证据目录ROOT/e2e-comparison-001，分析脚本先commands唯一归档SHA再执行。

## 用户 opt5 端到端复测结论（2026-11-04，只读）

明确排除用户指出的retest P16K测试问题，该原文件仍保留。两组CSV的其余四场景均D1024/C64/N128、每轮128成功、输入/输出总token计数一致。opt5原生perf.log交叉核验15个完整bench、每个128成功/0失败；命令为random、ignore-eos、无限速有限批次、每场景3轮、SKIP_FIRST=1；native num_warmups=0并有单请求initial test，无预冻结稳态准入，save_result/save_detailed均False，不能补造逐请求JSON或正式比较契约。

| 输入P，D1024/C64/N128 | retest全部3轮总TPS均值 | opt5全部3轮总TPS均值 | 观察变化 | 边界 |
|---|---:|---:|---:|---|
| 1024 | 2777.65 | 2156.93 | -22.35% | 两方短程过渡/不稳，不作稳态收益 |
| 4096 | 4358.46 | 5211.50 | +19.57% | retest第2→3轮3352.62→6271.68，不作稳态收益 |
| 32768 | 10920.01 | 10901.20 | -0.17% | 三轮接近；跨Host观察，非单变量因果 |
| 65536 | 9463.44 | 9383.47 | -0.85% | 三轮接近；跨Host观察，非单变量因果 |

原SUMMARY口径（Run2/3均值）P32K10952.51→10944.45（-0.07%），P64K9464.27→9391.24（-0.77%），方向与全三轮一致。P1K SUMMARY3095.10→2239.65（-27.64%），Run3也3171.76→2388.86（-24.68%），而opt5 Run2/3仍差约13.32%；不能一概称“所有场景差不多”，但也不能将该跨Host不稳差值全算为配置回退。P4K旧SUMMARY4812.15混入慢Run2，制造opt5 +23.68%表象；末轮6271.68→5954.30（-5.06%）仅为诊断点，不能挑出来补签稳态结论。

### 已生效和未改变的限制

目标文件当前仍SHA22670fd3。现服务启动日志的实际GEMM1 M8192为BK128/warps4/stages4/cpasync、fuse_silu=False；旧retest留档是BK64/warps8/stages2、fuse_silu=True。GEMM2的groupM由1变8。因此不是仅磁盘上补丁未载入；这两条只证明已记录的worker/shape，不伪造两个rank所有Decode shape的动态函数读取。

两组服务的KV容量都1,786,116tokens。KV>=99%且Waiting>0时，opt5有90个采样（Running49出现44次，Running26出现46次），旧retest有88个（43/45次）。两者长上下文驻留受限状态相同；Running是调度请求数，含Prefill/Decode，不是直接设备batch shape。KV预算/排队限制没变与长上下文TPS没有明显变化一致，但没有设备阶段trace/同机受控对照，不能给MoE或KV分别算精确耗时贡献。

Prefill代理：P32K SUMMARY meanTTFT61.90→61.71秒；P64K237.98→239.52秒。Decode代理：P32K meanTPOT120.23→120.47ms、medianITL49.00→50.18ms；P64K154.74→156.04ms、44.96→45.77ms；没有稳定阶段收益。P1K末轮TTFT1.696→1.688秒接近，而meanTPOT38.68→46.03ms、medianITL37.16→39.98ms升高，下一步优先小M Decode/尾部，而非把冷启动当目标。以上指标都含调度/排队/通信，不是纯GPU阶段时长。

静态配置比对进一步确认：M64两GEMM主要是stages2→3；M<=32另有BN128→64等差别，M<=8也改变BK和GEMM2 swap选择。大M主线参数在旧host上经UNFUSE兼容切到独立激活；它是否带来净收益依赖现有kernel及完整调用开销。前次PR参数对照位于主线实现，不能直接外推到旧kernel仅迁入主线配置的整模型。本轮兼容性已通过，E2E收益没有兑现。

### 决定、证据和下一步

此次只分析用户已跑结果，不新增模型/管理/benchmark/profiler请求，不重启、改源、回退安全KV预算或改变0.9；当前服务及配置保留。新结果来自mx-59，retest来自历史mx-104，C550同类硬件也不等于同机受控A/B。下一步如继续，应在59同GPU4/5按旧配置→新配置→旧配置、相同服务参数和充分稳态准入，先分离小M Decode与M8192 Prefill，再用同Mixed守护；不直接继续盲改tile或签正式性能收益。

ROOT/e2e-comparison-001保存原始CSV、service.log、client perf.log、旧service/client日志快照、collection.json、analysis-001.json及config-selection-diff.json。collector SHA9d996442b5a104389763df2ead3c1c46249cb4d9853bf92ca09d83f7c59259e5、analyzer SHA21055c16e5d8a33fda02d9937e910110c9e4321c17ca8cfa01bbfd6efc9ea667，均唯一归档后执行exit0，不重放。两边共同的FA2不可用探测日志已保留，不将这个共同背景日志冒称新增回退原因。

collection.json SHA8656c72632f2d637f8007cc8c82493abaabec98aced8245999b0e34183a84441；analysis-001.json SHA4f5605fc5eecee08e66d40bb865070219f3568cfa340ec13b5e5ba37491cbd0a。

## 59同机旧→新→旧1K短程诊断（执行前冻结）

用户明确要求在59 qwen36-35b执行，允许当前目标服务切换，作为原容器保护规则的本次限域例外；保持所有原argv/env/cwd、GPU4/5、0.9、prefix-off、TP2/graph64和GDN/采样。GPU0/3外部任务保留。仅MoE文件c467↔2267；maintained performance runner/compare逐字节归档，targeted/performance_only，不跑精度/其他上下文、不采profiler。

P1024/D1024/C64/N128与父目标相同，client temp1与真实默认相同、top_p.95/top_k20由服务保留，seed固定配对序列；每角色4预热+3测量，末2预热TPS spread<=3%，测量3轮spread<=5%，旧/回退漂移<=3%，全部轮次保留，不择优。Prefill/Decode用同Mixed的TTFT和TPOT/ITL代理，含排队/调度/通信残余。源6559保护清单及真实API身份先准入，再开始唯一controller；native dry-run先通过。

若完整且漂移有效的对照复现新配置下降>=3%，预先限定停止本角色服务后再做public MoE接口M8/32/64/128、BF16、固定合成均匀top8的旧/新/旧Graph微测；该数据不冒充实际模型路由/纯单GEMM归因。每个新服务有native graph capture及两次C8多token最小资格；最后finally恢复新配置与原模型参数、独立日志。任何已发性能请求的失败或不稳均保留，不重放同一run。

### 首组准入失败与形状冷路径发现

controlled-1k-001 nativeexit2：旧配置4轮全部128成功，但后2预热TPS2889.63/2159.40，spread28.93%>3%，0测量轮/新与回退未发，原始全部保留；已独立核验恢复new/原argv/env/cwd/6559源码。正常ITL约41ms，慢轮分别有20.79/32.38秒全流无token事件停顿；较快第3轮没有>0.5s全流间隙。

活跃缓存不是镜像遗留/root/.triton/cache，而是/tmp/torchinductor_root；首4轮580项新kernel metadata中560项_guarded_sweep，第二/四轮每个3.4–4.6秒停顿对应约16–18项该kernel新metadata。其M为constexpr，PASS0..7逐次launch，即使GPU失败标志使fallback跳过，首次CPU JIT仍会发生。该证据支持采样按实际行数冷编译影响finite-batch收尾，不是LibTuner显存修复回退。单独/root/.triton无新条目不能代表没有编译；原始冷缓存负证据保留。

新唯一followup保持所有推理代码和启动参数、同一seed策略，统一增加真实接口cohort64..1、每个重复2次、D8采样的形状预热，再2完整P1K预热+3测量，保持3%准入/旧回退漂移与5%测量spread；不修改采样、GDN或benchmark工具，不关闭调优器，不丢弃旧首组失败或补写成功结论。归档新plan/controller后再唯一启动旧/新/旧，末尾恢复new服务。

## 同机受控对照终态与独立复核（2026-11-04）

在59的同一个`qwen36-35b`、GPU4/5上完成旧→新→旧，最后恢复试验前的新配置。`controlled-1k-followup-001`原生exit0、summary completed/error/restore_error均null；maintained原生比较与独立重算均passed，scope为targeted/performance_only。独立新GET models/metrics exit0，running/waiting均0；没有新生成或管理请求。

每角色统一真实请求cohort64..1、各2次、D8采样形状预热，再2完整P1K预热+3测量，最后2预热spread<=3%、3测量spread<=5%、旧/回退漂移<=3%。请求cohort不是每步设备batch计数；最终用原生缓存与请求时间线独立检验冷路径是否还进入测量。首失败版本不覆盖、不挑轮、不从时长中扣掉停顿。原始client seed序列、P1024/D1024/C64/N128、ignoreEOS/temp1/top-p.95/top-k20、全部服务argv/env/cwd、TP2/0.9/prefix-off/graph64、GDN/采样均保持。

| 角色 | 三轮总TPS，tok/s（全保留） | 中位数 | 组内spread | mean TTFT代理中位数ms | mean TPOT代理中位数ms | median ITL代理中位数ms |
|---|---|---:|---:|---:|---:|---:|
| old1 | 2907.06, 2905.34, 2920.48 | 2907.06 | 0.521% | 1740.524 | 42.301 | 40.943 |
| new | 2991.22, 2982.58, 2972.17 | 2982.58 | 0.639% | 1682.126 | 41.266 | 39.560 |
| old2 | 2892.56, 2894.62, 2887.26 | 2892.56 | 0.254% | 1743.223 | 42.516 | 41.326 |

新配置相对首旧配置+2.5978%，旧/回退漂移-0.4989%；三组15个native轮次主请求各128成功/0失败，9个测量轮共1152主请求。新配置没有复现退化，预声明的>=3%回退触发条件未满足，因此没有再做public-MoE GPU微测。仅本机/此栈/此P1K finite-batch的诊断，不是持续容量或完整四场景验收；无新完整模型精度gate，不将+2.60%升级为所有场景收益。TTFT/TPOT/ITL含主机、排队、调度、采样与网络残余，不是纯设备分阶段时间。

### 具体原因：动态形状首次JIT混入了原测量

原失败旧配置第2轮111.12秒中有20.79秒全流无token事件间隙，第4轮121.40秒中有32.38秒；主要间隙为3.4–4.6秒，发生于batch收尾/补入时。第3轮没有>0.5秒全流间隙、没有新kernel metadata，TPS2889.63。终态独立分析直接重算原raw start_times/ttfts/itls，事件包络与native duration差约1ms；这是客户端事件重建，不冒充GPU空闲trace，也不据此调整TPS。

活跃缓存`/tmp/torchinductor_root`的四个timed区间有558项新`_guarded_sweep`元数据（336/94/0/128），另有copy、MoE align和scan首编译。此前带边界窗口的560项计数保留为不同时间口径，不能混作严格timed计数。绝大多数3.5秒间隙与16–18项该kernel元数据新建对齐；逐项JSON元数据已复制为独立冻结快照并保存SHA。

源码里采样fallback的M/PASS是constexpr，8个pass仍由CPU逐个launch；即使设备flag让fallback工作跳过，第一次遇到新M仍需准备其JIT specialization。模型Graph capture与贪心C8不覆盖这条采样冷路径，所以跳过第一轮或盲跑几轮不能保证尾部所有M都热。该现象属于首次JIT/装载准备，不是证明LibTuner重复跑GEMM候选或原显存引用修复失效。

保持所有推理代码不变、只统一形状预热后，15个followup轮次无新`_guarded_sweep`metadata；9个测量轮无任何新kernel metadata、无>0.5秒全流间隙，最大间隙仅0.4441秒。原生TPS恢复到约2.9k且旧/新/旧漂移有效。这确认本栈存在预热遗漏的测量干扰，排除了本次MoE配置迁入造成历史那种20%–30%稳态降速。历史opt5/retest跨Host且未保存逐请求明细，不能将每一分历史gap都唯一归给该机制。

### 路径与恢复

已停止的三组服务原生两rank日志均有实际M64 GEMM1/2：旧stages2→新stages3→旧stages2，BM16/BN64/BK64/warps4保持，证明实际配置已切换。不是只比磁盘字节。源码6559文件仅目标MoE允许c467/2267切换；末尾已完整恢复22670fd3，与初始NEW全清单一致，GDN/采样不变。

恢复服务已通过自己的Graph capture、两次C8多token资格及同样形状预热；活跃恢复日志仍可能有worker stdout缓冲，不能伪造所有rank的实时函数对象或callee日志读取。独立fresh核对精确API PID/start_ticks/argv/cwd/选定env和源清单；权重身份是名称/size/mtime加小文件字节与tokenizer字节，不冒充整权重内容hash。`start-model-flagos.sh`未改。当前服务日志：`/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/restored-new/service.log`。

首次发现活跃缓存的临时只读命令仅新建目录清单，未预先归档执行副本；原清单和早期错误root负证据保留。上述终态timeline/cache核验器则已唯一归档SHA后执行，重新读取并冻结真实元数据，没有重放任何模型/管理请求。最终报告回收一度较慢，改用紧凑只读摘录；原完整回收随后也完成，健康检查仅执行一次，没有重跑。

### 证据与规划复盘 main-config-review-002

证据截止：2026-11-04T21:21:38.563375+08:00。

- `native-result.json` SHA `9b093f50bbff40d86a6cb421dfbcc9a6787d638c2cda49f4391029374a158cf3`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/native-result.json`。
- `summary.json` SHA `68b5bbcd0d5ffdc3fd2bc08c7f18b94033de8306e8109ae93fe8c59b787252bc`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/summary.json`。
- `comparison-result.json` SHA `183ababbae2ff5bf745b7a427a5c594c96276dcc2fafd84e922516692e097a6f`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/comparison-result.json`。
- `independent-verification-001.json` SHA `4c787e3874aa8365091b53d7ba81336bc3da2af63bc8b0ca5f57609039280467`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/independent-verification-001.json`。
- `fresh-http-001.json` SHA `d1a2cab5558601e60a7a30d5c3c371b5d33e9549b3efc81965938be3c3f6eb51`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/fresh-http-001.json`。
- `fresh-http-001.result.json` SHA `6f3b805e4e667ffe4108056fa91a5dc4487689f31f77e1d574f416c9219864f2`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/fresh-http-001.result.json`。
- `execution-plan.json` SHA `53557fe79a8a2522fb18d26f55d52d7d49e87134ba81b0847df659de8a37fa8a`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/execution-plan.json`。
- `final-independent-command.json` SHA `5e831982d28c770835b6b0259ad1b0f370d01a32d8735087ea6e523bfc46c65c`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/final-independent-command.json`。
- `independent-timeline-cache-001.json` SHA `f9ec2d8931a9712e1b0a5eda89f43a5567e05931cc5c28a42faa58830c74ea88`，远端 `/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/controlled-1k-followup-001/independent-timeline-cache-001.json`。

本优化点依赖顺序：同镜像25数值/50变化输入Graph兼容验证→用户现栈主线配置迁入→首组稳态准入失败/自动恢复→统一形状预热后的旧/新/旧→独立复算/恢复核验。所有失败与未触发微测均保留，不将孤立kernel和端到端百分比相加。

Prefill只见TTFT代理轻微变化，Decode代理略低，Mixed总TPS+2.60%；没有设备trace，不能断言某个GEMM占比或当前纯设备热点。当前只保留用户原本的新配置，不新增推理源码优化，不把冷编译去除算作稳态优化收益。

下一轮优先级：①未来任何重启后的测试先用形状覆盖与原生稳态准入，违反3%/5%就保留incomplete而非丢轮；②若用户继续要求稳态优化，先按inference-profiling取得实际worker的Prefill/Decode/Mixed有限窗口，再用key-operator-analysis和无profiler性能Skill决定一项候选；没有有效/主要稳态热点就停止深度改写。保持旧/新/旧回退和完整正确性触发。③盲调GEMM1/2、进一步采样冷路径重写或未经核实的TLE改造暂缓，本轮退化触发未成立、用户要求采样不变。现有basic/cpasync配置已在安装编译器下真实执行，不代表全部TLE接口可用。

本次用户要求已完成，不自动启动新profiler、精度或性能；新版本/新稳态退化/新优化目标到来再复盘。该案例足以补充形状预热经验，不足以把64..1/cohort2次写成所有模型通用SOP；全局SOP与默认门槛不变。完整模型精度、正式每角色双服务四场景性能验收仍未执行。

补充独立文件语义复核已exit0：四个角色的6559文件清单逐项对照，仅目标MoE按c467/2267/ c467/2267变化，其余6558文件各角色均等同初始。该检查0模型/管理请求，报告`source-role-independent-001.json` SHA`4a1502a041383b31a8d441e26db2c7c5af799d17564367dd83b3258a11170187`，脚本SHA`c44027e67d45d31aae747ab2aa1353ca41f5b09b303a817e61f85e504fb2eb33`。

## 2026-11-05 MoE主线配置及GDN回退范围澄清（只读）

当前59 qwen36-35b的MoE仍为22670fd3。查询GitHub main固定到f4c16203083f3cbc712867fbc7d68e2ebb9d75a8；上游文件已位于`runtime/backend/_metax/ops/fused_moe.py`，其内容SHA仍9de7b6eb。目标`_is_qwen_tp2_moe_shape`/`_qwen_tp2_config`两函数AST与容器迁入版完全一致，故本模型TP2参数确实保持当前主线同款。整库checkout仍e1a02b6+定向兼容改动，不能称整仓同步到最新。

FGV `runtime/backend/_metax/fused/gdn_chunk.py`仍有本地Qwen H固定参数/prune和日志修改，但当前Plugin、vLLM及实际FlagGems源码未引用该FGV GDN实现；原启动脚本也没有runtime-tools/PYTHONPATH注入，site bootstrap未见相关注入。因此这份FGV本地调优可单独列为回退项，回退不会删除GDN算子文件/API本体，不应整文件回退共享`__init__.py`以免丢掉MoE/采样导出。

Plugin的GDN层注册另有职责：`ModelRunnerFL`在模型构造前显式导入`gdn_linear_attn`，其`register_oot`子类用bool代替hasattr分支、向gdn_attention_core传plain self.prefix，供MetaX层适配；原vLLM类则传_encode_layer_name(self.prefix)。该路径仍在现有启动链中，应保留，不能因FGV GDN没有接入就一并去掉。vendor `chunk_delta_h`也由patches包导入，是另外的vLLM FLA补丁，不能和FGV fixed-config残留混同。

检查时容器没有模型进程，以上为源码/现有启动脚本的接入链核对，没有伪造运行时函数命中证据。此次0 GPU/生成/管理请求，未回退代码、未启动或重启服务。新查到的静态事实不会重绑昨天的精度或性能gate。
