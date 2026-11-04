# perf-006 当前 opt2 P4 phase trace，原生 CLI 校正

承接perf005的采集前dryrun失败，旧记录全部保留。远端冻结工具C/vllm_profile.py build_common_args明确向native bench发送temperature0，而外层CLI没有--temperature参数。保持原工具，只删除外层多余参数；不改采样语义、场景、计时或参考。三场景完整dryrun与生成命令核验在服务transition之前完成，限定一次新控制流程，不盲重试。

沿用perf005阶段诊断契约：P4096/D2/C8/N16、P128/D256/C64/N64、P4096/D32/C64/N64，total runs2含warmup1、最后一轮profiler、seed42/temperature0/ignoreEOS，timeout600，record_shapes/stackfalse。Prefill/Decode/Mixed用实际attention路径/quantgrid/launch关联判断，全部8rank和frontend新trace必须核验。duration不冒充criticalpath或端到端收益。保持用户root、原11exports、source/TP8/7graph；临时profile-only restart后恢复无profiler并minimal105+2。

后续选择算子由当前trace证据决定，旧三负结果不丢弃。正式精度169/198仍为旧8025历史，下一保留候选需要当前身份full198>=81。原四场景正式验收尚未完成。

三场景nativecapture均exit0/complete，新trace共27份（每场景8rank+frontend），总压缩约421.7MiB；全rank/阶段/角色审核继续，尚不宣称热点定论。prefill分析全部8rank+front完整，PF包含无model graph的迭代；原source/root preserved，自动restore无profiler正在进行。native SHA见state，不以采集时间计算gain。

最终审核通过：27新trace，每场景8rank+frontend，阶段语义/graph关联通过。PF/Mixed包含attention Prefill与Decode混合，unknown2个marker保留，不按token拆总时间。MoE按每迭代114个kernel与同stream相邻成对grid G2/G1=8，全部rank未分类MoE0；G2寄存器240为Prefill主要线索，Decode fusedMoE为首位活动热点，duration非criticalpath。review e0f794...0a86，roles ad383e...a29d；恢复无profilerMF9d463...2223a及105+2 receipt183048...bb1e，root/source不变。plan034优先G2INT32单变量，次选G1真实partial-prefill M/config证明后有限K策略扩展。
