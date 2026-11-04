# perf-005 当前 opt2 P4K 全rank profiling

状态prepared，使用 inference-profiling capture→analyze。op005/006/007均无生产晋级；当前opt2已确认端到端观察收益，但局部试验不能继续解释净收益。将当前P4三个阶段以独立标记trace定位MoE G1/G2、activation/quant/sum、attention、通信及host间隙。mode与契约见state，Prefill4096/2/C8/N16、Decode128/256/C64/N64（与perf004的4096 prompt不同，只归因）、Mixed4096/32/C64/N64。各1warm+2run，只有最后run采集，temperature0/seed42/600s，trace预期8workers与frontend；record_shapes=true、stack=false控制产物体积。

仅在case脚本副本增加profiler-config，原root11env及用户port8035/nameopt2不改，源码/TP8/7+7graph不改；空闲检查后精确停止目标service关联进程并重启，源容器和无关服务保留。捕获前新105+2及graph2证明；采集后恢复无profiler并再次minimal。旧169/198原8025正式gate不能冒充当前8035绑定。trace原生产物、命令、SHA/rank覆盖保存在远端profiles/perf005-phase-profile-01，profile时长不计收益。

阶段用真实iteration/token/query和attention语义、kernelgrid、关联launch判断；无法关联graph节点的事件标unknown，不按token比例切总时长。热点duration可能重叠，不当criticalpath/devicebusy，通信负载不均与profiler扰动为竞争解释。仅在当前phase热点收敛后再选择bounded算子候选；停止条件为capture/parse/rank失败或外部请求干扰，保留证据，不自动重试。

失败：profile minimal105+2通过；capture dryrun不支持--temperature0（native旧C工具版本与本地README不同），没有发出采集请求/trace。已记录不完整，pipeline自动撤除profiler并恢复原配置。遗漏了变更前actualCLI核对，之后新增所有场景完整dryrun先于服务transition，不篡改旧runner或失败产物。
