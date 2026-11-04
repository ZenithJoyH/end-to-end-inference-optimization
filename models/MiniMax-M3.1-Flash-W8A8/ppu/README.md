# MiniMax-M3.1 Flash-W8A8 / PPU

本模型按 MiniMax-M3.1 Flash W8A8 统一归档。10 月 8 日 TP16 和 10 月 10 日 TP8 案例使用 09-29 preview 权重，10 月 19 日的三项精度评测使用 10-19 Flash 权重。比较结果时以各案例记录的权重、拓扑和服务为准。

- [20261019 Flash三项精度](20261019-flash-three-task-accuracy/README.md)：PPU-07、TP8、10/19Flash权重；GPQA198/Math500500/ERQA400精度完成：86.36% / 92.20% / 63.75%，monitor已暂停，与preview历史分开。

- [20261020 最新栈前8卡精度](20261020-latest-stack-tp8-0-7-accuracy/README.md)：最新容器 review-001 代码组合，物理0–7、8045；先设备/graph/模型回归，再单次串行三项全量，结果待生成。

<!-- case-navigation:start -->
## 完整案例入口

- 20261008-minimax-m31-w8a8-ppu-e2e：[baseline](20261008-minimax-m31-w8a8-ppu-e2e/baseline/README.md) · [optimize](20261008-minimax-m31-w8a8-ppu-e2e/optimize/README.md) · [acceptance](20261008-minimax-m31-w8a8-ppu-e2e/acceptance/README.md)
- 20261010-minimax-m31-w8a8-ppu-tp8-e2e：[baseline](20261010-minimax-m31-w8a8-ppu-tp8-e2e/baseline/README.md) · [optimize](20261010-minimax-m31-w8a8-ppu-tp8-e2e/optimize/README.md) · [acceptance](20261010-minimax-m31-w8a8-ppu-tp8-e2e/acceptance/README.md)
- 20261019-flash-three-task-accuracy：[baseline](20261019-flash-three-task-accuracy/baseline/README.md) · [optimize](20261019-flash-three-task-accuracy/optimize/README.md) · [acceptance](20261019-flash-three-task-accuracy/acceptance/README.md)
- 20261020-latest-stack-migration：[baseline](20261020-latest-stack-migration/baseline/README.md) · [optimize](20261020-latest-stack-migration/optimize/README.md) · [acceptance](20261020-latest-stack-migration/acceptance/README.md)
- 20261020-latest-stack-tp8-0-7-accuracy：[baseline](20261020-latest-stack-tp8-0-7-accuracy/baseline/README.md) · [optimize](20261020-latest-stack-tp8-0-7-accuracy/optimize/README.md) · [acceptance](20261020-latest-stack-tp8-0-7-accuracy/acceptance/README.md)
- 20261021-dot-k16-tp8-accuracy：[baseline](20261021-dot-k16-tp8-accuracy/baseline/README.md) · [optimize](20261021-dot-k16-tp8-accuracy/optimize/README.md) · [acceptance](20261021-dot-k16-tp8-accuracy/acceptance/README.md)
- 20261021-flagtree071-issue1407：[baseline](20261021-flagtree071-issue1407/baseline/README.md) · [optimize](20261021-flagtree071-issue1407/optimize/README.md) · [acceptance](20261021-flagtree071-issue1407/acceptance/README.md)
- 20261021-minimax-m31-topk-sigmoid-integration：[baseline](20261021-minimax-m31-topk-sigmoid-integration/baseline/README.md) · [optimize](20261021-minimax-m31-topk-sigmoid-integration/optimize/README.md) · [acceptance](20261021-minimax-m31-topk-sigmoid-integration/acceptance/README.md)
- 20261021-no-topk-patch-tp8-accuracy：[baseline](20261021-no-topk-patch-tp8-accuracy/baseline/README.md) · [optimize](20261021-no-topk-patch-tp8-accuracy/optimize/README.md) · [acceptance](20261021-no-topk-patch-tp8-accuracy/acceptance/README.md)
- 20261021-topk-sigmoid-tp8-accuracy：[baseline](20261021-topk-sigmoid-tp8-accuracy/baseline/README.md) · [optimize](20261021-topk-sigmoid-tp8-accuracy/optimize/README.md) · [acceptance](20261021-topk-sigmoid-tp8-accuracy/acceptance/README.md)
- 20261021-topk-unpatch-removal：[baseline](20261021-topk-unpatch-removal/baseline/README.md) · [optimize](20261021-topk-unpatch-removal/optimize/README.md) · [acceptance](20261021-topk-unpatch-removal/acceptance/README.md)
- 20261021-topk-unpatch-validation：[baseline](20261021-topk-unpatch-validation/baseline/README.md) · [optimize](20261021-topk-unpatch-validation/optimize/README.md) · [acceptance](20261021-topk-unpatch-validation/acceptance/README.md)
- 20261022-old-container-c64-accuracy：[baseline](20261022-old-container-c64-accuracy/baseline/README.md) · [optimize](20261022-old-container-c64-accuracy/optimize/README.md) · [acceptance](20261022-old-container-c64-accuracy/acceptance/README.md)
<!-- case-navigation:end -->

早期 TP16、TP8 的共享溯源字段见[历史账本迁移索引](optimize/README.md)。
