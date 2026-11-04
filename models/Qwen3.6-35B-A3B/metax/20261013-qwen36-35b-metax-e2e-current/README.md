# 20261013-qwen36-35b-metax-e2e-current

2026-10-15 review014：已捕获两 TP 的 shell → mxcc --fatbin → lld，LLVM/缓存对应 FlagGems-vllm MetaX `flash_varlen_fwd_d256_tn_kernel`。非 Split-KV launcher 将不参与计算的 Q_TILES 随动态批次改变，导致预热后新组合继续编译。私有单文件修复将该项固定为 1，真实 grid 和 Split-KV 保持原样。

25 项数值/CPU、8 组 graph 各两次 replay 已通过；六形状硬件实验的预热后新增编译数从 5 降为 0，输出/LSE 相同。Event 微测 24 组完整，最低比值 0.9922x。以上不能替代模型端到端收益；旧 operator 慢行和 CG benchmark 超时保留。

生产现为原GDN加这一处attention修复；24组原生CG护栏通过后条件加载，服务中断5分39秒并按原args/完整env恢复。API982315/TP2 GPU6/7正常；源码12252文件仅TN一处变化，C1/C8通过。新源GPQA全198题已完成170/198=85.8586%，当前服务原生gate已issue/check；UUID bcbef8f8ac274343b48751537e080c5c，旧164/198属于历史source。

短场景P1024/D128/C64/N128已完成4warm+3measured，吞吐801.7/805.6/809.9tok/s、波动1.02%，未观测编译器或ITL>1s、主kernel缓存无新增。004首轮编译导致的3warm失败保留，不能作精确加速比较。完整P1024/D1024/C64/N128已结束且稳定性incomplete，当前没有因果ABR收益结论。全部正式四场景和最终验收 incomplete。后台30分钟跟进ACTIVE，新测量前重新核验服务/source/gate/资源并冻结计划。

- [基线与原始性能结论](baseline/README.md)
- [当前实验、review014及状态](optimize/README.md)
- [attention 修复与完整证据](optimize/op-005-attention-compile-key-normalization.md)
- [最终验收](acceptance/README.md)

只限 mx-59、qwen3.6-35B、8010、TP2 GPU6/7；保留全部 FlagGems/attention/GDN/MoE workspace，不改vLLM、权重或tokenizer。所有远端大产物位于 `/public-flash/jinghao/qwen3.6-35B/20261013-qwen36-35b-metax-e2e-current`，命令与SHA在同一案例记录，旧进程/评测/生命周期不可重放。

review019当前：完整P1K006的三测量1133.4/991.2/1146.2tok/s，波动13.68%>10%而incomplete；第二测量轮有自有TP attention/MoE编译和13请求共同8.90s停顿。源/gate保持、APIidle、FG全启用，停止重复测量及预热加码，先按op005文档核残余SplitKV参数与MoE输出界限专化。D128稳定不推广为完整场景通过；仍无ABR收益或最终验收结论。

review020：已从真实编译IR确认可优化维度为boundary SplitKV的TAIL_ROWS、MoE stage1的两个buffer mask界限；它们随实际批次/长度变化进入constexpr键，稳态预热不等于形状覆盖。两独立私有候选已规划，当前生产未改，尚无新实现性能/精度/graph结果；详见optimize/op005、op006、op007及state。

当前op011-v3：按用户收窄范围，topk恢复目标分支原5参/4参兼容及renormalize，仅更换公共导入库；fused_experts快路径只对NV/MetaX放开，其他平台保留原分步或原独立路径。77CPU回归通过，仅两生产+两测试变动，其他算子/Gems/vLLM/模型/原服务保持；无callerworkspace复用。源已保存，未重启/热重载，设备graph/新fullGPQA/E2E待验证；automation维持PAUSED。见[op011完整记录](optimize/op-011-moe-library-owned-dispatch.md)。

用户授权发布已完成：当前两处MoE源码及两份测试已推送至020plugin-opt-metax，[提交b8f2734](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/b8f2734beb80738ce5e4f7c61c2056f41e5c9ba5)。远端SHA已核，提交字节与容器源一致；服务/容器Git索引及其他代码未改，无重启。77CPU回归已通过，新source设备graph/fullGPQA/E2E未执行，automation保持PAUSED。

FlagGems-vllm version update completed: official main05d0ff05->de2298be, editable0.3.0.dev1, existing GDN/attention/MoE local changes preserved. Syntax/API/nativeCPU34 passed, otherdependencies/Plugin/model/service unchanged, no restart. New graph/fullGPQA/E2E not_run; automationPAUSED. Seeop012 record.

Latest script-scope resume: approved restart completed, newAPI1008868; exact19scope, TP0/1 each22actualgraphlaunch, C1/C8 all9pass, profilerOFF. New full198/65536/.8 GPQA started13:44UTC, uniquecontroller1347505; no P1K untilnew nativegate. See op013/acc006 and currentstate; earlier no-restart/pause/oldgate text is historical.

13:47UTC precision terminal FAILED: UUID93378df7056a4feda30b619dec00112a strict0/198, flexible2/198. Bothfilters198 unique doc each (396rows); native resultSHA5600429275d8b34a6b47480577016fb65050044aaae56d948c1f4b47214e2422, samplesSHAf81e448b09ff1011b5334f48332b4ccaadf3c6ec92967af8e4918c4fa0c6feb8. Terminalvalidator executed once:12355source/model/env/instance/mount/config continuity passed then deliberately refusedbelow.8; no run-record/passinggate. P1K/performance stopped beforestart, no source optimization stacked. Accuracydiagnosis Skill invoked; root cause notconfirmed. New/oldMetaX MoE backendSHA75f34372... identical, Plugin call/import and otherpaths stillneed isolation. ServiceAPI1008868 remainsrunning/idle, no extra interruption.

Read-only utility initially parsedJSONL withstr.splitlines and broke Unicode separators, then usedliteral newline to verifycomplete396rows. This wasutilityfailure, notinvalidmodel dataset and notscorefix. Prior tinyhealth/graph qualifiedexecution only; no claim of semantic pass. Rawrequests/answers remainremote; currentfailure notrewritten/retried.

14:38UTC authorized cache-isolation lifecycle running: host1426324/birth501432585; candidateAPI1025146/birth501435120, C1/C8health passed, native graph/KVrole check in progress. Sole envdelta VLLM_CACHE_ROOT under current case, no source/19scope/cache deletion. Plan2ca14820..., lifecyclee27deeed..., monitor57dc52b4.... First0/198 remains failed; review023 ranks existing lifecycle then newfullGPQA ifqualified, P1K blocked. PrivateMoE4shape exact does not exclude graph/model. Actual vendorcacheblock32 corrects earlier1056 guess; unsupported1056 probe retained, not rootcause. OldFXartifact/cachebinding suspected, not confirmed.

14:42UTC cache-isolation window completed346.56s (14:32:48→14:38:34), one authorization consumed, no future restart permission. CurrentAPI1025146/birth501435120; GPU6host1428564/ns1025947 andGPU7host1428565/ns1025948 bothbirth501445784. Source12355/argv/19scope/model/image/mount unchanged, soleenvdeltaVLLM_CACHE_ROOT. Two ranks each22actualmcGraphLaunch and20cachewritecalls show K/Vboth[tokens,1,256], oldtraceVheads8 mismatch removed. C1/C8ninepassed, profilerOFF. Newservice52590ffc33cfb35e0877546c4b2611ac7bbea76f8b557955d9fba0cb8469bef4, runtime3ea0ea0895f3459d2b6921f2c7c08713b0c70dc73e07e00dd013851aac13e828, undermanifests/acc006-isolated-cache-{service,runtime}-20261015.json.

Oldcompileartifact24bc62e8... unchanged. NewrankFX d12605b2.../710ddf40... and correctKVshape are single-variable counterfactual evidence supporting stalecache input-binding hypothesis; formal semantic resolution notyetclaimed. CPUevidence accuracy/acc006-cache-counterfactual-evidence-20261015.json SHAc67dd01740541a644013e912b8d99760136cc6ef1d53c645bfef43f82ca16e33; creator55fb02e9... completed.

NewformalGPQA UUIDd7e72aff3e6a4a7c8809d3ae7113be32, hostcontroller1446999/birth501481765 started14:40:59UTC, eval_modelqwen36-35b-script19-isolated-cache-full-graph-c32-g64k; original198/65536/temp1/.95/k20/seed42/C32/strict>=.8 unchanged. Source/env-bound newservice; provenance2equal/preflight0. Config269a8003fea443f07bafea501f528f63567905c73d095a16a99c405fd62785c6, contract219a5d447c52e0ab459740ac562e8495fd32e0e95994da760981d059f8b33e5a. Launch3941ca83... executedonce. Monitor10573a53539cd44e93727a158f6f1e7ed869a00758e76c02032fcd91ca620894 saved; terminalvalidatora447e4f70a25e85ba9408384fe518f1da9c260d15366aeb1ce2d9ee678d589b0 savednotexecuted. 14:42snapshot0complete/0timeout/32active; notformal score. P1K blocked until native terminalgate, no concurrentGPUprobe/profile/benchmark/sourcechange. Firststrict0/198 remainsfrozen; no oldgate rebind. Heartbeat updated ACTIVE30min/quietunchanged for thisUUID.

2026-10-15 16:23UTC最新：隔离缓存后的正式GPQA已完成，UUID d7e72aff3e6a4a7c8809d3ae7113be32 strict164/198=82.8283%>=80，0timeout；全198/65536/temp1/top_p.95/top_k20/seed42/C32不变，全部filter/原生来源/config/12355源码/当前service/env/model/tokenizer/镜像挂载连续性通过。CPU收尾15:56:07完成，nativeissue/check成功：gate accuracy/acc006-isolated-cache-g64k-accuracy-gate-20261015.json SHA9fdcc14eec68a6203a3c46cbf7e45c46fdcea5474ba4def838119fedaf98a642；terminalcontinuity06b0a111d267331fd8525ed33c6be9b66add1385f36273844fd7c725683b8fb7，terminalvalidation4f6834150a253a745c977c3254a54fd3ba48a6ee734669d5f8e3d30c9e6940d8。未重复GPQA或issue/validator。当前API1025146及GPU6/7workers保持，旧cache/source未动，原19FG范围不变。

缓存隔离执行边界得到反事实支持：相同源码/参数，旧cache启动Vheads8且0/198，新增VLLM_CACHE_ROOT后K/V均1head、两TP各22actualgraphreplay、C1/C8和新full164/198通过；可恢复性能工作，内部缓存key/二进制失效机制仍不作过度确定归因。原始0/198、C1无关输出及私有负面/utility失败全部保留，不改判为通过。该分数只绑定当前组合/环境，不能归因单个Plugin/MoE/library改动或冒充NV验证。原用户启动脚本尚未写入cacheRoot；下次reload须保持隔离策略，不授权未来停服。

P1K新scene-entry基线已16:21:45启动：run-idop013-p1k-full-001，modebaseline/rolebaseline，controller1531875/birth502086404，nativeclientns1032848/birth502086510。完整P1024/D1024/C64/N128/temp1/ignoreEOS/seed42/range0，4warm末3spread<=5%/3measuredspread<=10%/600sround/全轮保留/无profiler。当前仅新scope单实例基线，不能与旧20scope不稳轮算精确gain。新planSHAf0a5bac2...、comparison8bbbadbd...、v2identityb5be1a8c...、observer1dfbb147...、v2launch36841b6f...。Freshsource/gate/APIidle/资源/镜像挂载/timeNS/cgroup通过。首版dryrun因baseline不能传--accuracy-gate而拒绝，0benchmarkrequests/无run目录，原文件日志保留；v2仅修原生接口，外部nativecheck+gateSHA仍冻结在identity/launch，七轮dryrun通过，不放宽测量/精度标准。真实测量尚无结果。

CPU收尾器1533067/birth502096784已16:23:29启动，commands/wait-finalize-op013-p1k-full-001-20261015.py SHAde78eacd2efda4335ae607c3812398f241dca454fc922a37ada40ac5b149d4d3；launcher11b45361...已执行，不可重放。只等现有native退出后finishd14dd85a...与analyzef929f151...，不产生新GPU工作。监控monitor-op013-p1k-full-001-20261015.py SHA3ffd90624dde2d41c84fb96fbe3a88ef0cafdb9b1a5d4775e8ec20e8f5c911d4。终态核native全部轮+稳定性+observer开销+source/gate连续性+compiler/共同停顿时间线；未达稳态/incomplete保留，不丢慢轮/自动加warm。review024首优先本轮baseline，其后按实际当前owner/routing/compiler证据重排；不能切P4K/最终acceptance通过。所有旧creator均不重放，heartbeat继续ACTIVE。

2026-10-15 16:47UTC P1K终态已核：op013-p1k-full-001 全7轮原生有效，各128成功/0失败，input/output各131072；末3warmspread0.843836%<=5%，3measured输出1132.9415/1132.7759/1133.0204tok/s，median1132.9415，spread0.021576%<=10%。3measured meanTTFT1923.3/1987.4/1855.0ms、meanTPOT54.593/54.545/54.665ms、medianITL52.935/52.803/52.880ms、maxITL.489/.509/.504s；均客户端proxy而非puredevice。全部7轮无ITL>1s/共同停顿、0root--fatbin编译事务；两TP仅warm1各mxcc--version，不当kernelcompile。Observer .011729core/p99sample12.442ms/5859samples missed0/fatalnull准入。Source12355/实例/env/模型/挂载/gate继续通过，APIidle，native和CPU收尾均退出。Nativecheck_run通过且project稳定通过，但仅新scope单实例sceneentrybaseline，无匹配anchor/candidate/revert，不能计算旧20scope精确收益或关闭P1K/最终验收。

证据：runrecord results/performance/op013-p1k-full-001/run-record.json SHA335474b47664a87497bed051134e47ccca4cc5bf660e5310b669a659387d4e73；terminalc5821fb18832a5bd2d472fe018ac3589034b79eee68715ca66c8ffa676c89bad；analysis23b0c1ffe48887b8901e836d4b99e48fb404556680a8eb5d16bed12c32a50875；postcontinuitya1691d4dfc78d41b946b95aa0ebed6098a0c2780fe46c5895228878e58951269。无编译/停顿结论仅限本workload、7轮、主线程5Hz/后代发现1Hz，不能排除亚秒进程或未测shape。

review025重排：先当前source稳态phase profiling确认compute/host/comm热点，再从真实dispatch/shape选择单变量算子或Plugin优化；旧samplerM1负面、旧MoErandomtile和当前范围未选FGattention延后。新profile_idprof-003-script19-steady-p1k已16:57:12启动：host1542915/birth502299063，commands/run-prof003-script19-steady-20261015.py SHA4f45257ce658ea0947e83b04c3ed17527b8af64cfcaee4889008c00d9305e2f9，launcherd1ec345f...已执行不可重放。Plan04fc6d9d...，P1024/D1024/C64/N128两轮firstwarm/lastprofile、600sround/temp1/seed42/ignoreEOS，沿用现有24step native profiler，无重启/源修改/关闭FG。旧4trace库存48be84c0...保持，actualnative source dfeb9bf4...证明初始单请求probe早于start_profile，抓主批次。按实际new/cached marker、query/cache shape、graph验证phase；cached可能仍chunkedprefill，不盲判pureDecode。当前仅capture，phase/rank/热点结论待生成；profiler耗时/导出暂停不算性能收益。monitor29008f0b5b4285eec82265400be0d6d918e589f3c26262470d18669437bbcdf7，唯一status results/prof003-script19-status-20261015.json。现有完整19FG/无callerworkspace/服务及精度gate9fdcc14e...保持；不并发其他GPU实验。

2026-10-16 review026: prof003 oldstdoutassert corrected by CPU-only existing-evidence continuation, no recapture; two ranks15graph each/current source+APIidle. Captured14C64Decode steps show MoE43–44% kernelactivity; private op014 exactM64 pairGEMM1 planned, noproductionchange/claimedgain. See optimize/op-013 and op-014.

2026-10-16 review027: MoE privatepair rejected after complete42native rows (.833/.873/1.006x targetrouting), no deployment/servicechange. Current postforward sampling scatter[64,248320] ~10ms slowcalls verified; next op003 currentbaseline incremental M64-only prototype audit, oldM1negative preserved. Currentbaseline1132.94tok/s/gate164/198 unchanged; formalE2Estillincomplete.

2026-10-16 review028：op003当前私有M64数值80组精确通过；native v1标签接口失败0timing保留、v2修正后在模型连续性预检停止，未生成有效性能行。Host/容器的 `/public-flash/models/Qwen3.6-35B-A3B` 同时缺失，原API/TP实例仍在且APIidle；NFS挂载仍在。历史164/198不改判，但当前artifact绑定阻塞；等待用户恢复/确认真实路径，暂停新GPU及自动续跑。服务19FG/无callerworkspace/生产源码未变。当前累计E2E收益未知，详见同op003与optimize/state.yml review028。

2026-10-16 review029：用户已原路径下载完成；35文件/26shards齐，配置/tokenizer/index SHA与size相同，mtime变更，原tensor内容SHA无记录，不能宣布新下载等价或已加载。服务/四进程/12355source/env保持，未重启/加载。新resident双绑定明确区分原已加载模型与磁盘恢复，仅资格当前实例，禁止future rebind。新完整GPQA acc007已于北京时间10:48:51启动，UUID198b58e3e9a3457094744f9c7f9f1f80、198/65536/temp1/.95/k20/seed42/C32/.8；初始0/198/32active，无gate，不并发性能。后台30minACTIVE安静监控。历史164与P1K数据不改，op003 private80numericpass但60行native续接等待新gate；生产未部署、无E2E收益。详见op013与state review029/acc007。
