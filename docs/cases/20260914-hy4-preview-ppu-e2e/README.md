# 20260914-hy4-preview-ppu-e2e：Hy4-preview / PPU 端到端优化

## 1. 摘要

- 执行规则：SOP `0.29` / 2026-09-11
- 验收范围：`diagnostic`
- 正确性/性能状态：`passed (minimal regression)` / `failed (first candidate)`
- 状态：`running`
- 结论：独立优化容器、P4K scout 基线和候选正确性护栏已建立。`max_num_batched_tokens=4096` 仅带来 `+0.195%` 输出吞吐，未达 5% 门槛且 P99 ITL 约翻倍，已拒绝并回退到 2048。
- 模型/平台产物：`models/Hy4-preview/ppu/{baseline,optimize,acceptance}/`

## 2. 任务与验收契约

- 模型：`Hy4-preview`，权重 `/mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/`
- 平台/Host：16× PPU-ZW810E / `PPU-07`
- 源适配容器：`hy4`，容器 ID `550e93f0ba4c...`，镜像 ID `sha256:f222f9a173b...`
- 引擎：vLLM `0.24.0+empty`，TP16，W8A8 linear/MoE，BF16 activation
- 当前源码：vLLM `ee0da84a`；Plugin `2fa5f181` + `thead.yaml` 已有修改；FlagGems `bca444b8`
- 当前服务：`hy4` / `127.0.0.1:8010`，100K context，`max-num-batched-tokens=2048`，FULL_DECODE_ONLY graph，prefix cache disabled
- 用户在适配阶段接受的精度结论：GPQA strict `180/198 = 90.91% >= 87%`；doc_id 81 的一个 `<TIMEOUT>`、runner exit 1 和缺少原生 passing receipt 继续作为限制保留。
- 当前 P4K targeted 主指标：output throughput；守护指标为 P99 TTFT、P99 TPOT、total-token throughput、失败和资源状态。搜索阶段最小有意义改善 5%，守护指标最大相对回退 10%。

## 3. 已导入诊断证据

适配仓库的五工况性能任务在源适配容器中运行后由用户终止，不能作为本项目正式基线：

- P1K/D1K/C64/N128 三轮成功，output throughput 摘要约 `37.40 tok/s`。
- P4K/D1K/C64/N128 三轮成功，output throughput 摘要约 `10.45 tok/s`。
- P16K、P32K、P64K/D1K/C64 均达到单轮 21,600 秒 timeout；最后一项仅首轮完整等待，runner exit 143。
- 服务 KV 容量为 401,791 tokens；P16K/P32K/P64K 的 C64 prompt 总量分别约 1.05M/2.10M/4.19M tokens。日志没有 preemption/recompute 记录，调度器主要通过限制驻留和排队避免 KV 溢出。
- `max-num-batched-tokens=2048` 下长 Prefill 推进缓慢，部分窗口约每 40–50 秒只新增两个驻留请求；这是首个框架工作点实验的直接证据。
- 服务日志明确记录 T-Head native extension bundle 不完整，vendor implementations 被禁用；dispatch 回退到 FlagGems/reference。该命中缺口必须在优化容器中复现并做单变量 A/B。

原始证据：

- `/mnt/nfs/users/jinghao/hy4-preview/04-runs/perf-full-default5-plugin2fa5f18-indexoff-20260911/`
- `/mnt/nfs/users/jinghao/hy4-preview/04-runs/service-plugin-2fa5f18-fgbca-indexoff-perf-noprefix-20260911/service.log`

## 4. 已完成门禁与实验

- 远程任务目录：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/`
- 源适配状态镜像：`hy4-preview-adapted:20260914-e2e-source`，优化容器：`hy4-opt-20260914`。
- `image_lineage=verified`、`mount_parity=passed`、`runtime_parity=passed`；唯一目录挂载仍为 `/mnt:/mnt` RW/rprivate。
- baseline 固定 chat smoke+C8 9/9 通过。P4096/D32/C8/N8 scout 基线两次 measured 输出吞吐为 0.331100/0.331106 tok/s，轮间稳定。
- 4096 候选固定 chat smoke+C8 9/9 通过。三方性能比较回执 `failed`：输出吞吐改善 `+0.195%`，未达 `+5%`。
- 候选已回退；revert 稳定身份与 baseline 匹配，输出吞吐中位数 0.334935 tok/s。

## 5. 下一步

1. 使用最小 P4K profiling 采集区分 prefill 算子、dispatch、通信与 host 等待，profiler-on 数据不用于性能收益声明。
2. 若 trace 确认具体算子，再对 T-Head bundle 中对应的单 op 做 vendor-first 数值、graph、命中和端到端 A/B；provision 与 dispatch 仍分开留证。
3. 只有 profiling 证明 prefill batch 组织仍是主瓶颈时，才评估 8192；4096 的负结果不支持盲目扩大参数扫描。

用户于 2026-09-14 指定当前阶段不建立 P16K/P32K/P64K 基线，先基于 P4K 优化。迭代场景冻结为 `P4096/D256/C64/N64`，保留候选后用 `P4096/D1024/C64/N128` 做 checkpoint；结论不外推到其他长度。
