# records-008-opt10-full-results opt10 全量端到端结果归档

记录日期：2026-10-22。状态：已归档五个场景完整结果；10月22日1K复测已完成4轮，用户明确确认稳态。记录更新完成，正式验收仍incomplete。类型为已有人工性能结果核验（checkpoint），没有执行新压测、profiler、源码修改或服务重启。

## 优化方向与本次范围

本次仅更新当前组合候选的端到端证据，不新增优化点。模型Qwen3-VL-30B-A3B-Instruct，mx-59/MetaX C550/TP2，生产容器`qwen3vl-p64k-opt-20261015`、端口9999、GPU6/7。独立记录身份用于隔离此前GPU0/1受控BCR，baseline_id中的no-anchor表示尚无当前五场景同契约anchor。

四个标准场景P1K/P4K/P16K/P32K均有完整CSV，额外保留P64K；全部D1024/C64/N128、finite batch。每轮CSV标注成功128，输入/输出token总量精确符合P*N/D*N，当前归档共24个完整场景历史轮次，另有4轮完整复测。没有将局部算子microbenchmark与本表混用。

## 当前保留实现和运行身份

- FlagGems保持gems-opt/c3c5f5ab2及sort整数直方图int32优化。
- FlagGems-vllm保持MetaX fused_experts_impl及内联分GEMM调优配置；当前MoE SHA为faeeead6…，外部JSON加载能力已按历史交付删除。
- Plugin通用FlagGems采样适配层直接调用FlagGems-vllm，保留不支持输入回退；不增加采样dispatch。
- 本轮采样局部直方图补丁保留，文件SHA `941bdc544401872327ee299aa0ab73387b43893e363f8c25b465fb607eb551eb`。
- maxbatched8192、maxseq64、显存比例0.91、FULL_AND_PIECEWISE/capture64、prefixcache关闭。当前取证时argv和环境与上述相符。
- 另一条main.py Flash Attention候选仅完成算子对照、未部署；沿用此前op007记录，不能把该实验计入opt10收益。

四仓当前revision、工作区状态、完整安全argv和关键文件hash均在外部导入清单。当前快照不是每个历史CSV轮次的严格运行绑定；不追认缺失的服务/客户端manifest、采样payload或设备历史。

## 完整场景结果

以下原样采用各CSV的SUMMARY；吞吐单位token/s，延迟毫秒，所有轮次仍在结构化记录中。当前表1K采用10月22日稳态复测第3–4轮SUMMARY，其余采用10月21日第3–4轮SUMMARY。旧1K第6–8轮SUMMARY2636.17单独保留为历史。

| 输入/输出 | 轮数 | 输出 token/s | 总 token/s | 平均 TTFT ms | 平均 TPOT ms | P99 ITL ms |
|---|---:|---:|---:|---:|---:|---:|
| 1K/1K | 4 | 1511.12 | 3022.26 | 1694.59 | 40.68 | 42.18 |
| 4K/1K | 4 | 1082.16 | 5410.82 | 4808.72 | 54.27 | 462.89 |
| 16K/1K | 4 | 374.66 | 6369.18 | 75029.02 | 79.66 | 642.51 |
| 32K/1K | 4 | 175.74 | 5799.26 | 223132.14 | 85.22 | 1006.30 |
| 64K/1K | 4 | 76.44 | 4968.68 | 588038.78 | 92.34 | 1559.34 |

每轮总吞吐=(输入+输出token数)/该轮端到端耗时。SUMMARY是逐轮指标的算术均值，不能拿SUMMARY token数除SUMMARY平均耗时要求得到同一数值。P99列是原SUMMARY对逐轮P99的平均，不是所有请求合并后的P99。P1K/P4K/P16K/P32K/P64K的输入+输出与输出比例分别为2/5/17/33/65，跨场景总吞吐不代表相同Decode能力。

## 波动和阶段视图

| 输入 | 全部逐轮总 token/s | 差幅 `(max-min)/median` | 原 SUMMARY 对应范围 |
|---|---|---:|---|
| 1K | 1773.42 / 1882.60 / 1933.44 / 2181.55 / 3079.71 / 3016.18 / 3027.93 / 1864.40 | 63.49% | Run6,Run7,Run8 |
| 4K | 5176.46 / 3717.15 / 5375.14 / 5446.50 | 32.78% | Run3,Run4 |
| 16K | 6353.73 / 6381.05 / 6391.66 / 6346.71 | 0.71% | Run3,Run4 |
| 32K | 5780.81 / 5813.00 / 5799.98 / 5798.54 | 0.56% | Run3,Run4 |
| 64K | 4959.51 / 4966.54 / 4968.34 / 4969.02 | 0.19% | Run3,Run4 |

全轮范围1K差幅63.49%、4K32.78%；16K/32K/64K分别约0.71%/0.56%/0.19%。这些是观测离散度，不是事后筛选出的稳态结果。此前diag006发现1K新batch M的采样JIT与进入/收尾慢窗口强相关；本次未新增归因测量，不能直接将该解释推广到每个长输入场景。

Prefill以TTFT为客户端代理，当前1K平均TTFT1694.59ms，随输入长度升至75/223/588秒；包括排队、编译和调度。Decode以TPOT/ITL为代理，长输入P99 ITL明显高于中位数，含Mixed干扰；本次没有纯设备阶段计时。Mixed采用完整finite batch总吞吐，进入/补入/收尾全部计入，不能把满batch日志峰值当整轮结果。

## 10月22日1K复测：稳态已确认

用户明确说明重新测试后性能已稳定。完整新文件4轮均成功128请求、输入/输出各131072token：

| 轮次 | 输出token/s | 总token/s | 整轮秒 | 平均TTFTms | 平均TPOTms |
|---|---:|---:|---:|---:|---:|
| 1 | 1505.65 | 3011.30 | 87.05 | 1704.70 | 40.82 |
| 2 | 1519.56 | 3039.13 | 86.26 | 1749.02 | 40.39 |
| 3 | 1522.10 | 3044.21 | 86.11 | 1696.18 | 40.37 |
| 4 | 1500.15 | 3000.31 | 87.37 | 1692.99 | 40.99 |
| 原SUMMARY（3–4轮均值） | 1511.12 | 3022.26 | 86.74 | 1694.59 | 40.68 |

四轮总吞吐中位3025.215，`(max-min)/median`=1.4511%。P99TTFT3582.65ms、P99TPOT41.82ms、P99ITL42.18ms来自新SUMMARY。当前1K状态更新为用户确认稳态，不再标记partial或稳态待确认。此确认范围是1K复测，不扩展为未执行的正式精度或全场景累计收益对照。

此前两轮partial快照与10月21日8轮波动数据均原样保留；新完整文件单独归档。旧组的JIT关联诊断不是本轮故意筛掉慢轮的理由；本轮4个实际值全部展示。

## 正确性、决定和下一步

前序数值、graph、TP2服务smoke和受控P1K B/C/R证据保留在父案例；本次只读核验CSV，不发正确性请求。正式GPQA仍按用户要求暂缓。

原始目录覆盖四个标准场景及额外P64K；这表示人工性能数据覆盖完整，不等于正式精度/性能验收通过。当前1K稳态已确认；正式验收仍缺少原生逐请求JSON/严格运行绑定、同配置全场景anchor/candidate/revert和正式精度gate。保持acceptance=incomplete；不计算历史各优化点收益相加或当前组合相对未优化路径的累计加速比。

当前实现保持不变。1K复测已完成并确认稳态，不再以缺少该确认要求重复测量；后续优化另立同配置可比实验，保留本次全部轮次。任何实现变更均另立实验，在独立容器验证数值/graph/E2E。

## 外部证据

原始目录：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt10`。
归档目录：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/results/csv/`，逐文件与原路径SHA一致。
导入清单：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/results/opt10-full-import.json`，SHA `ef8e4e33bcfe3bf2bcb16377fb6e1cc38fb509e0178d9fc009ddb484e7574b50`。
控制脚本：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/commands/import_opt10.py`，SHA `f45c122a7058f670f5efa4b77369e2bd509367968c7e23c6026c39ea9dac5d84`。

- `qwen3vl-opt10_1024in_1024out_c64_n128_20261021_143836.csv`：SHA `c6a504a730e432e42597973b61e38da8f08d45d38946d7a17320d627270dcce1`；8轮；完整SUMMARY。
- `qwen3vl-opt10_1024in_1024out_c64_n128_20261022_091827.csv`：SHA `4b821af17dfbd5904c6ba33d605c5a0a0f47b902b7883afc09f5de8710b6d07d`；2轮；partial。
- `qwen3vl-opt10_16384in_1024out_c64_n128_20261021_150247.csv`：SHA `98899b446d5abef3b80b15cf5f7e15b2c1b00022f8ac06ee3e05db84604c6026`；4轮；完整SUMMARY。
- `qwen3vl-opt10_32768in_1024out_c64_n128_20261021_150247.csv`：SHA `87ef269318b329c135df57172ecbb999076d13cc2a028e2d7554e294aff9014d`；4轮；完整SUMMARY。
- `qwen3vl-opt10_4096in_1024out_c64_n128_20261021_150247.csv`：SHA `75531c90ae922d6a73c551cd596845b3ce78cb866447ba7706142e7377343d7f`；4轮；完整SUMMARY。
- `qwen3vl-opt10_65536in_1024out_c64_n128_20261021_150247.csv`：SHA `9783918f3cce6a340f8b7698db0ab53ff8896b167abbee59e2873333bf55d72f`；4轮；完整SUMMARY。

前序：[采样局部直方图](../../20261021-qwen3vl-metax-p1k-opt9/optimize/op-005-sampling-local-histogram.md)、[opt10波动诊断](../../20261021-qwen3vl-metax-p1k-opt9/optimize/diag-006-opt10-throughput-variance.md)、[Flash Attention对照未部署](../../20261021-qwen3vl-metax-p1k-opt9/optimize/op-007-fa-main-native-micro.md)。


## 新完整复测的外部证据

- 原文件：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt10/qwen3vl-opt10_1024in_1024out_c64_n128_20261022_091827.csv`，SHA `acaa1957e6e093572f64cd1e900ceed90bb46d2281c57d110e2bf387716484b8`。
- 完整快照：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/results/csv/p1k-20261022-complete.csv`，同SHA；旧partial快照不覆盖。
- 确认回执：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-metax-opt10-results/results/opt10-p1k-confirmed.json`，SHA `b995ae48fa803b2236fe87ac3cbe839ea6d62f1873e7eb38f92d04dfa38c693e`。
- 控制脚本：远程案例 `commands/import_p1k_confirmed.py`，SHA `fc6efcddfa54bf50f4a85b5de851e959851bc02351d3cc114ad66470cc9e593d`。只读核验归档，未改动服务或源码。
