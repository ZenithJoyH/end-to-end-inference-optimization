# PPU-03 / hy4-preview 三仓库版本更新

用户于 2026-10-18 明确要求更新现有 `hy4-preview` 容器中的三个仓库。本次是环境版本更新，不开展端到端性能优化，不新建优化容器，不启动模型服务。

当前状态：`completed_version_update_imports_passed`。三个指定分支已安装并实际导入；原仓库及所有既有改动完整保留。目标 Plugin 分支缺少原 HY4 专用模型模块/注册，未进行模型推理验证。

## 范围与预检

- Host：inventory 的 `PPU-03`，`scripts/connectivity-check --limit PPU-03` 通过。
- 容器：精确名称 `hy4-preview`，当前运行，只有 init/bash，未发现模型服务。
- 镜像 ID：`sha256:dcfc456313fe0e9ae8444134bd37849c6bda7084eca3feef98a388db26f7bdbe`。
- 唯一挂载：`/mnt:/mnt`，RW/rprivate；三个源码目录及 site-packages 都在容器私有层。
- Python：`/usr/local/bin/python`；原三个安装都是 editable，默认没有 `PYTHONPATH`。
- vLLM：`0.24.0+empty`，源码 `ee0da84ab9e04ac7610e28580af62c365e898389`，工作区干净；本次保持不变。

| 仓库 | 原分支 / HEAD | 原工作区 | 指定分支 / 已核验目标 HEAD |
|---|---|---|---|
| `/workspace/vllm-plugin-FL` | `support-hy4-preview` / `f7d1aaa9935dd8d613376601504a793b11ee34e0` | 4 个 tracked 修改、1 个 untracked | `ZenithJoyH/vllm-plugin-FL:024plugin-opt` / `08da21cb39601752040196232b60a152382c0f8f` |
| `/workspace/FlagGems-vllm` | `support-hy4-preview` / `a26a90258de8bcad0a5d831f38b52f755c6a73b0` | 4 个 tracked 修改 | `ZenithJoyH/FlagGems-vllm:gems-opt` / `46387d7f96050204c1b932f35680a3ea03896fa6` |
| `/workspace/FlagGems` | `support-hy4-preview` / `0e02755770011d517c8de591bf91998bbcf30ad1` | 干净 | `ZenithJoyH/FlagGems:gems-opt` / `3ba1d1d99010de56d12088992f8b0da3444d90ca` |

## 执行前冻结的方案与命令

远端产物仅写入目标容器未挂载的私有新目录 `/workspace/.hy4-preview-update-20261018-01`。不使用 Host 共享目录，不改挂载。先以独立 clone 准备三个目标分支并核验固定 SHA，然后把三个原目录整体移动至该目录的 `originals/`，保留 Git 历史、未提交改动、untracked 与 ignored 文件。新 clone 移入原稳定导入路径，再使用现有 Python 构建工具以 `--no-deps --no-build-isolation` 重装 editable；不升级 vLLM、Torch、FlagTree 或平台 SDK。

所有执行脚本先保存到容器私有产物目录的 `commands/`，再运行。安装与验证失败时恢复原目录及原安装记录，失败候选留存；不 reset、clean 或覆盖旧源码。更新验证覆盖分支/HEAD、实际 `__file__`、editable metadata、Plugin entry point 与基本导入。模型精度、graph 和性能不在本次版本更新验收范围。

准备入口（执行前保存）：

```sh
ssh -o BatchMode=yes PPU-03 'docker exec hy4-preview /usr/local/bin/python /workspace/.hy4-preview-update-20261018-01/commands/prepare.py'
```

部署准备脚本时，使用 `docker exec -i hy4-preview python -c ...` 创建上述全新私有目录和 `commands/`，以 exclusive create 保存 stdin 脚本；保存后核验 SHA-256 为 `b4a257f7ea7a0268d69054e4b54576ebe656c7193ccb9937182bf688f5a128db`，再调用准备入口。未提供 Host 工作目录，不向 Host 文件系统写产物。

更新前三个包分别在新 Python 进程中导入成功。基础版本：Torch `2.10.0`、vLLM `0.24.0+empty`、FlagTree `0.6.2a1+ppu3.6`。三个版本更新后须保持一致。

准备已通过，三个 clone 与固定目标 SHA 一致。激活脚本 SHA-256：`220f89aea1ba36472c8fbba2ccf076920344db64b21517ad7005c35b0c02414f`。脚本先核验原仓库没有漂移；精确移动旧包的 `.dist-info`、editable finder/`.pth` 和 FlagGems console scripts 至 `original-install/`，避免旧 editable 映射残留。随后安装三个新版本，并比较全部 distribution 版本，允许变化仅限这三个包。失败自动恢复原安装文件和目录，候选及错误证据保留。

激活前重新检查容器进程，只允许原 init/bash；重新核验唯一挂载。将脚本以 exclusive create 保存到 `commands/activate.py`，校验上述 SHA 后执行：

```sh
ssh -o BatchMode=yes PPU-03 'docker exec hy4-preview /usr/local/bin/python /workspace/.hy4-preview-update-20261018-01/commands/activate.py'
```

实际构建使用容器现有 setuptools `80.10.2`、setuptools-scm `10.0.5`、wheel `0.45.1`。新 FlagGems 的隔离构建建议 `<77` / `<10` / `0.46.2`，本次采用 `--no-build-isolation` 验证现有组合，避免变更其他包；若构建失败则回退，不修改上游构建文件。

## 首次验证与修正

首次安装三个包全部成功，但验证脚本沿用了旧版 `vllm_fl.models.hy_v4` 模块名，其 import 失败。脚本自动回退成功，三个原 HEAD、未提交状态及全部 package 版本均恢复。证据：`logs/validation.log`、`activation-error.txt`、`rollback-passed.json`。

只读核验发现：目标 Plugin 的 `vllm_fl/models/` 只有 `__init__.py` 和 `qwen3_5.py`，Git grep 未发现 HY4 专用模块/注册；当前安装的 vLLM 也没有 `hy_v4.py`。这是所指定分支与原适配代码之间的实际差异，不能用基本 import 通过推断 HY4 可运行。按用户明确的分支替换请求，不向指定分支移植旧模型代码，不修改 vLLM。

第二次激活保持相同目标 SHA，复用已下载并留存的 clone，仅将 HY4 legacy 模块检查改成可见的能力记录；其余实际 import、HEAD、branch、editable metadata、entry point、工作区和非目标 package 版本检查保持。原失败记录保留。激活脚本 `commands/activate-v2.py` SHA-256：`0900881b69be96476a78c0ae40ea5f772eb462cc6b5563849746264dfa4ea03b`，执行前以 exclusive create 保存并校验。命令：

```sh
ssh -o BatchMode=yes PPU-03 'docker exec hy4-preview /usr/local/bin/python /workspace/.hy4-preview-update-20261018-01/commands/activate-v2.py'
```

第二次激活已完成：`ACTIVATION_PASSED`。HY4 模型运行能力 `not_validated`，已在对话中告知用户所指定分支缺少原专用模块。

## 完成结果与边界

| 包 | 分支 / HEAD | pip metadata | 实际导入路径 |
|---|---|---|---|
| Plugin | `024plugin-opt` / `08da21cb39601752040196232b60a152382c0f8f` | `0.0.0+g08da21cb3` | `/workspace/vllm-plugin-FL/vllm_fl/__init__.py` |
| FlagGems-vllm | `gems-opt` / `46387d7f96050204c1b932f35680a3ea03896fa6` | `0.3.0.dev1` | `/workspace/FlagGems-vllm/src/flaggems_vllm/__init__.py` |
| FlagGems | `gems-opt` / `3ba1d1d99010de56d12088992f8b0da3444d90ca` | `0.0+g3ba1d1d99` | `/workspace/FlagGems/src/flag_gems/__init__.py` |

上述版本在 `/tmp` 工作目录、无 `PYTHONPATH` 的新 Python 进程中验证。每个包仅一套 distribution metadata，均为 editable；两个 `fl` entry points 分别为 `vllm_fl:register` 和 `vllm_fl:register_model`，load 后可调用。三个 Git 工作区均干净且分支/HEAD 匹配指定来源。浅 clone 的 setuptools-scm 版本号作为安装显示值，以固定完整 Git SHA 为源码身份。

全部 distribution 版本差异仅涉及这三个目标包。Torch `2.10.0`、vLLM `0.24.0+empty`、FlagTree `0.6.2a1+ppu3.6` 均保持；vLLM HEAD 与工作区也保持。安装未修改原适配源码补丁，最终备份的 HEAD、完整 Git diff binary 补丁及 untracked 文件存在性均核验通过。

本次没有启动/重启容器或模型服务，没有数值、graph、正式精度或性能结论。指定 Plugin 分支的 HY4 支持缺口是后续启动模型前需要处理的事实，基本导入通过不代表模型已可用。本次无提交、推送或 PR，`pr_readiness=not_applicable`。

## 证据与回退

以下路径均位于 **PPU-03 的 hy4-preview 容器内**，根目录 `/workspace/.hy4-preview-update-20261018-01`：

- `originals/{vllm-plugin-FL,FlagGems-vllm,FlagGems}/`：三个原完整仓库，包括既有未提交与 ignored 文件。
- `original-install/`：原三个包的 metadata、editable 映射和 console scripts。
- `before.json` SHA-256：`de535a308f409f16eab2f1dcde4cd711fad1629b5c14b63b64f29f2d4b6a1593`。
- `runtime-receipt-v2.json` SHA-256：`a230d2503ecde4995ab8cde713715f4fd250af8cd89a76f79af9d7483986864f`。
- `activation-v2-passed.json` SHA-256：`d107e0bcb381cdc2ff37ecf8f2b8329d43a557d5e4f5c7078b61c436cae2222e`。
- `package-changes-v2.json` SHA-256：`73b6befd7200e6d5f12f24c35e4a057de1f91650d638a3e74d41e8251d61f0c4`。
- `commands/validate-v2.py` SHA-256：`d2c4edf988c34473c1eacf1c31164206a4c88a32b6366de82e10d3fcf89045c0`。
- `logs/validation-v2.log` SHA-256：`3ff30b28a986d2d127e5ea799ca6a01612973d043e49ff62c280d2063453855b`；安装日志为 `logs/<repository>.install-v2.log`。

未来回退时先重新确认准确 Host、容器及无模型进程，保存届时的新修改和安装记录；把当前三个源码目录及对应新安装文件移动到新的留存目录，再将 `originals/` 中三个目录移回原 `/workspace/` 路径，将 `original-install/` 相对于 `/usr/local/` 的文件恢复。最后按 `before.json` 核验 HEAD、旧工作区状态、包版本和无 `PYTHONPATH` 的实际导入。不得直接重跑本次激活脚本；脚本带一次性状态保护。第一次自动回退已实际验证成功。

本地文档检查：`git diff --check` 通过。该案例仅为版本更新观察，不修订性能 SOP。

后续用户要求的HY4迁移及启动验证另见 [兼容迁移案例](../20261018-hy4-preview-ppu03-migration/README.md)，本记录保持三包分支更新时的历史边界。
