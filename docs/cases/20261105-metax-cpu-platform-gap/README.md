# C588海光与C550 Intel：PCIe、RAM和CPU执行效率诊断

2026-11-05；policy0.44；acceptance_scope=diagnostic；状态diagnosed；三方向初步硬件诊断完成，非模型优化或正式性能验收。

最终结论：差异随工作集与执行路径变化，不能归纳为“海光全部CPU操作/RAM都慢”或仅归流水线深度。CPU/RAM对照为C588-5与104；用户指定后，PCIe对照改为CPU同型号/stepping/内核/驱动的59与C588-5。

- **CPU核内**：相同纯寄存器立即数ADD并行流，Intel约5.918 IPC、海光3.999 IPC，海光每op周期+47.99%、时间+33.31%；该结果属于特定指令模式，包含Intel可能的立即数折叠优势，不能当通用CPU分数或真实Torch dispatcher的完整解释。
- **Cache/NUMA**：海光每核L2 512KiB、Intel2MiB；1MiB与32MiB随机链海光慢70.52%/114.49%，8MiB反而更快。256MiB本地随机链均约128ns，单核复制海光略快；跨socket随机链海光354ns、Intel210ns。缓存层级和远端归属是明确差异，模型实际页/工作集仍需对齐。
- **Host传输**：同程序/同SDK、64MiB锁页单向传输，C550/59单卡H2D/D2H49.30/55.55GB/s，C588单die29.68/33.71GB/s；两设备并发聚合96.16/108.38对30.28/34.02。C588同模组双die没有叠加，存在共享Host路径上限；不能由此认定外部PCIe降代或唯一归因CPU。
- **launch边界**：交叉绑核后耗时明显变化，撤回将初测约79%/93%作为固定型号惩罚的解读；原始和交叉轮次完整保留。所有诊断容器已停止，测试进程退出，原模型服务没有被本任务停改。

用户要求比较mxC588-5海光7493与mx-104 Intel8460Y+，从PCIe传输、RAM带宽/延迟、dispatch所需周期及流水线/cache等因素解释相关Python/Tensor主机路径差异。

范围冻结：仅这两台Host，不访问103或101/102，不停止/重启/改动模型服务或源容器，不修改系统配置、驱动、源码、权重。先只读核对CPU/cache/NUMA/内存/PCIe实际拓扑和既有GPU-off PMU原始证据。新的CPU-only微探针须先确认资源、记录源码与预算，限制核心和内存；新GPU/PCIe传输实测需要独立诊断环境与设备空闲，不用当前业务服务做压测。

主指标：按路径的线程CPU时间、指令/周期/IPC，分层随机依赖访问延迟与受控单核RAM吞吐（如执行）；PCIe当前/最大代际和宽度，不能拿链路标称值当有效传输或doorbell成本。守护：无服务操作、无GPU分配；证据缺失保持unknown。

相关证据：[跨模型报告CPU与trace](../20261104-metax-models-c588-c550-overview/README.md)、[Qwen形状/通信只读分析](../20261104-qwen35-metax-c588-c550-gap/README.md)。临时控制与计算产物：/private/tmp/cpu-platform-gap-20261105。远程历史根沿用用户指定的C588 /data/jinghao/deepseek、104 /public-flash/jinghao/deepseekV4，仅在各自根下的新唯一case目录创建后续产物，不覆盖旧cpu-proof证据；本轮只读预检尚未创建远端目录。

方法边界：本地性能评测/Profiling Skill已读取，当前硬件探针不是vLLM性能runner支持的模型场景；不伪称Skill通过或新增runner替代原生模型评测。若仅消费既有CPU/trace，为只读analyze；若需GPU trace或无profiler模型测量，再按对应Skill与容器门禁执行。正式四场景及精度验收均not_run。

## 新探针执行前冻结

CPU-MEM-001：单核、nice19、无GPU访问。同一x86-64/AVX2二进制在104构建后原样用于C588，不升级依赖。每端两个不同socket空闲物理核，避免Intel忙碌SMT同胞；每种绑定2轮预热+5轮全部保留。随机依赖链16KiB/256KiB/1MiB/8MiB/32MiB/256MiB，固定64B随机链及seed731；MADV_NOHUGEPAGE统一页策略，mbind固定节点且move_pages抽检。另测128MiB源+128MiB目标、固定AVX2 NT复制，报告单核逻辑读写流量而非整机峰值。增加跨socket内存绑定对照；单进程峰值小于320MiB、单Host总预算120秒，CPU/PMU条件不符合则保留incomplete。不换算模型加速比。

CPU-CALL-001：同二进制的direct/fixed-indirect/two-target-random原生调用循环，测用户态cycles/instructions/branches/branch-misses及线程/墙钟。随机目标含额外选择工作，不把与fixed的时间差当纯分支预测惩罚；不代表真实PyTorch dispatcher。四PMU事件未支持/复用则标注缺失或incomplete。禁止关闭安全缓解机制、修改频率、缓存策略或服务。

准备入口 `/private/tmp/cpu-platform-gap-20261105/prepare_probe.py`，C源 `/private/tmp/cpu-platform-gap-20261105/host_probe.c`。104新远端根 `/public-flash/jinghao/deepseekV4/cpu-platform-gap-20261105-01`；C588新远端根 `/data/jinghao/deepseek/cpu-platform-gap-20261105-01`。先检查/唯一mkdir再写入，已有目录会拒绝覆盖。准备命令不执行探针，正式执行前另存控制命令与SHA。

构建校准：初版动态ELF未运行，因两Host libc可能不同改用静态链接公共ELF。实际源 `41cf2bb966e259db9f6f302fb3e74a7edc53cdcbe133eff5c25481598e6e51cb`；静态ELF 909976字节、SHA256 `59a885dc2c7902bdba4f0786349e62911d9acdcc519527b6ed193e72648f6b67`。精确执行控制脚本 `/private/tmp/cpu-platform-gap-20261105/run_probe.py` SHA256 `519f73ef924654749aba9b0dc12ca12fd4be61135e53b6f30e1a0d19c8f00126`；执行前部署到远端commands/run-probe01.py并验SHA。仅在空闲CPU及其SMT同胞均<=20%、节点Free>=2GiB时执行；每子进程RLIMIT_AS512MiB/CPU30秒，记录priority实际值，任一错误停止后续。

工具校准更正（测C588之前）：104初轮10.08秒完成、110行均成功/priority19、PMU无复用，但256MiB链每次仅从同一起点走100万步，实际热前缀约64MiB，可能落入Intel L3。该组不能用于DRAM延迟判断。原文件完整保留，不事后删慢轮。V2在每轮强制遍历至少全部cache line（256MiB为4194304步），两端统一以V2重跑；新文件host_probe-static-v2、commands/run-probe02.py、run-result02.json、results/probe02-*，不覆盖首轮。其他小工作集定义不变，但最终比较只用V2同批。C588尚未执行初轮。

V2执行身份：C源SHA256 `807ab342c1f06c2d8c55ef257866c25b205a43592d41ee998ca32ccdc068be5e`；静态ELF SHA256 `171d9da295781f2f41f68e85af7c35e07b044a8a20328d182be72d22edfdc2ce`；run-probe02.py SHA256 `58c8b468798b29f70a0809626a84ab3904c5a3351f5d402c6c0bf8ce1dc75694`。C588部署不重新编译，以SHA拒绝差异。

## CPU/RAM已完成结果（2026-11-05）

两机V2均110条成功，四个用户态PMU计数均无复用；全部页归属抽检成功。Intel两个socket选择CPU18/node0、CPU44/node1，海光CPU33/node2、CPU68/node4。每core/shape保留2预热后的全部5轮，表中为两个core各自中位数的算术均值。nice实际19；Intel22.13秒、海光27.52秒完成，最大wall/thread-CPU比例分别1.00117/1.00758。所有原生探针均已退出，没有GPU请求、模型请求或服务操作。

| 探针 | Intel104 | 海光C588-5 | 海光变化 |
|---|---:|---:|---:|
| 16KiB随机链，ns/访问 | 1.805 | 1.614 | -10.57% |
| 256KiB随机链，ns/访问 | 5.790 | 4.204 | -27.40% |
| 1MiB随机链，ns/访问 | 7.422 | 12.656 | +70.52% |
| 8MiB随机链，ns/访问 | 41.173 | 15.327 | -62.77% |
| 32MiB随机链，ns/访问 | 46.929 | 100.656 | +114.49% |
| 256MiB本地随机链，ns/访问 | 128.333 | 128.405 | +0.06% |
| 单核AVX2 NT逻辑读+写，GB/s | 21.825 | 23.707 | +8.62% |
| 原生直接调用循环，ns/次 | 1.144 | 0.968 | -15.34% |
| 原生固定目标间接调用循环，ns/次 | 2.246 | 1.936 | -13.77% |
| 原生随机双目标调用循环，ns/次 | 8.114 | 7.121 | -12.23% |

上表复制吞吐按逻辑读+写字节计算（每复制1B计2B），不是payload单向拷贝带宽、整机多通道峰值或PCIe带宽。随机链固定64B line、4KiB页、单依赖链，包含Cache/TLB与执行依赖，不是DRAM芯片裸时延。共享Host仍有其他模型工作负载，未测试空机峰值或全NUMA矩阵。

跨socket受控对照：Intel CPU18从node0本地128.766ns至node1远端209.555ns，+62.74%；海光CPU33从node2本地126.961ns至node4远端354.233ns，+179.01%。远端AVX2复制逻辑读写分别18.082/10.350GB/s。这证明当前两平台跨socket代价不同，但不证明模型对象实际分配在远端；旧NUMA绑定完整E2E没有改善的反例仍保留。

硬件现场：Intel每核L1D48KiB、L2 2MiB、每socket共享L3 105MiB（40核共享）；海光L1D32KiB、L2 512KiB、L3每共享域16MiB（CPU0域0–3，32域合计512MiB）。16KiB/256KiB/8MiB链海光更快，1MiB/32MiB明显更慢，256MiB本地基本持平，与两端L2/L3容量边界差异相符。不能从总L3大小推断单线程效果，也不能说缓存延迟全面更差。尚未证明真实Python/PyTorch指令和对象工作集恰好落入这些受损区间。

DMI：两端每socket均安装8条64GB DIMM；104 DDR5配置4800MT/s；海光DIMM额定5600、实际配置4400MT/s（应看Configured字段）。内存通道峰值和单线程延迟/吞吐不同：实际本地大工作集延迟相近、单核复制海光更快，因此不能用速率低8.33%直接解释Python路径慢50%。海光8NUMA/Intel2NUMA，远端访问需要单独关注。

真实Python/PyTorch旧GPU-off证据：Tensor view海光耗时+50.764%、周期+67.426%、指令-0.279%、IPC-40.439%，有效频率反而+11.052%。但V2原生直接/固定间接/随机双目标调用在海光均更快，固定间接调用约6.00周期，Intel约6.27周期；不能说CPU执行所有dispatch都需要更多周期。真实Torch dispatcher还包含解释器/调用栈/对象与分配器/引用管理/注册查找等，比热小循环复杂。没有实际路径cache/TLB miss和前后端停顿证据，流水线深度及唯一微架构原因仍unknown。

系统背景：104内核5.15.0-119、海光4.19.326；IntelSpectre-v2为Enhanced/Automatic IBRS，海光为Retpolines且Retbleed return thunk。官方Linux说明二者机制不同且可有性能影响，但sysfs状态不说明用户态库实际插入同样thunk，旧CPU探针系统时间远小于差距，不能直接把用户态IPC下降归因此项。本任务未关闭/修改任何安全机制。参考：https://www.kernel.org/doc/html/latest/admin-guide/hw-vuln/spectre.html 。Intel型号规格参考：https://www.intel.com/content/www/us/en/products/sku/231736/intel-xeon-platinum-8460y-processor-105m-cache-2-00-ghz/specifications.html 。

### PCIe当前边界及用户接续

两机8个物理MetaX端点及上游switch/root port均32GT/s x16，未发现降速/降宽。C588每物理模组有双die且只枚举一个GPU PCIe端点；还需区分单die与同模组双die并发Host传输，不能由每模组x16直接推成每die独享x16。实际H2D/D2H、host API发射、设备排队及空kernel launch尚未测；GPU-off的Python/Tensor差距本身不经过GPU PCIe，PCIe无法单独解释它。

104当前8GPU都在运行vLLM，故未注入PCIe压测。用户随后明确指示改在mx-59补测并询问CPU是否相同：已按inventory限定mx-59并通过connectivity；正在只读核对CPU/驱动/拓扑与空闲卡。原CPU/RAM结果仍绑定104，59如同SKU也不当成同机器；C588端选择空闲物理模组3的die6/7前仍须重新核验。不得停止任何已有服务。

### 产物

CPU两端远程根均为本记录前述cpu-platform-gap-20261105-01；源与控制脚本、build-static-v2-manifest、run-plan02、run-result02及110行逐次原始JSON保留；初轮校准文件亦完整保留。本地汇总 `/private/tmp/cpu-platform-gap-20261105/comparison-v2.json` SHA256 `027dd8a49c0853c20ce2a5d8a496b29498913148935c0f53757b867b7ba314b7`；相关文件清单artifact-manifest.json SHA256 `c5f0d75449c5d309cda4d6ad269d61e4e4cc4402b5d26dfd069ccc36b930b452`。旧PMU104摘要SHA1f0d386f…、海光89558c95…；完整SHA与只读源路径保留在本地prior-proof JSON中。

阶段状态：CPU/RAM微探针已完成，缓存容量/NUMA机制得到特定workload支持；真实Python热点的精确原因及模型E2E贡献仍待进一步验证。PCIe有效传输/launch接续59；未签任何模型性能或精度gate。

## PCIe/launch补测执行前冻结

CPU-REG-001最终证伪探针：鉴于原生调用快但Python路径IPC低，补测128次同寄存器依赖加法、8独立寄存器并行加法、128 NOP三种短循环，分离依赖链与独立指令吞吐；不从结果反推未公开的流水线深度。每项100万循环，每core2预热+5测量，PMU用户态cycles/instructions/branch计数全部保留；同一个通用x86-64共享对象在104构建后原样用于C588，Host仅ctypes加载本探针、不加载GPU库，nice19、20秒预算。Intel18/44、海光33/34/68（33/34覆盖launch交叉绑定），执行前核查core/SMT同胞负载<20%。仅新增本任务commands/register_probe.c和register_probe.so及register-result01，不覆盖旧探针；当前没有模型/算子候选变化。

用户明确指定mx-59并确认远端目录 `/public-flash/jinghao/deepseekV4/cpu-platform-gap-20261105-mx59-01`。只读已确认59与104同CPU型号/stepping、5.15.0-119内核、MetaX驱动3.8.1、PCIe5x16；当前59 GPU6/7空闲，C588物理模组3两个die（逻辑6/7）空闲。每次GPU调用前仍须复核占用，不使用0%利用率代替无模型进程证明。

PCIE-001：两端以既有Qwen35容器的SDK为独立诊断容器来源，保持全部目录挂载/模式/传播不变；源容器不编译、不跑GPU探针、不停服务。59源SDK无writable-layer改动；runtime SHA两端均941efe5d59db3e34c9fb525fe83702e20437a252c0706a00ff91982a7902a99b，镜像ID不同。新容器准备脚本会再次检查源SDK改动、源码/clone SDK指纹与原生mount-parity门禁。谱系只针对本探针消费的SDK文件，不是模型适配/精度gate。代码放已存在的相同bind映射，新增产物仅在pcie01/下。

预设测量：相同MACA C++程序，64MiB Host/GPU缓冲，绑定GPU本地CPU/NUMA并抽检Host页归属；4KiB/64KiB/1MiB/16MiB/64MiB、pageable/pinned、H2D/D2H各2预热+5测量全部保留；分别记录CPU发射、墙钟完成和stream事件跨度，不把stream跨度叫纯kernel时间。空kernel测批量异步发射与每次同步往返。再用同程序两进程READY屏障，在两个独立C550卡或C588同模组双die上做64MiB锁页传输，H2D/D2H各3个1秒窗口，按同Host单调时钟窗口并集计算聚合吞吐，不能只加不重叠峰值。该硬件探针不做模型请求、不修改框架/算子或系统参数；总预算每Host180秒，结束后进程退出释放GPU。

新容器名 `cpu-pcie-mx59-20261105-01` / `cpu-pcie-c5885-20261105-01`，仅sleep入口，无模型端口。环境准备命令在本地 `/private/tmp/cpu-platform-gap-20261105/prepare-gpu-mx59.py` SHA39ab89338c67b7de9cb916afdf631067247e659e1ab0a1b35c9cc870b53e6bea、prepare-gpu-c588.py SHAb411be79e4cfd02661f76bf990563683893e3ef816f78e2a2cac5292f3528e24保存后执行；create argv先写入远端commands再运行。首次仅在59验证，通过后才扩大C588。两端GPU/驱动/主机仍不同，传输差异属于平台组合，不自动归因CPU型号。

59环境门禁已通过：原生mount-parity passed、源SDK无writable-layer差异、source/clone五项SDK指纹一致，原源容器不变。首次构建成功但未执行；最终V2仅调整初始化辅助线程可用本地NUMA核心、计时主线程独立固定核心，避免把所有runtime线程压到同一核。最终C++ SHA256 `93a1e4993b3a9045fbe52994cd65832c49f505bf733a9aba76d86199b513ae9c`，公共ELF SHA256 `36c50106b0da5afd3cdf102064740818f3bad286c55e581a0fb405b22fb47ebb`，55504字节。控制器run_pcie.py SHA256 `66ac57384f6ed0d58077f1b3ca93c261c0d4be46367cabcbf8d3da0cf13d0340`，执行前写入远端commands/run-pcie01.py；先只在59跑完单卡与双卡，结束或错误均停止精确身份的本任务诊断容器并验证所选GPU无进程，保留源服务和全部结果。每次运行前检查所选物理板卡无任何GPU进程，并验证可见设备数2和每设备PCI BDF，Host缓冲为显式mbind+madvise+move_pages验证的mmap后按需注册锁页，减少分配策略差异。

59已完成PCIe单卡/双卡与空kernel共27.51秒，所有5轮/三并发窗口保留；GPU6/7已无进程，独立容器已停止。C588独立容器也通过mount-parity，五项SDK指纹与59完全一致；即将使用同ELF、同控制器测试空闲模组3双die。C588部署脚本install-pcie588.py SHA256 `6784b6badaff5d197f31e048bc473a22a56e0ca3976e72c395b0406b985e764b`；执行入口launch-pcie588.py SHA256 `4e6d5540154edbb37d7cc07c6ea8f83f62f586faaee6f364d52b047dc7745bd4`。

PCIE-CROSSOVER-001执行前冻结：C588初测已完成26.02秒并释放GPU，但die0/CPU33与die1/CPU34的空kernel发射存在差别，需拆分核心/设备/上下文因素。仅重启本任务独立诊断容器（精确ID6da5a946…），用相同ELF对调CPU绑定为die0/CPU34、die1/CPU33；相同全套2预热+5轮全部保留，不重跑并发负载。开始前板卡3无进程、两个core均<20%忙碌；总预算120秒，结束必停本任务容器并检查释放，不改任何源服务。控制源码crossover588.py SHA256 `30d7f8c7dab74bca0d6f75acd388c635ff0d019ff1f759ebee2dbde46935a941`，执行前部署commands/crossover01.py，结果另存crossover01.json，不覆盖初测。

## PCIe/launch完成结果与结论修订

59与C588均完成同ELF测试：59 27.51秒，C58826.02秒；全部单设备形状各2预热+5测量，两设备并发H2D/D2H各3个1秒窗口保留。Host页归属抽检均通过、可见设备数均2、PCI BDF核对成功。59设备6/7为ca:00.0与da:00.0两个端点，C588逻辑6/7都返回54:00.0同一物理端点。五项SDK文件指纹跨Host完全一致；GPU型号、底层驱动、OS和Host拓扑仍不同。

| 64MiB锁页传输，单向payload GB/s | C550/59 | C588-5 |
|---|---:|---:|
| 单设备H2D | 49.30 | 29.68 |
| 双设备并发H2D聚合 | 96.16 | 30.28 |
| 单设备D2H | 55.55 | 33.71 |
| 双设备并发D2H聚合 | 108.38 | 34.02 |

单设备栏为两个device的各自5轮中位数再取算术均值；并发栏为3个实际重叠窗口聚合值的中位数。64MiB锁页单设备轮内range/median均<2.54%；并发窗口重叠比例至少99.36%。C588单die大包比C550单卡低约39%–40%，两个die并发聚合仅约单die水平；C550双卡近似叠加。这直接说明该C588模组的Host传输存在共享上限，不能将每物理模组PCIe5x16当作每die独享同等Host吞吐。但上限具体在外部PCIe事务、模组内部转发、DMA/驱动组织还是NUMA节点的内存通道，需要继续拆分，不能因30GB/s接近某种理论值就宣布它实际降为PCIe4。sysfs链路检查仍全是PCIe5x16。

这属于CPU与GPU之间的Host传输，与GPU之间的MCCL/MetaXLink集合通信是不同路径；也不证明模型稳态在做大包Host传输。应结合真实H2D/D2H字节量和关键路径判断E2E贡献，不能把本表的39%或约68%聚合差异直接套给DeepSeek吞吐。

小包与pageable边界：已测全部4KiB/64KiB/1MiB/16MiB/64MiB。59五个pageable组range/median>10%（最高86.57%），C588部分4KiB/64KiB pinned组亦>10%。未丢任何计分轮，不对这些组签稳态或固定延迟结论；完整逐轮值保留analysis01。主结论采用稳定的大包锁页结果。单核RAM复制结果也不是DMA多通道峰值，不能用它排除NUMA本地节点内存通道对大包DMA的限制。

### 空kernel与交叉绑定：撤回固定平台加速比解读

初测batch空kernel平均每个完成墙钟约Intel59 3.98us、C5887.14us；发射主线程CPU约3.56/5.92us。每次launch后同步约14.51/27.98us。但C588两die/core差异促使同ELF交叉绑定：

| 配置 | batch完成墙钟us/个 | batch发射主线程CPU us/个 | 逐次同步墙钟us/个 |
|---|---:|---:|---:|
| die0/CPU33，初测 | 8.302 | 7.187 | 29.163 |
| die1/CPU34，初测 | 5.975 | 4.651 | 26.797 |
| die0/CPU34，交叉 | 2.514 | 1.993 | 13.138 |
| die1/CPU33，交叉 | 8.289 | 6.843 | 44.107 |

交叉时die1/CPU33的batch五轮还出现12.81/13.14/8.29/8.29/8.09us的明显变化；全部保留，不删前两轮。不能将初测+79.3%或+92.9%作为海光CPU型号的固定惩罚。核心/运行条件、runtime辅助线程布局、device上下文及Host调度/缓存交互尚未控制到底；无法仅由交叉断言CPU33硬件坏或某个die永远慢。GPU API本身包含driver/设备同步，不是纯Python/Torch dispatcher。

交叉原始结果SHA256 `2bdec43fa652217b2f79f36b762d4ed55e84801785f9e868bb90c4a9f1220894`，C588路径pcie01/results/crossover01.json；分析crossover-analysis01.json。两次C588GPU测试结束均精确停止本任务容器，源服务不变。

### CPU核内的最终寄存器探针

通用x86-64共享对象SHA256 `7840c47cb47fa068eac267842c60dca4c72703c512c7c353cd4353f764adca34`（16624字节）在两端完全一致；C源901f2b518276a641a9d42e99bbaa8373c001dc18747c6c1b606b53ffcdb95c4b，控制脚本381ce28067bee2fcde6836f0d155bd0d7afe86c1dc3cc2764ed6d3023cd40fc0。相同PMU、各core每项2预热+5测量；Intel18/44、海光33/34/68，全程无GPU库/模型调用；全部PMU无复用，最大wall/thread CPU比例Intel1.00095、海光1.00648。多个core方向一致。

| 纯寄存器短指令流 | Intel平均core中位IPC | 海光平均core中位IPC | 解释边界 |
|---|---:|---:|---|
| 8条独立链、128个ADD立即数/循环 | 5.918 | 3.999 | 海光每同样立即数加法需更多周期，时间约+33.31%；不是任意指令mix吞吐比 |
| 128 NOP/循环 | 5.523 | 4.998 | 前端/退休可达吞吐与指令类型相关，不等于前端宽度的严格上限 |
| 单寄存器128次ADD立即数链 | 5.893 | 1.015 | Intel可能有特定立即数折叠，不能把此值当通用ALU依赖延迟或流水线深度 |

反汇编已核对dep/parallel/nops的GCC constprop克隆：依赖链确为128条add $1,%rax，parallel为8个不同寄存器，NOP为128条0x90；没有RAM读写在计时循环内。Intel在这类ADD立即数链出现异常高IPC，与原始微基准研究中观察到的Sapphire Rapids立即数折叠现象相符（原始实验参考https://zenn.dev/herumi/articles/add-imm-fusion2?locale=en）；本轮未采集执行uop/端口事件，故将具体折叠机制记为候选，不能从这些测试反推出海光流水线有多少级。

该结果补强“CPU核内对特定指令模式的效率不同”，但未对真实Python/Tensor热点拆解cache/TLB miss、分支、uop供给和分配器/引用操作占比。不能用约33%寄存器探针时间差或其他单项差值精确解释全部E2E。旧Python view耗时+50.76%、周期+67.43%、指令近似、IPC下降的事实保持；基本原生函数调用海光较快的反例也保持。

### 汇总与下一步边界

本轮三方面已完成到可观测差异层级：Host传输存在实际吞吐差异与模组双die共享上限；本地大工作集内存未表现整体落后，特定Cache工作集和远端NUMA访问明显受损；CPU核内的特定短指令流也有每周期吞吐差异。实际DeepSeek Python/Tensor热点精确落在哪种瓶颈，以及各项E2E贡献，仍需在真实路径对齐cache/TLB/分支/Host数据传输与rank到达时间，不能宣布“CPU型号唯一原因”或优化完成。当前未修改任何推理源码、系统参数、安全缓解机制或原模型配置。

CPU微探针全部退出；GPU独立容器均停止。59 GPU6/7已无进程、显存862MiB/卡，约等于原861MiB设备基线；C588模组3释放复核在resource-release01.json。所有原模型服务没有被本任务停改。GPU源码/ELF/命令、inspect、SDK SHA、挂载diff、全部raw/result/analysis留在各自远程pcie01；只在仓库记录摘要。

PCIe原始：59 pcie01/results/run01.json SHA256 `f762756ade4c08af4b86b936aa961a63f43d8ba0dc7516105b02b8b08c268235`；C588 pcie01/results/run01.json SHA256 `e4ba7c2430ddad6583156e8a30bfb0e8b2ba8c90ad536ea64df96fb13cbc2dd6`。本地汇总pcie-comparison.json SHA256 `12317eb0150e6ee8ed4da81110a0ca43845c137436848886674704909104efe1`。寄存器原始104 register-result01.json SHA256 `4b80e1de73596c2a7ab94255108cb662af6584697aee163985c1a139fd0dbcf6`；C588同名SHA256 `ab8588914181c9068acc8dd12b4ecf2e877d9d3c32de428c9506be6c4f0cf612`；本地register-comparison.json SHA256 `b496dabd29da31b701bb56bf28c22903a3e0a89eb66cc105b6899c18b73dd01c`。

最终状态：diagnostic完成，证据为这些受控微负载下的可重复观察；CPU SKU唯一归因、模型E2E分摊、正式精度及优化验收均未完成/不适用。没有候选保留或源环境回退需求。

资源释放最终复核：59诊断容器running=false，GPU6/7均无进程、各862MiB；C588诊断容器running=false，模组3无进程、1727MiB，与预检基线一致。回执分别位于各远端pcie01/results/resource-release01.json；没有停止或重启原Qwen/DeepSeek等模型服务。
