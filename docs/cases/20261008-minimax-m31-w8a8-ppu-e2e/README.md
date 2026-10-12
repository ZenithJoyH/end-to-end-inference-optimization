# 20261008-minimax-m31-w8a8-ppu-e2e：MiniMax-M3.1 W8A8 / PPU 总吞吐优化

## 1. 摘要

**用户暂停**：自动压测/采样已停止，8035候选服务同实例保留且健康、running/waiting=0/0，供用户手动评测。candidate01原生11轮已完成，但完整准入、比较和后续角色未执行；不自动恢复。

执行规则为 SOP v0.40 / 2026-09-22，验收范围 formal，当前 plan-016。独立优化容器镜像谱系与挂载门禁通过，源8025服务按授权停止、源容器仍运行。fw-001+fw-002+op-002 原源码实验组合完整GPQA170/198=85.86%达到81%门槛，单配置P1K基线2466.07token/s已准入；尚无已接受累计收益或保留改动。formal01原始基线P99TTFT轮间波动11.49%而停止，其他角色未运行。全rank trace之后的GC计时诊断仅在短Prefill预热第2轮发现长GC，测量轮没有，临时补丁已撤除、原始4套源码恢复且105+2通过。新formal02按所有角色6轮预热+5轮测量冻结，中位数验收和原门限不变、算术均值补充报告，第一独立原始基线6+5轮全部有效、完整准入和资源通过；5测量吞吐均值232.07token/s、中位231.95token/s，吞吐spread0.72%、P99TTFT spread1.31%、quiet0。第一优化候选capture、fresh107和相同稳定身份精度gate rebind/check已通过，6+5性能测量已启动。P1K未关闭，P4K/P16K/P32K未测，最终四场景验收incomplete。

模型记录：[baseline](../../../models/MiniMax-M3.1-W8A8/ppu/baseline/README.md)、[optimize](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md)、[acceptance](../../../models/MiniMax-M3.1-W8A8/ppu/acceptance/README.md)。本任务与旧M3 BF16实验独立。

## 2. 任务与验收契约

- 模型：`/mnt/cpfs/models/MiniMax-M3.1-preview-private-W8A8-FlagOS-20260929`，served name `MiniMax-M3.1`，tokenizer来自同目录并已生成内容指纹。
- 目标：PPU-07，16×PPU-ZW810E/96GiB，TP16；稳态总吞吐 input+output token/s，TTFT、TPOT/ITL与稳定性为守护。
- 用户远程根目录：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize`；无symlink、root:root/0755、初检约9.28TB可用。唯一案例子目录 `20261008-minimax-m31-w8a8-ppu-e2e` 为0700，创建前不存在。
- 外部证据根目录：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261008-minimax-m31-w8a8-ppu-e2e`；下文外部相对路径均基于此目录。
- 源容器 `minimaxM3.1`；源镜像ID `sha256:66aba903fec3373d3518183f77227a713fb20e0fbf48038e6c813329cbd53172`。适配的必要代码位于writable layer，故以native commit生成不可变快照。
- 优化容器 `minimaxM3.1-opt-20261008`；快照镜像 `minimax-m31-adapted-snapshot:20261008-env001`，ID `sha256:78d8e42f2f21568667fd8727be790073b34f2683de2d9c2b734813aaf3b5a8fe`。三套实际源码及安装vLLM文件树在源前后与克隆中一致，`image_lineage=verified`。
- 目录挂载均只有 `/mnt`→`/mnt`、rw/rprivate；规范化清单与机器diff见 `manifests/mount-comparison.json`，`mount_parity=passed`。无新增挂载；/workspace源码是容器私有实际副本，共享/mnt不改。
- 容器保持host network/host IPC、原设备与资源配置。源服务原8025；用户明确授权停止该模型服务及关联worker并开展优化，操作见 `manifests/source-service-stop.json`。源容器继续运行，未停止/重启/删除；恢复脚本 `commands/source-restore-service.sh` 已保存且未执行。
- 复刻基线 vLLM0.24.0+empty；Plugin实际revision `cafe6363c8c3de5ba4693b91643089c17b3ab87c` 带原适配dirty改动；FlagGems `6b49cff993956bff8cef495abd84f2acb6a63df6` 原clean，op-001原型目前未启用、原始FlagGems指纹已恢复；安装FlagGems-vllm模块为 `flaggems_vllm`，基线导入及内容SHA在 `manifests/baseline-service.json`，当前指纹另由新source-delta/manifest绑定。
- anchor graph配置FULL_DECODE_ONLY/capture=[1,2,4,8,16,32]；fw-001仅追加64。当前实验性fw-001+fw-002为FULL_AND_PIECEWISE、capture=[1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192]，FULL Decode实际仅≤64，Mixed为14桶；seq64，batched_tokens8192，max_model_len204800，gpu_util0.90，BF16计算/W8A8权重，prefix cache关闭。
- 正式精度 `gpqa_diamond_generative_cot` 完整198题，`exact_match,strict-match >= 0.81`。用户指定81%优先于旧记录88%。工程改善门槛预冻结为总吞吐+5%、P99 TTFT/TPOT/ITL/E2EL各回退≤5%；无用户绝对SLO，不宣称业务达标。
- 授权范围为目标优化容器私有Plugin/FlagGems-vllm/FlagGems副本与启动配置；vLLM、权重/tokenizer默认只读，不提交/推送。

当前事实以目标运行时为准。本次只读查看目标远端原适配 `03-acceptance/`/`04-runs/` 交付；greedy45K历史163/198=82.3232%，其他采样记录见env-001。历史分数仅作事实，不继承到新服务gate；未修改上游适配记录。

## 3. Workload

正式目标顺序 P1K→P4K→P16K→P32K，均D1024/C64/N128 finite batch；当前仅P1K，其他三项not_run。最终仍须原anchor与最终组合覆盖全部四项，不以缩减探针替代。

P1K入口计划 `performance/entry-p1k/plan.json`：random精确长度、/v1/completions、temperature0、ignore_eos=true、seed42、3轮预热+3轮测量。准入为末3预热总吞吐spread≤5%，保留全部准入后的测量轮；每轮600秒、首次基线诊断预算3600秒。超预算保存partial并转hybrid recovery，不计算跨workload加速比。独立Prefill探针P1024/D1/C64/N128已有单独计划；Decode先用Mixed TPOT/ITL代理，不能称纯设备时间。

fw-001历史比较契约 `comparison-v3.json` scope=formal，同时绑定capture列表和重复argv参数；要求每角色两个独立服务实例、每实例3测量轮，spread与baseline/revert drift≤10%。统一formal-plan-v3为5预热/3测量、末3预热spread≤5%、每轮1800秒。candidate01五预热计数完整，但末三轮spread16.39%，零正式测量；旧600秒失败尝试仍保留，原目标正式比较未收齐。

诊断后统一冻结v4：9预热/3测量、末4预热spread≤5%，连续窗口从末4预热起至所有测量结束不得有新编译，前后同Host时钟差值校验；全部角色同规则重跑，旧轮不混用。候选v4单实例已通过，两个独立实例/role和回退仍缺失。accdiag-003（schema4 rebind与snapshot路径不兼容）已修复维护版比较器并原生重验，原始数据、gate和门槛不变。原路径baseline-v4-01中位233.04token/s，与候选2449.15的单实例比值10.5096×；candidate-v4-02因spread7.20%及新编译准入失败，零正式测量。plan-007转fw-002可行性并已通过；当前plan-008先等待新正式精度，再做无profiler增量targeted。新计划包含P1024/D2/C64/N128 Prefill sentinel和完整原P1K Mixed，9+3及每case编译静默，baseline/revert为fw-001 capture64、每role一实例；总TPS不回退/P99守护≤5%的工程局部判断不替代后续combo formal两独立实例及四场景验收。

## 4. 正确性护栏

- [acc-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/acc-001.md) 使用本地精度Skill baseline-sanity，覆盖env-001；固定北京/巴黎问答正确，完成FULL decode graph capture；两次C1多token请求符合当前dispatcher选择条件，未启用直接replay计数器，该证据边界保留。
- 原sanity在请求前因expected_samples10而数据集预检失败，分类measurement-invalid；实际完整数据集198条，limit10控制子集。已隔离原产物 `accuracy/baseline-sanity/`，仅修正expected_samples198，在 `accuracy/baseline-sanity-repaired/` 同服务/C8/greedy45K、IDs0–9重跑已exit0；10唯一ID/20filter行完整，strict7/10、空/乱码/超时均0。accdiag-001 resolved，无模型精度下降归因。
- heartbeat `minimax-m3-1-acc-001` 每30分钟只读监控，复用同一监控；无变化保持安静，实际精度终态暂停。fw-002完整198题exit0后工具确认PAUSED；新实例最小回归前另更新scope并恢复。
- 正式任务provenance两次独立采集完全一致，SHA `430b9c86396c19aab5bb1d2fb2925a093a522e7d71b16f8ab767b74ca8599397`。198题契约 `accuracy/formal/contract.json` SHA `979bfdfb65a3e1697d524851f943923178951cfec1ec1dedffaa75ebec03cf42`；fw-001独立capture64为168/198=84.85%，fw-001+fw-002新组合为170/198=85.86%，均≥81%，分别绑定原生gate。新组合gate SHA `07663e9979f0f548a19b915c0ac7b1dfea30d7eeb65790b62d6b75ff1caba1b2`；重启须fresh runtime/minimal及明确rebind，不能交叉复用配置分数。

## 5. 基线结果

P1K原场景首轮预热600秒timeout/0完成请求，deferred-too-slow/incomplete；Prefill与D128/N64缩减Mixed基线已完成，不能替代原目标。P4K/P16K/P32K未测，无可比收益数据。历史baseline manifest-v2 SHA `4fe65ac49984ce0a92eb8d483c49fd3b1f2b3fa294b53f4eb4a37cab1cfcaa3d`，历史fw-001恢复manifest SHA `0dbdc2448b885ef8752e8ee490e5c5624dbe9beebc960045f88749bfc6b6366e`；当前fw-002 verified manifest SHA见第7节。模型权重指纹是实际路径/大小/mtime_ns清单，未声称逐字节校验全部tensor payload。

## 6. 瓶颈证据

三阶段视图及两配置分别绑定的全rank profiling已形成，详细指标见模型记录。C64超过原capture32被dispatcher置NONE，capture64后缩减Mixed单实例中位6.095×；独立重复/回退仍缺失。实际为native BreakableCUDAGraphWrapper。原始P1K慢预热发生约16秒跨请求停顿，并与新Triton编译相关；快预热无新编译。历史固定四轮诊断采全部16worker和PPU状态，未复现长停顿；第二候选还出现无新编译的1.18秒停顿。fw-002实际Mixed图证明也不等于旧抖动已修复，不以正常短trace或P99 ITL代替偶发停顿归因。

## 7. 实验记录

| ID | 内容 | 结果 | 决定 |
|---|---|---|---|
| [env-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/env-001.md) | 独立环境及谱系/挂载门禁 | verified / passed，8035 ready | complete |
| [acc-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/acc-001.md) | 基础问答与前十题C8 | smoke正常，修复后10唯一ID完整，7/10无formal gate | complete |
| [perf-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-001.md) | P1K稳态入口与阶段视图 | 原P1K首轮timeout，缩减Mixed988.83token/s，Prefill较噪 | complete诊断视图 |
| [fw-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fw-001.md) | C64 graph覆盖 | 缩减Mixed988.83→6026.91token/s单实例；完整GPQA84.85%；Prefill准入失败后ABBA/trace归因 | incomplete，未保留 |
| [fw-002](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fw-002.md) | 有限Mixed PIECEWISE图 | 16rank图执行/105+2/GPQA170/198通过；对照两阶段准入通过，候选Prefill新编译与延迟波动超限，后续停止 | incomplete，未保留 |
| [op-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-001.md) | 行索引动态输入行数 | 私有补丁全rank trace/105+2/新完整GPQA170/198通过；新targeted旧源码baseline静默失败，候选未测 | 未保留，PR needs_revision |

op-001实验补丁已归档，pr_readiness=needs_revision；无已接受组合收益。每个优化点使用稳定experiment-id、单变量比较与回归，按规划复盘触发条件继续排序。

当前进展以模型optimize/state.yml为准：fw-001原始P1K单实例约10.51×仍缺独立重复/回退。fw-002旧源码GPQA170/198=85.86%通过81%阈值；其Prefill候选末轮新编译与TTFT/E2E波动超限，已停止该invocation的Mixed/revert。plan-009定位图外索引后，op-001私有FlagGems完整树SHA d40d650e通过34trace/16rank模型图、105+2及新完整GPQA170/198=85.86%；newgate37f094da独立绑定本次评测，198实际API请求/新缓存命令另核验。监控终态PAUSED。新targeted固定graph配置、只改变FG源码，新对照105+2/rebind完成，但第12轮16个新cumsum source使静默失败，Mixed/candidate/revert取消。plan-010转既有原生cumsum的独立张量可行性 [op-002](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-002.md)。图外元数据调优仍在，平台边界和最终工程整理needs_revision。无已接受组合性能收益，全部旧轮及manifest保留。

## 8. 最终候选与回归

最终组合、完整精度gate、四场景baseline/candidate/revert及回退验证尚未完成。acceptance保持incomplete，不将中间sanity或最好轮移作最终结果。

## 9. 产物与回退

远端 commands/ 保存执行前命令与SHA，manifests/保存身份和门禁，logs/保存服务日志，accuracy/与performance/保存原始评测证据；所有大产物及私有题目保留远端，不入仓库。源恢复脚本已归档；当前保持优化8035服务及源容器，后续变更只作用于优化环境。没有提交、推送或删除既有材料。

plan-010的op-002只追加cumsum_out排除项，源码不变；336张量/14 graph、模型C8+2和34trace全16rank原生scan/模型图证明passed。恢复无profiler后105+2/新完整198及匹配性能尚待执行；微基准约2倍调用加速不等于端到端收益，候选未保留。准确身份和SHA见模型optimize/state.yml及[op-002](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-002.md)。

最新op-002新配置GPQA198已通过170/198=85.86%，唯一题目/原生gate/新缓存及实际198请求均核验；配置单变量targeted在原路径Prefill基线因quiet66及P99TTFT/E2E波动13.52%/12.24%停止，候选未测。plan-011转为独立建立native配置原始P1K Mixed稳态基线，只报告单配置事实；当前没有通过全部角色的组合性能结论，P1K及最终四场景仍incomplete。

plan-012 update: native originalP1K configuration baseline admitted2466.07total token/s, with quiet0 and stable guards, one configuration only. New combined intermediate formal contracts are frozen (4warm/3measure, two independent instances/role). Originalgraph32 baseline01 fresh105+2 passed and native dry-run passed; first7round originalP1K benchmark now running with identical planned 5s resource sampling. Native full198170/198 gate remains candidate-configuration-specific; baseline01 has sanity only. No retained gain, isolated contribution, P1K closure, or finalfour acceptance yet.

Plan014 checkpoint: combo-formal-01 stopped at baseline01 admission, measured P99TTFT spread 11.4911% exceeds frozen10%; all7 native rounds retained, candidate/revert and finalizer not run. Two same-service D2 phase probes admitted/quiet0; deterministic seed-only cause unsupported, attribution unresolved. Original32 + profiler-only instance1708143:422026779 is ready, fresh107 sanity running before bounded all16rank Prefill/shortMixed profiling. No retained change or accepted gain; four-scenario final acceptance remains incomplete.

Plan015: original32 all16rank+frontend PF/shortMixed capture andclockalignment validated; rank0PF392ms hostnoAPIgap withother15rankcollectivewait, GCunmeasured/profileralternative. WorkerFL lifecycle missingnativepostwarmheapfreeze verifiedfromcurrentcode. fw003 temporarydefaultoffGCtimer diagnostic01 hadINFOlogsfiltered, stoppedwithoutmodeltraffic; diagnostic02 correctsloggingonly andall16callbackinstalls confirmed. NewPluginFPd403c625575a584dc2146d578788ee679490ff2a31de0157212448ddebeb784a, sourceoldgatesinvalid; fresh107running. Freeze notimplemented, no retainedgain/newformalretry.

Plan-016 checkpoint: GCtimer shortPrefill/Mixed completed andadmitted;16longGen2events onlyPrefillwarm2, no >=100msGC in measuredrounds. Diagnosticpatch reverting, noheapfreeze. User latermean suggestion incorporated into proposednewformal equal6warm5measure/allroundsretained, mean supplemental with unchangednativeacceptance. FullP1K variancecause unresolved; no acceptedgain, P4/P16/P32notrun.

用户要求先停止优化、自行运行端到端性能。已执行归档user-pause-combo2-candidate01-20261009.py（SHA2ed4db33c29ff10df8ef02ed933ef02dbf4efa2fd357e65ef1282437026ec9ee），只核验/停止本任务压测客户端和采样器；当前native客户端已自行exit0，11个轮次validation存在，尚未做候选完整准入、资源汇总或组合比较，不继续回退及第二组。实际暂停回执control/combo2-formal-candidate-01/user-pause-result-20261009.json：客户端无剩余、资源采样已停止、8035服务同实例1507199:424436444健康且running/waiting=0/0，源容器仍运行。精度心跳工具确认PAUSED。保留当前fw001+fw002+op002候选服务供用户手动评测；未接受优化收益，只有用户明确恢复后继续。

用户明确要求把手动端到端测试后的候选配置写入根目录启动脚本。已原子更新 /mnt/nfs/users/jinghao/minimaxM3.1/start-model.sh，SHA91b2d8f309614b4d86ccc8f23a476b6268c524b0803f1ba3f30c25d55bf78c34，保留0755/8025/MiniMax-M3.1/nohup/service.log接口；同步已验证候选环境exports、cumsum_out exclusion、FULL_AND_PIECEWISE和14 capture桶，并固定实际Python/vLLM入口。Host及优化容器bash -n通过；未执行新脚本，当前8035服务仍为原实例1507199:424436444，没有重启，自动优化保持用户暂停。原脚本备份于root-script-update-20261009/start-model.sh.original（SHAfdf2e0379c95d6f1a3acea18381c4126ae529ad851323dc2c7edfba2dc3a879c），回执/diff/更新副本均在该外部目录。首次控制因候选脚本served-name被编辑成-opt1而在任何写入前停止，已证明只该名称差异且运行服务仍为MiniMax-M3.1；v2不覆盖用户候选脚本，根入口保留原API名。

手动CSV报告P4K/P16K/P32K各3轮SUCCESS、每轮128请求，CSV自带SUMMARY总吞吐分别4223.31/5392.64/5653.19token/s。这是用户手动结果的原样摘要，原生rawrun/预热与聚合策略/服务绑定/匹配anchor及revert未齐；P1K CSV缺失，不据此关闭正式四场景或计算已接受收益。文件SHA和各轮原始精度见state.yml。

按用户要求精简根目录start-model.sh环境：恢复原脚本全部11个export名及原值，PATH/LD_LIBRARY_PATH回到原动态写法，删除此前增加的SDK/CUDA/NCCL_DEBUG/NCCL_IB_DISABLE等显式变量；原blacklist也恢复conv3d,cudnn_convolution，因此未来根入口不再启用op002 cumsum_out exclusion。保留FULL_AND_PIECEWISE及14capture桶、8025/MiniMax-M3.1/nohup和固定Python/vLLM入口。新SHA4f4f218afa9c76f5f0e6b304401a31420320301fafa8c3fa04719d44a5280fb2；Host/优化容器bash -n通过、export列表与原备份逐行完全相同。修改前完整环境脚本保存在外部root-original-env-20261009/start-model.sh.before-env-restore（SHA91b2d8f309614b4d86ccc8f23a476b6268c524b0803f1ba3f30c25d55bf78c34），控制/回执/diff均已归档。未启动或重启服务，当前8035仍为原三项组合候选、精度gate身份不变；新根8025配置尚未运行/验收，不继承当前三项组合gate。自动优化继续暂停。
