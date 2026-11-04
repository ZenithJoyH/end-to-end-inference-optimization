# accdiag-030：TP归约顺序、shape、目标行偏移

用户2026-10-19授权基于保存8rank输入区分BF16舍入和实现错误；保留i64/QSA M16，不访问8035、不全量GPQA，重启8010或加埋点前必须另告用户。先做CPU-only离线定位，无服务/源码/采样变更、无新增模型请求和GPU操作。方法inference-accuracy-diagnosis+key-operator-analysis；029正式前局部证据完整但原acc015164/198 failed-score/no gate仍阻止性能叠加。

029输入和输出固定：CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018；S=CASE/diagnostics/accdiag-029-tp-hc-boundary-20261018/runtime-001。029CPU report SHA c904d2e4544fa003ceaad87a4c75f451739750df169db2c78a4ae4e92f3ce968已重新核验。新root=CASE/diagnostics/accdiag-030-tp-reduction-order-shape-offset-20261019/cpu-001，旧PT/manifest/marker不可改。

已有完整目标矩阵778×2560与808×2560，各8rank C1和Mixed本地输入精确相同；postTP先不同。descriptor核验实际总shape分别778/808与785/815行、stride[2560,1]、BF16、storage_offset0，目标由row0移至row7，即17920元素/35840字节。不是非连续stride或实际storage_offset7；目标切片与整体allocation地址分别记录。指针改变不是错误证明。仅目标行被保存，Mixed另7peer的本地分支数据未全留存，独立重建整批时不能伪称原完整输入。

CPU首个证伪实验预冻结：对所有目标元素计算16种环形串行顺序（8起点×正反方向，每次加法BF16舍入）、16种环形balanced-tree、FP32累加最后BF16、FP64求和最后BF16。顺序不按结果挑选，保留所有候选匹配率；对C1和Mixed输出计算逐元素candidate bitmask、未匹配坐标、块/行共同可行顺序及标准7次加法gamma误差界。CPU-only shape/offset padding对照仅检验正确算术不应混行，不能冒充GPU对shape的因果验证。若已有输出可被固定BF16归约顺序精确解释，收窄嫌疑；若无匹配仍不能排除未覆盖顺序，不能立即认定实现错误。

CPU阶段单线程/CUDA不可见，不导入模型，不访问8010/8035或运行torch.distributed，新增产物排他保存。需要GPU重放以独立改变shape/offset时先核当前任务卡8–15资源与8010空闲，不触碰0–7/8035；显存不足或需服务重启/新埋点时停并先告用户，不自动释放服务。当前尚未执行GPU方案，CPU结果后再确定最小必要范围，不以新模型请求替代算子复现。

执行前冻结：CASE/commands/accdiag030-cpu-order.py SHA56d94d56a8cc6501ef1ff0d20bf0e6d75a6a5f2e8e362b917c51f287eef8726a，本地编译通过，32family定义及全元素bitmask/误差界/CPU shape-padding负对照写入RUN_STARTED。Host排他上传核SHA后，仅一次`docker exec -e CUDA_VISIBLE_DEVICES= -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 qwen38-eval-ppu07-acc015-c64-20261018 python3 CASE/commands/accdiag030-cpu-order.py`；CPU-only1200秒预算，已有root/失败不覆盖或自动重试。不改旧029的任何证据、模型/服务或采样，目标矩阵和误差mask均保留新目录。

CPU001一次执行3.23s终态，report d623a0e17438024377d0d477b8f86029420f4abfa35c6965276b69a20a5201b2、manifest f50b84b3e010a3d56ef14379e1fa49d5ec7e083cfeda351a5bea47b71525959a。4份输出全部元素在gamma7*sumabs界内，人工rank顺序族约94.6%元素可解释、仍有107019–111986未匹配，所有256元素块均无共同顺序；不能拿这组未覆盖的顺序族认定实现错误。CPU pad/offset负对照仅算术通过，不是设备因果证明。

029固定服务日志实际NCCL环为[0,1,2,6,5,4,7,3]及反向、[0,2,3,1,5,7,6,4]及反向，24通道，并非按rank编号单调。新CPU002对这些4环的8起点共32真实顺序逐元素复核；脚本CASE/commands/accdiag030-cpu-real-rings.py SHAd830a00ba8fecfa36792d89eb306c9ec547c0d7980a884d2a078b0a932adc667，原CPU001不改。一次同CPU容器/空CUDA执行，root cpu-002-real-rings，记录topology日志SHA与全部候选匹配率。该环配置不是每次kernel归约顺序的直接命中证明。

当前只读8010仍2727961/start504948954/argv5744d999，idle、counter9356/3523未变；没有读取8035。仅对物理8–15执行ppu-smi -q -d MEMORY -i各卡，free分别20184/20164MiB，可考虑不改服务的独立算子重放；尚未执行GPU，必须另冻结案例矩阵/进程/显存上限和原服务空闲守护，不扩大为模型请求/全量GPQA。

CPU002终态：report00cdffd1b167e4728ef8d11127de17ca7f9e6f0ad041610253d0baa207713fa0、manifestb778af46ea2a3ffbaf08048d72ba501507c1c4d7fb14c1dc16cd1496529935d3。4份输出**100%元素**都被实际环旋转的BF16串行舍入解释，所有7780/8080个256元素块各有共同可行顺序，仍不是一个全局固定顺序（仅761/778与790/808行有共同顺序）。这支持分块归约次序随位置改变，但原模型同时改变shape/offset，尚需因果拆分，不以per-element候选拟合当kernel命中。

## 独立设备算子重放契约（执行前冻结）

用户明确要求受控定位shape/offset，不需要重启8010或新埋点。仅在现8010空闲且counter9356/3523、精确API2727961/start504948954/argv5744d999不变、卡8–15各free>=8GiB时，启动一个**独立8rank PyNccl communicator**，不进模型、不修改模型或通信配置/来源、不访问8035；卡0–7不可见。相同安装PyNccl直接out-of-place ncclAllReduce，记录实际类源码SHA/native版本/新通信环日志；它是独立comm而非已加载模型comm，不能假称原服务实际内部算法已命中。PyNccl构造器1次标量zero warmup已明确计数。

固定2个保存前缀×BF16/FP32×6个case×3次重复=每rank72次payload collective，另构造1次标量；0模型请求，无额外微测/自动重试。6case分别：(N,target0,base0)、(N+7,target0,base0)仅shape、(N+7,target7,base0)仅target offset、(N+15,target7,base0)再次shape、(N+7,target7,base1row)allocation偏移、同shape/target且非目标7行由0改rank相关固定值的peer污染对照。原7peer分支未保存，此处零/固定填充值为明确合成背景，不冒充原完整Mixed输入。

每rankCUDA_VISIBLE_DEVICES明确8–15对应local0–7；CPU单线程，torch allocator上限总显存2%，PyNccl本身workspace另记录/保留至少8GiB准入余量。每case前CPU Gloo广播rank0对8010 idle/counter的只读门禁；运行计数/出现新负载则停止本测试、不操作服务。重复不等、跨rank不等、nonfinite、input被outofplace改写、输出guard损坏为真实异常，首marker排他保留当前完整input/output/descriptor及所有已保存结果，不自动重试；BF16不同case数值差异是预期观察，不提前当故障。只销毁本测试自己的communicator/进程，不发服务信号。

原始输出每case首次各rank保存完整target、rank0额外保存整个测试output、重复1/2完整SHA并精确比首轮；异常额外保存当前完整output。保存输入PT来源SHA、实际shape/stride/storage_offset、指针、目标行、canary、各rank输出SHA、已完成collective数；与CPU参考/原模型输出比较由后续CPU审计完成。eager算子路径仅解释原graphNONE首Prefill阶段，不做性能结论，不替代长Decode/C64/正式GPQA。

脚本：CASE/commands/accdiag030-gpu-replay.py SHAf032a10253f1603df1afe7c8bd9156cdf090ddb74563f63ce7fac2fe45f873a7；唯一launch脚本accdiag030-gpu-launch.py SHAb511a746cb36a233e86fa0e46356b17b007acbf75c87da0cbd97a8f21462033c，本地编译通过。排他上传核SHA后Host一次`python3 CASE/commands/accdiag030-gpu-launch.py`；根gpu-001须不存在、实际PID/精确argv写LAUNCH/PID，之后只监控原进程，不重复启动。环境仅测试进程使用loopback/IPv4、IB禁用，不改变原服务bond/IPv6；这是新comm差异需保留。私有017 index/index_put、QSA M16和029probe SHA启动前均核，不改源。若需要改服务、释放显存或加埋点，停并先告用户。

## 独立测试bootstrap控制面修正（0GPU/0模型请求）

09:40:59唯一docker exec PID3630612/start508988637已启动，但`torch.distributed.run --standalone`自动公布hostname在容器内不可解析，TCPStore循环gai -2；原生test launcher精确Host PID3630633，**尚无任何rank目录/worker或GPU payload、无FIRST_ANOMALY**。这不是模型/通信算子错误，旧gpu-001的driver/LAUNCH/PID原件保留。无需改模型服务或容器网络配置。

仅保存控制面修正：CASE/commands/accdiag030-abort-bootstrap.py SHAbd3c39a9e8e184972c50a939ce6879cae175c2c248491e492a9023cdc2981226，严格匹配3630633完整argv/当前start、无rank目录后仅该零worker等待launcher一次SIGTERM，自然退出，0服务信号/无其他kill。确认BOOTSTRAP_ABORTED后，新独立root gpu-002，replay-v2 SHA949fb97ce716fa5469bf19a25e0fe455893f05a1a6bad9adcbcf61fb248c5717仅产物root变化、同72payload/6case/2dtype/2point/3repeat。launch-v2 SHA972eec3fe32e1ff0803f4de039e8e95703b6290a7670403f27482c2e2b942cb2仅改static rendezvous显式127.0.0.1+新空闲临时端口、重核8010/counter/free/SHA。脚本均本地编译通过，排他上传核SHA后依次各一次Host执行abort-bootstrap和gpu-launch-v2。不是重跑已经执行的GPU/模型请求（此前全部0）；不删除旧记录，不改服务/probe/采样/全局DNS，不访问8035。

gpu001零worker等待launcher已单SIGTERM自然退出，0服务信号；gpu002实际Host dockerCLI3680331，8个worker已创建Gloo/CUDA context，但在首次归约前import失败：VLLM_PLUGINS空使平台误选默认CUDA，缺`vllm._C_stable_libtorch`。8rank ERROR ops_completed均0、无RUN_STARTED/comm构造zero/payload，FIRST_ANOMALY原始09:43:37.892193/rank0及完整driver日志保留。Torchrun自行终止其余测试workers、服务0信号，旧dockerCLI退出；这不是模型非法访存或数值事故，不改原marker。

CPU不可见CUDA导入预检：VLLM_PLUGINS=fl、PYTHONPATH指向已部署029私有Plugin后PyNccl导入成功，实际platform=vllm_fl.platform、CUDA未初始化。缺vendor计算扩展bundle的fallback告警仍保存，不涉及本测试native NCCL调用，不虚称这些计算扩展已可用。只对新独立测试进程启用原有PPU平台，不改运行中的服务或新增模型埋点。

v3固定算术矩阵仍完整未执行72payload：新root gpu-003，replay-v3 SHAa9674d1d01789ab785d6dfd938d5c51d30789457a33ac542485b41ff71538be1，仅root变化；launch-v3 SHAf63461d1ef0718741a1fb3f2d77b8e94bd54e47247f670968abcd8f49eed5191，仅指定既有PPU插件/private029与private017导入、新增CPU_IMPORT_PREFLIGHT排他证据并拒绝未通过导入。两个旧尝试未执行任何归约，环境修正不掩盖模型/算子失败，不自动重试实际failed collective。排他上传/核SHA后Host仅一次执行launch-v3，所有idle/资源/i64/M16/probe保护重核；用户未授权服务重载，始终0服务重启/新埋点/模型请求/8035访问。

09:47:05唯一gpu003 dockerCLI3752624/start509025210，CPU_IMPORT_PREFLIGHT通过；all8rank固定24case各3次payload已全部完成、72payload+1构造zero/rank、ERROR/首故障marker无。NCCL destroy/Abort结束时有socket/proxy warning，原始driver.log完整保留，不能删告警或冒称全日志无警告；告警发生于FINISHED之后、不掩盖某条失败归约（所有重复/canary/input未改写/跨rankSHA检查已通过）。该独立communicator销毁不是模型服务重启。

只读CPU快速结果：单改总shape不变，单改target offset0→7在BF16下分别607805/633283元素不同、max0.0078125，与原029计数/幅度相同；进一步shape、allocation起点1row、合成peer内容均不变。FP32 offset对照仅30/33元素不同、max1.4901161193847656e-8，转回BF16完全相同。完整张量逐位绑定原模型输出及CPU参考仍待独立终态审计，不提前声称修复原模型精度。

执行前保存终态脚本：CASE/commands/accdiag030-host-final.py SHAb2ab6baab5cd32f977b36b8c3d0e83b34b4cae5207a8fdd78d2617cbb28ce0a0，Host一次核原8010身份/idle/counter和4个i64/M16/probe SHA、测试CLI退出后排他写HOST_FINAL；不访问8035。CASE/commands/accdiag030-offline-final.py SHAb5bb32265c13cc554fc9ed073fe1b7a4e0e27aec61266847633be6c710cc94eb，仅CPU容器一次核400rank文件、72重复计数与输出SHA、shape/offset/precision和原模型逐位对照、真实环256块可行分段，排他写audit-001/report/manifest。两个脚本本地编译通过，上传核SHA后依次各一次执行，无GPU/推理/服务改动；如审计失败不修改原始证据。

## 终态：数值机制已受控复现，未改模型

独立重放all8rank均完成24case×3=72payload collective，另各1次构造标量zero；每case三重复精确、跨rank精确，input未被out-of-place调用改写、输出canary未损坏、无nonfinite/非法访问/真实归约故障。实际PyNccl类源码SHA28596817ee9fb842026624a8a6c32b0637630b6b908ddb2a79ecccbeac531e35，native version raw22703；独立进程中的实际调用路径已证明，不等同在原服务内部新增了分支追踪。原029的4份完整模型目标输出与本次独立BF16输出**全部逐位相同**：seq4/6匹配native-target、seq17/18匹配offset-only，而非只看首坐标/max误差相同。

### 单变量结果

| 对照（同8份目标数据） | BF16结果 | FP32结果 |
|---|---|---|
| 总shape N→N+7、目标仍row0 | 逐位相同 | 逐位相同 |
| 总shape固定N+7，目标row0→row7 | 778点607805/1991680、808点633283/2068480元素不同，max0.0078125 | 仅30/33元素不同、max1.4901161193847656e-8，转BF16全部相同 |
| 总shape N+7→N+15、目标仍row7 | 逐位相同 | 逐位相同 |
| allocation基址增加1row、同逻辑shape/target | 逐位相同 | 逐位相同 |
| 非目标7row从0改rank相关固定值 | 目标逐位相同 | 目标逐位相同 |

这些shape/offset结论只覆盖当前778/808、hidden2560和该native路径，不说所有shape永远不影响算法。对12个FP32测点（两输入×6case），与FP64精确求和参考最大差仅1.49e-8，**转BF16均逐元素等于FP64求和最后一次BF16舍入的参考**；FP32本身仍有30/33个位置相关末位差，不能宣传FP32全位不变。FP32归约仅在独立测试执行，8010仍原BF16路径，未热切换/改源码。

### 首坐标与归约块的解释

保存真实环顺序的CPU串行BF16参考覆盖4份输出100%元素；逐256元素块均有共同可行顺序。对这些mask求可行常序分段，前两全局区间为[0,38400)、[38400,76800)，分别使用环顺序候选id1/id9。C1目标从全局0开始，而Mixed目标从7×2560=17920开始，因此第一个边界对齐至目标flat **38400−17920=20480**，就是原029首次差异的目标row8/feature0。后续[76800,96000)等分段亦按同样全局坐标对齐。

坐标约定：本记录中的row8是从0计数的目标行索引8，即第9个token行；flat20480/hidden2560=8，避免把索引与自然语言序号混淆。

这是逐块可行算术顺序的重建，不是kernel运行时指令trace；但结合独立GPU单变量row-offset精确复现原4输出、三次重复和FP32消融，已经把原029首个TP差异收敛为**目标位置改变分块归约的有效累加顺序→BF16每步舍入不同**。在本验证矩阵中，没有支持越界、stride/target错行、peer污染、输入写坏或非法实现结果的证据。它符合低精度非结合性，不以“与FP64不同”或“有60万个元素不同”直接定NCCL错误；也不全面排除当前未覆盖的其他kernel/shape/原模型长Decode问题。

### 证据与运行边界

- `audit-001/report.json` SHA **486c9ccf5842b3b4a9dd4a1d6e527ad239b95b624356574c51ed2a8de9ba9d3d**，manifest **c1b6fc1273c4cbb97a3f4c824ab6d68a7498d38fe692d94e97d1574a82953c61**。独立CPU核验400份rank文件（192份完整目标输出PT、全部case/repeat/身份/计数），包括各首次输出/源目标/真实shape、stride、storage offset、指针和背景构造；无覆盖旧文件。
- `HOST_FINAL.json` SHAb1105afaa20108327eadfee4825fd5b94db28cb920210a3ff7e475036fe24ea7；原8010仍2727961/start504948954/argv5744d999，idle、prompt9356/generation3523未变，0新模型请求/重启/模型埋点，未访问8035。017 index/index_put、M16 QSA、029probe四文件前后SHA完全一致；不是重扫整棵所有仓库后声称全部代码未漂移。
- CPU001/002及audit三个manifest共8/9/1文件独立再次核验，gpu001/002/003完整driver log SHA与Host原件再次吻合。两个0归约环境失败/完整trace和首marker保留，v3销毁后的socket/proxy告警保留；不将它们混为数值事故，也不隐瞒日志。
- 测试进程均退出，PyTorch allocator峰值各rank23.984375MiB；这是allocator值，不包括NCCL native workspace/driver内存、不虚报总峰值。仅卡8–15可见，资源门禁前有约20GiB余量；无8010或其他服务停止/重载，只有gpu001精确零worker测试启动器被单SIGTERM。

## 决定与下一步

本轮诊断完成，**首个TP数值差异机制在该保存输入/shape矩阵上reproduced、因果变量已区分**；原GPQA低分/60K不收敛的模型级根因仍not-isolated。没有把独立FP32算子参考当成模型修复，没有签发gate，原acc015164/198 failed-score与性能阻塞保持。

候选修复方向为TP先转FP32归约、再转回原dtype，或在后端实现FP32累加的BF16归约；要进入8010模型链路验证，需要先说明范围/额外通信与转型代价、请求预算及必要重载，取得用户下一步方向。当前不改源码、不新增埋点/重启/模型请求或正式GPQA，不自动评测性能。下一轮首先检查同前缀logits/prob能否消除漂移，再验证原长Decode/C64，最后才按原正式契约复测；不可保证只修归约就达标。

知识差量refined：029怀疑shape/offset/实现错误，030通过真实环算术和独立GPU固定矩阵拆出row-offset而非这几个总shape/基址/peer值，且FP32消融消除转BF16后的分歧。下一次应先固定数据并拆分逻辑row-offset与tensor storage-offset、再核累加精度，不先改HC/QSA或把浮点误差当索引错。
