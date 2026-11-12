# C588 MiniMax-M3 实际通信配置对照

用户要求在 C588 对比默认通信和 4 通道/1MiB，均 0.92。通过原服务临时暂停、独立容器顺序运行 baseline/candidate/revert、最终按原配置恢复。工作根 `/data/jinghao/minimaxM3`；唯一目录 `/data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092`。仅本服务、模型、Host。先确认无在途请求及无其他设备使用者。

- 性能 Skill targeted；精度观察 baseline-sanity/minimal-regression。诊断型性能比较，不签发模型正式精度 gate。
- 目标 P32768/D1024/C64/N128，守护 P1024/D1024/C64/N128，finite batch；三角色独立服务。自动KV、maxlen70000、MBT8192、TP16、prefix off、graph、工作负载和采样固定。候选只改变 MCCL/NCCL 的 BUFFSIZE=1048576、MIN/MAX_NCHANNELS=4 和 MAX_P2P_NCHANNELS=4；两策略同样打开 INFO 留下真实命中证据。
- 两轮预热、两轮计分，预热吞吐相对跨度≤5%，计分跨度≤10%，默认回退漂移≤5%。32K 主指标总吞吐，≥5%作为有实际改善的判断线；1K报告实测相对变化，下降超过5%标记回归。所有轮保留。取实际KV bytes/tokens与活跃窗口Running分布，TTFT/TPOT作客户端阶段代理；显存探针结果不代替模型表现。
- 控制面预先保存脚本和SHA，启动前复核源镜像及挂载、18050/18150、设备归属与空闲。超时、异常、收到停止请求时精确结束实验进程；源服务按原参数、原缓存恢复至18050，恢复日志另写。服务就绪核对及 `/v1/models` 检查后结束。

执行前登记：`./scripts/playbook /private/tmp/m3-c588-comm-e2e/deploy.yml --limit mx588-6 --ask-pass`，playbook SHA256 `41d4cf2cbc1e35e2bfd2e8c9f31db826db7d3cd28b9517ae16682bdab22d71ab`，归档 deploy.py SHA `0be5e135051a465fea6ecc8e5fad9577ae21b3e7274809c0fb78d6c15808eeaf`，control.py SHA `f2d337c2db7a7fe5391fd3a1d08719cbeecfebe42c4ca3c66961436fab79607c`。原脚本 SHA `430ef1c6e38ab67f944a075491610ff4bcddc9172aa6ebfc67681aaccfd61941`。预检发现 16 die 进程均属于源 MiniMax，Running/Waiting 均为零，独立端口 18150。源状态切换前将再次核验。执行监控 `status.json`、`runs/<role>/client-state-v5.json` 与 `performance/<role>-<scene>/`。完整 GPQA gate 未在本次诊断签发，固定 C1/C8 观察单独归档。

首个默认实例的 1K 两轮预热为 958.95、1301.87 tok/s，跨度 30.34%，未进入计分。退出后的 180 秒回收检查超时；随后只读检查确认两个端口均关闭、诊断容器只有 sleep、GPU 无进程。恢复命令先归档并执行，使用同一原服务配置并在成功时保存 manifests/manual-restore-ready.json。
a3d67a7bdaa41af0e30ff13e3cced0c7c5ffd3cc24e697bd824e2e781c8062b3  /private/tmp/m3-c588-comm-e2e/restore_followup.py
3613777cbd52625010f6e82fbd32185dc9aff19ea8b4079e40228f0f620fc5d4  /private/tmp/m3-c588-comm-e2e/restore_followup.yml

第二次同配置对照独立归档在 /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2，三个角色各自从头测量，先 32K 后 1K，32K 增至三轮预热、1K 四轮，只检查最后两轮 5% 稳态，仍计分两轮。该版单场景未稳态将保留原始证据并继续独立场景，其他执行失败仍立即恢复源服务。放宽进程自然退出等待至 15 分钟，识别 zombie；检查 GPU 完全释放后才切换。新控制器等待首次恢复 18050 的原生就绪回执后才进行幂等预检和源服务空闲检查。执行 ./scripts/playbook /private/tmp/m3-c588-comm-e2e-r2/deploy.yml --limit mx588-6 --ask-pass。
35183a7d8e93ed961c62f78e102952462d490463fe69664b8fb43b2083223b26  /private/tmp/m3-c588-comm-e2e-r2/deploy.yml
7c17a710809d26e87c4ce88ec5e64a0919bac0cc74a0f99a1146de97f1727d26  /private/tmp/m3-c588-comm-e2e-r2/bundle/commands/control.py

R2 默认组 32K 计分 2289.98/2294.40，1K 1237.38/1253.49 tok/s，每轮成功 128 个。首个候选服务实际 KV 115301，MCCL 输出 4 coll/16 P2P 及明确读取 1048576 bytes，但 worker /proc/environ 只显示部分变量，客户端身份校验在计分前停止。继续实验保留全量证据和默认分数，使用同一隔离容器、cache、模型、服务参数、原生 runner 和 workload。启动参数及原生日志核实实际配置，/proc 可见字段仅用于验证无矛盾。新候选/回退日志放在 resume-runs/。源服务恢复回执前不得继续。执行 ./scripts/playbook /private/tmp/m3-c588-comm-e2e-r2/resume/continue.yml --limit mx588-6 --ask-pass。
b3ff481d56173fd3b2e7ea0fc5e9495945ad2430e5c6379a5819de503563f63a  /private/tmp/m3-c588-comm-e2e-r2/resume/continue.yml
b9e92c3a790b3a1f89c00818a013cb9a1e61adfe16283e869a2e7bb0bbb2c76d  /private/tmp/m3-c588-comm-e2e-r2/resume/resume-control.py
5e1ab7dccbf3c6ab3caecbc403665a48bf8e61df54ab3d6cc16a14401cacbc36  /private/tmp/m3-c588-comm-e2e-r2/resume/resume-identity.py

已计分的候选与默认组均为同一运行契约，默认 KV 88,939，候选 115,301 token。32K 默认 2,292.19、候选 2,506.29 tok/s，1K 默认 1,245.43、候选 1,575.76 tok/s。原生记录结束时间与文件系统时钟校正后的结束时间一致至约 1 秒。32K 两轮中，默认 Running=2 的活跃样本 1,795/1,878；候选 Running=3 的样本 1,538/1,718。该快照采集于回退验证完成前。

## 完成结果（2026-11-06）

所有实例均使用单机TP16、gpu_memory_utilization=0.92、自动KV。32K三轮预热、1K四轮预热，通过最后两轮跨度≤5%的准入后，各计分两轮。三组每个计分轮均完成128个请求，输入和输出token计数通过原生验证。下表吞吐为两轮中位数。

| 指标 | 默认基线 | 4通道 + 1MiB | 恢复默认 |
|---|---:|---:|---:|
| 引擎等效KV容量/token | 88,939 | 115,301 | 95,082 |
| 实际MCCL coll/P2P通道 | 32/32 | 4/16 | 32/32 |
| 32K总吞吐/tok/s | 2,292.19 | 2,506.29 | 2,301.52 |
| 32K活跃采样Running众数 | 2 | 3 | 2 |
| 32K众数样本占比 | 95.58% | 89.52% | 95.40% |
| 32K平均TTFT/秒 | 689.13 | 621.77 | 686.48 |
| 32K平均TPOT/毫秒 | 25.84 | 34.67 | 25.76 |
| 1K总吞吐/tok/s | 1,245.43 | 1,575.76 | 1,342.11 |
| 1K两计分轮各自preemption增量 | 47/47 | 16/16 | 38/38 |

Running按原生计分轮耗时窗口统计，采样周期约2秒，过滤Running=0后取分布。校验原生日期与时钟校正后的结果文件写入时间相差约1秒。preemption增量用连续完成轮次的累计counter之差计算。C64为客户端并发上限，Running反映实际活跃请求。

### 结论与范围

32K吞吐相对初始默认提高9.34%，相对恢复默认提高8.90%，默认前后漂移0.41%，预先冻结的原生比较通过。KV比初始默认增加26,362 token（29.64%），比恢复默认增加20,219 token（21.26%）。KV增加与实际Running从2增至3同步出现，支持KV容量限制有效并发这一机制。32K三组计分轮均无preemption。实验联合调整通信通道和buffer并让KV自动扩容，独立通信延迟贡献仍待固定KV的单变量实验拆分。

32K客户端TPOT提高34.20%，与吞吐增加同时出现，应按逐token延迟要求评估是否采用候选。TTFT含排队和调度，总体下降9.78%。

1K候选吞吐比初始默认提高26.52%，比恢复默认提高17.41%。候选优于两次默认结果，每轮preemption从47/38减少到16。默认两次自动KV容量和吞吐有波动，吞吐漂移7.76%超过预设5%，原生1K比较记为incomplete，精确的1K稳态收益需独立复测。

三个服务均通过固定C1与两批C8最小回归，graph完成PIECEWISE及FULL capture，并经过多轮服务请求。完整模型精度验收待补，本轮仅签发targeted性能诊断结论。

### 恢复与复现

实验结束后按原参数恢复minimaxM3的18050服务，16个die归还原服务。两个实验容器各只保留sleep进程，18150端口关闭。原启动脚本SHA256核验为430ef1c6e38ab67f944a075491610ff4bcddc9172aa6ebfc67681aaccfd61941。当前服务采用默认通信策略。

完整原始产物位于 /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2。baseline日志位于runs/baseline，实际候选和回退位于resume-runs。performance下三角色的short/long目录包含所有预热、计分及原生回执。首个未稳态实例和候选身份检查失败的证据均保留。

### 最终证据校验

- /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2/results/results-summary.json，SHA256 1f053a332cd21f20e25b8b7ecc2c9ed9c04112dfbdc09e0c0883c294ccf684d7
- /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2/results/long-comparison.json，SHA256 9304b02bd30448868a55d332d0b8db1191e3e277f75412c5ea7b85b2ac23b6c6
- /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2/results/short-comparison.json，SHA256 0aba03cee0b1830ef04891182384f2cc35634551bd17ceb961232e2739dbd88e
- /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2/manifests/resume-restore-ready.json，SHA256 dce1fabd52c32686fc6245d1137aeb2f81b65531964fb4db19ab28f8aba4b611
- /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2/resume-status.json，SHA256 6df1db44a2da876202e80d92773137fe434cfcde429dcc29d1f94aeb6c3f9cb4

## 用户指定正式启动脚本配置更新

2026-11-06 用户明确要求将 /data/jinghao/minimaxM3/start-model.sh 更新为4通道+1MiB、显存利用率0.92，后续自行端到端复测。在原脚本清理环境之后、服务启动前增加与已测候选一致的8个NCCL/MCCL变量。操作仅修改指定脚本。原文件备份和更新脚本保存在既有任务目录 commands/formal-launch-20261106。先检查旧SHA和bash语法、查看diff，再原子替换并从minimaxM3容器校验语法和SHA。生效时间为下次服务启动。
b8b5037f24d4ba5b0b3580d3e94eac4046e062d0471dcae9e4a815865446b5b6  /private/tmp/m3-c588-comm-e2e-r2/update_formal_launch.py

更新已执行。正式脚本SHA256为a0fe1b602415499012efcd7c8280e125db605fafe9a0cb53597813e9825ae1ef，宿主机与minimaxM3容器内语法检查通过且SHA一致。备份路径 /data/jinghao/minimaxM3/20261105-m3-c588-comm-e2e-092-r2/commands/formal-launch-20261106/start-model.sh.before。修改脚本后由用户下次启动时生效。本操作未触发服务重启。

## 用户五场景复测与64K回退复盘（2026-11-06）

复盘ID为review-optmccl-64k-20261106，范围为已有结果及日志的只读核验。用户基线目录为/data/jinghao/minimaxM3/test/perf_test/benchmark_results/minimax-m3，批次20261103_093147；候选目录为同级minimax-m3-optmccl，批次20261106_022320。两者P/D/C/N匹配，均P可变、D1024/C64/N128。当前perf.log预先声明RUNS=3、SKIP_FIRST=1，SUMMARY与后两轮算术平均一致。各轮成功128、输入P×128、输出131072。该历史比较与本案例先前seed42等独立诊断契约分开记录。

| 输入token | 历史默认tok/s | 用户optmccl tok/s | 相对变化 |
|---|---:|---:|---:|
| 1024 | 1000.70 | 1143.43 | +14.26% |
| 4096 | 1357.74 | 1472.52 | +8.45% |
| 16384 | 1941.83 | 2034.66 | +4.78% |
| 32768 | 1996.66 | 2252.16 | +12.80% |
| 65536 | 2050.63 | 1884.20 | -8.12% |

新64K计分轮为1881.55/1886.85 tok/s，跨度0.281%；旧64K为2050.90/2050.36，跨度0.026%。三轮均呈现退化。整轮均值4154.67→4521.66秒，增加366.99秒；TTFT1539.49→1678.67秒；TPOT25.64→25.79ms。吞吐下降8.12%。

当前脚本SHA为a7c2affa2da73247b649fa4f52b8de2d2d6c46e48d431cfe96e00ab2cd8cecc4，与原默认备份的diff仅包含通信变量块和模型别名minimax-m3-optmccl。现场进程读取到8个匹配的NCCL/MCCL变量，TP16、0.92、MBT8192、maxlen70000、prefix关闭。当前service.log报告KV115301，16个rank预算记录一致至小幅页差。当前日志缺少INFO级MCCL通道事件，原生通道数以先前独立候选的4coll/16P2P证据为参考，本轮仅核验环境变量与KV结果。

按perf.log每轮首个INFO到下轮INFO的近似窗口对齐service.log，64K两计分轮共880个Running>0采样全部为1，Waiting最高63，KV峰值57.8%。窗口包含少量客户端初始化和预检请求，精确设备step形状待trace确认。原历史只读证据64K Running中位数同为1。32K新两轮Running众数3，旧为2；16K新为6、旧为5。

两条完整64K输入需131072 token，带1024输出约133120；115301预算仍低于该量级。分页和分组使算术阈值仅为说明，实际Running采样提供更直接的证据。因此64K缺少32K那样的并发提升，通信参数代价可能直接体现在总耗时。

在Running约1的条件下用duration/128近似单请求服务周期，用1023×meanTPOT近似decode耗时。默认总周期32.458秒、decode26.230秒、剩余6.229秒；候选35.325秒、decode26.383秒、剩余8.942秒。新增2.867秒中约2.714秒、94.65%在decode以外。剩余项含prefill、调度、请求衔接及客户端开销，不能直接命名为纯GPU prefill或MCCL时间。TTFT含大量排队，用于证明用户等待增加。

阶段判断为prefill/请求衔接增加、decode代理接近、mixed因Running未扩容而净退化。较低通信并行度或较小buffer对长prefill的大消息路径不利是首要待证假设。本轮缺少同时间默认回切及多rank trace，具体通信贡献和通道/buffer独立影响尚未定位。

### 下一轮排序与停止条件

1. framework诊断优先。P65536/D1024/C64/N128为目标，先在独立隔离容器采用N4的同配置默认/当前候选短探针，均0.92，记录KV及Running；通过inference-performance-evaluation targeted固定稳态规则，再通过inference-profiling采集匹配prefill step和多rank MCCL。无profiler守护TPOT。若Running或请求形状不匹配，先调整证据对齐；若额外时间主要为非通信kernel/CPU空闲，停止以通信带宽为主因的归因。
2. 若通信假设成立，单独将通道4改8、buffer维持1MiB，观察64K额外时长是否回收。32K为守护并确认仍有足够KV支持Running3；若32K吞吐下降超过5%或64K改善低于5%，回退候选。随后再决定是否单独改变buffer，避免同时叠加两个变量。此项尚未执行。
3. 深度算子优化延后，直到多rank trace证明具体热点。当前没有足够证据把该退化直接归因CPU或某个计算kernel。

最小正确性仍需C1/C8，进入正式验收需完整精度gate。下次复盘在得到64K同条件回切/trace或首个单变量候选结果时触发。当前正式脚本继续承载用户指定配置，本轮只读诊断。

64K原始CSV SHA256分别为829d2c896bafe82ab7f5f04b368e6915b5db735ce5bc7c01222a07773fa95051和ef3d2921fdb9409d0b0321a6482bd28863864c904e91459d97f70f2fea9afcaf。日志依据为/data/jinghao/minimaxM3/service.log和/data/jinghao/minimaxM3/test/perf_test/perf.log。
