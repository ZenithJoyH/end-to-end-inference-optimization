# op-005 attention 编译键归一化

状态：单文件修复已加载并通过新源全量 GPQA 170/198=85.8586%；端到端性能尚未验证；目标为 P1K Mixed 停顿，parent P1024/D1024/C64/N128，diagnostic P1024/D128/C64/N128。分类 operator/improve（算子 host launch 重复专化），与 op001 定位关联，不重复计算收益。

## 证据与假设

003 的第三个 warmup 中57请求出现共同4.596s间隔；两TP wait4 的目标为各自shell，后代mxcc --fatbin→lld，输入LLVM kernel为flash_varlen_fwd_d256_tn_kernel。源码tn_direct.py SHA22036d9bd08d9e8a57f4336ae52b5bba3d4eaecf3c3665d209205c01912bc206。捕获LLVM前64KiB SHA与实际GOACEMDV36TG3AXDMQ7PBLYGZ4WVRIF4KBA63EGVLPSK66R2NAEQ缓存一致，产物mtime与停顿对齐。

缓存154个不同键、双rank308个optimizedTTIR，SHA均d11a2cfa7f74b35c17438fd3ac8c524fc28401e965dba7524f64cbd35487a9d6；编译metadata除hash外一致。证明重复编译，不等于154个键都仅由Q_TILES导致。源码libentry将constexpr实际值纳入entry key，Triton compute_cache_key按specialization/options组键；_launch_d256_tn_base设置Q_TILES=row_tiles，kernel非SplitKV分支只检查Q_TILES>0，计算使用grid/worklist，只有SplitKV才用Q_TILES进行整除/取余。假设：在此base launcher将Q_TILES固定1，保留真实grid，可消除动态row_tiles引起的冗余编译。需CPU launch contract与新编译/输出证据证伪，不预先宣称收益。

预热原因：warmup只触及当时批次/总query token组合，连续批处理变化后的row_tiles可能未出现；当前3warm并非枚举所有专化。此为源码支持的机制，实际kernel/cache/编译链已证，具体该键所有输入常量无法由现有metadata完整还原，不冒充完整runtime参数记录。

## 编码前项目真相表（G1）

| 字段 | 冻结内容 |
|---|---|
| Current op | 现有FlagGems-vllm MetaX paged varlen causal attention的D256 TN base launcher；用户请求定位/优化编译停顿；workflow末尾conv1d模板不适用 |
| Editable files | 先在/workspace/qwen36-e2e-op005/FlagGems-vllm私有当前GDN副本修改tn_direct.py中的一个cfg项；新增针对性tests/benchmark；不部署 |
| Read-only | 当前生产四repo、vLLM、权重/tokenizer、原003/002原生工具/计划/回执/完整白名单、SplitKV代码、其他平台、原参考快照 |
| Build | Python/Triton源无重装；in-memory compile/pytest collect；实际kernel由目标Triton编译，clean仅用新私有cache，不能清服务cache |
| Validation | CPU launch contract sweep原/候选除Q_TILES外完全相同且grid相同；GPU FP16/BF16 paged16/32 GQA8 D256 compact/direct irregular shapes原/候选torch.equal；原公共paged参考作辅助；graph capture+至少2replay；数值失败停止 |
| Benchmark | 新独立cache固定相同shape序列，原/候选记录独特编译键、首调用/已热调用ms；原生标准attention benchmark或适配明确支持paged scope；E2E同配置A/B/R无profiler，所有轮保留 |
| Active set | D256/GQA8、FP16/BF16、pages16/32、direct/compact、q1/3/5/17/32/33、raggedbatch、已有FAST_CAUSAL/BULK_TAIL/fallback flags之CPU契约；SplitKV原样作为守护 |
| Aggregation | 不相加kernel收益；逐shape全部报告，steady中位/尾部/编译次数；E2E必须3warm5%准入+3measured/600s；不放宽旧失败 |
| Timeout | CPU<=60s；最小GPU数值<=180s；完整standard bench预算测量前再冻结；任何需停服graph窗口先准备具体回退再请求，不默认授权 |
| Profiler | 当前服务未启用profiler；使用低开销子进程/wait4及编译LLVM/cache为替代证据，不等于GPU critical path |
| Autotune | no-autotune明确豁免：仅MetaX非SplitKV无效语义常量归一化，不改BLOCK/warp/stage，保留现有固定配置；不涉及NVIDIA autotune |
| Fallback | NO_TORCH_COMPUTE_FALLBACK；生产不新增torch计算/拷贝/类型转换/native绕过；测试参考可用Torch |

## 对齐契约表（G2）

| 字段 | 冻结内容 |
|---|---|
| API/reference | 现有MetaX _launch_d256_tn_base与flash_varlen_fwd_d256_tn_kernel前后逐元素一致，主参考为当前GDN源；数学辅助对应torch SDPA/paged attention，无通用torch注册接口变更 |
| Device/backend | MetaX C550 GPU6私有验证，最终TP2 GPU6/7；不操作其他卡/任务 |
| Input | Q[T,Hq,256]、paged K/V[P,page,Hkv,256]及现有strides；Hq/Hkv=8主scope；cuQ int32，KV length或cuK，blocktable int32；compact worklist[tiles,2]含-1padding；dtype FP16/BF16 |
| Output | 原o/lse调用者buffer、shape/dtype/alias保持；原实现写入路径不变，不新增out API |
| Dtype matrix | 本次承诺目标FP16/BF16；FP32/integer/complex/bool/其他headsize不新增支持，保留原路由 |
| Promotion/acc | 完全保留原FP32softmax/累加与outputcast，不改算术/scale |
| Semantics | causal/分页/packedGQA与原实现相同；NaN/Inf/signedzero/非法输入维持原实现，不扩大语义承诺；重复编译键证明不足以替代数值验证 |
| Autograd | inference forward-only，原无backward承诺 |
| Unsupported | 原page非16/32、非D256、缺prefix/length、tile非32x128的ValueError保留；不改变原unsupported/fallback |
| Torch use | 仅测试/benchmark生成输入/参考及assert；生产host只改字面量配置 |

## 路径表（G3）

| 路径 | 条件 | 实现/config | 验证与风险 |
|---|---|---|---|
| direct | base launcher无compact，SPLIT_KV=False | Q_TILES=1，真实grid row_tiles保持 | grid/参数合同+GPU数值+graph；风险遗漏此常量用途 |
| compact | base launcher有worklist，SPLIT_KV=False | 同上，实际工作量仍由descriptor/grid | ragged/尾tile/-1pad；不缩shape覆盖 |
| SplitKV | SPLIT_KV=True | 不修改Q_TILES和调用源 | AST/源hash守护；其除余依赖此常量 |
| other D256 boundary/gqa4/platform | 非本base launcher | 完全原样 | source diff证明范围；未硬件验证平台如实标记 |
| unsupported/early | 原ValueError/原early | 无新fallback/新导出/新注册 | CPU错误边界，保留行为；不调用torch compute |

目标AGENTS/workflow已读；optimization.md/deep_opt.md在当前目标repo缺失，记录为既有环境事实，按workflow和项目算子指南执行。现有tests/test_flash_attention.py多数通用flash路径跳过MetaX，不能拿skip冒充本paged TN通过；tests/test_triton_unified_attention.py提供paged参考输入/输出，可复用数学参考但主API不同；需新增targeted test而非修改既有reference。benchmark/test_flash_attention_forward.py为通用非paged，不可冒充本路径性能。

G4/G5私有实现与25项测试已通过，8组graph各2replay也已通过。原生Event微测完整；CG标准微测、实际模型候选TP2/full新源GPQA和E2E仍待验证。pr_readiness=experimental；没有生产保留改动或累计E2E收益。

预冻结第二阶段：原生benchmark runner的operator模式（不创建side stream）基线为旧Gems launcher，候选为新launcher。page16/ragged[1,5,17] direct+compact、page32/q5 direct+compact，FP16/BF16共8shape，3paired全保留；warmup5ms/iter50ms，180s进程预算。latency_base明确是旧Gems，不冒充裸Torch时间；Torch数值参考由已通过24组测试提供，通用torch flash benchmark不覆盖此paged scope。主目标是排查新增稳态调用开销，不能以此替代graph或E2E收益；G6仍待graph/E2E。默认stream graph直接capture已在32s内明确被torch拒绝“must be captured on a non-default stream”，未构造Stream；不重复该不支持的API路径，后续graph需具体授权的资源隔离。

operator v3原生3tests通过、24组计时完整，但pair0有BF16 direct .069126→.121315ms (0.570x)，不能宣称无回归；pair1/2多为.061ms附近不能据此丢pair0。先冻结新v4契约：每shape/pair原与候选共同至少2s预热后再进入相同原生operator计时，8shape×3paired全部保留，仍180s预算；旧v3保留不改判。隔离窗口graph benchmark使用相同显式预热，并将native cudagraph rep预冻结100ms，固定24组最低0.9x护栏，若缺项/失败/超预算不部署。这是独立新测量，不补写旧回执为通过。

私有实现结果：source新SHAbca465d21a01f28e4b0e1fb543df03c020cf626d7c8a3ad8d6a2eb74c00ebc07，patch SHA5a6a24782bc01bdb642a2fe8ce7a49bed0357f4df368462d8d82b9c59df723a0，原文件tar SHAfc568dc3da8d5a6286b04ed6b4cd5fc9276d7448dcf0dfeb85cbb486474930b4；311其他Python源完全一致，当前GDN exports保留。CPU336launch/3error/kernelAST全等，installedLibEntry.key constexpr组件6→1。nativepytest24数值+1CPU=25passed，FP16/BF16、page16/32、direct/compact/ragged，output/LSE逐元素相同且Torch参考通过；XML99bf3d824b9b5cb4d8e7fd6b6936e8f959033c2513ec4dfbf97da6bb1c3d0d72。未声称signedzero bitwise或全平台硬件通过。

原生operator v3/v4全24计时行保留；v3 .570x、v4 .709x负面行均不删、不重判成通过。v4虽然3pytestpassed，仅表示运行完整；性能资格仍未通过。下一步已由用户明确批准一次独占窗口，先8graph×2和nativecudagraph24项固定.9护栏，全部通过才加载一处TN文件；失败恢复原文件及原服务，完整Gems配置不变。plan SHA0a4a68c5f8ca74219c8e3ca513670de15e912bfadb69ba671dbd7bf47460bcbc，controller host893812/birth497257755，02:58UTC已8graph×2全部通过，benchmark仍运行，不并发其他GPU任务。source部署后必须新fullGPQA198/65536/temp1/top_p.95/top_k20/seed42/C32/80，不能复用旧实例gate。

控制工具失败保留：numericv1setsid(在导入前0input)、defaultgraphv1嵌套字符串syntax(0input)、benchmarkv1原生unpacker丢SimpleNamespace(0timing)、benchmarkv2旧SHA引用(0timing)，均已新独特命令修复；并非kernel数值失败。defaultgraphv2为真实API不支持默认stream capture，未创建Stream，独占窗口验证替代该路径。所有creator不可重放。

窗口终态：03:02:23达到300s预冻结private预算，nativegraph benchmark没有输出完整JSON/XML，private主进程wait4等待benchmark子进程975844，子进程主线程futex/syscall202，无Python栈证据；8组graph已通过但benchmark不完整，所以不部署。固定预算未放宽，按原计划停止精确private进程组并恢复原服务，02:56:59.108→03:05:19.603共500.495s（8分20.49秒）。当前API975866/birth497290308，TP0 host903589/ns976405/birth497296953、TP1 host903590/ns976406/birth497296954。恢复args/完整env/cwd一致，四repo12252文件/模型/镜像/规范化挂载保持，private975723/975844均退出，APIidle，完整FlagGems whitelist保持。生产source从未修改，旧precision82.8283%是历史实例，当前新绑定尚未签发，实际model replay count未观察；不把私有graph/9健康请求冒充当前TP设备计数。

终态证据/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/results/op005-original-restoration-final-20261015.json SHAe2cf5ce1e2aa547258d5426e0d0eda3224c04104fc1b06bab36ef0600766e427。validator v1 raw Mounts列表直接相等检查失败；v2复用既有SHA32adacf...规范化比较器，全部字段/镜像通过，非移除实际映射守护。下一步先单独定位harness运行环境，避免保留graph parent GPUcontext同时再启动benchmarkGPU子进程；准备同进程pytest.main+faulthandler方案（尚未执行/未新授权停服），不把这个结构性嫌疑写成已证queue机制/算子错误。

非停服device诊断预冻结：仅私有GPU6 operator，原生benchmark kernel模式（已读实际triton.testing.do_bench源码，使用当前stream Event，未构造新Stream），相同8shape×3paired/common2swarm，native warmup10ms/rep100ms，180s预算/all24保留。用途区分host operator计时波动和device latency；不能替换已超时的cudagraph回执或直接触发旧计划部署，不是当前模型formal性能；当前新实例精度绑定pending，不用旧gate冒充当前。原服务C1/C8已9请求全通过，fresh源/实例/资源核验后运行。

新增编译复用实验预冻结：fresh私有cache（不清理任何既有cache），BF16/page16/GQA8/D256/compact batch3，query lengths[1,5,q]、q5/9/17/33/65/129，tablepitch固定32，kernel其他语义和编译选项不变。原/候选各首形状连续预热两次，再扫5个未见长度；同一进程/现有默认stream、0模型请求、180s总预算。计数实际LibEntry新增和7个原生cache/TTIR，预期原6candidate1、预热后5vs0；逐次输出/LSE一致。此实验验证新形状导致的编译，不是默认冷启动性能优化，也不是E2E收益。


## review-014：编译复用实测与剩余验证

一处生产候选差异（仅私有副本，SplitKV原样）：

```diff
-        "Q_TILES": row_tiles,
+        # Only Split-KV uses Q_TILES; the direct grid/worklist carries row tiles.
+        "Q_TILES": 1,
```

恢复后C1/C8共9请求全部通过。原生Event/kernel模式24组完整，oldGems/candidate比值min0.992248、median1.008097、max1.024390，设备时间约0.031–0.033ms。其对照是旧Gems，不是表头所写的Torch；这份结果不覆盖/重判旧operator0.570x/0.709x负面行，也不补写已超时CG benchmark为通过。

真实新私有缓存实验按冻结六形状执行：BF16/page16/GQA8/D256、compact batch3、tablepitch32、q5/9/17/33/65/129。原路径6个LibEntry专化，候选1个；各首形状预热两次后，五个新长度原路径新增5次编译、候选新增0次。原路径每次约3.93–4.01s，候选调用0.129–0.159ms；输出/LSE全等，7个原生优化TTIR的SHA同为44e9ffe482119d7a56eaa7b9191d9a3ea70c47cb1e8c6f66333d98e1d510eb3e。这是编译复用实验，不是模型端到端或稳态kernel加速倍数；该原型TTIR与实际捕获的d11a...不同shape family，不混为同一产物。证明范围是本base launcher无效Q_TILES变化，其余真实编译选项变化仍可合法触发编译。

综合证据 results/op005-evidence-summary-20261015.json SHA81bc7fea6037e01d996a82b47d1ebe5604ee24d40464984e792c2ba2b35f23fc；编译序列 results/op005-compile-sequence-20261015.json SHA11d00b665730db72c31c88283d34aa2b409162f3bef0337a7b88fb1470980fdf；Event原生JSON SHAd8830ab0a9beb298cea853312d3a48d493bb3b68eee8c2a21820f41a93784c09。大产物保留远端唯一案例。

新window2方案已保存但未授权/执行：manifests/op005-window2-plan-20261015.json SHA44c407c40c35f2153017d5ecb17165c88e14c2467907db4a67c75e52cf6344a6。只补缺失的native CG24组，复用同SHA源已通过的8graph，改同进程pytest.main，避免父graph上下文驻留又启动第二GPU进程。旧子进程futex根因仍未证明；新增collection/per-test90s faulthandler只在卡住时留栈。原生do_bench_cudagraph源码已核：每计时创建Stream、估计并展开graph，故仍需独占窗口；不能在当前model资源压力下重复创建Stream。private300s、native rep100ms/common2swarm、每组>=0.9护栏保持，不事后放宽。通过才单文件加载；失败恢复原服务；全Gems保持。新source加载后重新full198/65536/temp1/top_p.95/top_k20/seed42/C32/80，随后新同配置P1K。

当前precision164/198属于历史API952702。原source不变且新API975866健康，但新实例binding尚未签发、实际模型TP graph replay count未直接记录；原gate不改写、不自动复用。四正式场景/最终验收均未完成。

window2最新：用户直接回复call_865367394382480bab2f103a851942ab“允许本次验证及条件加载”，授权已绑定既存44c407...计划。approval/launch命令SHA4127f1e616d99ab8079f90c3783a5fddcc18dcf385b25e0ca9cae42a85ff0569，monitor SHAa739886e9887f378c4b7070761db1aa2e950806f7ebb0857d11da7e98fd042e3；先fresh核验源/实例/资源/idle，且仅执行一次。

window2：原生同进程CG benchmark完整24行、3pytestpassed/112.28s，全部>=.9，min0.9904478/max1.009897，JSON/XML完整产生。旧CG超时保留，不改判；本次证明单进程harness可运行，旧futex具体原因仍未知。04:37:42UTC已按批准加载唯一TN文件并启动候选982315/birth497862111，服务就绪/源核验/健康与新fullGPQA仍待完成。无E2E收益结论。

04:41UTC候选核验通过：API982315/birth497862111，GPU6 host984269/ns982854、GPU7 host984270/ns982855（两birth497868637），都是新API后代。四repo12252文件仅TN一处由22036...变bca465...；vLLM/Plugin/FlagGems、权重/镜像/规范化挂载/完整env原样。Gems-vllm组合hash70760e674623ad2c0d8df138abe97b9388375dfc942004c81851af8bfe5c72e5。service SHA219007f85e2df9fcaa661370425497aaadb5d78031a6446a819805f2f218e245，runtime SHA07c1fc61e16d14534335c0fc713d5519b4b39d3b04815288d0831548ba1ca593，finalproof SHA84fc860e97aeb8663fafa8e260126e3ef74edb232f0055cbbab211419996609e。FULLcapture与两TP GDN命中证据已保存，实际modelreplaycount未知不造数。C1/C8共9请求全通过；来源采集两份相同、formalpreflight0，config SHAbffe0af5e7bb016f8cc81aba4529991ec1f28ae5fd1364de16e7ba573a082111/contract4e4e4a784c36658d3edf09807d01644c5c77203b1b96bed11adf97e0ebc8003d。启动唯一新fullGPQA，不复用原source分数；P1K待正式gate后。


## review-015：条件加载完成，新源全量精度运行中

window2完整24组原生CG、3tests通过，min0.9904478215/median0.9965656770/max1.0098969751；baseline为旧Gems。原生JSON SHA834565fc2ad0815dbc8d6dbcd0342617eba76a639aec7178626504957af6de1f，XML SHA066e10b262fc16a24af660c1cfd8b9496ec10367825a5383e441367ff34025f9，qualification SHAbcf6e194fc7a14e69404d587645a62bfadea9ab380d02a77ef42f4b962e3fac6。完整窗口中断339.013524s（5分39秒），未延长私有300s预算，原子加载唯一TN文件后服务就绪。回执 results/op005-window2-receipt-20261015.json SHAf3037ac371ae23fe684f533173bc3b7cbda7cad47fb7b1ac62cff5e30eb8a697。此前CG超时/两次operator负面行全部保留。

唯一新fullGPQA已于04:42:52UTC启动：host controller991129/birth497893115，UUID bcbef8f8ac274343b48751537e080c5c，eval_model qwen36-35b-op005-qtiles-full-graph-c32-g64k。原生formal_accuracy.py与规定镜像CPU评测容器；全198/65536/temp1/top_p.95/top_k20/seed42/C32/strict>=.8不变。首次04:43:25UTC 0/198完成、32active、0waiting，非正式分数。新响应cache独立，不复用原source分数。

只读monitor commands/monitor-op005-window2-g64k-20261015.py SHA8b4b2bd0078184f4d2090853580d591bb703a7b2ea0802d41a9b15f4e1de5398。终态validator commands/validate-op005-window2-g64k-terminal-20261015.py SHAdb758d15f4a598c8255aa4d501b439564c9dda3f405a63aa42ec808e48a75079已保存，尚未执行；只在controller退出/APIidle时核12252源/完整env/model/image/规范化挂载/frozen实际effective_config和唯一原生results/samples，再调用真实acceptance issue/check。任一输出已创建后不得重放validator；低分或证据无效freeze/diagnosis，不改契约不自动重跑。

后台qwen36-35b已恢复ACTIVE30min，状态不变安静；精度期间禁止并发任何GPUbenchmark/profile/probe/部署。通过后首要同配置P1K全时间线编译与暂停复测；旧002/003不稳，不从最快轮算精确收益。之后才评价Prefill/Decode/Mixed守护与A/B/R，四场景最终acceptance仍incomplete。

2026-10-15 05:06:19UTC只读跟进：同UUID bcbef8f8ac274343b48751537e080c5c/controller991129仍运行，71/198完成、0timeout、32active/0waiting，无native results/run-record；中途计分不作正式分数。未执行terminal validator、未发性能流量、无服务中断/源码变更。后台继续ACTIVE，原契约不变。

2026-10-15 05:39:41UTC只读跟进：同UUID/controller仍运行，154/198完成、0timeout、32active/0waiting，原生results/run-record未生成。仍非正式分数、不执行终态validator、不提前启动P1K；服务/源码未操作，后台ACTIVE保持。

2026-10-15 06:06:10UTC只读跟进：同UUID/controller仍运行，196/198完成、0timeout、2active/0waiting；无原生results/run-record。余题仍在生成，不能将中途得分当gate；不运行终态validator/P1K或重复评测，源与服务未操作，后台继续ACTIVE。


## review-016：新源正式精度达标

本UUID bcbef8f8ac274343b48751537e080c5c全198题已结束，原生strict-match170/198=85.8585858586%，timeout0，当前API无请求。原始results文件results_2026-10-15T06-10-19.814496.json与唯一samples/run-record齐备；wrapper及原生acceptance核验全部冻结filter/198唯一doc、provenance、actual effective_config、当前源12252文件/模型tokenizer/完整env/镜像/规范化挂载与精确实例后issue/check成功。没有复用旧分数，没有改变198/65536/80或采样契约。

当前gate accuracy/op005-window2-g64k-accuracy-gate-20261015.json SHA2d5064cebc8f504e97ae244aa2ed381ab3b2c63e0fbe6ee7c2797cf7c704ee3b；terminal continuity SHA cb32a6d4510dcc79bd0d3f9182d9b45e25cde7ec2a959ef927c77b900669b3dd；service仍219007f8.../API982315birth497862111。只执行了一次terminalvalidator，今后只读既有结果、不重放issue/creator或GPQA。

分数变化不单独归因attention修复；这轮是当前candidate的独立精度证明，没有模型E2E收益结论。新目标为targeted同配置P1K（P1024/D128/C64/N128）编译次数/暂停/吞吐与阶段守护，冻结新计划后运行。旧002/003不稳全轮保留；不能选快轮算加速，最终四场景/实际modeldevicegraphcount等债务保持显式。

用户明确要求继续P1K并确认预热后编译/停顿，全FG保持。本轮mode=targeted/run-id op005-p1k-compileobs-004，P1024/D128/C64/N128，parent D1024；plan字节同旧8a2a1260...；新comparison8f8868a9.../native-identity1740b77d.../observer53a0f559.../launchcontracte93f21fb...。3warm/window3<=5%后3measured/600s，全轮保留，测量波动阈值10%保持原comparisons。冻结ITL>1s、共同停顿>=8请求且交集>=.5s；5Hz TP后代compiler argv与LLVM hint、客户端来源分开，低开销<=.05core/p99<=20ms/missed<=1%仍须实测验证。cache前后CPU只读快照作旁证，mtime不能单独证明本服务编译。旧baseline不稳，不计算精确收益。启动脚本SHA389f32bef618e96569cc79640d6fe7b5f3c73dab50d734a6671c083358008ca2；fresh源/实例/gate/idle/resources后只启动一次，不重启模型服务。

P1K004已实际启动06:54:57UTC，hostcontroller1085680/birth498685578；先保存目标attention元数据430份before快照 SHAec9858c1cf195ffcd23b67350f66cbeeee6c41cee1112362cb12d5729df217ee，未清cache。观测分辨率勘误：复用observer主线程采样5Hz，后代/compiler发现为coarse1Hz；不能排除亚秒子进程，未更改源或事后阈值。API根遍历可能先发现TP后代，TP归属要按parent链/冻结worker PID判定，不能只看origin_target标签。nativecandidate role及targeted契约为准，supervisor历史baseline字符串只是控制日志标签。

## review-017：004首轮编译与新稳态契约

004终态：三轮原生counts/schema/config/SHA均有效，128成功/0失败、input131072/output16384各轮保持；32.099/21.030/20.769s、output510.414/779.082/788.864，固定3warm spread35.7408%>5%，0measured/nativecheck_run拒绝，项目incomplete。observer CPU.01429core/p9912.256ms/missed1of1462通过，fatalnull。post源/实例/完整env/model/gate保持，精度不失效。run-record SHA3ed601ee4918d202d3c08407b39300ead83e3c21ef1ac93ca9b685d5e1060f19，observerdata8826aeaeb5be167f406688b485fdd07632a639eaa7bdde95d8bb9a7ebf3a2f14。

实际parent链确认14compiler进程属于两TP、6rootmxcc事务（fast/direct/bulk各两TP）都在首轮。cache430→432，新增2direct目标metadata都在最后warm前；后两warm无compiler且ITL>1s为0，maxITL.580/.500s。首轮唯一ITL>1s为3.684s，未满足>=8请求共同>=.5s的cohort规则；初始meanTTFT7.418s不能当纯Prefill设备时间。分析results/op005-p1k-004-timeline-analysis-20261015.json SHA3739d474da14bb5c9f314faf0083a2342039d36e69bb990504626ae06b1035f8。因无measured，不能据此声明预热后的稳态编译/停顿已经消除。

新005仅调整预热预算3→4轮，原生准入仍最后3轮<=5%，通过后3measured/600s且测量spread<=10%。这是新测量契约，004慢轮/失败不删除不改判；今后baseline/candidate/revert必须都用4warm才能算比较，本次单候选只验证稳态与编译/暂停。源码、缓存保留、完整FlagGems与服务参数原样；005再不稳则定位残余cause，不盲目重复加warm。已先冻结再看新数据，无新源码或服务重启。

005新契约dryrun0：plan SHA74e8ee97537240a8e718f437efb1f8f9b200df707bce97709d497135002b4be0，comparison722bc3ed2794ac2750f10b66d2f8b00c8ef70a4a0a71656a07c050d8ba9073a4，launchcontractb2926d0632f71a8db1831b3795c07c028e9cf46cfecbc0e8a39db7d1b5954478。start脚本SHA34016326111df17867dc50c568189954b25fe874e1b083be02351834a5f45cc5，执行前再精确确认004控制器/客户端退出与当前gate/源/idle/GPUowner，既有cache不清理，原服务不重启。

005已于07:07:35UTC启动，controller1092436/birth498761407，before目标metadata432，SHA2e276b571c8a560eb07f840fa3f032e68ead269ef79ed8a8fe77fa3ba07b0f20。所有服务/源码/gate保持，不并发GPU任务。

后续006完整P1K工作负载的CPU方案已准备但未执行：targeted单候选P1024/D1024/C64/N128，4warm最后3<=5%、3measured/600s，仍不构成formal A/B/R或四场景验收。先要求005完整稳定且无postwarm编译/ITL>1s，再fresh核gate/source/资源与新计划dryrun。006缓存快照预先扩展为TN main/fast/bulk三family（CPU前后快照，不在测量窗口内扫描），不能与005仅main的元数据总数直接混比。

005终态通过targeted短场景：native check_run接受，7轮每轮128成功/0失败，4warm末3spread3.679877%通过；3measured20.437/20.339/20.229s、output801.673/805.565/809.923tok/s，spread1.02414%；medianITL50.832/50.668/50.248ms，最大ITL .494/.484/.477s。全run compiler0、rootmxcc0、ITL>1s0/cohort0，主TN cache432->432无新增。observerCPU.013845core/p9913.001ms/missed0of2552 admitted，fatalnull。run-record SHA6beec34665b99736f3e4d8dffe787f37c99e849a0fb19b9d8bf3c9b3fad3d97c；analysis9973c2f658bb14e007538966b7a4a58ee2414a6d4460938d23a33da76a9b08e9；postcontinuityfcd8aa5272ac6370a5d31e9417616f3a6cedfb49901aa98d3a876a303d99f340。未观测到预热后编译/旧秒级停顿只属于D128和1Hz后代采样范围，不能排除亚秒compiler/冒充设备criticalpath；004失败仍保留。

按用户P1K复测目标继续完整工作负载006：P1024/D1024/C64/N128，mode targeted单候选；planf0a5bac2d32f068b20e5f0875e0993e14b90b2436b83fac66dd6dfdc2d5338d9/comparison788a3e0920c37407c6e4114e5e7098139c9c999ef3536657bd5a71cd1eae2504/launchcontract0b0ee2ded3a0890af1b9a637a581cc290bdb39d6334af841abaac3b3cc36c198。仍4warm-last3<=5%/3measured600s/maxspread10%，同服务/源/FG/gate，不重启。startSHA32097bbb6c56acc54556f0e8e45ab1fb51d2a0a833eafaf5f8a2f45f17ec5d01，先确认005退出与freshgate/source/env/model/image/规范化挂载/资源idle，只有一次客户端；不能拿D128与D1024算加速比，未构成formalABR/四场景验收。

006完整P1K已实际启动：{"pid": 1110681, "start_ticks": "498848466", "started_utc": "2026-10-15T07:22:06.091653+00:00", "run_id": "op005-p1k-full-006", "mode": "targeted", "role": "candidate", "command": ["python3", "/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/commands/gdn-p1k-cpuobs-supervisor-20261014.py", "--contract", "/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current/commands/op005-p1k-006-launch-contract-20261015.json", "--contract-sha256", "0b0ee2ded3a0890af1b9a637a581cc290bdb39d6334af841abaac3b3cc36c198"], "launch_contract_sha256": "0b0ee2ded3a0890af1b9a637a581cc290bdb39d6334af841abaac3b3cc36c198", "scenario_id": "p1024-d1024-c64-n128", "parent_target_scenario": "p1024-d1024-c64-n128", "gate_check": "passed", "source_unchanged": true, "service_not_restarted": true, "fullFlagGems_unchanged": true, "supervisor_scope_label": "legacy baseline string; native runrecord candidate role and this targeted scope are authoritative", "observer_overhead_requires_terminal_check": true}
完整P1K的缓存before（三family）与controller已写state；只读监控/终态命令SHA：{"monitor-op005-p1k-full-006-20261015.py": "18243d3d6a7ef3674b684e6998b97623357edcf83eb85a7ea55d39bc78e30a00", "validate-op005-p1k-full-006-20261015.py": "6619bf69dd592c535be92a9c7ee5ef334d50e3b227f709731f79cf8f237c7990", "finish-op005-p1k-full-006-20261015.py": "172a9d30634c693bf729edbc1c8bf3628978cc239484b640d96f29b1dd187b46", "analyze-op005-p1k-full-006-20261015.py": "7e10abe667586f9c0c632eb2f16210d5331d17499803f2ad43b6165064ad29eb"}。结束前不并发其他GPU任务；中途结果不是完整验收。

## review-018：短场景稳态通过，完整P1K运行

同候选新005契约下的全部7轮、源/gate与观察器已核验；不是从004删首轮，也不以旧不稳数据算加速。当前证据支持D128测量窗口内未复现秒级停顿和编译，完整D1024仍待结果。006唯一controller1110681/birth498848466，CPU收尾器1112659/birth498873774只等待其退出后验真/cacheafter/CPU分析，不发送新请求或操作服务；收尾status/results文件存在时不得重复手动执行finish/analysis。最终同配置ABR、阶段守护及其他正式场景仍未完成。

2026-10-15 07:39:25UTC中途只读取证：006四轮warm和首measured r5均有效（r5 115.642s/1133.427tok/s、maxITL.583s、ITL>1s0）；此后捕获24个compiler后代进程，LLVM hint仍有flash_varlen_fwd_d256_tn_kernel。24不是root编译事务数，具体TP parent链/phase/请求停顿关联由已运行CPU收尾器终态分析，不预判整组稳定或编译消失。收尾器1112659/birth498873774仍在等待既有native退出，未重放终态/benchmark、未改源码/服务或关闭FG。

## review-019：完整 P1K 复现预热后编译及停顿

006 targeted单候选完整P1024/D1024/C64/N128结束，原生run完整、7轮各128成功/0失败且input/output各131072，所有原始轮保留。4warm最后3轮spread0.1441%通过，但3measured吞吐1133.427/991.227/1146.247tok/s、duration115.642/132.232/114.349s，spread13.6771%超过预冻结10%，项目结果incomplete；不丢r6、不加预热或重判。原生check_run接受只说明证据/配置完整，不能覆盖本项目测量稳定性失败。

r6存在21个ITL>1s，max8.902s，13请求共同间隔8.90094s。TP0/TP1在共同区间waitchild采样约6.60/6.40s，自己的后代捕获24个compiler进程、12个root mxcc事务（attention8，MoE stage1四个），全部位于r6。其余6轮无捕获compiler、无ITL>1s。TTFT三测量1.926/8.970/1.913s、medianITL52.388/52.326/52.212ms；含排队/网络/调度，不能当纯设备Prefill/Decode。5Hz主线程/1Hz后代发现的分辨率限制保留。

TN main/fast/bulk元数据466->474，8个新文件全r6，四个不同新TTIR各两TP。CPU对比显示这些产物无与before相同的原始TTIR；FP32输出指针和split_id/Q_TILES相关算术体现SplitKV partial路径。current splitkv.py:648仍以SPLIT_KV=True、NUM_SPLITS、Q_TILES和FP32scratch布局启动；不能把原非SplitKV无效Q_TILES的固定1补丁推广到实际依赖此值的SplitKV。下一步须解析真实参数/路径，区分合法新形状与剩余可压缩专化，而不是认定同kernel名就是旧修复失效。选取metadata最近选项的diff仅定位线索，不代表最接近的语义对照。

MoE LLVM自有根编译两组mask界48968/766和51064/798。匹配源码中的输出buffer长度为constexpr，有进一步收缩专化维度的候选；但真实函数owner/import/注册来源仍须核验，不能按同名文件推断，也不能把sharedcache中其他时间/shape的条目全归给本任务。先CPU证据，再为独立候选分配实验ID和私有验证，保持FlagGems全部启用。

observer .013530core、p9912.865ms、missed1/6037、fatalnull，准入通过；post continuity12252源/模型/env/精确实例/gate无漂移，APIidle且native与CPU收尾器均完成。当前正式170/198 gate有效，没有源码部署或服务中断。run-record SHA b1cc675b20886607e0509fbc943445e01d3bedc0f429439fafb820a8b4a0f47e；terminal b27ddf3bf1a7211d2fdff1864aaf1d41c852f163e3401d2a38c2083d9bd25d6d；timeline cc1698c1cc1986b7e2c3610e0c579e67176ec541e80747feaabfcae0e80b7abf；postcontinuity91543f8253c67f655d5323f9425a4d12e5d7871a80b4f53b5ea5d2e6098e8f95。新增CPUcache审计f0dab7523b7207ee7478a3c398887d05b7607032eed13418c234c5a676668e9b；SplitKV/MoE静态证据acb53efbac30335ca661892deb148588b92bd06e2ebaf6fd2db8cff07ade69ec、摘要e89a4ecfbced5a48351cc4df097c7bfffd889cc8191a0cfd020053d9ea33e4a4，大产物留ROOT/results。不得重放006或既有收尾/快照creator。

D128005稳定结论仍有效但范围有限；不能用它覆盖D1024失败、与旧不稳baseline最快轮算收益或直接切P4K。正式同配置ABR、阶段守护和四场景验收仍未完成。review019第一优先残余SplitKV参数及MoE真实路径/专化边界，sampler/MoE tile旧方向延后，不叠加生产修改。

## review-020：预热后新编译的标量专化条件已定位

本轮纯CPU取证，0生成请求/0GPUquery/0benchmark/0生产源码改动，当前源、完整env、模型、精确服务及正式gate通过只读复核。当前LibEntry key明确区分const_args取值、普通specialize标量(type,value)、do_not_specialize整数的宽度类型。

修正review019的宽泛入口线索：实际新编译是tn_direct.launch_d256_tn_direct的bulk边界路径，经tn_boundary.launch_tail_split调用主TN kernel，普通splitkv.py:648不是这四份产物的直接launcher。TAIL_ROWS=batch*(64//HEAD_RATIO)或batch*128；当前Hratio8时捕获B13/21，两prefix104/168、Q_TILES2/NUM_SPLITS16，两tail1664/2688、Q_TILES32/NUM_SPLITS4。TAIL_ROWS只有输出/LSE地址步长用途，每对完整TTIR只将debugloc及TAIL_ROWS、TAIL_ROWS*H8、TAIL_ROWS*H8*D256三个仿射常量归一后逐字相同。可优化的是TAIL_ROWS的值专化；Q_TILES/NUM_SPLITS在SplitKV实际参与任务映射、分片与归约，不能像非Split路径一样固定1。其他merge/prefix/aligned变体另审，不扩大首个单变量。

MoE真实编译owner由TTIR source location和自有LLVM常量对应确认是Gems-vllm/ops/moe_align_block_size.py:405。两份真实LLVM在只去临时ModuleID并将48968/51064与766/798对应替换后逐字相同；两个输出buffer长度是mask界限constexpr，同bucket的E256/tokens_per_thread256/blockSorted256/blockExpert4并未改变。两个bounds可提出运行时标量候选，向量/tiling参数保留，通用实现涉及其他后端的影响须在最终设计/回归中交代。

为何4warm后仍编译：C64只是并发上限，Mixed阶段每步实际批次及尾部scratch长度会变，当前key将每个长度值变成新specialization；四warm吞吐稳定不等于覆盖所有长度。原生冻结runner各轮seed74283..74289不同，P/D/N/C不变，不改seed来凑cache。只读连续性和cache证据不支持将此次归因源码漂移/主动清cache。这里的B/形状tuple由真实IR与当前host公式还原，没有伪造注入式livePythonhook。

计划[op006](op-006-attention-tail-workspace-runtime.md)先只改私有mainTN TAIL_ROWS运行时参数+do_not_specialize；[op007](op-007-moe-align-runtime-bounds.md)再独立处理MoE两mask界限。当前两项均planned/notimplemented，GPU数值/graph/原生benchmark/模型fullGPQA/E2E尚未运行，不声称性能收益，不动生产服务。正式precision170/198与006稳定性incomplete结论保持。

外部证据均在ROOT/results：audit SHA6e6ced5adb136f155aa9a436209c3ff77ec7899a3335c03ef12628d1c2989d57；tailrows caller d6b99d0394d370c13e1a55a2c03038c9f9387e6117f1b50f45e4d5157c04c4e9；完整IR配对证明2162268ffb833ff9e2101873414bf837b204e407cac39f6166a3b1d5fb14fc10；LibEntry/原生轮次policy2a2343977a90597e2e826d6683e0e784d705a053bfcb2b6205cd10f44674e08b；汇总结论75bbd364697597101ce2562acdb936a92e49c4a7ee928ce7af583f8e6a1028ec。命令及SHA写同state，不重放已完成creator。
