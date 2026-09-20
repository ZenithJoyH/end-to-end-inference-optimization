# Qwen3.8 重复 standard slot-mapping 消除草案

> 状态：未应用的实验草案。不是候选结论，不能作为性能或正确性证据。

## 基础事实

- 目标 Plugin：`/workspace/vllm-plugin-FL-qwen38-adaptation`
- branch / revision：`support-qwen3.8-flash` / `939600b323c02c21916f1f76bfb4cd8c2b02578d`
- 运行时实际导入：`/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl`
- 草案依赖当前工作树中已存在的 `common_slot_mapping.py` T-Head replay 同步改动和 `model_runner.py` blocking event 改动；应用前仍需重新核对 dirty diff，不能覆盖它们。

Qwen3.8 的每个正常执行 step 目前有两个 slot producer：

1. `_prepare_inputs()` 在 `model_runner.py:2232` 调用 vLLM `MultiGroupBlockTable.compute_slot_mapping()`；
2. graph dispatch 之后，`execute_model()` 在 `model_runner.py:4492` 调用 `_run_common_slot_mapping()`。

后者通过 `dispatch/backends/flaggems/impl/common_slot_mapping.py:23-42` 遍历所有 cache group，再次写入同一 `table.slot_mapping.gpu`，并额外刷新 graph padding block-table row 和 `num_computed_tokens`。Qwen3.8 包含 main attention、QSA raw/compressed side cache、GDN 和 PLE state 等多种 cache spec，重复调用会放大为每 step 多个 kernel launch。

## 草案设计

草案文件：`qwen38-skip-duplicate-standard-slot-mapping-draft.patch`

改动只改变 slot producer 所有权：

- `common_slot_mapping_graph is None`：保留原生 standard producer，非 Qwen3.8/PLE 路径行为不变。
- `common_slot_mapping_graph is not None`：跳过 standard producer，由稍后的 `_run_common_slot_mapping()` 独占写入权。
- graph key 缺失时，`CommonSlotMappingGraphRunner.run()` 会同步执行 eager `compute()`，因此草案不依赖 graph 必须命中才有 slot mapping。

将分支抽成小方法是为了用 Mock 直接证明“有 common owner 时 standard 调用次数为 0”，不需要构造整个 ModelRunner。

## 应用前门禁

1. 只向优化容器的私有 Plugin 副本应用，不得应用到源容器共享目录。
2. 再次记录 Plugin HEAD、branch、`git status --short` 和完整 dirty patch。
3. 先执行 `git apply --check <draft.patch>`；上下文不匹配时人工重建，不用 `--reject` 或强制应用。
4. 保存应用后 patch SHA256 与反向回退命令。

## 最小正确性测试

在优化容器私有 Plugin 副本中执行：

```bash
python -m pytest -q \
  tests/qwen3_8_flash_next/test_runner_ngram.py \
  tests/qwen3_8_flash_next/test_common_slot_mapping_graph.py
```

必须证明：

- 新的 unit test 在 common owner 存在时观测到 standard call count = 0；
- common owner 不存在时 call count = 1，且参数原样传递；
- common-slot eager、graph capture 及 changed-input replay 全部通过。

然后在 PPU graph 服务做两组固定 seed 护栏：

1. 同 shape 至少两次 replay；
2. batch/request churn：`1 -> 8 -> 32 -> 1 -> 32`，包含请求结束、row 复用和新请求替换；
3. 每组对比 baseline/candidate 的 token IDs、终止原因、空输出和服务健康；
4. graph 无 `Common slot mapping graph ... was not captured` warning；即使人工触发一次 missing-key，其 eager fallback 也必须生成正确 slot/state metadata。

任一 token 差异、PLE/GDN/QSA state 错位、非确定性、挂起或 graph fallback 异常都立即停止并回退。

## 命中证据

候选不能只用“代码分支存在”证明生效，需同时保留：

1. 单元测试中 standard call count `0/1` 的断言结果。
2. baseline 与 candidate 的同 shape Decode trace：
   - baseline 稳态 step 含 vLLM `_compute_slot_mapping_kernel`；
   - candidate 的 Qwen3.8 稳态 step 不再含该 standard kernel；
   - candidate 仍包含 FlagGems `_compute_slot_mapping_graph_kernel` 和 `_compute_num_computed_tokens_kernel`，或对应 graph replay node。
3. candidate 服务记录的 Plugin 导入路径、revision、patch SHA 和 graph capture/replay 成功证据。

如 PPU profiler 无法在 graph replay 中展开子 kernel，允许在孤立实验副本中加一次性调试计数器，记录 `_compute_standard_slot_mapping_if_needed()` 的 `False` 分支命中；计数器不进入最终候选补丁。

## 性能证伪

- 首个实验：P1K Decode milestone，固定 graph 模式、TP8、C8/C64、N、warmup/repeat 及所有其他启动参数，仅切换本补丁。
- 主观测：TPOT/ITL 和 output-token throughput；守护 TTFT、错误率、完成请求数及 rank 拖尾。
- 同步记录 steady-state 每 step 的 standard/common slot kernel 数量及 host launch gap。Profiler-on 数字不作为正式收益。
- 只有无 profiler 的三次重复超过预冻结噪声阈值，并在 P1K Mixed 中守住 TTFT/TPOT，才保留。若中位收益低于 1% 或不能与 standard kernel 消失建立因果，停止该候选。

## 风险与回退

主要风险是 standard producer 在当前 PPU runtime 中隐含了未文档化的 stream ordering 或初始化效果。虽然静态源码显示它只写 slot mapping，仍必须以 changed-input graph replay 和 request churn 否证。

回退时在同一私有副本对草案执行反向应用，重建服务并重新验证导入路径和 graph capture；不使用 `git reset --hard`，不丢弃原有 dirty 改动。
