# 20260914-hy4-preview-ppu-e2e：Hy4-preview / PPU 端到端优化

## 1. 摘要

- 执行规则：SOP `0.29` / 2026-09-11
- 验收范围：`performance_only targeted milestone`
- 正确性/性能状态：`passed (operator/graph)` / `targeted A/B/revert passed; parent P4K pending`
- 状态：`candidate_retained_service_stopped`
- 结论：组合重采样证明 `mm_out` 路由和 Indexer metadata 缓存均命中；残留算子热点收敛到 SQ2048 sparse MLA。新增 BK32 特化后，两个 profiler-off P4K 缩减场景的 output throughput 分别提升 `1.218%` 与 `1.291%`，独立回退复现基线且所有守护项通过。结论不外推到 `P4096/D1024/C64/N64`。
- 模型/平台产物：`models/Hy4-preview/ppu/{baseline,optimize,acceptance}/`

## 2. 任务与验收契约

- 模型：`Hy4-preview`，权重 `/mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/`
- 平台/Host：16× PPU-ZW810E / `PPU-07`
- 源适配容器：`hy4`，容器 ID `550e93f0ba4c...`，镜像 ID `sha256:f222f9a173b...`
- 引擎：vLLM `0.24.0+empty`，TP16，W8A8 linear/MoE，BF16 activation
- 当前源码：vLLM `ee0da84a`；Plugin `38f350b1`（已推送 `support-hy4-preview`）；FlagGems `5c2b9a16`（已推送 `support-hy4-preview`）
- 当前服务：`hy4-opt-20260914` 中的测试服务已停止，8010 未监听；源适配容器 `hy4` 未修改。FlagGems 工作区保留通过验证的 SQ2048 候选源码，但未启动服务。
- 用户在适配阶段接受的精度结论：GPQA strict `180/198 = 90.91% >= 87%`；doc_id 81 的一个 `<TIMEOUT>`、runner exit 1 和缺少原生 passing receipt 继续作为限制保留。
- 当前 P4K targeted 主指标：output throughput；SQ2048 单变量契约的最小改善为 0.5%，mean TTFT/TPOT 与 total-token throughput 为守护项，baseline/revert 最大漂移 10%。

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
- profiling 将约 143 秒的代表性 rank inclusive 时间和约 86,000 次逐行 Top-K 相关调用收敛到 `hyv4_bf16_sparse_attn_indexer` 外层行循环；block128 单设备探针在两段 P4K chunk 上分别达到 41.76x/29.17x，4096 行选择集合完全一致。
- block128 候选在冻结 P4096/D32/C8/N8 上 measured 两轮输出吞吐中位数 6.876431 tok/s；原基线 0.331103 tok/s，回退 0.333439 tok/s。所有轮次均完成 8/8 请求、无失败。
- 最终保留服务实例 `848575b2b0a8-pid1223838-start210872589`，Plugin 源码 SHA256 `e0f45312...3650e`；smoke+C8 9/9 通过，graph capture 完成并在 capture 后成功生成 521 个 completion token。
- 自动比较结果为 `incomplete`，唯一原因是沿用了上一项 2048→4096 契约的变量路径；旧 run-record 未被事后改写。因此保留结论只适用于 P4K scout milestone，不作为正式验收。

## 5. 暂停点与恢复入口

1. `mm_out` 已加入 `vllm_fl/dispatch/config/thead.yaml` 的 `flagos_blacklist`；实际策略解析得到 `use_flaggems_op("mm_out")=False`。`FLAGGEMS_ENABLE_OPLIST_PATH` 只指定 enabled-op 记录输出位置，不覆盖黑名单；必须在下一次服务启动后验证真实 dispatch 命中。
2. FlagGems `flashmla_sparse.py` 已加入 `BK64/BH4/4-warps/2-stages` autotune 候选。`SQ8/HQ4/DQK576/SKV8192/TOPK2048` 核心 kernel 从 `194.33 us` 降到 `176.85 us`（`1.099x`）；SQ1/8/64/256/2048 sweep 均为正收益。small-head pytest 3/3 通过，目标 shape graph capture + 3 replay 通过。
3. rank0 Indexer 已按互斥 CPU 区间拆分：Mixed/Decode 的 `cudaMemcpyAsync` host wait 分别占 Indexer wall time 的 `43.34%/55.13%`，而实际 device memcpy 仅 `6.650/14.828 ms`。典型 `int32[2]` DtoH 只传 8 bytes、耗时 0.6 us，但 host API 阻塞 50.412 ms，根因方向为 `.tolist()` 引发的 stream drain。
4. T-Head vendor fused 层已新增带严格门禁的 sparse MLA Split-K：仅覆盖 `SQ<=64/HQ4/DQK576/TOPK2048/DV512/sink/topk_length`，其他 shape/platform fallback。零长度、全无效 index、无限 sink、SQ128 fallback 及 graph replay 均通过；FlagGems 聚焦测试 5/5 通过。SQ128 实验版本曾退化 7.9%，已由最终门禁排除。
5. Indexer 已把同一个 per-execution chunk 的三份 host metadata 缓存在 chunk 上，并用 `bisect_right` 在 host 侧派生 sequence id。21 层隔离复现的 `cudaMemcpyAsync` 为 `105 -> 3`（`-97.14%`），host elapsed 为 `131.14 -> 2.48 ms`；Plugin HY4 聚焦测试 5/5 通过。
6. 恢复时先运行 profiler-off `P4096/D1024/C64/N64` 同配置 A/B，验证组合候选的服务级收益与 TTFT/TPOT/ITL 守护项；随后重新 profiling，按同一互斥口径拆分 Indexer 本体与 copy/sync。本轮不开展 P16K/P32K/P64K。

用户指定当前阶段不建立 P16K/P32K/P64K 基线，先基于 P4K 优化；当前用户目标为 `P4096/D1024/C64/N64`，本轮 profiling 使用的映射 milestone 为 `P4096/D128/C8/N8`。缩减结果和单算子结果均不外推为父场景的正式性能结论。

本轮远端证据：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/{sparse-mla-*,indexer-*}`；可复现脚本、候选源码快照和测试快照位于同一案例的 `commands/`。

## 6. 源码提交与推送

- Plugin 提交 `38f350b13fc15f08eb4641e1d6d1980ba3fc16aa`：`perf(hy4): reduce indexer host synchronization`；GitHub `support-hy4-preview` 分支头已反查匹配。
- FlagGems 提交 `5c2b9a1618c36651f96108d56f076361965f2d53`：`perf(thead): add split-k sparse MLA specialization`；GitHub `support-hy4-preview` 分支头已反查匹配，原远端分支 `sparse-mla-opt-w8a8-moe-fix` 已删除。
- 目标机缺少 GitHub HTTPS 交互式凭据，按用户预先授权通过完整 Git bundle 把原提交复制到本机推送；两边提交 SHA 保持不变。远端补丁备份 SHA256 分别为 `f78dee1a...fcb` 与 `92367d06...61e`。

## 7. 组合重采样与 SQ2048 sparse MLA 特化

用户授权停止当前服务并继续 profiling/优化后，先停止旧 8010 服务，再以同一个优化容器启动专用 profiler 服务。`P4096/D128/C8/N8` 采集覆盖 16/16 rank，trace 完整；采集完成后 profiler 服务已停止。

运行时命中与热点迁移如下：

- `mm_kernel_general` 从旧 profile 的 111,633 次、Decode 35.456 秒（33.40%）降为 0，证明 T-Head `mm_out` 黑名单命中。
- Indexer Prefill/Mixed/Decode 的 `cudaMemcpyAsync` host wait 从 652.255/4418.831/7825.059 ms 降为 6.930/4.253/25.130 ms（下降 98.9%–99.9%）；Indexer 总时长从 1414.041/10195.819/14193.560 ms 降为 743.904/5752.353/6339.257 ms。复制/同步已不再主导，剩余主要是 Indexer 本体。
- Split-K Decode stage1/stage2 各命中 28,885 次；剩余通用 `triton_flash_mla_sparse_fwd` 为 1,835 次、11.768 秒（20.03%）。关联 launch grid 与源码公式确认其 shape 为 `SQ2048/HQ4/DQK576/TOPK2048/DV512`。
- 新 profile 的 Prefill 前两项为通用 sparse MLA 22.64%、ring all-reduce 22.28%；Mixed 为 ring 23.30%、通用 sparse MLA 21.91%；Decode 为通用 sparse MLA 20.03%、linear 14.27%、fused MoE 13.53%。device activity 可跨 stream 重叠，只用于归因。

基于该证据，在 T-Head wrapper 加入精确 shape 门禁的 `BK32/BH4/4-warps/1-stage` 特化，其余 shape 保持原 fallback：

- 单算子当前配置中位数 6381.840 us，候选 5984.712 us，`1.066x`；`all_512/all_1024/ramp_1_2048/all_2048` 分布分别为 `1.112x/1.081x/1.121x/1.069x`。
- 最大绝对误差 `1.22e-4`；SQ1024 fallback、CUDA Graph capture 与两次 replay 通过。
- profiler-off、1 次预热 + 3 次 measured、独立服务重启的 baseline/candidate/revert 比较为 `passed`，唯一变量为 `/flaggems_sha256`，issues 为空。

| targeted 场景 | output throughput baseline | candidate | 改善 | mean TTFT 改善 | mean TPOT 改善 |
|---|---:|---:|---:|---:|---:|
| P4096/D32/C8/N8 | 11.7376 tok/s | 11.8805 tok/s | +1.218% | +1.524% | +0.896% |
| P4096/D128/C8/N8 | 35.3539 tok/s | 35.8103 tok/s | +1.291% | +1.844% | +0.842% |

独立回退输出吞吐分别为 11.7064/35.3557 tok/s，均复现基线且在冻结漂移范围内。该结果只支持两个缩减 milestone，父场景 `P4096/D1024/C64/N64` 尚未完成。

验证完成后，停止脚本最初暴露出 PID namespace 问题：`api.pid` 是容器 PID，旧脚本却在宿主机发送信号。修正版在 `hy4-opt-20260914` 容器内精确停止并在宿主机复核；最终优化容器仅剩 init/shell，8010 端口释放，源容器 `hy4` 无 vLLM 进程且未受影响。通过验证的候选源码 SHA256 `86d968c...d7f60` 已恢复到 FlagGems 工作区但未提交、未推送，也未重新启动服务。

证据入口：

- profile：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/p4k-d128-c8-n8-post-commit-reprofile-20260915-03/`
- 正式 targeted 比较：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/sq2048-bk32-targeted-comparison-20260915.json`
- 候选补丁：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/commands/flaggems-thead-sparse-mla-sq2048-bk32-20260915.patch`

## 8. Sparse MLA 后续证伪与 Indexer row-range Top-K

- SQ2048 sparse MLA 继续扫描 `BK16`、`BH1/BH2` 及不同 warp/stage，均慢于已保留的 BK32/BH4。2/4 路 Split-K 完整调用最好为 `0.901x`，ramp 长度仅 `0.596x`，并增加 32.125–64.25 MiB workspace；两项均回退，FlagGems 仍保留上一轮 BK32 候选。
- Indexer blocked prefill 改为把每行有效 start/end 直接交给已有 row-wise Top-K provider，删除 dense causal mask 和通用 `torch.topk`。32/64/128 行、2K/4K key 宽度微基准为 `1.093x–1.543x`；selected score 完全等价，4K 下仅存在同分 token 的合法 tie 差异。
- Plugin 聚焦测试 `6/6`、源码编译和 diff check 通过；新 `hy_v4.py` SHA256 为 `940e04f...501dc`。该候选尚无服务级性能结论，等待用户按 `max-num-batched-tokens=2048` 复测。
- 2048 不是全局最优证明，但 4096 的既有单变量实验只有 `+0.195%` throughput，P99 ITL 约翻倍且 KV 容量下降，因此当前继续用 2048 控制代码变量；后续可独立扫描 1024/1536/2048/3072。

## 9. 最新 P4K checkpoint 与第二轮优化

- 最新用户 CSV：`hy4_4096in_1024out_c64_n128_20260916_082820.csv`，SHA256 `bc89271b...5fdb0`。Run2/Run3 稳态 output throughput `224.03 tok/s`，相对 `20260915_171828` 提升 `3.57%`；mean TTFT/TPOT 分别改善约 `5.30%/3.14%`。Run1 为 `5350.86 s`，保留为未解决异常；此结果是 checkpoint，不是最新组合的 A/B/revert。
- `P4096/D128/C8/N8` 再次 reprofile，16/16 rank trace 完整，采集后服务及 worker 全部停止。Plugin builder shim 在 metadata 构造期利用 CPU 输入预置 host row ranges，使 Indexer 内 pageable DtoH 归零。Mixed memcpy API wait `1774.774 -> 1.372 ms`，Decode `310.392 -> 4.120 ms`；Mixed Indexer 总 wall time `5283.668 -> 3789.854 ms`。profiler-on output throughput `35.45 -> 37.14 tok/s` 仅作为诊断。
- 新 trace 中 sparse MLA 仍为 Prefill/Mixed/Decode 第一设备热点，单次耗时约 `3.37/3.43/6.15 ms`。BK32 的中间 SQ sweep 覆盖 128/256/512/1024/1536/2048，两类长度分布全部正收益，算子提升 `1.030x–1.185x`，最大绝对误差 `1.22e-4`。
- FlagGems 门禁扩展为 `128<=SQ<=2048`，SQ<=64 仍走 Split-K，65–127 fallback；graph capture 后 replay 两次并在输入变化后再次 replay，完整 small-head pytest `8/8` 通过。新范围尚未进入父场景 profiler-off 测量。
- 当前候选源码：Plugin `hy_v4.py` SHA256 `38a7965b...65a4b7`；FlagGems `flashmla_sparse.py` SHA256 `680eff6b...e4f4fc`。两者未提交、未推送。最终状态为服务停止、8010 释放。

证据入口：

- reprofile：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/p4k-d128-c8-n8-indexer-host-metadata-reprofile-20260916-03/`
- trace：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/profiling/p4k-d128-c8-n8-indexer-host-metadata-reprofile-20260916-03/traces/`
- sparse MLA SQ sweep：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/sparse-mla-hq4-bk32-sq-sweep-20260916.jsonl`
- planning review：`models/Hy4-preview/ppu/optimize/state.yml` 的 `20260916-latest-p4k-checkpoint`。

## 10. P4K/C16 profiling 与 Indexer exact 优化

为兼顾父场景代表性与 trace 体积，本轮选择 `P4096/D64/C16/N16`：保留 4K prompt，总输出仍为 1024 token，并把并发提高到 C16。旧 phase marker 会将部分 chunked-Prefill continuation 标成 Decode，因此热点和收益统一使用全 trace kernel 汇总与 launch grid 归因。

- Full-range Indexer bypass 在每行有效 key 数不超过 `topk` 时直接生成 request-relative 连续索引，跳过 gather/QK/ReLU/reduce/Top-K。算子对照 `8.462x–12.665x`，索引逐元素一致，graph capture 与输入变化 replay 通过。reprofile 恰好各消除 5,376 次 BMM、ReLU、reduce 和 Prefill Top-K；rank0 Indexer wall time `16441.335 -> 11975.788 ms`（`-27.16%`）。
- Exact pointwise 候选只融合 BF16 ReLU 与权重乘法，保留原生 `torch.sum`。乘积和 FP32 logits exact fraction 均为 1.0；归约链 `1.293x`，完整 scoring block `1.092x`。trace 中 ReLU+mul `353.904 -> 173.354 ms`（`-51.02%`），rank0 Indexer `11975.788 -> 11521.408 ms`（`-3.79%`），全 trace device activity `40147.078 -> 39968.609 ms`（`-0.44%`）。profiler-on throughput `+0.45%` 仅作诊断。
- `64/256/512` scoring block rows 均慢于当前 128。完全融合归约虽然更快，但改变约 `0.077%` Top-K 选择集合，已拒绝并由 exact 方案取代。
- Sparse MLA 仍为第一热点，rank0 `11779.021 ms`、占比 `29.47%`。现有 BK32 的 SQ 范围特化继续保留；其他 tile 和 SQ2048 Split-K 已被完整调用退化、ramp 退化及 workspace 成本证伪。下一轮不再盲扫同类参数，优先检查合计约 26.2% 的 fused MoE 与 scaled MM 是否已有可替换/可特化实现。

Plugin 聚焦测试 `9/9`、graph capture 和三次 replay（含输入变化）通过。当前 Plugin `hy_v4.py` SHA256 `7c1843727800a6e1bc5252c28aaf33f0801da672442aa4ad145c7ce613ec6ea2`；FlagGems `flashmla_sparse.py` SHA256 `680eff6be15e259d36036f82958fb383ba1acc781bee1046caa246ae99e4f4fc`。候选未提交、未推送；服务已停止、8010 未监听、worker 已释放。

结论只适用于 operator 和 profiler-on 缩减场景。父场景 `P4096/D1024/C64/N128` 的 profiler-off A/B/revert 仍待执行；在此之前不把 `+0.45%` 作为端到端正式收益。保持 `max-num-batched-tokens=2048` 作为控制值，代码冻结后再单独扫描配置。

证据：

- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/p4k-d64-c16-n16-full-range-reprofile-20260916-05/`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/p4k-d64-c16-n16-exact-pointwise-reprofile-20260916-06/`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/indexer-full-range-kernel-compare-20260916.json`

## 11. 最新父场景 checkpoint 归因与 scaled MM Prefill 配置优化

用户最新 CSV `hy4_4096in_1024out_c64_n128_20260916_155355.csv` 的 Run2/Run3 稳态 output throughput 为 `227.80 tok/s`，相对 `20260916_082820` 的 `224.03 tok/s` 提升 `1.683%`；total throughput 同比提升 `1.683%`，mean TTFT 改善 `4.546%`，mean TPOT 改善 `1.199%`。median ITL 反向变化 `+1.409%`，P99 ITL 改善 `2.114%`。Run1 从 `5350.86 s` 缩短到 `774.99 s`，但仍是本次稳态时长的 `1.347x`，因此冷启动/首轮异常尚未消失。该比较只有 CSV checkpoint 身份，不具备同轮 baseline/candidate/revert 证明。

算子收益未线性兑现到端到端，原因已经由现有 trace 量化：

- Exact pointwise 把局部 ReLU+mul kernel 降低 `51.02%`，但它在优化前只占整段 device activity 的约 `0.88%`，因此整段 device activity 实际只下降 `0.445%`；这是典型的 Amdahl 上限。
- Full-range Indexer 的 `-27.16%` 是包含嵌套调用、异步等待和跨 stream 重叠的 inclusive wall time，不能与 sparse MLA、MoE 或通信耗时相加后外推端到端收益。
- profiler milestone 为 `P4096/D64/C16/N16`，父场景为 `P4096/D1024/C64/N128`；更长 Decode 与更高并发改变了 Prefill 命中覆盖率，并放大调度、KV、MoE、通信和 graph replay 的占比。
- 最新 trace 中 sparse MLA、fused MoE、scaled MM、linear 与 ring all-reduce 仍分别占据显著份额；算子可能与通信或其他 stream 重叠，减少某个 kernel 的累计 duration 不等于同量减少关键路径。
- 最新 checkpoint 的 TTFT 改善约 `4.5%`、吞吐改善约 `1.7%`，与“优化主要作用于 Prefill/Indexer，而长 Decode 仍主导”的现象一致。

沿热点迁移继续分析 `scaled_mm_kernel`：rank0 全 trace 为 `4485.144 ms / 44928` 次，占 device activity `11.22%`。六个 `M=2048` Prefill 主力 shape 覆盖了大部分该热点，因此在 T-Head `tune_configs.yaml` 中加入三个通用候选，而未按模型名或精确 shape 写死实现：`BM128/BN64/BK64/s3`、`BM128/BN128/BK64/s3`、`BM64/BN256/BK64/s3`；同时保留原四个候选，其他平台不变。

应用前后的 fresh-process wrapper 微基准如下：

| M/N/K | 原 wrapper | 新 wrapper | 加速 |
|---|---:|---:|---:|
| 2048/256/6144 | 149.176 us | 129.832 us | 1.149x |
| 2048/1024/2048 | 142.000 us | 131.696 us | 1.078x |
| 2048/6144/1024 | 336.656 us | 269.856 us | 1.248x |
| 2048/576/6144 | 245.120 us | 158.056 us | 1.551x |
| 2048/6144/128 | 92.064 us | 71.120 us | 1.294x |
| 2048/2048/6144 | 657.360 us | 656.816 us | 1.001x |

按 trace 调用次数加权，六个 shape 的估算 kernel 时间从 `4041.731 ms` 降到 `3531.340 ms`，减少 `510.391 ms`（该子集 `-12.63%`）；相对全部 scaled MM 热点为约 `11.38%`，相对整段 device activity 的理论上限约 `1.28%`。这只是基于 trace 频次的投影，不能作为端到端收益。

运行时确认加载 7 个 T-Head `scaled_mm` 配置，六个主力 shape 实际分别命中上述三个新 tile，不是仅将配置写入磁盘。`M2048/K6144/N576` Prefill 与 `M16/K6144/N576` Decode shape 均完成 graph capture 和两次 replay，逐元素 exact fraction `1.0`、最大绝对误差 `0`。服务始终未启动，8010 未监听。当前新增 `tune_configs.yaml` SHA256 为 `2b44781b...65e220`，改动未提交、未推送；FlagGems 原有 sparse MLA 候选及测试改动保持不变。

证据：

- checkpoint 对比：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/performance/p4k-checkpoint-082820-vs-155355-20260916.json`
- shape/launch 归因：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/scaled-mm-shapes-rank0-v2-20260916.json`
- 应用前后算子结果：`.../results/operators/scaled-mm-prefill-tiles-20260916-{01,02}/summary.json`
- graph 验证：`.../results/operators/scaled-mm-prefill-config-validation-20260916-01/summary.json`
- 实际 tile 命中：`.../results/operators/scaled-mm-selected-configs-20260916-01/summary.json`

## 12. P4K/C32 大场景 profiling 与 W8A8 fused MoE 优化

本轮将诊断规模扩大为 `P4096/D128/C32/N32`：保持 4K prompt，把并发提升至
C32，并把总输出扩大到 4096 token。专用服务完成一轮预热、两轮 measured，
最后一轮启用 profiler；32/32 请求成功。16/16 rank trace 均通过 gzip 解压和
JSON 解析校验，总量约 2.3 GiB。采集和分析结束后服务已停止，8010 未监听，
16 张 PPU 无 worker。

抽样 rank0/1/15 的设备活动差异为 Prefill `1.38%`、Mixed `4.07%`、Decode
`1.10%`，覆盖稳定。阶段热点如下；旧 marker 可能把 chunked-Prefill continuation
标为 Decode，因此这些比例只用于热点排序，不作为端到端收益：

| 阶段 | sparse MLA | fused MoE | scaled MM | ring all-reduce | linear |
|---|---:|---:|---:|---:|---:|
| Prefill | 28.13% | 18.52% | 12.51% | 10.39% | 7.73% |
| Mixed | 27.86% | 16.35% | 11.05% | 8.51% | 6.83% |
| Decode | 28.77% | 15.50% | 9.49% | 5.08% | 10.47% |

调用链确认 Hy4 使用 Plugin `FlagGemsW8A8Experts`，并直接进入 FlagGems
`fused_experts_impl(use_int8_w8a8=True, per_channel_quant=True)`。主导调用为
`M=2048/E=256/topk=8`，TP16 本地权重形状为 `w1=[256,256,6144]`、
`w2=[256,6144,128]`。GEMM2 改用 `BLOCK_N=256` 的候选完整算子反而退化
约 `0.38%`，已拒绝。有限 tile sweep 表明瓶颈来自 PPU 上大 M 的 8-warp
配置；改为 4 warps 后收益稳定，且不需要改变 tile、路由元数据或数值路径。

最终改动仅在 `PPU-ZW810E + int8_w8a8 + M>=256` 时选择 4 warps，其他设备、
量化类型和小 M 行为不变。独立进程完整算子复验中，M256/M512/M1024/M2048
的中位数加速分别为 `1.060x/1.154x/1.167x/1.044x`；修改后源码的 M2048
120 个交错样本为 `2.4790 -> 2.3372 ms`，提升 `6.07%`。输出逐位一致；
graph capture 和两次 replay 通过且与 eager 逐位一致；配置测试 `26/26` 通过。

当前 `fused_moe.py` SHA256 为
`fa78e4c2e193be632399d0fb6749e1e031a4acae8f46e11c09651608ea4dde21`，测试文件
SHA256 为 `a5f805b3783451437a1b8ae8b2b88ee1dd28a6ac5b2a532b3bc9cf4cf9668dcf`。
改动位于 FlagGems `support-hy4-preview` 分支工作区，尚未提交、未推送。
这仍是 profiler-on 诊断和算子级证据；父场景端到端收益由用户下一轮
profiler-off 复测确认。

证据：

- profile：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/profiling/p4k-d128-c32-n32-scaled-mm-reprofile-20260916-07/`
- trace：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/profiling/p4k-d128-c32-n32-scaled-mm-reprofile-20260916-07/traces/`
- fused MoE 复验：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/fused-moe-warps4-20260916/`
- 补丁：`/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/commands/flaggems-hy4-w8a8-moe-warps4-20260916.patch`

## 13. C32 profile 后继续优化：精确量化、moe_sum 与 sparse-index 转换

用户判断上一轮预期端到端收益不足，因此本轮没有启动服务或执行端到端
benchmark，而是继续扩大可解释收益池。首先完成 W8A8 MoE 的精确 per-token
量化融合：已有 Plugin Triton 量化器虽然更快，但 reciprocal multiply 会让约
`0.017%` 量化元素产生 1 LSB 差异，未采用；最终使用
`libdevice.div_rn + libdevice.rint`，量化值和 scale 均逐位一致。它与已有
4-warp 规则组合后，M2048 完整 MoE 从 `2.49665 ms` 降到 `2.22164 ms`
（`1.1238x`），输出逐位一致，graph capture 和两次 replay 通过，完整
fused-MoE 测试 `56/56`。

归档中的 `phase-analysis-sampled.json` 复用了旧分析器，顶层 scenario/parent
元数据仍写成 C8/N8；其 trace 路径、kernel 次数、耗时和 32/32 请求证据来自
本轮 C32/N32 profile。后续归因以原始 trace 和 whole-trace kernel 汇总为准，
不使用该过期顶层标签。

`moe_sum` 进一步通过固定已测 tile 绕过通用 Triton autotuner 的每调用 host
分派。门禁限定为 T-Head、BF16、TopK8、hidden=6144 和连续 tensor；M256
为 `1.303x`，M2048 为 `1.072x`，逐位一致，graph 两次 replay 通过，完整
测试 `76/76`。尝试把求和直接融合进 GEMM2 的 atomic direct-sum 在 M256、
M2048 分别只有 `0.813x`、`0.340x`，且重复结果不稳定、最大绝对差
`0.125`，已完整回退。

最大的新增收益来自 vLLM sparse-index 转换。大 profile 中
`_convert_req_index_to_global_index_kernel` 在 Prefill/Mixed/Decode 分别占
`2.88%/2.70%/1.67%`；默认 `BLOCK_N=128` 使 TopK2048 每行产生 16 个
program 和 16 次 valid-count 原子加。Plugin shim 仅在 T-Head、TopK2048、
`return_valid_counts=True`、无 prefill workspace 时改用 `BLOCK_N=2048`，
其他路径原样 fallback。实际包装函数 M256 `1.567x`、M2048 `4.616x`，
indices/counts 均逐位一致，graph capture、两次 replay、eager/replay 均通过；
HY4 Plugin 测试 `10/10`。按 Prefill 热点份额计算的设备时间理论上限约
`2.25%`，但它不是端到端收益。

router FP32 linear 的详细数值审计更正了上一轮结论：native MM 默认运行在
`float32_matmul_precision=highest`、`allow_tf32=false`，其 `3.4x–17.4x`
收益不是来自 TF32。M1024/M2048 分别只有 1 行发生 Top-8 内相邻名次互换，
但两者的 Top-8 专家集合均 `100%` 相同，没有第 8/9 名跨界。抽取变化行并
对照 FP64 后，FlagGems/native 的平均绝对误差分别为 `7.80e-5/1.26e-3`，
表明差异来自 vendor GEMM 与 Triton GEMM 的 FP32 并行累加/tiling 顺序。
FlagGems `BLOCK_K=32/64/128` 输出逐位相同，而耗时约
`873/1486/2216 us`，无法通过扩大归约块获得收益。开启 TF32 可把 M2048
native MM 从约 `258 us` 进一步降到 `145 us`，但会实际改变 `10/2048`
行的专家集合，因此仍予以拒绝。

根据用户选择，full-FP32 native router MM 已在 Plugin 的 HY4 模型边界完成
接入。只有 T-Head、H6144/E256、FP32 weight/output、无 bias、`highest`、
TF32 关闭且有效 FlagGems policy 确认 `mm` 不被接管时才命中；其余输入回退
原 `GateLinear`。profiler 证明执行为 `aten::mm` 和 PPU vendor FP32 GEMM，
不是 FlagGems `linear_kernel`。包含 BF16→FP32 cast 的完整 wrapper 在 M1–2048
为 `2.78x–11.46x`，graph capture 与两次 replay 通过且 eager/replay 逐位一致，
Plugin 聚焦回归 `17/17`。同一随机验证在 M2048 有 `1/2048` 行跨越 Top-8
边界，该行基线 8/9 间隔仅 `0.001755`、逐行最大 MM 差 `0.004852`；因此候选
已接入源码，但模型精度 gate 是启用后的硬门禁，尚无端到端收益结论。当前
`hy_v4.py` SHA256 为 `7e42a416...c845e`，服务未启动。

当前源码哈希：Plugin `hy_v4.py` 为 `745d064d...bbba9`；FlagGems
`fused_moe.py` 为 `d7a1fbf3...7641`，`moe_sum.py` 为
`7419f5d6...b8a2`。FlagGems 当前分支为 `support-hy4-preview`；Plugin
运行工作区实际分支为 `codex/deploy-pr477-20260910`。两仓库改动均未提交、
未推送。服务保持停止、8010 未监听、PPU 无运行进程。

本轮 planning review 为 `20260916-post-c32-moe-and-index-convert`。scaled MM
约 `1.28%`、fused MoE 约 `1.9%–2.2%`、sparse-index Prefill 约 `2.25%`
以及 moe_sum 至多约 `0.25%` 都是可能重叠的阶段/device 上限，不能直接相加。
但与上一轮相比，组合收益池已明显扩大，下一项高信息量实验应是用户执行
`P4096/D1024/C64/N128`、`max-num-batched-tokens=2048` 的 profiler-off
端到端复测。

证据：

- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/fused-moe-warps4-20260916/source-verify-m2048-combined-with-moe-sum.json`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/moe-sum-20260916/moe-sum-source-verify.json`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/index-convert-20260916/index-convert-shim-verify.log`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/router-linear-20260916/router-linear-narrow.json`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/router-linear-20260917/router-linear-numerics-audit.json`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/router-linear-20260917/native-router-mm-integration.json`
- `/mnt/nfs/users/jinghao/hy4-preview/optimize/20260914-hy4-preview-ppu-e2e/results/operator/fused-moe-direct-sum-20260916/moe-direct-sum.json`

## 14. 最新 C64 checkpoint、热点迁移与 Indexer 无同步前缀回写

- `20260917_132531.csv` 的稳态 output/total throughput 为 `278.14/1390.72 tok/s`，相对 `20260916_155355` 提升 `22.10%`；mean TTFT/TPOT 改善 `10.18%/19.29%`，median/P99 ITL 改善 `26.35%/8.93%`。这是 checkpoint，不是同轮 A/B/revert。
- Run1 仍比稳态慢 `59.39%`，另行归因为首 shape autotune/graph/cache 准备问题，不与稳态算子收益混算。
- `P4096/D128/C64/N64` reprofile 覆盖 16/16 rank；sparse MLA 在 Prefill/Mixed/Decode 占 `31.14%/33.55%/35.52%`，为新的首位 device activity。native router MM 只剩约 `1.9%–3.1%`，证明 router 热点已明显下降。
- Indexer 单行布尔索引回写会触发 `nonzero + DtoH/sync`。候选改为对已证明全部有效的固定前缀直接原地加 offset，count 0/1/17/1024/2048、graph capture + 2 replay 和 Plugin `14/14` 测试均通过。42 次链路为 `2.842 -> 0.360 ms`（`7.90x`），但绝对节省只有 `2.48 ms`，不将 trace 中重叠的 `2.489 s` 等待外推为端到端收益。
- 已有 sparse MLA tile/Split-K 扫描边界保持不变；下一轮若继续攻 MLA，必须是新算法/并行或数据流机制，不再重复已证伪的 SQ2048 tile 穷举。
- 当前 Plugin SHA256 为 `7e65f869...204ed`，未提交、未推送。服务已停止，8010 端口空闲，PPU worker 已释放。
- 2026-09-18 用户确认当前优化环境的远程 GPQA 精度为 `91.92%`，服务精度验证通过；本项目暂未收到原生结果文件路径，不补猜 runner 参数或其他阈值。
