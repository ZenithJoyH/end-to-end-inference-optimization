# op-016: MoE split-K / reduction frontier

## 决策

- 类型：`operator/improve`，只读源码与现有证据审计。
- 状态：`stopped-before-microbenchmark`。
- 候选机制：将 GEMM2 的 top-k routed output 直接归约到最终
  hidden output，避免 `intermediate_cache3` 的独立 `moe_sum` launch。
- 结论：即使假设删除全部 `moe_sum` 完全免费，且 GEMM2 的
  atomic 写回与 output zeroing 也完全免费，M4096 Prefill 的完整
  GEMM+reduction transaction 收益上界仅 `5.143%`，prof005 Mixed 的宽松上界仅
  `4.808%`，M64 Decode 微基准上界仅 `0.562%`。三者都低于预冻结
  `8%` 完整 transaction 门槛，因此不写微基准、不改远端源码、
  不占用加速卡。

## 运行身份和源码路径

- 容器：`qwen3.8-flash-opt-candidate-20260919`。
- Plugin revision：`939600b323c02c21916f1f76bfb4cd8c2b02578d`。
- FlagGems revision：`2b1e5cfdbd22d453933b2c6589a29daf31315ccd`。
- Plugin 实际路径：
  `/workspace/vllm-plugin-FL-qwen38-adaptation/vllm_fl/ops/fused_moe/fused_moe.py`，
  SHA-256 `8749de1a11952718ef6562ef84e05531547af891bec9a0c89406f74f4f610b26`。
- FlagGems kernel：
  `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`，
  SHA-256 `a780da6348ba611640b546b47c60b79baa1312094386ce8f49d99d0d8e4750af`。
- FlagGems reduction：
  `/workspace/FlagGems/src/flag_gems/fused/moe_sum.py`，
  SHA-256 `1d56ffe67db83c9fbc21bf73d2df4818d25cd6f44c689e60902fb7386c412651`。
- 对上述三个文件的定向 `git status --short` 为空；本轮没有修改
  容器、服务或共享源码。

## live call chain、shape 和 buffer

Plugin 当前每层依次执行：

```text
fused_experts_impl
  -> moe_align_block_size
  -> invoke_fused_moe_triton_kernel          # GEMM1
  -> silu_and_mul                            # activation
  -> invoke_fused_moe_triton_kernel          # GEMM2, routed weight
  -> moe_sum                                 # top-k FP32 accumulation
```

rank-local BF16/TP8 生产 shape：

| stage | M64 Decode | M4096 Prefill/Mixed |
|---|---|---|
| hidden | `[64,2560]` | `[4096,2560]` |
| W1 | `[512,160,2560]` | 同左 |
| GEMM1 output/cache1 | `[64,10,160]` | `[4096,10,160]` |
| activation/cache2 | `[640,80]` | `[40960,80]` |
| W2 | `[512,2560,80]` | 同左 |
| GEMM2 output/cache3 | `[64,10,2560]` | `[4096,10,2560]` |
| final output | `[64,2560]` | `[4096,2560]` |

当前 tuned config：

- M64：`BM16/BN64/BK128/GROUP1/warps4/stages3/SPLIT_K1`。
- M4096（M2017 也相同）：
  `BM128/BN128/BK64/GROUP1/warps8/stages3/SPLIT_K1`。
- Plugin 只取一个 config 同时传给 GEMM1/GEMM2。FlagGems wrapper 再执行
  `config["SPLIT_K"] = 1`。当前 `fused_moe_kernel` 虽有 `SPLIT_K`
  constexpr，但 pid 映射、K 循环和写回都没有使用它；所以修改
  config 不是 split-K，真正 split-K 需要新的 K 分片 grid 和 partial-buffer/
  atomic reduction 路径。

M4096 中 cache1 约 `12.5 MiB`，cache2 约 `6.25 MiB`，cache3 约
`200 MiB`，final output 约 `20 MiB`。然而 Plugin 用
`M*topk*max(N,K)` 一次分配共享的 cache13；仅绕过 cache3 使用而不重写
分配逻辑，不会自动降低这个 `200 MiB` 峰值分配。

## direct-sum 扩展点和数值边界

FlagGems 已有一条非 live Plugin 路径的 `direct_sum` 能力：

1. wrapper 接受 `direct_sum`/`out_top_k`；
2. GEMM2 将 routed weight 乘到 accumulator 后，以
   `offs_token // OUT_TOP_K` 定位 final row；
3. 用 BF16 `tl.atomic_add(..., sem="relaxed")` 直接归约；
4. 高层实现会先对 final output `zero_()`，再省略 `moe_sum`。

这是可复用的最窄扩展点，但它比上界假设更昂贵：atomic 替换普通
GEMM2 store，且增加 zeroing。它的数值语义也不等同于当前
`moe_sum`：当前 kernel 先把 10 个 BF16 routed outputs 加到 FP32 accumulator
后写回 BF16；direct-sum 是多次 BF16 atomic 加，顺序和舍入都可变。
所以它若未被上界拒绝，仍必须单独验证 allclose、graph capture 和两次
replay 稳定性，不能以现有代码存在代替证明。

## 完整 transaction 收益上界

### M4096 Prefill

prof005 八 rank 中位数：

- `fused_moe_kernel`：96 calls / `107662.622 us`；
- `moe_sum_kernel`：48 calls / `5836.867 us`。

为了故意高估收益，分母只包含两个 GEMM 和 reduction，忽略了
activation、alignment、dispatch 等所有其他开销。再假设 `moe_sum`
可以零代价整个删除：

```text
upper_bound = 5836.867 / (107662.622 + 5836.867)
            = 5.1426%
```

### prof005 Mixed

八 rank 中位数：

- `fused_moe_kernel`：6046 calls / `7227220.500 us`；
- `moe_sum_kernel`：3023 calls / `365037.177 us`。

同样的宽松上界为：

```text
upper_bound = 365037.177 / (7227220.500 + 365037.177)
            = 4.8080%
```

这还高估了实际候选：Mixed 含 M4096 admission 和同时 Decode，而
M>=4096 guard 只能删除其中一部分 reduction；atomic 与 zeroing 的时间
也还没有扣除。

### M64 Decode

op011 相同生产 shape 微基准的 retained 中位数：

- `GEMM1 + activation + GEMM2` pair：`0.5754587936 ms`；
- 完整 pair + `moe_sum`：`0.5787131882 ms`。

即使把两个独立计时的差全部归因于可删除 reduction，上界也只有：

```text
upper_bound = (0.5787131882 - 0.5754587936) / 0.5787131882
            = 0.5624%
```

## split-K 判定

- GEMM2 的 K 只是 80：M64/BK128 只有 1 次 K 循环，M4096/BK64
  也只有 2 次，不是有意义的 split-K 对象。
- GEMM1 的 K=2560 虽然可分，但当前源码没有 split-K 实现，且 M64
  已有大量 expert/N programs；新路径还要支付 partial 写回和第二次归约。
- M64 中 GEMM1 仅为 `0.190775 / 0.578713 = 32.97%` 的完整
  transaction。在不计任何 split reduction 开销时，要获得 8%
  完整收益，GEMM1 至少需要缩短 `24.27%`（约 `1.3205x`）。现有
  trace/微基准和源码不支持这一预测，因此不越过“先预测
  >=8%”门禁去设计高成本 split-K 微基准。

## 停止条件与重开条件

本轮已命中停止条件：一个已有源码扩展点、且把实现成本置零后的
归约机制，在 M64、M4096 Prefill 和 P4K Mixed 都低于 8% 完整
transaction 门槛。

只有下列新证据才重开：

1. 新 profile 证明某个生产 shape 中 reduction 单独占完整 MoE
   transaction `>=8%`；或
2. 可复用的 PPU split-K kernel 在相同 BF16 expert-routed GEMM1 shape 上已有
   包含 partial reduction 的测量，能预测完整 transaction `>=8%`。

重开后仍必须先做最小独立微基准，要求 BF16 reference/allclose、
graph capture + 两次 replay，并将 zeroing、partial/atomic reduction 和完整
GEMM1+activation+GEMM2+reduction 全部纳入计时。

## 证据

- prof005 聚合：
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/profiling/prof-005-p4k-post-op010/summaries-v2/hotspot-aggregate.json`。
- M64 完整 transaction：
  `/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/microbench/op011-m64-gemm2-bn128-001/result.json`，
  SHA-256 `bbdcf8dae7f8aa4b86fa406cff6cf9532b0663c77f77c21412492ee5f5397db7`。
- 源码行为：FlagGems `fused_moe.py` 的 kernel 写回、wrapper 强制
  `SPLIT_K=1` 与高层 direct-sum guard；Plugin `fused_moe.py` 的 cache13/
  cache2 分配及 GEMM1→activation→GEMM2→`moe_sum` 调用链。
