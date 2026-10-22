# Qwen3.6-35B-A3B / mx-59：base 与 begin 性能 gap 诊断

取证日期：2026-10-13（Asia/Shanghai）。执行规则：SOP 0.40 / 2026-09-22。
`acceptance_scope=diagnostic`；`accuracy_status=incomplete`；`performance_status=incomplete`；证据等级 `observation`。

用户要求分析已有结果。本次只读访问 mx-59、两个指定容器和指定性能目录；未启动 benchmark、采集新 profile、重启服务或修改远端源码。没有新增优化容器或优化实验，镜像谱系、优化容器挂载门禁和正式验收均不适用本次历史分析。未访问“新模型适配”工作区。未指定新的远程工作目录，因此没有创建远端任务目录。

## 结论

唯一共同场景 P4096/D1024/C64/N128，begin 输出吞吐比 base 低 29.81%，平均 TPOT 高 40.87%。差距主要体现在首 token 之后的生成循环。两者是多变量环境比较：采样参数、GDN kernel、Attention/MoE dispatch、调度预算、graph 和软件工作区都不同。不能将全部差距归为 FlagGems 或某一个 Attention kernel。

尤其需要注意：base 本身启用了 FlagGems，并带有大量 vLLM/Plugin 本地优化；它不是未修改的原生 vLLM。begin CSV 的 P4K 测量发生于 10 月 10 日，但当前 FlagOS 服务在 10 月 12 日重启过，served name 也变成 `qwen36-35B-addattention`。当前源码和日志只能解释当前环境的候选机制，不能作为旧 CSV 对应执行路径的完整证明。

## 性能对比

以下使用原 CSV 的 SUMMARY，即 Run2/Run3 的算术平均；三轮原始数值均保留在远端。

| P4096/D1024/C64/N128 指标 | base | begin | begin 相对 base |
|---|---:|---:|---:|
| 批次完成时间（s） | 106.94 | 152.37 | +42.48% |
| 输出吞吐（tok/s） | 1225.58 | 860.24 | −29.81% |
| 总 token 吞吐（tok/s） | 6127.90 | 4301.18 | −29.81% |
| 平均 TTFT（ms） | 4652.68 | 6656.06 | +43.06% |
| 中位 TTFT（ms） | 2036.60 | 1479.53 | −27.35% |
| P99 TTFT（ms） | 14239.97 | 23939.36 | +68.11% |
| 平均 TPOT（ms） | 47.52 | 66.94 | +40.87% |
| 中位 ITL（ms） | 38.87 | 53.34 | +37.23% |
| P99 ITL（ms） | 450.49 | 215.38 | −52.19% |

两侧每轮均记录 128 个成功请求、524288 input tokens、131072 output tokens；base perf.log 中同时记录 failed=0。begin 目录仅有 CSV，缺原生逐请求 JSON 和旧客户端控制台证据。按全部三轮平均，输出吞吐分别为 1224.57 和 857.72 tok/s，gap 仍约 29.96%，不是 SUMMARY 略过第一轮造成的现象。

- Prefill 视图：平均/P99 TTFT 更慢，但 begin 中位 TTFT 更快；首 token 分布和调度有差异，不能称为每次纯 Prefill 都更慢。
- Decode 视图：TPOT 和中位 ITL 均更慢，存在广泛的逐步生成成本差异。按固定 1024 输出 token 估算，请求平均时长 `TTFT + 1023×TPOT` 从约 53.27s 增至 75.14s；增量约 21.87s，其中约 19.87s（90.84%）属于首 token 之后。这是客户端延迟分解，包含调度、网络、采样及资源竞争，不能当作纯设备时间或算子归因。
- Mixed 视图：base 平均生成间隔更低，但 P99 ITL 高约 2.09 倍，存在更长的少数停顿。较大的 Prefill chunk 可能造成 Decode 被长 Prefill 打断，需要 trace 才能确认。
- 仅 base 有 P1K：1555.23 output tok/s；仅 begin 有 P16K：418.67、P64K：104.34 output tok/s。这些长度不匹配，不能计算跨环境加速比；P32K 两侧均缺失。

## 已确认的环境差异与解释

### 1. 采样负载不同：先排除的配置混杂

base 启动参数为 `--generation-config vllm`；当前 vLLM SamplingParams 默认值为 temperature=1.0、top_p=1.0、top_k=0（不做 top-k 截断）。这不等于 greedy。

FlagOS 未设置该参数，模型 generation_config.json 为 temperature=1.0、top_k=20、top_p=0.95。service.log:413 明确记录三个参数覆盖默认值。当前 benchmark 没有 `--temperature` 或其他采样参数，perf.log 还提示新版 bench 不再默认设置 temperature=0。

当前 `vllm/v1/sample/ops/topk_topp_sampler.py` 中，不启用截断时 `apply_top_k_top_p` 直接返回；有截断时，batch≥8 且 HAS_TRITON 走 Triton 过滤，小 batch 走 PyTorch 排序、softmax、cumsum 和 scatter。模型词表为 248320，故每步过滤负载值得优先核验。不能仅凭源码宣称 C64 一定走全词表 PyTorch sort。不同采样还可能改变 MoE 路由和 token 内容，即使输出长度相同也不保证实际计算轨迹相同。

base 另有 Gumbel 采样 fastpath 补丁，但它受 `VLLM020_SAMPLING_GUMBEL_FASTPATH` 控制，当前进程环境未设置该开关，默认关闭；不将其算作已生效收益。

结论：当前采样配置差异已确认，额外过滤成本及对历史 gap 的具体贡献待同配置测量。begin 的旧请求参数未完整保留，不能追认旧轮的有效采样参数。

### 2. GDN packed decode 的 tile 有实质差异

模型 40 层中 30 层为 linear_attention，10 层为 full_attention。模型 linear value head dim=128，TP2 下通常为每 rank 16 个 value heads。

- base `vllm/model_executor/layers/fla/ops/fused_recurrent.py:439` 默认 `BV=min(next_power_of_2(V),32)`。
- FlagOS 同文件 :437 为 `BV=min(next_power_of_2(V),8)`，warps=1、stages=3。
- 相同 V=128 时，NV 从 16 变为 4；packed kernel 的 grid 是 `(NV,B×HV)`，base 的 program 数约为 FlagOS 的四分之一，单 program 工作量更大。减少 program 数不等于实测四倍提速，但这是比环境变量名字更明确的代码差异。
- 两侧源码都有 packed decode，不能说 FlagOS 完全没用融合 kernel。base 的 `VLLM020_GDN_PACKED_MIN_BATCH=32` 只控制 launch override 门槛，不是启用 packed decode 的开关；本次没有设置 BV/warps/stages override。
- base 有约 286 行 GDN 本地改动和 `VLLM020_GDN_T1_FUSED_H_SPLIT=1`。该 split 只在满足 decode 数、非 speculative、混合 Prefill 和 token shape 条件时适用；默认 Prefill token 范围限定 1024，不能声称覆盖所有 P4K step。

结论：GDN 是高优先级算子差异候选；缺历史 impl/shape trace 与同 shape A/B，贡献尚未量化。

### 3. MoE 不仅 GEMM 不同，路由与整理路径也不同

当前 base 日志选择 `vendor.metax`：topk_softmax、moe_align_block_size、invoke_fused_moe_triton_kernel、moe_sum。
当前 FlagOS 日志选择 `reference.torch`：topk_softmax、moe_align_block_size、moe_sum；GEMM invoke 仍为 `vendor.metax`。

当前 reference adapter 确实转到 Plugin 的 PyTorch reference：topk_softmax 组合 softmax/topk，moe_sum 使用 torch.sum。日志表示选择/初始化证据，不提供每层实际调用次数和占时；不能因为初始化日志里出现其他模型算子，就认定本模型执行了那些算子。

base 还开启 `VLLM020_MOE_EVEN_K_FASTPATH=1`，在 K 可整除 BLOCK_SIZE_K×SPLIT_K 时令 EVEN_KS=true，并有约 372 行 MoE 本地修改和 E256/N256/MetaX 配置文件。该模型 40 层 MoE、256 experts、top8 routing，因此值得核验每层重复的路由/整理/归约及 GEMM 成本，而非只看 full Attention。

结论：当前实现选择差异明确；reference 的相对性能必须实测，不按名称判定必然更慢。

2026-10-13 补充核验：`TritonExpertsFL.apply` 的当前 MetaX 非LoRA、无expert_map、FP16/BF16、SiLU、非上述量化路径（fused_moe_utils.py:363–408）直接调用完整库实现，优先 `fused_experts_with_workspace`，否则 `outplace_fused_experts`；随后立即 return。因此该路径不会执行后面的 Plugin staged `_moe_align_block_size` / `_moe_sum`，初始化的 reference 选择不能证明它们贡献了当前完整MoE路径的慢速。专家内排序/归约由库实现负责；外部路由 topk_softmax 需另行核验。这也进一步限制了用当前日志解释10月10日旧CSV的能力。

用户提出让Plugin直接调用公共 `fused_experts_impl`，由Gems做平台与shape分发。源码检查支持这个设计方向：`flaggems_vllm.__init__.py:33` 调用 `runtime.replace_customized_ops(globals())`，MetaX的ops导出fused_experts_impl；当前公共入口具备平台替换机制。应调用 `flaggems_vllm.fused_experts_impl`，避免公共Plugin模块依赖 `runtime.backend._metax` 私有目录。Plugin保留LoRA、量化契约、activation、layout、参数转换、output和workspace适配；MetaX的shape选择与kernel特化留在库中。简单 `output.copy_(...inplace=False)` 会重新分配库workspace并增加输出复制；若保留现有caller-buffer收益，须核验公共入口的out/workspace ABI，维持vLLM workspace角色交换与别名约束。库执行失败不应宽泛捕获后重试；旧库兼容在执行前按能力判断。

此补充为只读设计审查，源码SHA为 `5bb687951274c01d69b41391898cfc3a9991d0afb1a2d643fff6545af1b56532`（Plugin fused_moe_utils.py），尚未修改容器代码或完成新正确性/graph/性能验证。

后续用户明确要求实施该整理，执行情况单独记录在[公共MoE入口修改](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-moe-public-api/optimize/op-001-moe-public-api.md)。代码已修改，26项路由/契约、2项workspace别名和4项小形状硬件回归通过；服务未重启、端到端性能未测。本报告的历史性能数字及其测量身份不因此更新。

用户随后要求统一NV/MetaX调用层。当前代码已由[共享调用整理](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-moe-public-api/optimize/op-002-moe-unified-call.md)接替：保留通用workspace能力，两平台共享一次公共调用。删除复用的单token算子延迟退化25.79%，因此未删除；共享调用最终七组graph比较差异−0.149%到+0.125%，35项回归通过。NV硬件和模型端到端未测，服务仍未重启；历史gap不由这些算子结果重新归因。

### 4. Attention、调度和 graph 共同变化

| 项目 | base 当前服务 | FlagOS 当前服务 |
|---|---|---|
| attention_backend impl_id | vendor.metax | default.flagos |
| FlagOS Attention adapter | 未选中 | 当前源码导入 flaggems_vllm.flash_attn_varlen_func |
| max_num_batched_tokens | 8192，日志确认 | compile_ranges_endpoints=[2048]，实际预算仍需当前实例完整配置确认 |
| max_num_seqs | 显式 64 | 未显式指定，未补造实际默认值 |
| graph | FULL_DECODE_ONLY | FULL_AND_PIECEWISE |
| capture sizes | 1/2/4/8/16/24/32/40/48/56/64 | 相同列表 |
| contiguous single Prefill 环境变量 | 0 | 1；是否被当前选中 backend 消费未证明 |
| prefix caching | 关闭 | 关闭 |
| 设备组 | 4,5 | 6,7 |

两侧都有 FULL Decode 配置/capture；不能将 FlagOS 的较低吞吐解释为它只运行 eager。capture 日志不证明每个测量 step 的 replay。2048 与 8192 的预算差异会影响 Prefill chunk、请求准入及 Mixed 干扰，但 graph 模式不适合单凭名字判断谁更快。

模型 full Attention 每 rank 8 query heads / 1 KV head / head_dim256，是 GQA8；不能直接套用本项目 Qwen3.6-27B GQA6 的历史结论。当前 base KV cache 报告约 2179332 tokens、FlagOS 2037857 tokens；P4K/C64 每请求最多5120tokens，简单驻留总量327680tokens，不支持把 P4K gap 直接归为 KV 容量不足。混合状态池、碎片和抢占仍未采集。

## 软件身份和时间边界

实际包安装以 `/opt/conda/bin/python3.12` 的 metadata 为准；base 的系统 python3 看不到这些包，不能用其结果判定组件缺失。源码均是 editable 安装，除 FlagGems-vllm 在 base 不适用外，目录为 `/workspace/{vllm,vllm-plugin-FL,FlagGems,FlagGems-vllm}`。

| 组件 | base | FlagOS |
|---|---|---|
| vLLM | 0.20.2+empty；bc150f50299199599673614f80d12a196f377655，多文件已修改 | 相同 HEAD；fused_recurrent.py 已修改 |
| Plugin | 0.2.0+gd1653d9ff；d1653d9ff0450ce0366686bfcde5d8aecab44755，已修改 | 0.2.2rc2.post1+g8b059122e.d20261010；8b059122e32b9ac47b9820a9c7b1bb95077481a4，已修改 |
| FlagGems | 5.0.2；3123859968915e361e8452dd796dc6b27c956324，已修改 | metadata 5.4.0.dev588+gaf5291a06；当前 HEAD c6f46cc970ea0bef8927ee657c021bd8621e3bb0，干净 |
| FlagGems-vllm | 未安装 | 0.1.0；05d0ff0547dc9cc7cce18f47c6f57cc9d04f0777，已修改 |
| FlagTree | 0.5.1+metax3.0 | 0.7.0+metax.gitc39f1b1b |
| PyTorch | 2.8.0+metax3.7.0.7 | 相同 |

FlagOS FlagGems metadata 的 git 后缀与当前 HEAD 不同，采用当前 git/工作区事实，不把包版本后缀当作完整代码指纹。
mx-59 为 MetaX C550，驱动3.8.1、MACA3.7.1.5；检查时有其他设备运行任务，历史 GPU 时钟、4/5与6/7拓扑、CPU/带宽争用未冻结。硬件和共享负载仍为混杂。

两个容器共享 `/public-flash` 和 `/data` bind 映射，源码 `/workspace` 不在这两个 bind 中。容器镜像不同：

- base image ID：sha256:26050e208e6b5ca684a9e9daee9f0b41f6730a8df44438a133b492b75f84b0a8。
- FlagOS image ID：sha256:f7b2d280fd5ae061db1d66d9707273969c4c8c9508cd4167d0e15a9b8e2c4957。

## 下一步证伪顺序（未执行）

2026-10-13 后续证据更新：用户提供 `qwen36-35B-begin-novllmconfig-addattention-fusedmoeopt` 的 P1K/P4K 端到端 CSV，已在[共享调用实验的端到端复盘](../../../models/Qwen3.6-35B-A3B/metax/20261013-qwen36-35b-metax-moe-public-api/optimize/op-002-moe-unified-call.md)归档。相邻 addattention 对照的 SUMMARY 显示 P1K 吞吐 +14.71%、P4K −19.89%；两侧均存在慢轮，不能据此宣称稳定收益或归因为 buffer 复用。当前容器已发现相符服务，Agent 未重启它。另，本轮 `qwen36-35B-begin` 目录列出的文件已为 10-13 新测量，原报告引用的 10-10 文件未在当前列表；本报告原始数字/路径/SHA 保留其历史时点，不静默以新 CSV 替换旧基线。

1. 先保存历史身份缺口，在独立环境中对齐 benchmark 的显式采样参数、P4K workload、设备组、batch/seq预算、graph与缓存。机械增加 `--generation-config vllm` 会改变生成策略，只用于控制成本研究；业务目标若保留 top20/p0.95，就两侧都显式保留它。
2. 同一 FlagOS 源码/环境中，仅改变采样截断参数，测 TPOT/ITL 和 P4K Mixed；同时记录生成轨迹会改变的限制。若 gap 基本不变，降低采样候选优先级。
3. 固定采样后，对 GDN BV8/BV32 做目标 shape 正确性和 graph 下 microbenchmark，再回 P4K；不要直接复制 base 的大范围 vLLM 补丁。
4. 分别对 MoE 路由/整理/归约 backend、GEMM fastpath 做单变量测量，核验实际命中与非目标路径。
5. 最后单独比较 Attention backend，并采集覆盖两个 rank 的代表性 Prefill/Decode/Mixed trace。按需调用本地 Profiling Skill；Profiler-on 不作为正式收益。

新性能实验须先复刻独立优化容器，满足 image_lineage/mount_parity、正确性与服务门禁；本报告不是新测试的准入回执。当前历史差距可报告，但未签发性能/精度 gate，不部署或修改参数。

## 原始证据与校验

远端 Host：mx-59；路径根目录 `/public-flash/jinghao/qwen3.6-35B`。

| 路径（相对远端根目录） | SHA256 |
|---|---|
| start-model-base.sh | a9a7254ad5f7451277d822f5bdb8cd8ce16358571c9d62454f3064d9286d7480 |
| start-model-flagos.sh | ea722f727be33bb74acdd7d5347e4f8eecb47a6a190ec6495f6b8fbf7d92b232 |
| test/perf_test/vllm_perf.py | 0085fa60c9887cdabf0ca586a51aa952adebaea741b95b7af2e40cf31ec678ef |
| test/perf_test/benchmark_results/qwen36-base/qwen36-base_4096in_1024out_c64_n128_20261013_114116.csv | 9373d3925eb38e8ab5634ca3d9a211644f6aaa17707e6923048e88064608042b |
| test/perf_test/benchmark_results/qwen36-35B-begin/qwen36-35B-begin_4096in_1024out_c64_n128_20261010_164701.csv | 1e84514460698b185a36800246a390d0f08458c4f4157f278b0d0b223161ce4b |

服务日志为根目录 `service-base.log`（10-13启动）和 `service.log`（10-12启动）；当前客户端日志为 `test/perf_test/perf.log`，仅覆盖 base。日志可能继续追加，未赋不可变 SHA 或复制完整日志。关键源码 SHA：

- base topk_topp_sampler.py：e821fdb78e0a5e77efc0dd4638e78cd89b0aef5fcd142cfa202764cb4bba359a。
- FlagOS topk_topp_sampler.py：be6c3aa3ee35f4f03435a77653187028ceb0775c4100a1b23c905fea4505939f。
- base fused_recurrent.py：2096eae2949f88eb793add0a94035c0b8fe368fdd9aba053534e5f148acefcee。
- FlagOS fused_recurrent.py：5c21e23e2a4ffcc1b1c72544836c5f5a345ab8259d66006515b37bfd8e67bd36。
- FlagOS Plugin attention.py：235e9e6194bce868e1f6f41de79555b4791063eeca9b86b295cf80e3ac53f123。

精度状态、旧服务 graph replay、旧请求采样、稳态准入、独立服务重复与回退漂移均未证明。因此只给出诊断观察，不追认为正式验收。无新的单算子因果证据，不修订 SOP 或稳定算子知识。
