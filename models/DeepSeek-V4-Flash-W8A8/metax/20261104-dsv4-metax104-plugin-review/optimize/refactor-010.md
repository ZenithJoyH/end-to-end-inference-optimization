# refactor-010：三库适配代码整体收敛

当前结论（2026-11-06 23:09 北京时间）：**三库源码收敛、安装及暂存区统一已完成；GPU运行验证待执行。** 独立审计确认 Plugin641/FGV1189/FG6614 共8,444个普通文件和4个既有符号链接、权限、HEAD与index blob均匹配；安装前后无18001服务，本轮未启动/停止/重启服务。


用户要求：完成整个适配代码的收敛。范围为 mx-104 整改容器 deepseekV4-flash-refactor-20261104 实际安装 Plugin/FlagGems-vllm/FlagGems；保留必要模型语义、当前数值及公开契约。不重启服务、不提交推送，不改 vLLM、编译器、权重或缓存。

## review-refactor-010 规划检查点

ref006/op004 已有 GPU/精度历史；ref007有 GPU/dispatch/graph/model 最小验证；ref008接口归并与ref009配置归并已安装，只有CPU证据，不能继承旧版本GPU结论。旧性能目标已按用户暂停，不恢复自动benchmark；此次无累计性能收益结论。

优先级：1. Plugin模型/配置/dispatch单一来源及死路径；2. FGV主线接口复用、数值backend私有与重复封装；3. FG仅保留必要ATen兼容，核清暂存/工作区遗留。先冻结当前全文件SHA、工作区/暂存diff，再并行审查真实调用者。只能在调用契约、错误/fallback和math AST证据支持下移除或合并，不为减少行数改变数值算法。

验证计划：当前源码AST/引用闭包、既有CPU契约、针对共享路径的反例和幂等测试、工程lint；完整差异审查、严格SHA守卫安装及备份。GPU数值/真实dispatch/graph与模型验证保持待执行，不启动服务或新增GPU请求。失败保留证据，不跳过断言或放宽契约。

远端根：`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/converge-all01`。初次只读检查18001无API进程、health不可达；下次安装前须再次核验。

## 组合冻结与应用计划

{"package_sha256": "3c433c7f6217d9ea1cd844388c87e594a495be5718425b1f0fd052243c3df19f", "manifest_sha256": "5429691c4470be26a492ce6f99fa073256ed5cdb83d07047fe81ccbce7ea7d38", "commands": {"stage01.py": "5d014a713017b4ab2be6d75eceb1c998a0b6422e3846cc21fc63de0ea554873e", "apply03.py": "1efc649e69d0c5d6da0fc647c32f16f5aebea789703b75ebf68158960722bd06", "cpu-suite02.py": "c3822ba1316cb538dc04e803822148e18e48322d67433203155c97639a04f010", "dispatch-cpu02.py": "fa3f46f528441be15c9f544b1a5c92da2c312245093aa29e4f15fd7502f88146"}, "paths": {"plugin": {"paths": 13, "production": 10}, "fgv": {"paths": 11, "production": 5}, "fg": {"paths": 2, "production": 1}}, "install_guard_tests": 9}

三路审查与独立交叉审查通过；原始全部diff/每文件SHA冻结。精确26路径，三库原index/原文件先备份，再CPU候选与安装双重检查；仅本任务冻结diff与新路径的index统一，HEAD不变、不commit/push。每次写前检查无API及旧SHA，观察guard不是对用户另起launcher的原子互锁；本轮不改启动器，不声称跨文件原子更新。源码迁移影响JIT路径，旧GPU证据不可充当新门禁。apply01/02与input01/02仅本地审查superseded，未远端执行。


## 安装前 CPU 门禁发现的遗留测试

首个 `delivery01` 在候选 CPU 检查阶段停止，`source_paths_attempted_rollback=0`，安装源码与 index 尚未写入。`test_deepseek_v4_layer_boundaries.test_autotuner_is_not_mutated` 仍调用已删除的 `local_autotune`；before/candidate 的 `sparse_mla_policy.py` 相同且实际消费者只使用 `local_launch`。保留原失败与 input03，不恢复未用生产 API；修复测试以验证多个局部 launch 绑定独立、原 JIT/wrapper/config 不被改变。将使用新 input04/delivery02，并重新执行完整候选/安装 CPU 门禁。该失败不是 GPU/模型故障。


修正后完整本地 CPU 套件 162/162 通过；最终27路径=Plugin14/FGV11/FG2，其中生产文件数仍16、删除3模块。新冻结 input04 package SHA `68f50e5d29bc1cb7d6652fcff75260e6f0631ada4946991a17cb20d6293c240e`；manifest SHA `d181f3d1690980a58c4e3e1b7bccde59aa96e6fdcb54ccd0f9a3808657a73966`。新远端 `commands/ref010-stage02.py` SHA `b94414e8db883ad24d4e0d48b1be6cc64a31e5e033f2dde42a8e9a02ee0e6d6b`、`commands/ref010-apply04.py` SHA `21dda3dc5d56467048f1006bf45c104e164e06614174a3b3a7ea76d5b53e4082`；apply04只更新input/delivery路径，不改安装守卫。旧input03及delivery01不覆盖。


## 优化内容与适用边界

本轮属于全适配维护收敛，覆盖 Prefill / Decode / Mixed 共用的模型组织、dispatch 和算子封装；没有新的性能优化假设或收益门槛。此前 ref008/ref009 的当前 GPU 证据缺口保留。

| 组件 | 本轮收敛 | 必须保留的边界 |
|---|---|---|
| Plugin 模型和 Attention | 删除无消费者的 MTP buffer 分配/复制；`inputs_embeds` 对齐原生首 rank 语义；prefill chunk 继承原生单一常量；删除 `cublas` 误导别名，直接使用原 CachedOp key | speculative/MTP 仍构造前拒绝；原生构造器没有所需工厂扩展点，不能直接回退 native MoE/Attention。INT8 生命周期、TP/通信、metadata/workspace 仍归 Plugin |
| Plugin indexer | 删除只转发 CachedOp 的过渡模块；三项 dispatch 在真实调用者集中；移除未暴露且未用的 graphsafe=False CPU 同步诊断路径 | 实际 graph-safe 分支和非 MetaX native fallback 保留；不新增任意布局/FP4支持 |
| Plugin dispatch | 清理未读写的 failed-impl 状态与私有方法，保留公开兼容查询/清理 API；纠正旧“执行失败后换实现重试”的说明 | 仅执行前选择或fallback；已执行实现抛错继续传播，不跨实现重试；外部 policy/OOT 选择不变 |
| FGV | 删除两个旧 sparse_indexer 聚合模块，将 MQA/paged MQA/Top-k 私有实现归入对应公开算子族模块；修正 benchmark 的已删除公开名及 keyword-only `out` 调用 | 11 个迁移函数 AST 相同，全库1415个 JIT AST 多重集相同；不新写数值 kernel、不改公开签名、配置键及调优策略 |
| FG | `pad` 动态边界绑定限于 MetaX；其他平台恢复本 HEAD 的代码生成 | MetaX生成源码保持；必要的 zeros 绑定、mm/addmm厂商配置与错误传播保留；仅5个生产差异文件继续存在 |
| 测试与 index | 修正失效 local_autotune 测试，验证现行 local_launch 独立绑定；清理暂存区与工作区历史不一致 | 保留原文件、三库原 index 和完整patch；不恢复已弃用的旧FG实验，不通过删测试减少改动 |

FGV common/NVIDIA文件、本轮 op004 gather 修复、公共导出和operator catalog均逐字节不变。`mqa_logits`仍是当前新增的语义族，不能声称NV已提供完全相同的厂商扩展。内部历史tuner key仅用于既有缓存/策略，不作为公开API命名。

以下数值组合不能仅为减少代码而替换：BF16 inverse-RoPE的中间舍入与INT8投影不等价于NV FP8融合接口；packed BF16 MQA在MMA前的舍入、MODEL1稀疏MLA真实头数及workspace、mHC cast顺序也有明确契约差异。全部保留理由和逐项主线复用矩阵见外部 `input04/fgv-audit01.md`、`audit/plugin-model-review.json`、`fg-audit01.json`。

## 正确性与工程检查

- 本地组合CPU **162/162**：Plugin边界/配置/桥接/模型45，FGV公开API38，FG4，实际manager/registry/policy标准测试75。仅隔离包入口、设备发现和I/O dump；该75项不冒充GPU实际backend命中。
- FG rank1..8 ×6vendor 的48项生成源码逐字节比较：MetaX等于当前实现，其他5vendor等于HEAD。Plugin支持路径5个indexer与15个attention函数，在明确移除未用诊断/别名归一后AST一致；不是全模型运行证明。
- 本次Plugin修改使用实际Ruff0.14配置检查；FGV Black24.8/isort5.12/flake8 7.1通过。FG已用Black24.8/isort5.12/flake8检查，但原库要求Black26.5.1，未执行该版本，不能称完整pre-commit通过。
- 安装守卫9项故障注入通过，包括路径逃逸/符号链接拒绝、原子写失败保护、index漂移拒绝、外部index.lock保留及发布后新锁保留。独立审查确认input03资产及守卫；input04仅增加遗留测试修正和新尝试路径。
- 当前组合GPU数值、真实dispatch、capture/replay、模型最小回归、完整精度和端到端性能均未运行。JIT路径移动可能影响缓存身份，`inputs_embeds`正确接线也需要后续运行验证；旧版本GPU/精度gate不得直接绑定本版本。

## 性能效果

本轮无同workload B/C/R性能测量，吞吐/TTFT/TPOT及累计收益均未知；未恢复用户已暂停的32K或旧OOM任务。没有用代码行数、AST相同或CPU测试数代替端到端性能证据。

## 决定、风险与回退

决定：保留已审查的维护收敛，按用户授权应用实际安装源；运行验证状态保持待执行。收敛没有将不可证明等价的算法强行替换为主线，依赖未发布、非MetaX设备CI和原有microbenchmark限制仍保留。

回退入口为本次成功delivery的 `backup/`：原27路径字节/模式、三库原index及head/index/worktree补丁。回退需先核验无活跃服务、精确当前SHA并仅恢复本任务路径，不能覆盖用户并发修改。此次安装未触及vLLM/权重/tokenizer/编译器/启动脚本，未清理或修改模型JIT缓存。服务观察守卫不等同于与用户启动命令互斥，本轮不改变启动器来隐藏这个限制。


`delivery02`：162测试本身通过，但dispatch CPU夹具在目标环境的自动平台发现导入vLLM，末尾隔离断言失败；再次0生产写入。不能将这次运行声明为无设备依赖导入的CPU通过；该子进程已退出，不作为GPU数值证据。新夹具只把设备发现固定为unknown，新增硬import blocker并关闭pytest第三方插件自动加载，原75标准测试/实际manager-registry-policy/全部断言不变。生产input04不变；tooling05独立冻结新helper和apply05，目标新delivery03。

执行前冻结：tooling05 package SHA `eb2cd5323e5c7b6f0af96e224b8beac5e51c4b1d5bd234305d54bf80ec176c27`，manifest SHA `138cfcb997c9a29b114fbe9a917802f6752947645eb868dfc30b644a8c720bbf`；commands/ref010-stage05.py SHA `e75b3085c58b09b4e06e772b03ee73644c5ae58a290496fff590579878364674`；apply05 `c480bb1277cbfcba5f83003f8667b0f22bbb61446c1dec67af304350651fdd50`，cpu-suite03 `7e4d05bf9f9266ea3170f06cdb8ceb59d20d0926da10d3e3b4bf381b57a7d8d2`，dispatch-cpu03 `70f5a122dc7d4a238e5288a7a9f0b97630cc423ea519ad5a13f2553b06c122c5`。没有改旧冻结资产、原生测试或生产实现以绕过失败。


`delivery03`：硬import blocker下候选/安装两套162 CPU均通过；最后Git暂存路径含先前已暂存删除且index/worktree均不存在的rename旧源，`git add -A -- <精确路径>`报pathspec不存在。控制器回退27路径，无rollback conflict；独立核验三库HEAD/index原SHA、所有regular source均恢复before。初次只读核验把既有4条symlink当regular文件，显示集合差异；逐项确认Plugin1/FGV3既有链接后纠正该统计口径，不是源码漂移。后续独立审计须从原index备份核验120000链接及目标，不静默忽略。

新的暂存准备仅过滤同时不在private index与worktree的冻结路径，保留private index里已经完成的删除，不扩大到全库git add。使用真实临时git仓库证伪staged rename、tracked删除、新增和无关staged保留后，再执行新delivery04。生产input04及162项门禁不变；旧三次回执和CPU日志保留。


最终编排修复的真实Git场景4/4通过；工具06不修改候选/原生测试，增加逐库stage-selection证据与literal pathspec。冻结tooling06 package `af200a05a9bffef60e0f1db55ff156fcdaa1bf3fd4cd23d5fae787735bf970e5`、manifest `a9ae77643c26d552e68bd6e1533f6a4da3573233a2405212ab4f7cb590a682d4`；commands/ref010-stage06.py SHA `81b47e3d91b897ffb362ec7032bbe08d81cb6135a479930145c48f88659268ec`、apply06 `84f9f8aa2ffb58f84b78d116ce634f6e8404762c80db35a896ee8c5c685afc4e`。index-stage-test01.py SHA `59ab0d9631d3d127e65d9318f24213f3c564dd18a1dd594850875d40fe396a59`，report `2a3ef13c3ba2baac11f8493347a6f77fd5f7a24fdafd503a88064a4b0984c0fb`，同存tooling06；新delivery04完整复核，不复用失败的成功子集冒充终态。


`delivery04`再次被raw index守卫中止并回退27源码：备份的普通git diff在前次原子回退造成mtime变化后自动刷新index stat。只读二进制审计 `index-refresh-audit01.json` SHA `7e7c0dd89d0c29bcb2c7ffc3e5854251ebaccea50883d92b9f6f8f6cae937906` 证明仅Plugin1/FGV11条目ctime/mtime/dev/ino/uid/gid/size缓存不同；mode、路径、OID、flags、扩展和其他bytes完全相同，FG原index完全未变。不是用户暂存内容被改写；先由新 `commands/ref010-index-refresh-recover01.py`（SHA `d9d3035e17633a91723bbc4d320bcc0cc05509596210d6b836c37165357d5e97`）重复固定SHA、二进制证据、全原源码/HEAD及无API检查后，CAS恢复原2份index字节；不放宽rawSHA门禁。

只读Git修复实测4/4通过：仅GIT_OPTIONAL_LOCKS=0仍会刷新，需同时命令级 `-c diff.autoRefreshIndex=false`；不写仓库git配置。新apply07 SHA `cf582559551637aacba192b591c2db4cd18727e9c1ab98b61c01ad12e307b124` 使用tooling07/delivery05，生产/测试源码、staging/CAS/回滚守卫不变；只读回归脚本SHA `990bf3f1eee2f228364c29e929c8de1cc65a0a5f383c327a56a55fc04f378fe5`、报告SHA `9909184219cd058d806dd3f1d6545af938755f599853b85778b82521a8d0c3c8`。


原index精确恢复完成：`index-refresh-recovery01/result.json` SHA `2beeffc79876f14f953b7972e0dc6109617c13d068cf05f4d67d496e93bfc066`，仅Plugin/FGV缓存字节恢复，原源码/HEAD/index全守卫通过，无服务动作。最终tooling07 package SHA `07e1508f8c79c90bdff0001fc84cb77a18530c15f9fbee3b2a7ceee3a8e454c6`，manifest SHA `fee0aa76c9cba38d552d5db6854ca4ba2926408584408a9ba01b6438ccde82c5`；stage07 SHA `55418b7e5bff8fc73e85f0a5f6da71957873a0fca2f70454385c053494dc2fbb`。将执行唯一delivery05；其before仍用最初冻结input04的原SHA，未改为宽松逻辑相等判断。


唯一delivery05已成功安装27路径，candidate/installed各162 CPU passed，index统一且无commit/push/服务动作。结果SHA `99a6493b040c016671202c260d6f335b4b8f6c637160f280353b46b89096ad7b`。随后独立审计命令 `commands/ref010-review04.py` SHA `712c6883996f4c05dfbecc78e7ed75f95026a5e90197204c3474fe14f829f784`：从before+changes独立重建全树，验证regular modes/SHA、原4symlink、不变HEAD、stage0 blob与worktree、两套原生日志/计数、脚本SHA和无服务状态；不重跑测试/发模型请求。


## 最终交付与外部证据

实际容器 `deepseekV4-flash-refactor-20261104` 的安装目录：

- Plugin：`/opt/vllm-plugin-fl`，HEAD `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`。
- FGV：`/opt/dsv4-sources/FlagGems-vllm-main-reuse-20261105`，HEAD `025f3181e19283885513255d143ca2ad55e8d897`。
- FG：`/opt/dsv4-sources/FlagGems`，HEAD `8200f71f51d784d54a5a51019cb955acb74d64c1`。

最终 `delivery05`：27路径（Plugin14/FGV11/FG2），删除3个过渡模块；候选与安装后各162 CPU通过，stage0 index内容与当前全部工作区文件一致，未跟踪非忽略源码0，三库HEAD未变，未commit/push。FG原来5处只在index中的历史实验已随当前实际源码统一，不把这些弃用代码恢复回来。

独立审计：`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/converge-all01/independent-review04.json`，SHA `0e4e9e11e7a7de6aa19f76c0a0b5aaa0ef94a98eee656aa1e8362217b20a64fa`。成功安装回执同根 `delivery05/result.json`，SHA `99a6493b040c016671202c260d6f335b4b8f6c637160f280353b46b89096ad7b`；原文件/index回退材料同根 `delivery05/backup/`。

同根 `input04/` 为生产候选与逐文件审查；`tooling07/` 为最终只读Git/精确暂存处理及测试；`delivery01..04` 失败、回退、成功子检查证据全部保留，不拼装替代最终完整门禁。只读校验不跟随4条既有符号链接，使用原index中的目标独立核对。原启动脚本SHA `f38a0f9769a4a04aab255f8b123c46533eb0899148bb012ad876172516e19ea4` 未变，保持ref009简化配置。

当前状态仅源码/CPU交付。新组合的GPU数值、真实backend命中、capture与至少两次新输入replay、模型最小回归、正式精度和性能均未重新验证；不能用ref007的历史123项或旧GPQA分数覆盖。后续按用户要求单独冻结验证范围；本轮没有启动GPU任务或恢复旧自动评测。现有维护问题以本条与结构化state当前字段为准，前文“准备/将执行”为保留的历史过程。


## 2026-11-09 容器维护

用户明确允许重启整改容器以清理PID1 sleep收养的223个僵尸进程。只执行一次容器restart；即时状态断言失败回执保留，随后独立核验同容器ID/镜像/挂载且running，僵尸223→0，模型API/worker未运行、18001不可达。未启动模型服务、未修改适配代码，不产生新GPU/graph门禁。当前PID1仍sleep，未在本次维护中改变容器入口。

外部回执：`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/maintenance-zombie01/verification01.json`，SHA `b3046f4a349880d5f7ba0c519ea7417656592c0677830338816d3882e399fc2d`；命令及SHA见state的container_maintenance_20261109。

## 2026-11-10：当前FGV逐算子优化机制分析

范围：mx-104 / MetaX C550 TP8 / DeepSeek-V4-Flash W8A8。只读核验实际安装 `/opt/dsv4-sources/FlagGems-vllm-main-reuse-20261105`：HEAD `025f3181e19283885513255d143ca2ad55e8d897`，1189个普通文件与ref010最终manifest完全一致，无不同路径。下面以该固定主线为对照，结合早于主线收敛的历史实现记录；不把主线本身已有优化冒称本轮新开发。不修改库、服务或启动参数，不发GPU/模型请求。

本次采用本地key-operator-analysis的阶段/语义/调用链/证据方法，属于既有代码和既有结果的机制审阅；没有新的Profiler归因或性能实验。Prefill与Decode按实际token/shape分支区分，Mixed会同时触发两者。源码静态分支可用不等于当前服务实测命中；表中“收益机制”均不是本版本测得的加速比。

### 逐算子明细

1. **`scaled_int8_quant`：W8A8激活量化，Prefill/Decode共有。** 核心是每行absmax/scale与round/saturation。当前删除重复MetaX内核，经Plugin CachedOp复用根包common API。主线已有single-pass寄存器保留整行、main+tail避免不规则宽度填充等路径，它们不是本轮新增；single-pass相对双遍历可将输入读从约2×M×K降到1×M×K，但寄存器压力仍随行宽增加。实际改动为设备/layout/空行/static scale/zero-point契约、NaN转整数显式归零，以及MetaX标准YAML单配置，防捕获时benchmark/同步。固定配置牺牲部分shape最优性；历史30shape SDK对照中M64/K4096 FGV4.450µs、SDK2.587µs，M4096/K13824 FGV0.241ms、SDK0.197ms，不能称全面加速。来源 `ops/scaled_int8_quant.py:455` 与MetaX tune YAML；历史ref003。

2. **`silu_and_mul_with_clamp`：MoE两次GEMM之间的激活。** Plugin从原生compiled函数切到CachedOp→FGV既有公开融合接口，复用caller-owned out。算法为clamp gate、clamp up、SiLU与乘法，精确顺序见 `_silu_clamp_value`；没有额外发明第二套激活kernel。收益机制是避免中间结果和便于统一dispatch，但旧torch.compile生成物已显示可一次kernel完成同类链路，所以不成立“多个launch必然变成一个”的推断。新路径还会写BF16激活，随后独立INT8量化再读取；没有融合激活+量化。实际补丁修复fast-math下负零丢失，保持NaN/clamp语义和共享workspace非重叠视图。历史op003数值/graph通过；无匹配目标shape的新旧耗时归因。来源 `ops/silu_and_mul_with_clamp.py`、op003。

3. **`topk_softplus_sqrt`：MoE专家路由。** 对专家分数执行sqrt(softplus)、可选correction bias、Top-k与权重归一化，复用主线public API替代框架/FG自建评分。当前主线已有单warp/行的融合kernel，本轮不是新增该策略。相对HEAD的真实数值修改：hash分支使用log1p(exp(x))改善小值精度；非有限max时保证expert索引合法、显式传播NaN权重。该修改主要是精度/安全性，不能声称固定减少launch或提升吞吐；normal top-k和hash是不同分支。来源 `ops/topk_softplus_sqrt.py:35,119,186`。

4. **`moe_align_block_size_no_tle`：MoE路由排序和expert块对齐。** 目标E=256、连续路由、无expert_map和外部workspace。路由项数n<=512采用count+scatter两阶段，小decode批次避免完整大规模排序流水线；n>512用带初始化stage1并共享common stage2/3/4，不复制整个common算子。固定4warps/1stage限制C550资源使用，避免进程级编译器hook。代价是小分支会重复扫描路由，n增大会不划算，因此有明确阈值；其他expert数、map/workspace请求走原generic。这里只改善对齐，不是INT8 expert GEMM本身。来源 `runtime/backend/_metax/ops/moe_align_block_size.py:123`。

5. **`mhc_pre`：mHC残差混合前处理。** 特化BF16 residual[...,4,4096]、FP32 fn[24,16384]；投影、RMS、head变换/Sinkhorn及layer合成保持原cast顺序。T<=2048用split-K(2或4)提升小批并行度，再combine及layer；T=4096或T>=8192等已列分支用heads+layer融合，减少pre_scratch写回和launch，其他形状保留heads/layer拆分。不能概括为“始终一kernel”：fn→BF16 cast仍每次执行，小T有partials/square scratch，融合过大会增加寄存器/资源压力。非目标能力走common。来源 `runtime/backend/_metax/ops/mhc_pre.py:517,733`；使用现有6个私有kernel，未启用更改权重缓存或拷贝策略的草案。

6. **`fused_deepseek_v4_qnorm_rope_kv_rope_quant_insert`：Attention前Q/KV融合处理。** 复用已有QNorm、GPT-J interleaved RoPE及KV量化/写页缓存语义。大T>=512时MetaX program处理同一Q-head或KV槽的8个token，改善小program过碎与Q/KV工作不均，降低program数量；T<512回common，避免8token tile大量masked。D512中NOPE448量化FP8，RoPE64保留BF16，并保留scale字节格式。num_tokens/num_tokens_insert改runtime+do_not_specialize减少精确token数特化；不是去掉数学中必用的长度mask。不变更原地mutation/slot_mapping合同。来源common同名文件与vendor同名文件:35,174；大/小shape是可选路径，不能对decode小批宣称8倍收益。

7. **`cp_gather_indexer_k_quant_cache`：把paged indexer键/scale聚集到连续工作区。** 复用common并保留packed/pitched源stride。op004本轮历史修复是scale block ID在乘stride前转int64，避免高blockID跨层stride溢出；二分搜索用(batch+1).bit_length()覆盖B31/63边界。这是正确性修复，不是吞吐优化，也不是prefixON改变了数学语义。原15新增case中5失败、新18数值/graph通过，合法guard-storage复现；历史4shape微基准延迟C/B约+2.13%、+2.33%、-0.28%、-0.10%，没有整体加速。来源 `ops/cp_gather_indexer_k_quant_cache.py:86,92,158`，op004。

8. **`mqa_logits`共享BF16键分支及`fp8_fp4_mqa_logits`共享内核。** Query[M,64,128]、shared KV[N,128]，输出FP32[M,N]，数学为各head的ReLU(Q·K)乘权后求和。原两份prefill数值kernel合并为主线同一JIT的局部绑定：HAS_K_SCALE=False复用BF16 MMA，APPLY_ROW_MASK融合每行[start,end)，整个tile无有效键时直接填-inf并跳过dot；保持pitched/caller-owned out，row_shard的通信仍属Plugin。独立绑定不同launch配置，不全局修改tuner。已有FP8-query API在MetaX增加内核内E4M3→FP32→BF16转换以兼容当前编译器，避免额外转换kernel；有限E4M3可被BF16精确表示不等于与原FP8 dot全部累加行为等价，仍需独立测试。来源 `ops/fp8_fp4_mqa_logits.py:92` 和vendor `mqa_logits.py:17,90,104`。共享JIT减少维护重复，不能直接算设备加速。

9. **`mqa_logits` gathered分支：Decode每query已有独立FP8键工作区。** 以二维grid(row,key-block)一次调用覆盖多query，内核内先FP8键/scale按既有BF16顺序反量化，再dot→ReLU→head加权reduce→valid mask。减少Python逐query调用和反量化/加权中间张量；代价是gathered键本身按query复制/物化，缓冲量随M×N×D增大。Q BF16[M,64,128]、KV FP8[M,N,128]+FP32 scale[M,N]，N正数且128整除，越界位置-inf；不能替换成FP8-query接口而改变pre-MMA舍入。来源vendor `mqa_logits.py:159,200`。

10. **`paged_mqa_logits`：Decode直接读paged键。** BF16 Tensor query分支通过block table取FP8键/scale并完成相同评分，可以避开独立gather物化；完全超出context_len的block只填-inf，不读Q/KV、不dot。launch grid维持固定，长度判断在设备完成，适合graph replay。仍需写静态长度FP32 logits，无法消除全部padding带宽；随机page访问与输出量可能成为成本。tuple FP8 query仍委托common，BF16扩展是MetaX专用。它和第9项是由Plugin policy/next_n/head_dim选择的替代分支，不能重复相加收益。来源vendor `paged_mqa_logits.py:15,112`，Plugin indexer use_paged_indexer_logits。

11. **`top_k_per_row_prefill`：Prefill索引选择。** vendor仅保留pitched view/必要contiguous和非连续输出copyback，实际选择复用common非TLE路径。未用NUM_ROWS由constexpr改runtime+do_not_specialize，减少混合token数不断变化引发的编译特化；NVIDIA autotune NUM_ROWS key仍保留。历史固定dtype/config的69形状binder验证为B/C/R69→1→69，证明多余特化消除，不证明稳态kernel更快；也不代表跨dtype/config永远一个binary。普通pitched logits列连续时避免整矩阵复制，异常layout才转连续。来源common `ops/top_k_per_row_prefill.py:1347`及vendor同名薄wrapper。

12. **`top_k_per_row_decode`：Decode K512精确Top-k树。** next_n=1、FP32连续列、K512等条件下，每1024元素先局部选512，再成对归并至最终512。整块超出valid_len时跳过local topk；scratch预填-inf/-1保证padding。修正阈值ties：先保留所有严格大于阈值者，再取低索引相等者，避免按位置截断时漏掉后面的高分。代价是多层launch、每调用候选scratch及初始化；context很长会增大空间，不能说无分配或总优于通用算法。其他能力在执行前回原MetaX general；公开in-place/None返回契约不变。来源vendor `top_k_per_row_decode.py:17,51,96,135`。

13. **`flash_mla_with_kvcache`：稀疏MLA Decode。** MODEL1的512维QK/V保留MetaX packed FP8和extra KV/sink/有效topk合同。HQ16物理布局、单query、batch<=64等受限域用split-topk（默认4split），将一行长KV链拆为多个CTA，再以partial max/sum/acc做稳定softmax合并；half-D拆512→256、QK fold/block-diagonal MMA是为控制寄存器/适配矩阵执行，不表示改变有效head数学。real_num_heads屏蔽TP填充；caller-owned split workspace保持graph生命周期。仅acc[64,4,16,512]FP32约8MiB，另加统计及reduce开销，小batch/短topk可能得不偿失。未用Bsz scalar去特化，其他能力回原semantic kernel；dense/V32委托主线public。来源vendor `sparse_mla_decode.py:624,675,1014`。

14. **`flash_mla_sparse_fwd`：稀疏MLA Prefill。** 复用generic/TLE接口可用路径，针对headpacked BF16目标保留half-D、blockdiag和staged QK→PV。qk_states生成BF16局部exp概率和在线softmax rescale信息，pv_replay复用这些状态计算两个256维V片段，减少重复QK/softmax与单kernel超大live state；代价是P/A/F中间存取和第二阶段launch。这里的pv_replay是数值状态重放，不等同于CUDA Graph replay。P[T,ceil(Ksel/16),16,16]BF16占512×T×ceil(Ksel/16)字节，例如T1024/Ksel512约16MiB，分chunk/workspace预算属于Plugin，不能只看kernel时间。indices输出/statistics/caller buffer与真实head合同不能静态删除；ordinary3D与local2D是显式不同路径。来源vendor `sparse_mla_prefill.py:21,88,128,138,477,859`。

### 共用策略与范围澄清

- `sparse_mla_policy`是厂商launch元数据绑定，不是独立数学算子；复用主线JIT同时不修改全局autotuner/编译器。不能把它的清理当作单独一份kernel加速。
- 移除`gdn_chunk`导入时的编译器全局monkey patch是环境隔离修复；当前DeepSeek链路不走GDN，不计收益。
- FGV公开算子迁移/两个旧indexer聚合模块删除，是职责/可维护性收敛。ref010全FGV1415个JIT AST多重集保持，不能算又增加1415个算子。
- INT8 MoE GEMM使用Plugin的MetaX MCTlass路径；一般linear/mm策略在FlagGems而不是本次FGV清单。Gate BF16 F.linear→FP32 cast为继承路径，op002桥草案没有安装，不应列为已完成优化。
- 当前对照是安装所基于的固定main025，而非未经核验的2026-11-10远端最新主线。

### 如何理解累计收益与验证

输入评分计算约2×M×N×H×D操作，加权/激活还要额外工作；FP32 logits即4×M×N字节。即使消除gather或反量化临时，logits和后续topk成本仍在。mHC/MLA split用额外workspace和reduce换并行度，Prefill偏融合、Decode偏并行和减少固定上界浪费，不是所有shape都应融合得更多。

历史ref006有335项算子/dispatch/graph，ref007有123项及模型最小验证，op004有18+5和完整精度；它们是各自SHA对应版本的证据。当前ref008/009/010组合只有CPU/全源码审计，新GPU数值/真实dispatch/graph/model仍待验证。历史P4候选32K结果也不能当作本组合的B/C/R，更不能拆成每个算子的贡献。单算子B/C/R、同输入无profiler稳态E2E以及匹配实际分支的调用占比仍缺，不签发新性能结论。

本次结论：优先保留现有数学契约与库主线复用；目前可明确说明机制，无法为14项逐一填真实加速比。若后续做性能归因，应先验证当前组合GPU/graph，再测paged/gathered实际命中、MLA/mHC split与workspace、量化相对原生的真实shape成本；旧compiled SiLU和gather正确性修复不宜优先作为“大收益”解释。此为后续证据需求，不启动任何新测试。
