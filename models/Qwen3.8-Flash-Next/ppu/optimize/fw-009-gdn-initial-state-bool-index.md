# fw-009：GDN prefill initial-state 布尔索引同步探针

## 状态

`no_go_before_service_implementation` — 精确命中 FlagGems 的候选可把每次调用的
2 个 stream sync 降为 0，但按 prof-005 调用次数计算的 P4K/D128 乐观收益上界
约 0.51%，低于预冻结的 1% 服务集成门槛；未修改 vLLM 或 Plugin 源码。

## 真实调用点

prof-005 的 `_local_scalar_dense → item → nonzero_numpy → index_put_` stack 来自：

`/usr/local/lib/python3.12/site-packages/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py`

```python
initial_state[~prefill_has_initial_state, ...] = 0
```

Plugin 的 `Qwen38GatedDeltaNetAttention` 继承这段 upstream prefill 实现，仅特化
decode；36 个 linear-attention 层与 profiler 计数吻合。第一版原生 PyTorch 探针
没有复现服务 dispatch，保留为无效归因证据；第二版显式启用 FlagGems
`index_put_/_index_put_impl_/nonzero_numpy` 后才是有效结果。

## 精确探针

按 TP8 每请求状态 shape `[6,128,128]` 覆盖 B1 无初态、B1 有初态、B4 mixed
和 B64 mixed，比较原布尔索引、`masked_fill_` 与预计算整型索引 `index_fill_`：

- 全部 eager 输出 bit-exact，并包含 NaN 保留检查。
- 两个候选均完成 graph capture 与两次 replay；若空索引导致 empty-graph warning，
  仍不把微测代替服务 graph 门禁。
- 原 FlagGems 路径每调用命中 1 次 `index_put_`、1 次 `nonzero_numpy`、
  1 次 `item/_local_scalar_dense` 和 2 次 `cudaStreamSynchronize`；两个候选为 0 sync。
- 生产相关的 B1 无初态 host wall：原路径 `135.1458us`，`masked_fill_`
  `101.1551us`，预计算索引 `index_fill_` `33.2344us`。

有效结果：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/diagnostics/fw009-gdn-bool-index-probe-02/result.json`，
SHA-256 `496c0675c8dc666e6da32c2e91f62bd2388ca4bbf1efb97daf92d382b9711488`；
trace SHA-256 `b9c3c43cc3ef244b8fffcf4c1495c2a0aaf3c86188d3715975eaaa9435667412`。

## 收益上界与边界

prof-005 每 rank 的该路径计数为 Prefill/Mixed/Decode `36/2268/36`，合计
`2340 = 36 × (1 + 63 + 1)` 次。用 B1 无初态最优候选的
`135.1458 - 33.2344 = 101.9114us` 乐观放大：

`101.9114us × 2340 = 0.2385s`。

同配置 P4K/D128 约 46.35s，因此上界约 0.51%。该估计假设全部 host-wall 节省
都落在 critical path，且没有计入 CPU 索引传输到设备的成本，已属乐观。
另外真实调用点位于默认只读的上游 vLLM；即使可在 Plugin 覆盖 prefill，当前收益
也不足以承担实现和回归风险。因此停止集成，转向 common-slot cached64 graph
回放同步的因果分离。
