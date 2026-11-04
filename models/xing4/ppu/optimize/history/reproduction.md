# xing4 / PPU 优化复现入口

本文件保留仍有效的复现信息，替代案例目录中绑定旧 PID、容器状态和一次性安装步骤的大量 Shell 包装脚本。执行前必须重新核对当前优化容器、源码 revision、挂载、设备和端口，不能直接沿用历史运行状态。

## 实现

- FlagGems 基线 revision：`5941cd2225798bdfa611626f34e459c42cdf2904`
- 目标文件：`src/flag_gems/fused/flash_mla_with_kvcache.py`
- 基线 SHA-256：`b56bb7f1ff1a8ee27717b64f866433eb9ce81bfb34b546384cdcfe0a36d9b85e`
- 最终候选源码 SHA-256：`45eaf0e7342dcf9bfd0987dacb11dea6572d948b2334805639e50840b7d450c9`
- 最终候选测试 SHA-256：`cda6ae24958760777c19f95abb9699111bf7c77512780891bf2738439cf6e40c`
- 最终补丁 SHA-256：`7f2789a28620a103d30a9013d64a14426d9682ff1a418970bc942cf59e4a356d`
- PR 设计摘要：[patch-mla-tile16-pr.md](patch-mla-tile16-pr.md)；完整历史 patch 位于目标环境
  `/workspace/e2e-artifacts/patches/mla-tile16/`，实际实现以源码 revision 和 SHA 为准。
- 选择策略：根据 `SQ/H_rank/DQK/DV/page/dtype/stride` 自动分派，不使用实验环境变量。回退为反向应用补丁并以相同服务配置重启。

应用补丁前保存工作区状态并验证目标文件 SHA；对 revision 或 SHA 不匹配的源码不得强行应用。

## 服务可比条件

候选与回退固定：BF16、TP4、graph、`max_model_len=100000`、`gpu_memory_utilization=0.8`、prefix cache、`max_num_batched_tokens=8192`、served model `teleai-flagos`。设备和端口按当前新优化容器重新解析，不依赖历史 PID 或容器 ID。

每次启动后验证 `/v1/models`、health、进程环境不含旧实验变量、实际源码 SHA 和小 head 编译配置，并执行固定 C8 sanity。

2026-09-06 的设备映射记录显示重建容器暴露全部 16 张 PPU。2026-09-07 复测时发现受保护的
`xingchen4-opt` 服务占用物理 PPU1–4，因此最终候选改用同 NUMA 且空闲的 PPU8–11；执行前必须
重新检查占用，不能固定复用任一历史编号。详见 [PR 重构实验](20260907-mla-pr-refactor.md)。

历史容器启动脚本已外置，不作为当前模型目录的执行入口。后续复现应使用公共控制工具重新生成启动命令，
显式提供模型路径、served name、端口、设备、产物根目录和唯一服务标签，并按目标设置 TP 等参数。
启动逻辑必须检查已有服务与端口，只在 `/health` 和 `/v1/models` 的目标模型就绪后报告 Ready；
超时或子进程提前退出时保留外部日志供排障，并在重试前重新解析 PID 与服务状态。

编译缓存仍位于 `ARTIFACT_ROOT/cache/`。使用新目录或复用缓存应在实验计划中明确，启动器不会清理已有缓存，也不证明缓存冷热或资源隔离门禁已经通过。

启动器显式设置 `MAX_NUM_BATCHED_TOKENS`（默认 8192）及 `PREFIX_CACHING`（默认 `1`；`0` 关闭），避免这两个已记录的可比条件随引擎默认值漂移。任何覆盖都要进入实验变量或新基线。

## 当前工具入口

模型目录不再保存案例 wrapper、启动脚本、微基准脚本或结果收集脚本。新的服务控制、sanity、性能测量、
结果校验和 profiling 应使用项目公共的 `scripts/`、`evaluation/`、`test/` 或 `benchmarks/`；只有经过
参数化并确认可跨案例复用的工具才进入这些目录。公共配置及比较命令见
[性能工具](../../../../../evaluation/performance/README.md)。

历史 wrapper 的一轮预热、两轮测量与逐轮 seed 只是历史口径；固定轮数不证明稳态。新正式任务应按
预冻结契约直接配置公共计划中的预热判据、重复次数和主/守护指标，并以新的输出目录执行可比的
baseline/candidate/revert。原始结果保存在目标环境，紧凑索引见
[performance-measurements.json](../performance-measurements.json)。
