# 20261015-qwen38-flash-next-ppu07-master / optimize

2026-11-02T12:38:29.044878+08:00 [Plugin #573](https://github.com/flagos-ai/vllm-plugin-FL/pull/573)已转非草稿，基础CI/Code Scan通过、8硬件任务最后观察仍等待runner；用户随后要求暂不关注CI，停止跟进，原队列保留，无新定时任务/合并/部署/重启。算子依赖保持，完整CI不宣称通过。详见[eng-076](eng-076-plugin-pr-convergence.md)。

**2026-11-02T12:23:42.984811+08:00 已将13文件候选发布到原[Plugin PR #573](https://github.com/flagos-ai/vllm-plugin-FL/pull/573)，head `0dc1d64e2860c1aa2a6841db97baf924ec18ea37`；与main无冲突，保留历史且未force-push。209 pytest CPU+8 CPU graph生命周期契约、13文件lint/format/pre-commit通过。算子依赖未合入，草稿跳过必需CI作业导致gate失败；仍非完整CI/设备/模型验收。未部署/重启，定时任务保持删除。详情见[eng-076](eng-076-plugin-pr-convergence.md)。**

2026-11-02T11:47:44+08:00 [eng-076公开依赖核对](eng-076-plugin-pr-convergence.md)：复用既有FlagGems #5882/#7270及FGVLLM #959/#982/#989，均待合入；#7582为index重叠专项回归，#940/#6892已合入。已在[现有Plugin草稿#573](https://github.com/flagos-ai/vllm-plugin-FL/pull/573)补充merge blocker并精确读回；未新建重复PR、未commit/push源码。旧#573 head有冲突，当前13文件候选未推送；公共组合pin/安装、设备/graph/精度验证仍待做，未部署/重启/请求。

2026-11-02T11:18:37.546830+08:00 [eng-076五文件格式v4](eng-076-plugin-pr-convergence.md)：5文件格式债关闭，4文件AST相同、runner仅等价导入分组，业务AST/首次模块顺序/绑定/注释保持；155 CPU、最终13文件显式lint+format、原pre-commit7通过/2不适用，双重patch重建通过。本轮独立diff5文件+135/-89；最终组合13文件+1802/-139。11:19回读线上保持；未部署/请求/重启/提交推送，剩余公开依赖与真实codec/设备/graph/模型精度验证，needs_revision。

2026-11-02T11:03:12.178151+08:00 [eng-076视频loader v3](eng-076-plugin-pr-convergence.md)：移除共享Qwen3 FPS wrapper，改为专属注册backend及复制本模型media配置，保留其它模型原类/映射/异常和显式覆盖优先级。本轮2文件变化，最终13文件；155 CPU通过、pre-commit实际7通过/2不适用（更正此前8项计数），两种patch apply精确重建。公开固定依赖、5大文件格式债、codec/设备/graph/模型回归仍开放，needs_revision。11:04回读线上687成员/原API/计数未变，候选未部署；定时任务保持删除。

2026-11-02T10:46:13+08:00 按用户要求删除定时任务 `qwen-ppu07-c32`，产品回执确认 deleted；停止小时跟踪，当前工作聚焦 [eng-076 Plugin适配代码收敛](eng-076-plugin-pr-convergence.md)。GPQA未闭环事实保留；本次仅删除调度并更新记录，未执行远端、模型或服务操作。

2026-11-02T10:34:25.549253+08:00 [eng-076测试文件v2收敛](eng-076-plugin-pr-convergence.md)：RNG测试并入既有runner测试，新增测试文件3→2；多模态改pytest/fixtures并归patches，保留Mamba独立reference。136 CPU用例含14 RNG实际通过、pre-commit通过，352生产文件与v1相同；最新candidate-tests-v2未加载，原线上保持，0请求/服务动作。sampling_rng.py是已有discarded请求offset修复，生产文件本轮未动。

[eng-076 当前Plugin适配PR收敛](eng-076-plugin-pr-convergence.md)：隔离候选已整理，14→13差异路径，三主题patch及精确apply回读、67 CPU契约/pre-commit通过；线上687源码成员和BF16/Mamba/RNG修复保持。共享视频loader作用域、固定依赖及硬件/graph回归未闭环，needs_revision，0部署/请求/重启/提交推送。

2026-11-02T09:43:06.430608+08:00 完成当前8010免重启取证入口只读核验：现有IO dumper在当前graph启动路径跳过，RPC/profile路由未注册（OpenAPI+GET404），12文件SHA与原冻结版本相同。完整取证需有界worker埋点、仅8010受控重启及另批3短请求，均未授权/未执行；BF16及修复保持。机制证据见[acc023](acc-023-full-gpqa-c32-main.md)。

2026-11-02T09:32:59.683585+08:00 按用户要求完成doc81首差机制取证方案，仅规划0请求：完整版3×128输出C1请求（关trace/开trace/开trace重复），需worker logits+q/RNG+TP8 Mamba埋点；当前无已核实免重启启用入口，不能执行。HTTP-only2条只是初筛替代，不等同完整取证；判别表及停止边界见[acc023](acc-023-full-gpqa-c32-main.md)。保留BF16/现有修复，无部署或正式新分。

2026-11-02T09:12:41.547384+08:00 小时核验：首只读SSH超时255已保留；PPU-07连接检查通过后补核同8010健康空闲、源码及7回执未变，无服务日志错误。无模型请求/恢复操作或新增修复验证，GPQA174/198仍开放。

2026-11-02T07:28:38.333184+08:00 小时只读：8010健康空闲，源码及7份关键回执未变，无新错误；无新增定位/修复/验证，GPQA174/198仍开放，当前没有新修复执行或模型流量。

2026-11-02T06:29:35.098104+08:00 小时只读：8010健康空闲，源码及7份关键回执未变，无新日志错误；无新增定位/修复/验证，GPQA174/198仍开放，0新增请求或服务操作。

2026-11-02T05:27:40.170512+08:00 小时只读：8010健康空闲、源码及7份关键回执未变，无新日志错误；无新增定位/修复/模型验证，GPQA174/198仍开放，0新增请求或服务操作。

2026-11-02T04:30:13.505946+08:00 小时只读：8010健康空闲、源码及7份冻结回执不变，无新错误。无新增定位/修复/模型验证，GPQA174/198仍开放，0新增请求或服务操作。

2026-11-02T03:23:08.047561+08:00 小时只读：8010健康空闲，源码/7份关键回执/完成终态保持，无新错误；无新增定位/修复/验证结果，GPQA174/198仍开放，0新增请求或服务动作。

2026-11-02T02:26:03.104050+08:00 小时只读：无新增定位/修复/模型验证，8010健康空闲、源码及7份关键回执保持，无新日志错误。GPQA174/198仍开放，机制证据缺口不变，0新增请求/服务动作。

2026-11-02T01:23:23.734769+08:00 小时只读：无新增定位/修复/模型验证；8010健康空闲、源码及7份关键回执不变，无新日志错误。GPQA174/198仍未达标，机制证据缺口保持；不扩测，保留BF16及现有修复。

2026-11-02T00:20:41.348937+08:00 小时只读：8010及7份关键回执未变，健康空闲。已有doc81新增CPU定位：同prompt在输出112处已分叉（总位置890），当前60K输出无重复64token窗口/1–512周期尾部，不支持字面token死循环解释；尚无首差logits/RNG/state证据或源码修复结论。0新增请求/服务动作，GPQA正式仍174/198未达标。

2026-11-01T23:15:21.167554+08:00 新8题16条C1对照完整结束，独立审计退出0、driver/watch退出。xhigh3/8、medium5/8，本轮gain186/69、loss0；doc81两arm均错，medium仅缓解截断未答对。限制为本选定8题一次，无正式gate或默认策略变更；8010同BF16/修复健康空闲。GPQA174/198整体仍开放，保留小时只读跟踪。

2026-11-01T22:18:31.575083+08:00 快检仍15/16完整，末条doc69 medium在途，无新异常；距主通知数分钟不重复打扰，原队列自然继续。

2026-11-01T22:15:34.363747+08:00 新16条C1已15完整/7pairs，最后doc69 medium在途。局部doc186 medium恢复正确；doc81本轮两arm均错（xhigh60K截断、medium短答错误），不能单归因medium或称无截断就更准。15响应HTTP200/源码身份保持，无新基础设施异常；等原队列与CPU审计，不扩16预算。

2026-11-01T19:31:34.958406+08:00 只读快检新16条队列6派发/5完整/2pairs；doc111 xhigh在途，同API/source/runtime健康，无新异常。距主通知数分钟不重复通知，下一小时主动。

2026-11-01T19:29:15.496972+08:00 新8题C1对照已3派发/2完整/1pair：doc96 xhigh585/medium855均答对B并正常结束，medium并非保证更短；doc106 medium在途。原16预算自然继续，source/runtime/BF16修复保持，尚无整体修复或正式新分。

2026-11-01T19:27:21.003778+08:00 用户已授权新8题16条C1对照并启动，当前1派发/0完整，按冻结顺序、seed1234、BF16及现有修复。重点核medium同轮paired loss；原正式GPQA仍174/198未达88%。D=effort-heldout-c1-002，详情见[acc023](acc-023-full-gpqa-c32-main.md)。

2026-11-01T18:31:54.068578+08:00 小时只读：8010健康空闲、源码和10份关键冻结回执未变，无新错误或模型验证；新8题方案未执行。GPQA174/198<88%仍开放，继续小时跟踪，0新请求/服务动作。详见[acc023](acc-023-full-gpqa-c32-main.md)。

最新方案（2026-11-01T17:57:32.287735+08:00，未执行）：已有198题中排除原effort8题，冻结原答对96/111/176/81与原答错106/186/89/69，覆盖各3学科/4子域/4长度层，含58849-token长正确哨兵。拟16条C1/seed1234配对，重点统计同轮xhigh对→medium错；0新增请求，保留BF16/修复和8010。正式174/198无新gate；方案与29成员证据见[acc023](acc-023-full-gpqa-c32-main.md)。

最新小时只读（2026-11-01T17:32:01.799146+08:00）：无新增诊断或模型验证；4条复核及审计终态不变，同BF168010健康空闲、源码/7份关键回执一致、无新错误。GPQA174/198仍未达88%；记录已同步，继续小时只读后续，不新增请求/改变策略。

最新小时只读（2026-11-01T16:32:20.991301+08:00）：无新增诊断或模型验证；4条复核及审计终态不变，同BF168010健康空闲、源码/7份关键回执一致、无新错误。GPQA174/198仍未达88%；记录已同步，继续小时只读后续，不新增请求/改变策略。

最新小时只读（2026-11-01T15:28:09.954434+08:00）：无新增诊断或模型验证；4条复核与审计终态不变，同BF168010健康空闲、源码/7份关键回执一致、无新错误。GPQA174/198仍未达88%；记录已同步，继续小时只读后续，不新增请求/改变策略。

最新小时只读（2026-11-01T14:29:47.846607+08:00）：无新增诊断或验证；4/4复核及审计终态不变，同BF168010健康空闲、源码与7份冻结回执一致、无新错误。正式GPQA174/198未达88%，继续小时只读后续，不新增请求/修改策略。

最新小时只读（2026-11-01T13:25:19.393088+08:00）：无新增诊断或验证；4/4反序复核及审计保持终态，同BF168010健康空闲、源和7份冻结回执未变、无新错误。正式GPQA174/198仍未过88%，保持小时只读后续，不新增测试/修改策略。

最新终态（2026-11-01T12:24:23.599485+08:00回读）：4条反序C1已完成并停止，独立CPU审计及91/95成员回读通过，driver/CPUwatch退出。4arm完整token/message均与原轮精确相同：doc79 xhigh49012/D对、medium2506/A错；doc145 xhigh60000截断、medium1544/A对。两arm本轮均1/2正确，不能泛化统一收益或原C32根因。正式GPQA174/198仍未达88%，同BF168010健康空闲；整体小时只读监控保留，不再执行下一批。

最新小时只读（2026-11-01T11:10:05.045937+08:00）：反序复核完成2/4、1完整pair。doc79 xhigh49012/D对、medium2506/A错，两个arm均与原轮prompt及全部输出token/message完全一致；反序下此局部答案退化重现。doc145/xhigh在途，尚无该pair结果。同BF168010/源/控制保持，无新错误；原唯一4预算继续，4条即停。

最新小时只读（2026-11-01T10:15:05.315515+08:00）：四条反序C1仍1/4完整，doc79/xhigh在途，无新增完整结果；同8010健康running1，源和8份关键控制SHA保持、无新错误。原唯一队列继续，4条即停，不补发/重跑或操作服务，等待其余结果及独立CPU审计。

最新反序复核（2026-11-01T09:42:17.089499+08:00）：2派发/1完整，doc79 medium2506stop/finalA（goldD，错），同arm完整token/prompt与reasoning/final同上轮；doc79 xhigh在途。唯一4条客户端及CPUwatch健康，源与BF168010保持，严格4条即停，未有全范围终态或新formal分。

最新已执行（2026-11-01T09:38:57.515734+08:00）：用户授权的doc79/145四条反序C1已启动，1派发/0完整返回，当前79/medium在途；唯一driver1701290与CPUwatch1701313 active，同BF168010健康running1，source/runtime/原脚本保持、prefix命中未增。严格4POST/seed1234/0retry、4条即停，不额外全量/服务动作；监控切新绑定。旧8题1/8对3/8与正式174/198保持，尚无新结果。

最新已有产物答案核对（2026-11-01T09:30:09.624303+08:00）：8题xhigh1/8正确、medium3/8正确；截断5→0，但5个缓解中仅3个答对，另doc79由对变错，净增2仅限此选择样本。正式GPQA174/198及ERQA252/400不变。下一步4条C1反序复核仅方案未执行，保持BF168010与修复、0新请求，继续小时只读跟踪。详见[acc023](acc-023-full-gpqa-c32-main.md)。

最新小时只读（2026-11-01T09:10:56.413983+08:00）：无新增诊断或验证；同BF16 8010健康空闲，源码和7份关键冻结回执未变，原controller/CPUwatch均退出，无新服务错误。正式GPQA174/198未达88%；继续小时只读跟踪，不新增测试或改变策略。

最新小时只读（2026-11-01T08:03:27.965920+08:00）：无新增诊断或验证；同BF16 8010健康空闲、源码/7份关键回执不变，16/16对照已完成（xhigh5/8截断、medium0/8），正式GPQA174/198仍未达88%。保持小时只读后续，不新增测试或变更策略。

小时快检（2026-11-01T07:06:52.825249+08:00）：无新增诊断/验证；同8010健康空闲，源与7关键回执一致、无新增模型token，小对照终态不变。GPQA174/198仍未达88%，保持小时只读后续，不新增测试或改策略。

小时快检（2026-11-01T06:07:50.594645+08:00）：无新增诊断/验证；8题16/16对照及审计保持终态，同8010健康空闲、源/7关键回执未变。GPQA174/198仍未达88%，不新增测试或改默认策略；按用户要求保持小时只读后续。

本次8题对照16/16完整、独立CPU审计及300成员回读通过，原driver和CPUwatch2均退出。xhigh5/8截断，medium0/8，8题medium输出均更少；仅限该选定单次C1范围，不是完整GPQA精度通过。原GPQA174/198仍未达88%，ERQA252/400终态保留；同BF168010健康空闲，未重启、全量复测或改默认策略。小时监控转终态后只读整体跟踪，不再派发测试。

小时进展（2026-11-01T04:03:46.527518+08:00）：14/16完整、7pairs；doc147新对xhigh60000length/无final、medium22376stop/有final，完整raw/token/usage有效。当前7对xhigh5截断、medium0，限当前选定小范围；最后doc185/medium在途。同8010健康同源，原队列继续，无重试/全量评测/服务操作。

小时进展（2026-11-01T03:05:17.872349+08:00）：12/16完整、6pairs；doc145新对xhigh60000length/无final、medium1544stop/有final，完整raw/token/usage有效。当前6对xhigh4截断、medium0，限该小范围单次观察；doc147/xhigh在途。同8010健康同源，原队列继续无重试，不形成正式精度或唯一根因结论。

小时进展（2026-11-01T02:00:46.027166+08:00）：11/16完整、5pairs；doc127 xhigh60000length/无final、medium30418stop/有final，完整raw/token/usage有效。当前5对xhigh3截断、medium0，限该小范围单次观察；doc145/medium1544已stop，xhigh在途。同8010健康同源，原队列继续无重试，不形成正式精度或根因结论。

小时进展（2026-11-01T01:06:15.616128+08:00）：8/16完整、4pairs；doc88新对xhigh60000length/无final、medium29330stop/有final，完整raw/token/usage有效且无prefix命中。当前4题xhigh2截断、medium0，限小范围单次对照，不推广全量精度/根因。doc127/xhigh在途，同8010健康同源，无新故障或重试，原队列继续。

小时进展（2026-11-01T00:02:47.044214+08:00）：C1策略对照7/16完整、3pairs；doc88/medium29330token/stop/有final，完整raw/token/usage回读有效，xhigh在途，尚无第4pair结论。同8010健康C1/同源/无新故障，原队列继续、无手动重试或服务操作。

小时进展（2026-10-31T22:59:48.128243+08:00）：C1策略对照6/16完整、3pairs；doc79新对xhigh49012/medium2506均stop/有final，完整raw/token/usage回读有效、prefix增量0。前三对medium均更短，当前xhigh1/3截断、medium0/3，仅局部观察，不代表8题/正式精度。doc88/medium在途；同8010健康同源，原队列继续，无手动重试或服务操作。

小时进展（2026-10-31T21:59:32.224674+08:00）：8题C1对照4/16完整、2pairs。新doc71 xhigh60000length/无final，medium45740stop/有final，两HTTP200、完整token/usage及prompt回读有效、prefix增量0；局部支持effort影响该题截断，不是8题或正式分数结论。doc79/xhigh在途，同8010健康/同源，原队列自然继续、无手动重试。

小时进展（2026-10-31T20:57:14.239735+08:00）：[8题C1对照](acc-023-full-gpqa-c32-main.md)3/16完整、首pair doc32 xhigh52466与medium1452token均stop/有final；本次xhigh C1未复现历史C32的60K截断。doc71 medium45740已stop，xhigh在途。同8010健康、无源漂移/新故障；只读3条完整token/usage回读通过，不是全范围结论或新formal gate。

最新快检（2026-10-31T19:54:50.414968+08:00）：8题C1策略对照首条doc32/xhigh仍在生成，0/16完整响应；同8010健康running1、源/driver/CPUwatch2一致，无新故障。生成token增长不计完成，距启动通报不足1小时静默，小时跟踪继续。

最新进行中（2026-10-31 19:17）：[8题xhigh/medium C1单变量对照](acc-023-full-gpqa-c32-main.md)已按用户新授权启动：16请求预算、seed1234、原采样/max60000、0retry，仅变effort，交替arm顺序。当前首条doc32/xhigh在途、0完整结果；同8010健康、源和BF16/已有修复不变，不重启或全量GPQA。独立CPU终态审计和小时监控跟踪原唯一driver，不补发请求；原GPQA174/198低分和ERQA252/400保留。

小时核验（2026-10-31T18:53:31.526681+08:00）：无新增修复/诊断/验证；同一8010健康空闲、源与7份冻结回执一致，GPQA174/198仍未达88%、ERQA252/400已完成。仅只读跟踪，不补启动或复测；按用户要求本小时主动报告。

最近快检（2026-10-31T17:56:13.307164+08:00）：同一8010健康空闲、源及7份冻结回执一致，无新增修复/诊断/验证；GPQA174/198与ERQA252/400保持，距专项通报不足1小时静默，小时跟踪继续。

最新只读定位（2026-10-31 17:27）：[GPQA xhigh／采样／prefix专项](acc-023-full-gpqa-c32-main.md)完成；两轮198题完整prompt与输入token IDs相同、均默认xhigh；API seed1234/T1随机采样，非评测seed42或贪心。R5之后prefix命中增量0，排除本轮新前缀复用命中解释，但align状态数值路径未独立排除。8题输出预算耗尽，最大总长62933<上下文80000；69正确题也超过6400、6题超过51200，非统一边界必败。90成员CPU证据回读通过，0新增推理/生产变更/服务动作；174/198仍未达88%，底层唯一因果未确证，性能冻结、小时跟踪继续。

最新终态（2026-10-31）：[ERQA400/C32已完成](acc-024-full-erqa-c32-main.md)，252/400＝63.00%（无阈值score-only），全wire/真实ID映射及3098成员终态证据核验通过。401次HTTP均200，ERQA_240首次60K/None由原生重试一次后正常结束，未人工复跑。当前同一BF168010健康空闲、源与启动脚本保持；[GPQA重审](acc-023-full-gpqa-c32-main.md)有效174/198仍未达88%，无新passgate、底层原因未确证。按用户要求保留整体问题小时只读跟踪，不自动新增评测/修复/服务动作；下方运行中状态均历史。

最新（2026-10-31）：[审计映射已修复](acc-023-full-gpqa-c32-main.md)，已有GPQA重审198题完整有效，174/198＝87.8788%仍未达88%，原incomplete/首错不覆盖。8题60K是推理未结束而耗尽预算，另16题final明确字母与原生抽取一致；历史通过轮也有9题60K，不能归因单一新修复。按用户新授权，[当前同一8010的ERQA400/C32已08:07:56单次启动](acc-024-full-erqa-c32-main.md)，全wire/真实ID映射和终态CPU审计留存；0重启/0新GPQA/无8035/提交推送。小时汇报继续，以下早期段落为历史。

历史终态：[acc023原生GPQA终态](acc-023-full-gpqa-c32-main.md)174/198＝87.8788%，未达88%。198题及396双filter行、完整API已CPU核验；8题60K截断后finalNone，另16普通错答，无模型RPC/网络超时证据。原CPU审计因JSON聊天参数未解码而198条映射全漏，原队列以incomplete停止，ERQA未启动。审计首错和原分数完整冻结，未修生产/恢复队列；8010同实例健康空闲。采样修复的10条最小回归仍通过，但无新formal gate。小时汇报继续，待主聊天处理审计和低分；下方为历史阶段。

最新：[acc023采样RNG回退修复](acc-023-full-gpqa-c32-main.md)已部署，仅丢弃行恢复采样前offset，14项候选与14项仓库CPU测试通过。BF16和其他修复、用户启动脚本不变。新repair-validation-005冻结2条长C1→8C8，随后同实例C32 GPQA198→ERQA400；19:40已完成唯一一次8010重启，旧实例及8worker自然排空，新实例1336953已READY、两类capture各7/7，两条6500-token C1完整输出553/553逐token一致，第二条实际prefix命中6400，C1 FULL增量1013；10/10最小回归通过，C8 unpadded8 FULL增加244；修正版独立CPU审计32/32通过，19:53正式C32 GPQA198已启动、缓存旧答案0条，ERQA400串行排队，尚无正式分数。旧失败原件保留，小时汇报继续，无8035/提交/推送。下方为先前状态。

当前：[acc023 RPC预算修复与最小回归](acc-023-full-gpqa-c32-main.md)。用户start-model.sh已单次启动8010，RPC300→1800秒，保留BF16和现有源码修复。两条6500-token C1均HTTP200/答案B，无RPC超时；第二条实际prefix命中6400。但完整输出757/553token不一致，原队列在C1护栏停止，0C8/0GPQA/0ERQA，CPU审计incomplete。精确8010仍健康空闲，不再重启。采样随机数推进31040与partial-prefill回退4的源码兼容疑点已冻结，尚未确认本次根因，不能排除prefix数值差异。25成员诊断与终态日志已归档；小时汇报继续，无8035/提交/推送。

CPU定位新增：原函数体的元数据重放复现采样推进31040、丢弃时回退4、残留31036的兼容缺口；小尺寸推进4的对照正常。已保存CPU证据，尚无实际失败请求的RNG/logits/state对照，本次模型根因仍未确认，未改生产代码或新增推理。

C1定位已进一步收敛：当前8192预算下align仍强制6500→6400+100；已有日志证明Gems指数采样backend命中，CPU原函数体对照说明miss多一次discarded采样残留31036偏移，而hit从0开始。主要原因strongly-supported；Mamba复制规划CPU fixture一致，但实际设备状态值无现场，尚未应用修复或新增请求。

<!-- acc023-hourly-check -->
2026-10-31T16:54:07.221174+08:00 终态后快速只读：无新增修复/诊断/验证结果。ERQA252/400（63.00%）及GPQA174/198未达88%均不变，旧controller/CPUwatch均已退出、无新formal目录或错误flag；精确8010同API健康200/running0/waiting0/KV0/preempt0，完整source/runtime/原script一致。10份关键summary/manifest/audit/suite回执SHA验同；仅扫终态后service新窗口761bytes，无新fatal/RPC错误；free1402.37GiB。未重解析401份wire、重复full audit、发推理/改生产cache/操作服务/访问8035。距16:48完成通报仅数分钟，保持静默；小时整体GPQA低分后续跟踪ACTIVE，不补启动任何任务。
<!-- /acc023-hourly-check -->

以下为历史过程记录，不能代替上述当前状态。

此前[acc023修复验证](acc-023-full-gpqa-c32-main.md)：已按用户要求原样执行start-model.sh一次；两类capture各7/7后，22:52:23首请求因CPU RNG clone误分发HTTP500并自然退出。新增FlagGems注册修复已落地，9项CPU对照、2项仓库CPU测试、物理8的8项算子与FP32/BF16各两次graph replay通过；Mamba修复/BF16/原算子修复保留，启动脚本未改。首错、备份与审计完整保留，8010当前未运行，正式GPQA/ERQA未续跑；模型验证仍需下一次启动授权，不能宣布精度通过。以下为历史过程记录。

2026-10-29 [acc023修复已落地](acc-023-full-gpqa-c32-main.md)：Plugin按MambaSpec分组、type绑定copy funcs、独立请求状态并预分配；同构原路径不变，BF16/现有算子修复保留，vLLM源码未改。23 CPU测试及物理8真实复制/capture+2次更换输入replay通过，完整padding字节一致。模型验证尚未执行：自动审批拒绝启动8010与10请求，要求用户明确授权；已核无DRIVER_LAUNCH、8010无监听。最小控制器/输入已冻结，原失败证据保留，无新正式gate或性能结论。

2026-10-29 [acc023查因](acc-023-full-gpqa-c32-main.md)：prefix cache开启默认align，旧统一MambaBuffers要求GDN与PLE不同shape/dtype/type完全相等，首请求触发断言。CPU元数据抽取验证同类通过、混合失败、统一padding仍失败；关键方法与升级前备份相同，native mamba_utils与旧acc021相同，属于以前prefix disabled未覆盖的兼容缺口。短期可规避align、长期需框架按group/type拷贝状态；均未实施，无新GPU／推理／重启或正式gate。

2026-10-29 [acc023 C32 GPQA故障](acc-023-full-gpqa-c32-main.md)：首批请求18:55:12触发MambaBuffers/get_mamba_groups规格一致性断言，8010 API自然退出。原生0分由198题全部TIMEOUT占位造成，判incomplete而非有效精度0%；原controller已退出，79成员manifest及首错冻结，[acc024 ERQA未启动](acc-024-full-erqa-c32-main.md)。monitor已产品确认deleted；无Agent服务操作／恢复／改源码／重跑／8035／提交推送。根因待查，不能直接归因BF16/MoE或prefixcache。

2026-10-29 用户重启后的8010已单次启动[C32全量GPQA acc023](acc-023-full-gpqa-c32-main.md)→[C32全量ERQA acc024](acc-024-full-erqa-c32-main.md)串行各一轮。controller756726精确身份核验、GPQA原生attempt1/1及num_concurrent32已确认，ERQA已通过预检排队。三库新主线/BF16/image16、encoder graph关闭、用户prefix cache开启、无旧bootstrap/pin047；无服务动作或额外smoke。30分钟只读monitor qwen-ppu07-c32-gpqa-erqa ACTIVE，结果未出。

2026-10-29 [eng075 两算子库主线更新已完成](eng-075-operator-libraries-main-update.md)：FlagGems master04dafa8b、FlagGems-vllm main31a2705d已替换canonical /opt源码，剩2／6处本地差异。index_put采用上游PR6892，其他index/randn、PLE、MoE及原测试保留；6896语法、19既有MoE CPU mock、14 Qwen接口／QSA源检查通过，36项证据及新旧源码／双备份独立核验一致。原目录保留在/opt/qwen38-eng075-operator-libraries-20261029；editable不变，pip metadata标签仍旧build。Plugin／BF16／启动脚本未动，0启动／重启／推理／GPU／8035／提交推送，8010仍未监听。模型／graph／精度／性能not_run，旧gate不继承。

2026-10-29 [eng074 Plugin更新已完成](eng-074-plugin-main-update.md)：指定容器/opt/vllm-plugin-FL main已从a696859b更新到40f992dc（含已合入PR455），BF16／PPU MoE／视觉分发／视频防护及MoE配置保留，源码管理剩9处本地差异。513语法、7多模态CPU契约、80 MoE条件、4 BF16配置守护通过，683新源／660原备份／25证据manifest独立核验通过；完整回退原目录在/opt/qwen38-eng074-plugin-main-20261029/original-canonical。另两库／安装metadata／启动脚本未变，editable路径不变、pip版本标签仍旧build。0服务操作／推理／GPU／8035／提交推送，8010仍未监听；新主线模型／graph／精度／性能not_run，旧gate不继承。以下为准备及历史记录。

2026-10-29 [eng074 Plugin主线更新准备](eng-074-plugin-main-update.md)：核当前a696859b→官方main40f992dc，先备份含Git和本地修改的完整目录，在隔离候选合并；保留BF16和已有修复，尚未替换生产源码。仅工程更新，不启动／重启／推理／GPU／8035／提交推送；8010预检未监听，新源码模型验证not_run，旧gate不继承。

2026-10-26 [eng073 env-trim002已完成](eng-073-start-model-script-sync.md)：指定start-model.sh新SHAa62499ce，删除遗留QWEN38_FGVLLM_OPS／DNN_VENDOR及实验PYTHONPATH／DIAG047_CONFIG显式export并unset，启动入口不再依赖历史bootstrap／pin047。保留平台通信／FGVLLM开关／黑名单、BF16／16图及所有模型argv和源码修复；cache用默认路径，不删除文件。新备份`start-model.sh.bak-eng073-envtrim2-20261026`；五成员manifest与目标／备份独立回读、host／container语法／SHA、三库无PYTHONPATH解析/opt源码均通过。0启动／重启／推理／GPU／8035／提交推送，8010仍未监听。未来默认Inductor选参未做模型回归，旧gate不自动绑定。以下pin047保留说明为历史。

2026-10-26 [eng073 env-trim001已完成](eng-073-start-model-script-sync.md)：start-model.sh新SHA8703b935，四项自定义cache/DB路径与PYTHONDONTWRITEBYTECODE／旧DIAG清理项已移除，库使用默认cache行为；固定pin047所需PYTHONPATH／DIAG047_CONFIG及完整模型argv／平台／算子设置保留。原脚本备份为`start-model.sh.bak-eng073-envtrim-20261026`，主机／容器语法与SHA、5成员manifest独立回读通过，源码／容器／未监听8010不变；没有删除cache或执行启动、新推理／GPU／8035／提交推送，无新模型gate／性能结论。以下准备／旧SHA为历史。

2026-10-26 [eng073续行env-trim001](eng-073-start-model-script-sync.md)：用户要求精简非必要cache等变量，准备恢复四库cache/DB默认路径、去掉PYTHONDONTWRITEBYTECODE与旧DIAG清理项；固定pin047所需PYTHONPATH／DIAG047_CONFIG及模型argv／平台／算子设置保留。只更改启动文件并备份，不删除cache、不启动／重启／推理／8035或提交推送；执行前命令SHA已记录，新模型结果not_run。以下为前一阶段及历史。

2026-10-26 [eng073启动入口已更新](eng-073-start-model-script-sync.md)：指定`/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`已同步最新验证配置，新SHA d71854f0，原0755及nohup／service.log接口保留，原脚本备份为同目录`start-model.sh.bak-eng073-20261026`。完整模型argv／全部环境策略与eng072相等，host／container实际SHA／bash -n及5成员manifest独立回读通过，关键源码／容器ID不变；0启动／重启／推理／GPU／8035／提交推送，当前8010仍未监听，不签新模型通过或gate。以下为执行前及历史。

2026-10-26 [eng073用户启动入口同步](eng-073-start-model-script-sync.md)：仅将最新eng072／acc021／acc022已验证配置交付到指定start-model.sh，保留原nohup／service.log接口、BF16及修复，执行前备份与命令SHA已冻结。当前容器running但8010未监听；不执行启动、不发推理／GPU、不访问8035／提交推送，无新gate或性能结果。下文健康空闲为10月24日历史。

收尾确认：acc021／acc022全部终态和CPU审计已归档，ERQA新增5份审计文件SHA回读通过，monitor `qwen3-8-ppu07-mm16-accuracy`已产品确认deleted；全suite598次模型HTTP均200／0重试。保留健康空闲BF16／image16的8010等待用户方向，不自动启动新评测或性能。下文monitor待删除为执行前记录。

2026-10-24 当前多模态／16图／BF16同一8010的C64串行完整精度全部结束：[GPQA acc021](acc-021-full-gpqa-mm16.md)175/198＝88.3838%≥88%，有效原生gate；[ERQA acc022](acc-022-full-erqa-mm16.md)251/400＝62.75%，无预冻结阈值／同配置baseline，仅原生score。ERQA400完整wire／真实ID／native结果、3077原manifest／701冻结输入／125原生源码及630图SHA独立CPU核验通过，峰值在途64、400次HTTP200、0重试／超时／空final／60K截断；GPQA9题60K空final仍计错，非网络超时。原suite／evaluator／helper已退出，source前后当前／API3459214不变，health200空闲KV／抢占0；保持BF16／image16修复及encoder graph关闭，0重启／smoke／8035／提交推送，无新性能任务。两阶段终态已归档，monitor待删除；不直接推导开启多模态前后精度等价或16图C64容量结论。以下为历史。

2026-10-24 [acc021 GPQA已通过](acc-021-full-gpqa-mm16.md#本轮gpqa终态175198通过erqa继续原队列)：strict175/198＝88.3838%≥88%，198唯一题／396双filter行／80原manifest及198完整API-prompt逐题映射经独立CPU审计、原生gate check通过；198次HTTP200、0真实客户端超时。9题60000长度后final=None转TIMEOUT占位计错，另189正常stop／thinkend／EOS，不混称网络超时或因果等价。原[acc022 ERQA](acc-022-full-erqa-mm16.md)已自然串行开始400题C64，尚无终态分数；source前后当前／同一API3459214不变，0重启／新smoke，BF16／image16／修复保留、encoder graph关闭。monitor继续只读ERQA，不启动性能／8035／提交推送。以下为历史。

2026-10-24 新授权[acc021 GPQA](acc-021-full-gpqa-mm16.md)→[acc022 ERQA](acc-022-full-erqa-mm16.md)串行全量C64：两项预检通过，49／652冻结输入与新provenance／16图payload已核验，唯一controller2518158/start554233287已单次launch；GPQA原生runner attempt1/1已开始，ERQA等待，尚无终态分数或gate。复用当前eng072 API3459214／image16／BF16及修复，0新smoke／模型启动／重启，encoder graph关闭；ERQA是400题图文评分、无预定阈值，不冒称纯文本或精度等价。30分钟只读monitor qwen3-8-ppu07-mm16-accuracy已ACTIVE，仅实质结果／首异常／停滞／需处理通知。CPU准备首错及另存v2修正完整保留，不影响正式轮数；无8035／提交推送。以下为历史。

2026-10-24 [eng072多图最小回归已完成](eng-072-multi-image-input.md#终态14请求多图最小回归通过当前16图服务保留)：14/14完整HTTP200，异尺寸／换序／重复图／16图各C1及真实C8正确，双图270／16图183的C1重复完整token分别相同；0空final／截断／重试。异尺寸与16图各8rank真实BF16视觉调用nativeSDPA→Torch wrapper→`/opt/FlagGems` Attention；16图其中2图命中既有encoder cache、14图新增执行，完整16输入／输出均保留。语言capture各7/7、C8前FULL1309、summary FULL1791／unpadded8 FULL184；encoder graph关闭。156原manifest／36冻结输入／父8成员及588项独立CPU检查通过，source前后当前／三库HEAD-index及BF16修复不变，API3459214/start553495020健康空闲、KV／抢占0。仅本轮一次重启／一次精确SIGTERM，monitor已产品确认删除；保留image16当前8010等方向，无8035／全量评测／性能／提交推送，不签formal gate或任意16图C64容量结论。下列为历史。

2026-10-24 13:18+08 [eng072新授权多图最小回归](eng-072-multi-image-input.md#新授权仅一次8010重启及14请求多图minimal执行前冻结)：唯一精确SIGTERM自然排空旧8010后，已单次启动image16／video1／BF16服务，encoder graph与compile仍false。固定6C1＋8C8共14请求、0重试，覆盖异尺寸／换序／重复／16图，来源及replay为前置门禁；36输入与素材／argv独立核验通过。当前权重加载推进、8rank启动来源已有，尚无READY／新HTTP或回归通过；只读30分钟monitor已ACTIVE，禁止二次重启／新负载／8035／全量评测／提交推送，终态暂停并保留服务。下文“未应用”是上一阶段历史。

2026-10-24 用户暂停尚未启动的GPQA／ERQA，转做[eng072多图适配](eng-072-multi-image-input.md)：原生Qwen3VL逐图特征／占位符／MRoPE／DeepStack链路已有，明确阻塞是当前启动参数image1。准备仅改image16、video仍1的NOT-APPLIED配置及原argv回退副本；56项CPU抽取方法／替身检查通过，8份产物SHA回读一致，三库／vLLM生产源码0修改。当前8010仍原实例image1、健康空闲、prompt1944／generated1140不变；BF16及修复保留，0重启／推理／GPU／8035／提交推送。**候选未生效，多图设备／模型回归incomplete，等待另行重启授权**；16图C64显存／吞吐无保证，不自动恢复全量评测，monitor保持暂停。

2026-10-24 [eng071图片／视频最小回归通过](eng-071-ppu-image-video-minimal.md)：用户授权更正固定日志校验条件后，沿用同一8010，12/12 HTTP200（6图“红色”、6视频“先红，后蓝”）、两类C1完整token相同、真实C8及语言FULL replay通过。两媒体各8rank实际BF16 Tensor进入native SDPA→Torch SDPA→`/opt/FlagGems` Attention函数，16份来源及12份完整raw／token经独立CPU审计通过；原首次工具断言失败／19冻结输入／60manifest仍保留，续行124manifest另存。源码／三库HEAD-index及当前API不变、健康空闲、KV／抢占0；本次续行0重启／信号／重试，eng071总计仍仅一次重启。encoder graph关闭，monitor保持PAUSED，无8035／GPQA／提交推送；仅固定合成媒体minimal，不签formal gate或性能结论。以下eng070“不重启”等为上阶段历史。

2026-10-24 [eng070源码防护已落盘](eng-070-ppu-mm-dispatch-guards.md)：仅目标容器 `/opt/vllm-plugin-FL` 六文件，thead视觉Attention显式选择／绑定SDPA、拒绝未支持的pruning、采帧／timestamp前验证finite positive fps。7项CPU源码契约、六文件语法／Ruff、完整模型数值AST保护及三库源／HEAD／index审计通过，回退原件保留；BF16与现有算子修复不变。8010同进程未重启／未reload，0推理／GPU／8035访问／提交推送，encoder graph不启用，monitor不变。**仅落盘、设备与图片／视频验证not_run，无新gate／性能结论**；旧acc020只保留原op068绑定，不自动给新源码继承。

2026-10-24 [eng069多模态源码审计](eng-069-multimodal-source-audit.md)：图片／视频注册、视觉塔、权重映射、embedding合并与外层MRoPE主链路已接通，但PPU视觉Attention选择／OOT实际SDPA分发不一致，encoder graph有device cu_seqlens转CPU边界，正值视频pruning与模型关闭EVS不一致；均未实施补丁。6878＋18项源码快照SHA核验通过，0 import／推理／GPU／重启／解除暂停／8035访问／提交推送，monitor不变。容器开始paused、收尾外部已变running，本Agent未操作，完整运行绑定不作通过声明；仅源码结论，现有文本acc020 gate不外推多模态。

收尾确认：op068 monitor已由产品确认PAUSED，当前BF168010保留；本案例定向记录核验通过，全仓历史记录问题未在本轮处理。

2026-10-23 19:52+08 [acc020全量GPQA通过](acc-020-full-gpqa-op068-layout.md)：strict **176/198＝88.8889%≥88%**，198唯一题／396双filter行、70原manifest／49冻结输入、完整token与当前源／服务绑定及原生gate check均通过独立CPU审计。[op068](op-068-thead-moe-weight-layout-fix.md)当前组合的精度阻塞已清除；198次HTTP200、0真实客户端超时，但11题达到60K后空final→`<TIMEOUT>`占位，均计错，不能混称网络超时。原评测进程退出，8010同BF16实例健康空闲。写回后暂停monitor，不启动新性能；P1K Prefill/Decode/Mixed稳态基线及四场景验收仍未交付，不宣称端到端倍数。完整原件／首错与CPU审计路径见同一记录。以下是历史快照。

2026-10-23 18:16+08 [acc020只读监控](acc-020-full-gpqa-op068-layout.md)：原评测仍运行，当前BF16／op068实例8010健康，已有完整返回健康审计未见新异常，源与冻结输入一致；尚无终态分数或gate。继续原monitor，不新增推理／服务操作／性能测试。以下按时间保留。

2026-10-23 17:23+08 [op068模型最小回归通过](op-068-thead-moe-weight-layout-fix.md)：10完整HTTP、2C1 token相等、8rank真实完整MoE入口、两类capture各7/7、C8前FULL1136／终态1764及独立CPU审计通过，101原manifest与3审计成员回读一致。既有[acc020](acc-020-full-gpqa-op068-layout.md)控制器已17:17:43自动开始同实例198题/C64全量GPQA，0额外smoke／0新服务启动；新provenance／preflight／source与当前8010绑定通过，正在正常收集，无终态分数或gate。只读monitor继续，正常推进不通知；P1K性能尚未启动，不宣称旧11题超时或端到端回退已解决。以下加载／停服记录均为历史。

2026-10-23 16:53+08 op068新模型实例已16:44单次启动，加载／JIT中（尚无READY／新请求），原10条最小回归由唯一controller2113424执行。后继[acc020](acc-020-full-gpqa-op068-layout.md)控制器2462106已交付，仅等待“minimal终态＋独立CPU审计通过后→同契约198题/C64正式GPQA”；不再启动或重启模型服务。复用30分钟只读monitor qwen3-8-ppu07-op068。正式新gate前不叠加性能改动。

2026-10-23 用户恢复当前版本性能优化：read-only确认8010已停、物理8–15空闲、op068修复cac5b989与三库现有改动保留。先单次启动当前BF16／完整MoE版本做2C1＋8C8、capture／replay及8rank实际来源；通过后补同契约全量GPQA，清除acc019低分阻塞后再建立P1K阶段稳态基线。当前尚无新模型或性能结果，不升级源码／选参、不访问8035／提交推送。复盘及执行前命令SHA见[op068续行](op-068-thead-moe-weight-layout-fix.md#2026-10-23-主任务继续优化当前版本模型验证执行前冻结)与state的review-op068-resume-20261023；以下停服记录属上一阶段。

2026-10-23 [op068修复已提交独立正式PR #989](https://github.com/flagos-ai/FlagGems-vllm/pull/989)，head `058056c3`，仅thead自动权重转置策略删除及原测试文件（2文件+150/-65），不混入#959／#982。既有50项算子／16capture／64replay证据已回读；提交前6项CPU契约、54项CI工具测试及改动文件pre-commit通过。首次rule-check的模块marker识别问题仅用新增三类测试显式marker修正，测试逻辑／生产源不变；新head rule-check与basic ci均成功，设备jobs跳过（不计硬件验证）。本轮0容器修改／服务操作／GPU或推理，原8010停服决定不变；模型精度／性能仍未新增验收。细节见[同一op068记录](op-068-thead-moe-weight-layout-fix.md#2026-10-23-独立pr发布)。以下为发布前历史。

2026-10-23 15:25+08 侧对话独立修复：[op068 thead MoE原始权重布局PR候选](op-068-thead-moe-weight-layout-fix.md)。两文件+147/-65删除自动转置／缓存／显存门禁，kernel／选参／原测试AST保持，回退原件及其他修复／三库HEAD-index不变。原共卡方案被拒后，用户新授权停止原8010：精确API一次SIGTERM自然排空，**8010现保持关闭，未重启**；独占物理15对最终补丁单次50项FP16/BF16数值／边界／权重更新测试全部通过，16capture／64replay／110检查，max relative-L2约0.00606。945新产物SHA和110份CPU oracle独立重建审计通过（report822cc798）。PR为有硬件证据的独立审阅候选，上游基线／CI仍待提交前核对；模型minimal、GPQA和性能均未跑，不称旧11超时或端到端回退已解决。无8035／强杀／提交推送，不改变主线程决策；早期blocked证据保留。

2026-10-23 [op067关闭自动转置的独立算子/graph对照完成](op-067-moe-transpose-ab.md)：两组B/C/R、选参及修复逐项不变；126数值检查/30capture/120变化与恢复replay通过，20对B1/C1输出逐位相同。冷缓存单层完整MoE graph成本显著下降，重新开启后回退复现；最大测量spread2.45%/B-R漂移1.43%，2015原件及CPU审计通过。线上8010身份/源码/计数完全不变，0模型请求/重启/GPQA/8035访问；只保留证据，不部署，不宣称模型倍数或旧超时已解决。

| op067合成M，ms/完整算子graph | B转置开 | C关闭 | R重新开 | B/C（非模型倍数） |
|---|---:|---:|---:|---:|
| 1 | 2.513918 | 0.033558 | 2.533894 | 74.91× |
| 8 | 2.551588 | 0.084822 | 2.576526 | 30.08× |
| 64 | 3.175314 | 0.670138 | 3.138356 | 4.74× |
| 128哨兵 | 3.404422 | 0.867828 | 3.383336 | 3.92× |

2026-10-23 [acc019继续定位MoE选参/转置缓存](acc-019-full-gpqa-thead-full-moe.md#阶段结果首要嫌疑收敛至4项全局转置缓存选参是第二独立变量)：纯CPU重放原4项模块级缓存，48层/96稳定权重连续三轮均96次miss；若整步复制全层则payload28.125GiB/rank、逻辑读写56.25GiB，非实测流量。S的14个GEMM IR为原布局，F的17GEMM＋2GEMV均转置布局，含GPQA期新编译。小M G1存在宽N填充和102KiB shared、G2部分参数反而减少填充；先单变量隔离转置，再查tile，不能泛称全部配置退化。report a0ee43ee/manifest1e33b386，未改生产源/缓存/服务、未发GPU或推理，实际graph copy频率与时间占比仍未证实；保持failed-score和当前8010。

2026-10-23 [acc019的11题超时只读定位](acc-019-full-gpqa-thead-full-moe.md#11题超时的已有证据定位2026-10-23只读分析)：确认每次API的7200秒total timeout、最多3次总尝试及异常→None→TIMEOUT；11题中8题旧轮次已60K length，另3题旧输出43741/49542/58262 token。最接近入口切换的第二C1折算20.47→6.90 token/s，C8整批23.13→21.88（不同输出长度、非性能验收）；全量日志也明显慢速。已定位分步vLLM默认选参与完整thead独立tile/转置缓存/小M分支差异，强嫌疑为完整入口性能回退叠加原有长推理触发超时；具体kernel成本、数值差异尚未隔离。48/185旧正确而本轮超时，其余2对得失相抵；不把净降2分当数值等价证明。仅分析原件，无新推理/GPU/重启/源码变更/8035访问；保持failed-score与当前服务，等待方向。

2026-10-23 [acc019全量GPQA终态未达阈值](acc-019-full-gpqa-thead-full-moe.md)：strict **174/198＝87.8788%＜88%**，有效证据结论`failed-score`，无gate。198唯一题/396双filter行完整且原始内容无冲突；187份完整正常API响应中174正确、13错答，另11题为失败任务TIMEOUT占位；累计50条真实客户端7200秒超时事件，不能视作50道失败题或推定网络/MoE根因。已返回响应无空final/60K length，11未返回题缺完整token与状态现场。原88manifest成员与新100文件/93源前缀CPU审计通过（report454578fe、manifest37f1b8f3），原controller/eval/helper退出、三库/engine/模型元数据前后当前一致。8010同BF16实例健康空闲，0新smoke/0重启；按精度诊断冻结，暂停新性能优化，等用户方向。monitor已产品确认删除，不自动重测、修复或恢复FP32。下列运行中快照保留为历史。

2026-10-22 [acc019首次客户端超时](acc-019-full-gpqa-thead-full-moe.md#运行中首次真实客户端api超时2026-10-22)：20:29:27首次达到7200秒API时限，截至21:10:02共20条超时日志事件（非20唯一失败题、非None占位）；174完整响应均正常结束，同实例8010健康，24请求在运行，源码/评测工具未漂移。21:20已冻结23文件/源前缀并核SHA，manifest56e57879；CPU工具v1目录错误保留、v2完成，不是模型故障。原评测继续，无重启/新增请求/契约改动，终态分数仍待定；不能归因MoE或网络故障。

2026-10-22 18:29 [acc019完整MoE全量精度已启动](acc-019-full-gpqa-thead-full-moe.md)：复用eng066同一8010，唯一controller3724689已运行单轮198唯一题/C64/strict阈值88%；两次provenance一致、preflight通过，原生缓存命中0，分数待终态。0新smoke/0重启，无8035访问/提交推送，BF16及现有修复不变。新30分钟monitor已ACTIVE，只通知实质结果/完成/失败/需处理，不继承旧gate。

2026-10-22 [eng066完整thead MoE最小回归通过](eng-066-thead-full-moe-entry.md#终态10请求最小回归与独立cpu审计通过)：唯一重启后8rank真实栈证明Plugin apply进入FGVLLM thead fused_experts_impl；两类capture各7/7，C8前FULL1145、终态1878、实际unpadded8/FULL319。2C1均B580且完整token相等，8C8均正常最终B；10/10 HTTP200，0空final/截断/真实超时，只有1唯一短doc2。106冻结文件、完整raw/token、前后当前源码/三repo HEAD/index和8份引用编译模块经CPU审计通过。API1693692/start537709560健康空闲，BF16及全部现有修复保留；监控收尾删除，未访问8035/全量GPQA/提交推送。不继承旧gate，不声明完整数值等价或性能收益。

2026-10-22 [eng066开放PPU完整MoE磁盘入口](eng-066-thead-full-moe-entry.md)：仅原MoE平台条件增加thead＋FGVLLM开关1，不改全局is_cuda，保留LoRA/SiLU/clamp限制；复用原路由测试。两文件回读、126 CPU AST/mock、24证据SHA通过，BF16及现有算子修复/HEAD/index不变，原件备份保留。首次审计换行哈希误报在写入前停止，核实后另存apply002完成，首错不覆盖。8010同实例健康/请求计数不变，未重载/推理/8035/提交推送；新完整路径尚无设备/graph/模型或性能验证，不继承旧gate。下述env065调用链结论仍属运行实例/历史源码。

2026-10-22 MoE调用链只读纠正：当前Plugin完整fused_experts快路径要求NVIDIA-only的PlatformFL.is_cuda，PPU为false，实际为TritonExpertsFL分步→FGVLLM通用alignment/invoke；不能由库内thead no_tle推定Plugin已调用完整API。当前源SHA等于启动冻结值，19成功alignment/14generic GEMM编译产物支持该路径；CPU原/修复对照支持保留PR982平台门禁。空输入max1是公共API零边界修复，当前普通M0走naive且没有模型空alignment命中证据，不当本轮模型故障修复或性能收益。无新推理/GPU/重启/源码或PR变更；详见[env065复核](env-065-flaggems-vllm-routing-cleanup.md#moe-pr必要性与当前plugin调用链只读复核)。

2026-10-22 MoE两项独立提交[PR982](https://github.com/flagos-ai/FlagGems-vllm/pull/982)，head d614a6ae：算子内thead TLE门禁＋三处空extent max1，所有kernel不变；仅MoE源码和原测试文件2项，不混PR959。19 CPU/mock＋530geometry、本地7hooks及54CI工具测试通过，新增设备/compact graph用例未执行；初始rule-check/CLA成功、style运行中，不宣称硬件/模型或性能验收。远端源码/测试精确回读，PR959完全不变，不授予fork额外修改权限，无容器/服务/8035操作；详见[env065记录](env-065-flaggems-vllm-routing-cleanup.md#moe独立pr已提交)。

2026-10-22 [PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)按新授权已转Ready for review（head22194f0b不变）：风格/规则/目标选择/汇总/CLA通过，两个硬件测试/benchmark作业跳过；无失败/待完成检查，无review或未解决线程，仍待维护者审批。正文状态同步首次被安全审查阻止；后续获用户明确授权，仅3处替换草稿标题/状态和已核CI，回读精确一致，其余正文不变。无代码/容器/服务操作。QSA M16已由[PR940](https://github.com/flagos-ai/FlagGems-vllm/pull/940)合入main b4d3382b，不重复提交、不混入MoE；详见[env065记录](env-065-flaggems-vllm-routing-cleanup.md#非moe三个修复点的上游去重核验2026-10-22)。

2026-10-22 [env-065 FGVLLM测试/说明整理完成](env-065-flaggems-vllm-routing-cleanup.md)：旧PLE独立测试合入原test_ple_conv.py，31参数case静态等价，12 graph case/30 replay循环契约保留；旧文件移入回退备份。三说明文件恢复HEAD相对symlink且目标有效；5原件备份/27证据SHA核验通过。全部生产源码/修复、安装、HEAD/index与同一8010健康/计数不变，FGVLLM仅剩2生产＋2原测试差异。CPU工程passed，未执行新GPU/模型/全套pre-commit，无重启/8035/提交推送/新gate；此前Gems磁盘清退仍未重载。

2026-10-22 [env-065 后续Gems旧路径清退完成](env-065-flaggems-vllm-routing-cleanup.md)：`common_slot_mapping`及导出移出，自有MoE alignment和测试恢复精确HEAD；4份备份可恢复、26份证据hash核验通过，7296份源码精确符号引用为0。Gems仅剩index/index_put/randn三项修改；Plugin/FGVLLM修复及editable安装不变。同一8010健康空闲、请求计数不变，未重启/推理/访问8035/提交推送。CPU工程passed，最新磁盘源码模型回归incomplete（用户暂不重载），不签gate或性能结论。

env-065前一阶段：一次8010重启，三个editable库加载规范/opt目录、开关1；8rank来源/56源码SHA核验，capture各7/7、C8前FULL929、2C1均B517 token相同、8C8正常最终B，94份冻结文件和CPU审计通过。此10请求仅1唯一短doc2，属于上述清退前的历史结果，不自动绑定清退后的新磁盘源码；2500模块编译证据和原结果保留，monitor仍PAUSED。

2026-10-22 11:46 [env064只读复核](env-064-remove-pythonpath-override.md#2026-10-22-1146-08按用户要求再次只读核验三库和修复)：清除PYTHONPATH的新进程与新login bash均解析到`/opt/vllm-plugin-FL`、`/opt/FlagGems`、`/opt/FlagGems-vllm`源码editable；7项关键修复SHA吻合，Gems3713/FGVLLM397份src与在线私有副本逐文件相同，BF16模型一致、旧FP32 helper已无。当前8010未重启，仍原私有路径；无生产包初始化/推理/GPU/8035访问或新gate。

2026-10-22 [env-064 root shell旧PYTHONPATH清理完成](env-064-remove-pythonpath-override.md)：备份后仅在root bashrc/profile对精确旧acc011值unset，3种新shell模式无需env-u即可显示FlagGems `5.5.0.dev0+gf0aa7f121.env041 /opt/FlagGems`及FGVLLM `/opt/FlagGems-vllm`；显式自定义路径保持。用户已有终端需自行unset一次；Docker固定ENV未改，直接非shell docker exec仍需env-u。8010原显式环境/身份/health/计数不变，0重启/安装/算子修改/推理/GPU/8035访问/提交推送，无新gate，monitor保持PAUSED。

2026-10-22 [env-063 两个算子库规范源码安装和Git审阅完成](env-063-operator-source-directories.md)：editable分别指向`/opt/FlagGems`和`/opt/FlagGems-vllm`，版本及6613/1063项有效payload不变，i64/randn/MoE v2/PLE/QSA M16保留。真实本地基线f0aa7f12/b4d3382b、分支baseline、fsck通过；VS Code可显示Gems 6修改＋4未跟踪、FGVLLM 1修改＋1未跟踪＋3已有类型差异。4005 Python AST/6关键SHA/干净CPU spec/direct_url通过，25安装文件备份已校验；无依赖升级。当前8010仍旧私有BF16/算子路径，身份/health/计数不变；继承旧PYTHONPATH仍可能遮蔽安装，未修改在线启动配置。0重启/推理/GPU/8035/提交推送，无新gate或模型回归，monitor保持PAUSED。

2026-10-22 [env-062 标准源码目录BF16归并完成](env-062-bf16-source-sync.md)：`/opt/vllm-plugin-FL`模型与已测BF16/PR455原件逐字一致，去掉专用FP32 helper及测试、保留原PR3测试；仅3路径变化，既有i64/QSA M16/PLE/op061v2等算子依赖不改。完整FP32源码/Git/未跟踪文件备份659项及归档SHA校验通过，回退副本在`/opt/qwen38-env062-bf16-sync-20261022/fp32-source-backup`。384 CPU契约及448 Python语法检查通过，Gems/FGVLLM前后相等，暂存路径/mode/blob及cached diff不变（index stat缓存字节更新已补审计说明）。editable仍指向标准目录；当前8010继续加载独立acc018 BF16副本，身份/health不变，**未重启加载此次目录整理**。无新模型回归/gate/性能结论，无8035访问/推理/提交推送，monitor保持PAUSED。

此前用户已决定[保留BF16归约](acc-018-full-gpqa-bf16-reduction.md#用户决策保留当前bf16代码)，依据是acc018正式达标和perf060有界C64性能对照；不称精度等价、不关闭9题长推理或外推四场景性能。上述env062仅统一源码交付位置，原精度与性能证据不改写。

2026-10-22 [acc-018 BF16 TP归约全量GPQA已完成](acc-018-full-gpqa-bf16-reduction.md)：176/198＝88.89%≥88%，原生gate及维护check通过；198唯一题/396双filter行完整无冲突。189份正常final，9份60K length只有reasoning（doc71/88/90/121/127/130/145/147/164），samples的9个TIMEOUT是空content占位，不是网络超时。完整API token/usage/prompt/服务计数及76文件/8rank编译图CPU审计通过，原controller/eval/helper退出。BF16 API1924405/start531054985原实例健康空闲，source前后/当前及安装Git未变，保留全部既有修复；未重启/重跑/访问8035。00:30–09:09网关阻断导致通知延迟，不作模型故障。长推理问题仍存在，无同软件版本FP32正式对照，不能归因BF16或宣称全部修复；同一monitor已由产品工具确认PAUSED，等待用户方向。

2026-10-21 [perf-060 attempt004有效对照已完成](perf-060-fp32-reduction-overhead.md#attempt004终态有效对照完成fp32有小幅c64代价)：统一op061v2和现有修复，仅切TP累计精度。132轮/6600benchmark＋40短doc2护栏＝6640请求/4启动，全部原始SHA及772文件/32编译图CPU审计通过；预热/测量波动和回退漂移均在10%内。按预冻结“零回退”契约三阶段均failed，不是执行失败；FP32保持以供后续方向。

| 缩减case | 单位 | BF16 B | FP32 C | BF16 R | FP32变化 |
|---|---|---:|---:|---:|---:|
| Prefill P1024/D1/C64/N64 | request/s | 2.49241 | 2.46620 | 2.49434 | −1.05% |
| Decode P128/D128/C64/N64 | token/s | 701.94672 | 690.81641 | 699.16511 | −1.59% |
| Mixed P1024/D128/C64/N64 | token/s | 242.99528 | 240.18046 | 243.18490 | −1.16% |
| Mixed C8/N8哨兵 | token/s | 103.95021 | 106.03869 | 106.16502 | +2.01%（R也+2.13%，不归因加速） |

C64 p99 TTFT约+0.87%–1.26%，Decode/Mixed p99 TPOT约+2.08%/+1.20%；仅有界短批次/每角色1独立服务，TTFT/TPOT含调度网络，不是正式四场景或新GPQA gate。final FP32 API3852394/start530581998已恢复、health200且空闲，两类capture7/7、FULL1162、10护栏均正常；保留i64/QSA M16/PLE/FP32与全部现有修复，不访问8035、不追加测试或重启，终态暂停monitor等待用户方向。旧attempt002/003的incomplete历史不混入本轮。

2026-10-21 [op-061 v2最小回归终态通过](op-061-ppu-moe-tle-capability.md#v2终态算子边界graph与10请求最小回归通过)：CPU7dispatch/24606geometry、GPU68direct＋15replay通过；新8010 capture两类7/7、C1重复token570完全相等、实际C8及10/10正常final/诊断B通过。10次同一doc2/max2048，不是正式GPQA。83PT与10份raw/token、CPU终态11文件/SHA通过；API3619570/start529063124健康空闲，原修复/安装Git及v1首错保持。缓存MLIR有19份四阶段v2来源，无TLE字串（不当逐rank时序trace）；性能未测、无新gate。monitor已PAUSED，不访问8035/重跑/提交推送，保留服务等待方向。

2026-10-21 [perf-060 FP32性能回退核验](perf-060-fp32-reduction-overhead.md)：`attempt-003-warm8`于15:55在BF16 baseline Decode末2warm出现18.26%波动（421.62/506.35 token/s），超过10%门槛，原driver已退出；8warm仍未稳定。Prefill基线测量中位1.46059req/s、spread1.31%；候选/回退/Mixed未跑，三阶段维护比较回执均incomplete，不能判断FP32回退。16:44一次final FP32恢复成功，当前API979238/start528613221健康空闲；final10smoke均B且raw/token正常，两C1各493全序列相等，capture各7/7和实际replay通过。全轮共1216性能＋20smoke＝1236请求/2启动，source/Git未变；16:48终态119文件审计通过（summary3c5d2ad9、manifest64bd1f2e），heartbeat产品确认PAUSED，保留健康FP32，不补跑。旧attempt002原样保留。

16:26既有证据CPU定位：MoE alignment误选PPU不支持的TLE cooperative路径；旧IR真实parse及后端检查复现`tle.distributed_barrier`拒绝，18个缓存目录只有source、r8仍重写，失败后DEBUG回退且不缓存不支持能力，重复失败编译机制成立。末两轮总时差约94.61%对应TTFT变化，TPOT只波动2.18%；成本与全部波动归因仍待单变量A/B。审计`diagnosis-existing-001/analysis.json` SHA`e7c68178...`；随后仅形成op061隔离候选，未作用于恢复后的旧实例。

2026-10-21 [env-059 Git审阅信息补齐](env-059-plugin-git-metadata.md)：`/opt/vllm-plugin-FL/.git`恢复真实main/PR455历史，自包含且fsck通过；原PR52文件留暂存区，最终FP32三文件留修改/未跟踪，另如实显示历史复制导致的一份配置symlink→普通文件类型差异。源码/权限/editable绑定/依赖不改，无新提交推送/重启/推理/GPU/8035访问，8010身份health不变，回执e7e0a44d。没有新模型/gate/性能结果，监控仍暂停。

2026-10-21 [env-058目录规范完成](env-058-plugin-source-directory.md)：当前源码editable安装为`/opt/vllm-plugin-FL`，默认解析/清洁CPU实际导入及334份payload核验通过，版本/依赖不变，旧目录保留备份，回执c9af8a88。8010未重启，仍运行原eng053加载模块；0新推理/GPU/8035访问/提交推送，无新模型gate/性能结论，monitor保持PAUSED。以下env057为历史路径。

2026-10-21 [env-057源码安装完成](env-057-editable-slim-plugin.md)：按用户要求执行`pip install -e /opt/qwen38-plugin-eng055-final-20261021`；`editable=true`、默认及clean实际导入均指向该源码目录，334非版本payload及其他源/依赖不变，CPU受保护导入通过，回执7590c32a。替换上轮normal-wheel绑定，备份和旧wheel保留；8010未重启、原身份/health/counters不变，0推理/GPU/8035访问/提交推送，无新模型/gate/性能结论，monitor保持PAUSED。

2026-10-21 [env-056安装完成](env-056-install-slim-plugin.md)：eng055精简版已离线普通wheel安装到容器`site-packages/vllm_fl`，版本`0.3.0rc2.post1+ga696859b9.eng055.d20261021`；335文件、唯一distribution/原entrypoints/默认与清洁origin及受保护CPU根导入核验通过。旧editable绑定已备份、旧源及其他9包未改；初次核验仅过严格统计已拦截可选探测，原错误保留，未二次pip。**8010未重启，仍原eng053实例；0新推理/GPU/8035访问/提交推送**。回执3b42f398，未产生新模型/gate/性能结果，monitor仍PAUSED。

2026-10-21 [eng-055精简主补丁](eng-055-plugin-minimal-fp32.md)已取代eng054作为主交付：**3文件/+242/-10，生产仅+66/-3**，复用原PR模型/算子链路和原测试文件，0新测试文件；移出HC通用化/GDN小整理，合并重复TP测试。410 CPU通过、3原device测试保留但未跑，lint/format/apply-check及645文件交付核验通过（bd65d6cc）；337实际运行包文件与eng053逐字相同。线上8010未改、0新推理/重启/GPU/8035访问/提交推送，监控PAUSED。无新模型/GPQA/性能测量，旧同生产树eng053证据原样引用；父PR格式/CI等仍needs_revision。以下eng054为保留但不再晋级的扩大候选。

2026-10-21 [eng-054工程复用调整](eng-054-plugin-architecture-convergence.md)已在独立候选完成：HC纯数值接入现有CachedOp/registry和DEFAULT/REFERENCE，common去掉GPU反向依赖，保留GPU兼容导出；补真实native MoE方法契约并去重GDN signature检查。535 CPU契约全部通过，lint/补丁apply-check与650文件交付审计通过（6142089e）。FP32/i64/QSA M16/PLE及状态事务保持；**新候选未加载，模型graph/C1/C8与formal/性能not_run，总体minimal=incomplete，needs_revision**。线上eng053身份/源码/token计数不变、无重启/新推理/GPU/8035访问/提交推送，监控仍PAUSED。

2026-10-20终态：[eng-053收敛Plugin最小回归](eng-053-plugin-pr-cleanup.md#终态收敛候选10请求最小回归通过)20:05结束，20:29 CPU审计通过。2C1＋8C8共10请求全部HTTP200/正常final/think-end/EOS、诊断gold10/10匹配，无超时/60K截断/非法访存；两C1均B503完整tokens一致。capture两类7/7，C8前native FULL821，终态前缀7482（真实batch8共517）；86冻结文件SHA/完整raw-token/源码前后当前一致，report60aa8f3e。保留FP32/i64/QSA M16/PLE，新8010健康空闲保持运行，heartbeat PAUSED。无新formal gate/性能结论，不证明旧C64/60K解决；父PR格式/临时CI仍待处理，needs_revision。未访问8035/全量GPQA/提交推送或追加请求。

| 工程ID | 方向/范围 | 主要变量与产物 | 正确性 | 性能效果 | 决定 |
|---|---|---|---|---|---|
| [eng-071](eng-071-ppu-image-video-minimal.md) | 多模态minimal／视觉Prefill＋语言graph | 同实例更正工具日志条件，原12媒体请求预算 | 12HTTP通过、16份真实Tensor视觉来源、两C1重复／C8／语言replay及CPU审计通过 | passed-scoped | 原首错保留，续行0重启；保留同一BF168010，无formal gate或性能结论 |
| [eng-070](eng-070-ppu-mm-dispatch-guards.md) | framework／vision Prefill接入防护 | PPU显式SDPA分发＋视频pruning／fps校验，六文件 | CPU7／原源保护passed；eng071同实例12媒体请求／16来源最小回归passed | 性能not_run | 源码及备份保留，encoder graph关闭，invalid fps／pruning设备矩阵未测，无新gate |
| [eng-069](eng-069-multimodal-source-audit.md) | 多模态源码诊断／vision Prefill接入 | PPU视觉Attention分发、encoder graph、视频EVS配置边界；无代码变量 | 静态快照6896项核SHA，图片／视频／设备测试not_run | not_run | 分析完成，不实施；monitor不变，外部容器暂停状态变化已记录 |
| [op-061](op-061-ppu-moe-tle-capability.md) | operator/improve / PPU MoE alignment | PPU TLE门禁＋零launch extent修复；kernel不变 | v2 GPU68＋15replay、10短doc2/C8及CPU终态审计 passed | not_run | 当前8010健康保留、monitor PAUSED；仅最小回归，无新gate/性能结论 |
| [perf-060](perf-060-fp32-reduction-overhead.md) | 性能 / BF16与FP32归约代价 | op061v2统一、8warm＋3measure、B/C/R | 40短doc2均正常、graph/CPU终态passed | C64吞吐−1.05%/−1.59%/−1.16%；零回退契约failed、测量有效 | FP32已恢复；完整证据归档后暂停监控，无新formal gate |
| [env-059](env-059-plugin-git-metadata.md) | 环境 / VS Code可审阅性 | 仅补Git历史/index；原PR与自有补丁分区 | fsck、文件/权限/绑定不变通过 | not_run | Git可用，原类型差异保留可见，不提交/重启 |
| [env-058](env-058-plugin-source-directory.md) | 环境 / 源码目录命名 | pip -e绑定真实/opt/vllm-plugin-FL | editable/default/clean CPU与payload通过 | not_run | 当前安装路径；旧源备份，线上不重启 |
| [env-057](env-057-editable-slim-plugin.md) | 环境 / 用户要求源码安装 | pip -e绑定既有私有eng055源码 | editable/default/clean origin与CPU导入通过 | not_run | 当前生效安装；替代env056 normal绑定，不重启线上 |
| [env-056](env-056-install-slim-plugin.md) | 环境 / 安装最终精简Plugin | 普通wheel＋私有构建源，不再editable/PYTHONPATH绑定Plugin | 文件/绑定/受保护CPU导入通过；无新模型测试 | not_run | 已安装，线上实例未改；依赖和旧源保留，可回退 |
| [eng-055](eng-055-plugin-minimal-fp32.md) | framework / 最窄FP32主补丁 | 3文件/+242/-10；沿用原PR测试、生产全同eng053 | CPU410 passed；3旧device测试未跑；无新模型测量 | not_run | 主交付；不改线上，needs_revision，旧eng054保留不叠加 |
| [eng-054](eng-054-plugin-architecture-convergence.md) | framework / 复用与分层边界 | 独立HC dispatch＋native MoE契约；增量11文件 | CPU535 passed，未加载、graph/C1/C8 not_run，总体incomplete | not_run | 保留隔离候选，needs_revision；部署须新授权，线上eng053不改 |
| [eng-053](eng-053-plugin-pr-cleanup.md) | framework / 全阶段工程整理 | 三文件FP32最小PR补丁，新候选已加载 | 53 CPU/mock及graph/2C1/8C8通过；10/10诊断匹配，CPU审计通过，无formal | not_run，无speedup | 单次重启，监控已暂停；父PR格式/CI待处理，needs_revision |

此前[二次设计review](eng-053-plugin-pr-cleanup.md#二次整体设计review可收敛与复用边界)的实施现单独归档eng054，eng053源与已测证据不改；factory有runner_cls/args但模型构造未透传，仍避免复制构造器。父PR格式/临时CI问题尚待处理，不宣称正式PR就绪。

2026-10-20正式终态：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)18:40结束，strict177/198（89.39%）>=0.88，198唯一题/每filter完整、原生gate只读复验通过。7条doc71/81/88/127/145/147/164为60K reasoning-only，无提前EOS/真实HTTP失败/非法访存；191条正常final，全部198份API token匹配rank0前缀。9份冻结日志SHA通过、源码/8010绑定不变；无完整逐层现场/大索引覆盖证明，不宣称不收敛根因已修复或性能通过。原8010健康空闲、FP32/i64/QSA M16/PLE修复保留，heartbeat PAUSED，不访问8035/自动重启或重跑，等待用户方向。

2026-10-20模型回归终态：[accdiag052](accdiag-052-ple-fixed-model-regression.md#终态10请求回归通过原8010保持运行)固定2C1＋8C8共10请求/8唯一doc全部HTTP200、非空final/think-end/EOS，诊断性答案10/10匹配，无60K截断/非法访存；两C1完整token相等，doc178正常A2683。all8 capture各7/7、实际replay下界16000，新PLE3份IR证实乘前i64＋CTA barrier；完整raw/token与30份CPU审计SHA通过、8rank日志无丢尾。report9d0c1299/manifestf2e710fd，源前后相同；仅一次启动、保留FP32/i64/M16，8010健康空闲，heartbeat已PAUSED。不访问8035/追加/GPQA，不代正式精度或证明旧C64/60K已解决，无新gate/性能结论；以下历史。

2026-10-20测试合并：[PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)追加22194f0b，将新增测试全并入原test_ple_conv.py，移除两份独立文件；原/合并case集合211相同，重跑211/211通过（191.50秒、192capture/570replay），kernel字节不变，全仓pre-commit通过。3595文件/388cache别名核验，PR最终只改kernel原修复＋原测试两文件；新CI运行中，不重启/发模型请求/访问8035/GPQA。见[051合并终态](accdiag-051-ple-cta-sync-regression.md#合并验证终态与原pr更新)，以下保留历史。

2026-10-20 CI格式修复：[PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)追加bf1b4f2c，仅调整公开测试import分组，仓库root全7项pre-commit通过；kernel/测试主体未改，远端readback一致。新[CI39381445902](https://github.com/flagos-ai/FlagGems-vllm/actions/runs/39381445902)运行中，rule-check通过，尚不宣称上游CI绿灯。未连接PPU/重启8010/访问8035/GPQA。详见[051格式修复](accdiag-051-ple-cta-sync-regression.md#用户授权修正ci格式)，以下保留历史。

2026-10-20上游更新：[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)与[原草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)已补PLE早i64＋最窄CTA同步、独立缺陷归因及合成回归测试；追加commit683e8597，无force/重复PR。公开版再次211/211 passed、192capture/570replay，远端源码/测试回读等于已测字节。PR仍draft，未宣称CI/模型精度通过；8010未恢复，不访问8035/GPQA。见[051更新段](accdiag-051-ple-cta-sync-regression.md#用户授权更新issue958与pr959)，以下保留较早窗口。

2026-10-20最新：[accdiag051资源解除后完整回归通过](accdiag-051-ple-cta-sync-regression.md#续跑终态完整预冻结算子矩阵通过)。13:58逐张重核8–15均空闲，沿用原授权在新私有副本保留i64、仅补CTA同步。**211/211 passed、190.13秒，192capture/570replay**；原生产Decode/spec状态exact均通过，183实际state LLVM含barrier，3980份证据SHA通过。未替换全局安装/更新PR、未恢复8010/发模型请求，不访问8035/GPQA；无正式gate/性能结论，模型回归待新授权。下文资源停止为13:56旧窗口，不是当前结果。

2026-10-20最新：[accdiag051 CTA同步修复/完整回归资源门禁](accdiag-051-ple-cta-sync-regression.md)。用户已授权最窄同步修复和完整算子/graph，但PPU8仍有vLLM worker、占81444/98304MiB，资源隔离不满足；按要求停止，**未部署新源码、未发GPU测试/模型请求、未恢复8010**。不是实际OOM；不抢占、不访问8035/其他设备，不自动重试。050已有i64+barrier实验副本SHA94baded8保持，但旧57次通过不代本轮完整回归。等待资源释放/明确独占设备方向，incomplete/no gate，以下历史。

2026-10-20最新：[accdiag050 PLE状态竞争定位](accdiag-050-ple-state-synchronization.md)。已在算子层复现**跨warp原地读写缺少CTA同步**：同binary无同步66项中41项有差异；barrier57项（含18次graph换索引replay）、snapshot9项、单warp9项均exact。首差1152元素/9CTA可由合法warp交错完整重建；同/新cache与独立进程binary一致，不支持随机缓存损坏/算术误编译。499份证据已核SHA；未改正式源码/PR、未恢复8010或发模型请求，不访问8035/全量GPQA，不宣称60K问题或正式精度已修复。冻结时卡8新出现vLLM占用，未干预、未追加GPU。优先候选窄CTA同步，待用户方向及完整算子回归，无性能数字/新gate；以下历史。

2026-10-20最新：[accdiag049修复与验证](accdiag-049-ple-i64-fix-validation.md)。私有PLE state乘前i64修复通过新增11项边界/canary/graph测试（27次changed-index replay），21份实际state IR确认i64；但combined为29passed/2failed，原生产宽通道状态exact失败，低索引同输入A/B在原版与候选均复现，具体同步/编译机制尚未隔离。**最小回归failed，8010未恢复，0模型请求**；不访问8035/全量GPQA。503份证据已核SHA/大小；[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)与[草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)双向关联，PR精确等于测试源码/测试。等待下一步状态写回定位方向，不宣称模型修复/正式gate；旧失败分数及监控PAUSED保持。下文为历史。

2026-10-20最新：[accdiag048 PLE非法页访问定位](accdiag-048-ple-state-invalid-page.md)。FlagGems-vllm b4d3382/ple_conv.py输出kernel已i64，但state读写kernel仍`row_i32*204800`后才扩位。4特化IR确认缺陷；3驱动dump与Decode指令/PC0x1d8一致，合法row11242产生-8GiB地址偏差，首危险row10486（不是旧generic20972）。高置信度事故机制，未做GPU重现/修复，未解释旧60K因果。588文件SHA/大小核验通过、report9b1dc74d，0重启/推理/GPU/8035访问；等待修复/受控验证方向，不自动恢复或全量GPQA。acc016故障污染incomplete/no gate及性能阻塞不变；下文为历史。

2026-10-20当前：[acc016全量GPQA终态incomplete](acc-016-full-gpqa-fp32-fixed-qk.md)。11:20:40启动，约13分12秒后自然结束；11:33:22驱动`_ple_conv_state_kernel`非法页访问后多rank退出、8010拒绝连接。198唯一题各filter完整但仅39题正常API/38正确，159条真实连接失败占位；原生19.19%为故障污染，不能视为有效模型分数，无gate。39条均stop/think-end/EOS、无空final/60K截断；source-before/after相同、9份服务和8rank新窗口日志SHA/尾部核验通过，当前8rank显式graph replay count3328。缺故障实际索引/首次GPU状态及formal完整逐层logits，根因只到PLE kernel边界、未隔离机制。未重启/重跑/改源/访问8035；heartbeat已PAUSED，等用户方向。旧有效164/198失败和logits1.5差异不改，性能晋级仍阻塞。以下为历史。

2026-10-20当前：[runtime006重启复核](accdiag-047-fixed-tune-qk-state.md#runtime-006终态服务恢复正常旧043前向差异仍为15)仅恢复8010一次，11:05:37就绪，原2C1/max1均200/token1596、无NaN/首异常；all8两条输入/logits/prob/noise一致，重启前005→006 raw差0，**旧043→006 max仍1.5，重启未消除前向差异，不能宣称精度修复**。576GDN清零写回/384QK有限性检查与6256PT/14280冻结文件/21162缓存项核验，报告1e673c90/对照1e8cfa2b/Host5cb42239。源码/FP32/i64/M16/黑名单不变、8035/GPQA访问0；**8010现保持运行健康空闲**，无再次重启。C8/长输出/两次实际replay未覆盖，incomplete/no new gate、旧164/198 failed与heartbeatPAUSED保持。以下均为历史（含旧停服窗口）。

2026-10-20最新：[保存输入GPU A/B终态](accdiag-047-fixed-tune-qk-state.md#gpu-ab-002终态设备复现归约舍入模型差异因果仍未证明)按用户授权精确停止8010（1 SIGTERM，worker自然退出），仅卡15完成4组Q/K×3路径×2重复。当前重放Q/K全部等于模型旧存输出；旧sum仅R32→R64复现6个Q元素的1ULP差异/max0.015625，K输出相同，重复稳定/有限/guard正常。已复现归约舍入机制，但旧norm为语义重建、Q256/fusion仍耦合，不能解释或判定最终logits1.5/60K根因。142文件、5kernel/44cache及原始中间值/完整日志已冻，报告a2b095dc/清单0bfa435d；源码未变、0新模型请求/8035/GPQA。**8010保持停止**，8–15无残留进程，不自动恢复；旧failed/no gate与heartbeatPAUSED不改。以下历史。

2026-10-20前轮资源门禁（历史）：[gpu-ab-001](accdiag-047-fixed-tune-qk-state.md#保存输入gpu算子ab资源隔离门禁新用户授权)当时8–15均已有计算进程，虽free12.3–12.4GiB足够小张量，没有独占空闲卡；为不影响8010未启动GPU进程，incomplete-resource-isolation。该未执行门禁原件保留；后获停止8010授权的002见上，不将001改写为已执行。

2026-10-20最新离线定位：[accdiag-047来源分析](accdiag-047-fixed-tune-qk-state.md#离线终态编译路径为优先嫌疑当前初始化未支持故障旧043未排除)确认当前Q/K配置命中，但Q分支有效R256、K为R32；新增tap同时改变fusion，不能把旧043→047 max1.5当纯调优参数A/B。CPU192组实际输入的R32/R64有14组18元素BF16差异/max0.015625，仅支持舍入机制，不证明最终1.5因果。576GDN清零/192QK权重checkpoint检查正常，GDN不同槽、PLE同槽输出一致；旧043没有doc71中间值，历史初始化及首差层仍未知。主报告0be4a0ce、88文件清单e2de3256；本轮0HTTP/GPU/端点/重启/源码变更/8035，不全量GPQA，旧failed/no gate/PAUSED不改。以下历史。

2026-10-20最新终态：[accdiag-047/runtime005](accdiag-047-fixed-tune-qk-state.md#runtime-005终态两条正常完整sampler数值一致)无损内容去重后仅恢复8010一次，原两条doc71/343/C1/max1均200/token1596；all8 raw logits/概率/noise/seed/RNG逐字一致，576处GDN清零写回、1856项已配对子集一致，无异常标记。每rank约237MiB未再耗尽512MiB预算；6256观察记录+7924张量blob完整还原，14280冻结项/18602缓存成员SHA通过，报告39346897/e9e68d1a。8010同实例健康空闲、driver退出，黑名单/FP32/i64/M16保持，无8035或GPQA。旧043 raw差1.5仍未隔离；仅2C1，无C8/60K/实际两次graph replay，不签gate/性能结论，旧164/198 failed和heartbeatPAUSED不变。以下为历史。

2026-10-20当前终态：[accdiag-047/runtime004](accdiag-047-fixed-tune-qk-state.md#runtime-004异常终态首条成功第二条取证预算耗尽)仅恢复8010一次，绑定修正CPU11项/all8来源/graph通过。首条doc71正常200/token1596；第二条因观察器累计512MiB/rank预算耗尽500，服务已退出，未再次恢复。4120PT/4232冻结项/16042缓存成员SHA通过；384处GDN清零与写回一致、576已配对前沿/状态一致，但第二条最终logits/概率/token未产生，对照incomplete。首条相对旧043 raw差1.5未解决旧精度问题。黑名单/FP32/i64/M16保持，无8035/GPQA，旧failed/no gate/PAUSED保持；报告b57fd76d和43922cbe，以下历史不覆盖。

2026-10-20黑名单续跑终态：[accdiag-047/runtime003](accdiag-047-fixed-tune-qk-state.md#runtime-003终态黑名单越过旧oom但埋点参数读取失败)仅追加`normal_,index_select`，同一私有观察器/固定调优保留，8010一次启动后all8/两类graph7/7 READY；首请求越过旧index_select全池OOM点，但新增观察器把关键字参数当`a[1]`读取，IndexError/HTTP500，**服务退出，第二条未发送**。源码前后一致、16PT/120冻结项/13031编译成员SHA通过，两代cache各8rank均96FP32+2原BF16归约；CPU命名参数绑定8项通过但未部署，报告395ebc8c。未取得目标Q/K/state/logits/prob/token，原精度原因仍unknown；不再次恢复、不访问8035/GPQA，旧164/198 failed/no gate/PAUSED保持。runtime002准备AST错误与首CPU审计缓存代数假设错误均保留，不作模型故障。后续修埋点并恢复需用户方向。

2026-10-20终态：[accdiag-047](accdiag-047-fixed-tune-qk-state.md)仅8010一次重启后all8来源/两类graph7/7就绪，但首条doc71在新增取证`index_select→dim_compress→全池contiguous`尝试分配24.22GiB/free12.98GiB时OOM，HTTP500。**这是取证路径资源故障，Q/K/状态/logits尚未覆盖，不是原精度根因证据。** 第二条未派发、无重试/再次恢复；8010服务已退出。16PT/124冻结文件/10471缓存成员SHA通过，CPU安全单行切片拷贝3项通过但未部署；审计55bbaa3b。完整已产生日志与HTTP保留，未产生token/概率不补造。FP32/i64/M16源码不变，不访问8035/不跑GPQA；需新授权才能修正观察器并恢复8010，旧164/198 failed/no gate/性能阻塞/heartbeatPAUSED保持。以下准备进度为历史。

2026-10-20：[accdiag-047](accdiag-047-fixed-tune-qk-state.md)用户授权固定调优并窄抓doc71 Q/K归约与选中GDN/PLE初始化状态，仅8010一次重载。冻结两条相同343前缀/C1/max1、零重试、无隐藏预热；CPU18项与QK数学AST剥离等价通过，PREPARED282aabc6。保留FP32/i64/M16、不访问8035、不跑GPQA；本轮不保证两次graph replay/C8/长输出，不签gate。旧164/198 failed/no gate/性能阻塞保持，旧heartbeatPAUSED，使用前台进度。

2026-10-19离线终态：[accdiag-046](accdiag-046-offline-cache-compile-state.md)基于043/045旧输入/logits/缓存，64PT/all8输入-位置-RNG-noise一致，rawmax1.1875非简单平移；prob相同因过滤后1596单点概率1。8rank FX归一化相同、400AOTkeys相同、825共同ELF可执行section相同，**未支持同配置随机误编译/文件污染；优先嫌疑为Inductor调优选择**。800CRC bundle安全静态解析，367/400对子图存不同参数（803实例/202key），含17R0变化/9key；Q/K RMSNorm256平方和归约存在block32/64差异，但缺该处实际输入输出和doc71逐层/初始state，具体因果unconfirmed、初始化仍unresolved。报告1786277e/8a84e6cc/83511519/3d80b30b/909a6322；0新推理/GPU/埋点/重启/8035，FP32/i64/M16保持。下一窄取证/冻结配置A-B需新增范围先等用户方向，不自动执行；旧164/198 failed/no gate、性能阻塞和heartbeatPAUSED不变。

2026-10-19终态：[accdiag-045](accdiag-045-rollback044-first-request.md)回退044新增观察后，两条同前缀C1/max1均HTTP200，**首条NaN未复现；all8rank完整logits/prob及input/position/seed/RNG/noise逐位相同，token均1596**。但与043有限参考raw244308项不同/max1.1875，与044有限第二条max4.0625，过滤概率相同不能当跨实例前向恢复。原32+参考64PT/96原件/12656编译成员SHA核验，CPU1f8c2f65/Host00e7aa61，483源精确043、all8FX96FP32分支、i64/QSA M16保留且无44hook。一次重启、2请求/0重试/0追加、driver退出，8010API3385225/start513345302健康idle；无8035访问/全量GPQA，旧heartbeatPAUSED。两类capture7/7但实际replay0/C8未覆盖，通用minimal incomplete，无formal gate；撤销支持证据不等于具体probe根因，新cache/实例仍混杂。旧164/198 failed/no gate与性能阻塞保持，等待新方向不自动追加或重载。

2026-10-19终态：[accdiag-044](accdiag-044-layer38-hc-moe-reduce.md)仅8010一次重启，CPU59/45等价及all8 graph7/7通过，但**首条C1 doc71全部8rank raw248320项及概率全NaN，客户端停补位，仅2/19；doc81/Mixed/38层内部not-covered**。第二条同payload/实际input-position-row-seed-RNG-noise有限，却与043参考raw247334项不同/max3.7832；prob/token相同不代表前向正确。首异常18:39:41.250338/rank6原marker、2原始HTTP/完整token、32PT/113原件/12984编译成员/48旧新前缀PT核验，回执8138bb51/085505c0/6b61a306；all8FX96FP32branch+2BF16embedding、i64/M16源保持。该诊断变体minimal failed/nonfinite，具体探针/编译/初始化时序原因unconfirmed，缺首NaN层和内部状态，不称全因果现场或原38层根因已明。API3170010/start512161050健康idle但不视作数值有效，driver已退出，未补17/重试/再次重启/自动恢复/8035访问/全量GPQA。旧heartbeatPAUSED，后续隔离新tap或重载须用户方向；旧164/198 failed/no gate/性能阻塞保持。

2026-10-19终态：[accdiag-043](accdiag-043-doc81-layer-lmhead.md)仅8010一次授权重载、19/19 HTTP200/C<=8/零重试。**doc81两种前缀/all8rank首差为layer38/output-block的目标row254/channel1407，1 BF16 ULP=6.1035e-5；末token分别在layer39（778）/40（808）出现首差，LM-head输入最终max1.0/.75，raw logits max.34375/.296875、808概率L1 .06210178。** C1重复exact、Mixed token/noise相同不构成数值通过；差异在LM-head前已存在。7056 frontier+192输入采样PT、7434原始证据、14590编译成员SHA核验，all8 native7/7/实际replay>=384、FX96FP32 branch+2BF16 embedding，FP32/i64/M16源不变。证据回执49fdef30/db74debd，层边界reproduced但内部MLP-HCmix/router/专家/preTP未捕获，不点名kernel根因；tap影响融合/同步，短探针不替代60K或全量精度。API2199565/start511947447健康idle，driver自然退出，旧heartbeatPAUSED；不访问8035/追加请求/全量GPQA，进一步新埋点或重启等用户方向，旧164/198 failed/no gate及性能阻塞保持。

2026-10-19离线续查：[accdiag-042](accdiag-042-env041-same-prefix.md#离线续查终态fp32编译执行链已确认首个数值分歧层仍unknown)补核all8冻结FX/生成代码与320个AOT引用SHA，**attention48+MoE48条FP32→allreduce→BF16链/每rank已确认**；Python事件0是编译后直接custom op路径，不能推定修复未加载，原002 incomplete回执保留不改。Doc81相同输入/位置/温度/RNG/noise，96份CPU topk/topp参考最大误差1.49e-8，支持集及token一致，差异定位在**采样前模型前向**。未存当前逐层/TP两侧/LMhead前hidden，不能点名首层或归因新HC/QSA/Gems，旧034不同图不代当前数值证据。CPU2d182e36/744ba254及115+2内容文件SHA通过；本轮0新推理/GPU/源码/埋点/重启/8035，API仍941314/start511645150。后续窄doc81层/最终hidden埋点与一次重载须先获新范围，19/C8方案未执行；i64/M16保持、旧164/198 failed/no gate和性能阻塞不变。

2026-10-19终态：[accdiag-042](accdiag-042-env041-same-prefix.md)已移除本轮8010旧PYTHONPATH覆盖，仅重启一次，all8实际加载env041 masterf0aa7f12+三处i64/旧API兼容，保留Plugin显式/MoE FP32绑定和原生QSA M16。**19/19 HTTP200/C<=8/零重试，但C1/Mixed完整分布一致性未通过**：doc81 778/808 logits最大差1.0625/.5625，808概率L1=.03248567；doc71 343/353 raw最大差1.241943/.703125，353概率L1=.06098020。C1重复全向量exact，Mixed各point实际slot7+7Decode；noise和token相同不代表logits/prob相同。192PT/326原文件/完整日志与13286编译成员核SHA，首差异完整输入/采样保全；CPU28864e3e/Hostc70b0bf8。各rank48MoE FP32实例绑定与源保持，但运行时归约事件0，整体回执incomplete（不能称实际dtype已证明）；all8实际graph replay>=384/QSA命中、无新非法访问/HTTP异常。原CPU001 null usage工具错误保留、仅修CPU新002，不重推理。API941314/start511645150健康idle、源前后一致、无8035访问/全量GPQA，旧164/198 failed/no gate及性能阻塞不变。服务保留本轮候选，monitor仍PAUSED，后续埋点/重启先等用户方向。

2026-10-19安装更新：[env-041](env-041-flaggems-master-refresh.md)已将FlagGems新安装绑定到master f0aa7f12+index/index_put/randn三处i64及4个旧fused兼容模块（8文件本地差异），源`/opt/qwen38-flaggems-master-20261019-f0aa7f12`，本地版本5.5.0.dev0+gf0aa7f121.env041。CPU 8签名/16标量/全src AST、10兼容导出及thead包级导入通过、CUDA未初始化，旧4树源SHA与其他5包版本/来源不变，终态回执29ebc531。**继承Docker旧PYTHONPATH仍覆盖安装，新进程需env -u PYTHONPATH；8010仍旧private038且未重启。**未做模型/算子/graph/全量GPQA或8035访问，旧164/198 failed/no gate不变；不能以master更新或有PR就称主线已含索引修复。

2026-10-19索引修复上游查重与补充：[pr-040](pr-040-index-i64-upstream.md)发现既有index Issue4153/PR5882（bin913）及index_put Issue6411/PR6413（ZenithJoyH），纠正此前本案例检索不全的“未提交”答复；四处已补充本次PPU真实stride/行尾溢出边界/既有micro与IR证据并双向链接，正文逐字读回各一次。没有重复创建Issue/PR、改分支或重跑CI；两PR open/unmerged且有冲突，未解决冲突或声称可合并。本地私有patch验证不冒充两PR当前head测试。零PPU连接/8010或8035访问/模型或GPU请求，旧164/198无gate不变。

2026-10-19上游发布：[pr-039](pr-039-randn-i64-upstream.md)已创建[FlagGems Issue #7269](https://github.com/flagos-ai/FlagGems/issues/7269)与[PR #7270](https://github.com/flagos-ai/FlagGems/pull/7270)，GitHub实际closingIssuesReferences与Issue反向评论双向关联核验；commit56e1065c仅randn地址修复+public API测试2文件，生产源码字节等于038已验证版本。PR open/未合并、CI进行中，新pytest/其他硬件未称已通过；旧7179只关联、不关闭。零运行时变更/新GPU或HTTP推理/8035访问，038健康服务和原164/198无gate不变。

2026-10-19终态：[accdiag-038](accdiag-038-randn-i64-fix.md)**randn输出地址i64窄修复的算子回归与唯一8010启动验证通过**；81安全数值/RNG、18432有界地址、完整BF16 N6400030720/canary/reference及算子graph两次replay正常。新私有Gems12179文件仅randn不同，保留FP32/index-i64/QSA M16及固定Plugin/FGVLLM。8010 health200/all8worker存活/native两类capture7/7，无新SIGSEGV，3份实际服务randn IR均先扩i64再乘，10649编译成员/1.79GB逻辑内容完整SHA核验，startup report2c074210/manifest32c7f8de。原危险大N未运行，旧037工具时序限制保留，不把本轮成功说成完美因果闭环。零HTTP推理/计数0/不访问8035/无全量GPQA；原CPU审计自然结束，备用V2未运行；仅清理自身被动helper、0模型信号，服务保留运行。完整模型minimal/replay仍not_run、旧164/198无gate和性能阻塞不变，monitor仍PAUSED，等待下一范围。

2026-10-19最新：[accdiag-037离线续查](accdiag-037-startup-no-probe.md)发现**FlagGems randn的明确大N地址缺陷**：PLE融合benchmark合成BF16 weight[40000192,160]（N6400030720），store offset先i32乘加再sext64，block1048576产生-2147483648且mask仍true，对应base之前4GiB。036带probe与037无probe的相关TTIR逐字节相同，16600 CPU标量检查及TTIR/TTGIR/LLVM对齐，30派生文件核验；reportce9ea216/manifesta355e519。缺陷confirmed-static，启动崩溃因果strong-suspect、尚无设备A/B或allocator/最终二进制保护证明；不是旧index/index_put i64修复丢失，不声称解决旧GPQA精度。此轮无源码变更/重启/GPU/请求/8035访问，等待窄修复与受控验证方向。

037启动现场：固定env035、关闭模型诊断hook、仅一次8010启动，仍在编译阶段失败；**被动内核事件核实首TP3及all8 raw139/SIGSEGV11，原生栈为PPU formatted-output validate/parse/flush→device synchronize。**完整日志、8段native stack、1692编译缓存和原始退出信号已冻结，源文件FP32/i64/M16均未变；报告4aee7555/manifest53f26570，8010无监听/容器仍运行。外部ptrace取证曾误造成辅助线程暂停，已记录并移除、改被动kernel connector，同实例继续，无第二次模型启动；因此干净A/B因果比较incomplete，不把关闭hook仍崩溃提升为已确认上游bug。模型请求0/8035访问0/无GPQA，工具清理及CONT回执完整，旧164/198无gate/性能阻塞不变。

此前：[accdiag-036](accdiag-036-env035-same-prefix.md)profile/compile阶段worker3退出，0/19请求；离线收敛到PLE大词表embedding融合benchmark窗口（合成weight11.92GiB），305已保存stage链完整、488源级地址/mask比较一致，无原生退出信号。037补到SIGSEGV/native stack但未完成纯版本vs观察器因果隔离。036原始证据和结论保留，不用037覆盖历史现场。

2026-10-19环境更新：[env-035](env-035-plugin-pr455-fgvllm.md)已将默认安装切到Plugin main `a696859b` + PR455 head `3cb373b1`（无新提交合并）+本地显式/MoE FP32保护，FlagGems-vllm main `b4d3382b`（clean，上游已含PPU QSA M16）。两包新/opt私有副本，54项CPU mock及实际正常注册/模型模块导入通过；未加载模型、capture/replay或评测。旧源码/private017 i64不变，**8010仍运行034旧私有环境，不是新安装版本**；同API1767049、health200、9356/3328计数不变。未重载/访问8035/跑GPQA；旧164/198无gate及性能阻塞不改，后续服务切换需用户范围。终态回执80491282，monitor仍PAUSED。

2026-10-19终态：[accdiag-034](accdiag-034-moe-internal-fp32-tp.md)**所测doc81两prefix的C1/Mixed最终logits与概率向量逐位相同（max/L1均0）**。仅Qwen38 MoERunner实例late BF16 TP改FP32→BF16，原guard/fallback/truncation保持；19/19 HTTP200/C8/一次8010重载，既有FP32/i64/M16保留，无8035访问/全量GPQA。48份实际FP32路径、1632边界/192输入采样PT、2011原文件/日志/source/counter、跨033上游288项逐位同值及FP64参考全部核验；两类graph7/7、507FULL/rank。CPUdce66d1d/Host78c8d912/cross02df3e5c，当前8010候选健康idle、driver已退出、监控PAUSED。仅此短同前缀minimal-regression通过，60K/C64/正式198未跑、旧164/198无gate和性能阻塞不变；不自动扩大/再重载，等待下一范围。

2026-10-19终态：[accdiag-033](accdiag-033-layer0-mlp-moe-boundary.md)19/19 HTTP200/C8/仅8010一次重载，FP32/i64/M16保持、不访问8035/不全量GPQA。**all8rank两point的mix/router/topk/shared及routed局部输出/preTP均exact，首post-attn分歧确认在MoE内部BF16 late TP**（max.0078125），HC只传播。1536边界+192输入采样PT、1951原文件/日志尾/source/counter核验；CPU真实环32旋转逐元素/256块100%可解释，支持舍入顺序差、非该次GPU kernel-order trace。最终doc81 logits仍差1.15625/.84765625、808概率L1=.06714148，不算一致性/60K修复。CPUf55c7b66、Hostada0df29、ring87779b86；当前诊断候选idle，监控PAUSED。下一步MoE自有TP FP32→BF16候选/重载需用户方向，未执行；旧164/198无gate和性能阻塞不变。

2026-10-19只读终态：[accdiag-032](accdiag-032-post-attn-moe-reduction-offline.md)CPU重核48份031 post-attn目标全行/跨rank一致，25份当前source/cache复制核验；all8 layer0生成模块确认**MoE shared+routed合并后BF16直接late TP归约，不经外层FP32 helper**。但031未保存MLP mix/router/专家及该归约两侧数值，不能确认首分歧或60K根因；旧028不可代当前候选。CPU b060c6c9/compiled6190b125/Host17b9a387；离线manifest自身空条目工具错误已显式保留并新增内容清单，不冒充模型故障。0新推理/埋点/重载/8035访问，FP32/i64/M16及API259670、9356/3399不变。下一步需先获批仅8010窄MLP/MoE边界埋点与一次重载，建议同19/C8；未执行，不全量GPQA/无gate/性能。

2026-10-19：[accdiag-032](accdiag-032-post-attn-moe-reduction-offline.md)按新指令只读追踪031 post-attn之后MLP/MoE内部归约及现有编译/PT证据；0新增模型/GPU请求、重启或埋点，不访问8035，FP32/i64/M16保持。发现runner内部late归约不经外层FP32 helper，尚未证明首分歧；证据不足时先报最窄埋点方案等方向，不全量GPQA。

2026-10-19终态：[accdiag-031](accdiag-031-model-fp32-tp-reduction.md)模型两处显式TP改FP32→BF16，仅8010重启一次，19/19 HTTP200/C8/0错误重试，不访问8035。**实际all8rank layer0 postTP BF16与HC C1/Mixed已精确一致、匹配FP64参考，但最终doc81 logits/概率未消除**：778/808 raw最大差1.146484375/.9375；808概率L1=.097243741（原.092322201）。FP32本身30/33个1.49e-8末位差完整保留；doc71阴性和C1重复相同。720层边界+192输入采样PT独立CPU核验，1098原文件/日志尾部/source/counter9356-3399通过，CPUc40eb227/Hostb884fb0e。当前8010 API259670/start509233696健康idle、i64/M16保留，driver退出；MLP内部FusedMoE归约未改，不称该路径已覆盖或根因。最终一致性目标failed、不晋级，无新gate/性能或60K修复结论，旧164/198 failed-score不变，监控PAUSED，等待方向，不自动回退/二次重启/追加/全量。

2026-10-19新授权：[accdiag-031](accdiag-031-model-fp32-tp-reduction.md)将模型两处显式BF16 TP归约改为FP32归约再cast BF16；仅8010一次重启、同19请求/C<=8、i64/QSA M16保持，不访问8035、不跑全量GPQA。私有新副本及CPU门禁后执行，原029/030证据不覆盖；结果待验证，旧164/198 failed-score/no gate不变。

2026-10-19终态：[accdiag-030](accdiag-030-tp-reduction-order-shape-offset.md)已受控复现原029四份完整TP输出，机制收敛为**target row0→7改变分块归约顺序的BF16舍入**；单改总shape/allocator起点/peer内容不变。CPU真实环100%元素解释；独立8rank PyNccl固定72payload+1标量/rank、三重复/跨rank一致，FP32仅1.49e-8差、转BF16与FP64参考全同。firstflat20480=global块38400−目标偏移17920。400rank文件CPU/SHA核验通过，report486c9ccf/manifestc1b6fc12/Hostb1105afa；2个零归约启动环境错误与teardown告警完整保留。0新模型请求/服务重启/模型埋点，不访问8035；8010原2727961和counter9356/3523、i64/M16保留。没有把FP32接入模型或证明60K因果，原164/198 failed-score/no gate/性能阻塞保持；下一步模型候选验证需先说明精度改动/预算/必要重载并等用户方向，当前终态不追加。

2026-10-19：[accdiag-030](accdiag-030-tp-reduction-order-shape-offset.md)按新授权先基于029固定8rank输入CPU模拟BF16不同顺序/累加路径，核真实总shape及目标row7偏移；0新模型请求/服务重启/埋点、不访问8035、i64/M16保留。旧029 postTP首差异已确认，具体归约机制与60K因果仍未确认；新实验不签gate、不叠加性能。

2026-10-18终态：[accdiag-029](accdiag-029-tp-hc-boundary.md)19/19 HTTP200、0错误/重试、并发<=8，仅8010一次重启；不访问/操作8035。**all8rank/778与808首差异在layer0 TP allreduce之后、HC之前**（max0.0078125）；归约前本地branch相同，HC residual/norm/logits/weight相同，32份HC输出精确匹配保存输入的FP64公式最后BF16舍入。624完整边界PT+192输入/采样PT、19rawtoken/rank0/counter9356-3523和source一致性CPU复核通过，reportc904d2e4/manifest3a08e5b2；1002原始文件hash通过，仅活service日志追加前缀仍同。508FULL/rank、i64/M16保留，新8010 API2727961健康idle，client退出。TP归约顺序/shape/偏移是下一嫌疑，非已确认通信bug或60K根因；最终logit漂移不同于028，保留observer/cache限制。未跑全量GPQA、原164/198 failed-score/no gate不改，监控PAUSED，等待新方向，不追加GPU测试/请求或重启。以下为历史快照。

2026-10-18 22:28：[accdiag-029](accdiag-029-tp-hc-boundary.md)用户确认8035新实例且明确不需访问，后续不探测/操作8035；8010单SIGTERM自然退出、22:27:43唯一重载完成，新client2739268/start504951961等待READY。19/C8/零重试仅layer0 TP-HC观察，i64/M16保留、19CPU AST及source/image/mount门禁通过；PREPAREDb7652e7a/controller2ab40b3d，后续只监控原client、首次差异保全并CPU审计，不再重启/追加/全量GPQA。旧164/198 failed-score/no gate不变。

2026-10-18新授权：[accdiag-029](accdiag-029-tp-hc-boundary.md)仅8010一次重载、19/C8窄观察第0层TP归约后和HC combine完整输入/输出；19CPU AST检查通过、不初始化CUDA。prepare首行发现8035由null变为新2452583/start504867239/argv242fb3ad且health200，已按保护门禁停止，runtime/private未创建、0部署/重启/推理。8010旧1419056仍health200，等待用户确认新8035保护基准后才续，不全量GPQA。旧028结果及164/198 failed-score/no gate不改。

2026-10-18终态：[accdiag-028](accdiag-028-doc81-layer-first-difference.md)两段合计19/19 HTTP200、0错误/重试、并发<=8，本轮仅8010一次重启；8035再次停服经用户确认后同实例仅余13，不重发前6、不再重载。**all8rank/778与808两点首差异均为layer0 post-attn**，此前5frontier（含GDN局部分支）全目标行精确相同，C1重复全480精确；独立CPU复核192完整矩阵+192输入/采样PT通过。边界收敛至GDN后TP allreduce→HC combine，尚不知二者哪一步/是否数值bug，不能称60K根因已确认。最终logits/prob差异精确复现027（808 prob L1=.11867），同noise下一token不变。23040层PT+192采样/输入约244.3GiB冻结；CPUa4a5c111/Host403080d6/external6e362a3b齐，19token/rank0/counter/source匹配。保留guard旧state/调度间断/新缓存CPU同步限制，未改旧164/198 failed-score/no gate；前台终态、监控PAUSED，下一步若拆TP归约与HC需新观察点/重载先等用户方向，不自动推理或全量GPQA。

2026-10-18进行中：[accdiag-028](accdiag-028-doc81-layer-first-difference.md)用户授权doc81窄逐层19/C8/一次仅8010重启，14CPU正反例及source/image/mount门禁通过；21:22:20仅8010已重载一次、原API单SIGTERM自然退出、0其他信号，8035不动。唯一driver1430400/start504559909等待READY；后续不再启动/重启。只6doc81首次Prefill捕获8rank48层10frontier，全目标行64GiB/rank预算；原19payload及i64/QSA M16不变，新028 marker不继承旧控制面STOP。有限差异与真实异常分开，首差异和全向量/HTTP/token留证，非全量GPQA或新gate。

2026-10-18终态：[accdiag-027](accdiag-027-same-prefix-logits.md)同实例续跑19/19 HTTP200、0错误/重试，未再次重启8010、不动8035，i64/M16保留；192PT CPU解包/SHA与19API完整token/rank0/counter均核验，全8rank实际FULL回放507，4Mixed评分真实slot7+7Decode。C1重复全部逐元素相同；doc71 C1/Mixed raw/prob完全相同；doc81两点raw logits已在采样前不同（max1.67578/0.91406），808点过滤后概率L1=0.11867，同noise仍采494。短点thinkend过滤prob0不能解释48K–60K不收敛。完整向量/原始HTTP/token/日志及CPUreportcf8f5181、终态504ec4e7已保存；旧controlSTOP早冻结selectedstate，不冒充doc81首次差异完整逐层现场。rootnotisolated、旧164/198 no-gate不改；原监控PAUSED，不自动追加请求/埋点/重载或全量GPQA，后续逐层定位先等用户方向。

2026-10-18续跑：[accdiag-027](accdiag-027-same-prefix-logits.md)用户确认旧8035停服预期，已冻结其新实例3460404/start503952504作为只读保护；8010仍3199246/start503876115，未再次重启，i64/QSA M16不变。continuation-003唯一客户端3593385/start503991384按原清单d007a7a3执行19/C8/0重试，19:48:20为4派发/3完成/0错误。旧controller marker/STOP原样保留，新采样PT与HTTP/token独立留存；selected first-state可能提前冻结，不冒充新异常全池现场。仅监控该客户端，终态CPU分析同前缀logits/实际结束概率，无全量GPQA/新gate或性能结论。

2026-10-18执行受阻：[accdiag-027](accdiag-027-same-prefix-logits.md)已按用户授权仅8010窄采样埋点重载一次（旧API单SIGTERM自然退出、0其他信号），i64/M16/Plugin数学不变，新API3199246/start503876115 health200、8rank probe3324ec99与两类capture7/7确认。但唯一driver19:29:57启动时8035已无监听/旧PID退出，保护门禁使其0/19请求即退出；未擅自放宽基准/重发/再重启，无新logits概率或精度结论。首次自动freeze早于worker日志创建的错误原件保留；CPU补冻28文件前缀均SHA匹配（reportf0adee78/manifest7a82452e），全8rank仍step0，无实际replay。8035退出原因未知、未被本任务发信号；等待用户确认其变化是否预期及保护基准方向。heartbeat保持PAUSED，原164/198无gate不变。

2026-10-18准备：[accdiag-027](accdiag-027-same-prefix-logits.md)doc71/81正常与60K轨迹的精确同前缀已冻结（10/30共同输出token，首差异第11/31；prefixes91ce05ae/manifestdf807be9已核）。现有埋点只开放原doc178两个目标，API默认raw_logprobs/20不提供完整raw logits及真实过滤后prob，不能用缺失top20当think-end概率0。需仅8010新增窄采样埋点并重载才完成完整对照，已告用户、等待确认；建议先19请求/上限32/C8/零重试，长前缀/C64不自动扩大。当前仅CPU准备，0新推理/埋点/重启，不动8035，heartbeatPAUSED，无新概率结论或gate。

2026-10-18离线分析：[accdiag-026](accdiag-026-five-lengthcaps-offline.md)5题是题目相关的不收敛/反复复核，非简单token/整段循环（16token片段唯一率98.93%–100%）；没生成think-end/EOS而耗尽60K，不是parser丢final。doc71/81历史48K–54K能结束，doc32曾43K–57K结束且有对有错，doc79/88多轮cap，不能只加预算或归咎新QSA。doc32首Prefill实际42行slot32，其余4条MixedC64，首步索引均<20972/i64有效。288state CPU解包/1728tensor无非有限，但freeze只取row0/max-index、不是4条全部状态，且是共享pool last-writer；缺5题逐层/logits概率，数值根因未隔离。report808ce07d/state62d8622b/source6430ae50及manifest已核；0新请求/GPU测试/重启/改源，不动8035，heartbeat仍PAUSED。进一步同前缀logits/结束概率复现或新埋点/重载先等用户方向，原164/198无gate不改。

2026-10-18终态：[accdiag-025](accdiag-025-target-only-mixed-c64.md)128/128 HTTP200、117唯一doc，123正常final/5个60K reasoning-only（doc32/71/79/81/88），首例17:54:55 doc32；无新提前EOS/非法访存/RPC超时，早晚doc178真实MixedC64均正常A4183/4829，原问题未称修复。128 API完整tokens匹配rank0前缀/服务counter；6348项精确SHA+1项活日志原前缀匹配（追加尾独立冻结，不改旧size mismatch），5168目标PT+288首次state及副本ZIP检查正常，8rank日志尾齐/source一致，audit8404b79e/addendum88712ff0。first-state只剩后4在途、doc32已退，背景无逐层数值reference，不称完整因果；generic12604/packed10813未覆盖20972。双服务原绑定健康idle、driver17:57退出/17:58冻结完成，无重启/补发/全量GPQA；原164/198 failed-score无gate不变，终态暂停heartbeat等待方向。以下为历史在途快照。

2026-10-18 16:35：[accdiag-025](accdiag-025-target-only-mixed-c64.md)早晚doc178均8rank真实63Decode+455首次Prefill/slot63/graphNONE，step9328/13414；最终A4183/A4829，完整API token匹配实际rank0前缀、无提前EOS或空final。128已全派发/82成功返回（71唯一doc）/46在途/errors0；5168已提交目标PT约27.09GiB独立SHA/大小核验通过，背景无完整PT/state-byte-check未执行。generic12604/packed10813未跨20972，无新RPC超时或非法访存/marker；双服务原实例健康。未复现不称修复，原164/198无gate不改；继续原客户端自然排空与ACTIVE只读监控，不追加/重启/重跑全量GPQA。

2026-10-18 16:01：[accdiag-025](accdiag-025-target-only-mixed-c64.md)READY15:59、新8010 API3094123/start502592140，8rank实际新probe/i64来源和两类graph7/7已核。两C1均B538tokens且完整序列一致，8rank真实FULL回放>=2；当前10派发/2成功/8C8在途/errors0，背景focus PT=0。目标实际Mixed C64仍pending，现有唯一driver通过护栏后继续冻结128上限计划；双服务health200/8035原绑定不变，无再恢复/改源/补发/全量GPQA。原heartbeat ACTIVE只读实质变化跟进，无正式精度或性能通过结论。

2026-10-18 15:55新授权续跑：[accdiag-025](accdiag-025-target-only-mixed-c64.md)仅实际63Decode+doc178首次455Prefill/slot63/graphNONE才抓完整张量，背景只轻量索引/映射/token记录，不执行状态字节比较。15项CPU gate/scope检查及私有source/image/mount核验通过，i64/M16/Plugin数学不变；8010空端口已15:54:54恢复一次、0信号/不重启容器，8035原绑定健康。唯一driver3101938/start502594453等待READY，尚不称C64覆盖或精度通过。128请求/C64/零重试计划60359366冻结、首异常停补位/在途取证，原heartbeat复用ACTIVE30min仅实质变化通知；不重复恢复/追加/全量GPQA，旧164/198无gate不变。

2026-10-18终态审计：[accdiag-024](accdiag-024-c64-device-input-layer-logits.md)81,347文件/393,445,194,744字节独立SHA及大小全部一致（report8fa5725a、manifest48ac4d20），8rank完整日志尾部匹配、10成功API完整token等于真实rank0前缀；另7个未提交PT明确排除（4个ZIP不完整/3个虽有目录但未提交），无故障后GPU first-state。8010因300秒sample_tokens RPC超时退出，C64两doc178未派发；原精度根因仍未隔离，本轮execution-incomplete，不签gate。generic3190/packed559、20972未覆盖，最大实际batch42不冒充C64目标。8035原绑定健康；原heartbeat已产品确认PAUSED，未恢复/追加/重跑。后续如采用“背景轻量metadata、仅目标Mixed首Prefill完整抓取”以降低观察器干扰，须先获用户对埋点/重载/新请求的方向，当前不执行。

2026-10-18 15:30首次故障通知：[accdiag-024](accdiag-024-c64-device-input-layer-logits.md)8010在15:20:17因`sample_tokens`300秒RPC超时退出，非已记录非法访存；大规模同步取证约366GiB与超时冲突为嫌疑，原精度根因仍未隔离。10个C1/C8回复均正常（C8 doc178 A2695）；C64初始63条均真实HTTP500，completed73只是请求结束，不是73个成功问题，两C64目标seq73/119未派发。8rank52输入审计issues0/31首Prefill完成，最后42req/8192tokens步在layer6截断，无新GPU first-state，不称完整异常因果现场。driver15:32:54自然退出，81347文件manifest已冻，CPU-only独立SHA审计进行中；8010不监听/8035原实例health200，未恢复/重跑/补发。审计完成后暂停原heartbeat等待用户方向。

2026-10-18 15:04：[accdiag-024](accdiag-024-c64-device-input-layer-logits.md)READY15:01、新8010 API1932757/start502245175、8rank新probe/i64和两类graph7/7确认。两C1均B487tokens且完整序列一致，真实FULL回放>=2；当前10派发/2完成/8条C8护栏在途/errors0，无首异常，C64尚未覆盖，现有唯一driver通过护栏后接续固定118条C64，不补发/扩大/重启。8rank首Prefill实际输入/位置/行映射审计正常，48层输出及真实logits/prob/noise证据已保存待按manifest继续核验。8035原绑定health200，原monitor ACTIVE仅实质变化通知；不是正式精度/性能通过。

2026-10-18 14:57：[accdiag-024](accdiag-024-c64-device-input-layer-logits.md)按用户新授权仅8010补实际设备输入/映射/逐层输出/logits取证并重载一次，旧树单SIGTERM自然退出、未动8035。新Plugin字节同021-v2/i64与M16保留，PREPARED158ce426/requests d54d265f、唯一driver1940573/start502247549已接续等待READY，尚不把启动阶段称为模型复现或通过。固定128=2C1+8C8+118C64/并发<=64/零重试、首异常停补位并自然收集；不重跑全量GPQA。原heartbeat复用ACTIVE30min只读实质变化通知、终态暂停。正式164/198 failed-score无gate和性能阻塞不变。

2026-10-18离线定位：[accdiag-023](accdiag-023-current-formal-offline.md)已完成198题/8rank首Prefill与rank0实际token核对。11提前EOS之外发现doc85同类起始模板污染/invalid final，共12题从首token偏离，全部发生于真实63Decode+1fresh Prefill/slot63/graphNONE；同路径104题正确，不能以负载相关性代替根因。旧新198 API prompt文本及IDs一致；正常/异常均触达大索引，i64地址及已有守卫正常，不支持直接归为旧i32问题。其余11个明确final错答与11个60K耗尽分别记录。report61c1379b/refinement4f49ae2f独立SHA通过；缺当前C64设备输入/逐层hidden/logits，下一步定点埋点/8010重载或新复现需用户方向，尚未执行。请求0/服务变更0、双服务原绑定health200，heartbeat保持PAUSED，正式164/198与无gate不变。

2026-10-18终态：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)完整198题strict **164/198=82.83%<88%，failed-score，无gate**。22无final=11提前EOS（含doc17811tokens）+11个60K截断，另12题错答；无真实HTTP超时/新非法访问证据。两个filter各198、原生provenance/配置/样本/完整当前source与服务绑定通过，22异常API完整token均等于实际rank0采样前缀；observer83文件及terminal-audit001新增46文件SHA通过（report5ba94de8/manifest2e6e31d0）。11:28:56自然结束、约2小时19分，14:23完成审计；双服务原绑定health200/8010 idle，无重启/补发/重跑。generic32884/i64storage合法、packed32775，根因未隔离，继承旧freeze/无新C64逐层logits限制保留。按流程阻止叠加性能优化，原heartbeat已产品确认PAUSED，等待用户方向。以下是历史在途快照，不代表仍运行。

2026-10-18 11:11监控：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)194/198唯一题返回、4在途（145/147/185/186），约122分钟。新增8条60K length/reasoning-only，原11提前EOS不变，共19空final；不是HTTP超时。8条完整API tokens与实际rank0采样前缀一致，无think-end/EOS；CPU-only补冻003 report01e8bb6d/manifest172e4c38、29文件约3.192GB独立SHA核验通过。8rank无索引/state/nonfinite新故障，generic32884/packed32775/i64与关键源SHA不变。双服务原绑定health200、token推进，正式results/samples/分数/gate尚无；保留旧state冻结限制，继续原评测及ACTIVE监控，不重启/重跑/补发。

2026-10-18 10:40监控：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)178/198唯一题已返回、20在途，约91分钟；较上轮新增16题，原11条提前EOS空final未增加，暂无完成的60K截断/真实HTTP或客户端错误。双服务原绑定health200，running20/waiting0/preemption0、KV47.94%、token及8rank日志持续推进；generic32884/packed32775，i64地址合法，新窗口索引/状态/nonfinite/anomaly0，关键源SHA未变。正式results/samples和分数/gate尚未生成，不估ETA；原001/002证据保留，只读继续既有评测，无补发/重启/重跑。

2026-10-18 10:13监控：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)已核验162/198唯一题返回，11条提前EOS空final；新增doc178在09:46:10仅11tokens、无think-end/末248046，API完整token与rank0实际采样前缀一致。全8rank首Prefill97433/slot63/63Decode+455prompt518/graphNONE，108项GDN操作i64地址及storage合法；generic最大32884、packed32775，未见索引/状态/nonfinite错误，但根因未隔离。doc178解析回复/原始native行/完整token与8rank已有窗口补冻output-health002-doc178，report95892491/manifestf0e34770、15文件约2.189GB独立SHA核验通过；无新GPU首次state/C64逐层logits，不冒充完整因果现场。双服务原绑定health200，running36/waiting0，尚无正式分数/gate，继续原198题和只读monitor，不中断/重启/补发/重跑。

2026-10-18 09:44监控：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)仍运行，已核验105唯一doc（returned prompt_text精确内容映射，无未匹配/重复），其中10条2–99token提前EOS/空final、无think-end，不是60K或网络超时；最早doc76/09:12:29，真实C64首Prefill643prompt+63Decode/slot63，API完整token等于实际采样前缀。generic首次实际跨界index22630，当前最大28912，i64地址与storage合法，packed最大26580，未见index/state/nonfinite错误；EOS症状和大索引并存尚不证明因果。新CPU-only快照output-health001/439ac094/manifestf97e4eb6已冻验33文件约1.216GB；旧STOP/state未清除，无新GPU逐层现场，rank-1人工CPU日志不计TP。双服务原绑定health200，运行64/等待0，无HTTP/客户端错误，score/gate仍pending，helper86/90不作正式分数。继续既有正式198题及ACTIVE只读监控，不停/重跑/重启/改埋点。

2026-10-18 09:09启动：[acc-015](acc-015-full-gpqa-current-i64-qsa.md)当前同一8010实例正式198题GPQA/C64、原sampling/max60000/阈值.88；唯一controller3314096/start500159093、nativeUUIDc4dbee4b…，新eval/缓存初始命中0。两次provenance一致/198题和preflight通过，source8d139ffc/service72669721绑定当前private021-v2+i64/M16。09:10:53 running64/waiting0、已有2个正常API响应（不冒充唯一doc数）、无客户端/HTTP错误。无重启/源码/埋点变更、8035原绑定health200。旧STOP/state保留且不当本轮新现场，原monitor产品确认ACTIVE/30min只读，终态核198题/strict分数及gate后暂停；当前score pending，旧176/198或局部结果不替代本轮。

2026-10-17 22:16终态：[accdiag-022](accdiag-022-c64-doc178.md)128/128返回、127唯一doc，客户端22:05退出；doc18在21:58:18首个HTTP200/length60000/contentnull，另doc32/71/115同样reasoning-only截断，无thinkend/EOS、无真实HTTP失败或网络超时。早晚doc178真实C64均正常最终A4440/5226，提前EOS未复现。generic17044/packed16665未覆盖20972，无索引/state/nonfinite/非法访问记录。一次CPU审计5d1af3ac、FINALa23b55a4全部857文件约7.52GB的SHA/大小独立通过；128raw/完整token与计数50296prompt/1576267generation匹配，4异常API tokens与真实采样前缀一致。8rank各36PT已冻无缺失，但step76415冻结时doc18已完成，只是当前4在途与共享池last-writer快照，无C64完整逐层logits因果证据。双服务原绑定health200 idle、i64/M16与完整source树未变、无重启/补发/全量GPQA。长推理不结束及旧doc178 EOS根因仍not-isolated，无正式分数/gate/性能结论。原heartbeat已产品确认PAUSED，等待用户方向。以下为历史在途记录。

2026-10-17新增授权：[accdiag-022](accdiag-022-c64-doc178.md)准备同一8010实例C64持续更替、最多128请求/0重试，早晚两次doc178，其余126背景；保留i64/QSA M16、不动8035、不跑198全量。现有C8逐层/logits前缀不能直接用于C64，本轮只用已加载通用索引/状态/graph和完整HTTP/token、首次异常冻结，不新增埋点/重启。新目录与observer byte边界隔离旧R2证据；实际C64目标覆盖必须核验，不足不补发。尚未启动新请求。以下为上一轮终态。

2026-10-17 19:08终态：[accdiag-021 runtime002](accdiag-021-prefill-layer-sampler.md)10/10请求、8唯一doc均答案匹配且正常输出；doc178在真实Mixed C8下2164tokens/最终A/think-end1942/正常EOS，未复现原24token提前EOS。CPU审计8rank实际455输入与原题一致，384层output/96QSA有效KV及索引正常，264真实prob/noise与实际token一致、首32 EOSprob0/正常终EOSprob1。原始HTTP/完整tokens/状态与首Prefill逐层取证/完整可读服务driver及8rank日志已冻，FINAL709fcdcf、offline7aec6110、post8d0e819b，4905对runtime副本一致，无日志尾部缺失。两客户端进程退出、双服务原绑定/health200、8010 idle且计数精确等于10响应，i64/M16保留、无再重载/补发/全量GPQA。只称本次minimal-regression scoped passed，旧C64根因仍not-isolated，无新formal gate或性能结论；暂停本heartbeat待方向。以下为历史在途阶段。

2026-10-17 18:42续跑：[accdiag-021 runtime002](accdiag-021-prefill-layer-sampler.md)有效KV观察器修正已CPU96真fixture/9反例/7helper验证，仅8010再重载一次，i64/QSA M16不变、8035原4161238保持health200。新API2623908，8rank新probe与两类graph7/7+实际replay核验；10派发/4完成/6在途/errors0，两C1均B535完整token一致。doc178实际7Decode+455Prefill=462tokens/slot7/graphNONE，96QSA有效KV/输出/causal index无异常；8rank首32步EOS概率0、256实际prob/noise argmax匹配。目标最终回复尚未返回，不宣称提前EOS修复。只监控现有唯一driver/client，首真实异常保全并通知，不追加/重启/全量GPQA；monitor原ID ACTIVE。下面准备/旧终态为历史阶段。

2026-10-17新增授权：[accdiag-021](accdiag-021-prefill-layer-sampler.md)在独立runtime-002修正observer有效KV检查；原始全页/padding仍保存，有效KV/实际索引/输出异常仍报。准备最多10新请求/C8/0重试（2C1+7Decode对照+doc178 Mixed），CPU真实已存fixture和注入反例通过后仅8010再重载一次，i64/QSA M16/Plugin模型数学不变，8035只读保护。旧runtime0013条及首次误报警原件不改，无全量GPQA/新gate/性能结论。以下18:24是上一轮终态，不代表新续跑。

2026-10-17 18:24终态：[accdiag-021](accdiag-021-prefill-layer-sampler.md)只重载8010一次，3/11请求实际完成，doc178 C1正常3341token/最终A，未复现旧提前EOS。8rank首轮455实际input IDs与旧正式一致、384层输出/effective KV均finite；首32/EOS共264组真实概率/noise/RNG及完整HTTP/token/约56.7GB原件+冻结副本已审计保存。首次marker是观察器未mask未写KV padding，不是有效QSA NaN；按冻结规则停止派发，Mixed C8未覆盖、整体minimal incomplete、原问题根因未隔离。rank7尾部568bytes已另冻补齐，回执53d4c84c…；两进程退出，8010新诊断实例2000737/i64保留且health200 idle，8035原4161238不动。monitor已产品确认PAUSED。需要修正有效KV检查并再次仅8010重载/补Mixed时先等用户方向，不自动继续，全量GPQA未跑、无新gate/性能结论。以下为本轮较早阶段。

2026-10-17 18:09最新：[accdiag-021](accdiag-021-prefill-layer-sampler.md)按用户授权仅8010一次重载定点probe，保留i64/QSA M16；新API2000737/start494732818，8worker probe来源已核验，权重已加载、正在graph capture，尚0条模型请求。唯一driver2013273等待READY后才按冻结11请求/C8/0重试执行两C1→doc178 C1→小范围Mixed C8，首次异常停补位并冻结逐层/logits/实际prob/noise/RNG/HTTP/token，绝不另起客户端或全量GPQA。8035原保护4161238不动；完整源码审计证明原engine/Gems/FGVLLM/Plugin未变，仅新私有模型tap/观察器和编译缓存不同；新实例无新formal gate，历史176/198保留。原30分钟heartbeat已复用ACTIVE，只读跟进实质变化，终态暂停。以下为较早离线/正式记录。

2026-10-17最新离线诊断：[accdiag-020](accdiag-020-output7-offline.md)已区分6个60K推理截断与doc178的24token提前EOS。doc178首轮采样来自混合Prefill、graph NONE，随后才进入FULL Decode；8rank×36层×3阶段864次GDN搬运/清零/写回检查全部通过，288个EOS状态PT在CPU核验有限，实际last-writer索引padding0→26991与层46一致，未见旧slot残留。缺首token逐层数值/实际输入/logits/采样概率，根因仍未隔离；共享pool记录不是36层独立历史。本次零新请求/埋点/重启，不动8035，不重跑全量；需新增埋点或8010重载时先告知并等待用户方向。acc014有效176/198（88.89%）gate保持，heartbeat仍PAUSED。以下时点为历史记录。

当前终态（2026-10-17 00:34）：op-019共11请求/9唯一题全部结束，doc32正常输出53126token后选A，冻结标准B；其余答案匹配，未复现空最终/60K截断/HTTP超时/非法访存。按冻结停止规则性能**not_run**，当前8010/i64与8035绑定不变、无额外请求或重启。原始HTTP/完整token、8rank日志及服务/可读driver日志已冻结并复核76个不可变文件SHA；没有异常时逐层状态张量，不能宣称完整因果现场或QSA导致错误。暂停heartbeat待方向，无正式gate或性能收益。以下在途状态为历史快照。

00:24+08只读复核：仍10/11条完成、8唯一题，doc32持续生成，8rank推进；无新完成/异常/阶段切换，按通知规则安静跟进。i64/两服务身份不变，性能not_run，未追加请求或重启。

最新heartbeat（23:56+08）：op-019受控11条已完成10条、覆盖8唯一题，均答案匹配且最终正文/token正常；只剩doc32持续生成，不能把在途无最终答案算reasoning-only。8010/8035当前绑定不变、i64保留、8rank继续推进，无新增异常；generic最大740/packed597，20972未覆盖。性能尚未开始，继续既有唯一客户端/driver，不新增请求/重启/全量GPQA；heartbeat ACTIVE，无正式gate。

当前续跑（23:23+08）：用户确认8035旧停服预期，保护基准已更新为当前独立实例4161238；**8010未再次重启**，i64保留。op-019 PPU QSA min16正在`service-qsa-003`做11条最小回归，两次C1均B/544tokens且完整token相同，C8在途；精度全部通过才运行条件36条缩减性能探针，总47/C8/0重试，不跑全量GPQA。首次异常停后续派发、保全现有原始证据并通知；heartbeat只读ACTIVE，无正式gate/性能收益声明。以下17:55与接入准备段保留为历史阶段，不代替本轮状态。

本轮受控验证首异常（2026-10-16 17:55）：[op-019](op-019-fgvllm-integration.md)真实PPU检查前18项通过，第19项新QSA sparse GQA3在eager参考比较失败，2676/3840元素不符、最大绝对误差1.0859375；QSA graph2尚未执行。已按首次异常停止，**模型请求0/99、8010重载0/2、性能not_run**，8010和8035原身份及i64双SHA不变。完整日志/源/编译缓存保全；取证筛选遗漏本地runner帧，首次QKV/索引张量未保存，不宣称完整数值现场。新源码选BLOCK_M8，与既有PPU M8编译风险吻合但尚未隔离；不可归因此前旧GPQA异常。组合候选不能加载/晋级，等待用户另定QSA定位或HC/PLE-only范围，不自动重试、动服务或使用剩余99请求预算；无有效gate。

以下“最新接入准备”为此次数值门禁前的快照，已由上述失败状态替代。

最新接入准备：[op-019](op-019-fgvllm-integration.md)已在**未启用**私有Plugin接入官方FlagGems-vllm 6568039的HC/PLE/QSA窄路径，41项CPU路由/schema检查通过，GDN未改、017 i64双SHA保留；尚未做PPU数值/graph/模型/性能验证。8010/8035实例与原生效源码未动，零重启/零新模型请求。下一步需用户确认仅8010先baseline关闭新组、再candidate启用新组的两次重载；拟99请求/C<=8/零重试，不跑全量GPQA，不自动恢复monitor，无有效formal gate/性能收益声明。

加载前发现旧017客户端17:02自然终态：120/120完成、110唯一doc、在途0；doc32有一条60000 token/length/content=None，原始token无think-end/EOS，其余119条有最终输出。尾8未发，8rank generic最大18736，20972仍not-covered。已按精度定位流程冻结原始回复/token、8rank events与服务固定日志前缀，详见[017终态记录](accdiag-017-index-i64-fix.md)及op019链接。它是旧路径长推理截断，不能归因尚未加载的新算子或宣称与旧非法访问同因；heartbeat保持PAUSED。

## 历史快照（以下“当前”等用语仅指当时窗口）

当前（2026-10-16）：已按用户授权实施[accdiag-017索引i64修复](accdiag-017-index-i64-fix.md)，仅私有017中的gather/scatter先转int64再乘stride。真实35.85GB pool的36项链检查、小池24项API检查、三次changed-index graph replay均过，新IR确认load32→extsi64→muli64。仅8010恢复至API2235393/start484916288，8worker实际修复SHA命中及两类graph各7/7核验；两次C1均B/243tokens、本轮完整tokens一致，scope证据已冻结。唯一客户端2627674运行总128/maxC64/0retry，最新审计10派发/4完成/6在途/error0，C8进行中，C64及排空后8条未完；monitor ACTIVE。模型generic目前只覆盖到571，不能将算子87528覆盖替代模型边界或宣称旧reasoning-only已修复；新编译缓存也是声明差异，未重跑全量GPQA、未影响其他服务、无有效formal gate。下文为原故障及此前局部窗口。

最新事件（2026-10-16 14:17）：用户要求的一次[acc-013全量C64 GPQA复测](acc-013-full-gpqa-c64-diagv3.md)首Prefill实际GDN generic index23520×stride102400跨过20972，i64偏移2408448000而i32溢出为−1886519296。既有v3在危险kernel执行前冻结并抛错，8010退出；不是本轮已经非法访问，也未产生正常回复来验证reasoning-only。8rank共288个selected-state及8个operator文件齐全、324份observer副本SHA通过。原生198个失败占位/0分不可当有效精度，无gate；正式客户端已自然结束，monitor已PAUSED，未重启/修改/重跑。当前需要用户决定最窄i64索引修复及恢复范围；下文128请求未复现及20972-not-covered仅属于此前局部窗口，不与本次危险输入捕获矛盾。

终态（2026-10-16 13:22核验）：accdiag-016于12:48:18自然完成128/128请求、110唯一doc，全部有最终正文、正常think-end/stop/EOS，raw SHA和完整API token/usage一致，最长54740tokens；无非法访问、reasoning-only、HTTP错误、60K截断或已检查状态mismatch。generic gather/scatter最大20536、packed i64实际索引最大18856，**20972危险边界仍not-covered**，未复现不等于修复。311份冻结文件已独立SHA核验，回执位于`accdiag-016-gdn-state-graph-20261016/terminal-freeze-002/report.json`（SHA e2bf24cd11569aa356d6504c7a34f497ed4ee024832e4c496e50245d8cfc65fc）。原heartbeat已确认PAUSED、8010原实例健康空闲，未重启/扩请求/重跑全量GPQA。根因未隔离、无新gate，等待用户方向；下文各时间点为历史快照。详见[终态证据与限制](accdiag-016-gdn-state-graph-evidence.md#1322终态回执128128正常结束20972边界not-covered)。

12:47 heartbeat：126/128完成（108唯一doc），只余seq18/doc90、seq24/doc118生成，error0，全部完成raw/token及最终正文正常。C64早晚目标16/16正常，late doc155为28029 tokens。generic最大20536、packed18856均未变，仍未跨20972；FULL batch2和采样持续推进，无异常，不把进行中的reasoning当作空最终失败。仅继续既有两请求，不重启/加请求，终态后冻结与暂停monitor。

12:16 heartbeat：113/128完成（96唯一doc）、15在途、error0，全部已完成raw/token一致且最终正文正常，仍无reasoning-only、截断或FIRST_ANOMALY。generic最大20536/packed最大18856均未变、未跨20972；8rank及token继续推进，early doc1/late doc142已正常，目标仅late doc155待完成。其他8035已独立换为PID2941880，仅只读记录、未操作。8010原实例健康，不重启、不扩范围，等待原15请求自然结束。

11:46 heartbeat：已全派发128/128，最新完成91、在途37、error0，完成回复均有正文和think-end→EOS。generic int32 gather/scatter实测最大20536，距20972还差436；实际i32/i64地址一致且storage合法，尚未覆盖溢出边界。packed decode最大18856；8rank已检查状态/边界均无报警、无首次异常，服务健康并持续推进。只收集既有在途，终态未触边界则not-covered，不扩范围或重启。

11:18追加重点：用户要求继续监控20972实际大索引边界与首异常，已更新同一30分钟只读heartbeat。当前派发82、完成18、在途64，无异常；generic gather/scatter最大9290、packed decode最大5503，分开判读，尚未跨危险边界。不改运行、不扩128范围；首异常保全实际证据并通知，终态未覆盖则如实记录not-covered，不重启或重跑全量GPQA。

11:16 heartbeat：C64早期目标doc0/doc151正常最终输出（811/1197tokens）；累计派发79、完成15（10唯一doc）、在途64、error0。所有完成raw/token校验通过，8rank已检查索引/状态无报警，gather最大7057尚未跨20972边界；服务health200/running64，日志与token持续推进。无新异常或模型修复，继续原客户端/只读monitor。

最新只读核验（2026-10-16 11:13）：C1/C8共10条控制全部正常最终输出，进入C64持续更替；累计派发74/128、完成10（8唯一doc）、在途64、error0，无reasoning-only、60K截断或FIRST_ANOMALY。8rank索引/storage/状态检查未报警，但最大实际gather索引5007尚未到20972溢出边界，不能排除该假设。一次60秒广播等待告警后各rank及token仍推进。继续既有客户端和只读monitor，无额外请求、修改或重启。后文“C8运行中”为较早快照。

<!-- e2e:summary:start -->

- 案例：20261015-qwen38-flash-next-ppu07-master
- 当前状态：accdiag021_terminal3of11_doc178_C1_normal_probe_padding_false_alarm_C8_not_covered_heartbeat_paused
- 当前候选：master-85cc5ef-required-extensions-normal-fallback-private017-i64-private019-QSA-PPU-M16-private021-prefill-probe
- 下一步：等待用户方向修正仅有效KV区域检查及再次仅8010重载/新冻结Mixed C8；当前不追加请求/自动修复或全量GPQA。旧176/198仅为历史gate，未绑定新诊断实例；8035保持不动，monitor PAUSED。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| accdiag-021 | terminal-C1-normal-probe-padding-stop-C8-not-covered-no-new-gate | doc178-first-Prefill-layers-logits-actual-probabilities-noise | [accdiag-021-prefill-layer-sampler.md](accdiag-021-prefill-layer-sampler.md) |
| accdiag-020 | offline-complete-root-cause-not-isolated-no-new-inference | doc178-first-Prefill-sample-and-six60K-caps | [accdiag-020-output7-offline.md](accdiag-020-output7-offline.md) |
| acc-014 | passed-formal-176of198-output-health7-unresolved-evidence-frozen | — | [acc-014-full-gpqa-qsa-m16-i64.md](acc-014-full-gpqa-qsa-m16-i64.md) |
| op-019 | hold-QSA-candidate-after-scoped-doc32-A-vsB-no-promotion-no-auto-retry-or-restart | reduced-p4k-fgvllm-integration-diagnostic | [op-019-fgvllm-integration.md](op-019-fgvllm-integration.md) |
| env-018 | retain-installed-package-only-no-model-accuracy-or-performance-claim | container-package-update-no-model-requests | [env-018-flaggems-vllm-upstream.md](env-018-flaggems-vllm-upstream.md) |
| accdiag-017 | isolate-load-to-i64-before-stride-multiplication-then-only8010-controlled-validation | generic-index-i64-boundary-and-bounded128-model-regression | [accdiag-017-index-i64-fix.md](accdiag-017-index-i64-fix.md) |
| acc-013 | preserve-first-unsafe-index-state-no-valid-score-no-gate-wait-user-direction | gpqa-diamond-198-c64-existing-diagv3 | [acc-013-full-gpqa-c64-diagv3.md](acc-013-full-gpqa-c64-diagv3.md) |
| accdiag-016 | preserve-terminal-evidence-no-fix-no-gate-await-user-direction-no-automatic-scope-expansion | GDN-index-clear-writeback-graph-first-anomaly | [accdiag-016-gdn-state-graph-evidence.md](accdiag-016-gdn-state-graph-evidence.md) |
| accdiag-015 | no-model-fix-no-valid-gate-wait-for-user-direction | bounded-C64-churn128-and-large-valid-block-ID | [accdiag-015-c64-large-index.md](accdiag-015-c64-large-index.md) |
| accdiag-014 | no-fix-no-valid-gate-wait-for-user-direction | state-zero-and-eight-request-C1-C8-C1 | [accdiag-014-state-zero.md](accdiag-014-state-zero.md) |
| acc-012 | blocked-no-valid-accuracy-gate | gpqa-diamond-198-c64 | [acc-012-full-gpqa-c64.md](acc-012-full-gpqa-c64.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

最新执行状态：用户再次明确批准后，仅8010已重启加载CPU验证通过的私有诊断v3，新API1325804/start483425629。8 worker SHA核验与PIECEWISE/FULL各7/7 capture通过；唯一客户端1382210已启动，两条C1均B/441tokens、完整tokens相同并有实际FULL replay，当前C8合计分发10、完成4、在途6，无异常标记。总上限128含控制、并发64、首异常停止补位，尚未进入C64或达到i32高索引边界。其他8035在本次前后保持986018不动（它此前已独立换实例，旧PID528147保护检查曾在变更前拒绝，已据当前身份重新绑定）。多层共享pool的设备快照只覆盖最后写入，不能冒充独立每层快照。原heartbeat已更新本轮只读监控并ACTIVE，正式GPQA未重跑、根因未隔离、无模型修复/新gate。详见 [accdiag-016执行记录](accdiag-016-gdn-state-graph-evidence.md#第二次仅8010重启用户明确批准后执行)。以下只读阶段的0重启/0埋点为历史阶段，不代表当前部署状态。

2026-10-16 [accdiag-016](accdiag-016-gdn-state-graph-evidence.md)只读审计新增具体地址位宽线索：现有PPU gather/scatter IR有i32索引×stride先乘后扩展，gather LLVM仍保留该顺序。stride102400时索引20972开始行起始偏移溢出，可能负地址或绕回错误位置。旧driver寄存器及scheduler高block-ID与该机制兼容，但未绑定fault kernel hash、实际GPU索引/storage或group→GDN layer，也未证明与reasoning-only的因果关系；根因仍not-isolated。原始日志、516份缓存文本、CPU边界计算及4份LLVM已冻结，服务同实例health200且idle、累计token不变。本轮0新请求/0GPU微测/0埋点/0重启，无修复或新gate。下一阶段需先取得用户对任务私有Plugin/Gems取证埋点及仅8010一次诊断重启的确认；保持graph和采样，不改vLLM源码、不触碰0–7/8035、不重跑全量GPQA。

诊断 `accdiag-013-null-final-content` 已冻结最初32个异常回复：未见标准最终答案，存在乱码/短终止/循环；EOS正常stop不等于答案完整。新增第33个空最终回复则在reasoning中有答案文本，分开保存。评测器把None转成TIMEOUT、阶段计分排除None，均不能代替原始HTTP/输出健康结论。具体触发算子/状态/编译器尚未隔离，详见 [acc-012诊断记录](acc-012-full-gpqa-c64.md#accdiag-013空最终-content--异常-reasoning运行中只读定位)。

17:00原服务因TP7非法内存访问退出，原生strict结果127/198（64.14%），但控制器code1、结束绑定失败，未形成有效gate。198唯一题含61个TIMEOUT标签：35个空content占位、26个服务退出后失败；不是61次真实超时。故障报告位于正式case的 `diagnostics/accdiag-014-service-failure-20261015/freeze-001/report.json`。Python在GDN状态清零→Gems index_put_→nonzero_numpy同步点上报；旧驱动日志进一步明确fault kernel是 `_index_jit_function`，首个错误输入/机制及与乱码的关系尚未隔离。

用户授权后8010已于17:43恢复同一源码/参数候选；188次同步算子微测与CPU逐位一致，但不覆盖大block ID/服务graph复用。冻结8题、原采样不变的C1→C8→C1局部客户端于20:33:53正常完成24/24请求，耗时2小时45分38秒：全部有最终正文、正常think-end→主EOS，无空最终content、HTTP错误、60K截断或非法访问。8条前后C1的完整输出tokens和parsed message均相同，8条C8最终字母与C1相同；不构成新的GPQA评分。

20:58终态核验源码/import/model/tokenizer指纹及运行身份未变，服务health200且idle、客户端exit0。原始证据冻结于正式case的 `diagnostics/accdiag-014-service-failure-20261015/terminal-freeze-001/`，报告SHA `5b99b0b16f003e7e4b006ed3e60d79b1e05733263b78a2b2c0592d57ff157aac`。结论为局部未复现、根因未隔离、无修复/有效gate；仍未覆盖原C64持续更替及高block ID，正式性能blocked。原heartbeat已暂停、8010保留运行，等待用户另行确认受控C64或tensor取证范围，不自动扩展、不重跑全量GPQA。详见 [accdiag-014](accdiag-014-state-zero.md)。

后续用户已授权 [accdiag-015](accdiag-015-c64-large-index.md)：N6000大索引84项检查通过，N22000因显存准入未分配，按用户新指令暂停GPU微测、不动8010，执行冻结128请求/120唯一doc C64局部诊断。原客户端正常响应保存后触发日志重复at字段TypeError，已保留错误和原64请求、不重发；修正控制器仅承接seq64–127，合计在途≤64、总数≤128。存在调度间断，不宣称原生无间断C64或性能结果；逐轮证据见实验文档。

终态：128/128响应完整、120唯一doc，最后于22:56:29返回，请求窗口1小时28分26.933秒。全部有reasoning及最终content、正常stop/think-end/主EOS，raw SHA和usage一致；真实HTTP错误、空最终、60K截断及非法访问均0，最长57530 tokens。8目标早晚16响应完整、8组最终字母一致；不是正式得分，也不证明模型修复。原64条TypeError均为保存正常回复后的日志错误，原控制器rc1且无FINISHED不补造，接续rc0；两客户端均退出。8010原身份及完整源码/import/model/tokenizer指纹一致、health200且idle，服务保留运行。

23:05终态冻结于正式case的 `diagnostics/accdiag-015-c64-churn-large-index-20261015/terminal-freeze-001/`，包含368个manifest条目、全部raw/token/完整客户端日志和服务日志固定前缀。报告SHA `10eef46d1d79921fce2217c18b468a2f644f91633476192de600af2ba2662b29`，manifest SHA `7d948e0c4946820a45307bcc55a7ccd068ba4e2ad617ba0be826fbc128ac29dd`。根因仍not-isolated，无模型修复/有效gate，旧127/198及正式性能阻塞不变。原monitor已确认PAUSED，等待用户另定真实状态/索引取证范围，不追加请求、GPU微测、源码/服务修改或重跑全量GPQA。

- acc023/024 修复后重验：用户已授权再次通过原 `start-model.sh` 单次启动，准备 `repair-validation-002` 的10条最小回归及通过后的串行C32 GPQA/ERQA；旧错误保持冻结。
