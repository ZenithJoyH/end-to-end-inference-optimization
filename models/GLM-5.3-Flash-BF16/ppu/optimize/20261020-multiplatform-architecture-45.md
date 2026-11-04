# 点45：修正多平台架构边界、安装与版本去重

## 相对PR454的46文件审计与继续收敛（file-consolidation-04，14:51已完成）

已直接在容器实际editable Plugin应用窄化补丁：**46→42文件，7867→7684增行，原43删行不变，净减183行**。其中运行代码净减250行，测试净增67行；最终37运行代码/1策略YAML/4测试。删除两个转发Backend子类和两个MLA/MoE纯转发模块，不是把它们搬到另一个安装副本。HEAD保持纯PR454、当前分支不变，index tree `624d3ae78723e3cc117a56bb3f00769befcfa3ba`，42项暂存、零unstaged/untracked，VS Code源代码管理可直接查看。

实际安装目录的**95 CPU契约通过，0失败/跳过**；新进程重复注册及真实provider解析通过，MLA Prefill直接解析`flag_gems.flash_attn_varlen_func`，BF16 align/融合MoE直接解析`flaggems_vllm`公开导出。只解析函数、不调用数值kernel；不能将其写成设备命中/graph/完整精度通过。当前磁盘源码SHA `fa1ec556b1b938e700f38de1e40e9c2db466fa0b6f6723185794eaa223c27339`。

原7路径备份`file-consolidation-04/affected-files-before.tar.gz` SHA `82535cb2092c48e21e6def5b6e0f2b833cff125fae6464f543258a9a4abcd38a`，原index另存，删除的4文件可恢复，未触发回退。原始测试/真实解析/计数及前后运行身份分别保存在该目录的`installed-cpu.xml/log`、`installed-real-providers.log`、`numstat-before/after.txt`、`runtime-before.json`与`runtime-after-disk-update.json`，回执`completion.json`。服务仍是原实例、health200；源码以外的argv/环境、权重/tokenizer/DB与三个其他库一致。不重装、重启、停止、热重载或发推理请求，未commit/push。旧graph/gate不绑定新磁盘身份。

当前仍不能称为最小PR补丁：下一步应优先把2492行旧模型和774行cache/runner兼容层缩成公共模型的显式ABI适配，再收敛config/processor；需保持BF16/FP8缓存协议与多模态行为，并重新做graph/模型回归，不通过机械移动/合并文件降低计数。本次未进行这部分高风险合并，以下“执行前/预期”是保留的计划。

最终独立只读复核通过：95项无失败/错误/跳过，cached diff-check通过、无未暂存或未跟踪项，全部当前执行与源码身份仍等于完成回执，health200。`completion.json` SHA `724745b3df55efbb1f21b5a547458d1851124e5abe6cb29d2303b22f3b4fcbae`，`runtime-after-disk-update.json` SHA `a21ff4dbce8068211cb6383bc3dd14b7e1766694a399a70c28d6dbda0ba59d92`，`installed-cpu.xml` SHA `6fbec04631b1d8a3196792bf212b5a8ac755c80e4b82498c15ed33e9f68101bd`；`pr_readiness=needs_revision`，不是整套补丁已最小化或模型验收通过。

用户要求解释并进一步缩小46项修改。只读实际安装目录的暂存差异：35新增、11修改，共46文件，7867增行/43删行；其中4测试、1策略YAML、41运行代码，并非46项算子优化。主要膨胀来自保留BF16 indexer/cache/graph host实现，以及随附config、processor与多层转发适配。旧native模型2492行、兼容patch774行、processor868行、config269行合计4403行，超过新增行的一半；不能把这些都说成不可删除的优化。

首轮窄化改动只移除无语义的转发：两个BF16 Backend子类及FlagGems MLA Prefill/MoE转发模块，共4个新增文件；注册表直接懒解析现有FlagGems/FlagGems-vllm API与必要ABI adapter，复用公共Backend availability。保留impl ID、kind、vendor、priority、策略过滤与异常传播，不碰公共PR454默认注册，不引入平台判断、库升级或新开关。更新现有测试，以实际注册后的转发、prepare、参数/返回传递、缺库与错误传播检查代替已删除子类的继承断言。

暂不删除config/processor：实际权重经两套config解析后唯一字段差异是`text_config.head_dim`旧64/PR454为0；processor在视频采样、预算与`_smart_resize_max`接口上不等价。删除它们需要显式行为迁移与模型/多模态回归，不能本次称作等价清理。该差异只读检查的第一次输出工具因整数dict键打印失败，修正打印后两套config都成功解析；未构造模型或发请求。

精确目标不变：PPU-13 / `glm5.3-flash-opt-20260911`内实际editable `vllm-plugin-FL-review-20261020-p45-v4`，不是审查副本。预保存`file-consolidation-04/commands/apply-consolidation-v1.py` SHA `03893b27959601331a50f8fcce46bbb84330d10bdc3e7a8f16c3bc66ab601903`，输入补丁`file-consolidation-04/consolidation-v2-vs-installed.patch` SHA `275a789874858f07e4b5a81693b957c5b25405bb23d18bcc4bdc720393c0ab51`。执行前核对原46项的完整SHA/index和唯一安装目录，备份精确7路径与index，定向暂存；预期42项。失败且无并行编辑时精确回退。直接在安装目录跑CPU、真实provider解析和注册检查；只读核对服务身份/health。服务不重启/热重载，不发模型请求，不改其他库/脚本，不提交推送。graph/模型精度/性能本轮不测，不能自动沿用旧gate。

## 用户要求直接修改已安装源码（runtime-contract-apply-03，已完成13:41）

本次已经直接修改容器实际editable安装目录，不再只是审查副本：`/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4`。改动精确为`vllm_fl/__init__.py`、`vllm_fl/models/glm5/provider.py`修改，`vllm_fl/dispatch/backends/vendor/thead/bootstrap.py`删除，`tests/unit_tests/glm5/test_registration_cache_contract.py`新增。真实import/direct_url唯一性核验通过，在该实际目录且不设置PYTHONPATH的95项CPU和新进程provider注册检查通过。

当前原分支`glm53-multiplatform-worker-fix-p45`，HEAD仍为PR454 `f769696`；VS Code“暂存的更改”共**46项**、零unstaged/untracked，index tree `d2f7f39036dc5b79968caaf8c7f33f9f30c8f525`。原有其他改动保留，未commit/push。新磁盘Plugin内容SHA `4165a889f91374010f5f6069df8da32296043cebcffed6702f0a89dd43b5df7e`；旧a07快照分支仍保留，但不再等于当前磁盘源码。

原三个受影响文件的恢复归档`runtime-contract-apply-03/affected-files-before.tar.gz` SHA `011d532de160b8f82d54f0634d246cea9ebdee970a99b445eb34c1b9192bc966`，原index另存`index-before.bin`，因此已删除bootstrap可恢复；未触发回退。回执`runtime-contract-apply-03/completion.json`，原始验证为`installed-cpu.xml/log`及`installed-import-registration.log`，实际导入仍指向上述目录，非临时副本。

服务8011 health200，PID/start_ticks、argv/环境、权重/tokenizer/DB、vLLM/FlagGems/FlagGems-vllm不变。未重装包、未重启/停止/热重载模型或发模型请求。**本次是磁盘代码及新进程导入生效；现有worker加载新逻辑尚未证明，不能把旧graph/精度回执绑定新源码。**后续重新启动/回归前不宣称新运行时模型验收通过。

用户明确纠正上一轮仅修改审查副本，要求直接修改容器实际安装的Plugin。该指令覆盖此前本轮自设“未安装副本”边界。本次精确目标为`PPU-13 / glm5.3-flash-opt-20260911`的`/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4`，不再另建源码安装。先核对旧SCM/index/完整源文件与原回执、唯一editable direct_url及真实import，备份受影响旧文件和index，再应用已审查四文件补丁，定向暂存这些路径；预期相对PR454共46项，保留其他原始45项中仍有效的改动，不提交推送。

预保存命令`runtime-contract-apply-03/commands/apply-installed-v1.py` SHA `9c60b76f2824ec8d3e811d6f980a32b67d6ffcb0d30c7693b8fc586ed58e9491`；输入`runtime-contract-review-02/final-v3/runtime-contract-review-ready.patch` SHA `ca094df796b68ab65e2d406452b1fd4fc41b59873d083d05ce0071e78ff991cd`。实际目录直接跑95项CPU和新进程import/注册检查，失败仅在无并行用户编辑时恢复精确文件/index，不碰其他dirty内容。删除bootstrap有备份可恢复。

不停止、重启、热重载服务或发送模型请求。editable源码修改不需重装，但现有worker已导入的模块不保证自动加载新逻辑；本次只证明磁盘源码/新进程导入更新，旧模型graph/精度不能绑定到这份新磁盘身份。执行结果如本节开头，以下原审查阶段状态按时间保留，不覆盖本次已应用事实。

最新审查进展（2026-10-20 13:28）：用户进一步要求收敛通用入口的T-Head特判。新候选恢复唯一模型注册入口，按现有provider声明的缓存协议而非厂商选择；删除无调用方的新增bootstrap，保留真实vendor kernel边界。95项CPU与真实provider元数据/重复注册检查通过，**候选未安装，当前运行版及VS Code原45项更改不变**。它不是完整模型/graph/精度或端到端通过，仍保留两种不同缓存ABI的host实现；详见下方runtime-contract-review-02。

当前状态：2026-10-20 11:11，**修复版已安装，13个旧私有源码副本已删除，最终独立审计通过**。用户后续明确授权安装与去重，覆盖此前“先审查、不切服务”的限制。容器`glm5.3-flash-opt-20260911`内仅保留Plugin v4和FlagGems-vllm v3各一份，均为editable安装；8011服务健康，启动参数及交付脚本不变。源适配容器、共享源码、vLLM、FlagGems、权重/tokenizer与模型DB未改。安装后又按用户要求将Plugin现有改动提交为本地`a07f384`并保留PR454/冻结主线基线分支，源码字节和服务实例未变；未推送、未运行新全量GPQA或性能测量，历史分数不绑定新身份。

## 当前安装结果与验证边界

| 组件 | 唯一安装源码目录 | 基础revision / 当前运行源码SHA256 |
| --- | --- | --- |
| Plugin | `/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4` | PR454 `f7696963c44425fdf6603054248cc8256783b4c7`；`57a29e41e87586f46fe1b8f1d0b53f0f39971dfdca82b91b5e0fec1dbe410a2e` |
| FlagGems-vllm | `/workspace/e2e-opt/glm53-20260911/FlagGems-vllm-review-20261020-p45-v3` | 官方main `b4d3382bb04da4e0ab444849697865b4d5fcd86e`；`09fba322064d203ef48b580145c7d26473a7a3ba32d3ce21dabdc59ffcbe95ec` |

Plugin安装元数据版本`0.3.0rc2.post1+gf7696963c.d20261020`，FlagGems-vllm版本`0.3.0.dev1`；后续仅调整Git元数据、未重装，不把安装时版本字符串当成完整源码身份。安装元数据、editable direct_url、实际import路径及`/workspace`、`/opt`源码清单均独立核验，每库仅一份安装/展开源码。Plugin完整安装快照保存在`a07f384f62f6146195d9038ed7050bbb3e4c8c8e`，按用户VS Code要求，当前HEAD回到纯PR454 `f769696`，index/磁盘仍完整保留修复版，额外45项显示为暂存更改；库改动仍未commit。这不是纯净PR454运行或所有平台硬件验收。

验证：Plugin **70 CPU通过**、库 **46 CPU通过**；PPU clamp/align及fallback共**10组**设备回归，**9组graph各replay两次（18次）**；模型`FULL_DECODE_ONLY` **11/11 capture size**、固定C1/C8多token、16383/16384/16385输入边界与11项明确答案通过。边界输出与旧点44一致。没有逐rank设备trace，不将dispatch准备日志冒充每个kernel/rank命中，也不以最小回归替代新全量精度gate或端到端收益。

当前服务实例`PPU-13:glm5.3-flash-opt-20260911:2890600:517802756`，10:19:19 ready，10:22:34模型回归通过，10:22:38完成删除。仍沿用TP16/BF16、MBT32768/maxseq64、关闭前缀缓存及原启动脚本`/mnt/nfs/users/jinghao/glm5.3-flash/start-model-opt.sh`，无PYTHONPATH覆盖。模型级父/worker初始化修复已在同范围模型graph回归验证，首轮编译故障根因闭环；没有恢复通用注册整表平台切换或新增generic `thead_*`文件。

持久证据根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261020-point45-multiplatform/install-cleanup-02`。

- `completion.json` SHA `dede351041b2389d55380665fae84f52bf09a4f1b9c965884a5f58ec624ad02d`；`independent-final-audit.json` SHA `51e0696d67a98aca28ba5452410cc75b6643132b1e8e5a54610b233db239203b`。
- 删除前归档`deleted-source-copies.tar.gz`，648945117字节、12279文件逐项核验，SHA `f0f25319eb0e09c6656a61ca98f86b8b5d2dba59dd51091347f1a175a5a57737`。仅删除冻结清单内13个私有旧目录，可从该归档恢复；归档不是另一个安装版本。点43/44旧目录不能再直接切换，须先恢复对应目录。FlagGems不在删除范围。
- 当前[Plugin完整补丁](/tmp/glm-p45-Vdmo38/installed-plugin-vs-pr454.patch)为45文件，SHA `a1fe90a4d7349e07d4840e7c701113320e8eaa733fabce15efdb2a6b894a28c2`；[相对审查v3的worker修复](/tmp/glm-p45-Vdmo38/installed-worker-fix-vs-v3.patch)恰为2运行文件+1测试，SHA `4d4b720d6a6963f21396e6bdff7cedce5ee20d1f60aa716a0fb3d8e3cfea93e3`。
- [FlagGems-vllm完整补丁](/tmp/glm-p45-Vdmo38/flaggems-vllm-vs-official-main.patch)仍为26文件，SHA `4ea7df7433a950564f3455ae5f65b559df0a055fa1ac49b5461f092d8b5061da`。完整补丁持久副本位于上述根`review/`，原始index的apply-check通过；不是本次新增45/26文件。

`pr_readiness=needs_user_architecture_review_and_cross_platform_hardware_validation`。本次仅完成安装、清理与目标PPU最小回归，不自动继续正式精度/性能实验。以下审查与首轮失败记录按时间保留，不能覆盖上述当前状态。

## VS Code 原生源代码管理可视化（已完成，11:18）

### 后续通用入口厂商分叉收敛（runtime-contract-review-02，审查候选已就绪、未安装）

用户指出`register_model()`仍按`vendor_name == "thead"`切换整套模型注册。该判断不应停留在通用入口，也不能机械移动到另一个helper或按BF16权重dtype代替厂商：PR454自身使用BF16权重，但其indexer缓存协议仍是另一ABI。当前只在本地未安装副本`/tmp/glm-p45-contract-okK4Iv/plugin`整理，不改已安装目录、45项SCM展示、服务或FlagGems-vllm。

设计：通用入口恢复为唯一的GLM注册函数；模型边界复用现有`OpManager`与`sparse_indexer_capabilities`的纯元数据返回值选择缓存运行时。只有实际provider声明的BF16 query/cache、32-entry compressed page协议才选择既有BF16适配；无该能力项保持PR454路径。任何厂商只要提供同契约均可选择，PPU也不因身份强制选择；显式策略禁止/能力错误必须传播，不用宽泛捕获静默换ABI。FlagGems缺失保持原可选依赖语义。真实SDK加载与vendor kernel保留vendor边界，既有上游其他平台分支不无故改动。

否证测试：厂商标签与能力交叉组合、能力缺失/混合或不支持布局、显式策略拒绝、可选库缺失、重复注册与此前70项CPU契约。只证明静态/CPU路由，不宣称跨平台硬件/graph/完整精度或端到端收益；本轮不自动安装。

候选仅改`vllm_fl/__init__.py`和现有`models/glm5/provider.py`，新增一个契约测试，无新平台文件或配置开关；两个运行时保持lazy import，BF16分支不提前导入公共FP8模型编译依赖。先记录测试命令`runtime-contract-review-02/commands/review-test-v1.py` SHA `6af4378d02af23983009a04608c2ec59382fc90c90cb2dc393a816b863151184`和源码输入`candidate-v2.tar.gz` SHA `8fd732e7c87cb7024f925a1546f6aeff6ef11f97c26aa0faf856e841dd1f925e`。容器内只在临时目录解包，子进程临时PYTHONPATH做CPU及真实provider元数据/注册smoke，不构造模型、不安装；结束移除该临时源码，保留日志/回执与归档，原安装/SCM/服务须完全不变。

初版91/91 CPU通过（无fail/skip），真实provider返回BF16 query/cache与page32，连续注册两次成功且共享mHC类不变；未构造模型，临时源码已清理，服务/SCM/源码与之前相同，health200。回执SHA `f99239e348b04bb2a5420b7683f251ec15d9a8df14ac1277ecc7082f09258cd7`。随后静态审计确认新增`vendor/thead/bootstrap.py`在全库没有调用方或动态加载引用，最终候选删除该死代码，仍保留实际native loader与平台backend检测。最终差异恰为两运行文件修改、一个死文件删除、一个测试新增，无其他库改动。

最终重新验证先保存`runtime-contract-review-02/final-v2/commands/review-final-v2.py`，SHA `d51bfcea7c86365bbd57d1f3350ffe96198454602e52c810e27d1794ca2592e1`；最终源码包SHA `98bf892c649fedb004f89dc6c2e11386e807252be209e8ab57796f1c43bdab3b`，相对已安装快照的[四文件补丁](/tmp/glm-p45-contract-okK4Iv/runtime-contract-final-vs-installed.patch) SHA `99d410038535a559bd7decfc79b66a347a9e1546837a024c6b39479c9afad1e1`，apply-check通过。最终结果待回执，不将初版测试自动套到删除后的源码。

上述final-v2仅完成准备、未执行测试即被final-v3替代：再加未知dtype协议拒绝与packed FP8兼容测试，不让合法dtype但不支持的FP32等协议静默进入公共FP8运行时。新命令`runtime-contract-review-02/final-v3/commands/review-final-v3.py` SHA `b8eb22a14e78ad32e75e911ebedc7d545c342f965ceaa219fe4e9e5a0623beab`；源码包SHA `cea3657dd1899d758b158c0644c174057d826ffa9b15e320ff65ec6f91f3c4aa`；[当前最终四文件补丁](/tmp/glm-p45-contract-okK4Iv/runtime-contract-final-v3-vs-installed.patch) SHA `78043457f17bffcf56a828504ae4749f74f40e1d99fbaea041789aac5a73e664`。原准备证据保留，不盲重跑或改原回执。

最终验证95/95通过（无fail/skip）；包含此前70项和新增25项。真实PPU provider元数据为BF16 query/cache与page32，连续两次注册到`vllm_fl.models.glm5next`成功，共享mHC类未变；没有构造模型。临时源码已清理，实际安装、SCM45、服务实例/源码/配置/权重等仍与原回执相等，health200。`final-v3/completion.json` SHA `ac9cd6daf99aead361ef8a840905e663fa5e66471dbf646879963e21d382c03d`，详见`cpu-tests.xml`及`registration-smoke.log`。

随后仅更正provider docstring，明确dispatch既有availability仍可能做设备可用性探测，元数据操作不运行数值kernel。用去除docstring后的AST证明与95项验证版本完全一致，不声称重新执行了测试。供审查的[最新四文件补丁](/tmp/glm-p45-contract-okK4Iv/runtime-contract-review-ready.patch) SHA `ca094df796b68ab65e2d406452b1fd4fc41b59873d083d05ce0071e78ff991cd`；持久副本`runtime-contract-review-02/final-v3/runtime-contract-review-ready.patch`，配套`candidate-review-ready.tar.gz` SHA `dcba329cdb6fe50f517d73d5a9928248ddad571dff29f3c5dc97e5eaa195546b`。apply-check对原安装快照通过。

边界与下一验证：本轮消除的是新增通用入口厂商分叉和无调用方平台死代码，不宣称已合并两套不同缓存ABI的host实现。模型注册现在会较早初始化现有OpManager；其他平台真实启动/可选库组合仍待CI或对应平台runner验证。真正硬件可用性和native kernel加载仍保留在vendor边界，不删除上游原有平台检测。未执行当前候选的模型最小回归/graph/full GPQA/性能测试；未安装、提交或推送，不能将历史95项CPU、旧171/198或旧性能收益冒充新候选模型验收。

最终核验：当前分支`glm53-multiplatform-worker-fix-p45`，HEAD为`f769696`；快照`snapshot/glm53-installed-p45-a07f384`仍指向`a07f384`。VS Code原生**“暂存的更改”共45个文件**，零unstaged/零untracked，index tree `8938696d0bbf09f1ea0c8eefaddffc31f9b35f5d`与完整快照一致。源码逐文件SHA、服务进程/参数/环境、组件/权重/tokenizer/DB/thead指纹未变，health200。回执`vscode-scm-01/completion.json`及`runtime-after-scm.json`保留；没有模型请求、重装、重启或推送。

在VS Code通过Dev Containers附加到`glm5.3-flash-opt-20260911`，打开`/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4`；左侧“源代码管理”→“暂存的更改”，点文件即可看PR454原版与当前安装代码的可视化差异，不需要运行git diff。必须打开容器内该目录，而不是宿主挂载的历史产物或其他源码副本。只读审查时不要丢弃/清理这些更改，它们是服务实际editable源码。

用户不希望运行`git diff`，要求直接在VS Code源代码管理查看。准备在同一安装仓库保留快照分支`snapshot/glm53-installed-p45-a07f384`指向完整安装提交`a07f384`，再仅对当前分支执行`git reset --soft f769696`。它不修改index或工作文件；当前HEAD为纯PR454，index/磁盘仍是已验证安装版本，额外45项在VS Code原生“暂存的更改”中可点击逐文件对比。不会丢掉安装提交、不checkout、不重装、不重启或推送，也不新增源码副本。不要用discard/reset hard清除这些改动，否则会改动实际editable源码。

命令先保存为`vscode-scm-01/commands/vscode-scm-v1.py`，SHA `d4860a7ad5eaaf10076b9998da55a81b3b82066017fd949e9cf73724a7c5d91f`。前置要求现有HEAD/clean/index/source/服务与上一回执一致；执行后快照ref、index tree等于安装提交、45项staged/零unstaged和完整文件SHA、服务进程及配置/其他组件不变的断言均通过。

## 后续Git可比较分支整理（11:11历史快照）

以下为11:11已提交时的历史分支关系；后续当前分支HEAD已按上述VS Code要求软移动到基线，安装快照改由`snapshot/glm53-installed-p45-a07f384`保护：

| 分支 | 提交 | 用途 |
| --- | --- | --- |
| `baseline/upstream-main-20261019` | `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` | 迁移时使用的冻结官方主线，不宣称当前远端最新main |
| `baseline/pr454-f769696` | `f7696963c44425fdf6603054248cc8256783b4c7` | 当时使用的纯PR454基点，已包含上述主线 |
| `glm53-multiplatform-worker-fix-p45`（当前） | `a07f384f62f6146195d9038ed7050bbb3e4c8c8e` | 已安装源码的完整快照，父提交正是PR454基点 |

相对PR454共45文件、7727行新增/42行删除，包含累计BF16兼容、算子接入/优化、多平台边界及测试，不能称为本次新写45文件或全部为性能优化。工作区干净、提交blob和安装文件逐项一致，运行源码SHA仍为`57a29e41…`；进程/argv/环境、所有组件内容指纹、权重/tokenizer/DB/thead均未变，health200。只创建本地commit/refs；未checkout、重装、重启、发模型请求或推送。原最小回归结论不新增/改写成全量精度gate。

在容器内执行以下命令查看我在PR454之上的全部修改（不必切分支）：

```bash
cd /workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4
git diff --stat baseline/pr454-f769696..glm53-multiplatform-worker-fix-p45
git diff baseline/pr454-f769696..glm53-multiplatform-worker-fix-p45
git log --oneline baseline/pr454-f769696..glm53-multiplatform-worker-fix-p45
```

若要单看PR454相对当时官方main的内容，执行`git diff baseline/upstream-main-20261019..baseline/pr454-f769696`。持久回执`git-review-01/completion.json`及`runtime-after-git.json`记录最终核验；以下执行准备/工具失败按原样保留。

用户另行要求将已安装Plugin与使用的PR454保留成可比较分支，授权本地Git提交/分支整理，不含推送。已只读核对实际目录HEAD恰为`f769696`、当前分支`glm53-multiplatform-worker-fix-p45`，45项已安装源码/测试改动未提交、index空，无用户后续改动。计划保留`baseline/pr454-f769696`及冻结主线`baseline/upstream-main-20261019`，将当前精确45项改动提交到现有工作分支；不checkout、不改源码、不安装、不发模型请求、不重启服务。仓库缺少作者配置，单次提交使用Codex身份，不修改全局配置。

执行前保存命令`git-review-01/commands/git-review-v1.py`，SHA `5511938f4a9f3bc067c5fa2753137777165a9c521a2d483212e9718fd72ac890`。执行前后核验全部源码字节和运行身份/health，保留原index/refs与可校验Git bundle；实际结果待执行后填写，不用远端PR当前最新内容冒充当时使用的冻结版本。

v1已建立两个基线并暂存精确45项，在提交前cached whitespace检查停止：`bf16.py:116`和`impl/bf16_fused_moe.py:62`是原有文件末尾空行，尚无新commit。保留原始检查失败与index；恢复命令`git-review-01/commands/git-review-recover-v2.py` SHA `5be14ae2dcc625a8293c595de8e13a7f50d4c28b027f573e3a976ccb05d90692`只复用已核验refs/index，严格断言仅这两处格式提示，保留已安装源码原样提交，不掩盖其他检查错误。

v2在变更前因`runtime.sources`包含Git暂存状态而停止，源码SHA/进程/配置未变，未重复执行Git操作。保存v3元数据适配命令`git-review-01/commands/git-review-recover-v3.py` SHA `c35ff39be5bbe915ff640dacbd5e2a6720012c7f0fa6ff29830a0bf7a2ca5e28`：只允许用户要求改变的Plugin revision/status变化，其他运行字段、源码字节/SHA、root/import及其他组件仍须完全相等。旧命令/失败检查保留，不修改原始结果。

v3已创建commit `a07f384f62f6146195d9038ed7050bbb3e4c8c8e`，两个基线存在、工作区干净且源码/commit blob逐项相同；之后可选bundle归档失败，保留`git-operation-v2.log`，不重复commit。最终只读命令`git-review-01/commands/git-review-finalize-v4.py` SHA `8a450f8ac6e607d42563fec2722e1c2bf728f74c5d773d25d062a1b6cdff2af4`复核已有提交/refs/源码和服务后记录回执，不再执行Git写入。bundle不作为用户所需分支比较的前提，原补丁、index/refs证据仍保留。

## 审查阶段入口与结果（09:33历史快照）

建议先看本轮相对运行版本的 [Plugin 整理差异](/tmp/glm-p45-Vdmo38/plugin-vs-point44.patch) 与 [FlagGems-vllm 整理差异](/tmp/glm-p45-Vdmo38/flaggems-vllm-vs-point44.patch)。完整改动另外提供 [Plugin 相对 PR454](/tmp/glm-p45-Vdmo38/plugin-vs-pr454.patch)、[FlagGems-vllm 相对冻结官方 main](/tmp/glm-p45-Vdmo38/flaggems-vllm-vs-official-main.patch)，包含所有新增文件，不遗漏 untracked 源码。以上是本机临时审查副本，远端持久路径在文末。

| 设计问题 | 本轮修订 | 建议查看 |
| --- | --- | --- |
| 根据 vendor 选择另一整张通用注册表 | 所有平台先注册上游公共实现；BF16 ABI/能力使用独立 ID，不覆盖原有 ID | [公共注册](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/dispatch/backends/flaggems/register_ops.py)、[BF16 能力注册](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/dispatch/backends/flaggems/bf16_register_ops.py) |
| 相同算子名实际调用签名不同，fallback 有错配风险 | packed clamp、BF16 indexer top-k 使用 `bf16_silu_and_mul_with_clamp`、`bf16_indexer_topk_prefill/decode`；保留 PR454 的公共键与默认实现 | [原 BF16 模型调用点](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/models/glm5next.py:131)、[显式策略](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/dispatch/config/thead.yaml:30) |
| 通用 adapter/reference 被命名为 thead；重复公共实现 | generic backend 下不再有 `thead_*.py`；MLA/indexer/mHC/top-k/reference 按能力命名，删除重复 rotary、activation/MoE 通用方法，公共 MoE activation 恢复原路径 | [BF16 小适配层](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/dispatch/backends/flaggems/bf16.py)、[公共 MoE activation](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/ops/fused_moe/activation.py) |
| Plugin 散落平台 shape 判断和另一套 MoE activation | 小 M padded-stage2 策略及 BF16 clamp provider 收敛到库的 `_thead` backend；Plugin 调用公共 API。新增 `moe_align_block_size_bf16` 表达完整 host ABI，不覆盖原 public align | [align vendor 策略](/tmp/glm-p45-Vdmo38/gems/src/flaggems_vllm/runtime/backend/_thead/ops/moe_align_block_size.py)、[clamp provider](/tmp/glm-p45-Vdmo38/gems/src/flaggems_vllm/runtime/backend/_thead/ops/bounded_activation.py) |
| 全平台/全模型受到 PPU 兼容 hook 影响 | generic KDA 元数据仅由 BF16 模型验证器安装，builder 按模型 marker 旁路非目标；Worker 不再跳过所有 PPU 模型，保留非 GLM 的 empty-plan 生命周期保护 | [元数据 hook](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/patches/kda_prefill_metadata.py)、[Worker](/tmp/glm-p45-Vdmo38/plugin/vllm_fl/worker/worker.py:256) |

最终 CPU/mock：Plugin **67 passed**，FlagGems-vllm **46 passed**，合计 **113 passed**。覆盖 NVIDIA/PPU/MetaX/CPU 平台标识模拟、上游注册项未覆盖、独立 ABI 键、可选库缺失、懒解析、重复 ID 拒绝、显式配置 token、模型 hook 作用域、参考数值、旧优化的 shape/config 契约及 FakeTensor 注册。平台标识 mock 不是上述平台硬件验收；storage alias 检查在 custom-op 内，不把 Python storage 查询放进 Dynamo 追踪路径，但真实 graph capture/replay 仍未执行。

两份完整 patch 均以原始 index 执行 `git apply --check --cached` 通过，index SHA 前后未变；源码 AST / diff-check 通过。完整 Plugin patch 相对 PR454 为 44 文件，库相对官方 main 为 26 文件，包含此前必要适配/优化，**不是本轮新增这么多文件**。本轮相对点44 Plugin净减345行、库净增275行（含迁移、桥接和测试），不以行数作为设计正确或性能收益证明。

## 仍须用户重点审查的保留边界

1. 原 `models/glm5next.py`、配置/processor、KPool/混合缓存/graph 兼容仍保留：当前 native BF16 host/cache ABI 与 PR454 的公共 FP8 runtime 不等价。本轮没有通过重命名就声称这套模型已跨平台适配；`register_model()` 的 native 模型选择边界仍可见，不能把它和通用算子的多平台接入混为一谈。
2. 真正 PPU SDK/native 实现仍在 `dispatch/backends/vendor/thead/`，库平台特化仍在 `runtime/backend/_thead/`；本轮没有要求删除合理的 vendor 边界。其他平台策略文件未改。
3. Plugin 的新 BF16 align/clamp 适配依赖配套 FlagGems-vllm 公共导出；不能只应用一个仓库的补丁就测试。审查阶段两候选尚未安装，后续安装结果见文首。
4. 审查阶段`pr_readiness=needs_user_architecture_review_and_hardware_regression`，当时没有模型/设备回归。后续获授权完成目标PPU最小回归，但无新全量GPQA或端到端测量；历史171/198不绑定点45，其他平台硬件仍未测。

## 审查阶段只读运行核验（历史）

09:33 的 `final-review.json` 和 `runtime-final-readonly.json` 核对服务仍是 `PPU-13:glm5.3-flash-opt-20260911:2865123:512203485`；argv、环境、实际四组件源码、权重/tokenizer、DB、thead 配置与点44相同，health200/空闲。原安装目录和启动脚本未动。审查候选位于容器私有 `*-review-20261020-p45-v3`，两仓库分支名 `review-glm53-multiplatform-p45`；仅本地未提交改动，无 commit/push。

## 依据与复盘

点44的75 CPU、41选路、graph/C1/C8/16K回归均是原身份的有效运行证据，但不能证明工程设计合理。当前源码将FlagGems/PyTorch通用适配器命名成`thead_*`，公共注册器按vendor切换旧表，共享Worker/activation存在过宽PPU分支。应修订设计，不能只减少行数或机械改名。

调用`inference-optimization-planning`：本轮优先修复通用注册与平台边界，不叠加性能优化。历史Prefill/Decode/Mixed证据和精度口径不变，无新性能或精度结论。

## 设计归属与范围

1. 公共backend恢复上游默认注册；新增BF16/旧调用约定的能力作为显式impl注册，不按平台整体替换。存在不同签名时使用独立impl ID和策略，不用同名同ID悄悄替换。
2. 不依赖PPU SDK的MLA Prefill、BF16 indexer、MHC、top-k、bounded activation和reference代码使用语义名称，所有支持其依赖/输入契约的平台都可显式选择。
3. 真正PPU native实现保留在`vendor/thead`；算子平台特化由FlagGems-vllm对应vendor backend提供，Plugin使用公共API，不把调优平台判断散落在通用接入中。
4. KDA元数据按模型/能力作用域安装并保护非目标实例；Worker兼容例外限制到实际BF16模型运行时，不能跳过所有PPU模型。

不修改vLLM/FlagGems/权重/tokenizer/原交付脚本，不升级官方冻结版本。不通过另加临时平台开关回避设计。PPU特有的已验证BF16 native模型路径目前仍有真实ABI依赖，必须明确其边界，不能靠去掉文件前缀就宣称新公共GLM模型已适配。

## 审查阶段先验测试与停止条件（历史合同）

静态审计确认generic目录没有新增`thead_*`平行实现；公共注册表无vendor整表切换。CPU/mock验证NVIDIA/PPU/非CUDA/无可选库的导入、上游默认impl保持、显式BF16策略、重复注册保护、签名契约和懒解析。没有GPU模型请求，本轮不得写graph/精度/性能passed；后续若用户授权硬件验证，调用本地`e2e/accuracy minimal-regression`并按风险决定完整精度。

任何非目标默认实现改变、没有必要的vendor强依赖或隐式fallback改变，均阻止补丁进入可审查状态；修复或回到本轮独立副本，不影响运行服务。

## 审查阶段效果、决定与回退（历史）

审查阶段：性能not_run、模型最小回归not_run；当时服务仍为点44，决定停在审查、不自动安装。用户后续安装授权及当前结果见文首；原分数仍不绑定本候选，旧展开副本现已归档删除。

## 用户后续授权安装与去重（install-cleanup-01）

用户在审查阶段结束后明确要求“将最新修复版本安装到容器，只保留一份 Plugin 和 FlagGems-vllm，其他删除”。此前“不切换”约束的事实保留；本阶段授权覆盖精确优化容器的两包安装、关联服务重启与必要最小回归，以及已核验私有重复源码的清理，不扩大到其他容器/共享目录或 FlagGems/vLLM。沿用本实验 ID，不作为新性能优化或新全量精度通过。

先执行只读冻结命令 `install-cleanup-01/commands/deploy-preflight-v1.py`，保存实际导入、唯一服务身份、候选内容指纹、所有可删除的私有源码精确清单及挂载检查；变更前保存回退归档到用户工作目录，校验归档与原文件。候选验证通过后才删除精确清单；失败先恢复旧安装和原服务，不能先删除唯一回退副本。验证模式为本地精度 Skill `minimal-regression`，正式 GPQA/端到端性能不在本次安装清理中自动启动。

只读冻结命令 SHA256 `21d06e6f2f894f4a62b2999f8cddf628fad136846c6eb0b768b02a2a6a746896`。仅为本阶段创建 `install-cleanup-01/commands/`（Ansible file `--check --diff` 后创建），不创建另一个模型容器或改挂载。

只读预检通过：当前点44服务健康/空闲，最新两仓库源文件与审查 manifest 完全一致。`/workspace`、`/opt` 有限层次检查共14个两库源码副本，其中保留最新各一份；其余12份精确路径在 `preflight.json`，全部非符号链接、非挂载/共享内容，没有其他进程从这些目录运行。本轮不清理 FlagGems、vLLM、权重或 `/mnt` 内的历史证据。

部署命令 `commands/deploy-v1.py` SHA `cfff186c9bf9c491e9cace559918bfc89117863ce65bd424e31dea0ee787603f`；设备最小回归命令 `commands/device-regression-v1.py` SHA `6a3aac244f54cbe0265d715ec712b716aff424b05dd11545386bdb7d474c1da6`。唯一派发后按阶段停精确服务→归档校验→两包editable安装→变更clamp/align设备等价与graph两回放→原参数模型capture/C1/C8/16K及11答案回归→精确旧副本删除。设备短测使用独立tuning DB，服务继续沿用原DB和全部启动参数。删除前再次核验归档SHA/逐文件内容与权限/符号链接、当前源码与服务身份；归档置宿主任务目录，不作为第二个安装版本。

候选安装或回归失败时保留全部旧副本并恢复原安装/服务；只有清理工具失败时不停止已经通过回归的新版服务。完成前不称安装/清理成功。

### 首次安装失败与 worker 初始化修复

`install-cleanup-01` 两包安装、10组clamp/align设备等价通过，其中9组graph各两回放通过，但模型服务编译失败，尚未进入请求级最小回归；没有删除旧源码。原始 `installed/service.log`、`deployment-failure.json` 保留。首错在真实TP worker中命中 `flag_gems.fused.mhc.mhc_post.logger.debug`，Dynamo报 `logging.Logger method not supported for non-export cases`。这不是正式GPQA分数失败，也不是算子数值不一致。

调用`inference-accuracy-diagnosis`，issue=`point45-worker-local-setup-01`：点45把兼容设置从通用注册移到模型配置校验后，配置校验进程的Dynamo logger集合和metadata类patch不随spawn自动生效；原模型构造入口未再次设置。机制暂列suspected，待独立新进程最小复现和修复后同范围模型graph/C1/C8/边界回归闭环，不继续叠加性能优化。控制器09:55已重新安装点44并开始恢复服务，完成恢复前不执行第二次切换。

修复限制为Plugin同一BF16模型边界：共用`configure_bf16_runtime`从配置校验与每个worker的模型构造各调用一次，初始化过程幂等；不恢复按PPU整表切换、不改vLLM/FlagGems/数值kernel或启动参数。独立未安装Plugin v4只改两个运行文件并增加一个新进程回归文件，FG-vllm v3不改。准备命令/源码SHA先记录再执行，CPU复现不发模型请求。第二次安装与清理使用新的远端`install-cleanup-02`，保留首轮失败/回退证据。

`install-cleanup-02/commands/prepare-worker-fix-v1.py` SHA `bd8cf972b443242001c80bb6711ff22b604e85c2ad7a0f704e5ba41c5f52c34c`；完整Plugin输入 `plugin-worker-fix-v4.tar.gz` SHA `b8d11b1e1b9a14ad91ee28cc651b2d4fd1cd7fee78f581416bb9fd72d80bdea1`。新增目录前用Ansible file check/diff，只操作同一Host/容器私有副本，不在恢复中的旧安装上修改代码。

首轮已于09:59恢复点44，实例`PPU-13:glm5.3-flash-opt-20260911:2882053:517713113`，原参数、capture/回放、C1/C8、16K三边界与11答案全部通过，原副本未删除。新Plugin v4的70项CPU测试通过，新增全新进程用例稳定区分“未设置logger-ignore时同类Dynamo失败／模型级初始化后通过”；两个运行文件以外没有行为改动。根因机制已有最小复现，但实际固定版模型graph验证仍待第二轮，不能提前宣称闭环。

第二轮只读冻结 `commands/deploy-preflight-v2.py` SHA `2950988d1329d89a59994ee524ff831d54bfb3edfb07524e3b21b3b766ba9083`，先要求旧控制器结束、恢复回执与当前身份一致、源码CPU结果有效。第二轮控制器 `commands/deploy-v2.py` SHA `0ca73a23a1f8849c10f4a2e4f950d56ffee49b4a10e1024e904331bd4f8c7cb1`，设备命令 `commands/device-regression-v2.py` SHA `255bdba4c0e2ef81367626ff509ed722e0cf8e725d0ed42fd08b69f50eb5c89c`。沿用同一设备/模型回归合同；由于失败的Plugin v3也应删除，预期旧副本从12变13。对恢复重装后的实际文件重新归档校验，不拿首轮旧manifest掩盖metadata变化。

第二轮闭环后的独立审计命令 `commands/final-install-audit-v1.py` SHA `9870fc85fbc01804b0ea6c3a6567a6ecb3ac0b42d2371ecd482ade0fb979ea8a`，执行前先要求安装与清理完成回执passed；只读核验服务、安装包唯一性、源文件与冻结修复manifest、镜像/挂载、保留目录和已删除目录，重新导出包含全部新增文件的当前两仓库完整补丁以及相对审查v3的三文件修复diff，不触发模型请求。没有完整精度/性能或提交推送行为。

待执行准备命令：`commands/prepare-v1.py`，SHA256 `fee22a9e73fceceab8e975e97a43fe0c64b83285510d6111ec767b19d4b3d5b6`。只在新私有目录 clone/解包，子进程临时 PYTHONPATH 做 CPU/mock 测试；不安装包、不发模型请求。输入 `plugin-review-v1.tar.gz` SHA `44158887ec76af34e6cd4fae8799b830bad16e00b5833442216baa1e02cd36c1`、`gems-review-v1.tar.gz` SHA `2a5976c6ba94c7edde2ed4fbd8b43ab4ff31c1c9caf0540528670c7573612273`。执行前后只读核对点44实例、argv/环境/源码及权重等身份。

v1 已执行：Plugin 66 passed；FlagGems-vllm 44 passed/1 failed，原因是导入 child module 自动挂到父包，测试将非 callable module 属性误判为算子函数覆盖。原始日志与失败 completion 保留，不改写。v2 修复该断言并检查原 public align 函数来源，同时补齐 vendor clamp-out 的 Tensor 返回值、非 GLM empty-plan 生命周期保护和 common reference align 回退策略。

v2 待执行命令 `commands/prepare-v2.py` SHA `71f49ee3e0514693f803387ff8f6e7c283be6f28468c256da3f190afc704275c`；新私有副本后缀 `-review-20261020-p45-v2`，输出 `revision-v2/`。输入 Plugin SHA `6d208451ee10790b82227dc1cf34562ae87d3b72675f4b93a82f7c84fb3750fe`、FlagGems-vllm SHA `3d96e6647e2c0a5b0e8552cd1fb1d4bf531cedfe7c2cc756a68bdbd39afae396`。不在旧目录修补或覆盖结果。

v2 已通过 CPU 契约。v3 为最终审查副本：补齐所有 YAML 显式 impl token 的存在性测试、mutable clamp 的 FakeTensor 注册契约，将 storage alias 检查留在 custom-op 内而非 Dynamo 可见的 Python 路径；不增加数值 kernel。去除无用注册参数和模型类中的冗余平台限定。命令 `commands/prepare-v3.py` SHA `d7c9d98e23f065935e3fa98afae2bf8a0d3de00495970050bf010c0931662f54`，输出 `revision-v3/`；Plugin 输入 SHA `84e9d20874a74d825d309379c2469d5b4fb255fe5243658c8d9d43ba0ac573bc`、FlagGems-vllm 输入 SHA `b25b8c08fde92021bdfb530c286f8059e9b281f10836a9d56f084b97fa6ee5b1`。v1/v2 证据保留，三个副本均未安装。

最终导出命令（待 CPU 通过才执行）：`commands/export-review-v1.py` SHA `f376db69092b2473adac370e2e6e45f0cbd59b4de424e547f124e413fe528a03`。生成包含所有新增文件的完整 patch、相对点44的整理 patch、逐文件理由与 SHA 清单；用 `git apply --check --cached` 只读校验原始 index，前后核验 index SHA 未变。导出前后只读检查当前服务与源码身份，不包含模型请求、安装或服务变更。

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261020-point45-multiplatform`；一次性命令、完整patch、文件清单和CPU日志留在远端。本地临时审查副本`/tmp/glm-p45-Vdmo38`，不进入项目scripts或models目录。

最终完整证据为 `final-review.json`（SHA `ddbb9f3d373a7744eb1a2a8d77badcf5bf545b1ef8a4a452b30f5c82c83b7446`）、`runtime-final-readonly.json`（SHA `7c788b7be5ca578619a7ca586cfa927526323ba18daaf1f271090b88f0e49cbb`）、`review/patch-inventory.json`（逐文件增删改、理由、原/新 SHA），CPU 日志在 `revision-v3/`。完整 patch 为 `review/plugin-vs-pr454.patch` SHA `74adf1a21e1c1e9aaf86c251838261f09debfa844b8360d962f105aa9e8e7460`、`review/flaggems-vllm-vs-official-main.patch` SHA `4ea7df7433a950564f3455ae5f65b559df0a055fa1ac49b5461f092d8b5061da`；相对点44 delta 两份也保存在同一 `review/`。
