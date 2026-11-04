# MiniMax-M3：C588-6 单机与 C550 101/102 双机的历史性能对比

日期：2026-11-04。范围为只读诊断，证据等级 `observation`；未运行新 benchmark、profiling、正确性或精度评测，未修改任何模型服务、源码、启动配置或容器。不是 CPU 型号的单变量实验，也不是正式优化验收。

交付：已将本轮结果、配置/KV/Running 证据和归因边界追加到[飞书报告](https://jwolpxeehx.feishu.cn/docx/DuwsdmPo7oi979xodNac0OVknab)第八节，并通过页面“已经保存到云端”核验。mx-101、mx-102 的 CPU 型号和拓扑均已现场只读核验。

## 结论

MiniMax-M3 的差距随输入长度明显变化：C550 双机在 1K/16K 总吞吐高约 4%，4K 高 16.16%，32K/64K 高约 22%。同时，C588 的 mean TPOT 在五个场景都更低，不能概括成“C588 每个阶段都慢”。

当前最直接的差异是 **KV 容量和实际运行并发不同**。C588 日志报告 95,082 token，C550 为 155,136 token（后者多 63.16%）；16K/32K/64K 的引擎 Running 请求数中位数分别约为 5/2/1 与 9/4/2。较小的批处理负载有利于降低单请求 TPOT，却限制并发服务能力、增加排队；这与 C588 较低 TPOT、较高 TTFT 和较低总吞吐同时出现的现象一致。

这比“CPU 型号不同”更贴近本组数据的直接证据，但尚未通过对齐 KV 容量的单变量 A/B 量化贡献，不能宣称 KV 已解释全部差距。CPU、单机/双机通信、GPU/驱动、实际 batch 和 mixed 阶段干扰仍未完全拆分。

## 目标与事实来源

用户指定：

- C588-6：`/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3`。
- C550 双机：`/public-flash/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3`。

本项目与“新模型适配”中未找到这套 MiniMax MetaX 双机的有效交付记录；上游 `models/MiniMax-M3/metax/platform.yml` 仍是 not_started 骨架，与已运行事实不一致。本轮只读读取其登记，没有改动上游。另查询了本地聊天索引，未取得可替代运行证据的 MiniMax MetaX 交付记录。

通过已可访问的 mx-104 只读读取共享目录的 `serve_minimax_m3.sh`、`service101.log`、`service102.log`，再对 mx-101、mx-102 精确连接核验，确认双机为 101+102，TP16、每机 8 rank。没有操作 mx-103。为使用本项目控制面，在 inventory 新增已有 SSH 别名 mx588-6、mx-101、mx-102，不复制任何连接凭据；inventory/shell/playbook syntax 检查通过。

C588-6 的非交互连接检查因认证链失败，改用既有 SSH 别名的交互认证后核对 hostname、路径、容器与设备；没有用普通 SSH 退出码冒充连接检查通过。C550 101/102/104 均通过精确 Host connectivity-check。

## 性能数据与有效性

两端均为 random 固定输入、输出 1024、C64/N128、无限到达率的有限批次、/v1/completions、ignore_eos；CLI 实际 seed0、range_ratio0、prefix_len0、temperature=None（沿用服务默认），prefix cache 关闭。C588 客户端访问 localhost，C550 访问 101 的服务地址，网络路径不同。

CSV 批次分别为 `20261103_093147` 与 `20261029_070842`，并非同时测量。每场景 3 轮，源码预定 SKIP_FIRST=1，SUMMARY 是 Run2/Run3 各项指标的算术平均；本轮没有另行挑选或删轮。CSV 与 perf.log 的 15 组原生计数逐一交叉核对：每端全部 15 轮都是 128 成功、0 失败，输入数等于 P×128，输出数为 131072。主要 SUMMARY 指标与后两轮平均在两位小数舍入误差内一致。计分两轮 total tok/s 的相对跨度均小于 1%；这不是独立服务实例复测或统计置信区间。

表中 total tok/s 为输入加输出总 token / 整轮时长；同一长度分子相同，其相对差异也反映完整批次耗时差异。TTFT/TPOT 是客户端代理，包含排队、调度和阶段干扰，不能称为纯设备 prefill/decode 时间。

| 输入 | C588 total tok/s | C550 total tok/s | C550 相对 C588 | mean TTFT，秒，C588 / C550 | mean TPOT，ms，C588 / C550 |
|---|---:|---:|---:|---:|---:|
| 1K | 1000.70 | 1041.13 | +4.04% | 5.11 / 3.49 | 103.66 / 119.50 |
| 4K | 1357.74 | 1577.11 | +16.16% | 121.10 / 78.27 | 71.81 / 101.89 |
| 16K | 1941.83 | 2025.56 | +4.31% | 396.90 / 358.86 | 41.43 / 68.75 |
| 32K | 1996.66 | 2445.62 | +22.49% | 790.80 / 630.36 | 30.11 / 48.75 |
| 64K | 2050.63 | 2497.82 | +21.81% | 1539.49 / 1250.96 | 25.64 / 42.54 |

16K 是最直观的取舍：C588 TTFT 396.90 秒、C550 358.86 秒，但 TPOT 为 41.43/68.75 ms，C588 低 39.74%；总吞吐 C550 仅高 4.31%。32K/64K 的 TTFT 与整轮时长则明显有利于 C550。

## 配置、源码和模型身份

| 项目 | C588-6 | C550 101+102 |
|---|---|---|
| 设备拓扑 | 单机，8 个 C588 模块 / 16 个逻辑 die，TP16 | 双机，每机 8 张 C550，共 16 rank，TP16 |
| 物理显存总量 | 8×128 GiB，按 16 die 使用 | 16×64 GiB |
| CPU | Hygon C86-4G OPN7493，112 在线物理核 / 8 NUMA | 每机 Xeon Platinum8460Y+，80 核 /160 线程；合计 CPU 资源也不同 |
| GPU 驱动 | 3.9.61 | 3.8.1（102 现场核验） |
| 实际显存利用率参数 | 0.92 | 0.96 |
| 实际 max-model-len | 70000 | 131072 |
| 日志 KV token 容量 | 95082 | 155136 |
| dtype / KV / index KV | BF16 / BF16 / BF16 | 相同 |
| MBT / max-num-seqs / block | 8192 /64 /128 | 相同 |
| prefix cache / async scheduling | 关闭 /关闭 | 相同 |
| graph 日志配置 | breakable，FULL_AND_PIECEWISE，compile NONE | 相同 |
| 主要算子路线 | FlagGems-vllm=1，MetaX vendor indexer/MSA | 相同策略，15 bindings |
| 镜像仓库 | flagrelease-public/minimax-m3-metax | flagos-inner-models-release/minimax-m3-metax |

两镜像 tag 均 bf16-vllm0.24.0-fl976f389-20261028，但 image ID 不同：C588 `73cf6f40bdf2c662673895ce9a66ce7145c1df256f9c37bd53f3fe2ddbb780d4`，C550 `ec9fca6148438cdc7eef6aebc8d71069d81af89ef5730fa1f60178d7d00fbd0a`。不能称为完全同镜像 A/B。

已核验三仓 revision 和工作区均一致、干净：Plugin `976f3892106466435ab3b0fdd91c9307156398a0`，FlagGems-vllm `ff12e0bfa9e124827739ae2e4ce7d7592c7e65b1`，FlagGems `c7a255b6bb24d3e5b3c1d40aa392e590d84c29d6`。实际 Torch2.10.0+metax3.8.1.0、vLLM0.24.0+empty、Plugin0.0.0+g976f38921、FlagGems5.3.5.post1.dev1+gc7a255b6b、FlagGems-vllm0.1.0 一致；没有证明全部底层二进制相同。

源策略配置 SHA 均为 `b05ce41866efce280638f3ad41a9e068be27e75242ec00ebb2912620da3b1853`。实际 profile 去掉 infrastructure_env 后的规范 JSON SHA 均为 `c3b6fabd0553173805e0cdb84264a3f026455eaf0675aae066b7fd27355c58da`，包括 framework/kernels/linear/moe/attention/service 策略一致。profile 声明的 service 默认值不是 C588 实际 CLI 值，0.92/70000 以运行日志和 launcher 为准，不能被 JSON 默认的 0.96/131072 覆盖。

模型 config、tokenizer、tokenizer_config、权重索引、generation_config 的 SHA 全部相同。未全量哈希权重分片，不宣称逐权重字节等同。两个 vllm_perf.py 全文件 SHA 不同，但 10 个函数的 AST SHA 逐项相同；实际命令与 Namespace 的负载参数一致。没有以此证明所有 native benchmark 源码/二进制完全等同。

## KV 容量与实际并发的证据

从原有约 10 秒粒度的服务日志提取引擎 Running/Waiting/KV 使用率。按客户端各轮 INFO 时间建立近似窗口，C588 服务日志按 UTC、C550 按 UTC+8 对齐，排除每轮初始 60 秒，只统计 Running>0 的采样。相邻轮次开始为上界，末轮 C550 上界取启动后 3600 秒。初版使用共享文件 mtime 会截断 C550 第三轮，已纠正为日志边界；旧结果留外部临时产物，不纳入结论。

这些窗口覆盖编译前置/初始请求的残余时间及排队、收尾，Running 是引擎已运行请求数，**不是每个 GPU step 的精确 batch，也不是 profiler**。两计分轮的 Running 中位数：

| 输入 | C588 Run2 / Run3 | C550 Run2 / Run3 | C588 / C550 最大 Waiting |
|---|---:|---:|---:|
| 1K | 49 /49 | 64 /64 | 18 /0 |
| 4K | 19 /19 | 31 /31 | 46 /34 |
| 16K | 5 /5 | 9 /9 | 59 /56 |
| 32K | 2 /2 | 4 /4 | 62 /61 |
| 64K | 1 /1 | 2 /2 | 63 /62 |

16K 窗口 C588 224 个活跃采样中 203 次 Running=5，C550 216 个中 127 次 Running=9；32K 两端多数采样为 2/4；64K C588 818 个采样全部为1，C550 680 个中642次为2。这与 KV token 预算不同相吻合。不能把客户端 max_concurrency=64 当成两端都在设备上以 batch64 执行。

32K/64K 的 KV 使用率未达到100%也不否定容量门槛：剩余可用页可能不足以接纳下一条长请求。仅用容量除以完整 P+D 也不能精确反推 Running，因为请求在不同 prefill/decode 进度，且有缓存分组/块对齐。实际采样是更直接的并发证据。

显存比例不同是 KV 差异的一项明确配置因素，但还可能包含设备可用显存、graph/工作区、内存布局或启动时资源状态。未将 0.92 改为 0.96，也未做相同 KV budget 的反事实实验，不能将全部 60054 token 的容量差直接归为单个参数。不能在未核验余量时直接建议提高参数，以免 OOM。

## Prefill、Decode、Mixed 与通信

- Prefill/排队代理：C588 五场景 mean TTFT 均较高，长输入差距尤其明显；KV 受限下的 admission 和等待是重要候选。尚无隔离的 prefill 设备测量，不能据 TTFT 宣称某个 prefill kernel 较慢。
- Decode 代理：C588 mean TPOT 较低约13%–40%，但其 Running 更小，不能将该比例称为同 batch 下的 GPU decode 加速。
- Mixed：同一客户端上限下，C550 更多请求并行的吞吐收益与较高 TPOT 并存。C550 4K/16K/32K 的各轮 P99 ITL 平均约1062.95/1096.43/1074.14ms，C588为471.70/46.62/34.38ms，提示需检查 prefill/decode 干扰、调度与通信等待；不能仅凭约1秒尾部间隔认定 RDMA 慢。这里是轮内 P99 的平均，不是合并样本 P99。
- 双机通信：C550 确有跨节点 TP collective 和四通道 IB/RoCE 参数；C588 为单机。没有 MiniMax 多 rank trace 或通信单变量试验，无法拆出纯 MCCL 链路耗时。总吞吐与单 token 延迟可能被不同因素主导。

## 与 DeepSeek、Qwen 放在一起看

| 模型 /16K | 当前观测 | 可以支持的判断 |
|---|---|---|
| DeepSeek：C588-5 vs104，TP8 | C550 总吞吐高14.55%；trace历史为 C588/103，CPU/logging A/B及CPU-only PMU另有验证 | 当前实现的主机供给侧关键路径已有独立证据 |
| Qwen3.6-35B：C588-5 vs104，TP2 | 历史16K差约1.1%，同口径短负载CPU占用较低 | 与CPU余量更大机制一致；不是CPU型号单变量对照 |
| MiniMax-M3：C588-6 vs101+102，TP16 | 总吞吐差4.31%，C588 TPOT低39.74%；KV容量与Running不同 | 阶段取舍及容量/批处理差异更直接，不能把DeepSeek归因直接套用 |

MiniMax 是新的 C588-6 和 C550101/102 组合。此前 CPU-only PMU 实验在 C588-5/104 上完成，不能将其中约50%的热点 CPU 时间差直接外推为 MiniMax 的贡献比例。CPU 型号相同也不代表不同机器频率、争用、拓扑和驱动状态相同。

MiniMax 与 DeepSeek 当前软件执行组织也不同：前者明确启用 FlagGems-vllm 和 breakable FULL_AND_PIECEWISE 路线，后者历史为 FULL_DECODE_ONLY 且有 native clamp 展开热点。这个差异说明必须按实际模型路径判断；没有本轮 MiniMax trace，不能据图配置独自断言全部 prefill 都以图执行或 CPU 已完全不在关键路径。

## 后续优先级与未完成项

本轮已完成现有数据对比，未启动新性能实验。若继续做根因量化，建议按以下顺序冻结单变量契约：

1. 在隔离且资源可用的环境中核验显存，固定相同 KV token/block budget、max-model-len、负载、模型身份及稳态准入；保留原值作为基线/回退，验证 Running 与 TTFT/吞吐是否随 KV 对齐收敛。
2. 建立相同实际 batch 的 Prefill/Decode 缩减探针，再采低扰动多 rank 时序，区分 CPU launch、计算、collective 等待。不能只看均值 CPU 占用或不同 batch TPOT。
3. 单独评估跨机通信与 mixed prefill 干扰；比较阶段收益后回到完整 workload。禁止直接将每个候选的孤立收益相加。

没有正式精度 gate、本轮未做新精度/完整四场景正式验收。C550 的10月29日日志在约22:03出现 worker死亡/EngineDeadError，晚于五场景压测完成：最后一轮按客户端时间与时长约在21:10结束（共享存储mtime为21:07，存在时钟偏差）。原生结果均成功，但不将其称为长期稳定性通过。102旧容器目前已停止；只读 inspect 和 docker cp 读取保留策略，不重启、不操作其上其他模型。第一次 docker exec 因容器停止而失败，随后改用只读 docker cp，非复测失败。

## 证据位置与校验

C588：上述结果目录、`/data/jinghao/minimaxM3/service.log`、`test/perf_test/perf.log`、`start-model.sh`、`01-environment/minimax-m3-c588.json`。C550：共享根 `/public-flash/jinghao/minimaxM3` 下两节点 service日志、`test/perf_test/perf.log`、`serve_minimax_m3.sh`；容器内 `/cache/minimax-m3-976f389/node{0,1}/profile.json` 哈希均为 `fc0e60838f2cf4e39013ede148e7cabb72c1bc2ec6bf97076c390b78cdee3f54`。C588 profile原文件SHA为 `75844900f83e4319f9b402f5c3a68cb1cbc93b1ef6d9c253d082a66c46dd19de`。

C588 launcher SHA `430ef1c6e38ab67f944a075491610ff4bcddc9172aa6ebfc67681aaccfd61941`；C550 launcher `24be033ca92afc8afce4abe82e56b0b819be6503c11999026f64e6fe967c00cb`。C588 perf.log SHA `b9340f6404ca8bb298f90762fa54589dd65c0f61bb0448c40319492c85d13f02`。C550 service101/service102 SHA分别 `6c7ece38c167b775f1feba19e4695c7de4bda2957bdf41621680fb5833cfc81e` / `c9cc96693b0e9fcd25836ce5e4016a1f350e4780ab2d22268740e5e844dd607a`。

| CSV 输入 | C588 SHA256 | C550 SHA256 |
|---|---|---|
| 1K | `a78b0da51064b800c93d2938bdb907b435b709cc823848a40e07efdf614f8fe0` | `68e60768549fe6e1984e0cb955fbabc5cb15b737ac85a99b46f292688f0fe8fa` |
| 4K | `086e8ddd4b2ea221bbdae82376e984fcebaf7c12072eb3f54ceba7cb334be452` | `4d56afdc790e624d9db1260111b17b1870bb6d0106e1c992abf8e1b7db011374` |
| 16K | `ad7243ba1628bc675527027eb4db87ed009b534a5085cafe809563129aa78dfd` | `28a89b4b226946381aec8825ed2d45582c33cbde4d39edb9c6556c31a3ddbd4d` |
| 32K | `6c3e2f09ae5f564851288f049ef798ee9b419074c25193cfe758095ee9001227` | `daaa6e857ab85ddc8ab70e11ab062b6cb1f1f6efba0062a8fbb8c7f132b00382` |
| 64K | `829d2c896bafe82ab7f5f04b368e6915b5db735ce5bc7c01222a07773fa95051` | `270ee59944959dfc9063ebaf112f63fedc3d4ae54e87c3636abf0114e8fcaefe` |

本地外部临时解析与验证材料位于 `/private/tmp/minimax-m3-cross-20261104/`；长期原始证据仍为上述远端产物，不依赖临时副本存在。未提交、推送或变更上游记录。该观察不足以修订通用 SOP。

