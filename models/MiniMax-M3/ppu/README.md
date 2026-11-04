# MiniMax-M3 / PPU 端到端优化

- 案例：[20260921-minimax-m3-ppu-e2e](../../../docs/cases/20260921-minimax-m3-ppu-e2e/README.md)
- PPU-07 历史优化状态见下方长期入口；已保留代码于2026-10-15复制进PPU-13同镜像容器。当日旧容器8024服务的全量GPQA 198题/C64/60K为 strict-match 183/198=92.42%≥88%，当时正式gate签发及复验通过；性能未测。该历史结果不绑定2026-10-17的新容器或新Plugin分支。
- PPU-13 新案例：[20261015-minimax-m3-ppu13-clone](20261015-minimax-m3-ppu13-clone/README.md)
- 2026-10-17 当前新容器 `minimaxM3`：[指定Plugin分支验证](20261017-minimax-m3-ppu13-plugin-support/README.md)。fw-014路由dtype/边界与worker时机收敛后，fw-015移除新增测试和thead.yaml修改，fw-016按原参数重启并独立通过C1/C8 10/10、16rank capture及FULL replay。无黑名单启动约16分钟，Conv3d慢调优现场保留；当前8024运行，未修复/回退。accformal-006全量GPQA于19:27完成（198/C64/60K/88%）：179/198=90.40%，gate复验通过，14条60K截断单独记录，heartbeat暂停；性能未测，旧92.42%不适用。
- 长期入口：[baseline](baseline/README.md) / [optimize](optimize/README.md) / [acceptance](acceptance/README.md)

<!-- case-navigation:start -->
## 完整案例入口

- 20261015-minimax-m3-ppu13-clone：[baseline](20261015-minimax-m3-ppu13-clone/baseline/README.md) · [optimize](20261015-minimax-m3-ppu13-clone/optimize/README.md) · [acceptance](20261015-minimax-m3-ppu13-clone/acceptance/README.md)
- 20261017-minimax-m3-ppu13-plugin-support：[baseline](20261017-minimax-m3-ppu13-plugin-support/baseline/README.md) · [optimize](20261017-minimax-m3-ppu13-plugin-support/optimize/README.md) · [acceptance](20261017-minimax-m3-ppu13-plugin-support/acceptance/README.md)
- legacy-platform-layout：[baseline](./baseline/README.md) · [optimize](./optimize/README.md) · [acceptance](./acceptance/README.md)
<!-- case-navigation:end -->
