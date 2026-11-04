# HY4-preview / PPU-03 初步性能探索

已完成原2048基线和仅把token预算改为512的一次三阶段缩减性能试验。候选没有带来所要求的Mixed收益，TPOT/ITL守护未通过，不予保留；原8010/2048/prefix cache开启的服务已恢复并验证。三个推理仓库源码和两个gems-opt均未变更。

| 初测 C8/N8 | 原2048 | 512候选 |
|---|---:|---:|
| Prefill P1024/D1输入吞吐 | 94.61 token/s | 91.34 token/s |
| Mixed P1024/D128输出吞吐 | 10.18 token/s | 9.85 token/s |
| Mixed平均TPOT | 320.07 ms | 380.59 ms |

Decode原基线有大幅波动，所有慢轮保留；完整三角色比较incomplete，不宣称整体加速或正式验收通过。GPQA没有启动，四个正式场景未测。

- [Baseline](baseline/README.md)
- [优化账本](optimize/README.md) / [fw-001完整结果](optimize/fw-001.md)
- [验收状态](acceptance/README.md)

原8010当前服务身份`e6562463824a7aebecb1d655b8efdcfe1d2c27321329cff33a0a1f4b36304805`，C8 9/9、三阶段16rank各2replay、2×2689token分页通过，实际prefix hit **2624token**，16观察器退出。生产源码及两个gems-opt与基线相同。完整性能证据523文件已按SHA镜像保留到原容器相同绝对根，manifest SHA `b68a640938ac85228969d22dd1662066f4a445d69ddf7e883d1a25d9cac8e1e1`；源恢复JSON证据另存`source-recovery/`。

本页为旧FGV46387d7f下512试验的历史案例。新版FGV45e后的8192试验和当前原服务身份独立归档，见[新锚点8192案例](../20261020-hy4-preview-ppu03-batched8192/README.md)，不复用本页旧service ID作为当前运行事实。
