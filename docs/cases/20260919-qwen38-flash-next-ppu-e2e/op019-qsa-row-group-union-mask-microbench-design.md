# op-019：QSA row-group union/mask 完整事务微基准设计

## 结论与冻结候选

op-018 的真实 P4096 selected-index 遥测已经超过重开门槛：

| R | Prefill `rho_R` | Mixed `rho_R` | 解释 |
|---:|---:|---:|---|
| 2 | 44.0555% | 44.0526% | 同为 BM16 但复用和 metadata 不及 R4，不实现 |
| 4 | 69.5122% | 69.4798% | op-019 唯一首跑臂：12 query-head lanes 仍为 BM16 |
| 8 | 83.8933% | 83.7094% | 暂不实现，workspace/编译风险更高 |
| 16 | 91.7276% | 91.2856% | 暂不实现，workspace/编译风险更高 |

Mixed 的完整组 coverage 至少为 `99.479%`，并观测到 `rows=4096`、
`request_runs=2`。所以这不是只在单请求 Prefill 成立的交集。结合独立事务成本模型，
op-019 只实现 R4；R2 被同样 BM16 下更高的 metadata 和更低复用严格支配，
R8/R16 则会把物理 M tile 增至 32/64。

R4 不是为了追逐遥测中的最大百分比。对饱和 `|T_i|≈2051` 的近似形态：

```text
R2: U≈2*2051*(1-0.4405)=2295, dense score cells≈2*2295
R4: U≈4*2051*(1-0.6950)=2502, dense score cells≈4*2502
```

即 R4 的每组 union 只比 R2 大约 9%，而被同一份 K/V 服务的 query-head 数从
`2*3=6` 增至 `4*3=12`。若 PPU/Triton 的 dot M tile 实际下限仍为 16（op-015
已观察到小 M 会被调整），R2 只有 `6/16` 有效 query lanes，R4 为 `12/16`；
R4 可能比 R2 更符合硬件布局。代价是 R4 的 dense membership density 约 82%，
低于 R2 的约 89%，并且每组 union 建表更大。两臂必须分别测完整事务，不能只用
流量模型定胜负。

## 微基准回答的唯一问题

在真实 P4096 expanded selected-index 形态不变时，以下候选完整事务是否同时满足
数值、invalid、graph 和性能门禁：

```text
输入 selected [rows,2051]
  -> device-side 同请求连续行分组
  -> device-side union + per-row membership/multiplicity 建表
  -> grouped sparse attention（每行/每 head 独立 softmax state）
  -> 不合格组和 segment tail 的原路径 fallback
  -> BF16 output [rows,3,256]
```

基线是相同输入上的当前 `qsa_sparse_paged_attention`。候选计时区必须包含 union、
membership、layout 转换、grouped attention、tail/rejected fallback 和必要的 workspace
清零。`torch.topk + expand_qsa_block_indices` 是两边共同的上游，不计入本微基准；
如果最终方案把 union 生成融合进 select/expand，则另加一项 select-to-output 完整链路
测量，不能用本结果覆盖那部分开销。

禁止以下不完整比较：Host/Python 预建 union、计时前缓存 membership、只计 grouped
attention kernel、只测理想相同 selected set、或把 telemetry 的 `rho` 当作加速比。

## 可复现的真实 selected-index fixture

### 为什么 op-018 summary 不够

op-018 只保存 `(B,A_R,U_R,R*U_R,group_count,tail_count)`。这些计数足以证明复用
上界，但不能重建每个 token 属于哪些 row，也不能复现 union 构建、mask 访问和 causal
位置分布。因此 op-019 在写 kernel 前需做一次独立的、非计时 fixture capture；不得从
`rho` 合成一个“刚好过门槛”的集合。

### capture 内容

从与 op-018 相同的真实 rank0 P4096 Prefill 和 Mixed 调用各冻结一份：

- `selected.int32.bin`：最终 expand 后的 `[4096,2051]`，保留 `-1`；
- `token_to_req.int32.bin`：`[4096]`；
- `logical_positions.int64.bin`：`[4096]`；
- `query_start_loc.int32.bin`：`[num_reqs+1]`；
- `seq_lens.int32.bin`：`[num_reqs]`；
- `manifest.json`：shape、dtype、byte length、每个文件 SHA-256、phase、rows、
  request-runs、source SHA、Plugin/FlagGems revision、capture 时间和 op-018 summary SHA。

使用无 pickle 的原始 little-endian 连续数组；读取后校验 byte length 和 SHA，再复制到
device。fixture 只含逻辑位置，不含 prompt/token 内容或 K/V。它保留在远端 case artifact
目录，不提交仓库。

capture 后必须重新计算 op-018 的每个 R 指标，并与 summary 逐整数 counter 相等；否则
fixture 无效。对每 row 的非负 selected token 还需断言无重复。若真实输入存在重复，
候选必须保存 multiplicity，而不能把 set union 当成语义等价；在有 multiplicity 实现前
停止。selected 列顺序保留，不排序后落盘。

### 一次性 capture 材料与运行边界

- helper：`op019-qsa-exact-fixture-capture-helper.py`；
- SHA/anchor guarded apply：`prepare-op019-qsa-exact-fixture-capture.py`；
- 人工审查 patch：`op019-qsa-exact-fixture-capture.patch`；
- Prefill/Mixed 唯一 arm：`arm-op019-qsa-exact-fixture.py`；
- fixture/op-018 counter 校验：`verify-op019-qsa-exact-fixture.py`；
- exact revert：`revert-op019-qsa-exact-fixture-capture.sh`。

服务必须是隔离卡上的 `--enforce-eager` 诊断服务，并设置：

```text
VLLM_FL_QSA_FIXTURE_CAPTURE=1
VLLM_FL_QSA_FIXTURE_RANK=0
VLLM_FL_QSA_FIXTURE_ARM_FILE=<unique-phase-dir>/arm.json
VLLM_FL_QSA_FIXTURE_OUTPUT_DIR=<unique-phase-dir>
```

prepare 必须显式传当前 `qsa.py --expected-sha256`；revert 只接受 prepare 生成的
`patch-manifest.json`，且 patched source/helper 任一 SHA 漂移时拒绝盲回退。Prefill 和
Mixed 使用两个从未存在过的 output dir，各自启动或重启指向其 arm 的诊断服务。helper
只在 expected rows/request-runs 命中后原子 claim arm；完成后结果位于
`<output-dir>/<sample-id>/`，内含 manifest 和 SHA256SUMS。

helper 在 `qsa_select_paged_tokens` 可直接取得 `sequence_lengths`，因此保存真实 seq_lens；
该函数没有 `query_start_loc` 参数，保存值由本次调用的连续非负 `token_to_req` runs 重建。
它在 row-major、每个 request 只出现一个连续 run、负 padding 仅为 suffix 时与 scheduler
边界等价；helper 会逐项验证这些条件并在 manifest 记录限制。它不是 scheduler 原 tensor，
不得跨 QSA 调用或 step 复用。

### rows64 与 rows4096

- `rows4096`：完整 fixture，保留真实 request segments、segment tails 和 Mixed 两请求
  边界，是性能主场景。
- `rows64`：只作编译、正确性和小 shape 守护。选择算法固定为：在 fixture 中取最长的
  request segment（并列取最先者），取其中以 16 对齐、离 segment 中心最近的连续 64 行；
  记录原始 `[start,end)`。不得按 overlap 最大的窗口挑选。
- Prefill 和 Mixed fixture 分开跑；不能用 Prefill 的 rows4096 代替 Mixed。

Q/K/V 不从生产导出。按 `fixture_sha + phase + rows + mode` 派生固定随机种子，在设备上
生成 BF16 `q[rows,3,256]` 和紧凑 `k/v[num_pages,16,1,256]`。`num_pages` 由
`seq_lens` 和 selected 的最大合法 logical page 确定。这样 selected membership 是真实的，
数值输入可公开复现且不包含业务数据。

## valid 与 invalid/noncontiguous 两种模式

### valid

每个 request 的 block-table 是合法 logical page 到紧凑 physical page 的一一映射。
request 间允许复用相同 physical cache fixture，因为两个实现消费完全相同的表；manifest
必须记录这个合成边界。

### invalid_noncontiguous

从同一真实 selected fixture 确定性派生，不另选高 overlap 输入：

1. physical page 使用与 page 数互素的仿射置换；若 page 数不是 256，运行时选取最小
   互素 multiplier，禁止硬编码一个可能不互素的常数；每个 request 再做不同 roll；
2. block-table 每第 31 个 logical page 置 `-1`，覆盖 invalid physical page；
3. selected 每第 17 列置 `-1`，每第 97 列置为 table width 之外的 logical token；
4. 最后一行 `token_to_req=-1`，倒数第二行设为 `num_requests`；对应行输出必须 exact zero；
5. 再把一个完整组中的 `logical_positions` 置为不连续，另把一个 tail/padding position 置
   `-1`，证明候选不会跨非法边界分组；这些行走逐 row fallback，而非被静默删除。

invalid 模式是正确性压力测试，不用于 8% 性能判定。所有索引修改规则、实际修改计数和
派生输入 SHA 都写入结果。

## 候选语义与实现边界

完整组只能从 `query_start_loc` 的 request segment 首行开始按 R 非重叠切分，并满足：

- `0 <= token_to_req < num_requests` 且组内相同；
- `logical_positions >= 0` 且逐行 `+1`；
- 同一次调用、同一 layer/rank；
- segment 尾部不足 R 的 row 保留原路径。

对合法组，device builder 从各 row 的非负 selected 元素生成 stable first-occurrence
union；membership 至少能区分每个 `(row,union_token)` 是否存在。因 fixture 要求单 row
内无重复，bool/bit membership 足够；否则必须用 multiplicity count。union 顺序可以不同
于各 row 的 score-order，因此 grouped kernel 必须为每个 row、每个 query head 维护独立
online-softmax `(m,l,acc)`，不存在的 cell 当 `-inf/0 probability`。K/V 只允许在 group
层面按 union token 读取一次；page-table 解析仍按该 group 的 request 行进行。

候选 wrapper 的公开输入必须与基线相同，另加已有 grouping metadata；不得从 Host 读取
tensor 值。所有 workspace 在调用外按最大 shape 预分配，但 builder 的写入和清零在计时
函数内。结果记录 workspace 各 buffer 的 shape/dtype/bytes、峰值额外显存和实际 dot
`BLOCK_M/BLOCK_N`。若生成 IR 把 R2 与 R4 都扩成相同 M16，需要明确记录，而不是从 Python
meta-parameter 推断有效 tile。

## correctness reference

每个 phase/rows/mode/R 都执行三层检查：

1. **当前 generic oracle**：candidate 整张输出与当前
   `qsa_sparse_paged_attention` 比较，`atol=rtol=0.05`；两边必须 finite。
2. **独立 FP32 reference**：不调用候选 union 代码，按 selected 的原顺序逐 token 做
   page translation、QK、softmax、PV。至少抽取每个 request segment 的首/中/末行、完整
   group 两侧、segment tail、不连续 position 行和两个 invalid request 行；最多 32 行。
   reference 不自行去重 selected，避免在未来重复输入上改变 softmax multiplicity。
3. **结构 reference**：在 CPU 上为最多 8 个确定性 group 建 stable union/membership，和
   device builder 输出逐元素比较，包括 union size、membership、tail/rejected flags。

BF16 tolerance 沿用 op-015 的 `0.05/0.05`，但 invalid request 的输出必须逐 bit 为 0。
另外报告 candidate-vs-generic max/mean abs 和每个 FP32 sample 的最大误差；只有打印
`allclose=True` 不足以审计。

## graph capture 与动态输入证明

候选必须在生产 graph 模式完成 capture 和至少两次 replay。capture 内包括 builder、
workspace clear、grouped attention 和 fallback，不允许 capture-time `.item()`、Host 控制流、
动态分配或不稳定地址。

仅对相同静态输入 replay 两次不足以证明 union/membership 被 graph 重算。正确性流程固定为：

1. fixture A eager generic/candidate 对齐；
2. capture candidate(A)，保存输出 A；
3. 在 graph 外只把静态 selected buffer 改成 fixture B：保持 shape/segment/cardinality，按
   固定规则对若干合法 selected token 做范围内置换，Q/K/V 保持 A 不变；eager generic(B)
   生成 oracle；这样输出变化只能证明 graph 读取了新 selected，而不能被 Q/K/V 变化掩盖；
4. replay #1，candidate 必须匹配 generic(B)，并且输出不能与 A 完全相同；
5. 把 buffer 恢复 A，replay #2，candidate 必须重新匹配 generic(A)。

generic 也单独 capture 并做相同 replay 检查。性能 graph 使用原始 fixture A，输入变换不在
计时区。结果保存 capture/replay 次数以及 A/B/A 每次 output SHA 或小型数值摘要。

## eager/graph 计时

复用 op-015 的 CUDA event 与原始 samples 记录，但改成成对交错，降低热漂移：

- 首先完成编译和至少 5 次非计时 warmup；
- 每个 sample 内执行 `baseline -> candidate`，下一个 sample 反序；
- rows64 默认 `repeat=20`，rows4096 默认 `repeat=5`，每臂至少 7 samples；
- 每个 event 区间只包含同一函数的 repeat 次调用，之后一次 synchronize；
- eager 和 captured graph 分开计时；baseline/candidate 使用各自预分配 output/workspace；
- 记录每个 sample、median、p25/p75、MAD、min/max、执行顺序、温度/频率可获得信息和
  脚本 SHA。若样本 MAD/median >3%，追加到 11 个 samples，不删除离群点。

`gain=(baseline_median/candidate_median-1)*100%`。不能混用 profiler 时间，不能把 rows64
结果外推 rows4096，也不能把 invalid 模式计时用于晋级。

## 冻结门禁与选择规则

### R 的前置门禁

- op-019 首个且唯一正式候选为 R4：12 个 query-head lane 仍落在 BM16，
  而 69.5% 复用和近中性 metadata transaction 在同 BM16 下严格支配 R2。
- R8/R16 不在本轮范围，因为它们改变 M tile、accumulator 和 occupancy 机制。
- 只有 R4 因单 program 循环、spill 或 grid 并行度而失败，且 builder 与 K/V 删减本身仍有
  明确余量时，才允许一次同实现的 R2 因果对照；这不是预设第二候选。

### 正确性/graph 硬门禁

所有 Prefill/Mixed × rows64/4096 × valid/invalid 的 generic、FP32、结构 reference 均通过；
graph A/B/A 通过；invalid request exact zero；没有 NaN/Inf；segment/tail fallback 命中计数
与 CPU reference 相等。任一失败立即停止该 R。

### 性能主门禁

对 Prefill 和 Mixed 两个真实 `rows4096 valid` fixture，候选完整事务必须同时满足：

```text
eager gain >= 8%
graph gain >= 8%
```

取四个 gain 的最小值作为该 R 的晋级值，不能按 phase 或 execution mode 选择最好的一项。
`rows64 valid` 是小 shape 守护：graph 不得回退超过 2%，eager 不得回退超过 5%；它不提供
晋级收益。invalid 模式只判正确性。

R4 微基准通过只允许进入隔离服务的同配置 P4K milestone，不能直接保留
源码或宣称端到端收益。

## 结果 schema 最低字段

每个 result 至少包含：

- experiment/script/source/fixture SHA，revision/import path，R、phase、rows、mode；
- fixture origin range、request segments、eligible/full/tail/rejected group counts；
- `B/A_R/U_R/rho/coverage/mask_density` 的 fixture 重算值；
- Q/K/V/selected/block-table/workspace shape、dtype、bytes，实际 launch meta/IR 摘要；
- generic/candidate/FP32/structure correctness 与 graph A/B/A 证据；
- eager/graph 全部 raw samples、median/dispersion、gain 和逐项 gate；
- union builder、grouped kernel、fallback 的可选诊断分项时间；分项仅用于归因，正式 gate
  始终用完整事务；
- `primary_gate_passed`、明确 stop reason 和“未修改服务/未证明端到端”的结论边界。

## 从 op-015 复用与必须修正的部分

可直接复用：固定种子 BF16 Q/K/V、合法/invalid page-table、独立 FP32 sampled reference、
CUDA event median、graph capture 和两次 replay、原始 sample JSON、脚本自哈希。

必须修正：op-015 的 selected 是人工仿射排列，不是 production selected 形态；graph replay
没有变化输入；generic/candidate 分段计时而非交错；rows4096 只有一个 synthetic workload。
op-019 不得复制这四个限制。

## 停止条件

- 没有 exact selected fixture，或 fixture 重算 counter 与 op-018 不一致；
- union/membership 在 Host 构建或计时区外复用；
- 单 row selected 有重复但候选只保存 bool membership；
- candidate 没有包含 workspace clear、tail fallback 或 invalid-page 处理；
- graph capture/replay 或动态输入 A/B/A 失败；
- 任一正确性门禁失败；
- R4 完成有效测量，但无法让 Prefill/Mixed rows4096 的四项 eager/graph gain
  全部达到 8%，且分项证据不支持按上述限定做 R2 因果对照。

最后一条触发后停止本方向，不用 R8/R16 的更高理想复用掩盖 builder、mask、dot-layout 的
真实代价，除非新规划拿出独立、可证伪的分项证据。
