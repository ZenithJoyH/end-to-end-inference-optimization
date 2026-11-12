# BGE-M3 / mx-59 启动脚本整理

> 2026-11-06已按审查直接更新BGE-M3实际安装三库：Plugin运行时再少6行，FG补K检查，FGV对齐34参数并明确拒绝未支持FA4值；637项及127060数值零差通过。源服务未重启、GPU3释放，见[修复与验证](../../../models/BGE-M3/metax/20261105-bge-m3-mx59-base-1k/optimize/interface-fix-003.md)。

> 2026-11-06只读复核：没有新增公开算子或独立kernel；仍可去掉约6行Plugin转发。FGV与官方vLLM0.24.0 NVIDIA接口存在原版本继承的4项缺参和尾部位置顺序差异，当前BGE使用子集不触发。详见[收敛与接口审查](plugin-interface-audit.md)。本轮未改源码或服务。

> 最新Plugin收敛已完成：完整diff从34/+2089收敛到30/+1539，运行时代码新增480→431；363项测试、pre-commit及127060个数值逐位对照通过。详见[第二轮收敛](plugin-converge.md)。源仓库已更新，在线进程保持旧已加载代码，未重启。

> 当前启动脚本为23行：环境变量+显式CLI+nohup，自动加载Plugin平台默认metax.yaml，不再指定BGE专用YAML或追加attention黑名单。最新环境设置、备份和验证见[默认配置调整](serve-default.md)，简化过程见[启动脚本简化记录](serve-simple.md)；下文初次整理中的帮助/dry-run/YAML包装属于历史版本。

> 性能脚本404来自原客户端请求/v1/completions。按用户原生命令已将指定远端vllm_perf.py改为openai-embeddings /v1/embeddings，保存原生JSON并校验结果；离线回归、原生参数及单条16-token功能请求通过。当前vLLM不支持probe-request-rate，省略该选项并保留原生初始试请求。按用户后续要求恢复原代码组织和原22列CSV、每场景文件/Run标签/SUMMARY格式，embedding不适用指标留空。详见[性能脚本调整](embedding-perf-script.md)与[原404诊断](perf-404.md)；没有执行完整压测。

- 日期：2026-11-05（Asia/Shanghai）。范围：用户明确指定的 `/public-flash/jinghao/BGEM3/serve.sh`，仅整理启动脚本；不是性能优化或正式模型验收。
- 授权：当前对话用户要求“调整下 /public-flash/jinghao/BGEM3/serve.sh 脚本”。不修改镜像、模型、Plugin 源码、YAML 或容器配置，不启动或重启服务。
- 已完成 `scripts/inventory` 和 `scripts/connectivity-check --limit mx-59`；当前 BGE-M3 容器主命令为 `/bin/bash`，目录通过既有 `/public-flash` bind mount 可见。
- 原脚本 SHA256：`39e7d0656bdb1edcd06942216ee15ce11c5a07007368eda8ce04a25a577d589b`。

## 发现与改动

原文件复制自 Plugin 的 `examples/bge_m3_dense/serve.sh`，仍使用 `../..` 计算仓库根目录，且在脚本旁寻找 `serve.yaml`。复制后的实际配置位于同级 `vllm-plugin-FL/` 下。默认 `/models/bge-m3` 不存在；容器中已核验 `/public-flash/models/bge-m3/config.json` 可读。

集中配置模型、Plugin 配置根目录、监听地址和端口；改为从同级 `vllm-plugin-FL/` 读取两个 YAML。默认模型改为已核验的 `/public-flash/models/bge-m3`，保留监听 `127.0.0.1:8000` 及全部原有 MetaX 环境选项和 YAML 推理参数。增加帮助、启动前文件/可执行程序检查、命令回显和 `--dry-run`。保留位置模型参数及尾随 vLLM 参数覆盖能力。不改变 Python 导入路径：当前实际导入仍是镜像内 `/workspace/bge-m3/tune-src/vllm-plugin-FL/vllm_fl/__init__.py`；同级源码副本只作为配置来源，非 Git checkout，未推断其 revision。

## 执行方案（先记录后执行）

本地临时候选 `/tmp/bgem3-serve-cleanup-20261105.sh`，部署命令为 `python3 /tmp/bgem3-serve-cleanup-20261105-deploy.py`。部署脚本经 `ssh mx-59` 执行 Python：核对精确目标非 symlink 与原文件 SHA，在目标同目录创建独占临时文件，保持 owner/group/mode，运行 `bash -n`，独占备份原文与 owner/group/mode/时间戳，再次核对旧文件 SHA 后用 `os.replace` 原子替换。不会执行服务脚本或修改其他已有文件。备份位置和新 SHA 在执行后补充。

首次部署在备份的 `shutil.copystat` 扩展属性复制处遇到 NFS `EIO`，发生在替换前，原脚本未改动；遗留原文备份 `/public-flash/jinghao/BGEM3/.serve.sh.cleanup-714ehsdp.original`。改为显式保存 owner/group/mode/时间戳，不复制文件系统扩展属性，然后重试。后续验证先核对候选 SHA，禁止对未更新的脚本盲目使用新增选项。

首次部署失败后曾误对旧脚本运行 `--dry-run`，触发了 vLLM CLI 导入，在读取不存在的 `/public-flash/jinghao/BGEM3/serve.yaml` 时退出；没有启动模型服务。该次不是 dry-run 通过证据。已修正验证顺序：必须先核对候选 SHA，再调用新增选项。

- 部署完成，候选 SHA256：`4e3bd05a3ec7d2a63d59d7561d06ac9c5da5e37461d00b32627bbf844e65d993`；Host 与容器内核验一致。
- 可回退备份：`mx-59:/public-flash/jinghao/BGEM3/.serve.sh.cleanup-kqhknxx4.original`；SHA256 与原文件相同，`root:root`、`0755` 已核验。

回退：将执行后记录的备份复制回原路径（须先核对当前脚本无后续人工修改），然后运行 `bash -n`；不触发服务重启。

## 验证

- 本地 `bash -n` 和 `--help` 通过。
- 远端/容器内 `bash -n` 通过。
- 容器内默认 `--dry-run` 通过：模型 `/public-flash/models/bge-m3`，监听 `127.0.0.1:8000`，两个 YAML 路径存在且可读。
- 容器内显式模型目录、`--host 0.0.0.0 --port 8001` 的 dry-run 参数透传通过。
- `/bin/bash` 模型路径和不存在的 `PLUGIN_ROOT` 均在导入 vLLM 之前被清晰拒绝；没有启动服务。
- 未运行模型服务、精度测试或性能测试；不声明模型可服务或性能收益。

## 同任务追加：恢复实际安装 Plugin 的 Git 元数据

用户追加授权“容器中安装的 plugin 似乎已经不是一个代码仓库了，你调整下”。只恢复 BGE-M3 容器私有目录 `/workspace/bge-m3/tune-src/vllm-plugin-FL/.git`，不修改源码、安装绑定、依赖、共享副本或模型服务。

当前 editable 安装 `0.0.0+gef7339f1.review20261104`，`direct_url.json` 指向上述目录；`find_spec` 核验一致。镜像 `/workspace/bge-m3/IMAGE_MANIFEST.json` 明确记录基线 `ef7339f14c976f588d3762f55bfefef4f6ecae2e` 以及 `plugin_contains_reviewed_uncommitted_consolidation=true`。GitHub connector 已核验该真实提交，不能把现有整合补丁伪装成干净上游或升级到最新代码。

执行前计划：本地临时工具 `/tmp/bgem3-plugin-git-20261105.py` 复制至容器私有 `/tmp` 的唯一目录，再通过 `docker exec BGE-M3 /flagos/bin/python <工具> prepare` 执行。先记录全目录文件内容/权限/owner/group/符号链接及安装身份，在目标父目录新建唯一 `.plugin-git-restore-*` 暂存目录并保存工具副本、清单、既有差异和报告。以空模板初始化暂存 Git，从官方公开仓库 HTTPS fetch 精确基线的完整可达历史（不 checkout 工作树、不复制凭据/hooks），本地分支 `bge-m3-fp16-dense` 指向真实基线，index 读取基线树。`fsck`、无 alternates、源码和绑定不变及差异预览通过后，另行执行同一工具的 `publish <stage>`，只原子移入 `.git` 并重复核验。不创建提交、不推送、不重装、不重启服务。

这不是 Plugin 源码设计或性能修改，无精度/性能测试。回退只需在核对后移走新增 `.git` 并保留，工作树与安装绑定保持原样。

镜像清单的 654 项源文件哈希全部匹配，无交付后源码漂移。首次 prepare 暂存目录 `/workspace/bge-m3/tune-src/.plugin-git-restore-1zhr68hy`：Git 拒绝直接 fetch 到该暂存仓库 HEAD 指向的分支，目标源码未变且 `.git` 尚未发布。修正为先 fetch 到 `FETCH_HEAD`，再仅在暂存仓库 `update-ref` 建立本地分支；失败记录保留，使用新的独占暂存目录重试。容器只见两个 Bash 进程，无运行中的模型服务。

### 完成结果

- 实际安装目录已恢复自包含 `.git`，无 alternates，`git fsck --full` 通过。
- 分支 `bge-m3-fp16-dense`，HEAD 为真实基线 `ef7339f14c976f588d3762f55bfefef4f6ecae2e`；完整可达历史 178 个提交，未新建提交。
- `origin=https://github.com/flagos-ai/vllm-plugin-FL.git`。没有 fetch 最新分支、checkout、源码覆盖、提交、推送、依赖变更或服务重启。
- 现有差异完整可见：25 项 tracked 修改、3 项原有文档 JSON 删除、1 项未跟踪测试文件，共 29 项。tracked diff 为 28 files / +84 / -1542；删除是镜像已交付的差异，不是本轮删除。既有 patch SHA256：`e95e49fdc41a7b5abde2f197c620ec332495d2ce440e60921ffd3a7a5a24be0f`。
- 工作树 884 个文件/目录/链接条目的内容、mode、uid/gid 与链接指向前后完全相同。清单 SHA256：`ea9a54a7f58312f0ada67d16dee7fc869bf7201f172c9a6985c75af6a0231f2b`。
- editable 安装的 origin、版本与 direct_url 前后一致。共享 `/public-flash/jinghao/BGEM3/vllm-plugin-FL` 副本未修改，也未切换安装位置。
- 证据根：BGE-M3 容器内 `/workspace/bge-m3/tune-src/.plugin-git-restore-mje18mzd/`，保留 `restore-git.py`、`source-before.json`、`installation-before.json`、`existing-changes.patch`、`status-before.txt`、`PREPARED.json`、`FINAL_REPORT.json`；独立目标 `.git` 不依赖此目录。
- 原生回执 `FINAL_REPORT.json` SHA256：`c977681786ed32c2e71d11a961e5df8cdf9cfd15eab6116b81a406ec3651a73b`；执行工具 `restore-git.py` SHA256：`23f660c03ff63192bead53e018dd9fd8e8722889d92e2c175ca47e6306e7465f`。普通 `git -C` 的根路径、分支、log、remote 和 status 均已独立验证可用。
- 执行：`python3 /tmp/bgem3-plugin-git-20261105-control.py` 完成准备，`python3 /tmp/bgem3-plugin-git-20261105-control.py /workspace/bge-m3/tune-src/.plugin-git-restore-mje18mzd` 完成元数据发布。容器工具入口 `/tmp/bgem3-plugin-git-20261105.IjeQf5/restore-git.py`。

## 同任务追加：修正完整 BGE-M3 diff 的审阅基线

用户指出当前修改看起来基于已修改版本、diff 不正确，并要求调整。只读核验确认代码仍是同一镜像交付内容；上一轮恢复使用镜像头 `ef7339f1` 为 HEAD，因此普通 diff 仅显示其后的整理改动，未展开 BGE-M3 接入与三轮优化。PR #636 的四个提交正是 `e15c3d7`、`45a12d4`、`b9269d2`、`ef7339f1`。首次提交父节点为 `5463eae824b1fbaa3d331564ab2fb4c51f1b6e09`，不是取最新 main 或推断新的适配基线。

执行前方案：保留原分支 `bge-m3-fp16-dense` 及其真实镜像头，新建 `bge-m3-review`，HEAD 指向首次 BGE-M3 改动之前的 `5463eae`。现有文件保持逐项不变，只重新组织 Git HEAD/index；新增文件使用 intent-to-add，使普通 `git diff` 包含完整新增内容，但不暂存实际内容、不创建提交。不恢复镜像有意移除的三个 JSON 结果文件；相对于原始父提交它们本来就不存在，不再出现在完整 diff 中。当前代码不会因此被重写或叠加。

本地临时工具 `/tmp/bgem3-review-base-20261105.py`、控制入口 `/tmp/bgem3-review-base-20261105-control.py`。先通过独占容器 `/tmp` 保存执行工具，再 `prepare`：在私有源码父目录创建 `.plugin-review-base-*`，备份完整 `.git`、源码与绑定清单和旧差异，用独立临时 index 准备新基线/intent-to-add，校验无 staged 内容及 `git diff --check`。预览通过后另行 `publish <stage>`，用 index.lock 保护发布，新建分支并切换 HEAD、原子替换 index；不调用 checkout、hard reset、源码覆盖或安装命令。发布后核验原分支、源码/权限/链接、安装身份、完整 patch SHA 及 fsck。不启动或重启模型服务，无精度/性能测试。

回退入口是独占产物目录中的 `git-before/`、原分支与旧 index/HEAD；执行回退前须先核对是否已有后续人工 Git 操作。

### 完成结果：完整 diff 已展开

- 当前分支 `bge-m3-review`，HEAD `5463eae824b1fbaa3d331564ab2fb4c51f1b6e09`。原分支 `bge-m3-fp16-dense` 仍指向 `ef7339f14c976f588d3762f55bfefef4f6ecae2e`，四个 BGE 特性提交和历史全部保留。
- 普通 `git diff` 现在展示完整 BGE 接入、Linear/JSON/FP16 dense 优化及镜像清理后的最终实现：35 files / +2311 / -3。28 个新路径使用 intent-to-add，使新增文件也进入普通 diff；staged 内容变更为 0，新提交为 0。之前三个结果 JSON 的 -1422 行在正确父提交基线下自然消失，没有恢复或删除任何工作树文件。
- `git diff --check`、完整 patch SHA 一致性、`git fsck --full` 通过；完整 patch SHA256：`453043aea590d95f73e4bc2bbc22f9a75b2b208568b3adec2fe3ce8ee25bd897`。
- 884 个工作树文件/目录/链接的内容、mode、uid/gid、链接指向逐项不变；源清单 SHA256 仍是 `ea9a54a7f58312f0ada67d16dee7fc869bf7201f172c9a6985c75af6a0231f2b`。editable origin、版本与 direct_url 不变；本轮源码修改、重装、服务重启、模型请求均为 0。
- BGE-M3 容器内独占证据目录：`/workspace/bge-m3/tune-src/.plugin-review-base-vbx9sgbq/`。`git-before/` 为发布前完整元数据备份；另保存 `review-base.py`、前置清单、旧增量 patch/status、`full-feature.patch`、`intent-to-add.json`、新 index、`PREPARED.json`、`FINAL_REPORT.json` 和最终 status。
- `FINAL_REPORT.json` SHA256：`8bccab0f095c9877dc7489653595b84bf8fe7d0036a1d39cc34d22e59008cac5`；`review-base.py` SHA256：`9e5cc25d71c7fa9970cc759f966d9f902d2f793130da664ad0324e01b421f377`。普通 Git 环境已独立核验分支、shortstat、空 staged、旧分支和 whitespace 检查。
- 执行命令：`python3 /tmp/bgem3-review-base-20261105-control.py` 准备；`python3 /tmp/bgem3-review-base-20261105-control.py /workspace/bge-m3/tune-src/.plugin-review-base-vbx9sgbq` 发布。容器初始工具入口 `/tmp/bgem3-review-base-20261105.UFFjAy/review-base.py`。
- 结论边界：修正本地完整特性的审阅基线，不代表已经把特性重放至当前最新 main，也不代表 PR/精度/性能验收。只因元数据改变，不执行模型回归或性能测量。

## 同任务追加：完整 diff 开发规范审查

用户要求检查完整 diff 的必要性和项目开发规范符合性。本轮只读审查 `bge-m3-review` 相对 `5463eae` 的完整 35 文件补丁，不修复生产代码或改变 Git 基线。以 `docs/plugin-change-review.md`、`docs/plugin-development-standard-v1.md` 和算子规范第 0/1 节为标准；针对架构边界、分发/公开 API、实例隔离、契约/并发、依赖、测试、示例与文档分别核验。

已只读取回源码、原始基线和完整 patch 到本地临时目录 `/var/folders/r4/vg8kl9yj2651_r2x_0xzn4tw0000gn/T/bgem3-plugin-review-20261105-jxzmzmx9/`，不作为长期模型源码副本保存。接下来只读读取实际安装的 vLLM/FG/FGV 相关接口。CPU-only 单测计划：BGE-M3 模型单测、dispatch policy 单测及共享 Worker 的新契约测试；`-m 'not gpu'`，显式屏蔽 CUDA/MACA 设备，禁用 pytest 外部插件、源码字节码和 pytest cache，临时输出写入容器唯一 `/tmp`。只执行 CPU/mock 契约测试，不启动服务、GPU kernel、精度/性能测试。若依赖或导入导致失败，如实记录，不改源码或削弱测试绕过。

审查完成，详见 [完整 diff 审查报告](plugin-review.md)。`pr_readiness=needs_revision`：R1（P1）Plugin 中解包 FG 私有 Linear kernel、重建 tuner/launcher 且注册为 vendor；R2（P2）FP16 默认路径无条件安装纯转发 Linear 包装；R3（P2）缺从真实 BGE 入口经 dispatch 到真实 FGV 的数值/命中证据。共享 Worker 的异步 pooling 透传建议保留。

本轮 18 项 shell/HTTP CPU 测试通过；广泛 CPU 测试因既有 FG/FlagTree 在无 GPU 可见时的 driver 导入要求发生 5 个 collection errors，未运行到断言，不能标成通过或本次新回归。25 Python 文件及 shell 语法通过；ruff/shellcheck/pre-commit 未运行，GPU/模型/graph/性能未测。源码与完整 diff 未修改，patch SHA256 仍为 `453043aea590d95f73e4bc2bbc22f9a75b2b208568b3adec2fe3ce8ee25bd897`。

## 同任务追加：审查问题整改完成

用户随后授权按报告修复。详见 [整改与验证记录](plugin-review-fix.md)：R1/R2/R3 均已修复并部署到容器私有实际安装源码。删除 Plugin 的私有 Linear tuner/launcher 与默认纯转发绑定，将特化保留在 FG 公开 ATen Linear 路径；BGE attention 单次执行并保留既有 I/O 诊断；必要 Worker 修复保留。

最终 Plugin完整diff34 files/+2089/-3，SHA256 `146758d9791c8e6ceb7bb51695925215ca4d50ba2563c7dfaa4f99d2e935db42`。Plugin80项、FG24项及适用pre-commit通过；FP16/FP32原生embedding与全部8种joint选择对照110676个数值，最大绝对差2.3841858e-7，满足预冻结契约。FG真实capture+两次新输入replay通过。临时服务均已退出；未提交推送，未修改其他容器/共享副本/权重/vLLM/FlagTree/FGV。

状态 `local_fix_validated`，不构成正式精度/性能验收。配套FG改动尚未公开发布，Plugin与FG补丁必须成对交付，PR前须完成公开版本固定，故 `pr_readiness=experimental`。最终回执、失败诊断、备份和回退入口见整改记录。

## 同任务追加：两套算子库整理完成

按用户追加要求完成[FlagGems / FlagGems-vllm 仓库整理与审查](operator-repositories.md)。两套实际editable源码根均恢复自包含Git和缺失的测试/配置/文档，4362/284个完整可达历史提交；均在`bge-m3-review`，安装原提交保留为`bge-m3-source`。FG以4897cc306为基线，完整diff3 files/+191/-1；FGV以首次FP32支持之前741715844为基线，完整diff7 files/+617/-12，完整展开原两次FP32提交及本轮metadata校验/日志修正。

去掉FG无关导入变化，修复FGV在`python -O`下assert失效的执行前校验，并补规范要求的真实厂商命中日志。FG24、FGV133、优化解释器60、Plugin80及完整diff适用pre-commit通过。FP16原异步HTTP对照因26-token合批与12/14-token拆批混用而失效；按同一max_num_seqs1契约，before/current/revert每轮10240项与原baseline逐位一致，不放宽阈值、不丢首次；FP32原108628项max_abs2.38e-7。原失败证据保留。

状态`local_repositories_and_fixes_validated`；仅本地维护/功能回归，不是正式精度/性能验收。安装绑定、Plugin源码、权重/vLLM/FlagTree均未额外修改，测试服务全部退出；未提交推送，公开配套FG/FGV版本仍待PR前固定。最终三库补丁、回执及回退信息见算子库整理记录。
