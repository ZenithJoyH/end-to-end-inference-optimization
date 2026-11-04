# sampler-import-001 采样补丁导入生命周期修复

- 当前：`completed`；决定：`retained`；分类：`framework/import-lifecycle`。
- 目标：`mx-104` / `qwen3.6-35B-verify` / `/data/Qwen3.6-35B-A3B-nomtp`。
- 场景：`not_applicable`；阶段：服务初始化与采样；本轮无性能测量。
- 基线：Plugin `release/0.2@7cb559947cb61fd8b69fa5027d8ec113e528a644`，保留原有 8 个文件中的优化。
- 正确性方法：[本项目 inference-accuracy-evaluation](../../../../../skills/inference-accuracy-evaluation/SKILL.md)，显式模式 `minimal-regression`；最小回归状态 `passed`，正式精度/性能 `not_run`，未签 formal gate。

## 优化方向与瓶颈依据

vLLM 采样模块尚未定义 `TopKTopPSampler` 时，平台加载触发 MetaX 补丁对该类的继承，造成循环导入。之后更新原模块符号也不会自动更新消费者通过 `from ... import` 保存的类别名，可能继续创建原采样器。本次使用 Plugin 的 vendor patch 和 ModelRunner 初始化边界调整生命周期；不修改 vLLM 源文件，不改变采样算法。

首版移除了 sampler eager import，但目标仓库的 6 项导入顺序回归实际得到 **4 失败、2 通过**。额外 import-chain 诊断揭示剩余循环：`PlatformFL.import_kernels → metax.patches → gdn_linear_attn → vLLM GatedDeltaNetAttention → layernorm → vllm._aiter_ops.rocm_aiter_ops`，此时 `_aiter_ops` 尚未初始化完成。失败及 traceback 已保留，不能把通过的两种顺序代表全部启动路径。

第二版将 `gdn_linear_attn` 的 eager import 同样延迟至 MetaX worker hook，在构造模型之前完成注册。GDN 实现不变。第二版 6 项新鲜导入回归全部通过；实际 TP2 服务的两个 worker 均成功构造优化采样器及各 30 个 MacaGatedDeltaNetAttention 实例。

## 优化内容与适用边界

实际生产修改保持 3 个文件：

- `vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py`：推迟 sampler 和 GDN 相关导入。
- `vllm_fl/dispatch/backends/vendor/metax/patches/topk_topp_sampler.py`：保留原始基类，提供幂等 `apply_patch()`，刷新已知消费者符号，同时保留显式导入补丁的行为。
- `vllm_fl/worker/model_runner.py`：仅 MetaX 路径，在构造 sampler 前执行补丁和 GDN 注册，模型构造前完成。

新增 `tests/integration/test_metax_sampler_lifecycle.py`。原始 guards、helper、采样器 `__init__`/`forward_native` 的 **7 个 AST 均一致**；shortlist/counting 两个 kernel 文件字节不变。

`apply_patch()` 刷新精确模块/属性清单中已加载且 `hasattr` 的符号：sampler 的 `TopKTopPSampler`、rejection_sampler 与 gpu sample states 的 `apply_top_k_top_p`。它不是全模块遍历，但当前实现也不检查这些位置是否已有第三方替换；因此不声称会保留这些精确符号上的第三方 override。非目标平台硬件尚未验证。

shortlist 条件保持：`qwen3_5_moe`、BF16、256 experts、hidden size 2048、vocab 248320、C550；输入为连续 CUDA FP32 logits，batch 8–64，同设备连续 k/p 向量，k 为 int32/int64、p 为 FP32。内部 width=64；不满足 shortlist 安全条件仍走原 reference。VL counting 与其他 shape fallback 数值实现没有修改。

## 正确性与路径命中

| 检查 | 当前结果 | 证明范围 |
|---|---|---|
| 原函数 AST / 两个 kernel 字节 | passed | 7 个函数/方法 AST 一致，kernel SHA 一致 |
| 第一版导入顺序 | failed：4/6 失败，2/6 通过 | GDN eager import 尚存在循环；原始失败保留 |
| 第二版导入顺序 | passed：6/6，0 失败/错误/跳过 | 第二版重新运行；首版失败保留 |
| 单卡数值及边界 | passed：25/25 | 原优化类与修复类数值保持；不代表完整服务或模型精度 |
| 实际服务实例、forward、shortlist 命中 | passed | 两 worker 优化采样器；真实 C8 batch=8，成功 shortlist 504 次 |
| C1/C8 smoke、graph capture/两次 replay | passed | 17 请求 HTTP200 且非空；FULL/PIECEWISE capture 日志各5/5；两个 worker 均成功 replay，合计至少512次 |
| 正式模型精度/性能 | not_run | 无 gate、无性能提升结论 |

单卡回归仅使用 `CUDA_VISIBLE_DEVICES=0`，进程已退出。原优化类由 `before/` 中原始 FunctionDef/ClassDef AST 原样构建，使用真正的 vLLM 原始基类；当前类直接实例化，配置字段来自实际模型 config，BF16 fixture 与真实 C550 检测使两者 `_use_shortlist=true`、`_use_counting=false`。未替换实际采样方法、未修改源码。

15 个真实采样对照覆盖 B1/7/8/64/65，以及 B8 的 k1/p0、k63/p1、k64 内部 fallback、全相等 logits 内部 fallback、部分 -inf mask、缺 k、缺 p、双 None、BF16、非连续 logits。对照使用相同输入和每行 generator seed；**token 相同，processed_logits 与修改后输入逐字节相同，过滤 mask 相同，generator 末状态相同**。

9 个 guard 检查覆盖 int64 k、空 batch、不同 vocab、k float、p BF16、k CPU、非连续 k、非连续 p 和 CPU logits。以上 guard 检查仅证明支持条件，不冒充这些无效/边界输入的完整模型运行。另 1 项核验原数值 AST 与 kernel 字节，总计 25 项，原生 JSON `status=passed`、`passed_checks=25`、`failed_checks=0`。

数值回归时的 sampler SHA 为 `a2310f381803bce9292b89d4386f157ce233737dd2be88ead23c832fd7775613`，与 `implementation-v2.json` 中一致；第二版的后续变化在其他两个生命周期文件。数值结果可证明这些未变数值文件的保持性，不能替代第二版初始化与服务回归。

实际服务取证使用远端 `observer/sitecustomize.py`，没有把观察器写入 Plugin 源码。它通过 Python profile 事件记录真实对象与成功返回，区分启动阶段和请求阶段；观察开销不用于性能评价。实际启动为 TP2/GPU0,1、BF16、模型长度4096、max-num-seqs16，prefix cache关闭，graph模式 `FULL_AND_PIECEWISE`、capture sizes `[1,2,4,8,16]`。精确参数及进程身份保存于远端 `service-001/launch.json`，不在本地固化瞬时 PID。

两个 worker 的实例类均为 `MetaXTopKTopPSampler`，forward绑定 Plugin 的 `forward_native`，`_use_shortlist=true`、`_use_counting=false`；各构造30个 `MacaGatedDeltaNetAttention`，证明GDN延迟注册也在模型构造前生效。

C1 smoke和两轮C8共17请求，全部HTTP200且内容非空，C1算术答案为2。C1实际shape为`[1,248320]`，命中fallback范围；C8观测到真实shape`[8,248320]`，两轮各252次成功shortlist、合计504次。C8显式`ignore_eos=true`、`max_tokens=128`用于维持cohort，length终止是诊断设置，不冒充自然EOS验证。

原生日志显示PIECEWISE与FULL capture各5/5完成，两个worker均有请求阶段成功replay证据；请求阶段成功graph replay记录为C1=3、第一轮C8=255、第二轮C8=254，合计512。观察器每worker/phase/event/shape最多记录128项，因此该计数是成功调用的下界，不宣称完整调用总量。真实graph caller为Plugin的`vllm_fl/compilation/graph.py`。服务日志没有MetaX补丁循环导入warning；可选FA2探测不可用的信息另行记录，实际attention选择Maca。

最终源码审计：Plugin运行包317文件中只有本轮3个文件改变；另新增1个集成测试。vLLM运行包2176、FlagGems-vllm276、FlagGems2985文件全部保持原指纹，vLLM Git工作区干净，模型config未变。四包的真实模块来源均为既有editable源码目录。临时服务验证后已正常关闭，端口关闭、无GPU进程残留，容器继续运行；关闭及最终源码/安装核验分别见`service-001/shutdown.json`和`closeout.json`。

## 性能效果

`not_run`，累计收益 `null`。没有 baseline/candidate/revert 性能测量，不引用历史案例数字，不将命中计数当作吞吐提升。

## 决定、风险与回退

候选已保留，本轮指定容器中的导入修复与实际服务命中验证完成。`pr_readiness=reviewable_target_verified`：补丁和目标TP2证据可供评审；其他模型/平台硬件、绕开ModelRunnerFL生命周期的自定义runner、完整模型精度和正式性能均未测，不能据此宣称全平台或正式性能验收通过。源码变更后不复用旧精度gate。

原3文件及源码指纹保存在远端`before/`和`before.json`。保护性回退脚本为`commands/rollback-sampler-fix.py`，SHA核验后只恢复本轮文件并移除本轮新增测试，保留先前优化；本轮未执行回退。增量交付为`sampler-lifecycle-only.patch`。临时观察器只用于本轮诊断，不进入正式Plugin源。

## 外部证据

根目录：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-sampler-fix`。

| 文件 | 内容 | SHA256 |
|---|---|---|
| `before.json` | 修复前指纹 | `88cbf9c128cae39a47776a7806456d3a2e4bdadda28b071a0369f611eaf36e5c` |
| `implementation-v2.json` | 第二版 3 文件 SHA、AST 保持、worker/GDN hook | `56e7f0e61282e79b2447652f5b12da2eba8925fa4c5034faccbb85adb684daad` |
| `import-tests.xml` | 首版 4 失败、2 通过 | `9dc4f2f82d35bf06e7c4aa66858a74445f13e724d481aa6cc030b39e7234cc5f` |
| `import-chain-diagnosis.log` | GDN 导入环 traceback | `2c64bd92f17b220af25d997a31b8163731e09e00806253592564e51fb9e7b904` |
| `numerical-regression.json` | 25 项原生数值/边界结果 | `34deb691d54b7136a6f09a25d57e517c41ed7501342f0fe9e0b92a9fc66d6dcc` |
| `numerical-regression-execution.json` | 精确执行命令、exit 0、日志/结果 SHA | `33ce07845ad7dfb57c5fd70eae6fd902610693896c04487a7a07d66d1ee9c9ff` |

执行脚本为远端 `commands/numerical-regression.py`（SHA `a783172be621d18fe8e2a96ec36b1e9469901b81b7c9051962e3b19a72c18f81`）及 `commands/run-numerical-regression.py`。完整日志留在同根 `numerical-regression.log`、`import-tests.log`，未复制本地大体积日志。

最终新增证据：

| 文件 | 内容 | SHA256 |
|---|---|---|
| `import-tests-v2.xml` | 6通过、0失败/错误/跳过 | `5fba5e100215dc958eff19cf2fe89feffeb3dd2dde3c9cbce0a5ef3a4d968ede` |
| `service-001/verification.json` | 实际采样器/shortlist/graph及17请求验证 | `56c74b5a2834ad5b2a8fb043b5be07905c19082afaea71be29171d41c66d0f7e` |
| `final-source-audit.json` | 生产3文件/测试1文件及其他包不变 | `8b1e2022e851d118555b819d1918d40b722cdbdb20c79351b5036a01e983d7da` |
| `commands/rollback-sampler-fix.py` | 已生成、未执行的保护性回退 | `9e32e8b256fabe0da07a5fea3d33929e7b3175640cd1ea3c90baa9469f210610` |
| `service-001/shutdown.json` | 仅本轮临时服务关闭、端口关闭 | `eb533d915d16e673a838aa0f9d042541a5003b5256f139042b599f4129b3eddc` |
| `closeout.json` | 源码与editable来源不变、GPU无进程、容器运行 | `03d89228f2515c33619c07f947f94e19b3f89ccfea88fa4c3ff3588c2e835e17` |
