# fw-007：request-group index_put 同步因果探针

## 状态

`no_go_side_path` — 语义等价的 `index_fill_` 能消除 request-group 构造中的
同步，但该调用点不是 prof-005 的 `nonzero_numpy → item → index_put_` 热路径。
该实验作为旁路证据保留，未修改 Plugin 源码，也不据此计算 prof-005 收益。

## 源码定位

`PleShortConvAttentionMetadataBuilder.build()` 通过两次 advanced-index 赋值生成
request group：

```python
req_group[spec_req_idx] = 0
req_group[decode_req_idx_cpu.to(query_start_loc.device)] = 1
```

候选仅将赋值语义替换为一维整型 index 的 `index_fill_`，不改变
spec/decode/prefill 分组、原请求顺序或 token permutation。

后续按 profiler stack 逐帧回溯确认，prof-005 的目标链实际来自上游 vLLM
`qwen_gdn_linear_attn.py` 中的：

```python
initial_state[~prefill_has_initial_state, ...] = 0
```

该路径在 36 个 linear-attention 层中重复出现，另由 `fw-009` 单独验证。
因此本页的 request-group 结果不能冒充 prof-005 同步归因。

## 独立探针

覆盖 Prefill1、Mixed64、Decode64 和含 spec 的 Mixed64：

- 四组输出均 bit-exact。
- `index_fill_` 四组均通过 graph capture 和两次 replay。
- 原路径每调用为 2 次 `index_put_` / 2 次 stream sync；候选均为 0。
- 无 profiler host wall 从 `32.98–37.12us` 降到 `9.68–14.30us`，
  每调用节省 `22.82–23.30us`。

证据：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/diagnostics/fw007-index-put-index-fill-probe-01/result.json`，
SHA-256 `a2abe837c0391e1e3665eaebfe94cb33a34f6818fc034e610870d26cf6d9f073`。

## 决策

探针证明 request-group 构造存在可消除的同步，但它不是 prof-005 的目标调用点，
因此不再用 `36 层 × 193 step` 放大该结果。该旁路没有足够生产调用次数证据支持
至少 1% 的 P4K 收益，停止服务集成；真实 GDN 路径由 `fw-009` 评估。

## 运行状态

service56 按精确 PID/start-tick 停止并释放 PPU0–7 用于探针；
PPU8–15 上的保留 service50 始终 healthy。Plugin 文件仍为回退后 SHA-256
`3ae84180f7b5f4d70886c98f1d1afcf2255f8f7223a110397ec4894cf81a9a59`。
