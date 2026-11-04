# 20260921-p16k-phase-profile-18 P16K Prefill/Decode/Mixed 热点定位

- 状态：`complete`
- 分类：`framework`（诊断）
- 目标场景：`P16384/D1024/C64/N128`
- profile 模式：`capture_then_analyze`

## 优化方向与瓶颈依据

P16K 稳态入口基线为 434.205 tok/s，P99 TTFT 112.656 s、
P99 TPOT 143.780 ms。这些客户端指标不能区分长 Prompt Prefill、
逐 token Decode 和两者共存的 Mixed admission 干扰，也不能把 P4K
热点直接外推到 P16K，因此重新采集 16-rank trace。

## 优化内容与适用边界

本点不修改源码。使用与基线相同的 TP16/BF16/max64/
token-budget16384/FULL_DECODE_ONLY/前缀缓存关闭服务，只增加
torch profiler。完整运行一轮 profiler-off warmup 和一轮 profiler-on
P16K，profiler 记录 shape、gzip 输出，不记 stack/flops/memory，最多
120 个 model iteration。

分析使用 `execute_new_<new>_cached_<cached>` 成对 marker：new-only 为
Prefill，cached-only 为 Decode，同时存在为 Mixed。inclusive device activity
允许重叠，只用于热点排序，不解释为关键路径时间或正式吞吐。

## 正确性与路径命中

启动前核验三个仓库 revision/预期 dirty 集、exact-M64 guard、
FlagGems DB SHA 和前缀缓存指标。要求两轮各 128/128 请求成功、
DB SHA 不变、16/16 rank trace 新鲜可解析，且三个阶段的 marker
边界可辩护。

## 性能效果

profiler-off 和 profiler-on 两轮均 128/128 请求成功。profiler-off
输出吞吐 433.818 tok/s，与稳态基线 434.205 tok/s 相差约
-0.089%；profiler-on 为 253.386 tok/s，只表示 profiler 开销，不宣称
性能回归。DB SHA 前后不变，16/16 rank trace 新鲜可解析。

rank0 共获得 120 个 CPU marker 和 119 个 device marker：1 Prefill、
63 Mixed、56 Decode。Mixed 的 63 个 marker 全部是
`execute_new_1_cached_{1..63}`，证明 16384 token budget 在 P16K 下每波
只能 admission 1 个新请求。

rank0 summed device activity（允许重叠）的主要热点为：

- Prefill：Sparse MLA 27.968%、fused MoE 20.188%、large-M GEMM
  11.491%、MQA logits 7.420%、Ring all-reduce 6.305%；
- Mixed：Sparse MLA 26.041%、fused MoE 18.769%、MQA logits 12.765%、
  large-M GEMM 10.674%、Ring all-reduce 5.563%、KDA `h_o` 4.426%；
- Decode：fused MoE 39.123%、Sparse MLA kernel 7.664%、mHC pre
  5.643%、two-shot all-reduce 5.259%、reduction 5.091%、MoE align 4.850%。

Mixed device activity 跨 rank 相对离散 0.428%，Prefill 0.784%，Decode
2.157%，没有单 rank 拖尾证据。CPU inclusive 中 nonzero/to/copy/index/
stream synchronize 占比高，但存在大量重叠，且 P4K 已证明主要与
device busy 重叠，不单独作为 P16K 首个候选。

## 决定、风险与回退

三阶段视图完整，首个单变量选择
`max_num_batched_tokens=16384→32768`，直接针对每波仅 1 个新请求的
63 波 Mixed admission。P4K 同变量只有 +1.095% 的反证，因此先在
`P16384/D128/C64/N128` milestone 做同配置 A/B/R；输出吞吐低于
+3% 或 TTFT/TPOT 任一劣化超 5% 即停止，通过后才晋级完整 D1024。
数据采集后 profiler 服务已在队列为零时停止。

## 外部证据

`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/full-scenarios/p16384-d1024-c64-n128/profiling/p16k-d1k-maxseq64-retained-18/`

- `phase-analysis-v3.json` SHA-256：
  `cd5b90bf595eae9a667452d2d5c607933b8e601535a64ba837a45686fdfcd83f`
- `runtime-evidence.txt` SHA-256：
  `e27eed4fce64723fe3b57ab6ef37e3ac0ac4373e4585561bfacdbb9729ad3a0b`
- `diagnostic.json` SHA-256：
  `e76336c35726faf209811c64b5309d774b7aaf299e5b4bb9faf6a577653fa897`
- `trace-sha256.txt` SHA-256：
  `92892c2bf5634bce5992f0e668f60558684090b34790afd6739f808b75f1b69b`
