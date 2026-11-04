# Qwen3.6-27B / MetaX Flash Attention 优化

[delivery-008](delivery-008-flaggems-vllm-editable.md)：已按用户要求统一为 `/workspace/FlagGems-vllm` 可编辑安装；实际导入为该目录的 `src/flaggems_vllm`，无需 PYTHONPATH。与 delivery007 的385个源码/配置文件完全一致，GDN FP32/Decode/FA 修复保留，11个公共 API 验证通过。原目录（含 Git 和未跟踪测试）及旧安装完整备份；依赖及其他三仓库不变，服务未重启。该安装方式取代下述 delivery007 的普通 wheel 安装。

[delivery-007](delivery-007-flaggems-vllm-main-update.md)：优化容器已安装官方 FlagGems-vllm main `de2298be`，保留5处原有 MetaX 修复，FP32 GDN 与原 FA 补丁逐字节不变。77项 Plugin CPU 接口及34项上游 CPU 测试、385文件和11公共 API 导入校验通过；无需 PYTHONPATH，原安装已备份。服务未重启，下次启动生效；没有新 GPU/graph/GPQA/性能验收。包版本标记仍为0.3.0.dev1，源码 SHA 为 cb45b31d。

[delivery-006](delivery-006-plugin020-metax-sync.md): optimization container checkout now clean on020plugin-opt-metax at[b8f2734](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/b8f2734beb80738ce5e4f7c61c2056f41e5c9ba5), final remote head matched.64new CPU MoE contracts and7public API imports passed. Existing editable install retained; no model restart/hot reload/GPQA/performance tests. On-disk PluginSHA98f36f07; prior source/Git backed up.

[delivery-005](delivery-005-plugin020-metax-publish.md): current14-file Plugin snapshot committed/pushed to [020plugin-opt-metax](https://github.com/ZenithJoyH/vllm-plugin-FL/tree/020plugin-opt-metax), commit[f99f9db](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/f99f9dbbb4db72ea3ba93aa53e19a48f1ad4f641). Remote head verified; source matches container exactly, reverted_ready_pid omitted. 51CPU/mocked tests/syntax/whitespace passed. No model restart, container reinstall, GPU/fullGPQA/performance rerun or PR created.

[delivery-004](delivery-004-manager-fast-init-revert.md): user requested rollback of unproven_ready_pid optimization. manager.py now equals020branch original; its feature test archived/removed, all other Python files unchanged. Original manager suite38passed. On-disk PluginSHA b46d8e1b; running service not restarted, so rollback takes effect on next startup.

[delivery-003](delivery-003-plugin020-base.md) completed: current Plugin base already equals requested020plugin-opt commit8b059122. Detached HEAD aligned to that branch with zenithjoyh upstream; all9local tracked patches/7untracked files, installed source and existing service retained. Source unchanged; no reinstall/restart, graph/accuracy/performance rerun or new gain claim.

[diag-011](diag-011-startup-attention-cache-collision.md): user startup failed during native Attention decode graph capture (12 expected heads versus2 returned). Current whitelist has20 entries without attention_backend; the used compiled graph matches old FG cache and shares identical key factors with incompatible native graph. Read-only diagnosis; no cache cleanup/script patch/restart. Fresh-cache startup recovery not yet verified.

[delivery-002](delivery-002-install-no-pythonpath.md) completed: retained FP32 FlagGems-vllm wheel installed in the optimization container private site-packages; script PYTHONPATH removed, existing Plugin installation preserved. Imports without PYTHONPATH,378 exact source/config files and unchanged dependency versions verified. Other user script edits preserved; no model started or evaluated.

启动脚本已按用户要求简化为22行，仅保留必要环境变量、全21项FG及服务参数；去掉wrapper/hash检查/--check/profiler。需在 `qwen36-27b-fa-opt-20261012` 容器内直接运行，GPU2、3/18002/FP32版本不变；语法检查通过，未启动服务。详见[交付记录](delivery-001-retained-fp32-launch-script.md)。

2026-10-15 启动脚本已交付：[delivery-001](delivery-001-retained-fp32-launch-script.md)。已备份并更新 `/public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh`，默认优化容器/GPU2、3/18002/全21项FG/保留FP326ea；语法与宿主机、容器内 `--check` 均通过，本次未启动或重启模型。最新只读发现原756537已退出、优化容器内无模型服务，以下已完成实验的实例/gate为历史证据；后续启动需重新绑定。

当前[OP010 FP32热点优化](op-010-gdn-prefill-fp32-hotspot-optimization.md)三角色/三阶段已完成并验真：87轮/27measured/9408请求0失败。candidate Prefill吞吐+2.361%、meanTTFT−2.333%；Decode吞吐+0.648%、meanTPOT−0.198%、P99ITL+1.720%。Mixed名义吞吐+18.489%，但相同原FP32回退也+16.705%，baseline测量spread26.781%>10%，不能据此确认E2E收益。PrefillmeanTTFT回退漂移1.010247%、DecodeP99ITL2.415935%超冻结1%；三份原生比较均incomplete，候选不晋级。原FP32 6ea/full21/原容差/current756537已恢复并native166/198 gate重绑定/check通过，监控PAUSED；全部慢轮/旧失败/补丁保留，不追加测试。

当前任务已完成：[GDN FP32完整GPQA前后对照](diag-010-gdn-prefill-fp32-full-gpqa.md)。修复前162/198=81.82%，修复后166/198=83.84%，均通过80%；观察到+4题/+2.02个百分点（11错变对、7对变错），50000token截断5→3。完整21项FlagGems保持开启，当前OP0076ea/实例583672精度gate已绑定，监控PAUSED。单轮T1/C32差值不能全部因果归于FP32，PR925整理版源码不同，四场景性能仍未验收。

当前进展（2026-10-14）：[OP009 FP32性能代价](op-009-gdn-prefill-fp32-performance-cost.md)已完成既定三阶段与回退测试、恢复原FP32源码，全部21项FlagGems持续开启。Prefill在P1024/D1/C64/N128下吞吐下降8.30%、meanTTFT增加9.00%，回退漂移<1%，是可归因成本；Decode候选未稳态、Mixed基线未稳态且回退测量有50.7%吞吐散差，因此整体incomplete。全部异常轮保留，正式GPQA/四场景不验收。

此前：[OP008公开PR](op-008-gdn-prefill-precision-pr.md)完成，已将[Issue923](https://github.com/flagos-ai/FlagGems-vllm/issues/923)更新为BF16中间舍入导致GDN prefill最终状态超容差，并创建关联[Draft PR925](https://github.com/flagos-ai/FlagGems-vllm/pull/925)。仅发布MetaX精度修复与合成回归三个文件；上游复现7870个状态元素超限，最终提交11项测试、原9矩阵/18改变输入graph均通过，原.002/.02容差不变。性能代价、backward与其他平台未验证，正式GPQA/E2E未验收。

[OP007最终状态精度修复](op-007-gdn-prefill-state-precision.md)仍作为当前模型源码，原点误差.002556→5.4e-8；OP009结束时曾恢复同源526267实例；当前保留diag010评测后的583672/18002/GPU2、3，完整21项白名单含gdn_prefill，双rank graph/precisionWY、freshC8以及166/198正式gate通过。公开PR的独立scratch代码未替换运行目录，源8002未操作。

历史当前进展（2026-10-14）：[OP006 V-major纠错验证](op-006-gdn-prefill-vmajor-correction.md)终态failed/prefill-not-enabled，FG19已恢复运行。修正消除历史转置失败；完整7GPU矩阵6数值通过/1finalstate元素超原容差，14graph回放均通过。去掉空段后同一state差异逐位不变，具体BF16组块误差步骤未定位；未新增gdn_prefill。当前319960/18002/GPU2、3双rankgraph与同源C8绑定验真完成，源8002不变，全量精度/E2E门禁未解除。

2026-10-14更正prefill失败归因：实际MetaX导出已为V-major，此前generic式转置是接入错误；上游数值缺陷尚未证实。已发布[#923](https://github.com/flagos-ai/FlagGems-vllm/issues/923)请求明确状态ABI及增加校验/测试；仅引用公开源码。当前decode服务及白名单未变，prefill正确布局复测待完成。

历史attention黑名单原生black03在50000输出预算下为158/198＝79.80%，低于80%；该失败按原来源/契约保留，不覆盖当前OP007全21项FG的166/198达标结果。[diag-008固定seed/C1诊断](diag-008-c1-fixed-seed-regression.md)已完成：3题各3次均正确，完整token序列及全部返回logprobs一致；批执行差异的数值/RNG来源仍未定位。

历史30000修正版完整精度已通过：已确认GPQA预处理删除科学方括号，损坏12题选项、一题gold因字符串碰撞从C误设为A。该题两次同服务同seed原/修复对照均错误B→正确C。用户明确批准修复任务后完整198重测，FlagGems候选159/198＝80.30%，gate已签发并核验通过。

| 全量GPQA | strict | 唯一题数 | 状态 |
|---|---:|---:|---|
| 旧任务／原路径 | 156/198＝78.79% | 198 | 低于80%；原结果保留；任务存在科学文本预处理缺陷 |
| 旧任务／候选02 | 153/198＝77.27% | 198 | 低于80%；原结果保留；不能把3题差异直接归因补丁 |
| 修正版任务／同候选04 | 159/198＝80.30% | 198 | 历史passed；原gate保留，当前实例已停止 |
| 修正版任务／attention_backend黑名单／30000 | 160/198＝80.81% | 198 | 历史passed；black03在此契约下gate通过，净增1题 |
| 修正版任务／同原生black03／50000 | 158/198＝79.80% | 198 | failed；低于80%，没有新gate |

修复范围：独立规定镜像评测容器中，仅去掉helper删除科学方括号的regex。原始198题、strict-match、阈值80%、C32、temperature1/top_p.95/top_k20/cap30000、harness42/API1234均不变；另存新provenance，旧容器/结果保留。全部22个权重/tokenizer文件重验通过；候选04的源码、权重、设备、启动参数与旧候选02相等，两rankgraph和SplitKV命中确认。

源服务8002和源容器保留；只操作独立优化容器的2/3卡、18002服务。监控`qwen36-metax-flash-attention-op001`已在终态验真、gate签发/check通过后PAUSED。性能验证尚未启动。

| 实验 | 变量 | 已有证据 | 决定 |
|---|---|---|---|
| [op-001-metax-gqa-decode-scheduler](op-001-metax-gqa-decode-scheduler.md) | MetaX packed GQA6 SplitKV及partial独立strides | 主78项与长KV8项通过；真实2rank命中 | 私有候选04历史精度已通过；black03原生backend精度对比160/198通过，未部署源服务 |

| 完整算子调用 / B64 | baseline ms | candidate ms | revert ms | 加速 |
|---|---:|---:|---:|---:|
| KV1024 | 1.143482 | 0.307776 | 1.143277 | 3.715× |
| KV4096 | 4.450733 | 0.931104 | 4.454560 | 4.780× |
| KV16384 | 17.701721 | 3.413011 | 17.707584 | 5.187× |

算子契约：BF16 Q12/KV2/D256、page784、maxK参数262144、完整graph API调用含copy/partial/merge、5组交错×40回放、差≤0.0009765625。仅算子收益，端到端收益未知；正式四场景均未完成。

精度审计：原路径14题到30000cap，其中11题strict错；候选18题cap全部strict错。未发现非截断missing strict match或明显正确final tail被误拒，采样与模型原生generation_config相等。输出cap是已观测症状，未证实这些题延长预算便能答对，不删题或修改分数。doc171最小复现完成；doc81原prompt错，修复对照未完成，保留5/8计划请求证据和取消控制记录。

附加非目标算子失败如实保留：M4/D256强制split编译断言原版复现；已有M16矩阵30通过/6项FP32容差失败，9组代表性原/候选bitwise相等；默认fallback探针incomplete。不改写成全部通过。

rev-001复盘：先取得可信修正版正式gate；若失败，继续backend单变量数值定位；若通过，再验证P1K稳态baseline/candidate/revert和跨阶段守护，最终四场景验收仍需全部原矩阵。暂缓更多tile和冷启动方案。

全部配置、补丁、日志、样本、trace、请求响应和SHA均在`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention`及本目录state.yml索引。新正式进程回执`manifests/gpqa-corrected-op001-process.json`，结果目录`results/gpqa-corrected-op001`。旧正式分数按旧预处理契约保留。侧边任务的Draft PR发布记录另见案例目录，不代表当前模型验收通过。

终态结论：修正版159/198通过80%（超时0/拒绝0），完整样本和来源已验证，当时exactsource/instance匹配；candidate04已停止，历史gate不绑定black03。gate位于`results/gpqa-corrected-op001-accuracy-gate.json`，SHA2566bc8ef313c735d4f7e41581dc4f69778f03845480ad8ba813bdd263be9f8cf98。12个改变prompt的题旧4对/新5对；186个未改变prompt中9题由错变对、4题由对变错，故总+6题不能全部归因预处理。39道剩余错误未全部定位。旧分数保留；本轮只完成精度，不开展性能、不修改服务。

用户追加[diag-005-attention-blacklist](diag-005-attention-blacklist.md)已完成：等价complement blacklist仅关闭attention_backend，其余注册/源码/权重/采样不变。原生MetaX两rankkernel、graph190/rank与C8通过；独立compile cache解决旧缓存attention接口签名碰撞，未保留源码语义补丁。完整修正版160/198＝80.81%，较159/198多1题、+0.51个百分点；149双方正确、11仅黑名单正确、10仅旧候选正确、28双方错误，同198题/gold/arguments逐项相等。单轮temperature1/C32差异不证明FlagGems导致精度偏低，本轮未显示明显整体精度提升。

终态验证在`results/gpqa-attention-blacklist-terminal-validation.json`（SHA c9d47036d60d387b79f370081e92894bd75aae653ec62129427578ed8ae53ec2）；当前black03新gate `results/gpqa-attention-blacklist-accuracy-gate.json`（SHA db81877b5787e8d5c5177cc7b685e02fc5f96f1375b69d103cc3a345deb3c081）issue/check passed。超时0、完整198唯一题/两filter396行与来源验真；14个length仅作健康观察，不删题、不换分母。监控已PAUSED，服务保留、源服务未改、性能未开展。

用户追加[diag-006共同28题定位](diag-006-common-wrong-truncation-config.md)：离线审计8双方触顶、3单方触顶、17正常final错误；完整两轮各14条length且精确30000。输入/上下文、采样/seed/Thinking、gold映射及strict提取已核验，未发现正确final被错提取；doc17/106题意或标注疑点、126重复错误选项记录但不改分。两道30000vs81920/C4同采样token-prefix配对诊断已按用户新指令停止，保留两条30000触顶响应，长预算未完成，旧198分数/gate保留，监控ACTIVE；不开展性能。

用户批准的[diag007原生50000完整GPQA](diag-007-native-cap50000-full-gpqa.md)已结束并验真：158/198＝79.80%，低于冻结80%，较原生30000的160/198少2题、-1.01个百分点，未签发新gate；旧30000通过结果/gate保留。完整198唯一题/两filter396行、onlyoutputcap变化、same source/instance均核验，运行异常/超时0。

50000使length14→5（32/36/69/90/145，全错），原14触顶题10本轮正常结束、5本轮答对。3道新对题输出超过30000（27/45/71），2道不到30000（64/180）；新旧前缀均早期分叉，不能将所有得失严格归因预算。全题149双方对、9新对、11旧对、29双方错。减少截断未带来整体分数提升，当前50000范围失败需继续精度定位后再恢复性能；监控已PAUSED，服务及源8002未改，不自动重评/降预算/改指标。

rev-002复盘已归档到state.yml：累计E2E仍未知，op001micro在当前原生backend不生效。下一步规划优先同seed固定输入的批轨迹/稳定性证伪，然后定位持续错误的共享路径/独立reference，最后同契约正式验证；本次监控不启动新的请求或性能测试。

User-authorized follow-up: [diag-008 C1 fixed-seed regression](diag-008-c1-fixed-seed-regression.md), IDs21/93/129 x3 sequential requests, same native model instance/cap50000. Completed and validated; no new formal gate or performance traffic.

Diag-008 checkpoint (2026-10-13 04:56 UTC):4/9 complete; first21/93/129 C1 responses all correct. ID21 two repeats have identical3332 token IDs and all returned logprobs. ID93 repeat2 running; source unchanged at launch, terminal identity verification still pending. No formal score or batch-numeric causal conclusion from this partial probe.

[diag-008固定seed/C1终态](diag-008-c1-fixed-seed-regression.md)：21/93/129各3次均答B且正确，分别3332/39570/5061 token；每题3次完整token IDs和全部返回的采样token/Top5 logprobs完全相同，首分叉不存在。736次运行指标检查仅1请求在运行、0排队、0混入，全部stop、超时/异常0；终态same source/exactinstance再验通过。历史C32/50000三题均答A，本轮观测开关也有变化，故只能确认这3题C1稳定，不能断言批调度/RNG已确诊或排除批形状数值差异。正式50000失败未解除，不修改服务/源码、不补跑请求或性能；监控终态PAUSED。验真SHA `04069fc329e475c0c5f5d0307577aba14bef5261fd64b249fee6f085de1e8c04`，全部原始证据保留远端。

User resumed FlagGems performance2026-10-13: [diag-009 P1K phase baseline](diag-009-flaggems-p1k-performance.md), bounded diagnostic exception while50000 fullscore remains failed. Restore retainedOP001, then phase metrics and currenttrace; no formal acceptance from exception. rev003 recorded in state.yml.

当前FG性能恢复（diag009）：source不变、2rank实际SplitKV/graph及C8通过。已取得单实例PrefillP1K/D1/C64/N128 baseline input6115.7tok/s、P99TTFT轮中位10.914s；DecodeP1K/D512/C64/N64 output930.7tok/s、平均TPOT56.138ms（含初始prefill/调度残余）。MixedD256三轮预热未达10%稳态门槛，保留incomplete并按预冻结6warmup末3检查恢复。尚无candidate/revert或E2E收益结论；client私有薄CLI调用未改的安装版vllm benchmark，原服务/sourceCLI不改，当前模型仍FG。正式50000精度失败历史及身份记录缺口保留，用户本轮仅放行有界诊断性能。

[OP002：Packed Decode Split-KV 策略](op-002-packed-decode-split-policy.md) 正在独立进程比较拆分数；当前服务保留OP001，尚无新端到端收益。三阶段基线和双ranktrace已完成，FA占Decode kernel活动约11.9%。


rev005终态：OP002少拆分及OP003 tile32负结果保留，组合不晋级。九记录/60轮证据完成重验，终态SHA `e0dcdfc4341703a614ba1f4e9e0a4f8afcf4c88470e9ae2beec53ad47ea12b48`。比较配置缺口及Mixed失败不自动追加实验；后续路径见state.yml规划。原页784微测不能当真实页16服务收益。

用户重新请求端到端优化：[Framework001](framework-001-prefill-token-budget.md)已冻结一个8192→4096批处理预算实验，使用同契约三阶段/回退对照；指标声明缺口在新计划中补齐，不修改旧结果。诊断范围，正式精度失败/四场景未验收保留。

本轮硬约束：始终保留当前全部已开启FlagGems算子（包括attention_backend），不通过关闭或黑名单获得性能；允许优化FlagGems算子实现及其执行开销。

Framework001 checkpoint（22:56北京时间）：4096候选graph/C8与FlagGems保持开启核验通过；Prefill吞吐−4.33%、Decode−2.42%，Decode P99ITL50.4→743.6ms超守护。Mixed及回退对照仍运行，最终决定待原生终态与漂移验证；不追加实验。

rev007：九阶段结果及全部轮保留，原生比较与漂移以state.yml为准。未通过关闭FG获得收益；配置负结果已归档，下一轮需证明现有FG热点的完整调用成本，不自动新增实验。

2026-10-14继续[OP004](op-004-metax-packed-gqa-query-tile.md)：保持FG完整开启，刷新热点后尝试packed GQA6查询tile，编译/数值/真实命中先证伪，合格后再三阶段及回退。尚无收益结论。

OP009阶段记录：基线Prefill3测量轮原生重验通过，总token吞吐中位6183.139 tok/s，meanTTFT8285.204 ms，每轮128成功/0失败；Decode进行中，FP32及回退数据未齐，不作性能代价结论。

OP009当前：基线Decode3measured输出中位930.070tok/s、TPOT56.573ms；Mixed末3预热散差11.10%超10%，6warm/0measured，不能比较Mixed性能代价。按冻结对照继续FP32候选/回退，失败轮保留。

OP009最终三阶段（相同P1024，稳态测量轮中位数；破折号表示缺测）：

| phase / D/C/N | baseline | FP32候选 | revert | 结论 |
|---|---:|---:|---:|---|
| Prefill 1/64/128 总tok/s | 6183.139 | 5669.920 | 6233.579 | −8.30%；meanTTFT+9.00%，回退漂移<1% |
| Decode 512/64/64 输出tok/s | 930.070 | — | 934.948 | 候选warmspread21.90%，incomplete |
| Mixed 256/64/128 输出tok/s | — | 670.433 | 712.453* | baselinewarmspread11.10%；revert测量spread50.73%，incomplete |

*Mixed回退异常测量351.367tok/s、meanTTFT27.440s全量保留，中位不能掩盖。FP32原数值回归仍通过；保留正确FP32，下一步需先定位测量长尾，再优化FP32链。源码/实例/36warm+21measured及证据SHA在OP009/state；没有用历史微测数字相加成累计收益。

历史实验索引补充：[OP003](op-003-packed-decode-kv-tile.md)、[组合001](combo-001-fa-splits-warps.md)、[OP005](op-005-gdn-latest-routing.md)。rev008记录测量有效性与后续单变量方向，不追加GPU请求。

2026-10-15 OP010已恢复：/public-flash可用22–25TiB，严格numeric/graph-first，全21FG和.002/.02容差不变。r1原9case/18changedgraph通过，但N8完整调用仅+1.84%未达5%门槛，拒绝安装并恢复原FP32/graph/C8/native166gate。r2仅改变WY输出列tile执行顺序，原9/18再次通过，三组完整调用输出/state与原版bitwise相等；N8完整GDN微基准4.961647→4.278562ms（耗时−13.77%），微测baseline/revert漂移+3.85%保留。唯一r2controller786469/1792030166.5继续新三角色三阶段和原FP32回退；E2E收益待定，原1%模型对照漂移门槛不变。旧ENOSPC/部分Prefill保留，不混入新比较。30min只读监控已绑定r2，终态停用。
