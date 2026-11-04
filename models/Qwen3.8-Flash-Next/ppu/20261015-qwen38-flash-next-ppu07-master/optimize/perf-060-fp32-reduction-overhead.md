# perf-060：FP32 TP归约补丁性能回退核验

## attempt004终态：有效对照完成，FP32有小幅C64代价

终态记录写回后，产品工具已确认原heartbeat `qwen3-8-ppu07-gpqa-c64`为**PAUSED**，不再自动继续测试，健康FP32服务保持运行。

2026-10-21 22:11:29原controller自然完成并退出；22:31 CPU终态审计完成。9组原生run、132轮（固定8warm＋3measure/每case）、6600benchmark＋40smoke＝**6640请求/4启动/0推理重试**。无FIRST_ERROR，未补跑或挑轮，source/安装Git/全部依赖未变。所有12项case-role预热检查通过，维护比较器核验的测量指标spread最高3.16%、B/R主指标漂移最高2.13%，均在预冻结10%门槛内；这是有界工程比较，不是统计置信区间。

### 吞吐：各服务3个测量轮中位数

| case（P/D/C/N） | 单位 | BF16 baseline | FP32 candidate | BF16 revert | FP32相对baseline | revert相对baseline |
|---|---|---:|---:|---:|---:|---:|
| Prefill 1024/1/64/64 | request/s | 2.492407448 | 2.466195736 | 2.494338012 | −1.05% | +0.08% |
| Decode 128/128/64/64 | token/s | 701.946719 | 690.816413 | 699.165110 | −1.59% | −0.40% |
| Mixed 1024/128/64/64 | token/s | 242.995276 | 240.180464 | 243.184900 | −1.16% | +0.08% |
| Mixed哨兵 1024/128/8/8 | token/s | 103.950211 | 106.038686 | 106.165017 | +2.01% | +2.13% |

C64显示约1%–1.6%的FP32吞吐代价；Mixed baseline测量spread2.71%，候选0.34%、回退0.44%，不能把−1.16%说成高精度普适常数。C8的BF16回退同样变快且与FP32接近，**不把+2.01%归因为FP32加速**。每角色只有1个独立服务实例/3个测量轮，不能外推长期容量、原D1024或其他三个正式输入场景。

### 延迟守护：原生逐轮P99的中位数，不是全体请求合并P99

| case | p99 TTFT(ms)：B / C / R | FP32变化 | p99 TPOT(ms)：B / C / R | FP32变化 |
|---|---|---:|---|---:|
| Prefill C64 | 25664.153 / 25936.411 / 25645.901 | +1.06% | 不适用D1 | — |
| Decode C64 | 3754.835 / 3802.200 / 3769.324 | +1.26% | 71.242 / 72.723 / 71.604 | +2.08% |
| Mixed C64 | 26032.092 / 26259.468 / 25947.703 | +0.87% | 240.100 / 242.974 / 239.904 | +1.20% |
| Mixed C8 | 3639.981 / 3656.600 / 3619.260 | +0.46% | 69.447 / 68.037 / 67.971 | −2.03% |

三项维护比较回执均为`failed`：预冻结契约要求吞吐与p99延迟零回退，因此这些小幅代价仍不通过；**不是执行失败、预热失败或证据incomplete**。没有改阈值“转通过”，没有自动回退生产数学。原始比较和本轮CPU重验JSON逐字相同：prefill SHA`54f145e728b1e20533fbb9e6a0a2fe04e97bbb41c8219a926f77abab5ec6de4b`，decode `f2c3fbf0e6af887e72e351e24da0e4a32c061aa44bba846bc6c3bfa5696e9e66`，mixed `aff8adc3124cc4feac7b960ee506f01c3acf8b387179787b25556a2ff3b9076d`。

### 正确性护栏、路径与最终服务

四角色各10条同doc2短护栏全部HTTP200/非空final/stop/think-end248069/EOS248046/诊断B，完整raw SHA、prompt321与token usage一致；每角色各自两C1全序列相等。final两C1为277/277 tokens，C8按seq为632/632/581/581/632/632/632/636。候选两C1为570、final为277，属于不同实例已保存事实，**不宣称跨重启token确定性或未测完整GPQA精度通过**。

本轮32份8rank编译图已冻：B/R各rank98BF16归约，C/final各rank96FP32＋2BF16；两类capture均7/7、各角色FULL≥2，final原生统计FULL1162（含batch8）。编译/launch继承与native graph证据不冒充每rank逐步kernel trace、完整状态/logits或所有层现场。

最终8010为FP32 `/opt/vllm-plugin-FL`，API3852394/start530581998/argvSHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`，health200/running0/waiting0/preemption0；保留op061v2/i64/randn/QSA M16/PLE CTA/原黑名单和固定调优。仅按用户授权恢复后保持运行，不停止、不再重启。不访问8035、不GPQA、不提交推送。无新formal gate或四场景性能结论，后续需用户方向。

### 原始证据与CPU终态冻结

本轮绝对根即下方E：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/perf-060-fp32-reduction-overhead-20261021/attempt-004-op061-warm8`。

- `FINISHED.json` SHA`cf5e280870f65d3ae3e1ad70948ec673a99180f2727077a3ab3e812f45b09a33`；`comparison-summary.json` SHA`66d78fc01740c09e9fbf2b9fe23b3af29fbf6f109ea9b78c9d6ca6c3f84d8ce8`。
- `performance/<baseline|candidate|revert>-<prefill|decode|mixed>-001/run-record.json`及全部r1–11原始结果/validation；`<role>/reqNNN-*`保留40份原始HTTP/token/请求/headers/result。
- 一次CPU审计`terminal-audit-op061-001/summary.json` SHA`41c5ddc4cd784ca09d062a4135b0944613d3553cf749a83d63a7fa2ff053484f`；`snapshot-manifest.json` SHA`89570133f9947c37e47476396100f5dbc3e87fcc75fb2d6fa311fde2ddb93dda`，772份既有文件/日志已存在前缀与32份编译图保全，全部复制SHA通过，不声称运行中服务未来追加日志已冻结。
- `terminal-audit-op061-001/AUDIT_FINISHED.json` SHA`448e9bcb4954eff894a42c37a1465eeb04ab9fba75fc73c262ad7b453497eb02`；审计0新模型请求/0GPU测试/0服务动作，三项维护比较重验一致。该实验已结束，heartbeat随后暂停，保留健康FP32等待方向。

## 当前授权：attempt-004-op061-warm8（2026-10-21）

用户明确允许BF16 baseline→FP32 candidate→BF16 revert→final FP32，最多4启动、8warm＋3measure。模式`performance targeted / performance_only / steady_state`与`accuracy minimal-regression`；仅比较attention/MoE TP累计精度，权重/激活仍BF16。不访问8035/物理0–7、不全量GPQA、不提交推送，不签formal gate。

新远端根为`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/perf-060-fp32-reduction-overhead-20261021/attempt-004-op061-warm8`。各角色统一op061 v2 Gems（alignment SHA`a0ac9a7e1d7417fecc639765f2c74b08941b6497adbc8b2d41bcdd60293e0959`）、i64/randn、QSA M16、PLE i64+CTA、normal_/index_select黑名单、pin047固定调优，无模型诊断hooks；旧失败数据不混入。保持安装Git，BF16仅新真实私有副本model.py不同，四角色独立空cache在`/opt/qwen38-perf060-op061-warm8-20261021`，不删旧cache。

复用attempt003冻结维护版runner/比较器/HTTP collector，workload不变：Prefill P1024/D1/C64/N64、Decode P128/D128/C64/N64、Mixed P1024/D128/C64/N64及C8/N8。parent `p1024-d1024-c64-n128`，均finite-batch缩减探针，其他正式场景未测，TTFT/TPOT仍含调度/网络。每case固定8warm＋3measure(r9–11)，末2warm主spread≤10%、全部3measure spread≤10%、B/R漂移≤10%，每轮600s/readiness40min。保留全部轮，不追加或放宽门槛。

各角色先10短doc2/max2048/2C1＋8C8，完整HTTP/token、C1序列相等、两类capture7/7和FULL≥2后才benchmark；final只smoke，总40smoke＋6600benchmark＝6640请求/C≤64/0重试。首输出/HTTP/预热失败停止新增阶段。若driver退出、精确健康空闲BF16、final从未尝试，允许一次既定final恢复；已健康FP32不重复恢复，启动失败不强杀或重试。

只读前检API3619570/start529063124/argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`，health200、running/waiting/preemption0，新目录不存在，约6.38TiB空闲，PPU-07连接通过。执行前本地副本`/private/tmp/qwen38-perf060-op061.2FEf9s`：controller SHA`f3d7722484fe25b1937c4e4b5748077d528ee2531da644958500efb4710f3731`，prepare SHA`58e7a7d31c6c576779236c58b94de9d3059acf77a238a386286b29df72b940ae`，preflight SHA`eef7f36190548dcadd1a964d7593b0b14621567e4cb3eea5290bf2a621499281`。先排他上传`commands/`及未改toolchain，执行prepare、CPU CLI预检（0模型/服务动作），核SHA后仅一次launch；当前结果not_run。沿用30分钟监控，仅完成/失败/明显停滞/需处理通知。

## 请求、范围与方法

### attempt004终态审计执行前（22:28+08）

原driver已退出，`FINISHED.json`自然生成，四角色完成；final API3852394/start530581998/原argvSHA，health200/running0/waiting0/preemption0，10条final护栏通过、两C1各277完整tokens相等、FULL统计1162。原生三阶段比较均`failed`，不是执行错误或证据incomplete：预冻结阈值为零吞吐回退/零p99延迟回退，而FP32出现约1%–1.6%的C64吞吐代价。仍需核完整原始回执、全部轮次及SHA后归档，不改契约或重测。

执行前保存CPU-only审计脚本`commands/terminal-audit.py`（本地`/private/tmp/qwen38-perf060-op061.2FEf9s/terminal-audit.py`），SHA`793f1c9c69cbdce3b5712b04fc7b588207276c962df2d2faad96ce2e3550d709`。仅一次`PYTHONDONTWRITEBYTECODE=1 python3 <E>/commands/terminal-audit.py`，拒绝已有`terminal-audit-op061-001`；核driver退出/当前final/source/Git、40份旧raw请求响应/token、132轮原始SHA/计数，调用原维护比较器只读重验三项结果并核相同，复制32份已有编译图及任务文件/完整已存在日志前缀与SHA，不发推理/GPU、不重启、不访问8035。审计失败保留工具错误/中间产物，不修改模型或自动重试。

### attempt004只读监控：全部测量完成，final正在capture（21:59+08）

九组B/C/R原生run-record均complete，共132轮/6600benchmark，加已完成30smoke=6630请求；原driver存活、controller/source/Git未变，无FIRST_ERROR。R于21:39:48完成，由原controller正常排空，21:39:53执行第四次且最后一次授权final FP32启动。当前无8010listener/READY，不复用旧health；final日志PIECEWISE capture从1/7推进至6/7，属于持续编译/capture，不凭shm60s提示误判死锁。不得再调用restore或重复启动。final短护栏和三阶段原生compare尚pending，因此不提前通知完成或性能结论，monitor保持ACTIVE。

仅CPU读取本轮四角色各8rank共32份现有`cache/vllm/torch_compile_cache/*/rank_*_0/backbone/computation_graph.py`及SHA：B/R每rank98BF16+0FP32 all_reduce，C/final每rank96FP32+2BF16；同rank B/R及C/final内容SHA分别一致。这证明本轮编译图中的归约变量，**不是旧图复用、逐kernel时序trace或完整逐层state/logits现场**。终态再复制/冻结已有图及日志，不新增GPU/模型请求。正则工具FutureWarning仅CPU解析提示，全部32文件均读出预期计数，非服务故障。

### attempt004只读监控：B/C三阶段完成，R继续（21:24+08）

21:29+08续检：revert Decode也完成11轮，末2warm吞吐695.7953/711.4955 token/s、spread2.2313%通过；已8组完整native记录/benchmark完整记录下界5808＋30smoke，R Mixed按原计划运行，final尚未START。原driver/8010精确身份不变、health200/空闲采样点/preemption0、source/Git未变，无FIRST_ERROR。不能把轮间running0当完成或追加恢复，继续只监控；最终测量spread/回退漂移与FP32恢复仍pending，按约定不通知正常推进。

唯一driver1685489/start529438250及controller SHA不变，无FIRST_ERROR。baseline API1687226/start529438750和candidate API3919185/start529822430已各完成全部Prefill/Decode/Mixed+C8，并由原controller正常停止；当前revert API1785217/start530202227/原argvSHA一致，health200/running0/waiting0/preemption0，revert Prefill完成、Decode正在原计划中。final尚未START，不能调用restore或把阶段间空闲误作失败。source/安装Git与全部依赖只读复核未变；磁盘约6.38TiB空闲。

已有7组完整native run-record：B/C各44轮/2200请求，R Prefill11轮/704请求，已完整记录benchmark下界5104（不包含R在途/尚未写完整record的轮次）。三角色共30smoke均HTTP200、非空final/stop/think-end/EOS且各自C1完整token相等；B/C/R C1 token数分别580/570/590，跨角色/重启的差异不冒充同实例重复失败，也不产生正式精度结论。

已完成的末2warm主spread（%）：B Prefill0.0478、Decode0.6374、Mixed C640.1074/C82.0416；C Prefill0.1794、Decode2.4245、Mixed C640.1180/C80.9692；R Prefill0.2233，均在预冻结10%以内。这里只证明这些预热检查通过；**native complete仍不等于全部测量指标spread或B/R漂移通过**。等待R剩余计划、final恢复及原生比较，不提前宣布稳定性能差距或“无回退”。正常推进按用户要求不额外通知，monitor继续ACTIVE，无新请求/源码/服务动作。

### attempt004唯一启动回执（18:29+08）

已唯一launch：driver Host1685489/start529438250/argvSHA`92573b18601aba39d809b52623177a29575ef5cbb9681b46c7a3075e3c15fabe`；`DRIVER_PID.json` SHA`1fdf8ee4e82d56ca4fd26108980a12f8962e0f8596b5483008dab49b4d40734c`，`RUN_STARTED.json` SHA`44527bb7bb080b8921d837695f684e1a66f6b31581aac5c05b012e29af524a51`。旧API3619570精确SIGTERM并正常排空11个owned进程，新baseline一次START_ATTEMPT后docker-exec1687190/start529438748；launch SHA`e700a77a8c779ede4fd30b677cfc5603a725125a7b48c38fdd429d900f0a2c6e`。只读快照尚无READY/listener，服务日志在NCCL初始化持续推进，无FIRST_ERROR，未发模型/benchmark请求。不能把原实例旧health或旧归约编译图当新结果。

原heartbeat已通过产品工具更新为“Qwen3.8 PPU07 BF16与FP32性能对照”，产品确认ACTIVE/每30分钟，仅完成、失败、明显停滞或需处理通知。后续只监控该driver自然执行，不能重复launch/run；final异常恢复仅按本轮预冻结的健康空闲BF16与未尝试final等门禁。当前性能差距`pending`，不提前宣称解决原波动或FP32无回退。

attempt004启动前门禁通过：`PREPARED.json` SHA`b2e3cdb4afb896be2593a37060a49ff3f401fe519fd9659b271a2c50f72d9b65`、`source-facts.json` SHA`8d8281e48dbda8d410c627ec6e535da55bfd2129e98e9ffa2b2fcf45c5dadde4`、完整CLI能力预检SHA`400b98ffff15e9de622f42d0ef1edb88c60d59316a6aabcc711f220fbf438374`，版本0.24.0+empty、errors空；0模型/服务动作。`commands/prelaunch-audit.py` SHA`4d061a3f84668aa0633d0ba17b6d50452a08b3204cea8feb40ab8befd16636d2`已执行通过，核各计划与attempt003逐字相同、toolchain未改、source/Git未变、各角色launch仅声明的Plugin和隔离cache路径不同、原8010健康空闲。stage脚本SHA`d5febad30036044a755cd50404fe48505e58bb468f82a702574a75edc2aa940f`。Skill bundle performance `872b65dd0e7a4e8c5b342c37b1c34729f14154d1e68be01ed60938d5b22dc8d1`、accuracy `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。下一命令唯一`PYTHONDONTWRITEBYTECODE=1 python3 <本轮E>/commands/control.py --mode launch`，将由已授权controller精确SIGTERM排空原8010再执行固定四阶段，不强杀、不访问8035。

用户2026-10-21询问使用main＋PR455之外的三文件修改后性能是否下降。本次先只读检查证据和当前8010，不将询问扩大为服务切换授权；此前需要重启先告知、禁止访问8035仍有效。不改源码、依赖、采样或缓存，不推理/GPU测试，不提交推送。

使用项目本地`inference-performance-evaluation`（`e2e/performance`）的`targeted`模式进行比较前置检查；方法要求同配置baseline/candidate及revert漂移核验，分别保留Prefill/Decode/Mixed。已读取Skill、项目映射及维护版`evaluation/performance/README.md`。本轮尚未生成/执行性能计划，不能把方法检查称为benchmark。

## 授权前只读检查事实（历史阶段）

- 当前服务仍eng053：PPU-07/容器`qwen3.8-flash-opt-ppu07-20261015`、8010/TP8物理8–15，API2441711/start521315854/argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`；health200、running0/waiting0/KV0。仅查询8010，未查询8035或物理0–7。
- 实际argv显式`--no-enable-prefix-caching`、`--disable-custom-all-reduce`、BF16、FULL_AND_PIECEWISE、capture sizes1/2/4/8/16/32/64、TP8；metrics prefix queries/hits均0。实际PYTHONPATH仍eng053 bootstrap/candidate及FGVLLM051，不把已安装env058当热重载。
- 当前baseline记录明确performance_not_run；eng053/055仅正确性和CPU工程验证。031/034的同前缀实验用于数值因果，不是稳态吞吐/延迟比较；旧op019算子接入计划也不是此FP32单变量对照，不能借用其历史数值。
- 对应三文件只改归约精度与测试。静态风险：相同元素数collective输入从BF16 2 bytes/element变为FP32 4 bytes/element；有归约前后cast（实际launch/融合/缓冲成本未测）。这是输入载荷2倍，不是已测通信时间、端到端时延或显存2倍。

| 阶段 | BF16/FP32同配置证据 | 延迟/吞吐差异 | 判定 |
|---|---|---|---|
| Prefill | 尚无 | null | incomplete |
| Decode | 尚无 | null | incomplete |
| Mixed | 尚无 | null | incomplete |

结论：**目前不能证明性能无回退，也不能量化下降比例**。没有新增推理/服务重启/benchmark/正式精度或性能gate。

## 下一步（待用户确认8010切换）

- 单变量：同main＋PR455及相同依赖/调优，只将三文件FP32归约切换为原BF16归约；i64/randn、QSA M16、PLE修复全部保持。使用隔离真实源码副本，不checkout/覆盖用户`/opt/vllm-plugin-FL`工作树或清除Git修改。
- 初始父目标`p1024-d1024-c64-n128`，先使用有界targeted里程碑并配Prefill/Decode探针；具体P/D/C/N、预热/重复/超时/稳态准入/漂移阈值/停止规则在任何流量前冻结，再使用维护版`vllm_perf.py` dry-run、执行和原生比较。缩减输出/并发的结果不外推原C64长输出或四场景正式验收。
- 需要仅8010执行BF16 baseline→FP32 candidate→BF16 revert，最终恢复当前FP32组合；涉及服务切换，当前未获本轮重启次数/恢复范围授权，因此暂停于此。先各角色graph capture/至少2replay及最小回归；不重跑全量GPQA、不访问8035。
- 本轮不复用旧acc017 gate给新候选/实例；仅诊断性性能比较，不签正式门禁。来源/负载不一致、输出错误、预热不稳、测量漂移或缺失则incomplete，保留所有已准入测量轮，不挑最佳轮。
- 用户未指定允许回退阈值，仅报告实测差值与波动，不自行宣布正式达标。

得到明确服务切换方向后，在用户既有BASE下排他创建`engineering/perf-060-fp32-reduction-overhead-20261021`，保存冻结计划/比较契约/源码与服务身份/命令及SHA后执行；当前没有创建远端目录或发流量。heartbeat继续暂停。

## 2026-10-21用户授权后冻结的执行范围

用户明确“你可以停掉当前的模型服务，来做下验证”，承接上一轮仅8010 BF16→FP32→BF16对照并最终恢复FP32的提议。只对精确核验的8010 API发一次SIGTERM/阶段、自然排空，不升级信号，不重启容器或操作8035/物理0–7；最多4次服务启动（baseline/candidate/revert/final），每阶段失败不重试。若测试失败，先保留首错并停止测量；原driver退出且健康空闲、精确身份可核时，允许一次使用既定final阶段恢复FP32，不追加benchmark。无法安全排空/恢复时报告，不追杀历史PID。

模式：`e2e/performance targeted`＋`e2e/accuracy minimal-regression`，仅诊断，不签新formal gate。读取两Skill全包并冻结receipt；本轮不改用户已安装Plugin的Git工作区。BF16在容器私有`/opt/qwen38-perf060-20261021/bf16-plugin`副本恢复原PR模型文件SHA`d458a1ce...`，保留未被调用的helper文件；FP32使用`/opt/vllm-plugin-FL`，模型SHA`7bab501e...`。两者生产文件只有model.py字节不同，对应FP32调用及实例adapter；Gems/i64/randn、FGVLLM QSA M16/PLE CTA、fixed pin047、其他启动参数不变。

### 冻结负载与停止条件

| 角色/阶段 | P/D/C/N | 指标与边界 |
|---|---|---|
| Prefill探针 | 1024/1/64/64 | request throughput、mean/p99 TTFT、E2EL；客户端含网络/排队，不是纯设备Prefill |
| Decode探针 | 128/128/64/64 | output throughput、mean/p99 TPOT与ITL，仍包含Prefill残余 |
| Mixed目标里程碑 | 1024/128/64/64 | 完整finite-batch吞吐和TTFT/TPOT；单波填充/排空，不称持续C64 |
| Mixed相邻哨兵 | 1024/128/8/8 | 低batch守护，不外推C64 |

- 父目标`p1024-d1024-c64-n128`；本里程碑缩短D和N，其他P4K/P16K/P32K全部未测，不作正式四场景结论。
- 每角色/场景固定3warm＋3measure、末2warm主指标spread≤10%，3measure spread≤10%，baseline/revert漂移≤10%；所有测量轮保留，不丢慢首轮，不追加预热或重跑。每轮600秒预算，超时/incomplete保留原结果并停测。
- native `/v1/completions` random固定长度、temperature0/ignore_eos=true、seed42派生、range ratio0、finite batch，无profiler。native CLI源码已只读确认ready-check与num-warmups默认均0，维护runner不额外发请求。
- 每新服务先用复用eng053 HTTP collector做2C1＋8C8、全为固定doc2 payload、原采样/seed1234但max_tokens2048；C1完整token相同、健康输出及native FULL≥2才继续。只属于有界smoke，非原10不同题/全量精度。记录全部rawHTTP/token，任何HTTP/空final/length/NaN/非法访存/新异常停止新增阶段，在途自然取证。
- 最大perf请求3600、smoke40，总3640；零自动HTTP重试/额外推理/隐藏warmup。每角色各1独立服务实例、3测量轮，是targeted诊断重复，不是多实例正式验收。
- 比较器primary最低改善0、guard容许回退0用于标注变化方向，用户未定义业务容忍度，不能将工具passed/failed直接当业务达标。波动/漂移不满足则incomplete。
- 各实例使用对称新私有编译/FlagTune/vLLM cache、原pin047相同策略与固定预热。冷启动不纳入指标，不动旧缓存。

### 控制与客户端准备

本地控制副本`/private/tmp/qwen38-perf-060.XS225y`，`control.py`只编排服务和原生维护入口，性能工具chain为本仓库原件，不另造benchmark。新修改命令/launch/计划/contract/source/镜像挂载/Skill receipts先外部保存和SHA，dry-run后唯一driver运行；实际测量走`vllm_perf.py`和`compare_performance.py`，原生客户端/源文件完整校验。

客户端预检发现CVD空且插件禁用会选择不可用CUDA native，启用fl但CVD空时能力查询也失败；均未发模型请求/改服务。采用现有PPU SDK、fl插件、仅目标卡8可见的原生CLI已成功输出`0.24.0+empty`；保留原有vllm._C启动告警，不当新模型事故。客户端可做平台属性初始化，不访问0–7，不运行独立GPU单测。将在首个停止前完成完整CLI capability预检。

首prepare在任何停服/模型请求前因Gems清单不等拒绝。只读同口径重核：Gems全文件名/内容与eng053原件完全相同，差异仅新工具漏掉旧清单含有的6份`flag_gems.egg-info`元数据。原prepare错误保留，修正工具清单口径后排他进入同一实验`attempt-002`，不改库/模型、不放宽critical SHA；私有BF16副本尚未创建，无服务动作。之后原始计划/工具/回执实际均绑定该attempt目录，首轮不计性能或模型失败样本。

attempt002准备通过，已建立私有BF16副本；安装源Git工作区和源码、Gems/FGVLLM/native graph/权重与tokenizer身份均核验保持。控制器SHA`e8b3d4cd1b1eaf40e0d7f356a5512eeca60f61cfd4100bf11f7d3f68589f410c`，prepare-container SHA`ccb635aaf5ec557e3ccfc8e2233ab8c2d1c9f2f1f55709d273be2b27df359f91`，client-preflight SHA`4fc0a65e2c76726f3c66ebe1c9d0ee9fb8a77e588d46e7e18332312ed20e04c3`。完整原生CLI能力预检通过（0模型请求），版本`0.24.0+empty`、所需flag全部支持；客户端console与benchmark/CLI源指纹已保存。接下来仅一次`commands/control.py --mode launch`，后续只监控原driver，不重发launch/run。

唯一driver已启动：Host2656909/start527399773，argv SHA`bdcaacb6c08d13e620936127d7c6d7a0093a7a1ddb4eca7cd6fd7eee1f109983`。PREPARED SHA`ce71929b5539d766c71a7ae0fb2bf486db9f6662d6cb9bdd7bbddbe91bfd3943`、完整client-preflight SHA`d0d6aae95fd8e1f9d7a8127b39a5ee0511c504c1afee801fe9eef51656cb16d0`。原8010 API2441711已仅SIGTERM并自然排空全部owned tree，进入baseline启动；停止是本轮用户明确授权的对照步骤，不当服务事故。后续仅监控原driver/既有阶段产物。

## 运行进展：BF16 baseline

baseline已就绪：API2658773/start527400155，argv与原服务相同SHA`c146e2da...`、health200，两类graph各7/7。8rank本轮`computation_graph.py`均有98个BF16 allreduce（无FP32 allreduce），源路径及实际新编译图与BF16基线一致；属于编译/捕获结合来源证明，不冒充独立逐rank kernel trace。初次编译、capture和首Prefill JIT耗时均不进入性能聚合。

固定10请求/1唯一doc2已全HTTP200、正常final B/think-end/EOS/完整token，无空输出/截断/重试；两C1均580 tokens且完整序列相等，C8八条375/547/562/562/562/562/590/649，native FULL实际重放检查通过。此为bounded smoke，不当正式精度分数。

Prefill 6轮均原生完整性校验通过，每轮64成功/0失败、65536输入/64输出tokens。预热末两轮request/s为1.448275613/1.508184647，spread4.0528%通过10%准入；首次warm1含冷路径，固定列为warmup，不参与测量。

| BF16 Prefill测量轮 | request/s | total token/s | mean TTFT(ms) | p99 TTFT(ms) |
|---|---:|---:|---:|---:|
| r4 | 1.429848943 | 1465.595166 | 23673.552060 | 44745.848154 |
| r5 | 1.520704801 | 1558.722421 | 22193.807322 | 42072.114573 |
| r6 | 1.641817292 | 1682.862724 | 22568.615415 | 38968.931524 |
| 三轮中位数 | 1.520704801 | 1558.722421 | 22568.615415 | 42072.114573 |

**Prefill测量主指标spread约13.94%>预冻结10%，该阶段比较先标incomplete，不能删r4、放宽阈值或称稳态无回退。** native run-record complete只证明完成/计数校验，不代表比较稳定性通过。仍按原冻结独立计划收集Decode/Mixed及既定角色证据，不追加/重测任何Prefill轮；若需提升预热/新契约，须另报方向并对全角色重做，不用现有结果冒充新契约数据。当前只有baseline数据，无FP32回退百分比。三阶段各自使用独立比较契约，最后分别报告可比较性。

Decode 6轮也均完成且通过原生校验。末两轮warm output/s为566.561834/570.957349，spread0.7728%通过准入；**测量主吞吐spread32.3622%、p99 TTFT spread103.5181%超10%，因此该阶段主比较同样incomplete**。首测量轮TTFT偏高是观测，不未经因果闭环认定JIT/编译/时钟根因。已预声明收集的mean TPOT三轮spread仅1.3971%，可保留为描述性阶段代理，但不替代原吞吐主指标或绕过compare判定。

| BF16 Decode测量轮 | output token/s | mean TPOT(ms) | p99 TPOT(ms) | p99 TTFT(ms) |
|---|---:|---:|---:|---:|
| r4 | 384.914667 | 64.054865 | 90.432552 | 13293.644170 |
| r5 | 566.522815 | 63.163061 | 75.270658 | 6504.811209 |
| r6 | 561.173239 | 63.830398 | 76.016499 | 6558.114934 |
| 三轮中位数 | 561.173239 | 63.830398 | 76.016499 | 6558.114934 |

继续原先冻结的Mixed/C8及后续角色，所有不稳定记录完整保留；没有额外请求/更改阈值/增加预热，不因局部均值稳定就称端到端稳定。只有FP32及revert完成后才能给出受限差值，当前无候选百分比。

BF16 Mixed两个case均已完成原定6轮，所有native计数校验通过。C64测量如下，其已列指标spread全部≤10%，其中主吞吐约4.03%；仍须候选/revert稳定且漂移合格才形成有效比较。

| BF16 Mixed C64测量轮 | output token/s | mean TTFT(ms) | p99 TTFT(ms) | mean TPOT(ms) | p99 TPOT(ms) |
|---|---:|---:|---:|---:|---:|
| r4 | 155.897894 | 24923.790519 | 44669.799420 | 216.060063 | 369.158470 |
| r5 | 159.176070 | 23755.758863 | 43690.439647 | 216.742049 | 360.940491 |
| r6 | 162.319418 | 23308.186393 | 42668.870285 | 212.428404 | 352.847567 |
| 三轮中位数 | 159.176070 | 23755.758863 | 43690.439647 | 216.060063 | 360.940491 |

Mixed C8哨兵r4/r5/r6吞吐分别76.505437/57.786211/75.103178 token/s，存在明显跨轮波动；不剔除r5，其最终稳定性按冻结比较器核验，不把C64稳定外推为C8稳定。

## 运行进展：FP32 candidate

baseline已按原计划结束且running/waiting均0，唯一controller自然停止原8010并进入candidate启动，没有额外启动或重试。13:52+08编译图已生成，8rank均有96处FP32 allreduce及2处BF16 allreduce，区别于baseline98处全BF16。该证据证明本轮编译路径确实包含FP32归约，不冒充每rank独立kernel trace；候选仍在启动编译/graph阶段，暂无性能百分比。

14:05:08+08快照：候选PIECEWISE capture3/7，日志持续推进，尚无READY或FIRST_ERROR。baseline共1200性能请求＋10 smoke已完成。按用户新明确答复“启用监控，完成或失败时通知”，已复用同线程heartbeat `qwen3-8-ppu07-gpqa-c64`，更新为perf060并产品确认ACTIVE/每30分钟；不创建重复监控。仅完成、失败、明显停滞或需要处理时通知，正常推进安静。监控不重复run/launch、不追加轮数；若控制器失败，仅在原driver已退出、精确健康空闲BF16身份及一次final恢复条件全部满足时使用已获准的既定restore阶段，不能自动重测或任意重启；已健康FP32不为恢复重复启动。终态审核原始比较/完整轮数/来源和最终FP32绑定后暂停监控。

## 2026-10-21 14:38心跳：预热未达稳态，停止测试

原controller已退出，SHA保持`e8b3d4cd...`。首错`FIRST_ERROR.json`于14:30:52+08生成，SHA`6ee41c90912e35a7c817b4dd831f43f0ba04840f54690ecac20c8578357d712a`：candidate/decode未通过原生固定预热稳定性。三轮各64成功/0失败，末2轮output/s 559.9049568438583、500.00488199967623，spread0.1130286230940905>0.10；未产生Decode正式测量轮。这是测量准入失败，不是请求/模型执行失败。原生failed run-record SHA`a1184d4b58bcc58fcafc8950fe7b46b33ac11d2120c9ad97a178791176342d7e`，不修改阈值或补跑。

FP32候选已完成10 smoke，均正常最终B/完整token/think-end/EOS；两C1均602 tokens且完整相等，C8七条441及一条563，native FULL统计1578，最小健康检查通过（不当新正式精度）。当前8010 API542558/start527741852/原argv SHA`c146e2da...`，实际PYTHONPATH为本轮bootstrap＋`/opt/vllm-plugin-FL`＋FGVLLM051；health200、running0/waiting0/KV0/preemption0。当前已经FP32且健康空闲，**不调用restore、不再次重启**。revert/final没有START_ATTEMPT，candidate Mixed未启动；没有完整B/C/R比较，不能判定FP32真实性能回退比例。

终态取证仅CPU处理现有数据：先保存脚本到`attempt-002/commands/perf060-terminal-audit-001.py`，SHA`3716eecf64a59d63eb7768a3d2e99c68de423d2211fde809f6da33156bcd8dcb`，执行`PYTHONDONTWRITEBYTECODE=1 python3 <该绝对路径>`。它拒绝已有`terminal-audit-001`、核原controller已退出/当前FP32精确绑定及源码Git未变，核20份既有smoke raw/token和原生轮次SHA，调用维护比较器仅消费已有run-record签发incomplete诊断回执，记录16份既有编译图SHA/归约dtype，复制现有日志/请求/结果前缀并哈希。0推理/0GPU测试/0服务动作，不伪造原controller FINISHED或补跑缺失角色。源码/首错/旧证据不改；若审计失败保留中间原件，不改模型或重测。

### 已执行的终态核验与结论

CPU审计成功，`terminal-audit-001/AUDIT_FINISHED.json` SHA`f7f88fac57f465bbebedc7a395148538699a85190755e78f4b66b3324c65f338`，310份现有文件前缀已快照，manifest SHA`e237beeecb3b8c3548660ec81703bc4a9a16c49f66b350a9d2af59cfbc5348f4`。模型/依赖/安装源Git未变，当前FP32 API542558/start527741852仍health200、空闲，保留原服务，不增加恢复启动。两角色共20条smoke HTTP200、均正常最终B/完整token、各自两C1 token相等；没有把BF16与FP32跨角色token不同当成输出健康失败。

实际33轮native性能请求1776＋smoke20＝**1796请求/2次服务启动**；candidate Decode仅3轮warmup，candidate Mixed/revert/final均not_run。未追加流量、重测、改阈值、查8035或跑全量GPQA。冷启动、capture、JIT与预热轮不进入下表测量中位数。

| Prefill P1024/D1/C64/N64测量指标 | BF16中位数 | FP32中位数 | 描述性变化（FP32/BF16−1） |
|---|---:|---:|---:|
| request/s | 1.520704801 | 1.491258580 | −1.94% |
| total token/s | 1558.722421 | 1528.540044 | −1.94% |
| mean TTFT(ms) | 22568.615415 | 22844.033271 | +1.22% |
| p99 TTFT(ms) | 42072.114573 | 42903.877066 | +1.98% |

FP32 Prefill r4/r5/r6 request/s为1.429831090/1.491258580/1.595387983，测量spread11.10%（baseline13.94%），均超10%；p99 TTFT也分别有10.82%/13.73%波动。上表只描述已保留三轮，**不能把−1.94%归因成已证明的FP32性能退化**，也不能说无回退；没有revert漂移核验。Decode没有候选测量，Mixed没有候选数据，均不能量化真实变化。

原生维护比较器的只读终态回执均为`incomplete`（不是formal gate）：

- `terminal-audit-001/comparison-prefill.json`：缺revert独立实例，SHA`511af2855c4c10f358a2cdd36f8e8238b330209ff9eaeefb314792ab920352c5`。
- `terminal-audit-001/comparison-decode.json`：run failed/incomplete（预热稳态未过），SHA`7f9f000fdcd1fb1281224f9eec0c9037176cea481fef8bc6b7d2c00bfd5d8e16`。
- `terminal-audit-001/comparison-mixed.json`：缺candidate独立实例，SHA`589aafdf9e094f339c475ac361ec1bc3136e9969ac53372d025e681efa386ba1`。

比较器提前因缺角色返回，未输出表内描述性变化；这些值由已核验原始轮次计算并明确标注，不冒充原生通过结果。`compiled-allreduce-graphs.json`记录8rank baseline各98BF16、candidate各96FP32＋2BF16的路径与SHA；无新逐层/状态/profiler现场。

结果为`incomplete-performance-warmup-unstable`，首因尚未归因到客户端/调度/编译/设备噪声，不未经新证据宣称FP32实现错误或稳定性根因。当前候选只获短doc2输出健康回归，不继承旧acc017正式gate或产生新formal精度/性能结论。已按用户终态规则暂停原heartbeat，产品确认`PAUSED`；不自动恢复测试。若继续，需用户确定新的稳态准入与测量预算，所有B/C/R角色按同一新契约重做，不能改写本次门槛或挑轮。

## 用户授权的新契约：attempt-003-warm8（准备阶段）

用户新明确“那增加预热的轮次呢，看看是否会解决该问题？”，承接上一轮相同新契约重做B/C/R的建议。新授权仅改变预热预算，使用同一perf060实验下排他新目录`engineering/perf-060-fp32-reduction-overhead-20261021/attempt-003-warm8`，**不覆盖attempt002或把它的轮次混入新比较**。模式仍`performance targeted`＋`accuracy minimal-regression`，只是诊断测量稳定性，不是新性能优化或formal验收。

- 四个原缩减case及请求/并发、采样、每轮600s、客户端/原生工具、所有源码与依赖不变；**每case/角色固定8warm＋3measure**，仅把原3warm改为8。末2warm主指标spread≤10%、全部3measure spread≤10%、baseline/revert漂移≤10%，不放宽门槛、不新增SLO或弃轮。测量轮为r9–11，seed仍由原维护runner按轮次派生；不与旧r4–6混比。
- 同样串行BF16 baseline→FP32 candidate→BF16 revert，最后FP32恢复；最多4次启动，各角色10条doc2 bounded smoke（2C1＋8C8、max2048/0重试），capture两类7/7且至少2实际FULL重放后才benchmark。最多6600性能请求＋40smoke＝6640请求/C≤64；任何预热未稳、输出/HTTP/执行错误立即停止新增阶段，不自动继续加warmup。测量波动按原比较器诚实标incomplete。
- 各角色仍用对称全新私有cache，根改为`/opt/qwen38-perf060-warm8-20261021`，不复制旧cache或动用户安装源Git；BF16实体副本在其`bf16-plugin`，FP32仍`/opt/vllm-plugin-FL`。保留FP32数学/i64/randn/QSA M16/PLE CTA、黑名单与pin047固定调优。只切8010/物理8–15，不访问8035/物理0–7，不GPQA、不提交推送。
- 14:57只读前检：原FP32 API542558/start527741852/原argv精确不变，health200/running0/waiting0/preemption0；源码、Git、依赖、容器镜像/挂载与attempt002快照一致，远端磁盘余约6540GiB，新外部目录不存在。原controller已退出、新controller尚未启动。
- 成功条件：新末2warm和全部measure达到冻结门槛，B/C/R来源与漂移完整才报告该缩减scope可比较；不能因一次last2 warm通过就说8warm解决所有波动。若仍不稳，保留8轮曲线/错误、判incomplete，待新方向，不追求跑到通过。
- 继续使用用户已选的每30分钟监控/仅完成或失败通知，待唯一新driver成功启动后更新同一heartbeat，不复制旧PID或执行旧launch。终态先核现有FP32；已健康FP32不为恢复重复重启，若失败时为健康空闲BF16且既定final从未尝试，允许一次原final阶段恢复，否则报告阻塞。

远端变更前已保存本地命令副本`/private/tmp/qwen38-perf060-warm8.hZaNpj`：新controller SHA`5d47ac5e14c6a54b83272afb36618f1e0b70e8a4a72252d121221d5fb7c43c59`，prepare-container SHA`8fa2183fc0a9a19e9f625dcfc7736016856b7456cbda80c5877f5e74cc1ea440`，client-preflight SHA`c9cd1b43454e9d643133bc93e479466764ec78941359a33e62bbe334ad73b877`。将排他创建新E并上传到`E/commands/`与未改`E/toolchain/`，先`control.py --mode prepare`（只做私有副本/计划，0服务动作），然后既有client-env调用`client-preflight.py`（0模型请求）；核计划/dry-run/来源/SHA后仅一次`control.py --mode launch`。后续只监控唯一新driver，不重复prepare/launch/run。

15:02+08准备和完整CLI预检通过：`PREPARED.json` SHA`ee846f983a2ab12cc03b7dcb96b3ebc4c779373532cadcfa2efb74fee4d5c3a2`，client `0.24.0+empty`/`/usr/local/bin/vllm`、0请求；`contract-review-before-launch.json`已机器核对新旧每份plan仅warmup3→8、比较contract逐字相同、toolchain全部逐字相同。新Prefill/Decode/Mixed plan SHA分别`f1de721c3f6eb7c329f6edd3d2d72b9f4819003a65f22aba0807cd97e09687d2`、`3bc12a263fe3743676b9111024f3ae05f30af83beac471d6c52eae9b924a28fe`、`b6fe4c7b049a1254a05a27809e60d9372087929b6475d892be8994f54e84ae69`。Skill完整bundle SHA：performance `872b65dd0e7a4e8c5b342c37b1c34729f14154d1e68be01ed60938d5b22dc8d1`、accuracy `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。启动前精确FP32 API542558仍健康空闲，source/Git不变；接下来只执行一次新E下`--mode launch`，不是重发旧controller。

唯一新driver已于15:03:42+08启动：Host3034420/start528204904/argv SHA`8b81d6a4da7499736678641b67c28374e2110af29e27ee0a58e93990a454f83c`，`RUN_STARTED.json` SHA`a6cd41c1fb783e1d55c3c3130a68ab91a01ebeff9c5e45475ee3cc22fafde8a6`、client预检SHA`025f00c78b50a91525233473606d1fb2adc8fdd345c0a8f2aca0e6f5f43cb167`。原FP328010精确owned tree仅SIGTERM自然排空；新baseline已启动，15:07日志为torch.compile阶段，尚无READY、模型请求或FIRST_ERROR。已更新同一heartbeat到新E/新PID/8warm契约，产品确认ACTIVE、每30分钟，完成/失败/明显停滞或需处理时通知；不沿用旧PID或旧3warm失败作为本轮事件。当前只是开始验证，尚不能声称8warm解决波动或FP32无回退。

### 15:37:55+08只读监控：baseline已就绪，进入Prefill预热

唯一controller3034420/start528204904/argv及脚本SHA不变且存活。新BF16 API3035797/start528205255/原argv SHA`c146e2da...`，精确listener与READY绑定一致，health200。READY于15:28:30签发，SHA`6cb895d74fe4522c051c090f20b26cdeba215b4242cf9195f01a9ce3134e93b3`；两类capture各7/7。8rank本轮新编译图分别98BF16归约/0FP32，属于来源与编译/capture证明，不当逐rank独立kernel trace。

10份既有smoke均HTTP200/正常最终B/finish stop/think-end/EOS/321 prompt tokens，raw SHA和完整API token长度已只读核验；两C1均601 tokens且完整序列相等；C8按seq2..9为830/346/526/302/301/332/587/484。15:36:35 `SANITY_FINISHED.json` SHA`0526c5631390124f815e9fae3bdae1cb77c47e6150f3831f553dc68eda0f7d70`，native FULL执行统计1882，原controller已在C8前验证至少两次重放。仅1唯一doc2健康范围，不是正式精度分数或新gate。

当前进入`baseline-prefill-001`首轮预热；截至快照尚无完整native原始round/run-record，因此不报告性能请求完成数或8warm稳定性结果。快照running8/waiting23/preemption0，服务有prompt/generated推进，未见FIRST_ERROR或新HTTP/模型故障；不把正常Prefill排队和首JIT称停滞。candidate/revert/final均未启动。源码、依赖、安装Git仍与冻结facts完全相同，远端余约6539GiB；本心跳0新增推理/GPU测试/服务动作。仅正常推进，按用户偏好不发送阶段通知，monitor保持ACTIVE；后续只监控原driver，不重发、不追加warmup，不访问8035。

### 16:10+08：8轮预热仍未稳，拟执行已授权的一次final恢复

原controller3034420已退出，`FIRST_ERROR.json`记录baseline/decode固定预热失败；原生末2warm输出吞吐421.622592/506.352420 token/s，spread18.26123%超10%，没有Decode测量轮，也未启动candidate/revert。Prefill原生11轮已收齐，其complete仅为计数/来源校验，不先宣称测量稳定或性能通过。已及时通知用户此为测量稳定性失败，不是HTTP/模型故障，不重测。

16:10只读精确8010仍为baseline API3035797/start528205255/argvSHA`c146e2da...`，health200/running0/waiting0/preemption0；源码/依赖/安装Git未变。按用户已授权的失败后final恢复分支，下一步重新核controller SHA、final STOP/START和恢复进程均不存在、镜像挂载与冻结facts一致且当前精确BF16健康空闲，才**仅一次**执行：`PYTHONDONTWRITEBYTECODE=1 python3 <attempt-003-warm8>/commands/control.py --mode restore`。使用可返回session方式跟进；只精确SIGTERM当前8010、自然排空、加载既定final FP32并10条doc2 smoke，不benchmark、不访问8035。完整脚本已保存于上述路径，SHA仍`5d47ac5e14c6a54b83272afb36618f1e0b70e8a4a72252d121221d5fb7c43c59`，不改旧首错/契约，不再次恢复或强杀。

16:11恢复前全部门禁通过（原driver已退出、精确BF16健康空闲、final从未尝试/无恢复进程、镜像与挂载及source/Git均未变），一次恢复已执行。Host恢复进程977602/start528612804/argvSHA`b40346ed35b94f3d4a1a941b4e7a12d3882901c94bad76922f072740b3e67a18`，执行session60898；baseline owned tree仅SIGTERM自然排空，final START已签发，**绝不重复restore**。final STOP/START/LAUNCHED SHA分别`2be740b8...`/`0238eb7b...`/`651bbe77...`。16:12:56 final worker初始化/NCCL日志推进，READY与恢复完成回执尚无，不能称FP32已可用；监控继续ACTIVE，仅跟进原恢复进程与既定10smoke，不重测性能。

只读CPU核验了本轮全部19份原生结果及validation SHA、每轮64成功/输出长度/无错误：Prefill11轮704请求，Decode8warm512请求，合计1216性能请求＋10baseline smoke＝1226已完成；final smoke尚未开始。Prefill末2warm spread4.25349%，r9–11吞吐1.450510829/1.460588790/1.469613657 req/s，中位1.460588790、spread1.30789%；meanTTFT中位26052.046ms、p99TTFT中位43805.661ms。这只是BF16基线描述，FP32候选及revert没有数据，不计算收益。Decode完整warm曲线56.40349/407.93170/532.55274/569.11149/563.47396/534.24617/421.62259/506.35242 token/s，末2warm18.26123%未稳，无测量轮。Mixed未跑，三阶段B/C/R比较均incomplete。

首错原始时间15:55:33+08，`FIRST_ERROR.json` SHA`9b9e4d90a9cd8203a5da76f12ba2ebf558896ad5a0d79cb52835798009af5441`；Prefill/Decode run-record SHA分别`4546fa455b8abea5bf9204d30613f376b6e88ffb284f93b5ef38c424364c2b5f`/`98f20eba9fb1e686632b2b554274aeccbc1f636754c41102008576bca16beb0f`。原件全部保留；终态CPU快照/比较回执待原恢复进程退出与final证据齐全后补冻，不能直接运行硬编码attempt002的旧audit。已通知失败，未签新精度/性能gate。

### 用户授权的既有证据定位（2026-10-21）

仅分析旧数据/源码，不新增benchmark、GPU算子、埋点或服务动作；不访问8035。按performance targeted证据审查与关键算子分析方法，先区分客户端/TTFT/Decode，再核PPU后端与MoE dispatch。候选线索是`moe_align_block_size_tle_atomic_fused_coop`：baseline缓存18个同名目录都只有`.source`；r8末仍改写两份IR，无成功metadata/二进制。PPU `make_ttir`先调用`reject_unsupported_tle`，显式拒绝`tle.distributed_barrier`；现存IR含该op。Gems捕获Exception仅DEBUG记录并回退四阶段，未缓存不支持状态；libentry在成功返回后才保存kernel cache。尚须CPU解析旧IR确认真实拒绝，不把静态嫌疑直接当已测GPU瓶颈占比。

执行前保存CPU-only脚本`/private/tmp/perf060-existing-audit-001.py`，SHA`11f3412af475d4bae0c9c4d8987635d9e1f43083deaf098f4553c10812462aa5`；将排他上传到本轮`commands/perf060-existing-audit-001.py`，再执行`PYTHONDONTWRITEBYTECODE=1 python3 <该路径>`。它核旧首错/controller SHA、19份native raw/validation、原计数/全轮保留，复制既有日志/IR/相关源码到新`diagnosis-existing-001/`；CPU解析旧MLIR并仅调用真实PPU能力拒绝函数（无编译lowering/driver/kernel/硬件查询），保存首异常及SHA，核当前源码与原恢复进程。拒绝已有目录；工具失败保留原件不自动重试。此审计不是新性能测量或恢复命令，最终服务恢复审计仍待原进程完成。

#### 16:26 CPU旧IR审计结果：明确的能力误判与重复失败回退

审计已完成，0新增请求/0GPU测试/0服务动作，原源码/Git/依赖不变。`diagnosis-existing-001/analysis.json` SHA`e7c6817849bc16c086ea70a57f172fa9cfb2124038e3e0688775856b02b32298`，89份既有产物快照manifest SHA`9b97b6f49fcbf94511620eb9c50ed12cae47f170dd2dadfa511778f1ea76c8a5`；另冻18份原始cooperative IR及6份实际后端/缓存/客户端源码。真实旧MLIR在CPU成功parse，调用实际PPU拒绝函数得到`NotImplementedError: unsupported TLE feature on the 'ppu' backend: tle.distributed_barrier`；不是mock，也不是新GPU执行或原现场未捕获trace的冒充。CPU traceback保存在`CPU-IR-check-output.json`及analysis。

已闭合的机制：Gems `HAS_TLE`只检查版本/import，`moe_align_block_size_triton`行540又仅检查CUDA tensor和expert上限，没有PPU的distributed-barrier能力门禁；行558试cooperative，PPU `make_ttir`行270在第一pass前拒绝该IR；Gems行577–587吞Exception、只DEBUG打印并回退四阶段。异常文本不含`cooperative`，因此该拒绝直接False，不是降低grid后成功。`libentry.py`行1536成功返回后才在1574写cache；Triton compiler在metadata cache-miss后写`.source`，所有阶段成功后才写JSON/group。于是该失败不能变成成功cache，后续非graph调用仍会再走前端。r8的两份`.source`于15:55:20.8135及15:55:25.3405改写，但18个目录均无TTIR/metadata/binary，结合实际PPU拒绝规则确认重复失败编译→fallback机制。普通日志未打印错误不等于没有这类失败。

时间线证据（不改预冻结指标或弃轮）：r7/r8均64条成功、P128/D128，客户端请求开始窗口只有13.125/15.176ms，非客户端把64请求串成数秒。graph日志均为`NONE128 → FULL1 → NONE8065 → FULL64`，与先处理1条128prompt、再处理63条prompt+1条Decode一致，不能把capture已完成等同全部Prefill已graph化。r7/r8总时长19.42970/16.17846s（差3.25124s），meanTTFT11.28608/8.21009s（差3.07598s，约总差94.61%），postfirst平均差0.17573s，meanTPOT64.03677/62.65308ms（spread2.18438%）。单条最早TTFT6.09156/3.73575s，随后63条TTFT中位11.36845/8.28140s；首条请求有5.21573/4.48334s的一个早期ITL gap，与随后Mixed Prefill一致。后续FULL64的每token循环相对稳定；整体吞吐仍被短D128中的Prefill/主机fallback成本显著影响，不能把whole-batch output throughput直接解释成纯Decode kernel吞吐。

第1轮真实新二进制/IR较多，145.24s含初次JIT；后期不是同一个一次性冷启动理由。r2–r7缓存mtime未见新成功编译产物、r8仅上述两份未完成source，pin047配置记录已在15:25前结束。因此“再加warm就一定消失”不成立。明确的后端不支持路径误选已确认，但重复失败编译究竟贡献多少秒、TTFT残余变动来自CPU/调度还是其他数据依赖算子，缺少分段trace及仅绕开此失败尝试的A/B，仍未证实；不宣称它唯一解释所有18.26%波动，不归因于FP32（本轮失败发生在BF16基线）。

下一最窄证伪：在目标PPU backend能力边界仅跳过已知不支持的TLE alignment尝试，直接保留现有四阶段reference/fallback；不按模型名/机器名兜底，也不永久屏蔽所有未知异常。先CPU dispatch/错误分类，再目标算子数值/边界/graph、服务同配置Prefill/Decode/Mixed B/C/R；若需服务重载或新probe须先告用户，当前未修改/未执行。16:27:21既有一次final恢复仍存活，PIECEWISE capture1/7推进，READY尚无；monitor继续跟进原恢复，不重复restart/restore，不访问8035。

16:44:50只读核验原restorer977602已退出，`RESTORED_AFTER_FAILED_TEST.json`于16:44:01签发；FP32 API979238/start528613221/原argv精确绑定且health200。新op061候选仅私有副本、未安装加载，故旧perf060冻结source继续有效。终态CPU审计执行前保存`/private/tmp/perf060-warm8-terminal-audit.py`，SHA`8319da85022b66b7b8ba8ddd44ea525661f896254287ef3e17e9d41b0404d9b7`；排他上传到本轮`commands/`后仅一次运行。该脚本核原controller/restorer均退出、精确final健康空闲/source，核baseline/final共20份旧raw/token与capture/replay，复制日志尾部，核16份已有编译图，用原生比较器消费实际存在或缺失的B/C/R路径签发三项incomplete回执，不补造run-record；写新`terminal-audit-warm8-001`并拒绝覆盖。0新推理/GPU/服务动作，不动首错或旧证据；成功后按原监控契约暂停heartbeat，不自动复测或加载op061。

16:48:55终态审计完成：原driver与restorer均退出，当前FP32精确绑定健康空闲，原source/Git不变。baseline/final共20份raw HTTP/token/prompt/usage/SHA均通过；final两C1各493 tokens且全序列相等、C8为441/441/441/441/441/441/441/563，均B/非空final/stop/thinkend/EOS。两类capture各7/7、实际FULL≥2；8rank既有baseline图各98BF16，final各96FP32+2BF16，属于编译/capture来源证据，不是独立逐kernel trace。20smoke＋1216benchmark＝1236总请求，2启动，均在预算内；candidate/revert/Mixed未补跑。

`terminal-audit-warm8-001/summary.json` SHA`3c5d2ad99a43b72bc742d2cdcf9899db3fd97065ef5524c186cb5231e5d97a13`，119份既有文件快照manifest SHA`64bd1f2e957ab3fa0753be4841aa3c3b396da4630a3cc5d0743f70bc38767fd6`。同目录维护版`comparison-result-prefill/decode/mixed.json`均incomplete：缺候选/回退、基线Decode预热未稳、Mixed未执行。审计regex产生一条Python FutureWarning，仅工具提示；计数和SHA正常，不是模型故障。旧首错与8warm曲线保留，不签正式gate。产品已确认该heartbeat **PAUSED**，保留当前健康FP32；新op061只准备候选，未作用于本轮。
