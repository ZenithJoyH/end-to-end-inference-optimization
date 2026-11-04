# perf-003：TP8 Decode/Mixed 基线与全部 rank 阶段归因

状态 completed-diagnostic。plan-019在perf-002纯Prefill准入失败后独立补齐未运行阶段，不重试失败Prefill、不改旧结果；plan-020随后完成两场景profiling。源码、原11exports、TP8保持不变；profiling耗时不作为性能收益。

无profiler阶段探针均6warm+3measure，last3warm总TPS spread<=5%，全部三测量及守护spread<=10%，600s/round。Decode P128/D256/C64/N64总TPS均值1640.1420、中位1642.0512、spread0.6570%；P99 TTFT1576.5974ms、TPOT53.86465ms、ITL54.02254ms、E2EL14982.3602ms。Mixed P1024/D128/C64/N64总TPS均值4653.0659、中位4648.9945、spread0.5281%；P99 TTFT9042.5362ms、TPOT112.1912ms、ITL1067.8169ms、E2EL15831.5837ms。两场景各576请求有效，输入/结果/客户端SHA核验通过，控制exit0。TTFT/TPOT是客户端和调度代理，不能作为纯设备时间或不同workload间加速比；原P1K正式基线与纯Prefill incomplete仍保留。

两场景trace为P1024/D2/C64/N128与P1024/D32/C64/N64，各1warm+1profile。每场景覆盖全部8worker和frontend，native capture/parse及SHA核验通过。分析用真实sparse_fwd/sparse_decode、quant grid、CPU execute marker和driver关联GPU launch确定阶段；cached-only不等于Decode，两个marker保持unknown，Mixed共享GEMM不按token比例分摊。两场景全部rank的Prefill-containing迭代无graph launch、quant行数可达8192；后段query1 Decode模型graph关联到scaled_mm、quant和norm。MoE为Decode主要设备热点，PF/Mixed还含矩阵乘、attention、collective；profiler下rank通信差异可能有等待和采集扰动，尚不能认定系统通信为根因。Python嵌套span不计作热点独立成本，union与间隙不冒充critical path或设备利用率。

with_stack=true导致大trace和较慢分析，约5.5GB压缩产物留在远端。v2仅分析进程因开销过大按精确身份停止，partial结果保留；v3完成全部rank。后续如需reprofile，应按新冻结契约考虑with_stack=false，不把旧partial结果作最终归因。

已按精确进程树撤除profiler，恢复原7Mixed+7Decode配置。新实例3406668:433520474 fresh105+2通过，C8/C33/C64 Decode replay推导下界40/37/41，8rank fix001 backend命中。原schema3 gate执行native rebind/check通过，evaluation_reused=true，沿用170/198=85.86%，并非新198评测。当前监控终态PAUSED；随后服务进入fw-004单变量候选，恢复实例绑定是历史事实，不能直接用于新14桶配置。

远端根为 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e`。阶段基线 `performance/phase-followup-01`；全部rank审核 `profiles/perf003-phase-profile-01/profile-review.json` SHA d41c0a9a41705a743677375ada56416979c8ce13e1857e2ea0c6762e54982fc0；归因summary在analysis-prefill-02与analysis-mixed-02。恢复服务 `manifests/perf003-restored-service-verified.json` SHA40177e65bd96792cdebd43a536b4bb029758f2fa5239541072488b2365aff7ab；恢复gate `accuracy/perf003-restored-rebind-01/accuracy-gate.json` SHA31ec88d17c6260076984a5009ae6612a9742de77a86e7bb15232ecc16b075a47。所有控制、native回执和其他完整SHA见state.yml。

plan-021已据此选择[fw-004](fw-004.md)配置实验：新冻结8warm+5measure的Mixed/Decode三角色对照，原三轮结果仅为上下文。算子替换/深度优化仍须实际导入、dispatch、shape与数值oracle证明，不用kernel名称推断backend。当前无新增吞吐收益结论，无正式场景关闭。

在FW004新full198期间，只读核对文本config：128专家、top4、57MoE层/前3dense、shared1、hidden6144、intermediate3072、SwiGLU-OAI alpha1.702/limit7.0。有限rank0原trace来源扫描观察到FlagGemsW8A8Experts.apply → Plugin两GEMM fused_experts_impl → FlagGems backend invoke → `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py:1607`。v2回执 `profiles/perf003-phase-profile-01/moe-source-path-review-v2.json` SHA f07e83974a6ccf143eb187375fade5da4d396129fa01fdac3f42d076018e941e。此扫描只证明来源字符串出现，不用于调用数/时间/形状或当前candidate14全rank attestation；具体FG JIT specialization和真实分rankshape仍须核验。没有给模型加补丁，没有开始新算子性能实验。

MoE 配置来源补充只读核验：Plugin `ops/fused_moe/fused_moe.py` 从 vLLM 导入 `try_get_optimal_moe_config`，配置依次检查 vLLM override、用户/内置配置文件，再使用 vLLM default；选定配置传给 FlagGems kernel。FlagGems 自身 `get_default_config` 不能代表本服务所选配置。当前 override、有效 TP8 权重 shape 和真实 JIT tile 尚未核验；未实施新算子优化。
