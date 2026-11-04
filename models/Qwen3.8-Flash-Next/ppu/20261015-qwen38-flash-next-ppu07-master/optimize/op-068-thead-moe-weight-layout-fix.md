# op-068：thead MoE 原始权重布局修复／独立 PR 候选

## 当前模型验证结论（2026-10-23 19:52+08）

本修复的模型minimal及[acc020全量GPQA](acc-020-full-gpqa-op068-layout.md)均已完成并通过独立CPU核验。acc020单服务C64／198唯一题strict **176/198＝88.8889%≥88%**，原生gate及当前源／实例绑定有效，清除当前候选的正式精度阻塞；旧acc019的174/198仍为历史failed-score，不被覆盖或借分。

本轮198完整HTTP200与token/usage/prompt-doc映射齐全，0真实客户端超时事件；11条60000-token length造成content=None→`<TIMEOUT>`占位，不是网络超时，仍计错保留。当前8010同BF16实例健康空闲，三库／engine／元数据和权重stat／HEAD-index／bootstrap前后与当前一致。CPU report SHA d0f9ddb28d1bdb1de8dadcaa3901007f6f0673543e6c6038633a9762015a2452，详细原生结果与gate路径见acc020和state。

保留cac5b989及现有修复；本次仅审计已有证据，没有新请求／GPU测试／重启／提交推送或8035访问。停止本轮monitor，保持服务等待方向。新gate证明本绑定组合达标，不证明每个变化独立数值等价；没有全量逐层现场。P1K Prefill/Decode/Mixed稳态数据未建立，不能以算子倍数或GPQA时长宣称端到端性能完成。以下按原时间保留。

## 2026-10-23 主任务继续优化：当前版本模型验证（执行前冻结）

18:16+08续查：既有acc020仍运行，同一8010健康，21请求在运行、无等待或preemption；现有177份完整API返回对象的token/usage/finish健康核验无新异常，当前source／49冻结文件／评测源码SHA一致。尚无原生终态分数或新gate，P1K性能继续未启动；详见同一acc020记录，不由本monitor追加负载。

17:23+08只读监控更新：本轮17:09:03 READY，两类capture各7/7；17:17:09原minimal终态通过，driver已退出。2C1完整序列相等（各601 token），8C8分别610/563/529/269/570/578/561/511 token；10/10完整HTTP200、非空final、finish stop、thinkend248069和末EOS248046均核验，0短护栏异常。8rank真实Plugin apply栈进入vendor cac5b989；C8前native FULL1136、终态1764，包含真实unpadded8/FULL；不是逐rank独立kernel trace。

后继controller于17:17:12唯一执行既有CPU审计并通过，report SHA365252d66a7c10038cdf674bec7756364c78199fb43b406a260b241840857a5c；原101成员manifest e3a33855与审计3成员manifest c6572a44本次逐项回读无误。FINAL_SUMMARY a73ce8cd、FINISHED 5dc99fc9完整；三库／engine／模型元数据和权重stat／HEAD-index及bootstrap在正式准备与本次CPU回读中均匹配。权重stat不代表全量权重字节验证。

新API2114316/start546089295/argvSHA c146e2da与READY及8010 listener精确绑定。既有acc020已17:17:43自动开始同实例198题/C64正式GPQA，0额外smoke／0新启动；本heartbeat没有执行任何controller或模型请求。17:20:43 health200、running64/waiting0、KV9.28%、preemptions0，正式新日志窗口未见运行错误；17:23:21原formal controller／wrapper／lm_eval／helper仍在运行，无CLIENT_ERROR/FREEZE_ERROR/终态summary。当前仅短doc2最小回归passed，正式分数／新gate仍待终态，P1K性能未启动，不能宣称原11题超时或端到端性能回退已解决。30分钟monitor保持ACTIVE，正常阶段推进静默。以下16:53及更早记录按原时间保留。

16:53+08运行快照：stage回读6份命令／Skill receipt全部一致，CPU prepare完成且source的base／engine与op068独占验证终态逐项相同。PREPARED SHA383d7e74、requests9a36d142、launchabf7a258；16:44:26仅一次启动。唯一minimal driver2113424/start546089125/argvSHA01df0914de0eadb5b9555512fcde62da1298751c658e09673b7d042786cda85b；正在加载／JIT，已有rank0 compile222.31s回执，但尚无READY、模型请求0、无首错。不是性能结果，不据shm60s日志判死锁。后继acc020 controller2462106仅等待本轮terminal和CPU审计；详细固定契约及命令见acc-020-full-gpqa-op068-layout.md。30分钟monitor qwen3-8-ppu07-op068已ACTIVE，正常推进静默；没有第二次启动、停止或源码修改。

用户明确“基于当前的版本继续进行性能优化”。沿用现有已隔离优化容器，不升级仓库，不改变MoE选参、BF16、采样、黑名单或现有修复；不访问8035／物理0–7，不提交推送。此前保持停止属于上一验证／发布阶段；本次恢复先启动当前版本一次，不能追杀旧PID或重复恢复。

只读核实：8010无监听，物理8–15各1MiB／无计算进程；容器运行、原镜像67309a95保持，NFS剩余约5.7TiB。vendor源仍cac5b989，6个既有FGVLLM改动全部保留。新R为本E的 `model-regression-001`，排他创建；新cache为 `/opt/qwen38-op068-model-20261023/cache`，不清旧cache。先精确比较已验证op068的三库／engine／HEAD-index／模型元数据与权重stat，再绑定新实例；stat不冒充权重字节校验。

按accuracy/minimal-regression，复用原10条短doc2完整payload（max2048、原采样、2C1再8C8、0重试／0隐藏请求）。两类capture各7/7、2C1完整token一致、native FULL至少2次及8rank真实Plugin apply→thead fused_experts_impl栈命中后才派发C8。原一次性现有日志handler仅记录函数对象／来源，不替换数学函数、不读tensor。PYTHONPATH仅本R/bootstrap，三库canonical /opt editable；pin047固定调优不变。加载／首次JIT不作稳态性能。

新controller只启动空闲8010一次，没有stop／kill／restart／restore入口；40分钟readiness、每短请求600秒，首异常保留原件、停止新增阶段、等在途返回，不自动修复重测。冻结完整request/headers/response/token、rank-source/rank-call、graph／source前后、原生日志和manifest；终态独立CPU审计，short-doc2不代正式精度。

顺序：stage.py排他传送／SHA回读→新model-control.py --mode prepare（无启动／推理）→核PREPARED→唯一 --mode launch，由 --mode run单次启动及回归。命令先保存在 `/private/tmp/qwen38-op068-resume-20261023.xuEGmU`，远端副本R/commands。SHA：controller `76389b39d83ec98315f03528795d2f2959a2bf68cd49487ce9940837f6cb9e3e`，common `1b9f2ce84f1297b821e83160b73f51c5bbed044b5ba3aac6e080221946b5478f`，probe `2c80bf39fec8aa5234371de3066a4c1df12ce4f5de6ecbcd93d524f3816869b5`，origin `7fb2f5a7461ef18723e3beb18bd974904f62c036d68cd1db0f01adf3445d6b92`，stage `d689f41563ebf10377577e1ea4406e516b4beddb30bc75e79d7bbe77d54c1f5b`；完整accuracy Skill bundle随commands冻结。

复盘review-op068-resume-20261023：acc019有效174/198<.88未清；op067支持转置成本机制；op068算子数值／graph已通过但无模型数据。当前累计端到端收益未知，Prefill/Decode/Mixed基线均缺。最小回归通过后以维护formal_accuracy／原llmrun补同契约198题/C64 GPQA；新有效gate后才做P1K阶段稳态基线，再依据新热点排序框架浪费与MoE选参。不叠加旧局部倍数，不把不同revision历史分数直接归因单项修复。旧计划／产物保留；下次复盘触发为新gate＋阶段基线或验证失败。

- 当前发布状态（2026-10-23 15:48+08）：用户明确授权提交后，已创建独立正式PR [#989](https://github.com/flagos-ai/FlagGems-vllm/pull/989)。仅原布局修复与现有测试文件；未混入#959／#982。本次发布没有改容器／服务或重跑设备／模型测试。下文“未提交”等为此前阶段历史。
- 当前状态（2026-10-23 15:25+08）：两文件已备份并写回目标容器；获新授权自然停止原8010后，最终补丁50项算子硬件测试／16capture／64replay／110数值检查及独立CPU审计全部通过。8010保持关闭，不重启、不提交或推送。下文早期blocked/not_run记录按原时间保留，不代表当前算子验证状态。
- 授权：侧对话用户要求在算子内按正式 PR 标准修复，并后续明确“你可以把原来服务停掉验证下”。仅原8010单次SIGTERM＋独占物理15算子／graph；不继续主对话其他计划，不重启8010、不访问8035、不跑模型请求／全量GPQA或性能测试。
- 分类：`operator/improve`；这是 acc019 超时诊断的有界修复，不解除 failed-score 或签发精度／性能 gate。
- 方法：`key-operator-analysis`；沿用 op067 的机制与数值证据，但整理后的最终补丁必须独立检查，不能以旧微测冒充新硬件验证。

## 优化方向与瓶颈依据

op067 在当前 vendor 源 SHA `807d12ce829343bcd4ef72e809d5c772dd9be4095db6e77adcaacd7810ca0f7e` 下完成限域 B/C/R，支持自动转置策略会在冷缓存 graph 内引入明显成本。4项模块级缓存不能覆盖48层的96份权重；简单扩容还会增加约28GiB/rank，不采用。

修复归属为 FlagGems-vllm 的 `_thead/ops/fused_moe.py`，不修改 Plugin 路由。使用已有 stride-aware GEMM 的原始权重布局，删除自动转置 helper、缓存／weakref 和显存迟滞查询，不只是把调试开关设为False。保留全部 kernel、选参、GEMV override、量化、路由、dtype、公共签名和已有修复；非thead实现不变。不增加公开开关、模型名称白名单或永久配置。

## 编码前三张表

| 项目真相 | 冻结内容 |
|---|---|
| Current op | thead `fused_experts_impl` 的权重布局策略；非新算子、无对应单一 torch API |
| Editable | 独立克隆内 vendor `fused_moe.py`、现有 `tests/test_fused_moe.py` |
| Read-only | 原本地克隆、其他源码／测试、线上三库和8010、op067全部原件 |
| Source baseline | 本地已存在克隆 HEAD `7417158440a80753fb21dab3a124c1be388ab7eb`；vendor源与冻结807d12ce逐字匹配；不是新核验的上游最新main |
| Build | 纯Python host删减，无安装／构建；AST编译和相邻CI格式检查 |
| Validation | 源码等价／选择器不变检查、CPU host契约；现有测试追加多权重对象、权重更新、边界、dtype及changed-input/weight graph测试 |
| Benchmark | 本轮not_run；旧op067只作机制证据，不产生新speedup |
| Active set | host：96权重轮转、量化及内存分支保护；设备待验证：FP16/BF16，M0/1/8/12/13/64/128/256，原布局及带leading padding合法stride |
| Aggregation | 本轮无性能聚合；测试逐项报告，不把mock当GPU |
| Timeout / profiler | 本地CPU检查每次120s预算；不发profiler/GPU任务 |
| Autotune | 不改kernel或性能参数，NVIDIA配置与现有selector冻结；无新增autotune需求 |
| Fallback | 无新增torch计算fallback，仍为已有Triton计算路径 |

| 对齐契约 | 冻结内容 |
|---|---|
| API / reference | 保留当前完整函数签名；测试使用显式专家SwiGLU、GEMM2与top-k加权和作为参考 |
| Backend | 仅thead；非目标平台测试跳过vendor专用用例 |
| Input | 原有hidden连续、w1/w2末维stride=1约束不变；三维专家权重，topk形状相等 |
| Output | 原shape/dtype/device与inplace别名不变，算子不修改输入权重 |
| Dtype | 公开支持FP32/FP16/BF16及现有量化分支不变；新增硬件回归主覆盖FP16/BF16，其他不冒充已测 |
| Numeric | 不改cast/accumulate、SiLU、routing、NaN/Inf策略或舍入；只有输入权重物理布局改变为原始布局 |
| Lifecycle | 每次读取调用者当前权重；不得依赖陈旧副本或全局指针缓存；capture后同址输入／权重更新应被replay观察 |
| Unsupported | 原fp8/MXFP及其他报错策略保持；不扩展autograd／训练支持 |
| Torch reference | torch计算仅在测试；已有生产量化路径中的torch调用不在本轮重构或冒称已消除 |

| 实现路径 | 本轮行为 | 验证／风险 |
|---|---|---|
| empty | 沿用原返回与分配；不新增权重copy | M0边界 |
| plain fast/general | 原w1/w2对象直达原GEMM／GEMV | 多层轮转、合法stride、数值与graph待硬件 |
| quantized | 原量化与反量化逻辑不变；删除原先无条件显存查询 | CPU分支等价检查；硬件量化未测 |
| unsupported | 原异常保持 | CPU报错契约 |
| external-library | 无新增依赖、公开API或环境开关 | 非thead源码全同 |

## 正确性与路径命中

旧op067并非最终补丁的设备验收。本轮只有本地源码和CPU检查，不修改或查询生产服务。

最终两文件diff为+147/-65；生产仅+4/-65，其余为原`tests/test_fused_moe.py`追加143行。生产删除6份转置全局状态、`_transposed_view`和weakref import、原入口中的显存门禁与自动转置；新增4行解释现有stride-aware路径及graph复制风险。不更改`_GEMV_CFG`、导出、注册、公共签名、kernel、selector或量化／路由。严格整模块AST归一化核验：恰好去掉上述策略后原／新AST完全相同；原测试所有AST节点保持原样。

已执行结果：

- 六项CPU unittest通过（另以pytest复验6passed、JUnit留存）。真实host函数AST配mock元数据覆盖FP32/FP16/BF16×8个M×2种布局×4类plain/量化参数，共192组，原始权重对象保留，0查询／复制。不是数值硬件验证。
- 48对稳定权重连续三遍的原cache函数AST复现：原版288次copy／144次显存查询；候选0／0，144次调用均保持原权重对象。这里的次数是CPU mock，不称线上计数。
- Black/isort/flake8逐文件检查通过，`git diff --check`及对原基线`git apply --check`通过。isort5.12.0、flake8 7.1.0；缓存Black hook commit b965c2a5026f8ba399283ba3e01898b012853c79，实际build字符串0.1.dev1+gb965c2a50，不虚称新安装正式24.8.0或完整pre-commit全跑通过。最初Black要求格式化新增测试，已仅格式化候选测试并重新检查。
- 静态新增50个设备参数组合：32个FP16/BF16数值／边界／leading padding与原权重identity/stride；2个多层复用／原地更新与inplace别名；16个graph矩阵、各设计4次replay，分别改输入、只改权重、恢复权重、再改输入。包含M8/H1024 GEMV哨兵。测试防止重新引入`permute_copy`和显存查询；参考输出幅值归一化且变化必须显著，避免零输出／陈旧结果仅靠atol通过。
- 本地`pytest ... --collect-only -k thead`明确因缺少torch在conftest导入阶段退出4；以上50是静态组合数，不能当收集或执行通过。未安装新依赖、未发GPU/HTTP。
- 原生CI选择器命中`tests/test_fused_experts_impl.py`、`tests/test_fused_moe.py`和`benchmark/test_fused_moe.py`，mode=smoke。当前冻结capabilities没有thead runner，非thead新增测试会skip，不能用NVIDIA绿灯代替PPU验证；本轮不改CI。

## 性能效果

`not_run`：本轮不运行算子GPU、模型性能或GPQA。op067的约2.47–2.54ms差值是旧策略的冷缓存单层诊断，不作为最终PR的新测量，不宣称线上已恢复或11题超时已修复。

## 决定、风险与回退

仅保留独立可审阅补丁，`pr_readiness=needs_revision`，直到目标硬件对最终代码完成必要数值／graph验证并核对提交基线。删除自动布局策略可能影响其他thead形状性能，须在后续硬件矩阵明确未测风险。不扩到Plugin或其他平台。原克隆和线上文件保持原样，回退仅丢弃新克隆内本轮两文件diff，无服务操作。

## 外部证据

- 本地独立候选根：`/private/tmp/qwen38-moe-transpose-pr-20261023.WXOz1n`，拒绝复用主线程PR982克隆；生产源SHA与旧冻结匹配。
- 原克隆：`/private/tmp/moe-fgv-pr-20261022.lgc4aR/repo`，已有两个alignment未提交改动只读保留；新候选从其已提交HEAD克隆，最终补丁仅包含本轮两文件，不携带或撤销PR982。
- 连接预检失败：本地Ansible RPC服务未启动；沙箱外连接申请被权限审查拒绝。本轮不绕过拒绝，不通过其他接口访问远端。未核实时不得宣称容器已部署。
- 本轮不创建定时任务、PR、commit或push；不改主线程当前候选／next_action。
- 最终vendor源 SHA `cac5b98907033f3efe3e7cb63fedadfac92fd8798a29954cd4111a36f81e939b`；测试 SHA `fa0751a8685a65554db4495dcbebe8153badf75553917c357fd4685b552d74e9`。
- 根目录`thead-moe-original-weight-layout.patch` SHA `130c83256b9d685c48ae021226c9c53b23acc40aa460c7c96252224da97cbf21`，可在保留PR982改动的原克隆上通过apply-check（未实际应用）。
- 根目录`test_host_contract.py` SHA `17b8037626cd36deb3efd74fc074607f41267ac5e939228f7ebc1737b861a850`；`cpu-host-contract.xml` SHA `818d280204fac4e27c9ed62b95649f1831ed83b3c357994813ae468e420b0a40`。
- `baseline-fused_moe.py`与`baseline-test_fused_moe.py`分别匹配原源807d12ce和fb27592d，回退原件保留；原PR982克隆两份alignment差异未变。
- `PR_BODY.md`为未发布正文草稿；明确最终补丁硬件未验证、非合入就绪、不声明模型性能或超时恢复。

## 2026-10-23 续行授权：容器两文件写回及独立设备验证

用户在本侧对话明确回复“请继续”，对应上一条询问的“写回目标容器并做算子／graph小范围验证，仍不重启8010、不访问8035、不提交推送”。本节在执行前冻结并取代上文仅本地阶段的执行限制；不继续或调度主线程的其他计划。

- 目标仍为PPU-07容器`qwen3.8-flash-opt-ppu07-20261015`。只读连接预检已在新确认后通过；8010监听仍API1693692，后续必须用start/argv/health/空闲和计数绑定，不能仅凭旧PID。
- 当前容器HEAD b4d3382bb04da4e0ab444849697865b4d5fcd86e，已有4份PLE/alignment改动；两目标文件分别与807d12ce／fb27592d基线完全相同。仅`/mnt`共享挂载，`/opt`真实目录为容器私有层；不复制覆盖整个源码库。
- 远端新根E：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/operators/op-068-thead-moe-weight-layout-fix-20261023`。父目录已核规范路径、owner0/mode755、剩余约5.7TiB；拒绝覆盖任何已存在E。只在E放命令、payload、备份、隔离cache、测试原件、完整合成输入／reference／输出PT、日志和manifest。
- 写回前保存两份原文件及mode/uid/gid、三repo HEAD/index/status和完整source事实；每次原子替换前重新核对原SHA。只替换vendor `fused_moe.py`与原`tests/test_fused_moe.py`，其余源码、现有修复、采样、调优、黑名单、服务启动配置不变。
- 不重新安装、不重启或热替换服务函数。8010仍使用原已加载模块／graph，不宣称磁盘写回即在线性能恢复。全程0completion请求，0模型GPU工作。
- 设备验证只使用物理15（新独立进程逻辑0），预检86368/98304MiB、0%util、仅原TP7 worker；只借空闲余量，额外进程峰值reserved上限2.5GiB。服务身份／health变化、running或waiting非0、计数变化、磁盘不足或预算超限，停止自有验证，不操作服务。
- 一次collect-only确认恰50项，再一次`pytest -k thead -x`只执行新增50组合，不跑旧大范围矩阵、不重试失败case。FP16/BF16、M0/1/8/12/13/64/128/256、合法leading padding、多层对象更新和16个graph／64次变化与恢复replay；不额外跑benchmark，实际计时只能记验证耗时而非性能。
- 最多30分钟GPU验证、全量合成PT预算32GiB；新pytest cache禁用，JIT/Gems/SQLite/VLLM cache固定E内独立根，PYTHONPATH为空，无库覆盖，不清旧cache。pytest cwd与所有报告／临时目录也在E，不向源码目录写测试产物。
- 取证插件仅包裹测试输入／CPU oracle及断言，保存完整合成张量与误差；记录原生graph capture/replay入口计数和实际函数来源SHA，不修改生产计算函数／kernel／selector。CPU oracle可对已复制的相同CPU值运行，容差仍rtol.05/atol.01，附加relative-L2<=.03作为预冻结诊断守护。
- 首错保存并停新增case，保留原件，不强行通过、不自动重跑；源写回和测试失败不触发服务回退／重启。最终只允许说明算子级通过或incomplete，模型minimal/全量精度/端到端性能仍not_run，acc019无新gate。

方法：`key-operator-analysis`＋`e2e/accuracy / minimal-regression`仅算子子集；前台持续监控，不创建侧对话不支持的定时任务。命令SHA在执行前补入本节。

执行前已保存并完成6文件AST检查。`E/commands/`中：control.py `ce6ecbf1eff1d3ac2ca077829bb07e5e40550d7985b069f163773458e267486a`；deploy.py `da903e3a8ce1fd1dae9b2932d522c9c42ade41576774353f085e01e5f18ce961`；gpu_check.py `e79c14113fbedffe4543ce833354b3999e979bbedfe70938e929c3b57bd5061e`；common.py `42261dba17aab140bab9a59b55a9bc1b808d7e30b460180cc33083c9ffaec752`；source_probe.py `0bb91d5430202f9812e90c54569766c2c72cb1e484bdcc2e1d5f5f4e7db94c20`；transport.py `afbec4d09d44004dcb4f70c3c7a986c0950ececa369706ea151cea48616d54b9`。payload仍绑定本节之前的源／测试／patch SHA，不混入PR982。

先仅一次运行本地`python3 /private/tmp/qwen38-moe-transpose-pr-20261023.WXOz1n/commands/transport.py`，排他USTAR staging并回读所有字节SHA；其后仅一次Host `PYTHONDONTWRITEBYTECODE=1 python3 E/commands/control.py`。control只读绑定→备份／写回两文件→collect50→单次50项验证→冻结；无服务启动、kill、重启、GPQA或benchmark入口。旧acc019 helper只按固定SHA导入其runtime/metrics纯只读函数，不调用旧prepare/launch/run。

**权限审查结果与收窄（执行前）：** transport已排他staging9文件且SHA全部回读一致；但组合control的执行在创建进程前被拒绝，理由是物理15与8010共享，GPU测试仍可能竞争／OOM影响服务。因此原control／deploy／GPU测试均未执行，绝不换入口重发被拒的GPU动作。完成不受影响的已授权源码写回：新增完全CPU-only的`E/commands/cpu_writeback.py`，SHA `16919ffb1a2463bd1aebf2bc23326d677073ad62d6196eb8eddd86d0e5f4b203`，仅source/runtime只读→两文件备份与写回→CPU一致性审计，代码中没有设备查询或GPU任务入口。先用本地stage_cpu_only.py（SHA `a79ead4479f99bed10c66ba1ca92f36d1d856f745f3433ccd5903e60d0d11ada`）排他保存这个文件与独立SHA回执，不改原STAGED或任何既有脚本；再仅一次执行CPU-only命令。GPU验证继续blocked/not_run，等待明确共卡风险批准或独占设备，不能声称50项已执行。

CPU-only单次执行返回`source-writeback-and-CPU-audit-passed-GPU-blocked`，两文件已写回、原件在E/backups；source-after SHA `2c8096dbb5ebb5baf925920ca55315601f1fef127468e6231486a876ca1e4e04`，online runtime和计数不变。终态后另存只读CPU核验`E/commands/audit_cpu.py`，SHA `e26945365b686c45de5256e986b81d2756eeedb48c6e3707512110383e15e88c`；本地audit_transport.py SHA `bdc8f3cead91d931758f7cc48984a68c2146ae5e610557905a7e7c53966c42e1`仅排他保存并执行该CPU审计。它核manifest、备份／当前源SHA与mode、纯AST、原controller退出、原GPU controller／validation／cache均不存在，以及新取source/runtime仍与写回后相同；不运行PyTorch或GPU。

### 源码写回终态与独立回读

- `cpu-audit-001/report.json` SHA `2dc04fcceec9a7d1c487f0c3e522df49b8dbff93df0e310ccba770146f20da94`，原26个manifest成员全部SHA／size回读通过，原manifest SHA `195e04b4598d049bc41865fe9f09330997eabd4cb72d5af187941be52aaeff5d`。CPU controller已退出；原组合GPU controller未创建，validation、cache与GPU子进程回执均不存在。
- 当前容器vendor源与测试分别为cac5b989／fa0751a8；两份备份分别为807d12ce／fb27592d，原mode644、uid/gid均保留。严格AST再次证明除删除的自动转置策略外，生产函数／kernel／selector全同；原测试AST无删改。
- 三库／engine／模型元数据／tokenizer／权重stat清单、BF16与既有修复、原repo HEAD/index不变；完整source快照只允许vendor一项源码hash变化及该repo新增两条worktree状态，已严格核验。新取source-current与写回后相同。
- 8010 API1693692/start537709560/argvSHA c146e2da与原实例完全一致，health200、running/waiting/KV/preemptions均0；prompt104482/generation3552451前后当前不变。没有新推理、GPU测试、重载、停止、8035访问、commit或push。
- **当前仅磁盘源码修复完成，独立算子设备最小回归和服务最小回归均incomplete／not_run；不能把源码写回当成运行中的8010已切换，更不能宣称超时或端到端回退已解决。** PR候选继续needs_revision，正式精度阻塞仍为acc019 failed-score，无新gate。
- 下一步必须由用户明确指定独占空闲设备，或明确接受与8010共用物理15的竞争／OOM风险（已提出额外reserved上限2.5GiB、空闲监控和30分钟预算，但不能保证零影响），再决定设备验证。未获该选择前不启动任何GPU流程，也不自动恢复／重启服务。
- knowledge_delta=none：这轮新增的是工程源／备份一致性证据，没有新算子数值、graph或性能结果；不改算子稳定知识或复用旧op067为最终补丁通过。

## 2026-10-23 新授权：停止原8010后独占物理15验证

用户明确“你可以把原来服务停掉验证下”，授权本侧对话精确停止8010以释放设备。此授权取代上述共卡方案：不再与服务共卡；不重启／恢复任何服务、不访问8035和物理0–7、不提交推送。停止后保持8010关闭。前次容器内检查宿主PID失败属于命名空间差异；宿主机重新核对原API1693692/start537709560/argv c146e2da身份与健康空闲、计数均未变，并非服务退出。

新执行根`E/validation-stopped-001`拒绝覆盖，原E manifest、CPU写回及失败审批记录保留。新controller保存当前精确source／三库HEAD-index／容器边界／原API argv与白名单环境、API子孙树及日志边界；重新核对空闲后使用pidfd仅向该API发一次SIGTERM。最多180秒等待已绑定owned tree自然退出及8010监听消失，不强杀；物理15无其他进程、used<1GiB才启动测试。若排空不成或源漂移，停止，不启动GPU验证。

测试范围保持原冻结50组合、FP16/BF16、16capture/64replay/110数值检查、2.5GiB owned reserved、32GiB PT、30分钟：collect50后单次run，首错停新增case，不复测、不改生产数学／选参。新GPU守护只查8010是否意外重新监听与自有资源；宿主每5秒只查物理15并绑定测试进程argv／独有环境标记，不碰其他端口／设备。使用新独立cache与输出目录，所有完整输入／reference／输出PT、原生JUnit与JIT哈希保留。方法仍为key-operator-analysis及accuracy/minimal-regression算子子集；服务minimal、正式模型精度和性能仍not_run，无新gate。

执行前保存命令：`E/commands/stop_validate.py` SHA `cffa662c80b2959ea3be81c4772da6cb995b20839575f2b42450afbcd906e716`；`gpu_stopped.py` SHA `723e3260b695a567ec5860d8ee0646d0e11d899c6010411d3d17fa3f107d405b`；本地`stage_stopped.py` SHA `08790ff3b4a8d1472b9797e5ba2a55dabd237a56f9a1e11f378f828b0f69ce27`。先仅staging两文件和独立SHA回执，再单次Host `PYTHONDONTWRITEBYTECODE=1 python3 E/commands/stop_validate.py`；不执行原被拒的组合control或重新写回源码。

原controller已退出0，精确API单次SIGTERM自然排空，0新服务启动。一次collect确认50项后，一次run实际50passed／16capture／64replay／110数值检查，最大绝对误差0.00408935546875、最大relative-L2 0.0060572531，峰值owned reserved 1283457024字节；完整PT 10952331698字节。原controller source-before/after相等、8010保持无监听。此处先记录原生结果，独立CPU审计尚待执行，不先宣称终态证据完整。

终态后新保存并仅CPU执行`E/commands/audit_stopped.py` SHA `49c55047b78372a4e88353498dc6a6fedf5962a63c7d36c2e8690b1abab1b2f5`：核原26成员及新manifest全量size/SHA、50项各setup/call/teardown通过、每graph恰4replay与JUnit；从每条断言链接的完整CPU输入重建110份原CPU oracle，逐字匹配保存reference后重新对actual做相同容差检查，无GPU初始化；再核source/原进程退出、8010无监听及物理15空闲。审计另存terminal-audit-001，不覆盖原manifest、不运行任何推理或设备算子。

### 独占验证终态：算子子集passed，模型／性能未测

- 原API单次SIGTERM自然退出，15:21:00+08已无8010监听／原owned tree活进程，物理15为1MiB／无进程；最终回读仍无监听。没有新服务启动／恢复、强杀或容器重启。
- 实际函数对象来自canonical `/opt/FlagGems-vllm/src/flaggems_vllm/runtime/backend/_thead/ops/fused_moe.py`，SHA cac5b989；测试fa0751a8，PyTorch2.10.0／pytest7.2.0／PPU-ZW810E，PYTHONPATH为空。完整source前后及CPU当前严格相等，三库／engine／模型元数据／权重stat／HEAD-index与已有BF16等修复未变。
- 原生单次collect50、单次run50passed（无skip）；16个graph各1capture＋4replay，输入／权重修改和恢复皆观察到当前值；累计110次数值检查，rtol.05／atol.01及relative-L2<=.03全通过，max abs=.00408935546875、max relative-L2=.0060572531。没有调用受禁止的permute_copy／mem_get_info。不是逐kernel trace、不是模型级graph验证。
- 峰值owned reserved=1283457024字节（约1.20GiB）；完整合成输入／reference／输出PT=10952331698字节（约10.20GiB），原生JUnit、各case与JIT原件完整保留。未运行任何benchmark，测试耗时不能作性能结果。
- 独立CPU审计核945个新manifest成员及26个原CPU成员全部size/SHA，通过50×3原生阶段回执、每graph四replay、原进程／controller／docker-exec已退出、source稳定；对110份保存输入CPU重算oracle均逐字等于原reference，再对actual复验同一容差。没有CUDA初始化、推理或新设备计算。

证据根为`E/validation-stopped-001`：`STOPPED.json` SHA `8678d71bd7d9e81786bf2fd75d7c16202f71f17a2c3d235bd85fa628c9e4f663`；`run/SOURCE.json` SHA `db90a6bfbbfe0e31b1a84d4a4e451dba755f9c449c844c4a989840ee2dc29524`；`run/FINISHED.json` SHA `8ea87a1735ca8e1e95c03f5a6958caf284de04ab894ec620bb585e62e9abb3c8`；`FINAL_SUMMARY.json` SHA `765b1d42fdc9b46faf9c3fb536c49493983c8d06dfe2ef7a01ae766071cde003`；`manifest.json` SHA `c90c3465573c194024a1d6ef244c0d5f23e0f67965a3dc55239b7d08cd373c8c`；`terminal-audit-001/report.json` SHA `822cc798fee1fd49a9d4d94c2028b3c136d4e18337ac8f206ccbe490354d9ea6`，其manifest SHA `e89476384f8c33ac7d73d834acbd87d9c174e958934e916b4a0357efa36cfd2d`。

决定：保留两文件修复／回退原件与现有算子修复，形成有目标硬件数值与graph证据的独立PR审阅候选；提交前仍需核对当时上游基线／CI。此次测试为FP16/BF16未量化、E512/I80/topk10、H128（边界矩阵）和H1024/M8 GEMV哨兵；FP32、量化、其他平台／shape性能未实测。**模型minimal、端到端性能及GPQA均not_run；不能宣称11题超时已解决，acc019 failed-score不变，无新gate。** 不自行恢复8010、不创建PR或提交推送；原启动argv／环境白名单、回退原件均已保留。

knowledge_delta=confirmed/refined：旧策略成本机制延伸为最终删除版的明确生命周期回归：不靠隐式复制／mem_get_info仍能覆盖两布局、naive/aligned/GEMV边界及同地址权重更新后的changed-state graph。下一次布局缓存修复首先覆盖多个live权重对和权重修改／恢复replay，而非只验证同一静态输入重复输出；不扩大为任意shape或模型吞吐不变量。

## 2026-10-23 独立PR发布

用户主对话明确“我已经修复该问题了，请你将该问题的修复给flaggems-vllm提交一个PR”，授权本次commit／分支发布／PR创建。PPU-07连接检查通过后仅只读获取源码与原回执；两文件SHA逐字匹配上述最终设备验证的cac5b989／fa0751a8，独立CPU审计报告822cc798与原summary765b1d42再次回读一致。未访问8035、未发GPU或推理、未改容器或服务状态；保持此前服务已停决定。

从当时上游main `d3214ceefc921e688196f916560c24ad805575a9` 新克隆到 `/private/tmp/fgv-moe-pr-20261023.0HARVh/repo`，源／测试基线与原验证基线逐字相同。仅应用本修复，6项CPU host／AST契约、改动文件pre-commit全部适用hooks、54项CI工具单元、CI pin和diff检查通过。查重未发现相同修复PR；#959／#982与已合入QSA修复不重复提交。

已发布fork `ZenithJoyH/FlagGems-vllm` 分支 `fix/thead-moe-original-weight-layout-20261023`，初commit `63fc84fa9854c838c33696ea369b0f66b49d2370`。首轮rule-check因现有模块级marker未被脚本识别失败；仅对新增三类测试加冗余 `@pytest.mark.fused_moe`，没有修改CI规则／测试计算／容差或生产源。Python3.12重跑所有原rule-check脚本通过，AST剥除三个marker后与硬件验证测试完全相同。macOS默认Python3.9不支持该CI脚本的类型语法，最初本地调用报错；改用已有3.12环境，不修改工具源码，不把该报错当算子失败。

后续commit／当前head `058056c33d56a129372e9978613d3b4921f55832`，tree `318d74fbbdea578edfb7e0cf74795c5c869b7c65`；生产源仍cac5b989，提交测试SHA `466ea73dd22c306e9412c5ffd4e83b647f29e3847c3e65fa25bfe6301f246f2d`（仅marker差异，容器测试未写回）。PR #989为open／非draft，相对main仅2文件 +150/-65，无合并冲突，已附当前聊天。首次CI失败保留，新head CI待回执，不冒称全绿。PR正文列出既有50passed／16capture／64replay及未测的FP32、量化、其他平台和模型端到端范围；不使用op067旧倍数作为最终补丁或模型收益。

本地发布计划与正文留 `/private/tmp/fgv-moe-pr-20261023.0HARVh/`；原容器修复／测试／备份与远端验证产物全部保持。`pr_readiness=ready_for_review`仅表示可交维护者评审，不是正式精度或性能验收通过；未恢复8010、不新增模型gate。

15:49+08回读新head CI：rule-check run39920154276已success；basic ci run39920154430仍in_progress。旧首轮失败不删除、不重跑，无全绿声明；PR保持正式open、等待维护者review。

随后终态回读：同head的rule-check与basic ci均completed／success；code style（含完整pre-commit）、CI helper／target selection通过，NVIDIA和non-NVIDIA设备jobs为skipped，不能计硬件通过。已把准确CI状态同步PR正文。发布回执在新PR工作根`publication-result.json`；本轮仍无设备重测／容器或服务操作。
