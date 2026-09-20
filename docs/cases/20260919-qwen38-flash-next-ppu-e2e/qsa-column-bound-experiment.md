# QSA 实验 A：静态评分列上界

状态：`draft / not applied / not run`

产物：

- standalone microbenchmark：
  [qsa-column-bound-microbench.py](qsa-column-bound-microbench.py)
- 最小 FlagGems API 补丁草案：
  [qsa-column-bound-draft.patch](qsa-column-bound-draft.patch)
- live 路径证据：
  [qsa-live-path-readonly.md](qsa-live-path-readonly.md)

本轮没有应用补丁、修改远端服务或发送推理请求。

## 假设

当前 `qsa_select_paged_tokens` 总是用
`page_table_width * compressed_page_size` 作为 logits columns。live 服务的
`max_model_len=80000`、ratio=4 对应约 20000 columns；P1024/D128 的最大可见
compressed groups 仅 288，但 TopK 需要至少 512 columns。将评分宽度固定为
512 可保持 TopK/expand 契约，同时显著减少无效 program 和 Prefill workspace
chunk 数。

静态 bound 的安全条件为：

```text
block_topk <= static_score_columns <= cache_capacity
max_visible_groups_for_every_row <= static_score_columns
```

其中 `block_topk=2048/4=512`。bound 必须由 scheduler 或 graph bucket 在 host
侧保守给出，不能在 capture 内读取 device tensor 或 `.item()`。

## Benchmark tensor schema

| tensor | schema |
|---|---|
| indexer query | BF16 `[rows, 4, 128]` |
| compressed K | BF16 `[1250, 16, 1, 128]`，capacity 20000 |
| compressed table | int32 `[requests, 1250]`，contiguous |
| request mapping | int32 `[rows]` |
| query positions | int64 `[rows]` |
| sequence lengths | int32 `[requests]` |
| selection output | int32 `[rows, 2051]` |
| sparse query | BF16 `[rows, 3, 256]` |
| main K/V | BF16 `[main_pages, 16, 1, 256]` |
| main block table | int32 `[requests, main_pages]`，contiguous |
| sparse output | BF16 `[rows, 3, 256]` |

rows `1/8/64` 模拟 P1024/D128 的 late decode，position=1151；rows 4096 模拟
四个 P1K 请求组成的一个 Prefill 调度步，position 分别为 0..1023。

为控制显存，多个 synthetic request 共享同一组只读 physical cache pages；这不
影响 kernel 的 request-relative logical mapping 语义，但不代表真实请求的缓存
内容分布。真实候选晋级前必须用采集的 metadata shape 再测。

## 比较内容

每个 rows shape 分别运行：

1. full：`num_columns=20000`；
2. bounded：
   `max(512, round_up(max_sequence_length // 4, 32))`，当前均为 512；
3. 完整 selection：MQA scoring → TopK512 → expand 到 2051；
4. downstream sparse：`[rows,3,256]` GQA over selected indices；
5. eager event timing；
6. full/bounded 各自 warmup 后 capture，并 replay 两次；
7. graph replay timing。

TopK 对 `-inf` padding 的 tie 顺序无保证，因此 selection 正确性比较每 row 的
有效 token 集和 `-1` 数量，而不是直接比较 padding block 顺序。downstream
sparse output 使用 BF16 `atol=0.05, rtol=0.05`；同一 graph 的 capture 与两次
replay 必须逐位一致。

## 运行命令草案

只能在服务释放目标卡后、隔离的优化容器进程中运行：

```bash
python /path/in/container/qsa-column-bound-microbench.py \
  --rows 1,8,64,4096 \
  --capacity 20000 \
  --warmup 5 \
  --repeat 20
```

脚本直接复用现有 `qsa_mqa_paged(num_columns=...)`、
`expand_qsa_block_indices` 和 `qsa_sparse_paged_attention`，不要求先应用补丁。

## 补丁边界

补丁只为 `qsa_select_paged_tokens` 添加末尾可选参数
`static_score_columns=None`：

- 默认 `None` 完全保持当前 full-capacity 行为；
- 显式值必须在 `[block_topk, capacity]`；
- 同一个值同时控制 MQA `num_columns` 和 128 MiB workspace chunking；
- 不在算子内部计算 device max，不引入 host sync；
- 不改 Plugin/model caller。只有 standalone 结果通过后，才设计 scheduler/graph
  bucket 到该参数的传递链路，该部分属于独立 framework 实验。

补丁已在候选容器的 `/workspace/FlagGems` 当前 working tree 上通过只读
`git apply --check`，没有执行 apply。

## 晋级与停止条件

晋级：

- 四个 rows shape 的有效 selection 集完全一致；
- downstream sparse output 通过预冻结 BF16 阈值；
- full/bounded 都 capture 成功且各自 replay 两次逐位稳定；
- rows64 Decode、rows4096 Prefill 的完整 selection 至少提升 5%；
- 完整 selection+sparse transaction 无超过案例守护边界的回退。

立即停止：

- 任一 row 的有效 token 集、`-1` 数量或 downstream output 超阈值；
- graph capture/replay 失败或为计算 bound 引入 host sync；
- bound 小于任一 row 的 visible groups；
- 收益只来自 synthetic page sharing，换真实 metadata 后消失；
- 应用层需要每 step 重建 graph 或产生过多 bucket，抵消 kernel 收益。

## 适用性限制

- 这是 P1024/D128 诊断形状的证伪脚本，不是四场景正式性能结果。
- P4K/P16K/P32K 需要各自更大的保守 bound；当 visible groups 超过 512 时不能
  沿用 P1K 的 512。
- 正式 P1024/D1024 的序列最终达到 2048 token，visible groups 为 512，仍满足
  bound=512；若使用 prefix cache、spec decode 或不同调度上界，必须重新证明。
- standalone graph 只证明算子 transaction；最终仍需全模型 graph capture 和
  至少两次 replay。
