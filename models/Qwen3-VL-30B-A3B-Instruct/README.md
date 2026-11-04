# Qwen3-VL-30B-A3B-Instruct

<!-- model-navigation:start -->
## 案例导航（2026-11-02 本地记录）

每个案例独立绑定 Host、拓扑与 baseline；下列状态来自本地账本，不表示已重新核验服务。

| 案例 | 优化状态 | 三阶段入口 |
|---|---|---|
| 20261012-qwen3vl-metax-sampling-migration | completed-requested-rollback | [baseline](metax/20261012-qwen3vl-metax-sampling-migration/baseline/README.md) · [optimize](metax/20261012-qwen3vl-metax-sampling-migration/optimize/README.md) · [acceptance](metax/20261012-qwen3vl-metax-sampling-migration/acceptance/README.md) |
| 20261013-qwen3vl-metax-flaggems-e2e-opt1 | resumed-new-linked-p64k-case | [baseline](metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/baseline/README.md) · [optimize](metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/optimize/README.md) · [acceptance](metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/acceptance/README.md) |
| 20261015-qwen3vl-metax-p64k-opt3 | pr943-ready-for-review-source8111-restored | [baseline](metax/20261015-qwen3vl-metax-p64k-opt3/baseline/README.md) · [optimize](metax/20261015-qwen3vl-metax-p64k-opt3/optimize/README.md) · [acceptance](metax/20261015-qwen3vl-metax-p64k-opt3/acceptance/README.md) |
| 20261021-qwen3vl-metax-p1k-opt9 | opt10-read-only-diagnosis-complete-shape-JIT | [baseline](metax/20261021-qwen3vl-metax-p1k-opt9/baseline/README.md) · [optimize](metax/20261021-qwen3vl-metax-p1k-opt9/optimize/README.md) · [acceptance](metax/20261021-qwen3vl-metax-p1k-opt9/acceptance/README.md) |
| 20261022-qwen3vl-metax-opt10-results | accuracy-passed;P1K-steady-confirmed;full-performance-acceptance-pending | [baseline](metax/20261022-qwen3vl-metax-opt10-results/baseline/README.md) · [optimize](metax/20261022-qwen3vl-metax-opt10-results/optimize/README.md) · [acceptance](metax/20261022-qwen3vl-metax-opt10-results/acceptance/README.md) |
| 20261022-qwen3vl-metax-pr977 | kvcache-split1-GPQA-passed | [baseline](metax/20261022-qwen3vl-metax-pr977/baseline/README.md) · [optimize](metax/20261022-qwen3vl-metax-pr977/optimize/README.md) · [acceptance](metax/20261022-qwen3vl-metax-pr977/acceptance/README.md) |
| 20261023-qwen3vl-metax-mx104-migration | pr638-only-attention-on-disk-model-service-currently-not-running | [baseline](metax/20261023-qwen3vl-metax-mx104-migration/baseline/README.md) · [optimize](metax/20261023-qwen3vl-metax-mx104-migration/optimize/README.md) · [acceptance](metax/20261023-qwen3vl-metax-mx104-migration/acceptance/README.md) |
| 20261024-qwen3vl-metax-fixed-splits | split0-full-evaluation-completed-source1-restored | [baseline](metax/20261024-qwen3vl-metax-fixed-splits/baseline/README.md) · [optimize](metax/20261024-qwen3vl-metax-fixed-splits/optimize/README.md) · [acceptance](metax/20261024-qwen3vl-metax-fixed-splits/acceptance/README.md) |
| 20261026-qwen3vl-metax-release-splits | completed-full-evaluation-GPQA-blocker-source-restored | [baseline](metax/20261026-qwen3vl-metax-release-splits/baseline/README.md) · [optimize](metax/20261026-qwen3vl-metax-release-splits/optimize/README.md) · [acceptance](metax/20261026-qwen3vl-metax-release-splits/acceptance/README.md) |
| 20261026-qwen3vl-opt12-c64-default-accuracy | completed-both-accuracy-passed-user-service-retained | [baseline](metax/20261026-qwen3vl-opt12-c64-default-accuracy/baseline/README.md) · [optimize](metax/20261026-qwen3vl-opt12-c64-default-accuracy/optimize/README.md) · [acceptance](metax/20261026-qwen3vl-opt12-c64-default-accuracy/acceptance/README.md) |
| 20261027-qwen3vl-metax-native024-splits-audit | completed-auto0-variation-reproduced-vendor-alias-confirmed | [baseline](metax/20261027-qwen3vl-metax-native024-splits-audit/baseline/README.md) · [optimize](metax/20261027-qwen3vl-metax-native024-splits-audit/optimize/README.md) · [acceptance](metax/20261027-qwen3vl-metax-native024-splits-audit/acceptance/README.md) |
| 20261027-qwen3vl-metax-plugin0240-splits-audit | completed-auto0-batch-numerical-variation-reproduced | [baseline](metax/20261027-qwen3vl-metax-plugin0240-splits-audit/baseline/README.md) · [optimize](metax/20261027-qwen3vl-metax-plugin0240-splits-audit/optimize/README.md) · [acceptance](metax/20261027-qwen3vl-metax-plugin0240-splits-audit/acceptance/README.md) |
| 20261027-qwen3vl-metax-pr943-model-helpers | completed-pr943-updated-no-runtime-deployment | [baseline](metax/20261027-qwen3vl-metax-pr943-model-helpers/baseline/README.md) · [optimize](metax/20261027-qwen3vl-metax-pr943-model-helpers/optimize/README.md) · [acceptance](metax/20261027-qwen3vl-metax-pr943-model-helpers/acceptance/README.md) |
| 20261027-qwen3vl-opt13-performance-gap | PR638-reverted-on-disk | [baseline](metax/20261027-qwen3vl-opt13-performance-gap/baseline/README.md) · [optimize](metax/20261027-qwen3vl-opt13-performance-gap/optimize/README.md) · [acceptance](metax/20261027-qwen3vl-opt13-performance-gap/acceptance/README.md) |
| 20261028-qwen3vl-c64-default-accuracy | completed;accuracy-failed-GPQA;ERQA-passed | [baseline](metax/20261028-qwen3vl-c64-default-accuracy/baseline/README.md) · [optimize](metax/20261028-qwen3vl-c64-default-accuracy/optimize/README.md) · [acceptance](metax/20261028-qwen3vl-c64-default-accuracy/acceptance/README.md) |
| 20261028-qwen3vl-gpqa-controlled-opt12-opt14 | all experiments terminal;minimal batch-RNG firsttoken mechanism confirmed;source preserved | [baseline](metax/20261028-qwen3vl-gpqa-controlled-opt12-opt14/baseline/README.md) · [optimize](metax/20261028-qwen3vl-gpqa-controlled-opt12-opt14/optimize/README.md) · [acceptance](metax/20261028-qwen3vl-gpqa-controlled-opt12-opt14/acceptance/README.md) |
| 20261028-qwen3vl-opt15-c64-default-accuracy | completed | [baseline](metax/20261028-qwen3vl-opt15-c64-default-accuracy/baseline/README.md) · [optimize](metax/20261028-qwen3vl-opt15-c64-default-accuracy/optimize/README.md) · [acceptance](metax/20261028-qwen3vl-opt15-c64-default-accuracy/acceptance/README.md) |
<!-- model-navigation:end -->

## 对应的案例文档

- [Qwen3-VL / MetaX 采样算子归属迁移](../../docs/cases/20261012-qwen3vl-metax-sampling-migration/README.md)
- [Qwen3-VL / MetaX / FlagGems端到端优化](../../docs/cases/20261013-qwen3vl-metax-flaggems-e2e-opt1/README.md)
- [Qwen3-VL / MetaX / P64K opt3](../../docs/cases/20261015-qwen3vl-metax-p64k-opt3/README.md)
- [Qwen3-VL MetaX opt9 P1K 稳态](../../docs/cases/20261021-qwen3vl-metax-p1k-opt9/README.md)
- [Qwen3-VL / MetaX opt10 全量端到端记录](../../docs/cases/20261022-qwen3vl-metax-opt10-results/README.md)
- [Qwen3-VL / MetaX：PR977 最新上游验证](../../docs/cases/20261022-qwen3vl-metax-pr977/README.md)
- [Qwen3-VL / MetaX：mx-59 验证环境迁移至 mx-104](../../docs/cases/20261023-qwen3vl-metax-mx104-migration/README.md)
- [Qwen3-VL / MetaX：发布镜像splits与完整精度核验](../../docs/cases/20261026-qwen3vl-metax-release-splits/README.md)
- [沐曦优化单页汇报](../../artifacts/qwen3vl-metax-onepage-20261022/README.md)
- [Top-k / Top-p 分析](../../docs/qwen3vl-metax-topk-topp-analysis.md)
