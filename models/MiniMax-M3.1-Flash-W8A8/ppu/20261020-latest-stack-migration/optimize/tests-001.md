# tests-001 收敛测试文件与执行范围

按用户要求，已在最新容器 `minimaxM3.1-opt-latest-20261020` 的 `/workspace/vllm-plugin-fl/tests` 完成整理。**相对官方main，本轮适配新增的测试文件由11个收敛为2个；删除9个拆分文件，复用7个主题文件，没有新增测试文件。** 所有16处文件改动均位于tests，生产源码逐文件对比完全相同，FV/FG/FlagTree/vLLM/启动未改；无stash、提交或推送。

## 文件归属

| 内容 | 整理后的文件（容器tests相对路径） |
|---|---|
| W8A8实例参数、共享配置隔离、完整MoE融合/回退、库选择 | unit_tests/quantization/test_w8a8_moe_experts.py |
| 原量化方法身份与重复注册 | unit_tests/quantization/test_w8a8_moe.py |
| INT8 dtype、实际registry选择及strict/回退、量化开关 | unit_tests/dispatch/test_flaggems_quantization.py |
| 激活参数、策略/依赖/回退及PPU数值/graph类 | unit_tests/ops/test_activation.py |
| MoE层及routing调用；PPU routing数值/graph类 | unit_tests/ops/test_fused_moe_layer.py |
| 模型元数据/vision映射/直接预处理桥；PPU预处理数值/graph类 | unit_tests/patches/test_minimax_m3_registration.py |
| Thead top-k/GQA launch兼容及其他架构隔离 | unit_tests/dispatch/test_thead_launch_compat.py |

最后两项是仅保留的两个新增文件，其余均复用仓库已有文件。top-k与GQA共用同文件helper；W8A8参数测试不再跨文件导入私有helper。设备用例以类级gpu标记隔离，同文件CPU fixture仅作用于相应CPU类。

删除的9文件：

- `tests/test_minimax_m31_w8a8.py`
- `tests/unit_tests/dispatch/test_scaled_int8_mm.py`
- `tests/unit_tests/ops/test_swigluoai_activation_routing.py`
- `tests/unit_tests/dispatch/test_oai_quant_fusion.py`
- `tests/unit_tests/dispatch/test_minimax_m3_topk_compat.py`
- `tests/unit_tests/dispatch/test_flaggems_library_policy.py`
- `tests/unit_tests/ops/test_fused_moe_activation_thead.py`
- `tests/unit_tests/ops/test_fused_moe_router_thead.py`
- `tests/unit_tests/dispatch/test_thead_minimax_m3.py`

## 删除或合并的冗余

移除针对HEAD源码的AST逐字比对、CachedOp私有字段/固定property值检查、重复模型构造/映射检查、已由CPU覆盖的GPU缺少clamp检查，以及未修改上游wrapper的多重开关组合。INT8原先基于虚构OpImpl的strict测试改为实际registry+provider失败链路；可共用的测试建立局部helper，未增加通用测试框架。保留原env默认/显式选择、名单隔离、可选依赖、错误传播、真实FG FP8输入拒绝、实例间参数隔离和完整GEMM2调用合同。

数值/graph设备用例没有用mock替代；保留原PPU-native ABI环境约束检查，因此设备相关收集总计9项（8项数值/graph + 1项ABI环境检查）。路由仅检查调用参数的mock用例改为CPU，不再申请CUDA张量。

## 验证与历史范围更正

本轮回归方法为minimal-regression/test-maintenance，CPU命令明确 `-m "not gpu and not multi_gpu"`：**184通过、0失败、0跳过，9项设备相关用例排除**。另用 `--collect-only -m "gpu or multi_gpu"` 验证9项可发现性，未执行GPU测试、模型请求或服务启动。新增文件清点、生产源码不变、三库指纹/运行版本/启动SHA、两份补丁反向检查及git diff --check均通过。控制器首次将硬件收集预期写成8，实际额外保留ABI约束用例使其为9；pytest与184项CPU均成功，后续只修正控制计数并消费原收集日志，没有修改源码/测试或重跑通过项。

核对原生JUnit确认，之前policy-001和adapter-001/002/003/004的清单混入了现有gpu标记量化测试；旧的“纯CPU/零设备执行”描述不准确。已在各实验结构化记录和Markdown追加范围更正，原始通过总数和回执保持不变。**adapter-004的235项应读作234 CPU + 1 GPU量化测试，不能据此声称当前组合的完整设备/graph/模型验收通过。** 具体旧回执SHA及逐实验分项见state中的previous_scope_corrections。当前CPU筛选已显式隔离该测试，不再重复此错误。

本轮只整理测试，生产行为仍为adapter-004：激活参数局限在选中W8A8 experts实例。已有设备/graph/模型验证缺口保持incomplete/resource busy，未签新gate或做性能；不把测试整理当性能收益。原8035健康200，未停止其他负载，监控保持PAUSED。

## 产物与回退

远端 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/test-cleanup-20261020-01`。原生result SHA `88db48afe32df9c8790dd5f4d43eb9b55f5ea071dad32c12a7d3149c5bac5115`；覆盖映射、删除原因、JUnit、设备收集列表、历史范围更正和必要SHA见 [state.yml](state.yml)。完整原始产物只在远端。

- 增量test-only补丁：`426c717e5378cccc6e1b8e2aeb31e94a383adad04eb6e580d4d8feafb9c4382a`。
- Git-native main完整差异：`1e3b169bdcc824afd6b204940fd343d113a2b5c053f9b2e10cf7698c75b83cd2`。
- 改前源码备份plugin-before.tar.gz。核验目标空闲及当前tree后，仅反向应用增量恢复旧测试，不改生产运行环境。
