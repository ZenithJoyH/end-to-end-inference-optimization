# 最新栈迁移

<!-- e2e:summary:start -->

- 案例：20261020-latest-stack-migration
- 当前状态：pr_scope_refined_cpu_verified_device_model_pending
- 当前候选：minimaxM3.1-opt-latest-20261020
- 下一步：Wait for safely spare physical8-15 for current combination numerical/graph(two replays)/model smoke-C8-minimal validation. No automatic task/service/performance dispatch; preserve source8035 and Qwen.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| env-001 | operator_verified_model_pending | — | [env-001.md](env-001.md) |
| refactor-001 | retain maintainability refactor; no numerical kernel or performance claim | — | [refactor-001.md](refactor-001.md) |
| cleanup-001 | completed | — | [cleanup-001.md](cleanup-001.md) |
| rename-001 | completed | — | [rename-001.md](rename-001.md) |
| main-001 | completed | — | [main-001.md](main-001.md) |
| policy-001 | retain restoration of original upstream switch semantics and necessary existing optimized adapters only | — | [policy-001.md](policy-001.md) |
| adapter-001 | code_applied_unit_passed_device_pending | — | [adapter-001.md](adapter-001.md) |
| compat-001 | retain existing topk16 fixed-JIT workaround; no new platform logic or source edits | — | [compat-001.md](compat-001.md) |
| env-002 | retain user-requested upgrade; preserve unchanged topk/GQA workaround because same baseline bug persists; model/device validation remains incomplete | — | [env-002.md](env-002.md) |
| adapter-002 | applied_cpu_verified_device_pending | — | [adapter-002.md](adapter-002.md) |
| adapter-003 | source_fixed_cpu_contracts_passed_device_pending | — | [adapter-003.md](adapter-003.md) |
| adapter-004 | activation_params_scoped_cpu_contracts_passed_device_pending | — | [adapter-004.md](adapter-004.md) |
| tests-001 | tests_consolidated_cpu_passed | — | [tests-001.md](tests-001.md) |
| review-001 | pr_scope_refined_cpu_passed | — | [review-001.md](review-001.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

最新完成 [refactor-001](refactor-001.md)：通用 Linear/MoE 移除硬件判断，库选择收敛到配置/backend，MiniMax 语义统一入口，两个必要 launch 兼容集中 Thead backend。178 单测、56 INT8 graph、10 模型算子、2 原生 fallback 和模型 105+2 最小回归通过。新容器代码保留，临时8045已结束，源8035/全局脚本不变；完整精度与性能未测。

此前 [env-001](env-001.md) 迁移与其68单测、INT8 56/融合MoE34/视觉SDPA16证据独立保留；旧分数和 gate 不适用于本轮新组合。监控 PAUSED。

最新完成 [cleanup-001](cleanup-001.md)：10份历史Plugin/FV私有源码经宿主机归档及13,875条文件/链接校验后移除；容器仅保留最终安装源码，导入/注册及三库源码指纹复核通过，旧8035和全局脚本不变。

当前路径以 [rename-001](rename-001.md) 为准：最终Plugin `/workspace/vllm-plugin-fl`，FV `/workspace/flaggems-vllm`；editable来源/注册验证通过，源码及版本未变，旧plugin/fv目录已移除。独立启动脚本仍有效，无新增精度/性能测试。

[main-001](main-001.md)：当前Plugin已在官方main（a696859b9，跟踪origin/main）直接保留工作区修改；包版本0.0.0+ga696859b9.d20261020，源码未变，未用stash保存/恢复，没有提交推送。

当前策略以 [policy-001](policy-001.md) 为准：撤回非必要provider/平台白名单，恢复原有fl_envs开关；199单测、56 INT8 graph、10模型算子及105+2模型最小回归通过，临时8045已退役。仅新容器独立入口显式开启已有VLLM_FL_USE_FLAGGEMS_VLLM=1；原8035/全局脚本不改，正式精度/性能未测。

当前接入以 [adapter-001](adapter-001.md) 为准：去除两个cache/预处理dispatch及独立try融合dispatch，直接调用已有库能力；201单测通过。8–15卡被其他vLLM占用，设备/模型回归及去Thead补丁验证未执行，保留历史兼容，不冒充当前编译失败复现。原8035/全局脚本未变，无新gate或性能结果。

[compat-001](compat-001.md) 已离线复现当前top-k兼容的必要性：六原始配置直接编译均通过，但默认AABS把调整副本K缩为1，违反topk16的K>T约束，原生autotune最终编译失败；固定K128直接JIT编译通过。两处Thead兼容保留，三库源码及服务未改，无GPU计算/新精度或性能。

最新 [env-002](env-002.md)：FlagTree已升级至官方PPU0.7.0+ppu3.6（Triton3.6），精确安装备份及旧wheel已归档。新缓存原生AABS复现仍将K缩为1并最终编译失败，固定K128编译通过；保留top-k/GQA兼容。仅FlagTree发行包变化，三库源码/启动/旧8035未改；本轮无设备/graph/模型精度或性能验证。

上游跟踪：已在同根因[#1407的补充报告](https://github.com/flagos-ai/FlagTree/issues/1407#issuecomment-6286746272)中发布PPU0.7.0验证及已测试的独立最小复现；修复[PR1408](https://github.com/flagos-ai/FlagTree/pull/1408)仍未合并，本任务尚未验证该PR。详见[env-002](env-002.md)。
