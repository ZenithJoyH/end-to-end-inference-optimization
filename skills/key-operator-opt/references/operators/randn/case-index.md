# randn / 大输出地址证据卡

## Qwen3.8-Flash-Next / PPU：startup benchmark输出地址i64

- case_id：20261015-qwen38-flash-next-ppu07-master / accdiag-037→038。
- case_link：[038事实主记录](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-038-randn-i64-fix.md)，含外部原始路径/脚本/IR/输出/退出和审计SHA；037原事故与工具干扰记录不覆盖。
- upstream：[Issue7269](https://github.com/flagos-ai/FlagGems/issues/7269) / [PR7270](https://github.com/flagos-ai/FlagGems/pull/7270)，commit56e1065c，公开代码字节等于038固定版；未合并/新pytest与非PPU CI待验，发布不新增硬件证据。
- status：kept，仅算子子集与startup；完整模型精度blocked/not_run。
- evidence_level：reproduced（固定版边界/数值/graph），旧地址缺陷另有静态不变量证明；原worker SIGSEGV因果不是完美A/B。
- environment：Qwen3.8-Flash-Next；PPU-07/96GiB PPU，startup TP8；engine revision见主记录绑定，卡中unknown；Plugin main a696859b+PR455 head3cb373b1+保留显式/MoE FP32补丁；Gems源export无.git，旧randn f0c89b53→新48d700e3；FGVLLM b4d3382/官方PPU QSA M16。mode=both（算子eager/graph），非目标硬件未验证。
- operator_path：stage=startup/compile benchmark，不是请求Prefill/Decode/Mixed。`torch._dynamo.testing.rand_strided→torch.randn→Gems randn→randn_kernel`；合成BF16 weight[40000192,160]，N6400030720/连续布局/BLOCK512/UNROLL4。normal_ blacklist不覆盖单独注册的randn。
- bottleneck_evidence：原服务启动失败，native formatted-output validate/flush→device sync只给同步上报位置；不是端到端性能热点或收益测量。保存的BF16/N64 IR先i32 pid*2048，后sext64，负offset仍小于N64。
- change：operator/improve（正确性），仅输出pid在乘法前转i64，lane/四条store继承i64；RNG counter/seed/offset推进、算法、dtype、grid与API不变。适用guard为实际地址表达式类型和长度，不按机器/模型名dispatch。
- results.operator：81安全小shape/3dtype/seed-offset与wrapper RNG状态逐位相同；18432安全scratch地址位模式与CPU一致；固定版原大N全覆盖、canary、9个逻辑block紧凑RNG reference、capture及2replay通过。原危险大N不运行。
- results.end_to_end：唯一8010 startup健康、all8worker存活、原生两类capture完成；未发HTTP推理、未做性能测量，模型replay未跑，历史164/198 failed/no gate不改。
- results.correctness：固定大N子集通过；3份服务randn IR（含BF16/N64）确认扩i64在乘法前。10649编译成员及原始日志/信号/source独立SHA核验。
- results.regressions：已测小shape/RNG状态无变化；float64/complex、其他平台、完整模型精度未测，不称全域无回归。
- knowledge_delta：refined。N或最终GEP为i64不保证乘加未溢出；基于真实UNROLL的store地址链才是首个检查。block1048576/lane0/store0的2^31元素offset旧版变成−2^31，BF16指向base之前4GiB；本例RNG i4最大1.6e9仍在i32内，不能把输出地址与RNG计数简单一起改。
- future_first_check：从真实合成输入而非用户prompt长度计算最坏pid/lane，再核TTIR/LLVM每级类型和mask。先安全地址探针；固定版再做完整覆盖/canary/参考与graph，避免旧巨大越界写伤设备。
- limits：原037有外部ptrace时序干扰；未知allocator/最终二进制sanitizer现场。修复后startup未再崩溃提高关联置信度，但没有旧危险大N→修复→旧危险大N设备因果闭环；不能解释历史所有GPQA错误/60K不收敛，不签正式gate/性能结论。pr_readiness=experimental。
