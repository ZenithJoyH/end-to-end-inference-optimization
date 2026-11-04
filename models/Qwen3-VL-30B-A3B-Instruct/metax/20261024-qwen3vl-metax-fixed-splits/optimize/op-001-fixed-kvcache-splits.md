# op-001：固定 native KV-cache Attention 分片数的精度/性能折中

用户要求继续检查能否兼顾精度和正确性。按上下文，以保持数值/模型精度为硬门槛，再验证能否缓解split1的性能损失；不预设固定2/4有效。源为mx-104当前split1容器，prefixON、sampling/gems-opt/MoE与所有其他设置保持。本次独立case最初拟用GPU2/3，运行任何数值用例前因资源占用修订为GPU4/5。新结果不直接混入旧case。

来源证据：此前真实完整Q/K/V重放在query9/KV233下固定1/2/4均保持C1/C8一致；GPU4/5两组180轮已证明固定1的稳态吞吐代价P1K11.37%、缩减长KV38.30%。该证据定位算子参数，不代表其他长度下固定多分片仍有一致性。

设计归属：首先只通过已安装MACA flash_attn_with_kvcache的合法num_splits参数做组件控制；不修改vLLM、权重、采样、MoE、FlagGems-vllm或FlagGems。若候选通过，再在独立容器现有Plugin MetaX kvcache调用处替换单个常量，保持encoder/varlen/cascade/DCP路径。非目标模型共享该入口，最终适用范围须由真实shape/能力界定；当前pr_readiness=experimental。不得在模型路径/servedname或GPQA题目上特化。

步骤：只读资源预检→不暂停源服务的独立快照与精确挂载/内容/导入核验→复用历史真实输入及补充长KV/batch/dtype/layout检查→候选graphcapture和两次以上replay→原服务独立副本smoke/C8/固定前缀logits→完整GPQA198题、64分阈值→精度通过后同设备E2E对照。任何组件时间不冒充E2E；不关闭任何FlagGems算子，不挑轮或改精度阈值。

Prefill：当前改动仅decode/kvcache接口，cache命中后的短query也可能命中；TTFT仍有Mixed干扰，需守护。Decode：固定分片数可能稳定归约同时恢复KV并行度，未验证。Mixed：本case暂无模型级新基线，不混历史GPU4/5结果。

执行前命令：commands/prepare_isolated.py，SHA见state；保存源inspect与before/after指纹、无pause快照、目标inspect、machine-readable mountdiff和四仓库/实际import等价门禁。image_lineage=verified、mount_parity=passed；源与副本全源码内容及安全cwd下实际导入路径一致。当前仅开始组件验证。

组件测试执行前冻结：B1/8/32/64；KV1/233/1024/8192/65536（query1/9且KV>=query），BF16/FP16，Q16/KV2/D128/page16，非恒等物理页/有padding表行距；目标行相同、邻居同质及异质两类。要求目标行跨batch逐位一致，且CPU FP64 causal reference在BF16 atol0.002/rtol0.02、FP16 atol0.0005/rtol0.005内；固定1/2/4/8/16全部保留，自动0仅失败诊断参考。对B8/KV1024及65536/Q1及9/两dtype/各split做capture+3replay，再改变query做2replay。通过完整矩阵的显式split才计5轮20次完整API graphreplay的CUDA-event时间，split1首尾回测且全部保留；只作算子诊断，不替代模型精度或E2E。命令SHA及范围见state。

资源修订：GPU2/3 被无关服务占用，原算子预检在运行任何数值用例前拒绝。用户授权仅临时停止本任务18977服务并恢复原split1。矩阵不变，在GPU4运行算子验证；独立容器命令显式覆盖设备，finally恢复原服务。执行脚本及SHA见state.commands。

第一轮真实输入重放：rank0/1均成功逐位复现历史C1/C8自动路径输出，auto0目标行分别2692/2461个元素不同；固定1/2/4/8/16在这组真实query9/KV233输入上均一致。扩展合成矩阵0项完成，因输入stride不符停止，并已恢复原split1 graph16/C8。极小布局探针确认MACA四维CPU→GPU转换在启用FlagGems之前就采用channels-last；数据值不变，末维stride16不满足native接口。修正仅在测试生成器使用flatten传输后view，并逐项断言CPU字节和stride，保持矩阵/阈值不变，另存v3产物重跑，不把测试生成器失败归因于Attention。

修正布局后的完整组件结果已完成（component-fixed-splits-layout-v3.json，SHA见state）：固定1/2/4/8/16共90项均通过，自动0的18项中16项出现batch不一致；所有108项仍满足各dtype预冻结FP64参考容差，不能将逐位差异直接称为语义错误。48项graph capture/原输入3次与改query2次replay均通过。真实rank0/1 C1/C8原始输出逐位复现，固定各split一致，自动0差异复现。

算子完整API graph计时中位数（微秒，全部5轮保留）：KV1024/B8：split1=108.2624，16=35.4176；KV1024/B64：109.8240→63.5520；KV65536/B8：5752.6400→456.2816；KV65536/B64：5821.3568→1412.7360。固定4在短KV/B64稍优于16，但16在所有测量shape均明显优于1且长KV更好；本轮选择单一常量16，避免依batch特化。结果仅属算子诊断，不推算E2E比例。

原源服务已两次恢复并验证graph16/C8，最新历史实例919089:1112105886。首个模型控制器2977371因provenance文件名引用错误在停源服务前退出，0请求、0候选启动；另存v2修正。当前模型晋级控制器2979591:1112198243已实际启动，候选服务8248:1112200808于2026-10-24T03:07:41.533574+00:00运行：仅独立Plugin的kvcache参数改16（候选SHA见state），同token前缀0..64/C1/C8两次rawlogits检查通过后，重启至普通observer+全新KV的候选进程，再graph16/C8并跑GPQA198/64分，prefixON。全部结束或失败finally恢复原源容器split1、原argv/env。

评测准备发现两项非模型问题，均保留原失败产物：NFS copy2复制元数据EIO，改为新tools-v2逐文件字节复制并核对SHA；104规定官方镜像实际1396e5d与59原62dac不同，strict-match正则不同。新专属CPU evaluator按当前本任务原104 evaluator原件恢复已冻结规则，未看分或发送模型请求；两次v2 provenance已证明198题raw/processed内容及完整task_config与历史契约一致。新契约64分不变，不复用旧Host gate。后台监控复用qwen3-vl-gpqa-erqa，30分钟，正常无变化安静，仅关键变化通知。当前模型级最小回归/正式精度未完成，禁止宣称兼顾模型精度和E2E性能。

模型最小回归进展：v2实际候选8248:1112200808，两rank原生命中split16、graph capture/16 replay/C8 smoke通过。固定prefix0的n8请求被原调度器拆成5/1/2与1/1/6，因此采集器拒绝将多个文件冒充一个真实B8。所有已保存实际batch1/2/5/6、两次请求的全部目标logits都与C1逐位一致（prefix-fragment-diagnosis.json），但准确C8证明仍incomplete，0正式GPQA请求。v2退出后于03:15:37UTC恢复源split1实例927418:1112227059，graph16/C8和源身份均通过。

v3仅在临时诊断helper复用既有cohort admission barrier：active C8请求全部8个到齐才交给原Scheduler，原token预算8192不变，保留130项入批元数据；不修改生产scheduler源码/配置。候选20863:1112254818于03:16:41UTC启动，控制器3013860:1112252233。独立CPU审计3016716:1112262578核对全部65前缀、260重复比较及130个真实C8证明；若失败中止自己的控制器并恢复源服务。通过后启动普通observer的全新正式模型进程/KV，因此临时入批与logits观测均不进入正式GPQA；仍完整198题/64分、prefixON。当前原生进度logs/model-events-v3.jsonl，当前终态仅看v3结果与source-restored-model-v3.json；旧v2失败/恢复不当作现状。

关键模型结果：v3真实cohort8两次入批证明均为8、预算8192不变；prefix0 cached224/query9/相同token校验通过，但C1/C8原始logits最大差1.375、hidden也不同，最小严格数值回归失败，正式GPQA与E2E均未启动。组件通过并不能证明模型batch不变；没有相同方法split1对照前不归因fixed16。独立CPU审计在失败时重复SIGINT击中了模型控制器finally清理，候选终止但原source启动跳过；两诊断控制器均已退出，专用串行恢复3034962恢复原source935632:1112296896，2026-10-24T03:27:11UTC source-restored-audit-recovery.json passed（原split1/prefixON/argv/env、graph16/C8均实测）。后续禁用并发中断恢复方案，保留冲突原始证据。

当前最小受控对照：baseline1_control_controller.py SHA见state，唯一控制器3066695:1112399945；独立clone恢复原split1代码SHA2eaec0be…，同cohort观测helper、同prefix0、C1/C8各两次、同GPU4/5与原配置，记录所有snapshot/metadata。它只诊断，无论logits是否一致都保留结果，不自动跑正式精度或性能；finally单控制器恢复原source。终态split1-cohort-control-completed.json与source-restored-baseline1-control.json，后续比较split1/16并定位首个实际分歧算子。监控已同步当前任务，保持无变化安静。模型精度及端到端兼顾仍未证实。

2026-10-24 04:12UTC回查：split1同法对照已完成，真实C8/prefix0/cache224/query9/相同tokens、两rank与两次重复齐备。split1跨batch logits最大差1.5625、146102元素不同、RMS0.128646，hidden最大差0.9375；同batch重复逐位一致、C8所有同行一致，两rank观测一致。split16相应最大差1.375但RMS0.198692，因此不能挑最大差说16更好。split1/16在C1的logits最大差0.511719，在C8差0.6875；argmax均565只说明这一位置未换首选token，不是精度gate。完整16份snapshot比较split1-split16-prefix0-comparison.json（SHA3485903493e9595fea2f45071fb4f88f08b55bee9cba88f587936c9a2cce3258）。

结论边界：当前模型随batch变化并非仅固定16才存在；这是相对于本次16候选的继承问题。不能据此排除最新FlagGems-vllm的贡献，也不能把合法分片归约差异直接认定语义bug。此前将组件逐位一致外推到整个模型不成立。新原始对照证据优先，GPQA64/ERQA40契约不变且当前未运行/签发新gate。

源18977已于03:49:02UTC恢复split1/prefixON实例943956:1112428032，graph16/C8与源码/argv/env均passed。继续只做最窄的nativeAttention边界观测：独立clone仍split1，在已有opaque Attention内部调用原nativeAPI后读取Q/K/V/output，按layer/rank/请求全部保存，无模型forward hook或新增数学graph op。每batch的最终logits/hidden必须逐位等于上轮未观测基线，否则观测无效，不用于归因。分析区分共享cached224与新增9个KV、第一处Q/K/V输入变化和Attention输出变化。native_trace1_controller3137394:1112635119已启动，单控制器finally恢复原source split1；日志native-trace1-events.jsonl，capture结果native-trace1-capture-completed.json，分析native-trace1-analysis.json；当前恢复终态source-restored-native-trace1.json。无GPQA/性能流量、不叠加优化、不推送。

2026-10-24 04:42UTC后续：native-trace1已完成，192项layer/rank/repeat捕获；全部C1/C8、两遍及两rank的最终logits/hidden逐位等于未观测split1基线，观测中性通过。第0层native Attention的Q/K/V/output均逐位一致；第1层进入native前Q/newK/newV已不同，而cached224的K/V仍一致。rank0/1第1层Q最大差0.03125/0.0625、newV均0.0001220703125。当前首个已观察差异边界并非根因：应检查第0层输出投影、postnorm/MoE到第1层inputnorm/QKV/RoPE，不能将已不同输入的Attention输出差异归因给Attention。分析SHA cc095ef8ee22da077d667dd3800155c4363dec2807dc708e587dd9ddc8e56bbd。

源服务已04:28:29UTC恢复原split1/prefixON实例952146:1112664197，source-restored-native-trace1.json passed，原源码/argv/env及当前graph16/C8均核验。附加独立o_proj探针只使用捕获L0输出、当前checkpoint且与历史实际TP权重字节核对，相同mm/mm_out/layer_norm/log_softmax黑名单；M9/16/32/64/72仅测试形状数值依赖，不计时、不发模型请求、不作模型首算子结论。初版缺少阶段日志运行超预算，v2堆栈明确等待于torch.cuda.graph辅助器创建CUDA Stream、尚未capture，均归档incomplete并只终止自己的探针；不误称Attention或模型正确性失败。v3仅去掉独立graph构造检查数值，真实模型graph验证仍保留。后续native-trace2在原有opaque Attention backend返回处捕获完整padding形状/值和实际graph模式；仍须最终每batch输出逐位等于未观测基线，才能用于实际o_proj形状归因。无正式GPQA/E2E或新精度gate。

v3投影形状数值扫描已完成（o-proj-shape-replay-v3.json，SHA71cf1eece5b3de7d910a30b2ce0d795017e271ffcdf7115a6f062fd1520c7abb）：rank0 M64/M72相对M9仅两个元素不同、最大9.536743e-7，rank1所有M逐位一致；CPU模拟BF16两rank求和后全部逐位一致，未证明真实PYNCCL结果或编译后投影。因此暂不能将o_proj判为当前整模型差异的原因。预检docker top只给args字段被Docker拒绝，尚未变更helper或源服务；新prepare_native_trace2_v2修正pid,args，原失败归档，避免当模型失败。

当前唯一native-trace2控制器3209126:1112873992（脚本SHAdd813e050df18706f6980a68e1e9b5f16db2310166f7ede53158eeb824562c43）于05:00:19UTC临停源952146并启动独立split1实例53346:1112876576。原配置不变，只在现有opaque Attention backend的原forward返回后读取L0完整padding张量和实际graph模式，无模型module hook/新增数学graph op；此前全部层native捕获保留。新trial model/split1-native-return-trace，必须再证明最终logits/hidden两rank、每batch/每重复逐位等于未观测split1才使用结果。当前恢复终态仅看source-restored-native-trace2.json/source-restore-native-trace2-failure.json，旧恢复不作现状。单控制器finally负责原split1/prefixON/argv/env与当前graph16/C8核验，不启动并发中断审计。任务未完成，无GPQA/E2E流量或新gate。

2026-10-24 05:12UTC跟进：native-trace2已完成，最终全部logits/hidden相对未观测基线逐位中性，分析SHAfdbb85342dc778b10c96364cdcaac6bd003c2d351e0187d9376ba9de0fba4596。实际C1为paddedM16/actual9/PIECEWISE，C8为M72/actual72/NONE；第0层Attention完整return的前9行在两rank/两重复均逐位相同，因此不能把padding本身或图模式不同直接当成错误。源服务05:08:21UTC已恢复960552:1112903982原split1/prefixON/graph16/C8及source/launch验证通过。

后续最窄MoE观测（moe-trace3）：既有opaque MoERunner._forward_impl内部复制L0输入、_apply_quant_method的真实router_logits、TritonExpertsFL.apply的hidden/topk/输出，以及runner最终输出。原数学调用、路由、权重和配置不替换。诊断副本与单一freshness stamp写入随原graph一起capture，L0 Attention后将各候选stamp清零，L1 Attention中要求恰有一个本轮stamp=1，防止误读旧capture静态缓冲。只增加诊断copy节点，不加数学实现或模型module hook；全部最终logits/hidden仍须逐位等于未观测split1，否则拒绝用于归因。捕获缺失、stamp不唯一或中性失败均incomplete并finally恢复源split1；无GPQA/E2E，不叠加优化。命令/SHA已在state执行前归档。

当前moe-trace3唯一控制器3251778:1112984096（SHA1dc28e468b98e76d8883c120911af02df2813c865edc9c5744229a93abed0844），05:18:40UTC临停源960552后启动独立split1实例64033:1112986683，仍GPU4/5/TP2/18977/prefixON与原argv/env。当前终态moe-trace3-analysis.json、moe-trace3-failure.json、source-restored-moe-trace3.json或source-restore-moe-trace3-failure.json；不复用旧恢复身份或旧graph证明，不并发中断恢复控制器。

2026-10-24 05:42UTC跟进：moe-trace3在首个C1请求时拒绝缺失的实时副本（PIECEWISE/M16候选0、fresh0），HTTP500由诊断assert触发，无可用于归因的MoE数值结果，不称模型正确性失败。单控制器已05:26:27UTC恢复原source968760:1113012021，split1/prefixON/graph16/C8/source+launchpassed。文件证据显示native依赖的观测器安装晚于首次capture；原版因此不能证明C1图中包含copy。新v4将MoE复制观测独立提前到原MoE一次性命中检查之后、任何capture之前，硬断言原capture计数nc=0且当前不在capture；原生Attention探针仍等真正native命中后安装，保留真实native来源核验。额外记录各layer/M/mode/capture入口，并跨同M的捕获候选使用原freshness stamp选择，必须恰有一个本次执行写入，不依赖capture与运行期mode字符串相同。模型数学/配置不变、最终全logits/hidden中性门禁不变；本轮仅修诊断时机，不叠加优化或跑正式评测。命令/SHA执行前归档。

早安装准备v1/v2在修改helper、probe或停止源服务之前因换行/缩进匹配断言退出，实际SHA均仍等v3；原文件及失败回执保留。v3按实际唯一install_logits_probe调用行派生缩进，私有clone helper/probe新SHA在moe-trace4-variant.json保存，不影响原source。当前唯一moe-trace4控制器3314543:1113179838，SHA0f7e229ad5dadcc1df2b039bd3ba947d5996be836d0faf1e2dc5dbf8060dee14；05:51:17UTC临停源968760后启动独立split1实例76130:1113182424。原配置、prefixON、GPU4/5不变。终态仅用moe-trace4-analysis.json/failure.json与source-restored-moe-trace4.json或source-restore-moe-trace4-failure.json；严禁中断finally恢复。

moe-trace4成功：两rank均证明安装时nc=0/notcapturing，C1 PIECEWISE/M16与FULL/M16的两个候选中恰有一个stamp在本次执行写成1；C8 NONE/M72新副本同样唯一fresh。两rank/两batch/两遍最终logits/hidden对未观测split1全部逐位中性。L0 runner输入、gate logits、专家hidden、topk权重/ids均逐位一致；TritonExpertsFL.apply输出首次不同：rank0两遍均22元素、max0.0001220703125；rank1两遍均20元素、max0.0000152587890625。差异继续出现在quant输出和runner输出。分析SHA73fdd982247f1e5b513e4aa6058b1962ca9b75da19ec42da407830eabf9cbdbc。准确边界是专家计算调用（FV内部计算及Plugin结果copy），尚未排除copy，不直接宣称FV具体kernel或最新版本导致。

原source05:59:12UTC恢复976963:1113209024，原split1/prefixON/graph16/C8/source+launchpassed，旧控制器已终态。下一步stage5仅对实际FV的dispatch_fused_moe_kernel（GEMM1/2）输入输出、实际配置/融合/路由加权标记、独立activation/moe_sum及FV返回前进行复制，比较Plugin copy前后；模型原调用/配置不替换。不同fusion造成语义/shape不同的中间输出标为不可直接比较，不能强作数值归因。记录首次实际L0的TP w1/w2到远端供后续忠实重放/FP64参考，执行前磁盘>8GB；权重只读复制、不入本地/git。早安装/livefreshness/最终逐位中性/单控制器finally恢复与GPU4/5范围保持，命令SHA先归档。无GPQA/E2E、不启动新性能优化。

当前唯一moe-trace5控制器3347911:1113244105，SHA c3bdea7cc3f8a743192d6a3aaae5e6912292fe22287ab509dc049e3d53f220e6，已在stage4原服务恢复通过后启动。trial model/split1-moe-internal-trace-v5，日志moe-trace5-events.jsonl，终态moe-trace5-analysis/failure与source-restored-moe-trace5/source-restore-moe-trace5-failure。必须读新launch事件获实际候选身份，不沿用stage4实例，finally原split1/prefixON原配置。

2026-10-24 06:12UTC跟进：MoE5完成、全部freshness及最终logits/hidden对未观测baseline逐位中性。分析SHA ccceb4dba70cd75df4a6d737094735b83308b8f4d8d9009b18597485ddf06f4b。真正首差在FV GEMM1+SiLU融合输出：rank0两遍9个元素max6.103515625e-5，rank1两遍4个元素max3.0517578125e-5；其输入及topk仍exact。C1实际GEMM1为BM16/BN64/BK128/group1/warps4/stage3，C8为BM16/BN128/BK32/group4/warps2/stage3；两者FUSE_SILU均true。GEMM2输入已不同，不能以它的输出差异证明其为首次根因。FV_return和Plugin输出所有rank/batch/repeat逐位一致，本次已排除结果copy。两rank实际L0TP权重各约604MB已只读保存远端并带hash，供重放；不是新权重或模型修改。原source06:10UTC恢复985170:1113273767，原split1/prefixON/graph16/C8/source+launchpassed。

下一步冻结GEMM1 crossover诊断：两rank×M16/72×实际S配置、实际L配置、仅S的BK128改32，共12行；不修改实现/模型配置，非性能优化。实际S/M16与L/M72必须逐位重现模型捕获前9行，随后比较同配置跨M以及固定M换配置。每行两次普通调用+3次graph replay，不能以eager替代graph。FP64用实际TP权重计算dot+SiLU完整理想值，报告BF16舍入及差异坐标距相邻BF16中点的比例；这是诊断报告，不事后指定容差或签发精度gate。独占GPU4串行处理两rank，源18977按已有授权临停、900秒预算并finally恢复原split1，GPU5及其他服务不执行算子任务；命令SHA执行前记录。无正式精度/E2E、无版本回归结论。

GEMM1 controlled crossover6已完成：12行全部普通重复与graph capture/3replay通过；S/M16、L/M72两rank均逐位重现模型捕获的原生GEMM1结果。同一配置跨M16/72完全一致，固定M更换S/L重现原rank0 9元素、rank1 4元素差异；仅把S的BK128改32即完整重现该差异，并与L输出逐位相同。因此本组首差已因果锁定K分块，不是graph模式或Plugin copy。结果SHA8271ac6220e0841a47cfc8272a6a7e413bf4ced22785b5014d1681a6b0658f6e。CPU FP64理想参考报告显示大部分差异坐标处于BF16临界舍入或近零取消区域，其中一个近5e-9坐标相差6个BF16编码步，不能声称全部仅1ULP。整体FP64误差报告不签发模型精度gate，也不证明最新版本引入回归。06:24:41UTC原source993495:1113361483恢复split1/prefixON/graph16/C8/source+launchpassed，原controller终态。

GEMM2独立控制7冻结：先4行实际per-M输入/原配置逐位重现模型GEMM2捕获；再将两M的目标前72条激活行统一为C1输入，保留原邻居、专家编号和权重，进行12行S/L/SonlyBK32交叉，全部要求两次普通重复和3次graph replay。这样区分GEMM1传入差异与GEMM2自己的K分块影响。对共同输入计算FP64 dot+routerweight，只报告差异，无事后容差门禁。仍只做组件诊断，不修改模型的MoE配置或代码；单控制器临停已授权本任务服务、独占GPU4处理两rank并finally恢复原split1/prefixON，其他服务不动。命令和SHA执行前归档。

GEMM2 crossover7完成，4个实际输入/原配置结果逐位重现模型GEMM2捕获；12个共同输入交叉行及全部16行graph/3replay通过。共同输入下同配置跨M完全一致；S/L差异rank0 22元素max3.814697265625e-6、rank1 16元素max3.0517578125e-5，仅改S的BK128→32完全重现L，两M一致。因此GEMM2有独立K分块舍入差异，不全是GEMM1传播。结果SHA8c8727dd055edb0ca99c5563d167c6824a9ba5a9c672ae18a52e42ee8843c379；原source06:31:44UTC恢复1001678:1113404246，原split1/prefixON/graph16/C8/source+launchpassed。

版本归因下一步8：clone保留的旧树MoE文件SHAfaeeead6990fb078e4ab625dba092eec47e1680a16f869659bd7743c0803ca3d已只读核对，与旧diag004记录相同；当前runtime为bbc2edded。各用全新独立Python进程，使用当前真实输入/同TP权重/同编译器与gems-opt，比较两rank/M16,72的完整FV原生配置选择，以及双方严格相同的S阶段配置。每case两次普通调用及graph3replay，当前原生选择必须逐位重现模型FV返回且配置完全相同，禁止混合旧新namespace导入。保存operator和实际YAML的SHA，不修改服务器或任何库/config文件，只在组件进程选择import路径。它只区分本组算子代码/选参行为，不能把旧库放进新运行栈当作历史完整模型gate或GPQA版本回归证明。先完成7原服务恢复再串行停源运行8，finally原split1/prefixON恢复；不新增性能优化或正式评测。命令SHA已在执行前记录。

当前版本组件8唯一控制器3438192:1113465316，SHA069400ea902b7474f503408f989b03ca843c1d71ab25906397de87d40d2d8147。source先恢复通过后才启动，两个fresh解释器串行old/current原生与commonS，全case图重放校验；source-stopped事件前不误记服务已停止，后续finally恢复source身份按新回执读取。当前终态fv-versions8-comparison/failure及source-restored-fv-versions8/source-restore-fv-versions8-failure，不中断恢复。


### 06:44 UTC：新旧算子归因完成，转入同机正式精度对照

旧库与当前库在相同实际 TP 权重、输入、配置及 M 下，GEMM1、GEMM2 和 FV 返回均逐位一致，16 项 graph 重放全部通过。两版都存在相同的 BK128/BK32 分块舍入差异；本次首个 MoE 差异并非最新 FV 更新引入。这不代表整模型分数或所有输入的版本等价。比较证据远端 results/fv-versions8-comparison.json，SHA d9986d5b88cb54a279397519113135232b82a131d4c6bfbf753fb72130879fc6。源服务已按原 split1/prefix ON 恢复并验证 graph16/C8/source/argv/env。

先前将全模型 C1/C8 逐位一致列为硬准入，是 Agent 自行增加的过严诊断条件。项目原契约以正式分数达到阈值判断精度；保留全部差异与历史失败，不将它们改称通过，也不为消除舍入差异修改 MoE。新 formal9 计划取代未执行的 proposal-only 草案，按原 GPQA 198 题、strict-match、64 分、C32、task seed42、request seed1234，依次在同 GPU4/5 独立进程验证 split1 与 split16。仅后者改 native Attention 分片常量，其余配置与 prefix ON 不变。每实例重新验证 graph/C8/真实实现，移除所有 cohort、中间值复制与 logits 诊断，独立原生评测缓存与输出；finally 单控制器恢复源 split1。未有新正式分数，不签发候选 gate 或性能结论。


07:00 UTC 执行记录：首次 formal9 预检将已有 provenance 回执文件名次序写反，在停服务和 helper/源码变更之前退出，零模型评测请求；保留 formal9-failure.json，formal9-preflight-recovery.json 已记录修正。唯一 v2 控制器 3476227:1113593553（SHA 6b42c4cd6a28da0a4ef21caa363e8d200b8025d6d5b84f4971cf04f1a23d7673）随后启动；07:00:15 依授权停源服务，并以正常原始 helper 在 clone 启动 split1 103178:1113596207。当前为模型启动，尚未声称已发 GPQA 或出分。正式计划 SHA d9d1fff151216c1fc3db4a7803d3521f0d36bcbf7309ba319d185dba759b1a1a。后续只跟进 logs/formal9v2-events.jsonl 和 formal9v2 终态/恢复回执，不能把旧失败或旧恢复当作现状。既有半小时 heartbeat 已更新以跟进同一控制器。


07:04 UTC 跟进：唯一控制器 PID/startticks 未变。split1 当前实例 103178:1113596207 的两 rank 原生实现命中、graph capture/16 replay、C8 及源码/启动身份均通过（07:03:49）；正式 preflight 通过后于 07:03:57 启动 GPQA。原 runner 证明 limit0、198 题、C32、原生成参数及新 UUID 缓存，07:04:11 的命中数为 0 cached/198 remaining，模型正在处理 32 个请求。此为正常进度，尚无有效分数、无 gate。服务/runtime/minimal/正式启动 SHA 已入 state，继续等待同一进程，未重复启动。


07:34 UTC 只读跟进：唯一控制器 3476227/startticks1113593553 仍匹配，split1 正式评测尚未结束、split16 尚未启动。原生进度 07:31:25 为 190/198、strict 129/190、0 timeout；这些是部分进度，不签发分数/gate。07:34:40 服务仍有 7 个请求运行、0 排队、0 error，持续生成，prefix cache 命中计数实际增长；无原生最终 results 文件。未重启、未新增请求、未改变配置，保持原控制器继续完成和 finally 恢复。


08:04 UTC 关键进展：split1 正式 GPQA 已于 07:47:47 完成，198/198 唯一样本，strict-match 131/198 = 66.1616%，达到冻结阈值 64%。原生 result/sample/provenance、评测前后源码与服务身份均核验通过，独立签发并 check gate（SHA b016efd0d54f8d4db7285c07019b28ca81f220fe1f85f4ae44d0672a54da99b8）。此 gate 只绑定已评测的 clone 实例 103178:1113596207；该实例已按计划停止，不能自动用于当前 split16 或未来恢复源实例。

唯一控制器未变，07:48:14 启动 split16 实例 144806:1113884096，正常 helper/Plugin 分片常量16/实际 MoE 来源证明、两 rank graph16/C8/source+launch 于 07:51:48 通过，07:51:56 启动独立 UUID 正式评测。08:03:26 原生部分进度为 180/198、118 正确，尚无最终结果，不能将部分分数当精度结论。其余配置/prefix ON 均不变，继续同一控制器并等待 finally 恢复原 split1；未做新的性能实验。


08:34 UTC 正式失败冻结：split16 于08:10:25完成全部198题，strict-match120/198=60.6061%<64，原生证据及源码前后一致有效，不签发gate。split1为131/198=66.1616%。控制器08:14:20已finally恢复源split1/prefix ON，实例1018035:1114019911，graph16/C8/source/argv/env通过（恢复receipt SHA0af8bcbc855e266e0e03de93cd3c9bdf2c142edccce48616a602794c84f3ff74）。原两评测实例均停止。

精度定位 accdiag-fixed16-gpqa-001：逐题分析198个doc与request arguments指纹全部相同，权重/tokenizer/engine/FG/FV/argv/env一致，Plugin唯一差异为native Attention分片。111题两者对、58题两者错、20题1对16错、9题1错16对，净少11题；仅4条完整响应逐位相同。不能用单轮分差或探索性的配对统计断言根因或排除采样波动。正式性能晋级保持阻塞，原失败永久保留。

预冻结下一步formal10诊断：仅再跑一组同契约split1→split16，共两次198题，之后停止本轮重复系列并一起报告全部4轮；不根据分数继续加轮、不筛最好结果、不修改MoE/采样/gems-opt/阈值/数据。每角色独立fresh进程/KV和UUID，GPU4/5、prefix ON及当前argv/env不变，graph16/C8/实现命中与原生身份仍逐实例核验，finally恢复原source。重复通过不能覆盖已发生的split16失败，也不构成E2E结论。新脚本与SHA先入state，远端执行前归档commands。


08:39 UTC 第二组执行：formal10-plan 已在模型请求前冻结（SHA f0827b0a095d978d67fdc0e069c0bf83d97d8d80b749229ca37107a937b51c5b）。唯一控制器3707094:1114186258，SHA ede136b43a2aa0c356fcafefc723595e895637244ff8cad5955f967f91890fe3，08:39:02依授权临停刚恢复的源实例，clone split1 186652:1114188870 正在加载。第二组仍为诊断，前一组有效失败不作废，未启动新的性能优化或调整分片候选。逐题分析结果 SHA def810f0a39e6c9c4cb268dc58cdcedb3798bcb60e542c6c53d2f57cd39b7406 已记录。现有半小时监控已切换为formal10唯一控制器与其finally恢复回执，不能使用上一组历史恢复代表现状。


09:04 UTC 正常跟进：第二组唯一控制器3707094/startticks1114186258仍匹配，当前split1实例186652:1114188870的graph16/C8/真实实现及source+launch于08:42:40通过，08:42:48正式开始，独立UUID47911a4ae78a4c689cd64425ab5daeb0。09:02:55原生部分进度180/198、125正确、0timeout；当前15请求运行、0排队、0error，尚无最终result/gate，split16未开始。继续原控制器，不从部分结果推断重复性或新精度结论，不新增流量或变更配置。当前实例身份/运行/minimal/正式启动SHA写入state。


09:34 UTC 关键复现证据：第二次split1正式评测于09:26:33完成，仍为131/198=66.1616%，并非仅总分碰巧相同：198道题的doc、request arguments、完整响应SHA和正确性全部逐题一致；两次完整native样本文件也同SHA58027b2c0dd97fe364d42afed1e799e9f25d4f23975d787c8a11082af4b6ddb1。两次分别于07:04:11、08:43:02记录0 cached /198 remaining，使用独立UUID/cache和fresh模型实例，未跨次复用响应。因此在目前控制条件下split1整轮精确复现，不能简单将首组跨分片差异归结为已观察到的split1采样波动；仍须等待split16第二次最终证据，不能由此单独确认算子根因。

当前唯一控制器3707094未变，split1实例已停，09:27:00启动split16实例228286:1114476698，两rank graph16/C8/source+launch于09:30:29通过，09:30:36开始正式评测，UUIDbdce16fa1311431c8ff58f70ed24dd7b。09:33:46只有80/198部分进度，不作精度结论。保持原计划，完成后finally恢复原源split1，不加第三组或新分片/性能。


### 10:07 UTC 四轮归档与规划复盘

固定预算四轮结束：split1 131/198、131/198（均66.1616%>=64），split16 120/198、120/198（均60.6061%<64）。每种分片两次的198个题目、请求参数、完整响应与判分逐题一致；四轮均独立fresh模型/KV/UUID缓存且0cached/198remaining。跨分片仍为20题对变错、9题错变对，净少11题，仅4条完整响应相同。结果随1→16→1→16稳定复现；当前四次轮间采样波动为零，但不由此声称所有配置都无随机性或vendor实现必有bug。联合分析 formal-four-runs-analysis.json SHA c0e440a3051ecd31ee37319ddc3855516fd294a053e0ba6b2f2b2daff913db8e。完整重跑系列按冻结预算停止。

09:52:56已finally恢复源split1/prefix ON，实例1026202:1114611484，两rank graph16/C8/source/argv/env通过。split16不晋级；既有MoE、sampling、gems-opt不变。精度失败仍阻塞新性能优化，未测split16 E2E/ERQA，不以组件快或GPQA完成时间作性能结论。

规划复盘 plan-op001-accuracy4-20261024：无新的可保留端到端收益；旧split0/1稳态性能属不同实验，不累加。Prefill缺少新纯设备分段证据；Decode有native KV参数潜在代价但16仅组件收益；Mixed需在精度修复后重新测。优先1为same-prefix原生Attention边界捕获，优先2为实际同QKV/参数忠实重放与高精度参考；其他分片候选/算法暂缓，不能为过64分反复尝试参数。下一复盘触发为边界+重放证据或新的观测incomplete。

native11预冻结：独立clone仅保留失败候选split16，复用已有prefix0 fixture（缓存224/query9、C1和真实C8各两遍、两rank）；只在已有opaque Attention的原native调用返回后读取实际Q/K/V/output。先要求所有最终logits/hidden逐位等于未观测split16基线，再与已证明中性的split1 native1逐层同batch比较。输入已不同的下游输出不能当根因，缺失或不够中性即incomplete并恢复。该fixture来自doc0，两分片该题均正确，故只能定位数值机制，不能单凭它宣称解释了GPQA错误。无新完整评测、无新分片候选/数学kernel/性能改动，finally单控制器恢复原source。脚本执行前归档commands与SHA，所有权重/原始张量仍留远端。


13:19 UTC（以原生时钟为准）native11工具incident：初控制器T赋值仍引用旧model/split1-native-trace，打开xb日志时FileExists保护拒绝，旧日志未覆盖，candidate未启动、0诊断请求；仅授权源服务已停，finally正在恢复，不中断或并发审计恢复。错误属于控制脚本，非模型数值失败。v2已静态解析AST验证T必须等于新model/split16-native-cross-trace-v11，并在stop之前检查log不存在；额外preflight在首次finally恢复passed且控制器退出后才启动，检查目标日志全空、fixture字节相同、helper/probe SHA和clone无模型进程。旧failure保留，禁止强覆盖旧产物。


13:25 UTC 目录incident恢复与修正完成：初native11 finally于13:22:59恢复source1034234:1115870704，graph16/C8/source/launch通过，旧失败保留。v2 preflight静态T/空日志/fixture/SHA/无clone进程/旧controller已退出全passed后，唯一controller4180766:1115905576（SHA70dad3f002ccfd1578552e98fea157f0c5e78545d12bb104b3757c86c3abdffd）启动。13:25:34依授权临停该source，13:25:35于正确新目录启动clone269935:1115908162 split16数值诊断。当前尚在模型加载，无新数值结果；finally恢复以source-restored-native-trace11v2.json为准。监控已切换到v2，不能重复旧formal/旧controller或沿用历史恢复作现状。


### 13:33 UTC 首个跨分片数值边界已定位

native11v2 completed：384条实际native边界比较，全部8组（两rank×C1/C8×两遍）最终logits/hidden对未观测split16基线逐位中性，实际cohort8/缓存224/query9及真实native来源均证明。首差稳定在L0：Q/K/V和cached KV全部相同，其他native参数唯一区别num_splits；rank0输出3573元素不同、max1.220703125e-4，rank1输出3197元素不同、max2.44140625e-4，C1/C8及两次重复一致。分析SHAdd0b2eb48a51a4e44962aa6233b3c1dd63fd2143178c80413e98f6854d45516a。可以定位到nativeAttention输出对固定分片的数值变化，尚不能据小差异断言kernel错误，亦不能仅凭doc0解释GPQA错题。

13:33:35单finally已恢复原source1042549:1115934877 split1/prefixON，graph16/C8/source+launch通过，恢复receipt SHA64a530f56855bde5fc60829d9e45049010475c11f271e459feb3a7a62181618d。旧工具目录incident已解决并保留历史失败，不覆盖旧数据。

native12预冻结：在原服务恢复通过后，仅GPU4顺序重放两个rank的真实L0 C1/C8输入，保持KV原shape/stride/物理页/table，Q按存储的连续flat布局显式恢复，要求两分片均逐位复现对应完整native输出、重复与graph3，再计算CPU FP64 causal GQA参考。共8项不加新分片、不采集计时；报告abs/RMS/relative-L2及参考舍入到BF16的差异，原组件容差仅作诊断，不能覆盖GPQA失败。参数/精确重放/graph/内存门禁失败即incomplete，900秒预算，finally单控制器恢复原source。未改算子库/编译器/数学实现，MoE/sampling/gems-opt和生产参数不变。


13:42 UTC native12完成：两rank×C1/C8×split1/16共8项完整native输出逐位复现模型捕获，普通重复与graph3均exact，输入按真实KV shape/stride/物理页/table与存储连续Q重建。CPU FP64 causal GQA参考：rank0两分片maxabs均1.2620193582e-4，RMS分别4.5946e-6/4.5383e-6；rank1两分片maxabs均1.7626859485e-4，RMS7.2094e-6/7.1411e-6。原组件tol诊断8项通过，16的RMS略低。该证据不支持“大幅算错”的判断，符合不同分块/归并数值路径的可能性，但不能仅凭局部小误差排除实现问题或签发模型gate。结果SHA9a6ec7e37e2751520c4d313ef69a405c6a08bd8a3e86ad708424d3ea2799ce66。

13:42:23 finally恢复原source1050751:1115988182 split1/prefix ON，graph16/C8/source/argv/envpassed；service SHA5789299067dcfc269baf4574202f88ed003ba4b53dc235b81f0b890f1b8c539a，minimal SHAcec3f20f43a8870458a456fc9f25cd6443203110205e774d53277a239664bf0e。native12已退出，无活动诊断controller，没有新性能或完整精度评测。

v13仅CPU准备真实错题doc20：用原生iter_sample_records读取多行样本格式（直接逐行JSON解码失败仅为只读解析尝试，不是样本无效），实际注册OpenAIChatCompletion._create_payload生成原始请求（模块SHA83cb3d92、method3670e613），维持seed1234/max_completion_tokens18000/temp.7/topP.8/topK20及原factory stop。请求SHAf68c7f5d9989571e62d3b76c1bf7e10046040b637e47c760429eaf3d9cc2e36c，计划SHAc1c34ff7411c7e1e282953d34534bcd6c4b0bca9188e083cd46994f922d44147。旧正式响应1529/1470字符，仅前20字符相同；不能将旧文本重分词冒充实际生成token IDs。当前API支持return_token_ids；下一步须先冻结单题C1原请求、token元数据开关中性、可比prefix-cache准备、有限请求预算和finally恢复，再发GPU请求；C1不忠实则定位batch/cache，不能改seed或门槛消除失败。v13尚未启动模型请求或controller。


### v13 单题执行契约（执行前冻结）

仅原生错题doc20，source normal split1与失败split16各新建同配置graph服务。每角色固定3个C1请求：原始请求、仅return_token_ids=True元数据两遍，共6个，不自动扩C8/新分片/正式GPQA。原factory生成的prompt、seed1234、T.7/P.8/K20/max_completion_tokens18000、stop均不改，仅明确stream=False。HTTP180秒/角色就绪后600秒预算，异常保留并finally恢复原source。

代码核对表明/reset_prefix_cache HTTP200不检查底层成功，不能直接当缓存已清证据。每次仅在私有clone空闲时POST reset_running_requests=false/reset_external=false，缓存开关始终ON，前后采集实际metrics，要求本请求prefix queries增量>0且hits增量=0，否则同缓存条件不成立并停止归因。不触碰生产source缓存。plain与元数据请求须全文、prompt/completion计数一致，两个元数据请求实际prompt IDs/生成IDs逐位一致；使用API真实token IDs，不以旧文本重分词冒充。元数据中性失败即incomplete，原始响应全部保留。单题完整文本另与两组原formal文本比较，不忠实则明确标记reduced-reproducer-not-faithful并诊断batch/cache，不能解释为正式失败已消失。

使用正常one-shot真实native/MoE probes，当前实例graph16/C8/source/argv/env核验后发单题请求，前后sourceguard防漂移；clonehelper 9c2839da先备份，允许安全切换至normal helper，source cfa不变。当前controller/result/restore使用doc20-v13唯一名，T按model/doc20-v13-split{1,16}且stop前验证空目录，不复用旧日志路径。命令与SHA先归档，当前无新的性能或完整精度验收意图。


14:08 UTC v13运行时接口incident：split1当前实例graph16/C8/sourceguard已通过，但POST /reset_prefix_cache返回404。源码中确有dev路由定义，运行时未注册；先前只检查源码而漏检路由可用性。控制器在发doc20正文前退出，0目标请求，旧正式失败不受影响，finally恢复中，不中断或并发审计。此前single-request-started事件包含缓存预检起点，不能误算为已发模型请求。

v13v2新诊断契约：保留原6个目标请求预算，改为每个请求独立fresh服务/KV，分别1-plain/1-tokens-r1/1-tokens-r2/16同3项；不启用devmode、不添加API、不改vLLM或采样/源配置。每实例相同graph16/C8守护后仅发一个doc20，实际prefix queries增量>0/hits=0证明目标不复用前缀，prefix开关始终ON。6实例带来显式服务身份变化，跨fresh实例全文/usage计数和实际IDs一致用于观测一致性；若不一致不能只归因metadataflag。原HTTP180秒，整体1小时诊断预算（每次启动前检查），不自动加请求/C8/正式评测，finally仍单controller恢复源。新代码路径与SHA先归档；必须v1finally恢复passed且controller退出后才启动，0旧目标请求用原始文件检查证明。此为不可用接口替代缓存准备，不修改任何精度门槛或生产配置。


14:13 UTC v13接口incident恢复并启动v2：原source1058946:1116169177于14:12:33恢复split1/prefix ON、graph16/C8/source/launchpassed，原precheck404在发doc20正文之前，0目标请求已由原requests目录证明，incident-recovery回执保留旧失败并resolved。新v2契约SHA1e73fa2acc57b3d336b5895e81d011e62afd2cf959dbdcb3e0274adaaae66f58，唯一controller97218:1116195790（SHAef8f3854e2ce6722031dded845f8e3047d78478a950e3b044dbc8dc1f8c89740）14:13:31启动；14:13:57依既有授权停该source，clone首个fresh1-plain实例290029:1116198404正在加载。当前无新的doc20结果/实际token结论，finally恢复以source-restored-doc20-v13v2.json为准，监控已切换新唯一controller。

下一步采样分析的静态代码核对：当前vLLM random_sample按probabilities与exponential noise竞争选择token，不能盲假设CDF抽样。此为源码路径，不等于已证明本请求实际采样实现或捕获噪声/Generator状态；后续仍需真实路径和输入/状态证据，不能从top-k排序差异直接推断采样根因。


### 14:30 UTC 单题 C1 对照尚未忠实复现正式响应

split1 的 plain/tokens-r1/tokens-r2 三个 fresh 实例已完成并依次停止，各实例当前 graph16/C8/source 核验通过；三次全文与 usage 完全一致，两个 metadata 请求的实际 prompt IDs（362个）和生成 IDs（262个）逐位一致。各目标请求 prefix queries 增量362、hits增量0，开关仍ON；该结论只覆盖已测 C1/fresh-cache 条件。聚合回执 SHA8ce11cdd3925c2c4e92d664bfbec23d3eabc3c22e4b3515847a2136b06e41c9c。

但缩减 split1 全文930字符，原 C32 正式响应1529字符，仅20字符公共前缀（随后 identify which / identify the 开始分岔），两者最终答案均C。必须记为 reduced-reproducer-not-faithful，不能用 metadata 一致性宣称原正式错题因果已复现；batch/cache轨迹的影响仍未区分。split16 plain 首个请求已完成，362prompt/389completion、零目标prefix命中、全文1362字符且答案C，而原formal split16答案B；其余两次尚待结束，当前不下最终聚合结论。

同一控制器97218:1116195790继续冻结6请求；14:30:11已启动split16/tokens-r1，尚不启动额外C8/完整GPQA/新分片/性能。source由此控制器临停，当前finally恢复仍待完成，不能用14:12历史恢复证明当前服务。后续先核验全部6次、实际共同token前缀及单finally恢复，再设计batch/cache最窄诊断；不改变采样参数、MoE、gems-opt、精度阈值或prefix开关。


### v13v2 终态与 v14 最小并发诊断设计（GPU执行前）

14:38:20六次单题已全部完成；split16亦三次全文/usage一致、两次实际prompt/生成IDs精确重复，但不复现原formal。两split共同prompt362 IDs完全相同，共同生成55 tokens，第56个token分别26160/892，C1最终均C；不能解释formal split16的B。结果SHA3b735255d1eb59009af10cbd2b82e77515241c528acdde1bb83af807ac31da09，实际前缀SHA3eca5e26314fa29b518001848a36d4142e3ed4d357af76df2906cfa7179479c2。14:41:53单finally恢复source1066979:1116344664，原split1/prefixON/source/argv/env/graph16/C8通过，恢复SHA68e59fb4522c2b60e4f66168064712a29971c14397a3a09fb162d8c09fe99567；在source容器PID命名空间另核验同startticks、models HTTP200（host同PID不可直接代表容器进程）。

CPU补核：正式API amodel_call使用TemplateAPI默认_seed1234，无逐请求自增，prompt同为362tokens；formal1/16分别416/412completion，response未报告cached_tokens，不能假设缓存条件已知。实际context是JsonChatStr NamedTuple，len为1；API虽注释按文本长度排序，真实排序键在此都是1，不能用1398字符长度推断doc20排第38。必须运行原Collator重建实际队列并核验；原生样本顺序doc0..197，doc20属于原首32请求是待CPU断言验证项。response header日志第7/9次出现doc20并非请求发出顺序证明。

v14预冻结最小邻居复现：仅doc0..31，两个fresh私有角色1/16，各一次原C32 HTTP并发，总64请求、不重试、不补入doc32+。原factory生成全部payload并验证doc20字节语义等于既有body，只有doc20增加真实token元数据；全部streamFalse。prefix仍ON，各角色相同graph16/C8护栏后开始，源码/launch前后审计，保存aggregate缓存指标，不能当每请求命中证明。HTTP600秒、client660秒、整体30分钟启动前门禁；任何incomplete先finally恢复。只比较原正式全文是否忠实，未忠实则停止本缩减系列并CPU复盘，不自动扩完整GPQA/新split/性能；HTTP C32不当作实际GPU batch32。控制器复用已证明的原stop/launch/ready/facts/guard并验证依赖SHA，当前脚本与SHA已先记录，尚未发GPU请求。


v14 CPU预检已passed：原registered JsonChatStr + Collator实际重排结果严格保持doc0..197，doc20零基位置20；首32 payload与两split原生请求参数一致，doc20原body语义完全相同。计划SHAe719f1b84c72097cad7d21edcd0671672e4c7cf4e61c2bff4c3575a6c3ad3612，排序审计SHA940c33ad31cd8c05a1e4ba1879cc0ce9585f102ee58abb0641a2da9a445d21ed，冻结payloadSHA22d33ca329e7ad50bd5d356c873bf2ee1f2f02431fb0ab9501882f2781fffda3。接下来仅执行已冻结有限对照；无新的正式分数/gate意图。

15:07:50 UTC 已启动唯一v14 controller218801:1116521734，SHA c9b7b085e25ff6dd274f55e8798dfece6a94278b1dd0b719aeaa9be389af2079。后续以doc20-v14-events及source-restored-doc20-v14终态为准，旧v13v2恢复仅为本次临停前事实，不能当新finally证明。不得并发interrupt/重复控制器或重跑完整GPQA。


### v14 终态与规划复盘 plan-op001-reduced-repro5-20261024

15:32:41 完成两个角色全部64请求，client peak32，源码前后审计通过；15:36:10 单finally恢复原source1075030:1116670822，split1/prefixON/原argv+env/source/graph16/C8passed。恢复SHAf8c310ebccd0bfc972f87ac002b5cfcc0a0b8c65cf754904ce346828fd3c4cac。旧控制器退出，clone无模型实验运行，未追加GPU请求。

纯CPU联合分析使用冻结strict-match RegexFilter+TakeFirst与原exact_match(ignore_case/ignore_punctuation)，先逐条复核两份原首32样本的过滤答案与分数（共64）一致，避免将native filtered_resps列表误当str或把target(C)括号当错。未执行的分析v1在只读drycheck发现此表示差异，v2修正后运行成功；该工具预检不影响模型/正式评测。联合SHA b0e65820ef342c42f8d8dd23ef50655924bf372eaec2ae36adde2f70bfca983d。

split1目标strict=C正确、split16=B错误，与原formal错对方向相同；两者全文仍未忠实复现，分别仅8/32和7/32全文等于原formal。doc20全文1575/1752字符，与原对应公共前缀1195/873字符；实际prompt362 IDs相同，实际生成共同6 tokens，第7个为279/892。保存真实前缀fixture SHAee7e245b3a157e426edd8e2ab8b46e0c731955f059d697fa20372e878abffc07。两角色aggregate cache queries均10610/hits496，不足以证明doc20自身的cache命中/位置一致；HTTP32也不证明实际模型batch32。观察到同一scoreflip，但不能把fulltrajectory不忠实改成passed或推定已证明vendorbug/正式错误完整因果链。

本缩减系列按冻结停止，不继续扩cohort/补位或完整GPQA。复盘：当前保留source1，无新累计E2E收益；Prefill缺每请求cache/shape，Decode已知actualfirsttoken分歧但rawlogits/filterprobs/noise未观测，Mixed缺原完整补位轨迹，不能拿评测耗时作吞吐。接下来仅CPU设计最窄sampler窗口观察：核验request-row映射、partial-prefill被丢弃sample与真实generation index、真实bound/compiled函数、Generator seed/offset和观测不扰动条件；候选窗口为真实prompt362+共同生成6 IDs。必须归档新的有限契约、命令SHA、neutrality和单finally恢复策略后才允许再发GPU请求。目标是区分rawlogits/过滤probs变化与实际exponentialnoise/RNG状态，不假设CDF。没有新的GPU观察器/请求在本次复盘中安装或启动。若路径/映射/窗口/中性证明缺失则incomplete，优先恢复，不盲叠数学修改。只有概率输入分歧明确时再按doc20真实输入做native边界重放；其他分片/算法/性能继续暂缓。


### v15 只读采样路径审计：条件性 RNG 状态契约不匹配

本轮未停止模型服务、未发模型请求、未运行GPU算子，也未修改Plugin/FlagGems/vLLM数学实现。当前source1075030:1116670822仍存活，models HTTP200；split1/prefixON/原配置保留。实际ModelRunnerFL是独立复制的runner，不能只hook vLLM GPUModelRunner基类；其_sample和_bookkeeping_sync AST与当前vLLM实现相同。CachedRequestState/InputBatch来自vLLM，但row会随add/remove/swap/condense移动，必须req_ids[row]/req_id_to_index/request/generator对象一致；async输出可能是-1占位，不能把它当真实token。sample_with_exponential_noise当前无decorator，但实际forward/alias命中仍需运行时证明；它原地修改probs或q，必须在原调用前取原始值。

发现条件性接口问题：Plugin及vLLM现有_bookkeeping_sync对discarded采样的Generator固定执行offset-4；FlagGems MetaX exponential_按ceil(N/UNROLL)推进，FP32 UNROLL=4，共享helper将增量向上对齐4。用目标容器真实host函数AST、私有CPU int64状态和inert kernel stub做跨组件契约模拟（不是GPU测试）：N151936/FP32从0推进37984，实际discard loop回退4后为37980，未恢复原状态。N16为边界对照可恢复；FP64与其他N也完整保留。真实源码SHA：MetaX exp fa6de6cd、random_utils cc421b44、Plugin runner0ad5228b。CPU结果sampler-static-audit-v15.json SHA4affee808d016f14ef2724f4751666dbb79471d562e365ad812f209a3289e55a，观察设计sampler-observer-design-v15.json SHAa3685bda6ffea4fa57841ce37ac5cc8ac4801cd07866fd2063314087bc381cf2。

已有服务证据补强但不扩大结论：当前parent过滤后的env指向/tmp/qwen-vl/oplist.txt，黑名单仍mm,mm_out,layer_norm,log_softmax；该实际日志15:36:08.904760 UTC有FlagGems._metax.ops.exponential_的METAX GEMS EXPONENTIAL_函数入口记录，impl SHA与clone相同。默认/tmp/flaggems_enable_oplist.txt不是当前进程选择的路径，其缺少exponential记录不能当反证。已有日志证明当前服务曾进入该函数，并非仅注册key；但不绑定doc20、provided Generator、discarded prefill或实际offset增量。证据sampler-existing-runtime-log-v15.json SHA9337d23c1121c1b8b80175ad20692e66fa86524120514c6a729b278acdc6964b。禁止据此直接断言它解释了split1/16正式分数，亦未归因最新FlagGems-vllm更新。

复盘plan-op001-rng-contract6-20261024将最小实际RNG契约验证置于更多cohort/logitcopies之前。已冻结设计协议sampler-rng-validation-protocol-v15.json SHA1250e989a78e62c7d1b833541fd06a8f5fcbb076d15bca08890c27182bb2e611：StageA未来仅GPU4私有进程、原FlagGems配置、N16/N151936 FP32，每N control accepted/trial discarded/trial accepted-after-original-rewind共3次、总6次，不额外调用、不重试、设备180秒。必须先归档可执行probe/controller/launcher和SHA，验证源服务身份/空闲/资源，再按既有明确授权临停自己18977，singlefinally恢复原source1/prefixON/graph16/C8/source。只验证actual ATen函数命中、实际privateGenerator state/offset和丢弃应还原前状态的契约；不关闭FlagGems，不要求native RNG位级等同，不产生精度gate或性能结论。当前无StageA GPU控制器、无设备测试启动。

若actual实现未命中或实际消耗仅4，应保存反证并停止此假设；若非4且固定回退失败，只能确认组件契约问题，仍须新有限metadata-only模型观察证明doc20确有discard及初次分歧前offset/noise变化。没有该证据不改offset、不加黑名单。可能修复方向为还原每请求真实pre-sampling Generator状态而非假设-4，但未实施，须处理row移动、async/spec与各backend后再验证。Prefill风险仅在真实丢弃采样时；Decode/Mixed仍缺实际噪声/概率因果证据，无新的端到端收益。


### StageA RNG 设备验证执行前冻结

已准备真实ATen组件probe、singlefinally控制器与launcher，并先归档commands/SHA及执行契约。仅GPU4/私有Generator1234，N16及151936 FP32各control accepted、trial discarded、trial accepted-after-original-rewind三次，共6次，不重试/加调用，设备进程180秒；不发模型请求、不改算子实现、不关闭FlagGems。核对实际函数源码/日志入口而非仅注册key，同时保存每次Generator offset/state、noise原始CPU副本和私有进程default RNG前后不变；执行Plugin真实AST丢弃回退循环。

控制器在停服务前验证精确source PID/ticks及idle、GPU4/5全部进程属于source、clone仅sleep、镜像d732与mount parity、磁盘和依赖SHA，停自己的18977后才启动component，并确认GPU4无其他进程。异常/超时仅清理完整绝对script参数匹配的私有probe，finally恢复原source1/prefixON/argv/env并核验当前graph16/C8/source。期望恢复240秒、诊断预算1200秒不作为打断finally的理由。真实GPU增量为4或缺入口时保存反证/不完整，非4只确认组件契约问题，不认定doc20精度根因。执行契约SHA 108fbbb37a033dc9f28869a3d539411c574def63521b2ed0b21faf439a85271a。当前尚未启动。


### StageA 实际 GPU 契约验证结果（恢复尚在进行）

唯一controller346771:1117047348于16:35:26 UTC启动；镜像/挂载/源码依赖/空闲/同黑名单与GPU4/5进程归属预检通过，16:35:53仅停授权source1075030。组件16:35:54启动，16:36:19完成恰好6次actual ATen exponential_ 调用，返回完成、真实MetaX函数入口命中、GPU4 C550、Torch2.8.0+metax3.7.0.7，私有进程default RNG状态前后逐位一致。结果SHA7cf247dcd99c37612d2999ed8305dcca9a1344b0feb3a076fbadc25f3bcbcff6，原始noise仅保留远端rng-stageA15-captures。

N16每次实际offset增量4，丢弃回退后恢复offset0和原state，下一次accepted noise与control完全一致。N151936每次实际增量37984，执行Plugin真实discard AST回退4后offset37980、state未恢复，下一次accepted noise与control的151936个元素全部不同。由真实device/Generator测量证实跨组件RNG回退约定不匹配，不再只是CPU模拟。该证据仍不证明doc20实际触发discard或解释split1/16 GPQA差异；未改任何实现、黑名单或模型参数。

控制器16:36:29记录component-completed后进入singlefinally原服务恢复；不重复测试、不并发interrupt，不用15:36历史恢复当当前证明。后续只有当前source-restored-rng-stageA15.json通过后，才设计StageB metadata-only model观察：确认doc20当前row/accepted index/discard和Generator offset路径；无该链证据不直接修复或跑正式评测。


16:40:03 UTC StageA singlefinally已恢复原source1083269:1117053588，原split1/prefixON/argv/env/source/graph16/C8passed；restore SHA2b1c3f4cf3495b8445b4cc4db7257d23058e766102a4bf6b55572ca1c055e7ce，service9b3cc827/minimalb3a56e26。另实查当前source容器PIDticks1117053588与modelsHTTP200；控制器346771已退出、无活动GPU诊断任务。组件只执行6次exponential_，没有数据集请求；finally保留原single/C8恢复护栏，不是正式精度评测。旧15:36恢复已成为历史。

StageB尚未实现/启动，必须独立有限契约和命令SHA/CPU验证后才可继续模型观察。现有正常observer SHA cfa在one-shot TritonExpertsFL.apply中调用install_split1_probe；可在私有clone该已加载ModelRunnerFL的时机安装幂等metadata observer，source helper不动。计划最窄三个host边界：sample_tokens清execute_model_state前保存scheduler上下文，_sample原调用前后记录target/被discard行Generator offset，_bookkeeping_sync原调用前后记录实际回退；所有原方法调用且只调用一次，无新增GPU tensorcopy、RNG调用或状态设置。动态row+reqidmap+request+gen对象必须一致，async-1只作占位不能冒充真实ID。候选窗口仍真实prompt362+共同6 IDs、首7个accepted输出及之前discard；API真实tokenID事后按acceptedindex绑定，不能伪称抓到了原始GPU selectedtensor。CPU假runner需要覆盖row移动、discard、async占位、读状态不消耗、幂等安装/一次flush。metadata host开销仍可能改变调度，需记录actualbatch/cache与窗口/错对，不以少量token相同宣称完整模型中性。若doc20未discard或分歧前offset一致，应记录对直接RNG解释的反证，不把组件问题自动当GPQA根因。不启动更多无观测cohort、完整GPQA或新分片/性能。

### Stage B16：实际请求 RNG 元数据观察（执行前冻结）

Stage A 已确认组件回退契约问题；本步骤只查 doc20 是否真的丢弃采样及首 7 个 accepted 输出前的 offset。私有 clone 仅包装 `ModelRunnerFL.sample_tokens`、`_sample` 和 `_bookkeeping_sync`，原方法各调用一次，不复制 GPU 张量、不生成随机数、不改 offset。CPU 假 runner 已覆盖动态行移动、丢弃/接受、async -1、幂等及单次写回。

有限预算为 split1/16 各一次原首 32 请求（总 64），无重试、补位、完整 GPQA 或性能；只观察首 7 accepted 及此前丢弃，单 rank/角色最多 64 次目标采样。主机观察开销可能改变调度，不能宣称完整 formal 轨迹中性。缺映射/窗口/双 rank 证据则 incomplete 并恢复。无 target discard 或同前缀 offset 相同为本观察执行中直接 RNG 解释的反证，不外推所有 formal 执行。

远端执行前脚本：
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/rng_stageB16_observer.py`，SHA256 `bf1e521bbb4ae5341eea8133be30ccc65eb95a9f5b4e8ffeea31e676e16bcd0e`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/test_rng_stageB16_cpu.py`，SHA256 `cb2705ed33f3f7d150ebcad17a21ababda1463f6823402911cfc22437d7d9033`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/rng_stageB16_controller.py`，SHA256 `b182dd573c90c0de30dc1a6ce3e1d04d72c3eb866c4f852ab0a83f4a8d978656`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/prepare_rng_stageB16.py`，SHA256 `b2066946c58829e6b12dad90f980b883d133d0b06f0f92a4ce2d7a2e08e54b1c`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/start_rng_stageB16.py`，SHA256 `817258d26463c41881a4eaa5c0720910e1bd21996437bbd26f56905b530c15a1`。

仅临停原 source `1083269:1117053588` 的 18977 服务；单控制器 finally 恢复原 split1/prefixON/argv/env 并重新证明 graph16/C8。此刻未启动 Stage B GPU。

Stage B16 远端 CPU 自检 passed，回执 SHA `6c5f118242c8f2497fc9cfb1ff4838a53e25bba8a97d913d619013b07e152237`。有限契约 `configs/rng-stageB16-execution-contract.json` SHA `be5359db6063a586c5d94db18179e093a206115089dceb1e7685f09668050876`，私有 helper 1/16 SHA 分别 `592cd3218f840f5a6c2832f57bcbb218302d4a9d8fbbcffb8f52927b5b1d173a` / `0d8cdac9f6ba54d889b06f32fb72e0dba44b56153f40d4416413beb8a675dd0b`。上述引用已在启动前归档；source helper cfa 不改。

17:08:01 UTC 已启动唯一 Stage B16 控制器 `368736:1117242849`（`manifests/rng-stageB16-controller.json`）。预检、GPU 归属、source idle 和准确 PID 由该控制器核验后才停服务；无并发 interrupt 审计。最终状态读取 `results/rng-stageB16-completed.json` / `rng-stageB16-failure.json` 与本次 `source-restored-rng-stageB16.json` / `source-restore-rng-stageB16-failure.json`，不得以历史恢复作现状。

Stage B16 窗口已有双 rank 证据：doc20 7 次均不丢弃，seed1234，采样前 offset 两 split 均为 `[0,37984,75968,113952,151936,189920,227904]`。首步 row20、27 行 logits、num_computed16/scheduled346；后续 32 行、每步 scheduled1。第7 token仍279/892。这反驳本观察窗口中“目标请求被错误 rewind 导致首差”的直接解释，不能仅由相同 offset 推断实际 noise 相同。完整32请求及恢复未终态，暂不签发最终比较。CPU联合分析命令预归档 `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/analyze_rng_stageB16.py`，SHA `c90831f495fe66c5ca50e8f0ef37ce816c717ab1eb9bdadc81373d145aba7cbc`，只在两组及本次 source 恢复 passed 后执行。

sampler-window17 CPU 设计草案已归档 `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/configs/sampler-window17-design.json`，SHA `f217decf13e872d16aba09eec7a4210549051573e20ee4a2c52d4cfd2932cb8e`，不是执行契约。新问题仅为第7token同前缀的真实 rawlogits/probs/noise/selectedID；需在原地运算前复制、原函数一次、无额外RNG，并证明动态row/acceptedindex/API映射及当前真实函数入口。Stage B 恢复通过及联合分析前不启动新 GPU；未来另行 CPU测试/不可变脚本/有限执行契约。

17:32:47 UTC 两角色全部64请求完成，`results/rng-stageB16-completed.json` SHA `1569edbe3b86125fb5426f6ec75fdc69d5d1739dc7dad3c59ca5e6083a104ead`。原 source 正由同一个 finally 恢复，尚未把旧恢复当作本次通过。

规划复盘 `plan-op001-sampler-window7-20261024`：Stage A 是独立 RNG 契约问题，Stage B 对当前目标首差的直接 rewind 解释给出反证；不据此修改 offset。Prefill 实际目标 computed16/scheduled346 且不丢弃；Decode 同首6前缀及 offset、首差未消失；Mixed 缩减cohort仍非完整formal轨迹。累计无新 E2E 收益。下一主实验为首差这一步的 rawlogits/probs/actualnoise/selectedID 捕获，先 CPU 原地修改前副本/别名/原函数一次测试与独立有限契约；GPU执行需等本次恢复及CPU联合分析通过。新分片、完整GPQA重复和性能继续暂缓。

Stage B16 终态：CPU 联合分析 `results/rng-stageB16-joint-analysis.json` SHA `91b167ade163270b86ba5f36478701fd049f36e53dbf73fa683c06cfc76a14af`。两角色各32份全文均逐位等于既有未观测 v14，doc20全部实际生成IDs也精确相同。这证明本轮缩减cohort输出复现，不能外推原完整formal轨迹中性。doc20首7采样无discard、offset历史相同，首差仍279/892；目标直接rewind解释被本观察反证，实际noise未捕获，不能只由offset相同就称noise相同。

17:36:16 UTC single finally 恢复当前source `1091594:1117391436`，split1/prefixON/原argv+env/source，双rank graph16/C8通过。`results/source-restored-rng-stageB16.json` SHA `cd27d6cffa488c3c9e2ca62741b088d66bbd792f61c5b9d3a0c9696b72530e9a`；service SHA `781fcf5311939c729afc11eaef2eada0f723de241ce07a9d3ccbad1a1f3229cf`，minimal SHA `7f8b54b39cecdccd0075bc3eb0f403f3b4219c3b470412c57d126b70406ce5eb`。随后容器内PID/ticks与models HTTP200实查通过，source正常helper cfa未改，控制器退出，clone仅sleep。当前没有活动GPU诊断。

下一步只实施单个实际acceptedindex6窗口的CPU测试观察器，并冻结独立执行契约后再用GPU；不依据组件问题直接修改offset或追加完整精度/性能。规划复盘 `plan-op001-sampler-window7-20261024` 已纳入该反证及恢复闭环。

### Window17：首个分歧 token 的真实采样输入（执行前）

私有观察器只在 acceptedindex6 复制 rawlogits，再在实际 `sample_with_exponential_noise` 入口、原地运算前复制目标行 probs/q；原方法一次，原 `_sample` 返回后传回 CPU，并保存 noise 与 sampler 两处实际 selectedID。早于窗口/非目标请求无 GPU复制；noise hook 完成后恢复。CPU fakeTensor/runner 已验证原地修改前副本、包括 q 被原函数修改后的保真、调用一次/返回不变、无额外RNG、行移动/kwargs/async占位、CPU传输时机、幂等及错误隔离。

准备在远端 CPU 自检和独立有限契约完成后，执行现有 split1/16 各一次原首32请求、最多64、每rank/角色一次捕获，不追加完整GPQA或性能。实际prompt+首6IDs、offset227904/row/scheduler必须对齐已有StageB；selected tensor 需API[6]核对。所有全文/usage/IDs差异保留，不宣称全formal轨迹中性。仅临停自身当前source1091594，singlefinally精确恢复原配置及currentgraph16/C8。

执行前归档命令：
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/sampler_window17_observer.py` SHA `c2084c1fa062d5f2828841680f62f4ee97de74db6a8fd54c08fcaac066bc046b`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/test_sampler_window17_cpu.py` SHA `7c9ef5dfbeb5d2072f29a6a7e30fbaeb83f1bb69bee35524d41398d9ba5a19f3`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/sampler_window17_cpu_analysis.py` SHA `063158eabc4807bf7537f0807a7c0ffd9bf928e22cd01c12382ff320b73acc44`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/sampler_window17_controller.py` SHA `352c44e3fdeade545501a8be8abfd685cbb1c117ea0baa979cdd09b88b8f81bb`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/prepare_sampler_window17.py` SHA `b294e5065e4f005d7f30f66c86e307fa8b7f6d07062539b8eeb5c69df44461ed`。
- `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/start_sampler_window17.py` SHA `38d42878e14178c1bab3f037f0cc4fac32e67adf831c4c6da45df06bced11f8f`。

Window17 远端 fakeTensor 与 CPU Torch 分析自检均 passed（回执 SHA `15e09e29cafe1440696513162887961b8df2a43ba1fb19c6e938cbc07b5696a2`）。执行契约 `configs/sampler-window17-execution-contract.json` SHA `0db555512e60e715e40f5d89b4d64da2081d16cd35168ca73686a1495440abec`；variants SHA `46ec14ef70fbf426088653b08cbcb546a6b6fc8007e9bf1863db1554aa2caa67`，新 helper1/16 SHA `43b24ddc46bf2c7c32e295de5943a6995ea6045c4db389e85ed48b6569997580` / `8e2748d2ae7acb4581e2f786861e185e11fbfa771edce2a078f2cb25c7221e06`。上述 SHA 在启动前写入本地；source正常helper保持cfa不动。

18:07:53 UTC 启动唯一 Window17 控制器 `483594:1117601973`，controller SHA `352c44e3fdeade545501a8be8abfd685cbb1c117ea0baa979cdd09b88b8f81bb`。18:08:19 授权停原 source；split1 私有实例 `510277:1117604662` 正加载。没有新 offset/采样数学修改。终态读取 `results/sampler-window17-completed.json` / `sampler-window17-failure.json` 与 `source-restored-sampler-window17.json` / `source-restore-sampler-window17-failure.json`，禁止并发 interrupt 或复用历史恢复证明当前。

18:11:21 UTC 只读核验：split1 两rank `510764/510765` 的 `sampler-window17-installed` 与 worker 证明已落盘，服务正在graph预热；未见当前failure/restorefailure。此为安装证明，不提前当作实际采样捕获或最终比较通过。

Window17 两split双rank单步捕获均 completed；split1全部32响应复现StageB，split16其余请求尚未终态。只读临时命令拟将候选原始logits/probs/noise数值输出本地，自动审批因原始张量须留远端而拒绝，命令未执行。取消原始值导出；后续详细分析仅写远端，外发仅汇总统计。

CPU参考命令预归档 `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/sampler_window18_reference.py` SHA `0427d3f30b9fc6f4e6d985e72b0e16363952511d3ba428431ef1d818712e718b`，只在Window17全完成且本次source恢复passed后执行。提取当前vLLM真实PyTorch top-k/top-p函数AST（源码SHA35b9），以FP32参数T.7/K20/P.8对捕获rawlogits做CPU32/64参考，再结合实际保存noise核对选择。无模型请求/设备kernel/推理源码修改；参考一致只涵盖这两组输入，不据此假设所有processor/后端/原formal轨迹。原始张量和候选值保留远端。

Window17 已完成全部64请求和CPU联合比较，`results/sampler-window17-completed.json` SHA `25fc09a5d3f83fa39ddb21c376da1693fcc1253b351b0ab721e01ebdbd2d050a`。真实noise两split逐位相同，rawlogits有139351元素不同（maxabs0.53125/RMS0.0815749），过滤后probs仅2元素变化（maxabs0.2551312），支持集合2→1。真实ID1=279/16=892，CPU64交叉交换noise仍由所用probs决定279/892。两rank每项捕获一致、原noise函数入口1次、实际selected两处及API[6]一致，首6actualprefix/offset与scheduler元数据对齐StageB。

观测中性边界：doc20两split全部actualIDs及全文都精确复现StageB，但全部32全文只split1=32/32、split16=15/32；故禁止宣称整个cohort/原formal轨迹中性。只能就同prefix目标首差确认noise不是差异来源，下一CPU参考核验logits→过滤是否遵循当前vLLM数学。原source正由singlefinally恢复，未复用旧restore。

Window18 CPU 参考完成，`results/sampler-window18-reference.json` SHA `51766f45aa0ede97d96ef69ded71aee6cfd2bd004e34625fb04999511946d9d2`。使用当前vLLM真实PyTorch过滤AST，两个输入的CPU FP32概率与实际GPU捕获逐位相同（maxerror0），CPU32/64参考都复现实际279/892、support mask一致。这支持本窗口过滤/噪声选择遵循参考数学，未证vendorbug或所有formal错题原因。

补充CPU临界点命令预归档 `/public-flash/jinghao/qwen3-VL/20261024-qwen3vl-metax-fixed-splits/commands/sampler_window19_threshold.py` SHA `b3f89f67b6f1e227deb273b8a8e983a4fde5f0a024bd59a2e7460cd4789ec2d0`：仅确认K20后最大概率是否跨过P.8、279是否被mask及截断前winner是否被移除。详细数值远端，外发仅布尔/计数，不改变真实采样配置、不产生模型请求。

### 当前诊断系列终态（Window17–19）

Window19 `results/sampler-window19-threshold.json` SHA `a128fabc1898c7548a86bf5a89cc2533f35e2ad99f7e097d46a4be3240a07cf3`：K20后最大概率在split1低于P.8、split16达到P.8；top-p支持集合2→1，279在split16被删除，且截断前结合实际noise本会胜出的候选被该mask移除。结合Window17真实noise逐位相同、CPU18概率逐位一致，已解释本观察doc20首差：模型logits差异跨越top-p离散边界，再改变采样选择。没有改变温度/种子/top-p/top-k或修复任何算子；本输入不支持采样过滤数学错误。该机制不外推全部formal错题，不宣称vendorkernel缺陷；独立RNGrewind契约问题仍成立但不是该目标首差的直接原因。

18:36:36 UTC原source恢复为 `1099814:1117753486`，split1/prefixON/原argv+env/source、双rankgraph16/C8通过。`results/source-restored-sampler-window17.json` SHA `71fcde58fc9e7920676f562faa5c737fa7bbdb12e6c5a6439f81330657689eb5`；service SHA `ff3fd952d12546f74750fad10f005acd2e21b143fec8a0a14ce017c6f6701416`，minimal SHA `b16e97b75c6394463b0fa60a33ecf0226ead6b27a0d5f818cce995be6a841b33`。随后源容器PID/ticks、models HTTP200、source正常helper cfa实查通过，controller483594已退出，clone仅sleep；CPU18/19进程均完成。

决策：保留split1；split16两次完整GPQA60.6061低于64，不晋级，局部算子更快/参考误差小不能豁免。尚未获得兼顾门槛和稳态性能的新候选，不签发新gate，不自动追加分片/完整GPQA/性能。当前有限诊断系列全部终态、无待跑诊断；停止heartbeat。未来候选及独立RNG修复按新的受控实验推进，当前冻结不自动实施。

规划复盘 `plan-op001-nucleus-boundary8-20261024` 已记录失败/反证/观测全局非中性、Prefill/Decode/Mixed证据与无新增E2E收益。原始张量与候选值仅保存在远端；自动审批拒绝的原始值导出已取消并以汇总分析替代，无遗留审批阻塞。

App 回执确认 `qwen3-vl-gpqa-erqa` 已 PAUSED；这是有限诊断系列终态后的监控停用，不是整体端到端性能达标声明。所有未来候选维持当前冻结。
