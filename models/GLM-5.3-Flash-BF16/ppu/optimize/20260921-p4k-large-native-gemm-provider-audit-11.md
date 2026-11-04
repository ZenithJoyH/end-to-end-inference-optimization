# 20260921-p4k-large-native-gemm-provider-audit-11 P4K native GEMM provider 审计

- 状态：`rejected`
- 分类：`operator/replace`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed

## 优化方向与瓶颈依据

P4K rank0 profile 的平台 native 大 GEMM kernel 在 Mixed 占 12.515%，在 Prefill
占 6.720%，是已否决 Sparse MLA、large-M MoE、MQA、collective 与 mHC 后最大的
剩余可见算子族。当前 thead YAML 将 `addmm/linear/mm/mm_out` 保持在 FlagOS
blacklist，因此服务走平台 native/reference provider。

既有 General MM 对照只覆盖 P1K Decode 的七个小 M BF16 shape，FlagGems 在六个
主要 shape 上仅为 native 的 0.202×–0.382×；不能直接外推到 P4K 的 M4096、
M12769、M16384 大矩阵，但构成本点严格的负向先验。

## 优化内容与适用边界

第一步使用现有 P4K rank0 trace，将 `gemm_ktype...` device event 的 external id
反向关联到 `aten::mm/linear/addmm` 的真实输入维度，按 Prefill/Mixed 累计设备时间
排序。只对高权重且可直接构造的 BF16 shape 比较 native 与 FlagGems，保持单算子
调用、dtype、layout、输出和 graph 条件一致。

## 晋级与停止条件

- external-id/shape 映射完整且候选实际命中，不以函数存在代替 provider 命中；
- eager 与 graph 数值通过，capture 后至少 replay 两次；
- 覆盖主要设备时间的每个候选 shape 中位加速至少 1.05×；
- 若 FlagGems 无支持、fallback、任一主要 shape 低于 1.05×，或估算端到端上限不足
  1%，即停止，不修改 YAML、不启动服务；
- 只有通过算子门槛后才做 P4096/D128 fresh-service A/B/R。

## 当前结果

external-id 映射已将约 3,924,936 µs / 3,932,865 µs（约 99.8%）
的 GEMM device time 关联到真实 `aten::mm` shape。排名前五的 BF16 shape
共占已映射时间约 59.4%，已冻结为第一批算子筛选集。

首次执行在性能测量前因把数据库目录 `/opt/glm53-flash/flaggems`
误当作 FlagGems Git 源码目录而终止；只生成了 preflight 文件，没有
运行任何算子，保留为无效轮 `microbench-01`。实际导入源为
`/workspace/e2e-opt/glm53-20260911/FlagGems`，已修正后使用新目录
`microbench-02`。模型服务停止，YAML 与源码未修改。

五个主 shape 都完成 eager 和 graph 数值比较，并分别完成 capture 后
两次 replay，全部通过 `atol=0.1/rtol=0.02`。graph 中位结果为：

| `M×K×N` | native | FlagGems | native / FlagGems |
|---|---:|---:|---:|
| `16384×4096×512` | 0.56664 ms | 0.67136 ms | 0.844× |
| `16384×16384×24` | 0.47499 ms | 0.55183 ms | 0.861× |
| `16384×4096×2048` | 2.07039 ms | 2.62233 ms | 0.790× |
| `16384×512×4096` | 0.62016 ms | 0.75113 ms | 0.826× |
| `16384×1536×4096` | 1.61455 ms | 1.89876 ms | 0.850× |

这五个 shape 占已映射 GEMM device time 的 59.509%，0/5 达到
1.05× 门槛。按 trace device time 加权后 native / FlagGems 仅为
0.838×，即切换到 FlagGems 预计会使这组 GEMM 时间增加 19.308%。
调优数据库测量前后 SHA 均为 `1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`。

决定拒绝 provider 替换，继续保留 thead YAML 中
`addmm/linear/mm/mm_out` 黑名单和平台 native GEMM。根据预冻结停止条件，
不进入服务 A/B/R。源码、YAML 和启动脚本均未改动，服务保持停止。

## 外部证据

计划写入：
`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/large-native-gemm-11/`

- exact-shape 映射：`analysis/native-gemm-shapes-rank0.json`
- 有效微基准：`microbench-02/shape-*/result.json`
- 结构化摘要：`microbench-02/summary.json`
- 摘要 SHA-256：`6b9129dd1f53d3c675a25d7a87aca455b8e98878e798763fc7f9b3c62a090f0a`
