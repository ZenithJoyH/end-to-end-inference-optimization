# Qwen3-VL 在沐曦上的端到端优化

2026-10-27 容器维护：已删除其他8个Qwen-VL实验/评测容器，只保留 `qwen3vl-pr943-split1-mx104-20261023`，私有源码/评测文件已归档，镜像和Host数据保留。最终检查容器仍运行，但9999模型服务未运行；未自动重启，退出原因未定位。[维护记录](20261023-qwen3vl-metax-mx104-migration/optimize/maint-005-remove-other-qwen-vl-containers.md)。下文已完成精度分数是各次测量时的历史结果。


最新[opt12/C64/默认采样完整精度](20261026-qwen3vl-opt12-c64-default-accuracy/README.md)已于2026-10-27完成：GPQA129/198=65.1515>=64；ERQA原生168/398=42.21>=40，2超时保留、全部400计错42.00亦通过。当前用户服务为mx-104 `qwen3vl-pr943-split1-mx104-20261023` 中opt12/9999/GPU0,1/TP2/prefixON，PR638+decode split1及canonical FGV/gems-opt/MoE保留；评测没有改源码、重启服务或清cache。采集drain问题已CPU恢复、原生400条与源码/默认采样审计完整，旧失败保留，没有重跑。无新性能结论或PR638单变量归因。

此前[当前容器僵尸清理](20261023-qwen3vl-metax-mx104-migration/optimize/maint-003-current-container-zombies.md)完成138→0；该维护当时模型已未运行，是历史状态。之后用户已自行重启新opt12，不能再以该旧状态代表当前服务。标准FlagGems-vllm安装继续保留。

2026-10-26较早[仓库整理](20261023-qwen3vl-metax-mx104-migration/optimize/env-002-consolidate-flaggems-vllm.md)阶段的历史服务为同容器GPU4/5、TP2、18977、split1/prefixON；现行FlagGems-vllm已直接安装到标准/workspace/FlagGems-vllm，无需PYTHONPATH，冗余副本备份清理。该阶段graph16/C8属于其旧实例。另[原始发布镜像完整精度](20261026-qwen3vl-metax-release-splits/README.md)为GPQA63.6364%<64、ERQA40.75%>=40，不与新opt12默认采样/C64结果拼接。以下保留各历史实验的测量范围。

当前验证环境已按用户要求迁移到 [mx-104](20261023-qwen3vl-metax-mx104-migration/README.md)，GPU4/5、TP2、独立18977端口。ERQA400通过（native45.73，全部400保守45.50）。两组独立split0→1→0、180轮原生测量及源码核验完整，确认固定split1有性能代价：P1K/D1K/C64/N128输出/总吞吐下降11.37%，缩减P64K/D128/C8/N16下降38.30%，mean TPOT分别增加13.33%/85.27%；回切split0恢复，完整长KV尚未扩大。已恢复split1原helper、prefixON及原配置，graph16/C8和health通过，本轮监控已停用；无新Host GPQA gate或正式验收。生产9999不属于迁移范围。

最新记录：[opt10 全量结果（2026-10-22更新）](20261022-qwen3vl-metax-opt10-results/README.md)。生产环境为 mx-59、MetaX C550、TP2/GPU6,7、容器 `qwen3vl-p64k-opt-20261015`、端口9999。

当前保留 gems-opt 的 sort int32 计数优化、FlagGems-vllm 内联分 GEMM 的 MoE 调优、Plugin 通用 FlagGems 采样适配，以及采样局部直方图优化。此前采样M形状JIT波动证据保留；10月22日独立1K复测已由用户确认稳态，四轮总吞吐3000.31–3044.21token/s、差幅1.45%，SUMMARY3022.26token/s。

| 记录 | 主要内容 | 结论边界 |
|---|---|---|
| [PR977 最新上游验证](20261022-qwen3vl-metax-pr977/README.md) | 独立 GPU0/1，移除本地943 MoE改动，试用上游bad340d；保留采样和gems-opt | 纯上游E128大M仍超限；PR943已刷新316f并通过63GPU/TP2graph与CI；未回写生产、未测E2E |
| [opt10 全量结果](20261022-qwen3vl-metax-opt10-results/README.md) | P1K/P4K/P16K/P32K/P64K，D1K/C64/N128；输出/总吞吐、延迟、逐轮波动和文件SHA；今日1K完整稳态复测 | 人工CSV归档；完整场景不等于正式验收；不混算不同设备与预热条件 |
| [opt9 P1K受控优化](20261021-qwen3vl-metax-p1k-opt9/README.md) | GPU0/1：局部histogram保留，原/候选/回退对照；opt10波动诊断；Flash Attention候选未部署 | P1K局部收益；正式精度暂缓 |
| [MoE与P64K优化](20261015-qwen3vl-metax-p64k-opt3/README.md) | KV预算0.91、GEMM1/GEMM2调优、采样接入及内联配置收敛 | 各实验有独立范围；不相加为组合收益 |
| [FlagGems sort优化](20261013-qwen3vl-metax-flaggems-e2e-opt1/README.md) | int32整数直方图计数及历史受控P1K对照 | 历史环境与配置下的测量 |
| [采样与MoE链路整理](20261012-qwen3vl-metax-sampling-migration/README.md) | 算子归属、完整MoE接入、编译器兼容及调用层收敛 | 接入与正确性证据 |

2026-10-22原生产环境完整精度已完成：GPQA **130/198=65.66分**（阈值64），ERQA **162/400=40.50分**（阈值40），两项均通过。最新五场景的人工性能数据已覆盖完整；同契约全场景anchor/candidate/revert和正式验收仍未完成。

此前PR943316f036独立环境[完整精度](20261022-qwen3vl-metax-pr977/optimize/acc-003-pr943-gpqa-erqa.md)：GPQA123/198=62.12（阈值64，失败），ERQA164/400=41.00（阈值40，通过），prefix cache开启。该组合与原生产版本不同，不能互换精度结论或gate；[后续受控诊断](20261022-qwen3vl-metax-pr977/optimize/diag-004-gpqa-controlled.md)同卡四轮旧125/124、新128/125，未复现新版稳定下降；同seed并发回答有波动，固定输入MoE和采样组件复现通过。具体模型算子边界未隔离，原失败不覆盖。

2026-10-22 [diag-005](20261022-qwen3vl-metax-pr977/optimize/diag-005-fixed-prefix-logits.md)：独立环境按PR943 a1570df更新；同前缀首个batch数值分歧定位到MACA native kvcache默认自动路径，完整Q/K/V相同及忠实重放证实。组件固定split1消除差异但未部署，其他配置/prefix cache保留，18977正常，9999未动；无新正式精度或性能。

2026-10-23 [op-006](20261022-qwen3vl-metax-pr977/optimize/op-006-kvcache-split1-gpqa.md)：独立Plugin固定kvcache split1，数值/graph/C8及真实命中通过；唯一一轮完整GPQA 131/198=66.16分，达到64分阈值。prefix cache ON，其余配置/最新PR943/gems-opt/采样保留；ERQA/E2E未重测、未回写生产。

- 2026-10-27：[metax-plugin0240-base 镜像 splits 核验](20261027-qwen3vl-metax-plugin0240-splits-audit/README.md)：新版native仍复现auto0跨batch数值差异；24项FP64/16capture/48replay通过，未测模型分数。

- 2026-10-27：[官方vllm_metax0.24镜像Attention核验](20261027-qwen3vl-metax-native024-splits-audit/README.md)：默认prefill/decode分路、kvcache省略num_splits→0；原生24项对照复现batch差异，16capture/48replay通过；未测模型分数。

- 2026-10-27：[PR943按模型拆分helper](20261027-qwen3vl-metax-pr943-model-helpers/README.md)：提交97da71f9，553360主机对照通过，未同步运行容器。

- 2026-10-27：[opt13与历史opt10性能差距](20261027-qwen3vl-opt13-performance-gap/README.md)：已有CSV只读对照，P1K总吞吐-23.34%、P4K+1.95%、P16K-24.56%；当前split0/prefixOFF、采样与gems-opt补丁保留。P1K有持续采样编译证据，P16K主要表现为Prefill/Mixed长尾；PR638、MoE与跨Host因素尚未单变量归因，未改服务或新增压测。

- 2026-10-28：[opt14 C64默认采样完整精度](20261028-qwen3vl-c64-default-accuracy/README.md)：GPQA118/198=59.60<64未达标、ERQA181/400=45.25>=40通过（0拒答）；prefixON、FLA回退PR638/default0，原用户服务保留。来源/样本/源前后独立核验，GPQA根因未确认，无gate/性能结论，监控已删除。

<!-- case-navigation:start -->
## 完整案例入口

- 20261012-qwen3vl-metax-sampling-migration：[baseline](20261012-qwen3vl-metax-sampling-migration/baseline/README.md) · [optimize](20261012-qwen3vl-metax-sampling-migration/optimize/README.md) · [acceptance](20261012-qwen3vl-metax-sampling-migration/acceptance/README.md)
- 20261013-qwen3vl-metax-flaggems-e2e-opt1：[baseline](20261013-qwen3vl-metax-flaggems-e2e-opt1/baseline/README.md) · [optimize](20261013-qwen3vl-metax-flaggems-e2e-opt1/optimize/README.md) · [acceptance](20261013-qwen3vl-metax-flaggems-e2e-opt1/acceptance/README.md)
- 20261015-qwen3vl-metax-p64k-opt3：[baseline](20261015-qwen3vl-metax-p64k-opt3/baseline/README.md) · [optimize](20261015-qwen3vl-metax-p64k-opt3/optimize/README.md) · [acceptance](20261015-qwen3vl-metax-p64k-opt3/acceptance/README.md)
- 20261021-qwen3vl-metax-p1k-opt9：[baseline](20261021-qwen3vl-metax-p1k-opt9/baseline/README.md) · [optimize](20261021-qwen3vl-metax-p1k-opt9/optimize/README.md) · [acceptance](20261021-qwen3vl-metax-p1k-opt9/acceptance/README.md)
- 20261022-qwen3vl-metax-opt10-results：[baseline](20261022-qwen3vl-metax-opt10-results/baseline/README.md) · [optimize](20261022-qwen3vl-metax-opt10-results/optimize/README.md) · [acceptance](20261022-qwen3vl-metax-opt10-results/acceptance/README.md)
- 20261022-qwen3vl-metax-pr977：[baseline](20261022-qwen3vl-metax-pr977/baseline/README.md) · [optimize](20261022-qwen3vl-metax-pr977/optimize/README.md) · [acceptance](20261022-qwen3vl-metax-pr977/acceptance/README.md)
- 20261023-qwen3vl-metax-mx104-migration：[baseline](20261023-qwen3vl-metax-mx104-migration/baseline/README.md) · [optimize](20261023-qwen3vl-metax-mx104-migration/optimize/README.md) · [acceptance](20261023-qwen3vl-metax-mx104-migration/acceptance/README.md)
- 20261024-qwen3vl-metax-fixed-splits：[baseline](20261024-qwen3vl-metax-fixed-splits/baseline/README.md) · [optimize](20261024-qwen3vl-metax-fixed-splits/optimize/README.md) · [acceptance](20261024-qwen3vl-metax-fixed-splits/acceptance/README.md)
- 20261026-qwen3vl-metax-release-splits：[baseline](20261026-qwen3vl-metax-release-splits/baseline/README.md) · [optimize](20261026-qwen3vl-metax-release-splits/optimize/README.md) · [acceptance](20261026-qwen3vl-metax-release-splits/acceptance/README.md)
- 20261026-qwen3vl-opt12-c64-default-accuracy：[baseline](20261026-qwen3vl-opt12-c64-default-accuracy/baseline/README.md) · [optimize](20261026-qwen3vl-opt12-c64-default-accuracy/optimize/README.md) · [acceptance](20261026-qwen3vl-opt12-c64-default-accuracy/acceptance/README.md)
- 20261027-qwen3vl-metax-native024-splits-audit：[baseline](20261027-qwen3vl-metax-native024-splits-audit/baseline/README.md) · [optimize](20261027-qwen3vl-metax-native024-splits-audit/optimize/README.md) · [acceptance](20261027-qwen3vl-metax-native024-splits-audit/acceptance/README.md)
- 20261027-qwen3vl-metax-plugin0240-splits-audit：[baseline](20261027-qwen3vl-metax-plugin0240-splits-audit/baseline/README.md) · [optimize](20261027-qwen3vl-metax-plugin0240-splits-audit/optimize/README.md) · [acceptance](20261027-qwen3vl-metax-plugin0240-splits-audit/acceptance/README.md)
- 20261027-qwen3vl-metax-pr943-model-helpers：[baseline](20261027-qwen3vl-metax-pr943-model-helpers/baseline/README.md) · [optimize](20261027-qwen3vl-metax-pr943-model-helpers/optimize/README.md) · [acceptance](20261027-qwen3vl-metax-pr943-model-helpers/acceptance/README.md)
- 20261027-qwen3vl-opt13-performance-gap：[baseline](20261027-qwen3vl-opt13-performance-gap/baseline/README.md) · [optimize](20261027-qwen3vl-opt13-performance-gap/optimize/README.md) · [acceptance](20261027-qwen3vl-opt13-performance-gap/acceptance/README.md)
- 20261028-qwen3vl-c64-default-accuracy：[baseline](20261028-qwen3vl-c64-default-accuracy/baseline/README.md) · [optimize](20261028-qwen3vl-c64-default-accuracy/optimize/README.md) · [acceptance](20261028-qwen3vl-c64-default-accuracy/acceptance/README.md)
- 20261028-qwen3vl-gpqa-controlled-opt12-opt14：[baseline](20261028-qwen3vl-gpqa-controlled-opt12-opt14/baseline/README.md) · [optimize](20261028-qwen3vl-gpqa-controlled-opt12-opt14/optimize/README.md) · [acceptance](20261028-qwen3vl-gpqa-controlled-opt12-opt14/acceptance/README.md)
- 20261028-qwen3vl-opt15-c64-default-accuracy：[baseline](20261028-qwen3vl-opt15-c64-default-accuracy/baseline/README.md) · [optimize](20261028-qwen3vl-opt15-c64-default-accuracy/optimize/README.md) · [acceptance](20261028-qwen3vl-opt15-c64-default-accuracy/acceptance/README.md)
<!-- case-navigation:end -->
