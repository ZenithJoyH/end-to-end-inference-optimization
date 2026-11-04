# op-017: QSA sparse block-centric traversal frontier

## 决策

- 类型：`operator/improve`，只读源码和理论上界审计。
- 状态：`stopped-before-microbenchmark` / `no-credible-8%-bound`。
- 本轮唯一主候选：让 sparse GQA 直接消费 TopK 产生的
  `512` 个 compressed-block index，在 kernel 内按 `compression_ratio=4`
  生成逻辑 token，不再先物化 `[rows,2051]` 的 expanded-token
  index；同时把每 4 个 token 的 page translation 合并为一次。
- 结论：在对候选最有利的 rows4096 稀疏事务字节账中，即使
  expanded-index 写入、读取和可合并的 block-table 访问全部变为零成本，
  也只能移除约 `1.060%` 的显式 tensor traffic。它不改变
  `2051` 个 token 的 K/V 必需读取，也不减少 `129`
  个 online-softmax tile。现有证据也没有表明被删除的单个 expand launch
  占到达标所需的 `0.7595 ms`。因此不设计本地微基准，不修改
  FlagGems/Plugin，不占用远端加速卡。

## 与已有 QSA 实验的边界

| 已有方向 | 改变的机制 | 本轮为什么不重复 |
|---|---|---|
| `op-015` group-3 lane reduction | `BLOCK_M=16` 改为 literal four lanes | 本轮不改 query-head tile；改的是 TopK 之后的 index 物化和 block traversal |
| Qwen4 QSA dot replacement | MQA scorer 的 scalar dot 改为 `tl.dot` | 本轮不改 score kernel 或 dot 实现 |
| `op-005` row-range TopK | 替换 TopK provider，利用每行 visible range | 本轮保持同一 TopK 结果和顺序，只改 TopK 输出后的消费方式 |
| `op-006` / `op-008` score bound | 减少 MQA 打分列数 | 本轮不改 score width，也不使用 static/runtime bound |

## live 路径和 rows4096 契约

当前实际路径是：

```text
qsa_mqa_paged
  -> torch.topk(k=512, sorted=True)
  -> expand_qsa_block_indices(compression_ratio=4, token_topk=2048)
  -> int32 selected indices [rows, 2051]
  -> _qsa_sparse_paged_gqa_kernel
```

已核验的 TP8 rank-local sparse 契约：

- query：BF16 `[rows,3,256]`；
- K/V：BF16 `[blocks,16,1,256]`；
- selected indices：int32 `[rows,2051]`；
- 单 KV head，`compression_ratio=4`，TopK block 数 `512`；
- current sparse grid `[rows,1]`，`BLOCK_N=16`，每行执行
  `ceil(2051/16)=129` 次 online-softmax 迭代。

kernel 每个 tile 先读逻辑 token index，再通过 block table 映射到
physical page，然后读取 K 和 V，完成 query-key dot、online softmax
和 probability-value dot。候选只能省掉 metadata 物化/翻译；为了保持
精确 attention 语义，仍必须读取同样的 `2051` 份 K/V，也必须执行
同样数量的 dot 和 softmax 更新。

源码/环境身份沿用当前已核验 live path：Plugin revision
`939600b323c0`，FlagGems revision `2b1e5cfdbd22`，sparse kernel 为
`/workspace/FlagGems/src/flag_gems/fused/qsa.py::_qsa_sparse_paged_gqa_kernel`。
本轮没有远程命令、源码修改或服务实验。

## rows4096 完整 sparse 事务的字节上界

下表用源码中的逻辑元素计数，不假设某个未知的硬件带宽。
对 cache hit 和 block-table 重复加载都按最有利于候选的方式计数。

| 项目 | rows4096 显式字节 | 候选能否删除 |
|---|---:|---|
| K+V：`4096*2051*2*256*2` | `8,602,517,504` | 不能；精确 attention 的必需数据 |
| query + output | `12,582,912` | 不能 |
| expanded indices 写入 | `33,603,584` | 可删除 |
| expanded indices 读取 | `33,603,584` | 可删除 |
| 现有按 token 的 block-table 读取 | `33,603,584` | 最多合并其中 `25,165,824` |
| `token_to_req` | `16,384` | 不能 |

候选把 page translation 从 `2051` 次降到最多 `512+3`
次/行时，最宽松的可删除显式 traffic 是：

```text
33,603,584 + 33,603,584 + 25,165,824
= 92,372,992 bytes
```

将 expanded-index 的写入也纳入 baseline 后，上表事务共
`8,715,927,552 bytes`，所以理想 traffic 降幅只有：

```text
92,372,992 / 8,715,927,552 = 1.0598%
```

这个比例还是故意高估：

1. 它把当前四个相邻 token 对同一 block-table entry 的 cache/合并效果
   当作不存在；
2. 它把所有删除的 metadata 字节当作与 paged BF16 K/V 同等昂贵；
3. 它只用 sparse 事务作分母；完整 QSA 还包括 MQA score、native
   TopK 和 compressed-cache 读取，所以全事务比例只会更小。

`op-015` 的当前 rows4096 graph sparse 中位数是 `9.494234 ms`。
8% 门槛要求降到 `8.734695 ms`，即至少省 `0.759539 ms`。
若只按上述已证明 traffic 比例折算，理想时间仅降到约
`9.393612 ms`。要达标，被删除的单个 expand launch 还必须独立
贡献超过约 `0.66 ms`；它未出现在 prof005 当前报告的主要热点中，
也没有任何单独计时证据支持这个量级。因此不能把“少一个 launch”
当成 `>=8%` 的可信预测。

## 其他算法边界为什么不立即实现

### 跨 row 共享 selected K/V

这是精确语义下唯一可能显著降低 `8.60 GB` K/V 必需读取的方向：
把同一 request 的多个 query row 合并，对 selected-token 交集只读一次 K/V。
但当前证据没有保存 prof005 rows4096 相邻 row 的实际 selected-index
交集率，因此无法预测收益。

不计任何 union/sort/mask/reduction 开销时，将 `R` 行分组要单靠
共享读取节省 8%，每行 selected set 的共享比例至少需要：

| row group `R` | 最低共享比例（零开销理想值） |
|---:|---:|
| 2 | `16.00%` |
| 4 | `10.67%` |
| 8 | `9.14%` |
| 16 | `8.53%` |

实际门槛必然更高，因为 TopK 按 score 排序，相同 token 不保证位于
同一 tile；候选还需要 union/inverted mapping、每行 mask 和独立 online
softmax state。在没有生产 selected-set 交集证据前，直接写 row-block
kernel 属于无界高成本开发，不进入微基准。

### 变更 TopK 数量或 K/V 精度

- 将 `2051` 减少至约 `1887` 以下才可能仅凭 token 数量获得
  8% sparse 工作量降幅，但这会改变模型 attention 语义；
- FP8/int8 QSA K/V 副本有足够的字节上界，但会引入量化误差、额外
  cache store/dequant 和新的精度合同。

这两者都不是当前“不改输出语义”的精确优化，而且当前正式精度仍被
GPQA `170/198 = 85.86% < 88%` 阻塞，不应以尚无有效 gate 的近似路径
扩大变更范围。

## 停止条件与重开条件

本轮已命中停止条件：一个改变 TopK/block traversal 且保持精确语义的
最窄候选，在把显式 metadata 收益全部理想化后仍只有约 1.06% traffic
上界，且没有 launch 时间证据能把可信预测推高到 8%。

只在出现以下任一新证据后重开：

1. 生产 rows4096 selected-index 只读 telemetry 证明一个具体 row-group
   方案在扣除 union/mask 开销前仍能减少至少 12% K/V 读取；或
2. 有效 trace 将 `expand_qsa_block_indices` 本身独立定位为每次
   rows4096 `>=0.66 ms`，并且该时间不是前序 backlog/异步归因。

重开后才设计最小微基准；仍需覆盖完整 selection+sparse transaction、
BF16 reference、无效 request、非连续页、graph capture 和两次 replay，并在
rows4096 达到预冻结 `>=8%` 才允许修改实际源码。

## 证据

- live call chain 与 shape：
  `docs/cases/20260919-qwen38-flash-next-ppu-e2e/qsa-live-path-readonly.md`。
- rows4096 sparse baseline 与 group-3 反例：
  `models/Qwen3.8-Flash-Next/ppu/optimize/op-015-qsa-sparse-gqa-group3.md`。
- prof005 Mixed 归因：755 次 sparse 调用累计 `7.339s`，marker wall
  约 `40.1435s`；该 profiler-on 数据只用于热点定位：
  `models/Qwen3.8-Flash-Next/ppu/optimize/prof-005-p4k-post-op010.md`。
- 已拒绝/保留的 QSA 边界：
  `models/Qwen3.8-Flash-Next/ppu/optimize/README.md`。
