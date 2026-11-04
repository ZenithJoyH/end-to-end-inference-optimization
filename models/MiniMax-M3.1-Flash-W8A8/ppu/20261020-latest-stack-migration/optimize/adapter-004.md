# adapter-004 将激活参数收敛到 W8A8 experts 实例

按用户要求，已在 `minimaxM3.1-opt-latest-20261020` 的 `/workspace/vllm-plugin-fl` 完成收敛。仍基于官方 main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd` 直接保留工作区修改，无 stash/提交/推送。分类 framework/maintainability，无新性能主张。

## 最终代码与参数路径

`quantization/w8a8/moe.py` 删除 `install_fl_w8a8_activation_config` 的完整定义、安装调用及仅它使用的math/wraps导入，不再包装或替换vLLM的 `CompressedTensorsW8A8Int8MoEMethod.get_fused_moe_quant_config`，也未增加其他全局参数hook。

原生 `FusedMoEConfig` 已有 `swiglu_alpha/beta/limit`，原生layer.py在创建每层配置时写入同一组模型参数。`quantization/w8a8/moe_experts.py` 的 `FlagGemsW8A8Experts.__init__` 在实际选中并构造该experts后，仅对 `SWIGLUOAI_UNINTERLEAVE` 读取该层配置，检查有限alpha/beta/limit、正limit及动态INT8契约，保存到原有 `self.gemm1_alpha/beta/clamp_limit`。`apply` 改为读取当前实例字段，再将其原样传给Plugin MoE激活/INT8融合路径。

参数路径：`FusedMoEConfig.swiglu_* → selected FlagGemsW8A8Experts.__init__ → self.gemm1_* → apply → fused_experts_impl → activation/INT8 fusion`。参数只属于该experts实例；共享quant_config不写入或复制扩展字段，未选中该适配类的路径不附加检查。普通SiLU保留父类默认字段，原生/其他experts不改。

仅2个源码文件与3个测试文件变化。原有环境开关、名单和strict/fallback、无关W8A8 selector/builder兼容、Thead patch、FV/FG/FlagTree/vLLM/权重/启动均保持；这里删除的是本激活参数函数的全局方法包装，不宣称其他历史兼容hook都已移除。

## 实际验证与限制

调用本地 `inference-accuracy-evaluation`，mode=`minimal-regression`，覆盖adapter-004；bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。235/235 CPU单测通过，0失败、0跳过。新增/更新覆盖真实vLLM父类及Plugin experts构造、两个实例共用一个quant_config而参数独立、配置字段/引用未修改、缺失/非有限/非正limit和错误量化模式拒绝、普通激活与原生父类一致、实例参数传到完整MoE调用，以及重复两次注册后原vLLM量化方法仍为同一对象。计算体采用已有mock验证调用合同，不冒充设备数值/性能。

新进程真实导入及配置字段审计通过：全局安装函数不存在，原vLLM方法无本项目包装marker，重复注册前后方法对象不变，现有FusedMoEConfig字段可直接使用。源码前后指纹、运行时版本/启动SHA复核及增量/main完整补丁反向检查、`git diff --check HEAD`通过。最终Plugin tree `6ed47e1421e76c36ad329da82b562188b28242e841be5318626b89b72c9be794`。

物理8–15仍占用，**设备数值、两次graph replay、模型smoke/C8/最小回归未运行，总体minimal-regression为incomplete/resource busy**。旧验证不作本轮组合证明；无GPQA/Math500/ERQA/性能或新gate，formal performance不允许，PR readiness为experimental/device-validation-pending。

目标新容器没有启动8045；原8035健康为200，没有停止/重启其他服务。监控minimax-m3-1-acc-001保持PAUSED，无新自动验证或压测队列。代码收敛已落地，模型级验证留待安全空闲卡。

## 产物与回退

远端根 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/adapter-004-20261020-01`。原生 `result.json` SHA `8c82abf00a90dade6eec6c64fe5ec37d842ec9f06576642c25cb5b4f8e36527a`，JUnit、真实安装审计、资源与源码/版本证据及命令SHA见 [state.yml](state.yml)。大体积产物仅留远端。

- 增量 `incremental.patch` SHA `4bfc38eabf1bfaa01790981abe1651dd84cdd1ba0d7351c00a6a589dfe178a24`。
- Git-native main完整差异 `plugin-main-full.patch` SHA `58df6e5ca04c8ad74bf2613acbf3d35163c24f7ed26a7d2d5060bc64c03a805a`。
- 改前源码/Git元数据 `plugin-before.tar.gz`。核验目标空闲及当前源码后，只反向应用本轮增量回到213d231 tree，不改启动脚本/库/原服务。

2026-10-20 范围更正（[tests-001](tests-001.md)）：原回执实际为 **234 项CPU + 1 项GPU量化测试通过，共235项**。上文如称纯CPU或零设备测试，表述不准确；原生JUnit保留，本更正不改变通过总数，也不补齐模型/graph验证。后续CPU命令显式排除gpu/multi_gpu。
