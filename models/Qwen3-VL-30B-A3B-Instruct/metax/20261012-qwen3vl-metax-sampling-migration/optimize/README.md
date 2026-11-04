# 20261012-qwen3vl-metax-sampling-migration / optimize

<!-- e2e:summary:start -->

- 案例：20261012-qwen3vl-metax-sampling-migration
- 当前状态：completed-requested-rollback
- 当前候选：op-012-revert-plugin-sampler
- 下一步：Plugin采样恢复原HEAD PyTorch fallback，MoE保持op010；库算子保留但不再由Plugin采样入口调用。完整模型graph/C8与正式精度性能未测，不形成正式gate。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-001-sampling-library-migration | retained-code-only | p1024-d1024-c64-n128 | [op-001-sampling-library-migration.md](op-001-sampling-library-migration.md) |
| op-002-moe-path-review | diagnosis-only | p1024-d1024-c64-n128 | [op-002-moe-path-review.md](op-002-moe-path-review.md) |
| op-003-moe-library-switch | retained-code-only | p1024-d1024-c64-n128 | [op-003-moe-library-switch.md](op-003-moe-library-switch.md) |
| op-004-metax-full-moe | retained-code-only | p1024-d1024-c64-n128 | [op-004-metax-full-moe.md](op-004-metax-full-moe.md) |
| op-005-remove-sampling-switch | retained-code-only | p1024-d1024-c64-n128 | [op-005-remove-sampling-switch.md](op-005-remove-sampling-switch.md) |
| op-006-flagtree-upgrade-review | diagnosis-only | p1024-d1024-c64-n128 | [op-006-flagtree-upgrade-review.md](op-006-flagtree-upgrade-review.md) |
| op-007-worker-moe-cleanup | retained-code-and-runtime-only | p1024-d1024-c64-n128 | [op-007-worker-moe-cleanup.md](op-007-worker-moe-cleanup.md) |
| op-008-unquantized-entry-cleanup | retained-code-only | p1024-d1024-c64-n128 | [op-008-unquantized-entry-cleanup.md](op-008-unquantized-entry-cleanup.md) |
| op-009-moe-unification-review | diagnosis-only | p1024-d1024-c64-n128 | [op-009-moe-unification-review.md](op-009-moe-unification-review.md) |
| op-010-metax-nvidia-call-alignment | retained-code-only | p1024-d1024-c64-n128 | [op-010-metax-nvidia-call-alignment.md](op-010-metax-nvidia-call-alignment.md) |
| op-011-metax-official-image-moe-inspection | diagnosis-only | p1024-d1024-c64-n128 | [op-011-metax-official-image-moe-inspection.md](op-011-metax-official-image-moe-inspection.md) |
| op-012-revert-plugin-sampler | reverted-sampling-only | p1024-d1024-c64-n128 | [op-012-revert-plugin-sampler.md](op-012-revert-plugin-sampler.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| operator-m2-v257-bf16 | reference | filter_latency | 2.0703675746917725 | ms | operator-only |
| operator-m2-v257-bf16 | candidate | filter_latency | 0.4905545115470886 | ms | operator-only |
| operator-m2-v257-fp32 | reference | filter_latency | 2.031235694885254 | ms | operator-only |
| operator-m2-v257-fp32 | candidate | filter_latency | 0.6396776437759399 | ms | operator-only |
| operator-m64-v151936-bf16 | reference | filter_latency | 28.691558837890625 | ms | operator-only |
| operator-m64-v151936-bf16 | candidate | filter_latency | 1.8757048845291138 | ms | operator-only |
| operator-m64-v151936-fp32 | reference | filter_latency | 28.73948097229004 | ms | operator-only |
| operator-m64-v151936-fp32 | candidate | filter_latency | 22.478933334350586 | ms | operator-only |

<!-- e2e:summary:end -->

实现已迁移到 FlagGems-vllm 的 MetaX backend，通过公共API接入Plugin。49项算子、7项路由测试通过；两个旧失败用例的尾部计数根因已单变量确认。上述延迟属于算子测量，不是TTFT/TPOT；上述是op001当时的算子范围，后续模型graph见op004/op005；完整GPQA和端到端四场景仍未测。来源、补丁、兼容与回退详见 [迁移记录](op-001-sampling-library-migration.md)。

op003阶段完成 [两处公共调用来源切换](op-003-moe-library-switch.md)：分步骤 GEMM 与完整 fused_experts API 均来自 FlagGems-vllm。20 组设备数值与每组两次 graph replay、3 项接入检查通过；两文件已回写 qwen-vl 并核验默认 dispatch 接入，回退 dry-run 通过。未启用 MetaX 完整融合，未改默认策略/MCTLLASS 补丁，未重启模型服务，没有新增端到端收益证据。当前组合的模型精度和性能仍 incomplete。

完整MetaX MoE接入详见 [op-004](op-004-metax-full-moe.md)：设备21场景、11路由检查及TP2原graph模式18请求通过，三文件已回写源容器，未重启源服务。规划复盘 planning-op004-20261013：当前组合累计性能未知，Prefill/Decode/Mixed热点均待测；下一步先冻结正式精度/同配置P1K比较契约，再决定是否推进性能。其他MetaX模型warmup兼容与PR整理待补，不能将旧采样算子加速比与本轮接入相加。

2026-10-13 [op005整理](op-005-remove-sampling-switch.md)：旧采样开关从hook/测试/start-model.sh移除，按既有支持范围自动选择；必要Worker条件精简，完整MoE helper保留。独立0/1卡49项算子、8项路由、实际hook graph及TP2/18请求通过并回写qwen-vl，四文件回退dry-run通过。源卡号4/5不变、源服务未重启；验证服务已停止，0/1释放。正式GPQA/性能未测。

随后按用户反馈完成op005 r2：删除独立MoE helper并将相同条件内联到apply，净减15行；Worker只纠正MiniMax common kernel注释，逻辑未变。20项入口对照、2组native MoE graph、原TP2/18请求通过，已回写并核验源码；两文件回退dry-run通过，验证服务停止且0/1释放。当前使用commands/op005-inline/rollback.py回退r2，旧回退须先恢复前置版本。

[op006 FlagTree隔离预检](op-006-flagtree-upgrade-review.md)：官方MetaX0.7.0.post2/Triton3.6 wheel实际jit包含新参数，原MiniMax warmup模块正常导入，确认升级能修复这处TypeError。当时仅side-by-side overlay，新编译器下模型/算子graph未测；当时source/clone全局仍旧版本，Worker保护保留。正式更换前须完整兼容回归，不能将import passed当作全栈或性能通过。

当前 [op007](op-007-worker-moe-cleanup.md) 已验证并回写两个容器默认FlagTree0.7.0.post2+metax3.6/Triton3.6.0：Worker恢复正常kernel_warmup，旧MCTLLASS vendor特化和启动export删除，完整MoE保留必要支持/策略边界。49采样/8Plugin/20MoE路由/两dtype graph/TP2 FULL_AND_PIECEWISE/18请求通过，源不重启，验证卡已释放；129个旧编译器文件和3源码/1启动脚本回退dry-run通过。Docker固化MCTLLASS环境声明仍在，活动代码不读取；未重建容器。当前回退入口commands/op007/rollback.py。正式精度、累计端到端收益和跨平台硬件兼容均未测；planning-op007-20261013保留这些证据缺口。

当前[op008](op-008-unquantized-entry-cleanup.md)完成上游保证核对：仅删除quant_dtype/weight_quant_dtype/block_shape为None的三行重复判断；LoRA、SiLU、dtype、输入权重及per-op策略条件仍需保留。4构造/6prepare/19路由、3dtype各2次graph、TP2真实worker None配置与18请求通过，已回写一文件、回退dry-run通过；源未重启，验证服务和0/1卡已释放。正式精度/性能未测，当前回退入口commands/op008/rollback.py。

当前[op010](op-010-metax-nvidia-call-alignment.md)按用户要求仅将MetaX完整调用条件对齐原NVIDIA：no LoRA且CUDA/MetaX，无MetaX额外条件/per-op检查，也无新增dispatch/helper/env。18路由对照、三dtype graph、TP2/18请求通过并回写一文件；源未重启，验证卡释放，回退dry-run通过。USE_FLAGGEMS=0可关闭全局选择，但MetaX native选择器报现存UnboundLocalError；MoE/OOT黑名单不阻止oracle选TritonExpertsFL，没有有效单独MoE关闭入口，本轮不修。正式精度/性能未测，当前回退commands/op010/rollback.py。
