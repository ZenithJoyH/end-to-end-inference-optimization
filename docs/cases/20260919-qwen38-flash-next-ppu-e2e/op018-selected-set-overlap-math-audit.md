# op-018 selected-set overlap 数学审计

## 结论

`rows=4096` 的物理相邻行不能直接当作可复用组。一个可实现的
`R in {2,4,8,16}` 组必须同时满足：

1. 行来自同一次 QSA 调用、同一 layer 和同一 TP rank；
2. 行落在 `query_start_loc[r]:query_start_loc[r+1]` 的同一 request 段，
   且 `token_to_req` 逐行等于 `r`；
3. `logical_positions` 逐行加一；
4. 排除 `logical_positions < 0` 的 graph padding；
5. 从 request 段首开始按 `R` 做不重叠分组，段尾不足 `R` 的行保持
   原路径。

`token_to_req` 是当前 batch 内的 request-index，不是跨 step 稳定的
request ID；因此不得跨 QSA 调用或跨 step 分组。同一调用内，
`token_to_req` 相同意味消费同一 block-table row；再加上连续
`logical_positions` 才是“同 request、同 sequence 的相邻 query”的充分
实施条件。

## ratio-4 下的精确有效集合

对 row `i`，记 query 逻辑位置为 `p_i`，request sequence length 为
`l_i`。现有 expand kernel 使用：

```text
b_i = min(floor((p_i + 1) / 4), floor(l_i / 4), 512)
t_i = (p_i + 1) mod 4
```

compressed TopK 按 score 排序，只取前 `b_i` 个可见 complete-block
index 形成 `C_i`。精确的下游 K/V token 集合是：

```text
T_i = union({4*c, 4*c+1, 4*c+2, 4*c+3} for c in C_i)
      union {4*floor((p_i+1)/4) + j : 0 <= j < t_i}
```

最后还必须按 `0 <= token < l_i` 过滤。最安全的 telemetry 是直接对
expand 后 `[rows,2051]` 缓冲中的非负元素取集合；若只采集
compressed TopK512，则必须同时保存 `p_i/l_i`，按上式重建。
不能把 512 个 TopK 列原样当作有效集合，因为早期 causal row 会
在 TopK 尾部包含不可见的 `-inf` 列。

## 精确 K/V 读取复用率

对一个合法 row group `g`：

```text
a_g = sum_i |T_i|
u_g = |union_i T_i|
s_g = a_g - u_g
rho_g = s_g / a_g
```

`a_g` 是原路径 K 或 V 的 token-vector 读取数，`u_g` 是理想的
union-once 路径读取数，`s_g` 是最多可删读取数。K 和 V 同时读取
的因子 `2` 在比率中抵消。当 head dim=256、BF16 时，一个 token
的 K+V 显式 payload 为 `2*256*2=1024 bytes`，所以理想节省为
`1024*s_g` bytes。

不能对 `rho_g` 取算术平均。对整个 rows4096 调用，定义：

```text
B       = sum_all_eligible_rows |T_i|
A_R     = sum_full_groups a_g
U_R     = sum_full_groups u_g
rho_R   = (A_R - U_R) / B
coverage_R = A_R / B
rho_R_grouped = (A_R - U_R) / A_R
rho_R = coverage_R * rho_R_grouped
```

`B` 包含每个 request 段尾不足 `R` 的行，这些行的节省为零。
因此只有 `rho_R` 可用于重开判定；`rho_R_grouped` 必须与
`coverage_R` 同时报告，不能单独用于达标。

## union/mask 的最低逻辑量

若候选使用一个 group union 和逐行 membership mask，则每组至少有：

```text
union K/V token reads       = u_g
dense membership cells      = R * u_g
true membership cells       = a_g
false/masked score slots    = R * u_g - a_g
mask density                = a_g / (R * u_g)
```

如果确实物化 int32 union IDs，payload 至少是 `4*u_g` bytes；如果使用
一个 bit 表示每个 dense membership cell，bitmask footprint 是
`ceil(R*u_g/8)` bytes。这是 dense union/mask 设计的逻辑下界，尚未计入
union 构建、排序/去重、行映射、独立 softmax state 和 graph workspace；
它不是任意压缩编码的信息论下界。

最低充分统计是每个 `R` 的 `(B,A_R,U_R,sum_g R*u_g,full_group_count,
tail_row_count)`。这些总和可以精确重建全局复用率和 mask 量，不需要
保存用户 token 或完整 K/V。为了审计分布，可另外保存每组
`(a_g,u_g)` 直方图，但不以 percentile 代替加权总和。

## `>=12%` 重开门槛

对每个 `R=2/4/8/16` 分别计算上述整个调用加权的 `rho_R`。只有
某个具体 R 在生产代表性 rows4096 telemetry 上满足：

```text
rho_R >= 0.12
```

才重开 row-group kernel 微基准。这仍只是“未扣 union/mask 开销的
K/V 理想节省”，不是 12% 端到端收益承诺。

若用更强的简化模型：每行都有相同大小的有效集，且其中比例 `p`
的 token 被全部 `R` 行共享，其他 token 完全不共享，则使
`rho_R >= 12%` 的充分门槛是：

| R | all-row common-core 比例 `p >= 0.12*R/(R-1)` |
|---:|---:|
| 2 | 24.000% |
| 4 | 16.000% |
| 8 | 13.714% |
| 16 | 12.800% |

该表只是一个充分条件，不是必要条件；任意成对/局部重叠都应
通过 exact union 公式计算。在所有行都饱和为 compressed TopK512 且
暂时忽略 ratio-4 causal tail 的近似下，12% 门槛等价于 compressed
union 分别不超过 `901/1802/3604/7208`（R=2/4/8/16）；
正式判定仍必须用 expand 后 `T_i` 和精确 `rho_R`。

## 可复用的现有 metadata 位置

Plugin 的
`vllm_fl/models/qwen3_8_flash_next.py::QSAForwardMetadata` 已直接携带：

- `query_start_loc`：request 在 row-major query 张量中的段边界；
- `token_to_req`：每行到当前 batch request-index 的映射；
- `logical_positions`：每行逻辑 sequence 位置，padding 为 `-1`；
- `seq_lens`：每个 request 的 sequence length；
- `num_actual_tokens`：QSA 张量行数（graph bucket 中可包含 padding）。

`QSAMetadataBuilder.build()` 从 vLLM `CommonAttentionMetadata` 构造这些字段。
`token_to_req` 优先调用 `CommonAttentionMetadata.token_to_req_indices()`；
当前 vLLM 0.24 兼容分支使用
`repeat_interleave(arange(num_reqs), diff(query_start_loc))` 得到完全等价的
device mapping。`worker/model_runner.py::_prepare_inputs()` 先用 scheduler 的
`cu_num_tokens` 生成 `query_start_loc`，再把 `CommonAttentionMetadata` 传给
QSA builder。

因此 op-018 不需要使用 host `req_id` 或新建 row-to-request 映射。
若 telemetry 只在同一 QSA 调用内分组，现有 `query_start_loc +
token_to_req + logical_positions` 已能防止跨 request/sequence 误算，也避免
把 request-index 跨 step 复用误当成同一 request。

