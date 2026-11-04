# MiniMax旁路容器：算子接入与适配整理

当前容器 `minimaxM3.1-opt-topk-sigmoid-20261021`，Plugin `/workspace/vllm-plugin-fl`，FV `/workspace/flaggems-vllm`。源容器及其现有评测未改变；新容器未启动模型。

| 实验 | 改动 | 验证 | 决定 |
|---|---|---|---|
| [op-001](op-001.md) | 普通sigmoid+bias接入FV topk_sigmoid | 当轮CPU26通过 | 继承保留 |
| [env-002](env-002.md) | FV更新官方main0dfb5cd，原优化保留 | 当轮CPU112/API通过 | 独立容器保留 |
| [review-002](review-002.md) | 原生激活委托、W8A8校验合并，调用链清单 | 当轮CPU118通过 | 独立容器保留 |
| [compat-004](compat-004.md) | 完整入口与split桥接数值/调度核对 | CPU反例确认量化不同；默认K256白名单不同 | 保留桥接，未修改源码 |
| [op-003](op-003.md) | Thead完整experts支持packed SwiGLU-OAI与3个gemm1参数 | FV29+Plugin118 CPU通过；设备只收集 | 代码保留，Plugin桥接未切换 |
| [op-005](op-005.md) | 完整split W8A8量化/融合/受限GEMM策略修复 | FV58+Plugin118 CPU通过，实机未测 | 独立容器保留，Plugin桥接不切换 |

当前minimal-regression总体incomplete：设备数值、graph和模型精度未测，无新正式gate/性能结果。Thead完整入口保留原round-to-even量化，与Plugin融合的round-away不同；接入前需实机对照，见op-003。核对已发现确定差异，详见[compat-004](compat-004.md)；当前不能直接等价替换。事实以[state.yml](state.yml)为准。

最新op-005已实现库内修复，当前FV tree168b03f；设备全部占用，graph和模型验证待完成，尚未恢复性能或签发gate。

后续2026-10-22验证：上述“设备未测/模型未测”是本集成阶段历史状态。新容器设备与现有split模型三项全量已在[acc-001](../../20261021-topk-sigmoid-tp8-accuracy/optimize/acc-001.md)完成；完整API与split性能对照及配置归因见[perf-002](../../20261021-topk-sigmoid-tp8-accuracy/optimize/perf-002.md)。完整API仍未作为模型路径选中，不借split模型分数签发完整API模型精度。

最终状态更新（2026-10-22）：上述完整入口实验已按用户要求在[review-004](../../20261021-topk-sigmoid-tp8-accuracy/optimize/review-004.md)清理撤回，保留原split及topk-sigmoid调用。原测试/数值结果均保留为历史，不再表示当前源码保留该完整入口扩展。
