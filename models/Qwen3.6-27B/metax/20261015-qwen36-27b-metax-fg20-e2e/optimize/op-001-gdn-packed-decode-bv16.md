# op-001-gdn-packed-decode-bv16

状态：准备首个可证伪实验，尚未修改或安装候选。分类 `operator/improve`，父目标 P1024/D1024/C64/N128；当前 milestone 为 Prefill P1024/D1/C64/N128、Decode P1024/D512/C64/N64、Mixed P1024/D256/C64/N128。只在独立容器 `qwen36-27b-fg20-e2e-20261015` 修改实际 editable `/workspace/FlagGems-vllm`，源容器与原启动脚本不改。

当前 trace 将 Prefill 与 Decode 分开看：Prefill 中矩阵乘约49%、通信约17%，GDN FP32 H约6.0–6.3%、WY约5.48%、O约4.06%，均为可能重叠的设备活动时长和，不是端到端占比。Decode窗口包含初始Prefill；通过 `mcGraphLaunch` correlation 与 packed grid `[4,1536,1]`，两rank各分离54次B64 graph replay，每次48个GDN packed kernel，无GDN prefill kernel。该子集 packed kernel工作占比20.099%/20.079%，实际256regs/thread、block64、shared256B、BV32/K128/V128/H8/HV24。FP32 V-major state每次读写约201326592B，按约166us名义带宽约1.21TB/s；不能仅据寄存器高推定spill或必有收益。

假设：在当前BF16 packed输入、FP32 V-major state、K=V128且 `B*HV>=768` 路径，将V方向tile32缩为16，增加独立program数、减少每个program存活状态及寄存器压力。当前HV24对应B32起命中，B1/8/16/31及其他dtype/shape保留原策略；该条件按真实状态工作量设定，不按模型或机器身份选择。K方向归约宽度、FP32状态/累积、门控与beta量化、QK归一化、无效state索引规则及MTP旧入口均不改。

按精度Skill `minimal-regression`：固定量化后输入，独立FP32/FP64递推参考及原实现双重比较，原 `atol=0.002, rtol=0.02` 不变；覆盖B1/8/16/31/32/64、正/0/负索引、非零非对称state、非对齐/其他dtype回退、stride、QK归一化开关、多步状态累积和两次变化输入graph。失败停止候选晋级并做精度定位，不调容差。保持完整20项FlagGems注册、无blacklist、attention flag1、当前native attention路径；不通过关闭算子获取收益。

首个性能证伪：数值及graph通过后，空闲本案例GPU执行相同输入的完整wrapper B/C/R交错微基准，各shape5组、每组30次graph replay，保留全部组和精确compiled资源（能取到时含spill）。B64完整调用耗时降低至少20%，B32无退化，B8回退形状退化不超过5%，各shape baseline/revert微测漂移不超过5%，才安装唯一私有文件进入模型。微测计时覆盖wrapper产生的全部设备工作，排除模型graph执行同样不包含的Python校验开销；不是端到端收益。未通过则保留失败与原代码，恢复用户原服务，不自动运行完整模型候选。

冻结数值矩阵12case：B1/8/16/31/32/64，B64 padding与strided输入/索引，B32不做QK归一化，B64 FP32与B32 FP16回退，B32 H4/HV8/K96/V80非对齐回退，B128 H4/HV8/KV128命中。每case检查8步递推和2次变化输入的baseline/candidate graph replay；无归一化的QKV随机幅度0.03，其余0.3，均非零随机FP32初始state。测试原件SHA `5d15461a87db9b61adf6bbf52b576b9941fda9ed1e653ec98826926f0470a253`，候选SHA `e785e55bc9312eda4c42e99dec94c60ca03bd372e73e87d9aa36d29772ed9f31`，patch SHA `a8e4862fcccbb299f2021320b4ee72280c1ce0edd168d00a5cc50acd3859d2dd`。首轮只从case补丁目录加载两个独立模块，不修改安装源；唯一probe控制器负责精确暂停/恢复当前用户服务，探针结束仍保持安装源原样。

进入模型前另冻结新的B/C/R三阶段比较契约；不将已完成的初始基线事后绑定为因果对照。全部角色同配置、各自graph至少两次replay与fresh10doc/C8，所有测量轮保留，核对稳态、延迟守护与回退漂移。当前没有新正式198题gate，不宣称四场景正式验收完成。候选实际源码、最终比较阈值、命令SHA、结果、保留/回退决定在执行前后补充同一文档。

证据根：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261015-qwen36-27b-metax-fg20-e2e`。初始trace分别位于 `profiles/env001v5-{prefill,decode,mixed}` 的原生diagnostic回执；最终CPU分析将保存 `results/env001-v5-existing-analysis.json`。最终Mixed trace及原服务恢复核验仍待完成，此时无候选代码写入。

初始基线/采集终态已完成并恢复原服务，terminal SHA `7b562f450849c00371447ac4d27c8cd535de8d708342331b6a09ab03467d2a93`；三阶段全量CPU证据分析SHA `bb7ab1bdb6c2526d7cb0f90b546406340b6bf9af5b7ad4ae7231c88f61d93671`。Mixed同样分离54次B64graph，packed占20.083%/20.078% kernel工作；64iteration窗口不覆盖晚期第二波Prefill插入，Mixed P99 ITL根因仍未证明。

首轮r1在独立参考公式的beta广播上失败：`[B,HV,V] * [B,HV]`缺少末维扩展，发生于第一次oracle计算、目标kernel尚未执行，0个数值case完成、0微测、候选未安装。归类measurement-invalid，不能据此判定算子错误。原失败worker terminal SHA `2d59b4de48b1bfc8ae4f21eb815cd2c55f7b39f23eb28b88afa4cdb36201efcb`，控制器终态SHA `f9f707d6cd4fd693e96080d35ffd3b8a200bb8aea109809e4d4909c9a447e7ac`，原源服务已恢复ready。

修正参考为beta末维广播，输出分配跟随输入设备，候选代码/数值容差/输入种子不变。CPU预检用独立Python标量递推，4个小矩阵各8步，覆盖归一化开关与0/负索引；原公式可稳定复现错误，修正版最大输出差2.78e-17、最大state差8.33e-17。CPU回执 `results/op001-oracle-cpu-validation.json` SHA `b3779b7827ee99f81cc6d224f80e6c82c2e7686d0fd4bead9d4b5343de59b528`；GPU被显式设为不可见，0模型请求/0候选kernel调用。第一次CPU预检因原参考硬编码CUDA输出设备而被阻止，脚本保留，未使用GPU。r2重新执行原12case/8step/变化输入graph范围；这些是校验代码修正，不是修改算子使测试通过，也未放宽门槛。

r2终态：12case/96步及24组变化输入graph检查（每组原版/候选各一次replay）完整通过，所有输出/state与原版逐位相等。数值回执SHA `56c56a519ecefa4540fabe12d5565e81249102039701e4742b99fb22fcceba1e`。原BV32/W1编译256regs/12spills，BV16/W1为186regs/0spills。完整wrapper微测B32中位0.1105152→0.0994219ms（−10.0378%），B64为0.1888256→0.1677909ms（−11.1397%）；B8回退代码未变但计时差+1.8650%，不得计为算子收益。原版回退漂移B8/B32/B64分别0.5595%/0.2780%/0.1130%，全部5组30replays均保留。微测回执SHA `ff851ee4f440f872127293ee435db7b3d32796b589c677c4b2a0d5f530ecc720`。

决定：B64未达到预冻结20%耗时下降门槛，拒绝安装，不做该候选模型E2E。原源码与20项配置不变，原源服务已恢复ready；控制终态SHA `8a07526b2d6da6d7306fbcdfbebc8aa8fa356939dac4dd46ceb01380971d7122`。原始结果、微测和patch保留。该点只证明register/spill压力可减少，未证明服务收益。下一独立点OP002从原BV32/W1出发试W4，不叠加此BV16候选。
