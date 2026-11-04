# MiniMax-M3.1-Flash-W8A8

本模型按 MiniMax-M3.1 Flash W8A8 统一归档。10 月 8 日 TP16 和 10 月 10 日 TP8 案例使用 09-29 preview 权重，10 月 19 日的三项精度评测使用 10-19 Flash 权重。比较结果时以各案例记录的权重、拓扑和服务为准。

<!-- model-navigation:start -->
## 案例导航（2026-11-02 本地记录）

每个案例独立绑定 Host、拓扑与 baseline；下列状态来自本地账本，不表示已重新核验服务。

| 案例 | 优化状态 | 三阶段入口 |
|---|---|---|
| 20261008-minimax-m31-w8a8-ppu-e2e | user-paused-for-manual-end-to-end-performance | [baseline](ppu/20261008-minimax-m31-w8a8-ppu-e2e/baseline/README.md) · [optimize](ppu/20261008-minimax-m31-w8a8-ppu-e2e/optimize/README.md) · [acceptance](ppu/20261008-minimax-m31-w8a8-ppu-e2e/acceptance/README.md) |
| 20261010-minimax-m31-w8a8-ppu-tp8-e2e | FG-upgraded-minimal-passed-new-formal-pending | [baseline](ppu/20261010-minimax-m31-w8a8-ppu-tp8-e2e/baseline/README.md) · [optimize](ppu/20261010-minimax-m31-w8a8-ppu-tp8-e2e/optimize/README.md) · [acceptance](ppu/20261010-minimax-m31-w8a8-ppu-tp8-e2e/acceptance/README.md) |
| 20261019-flash-three-task-accuracy | completed | [baseline](ppu/20261019-flash-three-task-accuracy/baseline/README.md) · [optimize](ppu/20261019-flash-three-task-accuracy/optimize/README.md) · [acceptance](ppu/20261019-flash-three-task-accuracy/acceptance/README.md) |
| 20261020-latest-stack-migration | pr_scope_refined_cpu_verified_device_model_pending | [baseline](ppu/20261020-latest-stack-migration/baseline/README.md) · [optimize](ppu/20261020-latest-stack-migration/optimize/README.md) · [acceptance](ppu/20261020-latest-stack-migration/acceptance/README.md) |
| 20261020-latest-stack-tp8-0-7-accuracy | all_three_native_completed_verified | [baseline](ppu/20261020-latest-stack-tp8-0-7-accuracy/baseline/README.md) · [optimize](ppu/20261020-latest-stack-tp8-0-7-accuracy/optimize/README.md) · [acceptance](ppu/20261020-latest-stack-tp8-0-7-accuracy/acceptance/README.md) |
| 20261021-dot-k16-tp8-accuracy | resume02_all_three_native_completed_verified | [baseline](ppu/20261021-dot-k16-tp8-accuracy/baseline/README.md) · [optimize](ppu/20261021-dot-k16-tp8-accuracy/optimize/README.md) · [acceptance](ppu/20261021-dot-k16-tp8-accuracy/acceptance/README.md) |
| 20261021-flagtree071-issue1407 | default_compiler_upgraded_service_ready | [baseline](ppu/20261021-flagtree071-issue1407/baseline/README.md) · [optimize](ppu/20261021-flagtree071-issue1407/optimize/README.md) · [acceptance](ppu/20261021-flagtree071-issue1407/acceptance/README.md) |
| 20261021-minimax-m31-topk-sigmoid-integration | op-005-implemented-CPU-validated-awaiting-free-device | [baseline](ppu/20261021-minimax-m31-topk-sigmoid-integration/baseline/README.md) · [optimize](ppu/20261021-minimax-m31-topk-sigmoid-integration/optimize/README.md) · [acceptance](ppu/20261021-minimax-m31-topk-sigmoid-integration/acceptance/README.md) |
| 20261021-no-topk-patch-tp8-accuracy | all_three_native_completed_verified | [baseline](ppu/20261021-no-topk-patch-tp8-accuracy/baseline/README.md) · [optimize](ppu/20261021-no-topk-patch-tp8-accuracy/optimize/README.md) · [acceptance](ppu/20261021-no-topk-patch-tp8-accuracy/acceptance/README.md) |
| 20261021-topk-sigmoid-tp8-accuracy | latest-user-restarted-service-single-sample-diagnosed | [baseline](ppu/20261021-topk-sigmoid-tp8-accuracy/baseline/README.md) · [optimize](ppu/20261021-topk-sigmoid-tp8-accuracy/optimize/README.md) · [acceptance](ppu/20261021-topk-sigmoid-tp8-accuracy/acceptance/README.md) |
| 20261021-topk-unpatch-removal | topk_patch_removed_verified | [baseline](ppu/20261021-topk-unpatch-removal/baseline/README.md) · [optimize](ppu/20261021-topk-unpatch-removal/optimize/README.md) · [acceptance](ppu/20261021-topk-unpatch-removal/acceptance/README.md) |
| 20261021-topk-unpatch-validation | checks_completed_patch_retained_pending_model_accuracy | [baseline](ppu/20261021-topk-unpatch-validation/baseline/README.md) · [optimize](ppu/20261021-topk-unpatch-validation/optimize/README.md) · [acceptance](ppu/20261021-topk-unpatch-validation/acceptance/README.md) |
| 20261022-old-container-c64-accuracy | old-container-c64-all-three-complete-verified | [baseline](ppu/20261022-old-container-c64-accuracy/baseline/README.md) · [optimize](ppu/20261022-old-container-c64-accuracy/optimize/README.md) · [acceptance](ppu/20261022-old-container-c64-accuracy/acceptance/README.md) |
<!-- model-navigation:end -->

## 对应的案例文档

- [MiniMax-M3.1 Flash1019 / PPU-07 三项精度](../../docs/cases/20261019-minimax-m31-flash-ppu-tp8-accuracy/README.md)
- [MiniMax-M3.1 Flash / PPU-07 最新栈迁移](../../docs/cases/20261020-minimax-m31-latest-stack-migration/README.md)
- [MiniMax-M3.1 Flash 最新栈 / PPU-07 前8卡全量精度](../../docs/cases/20261020-minimax-m31-latest-stack-tp8-0-7-accuracy/README.md)
- [MiniMax Flash1019 编译器dot-K16精度复测](../../docs/cases/20261021-minimax-m31-dot-k16-tp8-accuracy/README.md)
- [MiniMax Flash1019 移除 top-k patch 精度复测](../../docs/cases/20261021-minimax-m31-no-topk-patch-tp8-accuracy/README.md)
- [MiniMax-M3.1 算子接入与适配整理](../../docs/cases/20261021-minimax-m31-topk-sigmoid-integration/README.md)
- [MiniMax Flash 新 topk-sigmoid 容器精度](../../docs/cases/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/README.md)
- [MiniMax Flash 原容器64并发精度重测](../../docs/cases/20261022-minimax-m31-old-container-c64-accuracy/README.md)

- [20261008-minimax-m31-w8a8-ppu-e2e：MiniMax-M3.1 Flash W8A8（09-29 preview） / PPU 总吞吐优化](../../docs/cases/20261008-minimax-m31-w8a8-ppu-e2e/README.md)
- [MiniMax-M3.1 Flash W8A8（09-29 preview） / PPU-07 / TP8 优化](../../docs/cases/20261010-minimax-m31-w8a8-ppu-tp8-e2e/README.md)
