# compat-004 完整experts与Plugin桥接兼容核对

## 结论与范围

已完成当前独立容器 `minimaxM3.1-opt-topk-sigmoid-20261021` 的源码与CPU兼容检查。**不能直接将split桥接替换为Thead完整experts并宣称行为等价。** Plugin桥接保持，FV/Plugin/FG源码与检查前tree一致，未启动模型、设备kernel、graph、正式精度或性能测试，也不影响主任务服务。

本轮仅诊断，无生产补丁。Thead实际Python量化函数运行于CPU；vLLM Triton量化采用按实际源码重建的CPU算术参照，未执行该GPU kernel。激活转发检查替换generic kernel为记录stub。结果不能当作硬件或模型精度通过。

## 对照结果

| 项目 | Plugin split桥接 | Thead完整入口 | 判断 |
|---|---|---|---|
| split布局与gate参数 | w1=[E,2I,H]，传alpha/beta/limit | 相同布局，传gemm1_alpha/beta/clamp_limit | 两个实际adapter均转发至同一generic packed激活；非默认(.7,-2,3.5)参数事件一致 |
| 动态per-token INT8 | vLLM int8_utils，先FP32，再absmax/floor；倒数乘；libdevice.round | 本地_int8_quantize，先原dtype clamp再FP32；除scale；torch.round | 舍入、floor精度和算术顺序不同，两次量化均受影响 |
| 激活+量化融合 | 满足BF16/width384/rows<=32768等条件时调用已保留融合 | packed激活后单独量化 | 完整入口尚未保留该优化链路；topk4对应每chunk最多8192 token可命中旧融合 |
| GEMM调度 | vLLM配置选择→FV低层invoke | Thead本地配置→dispatch→同一FV低层invoke | primitive虽共享，tile策略不同，不能假设原收益继承 |
| 分块 | 65536 token | 32768 token | 大输入的执行组织不同 |
| alignment | Plugin CachedOp，FlagGems backend低层alignment | 普通no_tle alignment；稀疏小M可naive分配 | E128/topk4/无expert_map时M<=8触发完整入口naive；未实测设备数值 |
| router权重与combine | 按input/output位置传递，moe_sum | 相同位置控制，常规路径moe_sum，direct_sum阈值2^60 | 源码顺序一致不代替真实kernel验证；expert_map路径还需实机覆盖 |

## CPU反例

BF16、FP16均使用输入 `[127,.5,1.5,2.5,-.5,-1.5,-2.5]`，scale=1：

- Thead实际函数得到 `[127,0,2,2,0,-2,-2]`。
- vLLM源码算术参照得到 `[127,1,2,3,-1,-2,-3]`。
- 各有4/7个INT8元素不一致。正值子例配全1权重的CPU点积分别131、133，说明量化差异可传播到后续计算；这不是实际模型误差或精度下降的测量。

全零行：BF16的floor在原dtype舍入后使scale为7.877513203e-13，FP32参照为7.874016109e-13；FP16中1e-10下溢，Thead scale=0，量化除法中间值非有限。CPU最终INT8恰为0不能证明该路径与原始正scale契约等价，也不能据此宣称GPU/model发生NaN。

## 配置核对

CPU求值实际配置函数，明确设置非ROCm、VLLM_BATCH_INVARIANT=False且不加载tuned-table/override，仅比较默认策略：

| M | Plugin默认BM/BN/BK | 完整入口base BM/BN/BK | 原K256白名单匹配 |
|---|---|---|---|
| 64 | 32/64/128 | 16/256/64 | Plugin是，full否 |
| 1024 | 128/128/64 | 32/128/64 | Plugin是，full否 |
| 8192 | 128/128/64 | 64/256/32 | Plugin是，full否 |

这只证明默认配置策略不等价；没有实际dispatch/tuning-table命中或吞吐结论。INT32累计路径本身仍共享，不能将K256失配误说成所有INT32优化丢失。

## 后续边界与证据

若下一步切换完整入口，应先在FV统一这条W8A8路径的量化约定、复用已保留的激活量化融合，并明确配置/alignment兼容策略，再做实际数值、graph两次replay和模型精度。当前未做这些修改。

远端案例：/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-integration

- commands/compat004-check.py，执行前归档，SHA见state.yml。
- validation/compat004-result.json，SHA256 5f76e258a8f7cfdc6b236f60c69db01986d3df78e6cfde949718fc605aff1c9c。
- validation/compat004-exit.json（0）与logs/compat004-check.log。
- 当前Plugin tree3a107b7、FV tree0d175b4、FG tree1798d77检查前后一致。
- 首次控制分发字符串占位符冲突在远端Python解析前失败，无检查/源码动作；改正控制后仅运行一次上述诊断。记录不算数值测试失败或重试。

## NV接口区别与修复设计（2026-10-21补充核对）

用户询问修复办法及NV能直接调用的原因。本补充只做源码分析，未修改实现。

1. 当前Plugin的FlagGemsW8A8Experts.apply在SWIGLUOAI_UNINTERLEAVE分支无条件选择Plugin桥接，不区分NV/Thead；VllmFunctionalW8A8Experts则明确拒绝该激活，因为当前vLLM functional入口不转发三个gate参数。因此“当前NV已在相同split路径上直接调用且数值验证通过”不是已有证据。
2. 在本轮FV revision0dfb5cd及当前保留补丁下，NV vendor/ampere/hopper没有fused_experts_impl override，包级入口使用generic ops.fused_moe；Thead由vendor override替换完整入口。generic完整入口已经包含packed枚举、显式gemm1参数、校验及激活调用，故源码具备接口能力；这不等于NV设备验证通过。
3. generic默认动态per-token量化同样采用源dtype floor、torch.round取偶；其可选quant/quant_oai融合也显式保持该原量化语义。Thead独立try_swigluoai_uninterleave_quant_int8则按原Plugin的vLLM provider采用FP32 floor、倒数乘、半整数远离零。两类融合虽然名称接近，不能替换使用。
4. compat-004的4/7是刻意构造的舍入边界反例，证明逐位不等价，不是实际模型误差比例，也不证明round-to-even在数学上错误或必然降低任务分数。不同tile、chunk和alignment本身也不是正确性bug；它们是迁移时的数值/性能回归验证项。FP16零scale是明确的边界健壮性问题。

建议修复边界：

- **先修复库内量化一致性**：在Thead完整入口的split+动态per-token W8A8路径中，让quant1和未融合quant2使用与现有Plugin一致的FP32 absmax/floor、scale、倒数乘和round-away约定；FP32 floor在低精度转换之前，确保全零行scale>0。不全局改变已有SiLU/静态或block量化行为。复用内部量化计算，避免再次复制整套experts流程或反向依赖vLLM。
- **复用已保留融合**：完整入口packed分支调用现有try_swigluoai_uninterleave_quant_int8；支持条件不满足时，执行packed激活+同约定量化。融合和fallback应对半整数、全零、小值和BF16 store保持一致。
- **再保护性能策略**：库内复用已有受设备/真实shape约束的GEMM调优策略，检查M64/1024/8192的K256白名单，以及GEMM2 INT32和alignment路径；不为匹配数字而强行改变所有Thead默认tile。chunk/naive优化是否保留由实际graph数值和性能比较决定。
- **验证后收敛Plugin**：完成两次量化/两次GEMM/激活/归约中间结果、支持条件两侧、BF16/FP16、空输入/zero-row、expert_map/router-weight/inplace/跨chunk检查，graph capture+至少两次replay和模型精度；满足库版本/能力契约后将Plugin split分支收敛为统一完整API调用和显式参数传递。保留现有环境变量/可选库选择及不支持路径语义，不移除vLLM native丢参数的真实guard。

实际NV硬件未检查，以上NV判断只属于当前源码的入口/能力分析，不将历史其他模型SiLU结果当成MiniMax split的硬件验证。
