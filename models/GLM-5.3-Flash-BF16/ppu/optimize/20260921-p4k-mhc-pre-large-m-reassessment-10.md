# 20260921-p4k-mhc-pre-large-m-reassessment-10 P4K mHC pre 大 M 复评

- 状态：`rejected`
- 分类：`operator/replace`
- 正式目标场景：`P4096/D1024/C64/N128`
- 目标阶段：Prefill、Mixed；Decode 为守护项

## 优化方向与瓶颈依据

P4K trace 中 `mhc_pre_fused_kernel_hc_mult_4` 占 Prefill 4.691%、Mixed
5.046%，`mhc_post` 另占 3.389%/3.570%。当前 `mhc_pre_with_norm` 被 thead
FlagOS blacklist 固定在 reference 路径。

此前 P1K Decode 实验中，FlagGems mHC pre 在 `M=1/8/16/24/32/1024` 上中位
加速 5.528×且数值/graph 全通过，但 P1K 端到端输出吞吐回退 0.587%，因此已经
恢复 blacklist。该结论只覆盖 P1K Decode，不能证明 P4K 大 M 也没有收益；同时它
要求本点不能仅凭算子加速保留候选。

## 优化内容与适用边界

第一步只从现有 16-rank P4K trace 提取 mHC 的真实 token shape 和 provider；随后在
服务停止状态下直接比较 reference 与 FlagGems，覆盖 Prefill/Mixed 大 M、数值和
graph capture/两次 replay。只有大 M 算子至少 2×，且按 5.046% 热点份额估算仍有
端到端意义时，才临时从 thead blacklist 移除 `mhc_pre_with_norm`，做
`P4096/D128/C64/N128` 短 A/B/R。

## 晋级与停止条件

- 精确大 M eager/graph 数值均满足既有 `rtol=atol=0.02`；
- graph capture 成功并 replay 至少两次；
- 大 M FlagGems/reference 中位加速至少 2×；
- 短服务 A/B/R 输出吞吐至少 +1%，P99 TTFT/TPOT 不回退超过 3%，revert 漂移不超过 3%；
- 任一条件失败即恢复/保持 blacklist，不进入完整 P4K。

## Exact shape 与算子结果

rank0 trace 确认：Prefill `M=4096`（89 次），Mixed 主批 `M=16384`
（1335 次），Mixed 尾批 `M=12769`（89 次）。三组 reference/FlagGems
成对微基准均完成 3 轮 eager 与 graph 计时：

| M | reference graph | FlagGems graph | 加速 |
|---:|---:|---:|---:|
| 4096 | 2.7811 ms | 0.7793 ms | 3.5688× |
| 12769 | 7.5696 ms | 2.2563 ms | 3.3548× |
| 16384 | 11.2661 ms | 2.9589 ms | 3.8076× |

eager 加速分别为 3.5627×、3.3382×、3.8191×。三组的三个输出均通过
`rtol=atol=0.02`，reference/FlagGems 均完成 graph capture 和两次 replay；
FlagGems DB 测前测后 SHA-256 均为
`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`。
算子门槛通过，随后完成 P4096/D128 fresh-service A/B/R。

## 服务级性能效果

每个角色均为 6 轮预热 + 3 轮 measured，16/16 rank 分别确认 baseline/revert
命中 `reference.torch`、candidate 命中 `default.flagos`：

| 角色 | 输出吞吐中位数 | measured 离散 | P99 TTFT | P99 TPOT |
|---|---:|---:|---:|---:|
| baseline | 281.7474 tok/s | 0.5292% | 24397.27 ms | 218.709 ms |
| candidate | 282.0116 tok/s | 0.1399% | 24358.25 ms | 218.926 ms |
| revert | 281.8327 tok/s | 0.0930% | 24404.61 ms | 219.017 ms |

candidate 输出吞吐仅 +0.0938%，低于 +1% 晋级门槛；TTFT -0.1599%，TPOT
+0.0992%，均在守护范围。revert 相对 baseline 为 +0.0303%，可比性成立；
1152/1152 measured 请求成功。

## 决定、风险与回退

拒绝 candidate，不晋级完整 P4096/D1024。该结果再次证明 isolated kernel
加速不能直接代表端到端收益：mHC pre 的 3.35×–3.81× graph 加速在当前 P4K
执行组织中只转化为 0.094% 吞吐差异。YAML 已逐字节恢复，SHA-256 为
`10e3a2bf36dbf38163e963b51552736f3d7e278b448a012a0b8883bcf3d6d88f`；
`mhc_pre_with_norm` 仍在 blacklist，8011 关闭，16 卡无模型进程。

## 外部证据

- 根目录：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p4096-d1024-c64-n128/operators/mhc-pre-large-m-10/`
- shape 分析 SHA-256：`7fa0f45fb6a8f7922ce06ae9d579a0516b63f803bddc79e408638a300d836727`
- M4096 结果 SHA-256：`0061c4447fe4daa0504efa7dbfba1dad223f9a0855862b8d2296a37583dcf217`
- M12769 结果 SHA-256：`e0bb1f6b64b66c0594203530f76b1a04ca53491faa7339193a006a0fc3ab9da9`
- M16384 结果 SHA-256：`3abc6676bd5b319ac3fa7be399e5c92cc43cfa4e5fd117b3ec09428e6d872a0b`
- A/B/R 汇总 SHA-256：`656d89b4e87c4231f073e61b08260e94bde59dcd8243366caf36e373dad04b4d`
