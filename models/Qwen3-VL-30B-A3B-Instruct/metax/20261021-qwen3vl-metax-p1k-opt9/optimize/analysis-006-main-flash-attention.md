# analysis-006：main.py 与容器 Attention 实现对比

后续已完成[op-007原生对比实测](op-007-fa-main-native-micro.md)：18个shape数值/graph通过，但main.py完整调用全部慢于原生。本页保留分析阶段的事实与未测边界，实际性能以op-007为准。

- 日期：2026-10-21；Host：`mx-59`；容器：`qwen3vl-p1k-opt9-20261021`。
- 状态：`static-analysis-complete / performance-not-proven`；分类：`operator/improve` 的候选分析。
- 范围：用户指定文件与容器源码只读比较、复核既有 trace、CPU 公式推导；未修改远端源码或服务，未运行 GPU 测试。
- 关联场景：`p1024-d1024-c64-n128`，同时讨论 Prefill、Decode 和 Mixed；不是新性能实验或正式验收。

## 结论与瓶颈依据

`main.py` 是完整的 Triton varlen Attention 候选实现。主要机制是直接在 kernel 内打包 GQA heads、转置 QK/PV 计算方向、按设备并行度启用 Split-KV，以及减少 wrapper 中的复制和辅助输出。它有研究价值，但目前不能认定比容器实际路径更快，也不适合原样全量替换。

本次最关键的核验是：**容器中存在 FlagGems-vllm Triton Attention，并不代表已有服务使用它。** 重新读取并校验已有双 rank 三阶段 trace，实际出现的是 `mcFlashAttn` 的原生 C++ kernel，而不是 `flash_varlen_fwd_kernel`。因此需要区分三个对象：

| 对象 | 入口与地位 | 证据等级 |
|---|---|---|
| 用户候选 | Host `/public-flash/jinghao/qwen3-VL/main.py` 中的 `run` | 本次读取源码；未取得当前版本 GPU 测量 |
| 库内 Triton 实现 | `/workspace/FlagGems-vllm/src/flaggems_vllm/ops/attention.py` → `flash_api.py` → MetaX `flash_attention/` | 本次读取源码；是源码对比对象，不是本服务已证实的执行路径 |
| 已有服务执行路径 | Plugin `MacaFlashAttentionBackend` → `flash_attn` → `mcFlashAttn` | 同案例已有 Prefill/Decode/Mixed trace 的原生 kernel 名称，以及当前读取的 backend 调用代码 |

既有 trace 的 rank0 摘要如下。它们来自不同缩减诊断 workload，不能跨行计算加速比；累计 kernel 活动可重叠，不是关键路径时间。

| 诊断阶段 | 原生 Attention 主要活动 | 累计时间 / 调用数 |
|---|---|---|
| Prefill | `flash_fwd_splitkv_kernel<...128,64,64,4...>` | 151.799 ms / 432 |
| Decode | `flash_fwd_splitkv_kernel<...128,16,16,1...>` | 27.816 ms / 3072 |
| Decode | `flash_fwd_splitkv_combine_kernel<...>` 的主要分组 | 23.876 ms / 2832 |
| Mixed | 上述 Decode 主 kernel | 163.733 ms / 3024 |
| Mixed | 上述 Prefill 主 kernel | 152.159 ms / 432 |

这证明已有服务已经执行原生 Split-KV/merge；不能把库内 D128 自动拆分的缺口当成该服务的实际缺口。Decode 诊断为 P1/D64，Mixed 为 P1024/D64，且最多采集 64 步；不能由其直接推断 P1024/D1024 全程热点。此轮未启动新服务，不声称取得新的运行中 worker 命中证据。

## 源码身份与调用链

当前读取四仓库 HEAD：

| 仓库 | revision | 工作区 |
|---|---|---|
| FlagGems | `c3c5f5ab274f7d1a8a95e3d3ba7bbac28e4a9fd4` | clean |
| FlagGems-vllm | `f6fdb9b120787e12892ac67e54979cbf829c7d64` | 既有 MoE、采样和 export 改动；Attention 目录未显示未提交修改 |
| Plugin | `08da21cb39601752040196232b60a152382c0f8f` | 既有采样接入改动 |
| vLLM | `ee0da84ab9e04ac7610e28580af62c365e898389` | clean |

候选文件 SHA256：`e2f78d30268caab7656193e070463eaab1271b9fac35c7ed57ffd4ef20cca642`，550 行。文件注释中的“436 correctness + 24 timing / aggregate 1.6537”是作者提供的历史说明；本次未取得其原始报告、shape、契约或当前版本复测，不作为相对此容器的 1.65× 收益证据。

当前 vendor 入口的源码路径（均为容器内路径）：

```text
vllm_fl/dispatch/backends/vendor/metax/metax.py:135
  → MacaFlashAttentionBackend
  → impl/attention/flash_attn.py:797
      Prefill → flash_attn_varlen_func
      Decode  → flash_attn_with_kvcache (:830)
  → impl/attention/utils/fa_utils.py:12
      from flash_attn import ...
  → trace 中的 mcFlashAttn native kernel
```

以上路径前缀为 `/workspace/vllm-plugin-FL/`。FlagGems backend 自身还通过 `VLLM_FL_USE_FLAGGEMS_ATTN` 控制其专用 Attention 选择（`dispatch/backends/flaggems/flaggems.py:191`）；已有归档启动环境没有该变量。`VLLM_FL_USE_FLAGGEMS_VLLM=1` 只能说明库选择条件，不能证明 Attention backend 已切换。实际选路以 trace 为准。

如果进入 FlagGems 专用 backend，源码调用关系是：

```text
Plugin .../flaggems/impl/attention.py:607
  → flaggems_vllm.flash_attn_varlen_func
  → ops/attention.py:1197
  → ops/flash_api.py:250 mha_varlan_fwd
  → runtime/backend/_metax/ops/flash_attention/launcher.py:189
  → scheduling.py 选择 direct / splitkv / D256 TN / worklist
```

## main.py 的优化机制与原实现的区别

按既有模型记录，TP2 每 rank 为 Q16/KV2/D128，GQA ratio=8。下述形状推导以此为前提，不代表每次调度都恰好 B64。

| 机制 | main.py | 容器 FlagGems-vllm | 判断 |
|---|---|---|---|
| GQA 打包 | `g_of=rr//ROWS`，每 CTA 对一个 KV head，直接从原始 Q 读取多个 query heads | 单 token Decode 已在 `flash_api.py:365` 将 group 维变为序列维；D256 TN 也打包 heads | 新点是统一到原布局 kernel、扩展覆盖，不能称原实现完全没有 GQA 复用 |
| 计算方向 | `K @ Qᵀ` 得 `[N,M]`；`Vᵀ @ P` 得 `[Dv,M]` | generic direct 为 `Q @ Kᵀ`；D256 TN 已有转置特化 | D128 是与库内 generic 路径的重要差异；内存和指令收益要看编译结果 |
| Split-KV | 按 natural CTA 数、SM 数、64 MiB PACC 上限选 splits，D128 也可自动启用 | auto 分支限 D256；D128 在支持条件下可显式请求 splits | 是相对库内 D128 的覆盖变化，实际 native 服务已经会 split |
| mask 分区 | clean 前缀与 masked 尾部，按列正向执行 | direct 已有 masked 尾部与无 causal mask 前缀，按列反向执行 | 属于实现重排，不能把全部 mask 消除收益归为新增 |
| 中间数据 | 原布局读 Q、写 out；不请求 LSE 时不产生 LSE；split partial 用 `empty` | Decode swap 可能复制 Q、out 和 LSE；wrapper 总是分配 LSE；Split-KV partial 也已经用 `empty` | wrapper/复制削减值得单独验证；partial 不清零并非相对此版本新增 |
| tile/pipeline | M64/N16/W4；D128 实际 stages=1 | D128 paged 长 Q 为 M128/N16/W8，通常 stages=3；Decode swap 后 M16/N16/W4 | 本模型不能归因为 stages2 流水线优化；CTA 工作量与资源配置也一起变化 |

`main.py:145` 中每个 query head 仍有独立 FP32 `(m,l,acc)`，没有在 heads 间混合 softmax。Split-KV 保存每段未归一化 acc、最大值 m、归一化和 l，merge 使用：

```text
M = max_s(m_s)
w_s = exp(m_s - M)
out = sum_s(w_s * acc_s) / sum_s(w_s * l_s)
```

这是代数上正确的全量 Attention 合并，不是稀疏或近似 Attention。但 QK/PV 的输入舍入、分块、遍历方向和归约顺序均可能改变，不能据此保证与原实现逐位相同。“固定分区确定性”也只适用于相同 shape、splits、硬件与编译环境。

## Decode：潜在收益及代价

`main.py` 对 G8 得到 `G_TILE=8, ROWS=8, NPASS=1`。按 C550 的 104 SM 假设，直接抽取原文件两个纯 Python host 函数进行 CPU 计算：

| B | 每请求 Q | maxK | natural CTA | auto splits | PACC+PML |
|---:|---:|---:|---:|---:|---:|
| 64 | 1 | 1024 | 128 | 4 | 2,129,920 B |
| 64 | 1 | 2048 | 128 | 4 | 2,129,920 B |
| 8 | 1 | 1024 | 16 | 26 | 1,730,560 B |
| 1 | 1 | 1024 | 2 | 32 | 266,240 B |

在 B64 时，拆分让 128 个自然 CTA 变为 512 个，试图填满设备；代价是额外 partial 写读和 merge kernel。8 个 heads 在 Q=1 时只占 M64 中的 8 个有效位置，不能从“64 行 tile”理解为 64 个有效 query。库内 Decode swap 后 M16 可有 8 个有效位置；因此候选扩大 tile 也可能增加无效矩阵工作与寄存器占用。

以 BF16、Q16/KV2/D128、B64/K1024、无额外 KV 重读为理想模型：QK+PV 约 `4*B*Hq*K*D = 0.537 GFLOP`，KV 最少读取 `2*B*Hkv*K*D*2 = 64 MiB`，算术强度约 8 FLOP/B。若已成功复用 GQA heads，候选没有再次减少 8 倍 KV 的空间；重点可能是并行度、布局和包装开销。这些是逻辑下界，未测 DRAM/L2 或实际 FLOPs。

对标准连续 Q 布局、B>1/Hkv>1，库内 group/sequence transpose 后 flatten 通常不能零复制表示，`reshape_view_or_copy` 会生成真实 Q copy；out 还原及 LSE 还原也可能有 copy。`main.py` 避开这套变换，值得单独量化，但不能把 native backend 的 copy 归因到这段未命中的 wrapper。

## Prefill 与 Mixed：不能照搬 Decode 判断

长 Q 时，`main.py` 的一块 M64 实际覆盖 8 token × 8 heads；库内 generic direct 的 M128 是单 head 的 128 token。

以每请求 Q1024 为例，库内 generic direct 约 `16*ceil(1024/128)=128 CTA`，候选约 `2*ceil(1024/8)=256 CTA`。候选跨 head 共享 KV，但 token tile 同时缩小 16 倍；忽略 causal 边缘、padding 和缓存后，每个 KV head 的完整扫描次数约是原来的 2 倍，不能声称长 Prefill KV 读取降低 8 倍。这是源码流量模型，不是 DRAM 实测，也不适用于直接推断 native kernel 的表现。

模型 D128 会把候选 stages 固定为1；B1/Q1024 时 natural=256，不拆分。长 Prefill 需要单独比较 tile、stage、带宽与占用率。Mixed 的 batch 和每请求 Q 长度不均匀时，两套策略仍按 maxQ 建矩形 grid；候选没有 compact worklist，不能据此宣称减少 ragged 空 CTA。若经 vendor 适配，Prefill/Decode 元数据切分和调用组织变化还可能引入额外收益或退化，必须与 kernel 改动分开归因。

## 接入和正确性问题

1. **与实际 vendor ABI 不直接兼容。** vendor Prefill 在 `flash_attn.py:807` 传 `block_table + cu_seqlens_k`，不传 `seqused_k`；候选 `main.py:417` 要求存在 block table 时必须提供 seqused，直接替换会 assertion。需要从已有元数据显式映射有效 KV 长度，不能把两种 ABI 静默混用。
2. **只改 varlen 不会覆盖 Decode。** vendor Decode 在 `:830` 调的是 `flash_attn_with_kvcache`，Q 有 batch/sequence 维。候选是扁平 varlen 接口；需独立适配 query、长度、block table、output buffer，并保留不支持条件的原路径。收益测量要覆盖完整适配调用。
3. **显式 num_splits 被忽略。** `main.py:389` 校验 0–32，但 `:483` 总调用 `_choose_splits`，没有应用用户值。`num_splits=1` 不能关闭拆分，显式值也不能稳定控制。原库的 scheduler 明确定义0=auto、1=禁用、>1=显式。CPU 示例 B64/Q1/K1024 会选4，即使传1也一样。
4. **非因果 ALiBi 公式错误。** 两处候选 bias 为 `slope*(key-diag)`；非因果契约和原库 `flash_kernel.py:116` 为 `-slope*abs(key-diag)`。例如 QK全0、Q=K=3、query位置1、slope=1、V=[0,1,2]：正确输出1，候选公式输出约1.575210；本次 CPU 公式复现。causal 下可见区间内二者才等价。该问题不说明当前无 ALiBi 的 Qwen 路径一定错误，但否定无 guard 的通用替换。
5. **输入检查没有完整继承。** 候选缺少原库的 fp16/bf16与QKV dtype一致、CuQ/CuK int32且连续、out形状和dtype、head dim上限及对齐等断言。CuQ/CuK 在候选 kernel 中按连续数组读取，因此不能把“无断言”当作支持任意 stride。不能以签名近似相同声称 ABI 相同。
6. **ALiBi 尾 head 还有潜在越界。** GROUP非2幂、NPASS最后一轮时，head可能超过合法范围；Q与store有rmask，但 `main.py:157` 读取alibi没有对应mask。G8不触发，通用支持必须处理。
7. **内存上限和 graph 尚未验证。** 64 MiB cap只计算PACC，PML额外占 `8*S*Hq*Tq` bytes；没有约束PACC+PML总和。固定CuQ、seqUsed、页表地址下变化内容 replay、空split、全mask行、非连续out、非对齐长度及实际页映射都需要设备验证。不能由只使用torch.empty就断言graph通过。

## 性能效果、决定与后续验证

本次没有 baseline/candidate/revert GPU 数值、性能或服务结果；收益、编译资源、graph稳定性、模型精度全部为 `not_run/unknown`。CPU推导和ALiBi反例不替代GPU验证。当前保留的 op005 采样候选与既有精度状态保持原样。

建议首个实验先修正/约束候选ABI，冻结 BF16、D128、G8、无ALiBi/softcap/window、真实KV页及graph条件，再分别进行三路比较：现行native、库内FlagGems、候选。先做数值和实际命中，再做完整API计时；这能区分“替换库内慢路径”与“加速现行服务”。

Decode覆盖B1/8/32/64、KV1K/2K/4K及尾段；Prefill覆盖长短Q和不等长请求。拆分、转置、tile和wrapper削减应尽量逐项消融。数值/graph失败、候选未命中或完整调用退化即停止晋级。只有有效的当前精度契约和相同稳态Mixed B/C/R结果才支持保留与端到端收益声明。此轮没有实施，不需要回退；不创建PR或提交代码。

## 补充：明确走 flagos/FlagGems 时的 kernel 序列

这是当前读取源码的条件推导，不是新服务 trace。首先 Attention 选择器必须实际返回 `AttentionFLBackend`；仅选择 flagos 不足以保证，FlagGems selector 还检查 `VLLM_FL_USE_FLAGGEMS_ATTN=1`。该 backend 再由 `VLLM_FL_USE_FLAGGEMS_VLLM=1` 选择 `flaggems_vllm` 包，否则导入 `flag_gems`。以下限定前者、当前 FGV revision、Q16/KV2/D128、BF16、paged KV、无 ALiBi/滑窗/dropout、无DCP/cascade，Plugin传 `num_splits=0`。

三阶段默认都选 scheduler 的 `LEGACY` family，调用 `direct.py:52` 的 `flash_varlen_fwd_kernel`。单个 kernel 内融合 QK、online softmax、PV、out及LSE写回；不是三个独立计算 kernel。D128不满足D256 TN、compact worklist、page16 decode或auto Split-KV的维度条件。

| 调用条件 | 有效Q布局 | M/N/K、warps/stages | Attention grid |
|---|---|---|---|
| Prefill：B8、每请求Q1024 | `[8192,16,128]`，不交换heads | `128/16/128, W8/S3` | `(8,8,16)`，1024 CTA |
| 纯Decode：B64、每请求Q1 | `[64,16,128]` → `[512,2,128]`，每请求有效Q8 | `16/16/128, W4/S3` | `(1,64,2)`，128 CTA |
| Mixed示例：1×Q1024+63×Q1 | `[1087,16,128]`，整批不交换 | `32/16/128, W4/S3` | `(32,64,16)`，32768 CTA |

以上通过直接执行源码的纯CPU scheduler验证family和M/grid，N/warps/stages按当前MetaX heuristic与launcher读取。不是所有Prefill都固定M128：选择量为 `min(total_q/batch, total_q*num_heads/104)`，依次以严格大于64/32/16选择M128/64/32，否则M16。

标准连续Q、B64、Plugin提供out时，纯Decode完整序列为：

```text
_copy_or_fill                # Q transpose/flatten不能作为零复制view
flash_varlen_fwd_kernel      # 128 CTA，GQA heads作为8个有效序列位置
_copy_or_fill                # 还原head布局，写入Plugin提供的out
_copy_or_fill                # LSE permute/reshape物化
```

纯CPU执行原 `_view_strides`，Q的 `(64,8,2,128)` / strides `(2048,128,1024,1)` → `(512,2,128)`，以及LSE的 `(2,8,64)` / strides `(512,1,8)` → `(16,64)`，均返回None，确认这些标准布局需要复制。B1、Hkv1或不同stride可能改变copy数。`return_softmax_lse=False`不阻止当前wrapper内部生成、还原LSE，最后只是不返回给调用方。

Mixed不采用vendor backend那种Prefill/Decode两次API调用：整个batch一次varlen。上述示例中仅1520个CTA对应有效Q tile，其余通常早退；这是矩形grid的名义任务数，不能视为32768个完整Attention任务的计算成本。D128没有compact worklist来去掉这些任务。KV cache写入由Plugin独立的 `do_kv_cache_update → reshape_and_cache_flash` 承担，不计入上面一个Attention主体/三次copy；服务其他算子也不在本序列中。

## 外部证据与源码锚点

远端原始文件保留原位，本地仅记录分析与SHA；临时下载副本不作长期证据根。

- Host候选：`/public-flash/jinghao/qwen3-VL/main.py`；SHA见上；GQA/转置`:94/:145`，clean`:110`，merge`:282`，splits`:349`，入口`:368`，stage门控`:512`。
- 容器库前缀：`/workspace/FlagGems-vllm/src/flaggems_vllm/`。
- `ops/attention.py` SHA256 `7632a53fe2eebee6e7d019ccc51bd1449be9458fb9f55b09d8cca9920d6874f5`。
- MetaX `flash_attention/scheduling.py` SHA256 `b4006c1360b33eef07789c77afd0ba771c5346a073f51f82591f0109d9fb5573`；自动D256条件`:330`附近。
- `flash_attention/direct.py` SHA256 `55432f624e753183b95ae6405b4c69ddd8086b746ec3103b93ebbc05482909af`；mask两段`:247/:353`，资源配置`:516`。
- `flash_attention/splitkv.py` SHA256 `2432a4d0328d00ed8caaf0b272bd4c0a0a1958634fb92d5ac63280465f6e322d`；partial用empty`:565`。
- 既有三阶段摘要：`/public-flash/jinghao/qwen3-VL/20261021-qwen3vl-metax-p1k-opt9/results/phase-trace-analysis.json`；SHA256 `8a61c13e921d7fc584ee4f852e1cc47a3cd085ce1a2b1df1afc77b3aa7436f95`，本次重新读取确认。
- 同案例 `manifests/baseline2-service.json`、`manifests/baseline2-launch.json` 及 `results/baseline2-worker-pid1295.json`、`baseline2-worker-pid1296.json`：已有TP2启动配置与真实导入路径。本次重新读取；不把历史服务身份当成本轮新绑定。

知识差量：`refined`。原先仅凭安装库、Qwen形状和D128 scheduler推断Attention优化空间不足以指导服务修改；必须先区分native varlen、native kvcache和FlagGems Triton。GQA打包也必须连同token tile跨度与已有Decode swap分析，不能单独计作8倍KV流量收益。
