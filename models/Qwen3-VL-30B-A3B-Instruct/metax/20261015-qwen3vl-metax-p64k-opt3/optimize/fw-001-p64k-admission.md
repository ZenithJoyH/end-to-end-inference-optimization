# fw-001-p64k-admission

running；framework；在diag001三阶段证据完成后，将server max_num_seqs从64改为8，并同步graph capture ceiling64→8，保持FULL_AND_PIECEWISE。客户端负载、所有算子选择、MoEJSON、sort和GPU memory utilization0.90不变。基于529824<8×66560=532480的容量边界，检验准入约束能否减少抢占重算；具体KV预算以每个服务实际启动证据为准。

milestone固定P65536/D1024/C16/N16，映射原始P64K/D1K/C64/N128，只缩减C/N；B/C/R各一进程、3warm+3measure，末3warmTPS spread≤10%、主TPS+5%、P99TTFT/TPOT回退≤5%、ITL≤10%、测量spread/B-R drift≤10%，每轮timeout1200s。较短P1K的5% warm门槛不移用于新P64K有限批次；本契约在观察本场景无profiler生命周期多轮结果前冻结，所有轮保留。

每个服务须healthC8、两worker graph和FG路径命中、源码/配置身份核验。先确定实际Attention provider，显式记录baseline/CUDA CG配置自动变化；不通过关闭FlagGems提速，不修改vLLM源码。正式模型精度仍按用户要求暂缓。

通过milestone后回到完整C64/N128验证原始场景；没有原始目标实测不报告其精确加速比。较小server maxseq仅是长上下文配置候选，短输入服务吞吐可能下降，未经跨场景验证不当成全模型通用默认。当前尚无通过比较验证的性能优化结论。

## 源码复核后的候选修订（尚未执行配置/测量）

原cap7方案在GPU实验前静态淘汰：当前Plugin _dummy_run的uniform-decode路径对sum(tokens)==capture_size有断言，不能保留capture64；且M7不在用户GEMM2 M8–64 JSON中。修订为max_num_seqs8，必要的graph capture ceiling同步64→8，保持FULL_AND_PIECEWISE并覆盖所有准入Decode batch。两个CLI字段为相关配置束，不能声称分别具有独立收益。其余参数、四仓库源码和所有FlagGems选择不变。

cap8还可能降低profiling阶段logits/sort最大临时分配峰值，从而增加有效KV预算；必须由实际KV容量与抢占增量验证，不能仅用静态容量数学证明收益。无profiler milestone仍按先前冻结P64K/D1K/C16/N16及所有轮次/阈值执行。旧v1控制脚本已留档但未执行，实际执行v2。

## 首次启动诊断失败与修复

v2新增观测代码在非配置上下文调用get_current_vllm_config，导致独立baseline启动失败；尚未产生任何性能轮次。保留失败日志，移除新增配置读取，恢复diag001已经通过的有界探针；Attention provider从启动dispatch日志获取。三个角色统一新探针和新产物前缀fw001r2，冻结的测量契约、产品源码和用户源服务均不变。实际执行v3。

## 无profiler基线进度（非最终比较）

独立baseline64/graph64的三轮预热TPS为67.2961515、67.2931603、67.4667957 token/s，全部16/16成功、每轮1048576输入及16384输出tokens；max–min/median约0.258%，低于冻结10%准入阈值。三轮后累计preemption增量6。后续三轮才计入稳态比较，当前不宣称候选收益。有效KV容量529824，Attention dispatch两rank均vendor.metax；健康/graph及四仓库内容指纹已通过。

基线6轮完成（3warm+3measure）：测量TPS 67.553、67.375、67.725 token/s，中位67.553，spread约0.52%；全部16/16成功。整个6轮counter delta为preemptions12、prompt6291456、generation98304，token总数与契约一致；此delta范围包含预热，不能当作仅测量3轮的精确隔离计数。候选正在独立容器启动；尚无候选收益结论。原生记录：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/performance/fw001r2-baseline-milestone-01/run-record.json`。

候选健康脚本因上一角色worker变为zombie但/proc仍存在，误选4条worker记录而失败。16条健康请求成功，未开始候选benchmark。v4筛选实际VLLM worker命令行且排除zombie；新健康产物使用-verified后缀，保留原失败证据和已完成baseline6轮，继续原冻结契约。候选实测KV容量529808（比baseline少16），因此“cap8增加KV预算”支假设未得到支持；仍须实测准入约束的性能作用。

控制脚本：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/prepare_fw001_v4.py` SHA256 `52daf8c940e3aba9fab859f187ebc50d72bad7ac0b8a7a0d8e62f92e14e42b14`。

控制脚本：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/run_fw001_v4.py` SHA256 `c3065d6f3fea85f574c2f65d7911fa5f09c546c467289754ad77f0c2ef10e1c7`。

候选三轮预热67.024、67.503、67.392 token/s，约0.71% spread，通过冻结10%门槛；全成功、每轮2preemptions。尚未计入候选收益比较，后续3轮为稳态测量。

候选3轮稳态TPS 67.461、67.780、67.907，中位67.780，相对baseline中位67.553约+0.34%，低于冻结5%门槛。整个3warm+3measure仍12次preemptions。当前回退服务已启动，完整原生B/C/R比较待完成；不保留cap8/graph8为已验证优化。下一项经源码复核简化为只增加memory utilization0.90→0.91，保持maxseq64/graph64及默认full-ISL准入检查。

## 完整结论

原生比较failed，唯一issue为主TPS收益不足5%；所有身份、warm/spread、TTFT/TPOT/ITL及B/R drift检查有效。P64K/D1K/C16/N16的B/C/R中位TPS=67.552845/67.780445/67.576739，候选+0.3369%，B/R TPS漂移约0.0354%。P99TTFT 196477.741→195659.632ms，P99TPOT112.71385→111.88898ms，P99ITL1547.247→1549.635ms。全部18轮16/16成功，token契约有效；每role6轮（含3warm）preemptions12。cap8/graph8已回退，不计入累计收益。

比较产物：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/fw001r2-milestone-comparison.json` SHA256 `f3d70d3d88a3519566eaf5b0caaf4111d55d756c28aaa064a49d4d1b111fc4e0`。正式模型精度仍deferred，本结果不属于原C64/N128或最终验收。
