# accdiag-051：PLE i64＋CTA同步完整算子回归通过，更新原Issue/PR

2026-10-20后续模型组合正式验收：[acc-017](acc-017-full-gpqa-ple-fixed.md#终态177198通过正式阈值7条60k问题仍存在)实际加载本轮PLE SHA2f273afa…，同FP32/i64/QSA M16组合177/198（89.39%）通过0.88阈值，原生gate核验通过、无本轮非法访存。仍有7条60K reasoning-only，不能由组合分数认定其根因解决或实际大索引覆盖；原算子矩阵/PR记录不改，未重启或重复测试。

## 授权与计划

用户2026-10-20授权最窄CTA同步修复，保留早i64，完整算子边界和graph回归，首次异常保留完整证据；不恢复8010、不访问8035、不全量GPQA，资源不足先停止。沿用inference-accuracy-evaluation minimal-regression、inference-accuracy-diagnosis、key-operator-analysis；不签模型gate，不将050局部结果当本轮完整通过。

目标为PPU-07/容器qwen3.8-flash-opt-ppu07-20261015/物理8。正式安装与049候选不直接修改；预期在新私有副本保留`row.to(tl.int64)`，仅在旧state加载后、写回前添加无条件CTA同步并更正同步注释，不改tile/warp/数学/采样。先过资源隔离门禁，再准备实现和测试。拟覆盖仓库原PLE测试、049大地址边界/canary/三dtype/empty、生产宽通道history/initial/spec/非连续layout，以及capture后更新device indices至少两次replay；具体新增矩阵在实际执行前冻结。本轮没有资源门禁后擅自展开测试或修改源码。

## 当前事实与停止决定

inventory目标解析及`./scripts/connectivity-check --limit PPU-07`通过，实际Host返回bm-aliyun-wlcb-zonea3-c-810e-96g-10-7。只读查询`ppu-smi -i 8`显示：总98304MiB、已用81444MiB，新VLLM::Worker_TP0约81248MiB。虽剩余显存约16.5GiB，**设备已有计算进程，不满足与无关负载隔离的验证门禁，不将其误记为实际OOM**；不因瞬时util0而视为可抢占。未查询8035/其他端口/物理0–7，不扩大搜索其他设备。

8010当前无listener，未恢复。只读回读049私有目标源码SHA611e4bc04be29c654c0d40f67d735b37e7af4a01d8bfd15768a7df654a95e180未变；050最窄实验barrier副本`/opt/qwen38-accdiag050-ple-sync-20261020/barrier.py` SHA94baded8a4fba03d9e5857c9c73a5cdac57774329d4f8f742bea7f7c94bc5b04仍存在，含早i64和单个CTA barrier。它的57次旧局部检查/18graph replay是050历史证据，不替代本轮完整回归。

按用户资源不足即停止的指令：本轮没有创建新远端目录/脚本/源码副本，没有启动任何GPU进程/测试、服务或模型请求，没有停止或操作现有worker，没有改安装/049候选/PR。只完成本地结构化记录；结果`incomplete-resource-isolation`，不是算子失败或修复通过。旧原始首差/状态/编译产物保持在050冻结目录，不覆盖、不编造本轮首次异常。监控保持PAUSED，不自动等待后重试。

## 待续范围与结论边界

需用户释放当前测试卡或指定可独占的任务设备并确认后，先重新核验当前资源/目标身份，再建立新私有正式候选和冻结完整算子矩阵；无论算子结果如何，仍不得恢复8010、访问8035或跑全量GPQA。现阶段只能说最窄同步方案已由050限域诊断支持，本轮生产修复和完整回归均未执行，无新formal gate、无性能结论。

## 13:58资源变化与同一授权续跑

用户随后询问“后八张卡不是空的吗”。2026-10-20 13:58:24–25+08只读逐张重核PPU8–15，全部为102MiB/98304MiB、无计算进程，原卡8占用已释放；先前只查卡8不能外推全部八张。保留13:56资源门禁原事实，不把两时点拼为工具错误或仍占用。按尚未完成的上一条修复授权继续同一051，不新增模型恢复或GPQA权限，不访问8035；执行前再次核卡8与镜像/挂载。

候选新私有目录`/opt/qwen38-accdiag051-ple-cta-sync-20261020/fgvllm`从049私有副本复制，保留早i64，只添加store前`tl.debug_barrier()`并纠正注释；不改任何launch/tile/warp/数学，原安装/049/050均不覆盖。后续完整算子契约在开始前冻结：仓库原20项+049大边界11项，外加144项全width1..8×dilation1/3×3dtype×decode/prefill/spec几何边界，以及36项生产channels10240/实际rowstride204800与contiguous布局、两index dtype、3dtype×3mode。新增几何每case1eager+3动态indices/flags/输入graph replay；生产每case3eager+3graph；保留所有检查，不以旧050结果代本轮。任何测试首失败保存原始CPU输入/实际与期望state-output/索引参数/完整traceback和全部编译cache并停止，不放宽容差或自动重试。

执行前保存至CASE/commands：accdiag051-ple_conv.py SHA2f273afafdfd1a991dd0138b0d330d001cf0cd17bdcb96b83a22a5f3929140c0；accdiag051-test_ple_cta_boundaries.py SHAd26b3c4c00e1b694d833cf7c2865dd60b0c061d406f76932aa7944cbbc525a7c；accdiag051-conftest.py SHA9fbefebc188868cea1da3314b29dfdad0fa63e778f9810e7b6bbc28f17b45cf4；唯一控制器accdiag051-control.py SHAbb5360b3181133ff6bccff6c71aba27c3e0f661d96ca70db347ce747bab11738。执行`python3 CASE/commands/accdiag051-control.py`，先核资源/8010无listener/镜像挂载，创建新D=CASE/diagnostics/accdiag-051-ple-cta-sync-20261020和私有K；1800秒预算，`pytest suite -q -ra -x`，首失败即停、无自动重试。取证fixture在每次普通调用/graph replay前落盘原始输入，失败收集参考值和实际state/output；大池不复制完整storage，只保存所有被寻址行/精确shape-stride-storage和测试canary，明确该限制，不伪称全池现场。实际加载路径/SHA、capture/replay计数和源差异另存新D；无模型请求或token。

结束后唯一CPU-only冻结脚本CASE/commands/accdiag051-freeze.py SHA394fb302580f09c480d7c893d1011b0fe11284a8dcadeb243c0082b9e457e13e；执行`python3 CASE/commands/accdiag051-freeze.py`仅在TEST_FINISHED存在后复制已有suite/修复源码/编译cache，核实际import与source SHA、已编译state CTA barrier、全部输入和日志SHA，记录卡8和8010只读状态，不要求结束时卡8必须空闲以免误将后续外部占用当测试错误。新D/terminal-evidence-001，不启动GPU或服务、不修改旧产物。

## 续跑终态：完整预冻结算子矩阵通过

唯一控制器自然结束，211/211 passed、无skip、无重试，用时190.13秒；原来的生产channels10240 Decode/spec两项state exact失败均通过。原始pytest日志SHA02f4ce223ee0784615aee7c4fb29e0310099366011676388f3148251e59d3590。输出继续使用原dtype容差（BF16 2e-2/FP16 3e-3/FP32 2e-5），state维持atol=rtol=0，不放宽契约。日志计4931 warnings，冻结的`--disable-warnings`未展开其详情，不据此宣称warning根因已查明或全部无害；未为此重跑选择结果。

| 已执行覆盖 | case数 | 结果 |
|---|---:|---|
| 原PLE仓库测试（含CPU拒绝、profile fallback、empty、原生产通道） | 20 | passed |
| 大stride204800/row10485、10486、11242、12000/NULL、负数、越界、empty/三dtype/canary | 11 | passed |
| width1..8×dilation1/3×BF16/FP16/FP32×decode/prefill/spec，含非对齐C1/33/129、empty ragged、initial/accepted边界 | 144 | passed |
| C10240/history capacity20，实际channel-contiguous rowstride204800与contiguous布局，int32/int64 indices、三dtype、三mode | 36 | passed |

实际192次graph capture、570次replay已从执行fixture计数核验：新增每case3次动态indices/flags/input replay；保留原3个legacy graph测试各1次replay，不将其单独说成每图两次。完整新矩阵覆盖多次重放，但没有模型服务graph启动/重放，因为用户禁止恢复8010。捕获与重放前共854份原始输入落盘；本轮无FIRST_FAILURE、无实际首次异常可声称捕获，不拿旧050首差当新事故。

actual-import绑定到新私有`/opt/qwen38-accdiag051-ple-cta-sync-20261020/fgvllm/src/flaggems_vllm/ops/qwen4/ple_conv.py`，SHA2f273afafdfd1a991dd0138b0d330d001cf0cd17bdcb96b83a22a5f3929140c0；183份实际state LLVM均存在CTA barrier。原安装源码163ebcd3与049 i64源码611e4bc0前后不变，未全局安装或被模型加载，FP32/Gems i64/randn/QSA M16/黑名单/固定调优未改。

终态3980份源码/suite/原始调用输入/完整可读日志/IR与二进制/回执文件独立SHA和大小核验。summary SHA5c473ca1d4e08fc8cf35159738ca841c35a84182a5880eaca094ae97d9c12909，manifest SHAe8083cf0b61cb722a29c2a8b76f65efdb588e72acb5caef79f13abd97ed17eed，均在D/terminal-evidence-001。大池只存所有被寻址行、元数据与canary，不是完整backing-storage或模型现场；无模型token/logits或HTTP可声称保全。

## 决定、复盘与边界

决定：**最窄i64＋CTA同步候选通过本次211项算子契约，保留新私有副本；未替换原安装、未更新PR959。** 复盘review-ple-051-20261020确认050的同步机制在更宽shape/dtype/layout/graph范围有支持；不是跨平台或所有可能输入的完备证明，性能成本未测、累计speedup=null。继续保留首次资源门禁停止及后来释放的时间线，不能把13:56占用改写成不存在，亦不能用它宣称13:58后仍不可测试。

8010终态仍连接拒绝（connect_ex111），0恢复/0模型请求；未访问8035/物理0–7，不全量GPQA。旧acc016故障污染incomplete及acc015164/198 failed-score不改，无formal gate；此前60K/reasoning-only因果未证明，模型最小回归因禁止恢复而not-run。等待用户下一步明确授权服务回归或上游补丁更新，不自动启动/重试/部署。监控仍PAUSED。

## 用户授权更新Issue958与PR959

用户随后明确要求更新已提交Issue/PR。已只读核远端：Issue958 open、PR959 open/draft，head仍a8d30bc17c1f213d91e1c432fdcbc453106c5347，无他人追加提交/评论；不新建Issue/PR、不改base、不force push。现有PR已附加当前任务。保留地址修复与051生产源码精确字节，补CTA同步；新增公开测试将144几何+36生产layout case整理为便携版本，生产fixture复用仓库`test_ple_conv.inputs`合成生成器，不包含内部目录、问题或模型权重。source SHA2f273afa不变；最终公开测试SHA5e429b8a07e4ec52636ecb29f04fcdb3c6d4312d146469d06af8948b06cca7f9，Black24.8/isort5.12/Flake8已过。新取证conftest SHA676f4914031abba03f6ab4c26af028fe2966667c89499a7178306571f7c9a35d仅留远端，不进PR，增加warnings逐条记录以补旧日志未展开的限制。

准备一次固定211项公开版回归：CASE/commands/accdiag051-publication-check.py，在执行前记录SHA；执行`python3 CASE/commands/accdiag051-publication-check.py`，先核物理8空闲/8010无listener/源SHA，不重启或改模型，不访问8035。suite/cache及证据位于同一051下全新publication-regression-001与私有publication-suite-001，首失败停止，无自动重试。公开测试整理后的实际结果独立报告，不把旧211通过自动追认为新文件已测。

公开版唯一控制器SHAb74dce0c492062532eeaa071f5ec5e3d326ad8c6f53e39677368e12b968a1689；公开源码/测试与取证helper均先排他保存CASE/commands并核SHA再执行，不覆盖原051命令/证据。

公开版实际211/211 passed、192.08秒、无skip/retry，192capture/570replay、854份调用前输入，无首失败；日志SHA027b4ff46781b4a5acac8bd0c5f5600657c602306d0906f099119fc2e568687c。4931 warnings逐条保留：4930条Python3.12下pytest assertion rewriter AST弃用，1条原有ple_fusion未注册mark；警告明细SHA4f15a7cc3b721ac2f8bdef2132e2f1d3c92d430252493afd9978c810fda469ef，不隐藏或丢弃case。原私有211测试的日志/manifest不改。

已将后续提交683e859750e22b0c49f88b907a39066fe63e4342以expected-head a8d30bc17c1f213d91e1c432fdcbc453106c5347租约fast-forward至原分支fix/ple-state-int64-addressing-20261020，无force。Issue958标题/正文及PR959标题/正文已更新，并追加双向进展评论6284840646/6284841348；PR保留Closes #958、原main base和draft状态。远端commit源码/新公开测试逐字回读等于已测文件，diff仅ple_conv.py和两份测试，原大地址测试未改。readback仍open/draft、head683e8597；当次check-runs为空，不宣称上游CI通过。只发布合成测试和获授权环境/寄存器摘要，不发布完整内部日志/数据集/权重。

拟执行一次CPU-only归档：CASE/commands/accdiag051-publication-freeze.py SHAa54b96909a54b749f1e70e0c3fba7530283554d4be6c8d06adc063c3d6d161ff。命令`python3 CASE/commands/accdiag051-publication-freeze.py`仅复制公开回归既有原始输入/日志、suite、源码与编译cache至新publication-evidence-001并逐文件核SHA/大小，记录上游链接/commit/readback回执；不发GPU/模型请求，不恢复8010，不访问8035，不改原terminal-evidence-001。

归档已复制全部结果/suite/cache/source并写publication-receipt，但首次manifest严格禁止symlink检查遇388条编译器正常`.cubin -> .hgbin`相对别名而停止；不是测试失败/损坏，也未再次运行GPU。保留此中断及既有文件，不删除、不重做测试。追加一次CPU-only完成脚本CASE/commands/accdiag051-publication-complete.py SHA96cd438541d3e4ad4a27d8712f6ac93397c406d45b391e127494ebf2dd9ff45a；执行前核SHA，`python3 CASE/commands/accdiag051-publication-complete.py`只核别名在同一归档内指向真实hgbin、逐文件SHA/大小，并排他生成尚不存在的manifest/COMPLETE。不改旧receipt或原051证据，不把symlink数量算独立binary。

CPU完成审计已结束：3588真实文件SHA/大小通过，388条内部别名目标/SHA通过；publication-evidence-001/manifest.json SHA02d306390ec235cc1abf044b7b2c631dd55569fa8340e3309c958957b231d8a7，publication-receipt.json SHA5af37ecbaca56bb257077068cfa864b3cbf8a562f57c4bcc333bad593c28a8fc，COMPLETE.json保存完成回执。首次严格断言的退出记录保留，未因此重跑算子或改变测试。YAML已解析、experiment_id唯一性及051范围/发布不变量通过，目标文件diff --check通过。此次0模型请求/0服务恢复，不访问8035；监控仍PAUSED，等待用户授权模型级回归，不自行恢复/GPQA。

## PR959当前CI失败只读定位

用户要求查看CI原因，本轮只读GitHub，不提交/推送/改PR或触发重跑，不连接PPU。head仍683e8597，CI检出merge fd35c0bb；basic ci run39380294456的code-style job118487633804失败于`pre-commit run --all-files --show-diff-on-failure`。flake8、black、空白/EOF/YAML/文件大小均通过；唯一实际hook失败为isort5.12.0 `--profile black`对新tests/test_ple_conv_state_boundaries.py的import分组重新排序。日志明确diff：将`from test_ple_conv import inputs`置于pytest/torch后，再空一行放`from flaggems_vllm.ops.qwen4.ple_conv import ple_short_conv_`（其后两空行）。没有执行算子测试，不能把此次CI红灯称为数值失败。

multi-backend summary job118488183645收到CODE_STYLE_RESULT=failure、SELECT_TARGETS_RESULT=skipped，按工作流返回1；select targets及NVIDIA/其他backend测试均skipped，是前置失败的连带结果。rule-check run39380294055成功。确切最窄修复为按仓库root的pre-commit/isort分组整理测试import，不改i64/CTA kernel或测试语义。此前临时目录孤立formatter通过不足以替代仓库root全量pre-commit；这是提交前验证上下文遗漏。当前用户仅授权诊断，未实施/推送修复，CI保持失败状态，原211硬件算子结果及无模型gate边界不改。

## 用户授权修正CI格式

用户随后要求调整。新隔离克隆/private/tmp/ple959-style-nfBkj8/repo精确head683e8597，完整读取目标AGENTS.md；仅调整tests/test_ple_conv_state_boundaries.py的import分组与空行。第一次全仓hooks将多余空行规范化并退出1，其修改保留，不误记通过；第二次仓库root执行`pre-commit run --all-files --show-diff-on-failure`全部7项hook通过且exit0。使用仓库固定isort5.12/Black24.8/Flake8等配置，macOS/Python3.9/pre-commit4.3与CI Ubuntu/Python3.11/pre-commit4.7不同，不冒充上游CI绿灯。最终test SHA1e8ae93b770183212d3cacd660a6b1e35cc75a2225c1d0ff034b6d4f6ccd2b79；AST除import顺序归一后完全相等，kernel SHA仍2f273afa，git diff仅1测试文件2add/1delete、diff --check通过。没有重跑GPU/模型。

计划用GitHub API在原fork分支追加单文件style提交，以当前head683e8597为parent、expected-head租约fast-forward，无force、无新分支/PR；推送后回读精确test/source，更新原PR证据说明格式整理的新SHA及未重跑硬件边界，查看自然触发CI，不手动重复触发。无PPU连接、8010重启、8035访问或GPQA。

实际已追加bf1b4f2c582887b98da4618a81db30e44ef0656d，expected-head683e8597租约fast-forward成功；远端test逐字回读等于本地最终文件，kernel逐字回读等于211项已验证源码。PR仍open/draft，原body保留并追加格式修复/新SHA/未重跑硬件的说明及评论6284998236，PR重新附加本任务。新basic CI run39381445902已自然启动(in_progress)，rule-check39381445529成功；尚未将CI判通过。没有额外GPU测试/PPU连接/服务变更，原211硬件结果仍绑定其旧测试SHA，不能称新格式文件重新跑过211。后续只读检查新CI结果，不手动重复触发。

最后只读快照：新code-style job118491240088已completed/success，确认本次isort问题在真实CI消除；select-ci-targets job118491573223仍in_progress，其余硬件/汇总结论未出，不能将格式通过扩大为全部CI通过。

## 用户授权合并新增测试到原文件

用户要求合并新增两文件至原test_ple_conv.py，保留边界/graph并验证通过后更新原PR，禁止改kernel/重启服务。按inference-accuracy-evaluation minimal-regression执行operator-only范围；模型smoke/C8及service graph不适用本次纯测试组织改动且未获服务权限，不产生formal gate。当前PR head bf1b4f2c；隔离克隆/private/tmp/ple959-merged-G54BnI/repo。将原测试和两新增文件函数合并，移除跨文件inputs import，复用本地inputs；保留原native reference及大地址/边界独立CPU oracle，避免为去重改变舍入/状态断言。仅将原边界文件module skip移至对应两test函数，所有16函数体/参数签名AST逐份一致；合并后仍20+11+144+36=211项预期，所有大row/canary/状态exact与192capture/570replay目标不减。移除的两文件是本PR新增测试，历史Git/已冻结远端证据均可恢复，不删除既有原始结果。

仓库root全7项pre-commit及diff --check通过。合并文件SHA6b987f18310465870ed19c2360cc9dceff578dad03c3bf84e7ebc57c302a6ad5；kernel SHA2f273afa保持，16函数体/签名AST相等。inventory及connectivity-check限定PPU-07通过；只读物理8为1MiB/98304MiB且无进程。新的唯一控制器CASE/commands/accdiag051-merged-check.py SHAfa8fd4cf8c9fd3f90349a39d79513efa639a9f4a71399f26ddf1f6faf8ef53bb，合并测试执行副本CASE/commands/accdiag051-test_ple_conv-merged.py，先核SHA再执行`python3 CASE/commands/accdiag051-merged-check.py`。仅在物理8仍独占、8010无listener及kernel SHA一致后运行；不停止任何占用者。新K/merged-suite-001、merged-cache及D/merged-regression-001，不覆盖旧目录或源码。

先分别原public suite与merged suite collect-only，对去文件名后的caseID/参数Counter逐份核相等且211无丢失/重复；然后同一合并文件一次211项GPU边界/graph回归，1800秒预算、首失败保存完整现有输入/期望实际/traceback并停，无自动重试。复用原公开取证conftest，854 pre-call/192 capture/570 replay计数核验；结束只CPU复制suite/cache/源码并逐文件SHA/别名验证，限制仍为大池被寻址行及canary而非全storage。服务不启动/重启、不访问8035、不GPQA、不改kernel/安装。只有测试有效通过才fast-forward更新原PR并删除原新增两文件；失败/资源门禁不足不冒充旧211通过。

### 合并验证终态与原PR更新

原suite和merged收集的case ID/参数Counter完全一致，均211，无丢失或重复；单文件GPU回归211/211 passed、191.50秒、无skip/retry，192capture/570replay、854 pre-call，无FIRST_FAILURE。3个原legacy graph各1次replay未改，189个新增graph各保留3次动态indices/flags/input replay。state继续exact、原output容差不变。真实actual-import为K/fgvllm/src/flaggems_vllm/ops/qwen4/ple_conv.py，SHA2f273afa；只是读取同一kernel，没有复制覆盖/改源码。warnings4927条明细保留（4926 pytest/Python AST弃用、1原ple_fusion未知mark），不把警告当失败或静默丢case。

raw pytest日志SHA8536bff29c70c5ae6590a4de7c4710c1c50a6d24c8c085baa8ed58ed62334753；TEST_FINISHED SHAafe2faf16e16a8d0c6cb92202711a53010503cc96698fb63c82b0206f4992c88；FINISHED SHA26364fcd9fb35c24e5bb09e171017cf701bd4c0ea2a8b277ec5a243b8022dccd。D/merged-regression-001已冻结suite/原始输入/日志/cache/source，3595真实文件及388内部cache别名逐份SHA/大小核验，manifest SHAe914d3890d6dcd3780bfdea1a405f8fbe22a9c529b2eaf6b43a67cb55d15808a；旧结果不改。大池保留被寻址行/shape-stride-storage与canary，非全storage/模型token现场。未新增GPU验证之外的模型请求，无服务恢复/重启，无8035访问，无formal gate或性能结论。

通过后追加commit22194f0b2ee0cebb51f945a20a157b82c4e19c65，以expected parent bf1b4f2c租约fast-forward原分支，无force/新分支/新PR。该commit仅修改test_ple_conv.py并移除两份本PR新增文件，未改kernel。远端test逐字回读等于已测6b987f18，kernel逐字回读等于2f273afa；最终PR diff仅kernel原修复＋原test_ple_conv.py扩展两文件。PR body更新为单文件执行命令/新SHA/211和192/570证据，保留Closes #958及draft；评论6285216503已补说明，PR重新附加当前任务。旧bf1b4f2c对应basic/rule-check均已completed success，不套到新提交；新basic CI39382991033 in_progress、rule-check39382990608 queued，尚不宣称新CI通过。等待维护者/用户下一步方向，不启动服务或全量评测。
