# op-002-moe-unified-call：NV/MetaX 共用完整 MoE 调用

- 状态：retained（当前源码保留；端到端性能晋级 pending），代码和算子回归已完成；分类：framework（调用组织与维护性）；父场景：P4K/D1K/C64/N128。
- 用户明确要求在性能影响可接受、能力相容时统一Plugin调用层。沿用指定源容器的修改授权；当前服务未重启。

## 优化方向与瓶颈依据

op-001已经通过公共入口执行MetaX MoE，但仍与NV分支重复一份调用逻辑。基础API参数契约一致，MetaX另有caller-buffer扩展。直接去掉workspace复用的graph算子比较显示rows1退化25.790%，rows17退化5.279%，未通过预设的5%上限；rows64退化3.667%。因此保留复用，在统一调用体中按公共能力启用buffer，而不是把MetaX强行改成分配后copy。

## 优化内容与适用边界

- NV和MetaX共用一份参数传递、一处公共fused_experts_impl调用与一处结果处理。
- 平台只选择库命名空间：NV使用flag_gems，MetaX使用flaggems_vllm。具体平台实现、shape特化与kernel参数由库决定。
- 公共buffer能力在共享代码中查询，不直接导入_metax私有模块。支持时传入output和角色交换后的两块workspace；返回对象已经是output时不再copy。NV当前没有该扩展时仍使用原来的普通分配/copy行为。
- 保留MetaX无LoRA、无expert-map、同dtype FP16/BF16、SiLU、非上述量化路径的边界；共享buffer能力也限制于未量化SiLU无expert-map。NV既有量化、scale、bias、router-weight参数保持传递。
- 公共入口缺失时保留此前的staged选择；旧库没有buffer扩展仍可调用普通入口。已选中实现执行错误不捕获后重试。

没有修改Gems源码、服务配置、模型权重或其他平台backend。公共接口签名和NV参数mock不能证明NV全硬件能力已通过；未扩大MetaX量化/EP/LoRA支持范围。

## Buffer 复用的来源与具体操作

修改前的容器代码已经具有 caller-buffer 能力、`supports_fused_experts_workspace` 判断及下表中的映射，原始 Plugin 文件 SHA 为 `5bb687951274c01d69b41391898cfc3a9991d0afb1a2d643fff6545af1b56532`，全文保存在 `/private/tmp/qwen36-moe-public-api-20261013/sources.json`。因此，本任务没有新增库侧 buffer API，也不能把这项既有能力记为本任务原创优化。op-001 将原先私有 MetaX 调用改为公共入口并保留复用；op-002 进一步把 NV/MetaX 调用体统一，并验证保留复用的必要性。

| 公共 `fused_experts_impl` 参数 | Plugin / vLLM 传入对象 | 用途 |
|---|---|---|
| `out` | `output` | 直接写入已有输出，避免另建输出及末尾复制 |
| `workspace13` | `workspace2` | 完整 MoE 的第一、第三中间结果共用存储 |
| `workspace2` | `workspace13` | 完整 MoE 的激活结果存储 |

两块 workspace 的名称不能直接一一对应：vLLM modular 路径和库内完整 MoE 对中间结果的尺寸、生命周期分组不同，故保留上述交换映射。复用只在现有支持边界内启用；`supports_fused_experts_workspace` 检查 shape、dtype、device、layout、容量及允许的内存别名关系，是 buffer 兼容性检查，不负责平台或 kernel 特化分发。

能力检查通过时，公共调用收到 `out=output, workspace13=workspace2, workspace2=workspace13`；返回值就是 `output` 时跳过 `output.copy_`。检查不通过或库没有该 helper 时，同一公共入口不传这三个可选参数，取得返回张量后复制到 `output`。不捕获算子执行异常再重试。所谓“旧 API”指缺少 caller-buffer 扩展的代码接口：目标 FlagGems-vllm Git HEAD `05d0ff0547dc9cc7cce18f47c6f57cc9d04f0777` 的接口与容器已有扩展不同，不能单靠包版本号 `0.1.0` 判断。

删除复用的对照中，普通分配/复制相对复用的 graph 算子延迟在 rows=1 增加 25.790%，rows=17 增加 5.279%，rows=64 增加 3.667%；这是目标硬件和所列 shape 的局部证据，不是端到端收益。最终共享调用仍保留复用，数值、输出别名及 graph capture/两次 replay 验证见下节，精确补丁和 SHA 防护回退入口见“外部证据”。

## 正确性与路径命中

应用前21项候选CPU路由测试通过。应用后29项Plugin路由/adapter契约通过，包含NV命名空间隔离、量化scale参数、通用buffer复用和避免重复copy；2项真实C550 workspace/output别名数值测试通过，包括graph capture与两次replay。4项小形状functional公共入口/staged数值与graph测试也通过，另8项未选择；合计35项回归通过。

硬件测试在空闲C550设备4执行；模型服务的设备6/7未用于本次测试。NV硬件、TP2完整服务graph、正式模型精度和端到端性能未测，不签发正式gate。

## 性能效果

复用现有benchmark/test_moe_workspace.py及其Benchmark计时框架，E256/H2048/每rank中间维256/top8/BF16，使用同输入对照。普通分配/copy与复用的初始比较用于否决删除复用，不作为最终候选加速比。

最终比较将原生Benchmark两个函数绑定为准确op-001 Plugin.apply和准确共享调用候选，两者使用实际Plugin依赖和相同TritonExpertsFL实例。下面是预先声明的热身后，三个独立进程的每shape中位graph延迟；包括所有七组，不选最好轮。

| token数 | 原调用（ms） | 共享调用（ms） | 延迟变化 |
|---|---:|---:|---:|
| 1 | 0.038536 | 0.038506 | -0.079% |
| 17 | 0.252593 | 0.252218 | -0.148% |
| 64 | 0.486812 | 0.486359 | -0.093% |
| 512 | 0.657534 | 0.657379 | -0.024% |
| 2048 | 1.269545 | 1.267772 | -0.140% |
| 4096 | 2.344866 | 2.343249 | -0.069% |
| 8192 | 5.364775 | 5.371432 | +0.124% |

全部变化在−0.149%到+0.125%之间，两侧进程间波动均小于1.54%，满足预冻结的各shape回退与波动不超过5%判据。这只支持算子graph调用没有明显退化，不宣称端到端加速。

按阶段看，rows1/17/64是Decode batch形状代理，rows512/2048/4096/8192是Prefill token形状代理；没有模型Mixed调度/网络证据，不把算子延迟冒充TTFT/TPOT或正式场景结果。

## 决定、风险与回退

保留共享调用候选和通用workspace能力。服务未重启，当前进程仍使用其已加载函数；下次启动加载最终代码。

测量记录保留：

1. 分配/copy候选：三进程200ms、七组齐全，rows1/17超过5%，否决删除复用。
2. 共享调用v1：三进程200ms，差异在±0.22%内，但rows8192候选波动5.015%略超5%，记incomplete，不删除任何轮。
3. v2：预算1000ms导致重复graph capture图过大，首进程180s超时，测试退出，无完整JSON，记incomplete。
4. v3：执行前改成300ms、一轮预先声明热身进程加三个测量进程，仍覆盖全七组和两路径，维持5%判据；全部通过。热身原始JSON单独保存，v1/v2未纳入聚合，也未改判。

Benchmark探针导入时出现原有MACA patch循环导入提示，两侧环境相同；公共完整MoE仍执行并生成全部有效结果。此证据不等于完整服务初始化验证。PR准备仍为needs_revision；NV硬件及工程lint未测，不提交/推送。

## 外部证据

外部本地目录：/private/tmp/qwen36-moe-unified-call-20261013。精确旧源码、候选、命令、原始JSON、全部日志、摘要和SHA在该目录，evidence-manifest.json为校验入口。

- 旧源码SHA：4466f9b6811a363951a2603a0629fbf3748f9201b9127c8db9a6f66e88cc3dda。
- 最终源码SHA：926a55449a14e3fbde52c6a999b4e537a92a02ab367d05e812199eb91706032e。
- 本轮完整patch SHA：9a4bf3e44613a9d7af9ef7361f8f0d6cde39ee8b638f857a2438490974ccb7fd。
- 分配对比原生目录：容器/tmp/qwen36-moe-call-compare-20261013-2k22udaa。
- 共享v1目录：容器/tmp/qwen36-moe-unified-graph-20261013-g09d8dja。
- v2超时目录：容器/tmp/qwen36-moe-unified-graph-20261013-xajctbox。
- 最终v3目录：容器/tmp/qwen36-moe-unified-graph-20261013-h2_9ljj0，graph-round-0是预声明热身；graph-round-1/2/3是测量。
- 回退脚本：外部目录rollback_remote.py（未执行），SHA防护后只恢复本轮两个目标文件至op-001；拒绝覆盖后续修改。

这些原始材料在临时外部位置，长期留存应移入用户指定的持久目录。没有新端到端证据，不修订SOP或宣称正式验收。

后续只读启动路径核验：当前start-model-flagos.sh为BF16/TP2且模型无量化；默认use_flaggems=True的OOT选择器会选TritonExpertsFL，再进入公共flaggems_vllm.fused_experts_impl。库公共函数实际绑定MetaX fused_moe文件。完整experts快路径不直接受分段算子白名单控制；缺少fused_moe OOT注册时，custom_ops会把上游oracle替换为Plugin选择器。检查时源容器仅有shell、未见vLLM服务进程，现有service.log属于此前实例，因此这是启动后代码路径预测，不是当前活跃请求命中证据。

## 用户补交端到端结果后的复盘（2026-10-13）

复盘 ID：`review-001-user-e2e-variance`。这是对用户已完成测量的只读分析；本轮没有运行新 benchmark、切换代码、重启服务或采集 profiler。使用本地推理优化规划复盘技能归纳冲突证据；性能评测 Skill 未启动新测量，不把旧 CSV 补造成正式回执。

用户提供的候选目录为 `/public-flash/jinghao/qwen3.6-35B/test/perf_test/benchmark_results/qwen36-35B-begin-novllmconfig-addattention-fusedmoeopt`，文件时间标识 `20261013_171526`。最邻近对照为同一根目录下的 `qwen36-35B-begin-novllmconfig-addattention`，时间标识 `20261013_145815`。两侧均 P1K/P4K、D1024/C64/N128；每轮 CSV 记录 128 成功请求、131072 输出 token，候选 perf.log 六轮均 failed=0。

候选 service.log 记录 17:12 启动及相符的 served name、BF16/TP2、8192 token budget、64 seq、关闭 prefix cache 和 FULL_AND_PIECEWISE；采样为模型配置 temperature=1、top_k=20、top_p=0.95。本轮容器进程检查发现相符服务正在运行，磁盘 Plugin SHA 仍为 `926a5544…`。这更新了前文“未发现服务”的历史时点，且不改变“Agent 未重启服务”的事实。缺少两侧测量时完整源码指纹、运行中函数/实际 buffer 接受计数及回退轮，因此仍不能签发调用改动的因果结论。

### 全部逐轮结果与汇总口径

原始 runner 使用 `valid_runs = all_runs[SKIP_FIRST:]`，现有 SUMMARY 是 Run2/Run3 的算术平均。下面保留全部轮次，不能事后删掉候选 Run2，也不能把对照 Run1 自动解释为预热。

| 场景 | 版本 | 三轮耗时（s） | 三轮输出吞吐（tok/s） |
|---|---|---|---|
| P1K | addattention | 181.20 / 131.45 / 132.10 | 723.35 / 997.10 / 992.20 |
| P1K | fusedmoeopt | 115.30 / 114.54 / 115.22 | 1136.83 / 1144.38 / 1137.57 |
| P4K | addattention | 289.95 / 143.73 / 148.06 | 452.06 / 911.95 / 885.26 |
| P4K | fusedmoeopt | 143.84 / 250.01 / 143.17 | 911.22 / 524.27 / 915.47 |

| CSV SUMMARY 指标 | P1K 对照 → 候选 | 变化 | P4K 对照 → 候选 | 变化 |
|---|---|---:|---|---:|
| 输出吞吐（tok/s） | 994.65 → 1140.97 | +14.71% | 898.61 → 719.87 | −19.89% |
| 批次耗时（s） | 131.77 → 114.88 | −12.82% | 145.89 → 196.59 | +34.75% |
| 平均 TTFT（ms） | 4344.35 → 1878.64 | −56.76% | 4952.81 → 21972.47 | +343.64% |
| 平均 TPOT（ms） | 60.09 → 54.24 | −9.74% | 66.19 → 74.34 | +12.31% |
| 每轮中位 ITL 的平均（ms） | 53.15 → 52.63 | −0.98% | 55.94 → 55.39 | −0.98% |

该表沿用 CSV 的汇总定义；中位数和 P99 的轮均值不是合并样本的总体中位数/P99。若诊断性地纳入全部三轮，P4K 算术平均输出吞吐为 749.76 → 783.65 tok/s（+4.52%），平均耗时为 193.91 → 179.01s（−7.69%）。它与 SUMMARY 的方向相反，只用于显示对慢轮位置的敏感性，不用来替换原 SUMMARY 或声称收益。没有稳态准入证据，任一口径均不足以确认稳定加速/退化。

### Prefill、Decode、Mixed 视图

- Prefill/请求准入：候选 P4K Run2 的平均 TTFT 为 38995.81ms，Run1/3 为 5082.60/4949.14ms。17:27:01 的服务日志记录 running=6、waiting=58；17:28:51 才达到 running=64、waiting=0，期间 prompt throughput 多为 819–3277 tok/s。正常轮部分相应窗口为约 17202 tok/s。不同窗口不能计算严格 Prefill 加速比，但足以将异常收敛到长时间的 prompt 填充/排队区间；不把 TTFT 当作纯 kernel 时间。
- Decode：P4K 候选三轮中位 ITL 为 55.35/55.42/55.37ms，没有与批次耗时相同幅度的普遍增长；17:29:01 后生成吞吐恢复约 1150 tok/s。Mean TPOT 仍显著退化，不能忽略 Mixed 中的长停顿。中位 ITL 稳定只说明大多数生成间隔相近，不排除少数长停顿、Prefill 干扰或数据相关路径。
- Mixed：候选中途慢轮和对照第一轮慢轮都存在，收益方向取决于汇总口径。当前证据支持“端到端收益未证实，P4K 存在严重波动”；不支持“buffer 复用新增后导致波动”，也不能排除 MoE 路径相关问题。

### 修正收益归属与下一步顺序

当前库的 `fused_experts_with_workspace` 只是把 buffers 传给 `fused_experts_impl` 的包装；修改前后仍执行同一完整实现并复用相同 buffers。本任务的公共入口/共享调用重构没有新增 buffer 复用。因此先前 rows=1 的 25.79% 结果是“故意移除既有复用”的算子代价，不是这次重构相对原代码的加速，更不是端到端收益。当前保留决定仅表示源码仍在、算子回归通过和调用维护性改善；端到端性能晋级 pending。

优先顺序如下；均未执行，不能累计或预测精确收益：

1. `framework` / Prefill+Mixed：先用精确原始 Plugin SHA `5bb68795…` 与当前 `926a5544…` 做 A/B/A，两侧均保留 buffer，排除调用重构本身。目标 P4K、P1K 为哨兵；性能 Skill `checkpoint`，准备独立优化容器、同采样/graph/设备、统一稳态准入及全部轮保存，并执行最小正确性。先解决不稳定，若回退后仍存在慢轮则不得归因于该重构；波动超预冻结界限时停止晋级。该次的端到端阈值须在新测量前冻结，不能复用算子阈值追认旧 CSV。
2. `framework` 或具体算子待定 / Prefill+Mixed：在可重复慢轮上用 Profiling Skill `capture/analyze`，覆盖 TP 两 rank，区分主机/编译/capture、调度、MoE fallback、Attention/GDN 或资源争用。没有 trace/设备同期证据前不选定 kernel 根因；profiler-on 耗时不纳入正式性能收益。
3. `framework` / buffer 生命周期：若仍需决定删除兼容/复用逻辑，再单独建立“公共入口 + 复用开/关”的同配置端到端对照，使用性能 Skill `targeted`、最小数值/别名/graph 回归，并以 P4K Mixed 和 P1K 守护项判定。不可把这项消融与第一项重构回退混为同一变量，也不可凭既有单 token microbenchmark 直接决定服务收益。

下一次复盘触发：可比较 A/B/A 得出结果、确认慢轮 trace 归因，或一次回退仍不能解决波动。正式精度和最终四场景验收仍未执行。历史 `qwen36-35B-begin` 目录本轮已看到新的 10-13 CSV，而原 gap 报告引用的 10-10 文件不在当前列表；旧报告保留旧路径/SHA，不把新目录内容静默当作同一基线。

本轮本地外部证据：`/private/tmp/qwen36-moe-e2e-review-20261013.VqBEzh`。`results.json` 保存十份当前 CSV 原文、路径/SHA 和筛选日志；`analysis.json` 保存全部轮与口径计算；`runtime-audit.json`、`path-check.json` 保存限定代码/日志/进程核验。原始材料仍在临时目录，项目只保留摘要与校验。当前正式判定：`performance_status=incomplete`，无因果归属、无正式 gate。
