# diag-014：opt4 与回退后的 opt6 性能差距

本轮只读分析，未修改代码、配置、黑名单或启动脚本，未重启服务、发送测试请求或争用用户正在测试的GPU。当前用户8111已重启为qwen3vl-opt6；旧diag013 R服务身份仅为历史。正式精度按用户要求暂缓。

## 已确认的现象

同为D1024/C64/N128，原CSV汇总采用第2、3轮；下表沿用此口径，同时保留全部三轮，不把首轮删除后追认为正式稳态门禁。opt4另有N64且带profile的文件，不能混入。

| 场景 | opt4三轮TPS | opt6三轮TPS | 原SUMMARY opt4→opt6 | 变化 |
|---|---|---|---|---|
| P4K | 923.14/982.34/988.57 | 847.09/903.75/897.56 | 985.46→900.65 | -8.61% |
| P16K | 352.15/355.53/353.67 | 329.95/330.83/332.15 | 354.60→331.49 | -6.52% |

所有已完成轮次128成功、输出131072token；P4后两轮差幅约0.63%/0.69%，P16约0.52%/0.40%，下降持续存在，不只冷首轮。opt6 P64仍在运行，尚无完整CSV，不能签发其差异。

P4平均TTFT增加19.28%、平均TPOT增加8.82%、P99ITL增加20.42%；P16分别增加9.96%、11.77%、15.12%。TTFT/TPOT是包含排队、调度、采样和重算的客户端代理，不是纯设备阶段时间。

## 最明确的回归检查点：MoE配置语义改变

opt4提供文件的起点是2026-10-16 11:33；旧Plugin备份及原代码SHA可回溯。15:09换到024plugin-opt/08da21c，15:36用户将FlagGems从9beec738+sort补丁换到gems-opt/c3c5f5ab。随后PR595完整表替换旧57项stage覆盖。因此opt4→opt6不是只切换一次采样调用。

旧表SHA ad5bf196af20be5f9bb2916527a9fd061172e7fbbc93ed329a3e925758654261，只在精确M8..64覆盖GEMM2的num_stages=1，其他字段保留默认选参，is_embedded=False。新PR595表SHA ec38e926b545f76888b4d4a1775405df422b6d66ba5a4659203090c4a6073ffa，按最近M选择完整配置并用于两个GEMM；命中后is_embedded=True，原默认按阶段fast-path选参不再执行。当前目录和新JSON已经生效，问题并非目录未加载。

| M64 / GEMM2 | 旧选择 | 当前选择 |
|---|---|---|
| BLOCK_SIZE_M | 16 | 16 |
| BLOCK_SIZE_N | 64 | 128 |
| BLOCK_SIZE_K | 128 | 32 |
| GROUP_SIZE_M | 1 | 4 |
| num_warps | 4 | 2 |
| num_stages | 1 | 3 |

两个版本的原函数AST已在CPU重放，未导入torch或启动GPU。共享内存用64/96/128KiB分支假设，不冒充硬件查询；M64上述结果在三种假设下相同。Prefill M4096/8192也改变：例如旧GEMM2 BN256/warps8/group2变为当前M8192 BN128/warps4/group8；旧大M的stage/paired标志依赖共享内存，不能无硬件事实宣称已启用paired。

已找回与opt4历史审计一致的原始MoE源码SHA575e94b132f2e62faa36c06ed5c11519161142a80f13bde156041d9ac5911716。5个Triton kernel AST与当前完全相同，计算体仅移除了config_dir参数及传递；中间目录参数改环境变量的快照有既有155232组配置等价证据。当前变化集中在get_moe_configs/try_get_optimal_moe_config。

注意：direct_sum阈值在两版均为1<<60，本场景都不启用，不能列作退化原因。SiLU计算融合也不能因为is_embedded=True就笼统声称被关闭。被绕过的是默认per-stage fast配置选择。

这证明旧MoE调优没有原样保留，是优先回归点；没有单变量GPU/端到端对照，尚不能把全部8.61%/6.52%精确归给它。JSON格式兼容不代表选参范围、阶段和执行策略等价。

## 已排查与结论边界

采样文件与当前Plugin HEAD一致，调用原PyTorch参考入口；opt6启动后未出现新库采样缓存产物。opt6的900.65TPS也接近此前受控参考路径902.13，但不同服务/seed的数值接近仅作一致性支持，不是新的因果比较。

sort源码SHA06208cc0d074bd5a38a9ed84afa5870ccbea062fe3d244a1b438c2dc5df2e184一致，int32优化保留。模型config/generation_config/权重索引SHA与历史相同，默认temperature0.7/top_k20/top_p0.8；未重新哈希全部权重。vLLM仍为ee0da84ab，无本轮源修改。

Plugin分支还将MoE路由topk_softmax从FlagGems切到FlagGems-vllm；两者kernel与launch相同，仅日志文本不同，不能因为仓库变了就归因为算法退化。FlagGems整体版本及Plugin其他改动仍是后续排查变量，未做独立消融，不擅自回退用户指定gems-opt。

当前参数为TP2/BF16/8192batchedtokens/maxseq64/FULL_AND_PIECEWISE64/memory0.91/prefixcache关闭，KV562992。P4最多64*(4096+1024)=327680tokens，不接近容量上限。历史0.90审计对应09:37那份已不同名的CSV，不适用于本次11:33结果。当前全进程累计抢占18，不能直接分配给某一轮P16/P64；P64第一轮在途时该计数未增加的单点亦不替代完整轮次差值。

旧N64 profiler文本与双rank trace已定位，仅作历史kernel符号和调查线索。未将累计kernel活动之和当关键路径占比，未将profile轮计入N128性能，也没有生成当前opt6匹配trace。

## 下一步证伪实验

先让用户当前测试完成。保持采样参考路径、gems-opt、sort、黑名单及其他参数，只切换旧/新MoE选参行为；先做完整MoE最小数值与生产graph，随后P4K/D1K/C64/N128同契约无profiler B/C/R。预热规则先冻结，保留全部准入测量，核验旧配置真正命中。收益阈值2%、延迟守护10%、波动/漂移8%；不达标即保留负结果，不靠关闭FlagGems或回退整个版本掩盖。必要时再沿Plugin/ATen变化和匹配phase trace分解剩余差额。此实验尚未执行，不声称已恢复性能。

## 证据

远端案例根目录：/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3。原始用户CSV保持原目录；新脚本/筛选后源码快照位于commands/diag014-opt4-opt6-20261017。

- 只读分析：/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/diag014-analysis01.json；SHA256 0f30eca5e90965118d03834a2dd91e329e8c8442393c634fa22f2b66f7ec8ba7。

- 原始opt4源码溯源：/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/results/diag014-lineage01.json；SHA256 ab51f4652e19056636be3d90aa23b5fba4c7b479c5313976b58cdde0dccd3e3e。

- 证据索引：/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3/commands/diag014-opt4-opt6-20261017/evidence-index-v2.json；SHA256 4de28f0b106290cae145cb67020b4c80b81484856c253aa51e48574da23b29dd。
