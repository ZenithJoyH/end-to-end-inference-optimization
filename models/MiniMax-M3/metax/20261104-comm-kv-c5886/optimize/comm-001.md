# comm-001 C588通信显存分阶段诊断

- 状态：complete（通信显存诊断）；framework；不作为无profiler吞吐结果。
- 目标：测得每rank通信资源的可归因显存增量，区分CUDA/MACA context、PyTorch process group、vLLM/PyNccl communicator、首次collective/peer连接、模型与graph。

## 优化方向与瓶颈依据

历史init_snapshot在通信初始化后，约4.11 GiB/rank总占用不能直接视为MCCL；后续约1.35 GiB non-Torch增量也不是纯通信。当前源服务占用全部16die，不能与探针争抢显存。

## 优化内容与适用边界

只在独立优化容器内运行。保留源容器、源码、启动脚本、原日志和挂载。新容器保持/data→/data及rslave传播，独立缓存、日志和端口；创建前后核验镜像有效状态及mount parity。vLLM源码只读，必要观测通过进程内诊断包装；不修改模型数学语义。

新进程按实际源码边界观测：绑定设备/context初始化→默认process group→vLLM TP/PP/DP组及PyNccl初始化→首个collective→多尺寸collective→销毁并退出。分别保存设备free/total、torch allocated/reserved、峰值及同步时点；不重复相加不同统计时点。每个rank单独记录，报告min/median/max及总和。纯context对照与通信进程隔离，至少重复3次；默认通信配置与C550四通道/1MiB策略分开记录，不将配置字符串当作生效证据。

如需要模型启动级观测，另记录权重加载、profile、KV分配、graph capture后时点；探针结果与真实服务初始化增量互相核验，不能用合成process group冒充所有生产communicator的精确分配。

## 服务切换与恢复方案（原方案，现已完成）

已核验目标为mx588-6、容器minimaxM3、API端口18050、模型minimax-m3、TP16。2026-11-04只读快照的API宿主PID为404527，EngineCore为404820、workers为404842–404857；执行时必须重新解析，不能直接使用历史PID。

只对匹配完整模型、端口和容器的API进程发送TERM，等待关联workers退出并确认16die空闲。保留容器，不执行docker stop/restart/rm，不影响其他进程。不自动扩大到KILL；未排空或未退出时停止推进并说明。

诊断服务使用独立端口18150。完成后停止本任务服务，按原start-model.sh的有效参数恢复minimaxM3内18050服务，恢复输出指向本案例新的restore-service.log，避免覆盖原service.log；检查/v1/models、readiness和配置一致性。用户已在当前任务明确答复“允许暂停并在诊断后恢复”，授权限此服务及关联workers，不涉及停止源容器或其他模型。

## 正确性与路径命中

通信探针已核验实际MCCL路径，全部rank数值校验通过；详见下方完成观测。未运行新的模型精度/性能测试。模型级优化仍须baseline-sanity与graph证据。

## 性能效果

not_run。内存观测阶段不用于吞吐比较；对吞吐的影响由关联C550同机KV实验验证。

## 决定、风险与回退

显存机制诊断完成，未保留模型配置优化；源服务已恢复。KV吞吐贡献仍incomplete，C550按用户要求停止。禁止直接提高利用率到0.96或将总non-Torch显存全算MCCL。

## 外部证据

远端计划根：/data/jinghao/minimaxM3/20261104-comm-kv-c5886。首次变更命令（执行前登记）：`./scripts/playbook /private/tmp/minimax-m3-comm-kv-20261104/prepare-c588.yml --limit mx588-6 --ask-pass --check --diff`，核对后移除`--check --diff`执行。Playbook只创建新case目录、保存控制脚本和脱敏inspect、从精确源image创建并启动CPU空闲命令的新容器，再用项目工具校验挂载；不停止源服务。

本地控制脚本`/private/tmp/minimax-m3-comm-kv-20261104/prepare_container.py`，远端执行副本位于`commands/prepare_container.py`；实际创建argv、源/目标inspect、挂载diff及门禁回执在`commands/`和`manifests/`。历史证据见docs/cases/20261104-minimax-m3-metax-cross-topology/README.md。

执行路径调整（执行前登记）：为避免文件传输检查的长等待，使用项目Ansible raw入口传送已审阅prepare及项目挂载校验器，先保存命令文件并核对SHA再执行。本地可读bootstrap为`/private/tmp/minimax-m3-comm-kv-20261104/bootstrap-mx588-6.py`，命令为`./scripts/ansible mx588-6 --limit mx588-6 --ask-pass -m ansible.builtin.raw -a "python3 -c <bootstrap源码>"`。只创建独立空闲容器，源服务暂不停止。

容器门禁已通过，远端`manifests/container-gates.json`确认精确源image及mount_parity passed。诊断脚本部署（执行前登记）：本地`deploy-probe-c588.py` SHA256 `f958216c0f28c72a1f2a26cb755606926cb429e9a3f4d3261f7254e63b14bb48`，经`invoke_ansible.py --host mx588-6 --file .../deploy-probe-c588.py --ask-pass`发送。它先校验原launcher和profile SHA，保存只读profile快照、恢复脚本、暂停脚本和通信探针；不立即暂停服务。

准备就绪后在Host执行`python3 <case>/commands/pause_source_c588.py`（仅空闲、精确匹配18050/模型/容器时TERM），再以独立日志后台运行`python3 <case>/commands/run_probe_suite_c588.py`。探针复用目标镜像实际`init_worker_distributed_environment`，观测原生GroupCoordinator、PyNccl/MCCL构造、首次all-reduce和TP大张量通信。默认策略与4通道/1MiB策略各3次全新16rank进程，每次900秒硬预算，保留全部成功/失败原始数据，不用显存观测时间计算E2E收益。worker结果做端点值校验，所有rank必须完成；失败停止后续运行并恢复源服务。

恢复入口已准备：`docker exec minimaxM3 /bin/bash --noprofile --norc <case>/commands/restore-source.sh`。它按原参数和原缓存启动18050，日志另写`<case>/logs/source-restored-service.log`，原service.log不覆盖。恢复前确保诊断进程和优化服务全部退出并核验设备空闲；恢复后核对模型列表/readiness。

## 已完成观测（2026-11-04）

通信探针两种策略各3次全新16rank，全部96个rank通过全尺寸all-reduce端点sum=136校验，无失败轮。设备free/total差分在张量释放、GC及empty_cache后测量，此时torch allocated/reserved均为0。实际库为 `libmccl.so`，`MCCLLibrary` 来自 `vllm_fl.dispatch.backends.vendor.metax.patches.pynccl_vllm024`。配置、context、group、native CommInitRank、首次all-reduce等边界均单独保存；没有加载模型、分配KV或capture graph。

下表为各策略48个rank样本的中位数，单位GiB/die，非整机总显存：

| 边界 | 默认通信 | 4 coll通道/1MiB策略 |
|---|---:|---:|
| context基础占用 | 1.504692 | 1.504681 |
| 分布式初始化后总占用 | 4.110428 | 2.407070 |
| 初始化相对context增量 | 2.605730 | 0.902395 |
| 大尺寸TP collective并清理张量后总占用 | 5.420860 | 2.863869 |
| 全通信路径相对context增量 | 3.916161 | 1.359184 |

默认策略通信路径增量min/max为3.916130/3.916180 GiB，策略之间每die总占用差2.556992 GiB。默认策略在init之后，首次TP collective再增加0.684959 GiB，8192×6144 BF16大通信再增加0.625458 GiB，合计1.310417 GiB，解释了历史约1.35GiB的profile期non-Torch增长大部分来自通信延迟分配的机制，但不能把合成探针精确等同真实模型的全部profile增量。

销毁通信组后，默认策略每die释放3.886936 GiB，剩余context及少量driver资源；这进一步支持差分来自通信路径。这里“通信占用”包含MCCL、设备侧连接/peer/driver资源，**不等同MCCL日志单个communicator的buffer字节数**；更不能把4.11GiB全部算通信。

实际命中：默认日志为32 coll channels/32 p2p channels；限额策略为4 coll channels/**16 p2p channels**，虽MAX_P2P_NCHANNELS=4被读取，实际拓扑仍建立16个P2P通道，不把环境值4当成P2P实际4。BUFFSIZE=1048576、MIN/MAX_NCHANNELS=4均有原生MCCL读取日志。该策略只测显存，没有服务级吞吐/数值/graph验收，不作为已保留优化。

源服务已按用户授权暂停并在探针结束后恢复原18050、原TP16/0.92/maxlen70000等配置。恢复日志另写 `logs/source-restored-service.log`，原容器保持运行，原launcher/profile SHA复核无变动。`/v1/models`与完整API参数验证通过，restore-ready回执SHA `14436a22521ca39fbad0cc6fb85e5017b4c8c6d24a4e192dededc1b2f08233c1`。此后C588不再承载本轮实验。

精确汇总：`results/communication-summary-compact.json` SHA `da6f955b6a534d73758cd179a9f824b0f7b3d7d938e71e99930a5fc5999c78bb`，路径均相对远端case；完整rank JSONL、逐轮日志、argv及done回执仍在results/与logs/。相关C550容量A/B/A继续，当前尚不能宣布KV容量是跨硬件端到端差距的主要原因。

方法边界：实际使用每个新进程内、通信前的context_ready基线，没有另外运行只含context的进程组。1.50GiB仅称通信前基础占用，包含已有设备基础与当前context，不把它全部当纯context成本。差分由同进程边界、三次重复及通信销毁释放共同核验。关联C550实验后已按用户要求停止，当前只完成既有证据分析。

## 2026-11-05：通信显存来源的只读再归因

用户要求继续分析 C588 通信显存为何更多。本次只读取历史探针 96 rank 记录、原生日志、当前源容器源码与二进制，不重启服务、不运行新的通信或推理测试。C550102 源容器已停止，未启动；通过 docker cp 流式哈希读取。

已核对：TP 与 EP 各创建并预热 1 个 16-rank PyNccl/MCCL 通信器；MetaX `pynccl_wrapper.py:464–470` 又将普通 all_reduce 改为 torch.distributed，在首个正常 TP collective 时惰性建立第三个通信器。默认首轮 16 rank 日志共有 48 个原生通道/初始化事件，匹配 3 套/rank。单例 DCP/PCP/PP/DP 组没有可测设备增量。此框架行为不是 C588 独有，主要放大每套资源成本，不得直接称两套 PyNccl 全部无用。

归档前登记：将精确只读结果、源码摘录/指纹及原因分解保存至远端 `results/communication-causes-20261105/`，仅新增该唯一子目录；执行控制副本先保存 `commands/archive-communication-causes-20261105.py` 并核对 SHA。该归档不接触模型、源配置或缓存；完成回执及汇总 SHA 更新至 state.yml。

归档已完成，所有6个JSON逐文件SHA验证通过；汇总 `communication-causes-20261105.json` SHA256 `0c966993a6871d33e4a24cd0440ac2afc752203a553736ceeccbb242667b5d94`，控制脚本SHA256 `c12e1b93845b3278e8081f6f76a040a84be9f06147741bdbf0a7f381965f95d0`。详见[原因分解报告第5节](../../../../../docs/cases/20261104-minimax-m3-metax-comm-kv-diagnosis/README.md)。

| 原生运行参数 | C550原日志 | C588默认 | C588限额 |
|---|---|---|---|
| collective/P2P通道 | 4/4 | 32/32 | 4/16 |
| P2P通道/peer | 1 | 4 | 4 |
| P2P chunk | 128KiB | 1MiB | 1MiB |
| Init COMPLETE typical used/rank/comm | 8.085MiB | 686.338MiB | 430.050MiB |

MCCL自身used统计不与物理总占用重复相加。C550显式启用tuning-ar512k.cfg；C588基础通信环境只有DEBUG，不等于完整策略对齐。同C588策略对照省下2.557GiB/die（65.29%）已实测，但通道、BUFFSIZE和P2P cap共同变化，未分别归因。三套通信器是共同框架机制，放大每套成本，不构成C588独有框架缺陷的证据。

两端当前libmccl.so、libmcruntime.so逐字节SHA相同（C550102源容器已停止，仅读取未启动），原生日志均MCCL2.16.5；当前代码相同不倒推历史二进制绝对相同。默认普通TP路径切到PyTorch但仍保留TP/EP PyNccl的初始化资源，可解释初始化后继续增长的机制；未证明PyNccl对其他collective全部无用，不能直接禁用。限额后较大的P2P/peer资源规模有日志证据，但驱动、拓扑及tuning各自贡献未拆，尚无ALLOC调用栈归因或新模型级验收。

上述内容已按用户要求汇总至[飞书文档](https://jwolpxeehx.feishu.cn/docx/DuwsdmPo7oi979xodNac0OVknab)第3.5节（2026-11-05补充），仅使用机器型号；参数表、三套通信器说明及未验证边界已在浏览器核验，显示已保存到云端。本次仅编辑文档，不改变模型服务状态。
