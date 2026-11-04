# 20261013-qwen36-35b-metax-e2e-current / optimize

<!-- e2e:summary:start -->

- 案例：20261013-qwen36-35b-metax-e2e-current
- 当前状态：CPU_packet_complete_waiting_user_for_bounded_numeric_GPU
- 当前候选：script19-plugin-publicMoE-gems-de2298be-isolated-cache
- 下一步：Await user decision for one new11group/13comparison numerical diagnostic on privateGPU6/defaultstream/max180s with fresh hostTP6/7 PIDs/source/env/resident/disk/APIidle/nativegate/resource checks. Do not execute current hard-disabled sources or flipoldfiles. Approval only permits newimmutable flag-enabled copies/finalbinding, no modelstop/performance/GPQA/graph or measurement001unlock.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-001-mixed-stall-localization | residual_compiler_value_specialization_causes_identified | p1024-d1024-c64-n128 | [op-001-mixed-stall-localization.md](op-001-mixed-stall-localization.md) |
| op-002-moe-stage-tile-diagnostic | pending_actual_routing_and_stable_e2e_not_deployed | p1024-d1024-c64-n128 | [op-002-moe-stage-tile-diagnostic.md](op-002-moe-stage-tile-diagnostic.md) |
| op-003-gems-sampling-prototype | private_not_deployed_M1guardfailed_numeric_packet_hard_disabled_waiting_user | p1024-d1024-c64-n128 | [op-003-gems-sampling-prototype.md](op-003-gems-sampling-prototype.md) |
| op-004-gdn-decode-call-transfer | user_loaded_current_GDN_full_precision_passed | — | [op-004-gdn-decode-call-transfer.md](op-004-gdn-decode-call-transfer.md) |
| acc-004-gdn-current-full-gate | passed | p1024-d1024-c64-n128 | [acc-004-gdn-current-full-gate.md](acc-004-gdn-current-full-gate.md) |
| op-005-attention-compile-key-normalization | deployed_precision_passed_fullP1K_incomplete_residual_SplitKV_and_MoE_compilation | p1024-d1024-c64-n128 | [op-005-attention-compile-key-normalization.md](op-005-attention-compile-key-normalization.md) |
| op-006-attention-tail-workspace-runtime | pending graph/nativeCG qualification; not deployed | p1024-d1024-c64-n128 | [op-006-attention-tail-workspace-runtime.md](op-006-attention-tail-workspace-runtime.md) |
| op-007-moe-align-runtime-bounds | pending privatevalidation; no productionstacking | p1024-d1024-c64-n128 | [op-007-moe-align-runtime-bounds.md](op-007-moe-align-runtime-bounds.md) |
| op-008-plugin-020plugin-opt-base | keep020plugin-opt at8b059; current GDN/attention/MoE changes retained | p1024-d1024-c64-n128 | [op-008-plugin-020plugin-opt-base.md](op-008-plugin-020plugin-opt-base.md) |
| op-009-moe-public-call-without-workspace | user requested simplified public call retained on disk; no reload/restart | p1024-d1024-c64-n128 | [op-009-moe-public-call-without-workspace.md](op-009-moe-public-call-without-workspace.md) |
| op-010-metax-branch-with-moe-public-call | user-specified version retained on disk; only two MoE tracked deviations; other 3repos/source/launch untouched | p1024-d1024-c64-n128 | [op-010-metax-branch-with-moe-public-call.md](op-010-metax-branch-with-moe-public-call.md) |
| op-011-moe-library-owned-dispatch | Latest user correction supersedes old v2 generic else/topk cleanup; no callerworkspace, no restart | p1024-d1024-c64-n128 | [op-011-moe-library-owned-dispatch.md](op-011-moe-library-owned-dispatch.md) |
| op-012-flaggems-vllm-version-refresh | current_combination_loaded_graph_and_full_precision_passed | — | [op-012-flaggems-vllm-version-refresh.md](op-012-flaggems-vllm-version-refresh.md) |
| op-013-script-scope-baseline | baseline retainedforcurrentscope; capturesteadyphasehotspots, no P4K/formalABR closure | p1024-d1024-c64-n128 | [op-013-script-scope-baseline.md](op-013-script-scope-baseline.md) |
| acc-006-script-scope-full-gate | retain cache-isolated current combination; performance may resume; not independent attribution to eachsourcepatch | — | [acc-006-script-scope-full-gate.md](acc-006-script-scope-full-gate.md) |
| op-014-moe-decode-paired-gemm1 | reject; production never changed, no graph/GPQA deployment promotion | p1024-d1024-c64-n128 | [op-014-moe-decode-paired-gemm1.md](op-014-moe-decode-paired-gemm1.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

当前无可声明的累计端到端收益，也没有已接受的服务源码改动。anchor完整GPQA65536为164/198=82.8283%，198唯一题/全部filter/配置/来源和四repo12249文件/模型/镜像挂载连续性通过，原生gate issue/check成功。旧30000 149/198失败完整保留，不把全部15题净增加都归因预算。

review-003：阶段基线与同步暂停重建后继续定位集中停顿。所有轮次保留；各场景的初始填充与持续解码成本尚未分成纯设备时间。

| 诊断阶段/workload | 三轮duration (s) | 吞吐 (tok/s) | 预热spread | 结论 |
|---|---|---|---:|---|
| Mixed P1K/D128/C64/N128 | 20.12/29.99/20.36 | output814.28/546.28/804.72 | 33.30% | incomplete，0measured |
| Prefill P1K/D1/C64/N128 | 7.95/7.10/7.11 | total16511.46/18466.30/18462.34 | 10.59% | incomplete，0measured |
| Decode P1K/D512/C64/N64 | 30.47/56.68/52.26 | output1075.42/578.12/627.01 | 79.31% | incomplete，0measured |

三阶段workload不同，各有自己的冻结基线；不相互计算加速比。Mixed慢轮有42/56请求同步4.6s间隔；Decode慢轮在初始fill有最长9.38s间隔，后段有57请求共同4.58s暂停；medianITL仍约52.5ms。原生日志未显示对应queue/OOM错误，私有Stream故障与此波动的关联仍未证明。

优先级：op001在现服务做有界prof-002 capture→analyze，覆盖initial Prefill/Mixed和early Decode、TP0/1各24iteration、两次capture；无服务中断/源码修改/FG关闭。其次整理私有op003测试oracle、API兼容和标准benchmark；其20numeric通过，但graph与post-fix性能不通过，资源隔离仍待明确服务中断授权。MoE tile局部收益需真实routing和稳定Mixed验证，未部署。

采样候选仍属高风险，实际部署需新198题/65536/80%正式精度gate。所有正式P1K→P4K→P16K→P32K、D1024/C64/N128及同配置baseline/candidate/revert未完成，最终验收incomplete。

独占graph的10–15分钟停服务方案已准备但未授权/执行。自动审批拒绝了未来服务中断扩展，后台仅执行不停止服务的工作；保持attention、FG完整白名单和MoE buffer复用。

prof-002已结束：两轮TP0/1共4新trace SHA及phase验证通过，各24step=1Prefill/8Mixed/15Decode、15graph launch，设备窗口4.66–4.72s没有重现原4–9s停顿。profile-stop/export造成约28.5s客户端暂停，只属profiling扰动。终态服务/source12249文件/模型/env未变，profiler OFF、API无请求。后续改变观测窗口或做完整时间线低开销主机/driver观测，不重复首24step、不归咎MoE、不报收益。


2026-10-14当前恢复事实：一次已授权中断285.98s后原服务恢复，当前namespacePID905636/birth489464369，source/args/env/FG白名单与workspace复用均保持；C1/C8 health、两rank各64graph launch通过。原正式164/198=82.83%已原生rebind/check新实例（evaluation_reused=true），不是新分数。gate accuracy/restored-anchor-accuracy-gate-20261014.json SHA161d7ffa...；旧gate仅是历史实例证据。私有采样20数值+8graph replay通过，资源条件为本服务停止时GPU6，尚无post-fix standardbenchmark或E2E，也未部署。后续CPU工程兼容及完整时间线观测按review-004，不重放已执行停止/评测脚本。

review013：003捕获实际attention fatbin编译停顿、154冗余TTIR cachekeys。003 warmup spread18.24%失败/0measured，非稳定性能结果。下一步[op-005-attention-compile-key-normalization](op-005-attention-compile-key-normalization.md)已冻结私有改动设计；生产GDN/fullGems与82.8283% gate不变。

op005批准窗口已结束：8graph×2通过，nativeCGbenchmark300s超时、未部署；原GDN服务恢复API975866，完整Gems/12252源文件不变。私有修复保留，性能资格和E2E收益仍incomplete。当前precision binding待新实例证据，旧分数仅历史；不得重放批准或重启窗口。

review014：动态形状硬件实验原6/candidate1专化，预热后5次新增编译→0，输出/LSE相同；Event24组min0.9922x/median1.0081x。仅证明私有编译复用和此微测设备耗时，不能代替模型E2E。原生CG窗口1超时、原operator慢行保留，生产source没有改动。当前API975866健康，旧164/198 gate为历史实例、新绑定pending。window2单进程方案已准备，需新的明确服务中断授权；全部正式场景/验收incomplete。

review015当前：CG24完整护栏通过，单文件已条件加载，API982315；新源GPQA UUIDbcbef8f8ac274343b48751537e080c5c运行，全198/65536/80门槛不变。窗口已结束339.013524s，授权不扩展为未来停服。旧负面/超时保留；没有E2E收益结论，P1K待新gate。

review016当前：op005 full198strict170/198=85.8586%、timeout0，nativegate2d5064ce...issue/check成功并绑定API982315当前源；下一步同配置P1K，仍无模型E2E收益。旧GPQA/terminalcreator均完成不可重放。

review018：004固定3warm首轮编译失败保留。005新4warm/windowlast3<=5%后3测量801.67/805.57/809.92tok/s，波动1.02%、compiler0、ITL>1s0、主cache无新增，observer admitted；只属D128局部稳态。完整P1K006(P1024/D1024/C64/N128)正在原服务执行，CPU收尾器已绑定，不重复启动或执行终态creator。没有因果ABR加速/正式四场景验收结论。

review019当前：完整P1K006的三测量1133.4/991.2/1146.2tok/s，波动13.68%>10%而incomplete；第二测量轮有自有TP attention/MoE编译和13请求共同8.90s停顿。源/gate保持、APIidle、FG全启用，停止重复测量及预热加码，先按op005文档核残余SplitKV参数与MoE输出界限专化。D128稳定不推广为完整场景通过；仍无ABR收益或最终验收结论。

review020：预热后编译的值专化原因已确认。SplitKV边界TAIL_ROWS=B*8/B*128随B13/21变化，相同分支的IR只差地址步长常量；MoE stage1 LLVM只差48968/766与51064/798两个mask界限。优先计划op006/007私有运行时标量方案，tile/Q_TILES/NUM_SPLITS保留。无新源码部署或GPU结果，旧006失败与当前精度gate不改判。

review021：op006私有主TN仅TAIL_ROWS参数分类调整，8原生测试/22输出与LSE对照通过；受控prefix/tail跨6种B的主key12→2，B13预热后B21候选无新增主key。生产gdn+op005源码/实例/FG和170/198gate不变，所有私有进程退出。graph/nativeCG与模型E2E未跑，不能把key数量当收益；下一步准备确切graph/benchmark/恢复资格方案，旧窗口不能重用。op007仍planned，正式006失败不改判。

用户指定Plugin020分支已对齐：目标与原HEAD均8b059122，容器原detached切到020plugin-opt，517源码文件与index/dirty完整保留；原服务/GDN/attention/MoE/精度gate保持，无代码替换或重启。见op008回执。

用户最新明确要求移除MoE workspace复用：op009仅当前Plugin apply块及CPU测试两文件已改，28CPU合同通过，其他515文件/GDN/attention/其他三repo原样，服务未重启。旧运行实例/170/198 source与新磁盘297da499严格区分，新源性能/精度待验证，不执行旧source完整校验后误判漂移或重写旧hash。

用户最新op010已完成：容器真正切入020plugin-opt-metax/f99的tracked基线，仅两处MoE补丁（去callerworkspace、公共API+copy）偏离分支；其他分支源码一致，额外本地测试保留。49CPU回归通过、原服务及其余3repo未改，新source graph/精度/性能未验证，旧gate不能复用。

最新op011按用户要求去掉MoE新增MetaX判断和私有backend导入，所有包装统一公共flaggems_vllm；fused_experts直接import/copy、无callerworkspace。原77矩阵只修正缺import的准确异常预期后全通过，首轮74/3保留。仅两生产+两CPU测试变更，服务/其他3repo不动，新source硬件graph/精度/性能未验证。

当前op011-v3：按用户收窄范围，topk恢复目标分支原5参/4参兼容及renormalize，仅更换公共导入库；fused_experts快路径只对NV/MetaX放开，其他平台保留原分步或原独立路径。77CPU回归通过，仅两生产+两测试变动，其他算子/Gems/vLLM/模型/原服务保持；无callerworkspace复用。源已保存，未重启/热重载，设备graph/新fullGPQA/E2E待验证；automation维持PAUSED。见[op011完整记录](op-011-moe-library-owned-dispatch.md)。

用户授权发布已完成：当前两处MoE源码及两份测试已推送至020plugin-opt-metax，[提交b8f2734](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/b8f2734beb80738ce5e4f7c61c2056f41e5c9ba5)。远端SHA已核，提交字节与容器源一致；服务/容器Git索引及其他代码未改，无重启。77CPU回归已通过，新source设备graph/fullGPQA/E2E未执行，automation保持PAUSED。

FlagGems-vllm version update completed: official main05d0ff05->de2298be, editable0.3.0.dev1, existing GDN/attention/MoE local changes preserved. Syntax/API/nativeCPU34 passed, otherdependencies/Plugin/model/service unchanged, no restart. New graph/fullGPQA/E2E not_run; automationPAUSED. Seeop012 record.

Review022: resumed on user currentstartscript19ops scope. CPU13 passed, registryattentionvendor.metax/GDNflagos/directMoE proven in fresh process. New baseline/source differs from old20ops service; old170/198 andP1K006 not reusable. Current8010oldprocess unchanged, new fullGPQA and nativeP1K pending controlledreload. Seeop013/acc006; op006 attention specialization deferred outsidecurrentdispatchscope.

Latest script-scope resume: approved restart completed, newAPI1008868; exact19scope, TP0/1 each22actualgraphlaunch, C1/C8 all9pass, profilerOFF. New full198/65536/.8 GPQA started13:44UTC, uniquecontroller1347505; no P1K untilnew nativegate. See op013/acc006 and currentstate; earlier no-restart/pause/oldgate text is historical.

13:47UTC precision terminal FAILED: UUID93378df7056a4feda30b619dec00112a strict0/198, flexible2/198. Bothfilters198 unique doc each (396rows); native resultSHA5600429275d8b34a6b47480577016fb65050044aaae56d948c1f4b47214e2422, samplesSHAf81e448b09ff1011b5334f48332b4ccaadf3c6ec92967af8e4918c4fa0c6feb8. Terminalvalidator executed once:12355source/model/env/instance/mount/config continuity passed then deliberately refusedbelow.8; no run-record/passinggate. P1K/performance stopped beforestart, no source optimization stacked. Accuracydiagnosis Skill invoked; root cause notconfirmed. New/oldMetaX MoE backendSHA75f34372... identical, Plugin call/import and otherpaths stillneed isolation. ServiceAPI1008868 remainsrunning/idle, no extra interruption.

Read-only utility initially parsedJSONL withstr.splitlines and broke Unicode separators, then usedliteral newline to verifycomplete396rows. This wasutilityfailure, notinvalidmodel dataset and notscorefix. Prior tinyhealth/graph qualifiedexecution only; no claim of semantic pass. Rawrequests/answers remainremote; currentfailure notrewritten/retried.

14:38UTC authorized cache-isolation lifecycle running: host1426324/birth501432585; candidateAPI1025146/birth501435120, C1/C8health passed, native graph/KVrole check in progress. Sole envdelta VLLM_CACHE_ROOT under current case, no source/19scope/cache deletion. Plan2ca14820..., lifecyclee27deeed..., monitor57dc52b4.... First0/198 remains failed; review023 ranks existing lifecycle then newfullGPQA ifqualified, P1K blocked. PrivateMoE4shape exact does not exclude graph/model. Actual vendorcacheblock32 corrects earlier1056 guess; unsupported1056 probe retained, not rootcause. OldFXartifact/cachebinding suspected, not confirmed.

14:42UTC cache-isolation window completed346.56s (14:32:48→14:38:34), one authorization consumed, no future restart permission. CurrentAPI1025146/birth501435120; GPU6host1428564/ns1025947 andGPU7host1428565/ns1025948 bothbirth501445784. Source12355/argv/19scope/model/image/mount unchanged, soleenvdeltaVLLM_CACHE_ROOT. Two ranks each22actualmcGraphLaunch and20cachewritecalls show K/Vboth[tokens,1,256], oldtraceVheads8 mismatch removed. C1/C8ninepassed, profilerOFF. Newservice52590ffc33cfb35e0877546c4b2611ac7bbea76f8b557955d9fba0cb8469bef4, runtime3ea0ea0895f3459d2b6921f2c7c08713b0c70dc73e07e00dd013851aac13e828, undermanifests/acc006-isolated-cache-{service,runtime}-20261015.json.

Oldcompileartifact24bc62e8... unchanged. NewrankFX d12605b2.../710ddf40... and correctKVshape are single-variable counterfactual evidence supporting stalecache input-binding hypothesis; formal semantic resolution notyetclaimed. CPUevidence accuracy/acc006-cache-counterfactual-evidence-20261015.json SHAc67dd01740541a644013e912b8d99760136cc6ef1d53c645bfef43f82ca16e33; creator55fb02e9... completed.

NewformalGPQA UUIDd7e72aff3e6a4a7c8809d3ae7113be32, hostcontroller1446999/birth501481765 started14:40:59UTC, eval_modelqwen36-35b-script19-isolated-cache-full-graph-c32-g64k; original198/65536/temp1/.95/k20/seed42/C32/strict>=.8 unchanged. Source/env-bound newservice; provenance2equal/preflight0. Config269a8003fea443f07bafea501f528f63567905c73d095a16a99c405fd62785c6, contract219a5d447c52e0ab459740ac562e8495fd32e0e95994da760981d059f8b33e5a. Launch3941ca83... executedonce. Monitor10573a53539cd44e93727a158f6f1e7ed869a00758e76c02032fcd91ca620894 saved; terminalvalidatora447e4f70a25e85ba9408384fe518f1da9c260d15366aeb1ce2d9ee678d589b0 savednotexecuted. 14:42snapshot0complete/0timeout/32active; notformal score. P1K blocked until native terminalgate, no concurrentGPUprobe/profile/benchmark/sourcechange. Firststrict0/198 remainsfrozen; no oldgate rebind. Heartbeat updated ACTIVE30min/quietunchanged for thisUUID.

15:50UTC：同GPQA UUID d7e72aff3e6a4a7c8809d3ae7113be32 已194/198、0timeout、4active/0waiting，无原生results/run-record/gate。中途不判定通过。

CPU-only自动收尾器已于15:48:20启动：host1507105/birth501885876，commands/wait-validate-acc006-isolated-cache-g64k-20261015.py SHA5ced19d97e59b2c69fbd35b3c4c70a700e56166e1b049c43c7fbffd48fe72217；launcherafa27a76b9f86c8273e2f5676a94ccb43264440a0f9fa4a11e17fc1d6d59b0d2已执行，严禁重放。它只等唯一正式controller退出后执行原terminalvalidator一次，无生成/性能/重启。状态accuracy/acc006-isolated-cache-g64k-postprocess-status-20261015.json当前waiting_exact_formal_controller。下次先读收尾状态/精确进程/已有outputs；waiting或validating时不可手动重复，任何terminal/gate已创建后不可重放原validator。若工具失败先核边界、新唯一安全续接，不能重复GPQA或掩盖分数。只读汇总monitor c1a66696b1161baa0ee91b0fcfd11a568d59c6d275149bf8eadd661d6a55c407已保存并执行。

P1K CPU准备仅在本地TEMP：inspect-op013-p1k-inputs-20261015.py SHA3ab6f3d3abc5890d36e05106e7e960e48f56d841c8fe52aad6c755a4972a7fcd；prepare-op013-p1k-full-001-20261015.py SHA0f155a7db5d2b37bbf5cbf791b1aa5a1055b8cfa2642ceded08252578fcf6e87。均仅AST/旧模板适配，未上传/执行/测量；必须新gate通过后fresh当前实例/source/env/model/mount/APIidle/GPU6/7/nativeclient/source-bound observer target并预览，不能拿这些草案当运行结果。后续modebaseline/rolebaseline/newrun-id op013-p1k-full-001，P1024/D1024/C64/N128；4warm末3<=5%、3measured<=10%、600sround/allrounds不变。当前19scope、源码、服务、旧cache均无改动，无P1K请求。HeartbeatACTIVE。

2026-10-15 16:23UTC最新：隔离缓存后的正式GPQA已完成，UUID d7e72aff3e6a4a7c8809d3ae7113be32 strict164/198=82.8283%>=80，0timeout；全198/65536/temp1/top_p.95/top_k20/seed42/C32不变，全部filter/原生来源/config/12355源码/当前service/env/model/tokenizer/镜像挂载连续性通过。CPU收尾15:56:07完成，nativeissue/check成功：gate accuracy/acc006-isolated-cache-g64k-accuracy-gate-20261015.json SHA9fdcc14eec68a6203a3c46cbf7e45c46fdcea5474ba4def838119fedaf98a642；terminalcontinuity06b0a111d267331fd8525ed33c6be9b66add1385f36273844fd7c725683b8fb7，terminalvalidation4f6834150a253a745c977c3254a54fd3ba48a6ee734669d5f8e3d30c9e6940d8。未重复GPQA或issue/validator。当前API1025146及GPU6/7workers保持，旧cache/source未动，原19FG范围不变。

缓存隔离执行边界得到反事实支持：相同源码/参数，旧cache启动Vheads8且0/198，新增VLLM_CACHE_ROOT后K/V均1head、两TP各22actualgraphreplay、C1/C8和新full164/198通过；可恢复性能工作，内部缓存key/二进制失效机制仍不作过度确定归因。原始0/198、C1无关输出及私有负面/utility失败全部保留，不改判为通过。该分数只绑定当前组合/环境，不能归因单个Plugin/MoE/library改动或冒充NV验证。原用户启动脚本尚未写入cacheRoot；下次reload须保持隔离策略，不授权未来停服。

P1K新scene-entry基线已16:21:45启动：run-idop013-p1k-full-001，modebaseline/rolebaseline，controller1531875/birth502086404，nativeclientns1032848/birth502086510。完整P1024/D1024/C64/N128/temp1/ignoreEOS/seed42/range0，4warm末3spread<=5%/3measuredspread<=10%/600sround/全轮保留/无profiler。当前仅新scope单实例基线，不能与旧20scope不稳轮算精确gain。新planSHAf0a5bac2...、comparison8bbbadbd...、v2identityb5be1a8c...、observer1dfbb147...、v2launch36841b6f...。Freshsource/gate/APIidle/资源/镜像挂载/timeNS/cgroup通过。首版dryrun因baseline不能传--accuracy-gate而拒绝，0benchmarkrequests/无run目录，原文件日志保留；v2仅修原生接口，外部nativecheck+gateSHA仍冻结在identity/launch，七轮dryrun通过，不放宽测量/精度标准。真实测量尚无结果。

CPU收尾器1533067/birth502096784已16:23:29启动，commands/wait-finalize-op013-p1k-full-001-20261015.py SHAde78eacd2efda4335ae607c3812398f241dca454fc922a37ada40ac5b149d4d3；launcher11b45361...已执行，不可重放。只等现有native退出后finishd14dd85a...与analyzef929f151...，不产生新GPU工作。监控monitor-op013-p1k-full-001-20261015.py SHA3ffd90624dde2d41c84fb96fbe3a88ef0cafdb9b1a5d4775e8ec20e8f5c911d4。终态核native全部轮+稳定性+observer开销+source/gate连续性+compiler/共同停顿时间线；未达稳态/incomplete保留，不丢慢轮/自动加warm。review024首优先本轮baseline，其后按实际当前owner/routing/compiler证据重排；不能切P4K/最终acceptance通过。所有旧creator均不重放，heartbeat继续ACTIVE。

16:26:56UTC同P1K controller1531875仍运行、64active；首轮warm原生valid，116.005s/output1129.879tok/s、meanTTFT2080.8ms、medianITL52.873ms、maxITL.637s、ITL>1s为0。仅捕获两TP各一次mxcc --version，均不是--fatbin编译事务；不把compiler_executable计数2当作新kernel编译。尚无正式measurement/稳态或预热后结论，不算收益。CPU收尾既有1533067继续等待，源码/服务/白名单不变。

2026-10-15 16:47UTC P1K终态已核：op013-p1k-full-001 全7轮原生有效，各128成功/0失败，input/output各131072；末3warmspread0.843836%<=5%，3measured输出1132.9415/1132.7759/1133.0204tok/s，median1132.9415，spread0.021576%<=10%。3measured meanTTFT1923.3/1987.4/1855.0ms、meanTPOT54.593/54.545/54.665ms、medianITL52.935/52.803/52.880ms、maxITL.489/.509/.504s；均客户端proxy而非puredevice。全部7轮无ITL>1s/共同停顿、0root--fatbin编译事务；两TP仅warm1各mxcc--version，不当kernelcompile。Observer .011729core/p99sample12.442ms/5859samples missed0/fatalnull准入。Source12355/实例/env/模型/挂载/gate继续通过，APIidle，native和CPU收尾均退出。Nativecheck_run通过且project稳定通过，但仅新scope单实例sceneentrybaseline，无匹配anchor/candidate/revert，不能计算旧20scope精确收益或关闭P1K/最终验收。

证据：runrecord results/performance/op013-p1k-full-001/run-record.json SHA335474b47664a87497bed051134e47ccca4cc5bf660e5310b669a659387d4e73；terminalc5821fb18832a5bd2d472fe018ac3589034b79eee68715ca66c8ffa676c89bad；analysis23b0c1ffe48887b8901e836d4b99e48fb404556680a8eb5d16bed12c32a50875；postcontinuitya1691d4dfc78d41b946b95aa0ebed6098a0c2780fe46c5895228878e58951269。无编译/停顿结论仅限本workload、7轮、主线程5Hz/后代发现1Hz，不能排除亚秒进程或未测shape。

review025重排：先当前source稳态phase profiling确认compute/host/comm热点，再从真实dispatch/shape选择单变量算子或Plugin优化；旧samplerM1负面、旧MoErandomtile和当前范围未选FGattention延后。新profile_idprof-003-script19-steady-p1k已16:57:12启动：host1542915/birth502299063，commands/run-prof003-script19-steady-20261015.py SHA4f45257ce658ea0947e83b04c3ed17527b8af64cfcaee4889008c00d9305e2f9，launcherd1ec345f...已执行不可重放。Plan04fc6d9d...，P1024/D1024/C64/N128两轮firstwarm/lastprofile、600sround/temp1/seed42/ignoreEOS，沿用现有24step native profiler，无重启/源修改/关闭FG。旧4trace库存48be84c0...保持，actualnative source dfeb9bf4...证明初始单请求probe早于start_profile，抓主批次。按实际new/cached marker、query/cache shape、graph验证phase；cached可能仍chunkedprefill，不盲判pureDecode。当前仅capture，phase/rank/热点结论待生成；profiler耗时/导出暂停不算性能收益。monitor29008f0b5b4285eec82265400be0d6d918e589f3c26262470d18669437bbcdf7，唯一status results/prof003-script19-status-20261015.json。现有完整19FG/无callerworkspace/服务及精度gate9fdcc14e...保持；不并发其他GPU实验。

- [op-014 Decode MoE GEMM1 pair](op-014-moe-decode-paired-gemm1.md): planned private single-variable test from current prof003 C64 evidence; no source deployment or claimed gain.

2026-10-16 review026: prof003 native client actually completed17:02:54UTC, 2 valid rounds each128success/0failed/input-output131072. Original controller wrongly demanded `Profiler started/stopped`; pinned native prints `Starting/Stopping profiler...`. Original failedstatus kept. No recapture or modeltraffic: new CPU existing-evidence validation bc88870e… / result1c5af5de… verifies current sameinstance/source12355/fullenv/weights/tokenizer and APIidle, old4traces unchanged, bothnewSHA traces with15 actualgraphlaunch/rank/KVheads1. Native stop and cleanupHTTP200 are OFF evidence; old continuity `profiler_off=true` is a hardcoded historical field, not an independent liveprobe.

CPU analysis final `results/prof003-phase-analysis-final-20261016.json` SHA49b505686d809552c7291787495f4cf8e229cf5787c83e4111ea28c1e67f6ac3: perrank 1M1024prefill/1C1decode/8batch-fillingMixed/14C64decode. CPU/GPU External IDs match; C64 tokeninput[64,1], onegraph/step,30packedrecurrentGDN and nochunk. Generic old provisional boilerplate remains in rawfinal limit field; concrete assertions/phase_boundary_proof supersede it. Prefill and fillingMixed coverage is early24steps only, not representative fullrun shares.

C64 MoE kernelactivity164.791/164.035ms totals,43.22%/44.21% of captured kernelactivity. GEMM1median180.695/179.778us (560calls/rank), GEMM2 100.920/100.594us. MixedMoE34.96%/34.41%, withGDN/comm/dense next. Kernelactivity/CPU nestedtime are notcriticalpath or E2Egain. LongCPUmcMemcpyAsync(~44ms) sampled actual2.1MB H2D46–48us containswait, so reject purecopy-bandwidth attribution.

Next [op014](op-014-moe-decode-paired-gemm1.md) private exact-M64 BF16 paired GEMM1 only; numerical/nativebenchmark/graph>=2 gates beforedeployment, preservepublicMoE/no callerworkspace/all19FG. Preparationutilityerrors preserved, noGPUresultyet; production unchanged. Current fullP1K baseline1132.9415tok/s stable and GPQA164/198 remain; no matchedA/B/Rgain or P1Kclosure.

## 2026-10-16 review027 — rejected, production unchanged

Native benchmark v2 completed: kernel/operator each3pytest passed,21 valid rows each, all42 rows retained. V1 CLI failure was0tests/0timing (`--metrics` is append notnargs), preserved, not performance failure reclassification. V2 used exact same data/matrix/timing gates plus collect-only3tests; no benchmark logic copied. Native column “Torch” is currentFG reference and “Gems” privateFG, not torch-vs-Gems.

| Full MoE routing M64 | Kernel current/private median ms | Median current/private speedup | Operator speedup |
| --- | --- | --- | --- |
| uniform | .504832 / .606208 | .832770× | .843555× |
| balanced | .585984 / .670976 | .872998× | .888153× |
| hot8 | .276864 / .275328 | 1.005579× | 1.004297× |

Primary nine target-row median .872998× misses >=1.05; every-row >=.95 guard also fails. M1 operator sentinel one .946505× row is retained; medians near1 do not erase it. Candidate rejected/not deployed. No graph or new GPQA needed for rejected candidate. Current source12355/env/model/precise service continue unchanged and APIidle. Private source and failed/successful utility artifacts preserved, no installed rollback necessary because production never changed. Resource/spill explanation remains hypothesis: CPU cached-artifact filter returned0matching records, no proof of register/spill cost. Do not assert driver/LLVM root cause or run another GPUtest solelytojustify rejection.

Evidence relative ROOT: native kernel8d4add1d5b797f9bf44417ce4e79e8578bcfa0bcfccf96e8adba4bdb6df7ae8c/operator73a055baebdb274f776af2f03cd03f948a6ab99e14c50d645f495b5205994474; XML760c487b…/49f2adc6…; results/op014-native-benchmark-supervisor-v2-20261016.json SHA4f6410fc525453b745e9e9d19199b7bfd92cc7d1ff9159236b9b4565e6bc8172; results/op014-native-v2-analysis-20261016.json SHA4cb7d6b9afa25155abcb110fc72f0269d17b8c1bb5946aeb3e704af62ea54a76. Numericale69651ea… remains minimalonly, notmodelprecision.


2026-10-16 review027 current-source follow-up: prof003 postforward CPU/GPU Externalid proves aten::scatter_ FP32[64,248320],24capturedcalls192.203/190.949ms totals; slowcalls~10ms. Current Plugin vendor/metax/patches/topk_topp_sampler.py SHA347cd1353bdd485a75b089db6148ec9c15caf0f7bfde758b43a371e0e4179af7 unconditionally redirects apply_top_k_top_p to PyTorch implementation because historical Triton failure. This fresh result reconfirms historicalop003 mechanism under newsource/script19/cache; no new sampler implementation or GPU sampling test has run. Artifact results/prof003-postforward-sampling-20261016.json SHA709a546cff14a279055ed6fc2b39fe0980ccccbed4baa78d37136973ea838619; CPU incremental dependency audit results/op003-current-scope-transfer-audit-20261016.json SHA0e7a7b44a2266c99af000666977cf5ed55fc18b3b0cf9a4f5b73c454463a0dd6. Current service API1025146/TP6,7 exactbirth and APIidle reconfirmed, no sourcechange.

Highest next priority is existing op003 current-scope variant, not a duplicate optimization ID: migrate only necessary MetaX top_k_top_p backend + small existing-boundary adapter into private current baseline; legacy backend6d07cbc64ec94aa66b938590f1dd5605ba378bd9e06fee665a7423f5ddccfad3 read-only reference. NEVER switch whole old private package/PYTHONPATH and lose GDN/attention/userMoE changes. Exact M64 FP32/V248320 metadata gate keeps old slowM1 originalcurrentfallback, withM1 sentinel and historicalnegative preserved. No library production edits or whitelistscope changes. First freeze current generationk/p and true reference/finite-value/tie/CDF/alias contract; old182/132/graph andpartialBF16fastrows do not qualify newsource. Then fresh current17ATen-FG reference numerics, fullnativebench acrossall declaredtarget/fallback rows, >=2graph, newfull198/.8 and sameP1KMixedA/B/R before retention. No automatic newStream under modelresident pressure or any future service interruption from old authorization.

2026-10-16 op003 当前源 M64 私有增量：80组有限域/fallback/CDF逐bit一致，5metadata拒绝通过；M1沿现路径，当前GDN/MoE包保持。原生v1标签接口失败无timing保留，v2仅dict标签修正已dispatch（预冻60行），待终态。生产未变，无新graph/模型精度/E2E通过。详见[同op003记录](op-003-gems-sampling-prototype.md)。

2026-10-16 review028：op003当前私有M64数值80组精确通过；native v1标签接口失败0timing保留、v2修正后在模型连续性预检停止，未生成有效性能行。Host/容器的 `/public-flash/models/Qwen3.6-35B-A3B` 同时缺失，原API/TP实例仍在且APIidle；NFS挂载仍在。历史164/198不改判，但当前artifact绑定阻塞；等待用户恢复/确认真实路径，暂停新GPU及自动续跑。服务19FG/无callerworkspace/生产源码未变。当前累计E2E收益未知，详见同op003与optimize/state.yml review028。

2026-10-16 review029：用户已原路径下载完成；35文件/26shards齐，配置/tokenizer/index SHA与size相同，mtime变更，原tensor内容SHA无记录，不能宣布新下载等价或已加载。服务/四进程/12355source/env保持，未重启/加载。新resident双绑定明确区分原已加载模型与磁盘恢复，仅资格当前实例，禁止future rebind。新完整GPQA acc007已于北京时间10:48:51启动，UUID198b58e3e9a3457094744f9c7f9f1f80、198/65536/temp1/.95/k20/seed42/C32/.8；初始0/198/32active，无gate，不并发性能。后台30minACTIVE安静监控。历史164与P1K数据不改，op003 private80numericpass但60行native续接等待新gate；生产未部署、无E2E收益。详见op013与state review029/acc007。

2026-10-16T02:52:46UTC（北京时间10:52）同acc007 UUID198b58e3e9a3457094744f9c7f9f1f80已21/198、0timeout、32active/0waiting，无native结果/回执/gate；不是正式分数。CPU收尾1880246精确实例alive/waiting_exact_formal_controller，禁止重复terminal。后台ACTIVE/30min已核，保持安静；无source部署/服务中断/newdownload加载。

2026-10-16北京时间11:12，同acc007仅64/198完成、0timeout、32active/0waiting，controller与CPU收尾精确实例活/waiting，无正式分数/gate。用户要求达标后继续M64收益/M1退化复测、完整FG保持。新native-v3续接/monitor/analysis仅上传，不执行；必须真gate+GPQA/收尾退出+fresh双绑定与gatecheck后一次启动，仍完整60行契约。详见同op003/state native_v3_prepared。

2026-10-16T03:21:28UTC只读核验：同acc007 UUID198b58e3e9a3457094744f9c7f9f1f80完成87/198、0timeout、32active/0waiting；唯一GPQA和CPU收尾精确进程均alive，收尾waiting_exact_formal_controller，无native结果/run-record/正式gate。未启动native-v3/新GPU/部署/服务操作，保持19项FlagGems及原采样契约；达标后按既有条件续接。

2026-10-16T03:26:43UTC（北京时间11:26）按用户查询只读检查：同acc007已98/198、0timeout、32active/0waiting，GPQA1870666及CPU收尾1880246精确实例仍活，收尾waiting；无原生结果/run-record/正式gate。M64/M1完整60行native-v3仍未执行，待正式>=80%及证据有效后续接，全部19项FlagGems保持，无生产源码/服务变更。

2026-10-16T03:51:13UTC只读监控：同acc007已176/198、0timeout、22active/0waiting，GPQA与CPU收尾精确实例alive/waiting；尚无原生results/run-record/正式gate，中途分数不作为结论。native-v3仍未启动，未重复GPQA/validator/numeric或增加GPU流量；保持19项FG/无callerworkspace/原服务与源码，正式终态达标且核验后续接M64/M1完整矩阵。

2026-10-16北京时间12:21确认acc007完整198题已于12:10完成：strict159/198=80.3030303%>=80、0timeout，真实原生issue/check通过；gate SHA6417ba2d5e82eb193b00c0e06377f86984e4f8afeac6a75327bdebeee8363b1f、terminalvalidation4214b14b81fd8dfef6caf241c8917726f586132e9c6bd884d4308eb3426811b6、continuity7afcd37fa9d6c6484fe9ae7795105669070008496b7808c93f89dd290785a5fe。GPQA/CPU收尾均退出，API0/0；仅资格原resident模型，非重新下载权重或私有候选。已确认native-v3所有启动边界为空，核SHA执行已保存launcher一次；只跟随现有进程，不重放。完整60行M64/M1微基准全FG保持，无生产修改/部署/重启，未提前宣称收益。

review030：acc007完整159/198＝80.3030%通过且0timeout，gate6417ba2d...绑定当前resident，不资格下载模型重载/私有候选。采样native-v3完整60行/6pytest通过，M64通用FP32 kernel/operator中位1.178364/1.171052x；BF16可精确表示输入4.502462/4.483891x仅特殊输入域。M1 kernel中位.968558x，seed43最差.946124x<冻结.95护栏；operator中位1.032765x。故暂不晋级/部署，不隐藏负面或重测挑快行。CPU审计M1走同当前FG参考，仅额外metadata/fallback包装；因果未证，下一步私有快速拒绝设计+新variant数值/完整同60行守护，不重放v3。完整数据/证据/三阶段限制见[op003](op-003-gems-sampling-prototype.md)和同state review030。生产source/服务/19FG无改，无模型E2E收益证明/未来停服许可。

review031：earlygate仅将supports的shape拒绝提前，36CPU/20真实数值+5metadata+2identity通过；native-v4完整60行/6pytest，M64通用FP32 kernel/operator1.17438/1.16736x，M1kernel min.943153<.95仍失败（median.989146），operator min.979857通过。暂拒绝该私有变体，不改判旧v3或部署。CPU确认Event逐次clearcache与wall批量重复的计时差别，根因仍未证。下一步A/A原FG同callable负控制草案仅本地，完整60行/原预算及预冻[.95,1/.95]；先审查native上下文、fresh门禁/源/资源/idle后新唯一执行。当前无GPU客户端，所有creator/测试不可重放，19FG/服务/源码未变，无E2E收益。[同op003](op-003-gems-sampling-prototype.md)与state review031为准。

review032：原FG同函数A/A001完整60行/6pytest完成，M1 Event ratio .666137..1.071585、wall1.018707..1.065756均越预冻区间；M64通用FP32控制约1.0，其他54行均在区间。证实M1成对计时不够稳定，不能唯一归因旧6%差异；v3/v4原护栏失败保持，候选未晋级/部署。下一步先设计原始Event分布/样本数及自身CPU调度/cgroup计数的低扰动AA002观测，保留原矩阵/预算/median方法，不盲重复AA001或改kernel。当前无GPU客户端，19FG/服务/源码/acc007 resident门禁保持；无E2E收益证明。同op003/state review032为准。

review033：AA002完整60行/6pytest、120次原生返回核验通过，但observer p99 2.526405ms超2ms预算，保留incomplete；M1 Event168–177样本/侧有长尾，wall seed43 A/A1.066510越界。挂载cgroup在已观测区间无throttle增量，因果仍unknown。无候选晋级/部署/新模型E2E收益。纯CPU更轻观察器草案p99.023687ms，尚不资格GPU负载；下一步先完成按组cgroup方案和新唯一控制计划，保持旧护栏/预算，禁止盲重跑。全部新SHA/原始证据及review033见[op003](op-003-gems-sampling-prototype.md)与state。19FG/原服务/12355源码未改，APIidle。

review034：AA003四CPU检查通过，但launcher计划字段顺序错误，创建native plan前KeyError；边界确认0GPU/0模型请求/API0/0，按停止条件结束observer路线，不修正重启或加AA004。新contract001仅CPU草案（e104c695...，execution_ready=false）：AB/BA每seed、统一100/1000ms、每角色120行/三角色360行，300s/mode及逐行5%护栏不变。七项CPU归一化检查和实际native AST/CLI审查（944e63f9...）通过，实际六组benchmark/最终契约/collect资格尚未形成。新旧范围不混算，原M1失败及所有负面保留；19FG/原服务/生产源码未改，候选未晋级，无模型E2E收益。详见同[op003](op-003-gems-sampling-prototype.md)/state review034。

review035：完整新原生包/12CPU构建与角色检查/真实collect6通过，100/1000ms AB/BA最终契约015b19f3...冻结。首次host因自身控制日志保护误判在0GPU前退出，证据保留；CPU9协议检查与amendment8a801a06...只识别精确旧控制日志，原数据/计时/阈值/07:35截止不变，安全续接的首次native准入已运行。只有120行A/A全部真通过/源与gate有效且进程退出后才candidate+revert。当前无新候选结论或E2E收益，19FG/生产未改。完整source/SHA/边界见同op003/state。

review036：新measurement001同函数准入完整120行但一行M1 operator42AB失败（.551420/.522508ms=1.055333>1.052632），候选与revert未启动。CPU审计9312ae4f...确认12/12 M1第一段更慢，未定位因果；现CPU无限额/throttle0为事后快照。已有trace CPU分析20c92f01...：每rank2个M1 scatter中位13.568us，15个M64 scatter中位10.373/10.303ms，仅早24step单kernel/profile-on，不能当新稳态交易或M1护栏。全部原失败保留，19FG/生产原样，无新E2E收益。下一轮CPU核真实调用生命周期及语义支持边界，不盲加控制/放宽阈值/继续已拒绝role。

review037：CPU原adapter函数体4项stub检查确认identity/选中/原参考fallback/异常上传；12符号metadata相同，无法排除异常值。当前caller p∈(0,1]校验、非法/关闭topk归一化到V，直接backend非法k指针风险不能归咎实际服务。采样前allowed-mask/badwords/processors的组合尚不能证明logits finite/非全屏蔽；冻结18项设计（不可执行、无新数值）。未找到同函数两slot不同计算，M1动态原因仍unknown；旧失败保持。07:49fresh源12355/env/resident/disk通过，19FG/生产不变。下一步CPU核当前Gems异常值处理，不追加A/A或GPU测试。

review038：genericradix位键区分±0、负NaN低于-Inf/正NaN高于+Inf，而私有thresholdkey归一±0；这是源码位运算事实，不等于当前torch硬件sort次序。softmax有局部all_neg_inf保护，最终异常传播及CDFfirst_keep等价仍不确定；CPUanalysis9eac2208...保留incomplete。冻结新11组/13比较安全数值草案339b3f03...（不执行），合法k/p、默认stream、180s、无graph/计时/请求/重启。旧M1失败和19FG/生产不变，无新E2E收益。

review039：独立数值fixture/完整plan/精确PID-birth-PGID超时控制准备完毕。22项本地CPU检查过、远端22项通过断言后归档helper遇str/Path错误；v1失败保留，新唯一CPU续接仅修Path/2项回归并归档，不重放旧tests/creator。准备plan8463434d...与CPUreview158a7201...均不可执行，GPU入口/watchdog双False；08:55:43fresh12355源/env/resident/disk/API0/0/startscript19FG通过。剩余异常语义只有真实硬件可确定，按用户不立即GPU约束暂停自动跟进，等待一次明确的13比较/180s/privateGPU6诊断决定；无新性能/graph/精度资格，measurement001仍blocked。

## 补充优化点与评测记录索引

以下为同目录已有记录；结论范围以各点文档和 `state.yml` 为准。

- [acc-006-script-scope-full-gate](acc-006-script-scope-full-gate.md)
- [op-012-flaggems-vllm-version-refresh](op-012-flaggems-vllm-version-refresh.md)
- [op-013-script-scope-baseline](op-013-script-scope-baseline.md)
