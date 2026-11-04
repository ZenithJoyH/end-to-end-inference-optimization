# 20260920-p4k-large-m-moe-config-audit-06 P4K large-M fused MoE

- 状态：`rejected/reverted`
- 分类：`operator/improve`
- 目标场景：P4096/D1024/C64/N128
- 目标阶段：Prefill、Mixed；Decode 作为守护

## 优化方向与瓶颈依据

P4K trace 中 fused MoE 占 rank0 Prefill/Mixed/Decode 累计设备活动
27.883%/22.019%/42.514%，其中 large-M GEMM 在 Mixed 单列约 12.515%。此前
Plugin 的 `M>=4096` BF16 stage config 在旧 launcher 上使 P4096/D128 吞吐
+2.609%，但迁仓后的当前 FlagGems-vllm 默认配置已经变成
`BM64/BN256/BK32/GM8/warps4/stages4/int32-offset`，旧 Plugin 特化所要求的
`BM128/BN128/BK64/GM1/warps8/stages3` 基线不再存在，因此旧 guard 不能证明
当前 P4K 仍需要旧 stage 配置。

## 单变量实验

在当前 FlagGems-vllm launcher、BF16、E288/H4096/I128/topk8、P4K 主
`M=16384` 上，分别比较：

- current：当前生产 `BM64/BN256/BK32/GM8/w4/s4/int32-offset`；
- legacy GEMM1：旧保留配置的 `BM128/BN128/BK128/GM1/w8/s3`；
- legacy GEMM2：旧保留配置的 `BM128/BN256/BK64/GM16/w8/s3`。

每个配置使用与自身 BM 一致的 MoE alignment，保持算法、权重、路由和输出语义
不变；graph capture + 两次 replay 后 5 次预热、11 次计量。legacy 仅在对应 stage
比 current 中位快至少 5%、数值通过时，才进入源码 guard 和 P4K 端到端验证。

## 算子筛选与落源验证

- 旧 GEMM1 配置：当前 `2.84852 ms`，旧配置 `3.14224 ms`，仅
  `0.9065x`，拒绝。
- 旧 GEMM2 `BM128` 配置：算子中为 `1.0903x`，但如果只在
  launcher 中替换会与当前 `BM64` 的 MoE alignment 边界不一致，不作为
  安全候选。
- 在保持 `BM64/BN256` 与当前 alignment 不变的扫描中，
  `BK64/GM16/warps8/stages3/int32-offset` 从 `3.22596 ms` 降到
  `3.00396 ms`，为 `1.07390x`，且输出精确一致。
- 候选以精确 guard 落到 FlagGems-vllm：仅命中
  `M16384/E288/H4096/I128/topk8/BF16/GEMM2`，其他 M/shape 保持原路径。
  源码命中后 graph A/B 为 `3.22860 → 3.00340 ms`，约
  `1.07498x`；graph capture 和两次 replay 通过，输出精确一致。
- 聚焦单测与已保留 small-M/M64 回归共 `42 passed`。

## 正确性与风险

算子输出对 current 使用 `atol=rtol=0.05`，同时记录最大绝对误差；
落源后另行要求 graph capture 与至少两次 replay。端到端使用新进程
baseline/candidate/revert，每个角色 6 轮预热 + 3 轮正式测量，共
`1152/1152` 个正式请求成功。测量后已恢复源文件 SHA
`f70ff827bc1bce13fc42ca05ac7dd11e28ffd83745aee9808f0715ac7b9baa66`，
它只包含之前已保留的 small-M/M64 优化，不包含 P4K 候选；服务已停止。

## 性能效果

端到端 milestone 映射到正式 `P4096/D1024/C64/N128`，实际使用
`P4096/D128/C64/N128`。三个角色均为全新服务进程、关闭前缀缓存，
启动参数除候选配置外一致。

| 角色 | output tok/s 中位数 | 正式轮离散度 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|---:|
| baseline | 282.7895 | 0.6883% | 24403.02 ms | 218.43 ms |
| candidate | 280.9980 | 9.7383% | 24390.93 ms | 219.44 ms |
| revert | 282.7046 | 0.6495% | 24399.94 ms | 218.56 ms |

- candidate 相对 baseline 吞吐 `-0.6336%`，未达 `+3%` 晋级门槛。
- candidate 第 8 轮降到 `255.4991 tok/s`，正式轮离散度 `9.7383%`，
  超过 5% 稳定性门槛。
- revert 相对 baseline 只漂移 `-0.0300%`，且离散度恢复到 `0.6495%`，
  证明整组环境可比。
- 结论：候选已拒绝并回退，不晋级 `P4096/D1024/C64/N128`。
  这一结果表明单个 large-M GEMM2 的局部 `~7.5%` 改善被 MoE 其他阶段、
  Sparse MLA、通信与调度开销稀释，且该配置存在额外抖动风险。

## 外部证据

- 算子审计路径：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/large-m-moe-06`
- 端到端 A/B/R：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/candidates/large-m-moe-gemm2-06/milestone-p4096-d128`
- 结构化摘要：上述目录中 `abr-summary.json`，SHA256
  `fa38960fa424aefc2485059a24bb80ce7e73177111c7277dc9c6e746fc53d141`。
- 候选源文件归档 SHA256：
  `4aa5f49ad5bb6ac1200dc433597630e4722857a83cf55ef88f2bb47058d6e4c6`。
