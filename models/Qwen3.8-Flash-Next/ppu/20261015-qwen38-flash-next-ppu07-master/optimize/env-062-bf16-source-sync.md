# env-062：BF16归约源码归并到标准Plugin目录

- 状态：completed，源码归并与CPU工程检查通过；新模型minimal为incomplete（未授权重启/请求）；分类：framework / 源码交付整理，非新增性能优化。
- 授权：2026-10-22用户要求把保留的BF16同步到容器`/opt/vllm-plugin-FL`，去掉闲置FP32归约，保留回退备份及算子修复；不重启、不访问8035、不提交推送。
- 目标：PPU-07 / `qwen3.8-flash-opt-ppu07-20261015`，当前8010仍使用acc018独立BF16副本，不变更其PYTHONPATH或进程。

## 设计与范围

复用main a696859b和PR455原模型TP归约，不新增公共dispatch、全局patch或数值实现。目标目录保持原Git/index和与本任务无关的改动。已测BF16模型SHA为`d458a1ceaa914945262e255ea1deb702766921fd7d3074ed9b37a9123e34517c`；只同步`vllm_fl/models/qwen3_8_flash_next/gpu/model.py`、移除其不再使用的`gpu/tp_reduction.py`及FP32专属测试，恢复原PR的`tests/qwen3_8_flash_next/test_operator_bindings.py`。不删除其他FP32计算：normalization等算法原有FP32与本次TP helper无关。Gems/FGVLLM及i64/randn/QSA M16/PLE/op061v2/黑名单/固定调优不变。

两个Plugin目录实际均为容器overlay私有目录，唯一挂载`/mnt→/mnt`；目标真实目录非symlink。原HEAD a696859b9aa528dfd5b21f5da3403fdc16bac4cd/main，PR455已有52文件暂存；保留暂存状态、已有配置文件symlink类型差异等，不用reset/checkout覆盖。editable已指向`file:///opt/vllm-plugin-FL`，无需pip重装。

## 执行前冻结

远端外部证据根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/env-062-bf16-source-sync-20261022`。容器备份根拟为`/opt/qwen38-env062-bf16-sync-20261022/fp32-source-backup`，先完整复制现有目标源码及.git/未跟踪文件并逐文件核验，另导出到外部证据根；备份未成功不改源码。可复现变更/核验命令先保存于上述证据根commands，记录SHA后执行，拒绝重复目录。

顺序：精确8010/源/隔离和共享使用者预检→完整备份/manifest→核BF16模型等于原PR index→窄同步和清理→语法/引用/原PR测试AST及CPU原生MoE归约契约检查→仅允许预定3文件变化，Git index/其余源码/算子来源/实际运行BF16树不变→记录最终SHA与回退步骤。保留首次工具错误，不自动改模型/重启来补测试。

## 验证与结论边界

使用本地`inference-accuracy-evaluation`的`minimal-regression`模式，限CPU工程子集。无GPU初始化、模型请求、服务重启、graph capture或新replay；现有acc018只属未改的实际BF16运行树，不给标准目录新绑定gate。未来若加载标准目录，需授权后的来源/graph/最小回归及对应gate验证。跨平台/完整模型回归未执行，不能标成新的模型minimal passed或性能收益。

## 回退

仅还原本次修改/删除的3个精确路径，先校备份SHA及当前预期内容；备份包含原始Git/index用于人工恢复，但本次不改Git index、不提供强制reset。回退不包含任何服务动作，需要服务变更时另行取得用户授权。

## 结果

执行命令已在本地`/private/tmp/qwen38-env062-bf16.Kuno1Z`保存并AST验证：`control.py` SHA`5a95688ed23372c541520345a6ec90ca1d2f4fdad5ba1d446ab0df22da7b31e7`、`sync.py` SHA`1fca052fe7b2d417ff55ae3c4e00e481392600a721893116a6052a29dd41fb2d`、`cpu-check.py` SHA`98b087044a89d6086e1da84a86d9bbcdf43dd287e0b0286b13c4a22165fd3f1e`。仅把这3个文件排他传入远端根`commands/`，复核SHA后一次`PYTHONDONTWRITEBYTECODE=1 python3 <远端根>/commands/control.py`；controller核精确8010并只调用容器中的源码同步与CPU检查，不包含kill/start/run-eval。

CPU检查复用eng055的安全原则：真实CPU tensor、直接执行安装vLLM原生MoE方法AST、mock collective，阻止GPU初始化/网络/子进程；模型双处原生allreduce AST、所有Python语法及原PR3测试保留。不是TP8数值或新模型验证。此为执行前记录，实际完成回执见下；监控保持PAUSED。

终态补充审计（执行前记录）：原同步已完成，但末尾`git status`刷新index stat缓存，导致index字节SHA变化，原摘要的`git_index_unchanged`需纠正为暂存内容语义不变。只读CPU脚本`final-audit.py` SHA`e94ab8b8251dd828cd83348cb7aa3d410602558a462100d8e89aa3dd576236f6`将核backup与当前全部`ls-files --stage`路径/mode/blob及cached diff、HEAD相等，确认实际源码只多出index元数据差异。使用`GIT_OPTIONAL_LOCKS=0`避免再次刷新；写新`final-audit-001`，不重跑同步或覆盖原回执。

### 完成回执

- 标准目录`/opt/vllm-plugin-FL`已同步BF16。模型文件与已测BF16及PR455暂存原件逐字相同（SHA见上），恢复原生两处TP collective和MoE原生late reduction；删除62行FP32专用helper，原测试文件恢复PR原件49行/3测试。仅上述3路径变化；未清理算法本身必要的FP32计算，未触碰其他模型/backend。
- 删除的helper及其FP32专属测试均可从完整备份恢复：容器`/opt/qwen38-env062-bf16-sync-20261022/fp32-source-backup`，外部`<远端根>/fp32-source-backup.tar.gz`。659项逐文件/模式校验及tar内659文件SHA通过，归档SHA`7f7d950b436c1a6700ec3eadab4e6b98e519fb670b5e4a31faa51a124b8019b8`；备份manifest SHA`da3912d0590f10d56f37d48167f3fb1bd17cf7662015a20a740cd5c5aca3b384`。完整.git和未跟踪文件保留，无物料不可恢复删除。
- CPU检查：384项实际安装vLLM原MoE方法/CPU tensor契约通过，涵盖SP/TP/EP/已归约、BF16/FP16/FP32、截断/空截断、转置/别名/stride；collective模拟，错误一次直传不重试。448 Python文件AST通过，原PR3测试保留但未执行其设备导入/Meta流程。CUDA未初始化，无被阻止的GPU/网络/子进程操作。CPU summary SHA`be3c5eba45f03c2416bcb1da96ef7646e9892489835f6503a5124b6fed01664e`。
- Gems 3713项、FGVLLM 397项源码前后指纹完全相同；实际运行的独立BF16整树未变。i64/randn/QSA M16/PLE/op061v2等修复不变。生产包与已测BF16包仅有未使用helper被移除的差异。
- editable绑定未改/未pip：干净CPU进程通过spec解析到`/opt/vllm-plugin-FL/vllm_fl/__init__.py`，未执行Plugin包初始化。8010 Host1924405/start531054985/argv和原PYTHONPATH不变，health200；仍使用acc018独立BF16目录，**尚未加载标准目录此次整理的源码**。
- 暂存路径/mode/blob、cached diff、HEAD均与完整备份一致；原52文件PR暂存及既有配置symlink类型差异保持。index字节因`git status`刷新而变，不能称字节完全未改；补审计确认除`.git/index`外最终树与同步后快照一致。最终index SHA`33cff45503eafc2880581dfee4bbb405d2a428cd03c9be53a87c457a173fa675`。没有git add/reset/commit/push；不改原摘要，`final-audit-001`明确纠正该项口径。
- 首次传输因macOS tar额外`._control.py`被严格白名单拒绝，发生在脚本执行和源码变更前；`STAGING_ERROR-001.json`保留。改用`COPYFILE_DISABLE=1`/ustar仅传3个原SHA文件后完成，不是模型或同步失败，不曾重复执行同步。

远端`FINAL_SUMMARY.json` SHA`21d29a2a9f8346f5c3cab95449b87ac42dd0463093899a9606a1fc141725a9d0`，原20文件manifest SHA`338522871aca321bb8b6c8dbcc3884a3eb73c3cd927cda1bd60b05854f23222e`。补审计summary SHA`8f728d67d500dc7d37f9391a5bb813ccbd13c290ae019f58a8f67252d4872eaa`、manifest SHA`83c323d1acd4b0dad94c1434b79c7e7f4bbc95e2a65ce04aa5c9e6d19fa1ace4`。所有原始回执保留，不覆盖历史acc018 gate/source。

决定：保留此次标准目录BF16整理；0服务动作/0推理/0GPU测试/0次8035访问/0提交推送，监控仍PAUSED。`pr_readiness=needs_revision`仅表示尚无此最终目录的完整设备CI/新模型加载回归，不能把CPU工程通过当作新formal gate或性能测试。未来如需从标准目录重启加载，应先取得授权再做来源/graph/最小回归及对应精度绑定；本次不自动执行。

本地记录校验：YAML解析/唯一env062条目/README链接及`git diff --check`通过。全仓`check-project-records.py`返回失败，报告其他既有案例schema/链接缺口及未迁移过程产物（493项旧登记等待迁移），不宣称全仓通过；本次没有新增仓内脚本或原始产物，不为此次任务修订无关案例。
