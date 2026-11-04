# accdiag-001：当前 graph 服务稳定生成 NUL 字符

- 状态：`resolved_at_configuration_bundle_boundary`
- 触发模式：`baseline-sanity` 前置 smoke
- 影响实验：`env-001-source-facts-and-replication` 之后、正式性能基线之前
- 分类：`launch configuration drift`（配置组合边界已确认；单个漂移变量未完全隔离）
- 是否阻塞：否。正确的无 prefix-cache graph 基线服务及 baseline-sanity 已通过。

## 现象与最小复现

当前 PPU-07 独立优化服务实例 `bd37abcb...-337-268927884` 已完成 51/51 个 `FULL_DECODE_ONLY` capture，health 与模型身份正常。`/v1/completions` 的两次 4-token 请求、`/v1/chat/completions` 的两次 64-token 请求，以及 2026-09-15 已知正确的“北京/巴黎”两条 prompt 均稳定生成与 token 数相同的 NUL 字符并以 `length` 结束。

失败证据：

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/baseline-service-runtime-20260921-01/`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/baseline-service-chat-replay-20260921-01/`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-001-known-good-prompts-current-graph/`

## 最后可信状态与差异

最后可信的已归档 graph smoke 位于 PPU-13 的 `04-runs/graph-service-run2/`：旧镜像 `sha256:f222...`、capture sizes 1/2/4/8/16/32 下，北京/巴黎 2/2 正常。后续适配交付明确记录最终启动必须使用 `FLAGTREE_AABS=0`，以规避 PPU prefill index-topk 的 FlagTree 自动 block-size 问题。

当前 PPU-07 的 `start-model.sh` SHA-256 为 `571593ae...`，已漂移为 `FLAGTREE_AABS=1`、`max-model-len=100000`、禁用 prefix cache、默认 51 个 capture size；上游已验证最终脚本 SHA-256 为 `e65ba3a1...`。当前代码 revision 与优化容器镜像保持不变，尚无性能补丁。

## 二分结果

1. 在漂移配置上只将 `FLAGTREE_AABS=1→0`，服务在 `determine_available_memory/profile_run` 以 HGGC illegal-memory 失败；因此 AABS 单变量不足以恢复。
2. 保持漂移配置并使用 `AABS=1 + eager`，同样在 profile_run 失败，说明问题不只是 CUDAGraph replay。
3. 当前镜像切回上游已验证交付组合：`AABS=0`、`max_model_len=65536`、`max_num_seqs=32`、prefix cache 开启、capture sizes `1,2,4,8,16,32`，服务完成 6/6 capture，北京/巴黎 2/2 正确。
4. 在正确组合上只关闭 prefix cache，服务再次完成 6/6 capture，北京/巴黎 2/2 正确且请求后 health 正常。这一实例满足本项目性能基线的缓存语义。

配置组合边界已经闭合，但没有把 `100000` 上下文、默认 51 个 capture size、未显式 `max_num_seqs` 和 AABS 漂移进一步逐项拆完；不把其中任一项单独宣称为根因。

## 结论边界

当前镜像与源码并非普遍无法生成文本；故障由未验证的漂移启动组合触发。恢复后的无 prefix-cache graph 服务通过两次 replay，随后固定前十题 GPQA greedy/C8 得到 strict-match `10/10=1.0`、0 timeout。doc_id 7 和 8 各达到 30000-token 上限，作为输出健康观察保留；依项目规则不单独使精度失败或阻止性能优化。

关键证据：

- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-001-aabs0-graph-start-failure/`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-001-aabs1-eager-start-failure/`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-001-delivered-config-replay/`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/accdiag-001-no-prefix-replay/`
- `/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/baseline-sanity/`
