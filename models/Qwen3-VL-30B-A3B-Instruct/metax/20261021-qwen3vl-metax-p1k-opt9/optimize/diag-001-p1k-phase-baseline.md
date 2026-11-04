# diag001：opt9 P1K入口基线与阶段归因

2026-10-21，mx-59。用户提供历史结果`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt9`，指定当前容器继续优化1K/1K。当前仅qwen3vl-p64k-opt-20261015存在，8111/8000均停止，8GPU空闲；不停止任何既有服务。源码仍是FlagGems gems-opt/c3c5f5ab2、FGV f6fdb9b+既有MoE/采样、Plugin08da21c+适配、vLLMee0da84只读。

历史P1K三轮941.46/1005.00/1069.49tok/s，SUMMARY1037.24使用后两轮；首轮TTFT偏高，后两轮吞吐差幅约6.2%。CSV仅作现象输入，不把历史汇总当作新基线，也不按结果事后删轮。

远端根目录/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9，用户授权根路径/public-flash/jinghao/qwen3-VL。新容器qwen3vl-p1k-opt9-20261021由当前有效writable-layer快照复刻，挂载必须相同，源码使用容器私有/workspace；当前源源码/启动脚本保持直至候选验证后必要回写。GPU0/1、端口18144，源8111当前关闭。

本轮选择e2e/accuracy baseline-sanity及后续minimal-regression；e2e/performance baseline/targeted、performance_only；需要时profiling capture后analyze。最终目标稳态输出吞吐；TTFT/TPOT/ITL、失败和graph为守护。采样temperature.7/topk20/topp.8/ignore_eos，与当前模型generation_config核对；seed42、固定random长度。不得通过关闭FlagGems算子优化；既有blacklist mm,mm_out,layer_norm,log_softmax保持，不新增禁用项。保留gems-opt/sort和当前MoE参数作为基线，不复用PR943新实现。

测量前冻结：目标P1024/D1024/C64/N128；低成本milestone P1024/D256/C64/N128映射同目标，用于证伪；Prefill探针P1024/D1/C64/N64、Decode探针P1/D256/C64/N64；残余网络/调度/prefill不冒充纯GPU阶段。先建立3阶段视图，再选择方向。收益判定预期>=2%，轮差幅<=8%、B/R漂移<=8%、P99延迟守护<=10%；无明确业务SLO，不宣称业务达标。初始三轮预热、两轮测量，预热末两轮差幅<=8%，所有准入测量轮保留；未稳则incomplete并对全部角色重建契约。若有采样新M编译，先覆盖M1..64，不将启动编译优化作为目标。每轮预算900s，baseline诊断总预算1800s，超时保留部分证据。

当前3阶段热点unknown，需基线/trace；不提前认定MoE或采样为瓶颈。正式精度与四场景full未执行，当前仅目标场景优化。

## Resource conflict before baseline

Initial mx-smi preflight showed8idle GPUs and no processes. During snapshot/startup, another TP8 service occupied all8cards (~59–62GiB/card). Dedicated workers then stalled in queue creation with only2MiB/card allocated, before model/graph/shape warmup. This is not a steady-state performance finding and is not evidence of an operator regression or driver defect. No benchmark or trace started. Stop only the dedicated18144 service, retain all evidence, and request two exclusive cards. The uploaded one-element device probe remains unexecuted after occupancy changed. Source container/repositories/start-model.sh remain unchanged.

## GPU validation resumed 2026-10-21

User explicitly authorized releasing GPU memory and proceeding with E2E validation. Fresh inventory/connectivity passed. Identified occupying service as deepseekV4-flash TP8, port18001. Release only exact verified API process and descendants; preserve container and save launch recovery information. Command: remote commands/release_tp8.py (same case root). Existing incomplete baseline files preserved; use new baseline2 role.

## Completed diagnostic phases

Baseline2privateimports/FlagOSMoE proven,graphcapture and16replays perrank passed; nine smoke/C8requests andtenfixedscienceprompts concurrency8passed output-health checks. FormalGPQAdeferred. Profiler traces: PrefillP1024/D2/C64/N64,DecodeP1/D64/C64/N64,MixedP1024/D64/C64/N128,each1warm/1captured,64iterationcap,bothranks verified. They are diagnostics only, not target throughput and not steady comparison. GPUexecute_new/cached annotations delimit model steps; cached-only P1 decode proxy retains scheduler/network/sampling residual. Mixed trace covers initial64steps, not entire finitebatchtail.

Rank0cumulative device Decode: MoE1159.384ms/6144calls;radixsweep291.676ms/512calls;hist81.156ms/64calls;count25.352ms/64calls. Median execute GPUregion34.223ms. Prefill MoE1636.338ms,AllReduce582.527ms,FlashAttention151.799ms. Mixed MoE2424.747ms,AllReduce689.328ms,sweep289.291ms. Sums can overlap and are not critical-path/deviceutilization/E2Etime. Evidence remote results/phase-trace-analysis.json SHA8a61c13e921d7fc584ee4f852e1cc47a3cd085ce1a2b1df1afc77b3aa7436f95.

Original source remains unchanged before full baseline; op005localhist only planned candidate. GPU0/1 exclusive to18144; a separate qwen3vl-opt9 port9999 service usesGPU6/7 and is not signaled. First profiling attempt failed preexisting trace-directory requirement before traffic; preserved, recreated with profile_v2.py.
