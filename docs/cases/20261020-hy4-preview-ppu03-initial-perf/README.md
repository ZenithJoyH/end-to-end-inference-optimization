# HY4-preview / PPU-03 初步性能探索

SOP0.40；performance_only，证据等级observation，正式精度未跑、完整性能比较incomplete。已完成原2048基线和一项CLI2048→512候选的三阶段缩减测试；未保留候选，原8010/2048/prefix cache已恢复。没有生产源码、两个Gems、权重或tokenizer变更。

[模型结果](../../../models/Hy4-preview/ppu/20261020-hy4-preview-ppu03-initial-perf/README.md) / [fw-001完整契约与数据](../../../models/Hy4-preview/ppu/20261020-hy4-preview-ppu03-initial-perf/optimize/fw-001.md)。

| 缩减C8/N8场景 | 原2048 | 512候选 |
|---|---:|---:|
| Prefill P1024/D1输入吞吐 | 94.61token/s | 91.34token/s |
| Mixed P1024/D128输出吞吐 | 10.18token/s | 9.85token/s |
| Mixed平均TTFT | 59.79s | 54.95s |
| Mixed平均TPOT | 320.07ms | 380.59ms |

首token较早没有变成吞吐净收益，TPOT/ITL未满足冻结5%守护，因此按预设停止条件回退；不再追加revert性能轮，维护比较器保留incomplete，不给因果加速比或形式验收。Decode基线两测量21.46/44.94token/s、spread70.75%，慢首轮完整保留；逐token可见共享早期30.83s停顿，精确设备/kernel原因尚未确认。候选Decode两测量44.47/44.32token/s较稳，但不能据此消除原参考缺口。

源容器hy4-preview，独立容器hy4-preview-perf-20261020-01，TP16 PPU-ZW810E。105GB私有有效状态保存到不可变snapshot，Parent=image核验通过；同/mnt Source/Destination/RW/rprivate。首次显式BindOptions不匹配被公共门禁拒绝，未进行推理；按源相同-v形式重新复刻后mount_parity passed。源模型占满16卡，用户明确批准暂时停止其精确进程树；源/优化容器均保留，当前仅原服务占用模型资源。

两Gems固定FGV46387d7f96050204c1b932f35680a3ea03896fa6、FG3ba1d1d99010de56d12088992f8b0da3444d90ca，clean/摘要一致；Plugin官方8b2033e加env030补丁，614文件、包SHA67ea7721…不变。vLLM轮包0.24.0+empty保持只读，原模型和tokenizer七项内容身份已重验相同。三个性能计划显式prefix cache关闭，Prefill2warmup+2measured、Decode/Mixed4warmup+2measured；原2warmupDecode失败21.6%证据保留，新合同先冻结再测，阈值未放宽。所有正式四场景D1K/C64/N128均not_run。

外部根/workspace/.hy4-preview-migration-20261018-01/perf-20261020-01，owner0/700，启动前空闲约13.57TB，实际私有安装隔离；完整命令、原生结果/失败/快慢轮、provenance和比较回执保留。523个性能证据文件按SHA非破坏镜像到原容器相同绝对路径；源恢复JSON另存source-recovery/，当前C8、三阶段16rank2replay、2×2689token分页通过且实际prefix hit2624token。最终核验SHA8946c53967a269b870b236648ecda153921344018b7c26e69c072ec85c7ad823。

plan-002：下一步先做代表性Prefill/Mixed profiling，核验设备/CPU/rank覆盖并确认热点，再选框架/既有算子方向。扩大graph桶需要显存/KV/编译成本证明；不从这次结果猜测具体kernel或自动修改两个Gems。当前没有启动第二项优化、GPQA或后续监控。
