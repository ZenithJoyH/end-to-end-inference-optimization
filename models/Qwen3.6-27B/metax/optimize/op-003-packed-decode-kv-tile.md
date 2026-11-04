# OP003：Packed Decode 的 KV tile

状态：终态；N32负优化，W2单独未过晋级，未接入保留源码。OP002拆分数未晋级；本点保持自动16 splits，仅将KV tile N16改为N32，尝试减少循环/访存指令。M16、warps1、stages1、FP32累加/merge均不变。共享内存预计24KiB->40KiB，可能降低CTA驻留数，因此需要实测。

在优化服务暂时停止、GPU2独占状态执行完整publicAPI graph，CPU FP32独立oracle atol0.002/rtol0.02。B1含0/1/783/784/785页边界和1K/4K/16K；B16/B64含1K/4K/16K。baseline/tile32/revert交替顺序，各5组×40replay。实验仅在进程内扩展tile校验和plan，源码/模型/tokenizer不变。

预冻结晋级条件：B64/K1K完整调用延迟下降至少15%，B16/B64的4K/16K退化不超过5%，全部数值检查通过。通过后才准备窄支持条件补丁、graph/C8和同契约P1K三phase及Mixed回退比较。失败则恢复原OP001开启FG服务；不根据结果改门槛。正式50000精度失败/历史30000分数与gate不改；局部micro收益不是E2E完成。

外部脚本/results/logs以 `op003-tile-probe`命名，路径与SHA在state.yml。源8002及其他GPU任务不操作。

N32/w1首轮14矩阵×3variant=42项数值检查通过，maxabs0.000993；B64/K1K0.3083->0.9690ms，K4K0.9316->4.9934ms，K16K3.4187->21.1698ms，全部负优化。该结果拒绝并保留。当前编译shared=40960，原tile24KiB；尚未证实寄存器spill。

预记录一次资源组织消融：2×2配置N16/N32×warp1/2，另加原N16w1回退。分别固定tile比较warp、固定warp比较tile，拆分数仍16，禁止直接相加加速比。输出compiled n_regs/n_spills/shared。原晋级门槛与数值/边界/计时契约不变；所有配置失败即停止本轮离线调参并恢复OP001服务。该消融在结果前冻结。

消融终态14×5=70项数值检查通过。编译证据：N16/W1 256regs/13spills/shared24KiB；N32/W1 256/206/40KiB；N16/W2 244/0/24KiB；N32/W2 256/182/40KiB。证实tile32有严重spill；N16增加warp可以消除spill。N16/W2在B64 K1K/4K/16K完整调用下降约9.36%/9.76%/9.77%，仍低于原15%晋级，未接入源码。

两独立小收益不相加。最后以[组合对照](combo-001-fa-splits-warps.md)验证B64限定8splits+W2交互，其他batch原路径；加入32K守护。保持原门槛，不重标OP002/003通过。组合无达标配置即恢复原服务，停止本轮离线调参。

周期收尾：实际模型kernel页16、逻辑页784，原页784 micro仅为独立算子矩阵；[组合001](combo-001-fa-splits-warps.md)已按真实页16验证但Mixed未完成，精确回退OP001并完成三阶段对照。没有新增保留的E2E收益，正式50000精度仍失败。
