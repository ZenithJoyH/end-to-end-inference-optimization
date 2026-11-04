# op-013 将已保留优化迁至 minimaxM3-latest-20260924

- 日期：2026-10-15；Host：PPU-07；模型：MiniMax-M3；状态：代码迁移并通过静态/导入校验，目标运行时验收待执行。
- 用户指令：将本任务所有优化内容迁入现有 `minimaxM3-latest-20260924` 容器。此项仅迁移此前实际留存的代码/配置，不把已回退的 op-005、op-007、op-009、op-010 等实验补丁重新启用，也不迁移历史服务 PID、精度 gate 或性能收益声明。
- 来源容器：`minimaxM3-opt-20260921`（ID `bd37abcbf719...`）；目标容器：`minimaxM3-latest-20260924`（ID `274609df1ca7...`）。两者当前镜像 ID 均为 `sha256:41d96df0b7b416e1e887fe1c4dab21dfc12819875524993f90213fe29214f541`，目录挂载均仅 `/mnt` → `/mnt`，RW、`rprivate`。这证明目标具备相同挂载及镜像身份；不把历史容器的运行时 gate 直接转移。
- 目标容器当前无模型服务（`docker top` 仅 init 与 bash），但另一 `minimaxM3.1-opt-20261008` 服务在 0–7 号 PPU 上运行。迁移不停止、重启或影响它；TP16 graph、smoke、GPQA 与性能测试暂不启动。

## 迁移边界与预检

| 组件 | 来源 | 目标预检 | 迁移内容 |
|---|---|---|---|
| FlagGems | `/workspace/FlagGems`，HEAD `3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85` | 同 HEAD、干净 | `fw-006` 的 `src/flag_gems/utils/models/sql.py` 单表 reflection；`op-011/012` 的 `_thead/fused/__init__.py` 与新 `fused_moe.py` 精确 M32 BK64/stages2 特化 |
| Plugin | `/workspace/vllm-plugin-FL`，HEAD `7e412e6f8b6d8a5e4350e0237e1a8548dfaf7b94` | HEAD `cafe6363c8c3de5ba4693b91643089c17b3ab87c`；目标 `thead.yaml` SHA256 与来源 HEAD 原版完全相同 | `op-003` 的 `flagos_blacklist: [conv3d,cudnn_convolution]`，仅改 `thead.yaml` |
| FlagGems-vllm | 来源 HEAD `bfe7ac06...` | 目标 HEAD `1f9ac0e0...`，两个已有修改文件 | 本任务无留存改动；保留目标已有修改，完全不写 |

来源四文件 SHA256：FlagGems `sql.py` `c70511b6afa820e0cc5bd469fe22e5f51b8f8ca176eaef57af13183ce1426db3`；`_thead/fused/__init__.py` `fae31da546fd72fb937a9a79033e3dae09ac730446d90eeeb08367da1ace9f9d`；`_thead/fused/fused_moe.py` `dcbfa3fd2011711fcd05a1045a3d918907f87c6b11039ee69a537b53c2f9e9ed`；Plugin `thead.yaml` `2b80df497c6200f190570d9ee3400c3935b758ca6fe2fa3993adc25eacd690e4`。目标原始 SHA256：对应 `sql.py` `c4dc2be44d6a00dc01abbb85e54e4d2bfdbd9f4ed119614fe7686fb53bd4eeee`、`__init__.py` `6a965e61477dde4bdc43e6c6587294a0e28debb9a91f4809eeb93e903c118994`、`thead.yaml` `a67e3df74706940f94a7bb0b9fd1e5afe7740e6ede1b387f6cfa851580a57f81`；目标不存在 `fused_moe.py`。

目标 `/workspace/FlagGems-vllm` 已有 `swigluoai_uninterleave.py` 和对应测试的未提交修改，Plugin 存在四个 `.orig` 未跟踪文件；均归目标原有状态，本次不覆盖、不清理。`/mnt/nfs/users/jinghao/minimaxM3/start-model.sh` 是共享挂载文件，本次不修改；过去 8013/8023 的服务脚本、输出与 gate 不复制成目标容器的有效结果。

远端工作根为用户提供的 `/mnt/nfs/users/jinghao/minimaxM3`，已核对 `realpath` 不变、owner `root:root`、权限 `777`、NFS 空余约 7.6T，专属新目录 `/mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-migration-to-latest` 预检不存在。执行前将在该目录保存运行脚本、原始目标文件备份、来源 payload、sanitized manifest 与 SHA；只创建这个新目录，不覆盖其他产物。先执行 `ssh PPU-07 'mkdir /mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-migration-to-latest'`，然后上传并运行校验过 SHA 的脚本。脚本执行时再次核验容器身份、镜像/挂载、目标空闲、Git 状态及全部预期文件 SHA；任一不符即停止而不写目标源码。

预检目录已按记录命令创建，未覆盖现有数据。迁移脚本本地执行副本 `/private/tmp/op013-migrate-retained-optimizations-20261015.sh`，SHA256 `ad73a5550b0b11c75f688a31f8f408375839839ae1e0e6a4ab12b9b6e7a0538a`，`bash -n` 通过。下一步精确命令：先 `ssh PPU-07 'mkdir /mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-migration-to-latest/commands'`，再把本地脚本上传到该目录同名文件、双端校验 SHA，最后在 PPU-07 用 `bash /mnt/nfs/users/jinghao/minimaxM3/20261015-minimax-m3-migration-to-latest/commands/op013-migrate-retained-optimizations-20261015.sh` 执行。脚本预检失败则不写目标源码；部署阶段失败则尝试从专属 backup 恢复原始三个文件并仅在 hash 匹配时移除本次新建的 `fused_moe.py`。

首次运行在任何 payload/backup 或目标源码写入之前停止：预检 `source/target mounts differ`，实际 `docker inspect --format '{{json .Mounts}}'` 两行完全相同；原因是 Bash `[[ lhs == rhs ]]` 右侧未加引号，把 JSON 的方括号作为模式。源码未变化。v2 只给比较两侧加引号，本地脚本新 SHA256 `7fbac1ef17e1d7d66ad6e36d0cdd29b2cbaaf12c7bbae4972823de7d3111861b`、`bash -n` 通过；远端将以新的 `commands/op013-migrate-retained-optimizations-20261015-v2.sh` 保存，校验后运行，不覆盖 v1。

## 验证与结论边界

迁移后核对四文件 SHA、FlagGems/Plugin Git diff、真实 Python 导入路径、代码语法和 YAML 解析；目标其他源码改动应保持原状。MoE 的 M32 特化是实验性保留项，8013 同配置 A/B 测试因尾延迟波动而 `incomplete`；不可宣称目标容器性能已改善。目标当前没有服务，且 16 卡不空闲，因此 graph capture/replay、GPQA 最小回归/198 题 gate 和四场景端到端比较都标记 `not_run`，不会使用来源容器的结果代替。

## 执行结果（2026-10-15）

- v2 脚本 SHA256 `7fbac1ef17e1d7d66ad6e36d0cdd29b2cbaaf12c7bbae4972823de7d3111861b` 已在双端校验并运行，返回 `MIGRATION_COMPLETE`。脚本内 `docker top -eo args` 因缺少 PID 列报错；该检查结果不能作为空闲证明。迁移前后单独用有效的 `docker top ... -eo pid,ppid,etime,args` 核对，目标容器均仅 init/bash，没有 vLLM 服务。该脚本缺陷没有影响四文件 SHA 验证和复制结果，后续不复用它进行迁移。
- 目标四文件 SHA 与来源四文件逐一完全相同，FlagGems Git 状态仅两 tracked 修改加一个本次新增 `fused_moe.py`；Plugin Git 状态仅 `thead.yaml` tracked 修改加迁移前已有的四个 `.orig`。`git diff --check` 两仓库通过。
- 目标 `flag_gems` 导入为 `/workspace/FlagGems/src/flag_gems/__init__.py`，Plugin 导入为 `/workspace/vllm-plugin-FL/vllm_fl/__init__.py`；`flag_gems.invoke_fused_moe_triton_kernel.__module__` 解析为 `_thead.fused.fused_moe`，目标 Plugin 的 `get_flagos_blacklist(load_platform_config('thead'))` 返回 `['conv3d', 'cudnn_convolution']`。这证明代码与配置导入，但不证明实际服务 graph replay 或 C64 工作负载的 M32 命中。
- 目标 `FlagGems-vllm` 两个迁移前已有修改文件 SHA 保持 `13d2afdb...` / `2322599c...`；共享 `/mnt/nfs/users/jinghao/minimaxM3/start-model.sh` SHA256 仍为 `ce6d0ec10b67a3c3fa9cb5d5969d50251fbc3327b562bbc129d73223eea3d3c7`，没有编辑。
- 源 payload、目标原文件备份和容器谱系分别留于远端专属目录的 `payload/`、`backup/`、`manifests/`；`manifests/file-sha256.txt` SHA256 `d56be69d678d22fe19db2aa6f9aca6c6653dbfcb8fcee5bc043ec7be0f4c12a7`，`manifests/container-lineage.txt` SHA256 `72a6f698915ad7daa29587abb540ffbb178f916ded8b07d00f2150d90bdd1729`。
- 回退脚本 `/private/tmp/op013-rollback-migration-20261015.sh` 已通过 `bash -n`，SHA256 `18862effd5d60f9166c5f27c9ef62d910384abd8fdb045a457c33b6e02951929`；远端 `commands/op013-rollback-migration-20261015.sh` 已核对同一 SHA。仅作准备，未执行；脚本在目标容器无服务、四文件仍为本次迁移 SHA、备份 SHA 均匹配时才会恢复原始文件与移除本次新增文件。
