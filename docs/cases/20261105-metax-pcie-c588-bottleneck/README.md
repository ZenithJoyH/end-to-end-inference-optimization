# C588 Host PCIe 单 die 与双 die 带宽归因

状态：受控诊断完成，`reproduced`（2026-11-05）。延续 [CPU 平台差异案例](../20261105-metax-cpu-platform-gap/README.md)，不构成模型优化、精度 gate 或正式性能验收。

## 当前结论

**C588 本地内存下单 die 约30/34 GB/s、双 die不叠加，最匹配“模组与主机之间存在公共I/O瓶颈及其配置约束”。普通memcpy提交方式和本地RAM的顺序流带宽不足，均不足以解释这个上限。** 但仍不能在模组内部公共通道、海光root complex/I/O coherency、驱动初始化/映射与固件配置之间签发唯一根因。

主要证据：C588两个逻辑die共用一个PCIe BDF；两个独立进程有真实重叠，合计仍约30/34 GB/s；改用GPU kernel直接读写注册Host内存，双die合计仍约30.4/34.2 GB/s。换大页、同步/异步API、自带pinned分配均未解除上限。本地RAM四核实际单向读/写46.24/57.22 GB/s，高于该上限。

**NUMA混用另有严重的放大效应。** 两个die的buffer分别位于同插槽node2/node3时，D2H合计降为约2.1 GB/s，复测与大页均重现；两个buffer都放在node3则恢复约34。不能简单称为远端节点RAM本身带宽低，也不能认为只绑CPU线程就能修复。

未停止、重启或修改现有模型服务，没有发送模型请求。所有GPU诊断结束后容器已停止、所选设备无进程，其他GPU进程行未变。短时探针仍使用Host公共资源，未测业务延迟，因此不宣称业务性能零扰动。

## 最终对照结果

单位为有效payload GB/s，H2D=Host→GPU，D2H=GPU→Host；双设备按真实union完成跨度合计，不是把独立中位数相加。持续并发引用`confirm03`，直接Host访问引用完整校验的`zero02`。

| 对照 | C550 / 59 | C588 |
|---|---:|---:|
| 单设备mcMemcpyAsync H2D | 49.31 | 29.94 |
| 单设备mcMemcpyAsync D2H | 55.41 | 33.62 |
| 双设备同向H2D合计 | 96.90 | 30.72 |
| 双设备同向D2H合计 | 110.30 | 34.00 |
| 双设备反向并发H2D+D2H合计 | 101.79 | 34.11 |
| 对调方向的反向并发合计 | 101.64 | 34.05 |
| 单设备kernel直接读Host（256 blocks） | 35.53 | 30.79 |
| 单设备kernel直接写Host（256 blocks） | 38.06 | 34.13 |
| 双设备kernel直接读Host合计 | 69.10 | 30.43 |
| 双设备kernel直接写Host合计 | 75.54 | 34.23 |
| 同一kernel的HBM→HBM payload | 569.95 | 573.00 |
| 四核本地RAM顺序读 | 52.02 | 46.24 |
| 四核本地RAM non-temporal写 | 78.42 | 57.22 |

直接Host访问通过`mcHostGetDevicePointer`获取指针，以GPU load/store避开memcpy复制实现，但仍依赖驱动注册、GPU MMU和公共I/O路径，不能完全排除驱动。C588单die的64/256/1024 blocks三组H2D为30.92/30.79/31.26，D2H为34.04/34.13/34.12；不同API/kernel在相近区间收敛。kernel未被证明最优，不能反过来把测量值当成物理理论极限。

双die直接读份额约25.40/5.92、直接写约27.21/7.10 GB/s，公平性不如memcpy约均分，但合计预算仍未翻倍。直接读重叠最低95.62%，直接写最低98.46%；持续memcpy双向重叠98.6%–99.7%。所有计分轮保留。

## NUMA复测及机制边界

以下为C588；复测首尾本地参考约30.06/33.60和30.03/33.67，排除了整个实验过程普遍变慢的解释。

| 变量 | H2D GB/s | D2H GB/s |
|---|---:|---:|
| 同插槽node3、单节点buffer、单die | 29.56 | 33.65 |
| 跨插槽node6、单节点buffer、单die | 23.90 | 30.86 |
| 单buffer按4KiB页交错node2/3、单die | 28.06 | 6.73 |
| 同样交错、实际2MiB THP、单die | 28.24 | 30.08 |
| mcMallocHost（落点无法验证，单列） | 30.13 | 33.58 |
| 双die两个buffer都node2（合计） | 30.72 | 34.00 |
| 双die两个buffer分别node2/node3（合计） | 14.53 | 2.09 |
| 双die分别node2/node3且实际THP（D2H合计） | 未测 | 2.07 |
| 双die两个buffer都node3（D2H合计） | 未测 | 33.99 |

分节点D2H首轮2.11、复测2.09 GB/s，真实重叠均约99.96%以上；59分节点D2H约110.26，没有同量级退化。4KiB交错与THP的对照支持页粒度/物理连续性参与；大页却不能修复两个buffer分节点的并发退化。这将额外问题收敛到不同NUMA物理地址混用时的I/O请求、翻译或一致性路径，尚未测到实际GPU页表粒度、SG段数和翻译命中率，不能宣称定位到具体TLB或映射bug。

## 驱动、链路与仍需区分的部分

| 项目 | C550 / 59 | C588 |
|---|---|---|
| CPU / NUMA | Xeon Platinum8460Y+，2节点 | Hygon C86-4G（OPN7493），8节点 |
| OS kernel | 5.15.0-119-generic | 4.19.326-0092.3.1.ctl3.x86_64 |
| MetaX KMD | 3.8.1 | 3.9.61 |
| 实测设备 | 两张独立卡，各独立PCIe BDF | 同模组两die，共同54:00.0 |
| endpoint MPS / MRRS | 256B / 4096B | 256B / 512B |
| 驱动runpm / runpm_link | 1 / 1 | 1 / 1 |
| xvm_page_size / pcie_width_index | 9 / 0 | 9 / 0 |

两端使用相同MACA 3.7用户态SDK关键文件指纹及每一版公共ELF，但KMD、OS、CPU和GPU拓扑仍不同。没有仅因镜像相同就把驱动视作一致。

设备至root port全链路在sysfs/lspci/mx-smi报告32 GT/s、x16；前后endpoint、switch、root port的AER计数均为0，没有观察到降代或半宽。不能仅因约30GB/s称其为Gen4，也不能以AER为0排除所有协议或内部瓶颈。设备没有iommu_group，C588的/sys/class/iommu为空；这不代表GPU自己的MMU不参与。

MRRS差异可能影响设备读Host内存的请求效率，但没有设置寄存器做A/B，不能定因，更不能单独解释D2H及反向并发共享约34GB/s。含义参见[Linux PCI API](https://kernel.org/doc/html/latest/driver-api/pci/pci.html)。

另有省电配置核对项：当前runpm=1，而[沐曦C500系列3.9.1驱动安装指南](https://developer.metax-tech.com/api/client/document/preview/%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97/%E9%A9%B1%E5%8A%A8%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97/%E6%9B%A6%E4%BA%91C500%E7%B3%BB%E5%88%97/3.9.1/split_files/%E5%AE%89%E8%A3%85%E4%B8%8E%E7%BB%B4%E6%8A%A4.html)要求C588关闭省电模式。传输采样中XCORE已升至1416MHz、MC1800MHz、链路仍报告Gen5，不能把空闲450MHz或runpm值直接当作根因。需要厂商结合当前3.9.61确认，在维护窗口单变量验证；本轮未修改。

只读检查已安装`/usr/src/metax-linux-3.9.61`：pcie_width_index/group_num/group_index是MCM参数，公开C源码检索仅见声明/定义，不能据0/1数值推导lane分配。`metaxgpu/metax_ttm.c`存在get_user_pages_fast与SG/DMA映射流程，但未对实际映射分段和内部仲裁采样，不能把源码存在当作热点命中。

RAM的顺序流余量不排除海光root complex、I/O fabric、BIOS或DMA小请求效率。本轮在保留服务条件下的区分已经完成；进一步区分海光公共I/O与C588内部通道/驱动固件配置，需要维护窗口的受支持KMD/固件/PCIe配置A/B，或同一C588模组在Intel平台的同口径对照。应先把这里的最小复现交给厂商确认MCM Host接口预期总带宽及跨NUMA并发写退化；不直接在线改驱动或寄存器。

未把PCIe差距换算为DeepSeek/Qwen端到端贡献；此前纯CPU Tensor元数据微基准不经过PCIe，其结论不能由本轮Host带宽替代。

## 冻结的范围与方法

- 对象：mx-59 的 C550 空闲卡 6/7，对比 mxC588-5 空闲模组 3 的逻辑 die 6/7。仅使用既有专用诊断容器；不修改、停止或向现有模型服务发送请求。
- C588 其他模组均有模型进程，本轮不能做跨模组实测；不得把利用率 0% 当作设备空闲。
- 待区分机制：Host NUMA 内存落点/页大小、同步/异步复制 API、同模组共享传输通道。只读核查链路速率、MRRS/MPS、IOMMU、AER、驱动版本；不修改 PCIe 配置、驱动参数或全局内存策略。
- 新产物子目录：59 `/public-flash/jinghao/deepseekV4/cpu-platform-gap-20261105-mx59-01/pcie02`；C588 `/data/jinghao/deepseek/cpu-platform-gap-20261105-01/pcie02`。沿用用户已确认的Host/任务目录，探针、关键配置及精确binary执行计划在执行前保存。
- 单变量探针：64 MiB 伪随机数据，注册 pinned 内存；默认 4 KiB 页，THP 仅在 smaps 证实后按大页解释；每组 2 次预热和 5 次计分，全部保留。逐组查询 64 个页面实际 NUMA 落点；CPU 固定在设备本地节点。单设备 16 次复制/轮，双设备 64 次复制/轮，以完成同步后的墙钟时间计算有效 payload GB/s。
- 双设备比较：同向、反向、Host buffer 同节点/分节点，记录真实重叠和联合完成跨度；未达到重叠要求不声称并发带宽。每组之间短暂停顿，避免持续压满现有服务所在 Host 的内存系统。
- 独立容器身份、SDK 指纹和挂载一致性重验后才运行；结束或失败均停止本任务专用容器并核查设备释放。既有模型进程存活检查只作为未停改服务证据，不宣称业务性能零扰动。

## 前置观察

此前同一 SDK/ELF 测得单设备 H2D/D2H：C550 为 49.30/55.55 GB/s，C588 为 29.68/33.71 GB/s；双设备同向合计为 C550 96.16/108.38、C588 30.28/34.02 GB/s。尚不能据此唯一归因于驱动、CPU root complex 或模组内部 DMA/桥接通道。

本次预检两端设备到 root port 均报告 32 GT/s、x16；MPS 均为 256B。设备 MRRS：C550 4096B，C588 512B。该差异可能影响设备读 Host 内存的并发效率，但仅凭配置不能证明吞吐差距因果，且不直接解释全部 D2H 差距。

## 结果与归因

首轮已完成：两端专用容器均已停止，所选设备无进程，其他 GPU 进程行未变。C588 本地注册内存单 die H2D/D2H 29.97/33.64 GB/s，同向双 die 合计 30.49/34.07 GB/s；大页 30.19/33.58，同步 API 29.83/33.12，均未消除上限。

C588 两个 Host buffer 分别置于 node2/node3 时，同向双 die H2D/D2H 合计降为 14.52/2.11 GB/s，五轮全部复现；4 KiB 页交错分配于 node2/node3 的单 die D2H 6.76 GB/s。单独使用 node3 时仍可达 33.65 GB/s，因此不能简单解释成 node3 本身的 RAM 带宽很低。

独立复测 `confirm03`，不覆盖首轮：双设备改为每轮至少 300 ms、每 4 次复制完成同步后检查期限，保留 2 次预热/5 次计分及实际重叠；复测分节点异常、两个 buffer 均在 node3、THP 交错和 THP 分节点。运行时自带 pinned 分配不再强制页面查询成功，但其实际落点未知时单列，不能冒充同 NUMA 对照。两端共用新 ELF，其他条件保持。原来固定等字节数的双向组存在提前结束，不能把联合批次带宽当成持续全双工带宽。

未进行驱动替换或 PCIe 配置 A/B，不能以排除部分内存因素代替唯一根因证明。

### 追加直接 Host 访问对照（zero01，执行前冻结）

SDK 头文件 `/opt/maca/include/mcr/mc_runtime_api.h:2768–2792` 明确支持对已注册 Host 内存获取 GPU 可访问指针。使用同一 pinned Host buffer，通过 GPU kernel 读写该指针，与 `mcMemcpyAsync` 比较，以检查 memcpy/DMA 路径之外是否仍有链路余量；不修改驱动、页表策略或现有模型。

64 MiB、设备本地 NUMA，kernel 为 uint64 顺序合并访问，256 线程、64/256/1024 blocks，写后 system fence；2 轮预热/5 轮计分，提交和完成同步全部计时。另测 HBM→HBM kernel 控制组、双 die 同向 kernel 并发，按前述至少 300 ms/轮记录实际重叠。kernel 未证明最优时，其较慢结果不能反向证明物理通道上限；若正确性检查通过且明显超过 memcpy 上限，才说明该方向的物理 Host 通道尚有余量。全部结果只属于硬件诊断，不替换模型算子。

复测控制器曾两次在挂载回执文件命名检查处失败（`confirm01`、`confirm02`），均未启动 GPU 探针。修正为独立 manifest 子目录后 `confirm03` 完成两端全部组，保留失败记录，不作为吞吐轮次。

`zero02` 保持计时 kernel 和矩阵，在计时后额外将目标清零、再次复制并逐 uint64 校验完整 64 MiB；避免原缓冲区已有相同内容掩盖未发生实际写入。最终引用 `zero02`，`zero01` 保留为初探，不用于正式归因。

### 最后一项 RAM 对照（ram01，执行前冻结）

仅对设备本地 NUMA 节点的自有 512 MiB 内存进行四物理核 AVX2 全 cache-line 读、non-temporal 写；实际页面落点查询验证。只选同节点 CPU 及其 SMT sibling 均低于 10% 使用率的四个核，否则跳过。每组 2 轮预热、5 轮计分，单轮至少 120 ms，轮间 200 ms 间隔，nice19；同一静态 ELF 两端执行，不运行模型请求。读、写各按单向有效字节计数，不以读写合计字节与 PCIe payload 混比。该项可检查 RAM 顺序流带宽余量，不能单独排除 root complex、I/O coherency 或小请求效率问题。

## 复现、原始产物与释放

两端上述pcie02根目录下，`commands/`保存源码/controller/config、每组精确命令和build命令；`manifests/read-only-evidence01.json`为筛选后的拓扑/驱动证据，`manifests/{confirm03,zero02}/mount-parity.json`为重验回执。`results/run01.json`、`confirm03.json`、`zero02.json`及逐组JSONL保留全部轮次，`analysis-confirm03.json`、`analysis-zero02-verified.json`为统计及完整校验回执；`ram01.json`为RAM原始轮次，`postcheck01.json`为链路/AER和GPU容器停止回执，`clock-bandwidth-*.json`为采样。

59的RAM控制器正文在执行后归档为`commands/ram-controller-archived-after-run.py`；两端源码和精确binary计划在执行前保存，C588控制器正文也先保存再执行。未隐瞒首轮mcMallocHost落点检查incomplete、confirm01/02控制器失败或zero01弱校验初探；最终分别采用confirm03和zero02。

| 公共产物 | SHA256 |
|---|---|
| run01 ELF `probe` | `4e55b1bea1391c25d2aaa2c23c7265322436d4dbd6ac584dc8b2602e6624c88b` |
| confirm03 ELF `probe-confirm` | `f6255e36732db4851bf25caef0af0124915551cc1ebcec65f149f1e36dda39fe` |
| zero02 ELF `probe-zero02` | `7578b4212bce3a899fa035812356bc76eee50396195e1f3784966226fbabfce3` |
| RAM静态ELF `ram-probe` | `f05eb03f851b1d2905c9e60fdfad38753af35d48bc85c557dad826ba33c39194` |
| RAM源码 `commands/ram.cpp` | `557c3d11c06a2f76e0b0c6f069ff8c46e62eefe58cf32114f810e33f4bb08bba` |

无需回退生产配置：本轮没有改变系统参数、驱动、固件、模型代码或生产配置。独立容器保留为stopped，测试进程退出；后续复现须重新核查设备无人占用，不能照搬旧空闲状态。

最终`results/resource-release-final.json`核验：59卡6/7各862MiB，C588模组3为1727MiB，均回到测试前基线、无设备进程，专用容器均为stopped。原有模型GPU进程在每轮开始/结束对比中未变。完整校验回执、5轮保留数及RAM10条计分记录已独立复核；本地`git diff --check`通过。

2026-11-05 按用户要求将本轮结果及此前CPU/缓存对照汇总到飞书[《Xeon 8460Y+/Hygon 7493对比》](https://jwolpxeehx.feishu.cn/docx/SQD7dLAipogFiYxMCKwceXignEg)。文档区分104历史CPU测试与59本轮PCIe/四核RAM测试，以C550为基线，保留归因边界和资源释放记录；浏览器回读表格并确认“已经保存到云端”。

同日按用户要求将飞书全文改为仅呈现CPU/GPU型号：移除机器编号和专属路径，NUMA位置改用已定义的逻辑标签，保留不同物理系统来源的说明。回读确认5张表的全部单元格符合修改预期、性能数值不变、无机器标识残留，且已保存到云端。本地和远端原始证据继续按真实Host绑定，未改写实验身份。

随后按用户指定的三个问题重组飞书为PCIe传输代价、RAM带宽/延迟、dispatch cycle与微架构因素三章。补充按有效带宽换算的64MiB均摊复制时间，并从既有CPU-only PMU证据列出Tensor view周期/指令/IPC；明确该代理路径额外cycle已测到，流水线深度和L2的真实因果贡献仍待拆解。5张新编排表回读与预期数值一致（仅3.10被表格显示为3.1），继续仅使用型号并已保存到云端。本次仅文档整理，未发起新硬件或模型测试。
