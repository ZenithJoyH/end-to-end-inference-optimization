# op-020：QSA producer-integrated R4 captured transaction 设计

## 结论与边界

本设计只解决 op-019 的一个硬阻塞：standalone graph 外部改写
`selected` 后，rows4096 QSA 无法证明 graph replay 重新消费了新的正整数索引。
op-020 不再把 `selected` 当作 graph 输入，而是把生产者和消费者放进同一个
captured transaction：

```text
index_q + compressed K/page metadata
  -> qsa_select_paged_tokens
       -> qsa_mqa_paged
       -> torch.topk
       -> expand_qsa_block_indices
       -> selected [rows, 2051]
  -> workspace clear
  -> R4 membership build
  -> R4 grouped sparse attention + exact fallback
  -> output [rows, 3, 256]
```

对照组必须是同一输入上的真实 `select + current sparse attention` 全链，
不得使用预存 selected，也不得从候选计时中扣掉 TopK、expand、clear 或
membership build。本设计不授权修改远端源码或服务；它是一个下轮实验的
源码和证据契约。

## 为什么 op-019 的 fixture 不能直接充当 op-020 输入

op-019 保存的是 expand 后 `selected` 及 request/position/length metadata，它能
验证 R4 重用率和 grouped kernel 语义，但没有保存 indexer query、compressed
K cache 和 compressed block table，因而不能重放真实 TopK+expand producer。
把旧 selected 在 graph 内作 device copy 也不等价：它既没有解决 op-019 的正整
数索引重放疑点，又会让 select 产物与 sparse 消费者断开。

因此 op-020 使用两级输入：

1. `rows64` 最小证伪使用 production shape/dtype 的确定性合成 Q/K，只回答
   producer 是否在 graph 内重写 selected，membership 是否随之重建。
2. `rows4096` 性能晋级必须使用受控非业务 prompt 生成的 rank0/P4K
   Prefill 和 Mixed producer 输入快照，或在模型 graph 中就地运行相同试验。
   若只有合成 producer 输入，可完成 graph 正确性，但不能晋级性能结论。

P4K 快照只需 indexer query、compressed K 的当次可见页、compressed table 和
request/position/length metadata。main sparse Q/K/V 可用固定 seed 的 BF16 合成值，
因为它们不影响 selected 或控制流。快照必须由本案例的一次性、明确
非敏感请求生成，只保存在远端产物目录，记录 shape/dtype/bytes/SHA，不提交
prompt、token id、模型权重或 tensor 原文到当前仓库。

## 首个实现的源码边界

首轮应是独立 microbenchmark，不先改 Plugin/FlagGems 公共 dispatch。脚本
`op020-qsa-producer-integrated-r4-microbench.py` 复用 op-019 已审计的 clear/build/
grouped kernel，只新增两个 Python transaction wrapper：

```python
def baseline_full(inputs, selected, out):
    qsa_select_paged_tokens(
        inputs.index_q,
        inputs.compressed_k,
        inputs.compressed_table,
        inputs.token_to_req,
        inputs.logical_positions,
        inputs.sequence_lengths,
        token_topk=2048,
        compress_ratio=4,
        out=selected,
        # 使用当前 op-008 实际 ABI 传入 capture-time 静态 8448 bound
    )
    qsa_sparse_paged_attention(
        inputs.sparse_q, inputs.main_k, inputs.main_v,
        selected, inputs.main_table, inputs.token_to_req, out=out,
    )
    return selected, out

def candidate_full(inputs, selected, workspace, out):
    qsa_select_paged_tokens(..., out=selected)
    out.zero_()
    clear_r4_workspace(workspace)
    build_r4_membership(
        selected, inputs.token_to_req, inputs.query_start_loc, workspace
    )
    r4_grouped_attention_with_exact_fallback(..., selected, workspace, out)
    return selected, workspace, out
```

运行时以当前实际导入函数签名为准，不在实验脚本复制或改写
`qsa_mqa_paged -> torch.topk -> expand_qsa_block_indices` 逻辑。这一点是
“真实 producer”的核心。`selected`/output/R4 workspace 在 capture 外按最大
shape 预分配；producer 现有 logits/TopK 内部分配可进入 graph pool，但必须
在 capture 前完成编译 warmup，不得在 transaction 内使用 `.item()`、CPU 分支或
synchronize。

candidate 的 R4 语义延续 op-019 审计结论：同 request、连续 position、
row 内无重复且 token 在 8192 direct-address domain 内时才进 grouped path；
其他整组走原顺序 exact fallback。grouped/fallback 必须是互斥单写者，invalid
request output 必须 exact zero。

## A/B/A：如何证明 producer 和 membership 都在 replay 重算

### 输入变体的前置门禁

只改 indexer `index_q`；compressed K/table、request/position/length、sparse Q 和 main
K/V 保持不变。A 使用固定 seed，B 使用独立 seed（或受控 prompt 的第二份
index Q）。在 capture 前用 eager 真实 producer 分别生成 `selected_A/B`，必须
同时满足：

- shape/cardinality/request segmentation 完全一致；
- 两份 selected 均通过 row-unique 和 token-domain 检查；
- 至少 25% row 的非负 selected set 不同，且至少 8 个完整 R4 group 的
  CPU membership 不同；
- 固定 sparse Q/K/V 下，eager generic A/B output 不是完全相同。

若不满足，只允许更换 B 的固定 seed；不允许手工改 selected 来凑差异。

### 硬门禁：单 graph 内生成 A/B/A，而不从 graph 外改 selected

op-019 已证明 rows4096 的 graph 外 tensor 更新不能作为可信前置条件，因此
op-020 的首个 rows64 证伪不依赖外部 `index_q.copy_`。在 captured transaction
最前加入一个只用于 correctness 的 phase-driven staging kernel：

1. capture 外固定分配只读 `index_q_A`、`index_q_B`、活动 `index_q_work` 和一个
   device phase scalar；A/B 必须先通过 eager producer 差异门禁。
2. graph 开头的单程序 kernel 把 phase 固定到 `phase_used` 并切换下一 phase；
   staging 只读取 `phase_used`，把 A 或 B 写入 `index_q_work`，随后执行真实
   `qsa_select_paged_tokens`、generic/candidate consumer 和完整 membership 构建。
3. 只 capture 一张 graph。目标 PPU 的首个 blocked smoke 已证明 capture 只记录而
   不执行 transaction，因此 capture 前把 phase 置为 A，并硬断言 capture 后仍为 A；
   随后连续三次 replay 由 graph 内 phase flip 自然产生 A/B/A。若后端语义变化并
   修改了 phase，实验必须停止。
4. 每次 replay 后同步并持久化 `index_q_work`、selected、membership/group map/
   overflow、generic output 和 candidate output；要求 A1/A2 全部逐元素相等，B
   在冻结的差异字段上不同，三次都对齐各自 eager/CPU oracle。
5. baseline 与 candidate 可以分别验证，但每一臂各自只能 capture 一张 graph，
   且 producer selected 必须逐元素相等。性能计时时移除 phase staging，固定使用
   A；staging 时间不进入收益数字。

这里的动态证据来自同一 graph 内 upstream Q 写入、真实 producer selected 写入和
membership 重建。完整 membership 由 CPU 对当次 selected 重建并逐元素比较，不能
只查一个 hash 或最终 output。若 phase scalar、staging Q、producer selected 或
membership 没有按 A/B/A 变化，实验立即停止。

两张独立 graph 即使共享 downstream workspace，也只能证明两个 capture 各自能
覆盖状态，不能证明同一 graph replay 会重读动态 producer 数据。因此双 graph
A/B/A 只可保留为诊断，**不满足 op-020 graph 硬门禁，也不能进入计时或服务集成**。

## 正确性与 graph 最小门禁

顺序固定，任一步失败都不开始 rows4096 计时：

1. `rows64/eager`：A 和 B 分别通过 candidate-vs-current generic，
   `atol=rtol=0.05`；抽样 FP32 reference 通过；invalid request exact zero；
   CPU 结构 reference 逐元素对齐 membership/group base/overflow。
2. `rows64/graph`：候选和 baseline 均各自只 capture 一张 graph，完成上述
   graph 内 phase-driven A/B/A，至少 3 次有效 replay，所有 A/B/A 结构与数值
   条件通过。
3. `rows4096/Prefill` 与 `rows4096/Mixed`：先在 eager 下确认生产者
   selected 的 R4 `rho`、union p50/p90/p99/max 与 op-019 对应真实 fixture
   在预记录误差窗内（`rho` ±3 percentage points，union 各分位数 ±5%）。
   不满足则输入快照不代表 op-019 形态，不得计算晋级收益。
4. 两个 rows4096 phase 均完成 A/B/A，并通过 candidate-vs-generic 全张
   BF16 比较、采样 FP32 reference 和完整 membership 结构比较。

结果必须保存 baseline/candidate 每次 replay 的 Q/selected/membership/output SHA，
A/B selected 差异 row/cell/group 计数，CPU reference 差异计数，graph capture/replay
次数，以及实际命中的 impl id 和源码 SHA。

## 计时契约和性能门禁

性能比较只用原始 A 输入，A/B/A 诊断不进入计时区。两臂计时边界为：

```text
baseline event:
  qsa_select_paged_tokens (MQA + TopK + expand)
  + current qsa_sparse_paged_attention

candidate event:
  qsa_select_paged_tokens (MQA + TopK + expand)
  + output/workspace clear
  + R4 build
  + R4 grouped attention and exact fallback
```

要求 eager 和 captured graph 分开计时；同一 sample 交错
`baseline -> candidate`，下一 sample 反序。先做至少 5 次非计时 warmup，
rows4096 每个 event 内 `repeat=5`，至少 7 samples；`MAD/median > 3%` 时
增至 11 samples 且不删异常点。报告每个 raw sample、median/p25/p75/MAD、
执行顺序和脚本 SHA。

不降低 op-017/op-019 的晋级标准：Prefill 和 Mixed rows4096 的完整
`select+sparse` transaction 在 eager **和** graph 下都必须

```text
gain = baseline_median / candidate_median - 1 >= 8%
```

对照与候选的 producer selected 必须逐元素相等。只有 grouped kernel 超过
8%、加上共同 producer 后不足 8%，仍然判定失败。rows64、kernel-only、
profiler-on 时间或与 op-019 预存 selected 的时间均只能诊断，不能晋级。

## 最小可证伪顺序与停止条件

实施时只做以下有界次序，避免在 graph 证据无效时就进行服务集成：

1. 完成 standalone 脚本语法检查和 rows64 eager compile/correctness。
2. 只跑 rows64 graph A/B/A。失败则保存最小证据并立即停止。
3. rows64 通过后才准备或就地读取 rows4096 非敏感 producer 快照；先验证
   op-019 形态，再跑 rows4096 correctness/A/B/A。
4. 所有 graph/correctness 门禁通过后，才跑 Prefill/Mixed 全链计时。
5. 仅两 phase、两 mode 均 `>=8%` 时，才允许设计 FlagGems/Plugin 服务集成。

以下任一项都是本轮硬停止：

- 真实 producer 没有在 replay 中产生与 eager B 相同的 selected，或 A2 不能
  回到 A1；
- full membership/group/overflow 与当次 selected 的 CPU reference 不同，或
  只能通过双 graph/静态 replay 获得 A/B 差异；
- candidate-vs-generic 超出 `0.05/0.05`、FP32 抽样失败、invalid 非 exact zero、
  不可访问页/overflow/row duplicate 没有整组 fallback；
- rows4096 producer 形态不在 op-019 预记录窗口内；
- 任一 Prefill/Mixed、eager/graph 全链收益 `<8%`，或重复后反转/波动无法
  排除；
- 任一 compile error、OOM、device fault、hang、capture 内 host sync 或 graph replay
  不稳定。

停止后不修改实际 FlagGems/Plugin 源码，不启动候选服务，不把局部
kernel 或静态 graph 数字写成端到端收益。即使本实验通过，它也只允许进入
服务集成；正式精度仍受已有 GPQA `170/198 = 85.86% < 88%` 阻塞，不能
宣称验收通过。
