# op-018 后续：QSA R4 row-group union/mask kernel 设计

状态：`design-ready-for-isolated-microbenchmark`。本文只做源码与实测证据审查，
没有修改远端源码、服务或优化状态。

## 1. 结论

首个可执行原型选择 `R=4`，不是复用率最低但代码最短的 `R=2`。

- op-018 的生产 `rows=4096` 样本中，R4 的精确 selected-set 复用率在
  Prefill/Mixed 分别为 `69.5122% / 69.4798%`，覆盖率分别为
  `100% / 99.8697%`。
- 每个 TP rank 有 3 个 query heads。R4 把 `4*3=12` 个 head lanes 放进
  当前 rows4096 已证明更合适的 `BLOCK_M=16`；R2 只使用 6/16 lanes，
  R8/R16 则必须把 tile 推到 32/64，显著放大 accumulator、寄存器和 dot
  工作量。op-015 已证明不能因为“小 tile 看起来浪费少”而忽略 PPU 上
  BLOCK_M16 的生产 rows 优势。
- R4 的 Prefill K/V token occurrence 从 `6,295,552` 降到 union 的
  `1,919,376`。按 BF16 K+V、head dim 256，即从 `6,446,645,248` bytes
  降到 `1,965,441,024` bytes，理想删除 `4,481,204,224` bytes。
- R4 的 membership workspace 比 R2 更小：在 8192-token direct-address
  bucket 下，`ceil(4096/4)*8192*4 = 32 MiB`；R2 需要 64 MiB。

R2 保留为编译时间、kernel duration 和并行度的因果对照。如果 R4 因单 program
循环过长、寄存器 spill 或有效并行度下降而失败，只允许把同一实现常量改为 R2，
不能同时改 BLOCK_N、membership 编码或排序方法。

## 2. 已核验的 live 边界

当前实际实现为：

```text
Plugin qwen3_8_flash_next.py::_run_qsa
  -> resolved qsa_sparse_paged_attention
  -> FlagGemsBackend.qsa_sparse_paged_attention
  -> flag_gems.fused.qsa.qsa_sparse_paged_attention
  -> _qsa_sparse_paged_gqa_kernel
```

目标 rank-local 契约：

```text
q                 BF16 [rows, 3, 256]
k_cache/v_cache  BF16 [blocks, 16, 1, 256]
logical_indices  int32 [rows, 2051]
block_table      int32 [requests, pages]
token_to_req     int32 [rows]
logical_positions int32/int64 [rows]
output            BF16 [rows, 3, 256]
```

当前 sparse kernel 的 grid 是 `[rows, 1]`，`BLOCK_M/N/D=16/16/256`，每行
进行 129 个 online-softmax tile。wrapper 位于
`/workspace/FlagGems/src/flag_gems/fused/qsa.py::qsa_sparse_paged_attention`；
模型调用点位于
`/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/models/qwen3_8_flash_next.py::_run_qsa`。
`QSAForwardMetadata` 已有 `token_to_req`、`logical_positions` 和
`query_start_loc`，所以不需要从 device tensor `.item()` 或重建 host request ID。

## 3. 精确语义与适用 guard

候选只在以下条件全部满足时启用，否则逐行执行与当前 kernel 等价的 fallback：

1. `q=[rows,3,256]`、单 KV head、BF16 K/V/Q、int32 `[rows,2051]` indices；
2. 四行都存在，`token_to_req` 相同且非负；
3. `logical_positions` 非负且逐行严格 `+1`；
4. 所有非负 logical token 小于静态 `TOKEN_BUCKET=8192`；
5. indices 由当前 `qsa_select_paged_tokens` 产生，因此每行非负 token 唯一。

第 5 条不是一般 `qsa_sparse_paged_attention` ABI 的性质，不能暗中应用到任意
调用者。当前 producer 的 TopK compressed-block index 唯一；每个 complete block
展开为互不相交的 4-token 区间，causal tail 来自未完成 block，也不与 complete
block 重叠。因此模型内部路径可以依赖唯一性，公共 wrapper 默认仍走原实现。

候选使用固定物理组 `[4g,4g+1,4g+2,4g+3]`，并在 kernel 内检查相同 request
和连续 position。它与 op-018 的“每个 request 段首对齐”统计略有差异，但不改变
正确性：跨 request 的物理组完整 fallback。对当前 Mixed 的两个 request runs，
最多只有一个边界组（4 行）失去复用；正式接入前应额外输出
`eligible_group_count/fallback_group_count`，不得仅用 op-018 的 coverage 代替命中证明。

“exact semantics”指 selected token 多重集合、causal/page-table 过滤和每行 softmax
数学语义不变，不承诺 bitwise 相同。共享 token 必须按统一 union 顺序处理，后续行的
FP32 online-softmax 累加顺序会变化；这需要数值 oracle，而不是 byte equality。

## 4. 最窄实现：direct-address membership，而不是 sort/unique

不要在 graph 内调用 `torch.sort/unique`，也不要物化 `[groups,R*TOPK]` 的 sorted
union。目标 P4K/D1K 的 logical token 小于 8192，可以使用 direct-address table：

```text
membership[g, token] : int32 bit mask
bit r == 1  <=>  group g 的第 r 行选择了 token
shape = [ceil(max_rows/4), 8192]
```

完整候选事务固定为三个 graph-safe kernel：

1. `_clear_qsa_group_membership_kernel`：把当前 groups 对应的 membership 和
   overflow flag 清零；
2. `_build_qsa_group_membership_kernel`：每个 `(group,row)` program 扫描该行
   2051 个 index，对 `membership[g,token]` 做 `atomic_or(1 << r)`；若出现
   `token>=8192`，对该组设置 overflow；
3. `_qsa_sparse_paged_gqa_group4_kernel`：每个 group 一个 program，读取 union
   token 的 K/V 一次，同时维护四行、每行三头的独立 online-softmax 状态。

三次 launch、workspace clear、membership build 都必须计入 candidate 时间。
direct-address table 避免 hash collision、probe 上限、非确定 compaction 和排序；
32 MiB clear 加约 64 MiB index/mask 流量，相对 R4 理想删除的约 4.48 GB K/V
payload 有明确的小量级，但只能由实测确认净收益。

### 4.0 三条 union 路线的选择

| 路线 | 是否选用 | 原因 |
|---|---|---|
| token-domain membership table + 原 occurrence scan | **选用** | P4K/D1K 有静态 8192 domain；direct address 无 collision/排序/compaction；用 bit mask 同时给出 union owner 和四行 membership；attention 仍按原 occurrence 顺序扫描 |
| leader（例如最后一行）+ additions | 暂不选 | op-018 只给 `|union|`，没有给 `|T_last|`、`|union-T_last|` 或“最后一行包含率”；69.5% 的全组复用不能证明任一行接近 union。若假设错误，会为 additions 再建 membership，复杂度并不低于 direct table |
| sort + unique/merge | 拒绝为首个原型 | 需要额外排序 workspace、compaction/prefix-sum 或二分 membership；graph 内地址和 launch 更多；排序还会改变全部行的累加顺序。它适合无静态 token domain 的通用实现，不是当前 P4K 的最窄证伪路径 |

这里的 token-domain table **不扫描 8192 个 slot 做 union compaction**。它只在
build 阶段作 membership scatter；attention 继续扫描四行原始 2051 occurrences，
用“最低 row bit 是 owner”把每个 union token 的 K/V load 激活一次。这样 direct
table 只承担 O(1) membership lookup，而不会把 8192-domain scan 乘进 dot/softmax。

若要重开 leader 路线，必须先加一项只读统计：对 R4 同时报告每个 leader choice
`sum_g |union_g - T_leader| / sum_g |union_g|`。只有某个固定 leader 在 Prefill 和
Mixed 都覆盖至少 90% union，且 additions 能保持无 sort 的 direct-address 构造，
才值得与本方案做单变量对照；当前证据不足以直接选它。

### 4.1 grid 与 lane layout

```text
clear grid:      [ceil(groups*8192/BLOCK_CLEAR)]
build grid:      [groups, 4]
attention grid:  [groups, NUM_KV_HEADS] = [1024, 1] at rows4096

group base row:  base = 4 * program_id(0)
head lane h:     row_in_group = h // 3, head_in_row = h % 3
valid head lanes h < 12
BLOCK_M/N/D:     16 / 16 / 256
```

attention kernel 仍使用 16-lane accumulator `[16,256]`，不引入 R8/R16 所需的
`[32,256]` 或 `[64,256]` FP32 state。

### 4.2 union owner 与 per-row mask

不需要 compact union。按行 0、1、2、3 的原始 index 顺序分别扫描；一个 token
由选择它的最小 row id 负责读取：

```python
bits = membership[g, token]
owner_r = (bits & ((1 << r) - 1)) == 0 and (bits & (1 << r)) != 0
head_uses_token = (bits & (1 << row_in_group)) != 0
score_mask = valid_token & owner_r & head_uses_token
```

因此每个 union token 的 page-table、K 和 V 只读一次；该 token 的 score/probability
同时更新所有选择它的行。后续行中重复出现的 occurrence 只执行 masked tile，不再读
K/V。四个 phase 总数仍是 `4*ceil(2051/16)=516`，与四个原 kernel 的总 dot tile
数相同；首个原型只验证“减少 K/V 读取”，不同时声称减少 tensor-dot 工作。

### 4.3 online softmax 状态

候选必须逐 head lane 保持独立：

```text
max_value  FP32 [16]
normalizer FP32 [16]
accumulator FP32 [16,256]
```

query 的缩放和 BF16 rounding point保持现实现：

```python
query = (query * softmax_scale * 1.4426950408889634).to(query.dtype)
```

对每个 union tile：

```python
scores = tl.dot(query, keys)
scores = tl.where(score_mask, scores, -1.0e20)
next_max = maximum(max_value, max(scores, axis=1))
alpha = exp2(max_value - next_max)
p = where(score_mask, exp2(scores - next_max[:, None]), 0)
accumulator = tl.dot(p.to(values.dtype), values,
                     acc=accumulator * alpha[:, None])
normalizer = normalizer * alpha + sum(p, axis=1)
max_value = next_max
```

每行的三个 heads 共用该行 membership，但 max/normalizer/accumulator 不共享。
无有效 token 时输出零，保持当前行为。

### 4.4 fallback

同一个 group kernel 处理 fallback，避免 candidate 和原 kernel 重复写 output：

- 若 full-group eligibility 或 token bucket guard 失败，phase `r` 只允许第 r 行的
  三个 head lanes，并按该行自己的 request 做 page translation；
- 尾部不足四行时仅处理存在的行；
- invalid request、invalid page、非连续物理页继续使用当前逐 token mask；
- fallback 不能读取 membership 来决定 token 集，必须直接消费原 indices，因而也
  能保护公共输入中的高 token id。

这样所有输入都有结果；只有 producer-unique + eligible + in-bucket group 获得复用。

## 5. 代码插点

### 独立 microbenchmark（第一步）

先仿照
`docs/cases/20260919-qwen38-flash-next-ppu-e2e/op015-qsa-sparse-group3-literal4-microbench.py`
新增一个自包含脚本，导入现有 `qsa_sparse_paged_attention` 作 baseline，并在脚本内
定义 clear/build/group4 三个 kernel。此阶段不改 FlagGems，也不启动服务。

### 仅在 microbenchmark 过门槛后的生产接入

1. 在 `/workspace/FlagGems/src/flag_gems/fused/qsa.py` 的
   `_qsa_sparse_paged_gqa_kernel` 后增加三个 kernel；在
   `qsa_sparse_paged_attention` 后增加独立的
   `qsa_sparse_paged_attention_group4(..., logical_positions, membership_workspace,
   overflow_workspace, out)`，不要改变公共函数默认行为。
2. 在 `flag_gems/fused/__init__.py` 显式导出新符号；在 Plugin
   `dispatch/backends/flaggems/flaggems.py` 增加同名窄转发。
3. 在 Plugin 模型 `_run_qsa` 中，仅对 Qwen3.8 target shape 调用新符号，并传
   `side_metadata.logical_positions[:num_tokens]`。原 resolved op 保留为 fallback。
4. membership workspace 必须预分配并在 12 个 QSA layer 间复用，不能在每层
   `register_buffer` 32 MiB。首选在共享 QSA metadata/model-runner workspace 中放一份
   `[ceil(max_num_batched_tokens/4),8192]` int32 buffer；确认所有 layer 同 stream
   顺序消费后再接入。若无法证明地址稳定且无跨 layer 并发，停止生产接入。

不应把模型路径或 served name写进 FlagGems dispatch guard；能力条件是上述 dtype、
shape、producer contract、workspace 和 logical-position metadata。

## 6. microbenchmark 契约

### 输入矩阵

| 维度 | 必测值 |
|---|---|
| rows | `64`, `4096`, `4094`, `4097` |
| group | R4 candidate；R2 只作后备因果对照 |
| selected set | op-018 Prefill 近似（cardinality 1537、R4 rho≈0.695）；Mixed 两 request 边界；零重叠；完全相同 |
| logical position | 连续；request 边界；不连续；`-1` padding |
| token range | `<4096`；`4096..8191`；单个 `>=8192` 触发整组 fallback |
| page table | 连续页；随机非连续页；`-1`/越界 physical page |
| execution | eager；graph capture；至少两次 changed-input replay |

生产分布最好直接从 op-018 同构生成器构造，不能复制用户 token 或完整遥测张量。

### correctness oracle

- baseline：当前 `qsa_sparse_paged_attention`，同一 Q/K/V/indices/table；
- FP32 小 shape reference：逐行 gather 有效 K/V，计算 GQA attention；
- 报告 `max_abs/max_rel` 和 BF16 elementwise mismatch；初始门槛
  `atol=rtol=0.05`，同时要求无 NaN/Inf；
- candidate 与 baseline 的有效 selected-token 多重集合必须一致；producer-contract
  测试额外断言每行非负 index 唯一；
- changed-input replay 必须改变 Q、K/V、indices、request boundary，防止 graph 只复用
  capture-time 地址或 membership。

### 计时

- PPU event/synchronize 方法与 op-015 相同；warmup 至少 20，正式至少 100 次，报告
  median/P90；baseline/candidate 交替测量；
- candidate 计时范围包括 workspace clear、membership build、group attention；
- 先分别报告三个 kernel 的诊断时间，再以完整 candidate 事务作唯一晋级指标；
- rows4096 同输入对 baseline/candidate 做 eager 与 graph 两套结果。

## 7. 晋级与停止条件

只有以下条件同时成立才允许改真实 FlagGems/Plugin 路径：

1. 全部 correctness、invalid page、request boundary、tail、bucket fallback 与
   graph changed-input replay 通过；
2. rows4096 graph 完整事务相对当前 baseline 至少 `+8%`；
3. R4 target distribution 的 group eligibility 至少 99%，且 overflow/fallback group
   计数与构造预期一致；
4. 没有编译超时、寄存器 spill 导致的明显反常、kernel watchdog 或图地址漂移。

立即停止 R4 并只允许做 R2 单变量对照的条件：

- rows4096 candidate 不快于 baseline，或 P90 退化；
- group attention 单 kernel 时间超过四个 baseline row kernel 的等价总时间；
- PPU 编译器把 `[16,256]` accumulator spill 到不可接受的本地/全局内存；
- 1024-program grid 的并行度不足成为新瓶颈。

R2 对照仍未达到 rows4096 `+8%` 时，整个 row-group direct-address 路线停止；不得
继续扫 R8/R16，因为它们改变 BLOCK_M/寄存器机制，且当前证据没有支持该额外成本。

即使 microbenchmark 通过，后续仍必须验证 graph 服务命中、capture+2 replay、最小
正确性、P4096 Mixed 无 profiler 端到端，以及 candidate/revert；profiler-on 或遥测
时间不能作为性能收益。当前 inherited GPQA `170/198=85.86% < 88%` 仍阻塞正式
精度验收，算子成功不能解除该 gate。

## 8. 证据边界

- op-018 summary：
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op018-qsa-overlap-summary-001.json`。
- Prefill/Mixed 都是 rank0、rows4096，Mixed `request_runs=2`；遥测时间包含同步，
  只证明 selected-set 结构，不是性能数据。
- 当前设计只覆盖 PPU/TP8/BF16、Qwen3.8 target QSA shape 和 graph workload。
  32K/其他平台/其他 QSA producer 不在结论范围内。
