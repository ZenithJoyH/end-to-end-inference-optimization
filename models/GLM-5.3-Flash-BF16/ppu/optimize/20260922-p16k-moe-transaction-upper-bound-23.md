# 20260922-p16k-moe-transaction-upper-bound-23：P16K MoE完整交易上界

## 方向与冻结范围

- 状态：`rejected/completed`；`operator/improve`，无源码变更。
- 父场景：`P16384/D1024/C64/N128`；TP16/BF16/max-seqs64/MBT32768/
  FULL_DECODE_ONLY/前缀缓存关闭。
- 当前保留组合不变；服务停止，本点首轮不启动服务。

## 规划复盘与可证伪假设

`planning_review_p16k_05`覆盖点20–22。三项均已拒绝：MQA在非对齐密集
边界退化30.30%；Sparse MLA `out=`复用约1.00×；exact-M32768 GEMM2虽然
源码命中微基准为1.072917×，但P16K/D128 fresh A/B/R只有+0.0198%。
当前组合的同完整workload证据仍是点19的434.205→474.526 output tok/s
（+9.286%，performance-only），不与任何micro比率相加。

点22证明单独调一个GEMM2 tile的可兑现收益已被完整MoE交易及其他热点
稀释。因此本点不继续扫更多tile，而是从点20现有rank0 trace分解完整MoE链路：

1. 在Prefill/Mixed/Decode中分别统计alignment/sort、GEMM1、activation、GEMM2、
   reduction/sum、collective与不可分类间隙；同时保留调用次数和已知live M。
2. 计算两个乐观代理：消除单一组件的上界，以及将可融合链路加速到
   一个明确比率时的Amdahl上界。device活动可重叠，所以只能称上界代理，
   不冒充关键路径收益。
3. 只有一个“完整调用机制”的乐观端到端代理超过3%，且不依赖
   vLLM修改、主机同步或无法验证的跨rank假设时，才建立完整调用micro。
4. 若乐观代理本身就低于3%，或不能从trace分离可消除的完整调用成本，
   立即停止本点，不写生产源码。

## 证据与边界

- 使用点20已校验的16-rank trace，首轮只解析rank0已分阶段事件；若需要全rank
  关键路径才能决策，返回Profiling Skill，不伪造排他耗时。
- 点20的rank0设备活动：Prefill/Mixed/Decode fused MoE为
  20.1812%/19.6521%/41.2481%；large-M主GEMM为11.4820%/11.7378%/—。
- 点22的新live shape是Mixed `M32768/H4096`共1302次；`M16384`和`M17377`继续作边界。
- 过程脚本只在`/private/tmp`生成，执行副本保存到远端
  `commands/p16k-moe-transaction-upper-bound-23-20260922/`；不写本地`/scripts`。

## 当前结果

rank0的5040次完整MoE设备调用均被无歧义配对：Prefill 42、Mixed 1343、
Decode 3594，且每次都是同stream上的routing、四阶段align、GEMM1、独立
SiLU、GEMM2和`moe_sum`；配对异常为0。两个`fused_moe_kernel`按
`moe_sum`前的时序分别归为GEMM1/GEMM2，只把两者之间的SiLU计入MoE激活，
没有把模型其余激活或普通GEMM混入。

| rank0设备活动占比 | Prefill | Mixed | Decode |
|---|---:|---:|---:|
| routing | 0.3377% | 0.3445% | 0.9243% |
| alignment | 0.2042% | 0.1337% | 6.1904% |
| GEMM1 | 10.4275% | 10.1614% | 23.5515% |
| 激活 | 0.1718% | 0.1778% | 0.2458% |
| GEMM2 | 9.7536% | 9.4907% | 17.6966% |
| reduction/sum | 1.4775% | 1.5490% | 0.2901% |
| 完整可归类MoE链路 | 22.3723% | 21.8571% | 48.8987% |
| 非GEMM部分 | 2.1912% | 2.2050% | 7.6506% |

三阶段GPU marker span合计103928472.489us。即使把所有routing、align、激活和
sum都当成串行关键路径并完全消除，完整采样窗口的乐观上限也只有2.3367203%。
进一步作更不现实的上界：把点22源码命中微基准的1.0729165954x同时应用到
Prefill/Mixed/Decode的全部GEMM2 shape，可再节省0.6511231%；两者合计
2.9878434%，仍低于预冻结3%门槛。实际点22只覆盖exact-M32768，服务兑现仅
+0.0198%，因此这个合并上界有意高估而非低估收益。

Decode alignment单阶段虽占6.1904%，但Decode marker span只占本次完整采样窗口
的一小部分；而且相同small-M stage2机制此前已得到3.635x源码路径加速、端到端
却为-1.308%并回退。当前源码还明确记录：large-M融合SiLU的GEMM1历史慢
11%–20%；direct-sum因PPU atomic add约慢9x而被禁用。这些反证排除了当前
范围内可兑现的完整调用机制。PCCL collective位于该FlagGems-vllm调用之外，
无法从本trace排他归入每次MoE，且既有协议对照均更慢，未把它伪装成可融合成本。

因此按预冻结停止条件拒绝本点，不建立micro、不启动服务、不运行精度或端到端
性能测试，也不修改交付脚本。FlagGems-vllm生产源SHA仍为
`f70ff827bc1bce13fc42ca05ac7dd11e28ffd83745aee9808f0715ac7b9baa66`；
服务保持停止，8011关闭。

## 原始证据

- 分解结果：`analysis/moe-transaction-upper-bound-23.json`，SHA256
  `bf9ea4bbbb6049d9f6e6a4d13ef0e66853774918e0e4334cc0a6a02b167bcce3`。
- 分析脚本：`commands/p16k-moe-transaction-upper-bound-23-20260922/analyze_moe_transaction.py`，
  SHA256 `2a67dadc186cac944fdd461348cbfc1d1dbea061c9a97cff294e59ef24101982`。
- 事件清单：`analysis/moe-event-inventory-23.json`，SHA256
  `8959ae316684ffede8313119dee8aed75fdd5564e1d146793c4dff3449395d1e`。
- 冻结契约SHA256：`1ecaa1645c4bd0a411f4896003a2cad3acfb6151d540dd9e01d105e90b4c6408`。
