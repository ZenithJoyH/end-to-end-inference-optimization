# review-004 最终 PR 范围收敛

状态：清理已安装，定向回归与最终源码/导入核验通过。用户要求清除完整入口优化遗留，仅保留topk-sigmoid版本及原分步链路所需改动。

上次op-003回退只撤回最终selector/workspace实验；本轮还发现集成阶段op-003/op-005的完整入口packed激活适配、quant1辅助实现和大段full-experts测试仍存在。当前模型实际走Plugin split桥接，这些扩展不在实际链路中。计划回到集成阶段完整入口扩展前归档，并逐函数对照官方HEAD，保留已有低层INT32/K256、alignment初始化及激活量化融合实现。

| 项目真相 | 本轮约束 |
|---|---|
| 代码根 | Plugin /workspace/vllm-plugin-fl；FV /workspace/flaggems-vllm；容器私有目录 |
| 当前参考 | Plugin main a696859；FV main 0dfb5cd；已归档完整入口扩展前快照 |
| 改动性质 | 删除未选中的完整入口实验；不新增kernel、调参、配置或导出 |
| 契约 | 保留split的alpha/beta/clamp透传、BF16激活后round-away/FP32 scale、INT8/FP8接口隔离、原env/dispatch/fallback |
| 验证 | 现有CPU合同；已有融合数值/变输入graph；样式/AST与实际导入检查 |
| 豁免 | 非新增算子，不进入新autotune/benchmark/deep-opt；不宣称新性能收益 |
| 边界 | 不重启服务，不跑全量精度或压测，不触碰8–15无关负载；CPU/mock不冒充其他平台实测 |

最终差异、跨仓库依赖、必要兼容patch及未测项将同步本文件；原始源码/补丁/测试回执归档远端，不提交推送或创建PR。

# MiniMax-M3 W8A8：最终 PR 范围

本次为维护性收敛，不引入新的性能候选或全量模型精度结果。源容器`minimaxM3.1-opt-topk-sigmoid-20261021`保留运行；Plugin仍使用已验证的packed split桥接。

## Plugin

拟题：Preserve MiniMax-M3 W8A8 contracts and dispatch biased sigmoid routing

- 基于官方main a696859b9aa528dfd5b21f5da3403fdc16bac4cd；规范目录/workspace/vllm-plugin-fl。
- 普通sigmoid+bias→现有CachedOp/FlagGems-vllm topk_sigmoid；真正grouped、softmax及不支持shape保留原路径，保留归一化、scaling及indices dtype契约。
- W8A8 packed激活参数仅保存在选中的experts实例，透传原Plugin分步桥接；无全局W8A8构造器/量化方法包装。可选融合符号缺失或不支持时沿原activation+quant2路径。
- 激活保留原SILU/GELU dispatch，其余原生激活委托vLLM；packed激活不新增独立dispatch key。
- scaled_int8_mm经现有registry进入FV的既有triton_scaled_mm接口；FV关闭时保留reference路径，不将INT8传给FP8-only FlagGems scaled_mm。
- MiniMax文字五路packed映射、视觉三路QKV映射仅属于目标模型及其quant-config实例；缺native preprocessing时的直接FV桥接不放进通用dispatch。
- Thead patch.py只保留目标架构/shape/签名守护的GQA head-tile兼容；历史top-k autotune patch不存在。它是明确的编译兼容例外，不是新增调度或模型语义分支。
- 本轮Plugin生产AST逐文件不变，仅格式整理；保留现有9个相关测试文件，不新增实验测试。

## FlagGems-vllm

拟题：Keep Thead W8A8 dense and split-MoE specializations behind existing APIs

- 基于官方main 0dfb5cd7478e58320e81124d31473f06eac79aba；规范目录/workspace/flaggems-vllm。
- topk_sigmoid本身已在此上游基线中，无需再复制一份库实现。
- 既有triton_scaled_mm接口下保留810E、INT8/BF16、M16/32/64/8192、K6144、N768/1536及scale/layout约束的split-K/Prefill布局策略；范围外走既有generic算子，显式tile优先级保持。
- 低层MoE保留既有受限K256/INT32 GEMM策略、non-TLE alignment初始化和激活+INT8量化融合，以及Plugin实际需要的包级导出。
- 完整入口enum/activation/default selector/fused_experts/inplace/outplace与官方HEAD AST一致；完整入口用的quant1 kernel、CPU量化回退、retained-config适配和共享workspace实验均移除。
- 删除test_swigluoai_quant_int8.py实验文件；两项必要融合测试并入既有test_fused_moe.py，使用当前可见设备和变输入两次graph回放。保留既有INT8 scaled-MM测试及benchmark条目。
- 本轮收敛未新写kernel或增加导出；相对官方HEAD，最终PR仍包含上述已保留的分步算子特化及必要的可选融合/低层导出。未增加dispatch key或环境变量，没有FV→Plugin/vLLM生产反向依赖。

## 跨仓库依赖与验证边界

Plugin的路由依赖上游已有FV topk_sigmoid；INT8路径复用既有triton_scaled_mm API。激活量化融合是可选能力，缺少该符号会回到原分步路径；目标环境保留其Thead实现。发布前按两库补丁组合测试，并保留VLLM_FL_USE_FLAGGEMS_VLLM原有开关/黑白名单语义。

针对当前PPU组合完成118项CPU/mock合同及75项物理0设备测试；后者覆盖49项topk-sigmoid、2项保留融合、24项INT8 dense graph。CPU9项GPU用例被deselect，与实际设备回执分开记；FV249项非目标用例deselect，不冒充全库通过。

已按两库CI配置检查ruff、black/isort/flake8，工具只装在本地/tmp，不改变容器依赖。两库完整最终补丁均包含原未跟踪文件，git diff --check与reverse --check通过。

未执行清理后的新模型加载/全量三数据集、端到端性能、其他平台硬件测试；旧GPQA167/198、Math500467/500、ERQA267/400仅为原运行组合历史结果，不改写为新分数。服务继续原实例、未重启，不签发新gate。不提交/推送或自动创建PR。

## 最终补丁与复核

- plugin: 23个相对HEAD差异文件；full-repository tree `7472d8c4a66b6779750333ab9973f2942f0f59318d64b6205327de761b901594`；补丁`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/review/review004-20261022-01/pr-plugin.patch`，SHA `e187b630c63630e06ba466f9bbfe979b3fe417cf8f40a987e23159e88939fd0e`，diff/reverse check均通过。
- fv: 8个相对HEAD差异文件；full-repository tree `13f04b779f9008f9a7d3019962fda7003db6a749b1df547239a12d3f64837f6f`；补丁`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/review/review004-20261022-01/pr-fv.patch`，SHA `41a9b1fc853c87ea23a63eeee7c25717d9008e2ed84064d3afe94607acf10f0b`，diff/reverse check均通过。

Plugin23文件（14生产/9测试），FV8文件（5生产/2测试/1benchmark）为相对官方基线的完整最终PR范围，不等于本轮新增文件。Plugin现有框架的router替换机制继续复用；本轮没有增加进程级W8A8方法包装。Thead headtile patch仍为已确认必要的、仅目标架构与形状生效的兼容例外，未擅自删除。

本轮相对清理前共调整22文件，其中归档删除1个实验测试模块；Plugin生产AST逐文件保持，FV六个完整入口节点AST与官方HEAD完全相同，保留的分步helper/kernel AST与完整入口扩展前归档完全相同。原共享量化helper被撤除，融合kernel恢复原内联表达式，其数值与变输入graph已过既有reference对照。

独立审计进程的新导入仍为两个规范目录；默认FV-enabled策略下topk_sigmoid、scaled_int8_mm、alignment、GEMM dispatch均解析为default.flagos；四个Thead算子实际函数对象来源正确，未靠fallback通过代替命中。实验量化/配置/helper定义、实验测试模块及其残留pyc均不存在。118 CPU tests passed（9 GPU cases deselected），75 physical0 tests passed（249非目标cases deselected）；未把CPU/mock或单设备验证标为8卡新模型验收。

最终两库完整patch包含未跟踪的新源码/测试，均通过git apply --reverse --check；未提交、推送、stash或建PR。ruff0.14、black24.8/isort5.12/flake8 7.1按库配置通过，工具只安装本地/tmp，不升级推理环境。pr_readiness=ready_for_review仅代表源码补丁可供评审；其他硬件、清理后新模型加载/正式精度/端到端性能仍未测，不签新gate。

兼容补丁的删除条件：缺native preprocessing的桥接在vLLM提供真实C符号时自动不安装；Thead GQA headtile覆盖仅在目标架构/真实shape/签名匹配时生效，需同版本不覆盖也可编译、capture和至少两次回放及模型最小回归通过，才可删除。目前未重新执行去headtile的设备验证。历史top-k autotune patch已不存在。

审计边界：import/dispatch结果来自独立新进程，不表示运行中workers已重新加载磁盘清理后的文件；既有服务实例未重启，旧正式结果和gate均未改写。

## 后续只读复核：进一步收敛空间

用户询问整个Plugin是否仍可简化。本次重新通过inventory/connectivity检查PPU-07，并只读核验容器Plugin的官方HEAD、工作区状态和完整repository tree；HEAD仍为a696859、tree仍为7472d8c4a66b6779750333ab9973f2942f0f59318d64b6205327de761b901594。本次没有修改容器源码、运行测试或重启服务。

结论是仍有小范围局部整理空间，不宜再大幅合并适配层：

- W8A8 experts的构造器提取并校验三个packed激活参数，apply再按另一组名称构造kwargs。可在选中实例内统一保存透传参数，减少重复字段转换；保留公共pipeline独立调用时的必要校验，不恢复全局方法包装。
- split pipeline中的可选激活量化融合、环境/能力条件和普通激活回退可考虑在现有activation模块中集中组织。必须保持普通激活API、alpha/beta/limit、融合不支持时返回原路径及INT8条件，不增加dispatch key或另建抽象框架；这是待验证设计，尚未实施。
- 测试可在原文件内复用setup/fixture和参数化；模型元数据与Thead启动兼容测试的隔离职责不同，不按文件数强行合并。

不建议删减topk支持范围与fallback、INT8/FP8 API隔离、目标模型/quant-config实例作用域和GQA签名/shape守护。当前W8A8大段tensor合同、原生/FlagGems双适配器、router类替换机制主要已存在于官方main；不能把它们全部算作本次新增复杂度。模型metadata在register_model阶段、执行桥接在worker加载阶段，合并两个时机会改变初始化边界。删除GQA兼容仍需独立无patch编译/graph及模型最小回归证据。

以上为源码审查建议，不是已实施改动、新验证结果或性能收益。进一步实施时另建稳定实验条目，运行受影响的既有测试；旧118/75测试回执仍仅属于review-004最终源码。
