# env-001-source-facts-and-replication 源环境事实与独立复刻

- 状态：`complete`
- 分类：`framework`
- 目标场景：环境门禁，映射后续全部场景
- 目标阶段：`mixed` 前置环境

## 优化方向与瓶颈依据

当前 PPU-07 源容器使用 MiniMax-M3 专用适配镜像。`docker diff` 仅显示 FlagGems/Triton 运行时缓存与使用统计，未观察到 `/workspace`、`/usr/local`、`/opt`、`/etc` 或 `/mnt` 中的代码/配置变化。

## 优化内容与适用边界

直接复用精确镜像 ID `sha256:41d96df0...`，以相同 `/mnt` bind mount 和容器运行参数创建 `minimaxM3-opt-20260921`。源/优化容器 Plugin、FlagGems-vllm、FlagGems revision 及工作区状态的 diff 为空。

## 正确性与路径命中

`image_lineage=verified`，`mount_parity=passed`，优化容器的导入路径与源容器一致。源服务已在用户明确授权后停止且源容器保持运行；独立优化服务正在 `8023` 启动，graph smoke/C8 尚未执行。

## 性能效果

环境实验，无性能加速声明。

## 决定、风险与回退

环境门禁保留。与源容器共享 `/mnt`，任何挂载内源码不得直接改写。源服务停止证据位于 `transitions/release-source-service-20260921-02/`；恢复时使用已归档的原启动脚本和 `8013`，不得与优化服务争抢设备。

## 外部证据

`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/`。
