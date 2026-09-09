# MLA 长上下文候选分析

日期：2026-09-04。状态：observation，已取得 kernel profile，候选性能待测。

## 当前事实

- 独立 graph 基线进行 GPQA C32 时，生成吞吐随运行阶段由约 736–800 降至约 182 tokens/s；后一个观测点仍为 32 running、0 waiting、0 KV preemption。不同时间点的上下文分布不同，这不是同条件性能比较。
- Plugin revision f91f4ed08e1cfef0e0efe1380a7721928eccc033，FlagGems revision 5941cd2225798bdfa611626f34e459c42cdf2904。代码读取自隔离容器 xingchen4-e2e-20260904。
- Plugin 的 `vllm_fl/dispatch/backends/flaggems/impl/mla.py::forward_mqa` 调用 `flash_mla_with_kvcache`。模型 TP4 下每 rank 8 个 query head，latent KV 512 加 RoPE 64，BF16。
- FlagGems `src/flag_gems/fused/flash_mla_with_kvcache.py:1308` 的普通 dense dispatch 使用 BLOCK_H=64，grid=(ceil(heads/64), batch*seq_q)，没有上下文 split 维度。kernel 内遍历完整历史序列。TLE 分支另有 head 整除和 page size 等条件，尚未用运行 trace 证明实际分支。
- Plugin 返回的 output/lse 有 clone，源码说明与 graph replay 缓冲区复用有关；不能仅凭看见 clone 就删除。

## 假设与边界

如果当前请求命中上述普通 dense 路径，8 heads 的 padding 和缺少 sequence split 可能使长上下文并行度不足。当前证据只能支持候选排查，不能认定其是吞吐下降的根因，也没有证实更改有效。

按每 rank H=8，忽略 softmax、分页和重复加载，每层每请求 attention core 的计算量为 17408*S FLOPs，理想 KV 读取为 1152*S bytes，理想算术强度约 15.11 FLOP/byte。不能套用历史 DeepSeek H128 的硬件性能判断。

## 后续验证

1. 完成当前固定配置精度评测，冻结用户精度门槛，再收集目标 workload 的短 profile，确认真实 kernel 和占比。
2. 优先比较已有兼容的分块实现（operator/replace）；若无兼容实现，再研究 split-KV 与 online-softmax merge（operator/improve）。
3. 覆盖 batch 1/8/32/64、短长及非对齐上下文、分页边界、BF16 数值 reference、eager 和 graph capture/两次 replay。
4. 任何微基准收益必须返回同条件端到端 baseline/candidate/revert，多轮报告输出及总 token 吞吐；当前没有候选改动。

## 23:00 短 profile 证据与优先级更新

按照用户新指示，GPQA已暂缓。使用复制的 vllm_profile.py，P1024/D128/C64/N64，先一轮无采集预热，再调用native --profile；服务delay_iterations=30、max_iterations=10。两轮均64/64成功。不同于完整吞吐case，采集结果只用于归因。

四rank各21820条kernel事件；仅按cat=kernel且ph=X聚合，不混入CPU/CUDA runtime时间。

| Rank | kernel累计ms | MLA累计ms | MLA调用数 | MLA占比 | MoE占比 | mm_kernel_general占比 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 591.422 | 359.736 | 400 | 60.83% | 15.66% | 11.32% |
| 1 | 591.446 | 358.223 | 400 | 60.57% | 15.64% | 11.30% |
| 2 | 591.434 | 360.209 | 400 | 60.90% | 15.67% | 11.30% |
| 3 | 593.589 | 360.484 | 400 | 60.73% | 15.60% | 11.24% |

实际kernel名为 `_dense_decode_kernel`，400次与40层×10迭代相符，平均每次约0.9ms。mHC pre约4%，PCCL allreduce约1.8–2.3%。这支持优先验证MLA，而不是无证据改变batch预算。累计kernel时间不是严格的关键路径墙钟占比。

已核对TLE_DECODE_BH=64，H=8不满足TLE分支；另一个flash_mla接口不返回LSE、scale和平台分支也不同，没有可直接替换且已验证的实现。

当前首个实验归类operator/improve：只改变head tile 64→16，保持BLOCK_N=64、num_warps=8以及同一选定stage。保留FP32 reference、混合长度和非对齐分页、eager、graph capture及replay检查。微基准运行时暂停新服务，避免设备竞争；原服务仍运行。

原始trace目录：新容器 `/workspace/e2e-artifacts/profiles-profile-decode-v2/`，4个rank的pt.trace.json.gz及profiler_out文本。驱动与结果目录 `/workspace/e2e-artifacts/profile-decode-p1024-v2/`。微基准工具保存在模型/平台的 `optimize/tools/mla_tile_bench.py`，完整输出留在目标环境，不提交trace。

参考技能：本项目 key-operator-analysis 的 operator-analysis-method.md、knowledge-index.md、MLA README。历史文档仅用于方法，当前实现事实以上述 revision 为准。
