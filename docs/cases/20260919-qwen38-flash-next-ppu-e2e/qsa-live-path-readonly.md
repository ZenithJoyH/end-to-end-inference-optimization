# Candidate 容器 QSA live path 只读核验

日期：2026-09-19  
容器：`qwen3.8-flash-opt-candidate-20260919`  
状态：只读核验；未应用补丁、未修改服务、未发送推理请求

## 1. 运行事实

- 容器运行中，镜像为 `qwen3.8-flash-adapted:20260919-e2e-source`。
- 服务端口 8030，TP=8，BF16，`max_model_len=80000`，
  `max_num_seqs=64`，`max_num_batched_tokens=4096`，graph 模式为
  `FULL_AND_PIECEWISE`。
- 实际导入：
  - Plugin：`/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl`
  - FlagGems：`/workspace/FlagGems/src/flag_gems`
  - FlagGems-vllm：`/workspace/FlagGems-vllm/src/flaggems_vllm`
- revision：Plugin `939600b323c0`；FlagGems `2b1e5cfdbd22`；
  FlagGems-vllm `5865ed53b183`。
- 独立只读 dispatch 解析结果：
  - `qsa_mqa_paged -> default.flagos`
  - `qsa_select_paged_tokens -> default.flagos`
  - `qsa_sparse_paged_attention -> default.flagos`
  三者均转发到
  `vllm_fl.dispatch.backends.flaggems.flaggems.FlagGemsBackend`；T-Head
  native extension bundle 不完整，vendor 实现被禁用。

## 2. 实际定义与调用链

### MQA 选块

定义：
`/workspace/FlagGems/src/flag_gems/fused/qsa.py:23`
`_qsa_mqa_paged_kernel`。

调用链：

```text
QSAIndexer.forward
  -> QSAIndexer._select
  -> resolved qsa_select_paged_tokens
  -> FlagGemsBackend.qsa_select_paged_tokens
  -> flag_gems.fused.qsa_select_paged_tokens
  -> qsa_mqa_paged
  -> _qsa_mqa_paged_kernel
  -> torch.topk(k=512)
  -> expand_qsa_block_indices
```

模型绑定位置：
`/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/models/qwen3_8_flash_next.py`
的 `QSAIndexer._select`；backend 转发位置为
`vllm_fl/dispatch/backends/flaggems/flaggems.py:95-98`。

### Sparse GQA

定义：
`/workspace/FlagGems/src/flag_gems/fused/qsa.py:191`
`_qsa_sparse_paged_gqa_kernel`。

调用链：

```text
Qwen3_8FlashNextQSAAttention.forward
  -> qwen3_8_flash_next_qsa_with_output
  -> Qwen3_8FlashNextQSAAttention._run_qsa
  -> resolved qsa_sparse_paged_attention
  -> FlagGemsBackend.qsa_sparse_paged_attention
  -> flag_gems.fused.qsa_sparse_paged_attention
  -> _qsa_sparse_paged_gqa_kernel
```

模型调用位置：同一模型文件 `_run_qsa`，约 2285 行；backend 转发位置为
`vllm_fl/dispatch/backends/flaggems/flaggems.py:110-113`。

## 3. 当前目标 shape、dtype 和布局

模型 `text_config`：主 attention 24 Q heads、2 KV heads、head dim 256；
indexer 为 4 Q heads、1 KV head、head dim 128、budget 2048、ratio 4。

TP8 后每 rank：

- MQA：query `[rows, 4, 128]` BF16；compressed K cache
  `[blocks, page, 1, 128]` BF16；logits `[rows, columns]` FP32；TopK 为
  `2048/4=512`；最终 indices `[rows, 2051]` int32。
- Sparse GQA：query `[rows, 3, 256]` BF16；K/V cache
  `[blocks, page, 1, 256]` BF16；indices `[rows, 2051]`；output 与 query
  同 shape/dtype。KV head 在 TP rank 间复制，因此 `GROUP_SIZE=3`。
- 主 K/V cache 必须是 vLLM 0.24 的逻辑
  `[blocks, 2, tokens, heads, dim]`；模型用 view 得到 K/V，不支持较新的
  packed 4-D ABI，避免 cache store 写进临时副本。
- 两个 kernel 都消费显式 tensor stride；MQA cache head 固定为 1，kernel
  仅传 block/token/dim stride。metadata 为 rank-2 block table 和逐 row
  request/position；模型路径生成 int32 indices，position/length 可为
  int32/int64。

当前 launch：

- MQA grid `[rows, ceil(columns/32)]`，`BLOCK_N=32`、`BLOCK_D=128`、
  `num_warps=4`。每个 head 顺序加载同一 K tile 并做 FP32 scalar reduction，
  四头 ReLU(dot) 求和后除以 `sqrt(128)`。
- Sparse grid `[rows, 1]`，`TOPK=2051`、`BLOCK_N=16`、
  `BLOCK_D=256`、`num_warps=4`、`num_stages=2`。由于
  `GROUP_SIZE=3`，wrapper 固定 `BLOCK_M=max(16,next_power_of_2(3))=16`；
  13/16 head lanes 被 mask，仍参与 tile 形状和 dot 计算。

## 4. Graph 约束

- 模型 import 时使用 `resolve_op` 固定函数对象，capture/replay 间不会重新
  dispatch。
- QSA indexer 的最终 selection buffer 与 sparse output 由模型预分配；但
  `qsa_select_paged_tokens` 在 capture 内创建 logits、visible-blocks 和 TopK
  输出。它们可进入 graph memory pool，但 replay 要求相同 shape、分支、
  Python chunk 数和地址生命周期。
- `rows_per_chunk` 由静态 `columns` 和 128 MiB workspace 决定；改变
  `columns` 会改变 Python loop 次数和 graph，需要按固定 bucket capture，不能
  在 capture 内用 `.item()`/host sync 动态求最大可见长度。
- Sparse 的 `TOPK`、`BLOCK_M/N/D` 都是 constexpr。切换有效 width 或 tile
  会产生不同 kernel/graph variant；必须 warmup 编译后 capture，并 replay
  至少两次。
- 现有 graph trace 已实际命中两 kernel，但这不证明任何新 backend 的 graph
  兼容；候选仍须单独验证命中、capture 和两次 replay。

## 5. Live trace 证据

证据目录：
`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-001-maxseq64-bt4096-mixed-capture/`

workload 是诊断场景 P1024/D128/C64/N64；不是最终 N128 full 验收。rank0：

- `_qsa_mqa_paged_kernel`：2124 calls，3.065 s，avg 1.443 ms，
  17.62% device time。
- `_qsa_sparse_paged_gqa_kernel`：1740 calls，2.259 s，avg 1.299 ms，
  12.99% device time。
- 外层 `vllm::qwen3_8_flash_next_qsa_with_output` 共 204 calls，device total
  5.607 s。

rank7 的两 kernel 累计时间几乎相同，说明不是单 rank 偏斜。

调用次数差为 `2124-1740=384`。该模型有 12 个 QSA 层，P1024/N64 在
4096-token 调度上产生 16 个 Prefill batch；每个 Prefill batch 若 MQA 被切为
3 个 workspace chunk，则相对 sparse 每层多 2 次 launch：
`12 * 16 * 2 = 384`，与 trace 完全一致。

`max_model_len=80000`、ratio=4 对应约 20000 compressed columns；
128 MiB / (`20000 * sizeof(float)`) 得到约 1677 rows/chunk，4096 rows 正好
需要 3 chunks。因此可以强推断：当前 P1K workload 的 MQA 按约 20k 最大
容量发 grid，而实际可见完整 group 只有约 256；即使无效列不读 K，也会执行
program、Q load、mask、reduction 和 `-inf` store。这比单纯把 scalar dot
替换为 tensor dot 更应先证伪。

## 6. 最小可证伪实验

所有实验需在隔离进程/优化容器内做，不改当前 live 服务；本只读核验未执行。

### 实验 A：安全收窄 MQA columns（首选）

用同一组真实 shape 和预分配 tensor，调用现有 `qsa_mqa_paged`：

1. baseline：`num_columns=20000`（实际 page-table capacity）；
2. candidate：P1K 使用
   `num_columns=max(block_topk=512, ceil(max_visible/32)*32)`；
3. 分别覆盖 rows `1/8/64/4096`，warmup 后测 eager，并 capture + replay 2 次；
4. 对 candidate logits 补 `-inf` 后执行同一 TopK+expand，比较最终 token
   indices（忽略 TopK 对不可见 `-inf` 项的任意次序，比较有效 token 集和
   `-1` 数量）；
5. 下游 sparse output 用 BF16 reference/tolerance 比较。

停止条件：任何有效 selected token 不一致、graph 需要 host sync、或主要 shape
完整 select transaction 收益低于 5%。若成立，再设计由 scheduler/graph bucket
提供 capture-safe width hint；不要在模型 forward 里 `.item()`。

### 实验 B：现有 Qwen4 tl.dot MQA 替换

FlagGems-vllm 已提供
`qwen4_qsa_mqa_paged_dot`，精确支持 BF16 `[rows,4,128]`、cache
`[...,1,128]`、ratio4，正好命中 live shape。保持 columns 相同，比较当前
scalar kernel 与 tl.dot kernel 的 logits、visible blocks、最终 TopK/expanded
indices，以及 eager/graph+2 replay 时间。

此实验属于 `operator/replace`，必须与实验 A 分开，避免把 grid 收窄收益算到
kernel replacement。若 PPU 上 BLOCK_H=16 的 padding 使 tl.dot 不快，立即停止。

### 实验 C：Sparse width/tile（后续）

先只做 microbenchmark：固定 `[rows,3,256]`，比较 `BLOCK_N=16/32/64`；
另在 P1K 证明 indices 有效项位于前缀后，比较 `TOPK=2051` 与固定 bucket slice
（例如 1155/2051）的最终 output。任何数值或 graph replay 差异即停止。

`BLOCK_M=16` 对 group3 的 13 个 padding lanes 是明确浪费，但直接改成 3 不满足
常规 `tl.dot` tile 约束；在没有 microbenchmark 证据前，不应先投入重写。

## 7. 只读证据命令

```bash
ssh PPU-01 "docker inspect -f '{{.State.Status}} {{.Config.Image}}' qwen3.8-flash-opt-candidate-20260919"
ssh PPU-01 "docker exec qwen3.8-flash-opt-candidate-20260919 ps -ef"
ssh PPU-01 "docker exec qwen3.8-flash-opt-candidate-20260919 grep -R 'def _qsa_mqa_paged_kernel\|def _qsa_sparse_paged_gqa_kernel' -n /workspace/FlagGems /workspace/FlagGems-vllm"
ssh PPU-01 "docker exec qwen3.8-flash-opt-candidate-20260919 sed -n '1,790p' /workspace/FlagGems/src/flag_gems/fused/qsa.py"
ssh PPU-01 "docker exec qwen3.8-flash-opt-candidate-20260919 grep -R 'qsa_mqa_paged\|qsa_sparse_paged_attention' -n /workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl"
ssh PPU-01 "docker exec qwen3.8-flash-opt-candidate-20260919 sed -n '1,80p' /mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-001-maxseq64-bt4096-mixed-capture/summaries/rank0.txt"
```

dispatch impl-id 使用独立 Python 进程调用
`get_default_manager().ensure_initialized()` 和 `_resolve_impl()`；只解析 registry，
未调用任何模型或算子。
