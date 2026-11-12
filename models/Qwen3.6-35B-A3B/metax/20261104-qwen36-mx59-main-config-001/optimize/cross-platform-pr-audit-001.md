# PR #699 / #702 跨平台源码审计

日期：2026-11-06。用户要求检查其他平台是否存在两个 PR 修复的问题。本次仅只读扫描源码和运行 CPU 控制流夹具，没有远程连接、模型请求、设备测试、PR 修改或服务操作。

## 版本与证据边界

- 仓库：flagos-ai/vllm-plugin-FL，`release/0.2` 基线 `6e11d0ab687247fdf4347a52788ec4f2baf57c79`。
- #699：`d2ce43f6fd7133f321b6abd033a0159552df498e`，MetaX GDN 延迟注册。
- #702：`42b27b3ed5f2259e2a3a1d5f2a5163b5d283d3c6`，MetaX 初始 non-Torch 物理占用扣减及 warmup 后建议值修正。
- 只针对上述版本和使用 `WorkerFL` 的路径；不是对其他平台原生 vLLM、最新主线或全部硬件版本的结论。
- [CPU 审计脚本](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/files/models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-main-config-001/optimize/cross-platform-pr-audit-001/audit.py) 与 [机器可读结果](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/files/models/Qwen3.6-35B-A3B/metax/20261104-qwen36-mx59-main-config-001/optimize/cross-platform-pr-audit-001/report.json) 保存逐源文件 SHA256。脚本从 Git 基线提取实际函数 AST，并对 #702 当前文件作比较；生产推理源码未修改。

## KV 预算：多个平台存在相同的遗漏项

`MemorySnapshot` 计算 `non_torch_memory = total - free - torch_reserved`。它包含驱动、通信等非 Torch 占用，也可能包含同卡其他进程；不能仅凭这个值判断泄漏来源。

`memory_profiling_fl` 只把 `after_profile.non_torch_memory - initial.non_torch_memory` 纳入 non-KV 预算。通用 Worker 用 `total * utilization - non_kv` 分配 KV，因此初始正占用没有被扣除。初始 free >= requested 的准入检查并不能补上这一项。

以“utilization 约束总物理占用”的语义、初始正占用保持稳定为前提，源码中的缺项是确定的；缺项是否在真实设备产生 OOM，还取决于初始占用、峰值估计、安全余量及其他进程变化。本次没有实测其他设备 OOM。

| 平台 / 源码 vendor | 自动 KV 预算 | warmup 后 requested-limit 建议 |
|---|---|---|
| NVIDIA / nvidia | 通用路径存在缺项 | 同样存在缺项 |
| 天数 / iluvatar | 通用路径存在缺项 | 同样存在缺项 |
| 海光 / hygon | 通用路径存在缺项 | 同样存在缺项 |
| 平头哥 / thead | 通用路径存在缺项 | 同样存在缺项 |
| 摩尔线程 / mthreads（musa） | 通用路径存在缺项 | 同样存在缺项 |
| 燧原 / enflame（gcu） | 通用路径存在缺项 | 同样存在缺项 |
| 昆仑芯 / kunlunxin | 通用路径存在缺项 | 同样存在缺项 |
| sunrise（ptpu） | 专用 plain-allocator 修正仍按初始快照作差，未纳入初始占用 | 仍走通用建议公式 |
| 昇腾 / ascend（npu） | 不属于同一个自动预算问题：从模型加载后的实时 total-free 扣除，再预留 50% | 仍复用通用建议，但 non_torch 被设为 0；建议值与其专用预算的记账不一致，须单独修正/验证 |
| tsingmicro（txda） | 提前返回固定/env KV 大小，不走 profiling 公式 | 此分支未设置 peak_activation_memory，通常不进入该提示；固定预算安全性不在本次结论内 |
| MetaX / metax | #702 已修正 | #702 已修正 requested-limit，free-based 建议保持原样 |

Sunrise 的特殊修正解决的是 `torch_reserved=0` 时权重被重复计入 non-Torch 的问题，并额外预留 activation margin；它使用 `after.cuda_memory - initial.cuda_memory`，因此不能把该修正当作已补上初始占用。额外余量可能掩盖风险，但不改变记账缺项。

两条手动建议不能一起机械扣减：基于初始 free 的建议已经排除了初始占用；只对基于总显存 requested-limit 的建议补项。也不能直接增大 `self.non_torch_memory`，否则影响前者。

### CPU 证据

- 实际 snapshot/profiling 函数：初始 non-Torch=100、后续增长=50、权重=200、activation=100，实际得到 `non_kv=350`，未含初始 100。
- requested=800 时，通用 Worker 返回 450；计入初始占用的物理预算应为 350。#702 的 MetaX 分支返回 350，其他通用分支仍为 450。
- 按基线和 #702 两个版本跑 11 个 vendor 分支，共 22 个分支调用；Ascend/TXDA 标为独立分支，不套用通用期望值。
- 18 个通用路径 warmup 后提示检查：执行实际 compile → kernel warmup → graph capture → hint 控制流。给定夹具中，requested-limit 应为 270 MiB，而未修正平台输出 370 MiB；free-based 应为且仍为 370 MiB。
- 执行 Sunrise 实际 allocator 修正块：保持相同模型/增长/activation及默认 1 GiB 最小余量，初始占用从 0 改为 100 MiB，得到的 non-KV 项均为 1274 MiB，证明初始占用未计入。该夹具仅验证算式，不模拟真实 allocator。

## GDN 导入：发现相似风险，但不能宣称同一循环已在其他设备复现

#699 的 MetaX 问题是过早导入原生 GDN 层；原生 GDN 又导入 `layernorm.RMSNormGated`，而 layernorm 初始化可经过平台/kernel 装载路径，形成重入。其他平台需要结合自己的注册入口和真实模块加载次序判断。

| 平台 | 扫描发现 | 本次证据强度 |
|---|---|---|
| GCU / enflame | vendor 包导入时立即 `apply_gcu_patches`，packed-decode 补丁导入原生 GDN；内部异常被吞后，外层仍设置 `_patches_applied=True`，后续整组调用不再重试 | CPU 注入早期 GDN ImportError 后已复现“内层未完成、外层已锁定”；真实 GCU 循环时序待设备验证 |
| Sunrise / PTPU | vendor 包初始化调用 FLA/GDN 补丁；FLA 的末尾 GDN 重绑定失败后仍设置 `_PATCH_APPLIED=True` | CPU 注入末尾 GDN 导入失败后，真实函数仍返回成功；后续调用直接跳过。真实平台循环时序未验证 |
| MUSA / mthreads | `import_kernels` 提前调用补丁组；组入口先置 `_patches_applied=True`，采样器导入失败仅记 debug | CPU 证明同进程后续调用不能重试。这是采样器导入的同类生命周期问题，不是已发现同一个 GDN 环 |
| Ascend、昆仑芯 | 检查到的 GDN 补丁经 Worker 的 `register_oot_ops` 调用，不是 MetaX 的早期 kernel 注册入口 | 未发现与 #699 相同的早期 GDN 入口；不等于证明所有导入路径均无环 |
| NVIDIA、天数、海光、平头哥、TXDA | 本次检查的 vendor 初始化入口未发现同类早期 GDN 导入 | 未发现该路径，未作设备启动保证 |

Sunrise `patch_gdn_core_attn_buf.apply_patch` 自身失败时不置成功标志，区别于上述 FLA 补丁；但它目前从包初始化调用，未发现常规后置显式重试入口，包导入成功缓存后不保证自动重试。

MUSA 源码注释承认早期采样器导入可能循环，并寄希望于独立 worker 重试；本次仅证明同进程被 latch 阻断。新的 worker 是否会遇到同样时序仍需实机确认，不能推定父进程失败必然导致 worker 失败。

### 导入验证方法及限制

提取实际 MUSA/GCU/Sunrise 函数，其他依赖用 CPU stub 替代，在相关 import 注入一次 ImportError，再解除故障并调用原公共入口。三个夹具均确认入口因“已应用”标志跳过重试；GCU/MUSA 直接调用内层补丁可恢复。未使用实际 SDK、vLLM import graph、GPU、graph capture 或模型运行，因此这是失败处理控制流证据，不是循环导入的硬件复现。

夹具开发时发现并修正了两处模拟环境问题：Python `__import__` 的 fromlist 可能为 None，以及 FLA stub 缺少原始函数属性。两次失败均发生在 CPU 夹具，无设备操作；最终全部断言通过。

## 建议的后续范围

1. 保留当前 #699/#702 的 MetaX 范围，不把未验证平台直接并入已有 PR。
2. 通用 KV 预算可另作跨平台修复，但应先确认各后端 `mem_get_info` / `memory_reserved` 的语义，单独处理 Ascend、Sunrise、TXDA，且覆盖两条 warmup 建议避免重复扣减。
3. GCU、Sunrise 优先验证真实 GDN 导入时序；MUSA 单独验证采样器补丁时序。补丁组不应把可恢复的局部导入失败锁定为全组成功；初始化后显式重试必须保留幂等和已有函数引用的一致性。

## 关键源码定位

以下链接固定到审计基线，不会随分支移动：

- [Worker snapshot/profiling](https://github.com/flagos-ai/vllm-plugin-FL/blob/6e11d0ab687247fdf4347a52788ec4f2baf57c79/vllm_fl/worker/worker.py#L91-L202)
- [Worker 自动预算](https://github.com/flagos-ai/vllm-plugin-FL/blob/6e11d0ab687247fdf4347a52788ec4f2baf57c79/vllm_fl/worker/worker.py#L452-L565)
- [MUSA 补丁组与异常处理](https://github.com/flagos-ai/vllm-plugin-FL/blob/6e11d0ab687247fdf4347a52788ec4f2baf57c79/vllm_fl/dispatch/backends/vendor/musa/patch.py#L13-L46)
- [GCU 补丁组](https://github.com/flagos-ai/vllm-plugin-FL/blob/6e11d0ab687247fdf4347a52788ec4f2baf57c79/vllm_fl/dispatch/backends/vendor/gcu/patch.py#L110-L137) / [GDN 重绑定](https://github.com/flagos-ai/vllm-plugin-FL/blob/6e11d0ab687247fdf4347a52788ec4f2baf57c79/vllm_fl/dispatch/backends/vendor/gcu/impl/fused_recurrent_packed_decode.py#L272-L311)
- [Sunrise GDN 重绑定及成功标志](https://github.com/flagos-ai/vllm-plugin-FL/blob/6e11d0ab687247fdf4347a52788ec4f2baf57c79/vllm_fl/dispatch/backends/vendor/sunrise/patches/patch_fla_ops.py#L170-L199)

## 2026-11-06 本地过程材料归档

本案例的本地过程文件已按原相对路径无损归档；正文中的历史命令和远端执行路径保留原意。查阅或恢复请使用[逐文件路径与 SHA 清单](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/migration-manifest.json)及[完整原文件备份](/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/before.zip)。本地副本位于 `/Users/baai/Documents/ChatGPT/端到端推理优化/.cache/model-record-archives/20261106-project-review-fixes-artifacts-001/files/`，按清单中的 `original_relative_path` 查找；不应直接重跑历史启动或修复脚本。本次未连接远端、未执行模型测试，也未改变既有实验结论。归档仅在当前工作区可用，恢复时先校验 SHA 并复制到新目录，不覆盖后续修改。
