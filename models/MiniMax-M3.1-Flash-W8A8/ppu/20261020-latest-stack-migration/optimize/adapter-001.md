# adapter-001 移除多余dispatch适配层

按用户指令，reshape/cache与MiniMax预处理直接使用原库调用，不作为Plugin可选dispatch算子；去除为可选激活+量化融合新增的try类Plugin算子与backend包装，保留已有FV融合kernel和原MoE两阶段回退链。只改调用组织，不改数学、缓存语义或库kernel；继续沿用原有fl_envs开关和现有activation策略，避免绕过用户的显式reference选择。

Thead patch不是融合算子注册，当前包含两处已遇到的原生launch兼容。本轮以隔离原生输入复现检查当前编译器是否仍失败，不能只凭文件名删除。精度mode=minimal-regression，运行直接调用/不注册/可选依赖/错误传播及融合回退合同、设备graph和模型105+2最小回归。不启动正式GPQA或性能。全部执行前备份并冻结源码，命令归档本case；不使用stash/提交/推送，不影响源8035。

## 最终代码

- `dispatch/backends/flaggems/register_ops.py` 删除 `reshape_and_cache_flash`、`fused_minimax_m3_qknorm_rope_kv_insert`、`try_swigluoai_uninterleave_quant_int8` 三个OpImpl；删除FG backend相应转发方法以及reference中的try占位方法和注册。
- `reshape_and_cache_flash` 原有attention代码本就直接import库接口，不需要本次新增的dispatch条目。该原有调用及上游_C schema保留，不额外修改。
- `patches/minimax_m3.py` 删除预处理CachedOp与重复完整签名转发。仅在vLLM原生_C算子缺失时保留幂等Python桥，调用时lazy import并直接调用FV公开预处理API；原生可用时保持原路径，未改变torch.ops私有ABI。
- `dispatch/backends/flaggems/impl/activation.py` 删除 `try_swigluoai_uninterleave_quant_int8_flaggems`。它是Plugin包装，不是新增kernel。实际融合算法仍为FV现有 `try_swigluoai_uninterleave_quant_int8`；`ops/fused_moe/fused_moe.py`在原链路内直接调用，不再制造独立CachedOp。原env开关、activation黑名单/显式reference策略、缺失/不支持时分开activation+quant，以及错误传播均有合同测试。
- FV/FG源文件逐项未变；Thead `patch.py`也未改。没有新增框架、配置或环境变量。

## patch.py的边界与验证状态

该文件承载历史遇到的两处vLLM原生kernel launch兼容：topk16固定合法配置；BF16 GQA8/D128/topk16的Prefill head tile填充到16。它修改launch metadata、不实现新数学kernel，在Thead worker加载对应MiniMax架构时安装，不用于算子dispatch，也不影响其他模型架构。

本轮试图独立验证当前栈是否已可去掉它，但**没有执行到原生kernel**。两次probe都在 `torch.cuda.mem_get_info(0)[0] > 80GiB` 门禁退出；初次对模块命名检查的判断不准确，第二版修改该检查并未解决资源问题，旧记录完整保留。后续真实ppu-smi显示物理8–15卡各占用约83.5GiB，归属 `qwen3.8-flash-opt-ppu07-20261015`。本轮没有停止、重启或抢占该工作负载，也没有启动8045验证服务。

因此，当前仍保留历史兼容；**不能据本轮宣称原生编译失败已重新复现，或当前patch已确认可删**。需要空闲卡上完成去补丁后的原生同shape数值、graph及服务验证；成功后再移除此兼容，失败则按实际错误收敛到必要范围。CPU/mock测试不能替代此结论。

## 实际验证和限制

201项单测通过，包含MoE融合结果直接进入GEMM2、缺失/不支持时原链路、显式开关/黑名单/reference选择、执行错误传播、MiniMax直接调用/原生路径/idempotency及三算子未注册。真实安装位置和builtin registry审计也通过；源码在官方main工作区，暂存区为空，没有stash/提交/推送。两份补丁反向检查与git diff --check HEAD通过。

当前Plugin源码tree `e905573a1382492b3c1dfc16ee8113d4610980cc30be031c158c54898571f1f5`。**本轮受影响设备数值/graph及模型最小回归未运行，状态incomplete/resource busy；不能复用policy-001的105+2来证明当前桥接版本。** 没有正式GPQA/Math500/ERQA或性能数据，不签发gate；pr_readiness=experimental。

独立启动入口仍为 `/workspace/minimax-m31-latest-stack-20261020/start-model.sh`，host当前归档为 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/commands/start-model-latest-direct-ops-20261020.sh`，已有开关=1及其余参数不变，仅本轮独立日志位置更新。启动前须确认8–15卡和8045端口空闲；本轮未实际启动。原容器8035仍健康，根目录全局start-model.sh未改。当前安装仍为 `/workspace/vllm-plugin-fl` 与 `/workspace/flaggems-vllm`。

原生证据根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/adapter-001-20261020-01`：`validation/unit-01.xml`、`validation/final-code-audit.json`、`validation/resource-status.json`、两个compiler-probe目录的原日志/exit、`source-before.json`、`candidate-source.json`、`source-after-verified.json`及`result.json`。路径和SHA见 [state.yml](state.yml)。

- 本轮增量 `adapter-only.patch`，SHA256 `70e7792215c801f111861a49910b47952ce8a92aaa44374ad503421f3f7e0aae`。
- 当前完整main差异 `official-head-combined.patch`，SHA256 `14eb7c7617935ee4ecfc51c7b018a1b9793ea37fddbbf9d855558d210da05d13`。
- 改前源码/Git元数据 `plugin-before.tar.gz`，独立启动旧版本 `start-model-before.sh`；均仅留在宿主机案例。回退时先核对目标空闲及源码身份，只反向应用本轮patch并恢复本轮启动前版本，再验证。

监控保持PAUSED，没有新设备任务、评测、压测或停止其他服务的动作。

2026-10-20 后续必要性复核见 [compat-001](compat-001.md)：当前默认FlagTree AABS会把原生top-k候选调整为K1，触发K>T断言；原生autotune最终编译失败、固定K128直接JIT编译通过。top-k绕过因此继续保留，GQA按用户要求保留。此次仅编译与控制流复现，无GPU计算，不替代本实验尚缺的设备/模型回归。

2026-10-20 范围更正（[tests-001](tests-001.md)）：原回执实际为 **200 项CPU + 1 项GPU量化测试通过，共201项**。上文如称纯CPU或零设备测试，表述不准确；原生JUnit保留，本更正不改变通过总数，也不补齐模型/graph验证。后续CPU命令显式排除gpu/multi_gpu。
