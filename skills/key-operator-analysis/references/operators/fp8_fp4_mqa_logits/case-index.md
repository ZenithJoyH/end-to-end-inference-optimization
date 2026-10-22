# FP8/FP4 MQA logits 实际案例证据索引

本文件保存跨仓库迁移、调优配置来源和冷 shape 行为的限域证据。算子数值与
服务健康验证不等同于新的模型精度或正式性能验收。

## 快速索引

| Case | 状态 | 匹配键 | 主要知识差量 | 证据等级 |
|---|---|---|---|---|
| [20260911-glm53-flash-ppu-e2e](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md) | kept | sparse-indexer MQA；PPU-ZW810E；TP16；BF16 inputs；graph | 跨仓库迁移算子时必须同步切换 tune-config runtime，并直接断言 tuner 的实际 config 集合 | `reproduced` |

## Case：20260911-glm53-flash-ppu-e2e

### 环境与路径

- 模型/平台：GLM-5.3-Flash-BF16，PPU-ZW810E，TP16，
  `FULL_DECODE_ONLY`，前缀缓存关闭。
- 算子路径：`flaggems_vllm.fp8_fp4_mqa_logits` →
  `_fp8_fp4_mqa_logits_kernel`；故障发生在 Mixed 调度中的新 prompt 批次。
- 故障 shape：`M=2901,N=725,H=32,D=128`；直接算子验证另覆盖
  非对齐 `M=17,N=73,H=32,D=128` 和 graph `M=4,N=64`。
- dtype：q/k 为 BF16，scale/weights/output 为 FP32；layout 未单独冻结。
- 代码基线：FlagGems-vllm `9117ae501e84ecf0776fa7f84dd7c1dfe4d3538d`；
  修复提交并推送为 `f7443e776fc078318685dc8456ef5a8b2281d0f0`。
- 完整证据：[案例摘要](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md)、
  [优化事实状态](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

### 改动、边界与结果

- 根因是迁移后的算子仍导入 `flag_gems.runtime`，读取了 144 个候选，而不是
  FlagGems-vllm thead YAML 中的单个已验证配置；在线调优超过 vLLM 300 秒
  worker RPC timeout，导致 EngineCore 退出。
- 单变量改动为把 runtime 来源切换成 `flaggems_vllm.runtime`，并新增测试直接
  比较 tuner 的实际 config 与包内 runtime 返回值；thead 上进一步断言唯一配置
  `BLOCK_M=4,BLOCK_N=64,HEAD_BLOCK=16,num_warps=4,num_ctas=1,num_stages=2`。
- 模块测试 `2 passed, 20 skipped`；20 个既有用例因缺少 DeepGEMM/FP8
  reference 按原条件跳过。
- 直接算子验证：故障 shape 最大绝对误差 `3.815e-6`、最大相对误差
  `5.686e-7`；非对齐 shape 最大绝对误差 `2.384e-6`；graph capture 和两次
  replay 均通过。
- 服务级精确复现使用 32 个请求、总 prompt token `2901`：冷运行 32/32
  HTTP 200，立即复跑 32/32 HTTP 200、耗时 `1.18455 s`，服务保持健康。
  冷运行期间全库 DB 因其他 tuner 写入而变化，但 MQA 的中断 benchmark 表和
  config 表均未新增行；复跑前后全库 DB 不再变化。
- 模型既有 score-only gate 保持 `172/198=86.87% >= 86%`；本修复未重新运行
  198 题正式精度，因此不产生新的模型精度分数。

### 知识差量

- `prior_belief`：把 kernel、测试和 tune YAML 迁入目标算子包即可让其使用目标
  包的 vendor 配置。
- `outcome`：`refined`。
- `revised_belief`：`libtuner` 在装饰器创建时消费的是显式传入的 config；若
  runtime import 仍指向旧包，YAML 已迁移也不会生效。配置来源必须作为可测试的
  运行依赖，而不是根据文件位置推断。
- `future_first_check`：跨仓库迁移带 autotune 的算子时，先比较
  `kernel.fn.configs` 与目标包 `runtime.get_tuned_config()` 的完整签名，再运行
  冷 shape；不要先用服务超时或整库 DB 变化间接判断。

### 适用限制

当前证据只覆盖上述模型、PPU-ZW810E、TP16、配置、dtype 和三个验证 shape。
没有新的正式端到端性能 A/B，也没有重新运行完整模型精度；其他平台、dtype、
layout 和 shape 必须重新验证。

### 同案例追加证据：2026-10-19 官方上游迁移

[点43](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261019-upstream-migration-43.md)
将 FlagGems-vllm 更新到官方 `b4d3382`、Plugin 到 PR454 `f769696`，
保持 PPU/TP16/BF16/D128 与原 graph 参数。新上游 host 显式只接受 FP8/FP4，
而旧 PPU 调用传 BF16 Q/K；虽然 tiled dot/clean kernel AST 相同，入口仍会拒绝。
16K 服务回归中 fallback reference 产生 8GiB 的 `[M,H,N]` 临时张量后 OOM；
并非新的 MQA 多配置调优问题，原候选失败与旧服务恢复证据均保留。

限域兼容入口仅在 thead backend 导出，BF16/D128/scale 已折叠等条件检查后复用
上游相同 kernel，其余 dtype 仍调用原上游入口；计算无需 `[M,H,N]` 临时张量。
7 项接口合同、6 组设备边界/空维度、4 组非空输出与旧版逐位一致、变更输入
并填毒后的两次 graph replay 通过，实际 tuner 仍是包内单配置。修复后16K边界
与旧输出一致；正式模型精度、端到端收益尚未确认，不能据此宣布迁移验收通过。

`knowledge_delta=refined`：跨版本迁移不仅要核验 kernel/tuner 来源，还必须核验
host dtype/scale/layout 契约；相同 impl_id 或 kernel 不能证明入口兼容。
未来先对实际 BF16 调用直接执行目标入口，禁止以 fallback 成功代替目标实现命中。
证据等级为本模型边界内 `reproduced`，不是跨平台不变量。
