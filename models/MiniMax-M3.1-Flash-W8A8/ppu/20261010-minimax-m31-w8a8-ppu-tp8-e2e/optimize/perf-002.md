# perf-002：TP8 P1K 稳态基线与阶段视图

mode=baseline。当前目标p1024-d1024-c64-n128，原用户TP8路径最小回归失败，fix-001是建立正确TP8基线的必要修复，不把跨TP16或错误路径吞吐归为优化收益。精度完整198达到81后才发送性能请求。提供的三份P4K/P16K/P32K CSV无绑定与稳态准入，不作为正式同配置baseline。

先测原P1K目标，再形成Prefill P1024/D1/C64/N128、Decode P128/D256/C64/N64、Mixed milestone P1024/D128/C64/N64。阶段TTFT/TPOT为客户端代理，仍含网络/调度/剩余Prefill或Decode开销；缩减场景不得冒充正式P1K。主指标total_token_throughput，守护P99 TTFT/TPOT/ITL/E2EL。每场景预冻结6warm+3measure，最后3warm相对spread<=5%，保留全部3测量轮，测量spread限10%；600s每轮预算。缺失SLO不宣称goodput。正式候选仍需同配置baseline/candidate/revert各2独立实例、3轮、主收益>=5%、latency守护<=5%、漂移<=10%。

只准备CPU配置，当前full198在运行，性能not_run。控制commands/tp8-phase-baseline-prepare.py SHA f8a3f575c219cc9289ebbda44ad1a45b202a755684f3b65b509eb85856d2051b，执行前记录。原target超时保存deferred-too-slow/incomplete，客户端和服务idle后才做缩减基线。P4K/P16K/P32K待按顺序推进，最终4项完整验收未开始。

完整TP8正式精度198题170/198=85.86%通过，当前gate SHA492470e965f1263459937f56656105e7fc38d2a0bd7a6bf41293fe5f7504f759，精度监控终态PAUSED confirmed。额外评测队列/客户端在两次明确用户授权后精确停止，容器保留；launch-v2完成当前源码/服务/gate/空闲/无额外8025客户端检查，启动四阶段顺序。commands/tp8-phase-baseline.sh SHAc8a8fd1da7b6812fc438f7cdac5c64d4fe7288db0d1afe0ee973c20eb8240e55，日志performance/entry-p1k/baseline.log；目前mixed-target预热，未产生测量结论。

P1K主场景6预热+3测量完整，全部1152请求成功；原生身份/输入/结果/SHA及稳态准入后3轮守护波动通过。总吞吐均值1968.2341、中位1968.3652token/s、相对极差0.1384%；P99 TTFT均值9031.90ms、TPOT63.8829ms、ITL58.3376ms、E2EL71918.42ms，最大守护极差0.3971%。review SHA569c4e8c...、run-record SHAd295bf4b...见state.yml；单实例基线事实，不是优化收益或正式关闭。

随后Prefill P1024/D1/C64/N128六轮预热全部native有效，但last3总TPS7316.4655/7016.9569/7505.7001，相对极差6.6800%超过冻结5%。零测量轮，native run-record failed，Skill结果incomplete；原顺序控制exit1并停止Decode/Mixed-short。源服务当前仍同实例、idle，抢占计数未增长。保留全部失败证据，不丢轮/延长预热/放宽阈值。plan-019新独立perf-003只执行此前未跑的两阶段，不重试失败Prefill；原正式P1K基线保持有效。
