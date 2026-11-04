# diag-001 P1K 稳态恢复

用户2026-10-14明确暂缓精度评测、稳态输出吞吐为主，守护TTFT/TPOT/ITL和请求错误。本轮performance Skill mode=targeted、scope=performance_only，不发GPQA请求，不签发正式精度/性能验收。既有FlagGems选择/blacklist/模型/TP2/graph/设备0,1/服务18430保持；源qwen-vl不修改。

旧18测量轮和原comparison保留incomplete：B03r8 P99TPOT波动超限。逐请求数据发现101个>800ms间隔、位于首波后段和下一波开头，相近单调时钟区间，最大1089.39ms；同种子其他角色最大431–452ms。不能将monotonic start_times当epoch对齐日志，也不据此断言JIT/客户端/设备根因。

前瞻性恢复假设：加三轮预热扩大过渡shape/执行状态覆盖。计划8warm+3measure，原吞吐准入末3轮≤5%、全测量主/守护波动≤10%、主改善≥5%、TTFT/TPOT退化≤5%、ITL≤10%、B/R漂移≤10%保持。新B05/C03/R03/B06/C04/R04全部独立实例，D1024/C64/N128/P1024不缩减，旧记录不混入新契约；只进行一次完整恢复系列，若新准入/请求/统计失败不继续盲目重跑，转专项trace归因。候选仍为已通过算子数值/graph回归的op002原补丁，未叠加新算子改动。

每个实例仅用16个短健康请求/C8确认非空/成功与两个worker16replay及取证撤销；不是模型精度评测。最终结论仅性能诊断，formal/四场景整体验收仍未签发。

执行前归档控制文件：

- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/prepare_stability_recovery.py` SHA256 `93d4b8cd2c09b1f5930e576484cb02d198381a3602a1662bddd7712af38e06c4`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/run_stability_recovery.py` SHA256 `8ce325722f056a4f7121eece9376dc47a08fdc2094f5a9c3c2757571bc603a43`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/compare_op002_stability_recovery.py` SHA256 `08df34d26e380b2fe8651df54b0773663f879427e495ed91b6749aff7b5b0d56`

每轮timeout600s，每实例11轮外层预算3300s；健康600s、启动600s。任一准入、请求或实例内指标spread失败立即停止系列，保留所有轮；无额外自动重跑。源代码切换仅作用于优化容器私有FG-vllm，精确SHA保护；每实例停止后等待API消失与GPU0/1空闲。

新远端计划/执行文件 SHA 清单见 `results/stability-recovery-preparation.json`（完整远端案例路径同上），回执SHA256 `55a8def0b8d01ecbfbd4e6bb937ca713f712ea6b672421321d0c60f104f0bf0e`。

- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/target-p1k-plan-recovery.json` SHA256 `2a214f87bee159ad26b4d3d7e60c1f9af47bbc6a27abc4c1aba01ce00e29e52f`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/comparison-stability-recovery.json` SHA256 `9a2f4c29e2a7bbd0c30c798189564d7473809ac52f5cdde7c543658c0f69b788`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/model_service_recovery_control.py` SHA256 `12f8f7348976cc43485c2ac3ac982d73ffe39f685dd79268aa33ae59505c3664`
- `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/switch_op002_recovery.py` SHA256 `f5d90d01e4cde7b0462d9b1a86f3879925f9b5aea7dfa830bcbab12e511e99b6`

启动命令：`ssh mx-59 python3 /public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1/commands/run_stability_recovery.py`。

B05启动、健康16/16与manifest/dryrun通过。两个worker均完成16次graph replay且取证hook撤销；实际四仓库指纹符合原路径身份。新测量round9/10/11的派生seed为74291/74292/74293，B/C/R一致；旧round6/7/8的数据不混入新比较。

恢复系列B05在8轮warmup后未准入：last3 TPS=[1761.4306720507077,1832.140373455048,1714.3292393257823]，spread=6.688377578443468%>5%；全部1024个请求成功，无测量轮获准，C03/R03/B06/C04/R04未启动。停止规则执行，不重跑；下一步profiling capture/analyze批次切换。停止自有B05命令：`ssh mx-59 python3 <remote-case>/commands/model_service_recovery_control.py stop baseline05`；不停止容器或源服务。

Profiling契约（capture→analyze，同diag001）：问题是第1/2波切换中的Mixed干扰/设备活动vs主机gap，并比较旧seed7/8；新的8轮预热未复现>800ms间隔但仍波动6.69%，不足以作纯设备归因。新服务transition01，仅profiler目录、delay_iterations=1000、max_iterations=120不同；源/实现/graph/TP2/CPUenv/采样/模型/设备与B05相同。P1024/D1024/C64/N128，ignoreEOS，temperature0，range0，每seed1完整诊断预热+1profile轮；seed7 profile派生74289（base47）、seed8派生74290（base48）。非稳态验收，不要求/声称预热准入；每轮timeout600s。窗口覆盖末尾Decode和波次Mixed，marker execute_new/cached+kernel correlation；purePrefill若窗口缺失标unknown，不假定。两个rank均须有新parseable GPU trace、实际graph/MoE命中；最多每seed采集一次，失败保留不盲重试。profile时间不报告性能收益。

执行前脚本 `<remote-case>/commands/prepare_transition_capture.py` SHA256 `9afd4d24a34b85bfb15dfcad42b588f1dc55edd82ee49491ec8f49d886985e04`。trace目录 `<remote-case>/profiles/transition01` 使用既有同一挂载；原生报告 `<remote-case>/results/profiling-transition01-seed7|seed8`。之前P1K无profiler B05 warmup上下文及op001两rank三阶段profile链接保留。

采集执行前控制程序 `<remote-case>/commands/run_transition_capture.py` SHA256 `1433e9663e88e0ed31c344837633ba76af82f342fb7da6718153df4e7a2bb333`，每seed外层预算1500s，finally精确停止自有服务并等待GPU空闲/API退出。运行命令 `ssh mx-59 python3 <remote-case>/commands/run_transition_capture.py`。

B05原生失败回执 `<remote-case>/results/performance/baseline05-target-p1k-01/run-record.json` SHA256 `49c1a1e15fcb617faf1896ce41500f7383780287400eeaf77c729f2c95f4ed97`。数据有效但warmup准入失败；8轮全部保留，不把预热作为正式测量。transition01已ready/16健康请求成功。执行前分析程序 `<remote-case>/commands/analyze_transition_capture.py` SHA256 `c4aaf9ad522f31aded4c0e9e74b1ead6b9b456b512b7349372f7adc9d8ef8faf`，产物 `<remote-case>/results/transition01-analysis.json`；将在两个采集完成且自有模型停止后执行。

收尾检查程序 `<remote-case>/commands/audit_transition_final_sources.py` SHA256 `6dd9e4f7532abc0d4040cb9a06347d788eea45fd2de5b82dacaac7e06e98f8b4`，待采集停止后核对源/private四仓库指纹、源8000服务、own18430退出；新产物名transition01-final-source-audit，旧audit不覆盖。

两seed两rank capture均complete，四trace解析及MoE关联unmapped=0。`results/transition01-analysis.json` SHA256 `cf0dfe9c0787719c0de2be57b28ac20dd09209328216801bc57b0e52c52aa1d0`；纯Decode110、Mixed10 marker/trace，无purePrefill，按契约保留窗口边界，purePrefill仍引用op001先前三阶段trace。进一步检查Mixed内部全GPU时间线gap及对应CPU活动：执行前 `commands/inspect_transition_gaps.py` SHA256 `434880c0d83cf8274731085eeda7273603b28fe64dccf07aa948a17d834a92b8`，新产物 `results/transition01-gap-inspection.json`。

本轮诊断结论：四新trace两rank均有效，110 Decode+10 Mixed marker/trace，MoE全部关联。相同M64 geometry下G1 seed7约175us、seed8约191us；G2约158/168us。窗口迭代间全GPUgap<6ms；Mixed内全GPUgap seed7约16–18ms，seed8约160–196ms，重叠copy_/cumsum/MoE CPU调用。不能把profile内部时延当无profiler原生性能，也不能断言新编译或路由分布根因（未采router值，默认Triton缓存时间窗未找到对应新元数据）。用户已明确保留op002并允许copy_/cumsum关闭诊断，后续转diag002，不继续盲加warmup。源保护审计passed，原/private在重新应用op002前均为初始身份；见新审计SHA f63b45b31405a7a48b66bb427d183e4a1b264576eda082fce0d3938f66d911bf。
