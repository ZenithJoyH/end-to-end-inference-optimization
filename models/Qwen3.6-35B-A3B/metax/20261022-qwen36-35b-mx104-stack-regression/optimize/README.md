# 20261022-qwen36-35b-mx104-stack-regression / optimize

原B接续只读复测：[retest-old](perf-retest-20261103-001.md#retest-old只读结果)同样下降，P32K各3轮总TPS-2.45%，P64K各前2轮-11.77%（本轮第3轮尚未完成）。确认opt4上午完成、KV预算补丁下午应用；补丁前后6515可比源码记录仅worker.py变化，当前原B仍保留修正。无新压测或服务操作。

当前稳态总吞吐诊断：[11月3日 retest](perf-retest-20261103-001.md)，对opt4的P32K/P64K全部三轮总TPS均值分别-2.13%/-11.77%。当前KV178.6万token，日志满载时Running49/26并排队；59,534源码/包记录相同，仅启动脚本变更。主解释为安全KV预算修正后的驻留限制，历史prefix/实例未完全绑定，因果占比尚未A/B量化；0新压测或服务修改。

容器存储维护：[当前B容器瘦身](container-slim-20261102-001.md)已完成，可写层26.05GB→10.14GB，回收15.91GB（61.08%）。59,535条源码/安装包记录前后内容一致，运行JIT缓存保留；两份冗余编译器副本已容器外归档。未启动服务或评测，旧评测/诊断继续暂停。

最新：[ERQA思考模式C32](erqa-thinking-c32-001.md) 未完成：104唯一请求中72成功/32HTTP500，296未发；MRoPE位置copy_的MetaX LLIR编译错误导致本轮服务退出，非OOM。thinking=True/max_tokens65536、显存0.9和6851源码保持；无有效全量分数，离线核验partial，监控已删除，不自动重跑。旧非思考47.5%保留。

最新全量与质量分析：预算修复后C32 GPQA159/198=80.30%（>=75%），ERQA400成功/无OOM、190/400=47.50%。[ERQA质量诊断](erqa-quality-001.md)确认17题因附加说明失去4.25个百分点；选项提取51.75%仅作诊断，官方分数不改。非思考短答与视觉推理仍待隔离验证；历史共同输入未见大幅新增下降。此次0新模型请求/服务修改。下文各实验早期状态保留为历史。

当前：[ERQA显存预算修复](erqa-memory-fix-001.md) 仅保留KV预算修正，`gpu-memory-utilization=0.9`、MoE/GDN/采样与LibTuner修复不变。预算版固定32题C32和35,112 raw patches原生视觉边界零OOM；69次短请求独立核验，无取证工具服务已恢复。图像拆批因未通过数值检查已回退，不能称两项均修复完成；未做全量GPQA/ERQA或性能，无新gate。

历史全量：C32 GPQA158/198（79.80%，>=75%）通过；ERQA180成功/32 HTTP500/188未提交，旧实例OOM退出，完整400分数未知。该旧gate不绑定当前改动后实例。C64 GPQA151/198及用户事后75%认可等原始记录均保留。

<!-- e2e:summary:start -->

- 案例：20261022-qwen36-35b-mx104-stack-regression
- 当前状态：container_slimmed_evaluation_user_paused_no_model_service
- 当前候选：release02@1bc0c77 + FGV guardedshortlist49e9/tuned MoE/GDN + FlagTree fe1d24f6 + Gems a456722a/lifetime-b639a0 + MetaX physical KV budget1ad4d858
- 下一步：Container cleanup verified; previous evaluation and diagnosis remain user-paused. No model service running was observed during cleanup; no service or model requests performed.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| container-slim-20261102-001 | completed_verified | — | [container-slim-20261102-001.md](container-slim-20261102-001.md) |
| user-gpqa-erqa-c32-20261029-003 | GPQA_passed_ERQA_complete_independently_verified | — | [user-gpqa-erqa-c32-20261029-003.md](user-gpqa-erqa-c32-20261029-003.md) |
| erqa-memory-fix-001 | budget_only_short_verified_image_split_reverted | — | [erqa-memory-fix-001.md](erqa-memory-fix-001.md) |
| user-gpqa-erqa-c32-20261029-002 | GPQA_passed_ERQA_partial_OOM_independently_verified | — | [user-gpqa-erqa-c32-20261029-002.md](user-gpqa-erqa-c32-20261029-002.md) |
| libtuner-context-lifetime-001 | kept_minimal_passed | — | [libtuner-context-lifetime-001.md](libtuner-context-lifetime-001.md) |
| erqa-tuner-retention-001 | verified_bounded_contribution_not_unique_OOM_cause | — | [erqa-tuner-retention-001.md](erqa-tuner-retention-001.md) |
| user-gpqa-erqa-c64-20261028-002 | GPQA159/198 passed; ERQA326 submitted/262 success/64 HTTP500/74 unsubmitted independently verified. No full400 score; service exited. Original0.9 and6850 sources unchanged; no retry or performance. | user-requested-GPQA198-ERQA400-C64 | [user-gpqa-erqa-c64-20261028-002.md](user-gpqa-erqa-c64-20261028-002.md) |
| regression-001 | Historical C32160/147 remains valid and original13 mechanism unconfirmed. Latest userrequested PR638+FGV MoE combined exact r39 originalnativeC64/full198160 independentlypassed with newgate. This does not prove pairedC32 recovery or isolated migration/backend causal gain; performance still unmeasured. | full-four-scenarios | [regression-001.md](regression-001.md) |
| pr638-001 | User explicitly accepts77.78% against suppliedNV77.53%; PR638 ready for review. Original native160/198 rejection retained unchanged, no rerun/new gate or isolated performance claim. | full-gpqa198-c64 | [pr638-001.md](pr638-001.md) |
| fgv-moe-001 | Current r39 real MetaX FGV fused_experts_impl on bothranks, numerical15+graph2, per-service graph2/C8/long and one original nativeC64/full198160/198 independentlypassed. New exact-launch gate at predeclaredNV.7753; score also equals old160 target. No performance claim or priorC32 causal resolution. | MoE-dispatch-current-model | [fgv-moe-001.md](fgv-moe-001.md) |
| fgv-moe-gemm-tune-001 | User requested direct code write: c4673a applied to private MetaX get_default_config, fresh import/four configs verified, one source file changed. Prior53+12+14 operator evidence reused via identical AST; model service not reloaded, no new GPQA/E2E. | p1024-d1024-c64-n128 | [fgv-moe-gemm-tune-001.md](fgv-moe-gemm-tune-001.md) |
| plugin-update-001 | Updated current release/0.2 from7cb5599 to1bc0c77 (merged PR638). All517 worktree file bytes equal backup, preserving six remaining tracked modifications/four untracked files. Conda+MACA import and399 Python syntax checks passed. No restart/model traffic/newgate. | environment-update | [plugin-update-001.md](plugin-update-001.md) |
| plugin-cleanup-001 | Restored dead env declaration, legacy Plugin full-MoE/fallback GEMM2+activation edits to upstream; archived unused E256N256 Plugin config. Entire active nonLoRA MoE branch AST identical, FGV c467/GDN/sampler/shortlist/PR638 preserved.399 syntax and real Conda+MACA/MPI imports passed. Port18135 not listening; no launch/model traffic/newgate. | environment-cleanup-current-unquantized-noLoRA | [plugin-cleanup-001.md](plugin-cleanup-001.md) |
| sampler-fgv-001 | Requested FGV filtering integration implemented. Plugin register_model installs idempotent filter wrapper; native sampler/RNG class unchanged.44 operator/6 import lifecycle plus final actual-FGV/RNG/fallback/repeat-registration and three cross-classification graph replays passed. Top-p-only safely retains native filtering after exact-mask failure; both-filter/k-only use FGV. Global FlagGems switch governs new explicit API like full MoE, no startup env changes. GDN/MoE/GEMM hashes unchanged. No model service/full GPQA/newgate/E2E run. | sampling-current-Qwen36 | [sampler-fgv-001.md](sampler-fgv-001.md) |
| env-cleanup-001 | Removed all13 Docker presets and5 MACA bashrc exports; original B retained. Follow-up confirms root user site absent and removes PYTHONNOUSERSITE and PER_OP from launcher. Only MetaX YAML topk_softmax order changes to flagos/vendor:metax/reference. Actual blacklist selects vendor.metax, allow selects default.flagos, vendor-denied selects reference.torch. Real imports with user site enabled passed; all5878 protected source fingerprints equal except intended YAML. GDN/sampler/MoE preserved. USE_FLAGTUNE=0 retained; GPU4/5/8020/opt2/all inference argv unchanged. No model launch/gate. | container-environment-and-launcher | [env-cleanup-001.md](env-cleanup-001.md) |
| flagtree-source-install-001 | Official main fe1d24f6 source-built MetaX wheel installed as FlagTree 0.7.0+metax.gitfe1d24f6, Triton3.6.0. Only runtime distribution FlagTree changed; 5878 protected source files and launcher unchanged, zero Docker presets. GPU4 three vector dtypes exact, BF16dot bitwise matches old runtime, graph2 and stack imports/router/native sampler passed. Inherited dot error9.54e-7 retained; strict integer probe failures and all build/rollback evidence preserved. Independent306 RECORD hashes/directwheel/nativeplugin verified. No model service/full GPQA/performance/new gate; original distribution backup retained. | compiler-source-update-metax | [flagtree-source-install-001.md](flagtree-source-install-001.md) |
| flaggems-update-001 | Installed official master a456722a as5.5.0.dev0+ga456722a1 in private checkout; old tree and editable metadata retained for rollback. Original N1 direct/ATen linear regression and scoped graph2 passed. Startup004 exposed CPU RNG clone incompatibility; CPU B/A/B confirmed clone-only exclusion. Service006 full startup/11 graph captures/health200/models200 passed. Launcher only appends clone blacklist; argv unchanged. All5878 protected source files unchanged, including FGV tunedMoE/GDN/sampler/vLLM/oldGems. No new GPQA, formal gate or performance claim. | latest-gems-linear-n1-regression | [flaggems-update-001.md](flaggems-update-001.md) |
| blacklist-gap-001 | Historical gap is mainly consistent with sampling API migration losing shortlist64. Current fixed-stack B/A/B P1K/D128/C64/N64 gives920.39/933.43/911.52 outputtok/s, whitelist recovery1.91%, return drift-0.964%. Six two-rank traces cover64actualC64 Decode steps each; full-vocab radix costs7.84ms perstep perrank. Exact old/new filtering micro2seeds new-old-new gives10.58vs2.30ms, +8.28ms. All rounds/failed001 preserved;9667sources unchanged and exact originalservice restored with blacklist/no profiler. No sourcefix/newGPQA/formalperformancegate. | p1024-d1024-c64-n128 | [blacklist-gap-001.md](blacklist-gap-001.md) |
| sampler-shortlist-001 | Guarded shortlist49e9 retained inside unchanged FGV API, pureGPU guard/original fallback, MoE/GDN preserved.88 exact/RNG/graph tests + realpublicAPI + B0/C1/R/C2 targeted control passed. One original-native rollingC64/full198 independently passed158/198>=userNV77.53; new exact c2 gate. Combined current stack only, not isolated accuracy attribution or old160-reference recovery. No full performance/automatic next optimization. | p1024-d1024-c64-n128 | [sampler-shortlist-001.md](sampler-shortlist-001.md) |
| maca-runtime-defaults-001 | Private-container SDK shell discovery and linker MPI path fixed. Fresh interactive/login/explicit-override/MPI and native bench-help pass without manual exports. Docker Env null, 6560 source/launcher bytes and live user opt3 binding unchanged; no model traffic, restart or gate. Existing terminal exec bash once; direct Docker binary calls use bash -lc. | container-sdk-runtime-usability | [maca-runtime-defaults-001.md](maca-runtime-defaults-001.md) |
| user-gpqa-erqa-c64-20261028-001 | Keep gpu-memory-utilization0.9 per user,0.8 proposal rejected. Existing GPQA161 pass retained; ERQA remains incomplete210/400. Source/log/CPU storage analysis narrows candidates but does not establish a GPU memory leak or MoE tuning root cause. No new generation/source/service changes. | full-GPQA198-and-official-ERQA400-C64 | [user-gpqa-erqa-c64-20261028-001.md](user-gpqa-erqa-c64-20261028-001.md) |
| erqa-oom-probe-001 | All161 diagnostic and32 followup qualification requests passed; OOM not reproduced. Native safe snapshots confirm narrow physical headroom and fragmentation pressure, not a unique cause. Clean original0.9 service restored with observer removed and6850 source files unchanged. | ERQA-short-memory-diagnosis-C64 | [erqa-oom-probe-001.md](erqa-oom-probe-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| p1024-d1024-c64-n128 | baseline | output_throughput | 1500.2496605103297 | token/s | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_ttft_ms | 1941.0504114348441 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_ttft_ms | 3740.857904739678 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_tpot_ms | 40.68825538566619 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_tpot_ms | 42.11236411701972 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_itl_ms | 40.68825552905164 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_itl_ms | 40.25421550497413 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | mean_e2el_ms | 43565.13567097136 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| p1024-d1024-c64-n128 | baseline | p99_e2el_ms | 45333.94738264382 | ms | 单实例3轮中位数观测；波动超限且整套incomplete，不作为完整验收 |
| moe-gemm1-bf16-m64 | baseline | graph_kernel_latency_median | 0.43741440773010254 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm1-bf16-m64 | candidate | graph_kernel_latency_median | 0.32403199672698973 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm2-bf16-m64 | baseline | graph_kernel_latency_median | 0.17830400466918944 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm2-bf16-m64 | candidate | graph_kernel_latency_median | 0.16625920534133912 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm1-bf16-m8192 | baseline | graph_kernel_latency_median | 6.347071838378906 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm1-bf16-m8192 | candidate | graph_kernel_latency_median | 1.8060287475585937 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm2-bf16-m8192 | baseline | graph_kernel_latency_median | 1.1698176383972168 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| moe-gemm2-bf16-m8192 | candidate | graph_kernel_latency_median | 1.038105583190918 | ms | 独立进程合成路由/graph5x20；固定BM单阶段，不含align/sum/TP/模型E2E |
| full-moe-bf16-m64-uniform | baseline | graph_full_moe_latency_median | 0.6110079765319825 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m64-uniform | candidate | graph_full_moe_latency_median | 0.48496642112731936 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m8192-uniform | baseline | graph_full_moe_latency_median | 7.821631622314453 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m8192-uniform | candidate | graph_full_moe_latency_median | 2.984435272216797 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m64-concentrated | baseline | graph_full_moe_latency_median | 0.13521920442581176 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m64-concentrated | candidate | graph_full_moe_latency_median | 0.12592639923095703 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m8192-concentrated | baseline | graph_full_moe_latency_median | 2.3563135147094725 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |
| full-moe-bf16-m8192-concentrated | candidate | graph_full_moe_latency_median | 2.004351997375488 | ms | 完整单rank MoE graph/合成路由；不含TP/模型E2E；非正式性能验收 |

<!-- e2e:summary:end -->

完整精度结果：基线160/198（80.81%），候选147/198（74.24%），候选低13题/6.5657个百分点，未达到冻结门槛，未签发gate。按精度诊断Skill保留失败证据并进行同请求B/A/B对照，根因未定；正式性能保持阻塞。性能原基线11轮全部保留，P4K预热不稳、P1K部分延迟波动，整体incomplete。安装一致性与FGV实际内核覆盖分别记录，未宣布最终验收。详见[state.yml](state.yml)及[完整实验](../optimize/regression-001.md)。


2026-10-28 当前opt3/prefix-on原生GPQA C64/full198：**161/198=81.3131%**，严格样本396行、旧160/147/161/154重现及当前前后fresh源码/服务身份独立通过；门槛77.53%在流量前冻结。验证：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/gpqa-followup-001/independent-verification-001/verification.json`（SHA c9437b838bd089152dc01a11c3f32076e89941334e545a89b8f175606366ebb9）。随后ERQA OOM退出，仍无完整400分数；本项只精度，不代表四场景性能验收完成。详见[本次实验](../optimize/user-gpqa-erqa-c64-20261028-001.md)。

ERQA partial210 success/64HTTP500/126unsubmitted independently verified; full400 score null. Frozen incident f0d8a15a6e9a2cdb29d0f9675592b24bc2824b24e75362037e19a4517b155239. Monitor deleted at terminal failure; awaiting user recovery approval.

User rejected lowering utilization. Latest read-only report: `/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy/user-gpqa-erqa-c64-20261028-001/erqa/oom-analysis-001/analysis.json`, SHA ef9f0fe401f33f4c4f29e080fcb2161c70c223a2cc067a0c5aea844be30b29c5. This supersedes the old inactive0.8 recovery proposal; no such change was executed.

用户进一步授权保持0.9恢复原参数并短程内存取证。当前[erqa-oom-probe-001](erqa-oom-probe-001.md)接续中：外部进程级观察器、有限文本/图文请求、不跑全量或改生产源码，结束移除观察器并恢复原参数服务。


2026-10-28 短程取证与清理完成：原0.9/TP2/GPU4/5/8020/opt3/prefix-on已恢复，当前API972456/start1148499863，日志在远端本实验followup-001/restored/service.log。两轮C8恢复检查16/16通过；全6850生产源码/编译器字节一致，观察器路径和token均已移除。没有新增完整GPQA/ERQA或gate。

冻结范围64文本+96图文(doc178..273)+1快照触发请求全部161/161成功，HTTP并发峰值64、零重试；本次服务自身资格和恢复资格共32请求。早期进程观察错误的24资格请求单独保留（8中断/16恢复成功），未进入短程子集、不与本次合并评分。独立核验SHA25c95fd1768ec3edc509750f67c607495d025d1b19485a82825d6f0fd590c2f8。
已确认0.9预算与实际物理占用不一致、图文分配器压力；短程未复现OOM，唯一历史根因未隔离。详见[短程内存取证](erqa-oom-probe-001.md)。

- [当前重启服务 GPQA198 / ERQA400 C64 第二轮](user-gpqa-erqa-c64-20261028-002.md)：用户新授权；当前984020/start1148579047，16/16资格与原生预检通过，GPQA198 C64已开始，ERQA400 C64串行队列等待。每小时监控已创建，当前无新最终分数。

2026-10-28本轮第二次重启服务评测：GPQA独立159/198（80.30%，>=77.53%）通过；ERQA400 C64已串行接续，仍运行，暂无完整ERQA分数。见[user-gpqa-erqa-c64-20261028-002](user-gpqa-erqa-c64-20261028-002.md)。

- [ERQA调优器引用显存验证](erqa-tuner-retention-001.md)：已独立核验：清引用实际释放232.8MiB/卡，释放组148图通过；原引用组连接partial，不宣称完整OOM修复。普通0.9服务已恢复，监控删除。

- [ERQA C32 OOM取证](erqa-c32-oom-001.md)：冻结现场重建6请求/11图片/33,148patch，视觉GELU输出138 MiB分配失败；比旧C64失败批次patch高5.15%。0.9保持，零新请求/重启/改源；预算余量与视觉合批共同压力，OOM瞬间allocator分区仍未知。

- [ERQA显存预算修正与图像批次验证](erqa-memory-fix-001.md)：保持0.9，KV预算扣除初始non-Torch占用；原生图像拆批因数值差异未通过并已回退。预算版69短请求及35,112patch边界独立通过、零OOM，当前无取证工具服务已恢复；图像拆批未交付，无新全量评测或gate。

本次用户重启后新授权[C32 GPQA与ERQA完整评测](user-gpqa-erqa-c32-20261029-003.md)：当前仅准备，保留0.9与KV预算修正、原图像路径及MoE/GDN/采样优化；新分数未知，不复用旧gate。

新预算版C32：GPQA已真实启动、原生cache0/198/C32；ERQA依赖恢复及串行接续已安排，详见[user-gpqa-erqa-c32-20261029-003](user-gpqa-erqa-c32-20261029-003.md)。无新分数/gate，0.9和服务配置保持。

最新预算修正版C32轮次：GPQA继续生成；ERQA独立依赖恢复与CPU准备已完成，唯一串行queue等待GPQA。尚无本轮最终分数，服务0.9和6851源码身份保持。详见[user-gpqa-erqa-c32-20261029-003](user-gpqa-erqa-c32-20261029-003.md)。

预算修正版本轮GPQA C32已独立通过159/198（80.30%，阈值75%）；官方ERQA400已串行接续，尚未完整结束，观察时50完成/0失败。服务0.9及MoE/GDN/采样保持，未运行性能测试。

**预算修正版C32双项全量已独立完成**：GPQA159/198=80.30%（阈值75%，通过）；官方ERQA190/400=47.50%（无阈值），400/400请求成功、无OOM失败，1条length原样计分。保持显存利用率0.9及MoE/GDN/采样；仅物理KV预算修复保留，图像拆批不启用。不外推C64、不作为正式性能结论；监控已结束。详见[user-gpqa-erqa-c32-20261029-003](user-gpqa-erqa-c32-20261029-003.md)。

## 补充优化点与评测记录索引

以下为同目录已有记录；结论范围以各点文档和 `state.yml` 为准。

- [libtuner-context-lifetime-001](libtuner-context-lifetime-001.md)
- [user-gpqa-erqa-c32-20261029-002](user-gpqa-erqa-c32-20261029-002.md)
- [user-gpqa-erqa-c64-20261029-001](user-gpqa-erqa-c64-20261029-001.md)
