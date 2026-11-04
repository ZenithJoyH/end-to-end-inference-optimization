# HY4-preview PPU-03 初步性能探索

已完成三阶段baseline和一次仅改CLI参数的targeted试验：2048→512。512候选没有达到预设Mixed吞吐收益，TPOT/ITL守护未通过，已决定恢复原2048；原8010服务已恢复并验证。Plugin和两个gems-opt的生产源码没有变化，没有保留性能改动。

| 实验 | 方向/变量 | 场景/阶段 | 结果 | 正确性 | 决定 |
|---|---|---|---|---|---|
| [env-001](env-001.md) | 独立快照、同挂载环境及原始2048 baseline | 三个P1K父目标缩减Prefill/Decode/Mixed C8/N8 | Prefill输入94.61token/s；Mixed输出10.18token/s；Decode基线波动70.75% | 9smoke/C8、16rank3组2replay、2×2689分页均通过 | 保留基线事实及所有不稳定证据 |
| [fw-001](fw-001.md) | framework，token预算2048→512 | 同三个缩减case | Prefill输入91.34token/s；Mixed输出9.85token/s，TPOT380.59ms | 同运行护栏全部通过；完整GPQA未跑 | 不保留；运行回退原2048 |

plan-002：图覆盖范围对齐不自动等于稳态吞吐收益；先考虑代表性Prefill/Mixed profiling，取得设备/CPU/调度及rank证据后再挑优化点。扩大graph桶需先评估显存/KV/编译成本，深度算子替换无热点证据且两个Gems版本固定，均暂缓。当前不自动启动下一项试验。

维护比较器回执incomplete（按预冻结无收益/守护失败条件停止，独立revert性能未跑），并且原Decode测量不稳；本轮不发布正式加速比/性能通过或87%精度结论。四个正式D1K/C64/N128场景均not_run。原生数据、SHA、完整数值、回退及归档状态见state.yml和各单点文档。

原8010当前服务身份`e6562463824a7aebecb1d655b8efdcfe1d2c27321329cff33a0a1f4b36304805`，C8 9/9、三阶段16rank各2replay、2×2689token分页通过，实际prefix hit **2624token**，16观察器退出。生产源码及两个gems-opt与基线相同。完整性能证据523文件已按SHA镜像保留到原容器相同绝对根，manifest SHA `b68a640938ac85228969d22dd1662066f4a445d69ddf7e883d1a25d9cac8e1e1`；源恢复JSON证据另存`source-recovery/`。

<!-- e2e:summary:start -->

- 案例：20261020-hy4-preview-ppu03-initial-perf
- 当前状态：completed_bounded_initial_probe_no_optimization_retained
- 当前候选：historical env0302048;512rejected
- 下一步：Historical oldFGV case complete; current env031 budget8192 task is separate case 20261020-hy4-preview-ppu03-batched8192

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| env-001 | incomplete steady-state Decode; stable Prefill/Mixed baseline and source identity verified | — | [env-001.md](env-001.md) |
| fw-001 | original8010 runtime restored and verified;512not retained | scout-p1024-d128-c8-n8 | [fw-001.md](fw-001.md) |
| fw-002 | linked_only_not_an_old_anchor_measurement | — | [fw-002.md](fw-002.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| scout-p128-d128-c8-n8 | baseline | output_throughput | 33.19921444475973 | token/s | observed-unsteady baseline |
| scout-p128-d128-c8-n8 | baseline | mean_ttft_ms | 16611.169643118046 | ms | observed-unsteady baseline |
| scout-p128-d128-c8-n8 | baseline | mean_tpot_ms | 146.17504272839113 | ms | observed-unsteady baseline |
| scout-p128-d128-c8-n8 | baseline | mean_e2el_ms | 35175.40006962372 | ms | observed-unsteady baseline |
| scout-p1024-d128-c8-n8 | baseline | output_throughput | 10.177078522622795 | token/s | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | baseline | mean_ttft_ms | 59794.034089369234 | ms | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | baseline | mean_tpot_ms | 320.0689241863919 | ms | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | baseline | mean_e2el_ms | 100442.787461041 | ms | reduced milestone performance_only |
| scout-p1024-d1-c8-n8 | baseline | output_throughput | 0.09239060912793885 | token/s | reduced milestone performance_only |
| scout-p1024-d1-c8-n8 | baseline | mean_ttft_ms | 52869.71296131378 | ms | reduced milestone performance_only |
| scout-p1024-d1-c8-n8 | baseline | mean_e2el_ms | 52869.712739950046 | ms | reduced milestone performance_only |
| scout-p128-d128-c8-n8 | candidate | output_throughput | 44.39215919356564 | token/s | reduced milestone performance_only |
| scout-p128-d128-c8-n8 | candidate | mean_ttft_ms | 7819.030101003591 | ms | reduced milestone performance_only |
| scout-p128-d128-c8-n8 | candidate | mean_tpot_ms | 119.22645891556428 | ms | reduced milestone performance_only |
| scout-p128-d128-c8-n8 | candidate | mean_e2el_ms | 22960.790383280255 | ms | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | candidate | output_throughput | 9.847526932655175 | token/s | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | candidate | mean_ttft_ms | 54953.20559974061 | ms | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | candidate | mean_tpot_ms | 380.59367417581524 | ms | reduced milestone performance_only |
| scout-p1024-d128-c8-n8 | candidate | mean_e2el_ms | 103288.60222006915 | ms | reduced milestone performance_only |
| scout-p1024-d1-c8-n8 | candidate | output_throughput | 0.08919915060868933 | token/s | reduced milestone performance_only |
| scout-p1024-d1-c8-n8 | candidate | mean_ttft_ms | 50538.74874400208 | ms | reduced milestone performance_only |
| scout-p1024-d1-c8-n8 | candidate | mean_e2el_ms | 50538.7485055835 | ms | reduced milestone performance_only |

<!-- e2e:summary:end -->
