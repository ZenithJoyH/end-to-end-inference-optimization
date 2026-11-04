# review-002 整体梳理 MiniMax 适配

后续更新：见[op-003](op-003.md)。旁路容器的Thead完整入口现已补齐packed参数支持（CPU合同通过、硬件未测）；本review记录的是改前限制。Plugin桥接仍按用户要求保留，完整入口量化舍入与桥接融合不同，尚未切换。

## 优化方向与瓶颈依据

用户要求按正式PR方向收敛算子调用和适配代码。分类 framework/maintainability，本轮没有改变 kernel 数值或调参，不产生性能结论。

## 优化内容与适用边界

本轮只改两个生产文件与两个既有测试文件，生产代码净减少36行：

- `vllm_fl/ops/fused_moe/activation.py`：保留FL SiLU/GELU dispatch与packed SwiGLU-OAI参数适配；SWIGLUOAI、SWIGLUSTEP及无乘法激活统一复用vLLM的apply_moe_activation，不再复制原生分支；保留输出/输入形状契约和alpha/beta/clamp透传。packed fallback仍保留可在PPU上执行的明确参数路径，不改为缺失native op。
- `vllm_fl/quantization/w8a8/moe_experts.py`：native与FlagGems两个functional adapter的动态INT8/config、LoRA、预量化输入及dtype检查收敛成一个局部helper；FlagGems权重/scale/layout校验、构造实例参数及split gate完整性校验保留。没有增加全局包装。
- 测试复用现有test_activation.py与test_w8a8_moe_experts.py，增加5个原生激活转发与native/FG共同输入拒绝覆盖；未新增测试文件。

### 全量调用链审查结论

| 功能 | 当前路径/职责 | 决定及原因 |
|---|---|---|
| 普通sigmoid+bias Router | CachedOp(topk_sigmoid)→FlagGems backend→FV通用kernel | 保留，原env/名单和native支持范围外fallback有效；真正grouped保持原路径 |
| W8A8 dense INT8 | dynamic quant CachedOp + scaled_int8_mm CachedOp→FV triton_scaled_mm→Thead特化 | 保留INT8/FP8接口隔离、原有split-K/形状与B布局策略；禁止退到FP8-only FG scaled_mm |
| 普通SiLU W8A8 MoE | selected FlagGemsW8A8Experts→库fused_experts_impl | 保留，遵循原库开关 |
| packed SwiGLU-OAI W8A8 MoE | 实例gate参数→Plugin现有pipeline→FV低层Thead GEMM/alignment→可选激活INT8融合→combine | 暂时保留：最新generic库支持gate参数，但Thead完整experts仍只有SiLU；直接换整段入口会改变支持契约与配置策略，不能只按API名称删除桥接 |
| 激活 | FL SiLU/GELU、packed特例；其余委托原生 | 本轮收敛重复原生实现 |
| QK norm/RoPE/KV预处理 | 仅目标模型加载、native符号缺失时的模型专用直接FV桥接 | 保留，未塞进通用dispatch，没有改模型构造函数 |
| 压缩权重映射 | 模型packed metadata + 当前quant-config实例vision QKV映射 | 保留，文本5路与视觉3路映射不同；不改全局config类 |
| W8A8 selector/builder | 原有窄入口兼容dynamic-token INT8 | 沿用main原有兼容，不以“整体梳理”扩成vLLM类方法全局包装 |
| Thead GQA launch | vendor worker model-load边界、严格模型/shape/签名、幂等headtile16 | 保留现有编译兼容；top-k patch已不存在；本轮无设备证据支持删headtile |

### 前一问题的进一步核实

`VllmFunctionalW8A8Experts` 的NotImplementedError仍需保留：实际vLLM0.24 functional入口从quant_config转发量化字段，却没有传gemm1_alpha/beta/clamp_limit；下层activation调用也未补这些参数。packed激活要求clamp_limit，因此不能仅凭默认alpha/beta或更新FV就放行。该拒绝只在native functional fallback，不是禁止正常FlagGems packed W8A8路径。

### PR边界

没有新env、独立activation dispatch、平台判断或全局hook。既有缺失native preprocess的模块级函数替换与Thead launch包装仍存在，范围在表中明示，不宣称“没有任何patch”。未运行其他平台硬件或GPU图测试；默认行为、strict/fallback和whitelist/blacklist由现有CPU合同验证。

## 正确性与路径命中

冻结10个既有测试文件，升级前112通过，FV-only112通过，整理组合118通过；9设备用例deselected。真实FV模块绑定审计、CPU generic/vendor拒绝不写、AST及增量反向apply检查通过。CPU/mock不冒充算子数值、graph或完整模型精度。整体minimal-regression=incomplete。

## 性能效果

无性能测量；不能从减少代码量推断端到端吞吐改善。

## 决定、风险与回退

独立容器保留，pr_readiness=experimental。下一步是安全安排设备数值/graph及正式精度；不自动启动模型/评测/压测。本轮4文件增量patch和完整源码备份均归档可回退，原容器未改。

## 外部证据

/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-integration

- patches/refresh-plugin-review.patch：本轮4文件增量；SHA与归档路径见state.yml。
- validation/refresh-reviewed.xml、refresh-api.json、refresh-final-report.json。
- 新Plugin仍基于官方main a696859；工作tree `3a107b713a50cefc6455eaa5a93e33af1453cd4b92a009a2ba79f16f1e954c88`。
