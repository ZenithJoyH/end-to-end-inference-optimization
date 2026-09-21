# QSA TopK `cudaStreamSynchronize` 独立微探针草案

状态：`draft / not run / no remote changes`

脚本：
[qsa-topk-sync-microprobe-draft.py](qsa-topk-sync-microprobe-draft.py)

## 目标与已有证据

本实验只验证一个问题：PPU native `torch.topk/mbtopk` 是否为每个 QSA
score chunk 引入 3 次 `cudaStreamSynchronize`。

已有 rank0 phase summary 的计数关系是：

- Prefill/Mixed graph：`_qsa_mqa_paged_kernel=540`、
  `cudaStreamSynchronize=1620`，恰好 `3:1`；
- Decode graph：`1532` 对 `4735`，减去 `3*1532` 后残留 `139`；
- 全局：`2124` 对 `6572`，减去 `3*2124` 后残留 `200`。

残留量与每 step 的
`common_slot_mapping.py -> current_stream().synchronize()` 同量级；
`prepare_inputs_event.synchronize()` 包装的是 `cudaEventSynchronize`，不属于本实验
计数。

现有 trace 带来的服务时长从 27.78 秒增至 45.74 秒，因此 trace 中同步累计时间
只能用于归因，不能直接当作可回收的端到端时间。

## 形状

默认覆盖笛卡尔积：

| rows | 语义 |
|---:|---|
| 64 | P4K Decode 并发行数 |
| 4096 | `max_num_batched_tokens=4096` 的 Prefill 调度步 |

| score columns | 语义 |
|---:|---|
| 1024 | 4096 token / compression ratio 4 |
| 1280 | P4K+D1K 的 5120 token / compression ratio 4 |

固定 `k=512`，来自 `token_topk=2048 / compression_ratio=4`。logits 使用 QSA
scoring 的真实 dtype FP32。四组形状都只产生一个 TopK，因此一次微探针 TopK
对应一次 QSA score-chunk TopK。

这里必须区分“语义可见列数”和“实际传给 TopK 的 logits 宽度”。案例现有记录同时
包含 `static_score_columns=8448` 以及 P4K/P5120 的可见宽度 1024/1280。
运行前应从当次服务 manifest 或 shape trace 核对实际 logits shape：

- 实际宽度为 1024/1280：使用默认值；
- 实际仍为 8448：追加 `--columns 1024,1280,8448`；
- 未收窄且仍按完整 cache capacity 运行：追加 20000。

不得用模型最大长度反推值覆盖实际运行证据。

## 探针设计

每个 shape 测四个 block：

1. eager `torch.topk(..., out=...)`；
2. eager control：同 shape 的 `torch.add(..., out=...)`；
3. TopK CUDA graph replay；
4. control CUDA graph replay。

每次调用放在独立 `record_function` 区间，并在区间末尾记录、等待一个 blocking
CUDA Event。这个等待对应 `cudaEventSynchronize`，用于保证异步 kernel 落在区间
内，不会向被测的 `cudaStreamSynchronize` 计数增加 1。

脚本自动输出：

- `aten::topk` 数量与时间；
- mbtopk kernel 数量、按 kernel name 的计数及累计时间；
- `cudaStreamSynchronize` 数量与累计时间；
- control 扣除后的每 TopK 同步次数；
- 无 profiler 的 host wall/device event 时间；
- graph capture 和 replay 正确性；
- trace、脚本 SHA 和唯一 `result.json`。

control 用于识别 profiler、event wait 或 graph replay 自身产生的同步。正式判断用
`topk_sync_count - control_sync_count`，不使用 trace 总量。

## 运行草案

只允许在服务已经释放、独占且确认空闲的卡上运行。脚本要求显式确认参数，并拒绝
覆盖已有输出目录：

```bash
python qsa-topk-sync-microprobe-draft.py \
  --rows 64,4096 \
  --columns 1024,1280 \
  --k 512 \
  --warmup 5 \
  --repeat 8 \
  --device-index 0 \
  --output-dir /absolute/unique/qsa-topk-sync-probe-001 \
  --acknowledge-isolated-device
```

若真实 shape 是静态 8448，再创建新的唯一输出目录运行：

```bash
python qsa-topk-sync-microprobe-draft.py \
  --rows 64,4096 \
  --columns 8448 \
  --k 512 \
  --warmup 5 \
  --repeat 8 \
  --device-index 0 \
  --output-dir /absolute/unique/qsa-topk-sync-probe-8448-001 \
  --acknowledge-isolated-device
```

默认只采 128 次短调用，关闭 stack、shape 和 memory profiling，避免再次生成多
GB 的 8-rank trace。它不启动、停止或连接服务，也不导入 vLLM、Plugin 或
FlagGems。

## 判定

支持假设：

- control 的 `cudaStreamSynchronize` 为 0；
- marker 数量等于 repeat；
- TopK 命中 mbtopk kernel；
- 扣除 control 后，canonical Prefill `(4096,1024)` 与 late Decode
  `(64,1280)` 均为精确 `3.0 sync / TopK`；
- 另外两组交叉 shape 结果一致。

证伪：

- control 为 0 且 mbtopk 命中，但四组 eager 的扣除后比率均不是 3；或
- 同一 shape 中同步数随 graph replay/control 数量变化，而不随 TopK 数量变化。

以下属于不确定，不能写成证伪：

- 没有命中 mbtopk；
- marker 未覆盖设备 kernel；
- control 自己产生 stream sync；
- graph capture 失败；
- 1024/1280 与实际服务 logits width 不一致。

如果 eager 为 3、graph replay 为 0，说明同步发生在 mbtopk launch/capture，而不
是 graph replay；还需要对 PPU graph capture/分段机制做单独归因，不能直接外推
到服务 trace。如果 eager 和 graph 都为 3，才支持“每次运行中的 QSA TopK 均有
3 次同步”。

## 风险与停止条件

- profiler 扰动显著：同步累计时间只比较同一次短 probe 的 TopK/control，不用于
  推算端到端加速比。
- `out=` 形式用于预分配和 graph capture；若实际服务落到不同 native overload，
  必须补做返回 tuple 的 eager 对照。
- synthetic logits 只验证 runtime 行为，不证明替换 TopK 的数值正确性、tie 顺序
  或服务收益。
- 任一 OOM、device error、hang、graph capture/replay 不稳定立即停止；不在同一
  进程继续测其他 shape。
- 如果独立 probe 不复现 3:1，停止 TopK 同步优化，不先写替换 kernel；转而给
  common-slot sync、graph wrapper 和 PPU runtime replay 做短范围调用栈归因。
- 如果复现 3:1，下一步也只能设计 graph-safe async TopK 候选，并覆盖 ties、
  `-inf` padding、values/indices、capture 与至少两次 replay；任何 indices/value
  差异或正式 Mixed 守护项回退都立即回退。
