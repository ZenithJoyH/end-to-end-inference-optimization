# 20261022-thinking-gpqa-metax103 / acceptance

<!-- e2e:summary:start -->

- 案例：20261022-thinking-gpqa-metax103
- 当前状态：three_p32_measures_complete_variability_incomplete_accuracy_historical
- 当前候选：mx59-acc003-5ea09be+fw-001+op-001
- 下一步：已完成本次32K三轮；稳态spread12.913%失败，精度与四场景gate未新增；不同源码的P16证据单列。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa-diamond-198-thinking | original_formal | exact_match,strict-match | 0.7727272727272727 | fraction | Historical frozen strict result; current acceptance uses user-confirmed170/198 |
| gpqa-diamond-198-thinking | user_accepted | bold_removed_exact_match | 0.8585858585858586 | fraction | Same198 outputs; bold normalization explicitly accepted by user2026-10-22 |

<!-- e2e:summary:end -->

历史170/198＝85.86%由用户确认精度通过，仍属于原attempt01与同一批198份输出；原strict153/198＝77.27%及其证据完整保留。恢复实例仅有新10/10最小回归和graph验证，没有新的完整GPQA分数或正式精度gate。

perf-001历史阶段性能验收为 **incomplete**：当时P1K/P4K完成，P16K MCCL OOM、P32K未执行；最新长场景结果见下方更新。没有四场景正式验收或A/B加速结论。详情见[baseline](../baseline/README.md)和[perf-001](../optimize/perf-001.md)。

<!-- long-context-repair:start -->

## 最新长场景修复与结果

| 输入 | 源码 | 输出吞吐(token/s) | mean TTFT(s) | mean TPOT(ms) | mean E2EL(s) | 整批耗时(s) |
|---|---|---:|---:|---:|---:|---:|
| p16384 | fw001_only_baseline | 191.64 | 70.752 | 260.926 | 337.508 | 683.963 |
| p32768 | fw001_op001_baseline | 109.52 | 140.343 | 439.042 | 589.336 | 1196.822 |

D1024/C64/N128、finite-batch、固定random长度、temperature0、ignore_eos；使用用户指定vllm_perf.py原run_once，prefix cache关闭。P16固定4预热+3测量；P32原4轮预热未稳态（零测量）全部保留，冻结恢复契约后再运行全新3轮预热（全部3轮spread≤5%）+3轮测量（要求spread≤10%，实际12.913%，未通过）。全部测量逐指标取描述性中位数，不丢第三轮；32K稳态性能结论为incomplete。TTFT/TPOT/ITL是含排队与调度的客户端代理。16K属于fw001-only，32K属于fw001+op001；没有同源码四目标正式验收或A/B加速结论。

32K每轮128/128成功，新恢复6轮合计768请求，无非法地址、OOM或服务ERROR；最终服务健康空闲。详细修复与逐轮值见[op-001](../optimize/op-001.md)和[fw-001](../optimize/fw-001.md)。32K结果：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/indexer-gather-oob-001/performance-recovery01/summary.json`，SHA `851fd8ff600e3fb412af18298f409352527c5d01670f117ec1c21373eeae805d`。

此结果补全用户要求的长场景运行，正式四场景验收仍incomplete；历史170/198＝85.86%用户接受结果保持原归属，没有新的完整GPQA分数或自动rebind。

<!-- long-context-repair:end -->
