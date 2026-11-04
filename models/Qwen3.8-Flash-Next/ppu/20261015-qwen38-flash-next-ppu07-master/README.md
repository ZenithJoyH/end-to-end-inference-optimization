# 20261015-qwen38-flash-next-ppu07-master

2026-10-22 [eng066规范Plugin源码开放thead完整MoE入口](optimize/eng-066-thead-full-moe-entry.md)：FGVLLM开关1且无LoRA/SiLU/无clamp时直接调用fused_experts_impl；开关0保留分步路径，NVIDIA/昆仑行为保留。只改两文件、126 CPU工程检查及回读SHA通过，有回退备份，BF16/i64/randn/PLE/QSA保留。8010未重载仍旧运行路径，设备/graph/模型待授权，无新gate或性能结论，不访问8035/提交推送。

2026-10-21 [当前Plugin源码目录为/opt/vllm-plugin-FL](optimize/env-058-plugin-source-directory.md)：`pip install -e /opt/vllm-plugin-FL`完成，默认与clean实际导入指向该目录`vllm_fl`，`editable=true`及334份非版本payload核验通过；版本/依赖不改，旧env057目录保留备份。[env059](optimize/env-059-plugin-git-metadata.md)已补真实Git历史/index，原PR暂存、最终3文件修改/未跟踪，另显式保留既有1份配置类型差异，源码/安装不变。8010未重启、仍原eng053加载模块，0推理/GPU/8035访问/推送；无新模型/精度gate或性能结果，monitor仍暂停。以下env056普通wheel已被替代。

2026-10-21 [最终精简Plugin已安装](optimize/env-056-install-slim-plugin.md)：目标容器普通wheel安装版本`0.3.0rc2.post1+ga696859b9.eng055.d20261021`，新默认路径`/usr/local/lib/python3.12/site-packages/vllm_fl`；335文件与唯一绑定/受保护CPU导入核验通过（report3b42f398）。旧源/依赖未改，绑定已备份；8010没有重启，仍已加载eng053，0新推理/GPU/8035访问/提交推送。安装不等于新模型测试通过，无新gate/性能结论，monitor保持暂停。

2026-10-21 [eng-055最小FP32主补丁完成](optimize/eng-055-plugin-minimal-fp32.md)：3文件/+242/-10（生产+66/-3），复用原PR原模型与测试文件，无新HC框架或独立测试文件；CPU410通过、lint/补丁/SHA审计通过，原3个device测试保留未跑。337实际生产包文件与eng053逐字相同，线上8010未改、0新推理/重启/GPU/8035访问/提交推送；无新graph/GPQA/性能测量、旧证据不重标。主交付以055替代054扩大候选，父PR格式/CI待处理、needs_revision，monitor仍PAUSED。

2026-10-21 [eng-054复用调整完成](optimize/eng-054-plugin-architecture-convergence.md)：独立候选将HC数值逻辑接入既有dispatch并解除common→GPU反向依赖；native MoE契约/HC/reference/缓存等535 CPU测试通过，lint和交付SHA审计通过。FP32/i64/QSA M16/PLE保留，线上eng053未动，0新推理/重启/GPU/8035访问/提交推送。新候选未加载，graph/C1/C8及formal/性能未测，minimal=incomplete/pr_readiness=needs_revision，待用户方向；以下eng053运行事实不变。

2026-10-20 [Plugin收敛候选eng-053最小回归通过](optimize/eng-053-plugin-pr-cleanup.md#终态收敛候选10请求最小回归通过)：20:05全部10HTTP200/正常final，诊断答案10/10匹配，无超时/60K截断/非法访存；两C1完整503tokens相同，graph两类7/7、replay及真实C8覆盖。20:29 CPU审计86文件SHA/raw-token/当前source全部通过（report60aa8f3e）。仅一次8010重启、保留FP32/i64/QSA M16/PLE，当前服务健康空闲保持运行；监控已PAUSED，不访问8035/全量GPQA/提交推送。新树无formal gate/性能结论，不证明旧C64/60K解决，父PR格式/临时CI待处理，needs_revision。

2026-10-20 [acc-017正式GPQA通过](optimize/acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)：18:40结束，177/198（89.39%）>=0.88，198唯一题与两filter完整、gate复验通过。仍有7条60K reasoning-only（doc71/81/88/127/145/147/164），无提前EOS/真实HTTP失败/非法访存；198份完整API token匹配rank0前缀，源码/服务不变、日志已冻结核SHA。轻量诊断没有完整逐层现场，不证明旧症状已修复或大索引已覆盖。8010健康空闲保持运行，heartbeat PAUSED；不访问8035、不自动追加/重启/重跑，等待方向。

2026-10-20 [模型回归052终态](optimize/accdiag-052-ple-fixed-model-regression.md#终态10请求回归通过原8010保持运行)：2C1＋8C8共10请求/8唯一doc全部正常final、诊断性答案10/10匹配，0HTTP失败/空final/60K截断/非法访存；完整raw/token与CPU审计通过，PLE新IR证实i64＋CTA同步。FP32/i64/QSA M16保留，源/8010绑定不变且健康空闲；仅一次启动，不访问8035/追加/GPQA，heartbeat已PAUSED。仅最小回归通过，不代表正式精度或旧C64/60K全部修复，无新gate。

2026-10-20 [PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)已按要求合并新增测试至原test_ple_conv.py，commit22194f0b；211/211新回归与192capture/570replay通过，kernel未改、服务未重启，无模型请求/8035访问/GPQA。新CI运行中；[051](optimize/accdiag-051-ple-cta-sync-regression.md#合并验证终态与原pr更新)保存精确证据和限制。

2026-10-20 [PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959) CI导入格式修复已追加bf1b4f2c，全仓pre-commit本地通过，kernel不变；新CI运行中、rule-check通过，未重跑GPU/模型。见[051](optimize/accdiag-051-ple-cta-sync-regression.md#用户授权修正ci格式)。

2026-10-20上游更新：[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)及[原草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)已补i64＋CTA同步修复与公开合成测试，head683e8597；公开版211项/192capture/570replay全过。模型服务未恢复，未访问8035/GPQA，无新formal gate，仍不能认定reasoning-only/60K因果已解决。见[051](optimize/accdiag-051-ple-cta-sync-regression.md#用户授权更新issue958与pr959)，以下历史不改。

2026-10-20最新：[accdiag051](optimize/accdiag-051-ple-cta-sync-regression.md#续跑终态完整预冻结算子矩阵通过)13:58确认后八卡已释放后，完成新私有i64＋最窄CTA同步修复，211项完整预冻结算子测试全过（192capture/570replay，3980证据SHA核验）。旧生产宽通道状态失败通过；没有恢复8010/替换原安装/访问8035/GPQA/更新PR。仅算子结果，不宣称模型精度或60K已修复，以下资源阻塞为较早窗口。

2026-10-20最新：[accdiag051](optimize/accdiag-051-ple-cta-sync-regression.md)获最窄CTA同步修复/完整算子回归授权，但卡8已有vLLM worker占约81.4GiB，未满足隔离条件，按要求停止。**本轮未部署/测试，未恢复8010/访问8035/重跑GPQA**；050实验i64+barrier副本保留，旧局部通过不当本轮完整结果。等待资源释放或明确独占测试设备，不自动重试；以下历史。

2026-10-20最新：[accdiag050](optimize/accdiag-050-ple-state-synchronization.md)将PLE写回不一致定位到CTA内history跨warp的原地WAR竞争：无同步41/66检查失败，barrier57/57、snapshot9/9、单warp9/9通过；首差1152元素精确重建，新旧cache编译binary一致。保留全部输入/state/差异/IR/二进制与日志，499文件SHA通过。**仅完成诊断，未修改正式安装/PR、未恢复8010/发模型请求**，不访问8035、不全量GPQA；不宣称原60K/模型精度已修复。GPU测试结束后卡8出现新占用，未操作；下一窄同步源修复待方向。以下为历史。

2026-10-20最新：[accdiag049](optimize/accdiag-049-ple-i64-fix-validation.md)已在私有副本修复PLE state乘前i64，新增11边界/graph测试通过，但原生产shape两项状态一致性失败仍在，原版低索引A/B亦复现。**整体minimal failed，未恢复8010/未发模型请求**，不访问8035、不全量GPQA；现有FP32/Gems i64/QSA M16等修复不变。503份证据已冻结核验，[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)及[关联草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)已提交；待独立状态写回问题定位后再晋级。无新精度gate/性能结论，以下为历史。

2026-10-20最新：[accdiag048离线定位](optimize/accdiag-048-ple-state-invalid-page.md)确认FlagGems-vllm的PLE状态kernel存在i32地址乘法缺陷，独立于已修复的index/index_put。stride204800下row10486起危险，3份故障寄存器反推row11242、地址提前8GiB，与驱动PC/现有Decode机器码吻合；事故机制高置信度，尚未修复或GPU验证。588份现有日志/源码/编译证据已独立验SHA；0重启/推理/GPU/8035访问，不自动全量重跑。建议state row乘前i64扩位并经批准做边界/graph受控验证；acc016仍incomplete、无gate，heartbeatPAUSED。以下为历史记录。

2026-10-20当前：[acc016全量正式GPQA因服务故障终态](optimize/acc-016-full-gpqa-fp32-fixed-qk.md)。11:33:22驱动报告`_ple_conv_state_kernel`非法页访问，随后多rank watchdog报错、8010退出。39题正常返回/38正确，159题连接失败占位；原生38/198（19.19%）为故障污染结果，`incomplete`、无gate，不代表有效模型精度。198唯一题/两filter原件、39条完整API tokens及服务/8rank日志已核验；source前后相同，但缺首次故障GPU状态和formal逐层logits。未重启/重跑/访问8035，同heartbeat已PAUSED，等待用户方向。旧acc015有效164/198失败仍保留，性能晋级继续阻塞。

2026-10-20当前：[runtime006恢复复核](optimize/accdiag-047-fixed-tune-qk-state.md#runtime-006终态服务恢复正常旧043前向差异仍为15)8010按同一源码/配置恢复一次，保持运行health200/idle，2条同前缀均200/token1596、无NaN。all8前后重启logits差0，但与旧043 max仍1.5，**原差异未消失，不是修复通过**。完整输入/状态/logits/prob/token/日志与编译证据已核验；FP32/i64/M16/index_select黑名单保留，未访问8035或跑全量GPQA。仅2C1/max1，C8/长推理与正式精度未验证，无新gate；以下为历史，旧“保持停止”状态已被本轮恢复取代。

2026-10-20当前：[GPU A/B已完成](optimize/accdiag-047-fixed-tune-qk-state.md#gpu-ab-002终态设备复现归约舍入模型差异因果仍未证明)。按用户授权只停止8010，卡15完成4组保存Q/K×3路径×2重复；当前kernel输出逐位复现旧存模型值，R32/R64仅改归约分组可复现6个Q元素1ULP/max0.015625，K相同，无NaN/越界/guard异常。完整数值/编译/日志证据142文件已核验，模型最终1.5及60K因果仍未证实，无formal gate。**8010当前保持停止、8–15无计算进程**；源码/修复未变、未访问8035/发模型请求/跑GPQA，不自动恢复。旧001资源门禁保留为历史，不覆盖。以下历史。

2026-10-20最新离线：[accdiag-047来源分析](optimize/accdiag-047-fixed-tune-qk-state.md#离线终态编译路径为优先嫌疑当前初始化未支持故障旧043未排除)优先怀疑编译fusion/归约路径变化：固定配置确实命中，但有效Q256/K32，新tap并非纯参数A/B。当前GDN清零和192QK权重未见初始化错误；旧043无doc71中间值，最终1.5原因仍未确认。88文件证据已归档，0新请求/GPU/重载/源码变更/8035；原修复保留、旧failed/no gate不改。以下历史。

2026-10-20最新：[accdiag-047/runtime005](optimize/accdiag-047-fixed-tune-qk-state.md#runtime-005终态两条正常完整sampler数值一致)无损去重取证后仅恢复8010一次，两条同前缀均正常200/token1596，all8 logits/概率/noise完全一致；576处GDN清零写回通过，预算约237MiB/rank未耗尽。完整窄证据已冻结校验，8010健康空闲；保留黑名单/FP32/i64/M16，未访问8035或全量GPQA。与旧043 raw差1.5尚未定位，不宣称原精度修复或新gate；以下历史。

2026-10-20当前终态：[accdiag-047/runtime004](optimize/accdiag-047-fixed-tune-qk-state.md#runtime-004异常终态首条成功第二条取证预算耗尽)已修绑定，仅8010一次恢复后首条200/token1596、第二条观察器累计512MiB预算耗尽500，服务退出、不再恢复。4120PT/全日志/缓存已冻结校验，已覆盖GDN清零写回一致；第二条logits/概率/token未产生，原精度原因未定，不能称修复。保留黑名单及FP32/i64/M16，无8035/GPQA；报告b57fd76d/43922cbe，旧failed/no gate不改，以下历史。

2026-10-20最新黑名单续跑：[accdiag-047](optimize/accdiag-047-fixed-tune-qk-state.md)当前验证脚本已追加`index_select`且新8010实际环境核验；首请求越过旧OOM，随后被我方观察器位置/关键字参数读取错误中断（HTTP500），**8010退出、第二条未发送，无自动恢复**。16PT/120冻结项/13031缓存成员与FP32/i64/M16源通过核验，报告395ebc8c；Q/K/状态/logits/prob/token仍未取得，不能宣称精度修复。参数绑定方案CPU8项通过但未部署；不访问8035/GPQA，旧failed/no gate/PAUSED保持。以下为历史窗口。

2026-10-20最新终态：[accdiag-047](optimize/accdiag-047-fixed-tune-qk-state.md)新取证路径在首请求用FlagGems index_select选状态时全池连续化，额外24.22GiB分配OOM；HTTP500，**8010已退出，未再次恢复，第二条未发送**。原精度原因仍未覆盖，Q/K/状态/logits/prob/token未取得，不能称完整因果现场。16PT/124冻结项/10471编译成员SHA通过、审计55bbaa3b；CPU单行切片拷贝修正方案已验证但未部署，恢复需新授权。FP32/i64/M16源不变，未访问8035/重跑GPQA，旧failed-score/no gate和PAUSED保持。以下为历史进度。

2026-10-20当前：[accdiag-047](optimize/accdiag-047-fixed-tune-qk-state.md)按用户新授权仅8010一次重启，固定Inductor合法候选选择并窄抓doc71 Q/K及选中GDN/PLE状态。两条相同343前缀/C1/max1、零重试、无额外预热；CPU18项/源与挂载/数学AST门禁通过，唯一driver等待编译与graph READY。保留FP32/i64/QSA M16，不访问8035、不跑GPQA；尚无新数值结论，旧164/198 failed/no gate及heartbeatPAUSED保持。

最新离线定位：[accdiag-046](optimize/accdiag-046-offline-cache-compile-state.md)排除所保存输入/RNG漂移，043/045的rawmax1.1875确为前向差异，过滤后prob单点1掩盖它。全8FX、400AOTkeys和825共同ELF可执行section同；800bundle解析证实367对子图保存不同autotune参数，Q/K RMSNorm256归约block32/64是优先嫌疑，尚不能确认因果/bug。缺doc71层与初始device state，初始化不能排除；本轮仅CPU/Host分析，0新模型/GPU请求/埋点/重启/8035，FP32/i64/QSA M16保留。进一步窄埋点/重载先需新方向，未自动执行，全量GPQA禁止、旧164/198 failed/no gate和heartbeatPAUSED不变。以下为045原受控验证终态。

终态：[accdiag-045](optimize/accdiag-045-rollback044-first-request.md)仅回退044新增观察、一次8010重启、固定两条C1已完成。**首条NaN未复现，两条all8rank完整logits/prob/input/RNG/noise逐位相同，token均1596**；但与043参考raw仍max1.1875，不能宣称数值完全恢复或具体埋点根因已明。32当前+64参考PT/96原件/12656编译成员核验，CPU1f8c2f65/Host00e7aa61；FP32/i64/QSA M16保留，8010API3385225/start513345302健康idle、原driver退出。两类graph7/7但实际replay0/C8未覆盖，不签通用minimal通过或formal gate；0额外请求/重试/再次重启/8035访问/全量GPQA，旧164/198 failed/no gate和heartbeatPAUSED保持。以下为044已完成历史窗口，不是当前服务来源。

当前：[accdiag-044](optimize/accdiag-044-layer38-hc-moe-reduce.md)仅8010一次授权重启后**首条C1 doc71全部8rank的logits/概率均NaN，按门禁仅完成2/19即停止；doc81/Mixed及38层内部未覆盖**。第二条同payload/实际输入/位置/选行/seed/RNG/noise恢复有限值，但与043参考raw max3.7832，prob/token相同不能称正确。32PT/113原件/12984编译成员及48份旧新前缀证据核验，CPU8138bb51/Host085505c0/对照6b61a306；全8rank FX96FP32分支、i64/QSA M16源保持，非有限根因未确认，不用旧043张量补本轮现场。8010当前实例health200/idle但数值回归failed，未补17条/自动回退或再次重启；不访问8035/全量GPQA，新隔离/重载须等待用户方向。旧164/198 failed/no gate及性能阻塞保持。以下为043已完成窗口。

当前：[accdiag-043 doc81逐层与LM-head边界](optimize/accdiag-043-doc81-layer-lmhead.md)已按授权仅8010重启一次，完成19/19 HTTP200/C<=8/零重试。**778/808两前缀/all8rank首个完整目标区间差异均在第38层（0-based）output-block，row254/channel1407仅1 BF16 ULP；LM-head前hidden随后明显不同，logits差异仍存在。** 已保存首差两侧完整张量、输入/绑定/完整logits-prob-noise-token及日志编译证据；7248PT/7434原件/14590编译成员SHA核验通过，all8 FP32编译链及graph实际replay>=384、i64/QSA M16保留。仅定位层级边界，内部MLP-HCmix/router/专家/归约根因未确认，也未证明原60K循环已修复。8010同本轮实例健康idle，无8035访问/全量GPQA；需进一步埋点/重启先获新方向，旧164/198 failed/no gate及性能阻塞保持。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)
