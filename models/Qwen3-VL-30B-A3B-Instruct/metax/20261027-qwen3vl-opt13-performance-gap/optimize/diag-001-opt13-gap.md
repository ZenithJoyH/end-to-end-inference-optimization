# diag-001：opt13 与历史 opt10 的已有性能数据对照

状态：只读诊断进行中。用户要求解释现有 opt13 与历史最佳版本的差距；不修改源码、启动参数或服务，不发新压测或生成请求。历史数据来自 mx-59，当前运行事实来自 mx-104，跨 Host 的差额只能作为现象，不能当作单变量代码收益。

使用项目 inference-performance-evaluation 方法核验已有 CSV 的 workload/成功数/计量口径，使用 inference-optimization-planning 复盘阶段差异。本次不是新性能测量，不签发正式性能或精度验收。

稳定实验 ID：diag-001-opt13-gap；复盘 ID：plan-opt13-gap-20261027。当前用户压测仍运行，服务保留。

## 证据与执行边界

用户数据根：/public-flash/jinghao/qwen3-VL/test/perf_test/benchmark_results/qwen3vl-opt13。
历史对照：qwen3vl-opt10，P1K 使用用户已确认稳态的 20261022_091827 四轮复测，其余采用 20261021_150247；不选历史单轮峰值。

外部新归档根：/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-opt13-performance-gap。
拟执行采集器：commands/collect_existing.py，SHA `5c4042aad62853e16eb72082222804a4b14b2a9c56af8917433c63f038601054`；仅复制既有 CSV 到新目录、记录 SHA、读当前配置/缓存和源码指纹，生成 results/existing-results-analysis.json。它不是 benchmark runner，不运行 GPU 算子，不遍历权重，不保存敏感环境信息。

远端根已核对真实路径、owner/权限、新子目录不存在及可用空间约 15TB；新目录只由此脚本保存本实验产物，拒绝覆盖。

## 初步事实

- opt13 与 opt10 均为 P/D/C/N=对应输入/1024/64/128，prefix cache OFF，TP2，batch token8192、seq64、显存比例0.91、FULL_AND_PIECEWISE/capture64。
- 当前 Attention 文件与 PR #638 精确相同、decode 不显式传 num_splits（默认0）；不是旧 split1 的性能回退。
- 现有采样实现 SHA941bdc…、Plugin sampler SHA c621c7…、FlagGems c3c5f5…与历史保留实现相同。
- 当前 PR #943 按模型拆分 helper 的新提交97da71f尚未部署，不能解释已产生的 opt13 结果。
- P1K 测量时间窗内发现 sort/sampling Triton metadata 新写入；最终计数和时间范围由归档脚本冻结。不能由缓存写入时间精确计算暂停时间或断言没有其他编译来源。
- P16K 后几轮的差距稳定，优先检查 Prefill/Mixed，不能只用首轮编译解释。

## 正确性与回退

没有新的 GPU/graph/模型正确性验证，没有对当前 opt13 绑定旧精度 gate。未作任何服务/源码变更，因此无回退操作。

## 性能效果与阶段视图

数据截止：2026-10-27，opt13 P1K/P4K/P16K 已完成四轮，P32K 正在执行、P64K 未完成。本表是原 CSV 的 SUMMARY（固定四轮、跳过前两轮、Run3/4 算术均值），不是本次重新选择测量轮。归档保留 opt10–13 所有已存在的逐轮结果；该 SUMMARY 规则并不自动证明当前服务已经稳态。

| P/D，C64/N128 | opt10 总 tok/s | opt13 总 tok/s | 差额 | opt10 输出 tok/s | opt13 输出 tok/s |
|---|---:|---:|---:|---:|---:|
| 1024/1024 | 3022.26 | 2316.93 | -23.3378% | 1511.12 | 1158.46 |
| 4096/1024 | 5410.82 | 5516.31 | +1.9496% | 1082.16 | 1103.26 |
| 16384/1024 | 6369.18 | 4804.64 | -24.5642% | 374.66 | 282.62 |

所有既有行均成功128，aggregate 输入/输出 token 数符合 P*128 和1024*128；未发现总量或吞吐口径变化。没有逐条原生 JSON，不能由总量正确进一步证明逐请求长度或采样 payload 全同。

- **P1K Prefill/Decode/Mixed**：MeanTTFT1694.59→2940.14ms；MeanTPOT40.68→45.67ms；MedianITL38.80→36.92ms，P99ITL42.18→40.08ms。常见 token 间隔更短，但平均与整轮耗时更高，整轮86.74→113.25秒。四轮总吞吐2197.72/2266.33/2244.82/2389.03，后两轮差幅约6.23%；历史稳态四轮3011.30/3039.13/3044.21/3000.31，全轮差幅1.4511%。当前性能损失集中在请求进入/长尾/停顿；没有逐请求 ITL 数组，不能量化各类停顿占比。
- **P1K 编译证据**：实际 TRITON_CACHE_DIR 下，在文件名起始时间14:04:53至保守截点14:12:06之间，新写384个 `_guarded_sweep` 和8个 `reduce_then_scan_root_scan_kernel_row` kernel metadata（不计 `__grp__` 文件）。其中14:10之后仍有写入；代表 `_guarded_sweep.source` 明确指向当前 FGV top_k_top_p.py 和 FG sort.py，包含 M62/vocab151936 特化。这支持动态采样 shape 预热不全/后续 JIT 的解释；缓存写入本身不等于该段全部时间都被编译阻塞，也不能由聚合 CSV 精确归属到每一轮。
- **时间戳限制**：新归档 JSON 内主机 observed_at_utc=07:20:46.753，而写入后的共享盘 mtime=07:17:07.851，相差约220秒（含短暂采集耗时）。NFS mtime 不能与本机 `/tmp` kernel mtime 直接当成精确同钟测量边界。上述缓存窗口仅作为 P1K 内保守子窗口，不是精确完整时窗，不能据此分配 Run3/4 的编译耗时。该补充纠正原始采集 JSON 中窗口字段可能造成的过强解读；保留原 JSON 不覆盖。
- **P4K**：总吞吐约+1.95%，TPOT54.27→52.91ms，中位ITL45.58→42.96ms；没有全场景一致退化。
- **P16K Prefill/Decode/Mixed**：TTFT75029.02→105108.36ms（+40.09%），TPOT79.66→102.88ms（+29.15%），P99ITL642.51→1432.66ms（+122.98%）；MedianITL49.52→48.31ms。后3轮总吞吐4849.93/4803.08/4806.20，差距较稳定；首先是长 Prefill 与 Mixed 干扰问题，不能仅以首轮编译或稳态 Decode kernel 普遍变慢解释。TTFT/TPOT仍是含排队、调度和通信的客户端代理，不是纯设备阶段时间。

## 版本差异与已排除项

| 项目 | 历史 opt10 | 当前 opt13 | 判断 |
|---|---|---|---|
| Decode KV splits | vendor 默认0 | vendor 默认0 | 不是旧 fixed1 回退 |
| prefix cache | OFF | OFF | 本次不是开关差异 |
| TP/batch/seq/mem/graph | 2/8192/64/.91/FULL_AND_PIECEWISE64 | 相同 | 主要启动参数未变 |
| FG gems-opt | c3c5f5ab2 | c3c5f5ab2 | 保留 |
| FGV sampler | SHA941bdc5444… | 相同 | 局部直方图补丁保留 |
| Plugin sampler | SHAc621c7e0f4… | 相同 | 适配保留 |
| Attention Prefill | 原 paged KV 路径 | PR638：单 prefill、KV>=2048、无量化时 gather K/V，再走 contiguous varlen | 明确新增路径，贡献待消融 |
| FGV MoE | faeeead699… | bbc2eddedc…，含上游977后的代码 | 代码变化，性能贡献未隔离 |
| 机器/设备 | mx-59 GPU6/7 | mx-104 GPU0/1 | 跨 Host 混杂因素 |
| 权重目录 | /public-flash/models | /data/models | 用户授权迁移；无旧全字节 SHA，不能声称全字节绑定 |

当前服务日志14:16:20明确命中 `Using contiguous KV for single-request prefill FlashAttention.`。该日志只证明此服务曾命中，不表示每一个P16K请求/层的分路计数。PR638 增加两次 index_select gather，也改变 varlen 内核输入布局；长输入可有额外复制/分配与不同 kernel 行为，但没有同机回切对照，**不能把P16K的24.56%直接归因给PR638**。MoE旧新16项忠实重放只覆盖 M16/72 的数值/graph，不是大M性能对照，不能证明性能相同或不同。

当前 HEADbad340d + MoEbbc2，与已发布但未部署的PR943 helper拆分97da71f不同；该新重构没有参与本次测试。当前源码三仓均没有读取 `VLLM_FL_METAX_QWEN3VL_MCTLLASS_GEMM2` / `VLLM_FL_FLAGTREE_QWEN3VL_WARMUP_COMPAT` 字符串，env=1不能单独当成相应新 kernel 已启用的证据。

## 决定与规划复盘 plan-opt13-gap-20261027

决定：**read-only diagnosis completed / causal attribution incomplete**。保持当前服务及用户压测不变，不将历史各优化加速比相加、不以跨 Host 差额签正式回退结论、不筛掉当前慢测量轮。

候选依赖顺序：原gems-opt→sampler直方图→原MoE特化→上游977后保留特化→PR638→默认split0。前几项是历史保留；当前没有同机anchor→最终组合的累计性能证明，正式精度也不能由旧split1/opt12实例转绑。

1. **P1K 稳态证据修复（framework，Prefill/Decode/Mixed）**：下一独立受控测量统一完成实际采样M1..64准备，固定预热预算和末3轮<=5%的准入，保留全部3测量轮；核验准备后第二遍0新增编译，原RNG/KV预算不变。先 CPU/最小正确性/graph，再按 performance Skill diagnostic 执行；不借准备改变采样算法。首证伪：相同单机P1024/D1024/C64/N128仍有>3%稳定吞吐差且无新增采样编译，则 JIT 不是剩余主因；不再盲增预热。该实验未启动，当前用户运行不触碰。
2. **P16K PR638有界消融（operator/replace，Prefill/Mixed）**：在独立环境，保留split0、同sampler/MoE/设备/argv，只切PR638的contiguous gather与原paged路径，先P16K缩减milestone再原场景B/C/R；仍监视Decode TPOT/ITL。最小正确性和graph必需，正式当前gate缺失须accuracy Skill补做后才有正式性能晋级。预记录吞吐3%、延迟10%与重复/漂移规则；无可复现差异则否定其为主要原因。该实验未执行。
3. **仍有P16K gap时分阶段profiling**：仅在前两项后，使用profiling Skill 区分 gather/varlenAttention、MoE大M、调度/通信/设备环境，按key-operator-analysis收敛到实际热点；采集开销不作正式收益。暂缓重新调MoE参数、新分片和全矩阵盲跑。

下一复盘触发：统一稳态证据取得、PR638单变量闭环或发现新明确热点。原服务不变，无新accepted E2E收益；P32/P64须等待用户当前运行产生自然结果，不能外推。

## 外部证据与归档

主回执：/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-opt13-performance-gap/results/existing-results-analysis.json，SHA `eea238c65efd36a1cbcf6d8c24fec44170835d3e7bccc6d33c7ecdc6a13cf764`。包含全部已读取CSV行、每文件SHA、指标计算和当前源码/配置指纹；`csv/`保留原字节，`snapshots/current-runtime.json`保留安全配置和缓存条目。

其他来源：旧opt10导入ef8e4e33…；旧新MoE重放fv-versions8-comparison.json SHA d9986d5b…；PR638-only回执3516f0fd…；当前服务/原bench脚本快照均在本远端目录。SFTP受限目录映射导致首次scp未写入，后改SSH标准输入保存同SHA脚本，首次脚本不存在退出无产物、无模型影响；成功运行唯一一次。
