# op017：小M完整 GEMM2 参数组合

本轮状态：原生 targeted 比较 **passed**；P4K/D1K/C64/N128 输出吞吐 baseline 865.38 → candidate 898.64 → revert 871.04 token/s，候选相对基线 **+3.844%**，B/R漂移+0.655%。运行保留 **candidate**，当前独立容器 qwen3vl-p64k-opt-20261015 / 8111 / API995053。这是当前栈内单变量贡献，不是完整opt4恢复或项目最终验收。

## 用户范围与设计

用户明确要求实现完整旧GEMM2参数，保持采样回退、gems-opt和其他配置，正确性和graph后测端到端；随后明确同意保存部分结果并停止当前opt7测试。正式GPQA继续暂缓。只调整Plugin现有 `vllm_fl/configs/moe/metax/gemm2/E=128,N=384,device_name=metax.json`，复用现有标准JSON/阶段加载入口，无新增库代码、worker逻辑或环境开关。不改基础PR595表、GEMM1、dtype、路由、采样、gems-opt/sort、黑名单、vLLM、启动参数或其他服务。

适用本次MetaX C550 TP2 BF16，每rank w1=(128,768,2048)、w2=(128,2048,384)、topk8。M8..64的GEMM2采用BM16/BN64/BK128/group1/warp4/stage1；M7与M65边界保持其他M行为。文件匹配范围沿用原E/N/device/dtype规则，同键其他模型/芯片未实测。依赖已有op015阶段加载支持，不增加跨仓库改动。

## 数值和 graph

- CPU实际选择器M0..65536、3种配置dtype共589833项检查通过：全部GEMM1及G2/M范围外不变，BM与共享token alignment一致，JSON压缩到8行。
- BF16/FP16完整MoE共28组，含M0/1/7/8/32/48/49/63/64/65/544/545/1024/8192；8组数学参考、14capture/28replay通过。前后最大绝对差0.0009765625、数学参考最大绝对差0.0012547374，符合事先冻结容差，并非逐bit相同。
- B/C/R及最终保留服务分别核验双worker真实G1/G2配置；生产graph capture、各worker16replay及17个smoke/C8通过，KV容量562992，观察hooks均恢复后才测性能。当前服务绑定见manifest，旧API证据未重标。
- 原始image lineage和实时挂载一致性重新通过；最终保护源8000及四源码指纹校验通过，只有指定G2JSON允许变化。

## 无 profiler 端到端

模式targeted / performance_only，P4096/D1024/C64/N128 finite-batch Mixed；seed42、temperature0.7、ignoreEOS、固定长度，prefixcache关闭；每角色独立新服务1实例，固定3预热、末2轮TPS spread<=8%准入，随后2测量轮全部保留。阈值在B前冻结：TPS提升>=2%，P99 TTFT/TPOT/ITL回退<=10%，轮间spread及B/R drift<=8%。仍使用维护版原生runner/比较器，没有自建benchmark替代。

| 角色 | 两轮测量TPS | 中位数TPS | 轮间跨度/中位数 |
|---|---|---:|---:|
| baseline | 862.48, 868.27 | 865.38 | 0.668% |
| candidate | 897.37, 899.91 | 898.64 | 0.283% |
| revert | 870.00, 872.08 | 871.04 | 0.240% |

| 客户端守护指标ms | baseline | candidate | revert | C/B变化 |
|---|---:|---:|---:|---:|
| p99_ttft_ms | 18476.55 | 18475.50 | 18470.36 | -0.006% |
| p99_tpot_ms | 72.78 | 70.03 | 72.30 | -3.782% |
| p99_itl_ms | 584.43 | 583.38 | 583.31 | -0.180% |

所有原生轮次128请求全部成功。TTFT作为Prefill代理、TPOT/ITL作为Decode代理，均含排队、调度及Mixed阶段干扰，不是纯设备阶段时间。案例原P64目标仍保持开放；本轮独立冻结的P4K恢复诊断不替代P64基线或收益。本轮结论只属于P4K；P1K/P16K/P32K及额外P64未覆盖本次矩阵。

## 算子对照与剩余边界

合成路由单卡完整MoE graph交错3profiles/10blocks/50replay：M64当前stage1 0.600719ms，完整旧G2几何0.527316ms，共享几何stage3对照0.517507ms。M8/M32候选分别慢约1.27%/2.64%，M65相同。它证明stage与tile/warp组合有关、旧profile不是每个M都更快；不是端到端加速比。数值/graph通过不等于完整模型精度gate。

opt4的GEMM1、小/大M默认选参及Plugin版本差异仍存在，未归因给本轮；不叠加历史P64或采样收益。若继续恢复旧整体性能，下一轮再隔离GEMM1或P64阶段配置；当前用户明确要求其他配置不变，本轮不实施这些候选。

## 执行保护、保留和回退

用户授权保存opt7 P64部分结果并精确停止wrapper949467/client955098；已完成P4/P16 CSV及现有log未覆盖，累计metrics单独保存，不用其推算完整P64。该P64为incomplete。仅停止本任务优化API并依次前台执行B/C/R，没有影响其他卡或源服务。

自动审批拒绝了脱离会话的持久控制器（未获持续自动化授权），控制器从未启动；随后改为当前会话内逐步前台执行，本轮测试因此完成，没有绕过拒绝或创建automation。

当前保留candidate；若需回退，只恢复外部baseline-gemm2.json到上述单文件并重启本优化服务，再做实际参数/graph/C8核验；不要复用历史PID。完整候选、原表、差异补丁和命令均在远端commands/op017-gemm2-profile-20261017，具体SHA见state.yml。

## 证据与复盘

远端根：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。最终回执results/op017-final.json；性能results/op017-comparison.json及results/performance/op017-{baseline,candidate,revert}-01/run-record.json；数值results/op017-numerics.json；微测results/op017-microtiming.json；当前manifest：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/manifests/op017-retained-service.json`。准确SHA由state.yml绑定，原始日志/JSON不复制进Git。

knowledge_delta=refined：单独恢复stage不足以复现旧调优，完整几何也有M依赖；先CPU证明选择域，再做完整算子数值/graph与Mixed B/C/R。planning-op017-profile-result-20261017已更新下一轮排序；pr_readiness=experimental，未签发正式GPQA或四场景验收。
