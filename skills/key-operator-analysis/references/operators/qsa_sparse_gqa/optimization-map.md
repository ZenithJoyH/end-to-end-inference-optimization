# QSA sparse GQA 案例驱动优化地图

## 已验证规则：小头维度特化必须在生产 rows 上过门槛

- 证据等级：`reproduced_microbenchmark_no_go`。
- 匹配范围：PPU，TP8，BF16，query heads 3，head dim 256，KV heads 1，
  TOPK 2051，FlagGems sparse paged GQA。
- 触发信号：wrapper 将 `GROUP_SIZE=3` 圆整到 `BLOCK_M=16`，拟通过
  字面量 4-lane tile 减少 masked 逻辑 lane。
- 第一检查：确认 live query/KV/index shape、dtype、TOPK、实际 dispatch 和
  生产 rows 分布；不能仅从 group size 判断优化价值。
- 首个实验：独立比较现 kernel 与无可调 `BLOCK_M` 的字面量 4-lane
  候选，至少覆盖 rows64 和生产 rows4096、无效 request、非连续页、
  BF16 reference、graph capture 与两次 replay。
- 已知结果：rows64 graph +21.659%，rows4096 graph -4.563%。小 shape 收益
  不能作为生产候选晋级依据。
- 停止条件：生产 rows 完整 sparse transaction 不达当前任务的预冻结
  算子门槛，或任一数值/graph/边界条件失败。
- 服务晋级：只有生产 rows 过门槛后才能修改实际源码，并回到
  无 profiler 的同卡组端到端评测。
- 来源：[Qwen3.8 op-015 证据卡](case-index.md#case20260919-qwen38-flash-next-ppu-e2e--op-015)。

## 已验证规则：selected-set 复用不能跳过完整构建成本门禁

- 证据等级：`reproduced_microbenchmark_no_go`。
- 匹配范围：PPU，TP8，BF16，rows4096，query heads 3，head dim 256，
  TOPK 2051，R4 跨行 selected-set union，8192-token direct-address
  membership。
- 触发信号：真实 P4K selected 形状中 R4 occurrence 复用约 69.5%，
  拟通过联合 K/V 读取降低 sparse GQA 成本。
- 第一检查：在服务接入前，用真实生产 rows 与 selected 分布计时完整
  consumer 事务；必须把 output clear、workspace clear、union/membership
  build、grouped attention 和 exact fallback 全部纳入。
- 已知结果：Prefill `rho=0.695121889`，但包含 33,644,552-byte
  workspace 的完整 R4 事务相对 generic 在 eager/graph 退化
  32.5219%/32.2212%；测量稳定且正确性全通过。
- 修正后的理解：高 selected overlap 只是 K/V 复用上界，不是净收益保证。
  任何依赖大型 direct-address workspace 的方案必须先证明构建和清零成本，
  不得只报 union 率或理想 K/V 字节节省。
- 停止条件：完整事务未达当前任务的 8% rows4096 门槛，或需要把
  clear/build/fallback 移出计时边界才显示收益。
- 来源：[Qwen3.8 op-022 证据卡](case-index.md#case20260919-qwen38-flash-next-ppu-e2e--op-022)。
