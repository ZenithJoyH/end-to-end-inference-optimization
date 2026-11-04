# 20261023-moe-align-prefix-56 非二次幂专家前缀计数向量化

- 当前状态（14:21）：用户明确接受+2.7148%并要求保留；`user-retain-03`已装回同一align候选，完整最小模型/FULL/C64及最终当前只读审计通过，8011健康空闲，交给用户跑性能。MBT/启动参数/用户Plugin/index不变，不自动评测或继续优化。原`cache-comparability-02`未达3%的failed和`abr-01`缓存混杂incomplete均保留，不改判；新FG源码未冒用旧173/198正式gate。
- 旧轮状态（04:10终态）：三臂九组各8+3、共99轮全部完成且原生复验稳定，Mixed/Decode A/B表观吞吐差值+4.1964%/+3.4519%；数值守护与回退漂移在阈值内，但实际DB身份差异使原生Mixed及阶段守护均`incomplete`，不确认净收益。原版源码/原参数服务及当前独立恢复审计通过，候选未部署、旧monitor已删除。
- 分类：`operator/improve`；父场景 `p1024-d1024-c64-n128`，Decode及Mixed，Prefill守护。
- 目标：PPU-13 / glm5.3-flash-opt-20260911 /8011；MBT32768及所有推理参数/启动脚本不变。
- 依据：[点55采集修复与归因](20261022-steady-decode-mixed-profile-55.md)；当前用户Plugin保留，不回到旧PPU执行分支。

## 用户授权接续：缓存可比性与绑定

### 用户决定保留并接管性能测试（user-retain-03）

用户明确认为2.71%也有收益，要求先保留同一align优化，然后由用户跑端到端。此决定覆盖部署选择，**不改写**原冻结3%契约或原生failed回执，也不伪造四场景/完整精度通过。当前原版实例`3825111:544654758`、源/index/原参数/DB均复核一致且health200空闲。

在新外部`user-retain-03`中重新应用完全相同的一份FlagGems补丁，FG树`1a6197b7…`→`030c82b8…`；Plugin/FGV、MBT32768/全部启动参数/原脚本/DB URL策略不变。最小回归Skill覆盖新实例C1/C8/三16K/11答案/C64/FULL capture及多token回放，成功后保持服务健康空闲交给用户。新零准备/唯一派发命令`user-retain-v1.py` SHA `c2ad2d7ec6664b4f87ea25cb45ed31bd2d0c35aaa0c6ea1e44292cc0c59522e0`，5项CPU编排测试通过，先保存再执行；失败仅精确回退本补丁并恢复原版，不盲重试。不自动跑性能、GPQA、profiler或下一优化，不提交推送；原173只属于原FG源码，不重绑给候选。

14:13:30部署准备通过，`retain-freeze.json` SHA `78f1e5480e8e35eb56d8214d44b8b72b3e0102022249b6d1273c3737de689d53`；新目录/镜像挂载/私有源/index及精确原服务检查通过，尚无源码/服务变更或生成请求。接下来只唯一派发部署与最小回归，不派发性能。

14:14:19部署与最小回归已唯一派发，控制器`2475687:545186864`。本轮只按用户要求装回同补丁并验证新实例，不运行benchmark；原比较文件不变。

14:18:07部署及完整最小模型回归终态通过；C1/C8、三16K边界、11明确答案、C64 64/64、FULL capture/多token运行回放覆盖及16worker无hook通过。零生成最终只读命令先保存`user-retain-03/commands/handoff-audit-v1.py`，SHA `e83209aa968c4889614398b02068587447bd3acf862f9cc12032faa034058999`，复验当前源/index/实例/参数/DB/安装/挂载/health，不重复模型回归或性能请求。

14:20:59最终只读审计通过：当前实例`3866321:545188042`，三库唯一安装/真实导入、四库源与index、原argv/env/权重/tokenizer/thead、镜像/挂载/私有源码、16worker PID/start无hook/TileLang和health200空闲均一致；DB仍`2c39b972…`。保留FG内容`030c82b8…`，Plugin`1ecb0ef3…`与FGV`ba76c1df…`不变。终态`completion.json` SHA `83a370d17580ae477c98d045b4d457e317f34d2eb247d2806b57f5e5e5bc7c73`；`handoff.json` SHA `b48a28afe1e2e0256d1a3deb9470b426fc68b9077213ba7bb1d641a129079e6d`；`handoff-readonly-audit-v1.json` SHA `d8580edcf3256768521487f3fe1e4301737ebe024df724c32ab119639d9ac4a5`，均在`user-retain-03/`。服务已按原`start-model-opt.sh`运行，无需重复启动。

本轮无性能/GPQA/profiler请求，无提交推送；用户接管端到端测试，Agent不再自动变更或发测试请求。历史同缓存Mixed输出1157.7680→1189.1990 token/s（+2.7148%）、Decode+2.3550%、Prefill−0.1645%仍是该契约下的证据，不等于新四场景验收。此次只做新实例完整最小回归，旧173/198不绑定到新FG源码，完整精度按后续累计/正式验收触发条件处理。

13:46只读发现新轮已于13:31:25终态：99轮均完成，原生Mixed比较`failed`（+2.7148%低于预冻结3%），Decode/Prefill守护passed。24个阶段/回归缓存检查点字节与逻辑SHA相同，故此次不再是缓存混杂的incomplete。控制器按契约未保留align，恢复原版新实例`3825111:544654758`，health200。正在独立复验原始九组数据、冻结比较、当前源码/index/参数/模型/FULL/安装/挂载；零生成命令`commands/cache-final-audit-v1.py` SHA `eec9c8e5e7343fafa55cbd997a66da4ae3aed041ededb9151096ede441112797`先记录再执行。原绑定3723831属于baseline历史，不能静默套给回退新实例。

若终态当前审计通过，仅为实际回退原版3825111签发一次新的精度绑定，直接引用原始schema3；不是重复给baseline3723831签发，也不链式消费已有schema6。零生成命令`commands/cache-bind-final-v2.py` SHA `bb38516523d904eda7e1808034e5ea0018efb990eeaa7f1544e994229534fb2f`先保存，仍只复用173/198及86%门槛、当前整模/FULL证据，不改源码/服务/参数/DB，不重跑模型或保留未达收益门槛的候选。

2026-10-23用户要求先核对DB具体变化，处理可比性/绑定，确认收益后保留align再继续优化，MBT和推理参数不变。10:47当前原版实例`3723831:541125214`、四库源/index、原argv/权重/tokenizer/thead和DB`2c39b972…`均未漂移，health200空闲。实际SQL实现启用WAL，`put_config`/`put_benchmark`对已有key直接返回，只插入新记录；正常写入不能等同于代码变更。

旧点54/55/56未保存点56基线`6a7822d7…`的DB/WAL字节快照，不能假装补出该次精确逐行差分。新子目录`cache-comparability-02`先保存当前一致性只读DB快照、逐表逻辑摘要/配置及写入实现校验，再与明确标注的更旧点51快照作辅助差分（不能冒充点56基线）。原生产DB不清、不覆盖/回退、不改URL/策略；证据备份不作为运行DB。

零生成准备命令先保存`abr-01/commands/cache-prepare-v1.py`（建立子目录后复制到新commands），SHA `a153aeccb5a027b8d4538c1cac24c74224736f7015ee5a838c563fc9e4473cb7`，本地AST通过；尚未执行模型/性能请求。精度使用`gate-check`核查缓存与实例差异，性能将用`targeted`新契约，原abr-01不改判；候选源码变化不能直接复用原173/198 gate。后续是否需要新三臂按证据决定，当前未开始新测量。

准备v1已成功保存SQLite一致性只读快照，但benchmark表含IEEE `inf`计时哨兵，严格JSON序列化拒绝，未运行模型、未更改生产DB。保留v1命令/快照；v2 SHA `b52d9d62c3741112ca423f71e85fde923f6e5ba990e5b50a59b9fbff8bab8f1c`仅改为带类型的`float.hex()`编码并复用既有快照，保留全部行和值，不把内部benchmark哨兵当模型性能的有效值，也不删表/行掩盖问题。

v2已生成全1319张表的逻辑摘要和较旧点51快照`088b82c8…`到当前的逐行差分：新增295表、共同表新增19139行、原有行修改/删除均0。此范围不能冒充精确点56基线差分。逻辑摘要SHA `0fb3c9fb2c69a3a061d576fb5298dbeadc2decaf4a71a3ea346246f816a7f177`，逻辑缓存SHA `81502ef5a08e3cbcb6e7b52c22d0bc9e405b3cf4ce877fe472fb2c2044969dc9`，差分SHA `a960446b0c37ea5f9e8b7fd033e3298532062e509b19e94d9ede8f894dfc6c40`。v2最后因误假设FGV也insert-only而停止：FGV实际用`session.merge`，不能放宽成“所有写入不可能改配置”。v3只接续原证据、分别记录两库真实未变策略，命令SHA `a49240ac1e1b48c70b209cee2d51f3ef489ea8da816c05824f8f8ef1c48f24f6`，零模型/生产DB变更，原失败保留。

11:05缓存审计接续通过：1319张表均为调参缓存，697张winner、622张benchmark、共82826行；当前一致性快照SHA `ccd2184275d2d8bdb295b30c088f233d07a4e9e51f98521f72a2d9d23dcd3ac7`（证据备份的物理文件SHA不等同于原DB主文件SHA，实际配置由逻辑摘要绑定）。生产DB/main与源码/原参数/实例未变，零生成。

新`targeted`对照控制命令`control-cache-v1.py` SHA `a4f3e943ed5c01b3919351100d4cc3439c84121b1e78f2fb0196c5aedde5244d`，9项CPU策略测试通过，含27种原生结果组合仅全pass才晋级，以及保留实例回归失败回退检查；不代表模型设备通过。独立只读DB快照工具SHA `5260f1ee04bf0d664b648548bcb05d2f2df74cd2ac34b9dd51f6f6634f92b1a1`。先prepare三项dry-run再唯一dispatch，重测新baseline/candidate/revert各Mixed→Decode→Prefill，仍为原P1K workload、8+3、3%收益/5%尾延迟与spread/3%回退漂移。旧abr-01保持incomplete，不修改比较器或增加允许DB变量。

本轮明确冻结每个角色/阶段前后及回归后：生产主文件SHA必须同为`2c39b972…`，全部1319表（含winner配置和benchmark）的逻辑SHA必须同为`81502ef5…`；每次保留一致性证据快照但不拿它替换运行DB。任意真实表/配置变化停止、不补跑、不归一化。目标命中复用完全相同候选/16rank trace的SHA验证，无新profiler配置。若新原生Mixed及两阶段守护全passed，按本次用户授权重新安装同一份FG补丁、原脚本启动并完整最小模型/FULL/C64回归后保留；否则精确恢复原版。不同于旧轮“终态总恢复原版”的授权，条件保留只适用于这次新闭环。源码变化不伪造173/198绑定或新正式gate，不自动关闭P1K/四场景，不提交推送。

对照准备v1在零请求阶段因缓存审计与复用生命周期模块都使用`prepared.json`文件名，模块读取`freeze_SHA`失败。已生成的原始快照、配置及freeze全部保留；v2 SHA `5301f2f0177b4e154b7a3d0281821db39b0531149b1b6e8efbf95fe4e12aa9b0`只接续现有材料，为模块单独路由准备回执，并将条件保留时第二次安装的源码回执另存，避免覆盖首个安装/回退记录。未改kernel/采样/阈值，准备失败未发模型或性能请求，未停止/改变服务。

11:17:08新三项dry-run、同缓存/源/index/实例检查通过，`control-freeze-v2.json` SHA `4b23408b631e3c485a964f669e0ff01baa72c25eff36b183e7321a99b1cbee29`；10项CPU编排策略测试通过。下一步仅唯一派发该v2新对照，不恢复/重启旧轮控制器。

11:18:41唯一派发新控制器`3054343:544133089`，新`control-dispatched.json`为归属证据。`glm-align`重新建立、每30min仅跟进此新目录，不以旧轮终态停止监控；准备阶段失败均已保留且零模型请求。原版baseline正在执行，候选尚未安装，不能提前保留或报新收益。

精度绑定工具新增独立schema6 `cache-rebind`，原schema4纯重启/schema5同实例缓存流程保持严格；只直接引用原始schema3，不能链式绑定。用户显式授权、缓存schema/writer和历史字节缺口、前后runtime、当前完整最小回归/FULL capture及至少两次多token运行回放覆盖均需SHA证据；源码/配置/设备/URL/策略仍严格相同。该工具只复用原生分数，不证明性能缓存可比性。新增8项combined分支测试及原缓存测试通过，代码全检255通过/3skip，随后增加原始观察引用复验并通过44项精度测试。零生成生产命令`cache-bind-original-v1.py` SHA `33b4402940fb7ba1ecd7096408d82ab8d7174a1d90bcbaeec99d2d168e29dea1`，只适用于当前未装align的原版实例；工具包SHA `4b7d00f4960a3ee731440cbb0d68034b486e5341f112101f5e317cfd01eb9f34`。当前模型多token回放属于runtime覆盖、不是逐rank launch trace，不能用旧候选trace代替当前证据。

11:27:58原版精度显式绑定签发及原生check通过：`accuracy-binding-original/accuracy-gate.json` SHA `5ab6067ef1aed0757e62fd9d6577db83ff0a9b8195aedda123adaec5b8f8aa99`，原始schema3 SHA `2f71fcd2dde7eac6282c1518a1a6283bf10fbd4a2debdfee57fa2ebd487c6266`。仍为原生单次173/198＝87.3737%≥86%，非重跑或补充分数；绑定原版`3723831:541125214`及当前DB，不改原manifest/URL/策略。零新模型/设备请求，未绑定尚未安装的新align。最终本地`validate-local --code`255通过/3skip，语法/帮助/原资产/空白检查通过；非远端模型或完整记录验收。

最新只读跟进：新控制器PID/start匹配、health200、无失败/恢复失败/终态回执，原版Mixed已有4份逐轮validation，尚未完成该组，候选未安装。全仓记录检查仍因其他案例已有过程文件失败，本GLM案例未出现匹配问题，未改无关记录。当前仅原版精度绑定修复和新对照执行，未确认新增收益。

### 11:52新轮基线进度（仅原版，不是收益）

`cache-comparability-02`的Mixed P1024/D1024/C64/N128已完成8预热+3测量并原生复验。末3预热吞吐spread1.4633%；测量输出吞吐中位1157.7680 token/s、spread1.3240%，全部约定指标spread≤5%。Decode正在执行、Prefill待执行，尚未安装候选。5个缓存检查点的主文件及全表逻辑SHA完全一致；当前原版源/index、实例、原参数与health200复核通过，schema6原173/198绑定再次原生check通过。

| Mixed baseline测量轮 | 输出token/s | 总token/s | P99 TTFT ms | P99 TPOT ms | P99 ITL ms | P99 E2EL ms |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1157.7680 | 2315.5360 | 5377.8155 | 53.8198 | 52.0635 | 57102.3946 |
| 2 | 1143.6935 | 2287.3870 | 5349.0141 | 54.6107 | 52.6243 | 57597.2797 |
| 3 | 1159.0224 | 2318.0449 | 5417.3913 | 53.9275 | 51.7454 | 56899.6438 |
| 中位 | 1157.7680 | 2315.5360 | 5377.8155 | 53.9275 | 52.0635 | 57102.3946 |

延迟均为客户端代理，不是纯设备耗时。请求吞吐三轮1.130632813/1.116888201/1.131857851 req/s。原生run-record SHA `e9234393a5a9d03c678d2f319afda5499401f632cadb0d62c233274e3ed2f08f`，阶段result SHA `e57985812b34b4abc732196c7ab3a436cbdd579a283ca1e1f9b7a1728065944d`；原始轮次全部保留。当前没有候选/回退比较，不输出新收益或漂移结论；monitor继续只读、不额外请求或重启。

## 新同缓存三臂终态：有小幅改善，但未达到保留门槛

新轮于2026-10-23 13:31:25结束，三臂三阶段各8预热+3测量共99轮全部完成；原生逐轮计数/长度/命令/输入和产物SHA、全部指标稳定性及冻结比较独立复验通过。Mixed比较是可比数据上的`failed`，**不是**DB混杂的`incomplete`：输出吞吐1157.7680→1189.1990 token/s，改善2.714796%，低于预冻结3%。Decode改善2.354972%，Prefill总吞吐下降0.164506%，两项非回归守护均通过。不能改成与回退或B/R均值比较以跨过门槛，不能混用旧轮4.1964%或丢慢轮。

| 阶段/角色 | 三轮主要吞吐（token/s） | 中位 | 吞吐spread | 全部约定指标最大spread | P99 TTFT/TPOT/ITL中位（ms） |
|---|---|---:|---:|---:|---|
| Mixed P1024/D1024/C64/N128 / baseline | 1157.7680 / 1143.6935 / 1159.0224 | 1157.7680 | 1.3240% | 1.6881% | 5377.8155 / 53.9275 / 52.0635 |
| Mixed P1024/D1024/C64/N128 / candidate | 1197.7364 / 1183.4996 / 1189.1990 | 1189.1990 | 1.1972% | 1.4006% | 5345.8286 / 52.5650 / 50.0375 |
| Mixed P1024/D1024/C64/N128 / revert | 1156.9011 / 1148.4791 / 1142.7079 | 1148.4791 | 1.2358% | 1.6625% | 5382.4503 / 54.0999 / 52.4485 |
| Decode P1024/D1024/C64/N64 / baseline | 1172.1567 / 1175.6079 / 1144.1783 | 1172.1567 | 2.6813% | 2.8494% | 5351.2856 / 52.5423 / 51.3325 |
| Decode P1024/D1024/C64/N64 / candidate | 1222.0905 / 1199.7607 / 1185.9110 | 1199.7607 | 3.0156% | 3.1062% | 5350.2585 / 51.2850 / 49.8176 |
| Decode P1024/D1024/C64/N64 / revert | 1171.4113 / 1159.3883 / 1156.8990 | 1159.3883 | 1.2517% | 1.3087% | 5343.0738 / 53.1519 / 51.9912 |
| Prefill P1024/D1/C64/N64 / baseline | 12290.0339 / 12299.4422 / 12333.0098 | 12299.4422 | 0.3494% | 0.3494% | 5324.6377 / — / — |
| Prefill P1024/D1/C64/N64 / candidate | 12303.0991 / 12279.2089 / 12184.7775 | 12279.2089 | 0.9636% | 0.9838% | 5332.6958 / — / — |
| Prefill P1024/D1/C64/N64 / revert | 12319.8535 / 12333.4188 / 12322.4409 | 12322.4409 | 0.1101% | 0.1101% | 5315.0000 / — / — |

Mixed/Decode主吞吐为输出token，Prefill为总token；延迟都是客户端代理，包含网络/调度/排队，不是纯设备耗时。单token的TPOT/ITL不适用。每项全部三轮和所有原生指标、run-record SHA保存在state的`cache_comparability_02.terminal_native_results`及远端原始记录，不仅保留表中中位数。

B/R吞吐漂移Mixed0.802314%、Decode1.089309%、Prefill0.186990%，所有约定BR守护<3%、测量spread最大3.106245%<5%；Decode候选吞吐spread3.015557%高于baseline2.681348%，不能宣称波动改善。Mixed P99 TTFT/TPOT/ITL分别改善0.594793%/2.526472%/3.891412%，不是可相加的总收益。

### 缓存、恢复和精度边界

本轮24个阶段/回归检查点加最终独立只读快照，共25个检查点，生产主SHA均`2c39b972…`、1319表逻辑SHA均`81502ef5…`；所有一致性证据备份SHA重新核验，未清/复制/回退生产DB或改URL/策略。真实代码/参数只有一份FG align差异，原冻结比较不增加DB允许变量。

控制器未安装retained实例，按原门槛精确回退一份FG补丁。13:51:38独立当前审计通过：实例`3825111:544654758`，原FG`1a6197b7…`/用户Plugin`1ecb0ef3…`/FGV`ba76c1df…`及vLLM源码、全部Git index、原argv/env/权重/tokenizer/thead、唯一安装、镜像和挂载、health200/空闲均核验；回退整模C1/C8/三16K/11答案/C64/FULL及多token运行覆盖通过，16worker无hook/TileLang。没有新模型请求或服务/源码变更。审计SHA `386243097fa45ff52f64f12e774540eb9e7f2c6923ab530084858bd6d71c8660`。

13:53:08回退原版实例`3825111:544654758`的新schema6 gate签发并原生check通过：`accuracy-binding-final/accuracy-gate.json` SHA `a4f3dbe1ec353a161c9bd644472cbec0385c18c11be9e6543c782a4d75beba69`，直接引用原始schema3（非baseline schema6链式），仍173/198＝87.3737%≥86%。旧baseline3723831绑定完整保留但不再声称为当前实例；此操作零模型/设备请求，没有新GPQA、分数或候选源码绑定。当前原版恢复及绑定闭环完成，`glm-align`已删除（工具返回deleteStatus=deleted），不再定期轮询本终态。

原生比较SHA `c25ca071c9bbecad287156a8ec12d76cef06c3074b94d5547604187910a4cc97`；守护SHA `52d1047e14561829a1d0f496400357d73a37392fac4b88c9cd42df1d22ffe950`；completion SHA `305b5a95ec753f19f80a193e9454b03eaee77b9a9767c86dc167e97f8edfdd36`；恢复SHA `ee1c69c929b89cc94b848ac8db6b6ba5d56872376cf530bd1139cdaeb59c5fc3`。这些结论只属于本轮targeted/performance_only P1K，不能作为新源码198题gate、四场景或长期稳定性验收。

### 复盘与下一方向（仅计划，不由monitor派发）

规划复盘`planning-20261023-point56-same-cache-terminal`：旧轮因缓存差异incomplete，当前轮可比但收益2.7148%未达3%，因此新align不保留。相对本轮scenario-entry没有已部署新增收益；当前用户源码组合与原版一致，不能将早期revision、单算子4.75×或两轮百分比累加。当前Prefill近似不变、Decode/Mixed有小幅改善，未做候选reprofile，热点迁移未知。

1. **MoE GEMM2实际配置/单K tile流水**（operator/improve，Decode/Mixed）：点55同源码MoE为最大已记录设备family，但具体GEMM1/2拆分及当前winner未证实。先离线使用既有trace、真实函数对象/源码和当前DB key确认dtype/shape/impl/config；若确有可消除流水开销，另冻结单变量全链FP32 oracle与改变输入graph微基准。编译器已消除该开销、未命中、数值/graph失败或全链无收益即停止。需要key-operator-analysis；设备实验前新experiment-id/冻约，后续必须targeted同配置Mixed≥3%及Decode/Prefill守护，不改MBT/启动参数。
2. **BMM producer-consumer layout/物化**（operator/replace或improve，Decode/Mixed）：点55BMM为第二family，先从既有correlation与真实callsite证明shape/stride及多余复制，不能仅凭累计kernel时间断言关键路径。只比较一项backend或融合变量，完整链数值/graph、额外复制代价和Mixed净收益一起检查；没有边界/依赖证明或复制抵消收益即停止。需要key-operator-analysis，缺归因时仅离线profiling analyze，是否重采另行冻结。

调度器泛化改写和通信重排暂缓：主机runqueue很小、PCCL存在rank重叠与等待，未证明可消除关键路径；不因本轮小幅正收益而叠加未证明的框架特例。下一复盘触发是首个上述候选的明确证伪/同配置结果、热点迁移或准备较大框架投入。没有自动安装下一候选、发额外请求或提交推送。

## 优化方向与瓶颈依据

当前实际通用MoE调用链是 Plugin `TritonExpertsFL` 分步流程→CachedOp/flagos→**FlagGems**，不是以环境变量默认0关闭的FGV通用MoE入口。GLM特定算子仍可使用FGV，不能泛化。真实Decode rank0的5376次`moe_align_block_size_stage2`累计277.698ms/6489.893ms窗口；该数值不是可直接消除的端到端时间或收益。Mixed完整归因是GPU实验的显式前置。

当前288专家不是二次幂，已有实现用288轮标量load/add/store；二次幂已有向量cumsum。首个证伪：给既有向量路径增加补齐维度、masked load(other0)/store，使非二次幂E≤1024复用；大非二次幂仍走原标量路径。只改变整数前缀计数，保留topk、专家顺序、padding、token scatter、GEMM、TLE及vendor override边界。

## 优化内容与设计边界

候选仅修改实际FlagGems既有`src/flag_gems/fused/moe_align_block_size.py`，不新增算子、thead文件或Plugin分支。拟修改11增/5删；这是现有kernel实现改善，不增加公共环境变量。二次幂路径仍用同样cumsum、mask全真；非二次幂>1024保留原实现。多平台公共fallback受影响但其他平台硬件未测，TLE和平台专用覆盖未修改；`pr_readiness=experimental`。

修改前身份：Plugin用户内容`1ecb0ef3…`/FGV`ba76c1df…`/FG`1a6197b7…`，完整身份和index引用点55修复轮当前审计。当前原服务3512273/540201965健康空闲、完整模型/FULL/C64已回归，原生173/198≥.86分数保留；重启及DB写入严格绑定缺口不伪造。本轮初始仅targeted微基准，不能代替正式模型精度或四场景验收。

## 预冻结证伪与晋级

1. 外部独立副本测试，不改已安装库或服务。精确int32前缀、完整route/padding/count oracle，覆盖E1..1025的二次幂/非二次幂、M0/1/8/31/32/63/64/65/127/128/129、int32/int64与均衡/集中路由；完整枚举以保存命令为准。两角色各至少2次改变输入的graph replay。
2. 全alignment graph微基准M8/32/64/128/256/1024/4096、E288/topk8/block32，baseline/candidate/revert各保留7轮。不是独立stage2或端到端测量。目标M64/128完整链中位耗时降低≥20%且正确性全过才进入安装候选；否则停止/复盘，不凭最好单轮晋级。
3. 晋级后先保留精确源文件/index快照，在原参数服务验证完整minimal、三16K边界、11答案、C64及FULL capture/至少两次多token回放。任何候选数值/服务/graph失败停止，回退仅本点精确SHA匹配diff，原有dirty/index不动。
4. 模型通过后采用性能Skill `targeted` 同配置无profiler Mixed三臂与Decode/Prefill守护，各8预热+3测量，最后3预热吞吐spread≤5%；Mixed吞吐≥3%、P99退化≤5%、全部约定测量spread≤5%、回退漂移≤3%。全部轮保留、失败不丢轮/盲重跑；它仍不是新正式gate或四场景验收。正式场景关闭前须补当前有效精度gate。

## 性能效果

### 04:10 最终结果：数值良好，严格归因incomplete

`targeted`，父场景P1024/D1024/C64/N128；Mixed测原父workload，Decode为N64阶段专项（仍含Prefill/调度），Prefill为D1/N64代理。三个角色每阶段8预热+3测量，共99轮全部保留、九份原生run-record重新核验通过，无补跑或丢慢轮。每角色仅一个独立服务实例，不声称统计置信区间、长稳或正式四场景验收。

| 阶段，吞吐口径 | baseline中位 | candidate中位 | revert中位 | A/B表观差值 | 吞吐spread B/C/R | B/R吞吐数值漂移 |
|---|---:|---:|---:|---:|---|---:|
| Mixed，输出token/s | 1144.050533 | 1192.058958 | 1149.902462 | +4.1964% | 1.3761% / 1.4775% / 1.6201% | 0.5115% |
| Decode，输出token/s | 1158.751948 | 1198.751213 | 1148.244912 | +3.4519% | 2.1158% / 2.5215% / 2.6444% | 0.9068% |
| Prefill，总token/s | 12314.228511 | 12324.112029 | 12316.471670 | +0.0803% | 0.1601% / 0.1696% / 0.1394% | 0.0182% |

九组所有约定测量指标spread最大3.2559%≤5%；Mixed所有约定指标最大B/R数值漂移0.5115%，Decode守护最大为P99 ITL的1.2824%，Prefill守护最大0.0191%，均≤3%。候选P99退化均≤5%，完整值见下方候选段及原生JSON。**稳定性达到数值阈值，不等于波动相较基线进一步降低**：Decode候选吞吐spread2.5215%高于基线2.1158%，不能宣称本点改善了波动。全部primary三轮已写state；回退Decode三轮1172.335207/1148.244912/1141.971190，Prefill三轮12301.310283/12316.471670/12318.473692 token/s。

最终`comparison-result.json` SHA `98b5acb32e45a99264fa9d25e5aa3db0657c532f9331a61b7d0764af361963b2`为`incomplete`：预冻结主要变量仅`/flaggems_sha256`，实际候选还变化了`/launch_config/flaggems_db_sha256`。`phase-guard-result.json` SHA `f51184f36d17bfd7c69542eec6eb46d17dc7fee9d47a507d1a9c7e86d9affd5c`的Decode/Prefill亦`incomplete`，虽数值非回归项全部通过，但B/R身份不一致且候选存在未声明DB差异。基线DB`6a7822d7…`，候选与回退DB`2c39b972…`；没有回退/清理/复制DB，没有修改原manifest或SHA，也没有事后增加允许变量。DB字节变化本身不证明模型精度或策略退化；本监控未查明具体调参行差异，不能将原生incomplete改报passed或failed。

### 当前恢复与审计闭环

04:10:41独立`final-monitor-readonly-audit-v2.json`通过，SHA `2641e47518b0676702818feecf7effc54b2ef6102a2562b549f55de223de46fc`。当前原版实例`PPU-13:glm5.3-flash-opt-20260911:3723831:541125214`健康200且空闲；四库源、三库index、argv/env、权重/tokenizer/thead及当前DB均与已恢复实例相符，原MBT32768和启动脚本/推理参数不变。Plugin/FGV/FG各一份安装，实际导入原私有目录；同一冻结镜像、源/优化容器挂载一致、源码不在共享挂载内。16个当前worker PID/start及无hook/TileLang maps通过，控制器均已终态。

已有同一回退实例C1/C8、三16K边界、11/11答案、C64 64/64与FULL捕获/多次多token请求证据有效；恢复实例未新增逐rank trace，实际16rank各5次graph launch属于候选诊断实例，不能混称。v1审计的schema错误和部分产物保留，v2仅修证据检查，零模型请求/服务或源码变更，九组native及原冻结比较重新核验得到相同incomplete。原173/198分数保留，不改绑新实例、不跑新GPQA或签造gate。

## 决定、风险与回退

`decision=incomplete`；部署决定为精确回退并保持原FG全树`1a6197b7…`，本点候选只作为外部patch保存，未自动部署/提交/推送。整数oracle、全链micro、整模最小回归和实际命中通过，支持“候选值得进一步可比性验证”；不能支持“确认当前E2E净收益”、正式P1K关闭、后续三场景或长期验收。

规划Skill复盘`planning-20261023-point56-terminal`：当前组合仍为用户Plugin1ecb0ef3/FGVba76c1df/原FG1a6197b7，本点没有新保留改动，累计收益unknown，不加总历史或micro加速。优先1是只读核对既有DB快照及实际命中key/config差异（若材料存在），判断缓存可比性；任何重测须另行授权并事前冻结一致缓存协议、原数值门槛和新三臂，不能重标旧轮。优先2为从点55既有trace拆分MoE两投影并确认真实选中配置，再证伪GEMM2 K128单K-tile流水；优先3为BMM布局/相邻依赖的shape/stride/correlation证明后单变量对照。每项均先oracle与改变输入graph、再同参数targeted Mixed及阶段守护；任何数值/graph失败或无完整链收益停止。未证明CPU排队为主瓶颈，暂不做通用调度重写，不改MBT或扩展Host。监控不执行任何新候选/采集/测量。

本轮正式终态及当前审计已闭环，`glm-align`已通过产品工具删除。下文全部为过程历史，不覆盖上述最终决定。

### 04:06 三臂终态，严格比较incomplete（终态当前审计待执行）

唯一控制器03:42:49结束，`follow-completion.json` SHA `7db516392eede73142c4c1e633321c25e1c09a689786d381c4409aa450ac3f83`；原版服务恢复回执SHA `438fb3c4e7939e620b2301367712cac4bc7101c1d920d745776f0904e0797fb4`。九个阶段/角色均完成，但原生Mixed比较与Decode/Prefill守护均`incomplete`，原因是冻结仅声明FG源码变化，实际另有DB SHA变化；不是精度失败，也不能把数值良好改判原生比较passed。

保存零生成终态审计命令`abr-01/commands/final-readonly-audit-v1.py`，SHA `51a6a06267b54e8527f9e83edc71c9a7d331bb32fc343d1317664bb0f4ea397e`（本地AST通过）；只重验现有原生结果、相同冻结比较和当前原版身份/安装/镜像挂载/健康/既有模型回归，不发模型请求、不改库/服务/DB/原始采样/门槛。审计完成后再记录闭环并删除monitor，不为此重新跑任何阶段。

审计v1在九组原生数据/比较复验及当前runtime取证后，因把`worker-no-tilelang.json`的原生PID映射误读成status/workers信封而KeyError；原命令与已生成runtime/service/worker证据保留，零模型请求、未动服务。新`commands/final-readonly-audit-v2.py` SHA `1e6608b146527ff8634250e8ac6bc28391390827578e97bdf3cf0a9f716db2d7`只修证据schema并重核16个相同PID/start及当前maps，不改变原生数值、门槛或三态比较。新文件保存后才执行，不重跑三臂或模型。

### 03:36 回退测量接续（未终态）

Mixed回退8+3已完成、原生复验通过，输出吞吐三轮1164.532592/1149.902462/1145.902640 token/s，中位1149.902462，吞吐spread1.6201%，全部约定测量指标最大spread1.8985%。相对基线的吞吐数值漂移0.5115%，全部约定指标最大B/R数值漂移亦0.5115%，均未超过3%；这里只说明已完成Mixed的数值检查，不代表严格身份比较通过或完整三臂通过。

Decode回退已有8轮validation但尚无终态run-record，Prefill待执行；控制器仍为原登记PID/start，当前原版四库和index guard通过、同一回退实例health200。DB差异保持原记录，未修改测试/门槛、追加请求或干预控制器。流程正常继续，等待剩余阶段和最终恢复审计；此时没有新的完整收益/失败结论，不重复通知常规进度。

### 03:06 候选三阶段完成，回退测量进行中

三个候选run-record经原生检查器再次零生成复验通过，各8预热+3测量，全部约定指标spread≤5%，全部采样保留。它们与基线的描述性差值如下；目前不是通过三臂验收的优化收益。

| 阶段与吞吐单位 | 候选三轮 | 候选中位数 | 吞吐spread | A/B表观差值 |
|---|---|---:|---:|---:|
| Mixed，输出token/s | 1207.796255 / 1192.058958 / 1190.183705 | 1192.058958 | 1.4775% | +4.1964% |
| Decode，输出token/s | 1216.877779 / 1198.751213 / 1186.650923 | 1198.751213 | 2.5215% | +3.4519% |
| Prefill，总token/s | 12329.418390 / 12308.516292 / 12324.112029 | 12324.112029 | 0.1696% | +0.0803% |

候选Mixed的P99 TTFT/TPOT/ITL相对基线分别+0.0382%/−4.3828%/−4.5063%，Decode分别+0.4508%/−3.4646%/−3.6665%，Prefill TTFT −0.0937%；均是客户端代理指标，不是纯设备阶段。全部约定测量指标最大spread为2.4072%/2.5215%/0.1696%。原生run-record SHA分别`4e19fd68132d6e24639c3ff878a25677bf40e9126c7e65710a5ddfe667a781ff`、`98dd476918372ff76f51e935a0ecfdcfc1929c80b9c0394852f0eeaf91e3e13a`、`911840916a0da1edf1eacc58d878bbcb53729f4b3055d7a89cf2ff95d14bb93d`，完整逐轮和P99留原生结果及state。

控制器已于02:57精确停止候选、SHA匹配反向补丁并恢复原FG全树`1a6197b7…`；`source-reverted.json` SHA `dadbf9fd4295c8bcccfe325527d825a1d9755dfd4d55981f6735186bc20694d8`。当前原参数、无profiler回退实例`3723831:541125214`已通过C1/C8、三16K、11答案、C64及FULL；模型audit SHA `159e7096ae626e336731fac580c478f483f15d74bc8f61de7f020348fd433bf4`。03:06当前四库源、全部index、推理稳定身份检查及health200通过，未动用户Plugin/FGV或原dirty。

回退Mixed已有2轮validation、未终态，Decode/Prefill待执行；必须继续原唯一控制器，不能补跑基线/候选或提前报回退漂移改善。候选三阶段前后及当前回退DB均`2c39b972…`，不同于基线`6a7822d7…`；最终严格原生身份比较与回退数值守护仍待定，原指纹不改写、不归一化、不宣称已确认收益。原173/198不改绑新实例/候选，本轮非新正式gate。监控仅复验已有证据；以下为历史时点。

### 02:36 实际命中与无profiler候选回归通过

`candidate-hit/hit-evidence.json` SHA `d9f1e0c67da4996c5a405cc0ee953cbb88b49159e7a311a17b1eee5f88b0c55e`证实16worker各有294次`moe_align_block_size_stage2_vec`、旧scalar为0、各5次graph launch，超过事前84/0/2要求。02:36只读复验全部原trace SHA和CPU PID—TP rank映射通过；不是仅以安装或类选择证明命中。诊断实例C64与完整最小模型/FULL亦通过，但采样时间不作为性能。

唯一控制器随后已停止精确诊断实例，并直接用原脚本启动无profiler候选；当前实例`3683676:540854246`。C1/C8、三个16K边界、11项明确答案与P4096/D16/C64/N64再次通过，`candidate/c64.json` SHA `9cefc3cb2c71ceeabfe94c8a9829c750030221074d60c278904b924c6873b11a`，`candidate/final-audit.json` SHA `bfd1920f553a16b57643b088868deed4c14642dc7efbaa1234db0e31e8e0d87e`。无profiler候选有FULL capture及多次多token请求证据；逐rank真实launch trace属于之前独立诊断实例，不冒称候选性能实例再次采trace，也不以旧公共子图证明本点。

02:36:38当前源/index及稳定推理身份检查通过，health200，原MBT32768和全部推理参数不变，无profiler。Mixed已9轮原生validation，每轮128成功/0失败，尚无阶段终态run-record；Decode/Prefill及revert未完成，不用部分轮次推算净收益。当前生产DB实际SHA为`2c39b972…`，与基线`6a7822d7…`不同，保留实际字节及原manifest；最终仍按冻结的严格身份比较，若存在未声明差异则维持incomplete，不为得到收益归一化DB或放宽阈值。监控只读，未追加生成、采集、服务操作或新实验；以下02:10及更早为历史。

### 02:10 基线终态与候选回归进度

`abr-01/baseline-completion.json`于02:02:06生成，SHA `f21a5ce74a88c0a0d5ea3bc69feab310eae5c7491d4ba986f51b48553bbad026`。02:10:21零生成再次调用原生检查器核验三个run-record，各8预热+3测量全部有效、全部约定指标spread≤5%；没有丢轮或补跑。

| 阶段与吞吐单位 | 三轮原始测量 | 中位数 | 吞吐spread | 全部约定指标最大spread |
|---|---|---:|---:|---:|
| Mixed，输出token/s | 1159.738046 / 1144.050533 / 1143.994555 | 1144.050533 | 1.3761% | 2.5475% |
| Decode，输出token/s | 1172.062262 / 1158.751948 / 1147.545032 | 1158.751948 | 2.1158% | 2.4444% |
| Prefill，总token/s | 12314.228511 / 12316.977408 / 12297.261637 | 12314.228511 | 0.1601% | 0.1711% |

最后3预热主要吞吐spread分别2.0535%/2.0923%/0.1417%；基线DB各阶段前后均`6a7822d7…`。这是原版基线，不是优化收益，也不能评价回退漂移。

唯一follow控制器在基线退出后于02:02:20安装精确单文件补丁（`source-applied.json`）；02:09:52再次只读核验FG候选全树`030c82b8…`，Plugin/FGV/vLLM与全部Git index保持原样，health200。当前仅临时profiler命中诊断实例，原MBT32768及推理参数未变；C1/C8、16383/16384/16385和11项明确答案已通过，C64仍执行中。尚无C64终态、16rank命中回执或候选/回退性能，不能把安装成功、部分回归或局部微基准当作实际命中及E2E提升。监控未追加模型请求或干预控制器，继续等待原冻结流程；下文为此前时点。

### 规划复盘与当前边界

`planning-20261023-point55repair-point56`按规划Skill复盘：当前实际组合仍为用户Plugin1ecb0ef3/FGVba76c1df/FG1a6197b7，点54后尚无新保留源码。点55旧partial及所有工具/空输入失败均保留；修复后完整归因通过，点56有效94组合/graph micro通过、ABR在运行，不能把局部加速或旧revision收益加到当前累计收益。当前累计改善仍unknown。

优先级1为本点实际高命中的低风险整数计数浪费，但采样占比仅2.9–4.3%，净Mixed收益可能不到3%；以当前冻结三臂证伪。优先级2才是最大MoE族中GEMM2 K128单K-tile流水：尚缺真实选中config和两投影耗时拆分，先做该证据和单变量完整链FP32 oracle/graph micro，不能照搬历史stage参数。优先级3是BMM布局及Mixed index_put/通信等待依赖，未证明可消除关键路径，暂不扩大到通用调度。下一复盘触发为本点三臂终态或任何正确性/身份/证据失败；monitor不自动安装另一候选。

### 独立PPU微基准通过

01:06:09新验证唯一派发3205984/540457955，冻结SHA `7ff50867efba58d3c605e1b27ea656b94e39833aef7576e63117e2865c19f8c1`；01:06:38完成，`device-validation-02/device-result.json` SHA `0b3c436d9bd866b3322307dcba58139677f599636fc053703c948a7c47eb247f`。94个有效非空组合、两角色共188次全过，13种专家数的前缀逐位一致、两角色各2次改变输入graph replay通过。8组M0均在原/候选复现相同stage1编译错误，继承边界已确认、未声称修复或新支持。生产源/index、原服务未变，零模型请求。此前摘要/prepare说明误算182，已按原始JSON纠正为14+10×2×2×2=94，未更改原始测试矩阵/结果/旧freeze；旧文字错误保留说明，不能解释为删减测试。

| 完整alignment链中位微秒，7轮全保留 | 原版 | 候选 | 回退 | 耗时降低 |
|---|---:|---:|---:|---:|
| M64/E288/topk8/B32 | 60.9906 | 12.8365 | 60.9599 | 78.9533% |
| M128/E288/topk8/B32 | 60.9152 | 12.8157 | 60.8926 | 78.9613% |

这是约4.75×的局部全算子链加速，不是端到端收益。M8/32/256/1024/4096及全部21组×7原始采样均留同一JSON；大shape M4096耗时降低73.3212%，不能据此外推P4K/P16K/P32K场景已验收。

下一冻结`abr-01`使用当前维护版工具包SHA `e9f9b9e0be5596a5fc9a760e6e71ff606b87a3c6a045f3c8b171f7e142c5f974`，基线组件`commands/baseline-v1.py` SHA `c3996fecbfd64eae61e74a96546d9a8d9c2deb1e9b10e09a185158961dcfc41a`，先零生成prepare/dry-run再唯一运行原服务Mixed→Decode→Prefill各8+3；不改源码或重启。候选与回退将复用本轮同一预冻结plan/contract，不能重新跑较慢baseline或丢弃轮次。正式场景关闭前仍需当前有效精度gate；本轮targeted不能签正式验收。实际DB指纹/原始manifest全保留，若B/R身份漂移则原生比较保持incomplete，不为得到收益归一化SHA。

`device-recovery-01`于01:00:13派发3083233/540422286；标准patch已通过且候选文件SHA为预期值，但原版M0在stage1的`tl.arange(0,0)`编译失败，未进入性能测量。此为旧实现空输入边界，不是模型精度下降或候选数值失败；按accuracy-diagnosis冻结`align56-empty-baseline-stage1`，不顺手改stage1或静默删样本。新独立`device-validation-02`契约要求：原182个非空case逐位oracle完全不变，8个空case在两角色分别复现同一继承编译错误，不声明公共M0已支持。实际目标M64/128和模型正batch graph仍须全过。算法、误差、性能和三臂阈值未变，旧失败原样保留。

新prepare SHA `ccc09512792f3d389292318f77d7506abc61124132e27cc7130cde97c2a38e3e`，micro v2 SHA `3117a91eb614ce01925ddcfb18ff16b1682eeb3fb2132a0b11d7e7192a5787ca`，bootstrap v3 SHA `599ffc58275ab7c5ca580446f0b6cd247dbe28244ff2611b7d8f55c1942c9811`，控制器v4 SHA `889b3c8afe0ddd5b1b414279018f0988aab1acbd3d3e2491243ec1f1a3497a2b`；4份AST通过。新一轮任何正输入数值/graph失败停止，不叠加新优化；模型库、服务和用户代码始终未改。

派发v1在任何进程/GPU/模型请求前因轻量runtime缺containers被拦截，原命令/错误保留，不是算子测试失败。新`commands/run-micro-v2.py` SHA `f5e1fbd52273c048ca198ec46ddeae8b9bed1b23d26c6737d82a707806d44189`只从已冻结点55完整snapshot取得容器身份，其他字段及原micro/patch/阈值不变；3项CPU元数据断言通过。设备检查16卡0%且只有本模型16worker，各卡余约5GiB，无其他任务，原服务空闲。

预注册时尚未运行；局部约4.3%采样占比只是上界线索，预计净收益可能不足3%，必须由全链微基准和无profiler三臂证伪。上文已补微基准实测，端到端仍未得到结果。

## 回退与证据

01:43:22最终只读进度：baseline3492342/540541665和follow3766457/540621566均原登记存活，Mixed已有10轮原生validation、每轮128/128成功且0失败，整阶段尚无终态run-record，不报三轮中位/收益。当前原版三库和index全量guard通过、health200，source-applied尚无，候选未安装。`glm-align`继续只读跟进，无新增模型请求或干预。

只读monitor `glm-align`已创建，每30分钟检查唯一baseline/follow与原生证据；无变化安静，只在实质进展、失败、完成或需用户操作时通知，终态当前恢复审计后删除。全项目`validate-local --records`仍因既有其他模型schema/链接与过程文件不合规未通过，本点YAML/94组合及16rank事实检查通过，不处理或删除无关用户文件，所有本点过程脚本均在临时/远端案例目录。

01:32:05 follow零模型请求prepare通过，冻结SHA `d21f92993cdfeadec6bee31ef8f460a2f59e63d89a4ebb3957e24b50ac89afae`。原baseline仍由唯一控制器执行；接续命令即使已派发，也只能等待完整基线稳定终态且其PID退出后才进入已预注册的候选流程，不重复任何基线。当前尚未安装FG候选。

基线于01:20:07唯一派发3492342/540541665。后续接续控制器`abr-01/commands/follow-v1.py` SHA `2a827ca55d583818ffe30810191d9934e58f30379b36e4b42e322e7f12478211`，18项CPU mock测试通过（SHA `9bd7d3dcb33d7bedb85b68f8c653bd6b89cf8f55f40a6481e5e2d068b4953f3e`），覆盖源/index漂移、PID复用/外部接管拒绝信号、DB身份漂移不掩盖、守护不要求加速及failed/incomplete区分，不代表硬件回归。

该控制器必须等本次baseline三阶段稳定且PID终态才操作；只停止已登记API及后代，完整树与index强校验后安装一份FG补丁。为证明实际模型命中，先沿用已批准的临时profiler配置（仅delay0/max8/ignore_frontend，全部推理参数不变），完整模型回归后采一组P1024/D16/C64/N64命中探针：16worker均需stage2_vec≥84次、旧scalar=0且graph launch≥2。此采集只作命中，不作性能。随后停止精确诊断API，重新直接原脚本、无任何profiler配置启动候选，再次完整minimal/三16K/11答案/C64/FULL后，才测同一预冻结三阶段8+3。最后仅SHA匹配反向补丁、原脚本恢复和完整回归，再测revert；不混profile耗时或自动重跑baseline。终态一律保持原版健康服务，候选是否保留由本轮证据决定，不能自动提交/推送/换模型/加新候选。源码均在唯一/mnt挂载外的私有/workspace，操作前再核验。

01:17:25三阶段零生成prepare/dry-run通过，实际使用`abr-01/commands/baseline-v2.py` SHA `1e4875ae61bd9debd8f95f75aae46c86ffb64b3f3198e2bcaf9f70b74f9c39db`；冻结SHA `8ba4b20dfd81eb87417c27c1764c62298f6861332a0da00e4732b64a9d34e396`。未改已安装源码，由原FG全树entries仅替换一份目标文件hash预计算候选全树SHA `030c82b854d282fc943cc78ab2bf3db86f501fed47aff294514500085caf838b`，供后续严格验证而不放宽用户源码/index保护。v1因误写组合数在目录创建/请求前被拦截，已改为逐项枚举比对，原文件保留；数值和性能阈值不变。

原v2派发2982112/540392642在补丁context检查失败，设备上下文/显存探测已执行，但尚无alignment调用、数值结果或已安装源码修改。原失败及log保留。标准上下文补丁`align-candidate-v2.patch` SHA `1b20634a3dd5d7c7551bca0487e6c994697cc08cdf699342cd4035f57781ecaa`已在精确原文件副本通过git apply --check；候选完整文件SHA `2bfa00c14dcc2ff158d4e840709369ade5a7d7dde64faee5e6310d5071bc8447`，算法仍为原11增/5删。仅工具恢复使用新`device-recovery-01`子目录，micro脚本字节/枚举/数值检查/阈值完全不变。prepare SHA `7bdc655c76e90b170664d294c91c050bdf026e8bf4f9d73f905863d5f3b292da`、控制器v3 SHA `064b4c719e153c681ab6f39cf2ded868b61d2b004b95be3b80a2a4454a86aace`、bootstrap v2 SHA `fa681dc41c89c7e8b9526a8ef2767b5479565f47c23f5b41718a86b5a03ae961`。必须先确认原独立进程已退出和原服务未变，禁止覆盖原结果或把工具修复当数值失败后的重试。

零生成prepare已通过，两段16rank报告、原服务3512273/540201965和用户源/index重新核验，微基准冻结SHA `c7d41bbae68b76a7821a9761a8ffa567234b79ce011b53754550a73ae96dcf62`，算子原文件SHA `46badb074aab716d8d3e0cfcaf1dee6fa7738e562f959095f54a51ad196bc3ef`。独立GPU控制器`commands/run-micro-v1.py` SHA `c29bde1b961d7e0541c455f5943869ad39deaf3bd4db61a71396ee61d1ffed94`，bootstrap SHA `f4dd14d38e75340a8d68232793c7ff6f467a7f6aae4bde73f926a25369c2a665`，预算1800秒，超时只清理登记的独立PID/ticks/argv，不向模型进程发信号。原服务不停止、不发模型请求，生产DB不改。

- 远端唯一新根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261023-point56-align-prefix`。
- 初始准备命令先保存点55修复目录`commands/point56-prepare-v1.py`，SHA `507f3de203d85d9ffa1bb48e25a8b1abccd962bb8eb0ade1f6f0d69318a36c09`；核验两段归因/原服务、规范路径/空间后建立新根，复制自身到新根commands。零模型/GPU请求。
- `commands/align-micro-v1.py` SHA `1a0a63481db691b76e63ef177fe710ec14055bbf2909894826e5a3efbfed76ac`；`commands/align-candidate.patch` SHA `e6d81a9e21a76f9e8693abefb37675850879353c6d10ee3a05825a60c84de85d`，本地AST与diff结构检查通过；不等于硬件通过。
- 初始微基准只在外部副本应用patch，已安装源文件SHA必须前后相同，不写生产调参DB、无服务请求。安装及三臂控制命令尚未执行，须另存SHA后再执行，不擅自提交/推送。
