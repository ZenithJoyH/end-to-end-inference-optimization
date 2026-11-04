# accdiag-050：PLE原地状态写回同步与编译路径定位

## 授权与执行范围

用户2026-10-20授权继续定位049遗留PLE状态写回不一致，重点区分原地读写同步和编译问题，保留首次差异完整证据；明确不恢复8010、不访问8035、不重跑全量GPQA。本轮按inference-accuracy-diagnosis/key-operator-analysis执行；隔离算子对照的正确性采用inference-accuracy-evaluation minimal-regression，不能签模型gate。保留attention/MoE FP32、Gems i64/randn、QSA M16、黑名单和固定QK；不改原安装、049候选、现有PR或模型服务。

Host=PPU-07；容器qwen3.8-flash-opt-ppu07-20261015；CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-016-full-gpqa-ppu07-c64-fp32-fixed-qk-20261020。新D=CASE/diagnostics/accdiag-050-ple-state-sync-20261020；仅在容器私有`/opt/qwen38-accdiag050-ple-sync-20261020`放实验variant和独立cache；GPU仅物理8，先核无进程/资源，资源不足停止，不碰0–7/其他服务。库存目标已解析；首次connectivity-check因本地Ansible RPC启动受sandbox影响失败，提权重跑成功并返回实际hostname，不以普通SSH退出码替代；PPU8只读预检无进程/102MiB。

## 冻结问题与证伪计划

049私有i64源码SHA611e4bc04be29c654c0d40f67d735b37e7af4a01d8bfd15768a7df654a95e180，原版163ebcd33074941a65ba8767ad518a4cf38073833f4617d1e59edfe60bc4e03b。已保存decode/spec/prefill channels10240低索引1/2/3/-1的输入、完整旧状态/CPU参考和18次结果，原版/候选均有state mismatch且数量不稳定。地址修复独立边界通过不替代此问题。

已读旧TTGIR的blocked layout为sizePerThread=[8,1]、threadsPerWarp=[16,2]、warpsPerCTA=[1,4]，二维为[C,S]：同一channel的history跨warp分布，源码注释“CTA读完再写”并未显式提供跨warp同步。这只是可检验嫌疑，不预先当编译误算或事故根因。

1. 先CPU-only读取原049 PT，验证来源/SHA，统计首次不一致的row/channel/history位置及值的来源（原始history或后续被写入值），检查不同CTA写集合不交叠、每CTA内部history读写依赖及有效mask；不重新生成随机输入。
2. 物理8小范围同输入单变量A/B/A：i64原state kernel；仅在旧state加载后加CTA barrier；同kernel改为只读snapshot/不同写地址（诊断性out-of-place，不保留到模型）；仅num_warps=1的布局哨兵；最后回到原i64。每mode decode/spec/prefill、每variant固定3次重置输入；先state-only排除前一output launch影响。保存每次全部state、mismatch位置和首个差异完整源输入，任何异常不覆盖。所有读取均低索引，不解引用溢出地址。
3. 只有证据支持时补固定scope的同cache新进程与独立cache编译对照、capture/至少2次replay，用来区分固有执行同步与随机编译缓存问题；执行前写明精确矩阵和预算，不无界改参数直到通过。

停止条件：GPU资源不独占、编译/设备异常、证据写失败即冻结停止；状态数值mismatch是预期定位信号，按既定有限矩阵收集，不自动部署修复或恢复模型。不能放宽state exact、只挑通过轮、把barrier有效单独当根因闭环。若未隔离到机制则suspected；旧60K/提前EOS、原GPQA完整根因仍未证明。最终记录首次差异原件/编译命中/依赖图、所有失败与对照；无性能结论、无新formal gate，旧PAUSED监控不启动。

CPU离线命令：CASE/commands/accdiag050-offline.py SHA84176e2483981d22a7318ebbf42d7cf10035cfd8dfeb096482481acb79d8bb7d；在当前模型容器`CUDA_VISIBLE_DEVICES=空/PYTHONPATH=空/OMP_NUM_THREADS=1`执行`python3 CASE/commands/accdiag050-offline.py`，只核049的22份已存原件、写新D报告及首次差异完整PT，不初始化GPU。

离线audit SHA3ddbaada5150569fab84928d390bbf49066811aad123982d9a3179dad1ce3f10、首差完整PT SHA08de34d6bbc2d721caf9634f4c3ec63a021c1346918707b82785e1e6d8cc2bdc。Decode所有原始/候选错误仅s=1/3/5/7，单片常128元素，吻合当前threadsPerWarp=[16,2]/warpsPerCTA=[1,4]的warp边界；尚非机制确认。

GPU有限矩阵控制器CASE/commands/accdiag050-matrix.py SHAe67af1c84cd60ad1fdcf1906613ef4525226b40caec812f27a741f718d6bc0ed，执行`python3 CASE/commands/accdiag050-matrix.py --mode host`。Host先核8010无listener/PPU8独占空闲/镜像挂载，容器独立cache、物理8、超时600秒；3mode×(i64-pre/barrier/separate-snapshot/one-warp/i64-return)×3repeat=45次state-only，每次全量原始state和bad坐标，首新差异立即排他保存完整输入/旧状态/实际/CPU参考，编译IR/二进制分别按variant归档。仅诊断私有生成源码，不改049或原安装、不改PR，不启动服务或模型请求。

首矩阵已完成45次。Decode原i64 pre=[0,1152,2047]、return=[2430,1919,2045]；spec pre=[383,767,766]、return=[0,638,1277]；prefill pre=[0,128,0]、return=[0,0,0]。barrier/snapshot/one-warp在全部3mode各3重复均0差异。report SHAe96ed11395b847573d75130c2ec0a61710d95c9dc7da8aa0e56d1676413d00bd；首新差异为Decode/i64_pre/repeat1/1152元素/max4.84375，完整PT SHAb1ef95b766fdca42c686ac248a4e55e5afe0e75170a92ce7543b777e5b84002b，旧原件未覆写。barrier版TTGIR布局仍[8,1]/[16,2]/[1,4]，LLVM实际产生cta.sync；所以不是仅更换tile或修改数学使差异消失。

第二阶段预冻结：同一源码、同一原049输入，只测i64无同步与barrier，各decode/spec/prefill先5次reset-eager，再capture+3次device indices置换replay；两个独立GPU进程，进程一复用050 matrix-cache、进程二使用新cache。每进程48次数值检查+6次capture调用，合计96次检查、12capture，不增加矩阵。保存全部state/编译IR和binary SHA，比较相同缓存与新编译是否改变机制。CPU离线枚举4warp的24种读完后写入顺序，尝试逐128channel CTA重建首差；枚举不匹配则如实保留，不能靠猜测归因。仍不恢复8010、不改现有候选/PR/其他服务。

第二阶段控制器CASE/commands/accdiag050-confirm.py SHAb3bd48ea161f1aefd7eef7c7db67ab749b8bfef5e5d548a417801d22180ef568，执行`python3 CASE/commands/accdiag050-confirm.py --mode host`，每进程前核PPU8无进程/8010无listener，最多600秒。不同索引置换参考由独立CPU状态更新公式重新计算，并先验证原索引与049已存参考全等；全部结果保留，不据结果删轮。说明：warp实际执行可在load/store之间交错，单纯24个整warp原子顺序不足；CPU证伪模型将枚举8个load/store事件且各warp load先于store的2520种合法交错，不等同真实硬件逐周期trace。

两个独立进程已完成96项检查/12capture/36实际replay。barrier全部48项检查为0差异（其中18次graph replay）；无同步版Decode两进程的5eager+3graph均复现，spec多数复现，prefill仅warm-cache的第三次graph出现256差异。warm report SHA28e9f6a513d2e9e1f26f5f6d5b49f339a5e31f23431d4bc287764b8551072f88，fresh SHA52428720b0f7cceeefba4d6c5b8274bb29e9aab13a46e9575e13c7b165ace526。无新增模型请求/重启/8035访问。

CPU因果核验CASE/commands/accdiag050-causal-audit.py SHA387a5a5f7fc7ccd6ae0eb66181873643773066bcff5e018708954356136635e6，在容器CUDA_VISIBLE_DEVICES空/PYTHONPATH空/OMP1执行。只分析首新差异1152元素的2520种warp事件交错、同cache/新cache实际binary SHA及barrier LLVM load→sync→store顺序，写D/causal-audit-001；无GPU/推理。

因果audit已完成：首差9个128channel CTA的全部1152错误元素均有合法warp交错的精确输入来源与整CTA重建，非仅最大误差相近。首元素row2/channel256/s7：应读old-history8=0.09130859375（warp3），却得到当前x=-0.36328125，因为warp0已把该x写入history8。四warp同时先读完再写可避免此跨warp依赖。source只有`tl.load`→elementwise→`tl.store`，没有CTA同步，注释“每CTA先读完”并非全warp执行保证。该CPU2520枚举是已存值的可行调度证据，不冒充逐周期硬件trace。

矩阵pre/return的binary一致；两个独立进程同cache/新cache编译的3mode×2variant全部hgbin SHA逐字一致。barrier保持相同blocked layout，LLVM每mode全部global load都在实际cta.sync之前、所有store在其后（Decode loads至77行/barrier94/stores100与105）。因此当前证据支持**源码缺少跨warp原地WAR同步，编译选择的history跨warp布局暴露该缺陷**，不支持随机cache损坏或编译器算术误算；不承诺排除所有backend问题。具体CPU因果summary SHA246ef46b7abd689f07ad6d19dd959562c22c3b5d408f0eadf69a0c3f20ab4fe5、完整逐元素witness SHA94938eb618bc9adeef19c6f862df7e730b0d8d99ae3e8adb49f8f5c1abb40b48、compiler-provenance SHA878163bcf5a037e85c7d0ca90a73163db777a9c086e48f1ec8f85048632ecd1d。

终态CPU/Host冻结CASE/commands/accdiag050-freeze.py SHA1dc5268fdca03685b317edae0e93c6dd54fa7aa5c6f314e885409cc57fbde026；执行`python3 CASE/commands/accdiag050-freeze.py`只复制050私有源码及matrix/fresh编译cache、核所有原始state/输入/差异/日志和命令SHA、回读原安装及049目标源码未变、核8010仍无listener/PPU8空闲，不查询8035/0–7、不发GPU或模型请求。产物D/terminal-evidence-001，旧现场不覆盖。暂不修正式源码/PR，不恢复服务。

冻结resource检查未通过：源码/cache已复制、原安装与049源码SHA已核不变，但PPU8出现新的VLLM::Worker_TP0/约81GiB占用，故原freeze在“必须空闲”的断言停止、尚未写终态summary/manifest。8010仍无listener；此前两个有限GPU进程均已自然退出，未发任何服务启动命令。不追查8035/其他端点、不停止新占用、不发更多GPU；这不是本轮算子故障。保留第一次冻结失败状态，采用CPU-only续归档CASE/commands/accdiag050-complete-freeze.py SHAbb9e00aebb665be455e9d8f370142fa9961c2e9bd3970fc57b9b2988c5970518，执行`python3 CASE/commands/accdiag050-complete-freeze.py`仅核已有文件/完成新summary与manifest，记录PPU8占用变化，不重跑任何算子。

## 终态结果与结论边界

| 同一保存输入、BF16/channels10240、三mode | 状态检查数 | 非零差异检查 | 结论 |
|---|---:|---:|---|
| i64无CTA同步，含A/B/A、新进程与graph | 66 | 41 | 相同binary也出现非确定状态错误，最多3199元素 |
| 仅加入CTA同步 | 57 | 0 | scoped exact通过，其中18次changed-index graph replay |
| 分离只读snapshot与写地址 | 9 | 0 | 去除原地依赖后正常，诊断参考非生产方案 |
| 仅num_warps=1 | 9 | 0 | 同history不再跨warp时正常，布局哨兵非生产方案 |

合计141项state exact检查、12次capture/36实际graph replay；全部轮次保留。首次差异的完整输入/旧state/实际state/CPU参考/所有坐标、actual indices与kwargs、variant源码、IR/LLVM/binary/命中hash和完整可读日志均已冻结。499份文件独立SHA与大小核验；terminal summary SHAddc147b8a09405ae0866e7c094f8bbeba708144ec8da50e04210cc972098c782，manifest SHAa062219b190a8b14ff383e5af9742508710b90b9612ec2dadd03a37b9f803395，D/terminal-evidence-001。此处没有模型HTTP、logits或token，不能虚称保存了本轮模型回复。

**算子机制结论：跨warp的原地global状态WAR竞争已在限域内复现，高置信度；不是由i64 cast单独引入，也没有随机缓存污染/编译器算术误算证据。** 编译器确实把history维分给多个warp，源码没有同步来保障完整旧值读取；输出kernel与state kernel的前后launch顺序不能解决state kernel内部的竞争。首差1152元素/9CTA全部由输入值和合法交错精确解释。

这是operator-only定位，不是正式模型精度问题已解决：未证明此前60K/reasoning-only由这条竞争造成，未恢复8010、未发任何模型请求、未改原安装/049候选或现有PR959，未访问8035/物理0–7。旧acc016故障污染incomplete和acc015有效164/198 failed/no gate不变，监控仍PAUSED；不恢复性能优化、不签formal gate。GPU新占用出现后只CPU归档，没有继续使用卡8或干预新worker。

## 复盘与下一步（review-ple-048-050-20261020）

按inference-optimization-planning归纳048→049→050：先隔离地址宽度缺陷，再发现独立状态一致性失败，本轮用三种对照和同binary回切把范围缩至CTA内WAR。三轮均无同配置端到端性能测量，累计speedup=null；Prefill/Decode仅有算子正确性，Mixed服务及正式分数待后续，不以操作数通过替代服务验证。

下一候选优先级：①最窄的旧state load后、store前无条件CTA同步，保留早i64和原数学；首证伪是原生产shape和大地址边界/三dtype/history/spec/empty/graph完整算子矩阵，任何state差异停止。②history不跨warp的显式layout，因改变occupancy/兼容面更大而暂缓。③snapshot/out-of-place因额外带宽和graph生命周期成本，仅作reference。barrier也有未测性能代价，不能预告加速。当前用户只授权定位，不将实验barrier正式安装或更新PR；等待修复方向，且资源空闲、服务恢复均须遵守新指令。下一次源修复回归有结果或出现平台/layout反例时复盘。
