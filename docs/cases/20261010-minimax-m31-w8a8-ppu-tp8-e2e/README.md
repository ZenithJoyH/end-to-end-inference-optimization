2026-10-18 19:18: [op-017](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-017.md) revised Prefill/Decode/Mixed baselines all complete with6warm3measure and zero failures, medians6788.29/1919.95/5627.04 totalTPS. Prototype not deployed; no candidate E2E gain measured. Existing queue terminal, read-only monitor paused.

2026-10-18 18:49: [op-017](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-017.md) preserved failed short-Prefill admission; two independent fusion exact/graph passes save20.67-25.40% joint-chain time, not model throughput. Production unchanged; new N32-window phase baselines are running.

2026-10-18 10:12：[op-017](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-017.md) 当前opt6迁移组合新正式GPQA171/198=86.36%通过81%阈值及native gate。原队列进入Prefill基线，融合未部署；只读监控已终态暂停，未变更远端流程。

2026-10-18：用户恢复优化；[op-017](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-017.md) 先对当前两分支迁移组合补完整GPQA，再串行建立Prefill/Decode/Mixed基线并测试保留真实量化公式的OAI+quant2融合原型。生产源码未改、无本轮新收益，准确进度/证据见模型state.yml。

2026-10-17: refreshed the installed private Plugin checkout from the user-selected024plugin-opt branch. HEAD remains08da21cb; required model adapters and source tree8320 are unchanged. Source/diff backed up; no restart or inference traffic. Evidence and validation limits: [env-004](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/env-004.md).

2026-10-16 latest: [env-004](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/env-004.md) completed the user-requested Plugin migration to024plugin-opt@08da in a private checkout. Focused unit45/PPU10/current native105+2/capture passed. TP8/8035/opt6 is healthy and quiet; root e12c3b/11exports and FVgems-opt463 unchanged. Old sources/install preserved for rollback. New formal GPQA and E2E are not run; pause continues.

# MiniMax-M3.1 W8A8 / PPU-07 / TP8 优化

2026-10-16 latest: [env-003](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/env-003.md) migrated the optimization container to ZenithJoyH gems-opt@46387d7, private `/workspace/FlagGems-vllm-gems-opt-20261016-01`. Public scaled-mm PPU backend and retained MoE policies are installed; Plugin bridges support this branch. Dense24/activation48/current model105+2 and graph checks passed. Service8035/nameopt6 healthy and quiet; original root e12c3b/11exports preserved. Formal GPQA for this changed source is pending; no oldgate rebind or new benchmark. Performance/optimization remain user-paused.

2026-10-15 opt4 最新状态：用户三轮CSV仅P4观察+2.59%，P16/P32近乎持平；[perf-007](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-007.md) 已完成当前8rank三阶段诊断，确认长KV Decode的M16/M32未进入旧M64特化。[op-014](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-014.md) 的API覆盖扩展micro通过，两组targeted基线已完成；候选已部署并通过graph/105+2，本轮新GPQA169/198=85.35%≥81%且nativegate通过，精度监控终态PAUSED；现有缩减targeted C已完成、R复测中，最终收益/保留待native比较。根脚本11exports保留，独立容器/私有源码延续；旧精度分数属于历史实例和name，完整四场景验收仍未完成。

用户2026-10-10明确恢复任务并切换8卡；继承模型适配和已隔离容器，不继承16卡性能或精度gate。目标稳态总吞吐，GPQA198题strict-match>=81%。正式场景顺序P1K/P4K/P16K/P32K，均D1024/C64/N128。

当前输入为用户start-model.sh SHA57442d5a08af565dcc317749536d7bf18e5ca63e61fb9614a1590eedbcc7f747，基线服务8025、TP8、7Mixed+7Decode buckets、原11exports；fw-004临时14Mixed/7Decode候选仅在案例启动副本测量。

外部案例：/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e。镜像谱系和挂载一致性通过。原 TP8 路径 C8 0/8、C1 0/3；[diag-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/diag-001.md) 将首次数值分歧定位到 PPU GQA8 sparse Prefill attention。私有 Plugin 的 [fix-001](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fix-001.md) 只为受支持形状将内部 head tile 补齐到16，24组算子检查、graph两次replay、当前105+2最小回归及8rank命中通过。临时观察补丁已撤除，完整TP8 GPQA Diamond198已通过：170/198=85.86%，strict-match>=81%；原实例native issue/check通过；profiling后恢复7桶服务 fresh105+2及native rebind/check通过，沿用原170/198；14桶新配置不能复用原gate；本轮新完整198为169/198=85.35%，native gate已绑定当前候选，门槛81%通过。

FG、FG-vllm、vLLM、源容器和根脚本保持原状态。[perf-002](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-002.md) 已完成P1K稳态单实例基线：三轮总TPS均值1968.23、相对极差0.1384%、延迟守护波动通过。纯Prefill未准入，last3warm spread6.68%>5%，零测量并停止原控制；[perf-003](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-003.md) 已补齐Decode/Mixed-short基线并完成两场景全部8rank与frontend trace归因，保留纯Prefill未准入证据；[fw-004](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fw-004.md) 新契约8warm+5measure的基线校验通过，Mixed4651.50、Decode1647.33TPS，14桶候选capture与105+2通过，因graph覆盖变化先新完整198（169/198，85.35%通过），候选Mixed五测量均值+0.60%、中位+1.29%低于3%，Decode8warm稳态5.19%>5%、零测量，固定序列停止并不保留。已恢复7桶，fresh105+2及原7桶170/198 native重绑定通过；plan-022转MoE实际shape/backend发现。用户CSV有P4K/P16K/P32K，缺P1K，且缺少服务绑定与稳态准入证据，保留为观察数据；目前没有8卡吞吐收益结论。

模型入口：[baseline](../../../models/MiniMax-M3.1-W8A8/ppu/baseline/README.md)、[optimize](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/README.md)、[acceptance](../../../models/MiniMax-M3.1-W8A8/ppu/acceptance/README.md)。

2026-10-12 根因机制：[diag-003](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/diag-003.md) 已用原始→仅修正A加载地址→原始证明PPU BF16 M8 shared-to-MMA路径漏lane16 K坐标；现有H16绕行的正确性来源已明确。全程独立空闲PPU8，生产服务与源码保持不变；编译器C++源码修复未实施，性能四场景仍未验收。

2026-10-12：diag-004已提交[FlagTree #1350](https://github.com/flagos-ai/FlagTree/issues/1350)。官方最新PPU wheel0.7.0+ppu3.6在独立进程/空闲设备同脚本复测仍失败；主分支未硬件验证。生产服务/源码/根脚本均保持，H16绕行继续保留。

2026-10-12 算子进展：[op-003](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-003.md) 的实际8rank MoE形状与硬件oracle/graph核验完成；原tile-only因强抵消FP32累加边界冻结，[fix-002](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/fix-002.md) 使用限域INT32精确累加，再叠加M64/M1024/M8192的GEMM1 K256特化。候选仅修改优化容器私有FG三个文件，源容器、FG-vllm/vLLM、原H16/TP8/7桶/11exports与根脚本不变；source SHA4292e8bd38116c7d7a502080df713092d337366ebfa1c9a43e4ec349f1f210ef，FG tree4e67f1a41f47b2227d67e6a1d7d15caa4335624b7f0bfac8ebe1f38864e36d90。新完整GPQA164/198=82.83%>=81%，较此前170/198少6题，不宣称分数不变。

旧Mixed回退ITL波动13.08%>10%保留为incomplete；Decode+7.43%、Prefill+2.74%原生对照通过。一次有界相同10warm5measure新Mixed审计全部三角色passed，中位4650.294→5066.445→4651.275 TPS，+8.95%、回退漂移0.021%，P99延迟守护均改善；native比较在外部 `performance/op003-mixed-repro-02/comparison-mixed.json`（SHA1b429deee95c41d8e6128582430242319a31396ec30014de780c4a9f2bcb2c84）。SSH断线发生在恢复原FG完成后/服务launch前，guarded resume沿用归档配置成功恢复，没有重复停止或变更。plan-028已晋级原P1024/D1024/C64/N128正式6warm5measure，目前基线运行中，候选尚未最终保留，四场景正式验收未完成。

2026-10-13：op-003 P1原始finite-batch正式三角色passed，totalTPS中位1976.823→2126.634→1970.851（+7.58%，回退漂移-0.30%），全部P99延迟改善。组合在P1 retained，正在恢复同字节FG4e67候选并补当前实例回归/原164重绑定；根11exports/TP8/7graph及H16保持，四场景最终验收未完成。后续P4须新冻结入口baseline_parent_candidate=当前P1保留组合，先重建三阶段视图，再选择算子方向。

2026-10-13 用户继续优化：当前用户服务8035 / MiniMax-M3.1-opt2，根脚本用户修改保持原11exports；实际私有FVf924/Plugin011f/FG1e56/engine5e7与op004完整169/198=85.35%版本相符。旧8025/name gate不能rebind；当前fresh105+2、all8 backend命中、graph>=2已passed。用户opt2三轮P4/P16/P32 totalTPS均值3728.56/4060.80/4163.90，相对opt1观察+7.69%/+5.87%/+6.44%，不是新的四场景正式验收。旧op004 P1迁移回归预热失败64个请求且后续切服，0测量，原生失败保留incomplete。

[perf-004](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/perf-004.md) 当前P4 reduced三阶段6warm3measure全部passed：PF P4096/D1/C8/N16 median7103.45TPS，Decode P4096/D256/C64/N64 median5551.33TPS，Mixed P4096/D128/C64/N64 median6259.07TPS；不同负载不互算速度，client/queue/PF干扰成本保留。下一项[op-005](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-005.md) 为PPU非TLE smallM对齐5→2launch独立原型，正在CPU路由oracle/graph2/完整两GEMM配对验证；尚无生产新改动或新增E2E收益。官方最新PPU FlagTree已隔离测试但barrier/remote缺lowering，未晋级生产。

2026-10-14继续用户opt2优化：op005对齐、op006行tile、op007 G2 stages试验均未满足预冻结晋级/guard，未改生产。下一步perf005全8rank当前P4阶段trace；最近baseline为perf004三个缩减阶段均通过，当前服务8035/nameopt2，旧8025 GPQA169/198为源历史精度，下一保留候选需新full198。

2026-10-14 op008：current8rank三阶段trace完成，G2 INT32仅M1024/8192两轮joint micro约12%（非E2Egain），selector15+模型107/actual8rankhit通过，privateFV一文件新候选d498已部署，root原11exports/8035/nameopt2保留。freshGPQA198>=81运行中，fullgate后同Mixed reducedB/C/R已排队，条件保留+exactscore rebind/回退；原P4完整D1024N128及4场景验收仍pending。auto-review拒绝导出远端评测控制代码，已全部留远端生成，未阻塞任务。


2026-10-14 opt3 算子续优化：op009/010/011三项MoE候选数值通过、性能拒绝；op012现成FV dense GEMM 36回归通过、12shape均更慢。op013新 dense INT8 split-K4 在M64/K6144/N1536/768上split+reduce耗时降低31.6%/49.0%，26 guard反例、6整数oracle/bitwise/graph与8 Plugin接入契约通过，代码staged尚未部署。当前opt3 source仍FVd498/Plugin011f，root原11exports不变；用户改name后旧opt2 gate不可复用，现已启动新完整GPQA198/81%。原生产物 accuracy/op013-baseline-formal；新精度gate通过后受保护queue只测完整P4基线B，不改代码。端到端提升、候选正式精度和最终四场景验收仍未完成，详见 models/MiniMax-M3.1-W8A8/ppu/optimize/op-013.md。

2026-10-14 用户基于 PR924 fb70fd2 对齐后 opt3-retry 明确恢复 split-K 验证。实际 FV 私有导入副本 /workspace/FlagGems-vllm-pr924-fb70fd2-20261014-side-01，根脚本 e13a1372...ec70c 保持11exports。op013最终Plugin量化+GEMM链路7case/显式vendor15calls/CPUint64/全输出bitwise/graph2通过，N768/N1536 median耗时下降46.31%/29.82%，不是端到端收益。候选source只staged，未部署；旧opt3 gate/B不绑定本次新来源。当前新baseline107回归通过，原生 fullGPQA198/81%已启动、same-run finalizer与只读30min monitor ACTIVE；P4新baseline protected队列等待此gate。正式候选精度、C/R和E2E收益仍pending。准确产物及plan-039见模型 optimize/state.yml、[op-013](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-013.md)。

2026-10-15 本轮已完成：修复finalizer两处source路径和SHA，以已有169/198=85.35%签baseline gate，未重跑GPQA。P4同配置6warm+3measure原生B/C/R总TPS中位3620.62→3699.32→3607.43；split-K +2.1738%，B/R漂移-0.3643%、四P99守护通过，因未达3%门槛native failed，**不保留split-K，当前恢复PR924 opt3-retry基线**。回退105+2/graph及原score native rebind/check通过；root原11exports不变，无待跑任务，monitor PAUSED。本轮performance_only，无候选formal GPQA或四场景验收。详见 [op-013](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-013.md)。

2026-10-15 用户选择保留split-K +2.17%：同字节候选已恢复至minimaxM3.1-opt-20261008，TP8/8035/root原11exports保留；新105+2/graph与两N各8worker命中通过。新的候选GPQA198/81%已启动，原生preflight通过，同run自动finalize及30min只读monitor ACTIVE，当前无分数/gate。产物 accuracy/op013-retained-formal-20261015-01；精度后用户自行压测，Agent无性能流量。旧native3%比较failed保持历史，用户保留例外单独记录；详见模型op-013。

2026-10-15 split-K已按用户决定保留并恢复，**新完整GPQA169/198=85.35%≥81%通过**，独立run cda243...9036、当前nativegate a97b30...7186和source/live check均通过。新native107/graph/两N8worker通过；TP8/8035/opt3-retry服务healthy且quiet，root原11exports不变；评测客户端已退出、monitor PAUSED。交用户自行端到端压测，本轮Agent未发性能流量；历史P4+2.17%<3%的native failed保持。详见 [op-013](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-013.md)。

2026-10-15 [op-014](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-014.md) 缩减B/C/R完成：P16D256N64总TPS中位5988.90→6031.87→5990.26（+0.7176%，低于1%，native failed）；P4D128N64 6519.48→6521.16→6518.50（+0.0257%，native passed），其它护栏通过，自动回退。用户明确选择恢复本轮M16/M32候选自行完整压测，已同字节恢复FV API4dc6/树61b3；当前新服务capture/最小及原85.35%正式gate native rebind待完成。原生性能结论不改写，完整四场景仍未验收；根脚本11exports保持，后续交用户后不再自动发性能流量。

2026-10-15 19:52 [op-014](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-014.md) 按用户选择已恢复M16/M32候选，48项8worker命中、FULL/PIECEWISE capture、107最小与38replay通过；本轮GPQA169/198=85.35%≥81%原score native rebind/check通过（gate96d4...03f0），未重跑。8035/nameopt4服务healthy/quiet，rootcd11/11exports不变，无评测或性能客户端/活动队列，monitor PAUSED；交用户直接压测，自动优化暂停。原缩减P16+0.7176%<1% failed/P4+0.0257%passed保留，完整4scene仍incomplete。

2026-10-16 10:33：op015四组tile×2shape数值全通过但全部更慢，无部署；op016 percall B列布局两轮独立actualPlugin链路耗时降低约39%，实际2文件FVf3ef候选已部署，graph/native107/33replay/全8workerPF命中/KV435584不变通过。新fullGPQA198/81%运行中，score/gate pending；原11exports/rootdd94/nameopt5保持，same-run nativefinalizer及gate后PF/P16Mixed/P4 C/R条件保留队列真实进程已核验，monitor30min ACTIVE。三组B总TPS中位7020.05/6402.53/6518.40已完成，C/R待新gate；没有新E2E提升或四场景通过结论。

2026-10-16 11:54 Asia/Shanghai：op016本轮新正式GPQA已完成，原生exit0，strict-match **169/198=85.3535%≥81%**。本轮run为349c167bf46a4b3f86344fa332e4fe00；JSONL逐物理行396条、唯一doc_id198、无无效行。原生gate `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/accuracy/op016-candidate-formal-20261016-01/accuracy-gate.json`（SHA a1d87d37395fb63a370271b2f7d6e1124b2442400de59aba2648e534b0fd793d）绑定本轮MF3a9a3975，nativefinalizer终态0。精度监控已PAUSED，既有性能流程继续。Prefill与P16缩减candidate原生record complete；P4 candidate已完成第4/6轮，R尚未开始、最终比较/保留未决定。当前无完整B/C/R收益结论，不是四场景full验收；没有由本次只读监控启动/重试/改变远端流程。

2026-10-16 14:20 Asia/Shanghai：三组缩减targeted B/C/R全部完成，native comparison均passed，按冻结的3warm+3measure保留全部测量轮并取中位总吞吐（token/s）：

| 场景 | Baseline | Candidate | Revert | C/B提升 | R/B漂移 |
|---|---:|---:|---:|---:|---:|
| Prefill P16384/D1/C8/N8 | 7020.05 | 7463.33 | 7017.96 | +6.3145% | -0.0297% |
| P16 Mixed P16384/D128/C32/N32 | 6402.53 | 6760.29 | 6408.47 | +5.5878% | +0.0928% |
| P4 P4096/D128/C64/N64 | 6518.40 | 6865.00 | 6520.18 | +5.3172% | +0.0272% |

Prefill p99TTFT/E2E降低5.94%；P16四项p99降低5.29–5.71%；P4四项p99降低5.06–6.31%，守护均通过。B/R漂移均不到0.1%。原生比较SHA依次916d4c08...04f8、f976292d...619b、0f7f87c9...b4bf；完整路径和全部三轮指标见state.yml performance_result。队列result d43339c5...73e确认按冻结条件保留候选。

retained服务MF7a701350...a238，native最小passed11961c8c...1619，runtime7764b143...7410；原正式85.35% gate的native rebind/check通过，reboundgate ac625c95...7d74。当前真实服务PID/startticks/argv与manifest相符、health200，两文件SHA仍为c9c2/b47f，FVf3ef；rootdd94/原11exports/nameopt5不变。候选在minimaxM3.1-opt-20261008的8035运行，精度monitor保持PAUSED；本次查询没有重跑测试或改动远端。提升仅属于上述缩减workload，未宣称D1024/N128四场景full收益；未提交/推送。

2026-10-16 14:32 Asia/Shanghai：用户明确暂停后续优化与压测，接管完整端到端性能验证。只读确认原生gate队列已终态保留且进程退出，无本任务op016控制/评测/压测进程，精度monitor已PAUSED；保留8035模型服务health200。根start-model.sh仍SHA dd94/原11exports/TP8/nameopt5，容器新Python解析到本轮FV私有根，两文件SHA与已保留候选一致。用户在minimaxM3.1-opt-20261008中使用同一根脚本即为本轮版本；当前服务已运行。交接后不自动启动后续优化/评测/压测，等待用户明确恢复。

2026-10-16 pr-002：dense INT8正式PR结构候选已独立整理并归档，公开scaled-mm接口复用、PPU backend集中、两仓库补丁分离；76项主机检查通过，未部署，不影响用户压测。详见模型optimize/pr-002.md；GPU与集成验证待明确恢复后进行。


2026-10-18 op-017：激活＋INT8融合已接入用户指定gems-opt/024plugin-opt私有副本，FV e182/Plugin fc226；8卡operator/graph、Plugin50项、模型8worker命中及原生105+2通过。新完整GPQA198阈值81%已启动，目录 `accuracy/op017-candidate-formal-20261018-01`，原生finalizer和30分钟只读监控已运行；尚无候选新分数/gate。根脚本/11exports/8035/nameopt6保持；用户将在精度结果后压测，本轮无自动E2E队列。详情与SHA见模型optimize/op-017.md和state.yml。


2026-10-18 op-017正式精度终态：融合候选新GPQA166/198=83.8384% >=81%，198唯一doc_id/396物理行，exit0；原生gate `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/accuracy/op017-candidate-formal-20261018-01/accuracy-gate.json` SHA256 `d47ef2cd0a3ca0c23b0c0baee88bf85e7050a98bab135ea67285368c278142d6`，原生issue/check通过。当前候选源与服务健康重新核验，GPQA与finalizer进程均退出，监控已PAUSED；模型服务和原根脚本/11exports保留，交用户跑端到端，未启动任何压测或新优化。旧基线171/198不作本轮分数。完整原生产物引用见模型optimize/op-017.md及state.yml。

2026-10-19 用户opt7新精度：按确认的temperature1/top_p.95/top_k-1，GPQA198默认18000已启动，Math500500默认28000及ERQA400/30000串行排队。当前opt7/8035/TP8服务、root11exports和prefix cache启用状态保留，源代码未改；三套实际payload已预检。产物在accuracy/user-opt7-t1-suite-20261019-01，监控ACTIVE，尚无新分数；详见op-017及state.user_requested_accuracy_current。旧t0融合166/198为历史独立结果。


2026-10-19 opt7三项原生精度完成：GPQA160/198=80.81%（低于81%，无gate）、Math500464/500=92.80%、ERQA158/400=39.50%。ERQA原生exit0/400唯一ID/正确数158已核验；队列收尾因磁盘启动脚本SHA漂移而断言失败，原生结果仍在pgt-mmeval私有目录，宿主拷贝未执行。监控已PAUSED；未重跑、未改远端或启动性能，历史t0的166/198保留。完整路径/SHA与异常边界见op-017及state.user_requested_accuracy_current。


2026-10-19 opt7低分离线诊断：GPQA21题18000预算触顶，其中19错，16次strict提取失败全部触顶；相对旧166/198还同时改变采样/预算/cache，不能归因算子。ERQA确认107/400原始输出为U+0000重复30000次，评分前已退化；其余293题158正确（53.92%）。归档报告SHA4f7c3200…acfc7，详见op-017 accdiag-006/007及state.accuracy_issues。实际token/logit、MM/C1/C16和算子因果仍未复现；未改服务/源码或发新模型请求，当前无81%gate，性能保持暂停。


2026-10-19 用户明确要求直接升级FG：canonical /workspace/FlagGems已固定上游3b76f81，editable版本5.4.0rc2.post1+g3b76f81d4。旧D80 SDPA splitKV combine stride问题在新版最小复现中消失；两文件回移8rank视觉层有限，原六次NUL前缀从6/6降至0/6。为新版FP8-only ATen scaled_mm修正FV/Plugin的PPU INT8提供者调用；20单测、八卡56项逐位相等/graph2、正常服务105+2全通过，最终新版6次ERQA短请求均无NUL。正常preview/8035服务保留、诊断扩展移除、根脚本及环境未新增；当前根脚本已由用户指向10/19Flash，不能混用其与运行中的9/29preview精度。新完整GPQA/ERQA和E2E未运行，历史分数不变，无新gate，监控PAUSED、性能仍暂停。当前结果/回退引用见[op-017](../../../models/MiniMax-M3.1-W8A8/ppu/optimize/op-017.md)及state中op-017.erqa_reproduction_20261019记录。


2026-10-19 16:44 Asia/Shanghai：按用户“重新跑下ERQA”授权，已启动新版FlagGems 3b76f81后的单次原生ERQA400全量验证。实际服务仍是preview 20260929/opt7/8035/TP8，未启动磁盘脚本指向的Flash。temperature1.0/top_p0.95/top_k-1/max_tokens30000/C16，禁用评测响应cache、保留服务prefix-cache；原数据SHA c0296383…663c及原生评分器已冻结，不改变评分。当前8/400唯一题号完成，0 NUL-only、0原始空响应、0触顶，服务health200/16个运行请求；尚无本轮正式分数，不以短前缀或旧158/400替代。原生任务与控制均已按本轮argv/startticks绑定，监控ACTIVE/30分钟，无变化安静，整轮归档与校验终态后暂停。预检-01因namespace包来源读取辅助脚本失败、零模型请求，记录保留；修正后在独立-02启动，无全量自动重试。

外部产物：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/accuracy/user-opt7-erqa-post-fg-20261019-02`；实际原生目录`pgt-mmeval:/mnt/op017-user-opt7-erqa-post-fg-20261019-02/outputs`。最终由既有控制核对400唯一ID、正确数与原生accuracy、数据/评分器/源树及服务连续性并归档result.json。ERQA无指定阈值、不签GPQAgate；本轮不跑其他数据集或性能、不改服务/源码。旧三项分数及GPQA门禁缺口保留。


2026-10-19 ERQA升级后完整复验终态：单次原生400题已完成并归档，**245/400=61.25%**，较旧158/400=39.50%增加87题、21.75个百分点。400个items和400个evaluated的唯一question_id均与冻结集合完全一致，原生正确数与accuracy一致，exit0，数据/图片/原生评分器及服务/source连续性核验通过；宿主归档副本及SHA独立复核通过。原始输出NUL-only为0/400（旧107/400）、真正空响应0/400，10题达到30000tokens上限；触顶是输出诊断，不是额外门禁。

本轮绑定8035/opt7/TP8、9月29日preview权重、FG3b76f81及已验证FV/Plugin INT8兼容补丁，temperature1.0/top_p0.95/top_k-1/max_tokens30000/C16。此为新的单次采样结果，不将分数差全归因某一题或冒充10月19日Flash验证。accdiag-007的NUL故障已获得原400题范围复验；旧GPQA160/198、Math500464/500及ERQA158/400历史保留，GPQA独立缺口仍在，无新GPQA gate，不启动性能或其他评测。整轮控制完成后监控已PAUSED。

原生结果：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/accuracy/user-opt7-erqa-post-fg-20261019-02/erqa/native-output/erqa/erqa_result.json`（SHA256 `45726e725b4520de1991bcfac4e71f2ecb0797756d7a516b86e51f0fbde9dbe7`）。同轮`result.json` SHA256 `6621076bdd75c97c7bf0ee0de6be687e8db98b0fa74a5a06b07321bbc6abc8f9`；`erqa/native-audit.json` SHA256 `d0ed3d692af428e33aa203f294b5bb87c01a8407d06f492228e00916d92f38e4`。完整路径/来源与运行后身份见state.user_requested_erqa_current.final_evidence；不保存题目或响应到本地。
