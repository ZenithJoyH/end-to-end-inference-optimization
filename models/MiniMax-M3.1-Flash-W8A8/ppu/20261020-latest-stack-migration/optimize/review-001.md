# review-001 Plugin 全量差异审查与 PR 收敛

已在 `PPU-07 / minimaxM3.1-opt-latest-20261020 / /workspace/vllm-plugin-fl` 完成修改。基线为官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，直接编辑工作树，无 stash、提交、推送或 PR。当前库位置和启动脚本不变；FV/FG/FlagTree/vLLM 均未变更。

## 本轮收敛

1. **删除量化配置类的全局包装。** 不再替换 `CompressedTensorsConfig.get_scheme_dict`。仅在选中 MiniMax-M3 的 Worker 模型加载前，对该服务的量化配置实例绑定视觉三路 QKV 映射；文本五路映射保持原样，其他实例与上游类方法不变。原生 `configure_quant_config` 仍负责填入模型 packed mapping，没有包装模型构造函数，也没有修改 vLLM。
2. **缩小原生算子桥接的安装时机。** general-plugin 的 `apply_minimax_m3_patches` 只设置模型元数据。缺失原生预处理算子的桥接在 MiniMax 模型加载阶段安装；已有原生算子时保留原实现，不经过 Plugin dispatch，不注册伪造私有 ABI。
3. **撤销无关平台行为变更。** `fused_moe_utils.py` 恢复官方 main，移除本任务额外扩大到 MetaX 的 SILU fastpath；未以 PPU 实测推断 MetaX 支持。
4. **删除重复转发层。** `dispatch/backends/flaggems/impl/fused_moe.py` 恢复 main；单一调用者的库选择留在原 W8A8 边界，继续遵守 `VLLM_FL_USE_FLAGGEMS_VLLM`。没有新增一套 provider 策略。
5. **修复共用路由合同。** 新增 biased-sigmoid 路径保留调用方传入的 `indices_type`；softmax 继续调用原生实现。通过已有测试文件覆盖 int32/int64 和非目标分支，无新增测试文件。

## 最终生产差异逐项审查

相对 main，生产差异从 16 个文件收敛为 14 个（含两个新增兼容模块）。每项保留原因如下。

| 文件或职责 | 保留理由与范围 |
|---|---|
| `__init__.py` | 注册模型 packed metadata；不再在所有 general-plugin 进程中安装执行 hook |
| `patches/minimax_m3.py` | 模型元数据、当前实例视觉映射、仅缺失 native op 的直接库桥接；无平台/Host/模型路径分支 |
| `worker/worker.py` | 模型加载前配置实例准备；Thead 编译 shim 仅在对应 vendor 的 worker 加载时调用，其他 vendor 不导入 Thead 模块 |
| `vendor/thead/patch.py` | 仅保留已定位的 topk16 和 BF16 GQA8/D128/topk16 编译兼容；架构、vendor、shape 与签名限制，幂等，非目标走 native；本轮未改其 kernel/调参 |
| FlagGems backend / quantization impl / registration | `scaled_int8_mm` 使用 FV INT8 API，通过既有 registry 与名单选择，不把 INT8 传给 FP8-only FG `scaled_mm` |
| Reference backend / registration | FV 禁用或未选择时保留 native INT8 fallback；不修改其他算子默认实现或 strict 机制 |
| `ops/fused_moe/activation.py` | 已有 FV 开关和 op 名单下直接调用库 packed activation，否则保留 native alpha/beta/clamp 合同；无独立 activation dispatch 项 |
| `ops/fused_moe/fused_moe.py` | 在已有 MoE 链路传递显式激活参数，调用可选融合 API；不支持时保留分离激活/量化，已选实现执行错误不吞掉；无平台检测与复制 kernel |
| `ops/fused_moe/router.py` | biased sigmoid 复用 grouped-topk CachedOp；保持 dtype、scale 和非目标 softmax 语义 |
| `quantization/w8a8/linear.py` | 用已有 CachedOp 接入 INT8 MM，修复原 FP8-only API 误用；其余 registry 顺序与 policy 保持 |
| `quantization/w8a8/moe_experts.py` | 激活参数仅在实际选中 experts 实例使用，不修改共享 quant_config、不包装原生 quant-method；保持其他激活与 W8A8 检查 |

官方 main 自带的 `quantization/w8a8/moe.py` selector/builder 兼容包装没有本任务新增差异，未借本轮收敛重新设计。Thead 编译兼容仍有既有编译失败证据，不能为减少文件而删除；待修复栈下的原路径编译及真实设备验证通过才能撤销。此处没有重新检查 issue/PR 最新网络状态，也不宣称上游已合入或未合入。

## 验证与边界

- 运行目标容器原生 pytest，明确 `-m "not gpu and not multi_gpu"`：**190 passed、0 failed、0 skipped；9 个设备用例 deselected**。设备用例独立 collect-only 验证，未执行。
- 真实 `CompressedTensorsConfig` 方法复现旧五路映射对视觉三路 ignore 的不一致错误，实例映射修正后正确忽略；原生类方法不变，另一配置实例不受影响，文本 mapping 不变，重复绑定幂等。
- Worker 顺序、其他架构隔离、general-plugin 仅 metadata、native bridge 可用/缺失/幂等、biased-sigmoid int32/int64、softmax native、W8A8 实例参数与融合链路、原 env/名单/strict/fallback 均在选定回归范围内通过。
- 三库逐文件指纹前后核对，只有归档列出的 11 个 Plugin 源码/测试文件改变。两文件恢复 main；未新增测试文件。真实导入审计确认全局配置方法保持 native。
- 增量与 Git-native main 全量补丁均通过反向 apply 检查，`git diff --check` 通过；改动 Python 文件可解析，所改主题测试/兼容模块 Ruff 检查通过（仓库生产代码本有 Ruff exclude，不将其解释为全生产 lint 完成）。
- 物理 8–15 仍被占用，本轮无设备运行、模型启动/请求、正式精度或性能测试；原 8035 health=200，未停止 Qwen。监控继续 PAUSED。

`minimal-regression` 的 CPU 合同部分 passed，**所需当前组合的设备数值/graph capture+两次 replay、模型 smoke/C8/native minimal 仍 incomplete**。还需新正式精度及绑定 gate 才能恢复正式性能。`pr_readiness=needs_revision`：代码职责已收敛，实机和模型证据尚不足，不能将旧栈精度/性能视为本轮结果。

## PR 说明草稿与跨仓依赖

问题：MiniMax-M3 动态 W8A8 的 packed activation 参数、视觉/文本不同 QKV packing 和缺失 native 预处理 API 需要保持明确契约，原 INT8 linear 不应调用 FP8 scaled-mm。最终改动在原有 registry、W8A8 experts 与模型加载边界接入相应库 API；可选融合未命中时仍执行原分离链路。改动不增加模型路径/机器身份选择，不扩展其他平台 fastpath。

依赖当前 FV 对 INT8 MM、packed activation 与 missing-native preprocess 的实现；融合 API 通过可选 capability 检查，不可用时回退。FP8-only FlagGems scaled-mm 不作为 INT8 fallback。Plugin 之外的算子补丁仍有独立原始归档；本轮没有修改它们。最终真实设备/模型回归与端到端对照留待资源可用，不据局部实现或 CPU 合同测试声称吞吐收益。

## 产物与回退

远端产物根：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/pr-review-20261020-01`。原生 result SHA `0c22aa3ae6983e2d7fe43fb619c099f8ed8ccd2005060a5b4496c58b57f9434a`；源码备份、前后指纹、原生 JUnit、工程检查和命令 SHA 见 [state.yml](state.yml) 的 review-001。当前 Plugin tree `f10e3075a69092f992135853987e45d82e18d59b2ac680edf34b23ed1a06baa5`。

增量 patch SHA `1072e0b102c74c62161b9111513b8800d09c2d662e5e7985f12e80d6791f7ad9`；完整 main patch SHA `d2eeb419f066d9eee8e8db00f67c6a0977d966a90d95dff2a67e6c16e5af9f0f`。回退前核验容器空闲与当前指纹，再仅反向应用增量恢复改前状态；不操作原服务或其他库。
