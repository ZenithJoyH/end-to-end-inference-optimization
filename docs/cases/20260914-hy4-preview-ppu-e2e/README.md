# 20260914-hy4-preview-ppu-e2e：Hy4-preview / PPU 端到端优化

## 1. 摘要

- 执行规则：SOP `0.29` / 2026-09-11
- 验收范围：`diagnostic`
- 精度/性能状态：`incomplete` / `incomplete`
- 状态：`running`
- 结论：已完成适配事实导入和 PPU-07 现场只读预检；独立优化容器、正确性护栏与新基线尚未建立。
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

## 4. 门禁与下一步

1. 确认当前优化任务可使用的远程工作根，在其下创建唯一 case 子目录。
2. 只读保存源容器 inspect、源码状态与实际导入路径；适配改动位于 `/workspace` writable layer，因此先形成并核验不可变适配状态镜像。
3. 创建新优化容器，保持 `/mnt:/mnt`、IPC、网络、设备、ulimit 等目录映射和运行条件一致；完成机器可读 mount diff。
4. 在优化容器上执行 baseline-sanity；随后由性能评测 Skill 的 `baseline` 模式建立新基线。
5. 首个低风险框架实验：保持其余条件不变，扫描 `max-num-batched-tokens` 2048→4096，证据支持时再到 8192；观察 Prefill 吞吐、TTFT、队列、KV 和输出吞吐。
6. 第二候选：从已存在且 digest 匹配 provenance 的本地镜像提取完整 T-Head bundle；bundle provision 与单个 op 的 vendor-first dispatch 分开验证。任何收益均回到无 profiler 端到端 A/B。

用户于 2026-09-14 指定当前阶段不建立 P16K/P32K/P64K 基线，先基于 P4K 优化。迭代场景冻结为 `P4096/D256/C64/N64`，保留候选后用 `P4096/D1024/C64/N128` 做 checkpoint；结论不外推到其他长度。
