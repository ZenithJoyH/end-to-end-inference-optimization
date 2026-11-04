# OP010：GDN prefill FP32热点定位与性能优化

状态：已完成R2既定三角色/三阶段及原生验真，三份性能比较均incomplete，候选未晋级；原FP32/full21/原容差已回退且166/198 gate同源重绑定通过，监控PAUSED。

<!-- op010-r2-final-start -->
## R2终态：全部对照完成，未晋级，原FP32已回退

证据截止：2026-10-15T12:02:13+08:00。9份run-record全部原生重验通过，3份比较结果与只读重算完全相等。共87轮（60warm/27measured）、9408个性能请求、0失败；三角色各自graph/两rank实际kernel和fresh10doc/C8/20filter证据SHA已核验。全部轮保留，没有以warmup替代实测、删除慢轮或放宽门槛。

| 缩减阶段 | baseline tok/s | candidate tok/s | revert tok/s | 候选相对baseline | 原版回退相对baseline | 原生结论 |
|---|---:|---:|---:|---:|---:|---|
| Prefill P1024/D1/C64/N128 | 5636.350 | 5769.415 | 5584.052 | +2.361% | -0.928% | incomplete |
| Decode P1024/D512/C64/N64 | 896.414 | 902.227 | 890.815 | +0.648% | -0.625% | incomplete |
| Mixed P1024/D256/C64/N128 | 572.813 | 678.723 | 668.501 | +18.489% | +16.705% | incomplete |

Prefill使用总token吞吐；Decode/Mixed使用输出token吞吐。全为每进程三轮中位数，不是总体请求P99或持续容量。Mixed名义+18.489%不能视为真实端到端增益：相同原FP32回退也提高16.705%，原baseline的measured吞吐spread26.781%、meanTTFT34.690%、TPOT21.537%、P99E2EL36.059%超过冻结10%；原始慢轮全部保留。candidate吞吐spread7.820%、revert0.605%不修复已失稳baseline的归因缺口，不将revert事后替换为有利新baseline。

| 阶段/客户端延迟(ms) | baseline | candidate | revert | 候选变化(负值改善) | 原版回退变化 |
|---|---:|---:|---:|---:|---:|
| prefill/mean_ttft_ms | 9085.535 | 8873.544 | 9177.321 | -2.333% | +1.010% |
| prefill/p99_ttft_ms | 11853.527 | 11574.128 | 11971.474 | -2.357% | +0.995% |
| prefill/p99_e2el_ms | 11853.527 | 11574.127 | 11971.473 | -2.357% | +0.995% |
| decode/mean_ttft_ms | 6963.169 | 6787.687 | 7018.273 | -2.520% | +0.791% |
| decode/mean_tpot_ms | 57.648 | 57.534 | 58.001 | -0.198% | +0.613% |
| decode/p99_itl_ms | 50.902 | 51.778 | 52.132 | +1.720% | +2.416% |
| decode/p99_e2el_ms | 36537.258 | 36303.311 | 36768.760 | -0.640% | +0.634% |
| mixed/mean_ttft_ms | 8914.044 | 5762.546 | 5962.209 | -35.354% | -33.114% |
| mixed/mean_tpot_ms | 76.934 | 71.798 | 72.485 | -6.676% | -5.783% |
| mixed/p99_itl_ms | 1519.548 | 1469.096 | 1523.967 | -3.320% | +0.291% |
| mixed/p99_e2el_ms | 38065.898 | 30365.156 | 30936.623 | -20.230% | -18.729% |

Prefill主指标+2.3608%未达到冻结3%；meanTTFT回退漂移1.010247%略超1%，不四舍五入改判。Decode P99ITL回退漂移2.415935%也超1%；candidate P99ITL+1.7198%仍在5%守护内。Mixed回退meanTTFT变化−33.114%、P99E2EL−18.729%、TPOT−5.783%，均体现相同原代码下的时间/执行上下文差异，根因尚未定位，不能单因果归于候选数值。三阶段原生状态均incomplete，区分数据完整与可比较性；本周期没有正式四场景或稳定E2E收益声明。

正确性保持原atol=.002/rtol=.02、FP32/IEEE中间链和V-major state：原9矩阵/18changed-input graph通过，三组complete micro输出/state bitwise相等。N8P1K complete微测4.961647→4.278562ms(−13.7673%)仅是局部增量。实际candidate两rank各96tiledWY/0originalWY、190graph；tile32/4warps实际block256threads、92regs/thread、24576Bshared，原版256regs/thread/49152Bshared。资源/微测改善不等于模型端同幅收益，也不证明spill或其他硬件/shape通过。

当前保持`qwen36-fa-opt:756537:1792034481.9`，优化容器18002/GPU2、3，full21+attention1/no blacklist/prefixoff/TP2BF16/8192/graph64；4repo原源码恢复，其中FG-vLLM为6ea79405，WY文件bf41e820。candidate b7a33aa（WY文件1c72a70a）已停止/撤回，命令与原件保留，不自动重装、不提交推送或更新PR。

原198题/50000/80%正式166/198分数同源native rebind/check通过，属既有已测score复用，非重新评测；新candidate没有该正式gate。当前service SHA `656b2feb83ed33bd68a733548a49acc6b0eb74263cb0cca0eb0eaa0ce4e255cf`、runtime SHA `09d57c9aeaf01886fb8cb4d48a8a095686599eac1a8af8d80c21f4f8c0d06ee6`、gate SHA `1470dc49a4190d9cc6732d416f6871955115782b92a166db865a4b56db0ef8fa`；请求running/waiting=0/0。源8002/其他GPU任务/共享代码/vLLM/权重/tokenizer未操作。本周期30min只读监控已PAUSED，无后续自动测试。

终态 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op010r2-terminal-control-receipt.json` SHA `c9309cd378547a2b45c3cd29868eacdbff9a8766a0824c6b984a8fe5af0d6724`。

- prefill: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op010r2-prefill-comparison-result.json` SHA `7eedf4313f7a0c91d033ed75c3ca4d83b37711aecb132bc85edfa50ffcf205c1`。
- decode: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op010r2-decode-comparison-result.json` SHA `5cdeed4fd4e1466b204efb6bd797a962f6c9964f2f001ad3525ce434c8f3e37a`。
- mixed: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/op010r2-mixed-comparison-result.json` SHA `42155b62d770b5ba6104d442f5e86af4728cec46e817ff658d26a9e1718c9edf`。

规划复盘rev-009已写state：先在原FP32上定位Mixed慢/快轮的完整batch/CPU/GPU执行差异，再建立有效同配置基线；后续才评估FP32H/O访存/融合。这里只记录候选方向，未启动新实验。不能把OP009成本、OP010微测和模型阶段百分比相加；当前保留组合仍为入口原FP32，累计E2E收益未建立。
<!-- op010-r2-final-end -->


入口：mx-59、独立优化容器qwen36-27b-fa-opt-20261012、18002/2、3卡，模型583672/create1791970287.66，源6ea79405，diag010完整198题166/198、strict80% gate已绑定。源8002、其他GPU任务、共享目录、vLLM、权重/tokenizer不改。这是原案例继续优化点，复用已核验的独立容器；不是新模型/新Host任务。挂载按规范化目录项比较，不按Docker列表次序。

首先capture→analyze：Prefill P1024/D2/C64/N128、Decode P1024/D256/C64/N64、Mixed P1024/D128/C64/N128，各3轮/2warm，最后一轮profile，T0/ignoreEOS/seed42。完整FG图模型请求，不以单个32token smoke代表目标负载；按GPU事件/shape与GDN prefill专属kernel分离KKT-inverse/WY/H/O/转换，同kernel跨阶段不能直接合并归因。Profiler-on值只用于热点诊断，不能报收益。

后续无profiler targeted三阶段冻结：Prefill P1024/D1/C64/N128、Decode P1024/D512/C64/N64、Mixed P1024/D256/C64/N128，warm6/6/8，固定末3准入≤10%，测量3轮，全部轮保留。预先候选选择阈值：Prefill吞吐≥3%改善，Mixed吞吐不退化、延迟守护≤5%，测量spread≤10%、baseline/revert漂移≤1%；失败/未稳态使用failed/incomplete，不删慢轮或补warmup。各角色同计划/client/seed；这里只服务最终P1K目标milestone，不等于四场景验收。

改动层：目标MetaX FlagGems-vllm私有实现，只选择一个热点及真实shape相关tile/warp或FP32数据流改动，保持FP32/IEEE、BF16输入/输出与FP32 Vmajor最终状态及原参考/容差；不降低精度，不关闭算子，不按模型路径特化。先原9矩阵/18changed-input graph、边界/慢衰减/非零state/noncontiguous回归，失败立即拒绝；graph服务双rank实际命中/两replay+C8后比较baseline→candidate→原FP32revert。若数值语义/累积顺序改变按高风险补正式198/50000/80%，旧gate不绑定新源码。

所有可执行命令先保存到 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/`，trace/raw结果/patch/SHAs外置，实验记录持续写回本文件和state/README。最终保持原FP32回退，未达到稳态/数值或真实收益时不自动保留候选。不提交推送或更新PR925。

已保存profile控制器 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op010-profile-controller.py` SHA `6ba66f80d442e51df8eb7ce8c212dbd40c5912084cbd5dc91e25dccdc3540f14`；launch SHA `d0feab3121594811730746b0133acfa401f18bbc718e1637efe7175ca6082cb6`。执行前精确核验空闲服务、4repo内容、规范化挂载、image以及原生gate check；三阶段按dry-run→真实profile顺序，只更改本案例trace/log产物。

Profiling v1在dry-run阶段失败，0模型请求/0服务变更；远端旧工具不支持显式temperature但内置benchmark为T0。v2仅移除冗余CLI参数，使用全新commands/process/progress/profile/log名称；失败证据保留，不属于候选性能或数值失败。v2controller SHA `527acd787cc002d476a661e1297e5d574357d0f43b8dcd00b9b505a6b981bc08`。

Prefill实际两rank GPU活动worksum：H6.14–6.33%、WY5.39%、O3.46–3.48%、KKT1.16–1.17%。WY256registers/thread/49152Bshared/13%estoccupancy，H126registers/10240B；选择单一WY输出列并行tile32，BT64归约/FP32 RHS/IEEE不变，能力guardBF16K=V128/BT64，其他shape走原正确FG路径。暂仅保存在commands独立候选；live模型源未改。Profile-onworksum不是criticalpath或收益；等待完整三阶段capture结束后串行原9/18容差与graph micro，拒绝数值失败/无实际收益候选。

第一离线probe第一组first-call数值通过后>600s无任何graph检查更新，无编译子进程，精确取消622073，parent622067按非零退出停止未启动micro；原JSON/日志保留，incomplete而非数值失败。V2同9矩阵/18replays/seed/原reference/.002/.02，增加sidewarm/capture日志与60sfaulthandler并将CPU参考线程限1，300s有界；候选文件/数学/活跃模型源码不变。

V2同矩阵在torch.cuda.Stream.__new__等待，尚未进入候选graph；300s超时仅取消ownchild622629。停止本case原583672/出生1791970287.66（要求idle/精确cmd/GPU2、3/四repo一致），在free ownGPUs串行V3同9/18与micro作隔离，然后不论数值probe返回成功/失败都启动新op010-baseline-01原FP32并graph+C8。源代码不改；初始gate在重启后必须native rebind，不按旧实例直接复用。停止与恢复所有命令已冻结记录；源8002及其他GPU不操作。

原FP32已恢复op010-baseline-01：622683/create1791988313.03，source6ea unchanged，新双rank190graph/96precisionWY及fresh10doc/20filter C8通过。native166/198 gate rebind/check passed，reused score而非新精度测量；serviceSHAc4c6a827、runtimeSHA3d5202e1、rebindgateSHA c3c8b0e9e2b204f3b30f411e7e06e1911ee653235f6a6575f56bd4ef2cbe85e4，原初snapshot保留。V3隔离探针在PIDexists断言前退出0GPU调用；旧583672为退出未回收的PID，v4正确检查no live served model/port（排除zombie），失败header/日志保留。

完整无profiler周期已冻结且仅一个controller：先原FP32 baseline三phase，精确停baseline，v4在freeGPU2串行原9/18+.002/.02+5组30graph交错micro；只有N8P1K完整调用≥5%改善、其他representative shape不退化>5%、全部numerical/graph通过才应用唯一私有WY文件、启动candidategraph/C8并测三phase。无数值/微测晋级时不安装候选，仍启动原FP32revert测三phase。最终必恢复原6ea、graph/C8/native166原gate rebind、原生三phasecompare，保持原FP32运行。不用warmup补measurement，不删慢轮，不放宽steady/drift规则。

Profile分析回执results/op010-fp32-hotspot-analysis.json SHAeff243f1：PrefillWY5.39%/H6.1–6.3%/O3.46–3.48%/inverse1.16%GPU活动worksum。Decode/Mixed各WY~4.8%仅对应max64初始步骤的窗口，包含Prefill，不能冒充完整或纯Decode分布；GPU活动时长可能重叠，不是criticalpath，最终收益仅由无profiler三phase+revert决定。主要总工作仍为GEMM/TP通信，局部WY优化有有限E2E上限。

## 当前中断：共享存储ENOSPC

控制器531816/create1791989431.4在baselineDecode启动后原生工具保存输入/状态时遇到errno28 No space left on device，日志同时确认错误handler写进度也失败，results/op010-e2e-progress.json被截断0字节。该文件不是有效running/terminal证据；只读从退出PID、完整错误日志和已存runrecords核对终态，不修写空文件或掩盖失败。df显示共享/public-flash350T全部已用、查询时仅1.3G可用，正在增长的其他写入未归因，本任务不扫描/清理无关目录。

有效原FP32 Prefill基线：P1024/D1/C64/N128、6warm+3measured，nativecheck_run passed；total throughput三轮5659.601748/5662.139330/5662.656019tok/s，中位5662.139330；meanTTFT9048.350769/9043.004143/9043.120319ms，中位9043.120319；P99TTFT中位11797.451910ms，吞吐spread0.053942%。每轮128成功/0失败/131072输入/128输出；recordSHA fd07402618abb076d56c66218265a20f93534cfbe622667d5e6c9ef9393a8991，全部轮保留。这是原FP32基线，不是优化收益。

Decode recordSHA7c2a764033d0c37fea0432f09a23d147b518f55ad89216344cca032bf1b91046，statusfailed、errno28、0轮。Mixed、v4隔离probe、完整micro、模型candidate与revert测量都未执行。候选只保存在commands，原容差/9/18未取得完整通过，未修改模型的gdn_wy.py，不能宣称加速或优化完成。

原FP32 current622683/create1791988313.03、source6ea、全21FG/attention1/无blacklist仍匹配，模型running/waiting0/0；现有166/198 schema4rebind/check仍有效，原源码未改无需再次回退。此前隔离恢复步骤后模型已回到正确FP32并graph/C8通过；本次e2e在第一角色未到stop就终止。source8002、其他GPU、共享源码/vLLM/权重/tokenizer不动。

监控已按失败终态PAUSED。已向用户请求mx-59上有空间的新产物目录，或释放/public-flash后继续原目录；未清理共享数据、不盲目重评。恢复时先核对身份/空间/旧请求是否结束，保存新唯一命令和结果位置，原失败/部分基线保持不覆盖。原实验目标仍待完成。

## 2026-10-15恢复r1

用户要求重新检查/public-flash并在空间足够时继续，先数值/graph再三阶段/回退，全21和原atol.002/rtol.02不变。两次只读available约21.68/24.74TiB；当前622683/1791988313.03原FP32源6ea、全21/attention1、idle0/0及规范化mountparity/image再次匹配。原失败与Prefill部分基线保留不混入新对照；r1先停本案例精确实例，在空闲GPU2串行v4原9case/18changedreplay及完整GDN微测，达冻结门槛后建立全新baseline/candidate/revert三phase。每stage20GiB空间护栏、主progress原子保存；终态保持原FP32并native166/198rebind。执行命令及SHA已写state.resume_r1，不提交推送。

2026-10-15 02:31 UTC监控新增有效结果：r2原FP32 Prefill的6warm/3measured完整保存，run-record SHA `b143bb4753fc30e4de86f0b5e213fb96415aafb6e5090c125209efa8c28778ab`。全部9轮原始/validation/output JSON及计划/契约/client/service SHA只读核对，每轮128成功/0失败/131072输入/128输出token；warm末3spread0.24015%通过。三次measured总token吞吐5634.799542/5636.349979/5636.926650tok/s，中位5636.349979、spread0.037739%；meanTTFT9085.534649/9086.092393/9084.125379ms，中位9085.534649；P99TTFT中位11853.526981ms。这里只是同周期原FP32基线，不是候选收益。Decode已完成6warm+1measured，各64成功/0失败/65536输入/32768输出token，仍在测量，尚无其终态record。当前controller精确PID/出生/SHA匹配、原665551/source6ea/full21+attention1/no blacklist及其他3repo内容相等；空间约26.99TiB。candidate/revert与终态回执尚无，继续只读监控，不追加请求/脚本/服务变更。

R1隔离v4完整通过：9case/18changed-input graph回放均output/state exceed0，保持原atol.002/rtol.02。saved异常元素误差5.40167e-8；原矩阵含边界、空段、零/非零/非连续state、慢衰减。numericresultSHA931cf192ea50b2a7a53140e86f7cf65eb827e4561b559d483c131e9879be66f0，原候选2a4a67dd，离线进程637274/1792029565.41。Stream等待在本次空闲GPU隔离后消失，不能据此断言driver底层根因。接下来完整GDN graph微基准与冻结晋级判断；尚无E2E收益。

R1微基准完成且数值均bitwise一致：N8P1K WY1.494025→.921105ms(-38.35%)，完整GDN4.654583→4.568883ms(-1.8412%)，revert4.790554ms（完整调用baseline/revert+2.92%）。完整调用未达到冻结5%门槛，拒绝安装，不采集此候选模型性能；局部收益不能冒充E2E。准备同一OP010的r2调度revision：输出列tile在gridx紧邻再推进chunk，降低A/输出访问间隔；只改CTA顺序，原FP32/IEEE/BT64及能力guard不变。候选SHA1c72a70a5b82f3ea60346dad32fe1a5efd79a3d0fdc22724cd97be59577b8577，重新相同9/18数值与graph、micro完整调用，原5%及三phase阈值不放宽。r2只有r1恢复graph/C8/native166gate并终态后才允许执行，命令与SHA预存state。

R2数值9case/18changedgraph均通过，numericSHA9f5be89dc1159c5df36fbb0fcf82efb6b1ea669e482ecf0170d9f6f28e099279；完整微测三shape结果SHA08ba80791fa216f3e70e95d3e7b8e392d045ff386f8c7406aa1c74b71e265935。N8 WY1.494707→.842453ms（-43.64%），完整GDN4.961647→4.278562ms（-13.7673%），revert5.152725ms（相对baseline+3.85%微测漂移，不能视为E2E稳定性）。P1完整-22.42%、ragged-19.17%，均未退化，通过原5%完整调用晋级；这不是端到端收益。原新baseline665551/1792030306.4启动，源6ea，全21；controller786469/1792030166.5按原契约后续采集三phase新角色，再原FP32回退与nativegate。30minread-only监控现已绑定R2精确controller/SHAs，终态停用。
