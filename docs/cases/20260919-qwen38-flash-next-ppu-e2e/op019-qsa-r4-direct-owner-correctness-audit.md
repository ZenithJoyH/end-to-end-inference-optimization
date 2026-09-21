# op-019：QSA R4 direct-address lowest-owner 正确性审计

## 审计结论

“按四行 occurrence 扫描、最低 row bit 为 owner、owner 处只读一次 K/V 并同时更新
12 个 query-head lanes”在以下前提全部成立时，数学语义正确：

1. 每行所有非负 selected token 在该行内唯一；
2. grouped 四行属于同一 **有效** request，即不仅相同且非负，还必须
   `request < block_table.shape[0]`；
3. logical positions 连续、四行都存在、所有非负 token `< TOKEN_BUCKET`；
4. membership 和 overflow 在每次调用前对当前 groups 完整清零，build 与 attention
   在同一 stream 顺序执行；
5. grouped 与 fallback 是互斥事务，每个存在的 output row/head 恰好一个 writer；
6. page-table/K/V load 使用 owner-column mask，softmax update 使用
   `owner-column mask AND target-row membership`，不能混用两种 mask。

因此本方案可进入独立微基准，但现有设计中的“attention 仍按原 occurrence 顺序扫描”
需要收紧：它只保留 **每个 owner 行内部** 的 occurrence 顺序，并不保留每个被更新目标
行的原顺序。对 target row `j`，实际顺序是：

```text
owner=0 且 j 选择的 token（按 row0 顺序）
owner=1 且 j 选择的 token（按 row1 顺序）
...
owner=j 且 j 选择的 token（按 rowj 顺序）
```

这与 row `j` 自己的 selected 顺序一般不同。softmax/PV 在实数数学中对排列不变，
所以 token 多重集合相同即可保持数学语义；FP32 online-softmax/BF16 probability 和
accumulation 不满足结合律，不能声称 bitwise 等价。顺序冲突必须成为数值压力测试，
`atol=rtol=0.05` 仍需实测，而不能由 owner 证明推出。

## 1. exactly-once 证明

对一个 eligible group 和一个 union token `t`，定义：

```text
S(t) = { r in {0,1,2,3} | t 在第 r 行出现 }
bits(t) = sum(1 << r for r in S(t))
r*(t) = min S(t)
```

若每行 `t` 最多出现一次：

- 在 phase `r*` 中，`t` 恰有一个 occurrence；
- `bits & ((1 << r*) - 1) == 0` 且 `bits & (1 << r*) != 0`，所以该 occurrence
  是唯一 owner；
- 对所有 `r > r*`，lower-bit test 为假；对 `r < r*`，该行没有 occurrence；
- 因而 page-table、K、V 恰好在 owner occurrence 处理一次；
- owner 处对每个 target row `j` 使用 `bits & (1 << j)`，所以 `t` 恰好更新所有且
  仅更新选择它的 `3*|S(t)|` 个 head lanes。

这也说明“后续 duplicate occurrence 完全跳过”的精确定义：后续行 occurrence 仍会读取
selected ID 和 membership bits，也可能占用一个 masked dot column；但必须在 page-table、
K/V load 和 softmax state 之前被 `owner_col=False` mask 掉。它不再产生 K/V 流量或状态
更新，但不能声称省掉了 tensor-dot 指令。

owner phase 的两个 mask 必须分开：

```text
load_col = logical_valid & owner_col & physical_page_valid
score_lane_col = load_col[None,:]
                 & row_membership_for_each_head_lane[:,None]
                 & (head_lane < 12)
```

K/V load 不能使用带 lane 维度的 `score_lane_col`；score 也不能只用 `owner_col`，否则
没有选择该 token 的 rows 会错误进入 softmax。

## 2. token 顺序与 online-softmax

例子：

```text
row0 = [20]
row1 = [30, 20]
```

baseline 的 row1 顺序是 `[30,20]`；owner 路径在 row0 phase 先用 `20` 更新 row1，
再在 row1 phase 用 `30`，有效顺序变成 `[20,30]`。因此不存在“所有行同时保持自己的
原顺序”的单一 shared-K/V traversal，除非这些行的 selected 顺序恰好一致。

对独立 lane 的 logits `s_t` 和 values `v_t`：

```text
sum_t exp(s_t) * v_t / sum_t exp(s_t)
```

对排列不变，所以 owner traversal 的实数结果等价。实现仍必须为每个 12 个有效 lanes
分别保存 `(max,normalizer,accumulator)`；不能在同一 row 的三个 heads 之间共享 max/norm，
也不能在四行之间共享。对某 lane 当前 tile 没有 token 时：

- 所有 score 置 `-1e20`；
- probability 必须显式为 0；
- `max/normalizer/accumulator` 必须保持不变。

测试不能只用相同 selected 顺序。至少加入：相同集合反序、循环移位、owner 行与后续行
完全相反的 TopK 顺序，以及 near-tie logits 配合正负交替 V 的 rounding 压力输入。

## 3. duplicate occurrence 的边界

int32 membership bit 只表达 presence，不表达 multiplicity。跨行重复由 owner 机制正确去重；
**同行重复不受支持**：

```text
row0 = [7]
row1 = [7,7]
```

baseline 的 row1 对 token 7 计权两次；owner 路径在 row0 只更新 row1 一次，而 row1 的两个
occurrence 都因不是 owner 被跳过。反向例子：

```text
row0 = [7,7]
row1 = [7]
```

row0 的两个 occurrence 都满足 lowest-owner，候选会把 row1 更新两次，baseline row1 只
更新一次。两种情况都错。

所以必须二选一：

- 当前最窄方案：只在已证明 unique 的 `qsa_select_paged_tokens` 私有 producer path
  dispatch，exact Prefill/Mixed fixture 对每行做 unique-count 证明，公共 sparse ABI 默认
  不选择该实现；或
- 把 membership 扩展为 per-row multiplicity，并设计“每个 target row 更新不同次数”的
  语义，这会破坏一次 shared K/V 对应一个 dense 12-lane update 的简单路径，需重新评估。

不能仅用 `atomic_or` 后的 bits 在 runtime 检测同行重复，因为第二次 OR 不会留下新信息。
若需要通用 runtime guard，builder 必须另存 occurrence counts 或 duplicate flag；检测到后
整组 fallback。

## 4. invalid token/page/request

### negative 与 bucket overflow

- `token < 0` 不写 membership、不设 overflow、occurrence 直接无效；
- `token >= TOKEN_BUCKET` 必须先设 group overflow，且 atomic pointer 使用 clamp 后的
  safe token 加 mask，不能先形成可访问的越界地址；
- overflow group 整组 fallback，不能只跳过 high token，否则在大 page-table 下会漏掉
  baseline 的合法 token。

build 已经写入的部分 membership 在 overflow fallback 中必须完全忽略。
attention 扫描 occurrence 时也必须用 clamp 后的 safe token，并以
`eligible & 0<=token<TOKEN_BUCKET` mask membership load；不能因为 overflow 已使
`eligible=False` 就无条件形成 `membership[g,token]` 地址。Triton 的 `tl.where`/masked
表达式不等于 Python short-circuit，所有候选地址都必须先保证安全。

### request guard

“四行 request 相同且非负”不充分。反例是四行都为 `request=num_requests`：最低-owner
逻辑会判 eligible，却会越界读取 block table。grouped 条件必须包含：

```text
0 <= common_request < num_requests
```

fallback 中每个 phase 独立计算 `valid_request`，用 clamp 后 `safe_request` 形成地址，只有
valid mask 才真正 load。invalid request lane 的最终 output exact zero。

### logical/physical page

同一 grouped request 对同一 logical token 使用同一 block-table entry。因此 owner token
若 logical page 越界或 physical page 为 `-1`/超 cache 范围，所有选择该 token 的 rows
都应跳过；后续非-owner occurrence 继续跳过是正确的。这个结论依赖 same-request guard；
跨 request 时同一 logical token 可能映射到不同 physical page，只能 fallback。

page validity 必须进入 `load_col`，否则 masked score 并不能阻止越界 K/V 读取。
同理，logical-page、physical-page、request 和 row 的 pointer 都先用 safe/clamped index
形成，再由 mask 决定访问；不能依赖 data-dependent branch 阻止错误地址求值。

## 5. fallback 与唯一写者

最安全的首个 kernel 不是“grouped kernel 写 eligible rows，再调用 baseline 修 rejected
rows”，因为 device eligibility、tail 和 overflow 很容易让两个 kernel 对同一 output 产生
重叠写或 race。建议一个 group program 内使用统一事务：

```text
eligible = full_four_rows
           & same_valid_request
           & consecutive_nonnegative_positions
           & !overflow
           & producer_unique_contract

phase r 的 column load mask =
    eligible ? (owner_col & valid_page) : (row_r_token & row_r_valid_page)

phase r 的 lane mask =
    eligible ? membership_of_each_lane_row : only_lanes_belonging_to_row_r
```

二者合成同一套 per-lane softmax state，循环结束后每个存在的 row/head 只 store 一次。
若编译器不支持可靠的 uniform device branch，也应使用上述互斥 masks；不能先执行 grouped
update 再叠加 fallback update。

具体要求：

- request boundary、不连续 position 或 overflow 使 **整组** `eligible=False`，不能只把
  单行送 fallback；
- fallback phase `r` 用第 r 行自己的 request 和原始 occurrence 顺序，只激活该行三个
  head lanes，membership 完全不参与；
- tail group 只 load/store `base+r < rows` 的 lanes；不存在的 row 不形成 query/output 地址；
- invalid request row 的状态保持空，final output 为零；同组其他合法 rows 仍分别 fallback；
- output 预填 sentinel，并用独立 `write_count[row,head]` 测试器证明存在 lanes 恰好写一次。

如果实现选择 separate grouped/fallback kernels，则必须先生成 disjoint group flags，并让
两个 kernel 的 output store masks 形式化互斥；这比统一 kernel 风险更高，不建议作为首个
原型。

## 6. 最小可执行伪代码

以下标准 Python 伪代码使用标量 K/V 表示一个 head-dim 元素，但完整表达 presence bits、
12 独立 lanes、online softmax、owner skip 和 fallback。把标量 `q*k`/`a+p*v` 替换为
向量 dot/accumulator 即是目标语义。

```python
from math import exp

R, H = 4, 3

def update(state, score, value):
    m, z, a = state
    nm = max(m, score)
    alpha = 0.0 if m == float("-inf") else exp(m - nm)
    p = exp(score - nm)
    return nm, z * alpha + p, a * alpha + p * value

def finish(state):
    _m, z, a = state
    return 0.0 if z == 0.0 else a / z

def r4_owner(selected, q, requests, positions, num_requests,
             token_bucket, lookup, producer_unique=True):
    # lookup(request, token) -> (key, value), or None for invalid page.
    full = len(selected) == R
    same_valid_request = (
        full and 0 <= requests[0] < num_requests
        and all(request == requests[0] for request in requests)
    )
    consecutive = (
        full and positions[0] >= 0
        and positions == list(range(positions[0], positions[0] + R))
    )
    overflow = any(
        token >= token_bucket for row in selected for token in row if token >= 0
    )
    unique = producer_unique and all(
        len([t for t in row if t >= 0]) == len(set(t for t in row if t >= 0))
        for row in selected
    )
    eligible = same_valid_request and consecutive and not overflow and unique

    states = [[(float("-inf"), 0.0, 0.0) for _ in range(H)] for _ in range(R)]
    load_trace = []
    update_trace = [[] for _ in range(R)]

    if not eligible:
        # Original occurrence order and multiplicity; one output transaction.
        for r, row in enumerate(selected):
            valid_request = 0 <= requests[r] < num_requests
            for token in row:
                if token < 0 or not valid_request:
                    continue
                kv = lookup(requests[r], token)
                if kv is None:
                    continue
                key, value = kv
                load_trace.append((r, token))
                update_trace[r].append(token)
                for h in range(H):
                    states[r][h] = update(states[r][h], q[r][h] * key, value)
        return [[finish(x) for x in row] for row in states], load_trace, update_trace

    bits = [0] * token_bucket
    for r, row in enumerate(selected):
        for token in row:
            if token >= 0:
                bits[token] |= 1 << r

    for owner_row, row in enumerate(selected):
        lower = (1 << owner_row) - 1
        for token in row:
            if token < 0:
                continue
            membership = bits[token]
            owner = (membership & lower) == 0 and (membership & (1 << owner_row))
            if not owner:
                continue                 # before page/K/V/state access
            kv = lookup(requests[0], token)
            if kv is None:
                continue
            key, value = kv              # one K/V load for all selected lanes
            load_trace.append((owner_row, token))
            for target_row in range(R):
                if not (membership & (1 << target_row)):
                    continue
                update_trace[target_row].append(token)
                for h in range(H):
                    states[target_row][h] = update(
                        states[target_row][h], q[target_row][h] * key, value
                    )
    return [[finish(x) for x in row] for row in states], load_trace, update_trace
```

实际 Triton tile 不能用 Python `continue` 跳过单 column，但必须用等价的
`owner_col/load_col/score_lane_col` masks，使上述 trace 和状态更新完全一致。

## 7. 必须执行的最小反例

### A. shared token exactly once + 顺序冲突

```python
selected = [[20], [30,20], [20,40], [40,30]]
```

断言：K/V load token 集合恰为 `{20,30,40}` 且每个一次；各 row update token 多重集合与
自己的 selected 相等；row1 baseline 顺序 `[30,20]`，candidate trace `[20,30]`，所以
只要求 FP32/BF16 tolerance，不要求 byte equality。

### B. lowest bit 不是 row0

```python
selected = [[1], [7], [2,7], [7,3]]
```

token 7 的 bits 为 `0b1110`，owner 必须是 row1；只在 row1 occurrence load 一次，并更新
rows1/2/3 的九个 head lanes。

### C. 同行 duplicate 反例

```python
[[7], [7,7], [], []]
[[7,7], [7], [], []]
```

若强制走 grouped，两例都必须故意显示与 baseline 不一致；正常 dispatch 必须因 producer
contract 不成立而 fallback，并精确保留 multiplicity。这是防止错误泛化到公共 ABI 的测试。

### D. invalid page owner

四行都选择 token 9，但 `lookup(request,9)=None`。断言 owner 和后续 occurrence 都不更新
任何 state、没有 K/V load、输出零。再让组内 requests 不同且只有 request1 的 token9
有效，断言整组 fallback，request1 正常输出，不能沿用 request0 的 invalid 结论。

### E. request 上界

四行 `request=num_requests`、position 连续、token 都小于 bucket。断言不能 grouped；
fallback 不读取 block-table，四行输出 exact zero。

### F. overflow 与部分 membership

前三行先写入正常 token，第四行含 `token=8192`。断言 overflow 使整组 fallback，正常
token 仍按原路径处理，高 token 是否有效由真实 page-table 决定；部分 membership 不得影响
输出。

### G. request boundary、tail 与唯一写者

- 物理 group 的 requests `[0,0,1,1]`；
- rows 总数为 `4094`、`4097`；
- 一个 position discontinuity 和一个 `-1` padding。

预填 output sentinel 并启用 write counter。断言每个存在且有效的 `(row,head)` 写一次，
不存在 row 零次；没有 grouped+fallback 双写，没有未写 sentinel。

### H. stale membership graph replay

capture A 中 token 5 bits=`0b0001`，replay B 中变为 `0b1000`，再恢复 A。若 clear 缺失，
B 会错误保留低 owner bit，使 row3 occurrence被跳过。A/B/A replay 必须分别得到 owner
row0/row3/row0，并匹配 generic oracle。

## 8. 实现审查清单

- [ ] unique producer contract 不暴露为一般 sparse ABI 默认路径；
- [ ] grouped request guard 包含 `< num_requests`；
- [ ] high token 在任何 membership address 前设置 overflow/safe pointer；
- [ ] build 和 attention 两处 membership address 都对 negative/high token 使用 safe index；
- [ ] clear 覆盖 current groups 的全部 8192 int32 slots 和 overflow flags；
- [ ] non-owner columns mask page-table/K/V load，未选 rows mask softmax update；
- [ ] 12 lanes 各有独立 FP32 max/norm/acc，lane12-15 永远不 store；
- [ ] grouped/fallback masks 互斥，fallback 不读取 membership；
- [ ] tail/invalid request 使用 safe address 和 exact-zero 输出；
- [ ] changed-order adversarial BF16 reference 通过，而非只测相同顺序；
- [ ] write counter 证明所有存在 lanes exactly once；
- [ ] A/B/A replay 证明 membership 和 overflow 每次重建。

只有清单全部满足，lowest-owner 才是“数学正确、实现可证伪”的候选；它仍不证明 PPU 上
完整事务变快，clear/build/group kernel 必须一起进入 rows4096 eager/graph 计时。
