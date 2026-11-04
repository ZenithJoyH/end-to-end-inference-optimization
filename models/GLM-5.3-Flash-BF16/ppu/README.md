2026-11-02：[点63 Plugin PR](optimize/20261102-plugin-sparse-mla-pr-63.md)已提交[Draft #669](https://github.com/flagos-ai/vllm-plugin-FL/pull/669)，明确依赖[FGV #1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)合入、公共组合pin收敛及后续回归。8文件/1提交，排除平台MM黑名单；独立副本CPU477/PPU153全部通过、3capture/6变化输入replay、适用pre-commit/额外生产Ruff和wheel内容核验通过。Hosted ci-gate因Draft使必需任务skipped而failure，已在PR披露，CLA passed；未改CI、不将skip当pass。生产源码/原实例/MBT32768/参数/DB不变，无新模型请求、GPQA或E2E收益。

2026-11-02 10:44：[点62 FGV算子PR](optimize/20261102-flaggems-vllm-sparse-mla-pr-62.md)已提交[Draft #1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)，聚焦紧凑H4 Sparse MLA/graph能力，5文件/1提交。真实PPU33项0失败0跳过、8capture/16新输入replay、7项pre-commit、wheel/54 CI helper通过，Hosted rule-check/basic CI/CLA成功（硬件job skipped）。12形状算子benchmark有2项SQ1/TOPK128低于0.9，性能门槛未过，全部披露并维持Draft；非E2E、未自动调优/安装。生产三库/原实例/MBT32768/原参数/DB均未变，health200空闲；SQL/MNNVL独立主题未混入。

2026-11-02 09:52：[点61 Plugin PR审查](optimize/20261102-plugin-pr-review-61.md)完成，实际安装Plugin仍5生产+3测试共8文件；仅修复两测试文件格式/import及thead标题注释，生产Python字节/配置值不变。原生CPU465项0失败0跳过、适用pre-commit通过；已准备metadata、graph/KPool/OOT、PPU临时MM排除三个主题补丁/英文说明，顺序应用逐字节验证通过，未提交推送。**PR状态needs_revision**：FGV公共固定依赖须先交付H4/graph能力，MM全PPU排除须单独界定影响范围。原实例/MBT32768/启动参数与DB不变，health200空闲，无新模型/精度/性能测量，点60分数独立保留。

2026-11-02 00:03：[点60全部20题补跑](optimize/20261101-adaptation-consolidation-60.md)已完成并最终核验：**10/20答对，统一替换后174/198=87.88%≥86%，补充口径达标**；原单次全量C64 164/198原样保留，无新完整gate。13题有最终正文（10对3错），7题HTTP成功/60K无正文被工具标TIMEOUT，实际HTTP超时0；原C64长请求根因未确认。源/实例/原脚本/MBT/RPC参数未变，DB正常运行字节前后均保留，当前health200空闲；未自动继续性能或新试验，监控`glm-20`已删除。以下为分时记录。

2026-11-01 20:27：[点60全部20题诊断补跑](optimize/20261101-adaptation-consolidation-60.md)已唯一启动，20请求实际运行。原异常为19题HTTP客户端14400秒超时，另1题doc190达到60K且无最终正文，被工具转为TIMEOUT；无服务OOM/非法访问/RPC日志。原参数/MBT/源/实例不变，C64上限实际20并发、原生成参数、独立缓存、零重试；全部20统一替换，其余178原样保留，原生全量164/198独立保留，无新完整gate。后台`glm-20`只读跟进，结果待定。

2026-11-01 20:04：[点60收敛版单次全量GPQA](optimize/20261101-adaptation-consolidation-60.md)已完成：**C64，strict164/198=82.83%，低于86%门槛**。198唯一题/396行/两filter及provenance和最终身份审计通过；20个timeout标记仅健康观察。原脚本/MBT32768/参数/源码/实例/DB均未变，服务health200空闲；未签发gate、未补跑或继续性能晋级，精度事件根因未确认。原生结果与失败完整保留，监控`glm-gpqa-c64`已删除。以下为分时记录。

# GLM-5.3-Flash-BF16 / PPU

2026-11-01 14:32：用户授权的[点60收敛后单次198题/C64 GPQA](optimize/20261101-adaptation-consolidation-60.md)已实际开始生成，strict门槛86%；原脚本/MBT/推理参数与当前收敛源码保持，服务health200，64请求运行。新分数/gate待定，不混用旧172补充；`glm-gpqa-c64`只读跟进，终态通知。

2026-11-01 13:18：[点60](optimize/20261101-adaptation-consolidation-60.md)已将当前实际安装三库差异18→16（10生产+6测试），纯metadata归框架并复用公共lookup；必要数值/平台兼容边界保留。CPU465、PPU145/6次变化输入graph、完整模型C1/C8/三16K/11答案/C64 64/64、FULL和当前身份/唯一安装/挂载审计通过，8011健康空闲；原脚本/MBT32768/RPC300及参数未改。没有新全量GPQA或性能、未提交推送；原172补充分数只属整理前版本。TileLang库加载为基线同样存在的观察，未作全栈无TileLang执行认证。下文为此前记录。

本目录记录 `PPU-13` 上 `GLM-5.3-Flash-BF16` 的端到端推理优化。源适配容器为
`glm5.3-flash`；优化工作必须在独立容器 `glm5.3-flash-opt-20260911` 中执行。

2026-11-01：[点59](optimize/20261030-native-mm-registration-repair-59.md)仅现有thead.yaml排除ATen mm/mm_out，CPU495项/4原有skip、单PPU24次独立数值与6次变化输入graph及真实注册验证通过；原300/原脚本完整回归21:46通过（C64 64/64、11/11答案、三16K、FULL）；同实例原生198题C64现已结束，strict163/198=82.3232%<86%，未达标，无新gate；保留外层4小时超时与完整原生结果，冻结性能晋级，当前同实例/源码/原参数/RPC300/唯一安装/health终态核验通过，零生成核验已归档。用户授权的21题统一补跑已于10-31 20:12结束，答对9题，其他177题不变，合并172/198=86.8687%≥86%，补充口径达标；原163/198与7个剩余timeout标记保留，不伪造新单次全量gate。无性能收益结论。点58原300回归P1K C8再次RPC超时并清理，原临时1200诊断通过后已停止，全部失败保留。官方三库及必要兼容安装各1份，MBT32768/模型参数/脚本未改，不推送。下文为此前记录。

2026-10-23 15:29：[点57](optimize/20261023-readaptation-e2e-gap-57.md)只读分析用户测试，P4K输出406.92对历史旧优化栈979.12token/s；当前MoE库路径不覆盖旧FGV特化，公共Prefill路径有明显Mixed停顿，混合缓存容量统计/准入仍须分组核验。具体因果份额未通过新ABR分离，P4K两轮spread8.918%；用户测试与align保持，不自动修复、重启或加跑。完整证据和后续顺序见点57。

2026-10-23 14:21：[点56](optimize/20261023-moe-align-prefix-56.md)按用户接受2.71%收益的明确决定保留同一align补丁；原3%比较failed保留。新实例C1/C8、三16K、11答案、C64 64/64、FULL及当前源/index/安装/挂载/health审计通过，8011健康空闲，MBT/原启动参数/用户Plugin保持。服务已运行，用户接管端到端测试；Agent不自动评测、继续变更或提交推送。新align源尚无新全量精度gate，不冒用旧173/198。以下为历史。

2026-10-23 13:53：[点56同缓存终态](optimize/20261023-moe-align-prefix-56.md)99轮完整稳定、DB字节及逻辑25检查点一致，Mixed+2.7148%未达预冻结3%故原生failed、align已回退；Decode/Prefill守护passed，B/R漂移受控。当前原版服务/完整模型/FULL/C64和源/index/安装/挂载审计通过，回退新实例173/198精度显式绑定通过（非新评测）。MBT/启动参数/用户Plugin不变，无新候选部署或提交推送。下一方向只规划MoE GEMM2实际配置与BMM全链证伪；下文为历史。

2026-10-23 11:28：[点56缓存核验接续](optimize/20261023-moe-align-prefix-56.md)当前缓存schema/writer和较早快照增量已核验；原版173/198的重启＋正常DB写入显式绑定通过，原生分数未改、零新精度请求。旧三臂缺精确基线DB快照仍incomplete，新同缓存三臂已唯一启动，逐阶段严格核验主文件/全表逻辑SHA；收益及条件保留待定。MBT/启动参数/用户Plugin不变，`glm-align`只读跟进新目录；下文为历史。

2026-10-23 04:10：[点55](optimize/20261022-steady-decode-mixed-profile-55.md)两段16rank与主机归因完成；[点56](optimize/20261023-moe-align-prefix-56.md)align向量化94组合/graph、真实16rank命中及整模最小回归通过，三臂99轮完成稳定。Mixed/Decode吞吐A/B表观+4.1964%/+3.4519%，回退吞吐漂移0.5115%/0.9068%，但调参DB身份差异使冻结比较incomplete，未确认净收益。候选已精确回退，原版服务/完整模型/FULL/C64及最终当前源/index/唯一安装/镜像挂载/健康审计通过，用户Plugin、MBT/推理参数不动。无新GPQA/gate/四场景/提交推送，`glm-align`已删除；下一步仅规划缓存可比性核查与MoE/BMM证伪，无自动新实验。

2026-10-22 23:12：[点55](optimize/20261022-steady-decode-mixed-profile-55.md)采集终态incomplete：模型/FULL/C64通过、Decode64/64与16worker设备trace有效，客户端日志断言错误使Mixed未运行；frontend只有元数据，完整主机归因仍缺。离线局部热点指向MoE/BMM/Sparse MLA，PCCL按实际符号补分类，未当端到端收益。原服务/完整回归与当前身份审计通过，用户源码/index、MBT和原参数保持；正常DB更新导致重启实例严格绑定缺口，原173/198达标事实不改。监控已删除，无补采或候选安装；详细证据/后续计划只维护在点55。下方为历史。

2026-10-22 21:12：[点54](optimize/20261022-user-plugin-production-rebaseline-54.md)当前用户源码的P1K三阶段各8+3完成，原生33轮及当前完整身份审计通过。Prefill总吞吐12310.59、Decode输出1157.79、Mixed输出1148.85 token/s（各三轮中位数），吞吐spread0.310%/1.504%/1.365%、约定P99均≤5%；原生173/198精度与同实例显式绑定有效。用户源码、MBT32768/原参数不变，服务健康空闲，monitor已删除；仅入口基线，不是ABR收益或四场景验收。下一轮仅规划稳态主机/设备/通信归因与条件式Sparse MLA算子对照，未启动新实验。下方为历史。

2026-10-22 19:35：[点54](optimize/20261022-user-plugin-production-rebaseline-54.md)当前用户Plugin1ecb0ef3…已通过CPU126和完整模型/FULL回归，新原生单次198题/C64 GPQA为173/198＝87.3737%≥86%，绑定及终态当前身份审计通过。P1K Prefill/Decode/Mixed稳态入口基线已唯一启动，各8预热+3测量，MBT和原参数不变，用户源码保留。旧结果独立记录，尚无新性能收益或四场景验收结论。

2026-10-22 15:35：[点53](optimize/20261022-steady-p1k-phase-baseline-53.md)Prefill/Decode/Mixed稳态入口基线完成，各8+3轮、全部原生复验通过。吞吐中位数12331.81（Prefill总token）/1155.96（Decode输出）/1152.85（Mixed输出）token/s，测量吞吐极差1.13%/1.69%/1.23%，相关P99极差均≤5%，非优化收益。终态当前审计发现Plugin磁盘内容529cd814…→4745048d…，当前源码未验证、不能复用原精度gate；原173/198结果保留，同实例health200/空闲，其他身份未变。未覆盖、重启或新测试；monitor已删除，待明确变更归属和当前版本验证。

2026-10-22 14:28：[点53](optimize/20261022-steady-p1k-phase-baseline-53.md)已处理正常调参DB写入的绑定问题；新增显式同实例缓存更新gate并通过原生check，173/198＝87.3737%≥86%的分数与原始证据未改，不重跑GPQA。原MBT/代码/启动参数不变，P1K Prefill/Decode/Mixed稳态基线已唯一启动，各8预热+3测量，`glm-p1k`只读跟进；无新收益结论。下文“无当前gate”是修复前历史。

2026-10-22 14:07终态：[点52生产GPQA](optimize/20261022-sparse-physical-index-fusion-52.md)原生单次198题/C64 **173/198＝87.3737% ≥ 86%**，分数达标，198唯一题/两filter396行与来源复验通过；5题60K不额外否定分数，未补跑。当前同实例health200、16worker无hook/TileLang、无OOM/RPC；MBT/启动参数不变。正式期间仅调参DB SHA变化，严格当前绑定incomplete、无gate；不改旧manifest或DB，不把此缺口说成模型精度失败，不自动继续性能。终态审计后监控已删除，以下运行中/待定是历史。

2026-10-22 12:20最新：[点52生产验证](optimize/20261022-sparse-physical-index-fusion-52.md)已按原启动脚本去掉全部临时MM/vendor/观测hook、使用默认flagos，MBT32768和参数未改。C64 64/64、C1/C8/三16K/11答案/FULL及16worker无hook/TileLang验证通过，无OOM/RPC。保持同一生产实例2151833:535760459，198题/C64/seed42/60K/strict≥86%全量GPQA已唯一派发，原生开始生成（独立UUID、0旧缓存命中），分数/gate待定；不重启、不修改源码，不自动继续性能。`glm-c64-gpqa`只读跟进；下文OFF/临时策略描述均为历史。

2026-10-22 11:40最新：[点52物理索引OOM修复](optimize/20261022-sparse-physical-index-fusion-52.md)FGV通用融合转换替代全尺寸int64中间量；保持MBT32768/原argv与脚本，原C64 64/64、C1/C8、三16K边界、11/11答案/FULL捕获及多token请求通过，16worker实际`32768×2176`命中，无OOM/RPC。H4+融合源码保留，完整源码/index/唯一安装/挂载/权重与生产DB审计通过，诊断实例已停止，8011 OFF，monitor删除。此次沿用MM07临时vendor/MM诊断策略，不代表默认flagos/生产MM策略、新198题gate或稳态性能验收；无提交推送。以下最新/运行均为各时点历史。

2026-10-22 10:37最新：[点51 MM07](optimize/20261021-sparse-mla-small-head-dual-backend-51.md)固定22组shape三臂及数值/动态graph通过，确认冷MM在线搜索的开销；模型C1/C8、三16K边界、11答案和FULL捕获通过，但C64在物理索引转换的remainder输出分配544MiB时全16rank OOM，非本轮RPC timeout，故不能认定充分修复。临时H4/策略已恢复且未保留，当前SQL-only/OFF全树/index/唯一安装/挂载/权重及DB审计通过；没有自动重试、GPQA或性能，终态monitor已删除。下文准备中/运行中均为各时点历史。

2026-10-22 09:40最新：[点51 MM06取回结果](optimize/20261021-sparse-mla-small-head-dual-backend-51.md)已确认昨晚23:54结束，当前完整审计SQL-only/OFF/生产DB未变，旧监控暂停。基线C8 237.634s通过、前4候选58.937s通过、回退300.728s RPC失败；三臂冷M不同、交集0，不能报严格稳态收益或充分修复。07正在准备固定22组shape/输入SHA的搜索对照，通过才接续原C64与完整minimal，不自动部署/派发GPQA或性能；下述23:36运行中为历史。

23:36进行中：[点51 MM因果对照06](optimize/20261021-sparse-mla-small-head-dual-backend-51.md)已通过真实PPU 92项FP32 oracle与8次动态graph回放，唯一派发原P4096/C1→C8策略A/B/R。role SQL缓存起始同源，候选仅临时限定前4合法配置，原MBT/FULL及生产DB不变；模型三臂尚无结论，不自动保留策略或跑GPQA/性能。已有只读heartbeat跟进，终态恢复SQL-only/OFF，旧23:04是前轮终态。

最新23:04：[点51 SQL修复与MM只读定位](optimize/20261021-sparse-mla-small-head-dual-backend-51.md)确认缓存正常写回，新增19个winner/2040条benchmark，旧结果未丢失。M20480已有11组，但实际20481和8198进入21504/9216冷bucket；候选114→合法104与C8事件一致，多个投影在请求内全搜索。SQL已修复且保留，剩余RPC充分修复仍需同初始缓存的MM策略对照；不能靠清库/盲暖到通过。另有do_bench协议tag隔离风险未修复。本轮零模型/GPU请求及库/生产DB变更，完整终态审计通过、服务OFF、H4未安装、monitor暂停。原C8约300s RPC失败、正式gate/性能缺口仍保留，无提交推送。

17:11只读定位：[点50](optimize/20261021-pr454-public-path-50.md)确认公共适配层把每rank4 heads补至64，SQ20172时Query/输出各1.23 GiB，输出切片不释放大存储；该方法与PR454相同。启动profile跳过真实attention，未覆盖其物化分配。全峰值和碎片占比仍未知，无代码/参数修改或模型重测，服务仍未启动、无gate。

最新16:53：[点50正式终态](optimize/20261021-pr454-public-path-50.md)C64全量GPQA失败：TP14的Sparse MLA输出分配OOM，随后RPC超时、服务退出。原生0/198且全198题timeout，不据此声称模型答案精度为零；86%门槛未过、无gate或性能晋级。三库磁盘源码/唯一安装及静态身份审计未漂移，8011当前拒绝连接，未自动重启、回退或重测；终态monitor暂停。更深峰值显存原因待定位，下述最小回归通过不代表C64验收通过。

最新16:37：[点50修复](optimize/20261021-pr454-public-path-50.md)已在实际私有安装根生效并通过完整最小回归：公共KPool稳定buffer、FG单表缓存反射，原FULL C1/C8/三16K-D8/11答案及独立身份/唯一安装/镜像挂载审计通过，16Worker无TileLang。Plugin12变动文件/FGV4/FG两个既有文件，无旧PPU模型路径或临时trace，原参数/脚本/vLLM不变。新198题/C64/86% GPQA已唯一运行，旧分数不复用、无新gate或性能，未提交推送；细节与失败/恢复见同点记录。

2026-10-21 13:56：[点50公共PR路径验证](optimize/20261021-pr454-public-path-50.md)按PPU仅用FlagGems/FlagGems-vllm，421相关CPU通过/4既有跳过，算子/子图通过；model05实际完成11/11档decode FULL捕获、未降级，但C8触发公共KPool批量Decode kernel设备非法内存访问，故整模未通过、候选不保留。原point49两库源码/index及原FULL服务已精确恢复，C1/C8、三16K边界、11答案、capture/多token回放和最终只读身份/唯一安装/镜像挂载审计通过，8011健康空闲。实际SCM仍52项、两库各1份安装；原参数和启动脚本未变，无新GPQA/gate/性能/提交推送。设备kernel已定位，输入/graph机制根因未确认，不以capture或旧分数证明公共迁移通过；监控暂停，下文是各轮历史。

2026-10-20 21:21：[点49按职责边界复查](optimize/20261020-responsibility-preserving-dedup-49.md)已直接修改实际安装Plugin并回归。仅共享两处一致的懒解析闭包，保留backend工厂/策略和vendor、MHC、缓存ABI、worker及processor必要边界；运行代码净减12行，无新增平台判断。543 CPU通过/4既有跳过，C1/C8/16K三边界/11答案/FULL_DECODE_ONLY capture及多token回放、最终只读审计通过。首轮工厂契约失败与回退保留，修订后原完整范围通过。当前源1244047d…，原参数服务健康，两库各1份安装，无新全量GPQA/性能/提交推送；PR仍有既有配套依赖与跨平台硬件验证缺口。以下“当前”均为各轮当时身份。

2026-10-20 20:18：[点48配置/处理器收敛](optimize/20261020-config-processor-consolidation-48.md)已直接安装并完成回归。旧配置269→45、processor868→226行，复用PR454公共实现，运行代码净减825行，无新增平台判断；188项旧新对照、536 CPU通过/4跳过、C1/C8/16K三边界/11答案、FULL_DECODE_ONLY capture/多token回放及最终审计通过。当前源1581bddf…、原参数服务健康，两库各1份editable安装；未提交推送，无新全量GPQA/性能结论，点46的175/198不得改绑。当前PR仍needs_revision，完整证据与未测项见单点记录；以下为各轮历史。

2026-10-20 19:41：[点47正式PR审查](optimize/20261020-pr-review-consolidation-47.md)已直接收敛实际安装Plugin，删除旧无调用indexer ABI/重复INT8覆盖/透传与实验日志，runtime净减428行、差异50→48；删除3文件有备份可恢复。CPU511通过/4跳过、模型C1/C8/16K/11答案、FULL_DECODE_ONLY graph及最终身份审计通过。当前源471a65fb…，未提交推送、无新性能/完整GPQA；下述175/198为点46旧源历史，不改绑。配套FGV依赖与非PPU/FP8/多模态验证仍待补，pr_readiness=needs_revision。

2026-10-20：[点46公共模型/BF16缓存ABI收敛](optimize/20261020-shared-model-cache-abi-46.md)已直接修改实际安装Plugin，复用PR454模型/共享indexer/cache生命周期，模型2492→321行、patch774→162行，缓存ABI176行，净减2252行。CPU498通过/4跳过；整模C1/C8、三个16K边界、11/11明确答案与FULL_DECODE_ONLY capture/多token回放通过。新身份独立全量GPQA198题/C64 strict为175/198＝88.3838%≥86%，原生gate与最终只读身份/样本审计通过，监控已暂停；8题timeout标记仅诊断，无补充替换。前五轮失败与精确恢复保留，无新性能或非PPU/多模态硬件结论，未提交推送；以下点45为历史。

最新2026-10-20 14:51：[点45文件收敛](optimize/20261020-multiplatform-architecture-45.md)已直接在实际安装Plugin删除4个纯转发文件，SCM46→42，净减183行；95 CPU、真实provider解析/注册与最终只读核验通过。服务/参数未变且健康，未重启、推理评测或提交推送。旧BF16 host及不同config/processor仍待进一步共享重构，当前新磁盘源码尚无模型graph/精度gate。以下46项状态是历史。

最新2026-10-20 13:41：[点45后续收敛补丁](optimize/20261020-multiplatform-architecture-45.md)已直接应用实际editable Plugin目录，SCM现46项。实际目录95项CPU及新进程导入/注册通过，服务未重启且健康；不声称既有worker已加载新代码，新源码模型/graph/精度/性能待后续回归。以下审查候选/SCM45描述为历史。

2026-10-20 13:28：[点45后续收敛候选](optimize/20261020-multiplatform-architecture-45.md)删除通用入口厂商判断、按缓存协议选运行时并删除死代码；95项CPU与元数据注册检查通过，未安装。当前容器/SCM/服务仍保持下述11:18状态，无新模型gate或性能结论。

2026-10-20 11:18：已按用户要求将实际Plugin目录配置为VS Code原生“暂存的更改”45项可视化展示。HEAD为纯PR454，index/磁盘仍是已验证修复版；完整commit `a07f384`保存在快照分支。源码、安装、运行实例不变、服务健康，未推送。具体打开目录与展示方式见[点45](optimize/20261020-multiplatform-architecture-45.md)。不要丢弃更改，它们是实际editable源码。

安装结果（2026-10-20 10:26）：[点45多平台结构修复与安装去重](optimize/20261020-multiplatform-architecture-45.md)已生效。Plugin v4、FlagGems-vllm v3各仅一份editable安装；13个旧私有源码目录已删除，可从宿主任务目录已核验归档恢复。116 CPU契约、10组PPU设备回归、graph及C1/C8/16K边界与明确答案最小回归通过，独立审计通过、8011服务健康。启动参数及脚本、vLLM/FlagGems/权重未改，源适配容器未动。后续Plugin本地提交见上，未推送，无新全量精度gate或性能测量，其他平台硬件未测。下述点43分数属于历史源码身份，不绑定点45。

历史2026-10-19 17:58：点43的14题统一补跑完成，185、194新增答对，全部14题替换、其余184题不变后171/198＝86.36%≥86%，按用户授权补充口径达标。原生单轮169/198仍保留，不签发新的单次全量gate；该次监控已暂停，没有自动继续性能优化。证据见[点43](optimize/20261019-upstream-migration-43.md)。

迁移记录（2026-10-19，覆盖下方点42闭环时状态）：[点43官方上游与PR454迁移](optimize/20261019-upstream-migration-43.md)已安装运行，最小回归通过；原单次198题/C64为169/198（85.35%）未过86%，后续用户授权14题补充后为171/198（86.36%）达标，两个口径分开记录。Plugin为`f769696`（包含冻结main `a696859`），FlagGems-vllm为官方main `b4d3382`加迁移补丁；PPU BF16兼容路径及保留优化迁入，vLLM/FlagGems/权重/启动参数不升级。当前证据见[台账](optimize/state.yml)，旧版本分数/收益不归属新版本；无新性能比较，未提交推送。

- [baseline](baseline/)：环境、容器门禁、冻结 workload 与基线事实。
- [optimize](optimize/)：当前组合、实验台账、性能数据、profiling 结论与下一候选。
- [acceptance](acceptance/)：正式精度与最终四场景性能验收；当前未完成。
- [案例摘要](../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md)

当前状态（2026-10-19）：[点42有界合批/晚到接纳](optimize/20261019-ready-prefill-coalescing-42.md)已闭环，不保留候选。日志修复和真实命中通过，但完整缩减Mixed三臂吞吐仅+0.035879%（原生failed），Decode guard因TTFT退化、波动和漂移保持incomplete。六组8+3全部完成，原配置/源码恢复及独立审计通过、monitor暂停；MBT32768/门槛/原dirty/启动脚本未改，下一候选仅记录未启动。精度保留原生169/198与用户认可统一补跑替换后173/198（87.37%≥86%）区别，不是新完整gate。具体以[optimize/state.yml](optimize/state.yml)和[总览](optimize/README.md)为准，正式四场景验收未完成。

以下为早期历史交付说明，不代表当前运行状态：独立优化容器已建立并完成多轮优化。GPQA 按用户确认的
score-only 口径为 172/198（86.87%），通过 86% 门槛。固定四场景中，当前已建立
预热 DB 后的 P1K 稳定 scenario-entry baseline，并完成同场景 16-rank profiling。
下一个 Decode MoE 候选只已规划，未实施，目前按用户要求暂停。
已保留优化已拆分并推送到 `ZenithJoyH` 名下三个仓库。所有新增的 GLM/vLLM
非 ATen 算子均归入 `FlagGems-vllm@9117ae5`（基于更新后的
`main@6e7ac61`）；Plugin 已删除或停止引用对应本地/FlagGems 实现并改用公共 API，
远端 HEAD 为 `95b04f7`。FlagGems 的两个旧模型专用提交已移除，其 `master` 和
`support-glm5.3-flash` 均收敛到最新上游 `9c9bff3`。当前运行副本尚未切换到
这些新交付 HEAD。
最后服务实例于 2026-09-14 18:07:48 因 EngineCore 异常退出，容器仍运行；
本轮仅提交源码，未重启服务。

本模型采用精简双视图：每个阶段以 `state.yml` 和 `README.md` 为入口，`optimize/`另有每个优化点一份Markdown；
实验历史已合并到 `optimize/state.yml`，原始产物保留在远端工作目录。
