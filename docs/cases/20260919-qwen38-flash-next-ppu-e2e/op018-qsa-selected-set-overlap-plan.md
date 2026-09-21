# op-018：P4K QSA selected-set overlap 一次性遥测

## 唯一问题与结论边界

只回答：真实 P4096 Prefill 与 Mixed 中，相邻同请求 query row 组成的
`R=2/4/8/16` 非重叠组，在 sparse QSA 最终实际读取的 K/V token 集合上，是否存在
足够的组内复用上界，值得继续实现 union/mask。

对 row `i`，令 `T_i` 为 `expand_qsa_block_indices` 后 `out[i] >= 0` 的去重 token
集合；对完整组 `g`，`a_g=sum_i |T_i|`、`u_g=|union_i T_i|`。正式诊断量为：

```text
rho_R = sum_full_eligible_groups(a_g - u_g)
        / sum_all_eligible_rows |T_i|
```

组必须从 request segment 的 `query_start_loc` 开始按 R 非重叠划分，并同时满足
`token_to_req` 相同、`logical_positions` 连续且均非负。尾部不足 R 的 row 保留在分母、
节省按 0 计。另报告 `coverage=完整合格组内 token occurrence/全部合格 row token
occurrence`。只有同一个 R 在 Prefill、Mixed 两份真实样本中都满足 `rho_R >= 0.12`，
才允许进入 union/mask microbenchmark；它仍不是性能收益或端到端结论。

## 精确插入点与产物

目标文件：
`/workspace/FlagGems/src/flag_gems/fused/qsa.py`，函数
`qsa_select_paged_tokens`。插入点固定为：

1. `block_topk = token_topk // compress_ratio` 后创建 collector，传完整
   `query_positions/token_to_req`；
2. 保持真实 `torch.topk`、`expand_qsa_block_indices` 原样；
3. Python chunk loop 完成、`return out` 前对最终 expanded `out` 调用 `finish(out)`。

不得直接用 compressed block 交集替代 `T_i`，因为有效 K/V 读取集合还受 expand、
边界与 `-1` mask 影响。

- 审查补丁：`op018-qsa-overlap-telemetry.patch`
- helper：`op018-qsa-overlap-telemetry-helper.py`
- 带 SHA/唯一 anchor 门禁的实际应用：`prepare-op018-qsa-overlap-telemetry.py`
- 请求与 artifact 校验：`run-op018-qsa-overlap-telemetry.sh`
- 两阶段判定：`analyze-op018-qsa-overlap.py`
- 精确回退：`revert-op018-qsa-overlap-telemetry.sh`

大 tensor 不复制到 Host。`out` 的逐 row 去重、组 union、分子、分母和 coverage 全部
在 device 上计算，只一次同步 18 个 int64 counter，最终每阶段写一个小 JSON。

## 服务与采样执行序列

1. 保持 service50（PPU8–15、8030）不变；只使用已释放 PPU0–7，在同一优化容器中
   启动独立 8031 诊断服务。先保存 `qsa.py` SHA、git status/import path 和服务 manifest。
2. 用 prepare 脚本应用；`--expected-sha256` 必须来自步骤 1，artifact 使用唯一目录。
3. 诊断服务基于 service50 launch args，只允许这些差异：设备 PPU0–7、端口 8031、
   新日志/manifest、加入 `--enforce-eager`，以及下列环境变量：

   ```text
   VLLM_FL_QSA_OVERLAP_TELEMETRY=1
   VLLM_FL_QSA_OVERLAP_RANK=0
   VLLM_FL_QSA_OVERLAP_MIN_ROWS=4096
   VLLM_FL_QSA_OVERLAP_ARM_FILE=<unique-output>/arm.json
   VLLM_FL_QSA_OVERLAP_OUTPUT_DIR=<unique-output>
   ```

   QSA bound 8448、native `mm/mm_out`、MoE M64/BM16、TP8、maxseq64、bt4096 及其他
   selected environment 必须与 service50 相同。显式记录 graph 差异为诊断变量。
4. readiness 后先做未 armed smoke。Prefill：在容器内执行 run 脚本
   `prefill 8031 <unique-prefill-dir>`，其 C1/N1/P4096/D1 只有一个 request segment，
   采第一层一次。
5. Mixed：新建另一个 unique output dir，服务环境的 ARM/OUTPUT 路径必须指向该目录，
   或重启同配置诊断服务；执行 `mixed 8031 <unique-mixed-dir>`。单个 client invocation
   同时提交 C2/N2/P4096/D128：第一个 request decode 时第二个 prompt 被接纳。只有
   telemetry 实测 `request_runs>=2` 才标为 Mixed；若 scheduler 未形成重叠，arm 保留且
   本轮判 `incomplete`，不能把纯 Prefill 当 Mixed。
6. 分别冻结 result/client/manifest/log 的 SHA，再运行 analyzer。采样只要求 rank0；
   TP0–7 仍须全部健康，请求必须全成功。该 rank coverage 足够回答选集语义，不能支持
   rank 间性能或不均衡结论。
7. 精确停止诊断服务；按 patch manifest 回退；核对 qsa.py 恢复原 SHA、helper 已删除，
   PPU0–7 释放，service50 health/canonical 不变。

注意：一个单请求不可能产生 `new>0,cached>0` 的 Mixed scheduler step，所以不能用
C1/N1 冒充 Mixed。这里的“最小”是 Prefill 一请求、Mixed 一次两请求 client invocation。

## 正确性、graph 与开销边界

- helper 只读最终 `out`，sort 在新 tensor 上，不修改 TopK、expand 或 sparse output。
- telemetry-off 的 patched source 必须通过原 full-graph capture + 至少两次 replay；这
  证明禁用分支没有破坏生产 graph。
- telemetry-on 明确 fail closed 于 capture，诊断服务必须 `--enforce-eager`。其结果只
  证明真实 workload 的 selected-set 语义，不证明 telemetry 或未来 union kernel graph-safe。
- 采样前后同一固定请求的 token IDs/文本/结束状态必须相同；任何请求失败、hang、NaN、
  source SHA 漂移或 retained service 异常立即停止回退。
- device sort、一次 `.item()` phase gate 和 counter `.cpu()` 都会同步 rank0，导致其他 TP
  rank collective 等待。因此 client latency、吞吐、trace duration 全部作废，不得进入任何
  performance comparison。

## 停止条件

- 任一阶段无新、非空、可解析 JSON，phase/request-runs 不符，或 coverage 为 0：
  `incomplete`，修复采集，不做优化推断。
- 所有 R 中没有一个同时在 Prefill 与 Mixed 达到 `rho>=0.12`：`no_go`，停止 QSA
  union/mask 方向。
- 某 R 两阶段均过 12%：仅晋级独立算子 microbenchmark；先计入 union 建表、mask、额外
  索引和 layout 成本，并要求完整 transaction `>=8%` 后才可讨论服务集成。
- coverage 很低时即使 rho 高也不得推广；优先解释 request tail/segment 结构并追加同契约
  样本，而不是选择性删除尾部。
