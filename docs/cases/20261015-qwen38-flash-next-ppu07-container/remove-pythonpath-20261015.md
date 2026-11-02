# 移除 FlagGems PYTHONPATH 依赖

用户明确要求去掉 `export PYTHONPATH=/opt/qwen38-acc011-cachefix-20260924/FlagGems/src`。本次仅操作 PPU-07 的 `qwen3.8-flash-opt-ppu07-20261015`，不修改 PPU-01，不启动或重启模型服务。

预检发现：之前的 master editable 安装在默认 Docker 环境下生效，但 `env -u PYTHONPATH python3` 实际导入 `/workspace/FlagGems/src/flag_gems/__init__.py`，而 metadata 显示新版。原因是 site-packages 同时存在 `5.3.5+g38653f94c` 和 `5.5.0.dev0+g85cc5efb1.d20261015` 两套 editable finder，旧版本的 `.pth` 先加载。上一轮验证依赖原 PYTHONPATH，未覆盖该场景；此次按真实导入结果修正，不以包版本号代替源码命中。

修复：把旧 `__editable__.flag_gems-5.3.5+g38653f94c.pth`、`__editable___flag_gems_5_3_5_g38653f94c_finder.py` 和 `flag_gems-5.3.5+g38653f94c.dist-info` 精确移动到容器私有 `/opt/qwen38-flaggems-backup-20261015-85cc5ef/old-editable-install/`，不删除，不改其他包或 `/workspace/FlagGems` 源码。新 master 的 editable finder 保留。验证无环境变量导入与 10 个模型扩展后，使用 `env -u PYTHONPATH` 执行全部 130 项模型算子单元测试；失败则自动移回旧安装记录。

启动脚本仅把原 export 行改为 `unset PYTHONPATH`，分别保留两个脚本各自所有其他内容：共享 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`（含用户的 graph sizes、service.log 配置）及容器 `/opt/start-model-ppu07.sh`。候选反向替换该行所得 SHA 与原文件 SHA 精确相同，已通过 `--check --diff`。显式 unset 是因为容器创建时 Config.Env 仍带有该变量；Docker 既有 Config.Env 不可原地删除，本次不为此重建容器。通过脚本启动的模型及 worker 不继承该变量；若交互 shell 直接运行 Python，需要自行 `unset PYTHONPATH` 或使用 `env -u PYTHONPATH`。此差异不影响已修复的 editable 安装。

本轮远端证据根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/remove-pythonpath-20261015-01/`。旧脚本分别备份为 `start-shared.before.sh` 和 `start-private.before.sh`。`commands/` 保存部署 playbook、修复脚本和两份新启动脚本；`validation.log` 保存无环境变量的导入及算子测试。

本地控制文件在同案例 `commands/`：`remove-start-pythonpath.yml` SHA-256 `4756c2c6d55236dcdff161be22a10766e0aa163eef3a1b60cae75350e7d65442`；`fix-flaggems-editable-no-pythonpath.sh` SHA-256 `3c957a7bafae21898391238fb5f2a9ae87c2048503a8ff4257512a056862b479`。

执行状态：`completed`。无 PYTHONPATH 导入已核验为新版私有目录，site-packages 仅识别一套新版 FlagGems metadata，10 个模型扩展 callable；全部模型单元测试 `130 passed in 15.94s`，日志末尾 `NO_PYTHONPATH_VALIDATED`。实际部署 playbook `failed=0`，最终容器仅保留原两个 bash，测试客户端均已退出，没有重启/启动服务。

新共享脚本 SHA-256 `2ef72c4c4f3121d499e9b5c7c4ad3f86134562c15058c721df6221775d7d3acb`；容器内脚本 SHA-256 `647fd1d6c37cfabb2f53aefc8faa9b6b90497d909c15e3b9d8f568ad1d6d9525`。两者均通过 bash 语法和预期 SHA 检查，差异仅一行 unset。`validation.log` SHA-256 `87972eb3f68b685008cf5c36c58bb50a19c654c9914d274c0e89f647756c2b1b`。完整模型 TP8 graph、GPQA 和端到端性能仍未测，不签发新 gate。

## 后续用户启动报错：只读分析

用户随后自行启动模型，要求分析 `/mnt/nfs/users/jinghao/qwen3.8-flash/service.log`。本轮不修改、重启或运行 GPU 复现，只读检查日志、进程、实际导入及源码。日志 361005 bytes、末次更新 2026-10-15 13:51:05 +08:00、SHA-256 `f0e4f9415d69eabf72ef667e9008deaa67de27b761ef087a477fe3dccd13d75e`。

直接故障证据：第 1701 行权重加载完成（20.06s），第 1707 行缓存 compile range `(1,8192)`；第 1708 行首次 `Segfault encountered`，第 1713 行 `hggc::_HGcontext::moduleLoadRawElf`，第 1747 行 `at::_ops::normal_::call`，再向上为 `at::native::randn` / Python dispatch。驱动顶部为 `hgiFoutputSubEntryValidate` / `_foutputParseFormattedOutput` / `foutputFlush`，不是 Python OOM/ImportError。随后多 worker 同类段错误、TP0 死亡，EngineCore 的 `RuntimeError: cancelled` 和 API 的初始化失败属于后果；泄漏 semaphore/shared_memory 警告是退出时清理观察，不作为首因。

当前环境已发生后续漂移：共享脚本 SHA 变为 `2d4e79e7472a02fbebdadd58fabe097e8a0f711971c7cc455518c0963612e78a`，未再包含交付脚本的 `VLLM_FL_FLAGOS_BLACKLIST_APPEND=_conv_depthwise2d,index,normal_`、`unset PYTHONPATH` 等行，且实际运行 gpu-memory-utilization 为 0.85、max_num_batched_tokens 默认为 8192。FlagTree 实测已是 `0.7.0+ppu3.6`，不是前述通过测试的 `0.6.2a1+ppu3.6`；master pyproject 的 thead 可选项声明 `0.6.2a2+ppu3.6`。这些都是事实差异，不能据此单独宣布 0.7 有 bug 或升级 master 必然有 bug。

实际导入（显式移除 PYTHONPATH）仍为 `/opt/qwen38-acc011-cachefix-20260924/FlagGems/src/flag_gems/__init__.py`，包版本仍 `5.5.0.dev0+g85cc5efb1.d20261015`、HEAD `85cc5efb195edefea284e8ac460840601ca4c02f`，Torch `2.10.0`、vLLM `0.24.0+empty`。非旧 editable 映射复发。源码 `normal_ -> normal_distribution -> randn_kernel`（及 transform pointwise）；T-Head 没有独立 normal_ override，FlagGems 将 `normal_` 注册到 ATen。因此首个有针对性的诊断变量是恢复 `normal_` 原生 fallback，其他条件不动；若继续崩溃，再用隔离新缓存与编译器版本对照定位。恢复历史 `_conv_depthwise2d,index` 保护属于另行恢复已验证配置，不与单变量根因实验混为一谈。

结论级别为调用链定位：随机数 normal_ 路径的二进制加载触发 PPU runtime 原生崩溃。尚没有本次实际 shape/dtype、独立复现或 fallback A/B，不能证明具体是 randn kernel、FlagTree、旧二进制缓存还是驱动缺陷；也不能以之前 130 项测试推定当前编译器和完整服务通过。使用 key-operator-analysis 方法区分直接故障点、配置诱因和未证实底层原因；本轮非性能实验，`knowledge_delta: none`，未签发 gate。

## 用户要求：将 normal_ 加入启动脚本黑名单

2026-10-15 14:08 +08:00 已按用户明确指令，在共享 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh` 的 SDK envsetup 之后仅新增 `export VLLM_FL_FLAGOS_BLACKLIST_APPEND=normal_`。保留当前网络、显存比例、graph sizes 等所有其他参数；未顺带恢复另外两个历史算子排除项，也未修改源码/编译器、启动/重启/停止服务。

执行前用 inventory 与 connectivity 限定核验 PPU-07，确认脚本仍为只读预检的 `2d4e79e7472a02fbebdadd58fabe097e8a0f711971c7cc455518c0963612e78a`；Ansible `--check --diff` 与实际差异均只有新增一行。实际 playbook `failed=0`，bash 语法检查通过，新脚本 SHA-256 `58d1b0655ed2a13d0ecaddba2e5004e0e8cd0e2458aca68d84e7cfa8cb70845c`。原文件备份在远端案例 `blacklist-normal-20261015-01/start-model.before.sh`，同目录 `commands/blacklist-normal-start.yml` 保存执行命令；本地同名 playbook SHA-256 `36cbdbeadd9e580c9e1ef528e84909f3c7696317c95ccb36f2348cad6dff7a04`。

仅完成配置变更；是否消除本次段错误仍待用户再次启动后的证据，不能宣称服务已恢复。
