# KPool / tail-cache graph 输入证据卡

## GLM-5.3-Flash / PPU：临时 tail slot mapping 与 FULL graph

- case_id：20261021-pr454-public-path-50 / diagnosis05。
- case_link：[事实主记录](../../../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-pr454-public-path-50.md)，原始命令、日志与SHA保留其远端根`diagnosis05/`；不复制完整样本或脚本到知识目录。
- status：not-proven（完整精度待测）；生命周期修复已在实际公共候选通过C8，必要主机SQL缓存修复后model08完整最小回归通过、当前安装保留待新gate。旧失败和回退保留，未宣称端到端性能完成。
- evidence_level：reproduced，输入指针生命周期机制、修复后真实动态子图和整模C8；原事故逐step输入仍未完整抓取。
- environment：PPU-13/ZW810E；模型TP16服务，独立GPU0诊断；vLLM0.24.0+empty；Plugin PR454 f769696+点50 v10候选；FGV main b4d3382+点50候选。所测KPool builder/kernel文件均未修改，SHA及完整身份见主记录。mode=graph，独立eager算子作控制，不启动eager服务。
- operator_path：Decode，公共`KpoolTailMetadataBuilder→compute_kpool_tail_slot_mapping→flaggems_vllm.ops.kpool.kpool_decode_update_and_maybe_write_cache_batched`；BF16 key/gate/tail、uint8 FP8 cache、int64 slots；B1/B8、next_n1、pool4、head128，tail stride=(4224,512,128,1)。
- bottleneck_evidence：原模型11/11档FULL捕获完成，必要C8回归设备报告`_kpool_decode_update_batched_kernel` invalid page；不是性能热点分析。Python index/同步栈可能是异步上报点。
- change：framework诊断与公共builder-owned固定容量slot buffer补丁。原槽位映射公式、数值kernel、positions=None原alias语义不变，无新平台分支；超容量/dtype/device变化明确拒绝，不悄悄换地址。先比同一合法槽位的新张量替换与capture原地址copy，再实施builder自身更新。
- results.operator：B1/B8各两次动态回放，新metadata地址未被graph消费，实际kernel写旧尾块；同址copy和同kernel eager新参数控制均精确匹配CPU tail-stash oracle，padding/sibling canary不变。
- results.address_lifetime：释放输入后第一笔分配复用同地址；graph仅复制槽位即读到受控覆盖值，可在CPU推导越界尾块。未把故意越界地址交给KPool执行，未产生设备非法访问。
- results.end_to_end：repair06/model06原FULL捕获11/11、C1/C8及P16383/P16384通过，P16385新RPC失败与原KPool故障分开。后续独立证明主机FlagGems调参缓存全表反射浪费并修复；无trace的model08实际公共路径通过C1/C8、三原16K/D8、11/11答案、FULL捕获/多token回放/16Worker无TileLang，final-audit-v5独立身份通过，原参数不变。新完整GPQA待测，无新性能结果；冷调参/缓存跨轮有变化，不以model08通过断言原RPC唯一根因已证实。
- results.correctness：428 CPU通过/4既有跳过；真实FGV B1/B8两个graph共享builder持有的同一base，8→1→8→1更换尾页、释放metadata/GC和padding7→8活动切换均精确匹配CPU stash oracle/canary，TileLang0。validation08新增空fixture构造错误与完整重测保留。局部修复通过不代表公共模型完整通过或正式gate。
- knowledge_delta：refined。单kernel支持graph和capture通过不能证明外部metadata适合FULL；必须同时证明对象存活和每step原地址刷新。仅keepalive仍可能使用旧slot mapping。
- future_first_check：确定metadata是在capture内还是外构造；检查返回张量是否新分配、谁持有、graph是否重跑Python，以及跨B1/B8/请求释放重用的地址和值更新。
- limits：未抓到原事故逐项slot dump，受控覆盖值不等于生产故障值；原机制探针metadata原语为Torch、算子为真实FGV，后续实际整模C8验证另列。P16385新RPC原因未定，单独MQA/TopK大shape通过不足以归因或排除真实Worker链路。公共PR默认eager attention边界未被本例否定；这是开放FULL后的兼容缺口，不外推所有平台或其他graph模式，不归因硬件/TileLang/FP8数学。
