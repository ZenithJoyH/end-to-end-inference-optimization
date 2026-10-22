# Qwen3.8-Flash-Next 优化容器复刻至 PPU-07

2026-10-21 [op061 v2最小回归通过](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/op-061-ppu-moe-tle-capability.md#v2终态算子边界graph与10请求最小回归通过)：实际compact零buffer三处launch extent补max1、所有kernel及正参数保持。GPU68项＋15replay、10短doc2（2C1＋8C8，全部正常B）、83PT/完整raw-token及CPU终态审计通过；新8010 API3619570/start529063124健康空闲，capture/replay满足要求。原修复/安装Git/v1首错保留，不访问8035/全量GPQA/性能/提交推送。monitor PAUSED，未签新gate或宣称性能波动已修复。

2026-10-21 [op061 TLE能力门禁受控验证](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/op-061-ppu-moe-tle-capability.md#首失败零token直接算子边界已停止晋级)：私有Gems仅排除PPU不支持的TLE barrier，CPU7 dispatch通过；GPU第一项空输入触发原fallback `arange(0,0)`编译失败，候选与原版该路径AST相同。首PT/失败source/CPU审计已保全，未重试；8010已自然停止、0候选启动/0模型请求，非空/graph/模型/性能未测。整体incomplete，保留全部修复，不访问8035/全量GPQA/提交推送；监控PAUSED，等待方向。不能把旧acc017 gate或CPU dispatch当本候选验收。

2026-10-21 [env-058最终Plugin源码目录规范完成](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/env-058-plugin-source-directory.md)：按用户要求pip -e绑定`/opt/vllm-plugin-FL`，实际导入其`vllm_fl`，editable/default/clean/CPU及334非版本payload核验通过；版本/依赖不变，旧env057源码和绑定备份保留。[env059](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/env-059-plugin-git-metadata.md)已恢复自包含Git历史/index，原PR暂存、自有3文件修改/未跟踪，另保留1份历史配置类型差异可见，不改源码或安装。8010仍原eng053加载模块，无重启/推理/GPU/8035访问/提交推送，无新gate/性能结论。

2026-10-21 [env-056最终精简版安装完成](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/env-056-install-slim-plugin.md)：已将eng055离线wheel安装到目标容器私有site-packages，版本标记eng055.d20261021，335文件/新默认绑定与受保护CPU导入核验通过；旧editable源码/绑定备份及其他依赖保持。8010原实例未重启、0新推理/GPU/8035访问/提交推送，无新模型或正式gate/性能结果，回执3b42f398，监控PAUSED。

2026-10-21 [eng-055主补丁精简完成](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/eng-055-plugin-minimal-fp32.md)：复用原PR模型与原测试文件，仅3文件/+242/-10、生产+66/-3，无新增测试文件或HC抽象；CPU410 passed、3原device测试未跑，目标lint/format/两补丁apply-check和645文件审计通过。实际生产源全同eng053，8010不改，0推理/重启/GPU/8035访问/提交推送；旧054源与证据完整保留，不再作为主交付。无新正式结果/性能结论、父PR格式/CI仍待处理，needs_revision，监控保持暂停。

2026-10-21 [eng-054工程复用收敛](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/eng-054-plugin-architecture-convergence.md)：独立候选完成HC公共dispatch/DEFAULT/REFERENCE、common依赖解耦及真实native MoE方法契约，CPU535 passed、目标lint/补丁及650文件交付审计通过。保留FP32/i64/QSA M16/PLE，未改线上eng053/重启/发推理/GPU测试/访问8035/提交推送。新候选模型graph/C1/C8及formal/性能未测，整体incomplete、needs_revision；不继承旧候选通过结论，等待用户方向。

2026-10-20 [eng-053收敛候选最小回归通过](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/eng-053-plugin-pr-cleanup.md#终态收敛候选10请求最小回归通过)：3文件/+257/-3及53 CPU/mock工程检查完成后，获授权仅8010一次重启；2C1＋8C8全部正常final/诊断匹配10/10、0超时/截断/非法访存，graph capture/replay和真实C8覆盖。20:29 CPU审计86文件/raw-token/source一致通过，证据report60aa8f3e。FP32/i64/QSA M16/PLE保留、新8010健康空闲、monitor PAUSED；不访问8035/全量GPQA/提交推送。无新formal gate/性能结论或旧长推理问题解决声明，父PR格式/CI仍needs_revision。

2026-10-20 [acc-017正式GPQA终态](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)：177/198（89.39%）通过0.88阈值，198唯一题/每filter恰一次、原生gate复验通过。7条60K reasoning-only仍存在，非网络超时；无提前EOS/非法访存，完整API token/采样前缀及冻结日志SHA通过。原8010健康空闲，FP32/i64/QSA M16/PLE修复和源码绑定不变；heartbeat已PAUSED、不访问8035/重启/自动重跑。无完整逐层状态或大索引覆盖证明，不宣称根因解决或性能完成；等待用户方向。

2026-10-20 [accdiag052终态](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-052-ple-fixed-model-regression.md#终态10请求回归通过原8010保持运行)：2C1＋8C8共10请求/8唯一doc全部正常，诊断性答案10/10匹配；无空final/60K截断/非法访存，完整raw/token、all8 graph、3份PLE i64＋CTA编译模块及CPU审计通过。原8010健康空闲、FP32/i64/QSA M16保留；heartbeat已PAUSED，未访问8035/追加/全量GPQA。局部passed不代表正式gate或旧C64/60K问题全部解决；以下历史不改。

2026-10-20 [PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)追加22194f0b：新增测试并入原test_ple_conv.py，边界/graph不减；单文件211/211新回归通过（192capture/570replay），不改kernel、不重启/发模型请求、不访问8035或GPQA，新CI运行中。见[051合并终态](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-051-ple-cta-sync-regression.md#合并验证终态与原pr更新)，以下历史不改。

2026-10-20 [PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)已追加CI import格式修复bf1b4f2c，仓库root pre-commit全过、kernel未改；新CI运行中，未发GPU/模型请求或访问其他服务。见[051](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-051-ple-cta-sync-regression.md#用户授权修正ci格式)，以下为历史。

2026-10-20上游更新：[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)与[原草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)已补PLE早i64＋CTA同步、归因和便携合成回归，commit683e8597，无force。公开版211/211通过、192capture/570replay，源码/测试逐字回读已核；PR仍draft，不冒充CI或模型验收。8010仍未恢复、不访问8035/GPQA。见[051](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-051-ple-cta-sync-regression.md#用户授权更新issue958与pr959)，以下为历史。

2026-10-20最新：[accdiag051](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-051-ple-cta-sync-regression.md#续跑终态完整预冻结算子矩阵通过)后八卡13:58重核空闲后续跑，最窄私有i64＋CTA同步修复211/211算子测试通过，192capture/570replay、3980证据SHA通过。8010未恢复，无8035访问/GPQA/全局安装或PR更新，不外推模型精度，以下为历史资源门禁。

2026-10-20最新：[accdiag051](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-051-ple-cta-sync-regression.md)最窄CTA同步修复及完整回归因PPU8现有vLLM占用/资源隔离门禁停止；没有新部署或GPU测试，8010未恢复、不访问8035或GPQA。旧050 i64+barrier实验副本保留，但不代本轮完整通过；等待资源方向，以下历史。

2026-10-20最新：[accdiag050](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-050-ple-state-synchronization.md)已复现PLE跨warp原地state WAR竞争，非随机cache污染：无同步41/66失败，加CTA同步57exact/含18graph replay；首差1152元素/9CTA逐值可重建，499证据SHA核验。未部署同步修复/更新PR/恢复8010/访问8035或GPQA；后续只做CPU归档，不干预卡8新增负载。正式精度阻塞与旧分数不变，等待源修复方向；以下历史。

2026-10-20最新：[accdiag049](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-049-ple-i64-fix-validation.md)PLE state乘前i64私有修复新增11边界/graph测试通过，但combined29pass/2原生产shape状态失败，原版/候选低索引A/B均复现；整体最小回归failed，**8010未恢复、0模型请求**。503份证据核验，[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)与[草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)双向关联；不访问8035/全量GPQA，无新gate，等待独立状态写回问题后续方向。旧分数/故障现场不改，以下为历史。

2026-10-20最新：[accdiag048](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-048-ple-state-invalid-page.md)确认独立PLE state kernel的32位乘法地址缺陷，stride204800的首危险row10486；驱动3dump反推合法row11242、地址偏差-8GiB，事故机制高置信度。不是通用index/index_put补丁失效；未修复/设备复现，不能解释旧60K。588份既有证据独立验SHA通过，不重启/推理/访问8035，不重跑全量；正式acc016仍incomplete/no gate，监控PAUSED，待用户方向。以下历史首次核验“机制未隔离”由该更窄离线结论补充，不改写原分数。

2026-10-20当前：[acc016全量GPQA故障终态](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/acc-016-full-gpqa-fp32-fixed-qk.md)。驱动在`_ple_conv_state_kernel`报告非法页访问，约11:33:22后多rank退出，8010不可用。原生38/198（19.19%）包含159条连接失败占位，仅39题正常返回，属于`incomplete`故障污染结果、无gate。两filter各198唯一题及原始API tokens/服务/8rank冻结日志已核验，source前后一致；缺首次GPU故障状态/有效索引/逐层logits，不宣称机制根因已查明。未重启/重跑/改代码/访问8035；heartbeat已产品确认PAUSED，等用户方向。旧164/198失败及历史局部数值差不改，性能晋级阻塞。以下为历史。

2026-10-20当前：[runtime006重启复核](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md#runtime-006终态服务恢复正常旧043前向差异仍为15)只恢复8010一次，现同实例健康空闲；原2同前缀HTTP200/token1596/all8重复性正常，无NaN，但相对旧043 rawmax仍1.5，与005重启前raw差0。**重启没有消除差异，不宣称原精度修复**；证据报告1e673c90/1e8cfa2b/5cb42239。保留所有修复、不访问8035、不全量GPQA，2C1/max1不代C8/长推理/正式gate，旧164/198 failed保持。以下历史含停服窗口，不代表当前8010状态。

2026-10-20当前：[保存输入GPU A/B完成](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md#gpu-ab-002终态设备复现归约舍入模型差异因果仍未证明)。获准仅停止8010后，卡15完成4组×3路径×2重复：当前重放输出与模型保存值全等，旧sum仅R32/R64复现6个Q元素1ULP舍入/max0.015625，K同、无NaN/越界或guard异常。报告a2b095dc/142文件清单0bfa435d；完整数值/编译/日志已保全，旧norm语义重建与Q256/fusion限制明确，最终1.5/60K根因仍未证实。**8010保持停止，不自行恢复**；现有源码/修复未变，0新模型请求/8035/GPQA，旧failed/no gate不改。原001资源未执行门禁保留。以下历史。

2026-10-20最新离线：[accdiag-047来源分析](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md#离线终态编译路径为优先嫌疑当前初始化未支持故障旧043未排除)编译fusion和归约变化为优先嫌疑，当前Q有效R256/K32；576GDN清零与192QK权重检查正常，旧043缺doc71中间值，max1.5尚未形成因果证明。0新推理/GPU/重启/埋点/8035；保留全部修复，完整离线报告0be4a0ce/清单e2de3256，不全量GPQA、不签新gate。以下历史。

2026-10-20最新：[accdiag-047/runtime005](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md#runtime-005终态两条正常完整sampler数值一致)观察器改为无损内容寻址去重，仅8010一次恢复、原2C1均200/token1596；all8 logits/概率/noise逐字一致，无NaN/非法访问/预算故障，完整窄取证已校验。8010健康空闲，黑名单/FP32/i64/M16保留，无8035/GPQA。237MiB/rank低于512MiB上限；旧043 raw差1.5及正式精度阻塞未解决，不能由两条max1推断长输出或C64通过；以下历史。

2026-10-20当前终态：[accdiag-047/runtime004](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md#runtime-004异常终态首条成功第二条取证预算耗尽)绑定修正并仅恢复8010一次，首条200/token1596、第二条观察器累计512MiB预算耗尽500，8010退出、不再恢复。4120PT/4232冻结项/16042编译成员SHA通过，已有GDN清零写回与配对前沿一致，第二条完整输出缺失，对照incomplete。保留黑名单/FP32/i64/M16，不访问8035或GPQA，旧164/198 failed/no gate保持。

2026-10-20黑名单最新：[accdiag-047](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md)仅8010一次启动追加index_select，READY后首请求越过旧OOM，但埋点读取a[1]触发IndexError/HTTP500、服务退出，第二条不发。报告395ebc8c、16PT/120冻结项/13031缓存成员SHA核验，FP32/i64/M16保持；CPU命名绑定方案8项通过未部署。未访问8035/全量GPQA，目标数值证据仍缺，需用户方向才再恢复；旧164/198 failed/no gate保持。

2026-10-20最新：[accdiag-047](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md)已使用唯一8010重启机会；新观察器index_select引发全池contiguous 24.22GiB OOM，第一请求HTTP500，服务退出。第二条未发送、不自动恢复；数值目标未覆盖。16PT/124冻结项/10471缓存成员哈希通过、报告55bbaa3b；有界CPU单行拷贝方案仅离线测试，需新授权恢复。FP32/i64/M16保持，不访问8035、不跑GPQA，旧164/198 failed/no gate不改。

2026-10-20当前：[accdiag-047](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-047-fixed-tune-qk-state.md)获仅8010一次重启授权，固定调优配置并采集doc71 Q/K RMSNorm与选中GDN/PLE清零写回；固定2/C1/max1、零重试/无隐藏预热。CPU18项与源/挂载/AST检查通过，唯一driver等待READY；不访问8035、不跑GPQA，FP32/i64/M16保持。旧精度failed/no gate不改，未得新因果结论。

2026-10-19最新离线：[accdiag-046](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-046-offline-cache-compile-state.md)对043/04564PT及两缓存归档核验，所保存输入/RNG同；825共同ELF代码段及400AOTkeys相同，未支持同配置随机误编译。800CRC bundle内367对/803实例/202key的调优参数不同，Q/K RMSNorm256归约block32/64为优先嫌疑，缺真实归约输入输出和doc71逐层/初始状态，因果unconfirmed。全套CPU报告与SHA在独立046目录，0新模型/GPU请求/重启/埋点/8035访问，FP32/i64/M16保持；下一在线取证需先获新范围，不自动全量GPQA，旧164/198 failed/no gate/性能阻塞与heartbeatPAUSED保持。以下为045及更早历史窗口。

2026-10-19当前终态：[accdiag-045](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-045-rollback044-first-request.md)按授权回退044新增tap/实例hook并唯一重启8010，固定两条C1同前缀max1均HTTP200，首NaN未复现；全部8rank完整logits/prob及输入/RNG/noise逐位一致，token均1596。与043有限参考raw仍max1.1875，故仅支持回退关联、根因unconfirmed；新实例/cache也变化且未再启44做反向验证。96当前及参考PT/96原件/12656编译成员SHA核验，CPU1f8c2f65/Host00e7aa61；all8FP32/i64/QSA M16保持、8010API3385225/start513345302健康idle、driver退出。两类capture7/7但实际replay0/C8未覆盖，不发新formal gate/性能结论，旧164/198 failed/no gate不变。未追加请求/重试/再重启/访问8035/全量GPQA，heartbeatPAUSED等待方向。以下为044及更早历史窗口。

2026-10-19当前：[accdiag-044](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-044-layer38-hc-moe-reduce.md)获批仅8010单重启/38层窄内部tap/19-C8，首条C1 doc71全部8rank logits/概率NaN，按既定门禁仅2/19停止；doc81/Mixed/内部状态未覆盖，不能回答原38层根因。第二条同输入/位置/选行/seed/RNG/noise有限但与043参考raw max3.7832；已保全2HTTP/完整token/32PT/113原件/12984编译成员和48旧新前缀PT，回执8138bb51/085505c0/6b61a306，源前后及FP32/i64/QSA M16保持。8010 health200/idle不代表数值通过；原driver自然退出、未补17/重试/再重启/自动回退/8035访问/全量GPQA。具体新增诊断与编译/初始化时序因果unconfirmed，需新范围后再隔离；旧164/198 failed/no gate/性能阻塞不变。以下为历史窗口。

2026-10-19当前：[accdiag-043](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-043-doc81-layer-lmhead.md)已仅8010重启一次、19/19 HTTP200/C<=8结束；doc81两前缀/all8rank首差定位layer38/output-block的row254/channel1407（1 BF16 ULP），末token后续layer39/40和LM-head前hidden/logits继续分歧。首差完整张量/绑定/全部API token及logits-prob-noise与7248PT/7434原件/14590编译成员核验，回执49fdef30/db74debd，FP32/i64/QSA M16保留；具体MLP-HCmix/router/专家/归约根因仍unconfirmed，短探针未验证60K收敛或正式精度。8010本轮实例健康idle，未访问8035/重跑全量GPQA；不再自动追加或重载，新埋点需用户方向，旧164/198 failed/no gate与性能阻塞保持。以下为历史窗口。

2026-10-19离线续查：[accdiag-042](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-042-env041-same-prefix.md)已补全all8 FP32编译路径证明（attention48+MoE48/每rank、生成缓冲dtype及320 AOT引用），不再将Python事件0当修复未生效。Doc81输入/位置/RNG/noise相同，96CPU概率参考最大误差1.49e-8，差异在采样前模型前向；缺当前逐层及LMhead前hidden，首个算子仍unknown。新CPU报告2d182e36/744ba254，原报告不覆盖。0新推理/GPU/源码变更/埋点/重启/8035访问，i64/M16保持，原API同实例、旧164/198无gate不变；下一窄层取证及一次重载须先获范围，未自动执行。以下为历史窗口。

2026-10-19当前：[accdiag-042](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-042-env041-same-prefix.md)已去掉8010旧Gems PYTHONPATH覆盖并仅重启一次，加载env041新版FlagGems，保留FP32实例绑定/i64/QSA M16。19/19 HTTP200/C<=8/零重试，all8 native graph7/7及实际replay>=384、QSA命中；**C1/Mixed logits仍不同，doc81 808点max.5625/概率L1 .03248567，不能通过一致性回归**。C1重复exact、Mixed token/noise相同；FP32实际归约事件未捕获，整体回执incomplete，不把绑定当实际dtype证明。192输入/采样PT及首次差异、326原始证据/完整日志、13286编译成员SHA已核，CPU28864e3e/Hostc70b0bf8。API941314/start511645150健康idle，未访问8035/全量GPQA；原164/198 failed/no gate/性能阻塞不变。服务保留，不再自动重启或追加，以下为此前历史窗口。

2026-10-19 FlagGems更新：[env-041](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/env-041-flaggems-master-refresh.md)已安装master f0aa7f12+保留的index/index_put/randn i64和4个旧融合兼容模块，源`/opt/qwen38-flaggems-master-20261019-f0aa7f12`，CPU源码/生成器与实际包级导入通过、CUDA未初始化。旧源码及其他依赖未改，**当前8010仍旧private038，未重启；Docker旧PYTHONPATH仍覆盖新安装，新进程需去除该覆盖**。零模型/算子请求/8035访问/全量GPQA，终态回执29ebc531，无新精度gate或模型graph验证。

2026-10-19发布：randn修复已提交[Issue #7269](https://github.com/flagos-ai/FlagGems/issues/7269)和[PR #7270](https://github.com/flagos-ai/FlagGems/pull/7270)，双向关联已核验，详见[pr-039](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/pr-039-randn-i64-upstream.md)。PR仅算子地址修复和公开API回归测试；未合并/不宣称新pytest已通过，本轮没有服务或GPU变更。

2026-10-19当前：[accdiag-038](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-038-randn-i64-fix.md)独立Gems副本randn输出地址乘法前i64修复已通过算子回归及唯一8010启动，保留FP32/index-i64/QSA M16与固定Plugin/FGVLLM版本。完整BF16 N6400030720/canary/reference、算子graph两次重放正常；8010 health200/all8worker存活/native两类capture7/7，10649编译成员独立SHA审计通过（report2c074210），服务保留运行。零HTTP推理/不访问8035/无全量GPQA，不把startup或算子通过当模型精度通过；原164/198/no gate和自动监控PAUSED不变，旧事故因果限制及完整结论以038主记录为准。以下状态为此前历史窗口。

最新状态2026-10-19：[accdiag-036](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-036-env035-same-prefix.md)仅8010一次重载加载env035后，worker3在显存探测/编译阶段意外退出，**8010无监听、19条对照实际0分发/0完成**。全8rank新source/FP32绑定/i64/M16已加载核验，但没有本轮模型graph或logits结果，root not-isolated。完整错误/源码/现有编译产物保留，未访问8035、未二次重启或GPQA；需先定位并另确认恢复，不能引用034局部通过称新版本通过。下方env035安装及034健康状态均为此前历史窗口。

2026-10-19安装更新：[env-035](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/env-035-plugin-pr455-fgvllm.md)默认Plugin已更新main a696859b+PR455 head3cb373b1+本地FP32保护，FGVLLM更新main b4d3382b/上游PPU QSA M16；新私有目录保留旧树及private017 i64。54CPU mock、实际注册及模型模块导入通过，无模型/graph/精度验收。8010未重载，仍034旧source/旧FGVLLM，同身份及计数不变；无8035访问或全量GPQA。不要把安装版本当当前在线版本；旧gate状态不变。

最新局部候选（2026-10-19）：[accdiag-034](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-034-moe-internal-fp32-tp.md)仅将当前模型MoE自有late TP改FP32→BF16，19/C8/仅8010一次重载后，**doc81所测两prefix的C1/Mixed最终logits及实际概率逐位一致**；288项跨033上游同值与实际FP32两侧/FP64参考补齐局部单变量证据。1632层边界、192采样/输入、2011文件及完整日志/source/counters核验。既有FP32/i64/M16保留，不访问8035、不全量GPQA；当前诊断候选idle，未把局部通过称60K或正式精度修复，无新gate/性能验收。原033/更早失败证据全部保留，下方均历史快照。

最新运行时定位（2026-10-19）：[accdiag-033](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-033-layer0-mlp-moe-boundary.md)同19/C8、仅8010一次重载，完整8rank张量证实MLP mix、router/topk、两local专家与preTP同值，**首post-attn差异在MoE自有BF16 late TP归约后**。CPU真实环舍入序列能解释全部元素/256块，HC保存输入公式吻合；不是router或专家局部输出先变，但尚非该次GPU归约顺序直接追踪/60K症状因果证明。1536边界+192采样PT与1951文件核验、所有原始证据保全。FP32/i64/M16保留，无8035访问/全量GPQA；未改内部归约，下一候选须新授权，无新gate/性能结论。下方为此前不同证据等级的历史快照。

最新只读定位（2026-10-19）：[accdiag-032](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-032-post-attn-moe-reduction-offline.md)CPU重核48份031 post-attn同值；8rank当前生成模块确认MoE shared+routed的BF16结果走内部late TP、不经外层FP32 helper。但031无内部张量，**首个MLP/后层数值分歧仍未确定**，需要先获批窄埋点与一次8010重载才能验证。0新推理/重载/埋点/8035访问，FP32/i64/M16和031实例/计数保持，无新gate或性能结论。旧清单自哈希工具错误已单列并附加内容核验回执，原件不改。

最新模型对照（2026-10-19）：[accdiag-031](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-031-model-fp32-tp-reduction.md)已把两处显式TP接入FP32归约后转BF16，19/19/C8/仅8010一次重启，无8035访问。all8rank layer0 postTP/HC的BF16差异消除，但最终doc81 raw logits/概率仍不同（808概率L1=.09724），最终一致性目标未达；当前FP32诊断服务健康idle，不自动回退或续跑。720边界/192采样PT与1098原始文件核验，i64/M16保持，旧164/198无gate/未测性能/60K因果不变。后续仍须定位剩余下游分歧，内部MoE归约本轮未改，不能认定为根因。以下为历史快照。

最新定位（2026-10-19）：[accdiag-030](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-030-tp-reduction-order-shape-offset.md)通过保存8rank输入的真实环CPU算术及独立设备单变量重放，逐位复现原4份TP输出，拆出目标row偏移引起的BF16分块归约舍入；shape-only/base/peer对照不变，FP32转BF16消除该差异。未见测试矩阵内实现错位/越界证据，尚未修改模型或证明60K/正式低分因果。0新模型请求/服务重启/模型埋点、不访问8035，i64/M16保留，原正式164/198无gate不变。

最新受控诊断（2026-10-18）：[accdiag-029](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-029-tp-hc-boundary.md)完成19请求/C8/仅8010一次重载，CPU核624完整边界PT+192输入采样PT，all8rank doc81同前缀首差异在TP归约后、HC合并前。HC保存输入的高精度公式与在线输出精确一致，支持其仅传播TP差异；归约顺序/shape/偏移机制和60K不收敛因果尚未确认。保留i64/QSA M16，不访问8035，不全量GPQA；旧正式164/198 failed-score无gate不改。完整事实及限制以模型实验记录为准，下方均历史交付快照。

当前状态（2026-10-16）：先前acc-012/013受故障污染，无有效正式gate；用户禁止继续全量GPQA。op-019的PPU QSA最小M16后端已通过14项CPU/12事务PPU算子回归；后续按用户授权仅重启8010一次，新API4022615 health200、两类graph capture完成、qsa-only和i64源码核验。23:02等待门禁发现保护端点8035 PID3611426监听消失，唯一driver已退出、原始证据冻结、heartbeat暂停，**模型请求0/47、精度incomplete、性能not_run**。本任务信号回执只有旧8010的SIGTERM，未操作8035，其退出原因未证明，不自动重绑/恢复或继续。详见[op-019事实记录](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/op-019-fgvllm-integration.md)及[当前精度状态](../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/README.md)。下面的“未启动模型”仅指最初环境交付时的历史事实。

后续状态以 [FlagGems master 更新记录](flaggems-master-update-20261015.md) 和 [去除 PYTHONPATH 依赖](remove-pythonpath-20261015.md) 为准；下方源码一致性与启动脚本校验是容器交付当时的历史事实，不能替代更新后的运行核验。

状态：`container_running_verified`。2026-10-15 12:31 +08:00 已启动并完成环境一致性检查，未启动模型服务，也没有产生新精度或性能 gate。

后续用户明确要求更新共享 `start-model.sh`，已按 PPU-07 简版配置完成；此变更见末节，不再沿用共享脚本原来的卡0–7/bond默认值。

用户于 2026-10-15 要求在平头哥07启动最新保留优化环境的容器，并确认可使用共享产物目录 `/mnt/nfs/users/jinghao/qwen3.8-flash`。本任务只创建和启动独立环境，不启动模型服务，不进行精度或性能评测，不停止任何既有服务。

源为 PPU-01 的 `qwen3.8-flash-opt-candidate-20260919`，容器 ID `9b65cc77d73c5ecb9b22f580235b0475e253f18ccca5c2106cb01aba0acfb5e4`，镜像 `sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6`。当前 Plugin HEAD `939600b323c02c21916f1f76bfb4cd8c2b02578d` 加既有补丁，tracked diff SHA-256 `19741357cd4283852ad1540c68353089cb9ea10e5c9cc997852bc28e5c45c461`；私有 FlagGems sql.py SHA-256 `f20c01b48ba749ff42fe3935466c3e658ea9c89c6dbf5bd9d9155b326dc4de4f`。不会自动拉取未经当前环境验证的新提交。

目标名称：`qwen3.8-flash-opt-ppu07-20261015`。远端唯一案例根目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container`。所有命令、镜像导出和校验产物集中于该目录，不修改共享 `start-model.sh`。

简版 PPU-07 专用启动脚本已放入新容器 `/opt/start-model-ppu07.sh`，只保存不执行，语法与 SHA 校验通过。它固定卡 8–15 / TP8 / 8010 / max-num-seqs32 / batched-tokens4096，保留私有 SQLite 修复、卷积 fallback 与 unbounded QSA。PPU-07 没有 `bond`，因此该副本使用实测 UP 且有 IPv4 的 `eth0`、`NCCL_SOCKET_FAMILY=AF_INET`，与 PPU-01 的 bond/IPv6 配置明确不同，未做 TP8 通信或模型精度验证。8010 在预检时无监听，不代表预留。正确版本为远端 `commands/start-model-ppu07-eth0.sh`，SHA-256 `183add493a8aeb5bffdebaf4c2af3e2f5deaff530cbbd5df60372f0f77afafd9`；先前 bond 草稿留档但不使用。模型启动前仍需重新检查资源和端口。

预检：PPU-07 有 16 张 96GiB PPU，driver 2.1.1-rbd225；卡 0–7 有其他 vLLM 工作负载，卡 8–15 无计算进程、利用率 0%。Docker 数据盘可用约 14T，共享 NFS 可用约 7.6T，模型目录可访问。PPU-07 未发现同模型镜像或容器。目标不运行模型，默认 CUDA_VISIBLE_DEVICES=8–15；设置私有 FlagGems 导入路径及 port8010 独立数据库。若未来运行共享启动脚本，须注意该脚本显式覆盖为卡 0–7，不能直接用于本次 PPU-07 的空闲卡组。

方案：源容器当前没有模型进程，采用不暂停源容器的不可变快照，核对快照前后源码指纹，再通过共享目录导出/导入镜像。保持唯一 bind `/mnt:/mnt` 的 RW/rprivate 属性与原设备、IPC、网络及 ulimit。目标 shell 容器启动后核验镜像 ID、挂载、源码与实际导入路径；所有差异记录于回执。旧 GPQA gate 不自动迁移为新 Host / 新实例的精度证明。

源镜像快照已完成：`qwen3.8-flash-optimized-snapshot:20261015-ppu07`，ID `sha256:67309a951e945ef8ac95e73511b7d17175b6b930a2d7f6899a1436c3d39730bc`，194,614,742,059 bytes；Parent 和 RootFS 前缀均核验指向原始镜像，快照前后源码指纹一致。原容器保持运行，没有暂停或停止。

完整压缩归档为远端根目录 `optimized-image.tar.gz`，46,925,595,709 bytes，SHA-256 `206370c9db701bf6d061055a93b6452959e8ecd7688e4dbd1cc5d268422dbcc6`，`export-receipt.json` 确认源指纹未变。PPU-07 再次核验该 SHA 后成功导入镜像；源端和目标异步作业均已结束，rc=0，不再存在迁移客户端。

最终容器 ID：`378fb2429d4cb36221ab5156d7417e18747c25544954c097c65195aafac21ddc`。`target-receipt.json` 确认 `image_lineage=verified`、`mount_parity=passed`、`source_fingerprint_equal=true`、`service_started=false`。原网络、IPC、设备、ulimit、资源设置及入口均核验；默认导入环境只增加明确的 CUDA_VISIBLE_DEVICES、私有 PYTHONPATH 和 FLAGGEMS_DB_URL。除独立启动脚本外，相关源码树与源环境完全一致。默认环境实测实际导入私有 FlagGems 及原 Plugin，Torch 枚举可见卡数为 8，容器内只有 bash，无模型进程。

原生回执位于本案例远端根目录：

- `target-receipt.json`：SHA-256 `27e1b0940a0bfd5065877dbc91879c4d6b5657d666d2b951f8a94fea8a938b41`。
- `mount-comparison.json`：SHA-256 `6d70a6cecdaacc9614c7d34c08761f113b1854508a9e9dd6e1dd0dbcaeab59d1`。
- `final-runtime-check.log`：SHA-256 `489b5c3c9e501cf58718fa9b23db664379e6ba459c23d8adfb929562aa36840c`。
- `source-fingerprint.json` / `target-fingerprint.json`、`source-inspect.json` / `target-inspect-running.json`、`image-load.log` 和 `container-startup.log` 保存完整非凭据环境证据；源/目标指纹记录版本和实际 import 目录。

进入容器：`docker exec -it qwen3.8-flash-opt-ppu07-20261015 bash`。启动模型仍需用户后续指令与当前设备/端口预检，不能因完成容器交付就直接启动服务。

首轮预检因 Docker top 要求输出包含 PID 而退出，发生在任何快照/源码操作之前。已保存失败日志并修正为 `pid,comm`；实际快照使用远端 `commands/clone_environment_v2.py`。本地 `commands/clone_environment.py` 为修正版本；首次原版仍保留在远端。实际源端异步作业为 `j521895181213.3503862`，原失败作业已确认结束，不存在重复运行。

不得将镜像快照或运行环境核验视为新模型精度/性能验收。

## 后续：用户明确要求更新共享启动脚本

2026-10-15 用户要求将 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh` 改为最新保留优化版本的启动命令。按本次最新 PPU-07 交付配置，已将该共享文件替换为与容器 `/opt/start-model-ppu07.sh` 字节相同的 33 行简版：卡8–15、TP8、8010、eth0/IPv4、max-num-seqs32、max-num-batched-tokens4096、80K 上下文、FULL_AND_PIECEWISE、私有 SQLite 修复及原卷积 fallback；不启用已回退实验。日志追加至本案例 `service-port8010.log`。已在对话中明确提示共享文件默认配置改为 PPU-07，未修改 PPU-01 的运行服务。

原共享脚本 SHA-256 `c039af5b8782ba45ec67bc243ce8f45f849122a526310de460a71d1a4b7341b7` 已备份到本案例远端 `shared-start-update-20261015-01/start-model.sh.ppu01-backup`。新共享脚本 SHA-256 `183add493a8aeb5bffdebaf4c2af3e2f5deaff530cbbd5df60372f0f77afafd9`，与 PPU-07 容器内脚本一致。执行命令为本地 `commands/update-shared-start-model.yml`，远端副本及候选在 `shared-start-update-20261015-01/commands/`。已通过原文件 SHA 冲突检查、Ansible `--check --diff`、备份后原子替换、容器内 bash 语法检查及新/旧 SHA 校验，实际 playbook `failed=0`。

本次仅更新脚本，没有执行模型启动命令、停止或重启服务，也未重新评测精度。
