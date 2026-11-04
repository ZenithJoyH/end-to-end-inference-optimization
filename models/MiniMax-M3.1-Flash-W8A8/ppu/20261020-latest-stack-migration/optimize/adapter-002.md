# adapter-002 收敛 split SwiGLU-OAI 独立 dispatch

已按用户确认在新容器 `minimaxM3.1-opt-latest-20261020` 的 `/workspace/vllm-plugin-fl` 中完成修改。基于官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` 直接保留工作区变更，没有 stash、提交、推送。分类为 framework/maintainability，没有新的吞吐主张。

## 最终调用与改动

- `ops/fused_moe/activation.py` 删除独立的 `CachedOp("swigluoai_uninterleave")`。现有 MoE 激活入口在原有 `fl_envs.VLLM_FL_USE_FLAGGEMS_VLLM` 和 `use_flaggems_op` 策略允许时，直接调用已安装 FV 的 `ops.fused_moe.apply_moe_activation`，传入该库的 `MoEActivation.SWIGLUOAI_UNINTERLEAVE`。`alpha/beta/clamp_limit` 对应完整传入 `gemm1_alpha/beta/clamp_limit`，输出张量契约保持。
- 开关关闭或全局策略/白名单/黑名单排除时，保持原生 `swiglu_oai_split(input, alpha, beta, clamp_limit)` 路径，库依赖 lazy import。缺少 clamp 会在调用前拒绝；已显式选中的库导入/执行错误直接暴露。
- 删除 FG/reference 的这项 OpImpl、backend 方法及 FG impl/activation 转发；去除为旧 standalone FV 接口保留的可选探测。当前 FV 已提供统一 MoE 激活 API，不再为这个分支增加独立可调度项。
- `ops/fused_moe/fused_moe.py` 删除 `get_selected_impl_id("swigluoai_uninterleave")` 及其 manager import；保留已有 FV 开关、算子名单策略、量化/shape 条件、原 FV 激活+INT8 融合调用和参数传递。缺少融合接口或返回 None 仍走激活后量化，再进入 GEMM2；执行失败不静默隐藏。
- 原生 SiLU/GELU 和其他 dispatch 未改。FV 的通用/Thead 激活、INT8 融合、dense split-K/B布局/MoE INT32、FG、FlagTree 0.7、vLLM、权重、启动脚本以及 Thead `patch.py` 都未改。

独立 dispatch 删除后，不再提供该 key 的 per-op impl override、manager 异常回退或 dump 计数。这属于删除该独立调度入口本身的边界；现有环境开关及算子名单控制继续生效。未新增配置或平台判断，没有恢复历史源码目录。

## 验证与结论边界

调用本地 `inference-accuracy-evaluation`，mode=`minimal-regression`，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，覆盖实验 adapter-002。220/220 CPU 单测通过，0 失败、0 跳过，包含真实策略解析、可选依赖、参数和输出契约、原生选择、融合直接进入 GEMM2/两步回退、错误传播，以及 registry 不再注册该算子。原有模型 W8A8 配置、量化、dispatch 和 Thead 兼容合同也通过。新增路由用例通过 mock 验证适配契约，不作为硬件数值证据。

真实安装导入、官方 main/空暂存区、独立注册和转发已移除、FV 融合仍存在均已核验；三库逐文件指纹复核及两份补丁的反向检查、`git diff --check HEAD` 通过。当前 Plugin tree `78f182d27758c0a6c693e901142e4968d37f1e9a22011bd47c74dcaab04f4f7f`。源码与测试结束后无漂移，原8035健康检查为200。

设备 8–15 仍被 `qwen3.8-flash-opt-ppu07-20261015` 占用；未申请设备张量或启动8045，没有停止其他负载。**本轮 minimal-regression 总状态为 incomplete/resource busy：设备数值、两次 graph replay、模型 smoke/C8/最小回归尚未执行**，旧验证不适用于本轮组合。正式 GPQA/Math500/ERQA 和性能均未运行，无新 gate，formal performance 不允许；PR readiness 为 experimental/device-validation-pending。

监控 `minimax-m3-1-acc-001` 保持 PAUSED。空闲卡出现后需完成当前组合的设备/graph/模型验证；本轮没有创建自动验证或性能队列，也没有启动服务。

## 原生产物与回退

远端产物根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/adapter-002-20261020-01`；必要 SHA 见 [state.yml](state.yml)。本轮证据为 `validation/unit-01.xml`、`validation/final-code-audit.json`、`validation/resource-status.json`、`validation/completion-receipt.json`、源码指纹和备份。

- 增量补丁 `incremental.patch`：SHA256 `d17f490da861b8101b00aeeec07470a0f614233fcdbaedb4569cbab065a38937`，仅本轮9文件变化（7源码+2测试），反向检查通过。
- 官方 main 完整差异 `plugin-main-full-v2.patch`：SHA256 `567bfb265deeaf6db5a801902aeae1e31d48b98c3f55340dbd3c697ff9c6964f`，Git 原生 binary-safe 导出，包含保留的未跟踪源文件，反向检查通过。
- 改前完整源码/Git 元数据 `plugin-before.tar.gz`；核验目标空闲及当前 tree 后，仅反向应用本轮增量恢复 e905 tree，不改启动脚本、库或其他服务。

执行记录保留三项控制/归档问题及修复：首次发行包名核验误用 triton metadata 在变更前退出；第二次完整 patch 导出误解码未改 PNG，在应用后、测试前退出；通用 difflib 全量导出未正确保留旧文件无末尾换行标记，最终用 Git 原生导出替换并验证。旧命令/无效导出保留且被明确标记 superseded，不作为有效回退文件；没有因这些归档问题重跑单测或改变候选源码。

2026-10-20 范围更正（[tests-001](tests-001.md)）：原回执实际为 **219 项CPU + 1 项GPU量化测试通过，共220项**。上文如称纯CPU或零设备测试，表述不准确；原生JUnit保留，本更正不改变通过总数，也不补齐模型/graph验证。后续CPU命令显式排除gpu/multi_gpu。
