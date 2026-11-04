# 20260921-p4k-request-index-conversion-review-13 P4K request-index 转换审计

- 状态：`rejected`
- 分类：`operator/improve`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed；Decode 为守护项

## 优化方向与瓶颈依据

rank0 profile 中 vLLM sparse-MLA
`_convert_req_index_to_global_index_kernel` 在 Mixed 占 2.239%，在
Prefill 占 1.965%。精确 launch 分布为：

- `M=16384, grid=(16384,17)`：165 次，中位 3.0078 ms；
- `M=12769, grid=(12769,17)`：11 次，中位 2.3416 ms；
- `M=4096, grid=(4096,17)`：11 次，中位 0.7548 ms；
- Decode `M=64`：1122 次，中位 6.52 µs。

live block 为 128 threads（`num_warps=4`），grid.y=17 与
`NUM_TOPK_TOKENS=2176/BLOCK_N=128` 一致。该实现位于 vLLM
`vllm/v1/attention/backends/mla/sparse_utils.py`，不在当前已授权修改的
Plugin/FlagGems-vllm/FlagGems 三个仓库内。

## 优化内容与适用边界

本点只读使用当前 vLLM kernel，直接筛选
`BLOCK_N{32,64,128}` 与 `num_warps{1,2,4,8}` 的有界组合，不修改
vLLM 源码。覆盖 M4096、M16384 及 Decode M64，保持 int32、
block-size64、top-k2176、valid-count atomic 语义一致。

## 晋级与停止条件

- 直接数值、graph capture 和两次 replay 必须通过；
- Prefill/Mixed 主 shape 加速至少 1.05×，Decode 不回退超过 3%；
- 按 Mixed 2.239% device share 估算的端到端收益低于 1% 则停止；
- 未通过上述门槛时，不请求 vLLM 修改授权、不启动服务；
- 若存在显著候选，先说明最窄 Plugin shim 或 vLLM 参数化方案、影响和回退，
  取得用户同意后再实施。

## 当前结果

三个 exact M 的 output、valid-count、graph capture 及两次 replay 均通过。
最好主 shape 配置为 `BLOCK_N=128/num_warps=1`：

| Shape | live `BN128/w4` | `BN128/w1` | 加速 |
|---|---:|---:|---:|
| Decode M64 | 10.001 µs | 7.617 µs | 1.313× |
| Prefill M4096 | 0.62649 ms | 0.51766 ms | 1.210× |
| Mixed M16384 | 3.10735 ms | 2.42227 ms | 1.283× |

`BN128/w2` 在 Decode 更快（1.368×），但大 M 均不如 `w1`；
`BLOCK_N=64/32` 因 program 数增加而显著回退。候选通过 1.05× 算子
门槛且 Decode 无回退，但按 Mixed 2.2392% device share 估算，
对应 Mixed device-time 收益只有 0.4937%，低于 1% 端到端晋级线。

因此该局部改进只作为未来组合候选记录，当前决定拒绝：没有修改
vLLM，也没有请求扩大授权或启动服务。vLLM 工作树与调优数据库在
测量前后不变；服务保持停止。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/request-index-conversion-13/`

- 精确 shape 结果：`microbench-01/tokens-{64,4096,16384}/result.json`
- 结构化摘要：`microbench-01/summary.json`
- 摘要 SHA-256：`c49a8b73a6bdec4080a2ee383510ef42d7eccf3cf42bb03ef149b7871675bfa4`
