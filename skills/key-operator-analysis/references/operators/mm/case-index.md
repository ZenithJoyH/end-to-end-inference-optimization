# MM 调参诊断证据卡

## GLM-5.3-Flash / PPU：新bucket触发请求内宽搜索

- case_id：20260911-glm53-flash-ppu-e2e / point51 / mm-cache-diagnosis-05。
- 完整事实：[点51记录](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-sparse-mla-small-head-dual-backend-51.md)，[案例摘要](../../../../../docs/cases/20260911-glm53-flash-ppu-e2e/README.md)。原始源码、CPU探针、DB副本和请求栈留模型记录所列远端目录。
- status：blocked；evidence_level：reproduced（原生请求RPC失败、真实事件、CPU原生key/prune与只读DB差分），不是修复通过或正式性能。
- 环境：PPU-13 / ZW810E / TP16 / BF16 / vLLM0.24.0；FlagGems `9c9bff3979a6f90ef0d0c78aa6a1da2262723f31`。Plugin PR454基线加公共路径/H4临时诊断补丁，具体内容SHA见点51；`FULL_DECODE_ONLY`捕获通过，Prefill不是整段FULL。
- operator_path：Mixed中Prefill投影；`aten.mm.out → FlagGems _thead/ops/mm.py → LibTuner → mm_kernel_ppu`，主路径M20481和8198、多组N/K、dense NT B、BF16；本卡不改变MM数学或cache key。
- change：framework诊断，只读CPU方法/元数据/缓存对照；FGV SQL修复为既有前置，未改MM策略或kernel。

### 证据摘要

1. P4096/D16 C1完成后，C8约300s RPC超时；16worker在多个采样点处于MM在线benchmark，至少995次/rank、约129s/rank已记录。事件触上限，不能称全部300s独占归因。
2. 原生key CPU对照：M20480→bucket20480、M20481→21504、M8198→9216。其余flags/N/K/4个BF16 dtype不变，11组相邻旧bucket命中、新bucket冷缺失。
3. 原生候选114，合法性裁剪后104，与实际前9组各104次一致。裁剪不是请求期搜索预算。
4. 同一命名空间ConfigCache299→318（+19、删除0），BenchmarkCache30631→32671（+2040、删除0）。19组各104条完成，另M8198/K1536/N4096只写64条、无winner；缓存正常持久化，并非反复失效。
5. ConfigCache的bucket key命中会跳过搜索；BenchmarkCache保留raw key并不意味着每个raw M变化都重调。
6. 额外独立风险：当前构造器生成的20/100与25/50 `do_bench`闭包都标记custom/-1/-1。CPU原构造器与实际DB tag支持该元数据碰撞，不是本次冷bucket缺失的直接原因；需独立修复验证。

### 知识差量与限制

- prior_belief：MM长停顿可能来自缓存失效、形状差异、宽搜索或设备异常。
- outcome：refined；当前直接机制是新Config bucket冷缺失触发宽搜索，已有结果正常写回；协议tag是另一个问题。
- future_first_check：重建实际bucket key与raw benchmark key，比较前后winner/候选行和namespace，再检查候选数及搜索预算；不要先清库、弱化key或盲加预热。
- 首个整模策略证伪已执行（MM06）：相同SQL起点和P4096/C8，baseline冷M12293为237.634s通过、candidate冷M28673为58.937s通过、revert冷M20481+8198为300.728s RPC失败。三角色16rank均有实际事件，候选176次policy调用将104合法候选限4；但冷shape交集为0，严格因果比较incomplete，不据这些冷耗时报稳态加速。
- 新差量`refined`：异步接纳改变冷M投影组数，进而改变请求内搜索预算，即使SQL初始字节与HTTP契约相同。未来首个实验改为固定shape序列和实际输入hash，再作策略A/B/R，后续才验证原C64和完整minimal。
- MM06候选未保留，断网后09:40只读完整审计SQL-only/OFF/DB不变；下一固定shape07仅准备中，不能填写通过。
- 数值、精度与验收：本轮无GPU/MM数值修复，无新GPQA或性能；SQL修复保留，临时H4回退、服务OFF。没有证明降低搜索空间后的精度/graph/端到端收益，不外推其他平台、shape或revision。
