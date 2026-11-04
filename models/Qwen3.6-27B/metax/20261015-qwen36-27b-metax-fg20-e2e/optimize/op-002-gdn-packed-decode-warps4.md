# op-002-gdn-packed-decode-warps4

状态：完成，真实ABI数值/graph通过；三阶段候选未达2%主门槛，已回退。分类 `operator/improve`，父目标 P1024/D1024/C64/N128。完整20项FlagGems、当前native attention、FP32 V-major状态、原atol0.002/rtol0.02保持不变。只修改独立优化容器私有 `/workspace/FlagGems-vllm`，原容器/共享源码/vLLM/权重不改。

依据当前三阶段基线和双rank trace，GDN packed在54个B64 decode graph replay中占约20.1%的kernel工作，实际原策略BV32/W1编译256regs、12spills。OP001的BV16/W1可消除spill且12case/96步/变化输入graph逐位相等，但B64完整调用只快11.14%，未达预冻结20%，拒绝安装；B8未改变的fallback也有约1.86%微测差异，不能把所有微测差值归因于代码。

本点从原BV32/W1重新开始，不叠加未保留的OP001。唯一变量是在BF16 packed/FP32 state/K=V128且B*HV>=768时将num_warps由1改4，BV策略保持原样。预期减少每线程状态和临时量、消除spill并提高可调度warp数；也可能增加K归约跨warp同步，故不能凭寄存器估算宣布收益。MetaX warp64，目标实际block应为256threads。MTP入口和其他dtype/shape保持原选择。改变线程分配可能改变FP32加法次序，必须报告原容差下全元素误差及与原版的逐位相等性，不能调整容差。

首个证伪沿用已CPU标量验证的reference、同12case/各8step/各两次变化输入graph、同种子和原容差。先数值/graph，再同输入B8/32/64完整wrapper CUDA graph B/C/R交错5组各30replay，保留全部组；B64耗时下降>=20%、B32不退化、B8回退退化<=5%、各shape原版回退漂移<=5%方可安装进入模型。否则拒绝安装，恢复原服务并保留证据。原GPU数值失败会停止叠加优化并进入精度诊断。

若微测通过，性能Skill模式targeted/diagnostic，冻结新的同配置baseline/candidate/revert：Prefill P1024/D1/C64/N128、Decode P1024/D512/C64/N64、Mixed P1024/D256/C64/N128；各6/6/8warm与3measured、固定末3throughputspread<=10%、600s/round/T0/ignoreEOS/seed42。不能复用初始env001结果作为事后绑定对照。所有测量轮/慢轮保留，全部比较指标spread<=10%，baseline/revert漂移<=1%；Decode与Mixed输出吞吐各至少+2%，跨阶段吞吐/延迟守护退化<=5%。Prefill为哨兵，只要求有效证据与守护，独立primary0%比较可如实failed，不把它改成passed；候选整体判断须单独说明该预冻结规则。

每个新模型角色要求两rank实际目标grid/block、graph至少两replay与fresh10doc/C8，目标分支需用足够batch命中，不能拿B1的graph证明大batch特化。数值/微测不是模型精度或端到端收益；当前20项新源码未运行正式198题，不签gate，不宣称四个正式场景完成。结束保持原源服务恢复，候选补丁供审查，不自动部署到用户启动脚本。

远端证据根：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e`。待执行命令、SHA、实际结果及保留/拒绝决定写回本文和state.yml。

终态：12case/96step与24组变化输入graph检查均通过原容差，FP32误差最大归一化容差比约0.02637；不是逐位一致。目标W4编译140regs/0spills，相比原W1的256regs/12spills降低。数值回执SHA `b6911a6492cf037d2e00bf5eaf337550e6dc638de304b52380823501f913c364`。

完整wrapper B32中位0.1104555→0.0946347ms（−14.3232%）；B64为0.1890304→0.1635840ms（−13.4615%）；B8未改动回退形状仍出现约1.8836%计时差，不计为代码收益。原版回退漂移分别0.2797%/0.00773%/0.07222%，5组30replay全部保留。微测回执SHA `c7d45ae6011d92f0fcdc2a885433886f1ff1e1246016da42ef3c933f39b2bb4d`。

决定：未达B64至少20%耗时下降的预冻结门槛，不安装到模型、不跑该候选E2E。控制器原源恢复ready、无恢复失败，终态SHA `10518b003aa7f3c1c52bb26c58de6281d5422b544a4182ba18f769d50928048e`；源码与全20项未变。两轮均不构成服务收益。复盘只保留一个组合候选BV16/W4，重新完整实测验证交互，不相加OP001/OP002的孤立数字；若仍未准入，停止这组tile/warp方向。

后续运行时校准发现：先前微测采用FP32 bias、int64索引、contiguous QKV/state；真实服务缓存IR是BF16 bias、int32索引、QKV行stride8192、FP32 state行stride401408（head16384），保留额外非SSM区域。a/b为contiguous HV24，QK归一化开启。证据 `results/runtime-packed-abi-001.json` SHA `b83e69b4368eb76a4add6b305c0c5518425c4582099251cde66d4842c80a6307`，绑定实际env001v5 runtime及两个已使用kernel IR的SHA。旧微测仍是其代理ABI的有效记录，不能将其spill数/收益直接归到真实模型；没有候选已安装或虚报E2E收益。

r2选择先复验代理场景中最好的同一W4候选（SHA37ac不变），不增加tile/warp候选、不降低20%门槛。按真实ABI重新建立baseline/candidate/revert微测；15个数值case包含原范围、legacy ABI、int64边界和gate阈值，另检查状态非SSM区域及QKV的Z/padding不被写入。每case8步和两组变化输入graph，原atol0.002/rtol0.02不变。CPU标量与真实布局构造预检已通过，回执SHA `be88f4093ca6a420cc9c8684cf691ba89ccdecdd5f87059e837c7dc51a41e6a6`，无CUDA使用。通过后才允许同一冻结三阶段契约进入模型；旧代理结果不混入新的比较。

目标库的AGENTS/workflow要求在生产源码修改前冻结三张表。此次尚未修改安装源；已有exports/注册继续使用，MetaX既有算子局部调度试验，非新Torch算子。该revision引用的optimization.md/deep_opt.md未在仓库找到，按本项目SOP/关键算子分析方法做真实ABI审计、限定候选和停止条件，不借缺失文档扩大搜索。workflow内conv1d任务模板与用户当前GDN请求无关，不套用。当前为实验补丁，非完整上游交付。

| 项目真相 | 本轮冻结内容 |
|---|---|
| op/可编辑 | 既有MetaX `gdn_packed_decode`；C私有 `_metax/ops/fused_recurrent.py` 一文件；base5d154，candidate37ac |
| 只读 | vLLM/Plugin/FlagGems、模型/tokenizer、源容器代码；已冻结reference/runner/plan/contract及旧产物不改 |
| build | 已有editable安装；Python源码原子切换后启动全新角色，无C++重建或依赖升级 |
| validation | CPU标量/布局预检；15case各8step、变化输入graph、padding保护；模型各角色双rank实际大batch/两replay与10docC8 |
| benchmark/聚合 | 真实ABI B8/32/64，5组30replay中位数；三阶段原生3measured中位数、全部轮保留 |
| gate/超时 | 微测B64耗时−20%门槛、B32不退化、B8/回退漂移5%；E2E原2%/5%/1%契约；probe900s/服务1800s/round600s |
| profiler | MetaX torch profiler及实际编译IR/资源；不用NVIDIA nsys/ncu命令，不以profiler时长作收益 |
| autotune | MetaX单个预注册固定调度试验，显式局部no-autotune豁免；原generic/NVIDIA配置均不改，非全硬件最优声明 |
| fallback | 原FlagGems Triton策略；无新增Torch compute/copy/cast fallback；Torch参考仅在case测试文件 |

| 数值/接口契约 | 范围 |
|---|---|
| API/参考 | vLLM专用packed GDN，无同名Torch API；现安装原函数与独立FP64递推参考，不伪造Torch conv1d契约 |
| 输入 | B×5120 BF16 QKV、BF16 a/b与bias、FP32 A_log/SSM state、int32索引；H8/HV24/KV128；真实leading strides如上 |
| 输出/alias | BF16 out `[B,1,24,128]`，FP32 V-major state原位更新；未选中state、0/负索引、相邻conv/Z区域不可覆盖 |
| 精度 | FP32状态/计算，QK norm eps1e-6，原beta量化；原atol0.002/rtol0.02，不改gold/正式80%阈值 |
| 边界 | 非对齐、strided、dtype与旧ABI回退；NaN/Inf/训练不作新语义承诺，保留既有行为；仅inference forward |
| 未覆盖 | 其他设备/模型及未列dtype组合性能未知；非通用算子完成或PR-ready声明 |

| 路径 | 实现/验证 |
|---|---|
| fast | BF16 packed/FP32 state/KV128/B*HV>=768，原BV策略、num_warps4；原容差+真实ABI微测与模型graph |
| small/general | 原num_warps1及BV heuristic，仍是FlagGems kernel；B1/8/16/31等与dtype/layout边界验证 |
| invalid/unsupported | 原索引<=0零输出且不改state；原rank/device/shape错误检查保留，不用Torch补洞 |
| MTP/external | MTP旧fwd入口不改；不切vendor/native以关闭目标FG路径，无新增external-library path |

新增生产hunk静态审计：只有Tensor.dtype/shape数值与dtype常量读取、num_warps选择，无Torch计算/拷贝/转换。完整模型正式198题尚未运行，不签发或复用旧精度gate。


真实ABI第一次GPU测量前的方法修订V2：V1命令仅保存、未启动，保留为superseded-before-execution。旧代理ABI的20%准入失败结论不变。本次将20%微测目标单独报告，数值15case/8step、两组变化输入graph及相邻区域保护仍按原容差通过；B8/32/64完整调用无超过5%退化且B/R微漂移<=5%后，允许一次独立三阶段B/C/R模型研究。最终是否有用仍由原生E2E的Decode/Mixed各+2%、跨阶段延迟/吞吐守护5%、测量spread10%、B/R漂移1%判断，原门槛不改。不将微测准入或临时安装等同候选保留，不自动部署源服务；旧对照不补绑。此前表格的20%安装门禁被本段V2明确替代，旧结果原样保留。

V2命令在执行前保存：
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/op002r2-probe-controller-v2.py` SHA `c4bb308d32d3714ebe1d0d39bbad06d4842b12d9a5f10d1ac602f61b3b861d3f`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/op002r2-model-service-v2.py` SHA `f879a7a5dd55c6aee46ac688a350be93b0ae933b76aeb6b8c5f965447054a1ea`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/op002r2-launch-probe-control-v2.py` SHA `f4fb98cb5c31793a1042f701b902c5f5f5842ad55e6ae9adc8bd57a8069e2374`
- `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/commands/op002r2-e2e-research-contract.json` SHA `fc86edc95d71332f34dc5d00624117a8c0ff35f390e5806bbbb7e4ed48646f6a`

V2唯一控制器已启动：host PID1546577/create1792084405.51/startticks502396451，进程回执SHA `f38af515fe149bcdf9bdb2f928fa7f162267cf6ca9071154a2ced85807fd6d48`，inputshas-v2 SHA `afc8b39149e7d6fc076dc929b32d897501f25f413cdb85cd1a1df36fbcc08218`。沿用用户授权30分钟纯只读监控，控制器承担既定动作；无新数值/微测/端到端结果前不声明收益。空间实查public-flash约24TiB、C私有盘约28TiB可用。

真实ABI数值已完成15case/120step/30组变化输入graph，全部通过原.002/.02，padding/QKVZ保护通过；最大归一化容差比0.0453742196，不是逐位相等。数值SHA `3d6d62757a6e1cbb185e2cc0613d7664133a454278445b40453051c1988f8166`。真实ABI目标原W1仍256regs/12spills，W4为140regs/0spills。

真实ABI完整调用5组交错中位：B8 0.0433749→0.0439552ms（慢1.3378%，代码未改动fallback）；B32 0.1036715→0.0954795ms（快7.9019%）；B64 0.1799680→0.1650432ms（快8.2930%）。B/R微漂移分别0.39346%/0.16462%/0.00473%，全部组保留。微测SHA `3d2009c6b8e77b50121e48b28db9955b4dd72ed72ab845f2c1d79d1d7c656193`。20%目标未达，原生probe标记incomplete/operator-admission-not-met保留；按测前V2独立研究契约，gross5%守护通过后正在启动全新baseline模型，尚无端到端收益或正式精度结论。


三阶段与回退最终结果（targeted/diagnostic，非四场景formal）：每角色Prefill6warm+3measured、Decode6warm+3、Mixed8warm+3，原生9份runrecord均complete，全部87轮/27测量轮保留，9408请求0失败。三角色双rank实际大batchgraph验证与fresh10docC8/20filter行通过；candidate W4实际block256，原版/回退64，保持当前20项FG且FG FA未命中。每角色缓存单独准备、无profiler计时；runner/plan/contract/client/SHA原生验证，变化仅FG-vLLM整体源码SHA。数值候选不逐位相同，但原容差全通过。

| 阶段与主指标 | baseline | candidate | revert | 候选变化 | 延迟变化 | B/R所有指标最大漂移 |
|---|---:|---:|---:|---:|---|---:|
| Prefill total tok/s | 5637.1361 | 5674.3920 | 5662.9698 | +0.6609% | meanTTFT 9086.16→9020.61ms（−0.7215%） | 0.5136% |
| Decode output tok/s | 937.5674 | 950.6012 | 938.6878 | +1.3902% | meanTPOT54.620→53.740ms（−1.6118%）；P99ITL48.165→47.075ms | 0.5570% |
| Mixed output tok/s | 696.3424 | 705.6152 | 698.1784 | +1.3316% | meanTPOT68.941→68.017ms（−1.3394%）；P99ITL1497.782→1481.699ms | 0.8287% |

原生Prefill比较passed；Decode/Mixed比较failed，唯一issue均为primary improvement below threshold（各低于2%）。延迟/吞吐守护5%、各指标spread10%、B/R漂移1%均通过。Prefill并非目标decode特化的直接收益，不能将+0.66%归为GDN prefill优化。全部指标最大测量spread：PF0.1197%、D1.9717%、M9.2236%（回退P99TPOT）；Mixed回退吞吐三轮698.1784/659.4583/698.8344全部保留，中间慢轮不删除。回退漂移在本次门槛内，不代表长期稳定或数值归因。

决定：本轮候选拒绝保留，独立容器一文件恢复原5d154/整体cb45；用户原服务qwen36-addgdn/18002已按原参数与原20项恢复ready，精确实例qwen36-addgdn:908003:1792090540.07。四repo源码在源/独立容器重新只读哈希均与baseline相等；源8002/其他GPU/shared/vLLM/权重未操作。未改用户启动脚本，不新发gate，不追加GPQA或性能。候选patch保留供审查，pr_readiness experimental，未提交/推送。30分钟监控终态后已暂停。

关键证据：
- prefill: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/op002r2-prefill-comparison-result.json` SHA `e85dbc1a90a9c08dac022468bc83465473ca44cb8951c545e1347e91c18e7206`
- decode: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/op002r2-decode-comparison-result.json` SHA `ab64011344680a15b2928af8c72ae692124c394d3439f65c4411402a980e0749`
- mixed: `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/op002r2-mixed-comparison-result.json` SHA `a69dbaad7bb3c866c245d03984d864bf8ae643a367cb2b0597bbdf34c17154fe`
- 原始九份记录：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/op002r2-E2E/op002r2-{baseline,candidate,revert}-{prefill,decode,mixed}/run-record.json`；各SHA与全部中位/原轮数组见state.yml。
- 控制终态SHA `dd80282a345805e185142317a74ee46f477e8f7a92da635126c2491424d42b31`；恢复manifest SHA `d29b32d5f567b71d0555c241f4b287d3d10eeb9de3ee8b6dfe4ba2eb5973a2d8`。
- 独立终态验真：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e/results/op002r2-existing-final-validation.json` SHA `02106fd22fc8387bb9f691b0820f6a5048e10623569d065ebc673183d9d4e34a`，命令只核验已存产物/当前身份，无新模型生成或测量。

复盘rev-014：真实ABI的完整调用8.29%仅转为约1.3%模型吞吐，原proxy13.46%不能替代。停止tile/warp组合搜索，不相加孤立加速；下一优先完整Mixed两cohort时间线与CPU/device重叠，按吞吐优先证据重新选框架或融合点。不能根据64迭代窗口或1.49s P99ITL就直接指认batch调度根因，也不能把已开启async调度作为新优化。当前20项无正式198 gate，四正式场景仍未验收。
