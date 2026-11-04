# env-001 PPU-13 启动当前 MiniMax-M3 容器

- 用户指令：在 PPU-13 启动一个以 PPU-07 当前 `minimaxM3-latest-20260924` 为来源的容器。
- 范围：只启动容器并迁移当前推理源码/配置状态；不启动 `vllm serve`、不做精度或性能测试，不停用 PPU-13 上其他容器。
- 来源：PPU-07 容器 `minimaxM3-latest-20260924`，ID `274609df1ca78264c1af0327ef1aa255f4e7be1ae164dd5d963fbd73a517f116`，镜像 ID `sha256:41d96df0b7b416e1e887fe1c4dab21dfc12819875524993f90213fe29214f541`，唯一目录挂载 `/mnt` → `/mnt`（RW、rprivate），host network/IPC、privileged、init、相同设备节点和 ulimit。来源容器仅 init/bash，没有模型服务。
- 目标预检：PPU-13 上同一镜像 ID 已存在；无同名容器；16 张 PPU 无计算进程；`/mnt/cpfs/models/MiniMax-M3/config.json` SHA256 `c9c97ce1e4eece60012d5a10ea87717458bfb1f19c2c7a615a3dbff83d090c6b`，共享 `start-model.sh` SHA256 `ce6d0ec10b67a3c3fa9cb5d5969d50251fbc3327b562bbc129d73223eea3d3c7`，两机一致；目标 Docker 数据盘空间充足。不会修改原 PPU-07 容器或 PPU-13 其他容器。
- PPU-13 未单独提供远程工作根目录；不把 PPU-07 的任务目录自动当作 PPU-13 本案例目录。此任务只在目标容器写私有源码，不在 PPU-13 Host 上新建持久脚本、日志或大体积中转产物；命令与摘要留在本地案例记录。

## 方案与变更命令（执行前冻结）

同一基础镜像已在 PPU-13，故无需将约 68GB 的基础镜像另行传输。PPU-07 当前容器的 `docker diff` 显示有效推理差异集中在 `/workspace/FlagGems`、`/workspace/vllm-plugin-FL`、`/workspace/FlagGems-vllm` 和小型 `/tmp/flaggems_enable_oplist.txt`；`/workspace/vllm` 只有 Git index 变化、工作树干净。运行缓存 `/root/.flaggems`、usage stats 不迁移，以免跨 Host 携带过时编译缓存。三个源码工作树将完整复制（包括既有未提交改动与 `.git`），而非仅复制四个先前优化文件；当前 Plugin/FlagGems-vllm revision 与基础镜像可能不同。

预定新容器名：`minimaxM3-latest-20260924`（Host 不同，PPU-13 上无重名）。创建命令：

```bash
docker create --name minimaxM3-latest-20260924 -it --init --privileged \
  --network host --ipc host --security-opt label=disable \
  --device=/dev/infiniband:/dev/infiniband \
  --device=/dev/alixpu_ctl:/dev/alixpu_ctl --device=/dev/alixpu:/dev/alixpu \
  --ulimit memlock=-1:-1 --ulimit stack=67108864:67108864 \
  --mount type=bind,src=/mnt,dst=/mnt \
  sha256:41d96df0b7b416e1e887fe1c4dab21dfc12819875524993f90213fe29214f541
docker start minimaxM3-latest-20260924
```

创建后重新 inspect 镜像 ID、挂载、设备、网络/IPC、ulimit 与启动进程；若不符，停止复制。目标容器内部先将三个基础源码目录精确改名为各自 `.preclone-20261015` 备份，确保无同名备份；再逐个使用管道 `ssh PPU-07 'docker cp minimaxM3-latest-20260924:/workspace/<repo> -' | ssh PPU-13 'docker cp - minimaxM3-latest-20260924:/workspace'` 流式复制 `FlagGems`、`vllm-plugin-FL`、`FlagGems-vllm`。复制前后均不触碰共享 `/mnt`。最后以相同方式复制 `/tmp/flaggems_enable_oplist.txt`。每次流使用 `pipefail`，失败时停止，不把不完整容器称作完成。

目标镜像自身已有 `/tmp/flaggems_enable_oplist.txt`（SHA256 `f0e95138d11bbe99b5fdcfdfcd17bf299a52bf0ec431e672fd4fd48ddf2b43ba`），而来源当前文件 SHA256 为 `4ae6085852212f5c37a2377303ac3751978ddd7f8e6772ef452f846b41adf860`。复制该文件之前，先在新容器精确改名为 `/tmp/flaggems_enable_oplist.txt.preclone-20261015`，避免丢失镜像原版；随后用同一 `docker cp` 流复制当前文件。

验证：三个 Git HEAD 和 `status --porcelain` 与来源逐一相同；关键四文件 SHA 保持 op-013 的迁移结果；目标 Python `flag_gems`、`vllm_fl`、`flaggems_vllm` 从 `/workspace` 导入，MoE 导出解析为 `_thead.fused.fused_moe`；Plugin T-Head blacklist 为 `[conv3d,cudnn_convolution]`；目标 `docker top` 仅启动脚本/init/bash，无 vLLM 服务。保留 `.preclone-20261015` 三目录以便回退，未经授权不删除。

结论边界：这形成可运行的同镜像/同推理源码容器，不等于完整 Docker writable layer 的逐字节快照，不携带编译缓存、历史日志或源 Host PID。跨 Host 的 graph、最小回归、198 题 gate 和性能需分别重新执行，旧容器结果不迁移。

## 执行与验证结果（2026-10-15）

- PPU-13 容器 `minimaxM3-latest-20260924` 已创建并运行，ID `97cffbb2cec03a0df9fa30cdb3c780ea5737f2352d48afd9488859ec8f8fa456`；基础镜像 ID 与来源相同。机器可读的两份 Docker Mounts 规范化比较为 `passed`：均只有 `/mnt` → `/mnt`、RW、rprivate。设备节点、host network/IPC、privileged、init、ulimit、TTY/stdin 与来源一致。最终 `docker top` 只有 init/bash，没有 `vllm serve`；该镜像无 Docker Health 字段，因此不宣称服务 health passed。
- 三个源码目录先备份为各自 `.preclone-20261015`，再分别通过 `docker cp` 流式复制；`/tmp/flaggems_enable_oplist.txt` 原版备份为 `.preclone-20261015` 后复制。三个备份仓库的 HEAD 可读，未删除。未向共享 `/mnt` 写代码或中转包，也未停止/更改 PPU-13 其他容器。
- `FlagGems` 来源/目标 HEAD 均为 `3c6f7537d2d5d3aa680c55bbee5c70f2100c5b85`，tracked binary diff SHA256 均为 `4d36e3598100d39c07fe71dde43322a6ce7274a6b510a42ad548254055dc8f78`，`git status --short` 同为两修改一新增。Plugin 来源/目标 HEAD 均为 `cafe6363c8c3de5ba4693b91643089c17b3ab87c`，diff SHA256 均为 `3c5ea3ec3a4826c92038754c4866b055826eeed277cb556aff2595d1815db607`，status 同为一个修改及四个原有 `.orig`。FlagGems-vllm 来源/目标 HEAD 均为 `1f9ac0e0caf3c32111f6be44c8e4d2fef2359546`，diff SHA256 均为 `1acdb40e31b333fd29328574160265fa6051c5b6e7498e7a38d65f418a38a764`，status 同为两个原有修改。三仓库 `git diff --check` 通过。
- PPU-13 目标 `sql.py`、T-Head fused `__init__.py`、`fused_moe.py`、Plugin `thead.yaml` SHA256 依次为 `c70511b6afa820e0cc5bd469fe22e5f51b8f8ca176eaef57af13183ce1426db3`、`fae31da546fd72fb937a9a79033e3dae09ac730446d90eeeb08367da1ace9f9d`、`dcbfa3fd2011711fcd05a1045a3d918907f87c6b11039ee69a537b53c2f9e9ed`、`2b80df497c6200f190570d9ee3400c3935b758ca6fe2fa3993adc25eacd690e4`，与 PPU-07 一致；oplist SHA256 `4ae6085852212f5c37a2377303ac3751978ddd7f8e6772ef452f846b41adf860` 一致。
- PPU-13 的 `flag_gems`、`vllm_fl`、`flaggems_vllm` 均从目标容器 `/workspace` 导入；MoE 导出解析为 `_thead.fused.fused_moe`，T-Head blacklist API 返回 `['conv3d', 'cudnn_convolution']`。这是导入/配置证明，不是 graph 或运行中算子命中证明。
- 正式判断：`container_started_and_inference_source_replicated`；`model_service=not_started`，`accuracy=not_run`，`performance=not_run`，`graph_capture=not_run`。后续如需启动服务，在 PPU-13 单独冻结端口、TP16 参数和精度/性能契约；不得沿用 PPU-07 实例 gate。

后续验证：用户在该容器启动8024服务后，2026-10-15的[accformal-005](accformal-005-ppu13-gpqa-c64-60k.md)对当前完整源码组合执行198题GPQA/C64/60K，strict-match183/198=92.42%≥88%，当前服务gate签发及复验通过。该精度属于PPU-13当前启动配置，不能回填为本环境复制步骤执行时已通过，也不构成端到端性能验收。
