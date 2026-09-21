# op-018 QSA union/mask transaction 成本模型

## 结论

`op-018` 证明 P4K 连续 Prefill row 有很高的 selected-set 重叠，
但它只是开发 union/mask kernel 的证据，不是端到端收益。
在 `R=2/4/8/16` 中，建议只先实现 **R=4**：

- R=4 在 Prefill/Mixed 中分别删除 `69.512%/69.480%` 的有效
  K/V token-vector 读取；
- 4 rows 乘 3 query heads 只有 12 个逻辑 lane，仍可放在现有
  `BLOCK_M=16` 中，不增加单个 program 的 query/softmax/accumulator
  tile extent；
- R=2 也占用 `BLOCK_M=16`，却只节省约 44% K/V，并且最低
  metadata 交易量比现路径多约 `18.8 MB`，被 R=4 严格支配；
- R=8/16 的 K/V 理想上界更高，但 `BLOCK_M` 至少上升为
  32/64，逻辑 dense score slot 增加约 28.5%/31.6%，寄存器、
  accumulator 和 occupancy 风险不适合作为首个实现。

R=4 必须先通过两级微基准：先是完整 sparse kernel，再是
`union/mask 构建 + sparse`完整 transaction；两者都要在 graph 下
相对同一份真实 selected-index 基线达到 `>=8%`。

## 冻结 fixture 补充验证

op-019 已用冻结 Prefill/Mixed exact fixture 逐整数复现 op-018
计数，并补齐了 summary 无法给出的分布：

| phase | R4 max union | R4 p99 union | row 内 duplicate | 最佳固定 leader 的 union coverage |
|---|---:|---:|---:|---:|
| Prefill | 3460 | 3292 | 0 | 约 82% |
| Mixed | 3400 | 3292 | 0 | 约 82% |

这些结果对设计有三个直接影响：

1. 两份 rows4096 fixture 的 compact-union capacity 取 4096 就能覆盖
   实测 max，但生产 P4096/D1024 的 logical token 可超过 4095；
   所以实际 direct-address guard 仍应使用 8192 bucket，超界整组
   fallback，不能把 fixture max 写成通用 ABI 上界。
2. 冻结 producer 路径已证明 duplicate 为零，因此 bool/bit membership
   在这两份 fixture 上不会丢 multiplicity。这仍不是公共
   `qsa_sparse_paged_attention` ABI 的性质；候选只能在已证明的
   Qwen3.8 producer contract 下启用。
3. 最佳 leader 仅覆盖约 82% union，低于预设的 90% 重开线。
   仍有约 18% union token 要通过 additions 表表达，因此不将
   leader-plus-additions 作为首轮实现，direct-address membership
   结论不变。

## 证据身份与口径

- 遥测 summary：
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/op018-qsa-overlap-summary-001.json`
- summary SHA-256：
  `fa68ef87513d228ee6db2456ad211baca492da2e1c516c85dd6a7b25e259958c`
- sparse rows4096 graph 参考基线：`9.494234 ms`，来自 `op-015`
  的全部 2051 个 index 有效的合成 shape。
- 当前 contract：query BF16 `[4096,3,256]`，K/V BF16
  `[blocks,16,1,256]`，selected indices int32 `[4096,2051]`，
  `BLOCK_N=16`，当前 `BLOCK_M=16`。

对组 `g` 定义 `a_g=sum_i |T_i|`、`u_g=|union_i T_i|`。
summary 中：

```text
B = 所有 eligible row 的 unique selected-token 总数
A = 完整分组覆盖的 row token 总数
U = 各完整分组 union cardinality 之和
S = A - U                         # 可删除 K/V token occurrences
K/V_candidate_occurrences = U + (B-A)
dense_cells = R*U
false_cells = R*U-A
```

每个 token 的 K+V payload 为 `2*256*2 = 1024 bytes`。

## 遥测计数与 K/V transaction

Prefill 的 `B=6,295,552`，Mixed 的 `B=6,295,554`，即每行平均
约 `1537` 个 unique token。当前路径的实际有效 K/V payload
约 `6.004 GiB`。下表用 Mixed 计数，因为它的 tail 覆盖略低；
Prefill 的差异很小。

| R | Prefill rho | Mixed rho | Mixed coverage | candidate K/V occurrences | candidate K/V GiB | dense cells / B | false cells / B |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 44.055% | 44.053% | 99.935% | 3,522,197 | 3.359 | 1.118 | 11.830% |
| 4 | 69.512% | 69.480% | 99.870% | 1,921,416 | 1.832 | 1.217 | 21.690% |
| 8 | 83.893% | 83.709% | 99.740% | 1,025,582 | 0.978 | 1.285 | 28.501% |
| 16 | 91.728% | 91.286% | 99.479% | 548,618 | 0.523 | 1.316 | 31.616% |

`dense cells / B > 1` 表示 union-once 虽然删除 K/V 读取，但稠密
membership 会增加 dot/mask/softmax 的逻辑 slot。因此 `rho` 不能
直接解释成 kernel 加速比。

## metadata/mask 下界

如果物化 int32 union ID 和 1-bit membership mask，则仅存储下界为：

```text
union IDs       = 4*U bytes
membership mask = ceil(R*U/8) bytes
```

下表还给出一个更现实的最低 transaction 计数：读一次
source selected IDs，union IDs 和 bitmask 各写入并读回一次，每个
union token 读一次 page-table entry，tail 仍走旧路径。它仍未计入
sort/unique/atomic/scan workspace，因而是下界而非预测。

| R | union-ID footprint | 1-bit mask | 最低 metadata R/W | 现 sparse index+page R | 差值 |
|---:|---:|---:|---:|---:|---:|
| 2 | 14.072 MB | 0.880 MB | 69.175 MB | 50.364 MB | +18.810 MB |
| 4 | 7.653 MB | 0.957 MB | 50.087 MB | 50.364 MB | -0.278 MB |
| 8 | 4.037 MB | 1.009 MB | 39.376 MB | 50.364 MB | -10.988 MB |
| 16 | 2.063 MB | 1.032 MB | 33.567 MB | 50.364 MB | -16.798 MB |

如果实现用 byte mask 而不是 bitmask，Mixed 的单份 mask 分别为
`7.036/7.653/8.073/8.253 MB`；写入加读回需要计两倍。
即使如此，metadata 仍远小于数 GiB 的 K/V payload，真正风险
是 union 构建、dense false slot 以及寄存器/occupancy，而不是 mask
的纯存储字节。

### 8192 int32 direct-address workspace 的精确字节账

R4 rows4096 的组数是 `ceil(4096/4)=1024`。因此：

```text
membership [1024,8192] int32 = 1024*8192*4
                                 = 33,554,432 bytes = 32 MiB
overflow   [1024]      int32 = 4,096 bytes
workspace total              = 33,558,528 bytes = 32.00390625 MiB
```

每次完整 transaction 都必须在计时区内 clear 这些地址，因而
clear 的最低写 payload 是精确的 `33,558,528 bytes`。build 至少
读完 `[4096,2051]` int32 selected fixture：

```text
4096*2051*4 = 33,603,584 bytes = 32.046875 MiB
```

已证明无 duplicate，所以 Prefill/Mixed 非负 occurrence 分别为
`6,295,552 / 6,295,554`。每个 occurrence 发起一次 int32
`atomic_or`时，仅按 4-byte 目的 operand 计算的逻辑触碰量是：

| phase | atomic 次数 | 4-byte logical touches | clear + selected read + one-touch lower bound | 按 atomic RMW 读+写的下界 |
|---|---:|---:|---:|---:|
| Prefill | 6,295,552 | 25,182,208 B | 92,344,320 B = 88.066406 MiB | 117,526,528 B = 112.082031 MiB |
| Mixed | 6,295,554 | 25,182,216 B | 92,344,328 B = 88.066414 MiB | 117,526,544 B = 112.082047 MiB |

若 builder 在读 selected 之前就判定并跳过 Mixed segment tail，则可用
`A_R=6,287,354` 次 atomic，对应 one-touch/RMW 下界为
`92,311,528 / 117,460,944 bytes`（`88.035133 / 112.019485 MiB`）。
表中只是 payload 下界；atomic serialization、cache-line transaction、
eligibility metadata 读取和 kernel launch 会增加实际成本。

## dot/softmax 与 tile 成本

当前 kernel 每行固定执行 `ceil(2051/16)=129` 个 N tile，
且虽然只有 3 个 head，M tile 仍是 16。因此合成 rows4096
基线的物理 dot cell 参考量为：

```text
4096 * (129*16) * 16 = 135,266,304 M-token cells
```

下面先给出 **compact union** 的理论模型。它需要先把 union
压紧成新 token list，不是 op-019 首轮冻结的 direct-address +
原 occurrence scan 实现。令 `BM_R=16/16/32/64`对应 R=2/4/8/16。
仅使用 summary 总和可以得到 padding 前后的严格区间：

```text
BM_R * U <= grouped physical cells <= BM_R * (U + 15*group_count)
```

加上 Mixed tail 原路径后，相对当前参考量是：

| R | compact-union physical dot ratio | 固定扫描 P4K 4096 token domain |
|---:|---:|---:|
| 2 | 41.66%--42.03% | 99.23% |
| 4 | **22.73%--22.91%** | **49.66%** |
| 8 | 24.07%--24.25% | 49.71% |
| 16 | 24.80%--24.98% | 49.81% |

这是 R=4 的关键优势：12 个逻辑 query-head lane 仍是一个
`BLOCK_M=16`，而 R=8/16 需要 32/64。以 FP32 accumulator 计，
物理 accumulator 状态从当前的 `16*256*4=16 KiB` 增长为
R=8 的 `32 KiB` 和 R=16 的 `64 KiB`，尚未计 query、max、
normalizer 和 compiler spill。

固定扫描 4096 token domain 可以避免动态 union 长度，对 graph 友好，
但它是 P4K 特化。P16K/P32K 不能直接扩大这个扫描范围，
必须有 compact union 或 fallback。

### 首轮 direct-address occurrence-scan 的真实 dot 边界

op-019 首轮并不扫描 8192 token domain，也不构建 compact union
list。它仍按 4 行原始 `[2051]` occurrence 顺序扫描，用
membership bit 决定哪一行的 occurrence 是 owner，只让 owner 读一次
K/V。因此每组仍执行：

```text
4 phases * ceil(2051/16) = 516 N tiles
```

这与 4 个现有 row kernel 的总 tile 数相同；两边 M tile 也都是
16。因此首轮候选的物理 dot cell 比率应按约 **100%**
建模，而不是上表 compact-union 的 22.7%。它的主要收益来自
K/V/page-table load 去重、更少的 attention program grid，以及可能的
cache 行为；dot/softmax 并没有理论删减。

冻结 fixture 的 R4 max union 小于 4096，说明 compact-union 是一个
未来可独立证伪的第二机制，但它需要 compaction/prefix-sum 和
另一套 graph workspace。不应把它的 dot 上界提前计入本轮
direct-address 候选。

## 与 9.494234 ms 基线的边界换算

op-019 冻结的 gain 定义是 `baseline/candidate-1`，因此
`9.494234 ms` 参考基线的 8% 门槛是
`9.494234/1.08 = 8.790957 ms`，需要至少节省 `0.703277 ms`。
这不等于直接减少 8% wall time；之前的 `0.92*baseline`
口径与冻结 gain 公式不一致，本次已纠正。该基线用了
`4096*2051=8,400,896` 个全有效
token occurrences，其 K/V payload 是 `8,602,517,504 bytes`。将它用作
仅供尺度校准的有效带宽，约为 `906.08 GB/s`。

用更保守的 Mixed `S`除以这个全有效 occurrence 分母，可得：

| R | 可删 K/V / synthetic full | 如全部时间随 K/V 线性缩放的理想时间 | 达 8% 后的理想 overhead budget | K/V 可缩放时间占比的最低要求 |
|---:|---:|---:|---:|---:|
| 2 | 33.013% | 6.359937 ms | 2.431020 ms | 22.44% |
| 4 | 52.068% | 4.550822 ms | 4.240135 ms | 14.23% |
| 8 | 62.731% | 3.538399 ms | 5.252558 ms | 11.81% |
| 16 | 68.409% | 2.999361 ms | 5.791597 ms | 10.83% |

“overhead budget”是 K/V 理想节省减去 `0.703277 ms`；它不是允许
实现消耗的实测时间，因为基线还包含 dot、softmax、page translation
和 launch，且遥测工作负载只有平均 1537 个有效 token，与
`op-015` 的 2051 全有效合成基线不同。这些数字只证明
R=4 有充足的理论 headroom，不能用来代替同输入 A/B 微基准。

## 最小可行实现与微基准门槛

首个候选应是 P4K-only R=4，其他 shape 和不足 4 rows 的
request tail 走原路径。最小实现应包含：

1. 只对同一 request segment 的连续 4 rows 分组；
2. 预分配、地址稳定的 union/membership workspace；
3. 无 `.item()`、host sync 或 capture-time allocation；
4. 在一个 `BLOCK_M=16` program 中放 12 个 query-head lane；
5. 每行保持独立 max/normalizer/accumulator，false membership 必须同时
   mask score 和 probability；
6. invalid request、non-contiguous page、tail row 和 zero-valid-token 回退要与
   现路径一致。

微基准分两步，不得只计 union 后的 sparse kernel：

- kernel-only：使用捕获的真实 selected sets，包含 R=4 full groups 和
  tail fallback，正确性、graph capture + 2 replay 通过，中位数收益
  `>=8%`；
- full transaction：把 graph-safe union/mask 构建加回，仍须相对同一
  current-path 基线 `>=8%`，且 p99 不能明显退化。

`8.790957 ms` 只是对 `op-015` 合成 sparse shape 的参考目标。
真正的 gate 必须重跑同一份生产 selected-index 输入的 current
baseline，不得把 1537-valid 候选与 2051-valid 基线直接求精确
加速比。

### 首轮 kernel-only 与 full-transaction 现场阈值

对每个 `phase in {Prefill,Mixed}` 和 `mode in {eager,graph}`，必须
先在同一份 fixture、同一 Q/K/V/page table 上现场测得 current generic
baseline `T_base[phase,mode]`。不能把 `9.494234 ms` 直接填入
正式判定。冻结 8% gain 的时间阈值统一是：

```text
T_gate[phase,mode] = T_base[phase,mode] / 1.08
```

因此：

```text
kernel-only 必要 screen:
    T_grouped_kernel[phase,mode] <= T_base[phase,mode] / 1.08

full transaction 正式门槛:
    T_clear_build_grouped_fallback[phase,mode]
        <= T_base[phase,mode] / 1.08

给定实测 grouped-kernel 时间 K 后，clear+build 可用预算:
    T_clear_build <= T_base/1.08 - K
```

kernel-only 过线只是 full transaction 的必要条件，不能单独晋级。
如果 `T_base/1.08-K <= 0`，则无论 builder 如何优化都应停止。
正式判定取 Prefill/Mixed × eager/graph 四项 gain 的最小值，
四项都必须 `>=8%`。

## 指标偏差和实现陷阱

1. **只采了一个 rank/一次 QSA call。** one-shot rank0 样本不能
   证明所有 layer、TP rank 和 scheduler step 都有同样的重叠。可进入
   微基准，但在 service 保留前必须补多 layer/rank/step 分布。
2. **Mixed 样本几乎被 Prefill 支配。** Mixed 比 Prefill 只多 2 个
   token occurrences，且 tail rows 恰为 R 的 `2/4/8/16`；这与
   一个 4095-row prompt segment 加一个 1-row decode segment 高度一致。
   因为规则禁止跨 request 分组，稳态 Decode 中“每 request 一行”
   通常没有可分组 row；所以候选主要是 Prefill 优化，不应
   将 Mixed rho 解释为 Decode 收益。
3. **duplicate 风险已对冻结 fixture 排除，但不能泛化。**
   Prefill/Mixed 的 row 内 duplicate 都为 0，所以本轮 bool membership
   不丢 multiplicity。公共 ABI 的其他 producer 仍可能有 duplicate，
   必须保持原路径。
4. **fixture 已给 max/p99，但不是生产全局上界。** Prefill
   max/p99 为 `3460/3292`，Mixed 为 `3400/3292`。这只能用于
   本 fixture 微基准；生产仍需 8192 token-domain guard 与 overflow fallback。
5. **TopK 顺序不是 token-ID 顺序。** 现输出按 score 排列，不能使用
   简单的有序 list merge 构建 union。P4K 可考虑逻辑 token-domain
   bitset/scan，或在 compressed-block 域中构建 mask，但必须包含
   ratio-4 causal tail。
6. **leader 快捷路径已不达预设门槛。** 冻结 fixture 的最佳
   固定 leader 仅覆盖约 82% union，低于 90% 重开线。首轮
   仍用 direct-address membership，不叠加 leader-plus-additions 第二机制。
7. **数学上的 set 不保留 reduction order。** attention 对 token 顺序在实数
   上等价，但 BF16/FP32 online-softmax 的 tile/reduction order 变化可造成
   末位差异。微基准必须用 FP32 reference 和预冻结 tolerance，
   不能只比较 set 相等。
8. **端到端上界还受 Prefill 占比限制。** 该 kernel 候选不会改善
   无同 request 连续 rows 的 Decode call。即使 rows4096 sparse 微基准
   通过 8%，仍必须回到 P4K Mixed 无 profiler 测量，并把 TPOT/ITL
   作为守护项。

## 决策

`op-018` 已足以重开 union/mask 微基准，但不支持同时开发
R=2/8/16。首个有界候选是 **P4K R=4**，因为它在不放大
`BLOCK_M=16` 的情况下已有约 69.5% K/V 理想删减，且最低
metadata transaction 与当前 sparse metadata 基本持平。任何候选
都要以实测的 full-transaction `>=8%` 为保留门槛，不得把
`rho` 或本文的带宽换算当作性能收益。
