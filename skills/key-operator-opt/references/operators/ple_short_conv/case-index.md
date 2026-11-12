# PLE short-conv 状态地址证据卡

## Qwen3.8-Flash-Next / PPU：输出i64但state更新仍i32

- 来源：[accdiag048](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-048-ple-state-invalid-page.md)与[accdiag049](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-049-ple-i64-fix-validation.md)，2026-10-20；status=blocked，evidence_level=reproduced（仅地址算术/固定版大索引合成路径及低索引state不一致；原非法访问事故仍为离线匹配，不真实越界重演）。
- 环境：PPU-ZW810E/TP8、vLLM0.24.0、graph、FlagGems-vllm b4d3382bb04da4e0ab444849697865b4d5fcd86e；Plugin private树按正式SHA绑定，无.git，不按其目录推测版本。
- 实际路径：Plugin PLE decode直接调用`ple_short_conv_`→`_ple_conv_kernel`→`_ple_conv_state_kernel`；BF16、channels10240/history9，state stride=(204800,1,10240)，saved capacity66135/84094。QSA-only开关不代表这条基础PLE调用关闭。
- 事故：完整GPQA中PLE kernel驱动invalid page，随后watchdog/服务退出；38/198原生分数被159条连接失败污染、incomplete/no gate，无性能结果。
- 机制：输出kernel加载row后i64，state kernel遗漏cast。4份TTIR及LLVM保留`mul i32→sext→GEP`。3个驱动dump的PC0x1d8/函数长度/局部指令吻合Decode特化，寄存器反推唯一合法row11242，地址较正确位置提前8GiB。没有原完整设备indices/launch binary SHA，事故机制高置信度但未做原危险地址解引用。
- knowledge_delta=refined：通用index/index_put或相邻输出kernel已修复，不能覆盖独立state写回；边界按真实stride计算，本案10486而非generic102400的20972。小索引C1通过不能覆盖大池地址安全。
- 候选（私有测试、未加载模型）：仅`tl.load(indices+...).to(tl.int64)`位于乘ss0之前。PPU8 GPU有界地址probe确认原i32溢出、固定i64符合CPU；新增11项BF16/FP16/FP32×decode/prefill/spec与empty通过，27次changed-index graph replay/canary/history精确校验，21实际state TTIR为早扩位；channels129/stride204800，非完整生产通道覆盖。
- 正确性反例：combined29passed/2failed，原channels10240的Decode/spec状态exact失败；同输入低索引1/2/3独立CPU参考、原版与候选各3次均有state mismatch且数量变化。支持继承状态写回一致性问题，未确认同步或编译机制；不能将小通道边界通过泛化为完整正确。0模型请求、8010未恢复；[Issue958](https://github.com/flagos-ai/FlagGems-vllm/issues/958)/[草稿PR959](https://github.com/flagos-ai/FlagGems-vllm/pull/959)。
- knowledge_delta补充=refined：地址安全与原地state更新一致性是两个独立门禁。未来首查先做生产宽通道同输入baseline/候选状态字节与独立CPU oracle，保留重复不确定性；不要放宽state容差、只重试挑通过或以output通过掩盖state失败。
- 后续[accdiag050](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-050-ple-state-synchronization.md)将额外state问题缩到跨warp原地WAR：TTGIR [C,S] layout threadsPerWarp=[16,2]/warpsPerCTA=[1,4]，history分给不同warp；无同步66项41项差异，加CTA barrier57项（18graph replay）、snapshot9、单warp9均exact。同/新cache与独立进程hgbin逐字一致；首1152错误元素/9CTA可由2520种合法load/store交错精确重建。operator机制reproduced，高置信度；不是完整模型事故已resolved。
- knowledge_delta=refined：CTA独占一段channel并不意味着其中warp读完旧history才写回。源码的整tensor load→store不自动提供跨warp的global-memory WAR同步；先核编译layout与history依赖，在读取旧state后写回前显式CTA同步为优先候选；单warp和snapshot为独立诊断反例。输出kernel先完成也不能消除state kernel内部竞争。
- 后续[accdiag051](../../../../../models/Qwen3.8-Flash-Next/ppu/20261015-qwen38-flash-next-ppu07-master/optimize/accdiag-051-ple-cta-sync-regression.md)保留早i64，仅加store前无条件CTA barrier/纠正注释，私有正式候选211/211预冻结算子测试通过（原20+大地址11+全width/dilation/dtype/mode144+生产dtype/layout/index36），含192capture/570replay，原失败生产Decode/spec exact通过。183 state LLVM均含barrier，3980原件核SHA；未全局安装/模型加载或PR更新。
- knowledge_delta=confirmed（限该PPU算子矩阵）：同步修复不仅改变调度概率，在保留原tile/warp/数学的更广width1..8/dilation1/3/C1、33、129、10240/三dtype/两index dtype/布局/graph范围通过；地址安全与state WAR仍分别验。不能把通过扩大为所有shape/平台不再需要验证。
- 限制：无修复后模型回归/新精度gate/端到端性能，不外推此前reasoning-only/60K因果或其他平台。CPU交错重建不是硬件逐周期trace，大池取证只保存被寻址行/布局/canary而非完整storage。
