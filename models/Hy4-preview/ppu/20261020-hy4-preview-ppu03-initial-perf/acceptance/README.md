# HY4-preview PPU-03 验收状态

状态incomplete。本轮只是用户授权的初步performance_only探索，不构成正式精度/性能验收。没有保留优化，512候选按原先无收益/守护失败条件回退；原8010服务已恢复并验证。

- GPQA未启动，87%阈值未更改，也没有当前完整score/gate。
- 四个原始正式P1K/P4K/P16K/P32K、D1K/C64/N128均not_run。
- 原Decode基线测量波动70.75%，慢轮完整保留。
- 未运行独立revert性能轮，维护比较结果incomplete；运行恢复和graph/分页证明不是性能或精度gate。

初测数值和边界见[优化账本](../optimize/README.md)，最终恢复身份及证据位置以state.yml和optimize/state.yml为准。

原8010当前服务身份`e6562463824a7aebecb1d655b8efdcfe1d2c27321329cff33a0a1f4b36304805`，C8 9/9、三阶段16rank各2replay、2×2689token分页通过，实际prefix hit **2624token**，16观察器退出。生产源码及两个gems-opt与基线相同。完整性能证据523文件已按SHA镜像保留到原容器相同绝对根，manifest SHA `b68a640938ac85228969d22dd1662066f4a445d69ddf7e883d1a25d9cac8e1e1`；源恢复JSON证据另存`source-recovery/`。

<!-- e2e:summary:start -->

- 案例：20261020-hy4-preview-ppu03-initial-perf
- 当前状态：incomplete_no_optimization_retained
- 当前候选：original env0302048/prefix enabled, source8010 ready
- 下一步：No formal acceptance; new explicit cycle needed for profiling or formal4scenario/accuracy work

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->
