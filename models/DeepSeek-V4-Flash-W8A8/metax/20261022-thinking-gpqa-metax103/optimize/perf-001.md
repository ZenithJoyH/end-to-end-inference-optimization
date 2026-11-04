# perf-001 当前代码端到端性能基线

- 状态/决定：incomplete；分类：measurement-only；场景：P1K/P4K/P16K/P32K、D1024/C64/N128；阶段：Mixed及Prefill/Decode客户端代理。

## 优化方向与瓶颈依据

perf-001历史快照时间：2026-10-23 00:23:00（Asia/Shanghai）。该阶段诊断性基线：P1K 642.29 token/s、P4K 437.87 token/s；P16K首次预热MCCL OOM，P32K未执行，四场景整体incomplete。

用户指定mx-103当前DeepSeekV4容器，要求使用 `/public-flash/jinghao/deepseekV4/test/perf_test/vllm_perf.py`，关闭prefix cache测端到端性能。本次测量当前保留组合`mx59-acc003-5ea09be`。

## 优化内容与适用边界

使用用户指定vllm_perf.py的原run_once，源文件未改；COMMON_ARGS按冻结契约设置。D1024/C64/N128、finite batch、temperature0、ignore_eos、固定输入输出长度，prefix cache关闭。P1K/P4K恢复补测各固定4轮完整预热，末3轮输出吞吐spread≤5%后采集3个全新measured轮；全部保留，逐指标取三轮中位数，测量spread≤10%才称稳定。不重标旧warmup、不混合两实例、不丢弃较慢测量轮。

初始实例P1K/P4K的3轮完整预热因首轮过渡未达≤5%准入，均零measured轮，所有旧轮次保留。P16K warmup1先出现MCCL内部44MiB/512MiB分配失败，随后indexer query-sharding all_gather报DistBackendError；日志不证明精确触发shape或allocator根因。按停止规则终止精确客户端；旧模型进程随后自行退出。同容器恢复同配置服务后仅补测P1K/P4K。P32K因前序服务故障未执行，不能宣称已证明unsupported。

原首轮变慢原因未完成归因；挂载文件mtime与进程墙钟不一致，撤回用缓存mtime区间证明编译/调优耗时的推断。性能duration采用原生计时，不从文件mtime推算。

## 正确性与路径命中

历史170/198＝85.86%由用户确认精度通过，仍属于原attempt01与同一批198份输出；原strict153/198＝77.27%及其证据完整保留。恢复实例仅有新10/10最小回归和graph验证，没有新的完整GPQA分数或正式精度gate。

恢复实例 `deepseekV4-flash:perf001-restore02:1282425:1110226189` 同配置/源码/cache，容器未重启；7/7 FULL capture完成，C1 FULL14次、C8 FULL2次。性能期间FULL padded64单条日志最大count为124，只保留最大一条，不跨rank或累计快照求和。证据 `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/completion-runtime-evidence.json`，SHA `61f4dbd1439b1bb42f4aaa8231df7d216ffa557609963ee276bdba70bcd7cc13`。

prefix cache从启动参数和运行cache_config_info均确认False；测后服务健康、队列空闲、配置身份不变。image_lineage=verified、mount_parity=passed，三源码包校验通过。

## 性能效果

| 场景（D1024/C64/N128） | 状态 | 输出吞吐(token/s) | 总token吞吐(token/s) | mean TTFT(ms) | mean TPOT(ms) | mean ITL(ms) | mean E2EL(ms) | 批次耗时(s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P1K | completed | 642.29 | 1,284.58 | 6,682.63 | 92.98 | 92.98 | 101,747.69 | 204.07 |
| P4K | completed | 437.87 | 2,189.36 | 19,049.12 | 126.37 | 126.37 | 148,586.35 | 299.34 |
| P16K | failed_oom_incomplete | — | — | — | — | — | — | — |
| P32K | not_run_incomplete | — | — | — | — | — | — | — |

TTFT与输入吞吐是Prefill客户端代理，TPOT/ITL是Decode客户端代理，均包含网络、排队和调度；完整批次吞吐/E2EL表示Mixed，不能冒充纯设备阶段时间。E2EL是请求延迟，benchmark_duration是整批墙钟耗时，两者不同。

逐轮值、中位数/范围、完整4预热与3测量spread见[baseline报告](../baseline/README.md)，结构化值见[baseline/state.yml](../baseline/state.yml)。

## 决定、风险与回退

这是已保留组合代码的scenario-entry诊断性当前基线。没有未优化anchor、candidate/revert A/B或单优化消融，没有设定性能SLO/通过阈值，不声称加速倍数或完整正式性能验收通过。生产源码、权重、tokenizer均未新增修改。

保留当前源码与恢复服务。P16K/P32K不得用缩短请求、降低并发或删除场景替代成功结果；后续需单独定位MCCL内存失败，再按原场景验证。只有在相同冻结workload下重新测得有效数据，才更新对应状态。

## 外部证据

远端根 `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001`；最终summary SHA `94a776834acea80de320369c18e1bdd46edba8715e785447053cc1a689a9953a`。恢复plan/contract/preflight及每轮原生JSON、stdout日志的绝对路径和SHA保存在state.yml；原始输出、完整日志和脚本保留远端，不复制到模型目录。

- 恢复plan：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/plan.json`；SHA `569ed8ddf4be820db89a64dafac22266902d4a0c72cc0d52c872aad80845de0a`。
- 恢复contract：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/contract.json`；SHA `8f88f7a07af557d803c0afc71568b8d664c778c1a53c56d378ad8e76dec6469b`。
- 恢复preflight：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/recovery-v2/preflight.json`；SHA `6b72116fda32444b67e97376ce3684231af7b694686617988013fbc09da76dd3`。
- 原P16K故障日志：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/performance-001/failure-evidence/server-at-failure.log`；SHA `1a0d700d01da84a922a1813b7b845ac54c5cba1273aae1e90e46e0724d9b6aee`。
