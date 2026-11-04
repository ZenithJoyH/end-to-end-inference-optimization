# combo-001-gdn-packed-bv16-warps4

状态：准备。分类operator/improve组合验证，基于原始BV32/W1 baseline，唯一组合候选为相同BF16/FP32state/KV128/B*HV>=768边界的BV16/W4。OP001的BV16/W1与OP002的BV32/W4均未保留，二者微测分别约11.14%与13.46%耗时下降，不能相加。本点重新完整比较组合与原版，实际收益未知。

根据当前双rank B64 graph中20.1% GDN packed kernel工作、编译器实测spill，以及两轮资源/完整调用结果，验证减少V tile后能否让4warp配置进一步降低每CTA寄存器消耗并改善调度。没有降低FP32精度或改变数学定义，线程分配可能影响浮点归约顺序，保持原atol0.002/rtol0.02，保留真实全元素误差，不要求虚假的逐位相等。原完整20项FlagGems、native attention路径及其他启动参数均保持原样。

数值/graph/微测沿用已CPU标量证明的reference、原12case各8step、两次变化输入的原版/候选graph、同输入seed、B8/32/64的5组30replay B/C/R。只有B64完整调用耗时下降>=20%、B32不退化、B8回退退化<=5%、各shape回退漂移<=5%才进入模型。原始输入/gold/容差均不变；失败保留原服务/原代码，不继续这组tile/warp搜索。

若通过，执行事先保存的同配置三角色/三阶段对照。Prefill P1024/D1/C64/N128为哨兵、Decode P1024/D512/C64/N64和Mixed P1024/D256/C64/N128各要求输出吞吐至少+2%；每阶段吞吐/延迟守护退化<=5%，测量spread<=10%，原版baseline/revert漂移<=1%。6/6/8warm+3measured、固定末3准入<=10%、600s/round、T0/ignoreEOS/seed42不变。所有测量轮保留。Prefill独立primary0%结果如实报告，不将该哨兵数值轻微退化改成passed；有效性、漂移与冻结guard仍须通过。

每个角色新graph实例，两rank目标实际grid/block、至少两次replay及fresh10docC8先通过再测量。候选必须看到大工作量grid NV8/block256，原版NV4/block64；不能以B1证明特化命中。只在独立容器私有editable源码切换一个文件，并保存原件/候选/SHA；不改vLLM、Plugin、通用FlagGems、权重/tokenizer或用户启动脚本。结束恢复原代码并恢复用户原服务。若micro不通过，不安装或跑模型候选。

父目标P1024/D1024/C64/N128，其余正式P4K/P16K/P32K尚未测量。本点为diagnostic/targeted，不是正式四场景验收；当前20项新源码没有198题正式gate，不复用历史全21项166/198。收益如有，仅属于实测milestone，后续formal前须新正式精度。


终态：原12case/96step/24变化输入graph通过原.002/.02，candidate编译112regs/0spills，但完整调用B32反而慢3.49%、B64慢8.9296%（0.1890219→0.2059008ms）。组合未达20%门槛，未安装或执行模型E2E；原服务已恢复ready。数值SHA `b42999284be6d7885e75bfc96a9445f8fa3078520efd5f49b186618f58d5b877`，微测SHA `81dd10888ead4f96b044e3d2f460a11ef9e121515dc6143e6bb97bca9e298bb0`，控制终态SHA `70f0e812c496719b55697c78736062b97a46e4c117b3683a3a2c65bf856ec3a0`。所有原组/失败与候选补丁保留，状态rejected。

后续运行IR校准表明本次微测biasFP32/indexI64/contiguous QKV和state与模型BF16bias/I32index/QKVstride8192/state401408有差异，故以上只能作为proxy-ABI组合反例；不能把组合退化推为真实模型退化。停止新增tile/warp组合搜索。OP002同一W4候选另以真实ABI重验，独立记录和新对照，不改写本次旧失败。寄存器/spill改善不是性能保证，孤立加速不可相加。
