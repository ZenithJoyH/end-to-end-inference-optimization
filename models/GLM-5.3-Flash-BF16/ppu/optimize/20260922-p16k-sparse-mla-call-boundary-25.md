# 20260922-p16k-sparse-mla-call-boundary-25：Sparse MLA完整调用边界

## 方向与冻结范围

- 状态：`rejected/completed`；`operator/improve`，无服务启动、无源码变更。
- 父场景：`P16384/D1024/C64/N128`；当前保留组合继续是MBT32768。
- 目标：量化thead vendor Sparse MLA kernel、包装调用、launch/gap及邻接操作，判断
  是否还存在不同于点21 `out=`复用的完整调用机制。

## 假设与停止条件

点20中Sparse MLA占rank0 Prefill/Mixed设备活动27.9745%/29.2729%，仍是最大
热点；但P4K generic实现慢约20.8%，点21的输出复用只有0.999978x–1.000507x。
因此不再比较已证伪provider或buffer复用，而是先将现有trace中的CPU调用与设备
kernel按correlation/时序配对，分别量化纯kernel和可消除的调用边界成本。

若非kernel/邻接成本映射到完整采样窗口的乐观上限低于3%，或剩余成本属于vendor
kernel黑盒、主机同步、跨rank collective或无法在Plugin/FlagGems-vllm安全隔离的
路径，则立即停止，不建立候选。只有存在明确的完整调用机制且乐观上限超过3%，才
进入graph micro和最小回归。

## 证据边界

- 输入：点20已校验的16-rank trace，首轮只解析rank0 Prefill/Mixed/Decode。
- 活动时长可能重叠，只作乐观上界，不冒充关键路径收益。
- 过程脚本位于`/private/tmp`，执行副本归档到
  `commands/p16k-sparse-mla-call-boundary-25-20260922/`；不写本地`scripts/`。

## 当前结果

rank0中精确识别到1320次
`flash_sparse_prefill_fwd_kernel`和1320次`concat_and_cache_mla_kernel`；
Prefill/Mixed/Decode分别为11/352/942次，恰好对应每个execute marker 11层。
可见CPU包装只覆盖非graph的1个Prefill和32个Mixed marker；Decode graph replay
没有逐算子CPU wrapper，不能伪造补齐。

| 指标 | Prefill | Mixed | Decode |
|---|---:|---:|---:|
| Sparse MLA kernel / marker span | 27.0553% | 28.7462% | 5.9876% |
| concat/cache kernel / marker span | 0.0158% | 0.0151% | 0.0762% |
| attention CPU wrapper / marker span | 0.6115% | 0.3242% | 无逐算子wrapper |
| KV update CPU wrapper / marker span | 0.1271% | 0.0669% | 无逐算子wrapper |
| attention+KV CPU区间并集 / marker span | 0.7387% | 0.3911% | 0% |

三阶段device marker span合计103928472.489us，attention+KV wrapper区间并集
只有399132.231us。即使把inclusive CPU区间错误地全部视为串行关键路径并零成本
消除，完整采样窗口的乐观上限也仅0.3840451%，远低于3%。CPU区间与设备活动
可能重叠，所以这仍是高估。

`sparse_attn_indexer_kpool`在Prefill/Mixed的CPU inclusive时间较大，但它属于
前置indexer/MQA路径，不是Sparse MLA wrapper self-time；其设备热点和候选已在
点20单独分析，非对齐密集shape退化30.30%而拒绝。未把它重复计入本点收益。
剩余约28.7%的Mixed活动是thead vendor kernel本体：P4K已有generic完整调用慢
约20.8%的反证，点21的`out=`复用也只有0.999978x–1.000507x，当前仓库没有
可修改的vendor kernel实现或新的安全机制。

因此按冻结停止条件拒绝本点，不建立micro、不启动服务、不改源码。服务继续停止，
8011关闭。

## 原始证据

- 事务分解：`analysis/sparse-mla-call-boundary-25.json`，SHA256
  `84ec358500b8444b0c278d5bc5ace54e902c49cc07802d1d4a15b9e039f615d0`。
- 分析脚本SHA256：`c3fb5e8bb310d5c359869b462206088d84ff7b593821187a9c2420d91cb1b3d0`。
- 事件清单SHA256：`70418b0927f3db82e31b500014997394b49d6a7b2185593ee45889e4e4eb324a`。
- inventory脚本SHA256：`68ede46c9666674d8f87deeccb8098672b40640bd4e28cc5a767745cd968f1c4`。
