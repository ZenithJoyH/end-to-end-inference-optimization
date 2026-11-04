2026-11-02 18:20：[点64 海光修复确认](20261102-public-pr-ci-followup-64.md)：当前e617头海光functional success，unit1596pass/164skip、functional13pass/42skip、多卡2skip，原106个编译失败在同套测试中消失，原断言/门禁未变。海光整模E2E仍排队，整体CI受两项基础设施失败及其他队列影响未完成；不宣称全CI/整模通过。生产源码/MBT/启动参数未变，FGV依赖保留。

2026-11-03 09:02：点64当前d86f CI终态失败：51job中46成功/3跳过/2失败（昆仑芯设备noc idle timeout及派生ci-gate）。NVIDIA测试隔离修复已在真实CI验证，其余平台既定任务通过；需要昆仑芯平台诊断证据，停止无意义轮询、不盲重试。最终当前生产只读审计通过，服务/MBT/参数/源码index/DB保持，候选未安装。两PR保持Ready与依赖、不合并。[点64记录](20261102-public-pr-ci-followup-64.md)。

2026-11-03 03:46：点64当前d86f808e NVIDIA真实CI确认测试隔离修复：unit1772/functional54通过、0失败（89/21跳过、多卡2跳过）；海光当前功能和两E2E也通过。全CI仍有昆仑芯设备超时及剩余队列，生产零操作。[点64记录](20261102-public-pr-ci-followup-64.md)。

2026-11-02 22:06：点64当前`d86f808e`昆仑芯unit1663/多卡2通过，但功能1项报设备`noc idle timeout`（6通过/42跳过），根因未知，保留原证据、不盲改源码或重试。NVIDIA/海光等CI待出，生产零操作。[点64记录](20261102-public-pr-ci-followup-64.md)。

2026-11-02 21:22：点64 [Plugin PR669](https://github.com/flagos-ai/vllm-plugin-FL/pull/669) 新头`d86f808e`仅修复GLM测试mock经惰性import污染HY4分发：同序列从5pass/1fail到6pass，CPU477/PPU159及3capture/6变化replay通过。CI41452027210已触发待平台；海光编译修复在父头已验证，不能算新头通过。生产服务/MBT/启动参数/DB保持，未安装候选。详见[点64记录](20261102-public-pr-ci-followup-64.md)。

2026-11-02 17:33：[点64 CI跟进](20261102-public-pr-ci-followup-64.md)：当前e617头新增昆仑芯inference E2E runner失联，GitHub注解明确且无步骤/模型报告；与天数安装前预检OOM共两项基础设施失败，待整轮终态去重后一次仓库机制重试，未修改源码/门禁。海光已执行中、结果待出，其他队列仍待；生产/MBT/启动参数未动，不是候选数值失败或整体通过。

2026-11-02 16:53：[点64 CI跟进](20261102-public-pr-ci-followup-64.md)：当前e617头昆仑芯功能suite成功（1663unit/2多卡/7functional），PPU功能/两E2E/benchmark和天数功能/serving也成功；天数inference在安装/模型测试前设备预检OOM，待整轮终态去重后按作者机制重试一次，尚未发送。分页32job仍有海光等排队，不宣称海光修复或全CI通过；未动生产/MBT/参数，FGV依赖保留。

2026-11-02 16:08：[点64 CI修复](20261102-public-pr-ci-followup-64.md)：旧头海光metadata编译106失败，针对HCU指针规范化准备单文件整数地址选择修复，CPU477/PPU159零fail/skip、3capture/6变化回放、precommit/Ruff/wheel内容均通过；已推送Plugin #669新头e6172c0c，CI41410524289已通过lint/build/discover/CodeScan、PPU功能及两E2E、天数功能；25job中其余平台/E2E仍执行或排队，海光/昆仑芯新结果待出。旧昆仑芯通过和天数预检OOM单独保留，不盲重试旧轮。生产同实例/源/index/DB/MBT32768/原参数未变，依赖FGV/pin不变。

2026-11-02 15:33：[点64 CI跟进](20261102-public-pr-ci-followup-64.md)：新头1c1551e5昆仑芯functional已success（unit1663pass/92skip、多卡2pass、functional7pass/42skip），原metadata失败在此suite修复获验证；平头哥/摩尔线程功能、两E2E及benchmark也success。天数在项目安装和测试前的32×32设备预检报OOM，属runner初始化失败证据，等待本轮CI终态按作者/rerun机制重试一次，未改库/门禁或生产。其他平台/E2E仍待，非全CI通过，依赖FGV/pin仍在。

2026-11-02 12:05：[点64 CI修复](20261102-public-pr-ci-followup-64.md)定位到初始PR头昆仑芯metadata测试110失败，平头哥两E2E成功；在独立副本准备合法访存/独立discard候选，CPU477/PPU159无失败跳过、3capture/6变化输入replay及wheel/适用precommit通过。仅两文件fast-forward提交Plugin #669新头1c1551e5，触发CI41386574541，昆仑芯修复效果待新CI，不混用旧头通过。生产实例/三库/原MBT32768/启动参数/DB均未动，FGV硬件CI按用户要求暂不跟进，合入依赖仍保留；原监控继续新头。

2026-11-02：[点64 两PR转Ready及CI跟进](20261102-public-pr-ci-followup-64.md)：[FGV1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)与[Plugin669](https://github.com/flagos-ai/vllm-plugin-FL/pull/669)均已非Draft，Plugin依赖FGV合入/组合公共pin/安装回归仍为合并阻塞。Plugin正常CI41382208784已启动，lint/build/CodeScan及NVIDIA/PPU/天数功能通过，E2E运行、其他平台排队，整体尚未通过。FGV硬件授权标签与重启返回403，用户明确暂不跟进算子库维护人员问题；原rule/basic/CLA成功、硬件skip不计pass。生产同实例/源/MBT32768/原参数/DB/health只读核验未变，零模型请求/重启/安装。以下保留历史Draft状态。

2026-11-02：[点63 Plugin PR](20261102-plugin-sparse-mla-pr-63.md)已提交[Draft #669](https://github.com/flagos-ai/vllm-plugin-FL/pull/669)，明确依赖[FGV #1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)合入、公共组合pin收敛及后续回归。8文件/1提交，排除平台MM黑名单；独立副本CPU477/PPU153全部通过、3capture/6变化输入replay、适用pre-commit/额外生产Ruff和wheel内容核验通过。Hosted ci-gate因Draft使必需任务skipped而failure，已在PR披露，CLA passed；未改CI、不将skip当pass。生产源码/原实例/MBT32768/参数/DB不变，无新模型请求、GPQA或E2E收益。

2026-11-02 10:44：[点62 FGV算子PR](20261102-flaggems-vllm-sparse-mla-pr-62.md)已提交[Draft #1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)，聚焦紧凑H4 Sparse MLA/graph能力，5文件/1提交。真实PPU33项0失败0跳过、8capture/16新输入replay、7项pre-commit、wheel/54 CI helper通过，Hosted rule-check/basic CI/CLA成功（硬件job skipped）。12形状算子benchmark有2项SQ1/TOPK128低于0.9，性能门槛未过，全部披露并维持Draft；非E2E、未自动调优/安装。生产三库/原实例/MBT32768/原参数/DB均未变，health200空闲；SQL/MNNVL独立主题未混入。

2026-11-02 09:52：[点61 Plugin PR审查](20261102-plugin-pr-review-61.md)完成，实际安装Plugin仍5生产+3测试共8文件；仅修复两测试文件格式/import及thead标题注释，生产Python字节/配置值不变。原生CPU465项0失败0跳过、适用pre-commit通过；已准备metadata、graph/KPool/OOT、PPU临时MM排除三个主题补丁/英文说明，顺序应用逐字节验证通过，未提交推送。**PR状态needs_revision**：FGV公共固定依赖须先交付H4/graph能力，MM全PPU排除须单独界定影响范围。原实例/MBT32768/启动参数与DB不变，health200空闲，无新模型/精度/性能测量，点60分数独立保留。

2026-11-02 00:03：[点60全部20题补跑](20261101-adaptation-consolidation-60.md)已完成并最终核验：**10/20答对，统一替换后174/198=87.88%≥86%，补充口径达标**；原单次全量C64 164/198原样保留，无新完整gate。13题有最终正文（10对3错），7题HTTP成功/60K无正文被工具标TIMEOUT，实际HTTP超时0；原C64长请求根因未确认。源/实例/原脚本/MBT/RPC参数未变，DB正常运行字节前后均保留，当前health200空闲；未自动继续性能或新试验，监控`glm-20`已删除。以下为分时记录。

2026-11-01 20:27：[点60全部20题诊断补跑](20261101-adaptation-consolidation-60.md)已唯一启动，20请求实际运行。原异常为19题HTTP客户端14400秒超时，另1题doc190达到60K且无最终正文，被工具转为TIMEOUT；无服务OOM/非法访问/RPC日志。原参数/MBT/源/实例不变，C64上限实际20并发、原生成参数、独立缓存、零重试；全部20统一替换，其余178原样保留，原生全量164/198独立保留，无新完整gate。后台`glm-20`只读跟进，结果待定。

2026-11-01 20:04：[点60收敛版单次全量GPQA](20261101-adaptation-consolidation-60.md)已完成：**C64，strict164/198=82.83%，低于86%门槛**。198唯一题/396行/两filter及provenance和最终身份审计通过；20个timeout标记仅健康观察。原脚本/MBT32768/参数/源码/实例/DB均未变，服务health200空闲；未签发gate、未补跑或继续性能晋级，精度事件根因未确认。原生结果与失败完整保留，监控`glm-gpqa-c64`已删除。以下为分时记录。

2026-11-01 14:32：[点60单次全量GPQA](20261101-adaptation-consolidation-60.md)已唯一派发并实际生成：198题/C64，strict≥86%，新UUID缓存/API及eval重试0；当前64请求运行、health200。原脚本/MBT32768/参数/源码/实例不变，分数待完整结果，不混用旧172补充。监控`glm-gpqa-c64`每30分钟只读跟进，未变安静、终态通知并清理。

2026-11-01：用户追加[点60](20261101-adaptation-consolidation-60.md)收敛后单次198题/C64正式GPQA，strict门槛86%；同实例/源码/原脚本/MBT/参数核验未变，正在零生成准备与冻结契约，尚未派发生成请求。

2026-11-01 13:18：[点60适配收敛](20261101-adaptation-consolidation-60.md)完成并保留到当前容器实际安装源码：18→16文件（10生产+6测试；Plugin8/FG2/FGV6），metadata归Plugin、复用公共lookup；必要H4/FULL/KPool/SQL/Autograd/MM兼容保留。CPU465、真实PPU metadata145/6次变化输入graph、完整模型C1/C8/三16K/11答案/C64 64/64及FULL/当前身份审计通过，服务8011健康空闲；原脚本/MBT32768/参数/RPC300不变。既有TileLang运行库加载观察原样记录，未宣称全栈无TileLang执行。无新GPQA/性能/gate或提交推送，原172补充仅属旧源码。

2026-11-01 12:50：[点60](20261101-adaptation-consolidation-60.md)已直接收敛实际安装源码，当前差异18→16（10生产+6测试）；CPU465与真实PPU metadata145全部通过，6次变化输入sentinel graph通过，公开导入归属核验通过。首次候选原脚本完整模型/FULL/C64回归启动中；原MBT/参数不变，暂无新全量精度或性能结论。

2026-11-01 12:14：[点60](20261101-adaptation-consolidation-60.md)首次编排在源码写入前触发ARG_MAX，六路径未变；原服务完整恢复回归正在运行。同候选标准输入传输修复已本机正反向SHA验证，等待原恢复终态后接续，尚无候选模型/性能结论。

2026-11-01：[点60适配补丁收敛](20261101-adaptation-consolidation-60.md)开始，只读盘点11生产+7测试文件。保持原参数与公共模型路径，先归档当前源码、逐项审查职责与重复，再实施必要收敛并回归；无新性能结论。

2026-11-01：[点59的21题统一补跑](20261030-native-mm-registration-repair-59.md)已于10-31 20:12结束，21题答对9题；全部替换、其他177题不变，补充口径 **172/198＝86.8687%≥86%，达标**。原生单次163/198及原失败保留；仍7题timeout标记不另设门槛，不做新一轮补跑、不伪造新单次全量gate或宣称性能收益。

# 总优化记录

2026-10-30：[点59原生ATen MM注册修复](20261030-native-mm-registration-repair-59.md)仅现有thead.yaml排除mm/mm_out，CPU495/4原有skip、单PPU24次独立数值与6次变化输入graph通过；原300/原脚本完整模型回归21:46通过（C1/C8、三16K、11/11答案、C64 64/64、FULL），无新RPC/OOM/非法访问。原生198题C64已结束，strict163/198=82.3232%，低于86%，未签发gate；外层4小时超时与完整原生结果均保留，现有完整原生证据与当前同实例/源码/原参数/RPC300/health终态核验通过，低分冻结性能晋级，不自动补跑；21题timeout标记（仅1题usage明确60K）不另设门槛。

2026-10-30：[点58](20261030-upstream-refresh-58.md)官方Plugin7094141/FGfe919c5/FGV9f6a0ef及必要兼容已安装，各1份editable；CPU/设备/SQL/Autograd专项通过。临时RPC1200的C1/C8/C64通过后已停止，原300完整回归在P1K C8仍RPC超时并清理，GPQA零请求、无新分数；当前问题接点59，原失败保留，不把临时诊断或旧分数当新版本验收。

2026-10-23 15:29只读差距诊断：[点57](20261023-readaptation-e2e-gap-57.md)用户P1K1096.30、P4K406.92token/s（第2/3轮均值），旧优化栈P4K979.12，描述差距−58.44%。确认当前MoE走FG而非旧特化所在FGV，MLA/Prefill公共算子路径变化，晚到Prefill时有generation0–5的长窗口。P16K存在容量等待/抢占，缓存并发汇总含KDA80000粒度，不能把135M当实际MLA容量；具体贡献待受控归因。P4K测量两轮spread8.918%超原5%，不冒充稳态ABR。align+2.71%不代表恢复旧栈性能；用户测试继续，源码参数不变，无新请求/重启/修复。

2026-10-23 14:21已保留：[点56 user-retain-03](20261023-moe-align-prefix-56.md)按用户明确决定保留同一align优化（同缓存Mixed+2.7148%）；原3%门槛failed回执不改写。新实例`3866321:545188042`的C1/C8、三16K、11/11答案、C64 64/64、FULL捕获/多token回放及当前源/index/安装/挂载/health审计通过，8011已健康空闲运行。MBT32768/原启动脚本与参数/用户Plugin不变，交给用户跑端到端，Agent停下、不自动跑性能/GPQA/profiler或下一候选。新源码未签新完整精度gate，旧173/198不改绑。下文为各时点历史。

2026-10-23 14:14用户保留决定：[点56 user-retain-03](20261023-moe-align-prefix-56.md)按用户明确指示接受2.7148%收益，重新部署已验证的同一align补丁；原3%契约及failed回执保留，不改成passed。部署与新实例完整最小模型/FULL/C64回归已唯一启动，MBT/启动参数/用户Plugin保持；通过后交给用户跑端到端，Agent不自动跑性能/GPQA或下一优化。下文13:53为此前回退终态。

2026-10-23 13:53终态：[点56同缓存复测](20261023-moe-align-prefix-56.md)三臂三阶段99轮完整、全部稳定，25个DB主文件/全表逻辑检查点完全一致，缓存可比性已解决。Mixed输出1157.77→1189.20 token/s（+2.7148%），低于预冻结3%保留门槛，原生`failed`而非incomplete；Decode+2.3550%、Prefill−0.1645%，两项守护passed，B/R吞吐漂移0.8023%/1.0893%/0.1870%均<3%。不改门槛/丢慢轮/混用旧4.1964%：align已精确回退，当前原版完整模型/FULL/C64与源/index/参数/DB/安装/镜像挂载/health审计通过。当前回退实例173/198＝87.3737%≥86%已显式绑定，非新GPQA；MBT/启动参数/用户Plugin保持，未提交推送。下一规划优先MoE GEMM2实际配置证伪，其次BMM布局全链，尚未派发；本轮`glm-align`已删除，不自行安装/发新实验。

| 同缓存targeted，主要吞吐token/s | baseline | candidate | revert | 候选变化 / 决定 |
|---|---:|---:|---:|---|
| Mixed P1024/D1024/C64/N128，输出 | 1157.7680 | 1189.1990 | 1148.4791 | +2.7148%，未达3%，已回退 |
| Decode P1024/D1024/C64/N64，输出 | 1172.1567 | 1199.7607 | 1159.3883 | +2.3550%，非回归守护通过 |
| Prefill P1024/D1/C64/N64，总token | 12299.4422 | 12279.2089 | 12322.4409 | −0.1645%，非回归守护通过 |

全部三轮/守护延迟及spread见同点文档和state；客户端代理不冒充设备时间。以下为历史进度与旧轮，不代表当前状态。

2026-10-23 11:52只读进度：[点56同缓存新轮](20261023-moe-align-prefix-56.md)Mixed原版基线8+3完成并原生复验，输出三轮1157.7680/1143.6935/1159.0224 token/s，中位1157.7680、spread1.3240%，全部约定指标稳定≤5%；P99 TTFT/TPOT/ITL中位5377.8155/53.9275/52.0635 ms，均为客户端代理。5个DB字节/全表逻辑检查点一致，原版实例/源/index/参数/health及173/198显式绑定复验通过；Decode进行中、候选尚未安装。只是基线进度，无新收益/三臂/回退漂移结论；monitor继续安静跟进。

11:28精度绑定补记：上述原版（未安装新align）的173/198＝87.3737%≥86%已通过显式schema6重启＋正常缓存写入审计和原生check，原始分数/manifest不改、零模型请求；只绑定原版当前实例，不证明性能可比性或新align源码精度。新三臂仍运行，尚未确认收益/保留。

2026-10-23 11:18接续：[点56同缓存核验](20261023-moe-align-prefix-56.md)当前1319张调参表逐行摘要已冻结；对更早点51快照发现新增295表/共同表19139行，旧行修改删除0，但精确旧三臂基线快照缺失，旧`abr-01`仍incomplete。新`cache-comparability-02`已唯一启动相同P1K三阶段三臂、8+3及原门槛，每阶段前后严格校验生产DB主文件与全表逻辑SHA，不重置/回退缓存、不允许比较器忽略差异。仅原生Mixed和Decode/Prefill守护全pass才按最新用户授权重新安装并完整模型/FULL/C64回归后保留，否则恢复原版。MBT/启动参数/用户Plugin不变；当前未确认新收益。`glm-align`只读跟进新轮，重启加正常DB写入精度绑定单独审计，不给新align源码套用旧173分数。下文为旧轮历史。

2026-10-23 04:10终态：[点56](20261023-moe-align-prefix-56.md)三臂三阶段各8+3共99轮全部完成且原生稳定性复验通过；Mixed/Decode A/B表观吞吐+4.1964%/+3.4519%，回退吞吐数值漂移0.5115%/0.9068%，P99非回归数值项均在阈值内。但基线DB与候选/回退DB指纹不同，原冻结严格Mixed及Decode/Prefill比较均`incomplete`，不是确认净收益，不改SHA/门槛、不重跑。已精确恢复原FG、原参数服务与完整模型/FULL/C64；最终当前源/index/安装/镜像挂载/权重/DB/health独立审计通过，用户Plugin/MBT保持、无新gate/提交推送，`glm-align`已删除。规划优先核清缓存等价性，之后才考虑MoE GEMM2/BMM热点，未自动执行。以下为历史时点。

| 点56 targeted吞吐中位，token/s | baseline | candidate | revert | 最终决定 |
|---|---:|---:|---:|---|
| Mixed P1024/D1024/C64/N128，输出 | 1144.05 | 1192.06 | 1149.90 | incomplete：DB身份差异，候选已回退 |
| Decode P1024/D1024/C64/N64，输出 | 1158.75 | 1198.75 | 1148.24 | 数值守护通过，身份守护incomplete |
| Prefill P1024/D1/C64/N64，总token | 12314.23 | 12324.11 | 12316.47 | 数值守护通过，身份守护incomplete |

2026-10-23 03:36只读续记：[点56](20261023-moe-align-prefix-56.md)Mixed回退完成且稳定，中位1149.90输出token/s、吞吐spread1.6201%、B/R吞吐数值漂移0.5115%；Decode回退尚未终态、Prefill待执行，严格DB身份及最终恢复审计待定，无完整三臂/确认收益结论。原版源/index、原参数和health200保持，未追加实验，monitor继续安静跟进。

2026-10-23 03:06：[点56](20261023-moe-align-prefix-56.md)候选三阶段各8+3完成且原生复验稳定通过；Mixed/Decode输出中位1192.06/1198.75 token/s、较基线表观+4.1964%/+3.4519%，Prefill总吞吐表观+0.0803%，尚非确认净收益。唯一控制器已精确回退一份FG补丁、恢复原参数无profiler服务，完整最小模型/FULL/C64再次通过；回退Mixed测量进行中。最终回退漂移与严格DB身份比较未出，保留实际DB差异，不能提前宣布三臂成功。用户源码/index和MBT/启动参数保持，`glm-align`继续只读监控；以下为历史时点。

2026-10-23 02:36：[点56](20261023-moe-align-prefix-56.md)16rank实际命中已确认：各294次向量前缀kernel、旧scalar0、graph launch5次，原trace SHA/PID映射复验通过。随后独立无profiler候选用原脚本启动，完整最小模型/三16K/11答案/C64/FULL回归通过；Mixed已有9轮128/128成功、阶段未终态，候选/回退三臂尚未结束，不报E2E收益。MBT/推理参数、用户Plugin/FGV及index保持，实际DB字节变化保留并等待冻结严格比较，不归一化指纹。`glm-align`继续只读监控；以下为历史时点。

2026-10-23 02:10：[点56](20261023-moe-align-prefix-56.md)无profiler原版Mixed/Decode/Prefill基线各8+3已完成，原生复验及全部指标稳定性通过；主要吞吐中位1144.05/1158.75/12314.23 token/s，吞吐spread1.376%/2.116%/0.160%。唯一接续控制器已安装一份FG补丁，用户Plugin/FGV及全部index未变，诊断实例C1/C8、三16K及11答案通过、C64进行中；实际16rank命中、候选/回退测量仍待完成，无E2E收益结论。MBT/推理参数不变，`glm-align`继续只读跟进。以下为历史时点。

2026-10-23 01:33：[点55](20261022-steady-decode-mixed-profile-55.md)主机/算子/通信采集修复与归因已闭环；[点56](20261023-moe-align-prefix-56.md)实际FlagGems非二次幂align前缀向量化已通过94组非空组合（原/候选188次）、13种前缀逐位检查及各2次改变输入graph，8组旧M0边界两者相同。M64/128全alignment链约61→12.8µs，仅为4.75×局部加速，尚无E2E收益。新`abr-01`无profile原版Mixed/Decode/Prefill各8+3已唯一启动；候选/回退接续唯一排队、等基线稳定终态后才装一份FG文件并做实际16rank命中和完整模型/FULL/C64，再同参数比较。当前用户Plugin/FGV、MBT32768/推理参数/原脚本均未改，候选尚未安装；`glm-align`只读跟进。早期182组合数为手算误写，原始矩阵/结果始终94，已按原JSON纠正，无删样本或改阈值。以下为历史时点。

2026-10-23归因完成：[点55修复轮](20261022-steady-decode-mixed-profile-55.md)两段16rank和前端/EngineCore采样已补齐并完成原服务回归/审计。rank0 Decode/Mixed窗口6.49/18.85秒，MoE GEMM累计2.46/6.44秒、BMM0.865/1.905秒、Sparse MLA0.562/1.503秒、显式PCCL并集0.371/1.128秒；主机CPU确有活动，但runqueue很小，未证明CPU调度为主瓶颈。CPU与设备重叠、通信非关键路径分解，不相加或称性能收益。下一[点56](20261023-moe-align-prefix-56.md)预注册实际FlagGems非二次幂align前缀计数向量化，先外部全链整数/graph微基准，未改Plugin、MBT或推理参数；通过才做模型回归与无profile三臂。

2026-10-23 00:37：[点55修复轮](20261022-steady-decode-mixed-profile-55.md)Decode64/64、Mixed128/128及两段16worker/前端/EngineCore覆盖均通过；原服务完整minimal/FULL/C64和当前只读身份审计通过，用户源码/index与MBT/推理参数不变。恢复过程中freeze旧路径错误已保留，仅接续未执行回归、没有二次重启或重采。离线逐rank及同时间窗主机/计算/通信分析运行中，尚未宣称新端到端收益。

2026-10-23 00:00点55修复接续：[同一点55记录](20261022-steady-decode-mixed-profile-55.md)的`capture-repair-02`已通过完整模型/FULL/C64回归；Decode稳态准入spread1.9744%，64/64请求、16rank设备/graph覆盖和API/EngineCore共约4.55万CPU栈样本均通过。日志判定修复和新host采样已实际验证，Mixed正在8+1准入；原MBT、推理参数、用户源码/index保持。完整归因待Mixed和最终原服务恢复完成，无新优化收益。下文23:12为旧轮终态。

23:12终态：[点55稳态Decode/Mixed归因](20261022-steady-decode-mixed-profile-55.md)为partial/incomplete。模型完整回归、Decode准入和64/64请求成功，16 worker均有128 graph launch及有效设备trace；控制器误在客户端查服务端日志短语而停止，Mixed未运行。离线证据恢复确认frontend仅元数据、主机Python归因缺失，不能将采集整体改判passed。rank0约6.519秒窗口内MoE/BMM/Sparse MLA累计约2503/865/562ms，PCCL通信并集355ms；这些是局部热点线索，不是端到端关键路径占比或收益。原服务22:44恢复，完整minimal/FULL/C64及22:59当前身份审计通过，用户源码/index、MBT和原启动参数不变；正常DB写入是严格rebind唯一差异，原173/198仍达标但未伪造新实例gate。监控已删除，无补采或新候选。下一轮先补可观测性/绑定缺口，再核对实际MoE阶段配置与BMM布局；以下为历史时点。

21:12终态：[点54](20261022-user-plugin-production-rebaseline-54.md)当前用户Plugin的P1K三阶段各8+3全部完成，33轮原生与当前源/index/实例/参数/安装/镜像挂载独立审计通过，768个测量请求0失败。Prefill总吞吐/Decode输出/Mixed输出中位数为12310.59/1157.79/1148.85 token/s，三轮spread为0.310%/1.504%/1.365%；全部约定P99稳定性≤5%。当前原生精度173/198＝87.3737%≥86%且显式绑定有效，MBT32768/用户源码/启动参数/DB不变，health200空闲；`glm-plugin`已删除。本轮仅稳态入口基线，无ABR收益/回退漂移或四场景验收。planning54优先提出Decode/Mixed主机—设备—通信归因，其次在实际热点证明后评估H4 Sparse MLA/融合索引算子；没有自动启动profile或候选。完整三轮、指标单位、证据SHA与限制见同页及state。以下为历史时点。

20:15只读进度：[点54当前版本基线](20261022-user-plugin-production-rebaseline-54.md)Prefill与Decode均完成8预热+3测量及原生复验。Decode输出吞吐中位数1157.7877 token/s、极差1.5042%，P99 TTFT/TPOT/ITL中位数5395.172/53.179/51.667 ms，全部约定稳定性指标≤5%。Mixed已有9/11轮validation，尚无终态；同一控制器、容器内API身份与health200已核对，未追加请求或改MBT/源码/服务。仅部分入口基线，不是ABR收益或回退漂移改善；以下为此前时点。

19:41只读进度：[点54当前版本基线](20261022-user-plugin-production-rebaseline-54.md)Prefill的8预热+3测量及原生复验通过：总token吞吐中位数12310.59 token/s、极差0.310%，P99 TTFT中位数5319.33 ms、极差0.314%，全部约定稳定性指标≤5%。Decode/Mixed仍待现控制器完成，服务同实例health200；当前只是阶段入口基线，无新收益或ABR结论。

19:35接续：[点54基于用户当前Plugin](20261022-user-plugin-production-rebaseline-54.md)当前SHA1ecb0ef3…原生单次198题/C64 GPQA **173/198＝87.3737%≥86%**，原生两个filter、来源和schema5绑定及终态当前身份复核通过；5个timeout标记仅健康观察，无补充/best-of。此前CPU126及完整C1/C8/16K/11答案/C64/FULL回归通过。保持用户源码、MBT32768和原启动参数，新版本P1K Prefill/Decode/Mixed入口基线已在`steady-p1k-01`唯一派发，统一8预热+3测量、5%稳定性契约。`glm-plugin`只读接续；旧点53单独保留，当前尚无新性能收益、ABR或四场景验收结论。

15:35终态：[点53三阶段入口基线](20261022-steady-p1k-phase-baseline-53.md)全部33轮原生复验通过，三阶段各8预热+3测量，768个测量请求0失败。Prefill总token吞吐中位数12331.81、Decode/Mixed输出吞吐1155.96/1152.85 token/s，吞吐极差1.13%/1.69%/1.23%，约定P99指标极差均≤5%。仅原源码基线，无ABR/收益/回退漂移结论。当前同实例health200/空闲，但Plugin磁盘内容在终态后观察到529cd814…→4745048d…变化；三份近期文件mtime15:32，当前源码绑定incomplete，原173/198分数不改，不覆盖外部编辑、重启或启动新实验。其他身份、唯一安装和镜像挂载复核未变，v2审计已保存，`glm-p1k`已删除。后续先确认外部变更归属与版本，再决定回归及Decode主机/设备profiling；以下15:01/14:28为过程历史。

15:01只读进度：[点53](20261022-steady-p1k-phase-baseline-53.md)Prefill与Decode各8预热+3测量已完成且原生证据有效，主要吞吐中位数分别12331.812499（总token）/1155.959926（输出）token/s，测量极差1.1338%/1.6863%，相关P99轮间极差均≤5%。Mixed仍预热，同实例health200，未改MBT/启动参数或发新实验。此为部分入口基线，不是ABR、优化收益或回退漂移改善；监控保持active，待三阶段终态审计。

14:28接续：[点53当前P1K稳态三阶段入口基线](20261022-steady-p1k-phase-baseline-53.md)已唯一派发。正常调参DB写入的显式同实例schema5 gate已通过原生check，保留173/198、86%阈值与原始DB/manifest；5项新绑定和原19+31+26项相关测试通过，另9项失败传播测试通过。MBT/启动参数不变，Prefill 1K/1/C64/N64、Decode 1K/1K/C64/N64、Mixed 1K/1K/C64/N128统一8预热+3测量，先取得稳态事实再选算子/框架候选。`glm-p1k`只读跟进，尚无新性能收益或四场景完成结论；以下14:07绑定缺口为修复前历史。

14:07终态（2026-10-22）：[点52无hook生产路径](20261022-sparse-physical-index-fusion-52.md)原生单次198题/C64 GPQA **173/198＝87.3737% ≥ 86%，分数达标**，两个filter共396行与来源/样本原生复验通过，无补充或best-of。5题触及60K，仅诊断、不另设门槛。服务同实例health200，16worker无hook/TileLang，未见OOM/RPC/非法访问；MBT和启动参数未变。严格manifest仅调参DB SHA由96ce45e2…变605719d9…，故当前绑定incomplete、未签gate；原记录与DB保留，不能把分数达标改报为精度失败，也不伪造当前绑定或自动晋级性能。终态审计完成、`glm-c64-gpqa`已删除。无新稳态性能或提交推送。以下12:18等均为历史。

12:18生产路径验证（2026-10-22）：[点52](20261022-sparse-physical-index-fusion-52.md)已彻底去掉临时MM/vendor/观测hook，直接原脚本默认flagos；原MBT32768和启动参数不变。C64 **64/64**、C1/C8、三16K边界、11/11答案及FULL捕获/多token请求通过，16worker无hook/TileLang，无OOM/非法访问/RPC timeout。服务保持同一实例`2151833:535760459`，新198题/C64/seed42/60K/strict≥86%全量GPQA已唯一启动，分数和gate待定；无补充/best-of、无稳态性能结论，`glm-c64-gpqa`只读跟进。生产DB正常调参写入已记录、未重置。下文11:54准备与11:40临时策略/OFF均为历史。

11:54生产验证接续（2026-10-22）：用户授权[点52](20261022-sparse-physical-index-fusion-52.md)去掉临时MM/观测hook，原MBT/启动脚本不变，验证实际默认flagos路径；当前源码、无API及16卡空闲已核验。新`production-no-mm-02`先重做C64与完整最小回归，全部通过后对同一新实例跑198题/C64全量GPQA，86%门槛，无自动补充/best-of。准备中，尚未派发模型或评测，不与上一轮临时策略结果混同。

11:40终态（2026-10-22）：[点52物理索引OOM修复](20261022-sparse-physical-index-fusion-52.md)已保留FGV通用融合转换和H4前置；原C64/N64的64个唯一请求全部成功，C1/C8、三16K边界、11/11明确答案和FULL 11/11捕获/多token请求通过，未见OOM/非法访问/RPC timeout。实际16worker命中`32768×2176`，输出272MiB+128KiB长度；旧一个同尺寸int64中间量即544MiB。CPU420/FGV设备145/原cache设备2/benchmark4通过，大shape微基准峰值下降不当作E2E收益。MBT32768及原启动argv/脚本、vLLM/FG/权重/tokenizer/生产DB不变，完整源码/index/唯一安装/镜像挂载和当前独立审计通过。诊断实例按冻结流程已停止，当前8011 OFF，`glm-oom`已删除，无提交推送。

本轮整模仍沿用MM07显式vendor和临时MM限4诊断hook，后者未安装到库；不能据此声称默认flagos或无hook生产路径已验收。planning52复盘：下一必要项为实际生产执行契约/最小回归→新身份198题正式gate→同配置稳态三阶段checkpoint；尚未自动启动，无当前正式gate/新四场景性能，累计收益未知。下面11:33及此前是过程历史。

11:33回归进度（2026-10-22）：[点52](20261022-sparse-physical-index-fusion-52.md)CPU420、FGV设备145、原cache设备2和benchmark4通过。8198×8320完整转换额外峰值从约3.88GiB降至260.22MiB（逐位一致；非模型总峰值或E2E收益）。原C1/C8、smoke/C8、三16K边界、11/11明确答案及FULL捕获已通过，C64进行中；尚无终态/gate，不提前宣布修复充分。

11:22测试分层恢复（2026-10-22）：[点52](20261022-sparse-physical-index-fusion-52.md)首轮CPU416通过/6失败，原因是旧CPU单测隐式执行了设备专用转换；在任何设备/模型请求前已精确回退。原失败保留，新`validation-recovery-01`只迁移两处原数值断言至真实PPU、隔离四处CPU路由测试依赖，生产kernel和wrapper SHA不变；独立新冻约/DB与控制器已唯一派发，增加两处原case的必要设备阶段，不放宽误差/graph/内存/参数。相同`glm-oom`监控已切新子目录，旧父根终态不用于结束新轮。

11:12接续（2026-10-22）：[点52物理索引融合OOM修复](20261022-sparse-physical-index-fusion-52.md)已冻结并唯一派发：FGV通用稳定压缩kernel直接输出int32，替换公共Plugin辅助函数的多份全尺寸int64中间量；不新增thead模型分支、不改MBT/启动参数。先CPU/设备逐位/动态graph/完整转换峰值检查，全部通过才继续原C1/C8/16K/11答案/C64模型回归。失败精确回退SQL-only/OFF；通过保留修复源码但关闭仅诊断实例，MM外部hook不安装，不自动GPQA/性能。新monitor `glm-oom`每30min只读、不变安静，终态审计后删除；旧点51监控已终结。

10:37终态（2026-10-22）：[点51 MM07](20261021-sparse-mla-small-head-dual-backend-51.md)固定shape三臂通过，但模型未修复完成。原C1/C8、三16K边界、11/11语义与FULL 11/11捕获通过；16worker各22次限4实际命中后，C64仍于物理索引转换`torch.remainder`输出申请544MiB时OOM（TP2仅余220.37MiB，全部16rank记录OOM），HTTP500。本轮不是sample_tokens RPC timeout，不能把新OOM直接归为旧RPC的同一根因；已证实冷搜索耗时，不是充分模型修复。控制器10:23精确恢复SQL-only/OFF，10:37当前全树/index/唯一安装/镜像挂载/权重/生产DB独立审计通过；H4/临时策略不保留，无自动重试、GPQA或性能，终态监控已删除。以下10:16及此前是各时点历史。

10:16只读结果（2026-10-22）：[点51 MM07](20261021-sparse-mla-small-head-dual-backend-51.md)固定22组shape/输入三臂全过FP32 oracle和每角色2次动态graph。原/候选/回退搜索各104/4/104配置，cold-call总和302.076/12.401/302.659秒，证实Default在线冷搜索开销可被该变量控制；这是单PPU诊断，不是稳态端到端或精确RPC请求耗时。模型02已临时应用H4并进入原TP16/FULL启动，尚无C1/C8/16K/语义/C64终态，不能宣布RPC充分修复；最终SQL-only/OFF恢复审计仍待控制器完成。无新模型请求派发或参数变更。

10:04接续（2026-10-22）：[点51 MM07](20261021-sparse-mla-small-head-dual-backend-51.md)固定22组MM shape/相同输入SHA的三臂已唯一派发。v1仅CPU进程退出观测竞态失败、零GPU/模型；v2保留失败证据并修复清理观测，原4项归属测试全过、16卡空闲、SQL-only/OFF预检通过。数值/动态graph/实际同scope命中全过才接续原C1/C8/16K/11答案/C64回归，不自动全量GPQA、稳态性能或部署；原30min monitor已更新同一07并ACTIVE。

09:40恢复核验（2026-10-22）：[点51 MM06](20261021-sparse-mla-small-head-dual-backend-51.md)其实昨晚23:54已结束；当前全树/index/唯一安装/镜像挂载及生产DB审计通过，SQL保留、H4恢复、服务OFF，旧monitor暂停。原策略C8通过237.634s、临时候选通过58.937s、回退300.728s RPC失败；但冷M分别12293/28673/20481+8198，交集为0，不能报严格稳态加速或充分修复。候选16rank实际命中，104→4配置；下一07固定22组shape/输入hash作搜索因果对照，通过才接续原C64及完整最小回归，不自动部署/跑GPQA/性能。下述网关阻塞和06运行中状态均为历史。

03:35核验缺口（2026-10-22）：PPU-13仍返回`no available gateway`。点51 MM06自派发已超过4h计划窗口，但控制器/三臂结果和源码/服务恢复状态均未知，不能推断测试仍在运行或已失败；已一次性提示检查网关访问，无重跑/重启/源码恢复操作，监控保持只读。下段00:06为首次阻塞记录。

00:06跟进受阻（2026-10-22）：[点51 MM06](20261021-sparse-mla-small-head-dual-backend-51.md)连接PPU-13返回`no available gateway`，未取到新原生结果；连接脚本成功退出属假阳性，不能当作已连通。三臂终态/恢复/health目前未核验，最后确认仍为23:37:55 baseline C1通过、C8运行。没有重跑/重启或改库/DB/服务，既有监控保持ACTIVE等待只读续查，不将网关故障记为候选失败或宣称已恢复。

点51接续06进行中（23:33）：[同初始SQL缓存MM策略对照](20261021-sparse-mla-small-head-dual-backend-51.md)。CPU14项、真实PPU四候选各23shape共92项FP32 oracle及共8次动态graph回放通过；最初导入重复注册工具失败保留且已单独恢复。原P4096 C1/C8的baseline/candidate/revert已唯一派发，候选仅临时缩为前4合法配置；MBT/FULL/kernel/key/生产DB不变。role SQL DB起始严格同源，编译cache共享限制保留；尚无模型三臂结论，不自动保留策略/跑GPQA/性能。已有heartbeat只读跟进，终态精确恢复SQL-only/OFF并暂停。

点51接续05只读定位（2026-10-21 23:04）：[MM缓存/搜索机制](20261021-sparse-mla-small-head-dual-backend-51.md)进一步确认，不是缓存反复失效。ConfigCache299→318、BenchmarkCache30631→32671，新增19个winner/2040条标签、删除0；M20480已有11组，M20481→21504、M8198→9216为冷bucket，同N/K/flags/dtype仅改M的11组CPU对照全部命中→未命中。原生Default114候选、合法性裁剪104，与真实逐组104次一致；20个新raw组中19组完整、最后一组64条未出winner。约244.8s只是协议名义预算，非实测性能；充分RPC修复仍需同初始缓存单变量MM策略对照。另发现生成do_bench闭包把20/100与25/50都标custom/-1/-1的协议tag风险，非本次冷bucket直接原因，未修复。本轮零模型/GPU请求、零库/生产DB变更，SQL保留/H4未安装/服务OFF/最终完整审计通过，monitor保持PAUSED。下一优先为生产Default小候选或有界冷miss策略，保留key/合法性及Expanded完整搜索，而非清库、改MBT或盲暖缓存。

点51接续04终态（2026-10-21 22:32）：[SQL修复及RPC取证](20261021-sparse-mla-small-head-dual-backend-51.md)已完成。FGV目标表反射1 runtime/1 test修复保留，10原生测试通过、真实DB1024表63175行全部schema/PK/nullable/行值等价。16worker实际命中修复，C8每rank5次反射仅0.029–0.035s；但P4096/D16 C1成功2.757s后，C8约300.758s再次RPC timeout、8/8 HTTP500，无观察OOM/非法访问。每rank至少995次MM候选benchmark、已记录约129s，实际M20481多组K/N各104次搜索；5/15/30/60/120/240s全16栈在MM调参，180s为index/nonzero/copy。事件触上限，仅下界；充分因果仍需固定缓存单变量MM策略对照，不能称全部300s唯一根因或稳态收益。首错停止，C64/完整最小回归/新GPQA/性能未执行；H4六文件精确恢复，SQL小补丁保留、FGV源aec7a802…，服务OFF/完整审计通过/monitor PAUSED。原失败、工具guard/E2BIG恢复证据保留，无提交推送；下一步优先限制请求内MM搜索而非改MBT/延长RPC。

点51诊断终态（2026-10-21 21:44）：[RPC取证](20261021-sparse-mla-small-head-dual-backend-51.md)完成。原候选P4096/D16单请求HTTP200、48.845s（诊断耗时，非性能）；请求1s和10s全部16 worker落在FGV缓存全库反射，30s全部落在FlagGems PPU MM在线调参。FGV实际SQL方法CPU只读副本对照为1022表/10222 SQL→1表/12 SQL，目标配置等价；此前仅FlagGems另一份实现修过，FGV遗漏确认。但原C64客户端早期RPC超时本轮C1未复现，DB缓存状态也变化，不能称已证明300s全部根因或排除未采样设备/通信问题。01启动退出/02观测guard失败保留，03真实栈/分析与完整恢复审计通过；六文件及全树/index精确恢复pre51，服务OFF，monitor PAUSED。未安装SQL/MM新修复，无新GPQA/gate/性能或提交推送；下一步需单变量修复/对照，候选仍未晋级。下段18:21为原失败终态。

点51终态：[公共Sparse MLA小head与双backend](20261021-sparse-mla-small-head-dual-backend-51.md)候选完成但未保留。421 CPU、11 FGV设备测试、两个真实provider公共adapter/CPU oracle/动态graph通过，无TileLang；SQ20172/TOPK128输出均78.80 MiB，为旧H64的1/16，仅synthetic存储证据。vendor整模FULL capture 11/11、C1/C8/三16K边界/11答案通过，但18:16:38在C64客户端守护早期出现sample_tokens RPC超时→HTTP500，失败实际4096 token/2 running请求，未观察OOM或非法访问，深层原因未知。flagos整模/新GPQA/性能未运行；六文件已精确回退到pre51公共repair08、原stage/index和MBT/FULL/交付脚本不动，服务OFF，不恢复旧PPU模型。18:21:59只读全树/唯一安装/权重/镜像挂载审计通过，monitor PAUSED。补丁及失败证据保留，下步先取原P4096 worker栈，不盲重跑或宣称完整修复/新gate/端到端收益。

点50定位更新（2026-10-21 17:11）：[OOM分析](20261021-pr454-public-path-50.md)确认公共Sparse MLA把TP16后的4 heads物化补至64；SQ20172时Query、输出各1260.75 MiB，有效输出仅78.796875 MiB，切回4-head的view仍保留完整大存储，分配式与原生1.23 GiB OOM吻合。该`forward_mqa`与PR454 AST相同，不是KPool/SQL补丁新增。启动最大token profile未执行真实attention，漏掉此路径分配；全峰值/碎片/缓存副本占比仍未知，CPU/meta只证明shape/alias非硬件重现。源码/参数未改、无GPU请求/服务重启或新gate，monitor仍暂停。下一方向为现有FGV算子小head支持及真实工作区预算，不以降MBT掩盖。

点50终态（2026-10-21 16:53）：[公共路径修复](20261021-pr454-public-path-50.md)最小回归通过后，C64全量GPQA仍失败。16:41:05 TP14在FlagGems-vllm Sparse MLA分配输出时OOM（需1.23 GiB、空闲988.65 MiB），继而16:42:47出现RPC超时、服务退出。原生0/198且198题全timeout，不是有效的模型答题精度测量；86%门槛未通过、无新gate，停止性能晋级。只读终态审计确认三库源码/index、唯一安装及镜像挂载/权重/tokenizer/thead/脚本未变，当前8011拒绝连接；未自动重启/回退/重跑或改参数。更深峰值显存来源待定位，证据保留`formal-terminal-audit-v1.json`与原始日志，终态monitor暂停；下述16:37为历史。

点50最新（2026-10-21 16:37）：[公共路径修复](20261021-pr454-public-path-50.md)已在实际安装目录通过完整最小回归。KPool稳定buffer、真实动态graph/428 CPU及FG单表反射/SQL12项回归通过；原FULL C1/C8、P16383/16384/16385各D8、11/11明确答案、16Worker无TileLang及独立只读身份/镜像挂载/唯一安装审计通过。原生PR454公共路径生效，Plugin12变动文件、FGV4、FG两个既有文件；无旧PPU模型路径或临时trace，原参数/脚本/vLLM不变。新身份198题/C64/strict>=86%全量GPQA已唯一派发，尚无分数/gate，不补充替换或复用旧分数；既有heartbeat只读跟进。旧失败/恢复及冷缓存因果限制保留，无新性能或提交推送。

最新21:21 +08：[点49按职责边界去重](20261020-responsibility-preserving-dedup-49.md)已直接修改唯一安装Plugin并保留。只提取FlagGems/reference相同的懒解析闭包，两端工厂/注册策略和vendor、MHC、缓存ABI、worker、processor边界保留；无新增平台判断。3运行文件净减12行，另扩展原测试7项，SCM51→52只新增25行私有helper，不追求文件数。首轮删除工厂导致1项原测试失败、已精确回退；保留入口后原路径复现通过，完整543 CPU通过/4既有跳过，C1/C8/三档16K边界/11答案/FULL_DECODE_ONLY capture及多token回放、最终只读身份/唯一安装/镜像挂载审计通过。当前源1244047d…，原参数8011服务健康，Plugin/FGV各1份editable；未提交推送，无新完整GPQA/性能，旧175/198不改绑。PR既有配套依赖和非PPU/FP8/多模态硬件/当前完整gate缺口仍保留；本轮结束，不自动派发新实验。

最新20:18 +08：[点48 config/processor公共实现复用](20261020-config-processor-consolidation-48.md)已直接修改实际安装Plugin并保留。旧配置269→45行、旧processor868→226行，复用PR454字段/序列化、patchify、归一化、配置加载、主调用和sampler，仅保留旧ABI/像素预算/geometry/提示词差异；公共默认及短视频非空守护不变，无新平台判断。运行代码净减825行，188/188新旧对照、536 CPU通过/4跳过、整模C1/C8/三档16K边界/11答案与FULL_DECODE_ONLY capture/多token回放、最终镜像/挂载/源码/唯一安装审计通过。新源1581bddf…、原参数服务健康，Plugin/FGV仍各1份安装；未提交推送，无新完整GPQA或性能结果，175/198仍只属点46旧源。本轮结束，不自动开启新实验；PR剩余配套依赖及非PPU/FP8/多模态硬件/最终新gate缺口。下文各点“当前源”为当时身份。

已完成一轮：[点47正式PR审查与收敛](20261020-pr-review-consolidation-47.md)。已直接修改实际安装Plugin：删除无消费者的旧BF16 indexer接口及重复INT8覆盖、5个FGV透传改直接注册、移除实验shape日志并补依赖说明；runtime净减428行、SCM50→48项，3个删除文件有精确备份可恢复。CPU511通过/4跳过、固定ruff0.14.0 lint/format、模型C1/C8/三个16K边界/11明确答案、FULL_DECODE_ONLY capture/多token回放和最终只读审计通过；当前源471a65fb…，Plugin/FGV仍各1份安装。未提交推送、无新性能或完整GPQA；点46的175/198只属于旧源，不能改绑。正式PR仍needs_revision：配套FGV依赖、非PPU/公共FP8 CI、多模态配置语义和最终新源gate待补。

已闭环：[点46公共模型/BF16缓存ABI收敛](20261020-shared-model-cache-abi-46.md)。实际安装Plugin模型2492→321行、patch774→162行、缓存ABI176行，净减2252行；CPU498通过/4跳过，整模C1/C8、三个16K边界、11/11明确答案及FULL_DECODE_ONLY capture/多token回放通过。新身份独立全量GPQA198题/C64的strict **175/198＝88.3838% ≥ 86%**，原生gate与18:14最终身份/198唯一题及两filter共396行审计通过，监控已暂停。8题原生timeout标记仅诊断，不改变通过结论、未补充替换或自动重跑。前五轮失败/恢复保留；无新性能收益或非PPU/多模态硬件结论、未提交推送。相对PR454文件数42→50源于公共复用接口/测试，并非新增平台模型副本。

历史17:42 +08进度为187/198；最终原生198/198与新绑定gate见上，不以历史阶段计数代替完整结果。本点停止，不自动开启性能实验；今后正式性能前须重新核验当时身份与gate。

最新2026-10-20 14:51：[点45文件审计与收敛](20261020-multiplatform-architecture-45.md)已直接修改实际安装Plugin：相对PR454 **46→42文件，净减183行**，其中37运行/1YAML/4测试。删除两个冗余BF16 Backend子类及MLA/MoE纯转发模块，直接懒解析现有provider，公共默认与ABI策略不变。实际目录95 CPU、真实provider解析、重复注册及最终只读身份/格式检查通过；删除可恢复，SCM42项可视化。服务未重启/热重载或发推理请求，未提交推送；没有新模型graph/精度/性能结论。仍保留大块不同cache ABI的旧host实现与非等价config/processor，不能称已最小化；下一步需公共模型小适配层与行为回归，不机械合并文件。以下SCM46为历史。

最新2026-10-20 13:41：[点45按用户要求直接修改实际安装源码](20261020-multiplatform-architecture-45.md)已完成，目标仍为容器私有`vllm-plugin-FL-review-20261020-p45-v4`。四路径补丁已应用，真实editable导入及该目录95项CPU/新进程注册检查通过；SCM为46项暂存更改，原有改动保留，删除bootstrap有恢复备份。源码磁盘SHA变为`4165a889…`，服务health200/进程和参数不变，未重启/热重载或发送模型请求，未commit/push。不能据新进程导入通过宣称既有worker已加载新逻辑；当前新磁盘身份尚无模型graph/精度/性能验收。以下“候选未安装/SCM45”属于此前历史。

最新2026-10-20 13:28：[点45继续收敛厂商特判](20261020-multiplatform-architecture-45.md)形成未安装审查候选。通用模型入口删除`thead`判断，由现有dispatch能力声明的缓存ABI选择；未知格式/策略拒绝明确失败，合法FP8保持原路径；删除无调用方`vendor/thead/bootstrap.py`。两运行文件修改、一死文件删除、一测试新增，95项CPU及真实provider元数据/重复注册通过。仍有两种缓存ABI的host实现，不宣称完整合并或跨平台硬件/模型graph通过；原安装、服务和SCM45不变，未提交推送。源码/补丁位置、初始化时序风险与未测项在同一实验文档；下面11:18仍为当前实际运行/审查目录状态。

最新2026-10-20 11:18：[点45 VS Code原生SCM展示](20261020-multiplatform-architecture-45.md)已按用户要求配置。打开容器内实际Plugin目录后，“暂存的更改”可直接查看45个文件相对纯PR454的差异；当前HEAD为`f769696`，index/磁盘仍是完整修复版，`snapshot/glm53-installed-p45-a07f384`保留完整提交。源码逐项不变、服务健康且未重启；未重装、推送或发模型请求。只读审查不要丢弃更改/硬回退，避免修改实际运行的editable源码。下面11:11分支比较方式为此前历史状态。

2026-10-20 11:11：[点45Git分支整理](20261020-multiplatform-architecture-45.md)已完成。已安装Plugin改动提交为本地`a07f384`，当前分支`glm53-multiplatform-worker-fix-p45`；纯PR454基线`baseline/pr454-f769696`和冻结官方main基线`baseline/upstream-main-20261019`保留，可直接git diff查看额外45文件改动。工作区干净，源码字节与原安装manifest逐项一致，服务未切换/重启且health200；未推送、未新增评测或收益。FlagGems-vllm不在本次Git提交范围，仍为原安装副本及未提交修改。

当前（2026-10-20 10:26）：[点45修复版安装与去重](20261020-multiplatform-architecture-45.md)已完成，用户后续安装授权覆盖此前只审查限制。Plugin v4与FlagGems-vllm v3各保留一份editable安装，13个旧私有源码目录已删除，宿主任务目录留有已逐项校验的恢复归档。116项CPU契约、10组PPU设备回归（9组graph各两回放）、模型11/11 capture、C1/C8、16K三边界和11答案通过，独立最终审计通过、8011健康。首轮worker进程Dynamo设置故障与自动回退证据保留，模型边界初始化修复已闭环；不恢复按平台整表切换或generic `thead_*`副本。启动脚本/参数及vLLM/FlagGems/权重未改，未推送，无新全量GPQA gate或性能结果；其他平台仅CPU/mock契约，不宣称硬件通过。

历史（2026-10-19 21:15）：[点44补丁收敛](20261019-minimal-patch-consolidation-44.md)曾安装运行并复核健康。Plugin新增文件38→35、内容8232→7530行（净减702，含注释/测试）；FlagGems-vllm调参YAML无关diff从426行收敛为8行，算子Python不变。75项CPU、41/41选路、graph capture/多token回放、11项明确答案与16K三边界回归通过。该版本现被点45替代，点43/44旧展开源码已归档删除，回退须先恢复归档。下述171/198是点43历史补充口径，不归到点44或45新身份。

17:58最新结论：点43的14题补跑完成，185、194新增答对；统一替换全部14题、保留其余184题后 **171/198＝86.36%≥86%，按用户授权补充口径达标**。原生单轮169/198保留；无best-of，仍有10题60K长度结束，不作为额外门槛。14题/各filter、原prompt/target、生成参数/provenance、精确替换和当前服务身份独立复验通过，health200。未签发新的单次全量gate、未自动继续性能优化，补跑监控已暂停。详见[点43补跑合同与证据](20261019-upstream-migration-43.md)。

历史17:18原生单轮终态：点43新版198题/C64 strict为169/198＝85.35%，低于86%且没有gate，原结果保留；后来按用户授权统一补跑14题后的171/198另行记录，不改写该原生结果。原生396行/两个filter各198唯一题及冻结SHA/provenance/metadata校验通过，失败仅因分数未达标。14题长度结束不额外作门槛。

2026-10-19：[点43上游迁移](20261019-upstream-migration-43.md)已安装运行，模型最小回归通过，用户授权补充后171/198达标；原生单次169/198失败另存。只读对照迁移前原生亦169/198，七题转对、七题转错，不能按同分宣称零回归或锁定算子根因；旧版补充173/198不混入新版。新私有源码为官方Plugin main `a696859` + PR454 `f769696`、官方FlagGems-vllm main `b4d3382`加迁移补丁，保留PPU BF16路径和有效优化，非纯净PR454 PPU验收。MBT/启动参数/交付脚本不变，无新性能测量、未提交推送，旧收益不归属新版本。

2026-10-19 13:19：[点42已闭环，不保留合批候选](20261019-ready-prefill-coalescing-42.md)。日志修复、实际hold/Decode继续命中和最小回归通过，但完整缩减三臂结果不支持端到端收益：Mixed原生比较`failed`，Decode guard `incomplete`。六组各8warmup+3measured全部完成，measured共1152成功0失败（含原baseline复用），没有删轮或改门槛。

| 缩减阶段 | baseline输出 token/s | candidate输出 token/s | revert输出 token/s | 结果 |
| --- | ---: | ---: | ---: | --- |
| Mixed P32768/D128/C64/N64 | 36.007581 | 36.020500 | 36.006874 | 仅+0.035879%，低于+3%；回退吞吐漂移0.001964% |
| Decode P1024/D512/C64/N64 | 1414.056136 | 1365.184691 | 1433.381873 | 候选−3.456118%，P99 TTFT+15.782213%；guard incomplete |

Decode TTFT的B/C/R轮间极差6.623264%/1.539956%/7.100835%；TTFT/TPOT绝对回退漂移5.145070%/5.515713%仍超3%，因此不能说波动/漂移已经解决，也不能把这些含接纳/填充的指标当纯kernel稳定性结论。原Scheduler/源码/参数于13:13恢复，13:18独立审计核对身份、镜像/挂载、graph、最小回归、health200/空闲均通过；仅新增三个SHA匹配文件被移除，修复源码在远端commands可恢复，原dirty及启动脚本不动。监控已暂停，无新gate、未部署或推送。本结果不是正式D1024/N128或四场景验收。

规划Skill复盘已同步state及点42文档：下一优先方向为前端render/IPC接纳细分及稳态合批命中率取证，其次是当前small-Mixed形状的算子完整交易优化；没有新实验启动，不盲扫MBT/预热/等待窗口，也不把点41或micro收益相加。

2026-10-19 12:47：[点42](20261019-ready-prefill-coalescing-42.md)本次只读跟进未执行远端命令：自动权限审核先容量不足、重试又超时。最新远端事实仍为下述12:17记录，不能确认后续回退/恢复进度或当前健康，也不据工具故障判服务失败。未启动新测试、改服务或放宽门槛；monitor保持active，下轮继续只读核验。

2026-10-19 12:17：[点42日志修复接续](20261019-ready-prefill-coalescing-42.md#日志修复与接续logging-recovery-01)candidate Mixed/Decode各8+3已完成、measured共384成功0失败，原生证据复核有效。当前A/B观察如下，**未见显著Mixed收益，Decode TTFT变慢**；candidate波动较小不等于整体通过。revert已ready、最小回归通过并开始Mixed，待收齐后判断回退漂移和完整结果，原门槛/MBT不变、monitor继续。

| 缩减阶段 | baseline输出 token/s | candidate输出 token/s | 变化 | P99 TTFT变化 |
| --- | ---: | ---: | ---: | ---: |
| Mixed P32768/D128/C64/N64 | 36.007581 | 36.020500 | +0.035879%（门槛+3%） | −0.041426% |
| Decode P1024/D512/C64/N64 | 1414.056136 | 1365.184691 | −3.456118% | +15.782213%（守护≤5%） |

candidate Decode TTFT轮间极差1.539956%，原baseline为6.623264%且仍超5%；不据此宣称长期稳定或漂移改善。回退正在测量，尚无比较/guard/completion，不自动部署候选。

2026-10-19 11:47：[点42日志修复接续](20261019-ready-prefill-coalescing-42.md#日志修复与接续logging-recovery-01)candidate最小回归与真实命中已通过：EngineCore记录`waiting=1/running=1/decode_tokens=1/new_prefills=0`并按deadline释放。candidate Mixed完成6/8轮预热（384成功0失败，原生validation/输出SHA有效），第7轮进行中，身份与冻结命令匹配、health200。随后Decode与revert两阶段，原baseline复用、门槛不变；尚无measured或新收益/稳定性结论。原服务将在结束后恢复，monitor跟进中。

2026-10-19 11:15：[点42日志修复接续](20261019-ready-prefill-coalescing-42.md#日志修复与接续logging-recovery-01)已唯一启动。只改logger层级、策略AST不变，15项CPU测试与远端INFO预检通过；复用原baseline、仅补candidate/revert，MBT32768与8+3/5%/3%门槛不变。先做真实Decode继续且new_prefills=0命中探针，未通过不进入性能。候选正在初始化，暂无新收益；旧incomplete与baseline TTFT6.623%缺口保留。结束恢复原配置，monitor已重新启用。

2026-10-19 10:56：[点42](20261019-ready-prefill-coalescing-42.md)以`incomplete`结束。候选最小语义回归通过，但Plugin INFO日志被WARNING级别过滤，激活日志断言误报“scheduler not loaded”，在候选性能采样前停止；实际合批hit仍缺证。candidate/revert没有性能数据，不能判断本次收益、Decode波动改善或回退漂移。原配置/源码已恢复，身份、graph及最小回归审计通过、health200，monitor暂停。仅移除本点新增的三个SHA匹配文件，外部原本可恢复，原有dirty与交付脚本不动。下述baseline数值保留，TTFT极差6.623%仍超5%；下一步是修复命中观测后复用基线继续未跑角色，尚未启动。

2026-10-19 10:47：[点42](20261019-ready-prefill-coalescing-42.md)baseline Mixed/Decode各8+3均完成（measured共384成功0失败），候选已安装并正在启动，revert未跑。原路径基线如下，尚无候选收益或回退漂移结论；Decode TTFT极差6.623%仍超冻结5%，不放宽或删除轮次。

| 点42原路径baseline，3轮measured中位数 | 输出吞吐 token/s | P99 TTFT ms | P99 TPOT ms | P99 ITL ms |
| --- | ---: | ---: | ---: | ---: |
| Mixed P32768/D128/C64/N64 | 36.007581 | 222728.086 | 1712.696 | 3498.246 |
| Decode P1024/D512/C64/N64 | 1414.056136 | 5251.007 | 43.466 | 36.070 |

2026-10-19 10:20：[点42](20261019-ready-prefill-coalescing-42.md)只读跟进：baseline Mixed已完成6/8轮预热（384成功、0失败，原生输出/validation SHA通过），第7轮进行中，实例与控制器身份匹配、health200。尚无measured或candidate/revert结果，不宣称收益，继续既有三臂。

2026-10-19 09:55：[点42有界Prefill合批](20261019-ready-prefill-coalescing-42.md)候选与14项CPU单测完成，原生dry-run及隔离校验通过，09:47已唯一启动三臂控制器。baseline已ready，graph/C1/C8/边界/迟到/取消最小回归通过，当前Mixed预热中，尚无新性能数值。MBT32768/maxseq64/threshold0不变，已有Decode继续执行时给晚到Prefill最多100ms/8步合批窗口；各臂Mixed/Decode均8+3。原5%波动/守护、3%回退漂移门槛不变；完成后恢复原配置，30分钟monitor只通知实质变化。规划复盘已写入state，点41结果不与本轮相加。

2026-10-18 23:18：[点41逐step最终结论](20261018-prefill-quantum-41.md#逐step最终结论2318)完成：**前端接纳/render时序触发，异步batch提前排定与step边界接纳放大，额外含Prefill step及不同shape兑现延迟；不是已证明的单算子或稳态Decode随机失速。** 三轮低开销诊断含Prefill step数5/3/4，P99 TTFT6380.672/4932.309/6030.044ms，后段Decode step中位数34.774/34.736/34.595ms；16/16 rank trace有效。晚到2题提交→scheduler接纳最长约2.349s，额外2110-token Mixed step约816ms执行跨度。不同seed与探针开销不支持精确因果占比，首次小shape/JIT成本仍未孤立。6轮384成功0失败，原配置已恢复健康并完成最小回归/身份审计；源码和启动脚本未改、没有新优化或gate。原Decode守护incomplete、Mixed缩减+5.3491%结论保持。下一方向为有界Prefill合批/晚到接纳验证，尚未实施。

2026-10-18 22:58：[点41逐step取证](20261018-prefill-quantum-41.md)按用户追加要求继续，冻结P1024/D512/C64/N64的2预热+3低开销诊断+1前12step设备trace，要求16rank和HTTP→接纳→调度shape→执行关联。两次准备检查分别因诊断PYTHONPATH及profiler JSON键序比较问题在采样前终止，均保留incomplete且原配置已恢复、minimal通过，无native请求/trace结果。v4只修复编排，已用保存runtime及四类反例验证；当前准备唯一03目录采样，不改模型源码、交付脚本或原guard，尚无新的归因结论。

2026-10-18 22:24：[点41 Decode离线诊断](20261018-prefill-quantum-41.md#decode波动诊断2026-10-18-2224离线完成)完成，33轮原生逐请求证据全部核验。**漂移主要落在每次突发请求的批次填充/Prefill接纳阶段，并非已证实的稳态Decode算子不稳定，也没有发现原生计时公式错误。** 基线→回退批次23.637498→22.942196s，最后首token时间5.816413→5.130791s，而共同已接纳窗口平均ITL34.921101→34.935963ms（仅+0.04256%）；2073个>200ms间隔全部始于批次尚未填满时。TTFT/TPOT包含该真实波动，不能作为纯Decode指标；具体前端/调度/shape成本待逐step证据，未启动新流量。原guard仍incomplete，不追认通过；Mixed+5.3491%保持原边界，候选未部署，原配置健康且未改，监控保持暂停。下一步是单轮细粒度接纳/调度归因，而不是盲目加warmup或重跑整套三臂。

2026-10-18 21:50：[点41新8+3完整三臂](20261018-prefill-quantum-41.md)已完成并审计。**Mixed P32768/D128/C64/N64端到端增量收益已确认：输出吞吐36.017673→37.944278→36.014891 token/s（B/C/R），候选+5.3491%，P99 TTFT/TPOT/ITL分别降低5.5989%/5.2141%/0.6247%，原生比较passed。** Decode吞吐B/C/R为1386.271921/1403.493620/1428.285235，但尾延迟波动和回退漂移超冻结范围，guard为incomplete；不能声称纯Decode改善或整体验收通过。六组测量全部完成，measured共1152成功、0失败；原服务参数/源码/权重/环境恢复核验一致且健康，候选未部署、脚本未改、监控暂停。本收益只属于缩减Mixed场景，不是D1024/N128或四场景正式验收，也不与Prefill/micro加速比相加。下一步只记录Decode波动离线定位、KPool完整交易融合探针和点40累计成本验证，均未启动。

2026-10-18 21:00：[点41新8+3轮](20261018-prefill-quantum-41.md)baseline/candidate两阶段均已完成，Mixed吞吐A/B为36.017673→37.944278 token/s（约+5.35%，仅观察）；revert已通过最小回归且开始Mixed预热，服务健康。candidate Decode P99 TTFT极差8.21213%仍超冻结5%，结果原样保留；等待回退和恢复后分别给出Mixed比较与Decode守护，不提前签发完整结论。

2026-10-18 19:54：[点41新8+3轮](20261018-prefill-quantum-41.md)baseline Mixed/Decode均完成，measured输出吞吐中位数36.017673/1386.271921 token/s，各192成功、0失败；候选已通过最小回归并开始Mixed，服务健康。Mixed基线稳定，但Decode measured P99 TTFT/TPOT极差13.83137%/8.88648%仍超冻结5%，全部轮次保留。继续测齐三臂并分别判定Mixed收益、Decode守护，暂无新收益结论。

2026-10-18 19:24：[点41新8+3三臂重测](20261018-prefill-quantum-41.md)基线已通过最小回归、服务健康；Mixed完成6/8轮warmup，尚未进入measured，暂无新收益结论。继续已启动控制器，未修改规则或重复实验。

2026-10-18 18:53：按用户明确要求，[点41](20261018-prefill-quantum-41.md)新一轮完整Mixed/Decode A/B/R已启动。三角色统一**8轮预热+3轮测量**，末3预热稳态准入，既有5%守护/波动和3%回退漂移门槛不变。每角色先Mixed再Decode，阶段独立留证；仅某阶段原生预热不稳定时继续另一个预声明阶段，不强行生成失败阶段measured。旧轮全部保留，不拼接旧结果；新轮暂无收益判定，脚本/源码未改，结束恢复原参数，监控已重新启用。

2026-10-18 18:42：[点41](20261018-prefill-quantum-41.md)本轮以`incomplete`闭环，候选未保留、原配置已恢复且健康，监控已暂停。已完成的同配置A/B中，Mixed `P32768/D128/C64/N64`输出吞吐35.991754→37.924562 token/s（+5.3701%），P99 TTFT-5.5992%、TPOT-5.2321%；Decode吞吐1347.292176→1435.592308（+6.5539%）。但回退Decode预热极差7.49696%超过冻结5%，未进入measured且Mixed回退未执行；baseline Decode尾延迟稳定性也有缺口。因此仅保留改善信号，**不能宣称已确认端到端收益或正式场景通过**。不挑轮、不补造回退、不自动重跑，交付脚本未改。下一轮先独立冻结测量稳定性契约，其次KPool完整交易融合探针，均未启动。

2026-10-18 16:23：[点41](20261018-prefill-quantum-41.md)的Decode基线已完成，输出吞吐中位数1347.292 token/s；Mixed基线完成3轮warmup，candidate/revert尚未测。服务健康。Decode measured P99 TTFT轮间极差约9.60%超过预冻结5%，该稳定性缺口原样保留，不能签发完整守护通过；继续已启动的Mixed取证与最终恢复，不改采样、不重跑。当前仍无新增Mixed端到端收益结论。

2026-10-18 16:02：[固定MBT的长Prefill请求配额16384（点41）](20261018-prefill-quantum-41.md)三臂完成：Prefill输出吞吐0.582195→0.607922→0.582129 token/s，候选+4.4189%，P99 TTFT-4.6795%、TPOT/ITL+0.4790%。原生比较因缺cache preparation描述保持incomplete；只补既有运行事实的独立恢复报告通过，原始采样/阈值/manifest未改。该结果仅支持Prefill晋级，不是Mixed收益。用户原配置已恢复核验后，新增Mixed/Decode同配置A/B/R现已启动；完成后仍恢复原参数，暂不修改交付脚本。

2026-10-18：[P32K阶段基线（点39）](20261018-p32k-phase-refresh-39.md)三个缩减场景全部完成，measured输出吞吐中位数分别为Prefill 0.582271、Decode 1355.755、Mixed 36.017783 token/s，各自workload见实验文档，不能跨场景比较加速比。MBT32768/maxseq64保持。
[CPU元数据消除同步候选（点40）](20261018-prefill-host-sync-40.md)隔离设备对照通过，每次host判断约省19.514µs，但尚未证明模型关键路径收益，候选暂存未安装。
下一算子候选为KPool gather/compress融合，尚未实现；须先验证完整交易、数值与graph，再决定是否进入服务。规划复盘已据点40的小量级探针与点41的Prefill信号重新排序，不叠加孤立加速比。

2026-10-18最新：[10道60K长度结束题目补跑](acc-20261018-gpqa-c64.md)已完成，新增4题正确；保留其他188题后，合并strict为**173/198 = 87.37%**，达到**86%**门槛。6题仍触及长度上限，不作为附加精度门槛。服务身份核验一致，监控已停用。

2026-10-18首轮记录：[用户当前服务的64并发全量GPQA](acc-20261018-gpqa-c64.md)完整结束。
198题、最大输出60K，strict为**169/198 = 85.35%**，低于86%门槛，正式精度失败，无gate。
原生证据和当前服务身份核验有效；10题出现60K长度结束/超时占位，尚未定位根因。
服务保持健康，监控已停用；不将历史32并发173/198作为当前64并发结果。

最新结果（2026-09-24）：按用户要求，[点38](20260924-p32k-align-direct-38.md)
已将 Plugin MoE align 窄路由重新接入 FlagGems-vllm；adapter 数值/graph、
C1/C8 均通过。当前实例的 198 题全量 GPQA strict 为 **173/198 =
0.873737**，高于冻结门槛 0.86，正式 gate 已签发。当前服务仍运行，
候选源码未漂移。点36同一候选在 D128 的 +0.0822% 仍低于原性能 +3%
门槛；本轮未重新测性能，不能宣称端到端收益或 P32K/D1024 完成。

最新状态（2026-09-23）：[点36](20260923-p32k-align-dispatch-36.md)已
查明 MoE align 候选不命中的原因：服务 Decode 为无 EP map、
`ignore_invalid_experts=False`，形状 M16–32/BM16、M40–64/BM32。
修正窄 Plugin 路由后，16/16 rank 均命中新 stage2，完整 align 调用快
3.68–3.91×；但 P32768/D128/C64/N128 同配置无 profiler A/B/R 的
输出吞吐仅 36.17765→36.20737 tok/s（+0.0822%），低于预冻结 +3%
门槛，已回退 Plugin 路由，不记作端到端收益。

[点37](20260923-p32k-prefill-quanta-37.md)保持 MBT32768 不变，尝试
`long_prefill_token_threshold=8192`。P32768/D32/C64/N64 基线两轮
measured 输出吞吐 9.159345/9.162076 tok/s；候选 2 轮 warmup 的吞吐
离散 11.223%，超过预冻结 5% 稳态准入，runner 在 measured 前停止。
边界与 C1/C8 正确性通过，但性能为 `incomplete`，不能据候选 warmup
判断收益。阈值已回退为 0；回退服务健康，代码、模型、MBT、graph、
前缀缓存配置与基线一致，8191/8192/8193-token 输出逐项相同。
P32K/D1024 正式场景仍未关闭，当前没有新增可保留的端到端收益。

`planning_review_p32k_06` 将下一步定为先只读审计 partial-prefill
并发和真实 scheduler admission，再决定是否值得冻结新的单变量 Mixed
A/B/R；次选精确 shape 的 MQA logits + row-range Top-K 完整交易
microbenchmark，须先证明至少 1.25× 且 graph/数值正确，再考虑服务验证。
点33 FlagGems-vllm 实验代码仍安装但原 Plugin 路径未命中；当前保留组合
仍是先前算子改动加 MBT32768。没有同身份四正式场景 anchor→当前组合
累计验收，也没有本次重启/配置后的新正式精度绑定。

P16K 算子层继续固定MBT32768推进。[点20](20260921-p16k-operator-20.md)的MQA有效区间原型因非对齐密集反例退化30.30%未晋级；[点21](20260921-p16k-sparse-mla-out-buffer-21.md)的thead vendor Sparse MLA `out=`复用在三个shape只有0.999978×–1.000507×，也未晋级。[点22](20260921-p16k-moe-live-shape-22.md)发现新主导`M32768`：GEMM2组合配置的源码命中微基准为1.072917×，但P16K/D128 fresh A/B/R只有`+0.0198%`输出吞吐，因此已拒绝并完整回退。[点23](20260922-p16k-moe-transaction-upper-bound-23.md)进一步无歧义分解5040次完整MoE调用：无限消除全部非GEMM成本的完整采样窗口上限仅2.3367%；再把点22加速不现实地套到所有GEMM2 shape，合计仍只有2.9878%，低于3%，故按冻结条件停止且没有改源码。[点24](20260922-p16k-mbt49152-24.md)完成fresh 6+3×3：原始measured显示吞吐仅+1.7486%、ITL恶化46.70%，低于3%而拒绝；冻结比较契约漏声明两个manifest镜像路径，正式回执按`incomplete`保留，没有伪造修复。交付仍保留MBT32768。[点25](20260922-p16k-sparse-mla-call-boundary-25.md)确认Sparse MLA的可见CPU调用边界完整采样上限仅0.3840%，剩余大头是generic更慢的vendor kernel黑盒，已停止。`planning_review_p16k_08`据此结束P16K候选探索。[点26](20260922-p32k-scenario-entry-baseline-26.md)的P32K入口因首轮冷态导致warmup离散8.685%而未进入measured；[点27](20260922-p32k-baseline-recovery-27.md)完成6轮warmup后，第4–6轮离散3.3232%，仅超过3%门禁，仍按冻结契约失败保留且未进入measured。[点28](20260922-p32k-baseline-recovery-28.md)以事前冻结的5%长prompt可用性容差重建fresh 6+3：稳态warmup与measured离散分别仅0.04218%和0.04045%，1152/1152请求成功，建立当前保留组合的P32K/D128入口基线36.1742 tok/s。[点29](20260922-p32k-phase-profile-29.md)完成16-rank分阶段采集：1 Prefill、63个每波只admission 1个新请求的Mixed、56 Decode；Mixed主要是Sparse MLA 27.09%、fused MoE 17.58%、MQA 13.11%和large-M GEMM 10.52%。[点30](20260922-p32k-mbt65536-topology-30.md)证明MBT65536在32个Mixed marker中有31个每波admission 2个新请求，但1轮profiler-off没有同workload对照，不构成收益证据；候选未写入交付脚本，仍保留MBT32768。服务已停止，当前按用户要求暂停；恢复时先做同workload MBT32768→65536→32768 A/B/R。当前无新增可保留端到端收益；点19完整workload数字为performance-only测量，不代表新身份下的正式精度/四场景验收。
P16K 算子层继续固定MBT32768推进。[点20](20260921-p16k-operator-20.md)的MQA有效区间原型因非对齐密集反例退化30.30%未晋级；[点21](20260921-p16k-sparse-mla-out-buffer-21.md)的thead vendor Sparse MLA `out=`复用在三个shape只有0.999978×–1.000507×，也未晋级。[点22](20260921-p16k-moe-live-shape-22.md)发现新主导`M32768`：GEMM2组合配置的源码命中微基准为1.072917×，但P16K/D128 fresh A/B/R只有`+0.0198%`输出吞吐，因此已拒绝并完整回退。[点23](20260922-p16k-moe-transaction-upper-bound-23.md)进一步无歧义分解5040次完整MoE调用：无限消除全部非GEMM成本的完整采样窗口上限仅2.3367%；再把点22加速不现实地套到所有GEMM2 shape，合计仍只有2.9878%，低于3%，故按冻结条件停止且没有改源码。[点24](20260922-p16k-mbt49152-24.md)完成fresh 6+3×3：原始measured显示吞吐仅+1.7486%、ITL恶化46.70%，低于3%而拒绝；冻结比较契约漏声明两个manifest镜像路径，正式回执按`incomplete`保留，没有伪造修复。交付仍保留MBT32768。[点25](20260922-p16k-sparse-mla-call-boundary-25.md)确认Sparse MLA的可见CPU调用边界完整采样上限仅0.3840%，剩余大头是generic更慢的vendor kernel黑盒，已停止。`planning_review_p16k_08`据此结束P16K候选探索。[点26](20260922-p32k-scenario-entry-baseline-26.md)的P32K入口因首轮冷态导致warmup离散8.685%而未进入measured；[点27](20260922-p32k-baseline-recovery-27.md)完成6轮warmup后，第4–6轮离散3.3232%，仅超过3%门禁，仍按冻结契约失败保留且未进入measured。[点28](20260922-p32k-baseline-recovery-28.md)以事前冻结的5%长prompt可用性容差重建fresh 6+3：稳态warmup与measured离散分别仅0.04218%和0.04045%，1152/1152请求成功，建立当前保留组合的P32K/D128入口基线36.1742 tok/s。[点29](20260922-p32k-phase-profile-29.md)完成16-rank分阶段采集：1 Prefill、63个每波只admission 1个新请求的Mixed、56 Decode；Mixed主要是Sparse MLA 27.09%、fused MoE 17.58%、MQA 13.11%和large-M GEMM 10.52%。[点30](20260922-p32k-mbt65536-topology-30.md)证明MBT65536在32个Mixed marker中有31个每波admission 2个新请求，但1轮profiler-off没有同workload对照，不构成收益证据；候选未写入交付脚本，仍保留MBT32768。服务已停止，当前按用户要求暂停。`planning_review_p32k_02`将下一算子方向排序为：先对H4 Sparse MLA增加BH4小head tile并直接挑战vendor，其次研究MQA logits与row-range Top-K融合，最后只在P32K MoE完整交易上界超门槛时才开发新kernel。恢复时先做算子点31，不与MBT65536 A/B/R混测。当前无新增可保留端到端收益；点19完整workload数字为performance-only测量，不代表新身份下的正式精度/四场景验收。

结构化事实以 [state.yml](state.yml) 为准。以下回顾按固定四场景
P1K→P4K→P16K→P32K 顺序推进的历史过程；点30后曾按用户要求暂停，
当前服务与最新诊断状态见页首。2026-09-19 已完成
`M<=32/E=288/H=4096/I=128/topk=8` fused-MoE GEMM2 小矩阵特化：
多 shape/多 seed 微基准、数值、graph 和 P1K targeted A/B/R 均完成。
候选源码已保留，未提交、未推送。用户随后把总输出吞吐设为主指标并接受
`max_num_seqs=64`。当前已完成 max64 的 16-rank 分阶段 profile，并为实际
`M=64` Decode GEMM2 增加严格限域配置；P1K 同配置端到端吞吐提升
18.447%，候选已保留。随后完成了保留组合的 16-rank reprofile、M64 GEMM1
扫描和 `max_num_batched_tokens=32768` 探针；后两者均未晋级，当前最优组合
不变。P4K 首次入口基线因首轮冷态导致 20.418% 预热离散而在 measured 前停止，
稳态 baseline recovery 与 Prefill/Decode/Mixed profiling 已完成。基于 P4K
Mixed 的四请求 admission 证据完成 token budget 32768 的 6+3 实验：吞吐仅
+1.095%，低于 +3% 门槛，已拒绝并保持 16384。随后已逐项审计
Sparse MLA、large-M fused MoE、CPU 同步、MQA、PCCL Simple、mHC、大 M
native GEMM、KDA forward、request-index 转换和 MoE sum provider，均未产生
可保留的 P4K 端到端收益。其中 GEMM 对照覆盖了 59.5% 的已映射
时间，FlagGems 加权慢 19.3%；最后的 thead MoE sum 在三组精确 shape
也只有当前通用实现的 0.984×–0.989×。现已切换到 P16K，先建立当前
保留组合的入口基线和 Prefill/Decode/Mixed 证据。P16K 首次
入口因首轮冷态导致 14.331% 预热离散，稳态恢复已完成：输出吞吐
中位数 434.205 tok/s，measured 离散 0.156%，768/768 请求成功。
分阶段归因也已完成：1 Prefill、63 Mixed、56 Decode marker，Mixed 每波
只 admission 1 个 16K 新请求。token budget 16384→32768 已通过
D128 里程碑和完整 `P16384/D1024/C64/N128` candidate/revert：候选
474.526 tok/s，较冻结基线 434.205 tok/s 提升 9.286%，回退漂移
+0.267%，七项门禁全部通过。TTFT/TPOT/E2E 分别改善
11.520%/8.471%/12.399%，但 P99 ITL 劣化 75.297%，是保留候选的
明确取舍。交付脚本已改为 MBT32768。P32K的D128稳态入口基线、
16-rank分阶段profile和MBT65536拓扑探针均已完成；MBT65536未经同配置
A/B/R，所以未保留。服务已停止。
尚未进行四场景最终验收。

## 当前服务

- 最近服务级运行是用户 2026-09-23 的四场景端到端测试，三轮共
  1536/1536 请求成功。读取结果时服务仍运行、8011 监听；无 point33 候选
  align kernel 命中证据，也无同配置 A/B/R，因此不作该补丁收益结论。
- 状态：M<=32 与 exact-M64 GEMM2 候选仍保留在 FlagGems-vllm 工作树；
  P16K 通过的 MBT32768 已写入交付脚本，其他失败候选未写入。
- 关键配置：TP16、BF16、`max_num_batched_tokens=32768`、
  `max_model_len=80000`、`max_num_seqs=64`、`FULL_DECODE_ONLY`、前缀缓存关闭。
- 最后健康运行时前缀缓存内外部 query/hit 全为 0。
- FlagGems DB SHA-256：`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`；
  三个有效角色测量期间不变，WAL 均为 0 字节。

## 2026-09-18 精度评测中途退出定位

根因已确认为 `FlagGems-vllm` 的
`_fp8_fp4_mqa_logits_kernel` 在新 shape 上同步在线 autotune，不是 OOM、
`/dev/shm` 耗尽、PPU ECC 错误或主机内核故障。崩溃迭代的 scheduler 记录
`new_prompt_tokens=2901`，新建的 MQA benchmark 表键恰好是
`M=2901,N=725,H=32,D=128`；它仅写入前 5 个候选后，vLLM 的
`sample_tokens` RPC 超过默认 300 秒，EngineCore 和 API server 随后退出。

实际运行时打印证实 `runtime.get_tuned_config("fp8_fp4_mqa_logits")`
返回 144 个候选，而迁移到 `FlagGems-vllm` thead YAML 的预期配置只有
1 个。原因是算子迁移后仍使用 `from flag_gems import runtime`，因此
不会读取 `FlagGems-vllm` 中的固定 thead 配置。这也使原先“新 shape
从 144 组收敛为单配置”的优化在仓库归位后实际失效。

热缓存对照也已完成：同一组 C8 请求首次约 133.87 秒，立即复跑只用
1.617 秒，8/8 请求全部 HTTP 200，复跑前后 DB SHA、大小和 mtime 均未变化。
证据保存在远端
`diagnostics/accuracy-health-rpc-timeout-20260918-01/`，诊断命令保存在
`commands/diagnose-accuracy-hang-20260918/`。精度 gate 仍按用户指定的
`172/198=0.868686 >= 0.86` 保持通过；本事件属于输出健康问题，不改变分数结论。

修复以 FlagGems-vllm `9117ae5` 为基线实施：
`fp8_fp4_mqa_logits.py` 改为从 `flaggems_vllm.runtime` 读取配置，并新增测试
直接断言实际 tuner config 与包内 runtime 一致；thead 上确认唯一配置为
`BLOCK_M=4/BLOCK_N=64/HEAD_BLOCK=16/warps=4/ctas=1/stages=2`。
完整模块测试为 `2 passed, 20 skipped`，跳过项是既有 DeepGEMM/FP8 reference
依赖。直接算子验证覆盖非对齐 `M17/N73`、原故障 `M2901/N725` 和 graph
capture/两次 replay，最大绝对误差不超过 `3.815e-6`。

服务级验证用 32 请求构造总 prompt token 精确为 2901 的批次：首次和立即复跑
均为 32/32 HTTP 200，复跑耗时 1.18455 秒，EngineCore 保持健康。首次运行时
整库 DB 因其他已有 tuner 写入而变化，但 MQA 对应中断 benchmark/config 表均未
新增行；第二次全库 DB 也保持不变。修复证据位于远端
`diagnostics/accuracy-health-rpc-timeout-20260918-01/mqa-fix-validation-01/`，
SHA 清单已校验。两文件修复已提交为 `f7443e7` 并 fast-forward 推送到
`ZenithJoyH/FlagGems-vllm: support-glm5.3-flash`，远端 HEAD 已独立核验。
本次没有重跑 198 题正式精度；既有 score-only gate 继续有效。

2026-09-21 已把
`/mnt/nfs/users/jinghao/glm5.3-flash/start-model-opt.sh` 更新为最新交付分支专用
启动脚本，SHA-256 为
`c9dc6073aa1ee0455fb5df4f8848c3827a09f1a60c490f4c53133fb24ec4c02b`。
脚本保留 `0.0.0.0:8011`、TP16、BF16、`max_num_batched_tokens=32768`、
`gpu_memory_utilization=0.90`、`glm45` reasoning parser、前缀缓存关闭和
`FULL_DECODE_ONLY`，并把 `max_num_seqs` 固定为 64；`max_model_len=80000`
已在完整 P16K candidate/revert 中健康运行。应用户要求，脚本保持精简，
只保留 PPU 运行环境、
FlagGems DB、旧实验环境变量清理和核心 `vllm serve` 参数；
不再包含 revision 检查、帮助函数、`--check`、PID 管理或 Python 导入检查。
本次 P16K 仅将 MBT16384 改为 MBT32768，原脚本和 diff 保存在远端
`full-p16k-d1024-retry-01/delivery-adoption/`。

`FlagGems-vllm` 已在优化容器中切换至 `f7443e7`，并从
`/workspace/e2e-opt/glm53-20260911/FlagGems-vllm` 完成 editable 安装。
在显式清空 `PYTHONPATH` 后，`flaggems_vllm`、`flag_gems` 和 `vllm_fl`
均能从各自源码目录正确导入，所需 FlagGems-vllm 公共导出验证通过。因此启动脚本已删除
`PYTHONPATH` 设置。

容器中的三个运行工作树仍绑定到 Plugin `95b04f7`、FlagGems
`9c9bff3` 和 FlagGems-vllm `f7443e7`。FlagGems 保持 clean；Plugin 保留 graph-safe
reference lazy import 及 thead GEMM 稳定性黑名单，FlagGems-vllm 保留
M<=32 与 exact-M64 GEMM2 候选及其单测，因此后两个工作树为预期的未提交状态。
当时服务已停止，8011 关闭；最新运行状态见页首。
旧脚本和安装命令保存在远端
`commands/update-start-script-20260918/`，未创建本地 `history/` 目录。

## Git 提交状态

`vllm-plugin-FL` 原始优化按优化点拆分为 5 个 commit，随后增加 4 个
跨仓库归位 commit：

| Commit | 优化点 |
|---|---|
| `85302a7` | `index` FlagGems 黑名单 |
| `dbb0e67` | vendor sparse MLA 与 layout fallback |
| `062c06f` | 长 Prefill causal-conv native 路由 |
| `ef19fd9` | 长 Prefill Chunk KDA vendor 路由 |
| `96eb1bf` | 大 M BF16 MoE 分阶段配置 |
| `c8ce8b7` | causal-conv 实现迁出 Plugin，改从 FlagGems-vllm 延迟导入 |
| `11b2285` | Chunk KDA 实现迁出 Plugin，改从 FlagGems-vllm 延迟导入 |
| `cb371ec` | MQA 与 fused-MoE launcher 改从 FlagGems-vllm 公共 API 导入 |
| `95b04f7` | 其余 GLM serving 非 ATen 算子统一改从 FlagGems-vllm 导入 |

2026-09-15 曾在 `FlagGems` 支持分支保留 `4a3cba0` day-0 kernels 和
`fec9807` MQA 配置。2026-09-18 完成全量归位后，这两个模型专用提交均已从
FlagGems `support-glm5.3-flash` 移除；fork `master` 与支持分支现在都指向
最新上游 `9c9bff3`，相对主线不再有模型专用 commit。Plugin 支持分支远端
HEAD 为 `95b04f7`，三个远端 ref 均经 `git ls-remote` 核验。
远端容器因缺少 HTTPS 凭据未产生推送，随后通过校验一致的 Git bundle 和本机
GitHub SSH 身份完成交付。实际脚本归档在远端任务目录的
`commands/{push-source-branches-20260915,migrate-flaggems-vllm-20260918}/`。

2026-09-18 又将上述 vLLM 专用 MQA 配置及本任务新增的非 ATen 算子迁移到
`ZenithJoyH/FlagGems-vllm` 新分支 `support-glm5.3-flash`。该仓库已经包含
`fp8_fp4_mqa_logits` 的实现、测试和 benchmark，因此 `9eda5fb` 只增加 thead
固定调优配置；后续 `00fe8bf`、`557efee`、`27160fc` 分别承载
causal-conv、Chunk KDA 和 thead fused-MoE launcher 的公共导出；
`37ea002`、`ff43ce8`、`9117ae5` 又分别迁入 sparse-indexer serving ops、
recurrent sequence ops 和 sparse-MLA small-head 支持。分支基于 fork 的
最新 `main@6e7ac61`，远端 HEAD 已核验。fork 主分支先从 `e15ed30`
纯 fast-forward 29 个上游提交，新分支随后通过带精确租约的更新重放到最新主线，
本次再以 `f7443e7` 修复 MQA runtime 配置来源；当前比 `main` 多 8 个提交，
远端 HEAD 为 `f7443e7`。

Plugin 已删除 causal-conv 与 Chunk KDA 的本地实现，并统一通过
`flaggems_vllm` 公共 API 延迟导入 causal-conv、Chunk KDA、MQA、fused-MoE、
graph-safe BF16 MQA、BF16 cache gather、indexer pool、prefill tail、kpool、
causal-conv update、recurrent KDA 和 safe gate；原
`VLLM_FL_PPU_MOE_STAGE_CONFIG` 逻辑也已从交付分支删除。
最终隔离验证使用不含旧模型提交的最新 FlagGems `9c9bff3`，公共导出、Plugin
import/dispatch 均通过，FlagGems-vllm 测试 23/23、Plugin 聚焦测试 11/11
通过。此前 MQA focused pytest 收集 20 个用例，
因目标环境缺少其要求的 vLLM DeepGEMM/FP8 reference 全部跳过。最后验证实例使用
与 `FlagGems-vllm@f7443e7` 内容一致的工作树；本次事件表明上述测试没有覆盖 MQA 迁移后的
runtime tune-config 来源。

## P1K 稳定场景入口基线

| 场景 | 状态 | 预热离散 | 输出吞吐中位数 | P99 TTFT 中位数 | P99 TPOT 中位数 |
|---|---|---:|---:|---:|---:|
| P1024/D1024/C64/N128 | `complete` | 1.014% | 770.006 tok/s | 45.254 s | 41.335 ms |

这是“已保留组合 + 预热 DB”的 scenario-entry baseline，不是未优化
原路径 anchor，也不支持累计加速声明。

## 优化点索引与决策摘要

每个有结论的优化点使用一份同 ID Markdown。profiling、reprofile 和运行轮次作为
对应优化点的证据写入单点文档，不创建过程目录。

| ID / 文档 | 优化方向 | 场景 / 阶段 | 主要变量 | 性能效果 | 正确性 | 决定 |
|---|---|---|---|---|---|---|
| [20261022-steady-decode-mixed-profile-55](20261022-steady-decode-mixed-profile-55.md) | 主机/算子/通信归因 | P1K / Decode；Mixed未跑 | profiler-only，原参数已恢复 | Decode16rank局部MoE/BMM/MLA/PCCL线索；frontend缺失，incomplete，无新收益 | 原173/198保留；恢复完整回归通过，重启+DB更新绑定缺口保留 | 原服务恢复/当前审计通过，监控删除，无自动补采/候选 |
| [20260911-index-op-blacklist](20260911-index-op-blacklist.md) | index 路由 | 通用 / Prefill、Mixed | thead blacklist | 无隔离 A/B；降低调优风险 | 后续服务与精度通过 | 保留 |
| [20260911-mqa-thead-fixed-config](20260911-mqa-thead-fixed-config.md) | MQA 冷 shape 稳定性 | Sparse MQA / Prefill、Mixed | 144 配置→1 配置 | 消除 300s RPC timeout；不声明稳态吞吐 | 故障 shape、graph、32/32 服务通过 | 保留、已推送 |
| [20260911-sparse-mla-native](20260911-sparse-mla-native.md) | vendor Sparse MLA | 三个诊断场景 / Prefill、Mixed | backend 路由 | +1.816%～+4.840% | 服务与 fallback 通过 | 保留 |
| [20260911-causal-conv-native-checkpoint-02](20260911-causal-conv-native-checkpoint-02.md) | causal-conv 路由 | 三个诊断场景 / Prefill、Mixed | thead adaptive backend | +0.292%～+14.991% | 服务通过 | 保留、已推送 |
| [20260911-mqa-logits-reference](20260911-mqa-logits-reference.md) | MQA backend 对照 | 长 Prefill | reference 实现 | OOM，无有效性能结果 | 未形成晋级证据 | 失败 |
| [20260911-kda-block-config](20260911-kda-block-config.md) | KDA kernel 调参 | 多 shape / Prefill、Decode | BLOCK_V、warp | 无候选通过跨 shape gate | 算子筛选完成 | 失败 |
| [20260911-moe-tuned-config](20260911-moe-tuned-config.md) | MoE 通用 config | large-M / Prefill、Mixed | tile config | 仅 +1.01%/+0.44% | 算子筛选完成 | 失败 |
| [20260912-kda-chunk-replace-checkpoint-01](20260912-kda-chunk-replace-checkpoint-01.md) | vendor Chunk KDA | 三个诊断场景 / Prefill、Mixed | query-length 路由 | +0.796%～+23.847% | 服务与 graph 通过 | 保留、已推送 |
| [20260912-max-batched-tokens-16384](20260912-max-batched-tokens-16384.md) | scheduler 批量化 | 三个诊断场景 / Prefill、Mixed | batched tokens 16384 | +1.121%～+3.912% | 服务通过 | 保留 |
| [20260912-max-batched-tokens-32768](20260912-max-batched-tokens-32768.md) | scheduler 批量化 | max32 / Prefill、Mixed | batched tokens 32768 | 一场景 -1.523%，首轮不稳定 | 请求完成 | 失败 |
| [20260912-mqa-large-prefill-config](20260912-mqa-large-prefill-config.md) | MQA kernel 调参 | large Prefill | tile config | +1.71%/+1.91%，低于门槛 | 微基准完成 | 失败 |
| [20260912-moe-implementation-compare](20260912-moe-implementation-compare.md) | MoE backend 对照 | Prefill、Mixed | reference/native/fused | reference、native sum 均更慢 | alignment 等价性不足 | 失败 |
| [20260913-max-batched-tokens-24576](20260913-max-batched-tokens-24576.md) | scheduler 批量化 | max32 / Prefill、Mixed | batched tokens 24576 | +0.875% / -0.638% | 请求完成 | 失败 |
| [20260913-moe-stage-config](20260913-moe-stage-config.md) | large-M MoE stage config | P4096/D128 等 / Prefill、Mixed | M>=4096 GEMM1/2 config | +2.609% / +0.344% | graph 服务通过 | 保留、已推送 |
| [20260913-sparse-index-convert](20260913-sparse-index-convert.md) | sparse index 辅助 kernel | 两个场景 / Prefill、Mixed | BLOCK_N=1024 | 算子 3.55×～4.54×；服务 -0.041%/-0.005% | 数值与服务通过 | 回退 |
| [20260913-general-mm-analysis](20260913-general-mm-analysis.md) | MM backend 对照 | P1K / Decode | FlagGems vs native | FlagGems 仅 native 的 0.202×～0.382× | 七 shape 数值/graph 通过 | 失败 |
| [20260914-nonzero-blacklist](20260914-nonzero-blacklist.md) | nonzero 路由 | P1K / Mixed | blacklist | 不稳定，无 measured 晋级结果 | 路径命中、告警消失 | 回退 |
| [20260914-gemm-m-key-bucketing](20260914-gemm-m-key-bucketing.md) | 调优 key 分桶 | P1K / Mixed、Decode | log M-key | 吞吐 -0.222% | A/B/revert 完成 | 回退 |
| [20260914-flaggems-db-image](20260914-flaggems-db-image.md) | 调优库固化 | 全场景 | 冻结 DB SHA | 不声明独立吞吐；提高可复现性 | DB/WAL 校验通过 | 保留 |
| [20260914-thead-yaml-deployment-config](20260914-thead-yaml-deployment-config.md) | 部署配置收敛 | 全场景 | YAML 替代环境变量 | 不声明独立吞吐；消除配置漂移 | YAML、导入、服务通过 | 保留 |
| [20260919-decode-moe-smallm-config-scan-01](20260919-decode-moe-smallm-config-scan-01.md) | small-M MoE GEMM2 | P1K max32 / Decode | M<=32 config | 算子 2.1424×；吞吐 +19.432% | 18/18、graph、A/B/R 通过 | 保留、未提交 |
| [20260919-moe-align-smallm-stage2-01](20260919-moe-align-smallm-stage2-01.md) | MoE align kernel | P1K / Decode | stage2 cumsum | 算子 3.635×；A/B/R -1.308% 但特化未命中 | 34/34、graph 通过；补充 trace 纠正 | no-op 候选，回退 |
| [20260919-mhc-pre-flaggems-01](20260919-mhc-pre-flaggems-01.md) | mHC backend 替换 | P1K / Decode | FlagGems mHC pre | 微基准 5.528×；吞吐 -0.587% | graph、16 rank provider 命中；服务 reference 图已降到融合内核 | 回退 |
| [20260919-pccl-exact-decode-shape-bf16-02](20260919-pccl-exact-decode-shape-bf16-02.md) | collective 算法 | TP16 BF16 / Decode | auto/Ring/Tree | Ring/Tree 慢 40.7%/236% | 9/9、`#wrong=0` | 失败，保留 auto |
| [20260919-max-num-seqs64-p1k-milestone-01](20260919-max-num-seqs64-p1k-milestone-01.md) | scheduler 并发 | P1K / Mixed、Decode | max seqs 32→64 | 吞吐 +26.058%，TPOT +57.450% | 768/768、graph 通过 | 按吞吐目标保留 |
| [20260919-maxseq64-m64-gemm2-01](20260919-maxseq64-m64-gemm2-01.md) | exact-M64 MoE GEMM2 | P1K max64 / Decode | M64 config | 算子 2.003×；吞吐 +18.447% | 22/22、graph、reprofile 命中 | 保留、未提交 |
| [20260919-maxseq64-m64-gemm1-config-01](20260919-maxseq64-m64-gemm1-config-01.md) | exact-M64 MoE GEMM1 | P1K max64 / Decode | M64 config | 1.048522×，低于 1.05× gate | 3 seed、graph 通过 | 失败 |
| [20260919-maxseq64-mbt32768-01](20260919-maxseq64-mbt32768-01.md) | max64 token budget | P1K / Mixed | 16384→32768 | warmup 离散 17.771%，无 measured | 384/384 请求成功 | 失败/incomplete |
| [20260920-p4k-scenario-entry-baseline-01](20260920-p4k-scenario-entry-baseline-01.md) | P4K 场景入口与分阶段定位 | P4K / Prefill、Decode、Mixed | 当前保留组合 baseline | 预热 859.648/1020.995/1068.110 tok/s，离散 20.418% | 384/384 请求成功 | 失败/incomplete |
| [20260920-p4k-baseline-recovery-02](20260920-p4k-baseline-recovery-02.md) | P4K 稳态基线恢复 | P4K / Mixed | 三轮完整预调后独立 3+3 | 1071.417 tok/s；measured 离散 0.584% | 768/768 请求成功 | 完成 |
| [20260920-p4k-phase-profile-03](20260920-p4k-phase-profile-03.md) | P4K 分阶段热点定位 | P4K / Prefill、Decode、Mixed | 16-rank torch trace | Mixed: Sparse MLA 24.694%、fused MoE 22.019%；16 个 admission wave | 256/256、16-rank trace 通过 | 完成 |
| [20260920-p4k-mbt32768-04](20260920-p4k-mbt32768-04.md) | P4K scheduler 批量化 | P4K / Mixed | batched tokens 16384→32768 | 吞吐 +1.095%，低于 +3% 门槛 | 1152/1152、graph 通过 | 拒绝，保持 16384 |
| [20260920-p4k-sparse-mla-shape-analysis-05](20260920-p4k-sparse-mla-shape-analysis-05.md) | Sparse MLA 主路径 | P4K / Prefill、Mixed | vendor vs generic 完整调用 | generic 0.828x，慢约 20.8% | 数值通过，未改源码 | 拒绝，保留 vendor |
| [20260920-p4k-large-m-moe-config-audit-06](20260920-p4k-large-m-moe-config-audit-06.md) | large-M fused MoE | P4K / Prefill、Mixed | exact M16384 GEMM2 config | 算子 1.075x；端到端 -0.634%、离散 9.738% | 42 tests、graph、1152/1152 | 拒绝并回退 |
| [20260921-p4k-mixed-cpu-sync-attribution-07](20260921-p4k-mixed-cpu-sync-attribution-07.md) | Mixed 主机同步归因 | P4K / Mixed | CPU self-time + device-gap correlation | 同步与设备忙碌重叠中位 99.791%，nonzero self 0.454% | 16/16 rank | 完成，无代码改动 |
| [20260921-p4k-mqa-logits-exact-shape-review-08](20260921-p4k-mqa-logits-exact-shape-review-08.md) | MQA logits 精确 shape | P4K / Mixed、Prefill | live config + trace grid + historical microbenchmark | 最佳 1.017x/1.019x，低于 1.05x | 16 waves、每 wave 11 次 | 拒绝，无新运行 |
| [20260921-p4k-pccl-simple-protocol-09](20260921-p4k-pccl-simple-protocol-09.md) | collective 协议 | P4K / Prefill、Mixed | auto vs `NCCL_PROTO=Simple` | 32–128 MiB 慢 34.2%～56.7%；Decode 慢 231% | 24/24、wrong/OOB=0 | 拒绝，保持 auto |
| [20260921-p4k-mhc-pre-large-m-reassessment-10](20260921-p4k-mhc-pre-large-m-reassessment-10.md) | mHC pre 大 M provider | P4K / Prefill、Mixed | reference→FlagGems | graph 3.35×–3.81×；P4096/D128 吞吐仅 +0.094% | graph、16-rank、1152/1152 | 拒绝并恢复 blacklist |
| [20260921-p4k-large-native-gemm-provider-audit-11](20260921-p4k-large-native-gemm-provider-audit-11.md) | 大 M GEMM provider | P4K / Prefill、Mixed | native vs FlagGems 前五 shape | FlagGems 0.790×–0.861×；加权慢 19.3% | 数值、graph、两次 replay 通过 | 拒绝，保留 native |
| [20260921-p4k-kda-forward-config-review-12](20260921-p4k-kda-forward-config-review-12.md) | KDA `h_o` 配置 | P4K / Prefill、Mixed | `BV{32,64}×warps{2,4}` | Mixed 最好 1.028×，Prefill 回退 18.1%，估算收益 0.046% | 数值、graph、两次 replay 通过 | 拒绝，保留 BV32/w4 |
| [20260921-p4k-request-index-conversion-review-13](20260921-p4k-request-index-conversion-review-13.md) | request-index 转换 | P4K / Prefill、Mixed | vLLM `BN128/w4→w1` 只读筛选 | M4096 1.210×、M16384 1.283×，估算收益 0.494% | int32 精确数值、graph 通过 | 未改 vLLM，低于端到端门槛 |
| [20260921-p4k-mhc-post-provider-review-14](20260921-p4k-mhc-post-provider-review-14.md) | mHC post provider | P4K / Prefill、Mixed | FlagGems vs reference | reference 只有 FlagGems 的 0.0492×–0.0498× | 数值、graph、两次 replay 通过 | 拒绝，保留 FlagGems |
| [20260921-p4k-moe-sum-provider-review-15](20260921-p4k-moe-sum-provider-review-15.md) | MoE sum provider | P4K / Prefill、Mixed | 通用 FlagGems vs thead multi-token | thead 仅 0.984×–0.989×，最差约 -1.61% | 数值、graph、两次 replay；生产 DB 未变 | 拒绝，保留通用 FlagGems |
| [20260921-p16k-scenario-entry-baseline-16](20260921-p16k-scenario-entry-baseline-16.md) | P16K 场景入口与分阶段定位 | P16K / Prefill、Decode、Mixed | 当前保留组合 3 warmup + 3 measured | warmup 373.524/435.222/435.896 tok/s，离散 14.331% | C1 1/1、C8 8/8；384/384 | 失败/incomplete，转稳态恢复 |
| [20260921-p16k-baseline-recovery-17](20260921-p16k-baseline-recovery-17.md) | P16K 稳态基线恢复 | P16K / Mixed | 同实例已完成三轮预调后独立 3+3 | 434.205 tok/s；measured 离散 0.156% | 768/768，C1+C8 通过 | 完成，作为稳态入口基线 |
| [20260921-p16k-phase-profile-18](20260921-p16k-phase-profile-18.md) | P16K 分阶段热点定位 | P16K / Prefill、Decode、Mixed | 16-rank torch trace，120 iteration | Mixed 63 波均只 admission 1 个新请求；Decode fused MoE 39.123% | 256/256、16/16 rank、DB SHA 不变 | 完成，首选 MBT32768 milestone |
| [20260921-p16k-mbt32768-19](20260921-p16k-mbt32768-19.md) | P16K scheduler 批量化 | P16K / Mixed | token budget 16384→32768，D128 里程碑 + D1024 full | full 吞吐 +9.286%，TTFT/TPOT/E2E 均改善；ITL +75.297% 取舍 | candidate/revert 各 1152/1152，回退漂移 +0.267% | 保留，交付脚本 MBT32768，服务已停 |
| [20260921-p16k-operator-20](20260921-p16k-operator-20.md) | P16K 热点算子再定位与 MQA 原型 | P16K / Prefill、Mixed、Decode | 16-rank reprofile + Top-K 等价性诊断 | MQA 非对齐密集反例退化 30.30% | 最小回归失败后完成定位 | 拒绝，无源码保留 |
| [20260921-p16k-sparse-mla-out-buffer-21](20260921-p16k-sparse-mla-out-buffer-21.md) | Sparse MLA `out=` 复用 | P16K / Prefill、Mixed、Decode | 3 shape graph micro | 0.999978×–1.000507× | BF16输出精确；LSE oracle已诊断 | 拒绝，无源码变更 |
| [20260921-p16k-moe-live-shape-22](20260921-p16k-moe-live-shape-22.md) | exact-M32768 BF16 MoE GEMM2 | P16K / Mixed | 3seed micro + D128 fresh A/B/R | 算子1.072917×；端到端 +0.0198% | 41 tests、C1 1/1、C8 8/8、3456/3456 | 拒绝并回退，服务已停 |
| [20260922-p16k-moe-transaction-upper-bound-23](20260922-p16k-moe-transaction-upper-bound-23.md) | MoE 完整交易上界 | P16K / Prefill、Mixed、Decode | 5040次调用分解 | 非GEMM无限消除2.3367%；叠加全shape GEMM2仍仅2.9878% | 配对异常0；无源码变更 | 拒绝，服务保持停止 |
| [20260922-p16k-mbt49152-24](20260922-p16k-mbt49152-24.md) | scheduler 批量化 | P16K / Mixed | batched tokens 32768→49152 | diagnostic +1.7486%；ITL +46.70%，低于+3% | C1/C8、1152/1152；正式比较契约不完整 | 拒绝，保持32768 |
| [20260922-p16k-sparse-mla-call-boundary-25](20260922-p16k-sparse-mla-call-boundary-25.md) | Sparse MLA完整调用 | P16K / Prefill、Mixed、Decode | 现有trace CPU↔device边界 | CPU边界完整采样上限0.3840%；Mixed vendor kernel 28.7462% | 1320次kernel；无源码变更 | 拒绝，vendor黑盒无新机制 |
| [20260922-p32k-scenario-entry-baseline-26](20260922-p32k-scenario-entry-baseline-26.md) | P32K场景入口 | P32K / Mixed | 当前保留组合 D128里程碑 | warmup 33.036/36.178/36.173 tok/s，离散8.685% | C1/C8、384/384；无measured | 失败/incomplete，转稳态恢复 |
| [20260922-p32k-baseline-recovery-27](20260922-p32k-baseline-recovery-27.md) | P32K稳态恢复 | P32K / Mixed | fresh 6+3 D128 | 第4–6轮离散3.3232%，超过3% | 768/768，C1+C8通过 | 失败/incomplete |
| [20260922-p32k-baseline-recovery-28](20260922-p32k-baseline-recovery-28.md) | P32K入口基线恢复 | P32K / Mixed | fresh 6+3 D128，5%可用性容差 | 36.1742 tok/s；measured离散0.04045% | 1152/1152，C1+C8通过 | 完成 |
| [20260922-p32k-phase-profile-29](20260922-p32k-phase-profile-29.md) | P32K分阶段定位 | P32K / Prefill、Mixed、Decode | 16-rank trace，MBT32768 | 63个Mixed波均只admission 1个新请求 | 256/256、16/16 rank | 完成 |
| [20260922-p32k-mbt65536-topology-30](20260922-p32k-mbt65536-topology-30.md) | P32K scheduler拓扑探针 | P32K / Mixed | MBT32768→65536，D16诊断 | 31/32 Mixed波admission 2；无对照不声称加速 | 128/128、16/16 rank、C1+C8 | 拓扑通过，未保留 |
| [20260922-p32k-sparse-mla-bh4-31](20260922-p32k-sparse-mla-bh4-31.md) | Sparse MLA BH4 特化 | P32K / Prefill、Mixed | BH4/BK/warp/stage | 主 bucket 仅 vendor 的 0.831×，所有边界更慢 | output/max-logits/LSE、graph 通过 | 服务前拒绝并回退 |
| [20260922-mhc-moe-align-critical-path-32](20260922-mhc-moe-align-critical-path-32.md) | mHC/MoE align 临界路径归因 | P1K/P4K/P32K | 服务图与微基准边界 | mHC reference 图已是融合内核；MoE 特化 0 次命中 | rank0 trace + 16-rank manifest | 归因完成 |
| [20260922-p32k-moe-align-ep-33](20260922-p32k-moe-align-ep-33.md) | MoE align EP 路径特化 | P32K / Decode、Mixed | expert-map + M64 padded cumsum | 完整 align 2.84×–3.12×；用户 E2E 1536/1536 成功但当前 `flagos` align 路径绕开候选 | 16 EP maps、4 shapes、graph 通过；无服务候选命中证据 | 实验性安装，待真实命中与同配置 A/B/R |
| [20260923-p32k-align-dispatch-36](20260923-p32k-align-dispatch-36.md) | MoE align 真实路径接入 | P32K / Decode、Mixed | Plugin 窄 dispatch 接入 FlagGems-vllm | 完整 align 3.68–3.91×；P32K/D128 Mixed 吞吐仅 +0.0822% | 数值/graph、16/16 rank 命中；A/B/R 9轮/臂有效，回退漂移 +0.0594% | 收益门槛失败，Plugin 已回退 |
| [20260924-p32k-align-direct-38](20260924-p32k-align-direct-38.md) | MoE align 直接接入及全量 GPQA | P32K / Decode、Mixed | 复用点36窄 Plugin 路由，接入 FlagGems-vllm | 新性能未测；点36旧 D128 +0.0822% | 最小回归通过；198 题 strict 173/198=0.873737≥0.86，正式 gate passed | 精度通过、源码保留；性能未晋级 |
| [20260923-p32k-prefill-quanta-37](20260923-p32k-prefill-quanta-37.md) | 长 Prefill 分块调度 | P32K / Prefill、Decode、Mixed | MBT32768 不变，threshold 0→8192→0 | `incomplete`：候选 warmup 离散 11.223% > 5%，无 measured 轮 | 边界/C1/C8 通过，回退服务已核验 | reverted |

完整结构化实验台账、原始精度数值、证据 SHA 和远端路径均在
[state.yml](state.yml)。根据用户要求，本模型不保留本地 `history/`、
`experiments/` 或其他逐轮目录。

完成 point31–33 时的规划复盘结论是：三点都未晋级为新保留代码，当前正式组合
仍为 MBT32768 加先前已保留算子。之后用户明确要求保留 point33 进行端到端测试，
因此该补丁已重新装入优化容器。用户的 P4K/P16K/P32K/P65536 三轮测试均
128/128 成功，服务现正在运行；但其日志中的 align dispatch 选中
`default.flagos`，当前调用链绕开补丁入口，尚无候选 kernel 命中证据或同配置
A/B/R。原计划中的 MQA row-range Top-K 融合与 MBT65536 A/B/R 暂缓，先核实
真实接入。此前首批请求停滞未在用户这轮测试中复现，且不能在不同 dispatch
路径间直接归因。

## 当前已完成的 Decode MoE 候选

`operator/improve`：在 PPU aligned BF16 路径上，对
`E=288/H=4096/I=128/topk=8/1<=M<=32` 的非量化 GEMM2 选用
`BM16/BN128/BK32/GM8/warps4/stages4/int32-offset`，未命中的 shape
保持原路径。GEMM1 没有更快候选，继续使用基线配置。

首轮 GEMM2 从 0.34180 ms 降至 0.15886 ms，约 2.1516×。
M=1/8/16/31/32、每个 3 个 seed 的成对确认全部通过，整体中位
2.1424×，最低观测 1.3663×；数值、graph capture 和两次 replay
全部通过。候选落源后聚焦测试 18/18 通过。

P1024/D1024/C64/N128 targeted 3 预热 + 3 measured A/B/R 结果：

| 角色 | 输出吞吐中位数 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 840.963 tok/s | 43.028 s | 37.793 ms |
| candidate | 1004.382 tok/s | 36.759 s | 31.647 ms |
| revert | 847.618 tok/s | 42.251 s | 37.619 ms |

候选相对基线的输出吞吐提升 19.432%，P99 TTFT 降低 14.569%，
P99 TPOT 降低 16.262%；回退相对基线的吞吐漂移为 0.791%。三个
有效角色的预热/测量离散、延迟守护和回退漂移都满足冻结数值门槛。

正式比较器仍将这次 `performance_only` 判为 `incomplete`：冻结的
比较契约要求 SLO attainment，但测量计划没有冻结延迟 SLO 阈值。
这是契约/工具证据不完整，不是候选指标未达标；本次只保留为
P1K targeted 结果，不伪装成 formal/full 验收。未来如需正式比较，
必须在重新收集 A/B/R 前冻结修正后的契约。

获胜候选已重新应用到 FlagGems-vllm 工作树，未提交、未推送。
回退验证服务已停止，8011 关闭；当前继续做下一热点的只读路径分析。

## 继续探索结果

当前保留的 small-M GEMM2 候选已完成新的 P1K Prefill/Decode/Mixed
profiling：16/16 rank trace 可解析，阶段边界有效。新的 rank0 Decode
设备活动中，fused-MoE 仍占 38.59%，其后依次为 `mhc_pre` 8.28%、
`reduction_dtype` 7.81%、`moe_align_stage2` 7.68% 和 two-shot all-reduce
6.25%。profiler-off 诊断轮吞吐约 1000.41 tok/s；profiler-on 的
757.15 tok/s 只用于热点归因，不作为性能收益。

根据新 trace，首先验证了非 2 次幂专家数的 stage2 padded vector cumsum。
独立 15 组 `M=10/16/24/31/32`、3 seed 测试全部通过 eager、graph capture
和两次 replay；整体中位加速 3.883×。落源后聚焦测试 34/34 通过，5 个
source-path shape 中位提升 72.49%（3.635×），最低提升 72.22%。

但相同 P1024/D1024/C64/N128 的 3 预热 + 3 measured A/B/R 否定了端到端收益：

| 角色 | 输出吞吐中位数 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 1011.168 tok/s | 35.249 s | 31.397 ms |
| candidate | 997.942 tok/s | 36.338 s | 31.867 ms |
| revert | 1002.872 tok/s | 36.167 s | 31.838 ms |

候选输出吞吐下降 1.308%，P99 TTFT/TPOT 分别退化 3.089%/1.495%，未达到
预冻结的吞吐提升 3% 门槛；baseline↔revert 吞吐漂移仅 0.820%，三角色
离散均低于 10%，FlagGems DB 未变化。因此该优化按失败回退，未提交、未推送。
正式比较器仍因已知的 SLO-contract 缺口标记 `incomplete`，但不改变候选明确
未通过数值主门槛的结论。

随后对 mHC 与通信/归约路径继续做了两轮验证。mHC 的直接精确 shape
微基准覆盖 `M=1/8/16/24/32/1024`，eager、graph capture、两次 replay
和数值均通过，FlagGems 相对 reference 的中位加速为 5.528×。候选服务的
16/16 rank 也全部确认命中 `default.flagos`，并完成 3 预热 + 3 measured，
从而否定了“mHC 本身必然导致旧 RPC timeout”的稳定性猜测。

但 mHC 的 P1K A/B/R 仍明确失败：

| 角色 | 输出吞吐中位数 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| baseline | 1011.860 tok/s | 35.323 s | 31.376 ms |
| candidate | 1005.918 tok/s | 36.796 s | 31.948 ms |
| revert | 1013.657 tok/s | 35.190 s | 31.281 ms |

候选吞吐下降 0.587%，P99 TTFT/TPOT 分别退化 4.171%/1.821%，
baseline↔revert 吞吐漂移仅 0.178%。因此 `mhc_pre_with_norm` 已恢复到
thead FlagOS 黑名单，未提交、未推送。正式比较器依旧因为冻结契约要求 SLO
attainment 却没有阈值而返回 `incomplete`；独立冻结的吞吐主门槛已经明确失败，
所以这个工具缺口不影响回退决定。

trace 父调用分析进一步确认：`reduction_dtype` 是多组 native split-K
`aten::mm` 的归约 kernel，不是可独立替换的模型算子；而精确 Decode
all-reduce 是 TP16 BF16 `[32,4096]`，即 256 KiB payload，实际调用链为
`vllm::all_reduce → CommunicatorFL → PyFlagcxCommunicator → flagcxAllReduce
→ PCCL two-shot`。SDK 自带 benchmark 的三进程中位数如下：

| PCCL 选择 | 延迟中位数 | 相对自动选择 |
|---|---:|---:|
| 自动 | 78.45 μs | 基线 |
| 强制 Ring | 110.4 μs | 慢 40.7% |
| 强制 Tree | 263.9 μs | 慢 236% |

9/9 进程均退出 0、`#wrong=0`、越界为 0，因此继续保留 PCCL 自动选择，
不启动端到端 collective 候选。第一轮曾误用工具不识别的 `bfloat16` 字符串并
被静默回退为 FP32；该轮没有用于结论，最终数据使用工具实际支持的 `bf16`。

三项连续负结果后测试了 `max_num_seqs=32→64`。graph 服务成功启动，
3 轮预热和 3 轮 measured 全部完成，768/768 请求成功；measured 吞吐离散
仅 0.775%。相对保守的 `max_num_seqs=32` contemporary reference，结果为：

| 配置 | 输出吞吐中位数 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| `max_num_seqs=32` reference | 1013.657 tok/s | 35.190 s | 31.281 ms |
| `max_num_seqs=64` candidate | 1277.797 tok/s | 6.918 s | 49.251 ms |

吞吐提高 26.058%、P99 TTFT 改善 80.342%，P99 TPOT 退化 57.450%。按原综合
延迟守护线它曾被拒绝；用户随后明确把总输出吞吐设为主指标并接受这一取舍，
因此正式启动脚本已改为 `max_num_seqs=64`。旧结论保留为目标变化前的历史判定，
不再作为当前 max64 优化的否决条件。

## max_num_seqs=64 分析与 exact-M64 MoE 优化

新的 16-rank 分阶段 profile 显示，max32 与 max64 的 Decode marker 分别主要为
`execute_new_0_cached_32` 和 `execute_new_0_cached_64`。rank0 每步近似设备时间从
28.49 ms 增至 42.27 ms，增加约 48.4%，但每步可处理 token 数翻倍；所以总 token
吞吐提高，而单请求 TPOT 可能变差。这是并发批量化的正常吞吐/延迟取舍，不是
测量矛盾。

max64 下 fused MoE 从 max32 的 38.59% 上升到 rank0 Decode device activity 的
53.20%，每步约从 10.68 ms 增至 22.07 ms，成为明确首要热点。首次 M64 微基准
因错误假设其基线配置与 M32 相同而在测量前失败；实际 M64 基线为
`BM32/BN64/BK128/GM1/SPLIT_K1/warps4/stages3`。纠正后 3-seed 扫描中，最快
配置会把 BM32 改为 BM16、改变 padding 边界，因此没有采用；最终选取保持 BM32
对齐边界的 `BM32/BN128/BK32/GM1/SPLIT_K1/warps4/stages3/int32-offset`，
微基准中位 2.00306×、最低 2.00115×，数值、graph capture 和 replay 均通过。

源码只在 PPU aligned BF16、E288/H4096/I128/topk8、非量化 GEMM2、精确
`M=64` 且 incoming BM32 时命中；M<=32 原特化不变，M33–63、M>=65 及其他
dtype/量化/layout/config 全部回退。落源聚焦测试 22/22 通过。随后同一
P1024/D1024/C64/N128、max64 的 3+3 milestone 结果为：

| max64 组合 | 输出吞吐中位数 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|
| 优化前 | 1277.797 tok/s | 6.918 s | 49.251 ms |
| exact-M64 GEMM2 | 1513.513 tok/s | 5.827 s | 41.587 ms |

候选总输出吞吐提升 18.447%，三轮 measured 相对极差 2.687%，128×3 请求全部
成功；P99 TTFT 和 TPOT 还分别改善 15.769% 与 15.561%。因此候选按当前目标
保留，未提交、未推送。结构化摘要 SHA-256 为
`afabfe0d5d0ebbdad65017f2dbd985595427cebf436a9bec8820f7e75a035b07`。
服务已停止，8011 关闭且没有遗留 worker/EngineCore。

“算子快、端到端反而慢”的两个旧反例已用服务 trace 重新归因。mHC 的
`reference.torch` 只是 dispatch 语义路由，vLLM 编译图中已实际执行
`mhc_pre_fused_kernel_hc_mult_4`；因此 3.35×–5.53× 的微基准比较了
不等价分母，provider 切换没有在服务中删掉这段已融合成本。MoE align 则是
更直接的接入问题：生产 EP 路径的 `expert_map` 使 selector 不成立，候选
`stage2_padded_vec` 在 C32 服务 trace 中 0 次命中，老 stage2 仍执行 2772 次。
所以历史 -1.308% 是 no-op 候选的漂移，不是算子收益被邻接开销抵消。

本轮已尝试把 MoE align 特化扩到 `expert_map != None` 和 Decode `M=64`。完整
align 调用在 16 个 EP map 上精确等价，且加速 2.84×–3.12×；但 TP16 服务
在首批 C64 请求上出现 worker 同步停滞，未通过服务门禁，因此已拒绝并完整回退。
相反，exact-M64 GEMM2 先证明 live shape 和 53.20% 热点份额，再获得 +18.447%
无 profiler 服务收益；这说明只有真实命中、缩短服务关键路径且通过同 workload
复测的算子收益才能兑现。

## exact-M64 后续 reprofile 与候选收敛

保留 exact-M64 GEMM2 后的 16-rank reprofile 已完成。rank0 Decode marker span
从优化前的 4.861 s 降至 4.082 s（-16.018%），fused-MoE 活动时长从
2.538 s 降至 1.761 s（-30.617%），占比从 53.20% 降至 44.12%。这同时证明
配置在 live graph 中命中并解释了端到端收益；profiler-off 诊断轮为
1484.69 tok/s、128/128 请求成功。profiler-on 数字只用于归因。

fused-MoE 仍是 Decode 首热点，但进一步的 M64 GEMM1 配置扫描没有足够收益。
3 个 seed 的数值、eager、graph capture 和 replay 全部通过；最佳且保持 BM32
对齐边界的候选只从 0.30296 ms 降至 0.28894 ms，中位 1.048522×、最低
1.036492×，未达到预冻结的 1.05× 算子门槛，因此没有改源码，也没有进入服务 A/B。

Mixed trace 显示 16384 token budget 以约 16 个新请求为一波完成四次 admission，
因此又单变量测试了 32768。三轮 warmup 吞吐为 1231.792、1472.236、
1493.423 tok/s，离散 17.771%，超过 5% 稳定性门槛，没有进入 measured；后两轮
仍低于当前 16384 配置的 1513.513 tok/s 中位数，也没有 +3% 晋级信号。该实验按
冻结停止条件判 `failed/incomplete/rejected`，启动脚本继续保留 16384。

当前 P1K 的低风险单变量方向已基本收敛：mHC、MoE align、强制 PCCL 算法、
FlagGems general MM、`nonzero` 黑名单、sparse-index BN1024、GEMM1 配置与 32768
token budget 均已被同场景证据否定或未过筛。remaining fused-MoE split-K reduction
融合属于高成本候选，现有证据不足以优先投入。下一步应先用修正后的总吞吐契约
完成 P1K 中间 checkpoint，再进入 P4096/D1024/C64/N128 建立 scenario-entry
baseline 与新 profile；长 prompt 会给 Prefill/Mixed 提供比 P1K 更有价值的证据。

原始 benchmark、trace、脚本和回退补丁仍在远端
`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/`；本地仅保留状态和摘要。

2026-11-02：[点62 FGV Sparse MLA PR整理](20261102-flaggems-vllm-sparse-mla-pr-62.md)按用户授权开始，独立副本基于官方main；生产源/服务保持，拟交付公开H4/graph能力与测试，未有提交结论。

[点63 Plugin PR提交](20261102-plugin-sparse-mla-pr-63.md)已按用户授权准备，明确依赖FGV #1044合入及共享pin收敛；未改生产源码/服务。

[点64 两PR转Ready与CI修复](20261102-public-pr-ci-followup-64.md)按用户授权开始，保留依赖、生产只读不改服务参数。
