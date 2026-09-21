# 20260919-qwen38-flash-next-ppu-e2e：Qwen3.8-Flash-Next / PPU 端到端优化

## 1. 摘要

当前进度以 [模型优化总览](../../../models/Qwen3.8-Flash-Next/ppu/optimize/README.md) 和
[结构化状态](../../../models/Qwen3.8-Flash-Next/ppu/optimize/state.yml) 为准。
以下摘要是 P1K 早期快照，不表示当前仍处于环境准备；其中截断只是输出健康观察，不是独立精度失败条件。
正式精度阻塞及后续准入以模型记录中的规则审查为准。

- 执行规则：SOP `0.38` / 2026-09-14
- 验收范围：`diagnostic`（用户未指定绝对 SLO 或相对改善门槛）
- 精度/性能状态：`failed_baseline_sanity_output_health` / `p1k_screening`
- 状态：`running`
- 结论：P1K Prefill、Decode、Mixed 无干扰基线已完成。`max-num-seqs 32→64` 单变量 screening 将 Mixed 输出吞吐提高 72.51%、P99 TTFT 降低 88.14%，但 P99 TPOT 回退 14.97%、P99 ITL 回退 561.37%；保留为 Pareto 候选，不在缺少 SLO 与独立实例 A/B/R 时宣布最终选型。标准 30000-token 生成契约的 baseline-sanity 有1个样本在上限截断，不签发精度 gate。
- 证据等级：`observation`
- 模型/平台产物：`models/Qwen3.8-Flash-Next/ppu/{baseline,optimize,acceptance}/`

## 2. 任务与验收契约

- 模型：`/mnt/cpfs/models/Qwen3.8-Flash-Next`
- 平台/Host：T-Head PPU / `PPU-01`（远端 hostname `bm-aliyun-wlcb-zonea3-c-810e-96g-10-1`）
- 远程工作根目录：`/mnt/nfs/users/jinghao/qwen3.8-flash`
- 本案例远程子目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e`
- 源适配容器：`qwen3.8-flash`
- 新优化容器：`qwen3.8-flash-opt-20260919`（PPU 0–7 / 端口 8020）与 `qwen3.8-flash-opt-candidate-20260919`（PPU 8–15 / 端口 8030）
- 适配快照：`qwen3.8-flash-adapted:20260919-e2e-source` / `sha256:d87b7b26da3623b18863d47fa623135d0dfc3ba3288293be18aa6f928cb9bbe6`
- 镜像谱系/挂载：`verified` / `passed`
- 主目标：综合改善固定四场景的输出 token 吞吐与 TPOT/ITL，同时降低或不显著恶化 TTFT。
- 守护指标：正确性、失败率、尾延迟、显存、稳定性、Prefill/Decode 交叉阶段不显著回退。
- 通过门槛：用户未预冻结；本案例只报告客观改善/回退/未证实，不声称“达标”。
- 修改边界：可修改目标环境私有副本中的 `vllm-plugin-FL`、`FlagGems-vllm`、`FlagGems`；vLLM、权重、tokenizer、基础镜像和共享配置默认只读。

## 3. Workload

- 正式顺序：`p1024-d1024-c64-n128` → `p4096-d1024-c64-n128` → `p16384-d1024-c64-n128` → `p32768-d1024-c64-n128`
- 当前目标：`p1024-d1024-c64-n128`，`finite_batch`
- 当前阶段：P1K baseline、`max-num-seqs=48/64` 与 `64/2048` 配置 screening 完成；2048 未达 ITL 恢复门槛，进入 bounded Mixed profiling。
- 性能启动硬要求：显式 `--no-enable-prefix-caching`，graph 模式启动、capture 并至少 replay 两次。

## 4. 预检证据

- inventory 将“平头哥01”解析为 `PPU-01`，连通性检查通过。
- 工作根目录解析为原路径，owner/group `root:root`，mode `777`，所在 NFS 约 9.3T 可用。
- 模型目录解析为原路径，owner/group `root:root`，mode `755`，可见 131 分片命名的 safetensors 权重。
- 目标机为 PPU-ZW810E；预检时设备显存已有大量驻留，须在创建优化服务前解析占用者与资源隔离。
- 精确源容器 `qwen3.8-flash` 处于运行状态；同机还有名为 `qwen3.8-flash-test` 的运行容器，不视为本任务优化容器。

## 5. 当前门禁与下一步

1. 固定 10 题、并发 8 的 `baseline-sanity` 在 2048、8192 和标准 30000-token 上限下分别有 3、1、1 个截断；最后一轮 strict-match `0.9`，但 `timeouts=1`，因此证据保留为失败的输出健康基线，不冒充 gate。
2. 无干扰 exact P1K Mixed 基线完成：三轮输出吞吐 `331.40/330.73/330.72 tok/s`，中位数 `330.73 tok/s`；P99 TTFT 中位数 `104.90s`，显示 C64 在 `max-num-seqs=32` 下的显著 admission 排队。
3. `max-num-seqs=64` 三轮正式测量的中位数为输出吞吐 `570.53 tok/s`、P99 TTFT `12.44s`、P99 E2E `124.52s`、P99 TPOT `110.91ms`、P99 ITL `628.03ms`；全部 128/128 成功，warmup spread `0.137%`。graph replay canonical 与 32 一致。
4. `max-num-seqs=48` 三轮正式测量的中位数为输出吞吐 `417.28 tok/s`、P99 TTFT `110.49s`、P99 E2E `216.91s`、P99 TPOT `104.65ms`、P99 ITL `107.28ms`；相对 32 吞吐提高 26.17%，但五项延迟守护均回退。全部 128/128 成功，warmup spread `0.594%`，canonical 一致。
5. 规划复盘 `plan-001-20260919-p1k-maxseq` 将下一实验冻结为 `max-num-seqs=64 + max-num-batched-tokens=2048`，目标是至少恢复 30% 的 64 配置 P99 ITL 回退，同时保留至少 90% 吞吐且 P99 E2E 继续优于 32。任何保留配置仍须独立实例 A/B/R。
6. `64/2048` 正式中位数为吞吐 `550.67 tok/s`、P99 TTFT `16.36s`、P99 E2E `132.62s`、P99 TPOT `114.21ms`、P99 ITL `507.11ms`。相对 `64/4096`，ITL 仅改善 19.25%，未达 30% 目标，且其他主/守护指标均回退，因此配置回退。`plan-002-20260919-p1k-profile` 冻结下一步为恢复 `64/4096` 并采集 bounded Mixed trace。

## 6. 已收敛候选

- `framework`：最高优先级改为 `max-num-seqs=64/max-num-batched-tokens=4096` 的 bounded Mixed profiling，定位 ITL 回退来自调度间隙、Prefill/Decode 干扰、通信、dispatch、graph 还是 kernel。Qwen3.8 标准与 common slot-mapping 重复计算消除排在 trace 命中证明之后。
- `operator/improve`：QSA compress+norm+MRoPE+store 融合、HC 三个专用 kernel、QSA K/V 双写融合。
- `operator/replace`：QSA paged-dot；需保护 top-k 排序与最终 sparse-attention 数值。
- `operator/improve`：PPU small-M FusedMoE 配置、QSA group-size=3 tile、packed GDN decode tile；先由 profiling 决定优先级。
