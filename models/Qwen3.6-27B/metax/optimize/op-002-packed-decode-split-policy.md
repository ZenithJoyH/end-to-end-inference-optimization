# OP002：Packed Decode 的 Split-KV 拆分策略

状态：终态 rejected_no_source_change；拆分单变量未过晋级，负结果与后续组合回退均已保留。用户要求继续开启 FlagGems Flash Attention 的性能优化，本实验属于当前有界诊断范围，正式精度失败记录保留。

双 rank 当前 trace 已按 Plugin Worker 的 `execute_new_N_cached_M` GPU 范围切分；Decode 55 次迭代、880 次 partial/merge，FA 约占 kernel activity 11.9%。Prefill 与 Mixed 分别约3.5%/4.0%，主成本是 GEMM/通信。该占比不是关键路径时间或端到端收益。当前 Decode grid 为 `[16,64,2]`，实际上下文约1K，但主机调度使用模型上限262144。

假设：降低拆分数可减少 CTA 波次、局部结果和 merge 成本。先在独立微基准进程比较 auto/2/4/8/16，服务和源码保持当前 OP001。计时包含 public API 的 packing/layout/copy/partial/merge，CUDA Graph 5组×40次 replay，正反顺序交替。BF16、页784、Q12/KV2/D256，B1/16/64 × KV1024/4096/16384；FP32 分组矩阵乘法和 softmax 为独立 oracle，atol0.002/rtol0.02。

预冻结晋级条件：B64/K1K 完整调用延迟下降至少15%，B16/B64 的4K/16K退化不超过5%，全部数值检查通过。否则保存负结果、不修改运行服务。通过后才选择基于支持条件的窄 guard，并验证 C8/graph、同契约 Mixed baseline/candidate/revert 与阶段守护项；正式50000 GPQA 及四场景验收另行进行。

GPU 探针仅在18002无排队/运行请求时串行执行，使用优化容器2/3卡中的2卡；不操作源8002。完整原始结果位于远程 `results/op002-split-probe.json`。

执行前脚本：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/op002-split-probe.py`，SHA256 `9401b7d48f55dd0f31f164d6c08b06cb4d9e5bfed76e832e7cc37e0dbc294dae`。

首次探针在首矩阵等待362秒、0测量结果，目标GPU空闲；精确停止微基准PID，服务保持运行。原结果标为incomplete保留。仅进行一次带阶段日志/堆栈的定位版本：参考计算放在CPU FP32、客户端OMP/MKL/torch线程数1；全部GPU graph计时条件/比较variant保持一致。尚不把等待归因到Flash Attention。

终态：独占GPU2后全部9矩阵×5variant=45项FP32检查通过，最大绝对误差0.001021。B64/K1K auto16=0.307462ms，8split=0.277722ms（延迟降9.67%），未达冻结15%；B16/K4K和16K的8split分别退化约22%/27.8%。OP002不晋级、不修改源码/服务策略，也没有候选端到端收益。原始终态SHA94364268aec763f34a5763bb48843a8159e9785d4883b3d596fae265e09d6ad7。

新增理解：模型maxK不等于实际K的事实不足以支持少拆分；小batch依赖更多split填充SM。服务与独立graph进程并存的MACA queue创建超时在停止本任务服务后消失，支持资源冲突解释，不能归因FA数值。后续微基准先独占目标GPU；原失败尝试全部保留。规划rev004保持OP001，仅新增一个KV tile变量实验，服务恢复后仍需真实E2E比较。

周期收尾：实际模型kernel页16、逻辑页784，原页784 micro仅为独立算子矩阵；[组合001](combo-001-fa-splits-warps.md)已按真实页16验证但Mixed未完成，精确回退OP001并完成三阶段对照。没有新增保留的E2E收益，正式50000精度仍失败。
