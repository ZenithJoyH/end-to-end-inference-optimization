# 沐曦59 DeepSeek V4 Flash 容器

> 最新诊断候选 attempt18 全量 GPQA 为 **100/198，strict-match 50.51%，低于80%**；仅去加粗的辅助分数140/198=70.71%。已修复真实 MoE SwiGLU limit=10 在INT8路径丢失的问题，但同契约回归未改善分数，不能认定为低分主因。原101/198=51.01%结果保留；默认thinking=False及格式影响已取证，剩余答错尚未完全归因。未签发gate。详见模型案例 `20261020-env011-gpqa-metax59/optimize/acc-003.md`；下方env-011为历史短请求快照。

## 当前交付（env-011，2026-10-20）

`mx-59 / deepseekV4-flash` 已完成剩余 24 个生产文件的原生扩展点复查：生产改动 **24→23 个文件、7,830→7,775 行新增**；完整补丁 **37→36 个文件、9,661→9,608 行新增、6→4 行删除**。`vllm_fl/worker/model_runner.py` 恢复 Plugin main 原文；删除全局多流 helper 替换，使用 vLLM 原生 `aux_stream=None` 顺序分支，取消模型中未使用的三条 stream 构造。20 个其他生产文件本轮逐字节不变，Attention/Model 的非构造计算方法与五个 MetaX kernel/policy 文件保持。详见 [24 文件复查](env-011-file-audit.md)。

Attention/Indexer 构造缺少原生组件工厂，继续保留一次静态注册的明确 MetaX 构造；原生类不是 CustomOp/PluggableLayer，不为缩减行数引入全局类型替换或重复构造。原生 `backend_cls`、`get_attn_backend/get_kv_cache_shape` 及 forward 方法继续承担可复用部分。RMS4096 是当前数学体与 rank 配置下的 Inductor launch 调优，vLLM 没有对应 tuner 扩展点，本轮保留其数值与配置。

Plugin 实际 editable 来源 `/opt/vllm-plugin-fl` 与 VS Code 副本 `/public-flash/jinghao/deepseekV4/vllm-plugin-fl` 完整补丁一致，SHA `d85f8340751bdaf89b0da9c842a6efea9e4d202058536ad794c2c4c42a71ae54`。两边各 36 个真实内容差异，暂存 diff 为空、无 MM/AM 或 HEAD 字节相同仍标 M 的文件。vLLM `0.24.0+empty` 的 2,469 个安装文件未变，无 native .so/`vllm_metax`；Torch、源码 FlagTree、FG/FGV、权重 metadata、镜像和三个挂载均不变。

新实例 `attempt15` 保持在 `http://127.0.0.1:18001`：30 项 CPU、42 项 GPU 缓存布局与 3 项原生顺序 helper 检查通过，TP8 的 10 个 C1/C8 固定请求和七档 FULL decode capture/replay 通过，原生 C1 FULL×14 / C8 FULL×2。8 worker hash 表、24 个 hash-layer/rank 原生 GateLinear 和 12 个 bootstrap 绑定审计通过。完整回执 SHA `e3f1076c6abd00a25c3e8b289b8717e573b35a00f39cb7d186a6b9729754e06e`；正式精度、性能、长上下文、MTP、BF16/其他平台未验收，`pr_readiness=experimental`。未 commit/push 或创建 PR。

## env-010 阶段交付（历史，2026-10-20）

`mx-59 / deepseekV4-flash` 已完成剩余 25 个生产文件复查并安装收敛结果：相对 Plugin main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，生产改动 **25→24 个文件、8,519→7,830 行新增**；完整补丁 **38→37 个文件、10,297→9,661 行新增、6 行删除**。直接继承 vLLM 0.24 Attention 的 `forward/attention_impl` 与 Indexer 的 `forward`，复用原生 RMS、FP8 query RoPE/quant、cache gather 和 modular MoE workspace/activation/reduction，删除重复 functional MoE 文件。保留 MetaX sparse attention/indexer、INT8 GEMM、graph ABI 与明确的优化路径，18 个其他生产文件本轮字节不变。逐文件依据见 [env-010-file-audit.md](env-010-file-audit.md)。

当前实际导入仍为 editable `/opt/vllm-plugin-fl`；VS Code 目录 `/public-flash/jinghao/deepseekV4/vllm-plugin-fl` 与其完整补丁相同，SHA `005c7e074aa31014ef287192eb60a5ce78aabce8360b276bf5ef3dffe344d116`。两边各 37 个真实内容差异，暂存 diff 为空，无 MM/AM 或与 HEAD 内容相同仍标修改的文件。vLLM `0.24.0+empty` 的 2,469 个安装文件校验通过，无 native .so、无 `vllm_metax`；FlagTree、Torch、FG/FGV、权重 metadata 与容器挂载未改变。

新实例 `attempt14` 在 `http://127.0.0.1:18001` 保持运行：30 项 CPU 检查、42 项设备逐位比较、TP8 的 C1/C8 共 10 个固定请求和七档 FULL decode capture 全部通过；原生 runtime 记录 C1 FULL×14 / C8 FULL×2。8 worker hash 表及 24 个 hash-layer/rank 原生 GateLinear 组合审计通过。完整证据与回退见文末 env-010；综合回执 SHA `a55cac8b7f9379151e566def522e7f28c20ad8e9f9d2b3e94cb59f54115635f0`。正式精度、稳态性能、长上下文、MTP、BF16/其他平台未运行，`pr_readiness=experimental`。未 commit/push 或创建 PR。

## env-008 阶段交付（历史，2026-10-20）

`mx-59 / deepseekV4-flash / /opt/vllm-plugin-fl` 已完成进一步收敛并恢复 TP8 graph 服务。相对 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，补丁由 **56→43 个文件、18,156→11,619 行新增**；43 文件包括生产代码 30、交付样例/配置 11、测试 2。参照 PR #427 的原生继承方式，Model/CausalLM 复用权重加载、专家映射和通用方法，MoE 直接采用原生类；MLA forward_mqa/cache spec、compressed/SWA metadata、IndexerCache、compressor 状态与数值 kernel 来自 vLLM 0.24。MetaX 保留窄构造、INT8/graph 接口与必要算子实现。

当前实例为 `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt12/`，容器内 endpoint `http://127.0.0.1:18001`，served model `deepseek-v4-flash-w8a8-int8`。7/7 FULL decode capture、C1/C8 共 10/10 固定请求、原生 C1 FULL×14 / C8 FULL×2、8 worker hash 表审计均通过，readiness 后无 ERROR。29 项 CPU 检查通过；保留的 46 个 JIT 函数体未变，三个 compressor 场景的状态/缓存逐位相同。独立组件 graph 探针为 incomplete，完整模型的 capture/replay 另有原生证据，不混写为组件通过。

Plugin 仍从 `/opt/vllm-plugin-fl` editable 安装；vLLM `0.24.0+empty` 的 2,469 个 package 文件哈希与安装 RECORD 一致、无原生 `.so`，`vllm_metax` 仍未安装。FlagTree、Torch、FG/FGV revision/补丁未变。DeepSeek 与 Qwen 容器均运行，原挂载和共享权重 metadata 未变。旧 BF16/MTP 副本、无实现 provider 和未接入的 INT8-indexer 原型已完整备份并退出当前 Plugin 覆盖；native MTP 注册保留。当前 profile 支持 W8A8 INT8 / FP8 KV / TP8 / PP1 / 无 MTP；正式 GPQA、性能、长上下文、BF16/MTP 和其他平台未验收，`pr_readiness=experimental`。

完整 Plugin 补丁 SHA `358d520bebee70be47ace0ccf1700ac8c67dfa896163557330bdfd9c045cf25a`。回执 `/opt/dsv4-upgrades/20261020-plugin-native024-01/native024-receipt.json`，SHA `c185f46959e3d9ebfebf25a12e1f0ba64bed72871371bccd1c1907862c26ee3e`；本机审阅补丁 `/tmp/dsv4-env008-native024.patch`。同根目录保存完整源码/index 备份、命令、失败探针和回退脚本。服务由 `commands/start-model.py` 启动，容器 PID1 仍为 sleep，重启容器后需核验实例并用新 attempt/cache 启动。未 commit/push 或创建 PR。

## env-007 阶段交付（历史）

`mx-59 / deepseekV4-flash / /opt/vllm-plugin-fl` 已完成适配收敛并恢复 TP8 graph 服务。相对当前 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，改动由 **87→56 个文件**，新增代码由 **21,323→18,156 行**；含新增的单次注册回归测试。参考 PR #427 的职责分层，移除旧 `compat/dsv4` 复制，复用 vLLM 0.24 indexer 与通用 metadata，集中启动入口和 provider 包装；MetaX packed KV cache 的必要差异仍在 Plugin 内维护，没有替换成 NVIDIA 执行路径。

当前实例为 `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt11/`，容器内 endpoint `http://127.0.0.1:18001`，served model `deepseek-v4-flash-w8a8-int8`。7/7 FULL decode capture、C1/C8 共 10/10 请求、原生 C1 FULL×14 / C8 FULL×2 replay、8 worker hash 表审计全部通过，readiness 后无 ERROR。29 项 CPU 契约通过，55 个保留/迁移的数值 JIT 函数体 AST 未变。

Plugin 仍从 `/opt/vllm-plugin-fl` editable 安装；vLLM `0.24.0+empty`、已卸载的 `vllm_metax`、源码 FlagTree `0.7.0+metax.git317a0249`、Torch 与两个算子库均维持 env-006 身份。两个原容器均运行，目录挂载和共享权重 metadata 未变。服务由 env-007 `commands/start-model.py` 启动，容器 PID1 仍为 sleep；容器重启后需核验实例并使用新的 attempt/cache 启动。

最终完整 Plugin 补丁 SHA `379414ef5541d925842c496d25a967209f689f40c63e90e0e348c22ada66105e`；相对整理前的 `consolidation.patch` SHA `6ef913deeaeaa789b086ae6edb3271bd1469ed16f735b71bea5bd8f24464531a`。原始证据与回退位于 `/opt/dsv4-upgrades/20261020-plugin-consolidation-01/`，本机可审阅补丁 `/tmp/dsv4-env007-consolidation.patch`。本次未运行正式 GPQA、性能、长上下文、MTP、BF16 attention 或其他平台；`pr_readiness=experimental`，没有提交或推送。

## env-007：参照 PR #427 收敛 Plugin 适配（已完成）

用户要求收敛当前 Plugin 适配文件，参考 [PR #427](https://github.com/flagos-ai/vllm-plugin-FL/pull/427)。本次只重构当前 `/opt/vllm-plugin-fl` 中的有效 DS 适配，不升级依赖、不改共享权重或 vLLM 源码，不开展性能优化。已重新通过单机 connectivity-check；当前 attempt09 health=200。真实基线为 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，相对 HEAD 为 87 个文件、21,323 行新增；此前对话中的 93 为粗略统计，以本次 Git 结果为准。

参考 PR 读取时为 open/unmerged，head `da62cddeb538f3d9d203e4e07cbc164e94f76869`、base `d2d7234aa576a5b6224e99d18500f9b177ebb1e4`，30 个文件，面向 NVIDIA/vLLM 0.24。采用其 ModelRegistry 模型扩展、CachedOp 前端、backend 实现的职责划分；不引入其 NVIDIA 实现、CI 修改或性能结论。

执行前设计：删除可由 vLLM 0.24 原生类承担的旧兼容复制；简化重复构造/覆盖的 attention 层；按 attention、indexer、MoE、backend 和启动生命周期聚合小模块，保留数学与 dispatch/fallback 契约，不用一个巨型文件或动态 sys.modules 别名掩盖文件数量。无法由新版原生层替代的 MetaX cache ABI 明确留在 Plugin 边界。先在离线真实源码副本整理，检查引用、语法、契约与数值实现，再结束本任务服务、应用精确文件清单、源码重装并以新 attempt/cache 验证 TP8、C1/C8、capture/两次 replay；同名未改动模块仍需绑定新的来源与补丁身份。

产物计划置于本容器私有 `/opt/dsv4-upgrades/20261020-plugin-consolidation-01/`：完整源码/安装 metadata/index 备份、原/新文件清单、PR 身份、重构脚本和可审阅补丁、CPU/设备检查与模型原始证据。应用前比较全部受影响源文件 SHA，发现并发更改即停止覆盖；回退恢复同一备份并新建服务实例。仅停止当前 DeepSeek 服务进程组，保持两个原容器与挂载运行，不触碰 Qwen 服务或其他机器；不提交或推送。

离线候选结果：87→56 个文件，21,323→18,106 行新增（含补充架构说明）；40 个旧文件移除，9 个职责明确的新模块，其他相关文件更新引用。启动生命周期合为单个 `patches/deepseek_v4_metax.py`，小型 FlagGems provider 合为两个 impl 模块，prefill/replay/headpack 及 indexer helper 按领域归并。整个 `compat/dsv4` 快照被移除；indexer 直接复用原生 0.24，FlashMLA builder 继承原生通用方法，仅保留压缩 KV 的差异，compressor 通用 metadata 三类与原生 AST 完全一致后直接复用。MetaX SWA provider 静态绑定到已验证的 FlagGems 函数，取消额外 monkey-patch；模型直接构造 FL MLA 一次，避免先建旧层、再删除覆盖。

本地 20+8 项 CPU 契约与目标文件 F821/F811 检查通过；55 个保留/迁移的数值 JIT 函数 AST 全部不变。第一次离线真实初始化发现合并 provider 的相对导入层级错误，冻结在 `candidate/tree` 和 `logs/stage-probe.log`，生产服务未切换；修正后的独立 `candidate/tree-v2` 初始化通过：45 ops / 62 implementations，41 个显式绑定，旧 compat 模块未导入，MLA/model/provider 真实 origin 均来自候选目录。应用脚本再次按该通过候选逐项比较 Python 内容后才切换。完整编译器、算子库与运行时版本保持 env-006 身份；正式结果等待新 TP8 实例。

首次应用已安装 56 文件候选，补丁 `2ff402af59b4202c701c000302cf00cfd36e2efa8eabf264371b8d8f610270d1`，随后 attempt10 在构造第一层 MLA 时失败：`DeepseekV4MLAAttention.__init__` 遗留的 `static_forward_context.pop(prefix)` 仍假定此前已构造一个待替换层。单次构造后该前提不成立，产生 KeyError；并非模型输出/数值分数下降。按本地诊断技能冻结 attempt10 日志、launch/cache 和候选身份，问题 ID `env007-mla-once-registration`，分类 execution-mode regression。修复只去掉这处过时 pop，保留显式重复注册 ValueError；新增 CPU 契约覆盖首次注册成功、其他层不变、重复注册拒绝。失败进程组已自行退出，无存活关联进程，不向旧 PID 发送信号；使用新 attempt11/cache 重验相同完整最小范围。初版文件计划、补丁和回执另存，不用后续成功覆盖失败证据。

### env-007 最终结果与证据

注册最小复现证明原候选稳定报 KeyError，单变量修复后首次注册成功、重复注册报 ValueError；目标容器 20+9 CPU 测试通过。attempt11 完成 62 分片加载和全部 graph capture，固定 C1/C8 原请求、temperature=0、seed=0、max_tokens=96、非 thinking 与 prefix cache 关闭的相同契约下 10/10 通过，全部 HTTP200、非空且 finish_reason=stop。单请求返回 `42` 和“水在标准大气压下的沸点是100摄氏度。”，并发结果为 34/36/38/40/42/44/46/48，与 env-006 相同。该启动问题已在本次最小范围中修复；未发生正式分数失败，也未签发正式精度 gate。

| 证据 | 容器内绝对路径 / SHA |
|---|---|
| 最终收敛回执 | `/opt/dsv4-upgrades/20261020-plugin-consolidation-01/consolidation-receipt.json`；`7f610daa88e6fbdfe14609a1b64b097c8a125d52fc3cb28f0477ad10ce256a5c` |
| 服务、graph、metadata、8 worker hash 审计 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt11/verification-01/result.json`；`c854a89c471d96e1cf38c6383854b8d318be027233e05bd2eb3c79f994d00ca7`；原生 C1 FULL×14、C8 FULL×2 |
| 原始请求/响应 | 同 attempt 的 `minimal-regression/`；graph 原始摘录为 `verification-01/graph-runtime-evidence.log` |
| 实际启动 provider | 同 attempt 的 `cache/startup_audit/`；12 个启动进程的显式绑定，8 个模型 worker 的三层 hash 表审计；没有 vendor framework 导入或全局 FGV ATen 注册 |
| 数值源码与 footprint | env-007 `analysis/numerical-source-audit.json`（55 个 JIT AST 保持，3 个原生 metadata 类等价）和 `analysis/footprint.json`（56 files / 18,156 insertions / 13 deletions） |
| 注册问题定位 | env-007 `analysis/registration-minimal-reproducer.json`、`commands/fix-registration.py`；失败 attempt10 与 `*-attempt10.json`、`*.attempt10` 全部保留 |
| 完整候选与相对整理前补丁 | env-007 `Plugin-consolidated.patch`、`consolidation.patch`；后者也保存在本机 `/tmp/dsv4-env007-consolidation.patch`，已对整理前副本执行 `git apply --check` |
| 回退 | env-007 `commands/rollback.py` 默认 dry-run；先按实时身份结束本任务服务，再显式执行，恢复已备份的原源码/index 并重装同一 editable 目录，随后以新缓存验证 |

两个原容器和挂载再次核验为运行/一致，证据 `analysis/final-containers.json`；未停止容器、修改共享权重或 Host 驱动。最终 29 项 CPU、目标文件 F821/F811、`git diff --check HEAD` 与最小 TP8 graph 范围通过；完整正式精度、性能及非目标路径不据此宣称通过。服务保留运行，没有 Git commit/push 或创建 PR。

## env-006 阶段交付（历史，env-007 已进入新实例验证）

`mx-59 / deepseekV4-flash` 已卸载 `vllm_metax`，安装真实源码构建的 **`vllm 0.24.0+empty`**，并从真实 **`/opt/vllm-plugin-fl`** editable 源码安装 Plugin。Plugin 仍为官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` + 已有 DeepSeek V4 适配；迁移只更新 launcher 和依赖锁的 vLLM 精确版本，其余有效源码逐文件保留。

| 组件 | 当前身份 |
|---|---|
| vLLM | `0.24.0+empty`；官方源码 `ee0da84ab9e04ac7610e28580af62c365e898389`；源码 `/opt/dsv4-sources/vllm-0.24.0-empty`；实际安装 `/opt/conda/lib/python3.12/site-packages/vllm`，无原生 `.so` |
| Plugin | `0.3.0rc2.post1+ga696859b9.d20261020`；editable `/opt/vllm-plugin-fl`；实际 import `/opt/vllm-plugin-fl/vllm_fl/__init__.py` |
| vllm_metax | distribution、模块和 entry point 均已移除 |
| FlagTree | 官方 main 源码构建 `0.7.0+metax.git317a0249`；实际 triton import `3.6.0`，MetaX backend |
| Torch / 算子库 | Torch `2.10.0+metax3.8.2.2`；FlagGems `5.5.0.dev0+g8200f71f5.d20261020`；FGV `0.3.0.dev1` |

新实例 `attempt09` 已完成 TP8 权重加载、7/7 FULL decode capture、C1/C8 共 10/10 固定请求；原生统计 C1 FULL×14、C8 FULL×2。八个 worker 的 hash 表与当前 bootstrap 路径核验通过，readiness 后无 ERROR；权重 metadata SHA 未变。容器内 endpoint 为 `http://127.0.0.1:18001`，served model 为 `deepseek-v4-flash-w8a8-int8`。服务及两个原容器均保持运行；挂载仍为 `/public-flash`、`/data` 和原 `/var/lib/dsv4` volume。

当前启动命令由 `/opt/dsv4-upgrades/20261020-empty-vllm-plugin-dir-01/commands/start-model-empty.py` 保存；容器 PID1 仍为 sleep，容器重启后需先核验服务身份再使用新的 attempt/cache 启动。安装/验证回执 `installation-receipt.json` SHA `021d97b5be977c416aaed971d6923c3064a8cf23124309870726cc36f38ff221`；模型回执 `attempt09/verification-01/result.json` SHA `f4532e51ec6885b765b9c08b01b41521af52759e0957501c51b40542b7a13111`。完整路径和回退入口见 env-006 记录。

范围仅为环境切换与 graph 最小回归，正式 GPQA、长上下文、性能、BF16 attention 及其他平台未测；`pr_readiness=experimental`。pip check 仍有 7 项既有依赖提示，详见下文；未签发正式精度 gate 或性能验收。

## env-006：按用户要求切换 empty vLLM 与 Plugin 源码目录（已完成）

用户最新明确要求卸载 `vllm_metax`、安装 vLLM 0.24.0 empty，并从名为 `vllm-plugin-fl` 的目录源码安装 Plugin；本要求取代 env-002 的完整 vendor vLLM 选择。当前连接已重新验证。计划在容器私有 `/opt/dsv4-upgrades/20261020-empty-vllm-plugin-dir-01/` 保存命令、包文件备份、源码、版本和验证证据；先核验已有 FlagOS 镜像中 `0.24.0+empty` 的来源、文件和依赖，再准备可复用安装产物。保留当前成功环境和全部适配补丁，将有效 `/opt/dsv4-fl-source` 真实源码迁移到 `/opt/vllm-plugin-fl`，不使用历史 `/opt/vllm-plugin-FL` 冒充当前版本。

切换前仅结束 env-004 attempt08 的本任务服务进程组，保持容器运行。卸载/安装均限制当前容器的私有 Python 前缀，不自动解析依赖替换 Torch/FlagTree 或其他运行库。同步修正当前 launcher 的真实版本锁与路径，使用全新缓存重启，按本地精度技能 `minimal-regression` 复核 C1/C8、capture 和至少两次 replay。旧 attempt08 的通过仅作为历史证据，不自动绑定到新环境；本次不运行正式精度或性能验收。不改共享权重、挂载、Host 驱动和 Qwen 容器。

来源候选为已存在的 FlagOS Qwen3-VL 发布镜像 `sha256:07cf737e3e20…`，此前只读记录显示 `/opt/conda` 内为 `vllm 0.24.0+empty`；完整身份与安装产物仍待本次核验。回退使用本次备份恢复旧包和有效源码路径，并新建服务 attempt，不覆盖旧日志。

只读核验该镜像完整 ID 为 `sha256:07cf737e3e20e76b26fa2bc1264de98bc07f1977408416b61ab134d7acf51c3e`，其中 empty 是 `/workspace/vllm` 的 editable 安装，不是可直接复制的普通 site-packages 目录。源码官方 origin 为 `vllm-project/vllm`，HEAD `ee0da84ab9e04ac7610e28580af62c365e898389`，tracked 工作区干净，无 `.so`；当前计划把该真实源码完整复制至容器私有 `/opt/dsv4-sources/vllm-0.24.0-empty`，以 `VLLM_TARGET_DEVICE=empty` 构建 wheel 并安装，保留来源与构建日志。首次探针误假定 package 位于 site-packages，缺少 `_version.py` 后失败，原始 stderr 已保留；改为核验 editable 指向的真实源码，没有通过编辑 metadata 伪造 empty。

empty wheel 已由该源码构建：`vllm-0.24.0+empty-cp312-cp312-linux_x86_64.whl`，7,582,184 bytes，SHA `e4c7607d1799f16f44cf8738bae477825073d1cb941c5aa13e01772bb369e98d`。构建在 uv 创建的 `.venv` 中使用现有 MetaX Torch 与 `--no-build-isolation --no-deps`；uv/setuptools-rust/semantic-version 仅位于本任务私有 build-tools。wheel 无 `.so`，其 Python/数据文件与之前 vendor vLLM 对应文件全部相同，临时目录实际导入和关键 API 检查通过，两个旧 distribution 的 RECORD 无重叠。

备份校验后已仅结束 attempt08 的服务进程组，容器保持运行；卸载 `vllm_metax` 与原 vLLM，安装 empty wheel 成功。Docker overlay 对原下层目录直接 rename 返回 EXDEV，未改动原目录；续接命令改为完整真实 copytree 至 `/opt/vllm-plugin-fl`，保留原目录 inactive，用 `pip install --no-deps --no-build-isolation --force-reinstall -e /opt/vllm-plugin-fl` 重装。launcher 与依赖锁仅将 vLLM 精确版本更新为 `0.24.0+empty`，不改模型算法；适用范围限 DS 示例环境核验。回退入口改为 `commands/rollback-v2.py`（默认 dry-run），保留首轮失败脚本与日志，不运行失效的初版回退。

安装审计通过：2,469 个 vLLM package 文件与 wheel 逐项 SHA 一致，实际 package 目录无 `.so`；`vllm_metax` distribution、module spec 和全部相关 entry point 均不存在。Plugin 的 editable direct_url 与 import origin 都指向真实 `/opt/vllm-plugin-fl`；迁移前后 686 个有效源文件完全相同，仅 DS launcher 和依赖锁两文件更新精确版本。20+8 项原生 CPU unittest 及三个仓库 `git diff --check HEAD` 通过。pip check 从原 20 项降至 7 项：5 项要求名为 triton 的 distribution（由 FlagTree 提供实际模块）、既有 xgrammar 版本和 xformers/setuptools 约束差异，未静默升级这些 vendor 依赖，也不宣称 pip check 全通过。当前使用新 attempt09/cache 进行整模型验证。

### env-006 最终验证与回退

使用本地 `e2e/accuracy` 的 `minimal-regression` 模式，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，前台跟进，无定时任务。新 `attempt09` 使用与上一实例相同的 TP8、FP8 KV、FULL_DECODE_ONLY、prefix cache 关闭及 INT8 expert override，所有缓存独立。62 分片加载、全部 7 个 capture、10/10 请求和实际 FULL graph replay 通过；8 个 worker 的三层 hash 表、当前 `/opt/vllm-plugin-fl` bootstrap 环境、权重 metadata 和当前源码补丁身份均重新绑定，不复用旧实例回执。两个顺序请求返回 `42` 与中文“水在标准大气压下的沸点是100摄氏度。”，并发八请求返回 34/36/38/40/42/44/46/48，均 HTTP200、finish_reason=stop。

| 证据 | 容器内绝对路径 / SHA |
|---|---|
| 安装与最终绑定回执 | `/opt/dsv4-upgrades/20261020-empty-vllm-plugin-dir-01/installation-receipt.json`；`021d97b5be977c416aaed971d6923c3064a8cf23124309870726cc36f38ff221` |
| 模型、graph、权重与 worker 审计 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt09/verification-01/result.json`；`f4532e51ec6885b765b9c08b01b41521af52759e0957501c51b40542b7a13111` |
| 10 请求原始契约/响应与 graph 日志 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt09/minimal-regression/`、同 attempt 的 `verification-01/graph-runtime-evidence.log` |
| 包/源码安装审计、CPU 检查、容器状态 | env-006 根目录 `analysis/installation-audit.json`、`analysis/cpu-and-source-check.json`、`analysis/final-containers.json` |
| 最终 Plugin 补丁 | env-006 根目录 `Plugin-installed.patch`；`fdc25a93edc4f87896a79339c584189e12c650b1454f25b6204355c4ec2396e6` |
| 算子库补丁 | FGV `961849cb4f411f0bef0ad22c36f02361be8fe5babec603e30c73c5aad621e7ac`；FlagGems `6cb6c8e2daab5829a6a18a7b6ef3c8137ad50f566f9a924df047a36c8514b258`，均与切换前一致 |
| 回退 | `/opt/dsv4-upgrades/20261020-empty-vllm-plugin-dir-01/commands/rollback-v2.py`，默认 dry-run；必须先按实时身份结束本任务服务，再显式 `--execute` 恢复旧包与旧 editable 路径，并以新缓存复验 |

env-006 backup 完整保留旧包 RECORD 对应文件/metadata 和 Plugin 工作树；原 `/opt/dsv4-fl-source` 为 inactive 保留副本，不在当前 editable 路径中。所有操作仅作用本容器私有前缀/源码，未停止任何容器、改动 Host 驱动/挂载/共享权重、Git commit 或 push。此前 env-005 完整 vendor vLLM 的成功记录仅为历史，当前以本节 empty 运行结果为准。

## env-005 阶段交付（历史，已由 env-006 替换）

`mx-59 / deepseekV4-flash` 已完成源码与运行时升级，当前 TP8 graph 服务运行中；C1/C8 共 10 个固定请求全部通过。容器内 endpoint 为 `http://127.0.0.1:18001`，served model 为 `deepseek-v4-flash-w8a8-int8`。本次是环境与最小运行验证，未运行正式 GPQA、长上下文验收或性能测试。

| 组件 | 当前实际身份 |
|---|---|
| FlagTree | **官方 main 源码本机构建安装**，`0.7.0+metax.git317a0249`；commit `317a0249ec25c6756e0aee3a87e8e3c92f154335`；源 `/opt/dsv4-sources/FlagTree`；实际 triton import version `3.6.0`，target `maca/arch80/warp64` |
| Plugin | 官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` + 原 DS 适配与 vLLM 0.24 私有兼容补丁；源 `/opt/dsv4-fl-source` |
| FlagGems | master `8200f71f51d784d54a5a51019cb955acb74d64c1` + 保留适配；`5.5.0.dev0+g8200f71f5.d20261020` |
| FlagGems-vllm | main `fa78ddee4c3e78ce5047213ff0ef02acff34b2d5` + 保留适配与新编译器的局部兼容；`0.3.0.dev1` |
| vLLM / Torch | 完整 vendor vLLM `0.24.0`，已替换原 empty 版本；Torch `2.10.0+metax3.8.2.2` |

挂载为 `/public-flash:/public-flash:rw,rprivate`、`/data:/data:rw,rslave`，原 `/var/lib/dsv4` volume 保留。模型使用用户指定的 `/public-flash/models/DeepSeek-V4-Flash-0731-Quant-W-INT8-PerChannel-A-INT8-PerToken`，实际 expert 权重为 INT8，通过启动 override 纠正原 metadata 的 fp4 标记，共享模型文件未改。

当前验证实例为容器私有 `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt08/`：7 个 batch size capture 完成，原生统计 C1 有 14 次、C8 有 2 次 FULL decode graph 执行；8 个 worker 的三层 hash 表审计通过。Qwen 服务进程按用户指令终止，`qwen3vl-p64k-opt-20261015` 容器保持运行。两个容器最终均为 running。

容器 PID1 仍为 `sleep infinity`，当前推理服务由已保存脚本启动；容器重启后需用 `commands/start-model-flagtree.py` 和新的 attempt ID 重启服务，不能覆盖已有缓存/证据。FlagTree 精确回退脚本为 `/opt/dsv4-upgrades/20261020-flagtree-source-01/commands/rollback.py`，默认 dry-run，未执行回退。

最终模型回执 SHA：`5dc868e098a3ffb77cb4c13de820adba543fbffb0fd75924f9ddc1d6319b27f5`。源码安装最终回执 SHA：`43449a91d139a370f518148593616a0877596a1d19d75d8d6f3f112f1e1e7222`。详细过程及结论边界保留于下文；旧阶段的“未运行/未升级”只描述当时状态。

## 初始创建记录（历史）

- 日期：2026-10-20（Asia/Shanghai）。
- 用户请求：在沐曦59使用 `harbor.baai.ac.cn/flagos-inner-models-release/dsv4-flash-w8a8-metax:20261020` 启动名为 `deepseekV4-flash` 的容器。
- 范围：创建运行中的工作容器；未请求启动推理服务或性能优化，不进入模型评测流程。
- Host：inventory 的 `metax/mx-59`；仓库 connectivity-check 已通过。
- 镜像：本机已存在指定标签，ID 与 RepoDigest 均为 `sha256:8c27bc8fba95205262c0ae9be855b9c9b8da07509962a7f6d6008d08d3a14412`；执行时固定 ID，避免标签漂移。
- 镜像默认入口会以 TP8 启动模型服务，模型路径 `/models/DeepSeek-V4-Flash-W8A8-INT8`、端口 `18001`。当前 GPU 0/1 已被占用，因此本次覆盖入口为 `sleep infinity`，仅准备工作环境。
- 配置：映射 `/dev/dri` 与 `/dev/mxcd`，私有 IPC、64 GiB shm、默认 bridge 网络，无发布端口，不增加宿主机目录挂载。镜像声明的 `/var/lib/dsv4` 由 Docker 创建匿名 volume。
- 状态：completed；已创建并启动，执行命令退出码为 0。
- 验证：`docker inspect` 确认运行中、镜像 ID 完全一致、入口为 `/bin/sleep infinity`、IPC 为 private、网络为 bridge、shm 为 68,719,476,736 bytes；无宿主机目录 bind mount，只有镜像声明的 `/var/lib/dsv4` 匿名 volume。容器内 `mx-smi -L` 成功列出 8 张 MetaX C550，`df -h /dev/shm` 确认为 64 GiB，Python 位于 `/opt/conda/bin/python`。未加载模型或启动推理服务。

## 执行命令（Host mx-59）

```sh
set -eu
if docker container inspect deepseekV4-flash >/dev/null 2>&1; then
  echo 'Container name already exists; aborting without changes.' >&2
  exit 1
fi
test -d /dev/dri
test -c /dev/mxcd
docker image inspect sha256:8c27bc8fba95205262c0ae9be855b9c9b8da07509962a7f6d6008d08d3a14412 >/dev/null
docker run -d \
  --name deepseekV4-flash \
  --device /dev/dri:/dev/dri \
  --device /dev/mxcd:/dev/mxcd \
  --shm-size 64g \
  --label org.baai.task=20261020-deepseekv4-flash-metax59-container \
  --entrypoint /bin/sleep \
  sha256:8c27bc8fba95205262c0ae9be855b9c9b8da07509962a7f6d6008d08d3a14412 \
  infinity
```

进入容器：`ssh mx-59` 后执行 `docker exec -it deepseekV4-flash bash`。

如需回退，仅在用户要求时停止并移除本次新建容器及其独占匿名 volume；不涉及其他容器或镜像。

## env-001：更新兼容版本并迁移原有改动（已完成）

用户于 2026-10-20 授权使用其提供的网络代理，在本容器更新 Plugin、FlagGems-vllm、FlagGems，并将既有改动迁移到最新版本。代理凭据不写入本记录，只用于更新进程环境。

已核验源码均位于本容器私有 writable layer；无其他容器共享源码或 site-packages。本次是环境升级，不启动模型服务、不修改 vLLM/Torch/Triton/vendor 二进制，不进行性能或正式精度验收。

原始版本：

| 组件 | 实际来源 | 原 revision / 改动 |
|---|---|---|
| Plugin | `/opt/dsv4-fl-source`，另有已安装包 | `334078282fd5be409e4a3b917e13cabfdf8e2abc`，35 个 staged 文件改动；另一个 `/opt/vllm-plugin-FL` 为历史源码，不据此判断在线版本 |
| FlagGems | `/opt/dsv4-sources/FlagGems`，已安装 wheel | `0ebb95bd47c902de9909e653f318fc57a5e315cf`，工作树干净，含历史兼容提交 |
| FlagGems-vllm | `/opt/dsv4-sources/FlagGems-vllm`，已安装 wheel | `9ae5b26e286a91c1dc1de50662373eef0715308a`，工作树干净，含历史兼容提交 |
| vLLM / Torch / Triton | 原 vendor wheel | `0.20.2+empty` / `2.8.0+metax3.7.0.7` / `3.0.0+metax3.7.0.7`，保持现有版本 |

执行计划（执行前记录）：在容器私有 `/opt/dsv4-upgrades/20261020-latest-stack-01/` 保存原工作树、staged/unstaged diff、安装包及配置备份；从官方 `flagos-ai/vllm-plugin-FL`、`flagos-ai/FlagGems`、`flagos-ai/FlagGems-vllm` 获取默认分支最新 SHA，保存网络操作的脱敏回执；以新源码副本进行三方合并，冲突逐项按当前接口迁移，保留所有旧适配；不提交或推送 Git。安装使用本地源码和 `--no-deps --no-build-isolation`，防止替换 vendor 依赖。更新精确依赖锁与 launcher 中的版本校验，再核验真实导入路径、注册、相关 CPU 回归和可安全执行的设备最小验证。所有命令、原始输出及补丁保存在该容器目录；本记录只保存摘要及校验信息。

回退：保留原源码与已安装包的完整备份及 package metadata，恢复本次替换的三包和 launcher 配置即可；不恢复或改动其他容器。

### 最终版本与分支选择

Plugin 官方 `main=a696859b9aa528dfd5b21f5da3403fdc16bac4cd` 的测试依赖已面向 vLLM 0.24.0，且不含当前镜像基于 release/0.2 的 DeepSeek V4 代码。直接合并还会带入两发布分支间的大量无关差异。因此已向用户说明并询问分支偏好；未收到进一步指定后，采用已说明的兼容分支默认方案，保持 vendor vLLM 0.20.2。**本次没有迁移 Plugin 到 main，也没有升级 vLLM。** 原适配已合入 release/0.2 最新提交，本次以该官方提交重建工作树，完整保留原有效改动并适配新库接口。

| 组件 | 官方最新基线 | 当前安装版本 | 实际源码 / 导入根目录 |
|---|---|---|---|
| Plugin | `release/0.2`，`7cb559947cb61fd8b69fa5027d8ec113e528a644` | `0.2.2rc2.post1+g7cb559947.d20261020` | `/opt/dsv4-fl-source/vllm_fl` |
| FlagGems | `master`，`8200f71f51d784d54a5a51019cb955acb74d64c1` | `5.5.0.dev0+g8200f71f5.d20261020` | `/opt/dsv4-sources/FlagGems/src/flag_gems` |
| FlagGems-vllm | `main`，`fa78ddee4c3e78ce5047213ff0ef02acff34b2d5` | `0.3.0.dev1` | `/opt/dsv4-sources/FlagGems-vllm/src/flaggems_vllm` |

三个仓库均以未提交补丁保留适配，已添加指向官方仓库的 `upstream` remote，无 unresolved conflict 或进行中的 merge；没有创建提交或推送。`/opt/vllm-plugin-FL` 是镜像历史副本，未安装或改作当前导入源。

### 保留与调整

- Plugin 原有效 DS 源码在重建时逐文件核验一致。随后仅为新库接口调整显式 SiLU 调用及移除无用导入，并更新 launcher、依赖锁、对应包装回归及部署说明。
- FlagGems 原 `dsv4_masked_fill.py`、`metax_launch_policy.py`；FGV 原 INT8 quant、launch cache、MetaX MHC pre、非 TLE MoE alignment 均与备份逐字节相同。topk 数值保护、独立缓存、GDN 不修改全局编译器的保护继续保留。
- Gather 保留 padded page 的无拷贝视图、page stride、空请求返回、纯元数据 tuning key 和按选中 `num_workers` 生成 grid；合入上游新配置与实现。
- 上游 SiLU 改为新 kernel/tuner 且公开接口只接收标量。保留最新实现，将原 1024 tile 限制迁入 MetaX YAML；另在 MetaX backend 保留原 tensor-limit ABI，复用最新数学 helper。Plugin 改调该接口，未增加 `.item()` 或主机同步，未把旧 kernel 覆盖回通用实现。
- 三包使用 `--no-deps --no-build-isolation -e` 安装。移走了无任何现有发行包拥有的旧 FlagGems namespace 残留，完整保存在 `orphaned-installed/`，并确认真实导入路径。依赖锁同时核验 editable 路径、版本、包内容 SHA 和补丁 SHA，保留旧 VCS 校验逻辑。
- 为满足最新 FlagGems 的明确依赖，将 PyYAML `6.0.3 → 6.0.1`；原包文件已完整备份。vLLM、Torch、Triton 和 vendor 二进制未更新。

### 验证与边界

| 验证 | 结果 / 原始证据（均为容器内路径） |
|---|---|
| 最终 CPU 包装 / 层边界 | 20 + 8 项通过；`logs/final-test_deepseek_v4_packaging.py.log`、`logs/final-test_deepseek_v4_layer_boundaries.py.log` |
| 缓存页布局与 MoE graph | 27 passed，172 deselected；`logs/operators-tests.log`；覆盖四种布局、两种 block size、三种 gather 模式，以及三种 MoE token 数的改变输入重放 |
| SiLU / gather / Plugin 显式 tensor-limit | 18 项通过；`graph-smoke-results.json`、`logs/graph-smoke-03.log`；三条路径各 capture 后两次改变输入 replay；沿用现有数值断言 |
| 生产 bootstrap 与模型模块导入 | 通过；`logs/installed-model-import-02.log`，41 处绑定；无 `vllm_metax` 导入，全局编译器入口保持原状 |
| 三仓库 `git diff --check HEAD` | 全部通过；`logs/*-diff-check.log` |
| 依赖差异 | 无新增未满足依赖；`dependency-audit-final.json`。镜像原有 OpenCV / setuptools 两项冲突保持，不能把整体 pip check 写成通过 |
| 完整模型 / 正式精度 / 性能 | `not_run`；模型权重未挂载，未启动模型服务；算子 graph 不代表完整模型 graph / TP8 通过 |
| PR 准备 | `experimental`；非目标平台硬件和完整模型未测，未运行缺失的 lint 工具 |

修复过程中的导入失败、旧缓存路径失效、namespace 优先级问题、旧 SiLU 符号缺失及测试脚本相对导入错误的原始日志均保留；最终通过记录不覆盖早先失败记录。原始 `sources/plugin/` 是未采用的 main 合并诊断副本，不是当前安装源。

### 归档与回退

容器内产物根目录：`/opt/dsv4-upgrades/20261020-latest-stack-01/`。

- `backup/`：原源码及原安装文件；`original-source/`：切换前原树；`commands/`：执行脚本；`logs/`：原始验证记录。代理只通过更新进程环境使用，没有持久配置凭据。
- `upgrade-receipt.json`：最终结构化回执，SHA-256 `f96b3f03dd76bd3d42e0494ccc0fdce17503481345ba5e81a865c421548bb000`。
- `plugin-final.patch`：SHA-256 `89f05d1795767e590594c3fe5dc0de922bc681d9d1089accd89e169a7d05356d`。
- `FlagGems-final.patch`：SHA-256 `6cb6c8e2daab5829a6a18a7b6ef3c8137ad50f566f9a924df047a36c8514b258`。
- `FlagGems-vllm-final.patch`：SHA-256 `99442e1cf6b7ab9581331c368bd01d8bd38939eaa4791c1781f18c248a4b83c9`。
- `commands/rollback.py`：默认只打印操作说明；仅在用户要求回退且相关后续服务已停止时使用 `--execute`，恢复原三个源码目录与原四包安装文件，保留升级后源码，不影响其他容器。未执行回退。

镜像内原始 `/opt/dsv4/image_manifest.json` / `versions.lock.json` 仍代表原镜像，不改写为新镜像已验收；当前版本以上述实际导入、源码锁及升级回执为准。容器继续保持工作环境运行。

## env-002：迁移 Plugin main 并替换 empty vLLM（已切换，组件回归通过）

用户回复 env-001 分支问题，明确要求“必须迁移到 main，另行评估运行时升级”。该指令替代 env-001 的兼容分支默认选择。范围为迁移 Plugin 的原有 DS 适配到官方最新 main，并评估运行时升级；尚不据此推定已授权修改 vLLM、Torch/Triton、vendor 二进制或基础镜像。

执行前计划：在容器私有 `/opt/dsv4-upgrades/20261020-plugin-main-01/` 保存 env-001 有效源码、安装状态和精确版本；重新确认 main 最新 SHA。以 main 干净工作树为起点，只迁移 DeepSeek V4 所需前置及原有补丁，不把旧 release 分支的其他平台和基础框架差异整体带回 main。按当前 registry/dispatch、模型、MetaX backend 边界调整接口，保留 env-001 已完成的算子库更新及 tensor-limit 修复。先用导入、CPU 契约和静态 API 差异判断当前 vendor vLLM 0.20.2 是否足够；如需升级运行时，完成具体依赖/改动/回退方案和可评审源码后再请求必要授权，不先改 vLLM 源码或 vendor 安装。

main 候选通过可执行检查后再切换本容器安装；无法在现运行时使用时保留完整候选与证据，准确记录尚缺的运行时条件，不把源码迁移等同运行验收。无模型权重、TP8 或正式精度/性能授权的现状不变。

用户随后明确要求“你还需要替换容器中 vllm 的 empty 版本”，现已授权实际替换本容器 vLLM 运行时。执行计划补充：优先检查 Host 已有官方/vendor 镜像的真实版本、DS V4 前置、原生扩展及 Torch/MACA ABI，选择完整匹配的非 empty 运行时；先保存旧运行时完整回退材料，在容器私有目录验证后切换。不得仅改版本字符串，不修改 Host 驱动或其他容器。若运行时存在与 main 的 API 差异，将按实际代码调整本任务私有 Plugin/必要运行时兼容层并保留补丁。

### main 与运行时候选检查

重新 fetch 确认官方 main 为 `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`。现有 `0.20.2+empty` 缺少 main 所需 `experts.triton_moe` / `mamba.gdn` 接口。已检查的 FlagOS 0.24 模型镜像仍为 `+empty`，另一 `0.24.0+flagos` 发行包也不含原生扩展，均未作为本次替代版本。

选用 Host 已有 MetaX 官方 vendor 镜像 `cr.metax-tech.com/public-ai-release/maca/vllm-metax:0.24.0-maca.ai3.8.2.5-torch2.10-py312-ubuntu22.04-amd64`（镜像 ID 前缀 `d080f0f3aa71`）中的完整运行时，先暂存到容器私有 `runtime-stage/conda`；匹配 SDK 放在 `/opt/maca-3.8.2`。实际版本为 vLLM `0.24.0`、Torch `2.10.0+metax3.8.2.2`、Triton `3.6.0+metax3.8.2.2`、mctlassEx `0.1.1+metax3.8.2.2torch2.10`、mcoplib `0.4.9+g8b5bd8b.maca3.8.0.25.torch2.10`。这是实际更换匹配 Python/vendor 包与 SDK，不是改名或改版本后缀。Host 驱动不变。该镜像 DS V4 已重构到 `vllm/models/deepseek_v4/`，旧单文件路径不存在不能解释为缺少 DS V4 能力。

main 保留新版 MoE 工厂、CachedOp/prewarm 返回契约、通用过滤和其他平台路径；原 DS 专用层 ABI 放入 Plugin 私有 `vllm_fl.compat.dsv4`，不覆盖新版 vLLM 通用源码。DS 路由保留 input_ids/hash table/scaling；共享 KV cache 的 dtype 从各层 spec 取值。DS backend 与 main 新 MLA provider 按算子名称去重。新 launcher 通过 main 已有环境变量入口明确应用原 topk 黑名单，并严格要求 vLLM `0.24.0`，不再接受 `+empty` 后缀。

暂存验证：main Worker/ModelRunner 导入通过；28 项 CPU 契约通过；18 项 SiLU/gather/显式 tensor-limit 数值与 graph 检查通过；27 项缓存布局与 MoE alignment graph 回归通过；实际 mctlassEx INT8 GEMM 三种 shape 均通过数值检查及两次改变输入 replay。生产 bootstrap 与模型/OOT 注册通过，39 处绑定、无 `vllm_metax` 导入、全局编译器入口未变。W8A8 路径不执行的 FP8 einsum / Mega-MoE 缺失明确记录为 optional，不冒充可用。

运行时切换命令保存在 `commands/runtime-switch*.py`。首次对原镜像 lower-layer `/opt/conda` 执行 rename 被 Docker overlay 以 `EXDEV` 拒绝，尚未改变默认运行时；后续改为完整复制旧 prefix、逐文件/符号链接哈希一致后再替换，保留验证回执和失败自动恢复方案。

### 最终默认环境

已完成切换，容器仍为 `running`。实际入口是 `/opt/conda/bin/python`，SDK 链接 `/opt/maca → /opt/maca-3.8.2`；原基础镜像身份与唯一 `/var/lib/dsv4` volume 挂载均未改变。运行时来源完整镜像 ID 为 `sha256:d080f0f3aa7108b7e9d9cc23eec704bdb7828ec6bb731dab6129a77200238d1e`。

| 组件 | 最终实际版本 / 源码身份 |
|---|---|
| vLLM | `0.24.0`，实际替换原 `0.20.2+empty`，未改版本元数据冒充升级 |
| Plugin | `0.3.0rc2.post1+ga696859b9.d20261020`；官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` + 未提交适配补丁，分支 `upgrade/20261020-main`；实际源 `/opt/dsv4-fl-source` |
| FlagGems | `5.5.0.dev0+g8200f71f5.d20261020`；`8200f71f51d784d54a5a51019cb955acb74d64c1` + env-001 适配补丁 |
| FlagGems-vllm | `0.3.0.dev1`；`fa78ddee4c3e78ce5047213ff0ef02acff34b2d5` + env-001 适配补丁 |
| Torch / Triton | `2.10.0+metax3.8.2.2` / `3.6.0+metax3.8.2.2`；原 FlagTree 运行时被匹配 vendor Triton 替代 |
| mctlassEx / mcoplib | `0.1.1+metax3.8.2.2torch2.10` / `0.4.9+g8b5bd8b.maca3.8.0.25.torch2.10` |

最终默认 Python/SDK 的生产 bootstrap、DS 模型/Worker/ModelRunner 导入及重复 `register_model()` 均通过，日志 `logs/final-production-bootstrap.log`。28 项 CPU 契约在切换后的默认 Python 再次通过；设备数值/graph 测试在与最终环境相同的暂存包和 SDK 上通过，源与 ABI 均保持。三仓库 `git diff --check HEAD` 通过。未创建 Git 提交或推送。

原始证据均位于容器 `/opt/dsv4-upgrades/20261020-plugin-main-01/`：

- `logs/stage-graph-smoke.log`：18 项，SiLU / padded gather / tensor-limit 均 capture 后两次改变输入 replay。
- `logs/stage-operators.log`：27 passed，172 deselected；缓存布局与 alignment graph。
- `analysis/native-gemm.json`、`logs/stage-native-gemm.log`：实际 mctlassEx 原生 INT8 GEMM，三种 shape 数值检查、各两次改变输入 replay。
- `logs/final-test_deepseek_v4_packaging.py.log`、`logs/final-test_deepseek_v4_layer_boundaries.py.log`：20 + 8 项通过。
- `analysis/dependency-delta.json`：最终 `pip check` 仍有 vendor 原镜像已有的 15 项缺失/版本差异，新增 0 项，不将整体依赖检查记为通过。未为满足 NVIDIA 通用 wheel 元数据而覆盖 MetaX Torch ABI 或安装 CUDA 栈。该包内 NVIDIA CUDA 扩展在 MetaX 上缺少 `libcudart.so.13`，没有宣称它们加载成功；目标原生路径用实际 mctlassEx/MCOP 和 Triton 验证。
- `plugin-final.patch`：SHA-256 `45b18ed18c3804b0eeaf42e94edf46153cf2f1da7a95103a7050b626bf312270`；两算子库补丁 SHA 与 env-001 相同。

备份：`backup/conda-env001` 为完整旧运行时，96,286 个条目及内容/链接 SHA-256 `a9094c28c0006170d96b3c21cbcaa69a6d0ccb4a643b098c710db2e6ff1249b9`，源与备份一致；`backup/plugin-env001-tree` 为切换前实际 Plugin；`/opt/maca-3.7.0` 原 SDK 保留。`commands/runtime-rollback.py` 默认仅 dry-run，恢复需在用户明确要求回退且目标推理服务停止后使用 `--execute`，会保留当前环境；没有执行回退。

结论边界：本次完成容器环境升级与组件回归。权重仍未挂载，没有启动推理服务，也没有完整模型 graph、TP8、正式精度或性能验收；`pr_readiness=experimental`。env-001 回执和原镜像 manifest 继续作为历史记录，当前默认事实以 env-002 的 `upgrade-receipt.json` 为准。

env-002 最终回执 SHA-256：`7b4e57670c0c48a7345be3f53662690ebe98bda8c2cc04e346fd83f63f8fc6f3`。

## env-003：补充主机目录挂载（已完成）

用户明确要求给当前容器增加 Host `/public-flash`、`/data` 挂载。已通过 inventory 与 `connectivity-check --limit mx-59`；两个目录均为真实目录、无符号链接，容器内对应路径不存在，目标容器当时仅运行 `/bin/sleep infinity`。按用户指定路径增加同名读写 bind mount；共享业务目录仅做 stat 检查，没有写入探针文件。Docker 在其 `/data/docker` 存储目录内正常保存快照与容器元数据。

Docker 不支持直接给现有容器增加持久 bind mount。本次先在容器私有 `/opt/dsv4-upgrades/20261020-add-host-mounts-01/` 保存脱敏 inspect、精确命令、配置与版本身份；将当前已升级 writable layer commit 为本地不可变快照。使用原有效 Config/HostConfig 创建候选容器，复用既有 `/var/lib/dsv4` volume，增加 `/public-flash:/public-flash:rw`、`/data:/data:rw`。核验候选配置后，仅停止并改名本任务当前容器，将候选改名为 `deepseekV4-flash` 并启动；保留旧容器和快照，不删除 volume 或其他容器。

启动后核验挂载 Source/Destination/RW、目录设备号/inode、现有 volume、镜像谱系及 main/vLLM/算子库源码和版本；不得把目录可见误报为完整模型验收。失败时保留失败候选并恢复原容器名称与运行状态。命令先保存再执行；无 Host 目录中新增控制文件，无凭据或完整环境变量落盘。

### 最终结果与验证

`deepseekV4-flash` 已重建并运行，仍使用 `/bin/sleep infinity`，没有启动推理服务。当前挂载为：

| Host 来源 | 容器目标 | 访问 / 传播 |
|---|---|---|
| `/public-flash` | `/public-flash` | `rw` / `rprivate` |
| `/data` | `/data` | `rw` / `rslave` |
| 原匿名 volume `ced56f1c…` | `/var/lib/dsv4` | 原 Source、Name、Driver、RW、Propagation 保留；Mode `rw` 与原空 Mode 归一化相等 |

Docker 要求包含 daemon root `/data/docker` 的 `/data` bind 使用 `rslave` 或 `rshared`；选择单向传播的 `rslave`，未修改 Host 的 mount propagation 配置。API 默认给显式 volume 加入了 `z` 标记，最终改用原 volume 名的 `:rw` 声明，恢复原有效挂载选项。`OomKillDisable: null → false` 是 Docker 默认值规范化，OOM kill 仍为启用；设备、64 GiB shm、IPC、网络、资源限制及原环境变量保持。

当前环境从原容器约 29.7 GB 的有效 writable layer 保存为不可变本地快照，完整保留 env-002 的 main、非 empty vLLM 与回退材料：

- 快照：`flagos-local/deepseekv4-flash-main-vllm024:20261020-before-host-mounts-01`。
- 镜像 ID：`sha256:746168529b418c5b6b4616650f128da8a1f87cb542f75bd9012b6c75b24ecc7c`。
- 原容器保留为 `deepseekV4-flash-before-host-mounts-20261020-01`，已停止；校正 volume 选项的中间容器保留为 `deepseekV4-flash-mount-options-backup-20261020-01`，已停止。没有删除原容器、镜像或数据卷，也没有停止其他服务。

版本、三个仓库 HEAD / 完整补丁 SHA，以及 env-002 回执内容 SHA 在重建前后完全一致；包括 vLLM `0.24.0`、Plugin `0.3.0rc2.post1+ga696859b9.d20261020`、Torch `2.10.0+metax3.8.2.2`、Triton `3.6.0+metax3.8.2.2`。两个 bind 的容器内设备号和 inode 均与 Host 目录一致。项目 `verify-container-mounts.py` 对照“原挂载 + 用户明确要求的两个 bind”输出 `mount_parity=passed`；这不是原挂载清单未改变的声明，授权新增项已单独记录。

证据根目录：容器 `/opt/dsv4-upgrades/20261020-add-host-mounts-01/`。`commands/` 保留原编排、续接修正与最终挂载检查命令；`source-identity.json`、`final.inspect.sanitized.json`、`volume-mode-parity.json`、`desired-mount-comparison.json` 和 `mount-update-receipt.json` 保存身份与验证。inspect 删除完整 Env 后归档。Docker 29 的 commit 弃用提示首次混入 stdout 导致镜像 ID 解析失败，已改用 image inspect；挂载传播与默认字段差异均按当前 daemon 的真实结果调整，未重复保存快照。

最终挂载回执 SHA-256：`fa1a191a1104ae0b4cc2c5299dcf7c79265bd9c567628c3a5c77681fe396ca4a`。本次仅改变挂载与容器运行身份，未重跑正式精度/性能，未宣称完整模型验收。

## env-004：指定权重的模型运行验证（minimal-regression 已通过）

用户提供模型目录 `/public-flash/models/DeepSeek-V4-Flash-0731-Quant-W-INT8-PerChannel-A-INT8-PerToken`，要求验证当前容器。执行范围为当前环境的模型运行与 `minimal-regression`，不开展性能优化或签发正式精度 gate。使用本地 `e2e/accuracy` 技能，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；短检查采用前台进度，不新建定时任务。

只读预检：Host 与连接已验证；目录可见，index 列出 72,317 个 tensor、62 个分片，分片均存在、总文件大小 306,197,836,792 bytes。`config.json` SHA `4db517940da11dc9f1578059c39140e2b563faf34ba977041e4e38686f511584`；index SHA `43bf89afab8a3c1585e883623802102d08218851ecae68c882fff26891a1dc53`。配置 architecture 为 DeepseekV4ForCausalLM、43 层、64 heads、hidden 4096，compressed-tensors 声明 W8A8 channel/token symmetric INT8；`expert_dtype=fp4` 与之不一致，下一步从 safetensors 实际头部核验，不能直接改共享权重。

资源与授权：GPU0/1 每卡约 62 GB 被 `qwen3vl-p64k-opt-20261015` 的服务占用，其余六卡接近空闲。用户明确回复“你直接把进程 kill 掉就行了，不要停容器”，已授权只终止该 Qwen 推理服务进程树以释放资源，必须保持容器运行，不扩大到其他进程或服务。先重新读取实时进程身份、父子关系、命令与容器归属，保存精确操作再执行；记录结果和设备释放情况。

验证计划：在 DeepSeek 容器私有 `/opt/dsv4-upgrades/20261020-model-smoke-01/` 保存执行脚本、配置、身份、日志和原始响应。先核验所有 safetensors 头部/索引/offset/大小及量化 dtype，再核验 tokenizer 与当前 CLI；必要的模型配置适配通过启动 override 或 Plugin 私有兼容层实现，保留改动与回退，不修改共享权重目录。按原 TP8 / graph 配置启动，使用无冲突端口，检查 readiness、capture 与两次 replay、固定单请求和 C8 输出。失败即冻结原始证据，定位启动或运行问题后重试；完整 GPQA/性能未运行时明确记为未验收。

资源释放已完成：精确核验 Qwen 服务进程组与容器归属后，先 TERM、对剩余服务父进程 KILL；Qwen 容器仍运行。八卡随后无业务占用。证据为 `analysis/qwen-service-stop.json`。

全部分片头部、索引、shape/offset/大小检查通过；35,328 个 expert 权重 tensor 均为 I8。原 `expert_dtype=fp4` 为不匹配元数据，通过 CLI `--hf-overrides '{"expert_dtype":"int8"}'` 纠正，不修改共享权重。三个 hash MoE 路由表实际内容与原适配契约逐一匹配。完整 payload 校验和未计算。

attempt01 使用 TP8、FP8 KV、FULL_DECODE_ONLY、最大上下文 66560、端口 18001；新 vendor 运行时启用 breakable cudagraph 并将 compile mode 设为 none。首次进入权重加载时，旧 `FusedMoE.make_expert_params_mapping` 调用失败，因为新版为工厂函数。失败日志原样保存在 `attempt01/server.log`。修复计划：仅在 Plugin DeepSeek 模型使用新版公开独立映射函数，并将旧 FP8 分支类型检查对应到新版 RoutedExperts；不改 native vLLM。保存文件备份和补丁后用新 attempt/cache 再启动。

映射修复已执行，原文件为 `backup/deepseek_v4-before-mapping.py`，变更身份为 `analysis/mapping-fix.json`。attempt02 已越过该失败点进入分片加载；为补齐 graph 实际执行证据，在加载早期仅结束本任务服务进程组，保留日志，使用 `commands/start-model-v2.py` 开启原生 `--cudagraph-metrics`，新 attempt03 / 独立缓存继续验证。固定两个 C1 加八个并发请求的契约由 `commands/minimal-regression.py` 在发送前冻结，temperature=0、seed=0、max_tokens=96、关闭 thinking；非正式精度评分。

attempt03 完成 62 分片加载（rank0 日志 158.36 秒），在 warmup 的动态 INT8 量化中失败。`flaggems_vllm/ops/dsv4_int8_quant.py` 的私有 reciprocal extern 以 `mxc_rcp` 定义，却只作为 `libdevice.dsv4_mxc_rcp` 导出；新 Triton 编译器按函数名解析，产生 `libdevice.mxc_rcp` 缺失。计划先保存 `logs/quant-before.log` 最小复现，再只对齐私有函数定义/调用/导出名称，保留 `llvm.mxc.rcp.f32` 和全部量化算术顺序；不覆盖任何现有 Triton 内置函数。使用设备数值和改变输入的 graph replay 检查后更新真实 source hash 锁，新 attempt/cache 验证。诊断技能 bundle SHA `796f57d730fa08a05afa0417af3107087e8513d3de2c989d6a14b80ee8aece2e`；两个启动阻塞均归为执行/API 迁移，完整模型回归仍待完成。

量化诊断续接：仅对齐函数名仍因新版 compiler module-map 失败（`logs/quant-after.log`）。最终按实际 Triton 3.6 extern 契约改用 `_semantic`，直接发出相同 `llvm.mxc.rcp.f32`，移除旧 FlagTree 的 `__module__` 伪装、libdevice 动态属性和私有全局映射表增项。1×4096 最小复现已编译执行成功（`logs/quant-after-v2.log`）。随后运行 `commands/quant-validation.py`：与实际 `mcoplib._C` 的动态 INT8 原生 kernel 比较，覆盖空输入、零行、K=8192/8193 两侧、16384 上界及 graph 两次改变输入 replay；结果待回收。原始文件和失败中间文件均保留。

量化回归结果：8 组 shape 的 q/scale 与当前原生参考逐位一致，7 组非空各完成两次改变输入 graph replay；`analysis/quant-validation.json`。依赖锁已更新为实际内容与当前 runtime 版本（原 runtime_distributions 仍留有 env-001 历史值，本次校正）；SHA `a3f16f2ea8365adb4d7e3125bf971f7167288c2194e48829c1f6530f74215edf`。attempt04 已启动，随后用户要求源码升级 FlagTree，按新指令先结束该验证服务进程组，保留全部日志；完整模型 smoke/C8/graph 仍未通过，不据组件量化检查宣称整模型成功。

## env-005：从官方源码升级 MetaX FlagTree（已完成，整模型最小验证通过）

用户指定官方 Wiki `https://github.com/flagos-ai/FlagTree/wiki/User-manual-for-metax`，要求源码方式安装 FlagTree。本次授权覆盖当前目标容器的编译器替换；不涉及其他容器或 Host 驱动。官方当前 MetaX 3.6 手册要求 main、`FLAGTREE_BACKEND=metax`、源码根目录 `pip install . --no-build-isolation`，使用 MetaX LLVM19 与 Python3.12 plugin。执行前计划：在私有 `/opt/dsv4-upgrades/20261020-flagtree-source-01/` 记录手册/源码 SHA、当前 Torch/Triton/FGV 身份和备份；从官方 main 获取源码与精确构建依赖，先构建 wheel，保留完整构建日志，再替换本容器编译器并核验实际导入、MetaX backend、设备算子、graph 及整模型验证。原 vendor Triton 安装文件/metadata 完整保留，可精确回退；不修改共享模型目录，不降级当前 main/两算子库或更换 Host SDK/驱动。代理仅经进程环境使用，不保存凭据。新远端命令先保存再执行。

已获取官方 main `317a0249ec25c6756e0aee3a87e8e3c92f154335`，Git fetch 与 GitHub main API 返回一致；源码 `/opt/dsv4-sources/FlagTree`。Wiki 通过文档工具读取成功，raw Wiki URL 归档请求返回 404，不影响源码身份。实际 main 锁定 MetaX LLVM19 `3.8.0.6/v0.6.0` 与 plugin `v0.6.2`，后者较 Wiki 示例 `v0.6.1` 更新；按实际源码依赖构建。当前 vendor Triton 的 443 个安装条目已完整备份并逐文件校验，见 `backup/vendor-triton-prefix/` 和 `backup/vendor-triton-files.json`。容器默认 pip 的 HTTP Aliyun index 未找到构建包，失败日志保留；`commands/build-v2.py` 改用官方 PyPI，仅安装源码声明的构建工具，之后 `FLAGTREE_BACKEND=metax MAX_JOBS=32 pip wheel . --no-build-isolation --no-deps`。不会因手册 Qwen 示例回退当前 Plugin/FlagGems。

构建推进：已安装 CMake 4.0.3、pybind11-stubgen 3.0.0，已有 pybind11 3.1.0/ninja/setuptools 保持。官方依赖下载经代理返回 tunnel 500，直连均为 HTTP200；`analysis/dependency-network-probe.json` 保存四路测试。`commands/build-v3.py` 仅让官方依赖主机直连，成功获取并解压 MetaX LLVM/plugin；CMake 生成阶段因缺少 ZLIB 开发目标失败，日志保留。当前正执行容器内 `apt-get update` 和 zlib1g-dev dry-run，核验影响后补齐构建依赖。旧 Triton 尚未卸载。备份 manifest SHA `7cfd565fe020f80d5a068231b0e2c20d392d8613c652a7deb9f3dc0ef74ae4ba`。备用官方 commit 源码归档 22,223,870 bytes，SHA `075eb5b382dc438e9a54b87d9de6895b5e22dd1c674c04379802cff6973501fb`；实际构建仍使用已核验的 Git main 源码。

源码构建完成：zlib dry-run 确认 0 升级/1 新增/0 删除，精确安装 `zlib1g-dev=1:1.2.11.dfsg-2ubuntu9.2`，现有 zlib runtime 保持。`commands/build-v4.py` 完成 416 个编译/链接目标并生成 `flagtree-0.7.0+metax.git317a0249-cp312-cp312-linux_x86_64.whl`，426,228,107 bytes，SHA `7f084144691a04e3e546ec5d0d5cb40915667b4d52de6a208a7c0d2c52f08716`；完整日志为 `logs/source-wheel-v4.log`。这是真实本机源码构建，非下载预编译 FlagTree wheel。当前使用 `commands/stage-validation.py` 安装至私有临时目录，检查 wheel 的 MetaX marker、实际 target，以及量化/SiLU/KV gather graph；通过后 `commands/install-default.py` 才卸载 vendor Triton 并安装本 wheel，失败自动恢复 443 个旧文件。随后更新 launcher/依赖锁，将发行包 `flagtree` 与其提供的 `triton` 导入模块分别核验；不伪造 triton 包元数据。

首轮临时检查：实际设备为 MetaX C550，target 为 `maca/arch80/warp64`，但首个 kernel 编译在 `load_dialects(MLIRContext)` 失败。二进制证据确认官方 plugin 的 pybind internals 为 v11，而现有 pybind11 3.1.0 让本机新建 libtriton 使用 v12；wheel 构建成功不代表可用。首轮 wheel 与 `stage/` 保留，未替换默认编译器。`commands/build-v5.py` 改为在私有 `build-pybind11-v11/` 安装 pybind11 3.0.1，并仅通过构建进程 PYTHONPATH 使用；不降级默认 pybind 或 Torch。CMake 已明确识别该 3.0.1 路径，重新构建至 `wheels-v11/`，后续使用独立 `stage-v11/` 与日志验证。源码 main 与官方 plugin 均不打补丁。

ABI 对齐构建的最终 wheel：424,444,490 bytes，SHA `4a5286b195652a01dbf16393f69ec97ea36bdba863a41f69f7f54528e66704c5`，发行版 `0.7.0+metax.git317a0249`。`analysis/pybind-abi.json` 证明 plugin 与重建 libtriton 均为 internals v11，首轮 libtriton 为 v12。新 backend 的 warp64 使原单 token K4096 的 16-warps 默认配置超过该 kernel 的 512-thread 上限；仅将该自动默认值改为 8，保留显式参数和全部量化数学。补丁位于 FGV 原 DS 专用量化文件，不改通用 dispatch 或 FlagTree。原文件与失败 stage-v11 日志保留。

`stage-v11b/` 验证全部通过：实际 target 为 `GPUTarget(backend='maca', arch=80, warp_size=64)`；8 组量化的 q/scale 与当前 MetaX 原生实现逐位相同，7 组非空输入各两次改变输入 graph replay；18 项 SiLU/gather/tensor-limit 数值与 graph 检查通过。随后已卸载 vendor `triton 3.6.0+metax3.8.2.2`，把本机源码 wheel 安装到默认 `/opt/conda`；实际导入为 `/opt/conda/lib/python3.12/site-packages/triton`，import version 为 `3.6.0`，发行包名为 `flagtree`。关键 Python/marker/两个 .so 文件均与该 wheel 内容 SHA 一致。Torch `2.10.0+metax3.8.2.2`、vLLM `0.24.0`、默认 pybind11 `3.1.0`、SDK 与 Host 驱动保持。

launcher 与依赖锁已核验 FlagTree 真实发行版、实际 triton 模块来源及 MetaX marker。CPU 原生直接 unittest 20+8 项通过；首次误用 pytest 会被根 conftest 预先导入 Torch，污染 no-import 测试，27+1 的失败日志保留并记为 runner 不适用，未为此修改产品逻辑。三仓库与 FlagTree `git diff --check HEAD` 均通过，无 Git 提交或推送。pip check 保留原 15 项 vendor 差异，并新增 5 项依赖发行包名 `triton` 的提示；实际 triton 模块由 FlagTree 提供且已硬件验证，不伪造 triton metadata，不将整体 pip check 写成通过。

整模型在 env-004 `attempt05/` 使用新 FlagTree、实时版本身份和全新缓存重新启动；62 分片加载完成（rank0 40.16 秒），warmup 越过量化后发现 DS router 的 `_fused_topk_bias` 缺少 CachedOp 全局绑定。已仅补齐已有 dispatch 对象；通用非 DS 分支仍使用 main 的 native 路径。`commands/fix-router-binding.py` 保存修复与相关 DS 模块全局名静态审计，未再发现未定义全局名。上次服务随后已自行退出，只剩 root zombie，无存活关联进程，未对失效 PID 发送信号；`attempt06/` 使用新缓存继续验证。尚未签发完整模型 smoke、graph 或正式精度结论。

安装回执为 env-005 根目录 `source-install-receipt.json`，当前包含 wheel/已安装文件校验、源码/补丁 SHA、组件回归和依赖差异；最终模型结果回写 env-004，并在最后刷新补丁身份。

env-004 续接：attempt06 已越过 MoE 路由并进入 decode metadata warmup，失败于 NVIDIA `get_mla_metadata` 不可用。已定位为原 `apply_metax_swa_patch()` 仍导入 native 旧 `sparse_swa`，而当前模型使用 Plugin 私有兼容模块；不是缺少模型权重或需要安装 NVIDIA 栈。修复只将该既有 MetaX hook 的目标改为 `vllm_fl.compat.dsv4.sparse_swa`，继续使用当前 FlagGems 的 schedule metadata 与 SWA index kernel，不改 native vLLM。失败日志和原文件保留；先用 `commands/swa-binding-probe.py` 核验重复应用、空 schedule 结构和 native 模块不受影响，再以新 attempt/cache 重试。

SWA probe 已通过：两次应用幂等，provider 为 `flag_gems.fused.flash_mla_with_kvcache`，native 模块不变。attempt07 进一步进入 indexer decode warmup，失败于消费者仍断言 native `DeepseekV32IndexerMetadata`，实际 producer 为私有旧 ABI 的同名类。保留类型断言，在 `_dsv4.is_enabled()` 分支精确检查私有类，其他模型仍检查 native 类；FP8/BF16 两个原 DS indexer 入口同步此类型边界，BF16 硬件路径记为未测。`commands/fix-indexer-metadata-type.py` 保存原文件、SHA 与语法检查；attempt08 新缓存继续验证。

### 最终模型运行结果与归档

attempt08 完成 TP8 权重加载、KV 规划、decode warmup 和全部 `[1,2,4,8,16,32,64]` capture，API readiness 通过。固定请求 temperature=0、seed=0、max_tokens=96、关闭 thinking、prefix caching 关闭；2 个顺序单请求与 8 个同步发出的并发请求均 HTTP200、预期答案匹配、非空、finish_reason=stop。算式返回 `42`，中文返回“水在标准大气压下的沸点是100摄氏度。”，C8 八个结果依次为 34/36/38/40/42/44/46/48。无 readiness 后 ERROR。该结果只属于冻结的短请求最小回归。

| 验证 | 最终证据（容器内路径） |
|---|---|
| 原始 10 请求/响应、采样契约及输出检查 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt08/minimal-regression/`，`result.json` 为 10/10 passed |
| 完整模型 graph | `attempt08/verification-01/graph-runtime-evidence.log`；原生 runtime 表记录 C1 batch1 FULL×14、C8 batch8 FULL×2，预填充 NONE 为 FULL_DECODE_ONLY 的预期行为 |
| 当前实例身份、权重 metadata 未变、8 worker hash 审计与健康 | `attempt08/verification-01/result.json`，SHA `5dc868e098a3ffb77cb4c13de820adba543fbffb0fd75924f9ddc1d6319b27f5`；62 分片/72,317 tensor 的头部与索引验证保留，未计算完整 payload checksum |
| 最终源码 CPU 契约 | env-005 `analysis/cpu-final-direct-results.json`；20+8 项直接 unittest 全通过，日志另存 `*-final-direct.log` |
| FlagTree 安装与实际文件一致性 | env-005 `source-install-receipt.json`，SHA `43449a91d139a370f518148593616a0877596a1d19d75d8d6f3f112f1e1e7222`；本机源码 wheel 与默认安装的关键 Python/marker/.so SHA 一致 |
| 最终补丁 | env-005 `Plugin-installed.patch` SHA `0e6667b381c836446a41043d7b0e23c05ea6ccb96a7160b85b202384ed656973`；`FlagGems-vllm-installed.patch` SHA `961849cb4f411f0bef0ad22c36f02361be8fe5babec603e30c73c5aad621e7ac`；FlagGems 补丁仍为 `6cb6c8e2daab5829a6a18a7b6ef3c8137ad50f566f9a924df047a36c8514b258` |

当前服务与容器保留运行，没有停止 Qwen 容器、改动 Host 驱动或共享权重，也没有 Git commit/push。source-install 的早期 compiler-stage 回执和所有失败 attempt 均保留，最终以本节和顶部当前交付为准。FlagTune 缺少可选 xgboost 时按现有机制采用默认配置，未宣称启用该预测器。

结论：环境升级及该权重的 TP8 graph 最小回归 `passed`。正式 GPQA/精度 gate、长上下文、性能、BF16 attention、非目标平台与完整 FlagTree CI 均未运行；不能据此进入正式性能验收或声称全模型精度/端到端优化完成。`pr_readiness=experimental`。后续开始性能优化前仍须按项目流程创建独立优化环境并建立对应正式精度与性能契约。


## env-008：继续收敛到 vLLM 0.24 原生实现（已完成）

用户要求继续参考 PR #427，56 文件仍过多；本轮以真实删除旧模型/metadata/状态缓存副本为目标，不以文件拼接代替复用。已用 inventory 和 connectivity-check --limit mx-59 重新验证连接，实时 Plugin main HEAD a696859b9aa528dfd5b21f5da3403fdc16bac4cd、完整补丁 SHA 379414ef5541d925842c496d25a967209f689f40c63e90e0e348c22ada66105e 与 env-007 一致；attempt11 健康。

实施前计划：在本机 /tmp 创建独立候选副本，核对 PR #427 head da62cddeb538f3d9d203e4e07cbc164e94f76869 与官方 vLLM 0.24.0 ee0da84ab9e04ac7610e28580af62c365e898389。优先继承原生 Model/CausalLM 的权重加载、专家映射及通用转发，直接使用原生 MoE/MLP；替换旧 compressed/SWA metadata、状态缓存与重复 partial-state kernel。对必须保留的 MetaX INT8 cache、mctlass、graph 边界及本地算子保留窄覆盖；构造差异显式留在模型/平台边界，避免修改 vLLM 源文件或全局替换原生类。

远端全部新增材料使用当前容器私有 /opt/dsv4-upgrades/20261020-plugin-native024-01/，先保存命令、当前完整源码/.git index/补丁/源文件 SHA 和回退步骤，再 staging 验证导入、继承来源及数值边界。当前有效服务在候选准备完成前保持运行；切换前只按实时 PID/starttime/PGID 核验并结束本任务 attempt11 服务，保留容器。新 attempt12 及后续唯一缓存重跑 TP8、C1/C8、七档 capture 和两次 graph replay；不更改共享权重、挂载、FG/FGV/FlagTree。结果写回本节，正式 GPQA、性能与其他平台不据短检查签发通过；不 commit/push。

候选检查：staging 已验证实际继承来源。Model 的 load_weights/get_expert_mapping/finalize/embed、CausalLM 的通用转发/logits/MoE 参数收集、MoE、MLA forward_mqa/cache spec、SWA metadata build、Compressor 构造和 IndexerCache 均指向官方 vLLM 0.24。旧 BF16/MTP Plugin 副本、无实现的 BF16 provider 和未接入的 INT8-indexer 原型退出当前 W8A8 交付；native MTP registry 不再覆盖。当前 opt-in profile 明确支持 W8A8 INT8 / FP8 KV / TP8 / PP1 / 无 MTP，其他路径未验证。候选为 43 文件、11619 新增行（原 56 / 18156）；保留的 46 个数值 JIT 函数 AST 相同。CPU 20+9 检查通过。全仓静态扫描另有 7 个 main 原有问题，未修改无关平台；本轮涉及文件除 model_runner 的既有问题外 F821/F811 通过。

原生 compressor 完整 forward 在 MetaX FlagTree 上因 launch_pdl=False 仍为未知 keyword 而失败，保留一个小调用适配来省略该 keyword，复用原生状态缓存与 save/compress kernel。第一次独立 graph 组件探针超过 10 分钟未产出新证据，按实时 PID/命令核验后仅终止本探针，证据标为 incomplete；改为 180 秒上限的数值比较，三个场景（512/C4、512/C128、128/C4，均含 padding）状态与缓存逐位一致。组件 graph 不计通过，必须由完整新服务证明。

切换执行：SHA 守卫的 commands/apply.py 先校验备份及候选文件、staging 和数值比较，再仅结束本任务 attempt11、源码重装 Plugin，开启 attempt12 的全新缓存；容器和其他服务不停止。完整回退源码和 .git index 位于 env-008 的 backup/tree，旧服务日志及全部失败探针保留。

### env-008 最终验证与回退

attempt12 完成原 TP8 配置的权重加载与七档 `[1,2,4,8,16,32,64]` FULL decode capture。相同的 temperature=0、seed=0、max_tokens=96、非 thinking、prefix caching 关闭契约下，2 个单请求与 8 个同步并发请求全部 HTTP200、预期答案匹配、finish_reason=stop；单请求仍为 `42` 和“水在标准大气压下的沸点是100摄氏度。”，C8 为 34/36/38/40/42/44/46/48。原生 graph 统计 C1 FULL×14、C8 FULL×2；八个 worker 的三层 hash 表与基线匹配，12 个启动进程显式绑定审计通过，没有 vendor framework 导入或全局 FGV ATen 注册。readiness 后无 ERROR。本轮仅签发最小回归通过，正式精度/性能未运行。

| 证据 | 容器内绝对路径 / SHA |
|---|---|
| 最终回执 | `/opt/dsv4-upgrades/20261020-plugin-native024-01/native024-receipt.json`；`c185f46959e3d9ebfebf25a12e1f0ba64bed72871371bccd1c1907862c26ee3e` |
| 完整模型、graph、hash 表与权重 metadata | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt12/verification-01/result.json`；`6260ac24ba85f05f1ec7aa0f79845a8372a8cc7837a39acb40c122165f98e1cf` |
| 10 个原始请求/响应及预冻结契约 | 同 attempt 的 `minimal-regression/`；graph 摘录为 `verification-01/graph-runtime-evidence.log` |
| 原生复用与数值证据 | env-008 `logs/stage-v3.log`、`analysis/native-compressor-numerical.json`、`analysis/numerical-source-audit.json`；512/C4、512/C128、128/C4 均含 padding；原生 partial-state kernel 与基线 AST 相同 |
| footprint / 安装身份 | env-008 `analysis/installed.json`、`Plugin-native024.patch`；43 files / 11,619 insertions / 13 deletions，editable 安装与全部依赖版本不变；vLLM 2,469 个已记录 package 文件全量哈希核验 |
| 挂载与两个容器 | env-008 `analysis/final-containers.json`，三个 Mount Source/Destination/RW/Propagation 保持 |
| 可审阅差量补丁 | env-008 `native024-refactor.patch`；本机 `/tmp/dsv4-env008-native024.patch`，相对 env-007 有效源码执行 `git apply --check` 通过 |
| 回退 | env-008 `commands/rollback.py` 默认 dry-run；按实时 PID/starttime/PGID 仅结束当前 DeepSeek 服务后显式 `--execute`，从 `backup/tree` 恢复源码及 index、校验 env-007 补丁 SHA 并 editable 重装，再用新 attempt/cache 验证 |

早期自动审批因把旧 env-007/attempt09 脚本上下文视为本轮动作而拒绝切换；随后只读检查当前脚本及备份，`apply.py --check-only` 实时核验 env-008/attempt11、PID/starttime、全部原/新文件 SHA 与完整 index 备份后，同一切换操作获准执行。没有绕过审批或扩大停止范围。

Staging 上传：仅向 env-009 私有目录解压候选源码和已保存的 `commands/stage.py` / `commands/probe-inner.py`；以候选 PYTHONPATH 运行 240 秒上限检查，当前 attempt12 继续服务。归档 SHA256：`79896f0ffb06da5e34da9bf73927266dce3d41082dd90bc47965921d12246688`。使用 native Triton cache-index integer kernel 的边界比较，以及旧/新 W8A8 MoE 的空输入、C1/C8、chunk 边界、两种路由权重位置逐位比较；成功后再切换。

Staging v1 在注册阶段发现 main Backend 并无 fused_marlin_moe/cutlass_scaled_mm 方法；原实现只在 DS profile 增补，当前 W8A8 不使用。删除对应两项死注册，保留其他模型 main 行为，以新 tree-v2/cache-v2 重跑。未停止当前服务或应用失败候选。

Staging v2 阻止切换：预热发生在模型/attention 模块加载前，新建 CachedOp 尚未注册。修正为先显式加载既有审计模块，再调用未修改的 main prewarm，审计只读核对实际缓存 impl_id，不覆写其状态。新 tree-v3/cache-v3 重试；有效服务仍为 attempt12。

Staging v3 的原生归属、main prewarm 与 37 项绑定检查已通过；数值探针试图修改已冻结 policy 被正确拒绝。修正仅限探针：在其独立 cache/config 生成时设 chunk_size=32，启动后不修改冻结策略，以新 cache-v4 检查 chunk 边界；正式服务仍保持原 chunk 参数。

候选切换与索引整理脚本已写入本机 `/tmp/dsv4_env009_apply.py`，执行副本将保存到 env-009 `commands/apply.py`。其 `--check-only` 校验两目录 645 个文件及当前 index SHA、候选差量 SHA、14 项组件比较、当前 attempt12 PID/starttime/PGID 和两套备份；实际执行仅终止该服务进程组，然后应用同一差量、对原 43 个任务路径清理旧暂存并保留新增文件 intent-to-add、验证整理索引时工作区字节不变、editable 重装和 28 项 CPU 检查。回退脚本为 `commands/rollback.py`，默认 dry-run，恢复两套源码差量及完整原 index。

Staging v4：旧/新 W8A8 MoE 的 10 项设备输出全部逐位一致，包含 0/1/8/33/65 tokens、chunk32 和两种权重位置。随后空输入的旧 FlagGems global-index tuner 在 log2(0) 失败，属于旧参考的边界限制；cache-index 探针改用显式 Torch 语义参考，非空同时对比旧实现，并将 stride 用例限定为接口支持的 row-strided（末维连续）。不改变生产候选，以 cache-v5 继续。

待执行控制归档 `/tmp/dsv4-env009-control.tar` SHA256 `30fe323ead3568173b3e23f9e1475339e08e187faf6fa815f480b20c3e924f39`；上传后先执行 `commands/apply.py --check-only`，核验成功后同一脚本无 flag 执行。默认回退脚本先 dry-run。

已应用：两目录同一补丁 SHA256 `ce139038071999ce7205c316486733ee7a81abdf33a2809babf1e0aabb095047`，38 文件（25 生产），10,297 新增/6 删除；生产新增行 9,792→8,519。18 个 MM/AM 整理为真实工作区差异，整理索引前后文件内容 SHA 均不变，5 个恢复 main 的文件已退出修改清单。28 项 CPU 与 editable 安装通过，版本不变。下一步执行保存的 `commands/prepare-validation.py` 更新本轮验证标签、回退 dry-run，并以原配置启动唯一 attempt13；再运行 `commands/wait-and-regress.py attempt13`、`commands/verify-model.py attempt13`。

组件检查最终已通过：`logs/stage-v5.log` 与 `analysis/components.json` 共 14 项；MoE 10 项旧新逐位一致，cache-index 4 项均与显式 Torch 语义相同，非空还与旧 FlagGems 一致。五个 MetaX kernel/policy 文件（44 个顶层函数）字节完全不变。attempt13 已启动，执行本轮同契约验证；两个容器的镜像/挂载/运行检查使用本机 `/tmp/dsv4_env009_containers.py`，仅保存筛选后的 inspect，不读取或保存完整环境变量。

最终回执生成器保存为 env-009 `commands/final-env009-receipt.py`（本机脚本 SHA256 `de35ae364f28b82c93abff05a8688fce38ed604bb34da02928ab5355b8da0e9d`）；待整模型通过后执行。它重新核验两套补丁/38 个真实差异、5 个 HEAD 原文文件、零 MM/AM/空 diff 的 M、版本与 vLLM RECORD、FG/FGV 补丁不变、30 项审查表 SHA、14 项组件比较、hash 表及原生 GateLinear 绑定、graph replay 和两个容器。正式精度/性能/其他平台明确 not_run。

回退保护补充：显式执行前要求当前完整补丁、暂存差异和 Git 状态仍等于本轮已安装快照；发现后续人工源码/暂存变更即停止，避免旧 index 覆盖新工作。该补充只更新回退控制脚本，不改变服务源码。

### env-009 最终结果

本轮从 30 个生产文件逐项审查后保留 25 个；完整补丁 43→38 文件，其中 examples 11、tests 2。生产新增行 9,792→8,519；完整新增行 11,619→10,297，删除行 13→6。恢复 main 原文的五个文件为 `dispatch/__init__.py`、`platform.py`、`ops/custom_ops.py`、`vendor/metax/metax.py`、`vendor/metax/register_ops.py`（完整路径见审查表）。原生 GateLinear、Indexer workspace/cache view/fake、global-index kernel、MoE 默认配置和主线 prewarm 已复用；保留 MetaX mHC、INT8 舍入、MCTlass、no-TLE、稀疏 MLA、Indexer 分片及必要 graph 边界。五个 kernel/policy 文件的 44 个顶层函数所在文件字节不变。详细决定见 [30 个文件逐项审查](env-009-file-audit.md)。

用户 VS Code 目录 `/public-flash/jinghao/deepseekV4/vllm-plugin-fl` 与 editable 运行源码 `/opt/vllm-plugin-fl` 是独立副本，已应用同一候选并逐字节核对完整 Git 补丁。原来的 18 个 MM/AM 来自旧暂存版本与新工作区不一致；备份两套完整 .git/index 后，只整理本任务路径的暂存状态，整理过程工作区字节不变。最终两边均 38 个真实内容差异，暂存 diff 为空、MM/AM 为 0、与 HEAD 内容相同仍标修改的路径为 0；没有通过 core.filemode 或忽略规则隐藏改动。恢复 main 的五项已退出修改清单，其余 M/A 保留真实改动。

attempt13 完成 TP8 权重加载与七档 `[1,2,4,8,16,32,64]` FULL decode capture。两个 C1 和八个同步并发请求全部 HTTP200、内容匹配、finish_reason=stop；原生统计 C1 FULL×14、C8 FULL×2。八个 worker 的 hash 表通过；24 个 hash-layer/rank 组合证实调用原生 GateLinear，specialized/cublas 均 false，原重复子类可以删除。12 个 bootstrap 的 37 项绑定审计通过，无 vendor framework 导入或全局 FGV ATen 注册。readiness 后无 ERROR。28 项 CPU 检查、14 项设备比较、局部 F821/F811 与 git diff --check 均通过；全仓已有 main lint 问题仍按 env-008 记录，不修改无关文件。

vLLM 仍为 `0.24.0+empty`，2,469 个 RECORD 文件逐一校验，包内无 native .so，`vllm_metax` 缺席；Torch、源码 FlagTree、FG/FGV 的版本及完整补丁未改变。服务保持在 18001，两个容器运行、三项挂载与镜像不变。组件与短请求通过不能替代正式精度或端到端性能；GPQA、正式性能、长上下文、MTP、BF16/其他平台本轮未验证，`pr_readiness=experimental`，serial/RMS hook 仍受版本/profile 约束。不 commit/push。

| 证据 | 容器内绝对路径 / SHA |
|---|---|
| 最终综合回执 | `/opt/dsv4-upgrades/20261020-plugin-native-minimal-01/native-minimal-receipt.json`；`dac8bc2d992ee259740cd0ddd1457186db5b7089d8e1074c82116e4e6664cc5f` |
| 整模型最小回归、graph、hash 表 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt13/verification-01/result.json`；`6430493504bfa438cf60e8626292e870996485b684a9d19d200495c64b65fea6` |
| 当前源码完整补丁 | env-009 `installed-native-minimal.patch` 与 `vscode-native-minimal.patch`；两者 SHA `ce139038071999ce7205c316486733ee7a81abdf33a2809babf1e0aabb095047` |
| 逐文件与数值证据 | env-009 `analysis/file-audit.json`、`analysis/numerical-audit.json`、`analysis/components.json`、`logs/stage-v5.log`；空输入 cache-index 与显式 Torch 语义比较，非空另与旧实现比较 |
| Git 整理与最终复核 | env-009 `analysis/git-normalization.json`、`analysis/final-git.json`；完整原源码和 index 分别在 `backup/installed/`、`backup/vscode/` |
| 容器与挂载 | env-009 `analysis/final-containers.json`；筛选 inspect 无完整环境变量 |
| 回退 | env-009 `commands/rollback.py` 默认 dry-run；先精确停止当前本任务服务，再显式 `--execute --stopped-attempt attempt13`。检查当前补丁、状态与暂存区仍匹配本轮快照，发现后续人工改动即停止；恢复两套 env-008 源码差量及原 index 后 editable 重装，以新 attempt/cache 验证 |

复盘：通用路径的原生复用需要同时删除过期 registry 项，prewarm 必须在相关模块创建 CachedOp 后执行；冻结 policy 应在进程初始化前设置测试差异，不能在探针运行中修改。旧 FlagGems tuner 的 log2(0) 限制不能作为空输入的语义参考，应使用独立参考并保留失败日志。本次只形成当前版本与硬件的 observation，不修订通用 SOP 或宣称新增性能收益。

## env-010：Attention、Indexer 与 MoE 原生复用（已完成）

本轮是适配代码收敛，不是端到端性能实验。检查全部剩余 25 个生产文件，以 env-009 完整补丁 `ce139038071999ce7205c316486733ee7a81abdf33a2809babf1e0aabb095047` 为基线，两份源码与 index 均先完整备份。Host inventory 与实际 connectivity-check 通过；最初 sandbox Ansible RPC 失败，经授权范围内的提升执行完成连接验证。远端私有产物根目录 `/opt/dsv4-upgrades/20261020-plugin-native-components-01/`，下文 env-010 路径均相对此目录。变更脚本先保存至 `commands/`，通过 staging 的设备检查和 `apply.py --check-only` 后，才精确停止旧 attempt13 本任务服务进程组。容器始终运行，其他服务未受影响。

### 收敛与保留依据

- Attention：直接继承原生 `forward` 与 `attention_impl`，删除整段复制编排及冗余 Torch custom-op/fake/registration；原生 qkv RMS 接管。Indexer 继承原生 `forward`，使用原生 FP8 query RoPE/quant；packed cache gather 直接引用原生 Triton helper。原生 `eager_break_during_capture` 装饰器在 FULL runtime 下直接调用函数，整模型实测无 eager break。构造函数仍显式保留，因为原生构造硬编码 Compressor、Indexer、SWA，缺少工厂扩展点；不使用全局类型替换或类型伪装。保留 MetaX Compressor GEMM/PDL、INT8 o-proj、HQ16 和 sparse kernel；移除 checkpoint 不含且未使用的 indexer.k_norm。
- Sparse Indexer：FL custom-op 只承担 MetaX FP8 路径；非 MetaX `forward_oot` 委派原生 `forward_native`，由原生拥有 CUDA/ROCm/XPU/FP4 分派。MetaX FP4 显式不支持；当前验证是 FP8。原有 MetaX paged/fused logits、graph-safe、query-row sharding、tree topk 与可选路径保留。其他平台仅验证路由契约，没有硬件通过结论。
- MoE：MetaX W8A8 Experts 复用原生 `workspace_shapes`、`_resize_cache`、`moe_problem_size`、activation、moe_sum 和量化 helper；删除 329 行 functional `vendor/metax/impl/dsv4/moe.py`，消除私有 scratch 分配与输出 copy。保留 MCTlass GEMM ABI、no-TLE 对齐、kernel-M cache、chunking 及 H-config/SPLIT_K 语义；每个 chunk 使用独立 workspace slice，保护输出与 workspace13 alias。旧 Triton tile/stage 字段未传入 vendor tensor ABI，不再解析。原生 compressed-tensors W8 builder 未传 gemm1 clamp，本轮保持其实际量化契约与原数学，shared dense expert clamp 不变。
- 删除两个过期 RMS/query provider 与注册项，原生跨模块别名显式导出。没有改数值 kernel；五个 MetaX kernel/policy 文件逐字节相同、44 个顶层函数通过审计。25 个决策中 6 个文件缩减/重构、1 个删除、18 个文件字节不变；详见逐文件审计。

初版候选因 F401 自动修复删除了跨模块使用的原生别名而失败，通过显式 exports 修复；失败日志保留，未切生产服务。macOS Python3.9 的测试 harness 首次因运行时评估 `|` 类型注解失败，改用 postponed-annotations compile 后通过。没有为测试通过更改产品语义。第二版使用新缓存重验，之后安装同一通过候选。

### 验证结果与边界

30 项 CPU 测试（19 packaging + 11 layer boundary）在本地及安装后均通过，包含非 MetaX 原生路由、FP4 边界与原生方法身份；目标源码 F821/F811、源码 `git diff --check HEAD` 通过。全仓 main 已有 lint 问题仍按 env-008 记录，未修改无关文件。

22 项原生算子设备比较均逐位相同：qkv RMS 与 FP8 query 分别覆盖 M=0/1/8/33/129，RMS 输入含 stride=2048 的 q/kv views；cache gather 覆盖 block16/64/256、full/window、offset0/13 共 12 项，包含未写入 sentinel。20 项 modular MoE 与 env-009 functional 实现比较均逐位相同，覆盖 M=0/1/8/33/65、chunk32、router weight input 开关及输出/workspace13 alias，workspace 预填 NaN，GEMM 输出地址验证落在原生 workspace2 内。

attempt14 使用原 TP8 / FULL_DECODE_ONLY / capture sizes `[1,2,4,8,16,32,64]`、新独立缓存，prefix cache 关闭。七档 capture 全通过，两个 C1 与八个同步并发请求均 HTTP200、预期答案匹配、finish_reason=stop：C1 为 `42` 和“水在标准大气压下的沸点是100摄氏度。”，C8 为 34/36/38/40/42/44/46/48。原生 runtime 表为 C1 FULL×14、C8 FULL×2；8 worker hash 表、24 个 hash-layer/rank 的原生 GateLinear 与 12 个 bootstrap 绑定审计通过。首请求/JIT 耗时仅保留诊断，不作为性能收益。

最终回执重新核验两份完整补丁、25 项源文件决策、真实 Git 差异和全部组件/模型证据。两边各 37 个真实内容差异，暂存 diff 为空，MM/AM 与 HEAD 字节相同仍标修改均为 0；没有通过忽略规则隐藏改动。vLLM 2,469 个 RECORD 文件未变、无 native .so、无 vllm_metax；Torch、源码 FlagTree、FG/FGV 版本及补丁未改。两个容器均运行，原镜像及 `/public-flash`、`/data`、原 named volume 三项挂载不变，权重 metadata 不变。

| 证据 | 容器内绝对路径 / SHA |
|---|---|
| 最终综合回执 | `/opt/dsv4-upgrades/20261020-plugin-native-components-01/native-components-receipt.json`；SHA `a55cac8b7f9379151e566def522e7f28c20ad8e9f9d2b3e94cb59f54115635f0` |
| 完整模型/graph/8 worker 身份 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt14/verification-01/result.json`；SHA `e1ca9b701ff5f1aadf040fff8d8810afe1b1e40a618c6b5957cd3653fe3d8441`；同 attempt 保留原始请求、日志、launch 和缓存审计 |
| 两份完整补丁 | env-010 `installed-native-components.patch`、`vscode-native-components.patch`；均为 `005c7e074aa31014ef287192eb60a5ce78aabce8360b276bf5ef3dffe344d116` |
| 原生算子与 MoE 设备比较 | env-010 `analysis/native-components-probe.json`、`analysis/modular-moe-components.json`；日志 `logs/stage-native.log`、`logs/stage-candidate2.log`，失败 stage 日志另保留 |
| 逐文件、kernel 与 Git | env-010 `analysis/file-audit.json`、`analysis/kernel-audit.json`、`analysis/final-git.json`；本地 [25 文件复查记录](env-010-file-audit.md) |
| 容器与挂载 | env-010 `analysis/final-containers.json`，筛选 inspect 不含完整 Env 或凭据 |
| 备份与回退 | env-010 `backup/installed/`、`backup/vscode/` 完整源码/index；`commands/rollback.py` 默认 dry-run，已通过检查 |

回退时必须先按实时身份精确停止当前本任务服务，再显式 `--execute --stopped-attempt attempt14`；脚本检查完整补丁、状态、暂存区仍匹配本轮快照，发现后续人工修改即拒绝覆盖。恢复两套源文件差量（包括被删除 functional MoE）与旧完整 index、editable 重装，再用新 attempt/cache 验证。不能直接使用旧服务 PID。

本轮最小范围 `passed`，正式精度 gate/GPQA、稳态性能、长上下文、MTP、BF16 和其他平台均 `not_run`；`pr_readiness=experimental`，既有 serial/RMS runtime hook 仍受版本/profile 约束。没有提交、推送或创建 PR。复盘：优先继承原生编排及 modular workspace，数值 ABI 的 MetaX 边界继续显式保留；跨模块引用应明确导出，不能仅凭本文件使用情况自动清理。workspace alias 与 chunk 尾块须用 poisoned scratch 和地址检查验证。当前结果为版本与硬件限定的 observation，不据此修订通用 SOP 或宣称性能收益。

## env-011：构造、runtime patch 与 model_runner 原生扩展点复查（已完成）

这是适配源码收敛，不是性能实验。对象为 mx-59 / deepseekV4-flash / W8A8 INT8、FP8 KV、TP8/PP1、无 MTP。开始前 inventory 与实际 connectivity-check 通过；sandbox RPC 失败后提升执行通过，不以普通 SSH 退出码替代。两份源码基线补丁均为 env-010 `005c7e074aa31014ef287192eb60a5ce78aabce8360b276bf5ef3dffe344d116`，attempt14 health=200。新私有产物根 `/opt/dsv4-upgrades/20261020-plugin-native-hooks-01/`，以下 env-011 相对路径均指该目录。两份完整源码、全部文件 SHA、Git index、状态与版本先备份；所有远端变更命令先保存到 `commands/` 再执行。

### 设计决定与实际改动

1. **model_runner 恢复 main**：原两行修改把全局 cache dtype 改为 per-spec 字符串。逐项核对后，原生 MLA/SWA backend 根据 packed FP8 格式处理语义 head_dim；Indexer 和 Compressor backend 本就根据自身 head_size/spec 产生 shape、不使用该全局 dtype 来选择其他格式。原生 `get_attn_backend/get_kv_cache_shape` 已承担区别，无需 runner 覆盖。恢复 Plugin main 原文，并非把 Plugin 既有 Worker/ModelRunner 整体替换成 vLLM GPU Worker；后者需要更大生命周期改动，当前无必要。
2. **删除多流 runtime patch**：删除 `run_pair_serially`、`run_branches_serially`、`install_serial_execution` 与已无用途的 `compatibility.multi_stream_source_sha256`。Attention/Indexer 均传 `None`，原生 `execute_in_parallel/maybe_execute_in_parallel` 已内置同样顺序分支，且原生模块与其调用者导入的函数对象一致。模型不再创建随后被丢弃的三条 aux stream；attention 构造删除旧 indexer stream 选择。原数值方法及 MetaX compressor GEMM 顺序未变。
3. **Attention 构造保留边界**：已检查 vLLM 0.24 Attention、Indexer、Compressor、SWA Cache 的类层级及 CustomOp/PluggableLayer 注册 API。前三者不是可替换的 PluggableLayer，原构造仍硬编码子组件；CustomOp 的 OOT 可复用 SparseAttnIndexer，不能替换整个 Compressor/SWA 构造。保留 MetaX SWA tile scheduler、Compressor PDL adapter、INT8 o-proj 与 HQ16 构造门禁；不采用替换模块 globals、复制函数 globals、类型伪装或先构造后覆盖静态注册。将来原生提供组件工厂且相同缓存/权重/注册契约通过后，才可继续删除这部分。
4. **RMS runtime 调优保留**：该 hook 面向 Torch Inductor 生成的三类已审计 RMS 数学体、K4096 与 rank warps；vLLM 的 layer/OOT/backend 扩展点不能为这些生成 kernel 提供同等 tuner 配置。替换 RMS provider 会改变既定执行与数值路径，移除 tuning 则会丢失当前 MetaX launch 配置，缺少同条件验证不能宣称等价。因此原 RMS policy、vendor guard、hash 验证与幂等 bootstrap 均保持 AST；`pr_readiness` 仍 experimental。删除条件为编译器/算子层提供同数学体、相同配置的正式扩展入口并完成回归。

24 项决策中 1 个文件恢复 main 原文、3 个生产文件缩减、20 个逐字节不变；没有删除或创建源文件。另更新两个已有 example 文件（config/README）。五个 MetaX kernel/policy 文件逐字节相同，Attention/Model 的全部非构造计算方法 AST 相同；RMS 与保留的验证函数 AST 相同。完整 Plugin diff 36 文件包含生产 23、examples 11、tests 2；生产新增行减少 55，总新增减少 53，删除减少 2，不以机械移动文件制造下降。

### 验证、切换与证据

组件 staging 在旧服务继续运行时验证。42 项 GPU 缓存布局覆盖原生 spec：MLA C4/C128、SWA、Indexer、Compressor H512 C4/C128 与 H128 C4；每种分别测试 0/1/3 blocks 与普通/packed 页。两种 runner 的 shape、dtype、stride、storage_offset、data_ptr、内容逐一相同，包含 FP32 state 与 uint8 cache、576 对齐和 packed offset。当前模型无 Mamba，hybrid 分支不执行，其他模型的硬件验证未扩大。另 3 项行为检查覆盖 native pair 顺序执行、N 分支无 stream/显式 disabled、None 分支槽位；访问任何 event/stream 即失败。原生 helper 身份、已初始化后再次 initialize 的幂等与原生 Attention/Indexer forward 身份检查通过。

30 项 CPU 测试（19 packaging + 11 boundary）在本地和 editable 安装后通过；目标源码 F821/F811、`git diff --check HEAD` 通过。全仓已有 main lint 问题不扩大修改。组件候选首次验证通过，没有失败的模型候选被覆盖；本地控制脚本的编码/传输与 Skill selection 调整未改变生产源码，原工具输出保留，不作为模型通过证据。

`commands/apply.py --check-only` 校验全部 644 个源文件、两套 index、候选 hash、45 项组件证据及 attempt14 实时 PID/starttime/PGID 后通过；执行模式只停止该本任务服务组，两个容器持续运行，其他服务未变。应用 6 个文件并只整理原 37 个任务路径的 index，工作区字节未被 index 操作改变，随后 editable 重装。两份完整补丁 `d85f8340751bdaf89b0da9c842a6efea9e4d202058536ad794c2c4c42a71ae54`，版本保持，30 项 CPU 再次通过。回退 dry-run 完成，使用相同 TP8 启动配置与全新 attempt15/cache 重验。

本地 `$inference-accuracy-evaluation` / `e2e/accuracy` 显式模式 `minimal-regression`，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，本轮覆盖 env-011。沿用已冻结契约：两个 C1 加八个同步并发请求、temperature=0、seed=0、max_tokens=96、thinking/prefix cache 关闭。短任务前台检查，无监控自动化。attempt15 七档 `[1,2,4,8,16,32,64]` FULL decode capture 全通过，10/10 HTTP200、内容匹配、finish_reason=stop；C1 为 `42` 和“水在标准大气压下的沸点是100摄氏度。”，C8 为 34/36/38/40/42/44/46/48。原生 runtime 统计 C1 FULL×14 / C8 FULL×2，8 worker hash 表、24 个原生 GateLinear 组合与 12 bootstrap 的 35 项以上绑定审计通过。首请求/JIT 时间仅为诊断，不能作为稳态性能结果。

| 证据 | 容器内绝对路径 / SHA |
|---|---|
| 最终综合回执 | `/opt/dsv4-upgrades/20261020-plugin-native-hooks-01/native-hooks-receipt.json`；SHA `e3f1076c6abd00a25c3e8b289b8717e573b35a00f39cb7d186a6b9729754e06e` |
| 实例、C1/C8、graph/hash 审计 | `/opt/dsv4-upgrades/20261020-model-smoke-01/attempt15/verification-01/result.json`；SHA `0ff7c8c7abfcdff57cdcb6949e25b5f6db5c73b73f1782c6fb7579ee63d1fde5`；同 attempt 保存原始日志/响应/launch/cache 审计 |
| 完整源码补丁 | env-011 `installed-native-hooks.patch`、`vscode-native-hooks.patch`；均为 `d85f8340751bdaf89b0da9c842a6efea9e4d202058536ad794c2c4c42a71ae54`；`env010-to-env011.patch` 为本轮差量 |
| 组件与原生方法证明 | env-011 `analysis/native-hooks-components.json`（42 GPU + 3 helper）、`analysis/native-hooks-proof.json`、`logs/stage-candidate1.log` |
| 源码边界与逐文件复查 | env-011 `analysis/file-audit.json`、`analysis/kernel-audit.json`、`analysis/footprint.json`；本地 [24 文件复查](env-011-file-audit.md) |
| Git/容器/依赖 | env-011 `analysis/final-git.json`、`analysis/git-normalization.json`、`analysis/final-containers.json`；综合回执核验 vLLM 2,469 RECORD 与 FG/FGV 补丁 |
| 备份与回退 | env-011 `backup/installed/`、`backup/vscode/` 完整源码与 index；`commands/rollback.py` 默认 dry-run |

最终核验：两份各 36 个真实内容差异，暂存 diff 为空、无 MM/AM/HEAD 相同仍标 M，恢复 main 的 runner 已退出修改列表。vLLM 0.24.0+empty 文件哈希未变，无 native .so/`vllm_metax`；FlagGems、FlagGems-vllm、源码 FlagTree、Torch 未改。两个原容器运行、镜像与三项挂载一致，权重 metadata 未变。未 commit/push 或创建 PR。

回退须先重新核验并只停止当前本任务实例，再显式 `--execute --stopped-attempt attempt15`。脚本检查完整补丁、Git 状态与暂存区仍匹配本轮快照，拒绝覆盖后续人工更改；恢复两套 env-010 文件差量和完整原 index、editable 重装，再用新 attempt/cache 验证。不得复用旧 PID 或旧缓存。最小范围 passed；正式 GPQA/gate、稳态性能、长上下文、MTP、BF16/其他平台均 not_run，不能签发正式性能结论。

复盘：先证明原生分支已能表达需求，再移除历史全局替换；对 runner 的 per-layer dtype 适配须沿 backend 真正消费参数的路径核验，不能仅看字段名推断必要性。无组件工厂时保留明确构造，比引入隐藏全局替换更易维护。当前结论是固定版本/硬件的 observation，不修改通用 SOP。

## acc-001: full GPQA Diamond (preparing)

User requested full accuracy and explicitly froze threshold 80%. Use e2e/accuracy formal-gate, full 198 IDs/limit0, fixed native strict-match metric; no code changes. Current env011 source patch d85f8340751bdaf89b0da9c842a6efea9e4d202058536ad794c2c4c42a71ae54 and attempt15 health200 verified. New CPU evaluator deepseekV4-flash-gpqa-20261020-01 uses official flageval-llmeval:v1 image and network namespace of the target inference container, no GPU or shared source mounts. Private evaluator artifacts /opt/dsv4-accuracy/20261020-env011-gpqa-01; inference-side control root /opt/dsv4-upgrades/20261020-formal-accuracy-01. Save all create/copy/probe/launch commands before execution. Existing containers remain unchanged. Task/data provenance twice, fresh measured model/tokenizer/source/runtime manifests, preflight then full native runner; no cross-run response reuse. Foreground progress, no unsolicited schedule. Structured state: models/DeepSeek-V4-Flash-W8A8/metax/20261020-env011-gpqa-metax59/acceptance/state.yml.

Before formal requests, capture current service manifest with full SHA256 for all 62 weight shards (8 read-only checksum workers), tokenizer files, actual installed engine/source package content, process command/starttime, graph evidence, and current image/mount inspect. Saved local command /tmp/dsv4_accuracy_capture_service.py sha256=0ed621033ee6b68595a0c8870a5719e1edc64021d9c119d9972759a9c86c5d0b. This reads data but changes neither weights nor source.

acc-001 preflight passed. Native task/data captured twice byte-identically (198 raw/processed IDs), provenance SHA d5a444983da9b0cb1f85d1977166cdbf1b439f3c722fa5f3e9c5ce4bcd0c7bb5, contract SHA cd0423d29a89946a78dd61e34d365c8fde2bcb0aca1ecc78d3fab53511cc50fc. Frozen generation follows measured model defaults temperature1/top_p1, top_k=-1, max_gen_toks30000, do_sample=True, request/CLI seed42; C32, full limit0, expected198; native model reasoning mode without smoke disabling overrides. Full 62-shard SHA256 manifest completed for 306,197,836,792 bytes; model identity ea2aec14c01b9677a75fae402ce2b084667195287038f5d131a0e98feb7f61b3. Official image actual customized lm_eval0.4.8 supports the collected task/API schema; no evaluator or model source changes. Native strict-match is primary; flexible-extract only auxiliary.

Formal launch saved as evaluator commands/launch-evaluation.py, sha256=d49950f6b142a27ac75d4560a1fd8f6708d1afbd64f716a544b1e6341b09c9e7. Source inspection confirmed native CLI TaskManager metadata merge, result seed/generation fields and multi-filter sample schema for actual custom lm_eval0.4.8; captured full evaluator source is bound in provenance. Launch once only, no whole-run automatic retry, retain exact supervisor/child identities and exit status.

acc-001 native full evaluation started 2026-10-20 13:24:34 UTC, one supervisor and one wrapper, external supervisor-process.json/formal-process.json. Foreground read-only status monitor commands/status.py observes native cache rows, HTTP metrics and exact child identities, without replacing scoring. No result yet.

acc-001 first full native run ended with strict/flexible0 and 198 API failures after EngineDeadError; retain raw run aefa3e513102461f845264e535f7ffee and no gate. Frozen failed server log at inference diagnosis-001/server-failed.log. First meaningful cause: FlagGems MetaX top_k_per_row_prefill invokes _sort_cand_kernel with16 warps, native FlagTree warp64 requires1024 threads but compiled kernel supports512. CachedOp then records provider failed and subsequent calls fail. This is execution failure, not evidence of GPQA knowledge score; do not substitute auxiliary filter or relax80%. Diagnosis uses local SKILL directly (no interface.json exists; no fabricated bundle receipt). Next: faithful op reproduction, isolated launch-metadata fix in actual MetaX library, graph/numerical checks, new service and same full contract with new response cache.

Compatibility fix plan before edits: actual MetaX vendor file only, sort_warps16 to8 (warp64/512-thread limit), no JIT mathematical-body changes. Save FlagGems full patch/index and exact file plus both Plugin dependency-lock/index/patches. Private candidate tests old minimal1x257/K128 failure against candidate8; FP32 sorted reference across strided logits, nonzero starts, padded output stride, tie order and two changed-input graph replays. Source-root is private /opt within this target container. No main vLLM or weights changes. Promotion only after device proof, update exact FG content lock in both Plugin copies and new service/accuracy manifest, retain unchanged198/80%/generation contract.

Operator minimal reproducer confirmed original1024>512 OutOfResources. First candidate FP32 random/graph check passed; a signed-zero tie reference mismatch stopped promotion. Candidate numerical code remains unmodified: correct reference ordering distinguishes +0/-0 as the existing uint32-key contract does. Repeat full matrix in versioned v2 logs and proof before promotion. A separate sample summary initially used splitlines and failed at legal U+2028 separators; switch to physical JSONL lines per maintained sample_validation, without altering native samples or evaluator. The actual MetaX top-k file matches current FlagGems HEAD byte-for-byte, so the launch incompatibility is inherited from the runtime/source combination, not introduced by env011 helper/runner reduction.

All seven v2 FP32/top-k cases and two changed-input graph replays per case passed. Old launch reliably fails1024>512. Candidate only changes sort_warps16->8; all four JIT kernel bodies identical. Guards/promotion/rollback saved in commands/apply-topk.py and commands/rollback-topk.py; default check/dry-run first. Only actual vendor file and the FG content fingerprint in both Plugin lock files change; no Plugin production file added. attempt15 exited itself; require no live own PGID before edits. Start attempt16 with new cache after30 CPU tests, then same full198/generation/80% contract.

acc-001 launch compatibility fix installed after guards: seven op/reference cases and14 changed-input graph replays passed; all JIT bodies unchanged. Full FlagGems patch6be5befa86f2568f94de51bc12be73a74f24acb53beb690cc7f988b905930c21; top-k file3bc33f15afca75d578596060e5d50e65264b56d983dea3a812b5f63b337b4bea. Both Plugin copies only update FG content lock, full patchfc653169d482b61133db1783f22921a5432b7f7b4bf4e7a3eb67022f8c649223; production adaptation remains23 files.30 CPU passed. attempt16/new cache uses same runtime/launch configuration; full score remains pending. First native run confirmed198 unique docs/396 filter rows, all198 TIMEOUT, samplesSHA474d93688713d7e6c841fcad5297015fb14b072999e8d915e8c5bd319e92d03d.

acc-001 attempt16 passed model verification: 10 requests, seven capture sizes, 14 FULL C1 and two FULL C8 replays. The separate 3616-token probe hit actual prefill top-k and returned HTTP200. All 62 weight payloads were hashed again and match the first full-run manifest. New service identity `deepseekV4-flash:attempt16:3456148:544417809`; source/service evidence `/opt/dsv4-upgrades/20261020-formal-accuracy-02/`. Two provenance captures exactly match the first run, SHA `d5a444983da9b0cb1f85d1977166cdbf1b439f3c722fa5f3e9c5ce4bcd0c7bb5`. New serialized contract SHA `8f73eebff5e2de553c133e739034da8f3b36d7d570926efd3b83e2addaa59ae8` changes only the provenance artifact path; metric/threshold/data/generation/concurrency are identical. Preflight passed. Full run `15b9eb63f95c471d8d8c02dfb3d65256` started UTC14:11:48, evaluator evidence `/opt/dsv4-accuracy/20261020-env011-gpqa-02/`, fresh UUID response cache, foreground monitoring active. No final score or gate yet.

Final acc-001/acc-002 outcome: full run ended UTC14:30:06 with strict101/198=51.010101%, below the frozen80% threshold. 198 unique docs/396 filter rows passed provenance and completeness validation; timeout/empty/truncation/garbled observations all0. Wrapper exit1 is the threshold failure, not a service crash; no run-record or gate. SamplesSHA `bad72ffb7baa111d61cd3dc321e71a280df90be3e3d11e6a23f6e93421025177`; resultsSHA `ff2edc4c48650624dd969e667c542c437befce89a45a4b50bab5cc9b1ff521cc`. Actual native RegexFilter replay matches all198 original records;61 invalid extractions are explained by Markdown-bold answer letters. Independent offline bold-removal diagnostic changes no original output/filter/score. Another36 valid extractions disagree with gold; no comparable known-good full baseline exists, so no attribution to a specific Plugin or numeric change. Formal accuracy remains failed; no performance work. Both full evaluator roots were archived at identical absolute paths in deepseekV4-flash:119files/14,664,179bytes, per-file SHA parity passed. Complete current result and open diagnosis are in models/DeepSeek-V4-Flash-W8A8/metax/20261020-env011-gpqa-metax59/acceptance/README.md and optimize/acc-002.md. Foreground monitor completed normally.

2026-10-21 acc-003 推理链路诊断：确认 native INT8 quant-config 遗失模型 routed MoE 的 swiglu_limit=10。attempt17 原数学观察器在8rank/688call中发现真实越界，最大激活2124，相同8请求与原路径内容/usage完全一致。设备12例 FP32/BF16限幅参考、30项独立unittest、整模型7次graph capture和C1/C8回放全部通过。只在现有MetaX expert构造中补传私有quant-config，复用原生activation，生产文件仍23。Plugin完整补丁为5ea09be19685b023b68ec43eed537793c366e7fa1c2fe6f5004361b2f948b4a9。

attempt18按相同198/C32/default-chat/strict80%契约完成全量回归：100/198=50.51%，去加粗辅助140/198=70.71%，未达80%；198唯一题/396行、原生结果归属和评测前后源码/实例核验均有效，超时/空输出/截断/乱码为0。限幅是必要语义修复，但本轮不支持其为低分主因。原101/198失败记录保留，无run-record/gate，无性能晋级。两份新诊断/评测目录已按相同绝对路径归档至推理容器，逐文件SHA通过。收尾实际运行源码保持5ea09be…；原VS Code副本目录在宿主机/容器中均已不存在，原因未知，未重建共享目录。完整结论与证据见模型案例 optimize/acc-003.md。
