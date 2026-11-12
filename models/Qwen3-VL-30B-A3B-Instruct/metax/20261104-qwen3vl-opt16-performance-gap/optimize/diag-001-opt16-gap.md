# diag-001-opt16-gap：opt16 已有端到端结果只读诊断

- 状态：只读分析完成；根因占比与正式比较 **incomplete**。未实施优化、未新增请求/benchmark/profile、未停重启服务、未改源码或缓存。
- 当前 Host：mx-59；容器 qwen3vl；qwen3vl-opt16/8030、GPU0/1 TP2 BF16。截止 2026-11-04T23:03:44.822756+08:00。
- 目标：分析用户现有结果差距；P1K为优先问题，阶段覆盖 Prefill/Decode/Mixed。
- 方法：读取本地 inference-performance-evaluation 与规划 Skill；本次仅审计已有结果，不冒充一次新 Skill 测量。无新 baseline/candidate/revert 或精度 gate。

## 优化方向与瓶颈依据

主比较固定整个 opt15 版本，不逐场景挑最好结果；opt10仅作另一历史整组参照。CSV中四轮均成功128请求、输入P×128与输出131072 token一致；SUMMARY按脚本预设取第3/4轮算术平均，保留前两轮，未事后丢弃数据。

| 输入 / D1K C64 N128 | opt15总token/s | opt16总token/s | 变化 | 中位ITL ms |
|---|---:|---:|---:|---:|
| 1K | 3181.19 | 2061.18 | -35.21% | 37.03 → 38.80 |
| 4K | 5621.01 | 5432.63 | -3.35% | 43.19 → 45.32 |
| 16K | 6499.96 | 6363.50 | -2.10% | 47.75 → 49.91 |
| 32K | 6013.93 | 5817.90 | -3.26% | 38.09 → 40.98 |

P1K耗时82.41→127.41s（+54.61%），mean TTFT1626.23→2688.43ms、mean TPOT38.63→49.94ms。中位ITL仅37.03→38.80ms，不能把总吞吐-35.21%解释为每个decode kernel都慢35%。当前P1K第3/4轮总吞吐2148.39/1973.97，差幅8.46%；opt15为3154.17/3208.22，差幅1.70%。首轮冷启动153.47s不作为默认稳态优化目标，但后两轮仍缺少稳定准入证据。

相对已确认稳态的opt10：P1K -31.80%，P4K +0.40%，P16K -0.09%，P32K +0.32%。长输入没有出现与P1K同量级的普遍回退。P32K现已完整4轮；P64K尚无结果，不能宣布五场景完成。

三阶段视图：Prefill以客户端TTFT为代理，P4K/P16K/P32K相对opt15只高约1.7/1.9/3.4%；Decode常见ITL仍有小差距（P1K/P4K/P16K约4.5–4.9%，P32K7.6%）；Mixed中P1K的长停顿放大总耗时。TTFT/ITL包含调度、排队和客户端开销，不是纯设备时间。

## 优化内容与适用边界

**本轮无修改。最强假设是实际采样形状预热覆盖不足。** 当前vLLM0.24 benchmark未传temperature/top-p/top-k，默认temperature=None，并非强制greedy；服务实际generation config是T.7/P.8/K20，因此走真实采样过滤。prefix cache当前OFF（--no-enable-prefix-caching），不得沿用历史精度任务的prefixON描述本次性能服务。

启动graph完成不等于采样路径全热。容器私有cache实际记录：启动期新模板M64/top-k int64；真实请求之后生成M1..64/top-k int32。benchmark21:03:14开始后出现62个hist、992个guarded_sweep、64个extract、63个find_first_keep缓存元数据；实际int32模板生成范围21:03:52至21:23:53。来源定位到当前MetaX top_k_top_p及FlagGems sort。这是编译缓存个数，**不是kernel执行次数或编译秒数**；无时间对齐trace，不能把全部45秒差距定量归给JIT。NFS文件mtime与log时钟约差225.6s，不将具体事件硬分到Run3/4。

**另一真实新增工作是out-of-place全logits拷贝。** 旧API apply_top_k_top_p原地过滤，新API top_k_top_p为了输入保持先clone。M64/V151936/FP32约37.1MiB/调用；实际耗时未测，不能直接等同于ITL差距。逐函数AST比较：M>1排序辅助函数不变，只_sorted_values增加M1快路；PR1069的主要特化针对M1，不能据组件M1收益预期C64模型整体变快。后续若做优化，可评估将输入拷贝融合到输出mask写入，必须保持out-of-place、过滤语义与错误传播；当前未实施。

## 正确性与路径命中

Attention文件仍f81（原paged/default split0，PR638已回退），与旧opt15记录一致；FlagGems sort、vLLM原Sampler/TopK模块SHA也相同。主线MetaX MoE kernel AST与旧调优数值路径相同的既有审计保留；当前模型quantization=None/BF16，通用INT8大stride修复不是该BF16路径的新增热计算，不能据这次性能下降就归责该修复。

当前env与两个worker证明FlagGems-vllm启用；采样IR缓存source指向真实导入文件。oplist未单列TopK不是未命中的反证。当前startup有graph capture，未新增运行期profile/replay计数或模型精度评测；既有组件正确性不能当本次完整模型gate。

## 性能效果与可比性

以上全部是已有CSV观察，不是同机受控因果收益。opt10旧GPU6/7与当前0/1不同；opt15历史源码快照可核对关键路径，但CSV没有精确绑定其性能进程/Host/参数/权重全字节身份。当前与历史默认采样无request seed，批轨迹和NUMA/宿主负载也未冻结。当前GPU0/1未见其他GPU进程共用，不能因此宣称无共享CPU/带宽影响。

## 决定、风险与回退

保留当前用户运行服务及测试，零远端变更，无需回退。本轮诊断不签发性能/精度gate，不改PR或容器代码。

规划复盘 plan-opt16-gap-001-20261104：优先在当前矩阵自然结束后，另冻结同源同卡P1K预热/稳态证伪；覆盖真实M1..64及K dtype，再一遍无新编译元数据，预先固定三轮/差幅≤5%的新准入规则，全部测量保留。该规则是**下一次建议**，不追溯改判旧数据。若热态仍有差距，JIT-only解释被否证，再针对全过滤API的clone/mask与实际decode做窄profile/对照。最后才用同硬件B/C/R隔离设备/NUMA因素。不得在当前正在跑的矩阵里插入预热或修改配置。

## 外部证据

用户原路径：/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt16；opt15/opt10同级。当前opt16文件后缀20261104_210314，历史opt15后缀20261029_103926，opt10 P1K取用户确认的20261022_091827，其余20261021_150247。

服务log/cache：容器qwen3vl内/tmp/qwen-vl（日志与triton_cache）；源代码/workspace/FlagGems-vllm、/workspace/FlagGems、/workspace/vllm-plugin-FL。当前元数据/只读脚本及计算临时保存在本地/tmp/qwen3vl-opt16-gap-20261104；没有为分析创建新远端任务目录或写文件，远端CSV/log/cache未动。各路径SHA与命令SHA见state.yml；这些是临时采集快照，不保证长期/tmp留存，主要原始证据仍为远端用户产物。

- opt16 P1024：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt16/qwen3vl-opt16_1024in_1024out_c64_n128_20261104_210314.csv` SHA256 `2b153e0585e2e37b13d640094c99e06419812e4ba05784c2d61904d546f50ca1`；opt15：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt15/qwen3vl-opt15_1024in_1024out_c64_n128_20261029_103926.csv` SHA256 `974c1a0c1f74d545633363d061ab98dff7e0147d078fee8014104c235e7c9f5f`。
- opt16 P16384：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt16/qwen3vl-opt16_16384in_1024out_c64_n128_20261104_210314.csv` SHA256 `fcf66eeec81e41097f9fa31defb48cc1dc769904b80a8568980dc3143e833b72`；opt15：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt15/qwen3vl-opt15_16384in_1024out_c64_n128_20261029_103926.csv` SHA256 `30821997b3f1bbc9a2fd5c53e012a5f58be22ec834caa59e5a02c7effaad972c`。
- opt16 P32768：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt16/qwen3vl-opt16_32768in_1024out_c64_n128_20261104_210314.csv` SHA256 `debf2ff448d2500ffcfd18f96f3984e10d76926980e1615f936e05bf76667f8f`；opt15：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt15/qwen3vl-opt15_32768in_1024out_c64_n128_20261029_103926.csv` SHA256 `2f019ca774e7babf3153322383affb2b888e04d61ea6316ccb6761ec1ba66f31`。
- opt16 P4096：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt16/qwen3vl-opt16_4096in_1024out_c64_n128_20261104_210314.csv` SHA256 `86543e938f4f8078d22143475681fb0a7e2add66db489933963bc0a9848559a1`；opt15：`/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt15/qwen3vl-opt15_4096in_1024out_c64_n128_20261029_103926.csv` SHA256 `f042e02e4a3885b75684a786fdd84121001f4e3997deb2d0ecda003a687150e5`。

当前关键源码SHA：

- Attention: `f81fa552667b3ed98d1cf141d2dee33ba10476cda9a997744495bdbc36289ef2`
- FlagGems_sort: `06208cc0d074bd5a38a9ed84afa5870ccbea062fe3d244a1b438c2dc5df2e184`
- native_sampler: `1a2f18ddc91c89f3744ab5a93624be056bf20b7a8b2e6e13d0236182718a2253`
- 新MetaX TopK: `0f3f4eeb160032a6832e0ac214e947bb9fe435570f4de22eb1791f63d4befbb4`；旧: `941bdc544401872327ee299aa0ab73387b43893e363f8c25b465fb607eb551eb`。
