# batch-budget-004：1K批处理token预算对比

2026-11-06，用户要求只将max-num-batched-tokens从32768改为65536，保持其他参数不变，对比1K总吞吐。分类framework，mode=targeted，scenario=embedding-p1024-c64-n256，结论仅为本场景诊断；继承当前interface-fix-003三库源码，重新测基线，不使用旧镜像对比数据。

## 方向与冻结契约

从BGE-M3私有可写层不暂停地快照创建新隔离容器，GPU3/18340串行A32768→B65536→A2 32768，源GPU2/8000保持运行。挂载、源码、安装、权重/tokenizer身份必须核验相同；相对源仅实验端口/GPU/日志目录隔离，对比三组均相同。实际启动保持FP16/TP1/eager、maxlen8192、maxseq64、memory-utilization0.90、prefix/cache与chunked-prefill关闭及seed20261023。

每组使用原用户vllm_perf.py不改代码/CSV列，P1024/C64/N256、seed0、random range0、batch1、request-rate inf，原extra-body，原生outputlen1占位但实际生成0。固定5轮预热，末3轮吞吐span/median≤15%才准入5轮测量，全部测量轮保留；测量span/median≤15%，A/A2均值漂移≤15%。未准入组只保留预热诊断，不挑轮。总吞吐主值为测量轮算术均值；另外给中位数及sum(tokens)/sum(duration)。零失败，原生每轮256成功、262144输入token。5%为局部改善信号、P99回退守护15%，非用户业务SLO/正式达标。

## 正确性与边界

精度Skill baseline-sanity/minimal-regression，固定短文本C1/C8及token输入batch64×1024、batch2×8192；比较maxabs≤1e-3、cos≥0.99999、1024维有限/单位norm。BGE不适用生成式GPQA/Decode/TTFT/TPOT/ITL，用户要求保持eager且双向encoder不支持prefix cache；这些例外仅用于诊断，不签发正式gate。Prefill证据为包含排队/编码/pooling/网络的API端到端值，Mixed生成阶段不适用。维护版性能runner不支持embeddings，沿用当前已授权wrapper→vLLM原生openai-embeddings，不写新性能引擎。

## 执行与回退

每个启动/停止仅操作本轮隔离容器内带唯一phase标识的进程树并核验start ticks；不停止源容器或其他GPU。每轮超时120s/阶段1200s/readiness300s，OOM/错误停止推进，保留原始证据。记录GPU/CPU采样，未定位的主机竞争不当作已消除。只更改优化服务MBT，回退即恢复32768；源脚本修改待对比后记录，任何实际改动保存原文且仅替换一个值。

## 外部证据

远端根：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261106-bge-m3-mx59-mbt-004-c7d90a`。本地准备目录`/tmp/bgem3-mbt-004-20261106`；准备/控制脚本执行前复制到远端commands并冻结SHA。结果待执行。

准备工具commands/prepare.py SHA `2435b7dc4de5e4838f1a2384c84a78780e48c4b8bde59a5b26ca9685f4436c71`；完整commands文件SHA由commands/SHA256.json记录。首次本地打包缺少skill_bundle inspect输出文件，旧工具只输出stdout不写receipt；尚未执行远端prepare，已修正为保存stdout并上传缺失的两个bundle与SHA清单。执行 `python3 <case>/commands/prepare.py`，仅commit --no-pause、create/start本轮idle容器；门禁通过才对比。

上传shell命令因SSH参数引用方式错误在远端执行前失败，未创建case。改用保存的bootstrap.py经stdin传输；SHA `e5f9543d6832582ef93098f4f5ce505ff0c30542bdc5d2d347b3da94c638d052`，逐文件拒绝覆盖并核对SHA，再执行prepare。

prepare初次在copy2复制文件xattr时遇共享文件系统EIO，发生于commit/create之前；文件内容已复制但属性复制失败。保留回执，prepare-v2改为只复制内容并核对既有副本相同，新预检保存独立v2文件。SHA `1dee1310ed4428f223080a00e8c7a25915fe210ee273143c6d56cf5f1570016a`。

执行前复核加固停止逻辑：commands/service-v2.py SHA `68c11aecea684a5c337dd3ba05820fb9146844a569679989c16ef2b8152b9743`，对活跃/僵尸root均核对start ticks，精确phase环境标记识别本轮进程（含遗留worker），每次信号前重新核验身份与标记，拒绝PID复用。旧service.py保留未执行，运行只用v2。

最终控制器使用service-v3.py（v2另补最终phase残留扫描）及client-v2.py（SIGINT后核验wrapper及已捕获原生client子树确已退出）；均保留旧工具，不覆盖。SHA {'service-v3.py': '136eda84353edb87747b492c7cfc0b117ed8932bf04fb5a7f0cff164b5fc5f8c', 'client-v2.py': '763c1ac530a48a6b78a065f05d5463496607e8c874de0718468d6ee0f39b29c0'}。

准备门禁通过：快照镜像sha256:164565fd0aed8a01364bdcdf40571c72ff114f5beaa87b868cae6723178277ff，容器bge-m3-mbt-20261106-c7d90a，image_lineage=verified/mount_parity=passed/source_unchanged。commands/compare.py SHA `6311125213c18f24fa08adf2a89b048b131b418cb9de4bdc95c0c27934a559e2`已冻结并经本地三条控制流验证；执行 `python3 <case>/commands/compare.py`，使用service-v3/client-v2、已冻结原benchmark.py。

结果封存工具commands/finalize.py SHA `a60aeedf166e150582b3e2f859b4bac246a7deee785c3705cab4ea941d3b0834`：待全部比较结束后核对源身份/脚本及benchmark原文，汇总采样资源、写FINAL_REPORT/SHA256SUMS，不修改服务配置。

## 首轮结果与数值阻塞

A32768五轮预热通过，末3轮span/median=1.3425%；五轮测量120301.8466、107176.7513、103715.0133、118314.2104、122462.5110 tok/s，均值114394.0665，测量span超过15%冻结限制。B65536服务启动正常，身份/参数核验通过，但最小数值回归maxabs=0.0010302955、mincos=0.9999398247，超过冻结1e-3/.99999阈值。控制器停止推进，B未跑任何性能轮、A2未启动；GPU3已释放，源服务/文件不变且health200。不能计算两参数加速比。

问题ID batch-budget-004-numeric-001，调用accuracy-diagnosis；不放宽容差、不叠加其他代码/配置变化。原sanity在最终assert后保存，导致失败组原始输出未落盘，属诊断采样缺口；用独立工具修复为每组输出先保存再判断，不改原失败结果。新诊断顺序D-B-65536重复两次→D-A-32768回退重复两次，原C1/C8/batch64x1024/batch2x8192和token生成规则不变，另比较batch64第0样本单条与整批输出以定位batch相关差异。数值失败仅允许继续诊断，不允许恢复性能测量。

诊断工具commands/diagnose.py SHA `5f4204a006e15d46b6f20e0b280025ff18b4dd0f14d77ef2b5cf584c383b64a4`，调用已保存service-diagnose.py启动D-B65536/D-A32768；复用原HTTP函数、输入、环境/容差，保存完整vector后逐组判断，未运行benchmark或更改模型。原FP16路径不命中新加FP32算子；真实batch变化、native FlashAttention或GEMM舍入仅为候选原因，尚无算子级根因证明。

封存改用finalize-v2.py（SHA `cc3bdc225ba7e45ffb332af363d097f1d40281842864fd68ef6aa26eab0f3e7d`），额外合并诊断摘要与源health/GPU释放核验。原finalize.py尚未执行。无默认脚本/在线服务变更。

## 用户明确授权的诊断吞吐续测

用户回复“继续仅诊断吞吐，保留数值失败标记”。范围仅补B65536和A2 32768吞吐，保留同场景/5warm+5measured/15%原阈值及数值失败，不修改在线服务或默认启动脚本，不签发精度或性能收益gate。原A测量与已封存失败/复现证据不重写。续测原始产物位于同case的diagnostic-continuation；prepare-continuation.py SHA `fa8ed9b5343ac97f7d2a049053d4bf542f7eeeb7b1dba203a93d8c73249da332`只新建命令/身份副本并增加用户授权字段，其余测量契约保持。

诊断完成：B65536两次64×1024输出均复现同一差异，最大误差样本27；同配置重复输出逐位一致。回退32768的64×1024两次均与原A逐位一致。短C1/长2×8192保持一致；回退C8一次maxabs0.00024549、cos0.999998949仍通过。定位到大batch相关数值变化，未证明具体kernel机制或实际检索质量下降。原试验FINAL_REPORT.json和SHA256SUMS已封存；续测属于用户明确授权的诊断例外，精度失败状态不变。

续测入口diagnostic-continuation/commands/continue_perf.py SHA `bd7ce33622e7cd6bba4d075080280f2de60a8d7a570003adb71a80b73d3b8778`，重验原A全部round SHA与两次诊断输入/输出/参数身份，复用已冻结compare.run_phase，实际执行顺序B65536→A2 32768。数值回执B passed=false，整体numeric_gate_passed=false永久保留；新服务绑定同预算诊断记录，注明未重新发送数值检查请求，不伪造新通过回执。原生请求/长度/失败、预热与测量波动检查保持，未准入不取预热冒充测量。

续测封存工具commands/finalize-continuation.py SHA `4d4c820062fa8fac358dca64aac2ccd64839169c96b5a84eda3dcf7c9b4650d4`：执行结束后重新核对源服务/三库与原脚本不变、GPU3释放，合并原A与新B/A2的所有测量轮和资源观察，保留数值失败/用户诊断授权，不改生产配置。

65536初次续测5轮预热17389.74、17446.21、39747.47、40644.64、118145.74 tok/s，准入失败，不运行其measurement。为避免混用不同预热规则，准备统一扩展预热上限后fresh A/B/A，原A/B部分全部保留incomplete。只向本轮continue_perf.py精确argv/PID/start_ticks发SIGINT，由其原finally回收自己的client/service；stop-continuation.py SHA `f57ef1abb41fc23e341266ac26c89d50cbd43da96068a772168ae4ff75a6cc66`。停止原因是已冻结的预热未稳定，不是丢弃慢的测量轮。

统一稳态复测契约在新结果出现前冻结：steady-recheck新根；fresh A32768→B65536→A2 32768，不复用旧A性能。每组至少5轮warmup，末3轮span/median≤15%才准入，否则每次补1轮至最多12；全部warmup保留，最多一次追加重测，未稳定即incomplete。准入后5轮全纳入，仍span≤15%、A/A2≤15%，单轮120s/组1200s。benchmark本体、CSV、请求与模型参数不变，三组执行完全相同规则；数值失败例外继续有效。prepare-steady.py SHA `857a0ee2eaba5e29250d62588eb344dd4860b29182ecd967fd02b5de6e1f183f`。

统一复测封存工具commands/finalize-steady.py SHA `6a5da4fa7a24eea1307571998ccb6ef5fc80ddb1a96b67bda0fd134c0290ddd8`，只汇总新A/B/A及其资源，不将旧A作为新契约数据；源文件不变/环境释放与数值失败保留同前。

steady-recheck/commands/steady_recheck.py SHA `daaee2789b6cb15a4626754588071b3901c6b89ef687cd4fc631235c2e1e9c95`已冻结并语法检查。原controller已通过精确SIGINT退出，原client子树/service均回收，源health200/GPU3free。新工具复用原run_phase及诊断身份核验，只为三组统一增加有上限warmup；每个扩展单轮保留native_batch/native_round/global_round及每次准入回执，不复用原A测量。执行后不再自动改契约/追加尝试。

只读缓存设计核对：当前FG/FGV默认缓存分别取Path.home()/.flaggems和.flagdnn，SQLite配置库key含align32(M,N,K)+dtype；无FLAGGEMS_CACHE_DIR/FLAGGEMS_DB_URL覆盖时不随实验cwd变化。每个新服务进程内存kernel缓存重建。该静态证据仅排除“阶段日志目录改变默认调优目录”的假设，不能证明此前暂态具体由编译/调优造成；未修改或清空任何缓存。

用户明确要求“不用做回退组的实验了，停止吧”。立即停止本轮steady_recheck控制器；仅核验精确argv/PID/start_ticks后SIGINT，让原finally回收当前client/service。保留A/B已完成结果及回退组部分原始材料，不再重启/继续任何测量。停止工具SHA `7554d8a2303485072306a0b691aa719fa7988900ecebfb9d6643b3c6baf5f133`。

## 用户停止后的结果归档（2026-11-06）

按用户指令停止回退组，所有测试进程已退出，GPU3 已释放；隔离容器保留 idle。源 BGE-M3 服务、三库源码和默认启动脚本保持不变，默认预算仍为 32768。不再继续测试或数值定位。

A/B 均按同一契约完成 5 轮预热及 5 轮测量，全部测量轮保留。回退组 A2 在测量期间由用户取消，部分原始材料保留且不纳入对比。控制器原始状态 incomplete_error/failed 来自此次 SIGINT，不代表另一个运行故障。

| max-num-batched-tokens | 5轮平均总吞吐 token/s | 平均请求/s | 平均 E2EL ms | 测量 span/median |
|---:|---:|---:|---:|---:|
| 32768 | 119242.21 | 116.45 | 509.80 | 3.70% |
| 65536 | 119764.47 | 116.96 | 506.86 | 4.23% |

65536 相对 32768 的观测均值为 +0.44%，低于预记录的 5% 改善信号；未见明显吞吐收益。此处为已完成 A/B 的描述性比较，未完成回退漂移验证，不宣称完整 A/B/A 稳态验收通过。

逐轮总吞吐（token/s）：
- A-32768: 119807.37, 116471.22, 119317.67, 120898.51, 119716.26。
- B-65536: 119995.45, 116801.41, 121879.79, 119621.25, 120524.43。

总吞吐按每轮 262144 输入 token / 原生 benchmark 时长计算，再取全部 5 轮算术均值；embedding 无生成 token。原始脚本及 22 列 CSV 格式未改。数值失败标记保留（maxabs 0.0010302955，mincos 0.9999398247），不签发精度或正式性能 gate。

证据：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261106-bge-m3-mx59-mbt-004-c7d90a/steady-recheck/FINAL_REPORT.json`，SHA `9acaf13bea927850b23dd11d9552464bf38b8eca8723a0f34c97167392550631`；`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261106-bge-m3-mx59-mbt-004-c7d90a/steady-recheck/SHA256SUMS.json`，SHA `abff26575b09a047edab6551f72c5815b8a731b532798a8b65651f3f8fbef466`。停止回执：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261106-bge-m3-mx59-mbt-004-c7d90a/steady-recheck/commands/user-stop.receipt.json`。
