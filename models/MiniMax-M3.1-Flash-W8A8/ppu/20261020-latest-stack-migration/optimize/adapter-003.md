# adapter-003 修复 INT8 入口误用 FP8 scaled_mm

用户指出当前 `scaled_int8_mm_flaggems` 的 FlagGems 分支是否只支持 FP8。已只读核验新容器 `minimaxM3.1-opt-latest-20261020` 当前 FG `8200f71f51d784d54a5a51019cb955acb74d64c1`：`/workspace/minimax-m31-latest-stack-20261020/fg/src/flag_gems/ops/scaled_mm.py` 的 `_check_inputs` 第40–41行只接受 FP8 A/B，`_prepare_scaled_mm` 第108行在分配/执行 kernel 前调用该检查。使用真实公开 `flag_gems.scaled_mm` 和 CPU INT8 输入复现 `mat1 and mat2 must be Float8 matrices`。旧 mock 测试错误假设该 API 支持 INT8，掩盖了接入缺陷；这不是新发现的 kernel 数值故障。

## 实施与设计边界

基于官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` 直接修复3文件（2源码+1测试），没有 stash、提交或推送。此项为 framework/contract-fix，修复本任务新增的 INT8 backend，不修改已有 FP8 接口或其他原有算子的环境开关。

- `dispatch/backends/flaggems/impl/quantization.py` 的 `scaled_int8_mm_flaggems` 删除错误的 `from flag_gems import scaled_mm` 分支，仅调用 FV 公开 `triton_scaled_mm(a,b,scale_a,scale_b,out_dtype,bias)`，不做平台判断或宽泛异常捕获。
- `dispatch/backends/flaggems/register_ops.py` 在现有 `scaled_int8_mm/default.flagos` 的 `_is_available` 回调中加入原有 `VLLM_FL_USE_FLAGGEMS_VLLM` 条件。开关开启且 backend 可用才参与选择；关闭或未设置时，manager 直接选择现有 `reference.torch`，调用 `vllm.model_executor.kernels.linear.scaled_mm.triton.triton_scaled_mm`。strict 模式同样通过能力过滤选择 reference，不依赖先报错再回退，也不会把原生执行误记为 default.flagos。
- 原有 policy、白/黑名单、strict/非strict执行失败回退与 reference 实现都未改变。开关为1时的 FV 调用参数和已保留优化不变；FV/FG/FlagTree0.7/vLLM/权重/启动/Thead patch 均未改。

## 验证

选择本地 `inference-accuracy-evaluation` 的 `minimal-regression`，覆盖 adapter-003；bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。

230/230 CPU 单测通过，0失败、0跳过。新证据包含真实 FG API 对 INT8 的拒绝；真实 registry+manager 在 unset/0/false/1/true 与 strict/非strict 共10种情况下的选择，传入实际 INT8 CPU 张量，验证不调用 FP8 API、关闭时不需要 FV、scale/out_dtype/bias 透传；保留已选库执行失败和 fallback 测试。FV 和 native 的计算体仍使用 mock，不能据此声称设备数值或吞吐通过。整个现有模型/量化/融合/dispatch CPU 套件也通过。

最终真实安装入口、三库逐文件指纹、运行时版本和启动 SHA 复核通过，增量及 main 完整差异均通过反向应用检查，`git diff --check HEAD` 通过。Plugin tree `213d231f283ebc2e25352f7c335b372766bdb82523ad83be4eb35c875b463bf5`。源8035健康为200，本轮无模型请求、无8045服务启动，没有停止其他工作负载。

物理8–15仍占用，未运行设备数值、目标graph两次回放或模型 smoke/C8/最小回归；**minimal-regression 整体状态 incomplete/resource busy**。正式精度和性能未运行，无gate，formal performance 不允许；PR readiness 仍为 experimental/device-validation-pending。监控 `minimax-m3-1-acc-001` 保持 PAUSED，未安排新评测或压测。

## 产物与回退

远端根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/adapter-003-20261020-01`。完整结果、逐文件指纹、真实安装审计、JUnit、运行参数、资源状态和必要 SHA 见 [state.yml](state.yml)。未向本地复制大体积原始结果。

- 增量 `incremental.patch`：`183ba6614b77f6f744157926828a6ab8d119bb8fbcea8712bd6dc9ad6d7a2af6`。
- Git 原生 main 完整差异 `plugin-main-full.patch`：`436e08a13f5348c4cc9a0176d34e9a7f017c2b990a2518bd842624175aad84f5`。
- 改前源码/Git元数据 `plugin-before.tar.gz`；回退前核验目标空闲及当前 tree，仅反向应用本轮增量回到 `78f182d27758c0a6c693e901142e4968d37f1e9a22011bd47c74dcaab04f4f7f`，不改启动脚本和库。

2026-10-20 范围更正（[tests-001](tests-001.md)）：原回执实际为 **229 项CPU + 1 项GPU量化测试通过，共230项**。上文如称纯CPU或零设备测试，表述不准确；原生JUnit保留，本更正不改变通过总数，也不补齐模型/graph验证。后续CPU命令显式排除gpu/multi_gpu。
