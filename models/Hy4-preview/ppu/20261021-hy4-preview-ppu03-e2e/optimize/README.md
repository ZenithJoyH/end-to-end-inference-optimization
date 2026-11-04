性能优化与自动跟进保持暂停。用户已授权适配新多模态权重，且提供 day0 参考包；启动适配单独记录于 本地案例 `models/Hy4-testing-W8A8/ppu/20261023-hy4-testing-ppu03-startup/README.md`。旧 007 冻结证据不变。

007 C32 已完成并冻结：54轮全新测量、两原生比较passed，0丢轮；Prefill总吞吐12.599x，Mixed输出7.81187x，全部B/R指标最大漂移0.953954%。621项SHA及3份服务日志固定前缀独立复核passed。当前为007空闲before回退服务，候选未自动保留。008稳态profiling已准备本地契约、三阶段dry-run、流式校验器（17项）、预热准入（24项）及进程树资源采样/判定（27项本地检查）；实际watchdog、原生回执和生命周期尚待集成，未部署/采集。acceptance仍incomplete，无精度gate或C64正式结论。

006 的 C16 两组 B/C/R 共54轮全新测量全部准入，两原生比较passed：Prefill总吞吐93.743→1197.995→94.134 token/s（12.780x），Mixed输出10.894→70.786→10.659 token/s（6.497x）。最大基线/回退指标漂移2.373%。终态619项SHA及三服务日志前缀独立复核通过；006各服务随后已停止，证据保持冻结。007 C32结果见本页当前摘要。无新精度gate/C64正式验收；两库及batch2048不变。

# HY4 当前版本性能优化

历史[diag-001 日志诊断]（截至18:08，用户随后停止该压测）(diag-001.md)：用户已用统一默认YAML启动8010服务，正在运行P4K/D1K/C64/N128。日志显示Decode主导连续窗口243–250 token/s，Prefill加入时多次0–6 token/s；当前原逐行indexer仍在。优先减少Prefill组织开销，再独立比较2048/8192及KV、graph守护；8192尚未采用。本轮仅被动读取，不改库、不重启、不启动精度。

历史 fw001 已完成同参数 baseline/candidate/revert 三阶段共81轮无profiler测量。**Prefill、Mixed通过；Decode因TTFT波动超限为incomplete。** fw001对比收尾时已恢复原基线源码，fw001补丁仍仅为提案。当前另保留fw002最小修复：FGV45e14232一文件PPU参数补丁；FG3ba1d1d9、Plugin/vLLM内容及两个库安装版本不变。

TTFT专项已确认AsyncScheduler的两步异步队列会在请求尚未全部加入scheduler时提交前两批，随后长Prefill造成首token分组和早期Decode停顿；原warmup仅检查输出吞吐。六轮补采属于有界诊断，触发预热稳定性停止、0个测量轮，不能替换原incomplete结果；详细时间表、graph证据与当时新增的28.6s观察见[fw-001](fw-001.md#ttft-超限的详细定位ttft-diag-001)。普通启动器已恢复，启动/16rank三阶段replay/C8/分页通过，四包源码与两库不变；380个诊断证据文件已SHA备份。

后续[Mixed阻塞专项](fw-001.md#已确认的阻塞阶段与触发条件)已确认5行Decode TopK首次JIT：冷编译24.274s，TTGIR20.763s；未使用的NUM_ROWS constexpr造成不同cache key而IR/二进制相同。仅编译、0模型请求，服务/源码/两库不变，138文件已SHA备份；原Decode incomplete不变，不启动精度。

[fw-002](fw-002.md) 已通过本次请求的启动、16rank三阶段graph各>=2replay、9/9smoke+C8、两次2689token分页。全部16rank各2次精确389-token Mixed没有TopK编译，rank0墙时4.368/4.164秒；首次5行算子调用也已证明复用1行特化。只保留这一处补丁，不叠加fw001历史收益，不启动精度。失败v1探针与修正后v2均保留；247文件含静态日志快照已在原优化容器校验，跨容器备份未执行。

以下为历史fw001的C8/N8缩减场景、3测量轮中位数，不能替代正式C64/N128四场景或完整198题精度：

| 场景 | 指标 | 基线 | 候选 | 回退 | 判定 |
|---|---|---:|---:|---:|---|
| scout-p1024-d1-c8-n8 | 总token/s | 94.00 | 1211.14 | 94.96 | passed |
| scout-p128-d128-c8-n8 | 输出token/s | 44.60 | 79.33 | 44.51 | incomplete |
| scout-p1024-d128-c8-n8 | 输出token/s | 10.21 | 49.42 | 10.16 | passed |

Mixed输出为基线4.84倍，meanTTFT59.56→4.82秒，meanE2E100.10→20.55秒；回退输出10.16tok/s，较基线漂移约0.52%，支持该单文件改动的局部因果收益。Decode ITL中位数约94.4ms基本相同，不声称Decode kernel加速；所有不稳定轮保留。

[fw-001：单文件15行批量索引、完整B/C/R与边界](fw-001.md)；[env-001：profiling主机OOM与16rank流式证据](env-001.md)。完整终态739文件/17.13MB已逐文件SHA备份到评测容器。原profile trace仍留原证据根。

正式精度gate、完整P1K父场景和其余三场景未运行，提案尚未部署或通过最终验收。review-001规划已写state；本轮没有继续升级库、添加优化点或启动GPQA。

<!-- e2e:summary:start -->

- 案例：20261021-hy4-preview-ppu03-e2e
- 当前状态：user_paused_multimodal_adaptation_separate_case
- 当前候选：C32 BCR confirms same15linefw003; current live idle007revert before source; selectedcandidate not yet retained
- 下一步：Optimization and heartbeat PAUSED. User authorized Hy4-testing multimodal adaptation and supplied day0 ZIP; new startup tracked in models/Hy4-testing-W8A8/ppu/20261023-hy4-testing-ppu03-startup. No old trial restarts or refreezing.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| env-001 | diagnosis_resolved_and16traces_recovered | — | [env-001.md](env-001.md) |
| fw-001 | measured_milestone_gain_confirmed_proposal_not_promoted | — | [fw-001.md](fw-001.md) |
| fw-002 | retained_minimal_fix_only_no_formal_precision_or_performance_claim | — | [fw-002.md](fw-002.md) |
| diag-001 | prioritize_prefill_rowwise_overhead_then_single_variable_budget_comparison | — | [diag-001.md](diag-001.md) |
| fw-003 | Same15line candidate confirmed under006 and selected for next bounded scale trial; actual currentservice is before-source revert, no automatic newretained action | — | [fw-003.md](fw-003.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| scout-p1024-d1-c8-n8 | baseline | output_throughput | 0.09171123676562414 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | baseline | total_token_throughput | 94.00401768476475 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | baseline | mean_ttft_ms | 53344.21521250624 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | baseline | mean_e2el_ms | 53344.21497920994 | ms | diagnostic targeted milestone; passed |
| scout-p128-d128-c8-n8 | baseline | output_throughput | 44.6016774023528 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | total_token_throughput | 89.2033548047056 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_ttft_ms | 8789.069547434337 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_tpot_ms | 111.08593440405643 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_itl_ms | 111.08593563787551 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | baseline | mean_e2el_ms | 22922.00695676729 | ms | diagnostic targeted milestone; incomplete |
| scout-p1024-d128-c8-n8 | baseline | output_throughput | 10.211998833787057 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | total_token_throughput | 91.90798950408352 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_ttft_ms | 59557.19456530642 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_tpot_ms | 319.30519125101665 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_itl_ms | 319.3051937305713 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | baseline | mean_e2el_ms | 100098.61227648798 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | candidate | output_throughput | 1.1816024414034623 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | candidate | total_token_throughput | 1211.142502438549 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | candidate | mean_ttft_ms | 4141.578180133365 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | candidate | mean_e2el_ms | 4141.577976173721 | ms | diagnostic targeted milestone; passed |
| scout-p128-d128-c8-n8 | candidate | output_throughput | 79.32718171529551 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | candidate | total_token_throughput | 158.65436343059102 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | candidate | mean_ttft_ms | 769.8875191854313 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | candidate | mean_tpot_ms | 95.28993411304972 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | candidate | mean_itl_ms | 95.28993544586766 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | candidate | mean_e2el_ms | 12871.709151542746 | ms | diagnostic targeted milestone; incomplete |
| scout-p1024-d128-c8-n8 | candidate | output_throughput | 49.41562219497204 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | candidate | total_token_throughput | 444.74059975474836 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | candidate | mean_ttft_ms | 4815.86992170196 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | candidate | mean_tpot_ms | 123.81150091789281 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | candidate | mean_itl_ms | 123.81150287678686 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | candidate | mean_e2el_ms | 20546.791114262305 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | revert | output_throughput | 0.09263922177394125 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | revert | total_token_throughput | 94.95520231828978 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | revert | mean_ttft_ms | 52678.33825782873 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d1-c8-n8 | revert | mean_e2el_ms | 52678.33803431131 | ms | diagnostic targeted milestone; passed |
| scout-p128-d128-c8-n8 | revert | output_throughput | 44.51481029213962 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | revert | total_token_throughput | 89.02962058427924 | token/s | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | revert | mean_ttft_ms | 8805.955014424399 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | revert | mean_tpot_ms | 111.50169598697649 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | revert | mean_itl_ms | 111.50169780195552 | ms | diagnostic targeted milestone; incomplete |
| scout-p128-d128-c8-n8 | revert | mean_e2el_ms | 22966.67040477041 | ms | diagnostic targeted milestone; incomplete |
| scout-p1024-d128-c8-n8 | revert | output_throughput | 10.159049831941967 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | revert | total_token_throughput | 91.43144848747771 | token/s | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | revert | mean_ttft_ms | 59792.37898194697 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | revert | mean_tpot_ms | 320.73816844705846 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | revert | mean_itl_ms | 320.7381708624472 | ms | diagnostic targeted milestone; passed |
| scout-p1024-d128-c8-n8 | revert | mean_e2el_ms | 100620.5732692033 | ms | diagnostic targeted milestone; passed |
| fw003-v2-prefill-p1024-d1-c8-n8 | baseline | total_token_throughput | 92.8558169206098 | token/s | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-prefill-p1024-d1-c8-n8 | baseline | output_throughput | 0.0905910408981559 | token/s | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-prefill-p1024-d1-c8-n8 | baseline | mean_ttft_ms | 53894.21713864431 | ms | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-mixed-p1024-d128-c8-n8 | baseline | total_token_throughput | 89.97896833835337 | token/s | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-mixed-p1024-d128-c8-n8 | baseline | output_throughput | 9.99766314870593 | token/s | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-mixed-p1024-d128-c8-n8 | baseline | mean_ttft_ms | 61075.0647719251 | ms | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-p4k-sentinel-p4096-d32-c2-n2 | baseline | total_token_throughput | 58.73044285852542 | token/s | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-p4k-sentinel-p4096-d32-c2-n2 | baseline | output_throughput | 0.4552747508412823 | token/s | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v2-p4k-sentinel-p4096-d32-c2-n2 | baseline | mean_ttft_ms | 102935.36836840212 | ms | fw003 trial002 reduced milestone baseline only; no candidate/revert comparison |
| fw003-v6-prefill-p1024-d1-c16-n16 | baseline | total_token_throughput | 93.743186895077 | token/s | 006targeted C16/N16 Prefill baselineonly; no relativebenefit |
| fw003-v6-mixed-p1024-d128-c16-n16 | baseline | output_throughput | 10.89434205542067 | token/s | 006 C16Mixed newbaseline only, no relativegain |
| fw003-v6-prefill-p1024-d1-c16-n16 | candidate | total_token_throughput | 1197.994868293934 | token/s | 006C16 observedcandidate only, B/R/comparisonpending |
| fw003-v6-mixed-p1024-d128-c16-n16 | candidate | output_throughput | 70.78576718116794 | token/s | 006C16 observedcandidate only, B/R/comparisonpending |
| fw003-v6-prefill-p1024-d1-c16-n16 | revert | total_token_throughput | 94.1338253985241 | token/s | 006 targeted C16 Prefill revert only; final comparison pending |
| fw003-v6-mixed-p1024-d128-c16-n16 | revert | output_throughput | 10.658738272430385 | token/s | 006 targeted C16/N16 Mixed only |
| fw003-v7-prefill-p1024-d1-c32-n32 | baseline | total_token_throughput | 93.59706984841182 | token/s | 007 targeted C32/N32 baseline only |
| fw003-v7-mixed-p1024-d128-c32-n32 | baseline | output_throughput | 11.08142453527578 | token/s | 007 targeted C32/N32 baseline only |
| fw003-v7-prefill-p1024-d1-c32-n32 | candidate | total_token_throughput | 1179.2403557759826 | token/s | 007 candidate Prefill observation only |
| fw003-v7-mixed-p1024-d128-c32-n32 | candidate | output_throughput | 86.56665198700075 | token/s | 007 C32 candidate observed only; revert/comparison pending |

<!-- e2e:summary:end -->

用户NFS启动脚本已对齐当前配置，保留8010；capture最大512、dispatch及缓存目录与prefixOFF已显式设置。原文件备份、语法/参数比对通过，未运行脚本。见[fw-002](fw-002.md#用户启动脚本对齐仅编辑不启动)。

最新配置归并：安装版`vllm_fl/dispatch/config/thead.yaml`已承接dispatch与41项blacklist；脚本清除VLLM_FL_CONFIG/BLACKLIST覆盖，默认自动读取YAML。新鲜配置API验证与此前有效配置逐项相等，未重启/启动服务或精度评测；两个库内容未变。详见[配置归并记录](fw-002.md#安装版ppu-yaml归并仅配置不启动)。


## review-004：连续准入失败后的顺序调整

当前组合env031+fw002+yaml001；fw003未安装，累计端到端收益未知。001/002是同一服务、不同固定预热契约的两次失败，不能合并为独立重复。002三个可用缩减基线为Prefill总92.856token/s、Mixed输出9.998token/s、P4K输出0.4553token/s；Decode没有有效测量轮。TTFT/TPOT包含排队与阶段干扰，不能直接视为设备耗时。

下一轮先只读对齐002 r4/r5/r6的逐请求SSE/ITL、服务日志和已有资源记录；缺少同期信息时才另行冻结有界profiling。不能把001缓存mtime解释为002 r5多出的全部6.7秒。归因清楚后，再考虑同一15行候选的新契约B/C/R和模型graph/C8/分页验证；8192单变量比较继续后置。任何准入失败、数值/graph异常或无净收益即停止，不追加预热、丢慢轮或放宽阈值。本heartbeat没有执行新实验；完整精度和四正式场景仍未运行。详细停止条件和旧决定摘要在state.yml的review-004中。

本轮试验已终态冻结，heartbeat `hy4-ppu-03` 已删除；现有baseline服务保留，不继续自动测量。


## review-005：004同组合里程碑收益与保留验证

004以env031+fw002+yaml001为基线，仅增加同15行整数索引批量构造。四组各B/C/R均6warm+3measured，81新轮+27原002基线引用轮，预热及全部约定正式轮指标spread、守护和回退漂移通过；原生comparison四组passed。

|targeted工作负载|指标token/s|基线|候选|回退|变化|
|---|---|---:|---:|---:|---:|
|P1024/D1/C8/N8|总吞吐|92.856|1210.098|92.515|13.032倍|
|P128/D128/C1/N1|输出吞吐|11.3605|12.7370|11.3172|+12.117%|
|P1024/D128/C8/N8|输出吞吐|9.9977|49.3308|9.9305|4.934倍|
|P4096/D32/C2/N2|输出吞吐|0.4553|0.6415|0.4569|+40.913%|

主Mixed TTFT61.075→4.817s，E2E102.248→20.581s；C1 meanITL77.304→77.519ms无Decode内环加速证据。同15行已独立保留并完成新启动/graph/C8/分页验证，119项证据SHA通过；当前保留服务健康。下一轮先冻结P1K向C64扩展的可完成targeted里程碑及预算，必要时再做有界稳态profiling；不直接复用004数字，不调8192或两库，不跑GPQA，正式验收仍incomplete。详见[fw-003](fw-003.md)及state.planning_review_current。
