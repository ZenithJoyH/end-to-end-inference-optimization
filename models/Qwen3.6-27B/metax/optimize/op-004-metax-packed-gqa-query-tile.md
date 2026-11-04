# OP004：Packed GQA查询tile

当前先刷新热点，分类operator/improve，目标P1K。用户明确要求所有已开启FlagGems算子保持开启，选一个有端到端空间的FG算子优化，并验证三阶段/回退。本点只针对实际FG FlashAttention；GDN热点由原生packed核执行，不按名字误判成FG。

原OP001在Decode用GQA6 packed查询，M16对6有效行有padding；假设M8减少无效dot/accumulator/register压力。先检查编译器和硬件支持，splits16/N16/warp1不变。当前profile需重新验证双rank和三个阶段；旧FA活动占比约12%是活动和而非关键路径。

预冻结micro：B1/16/64×KV1K4K16K32K，BF16/D256/Q12KV2、物理页16/逻辑784、49物理页每逻辑组；完整publicAPI graph5组×40replay，baseline/targetM8/revert，CPUFP32 atol.002/rtol.02，graph两replay。只对B64,GQA6,physical16窄形状尝试，其他路径原样。晋级要求B64K1K延迟减少>=15%，其他B64长度退化<=5%，数值/fallback全通过。编译/队列/数值失败即保留证据并停止该候选，不修改运行源码。

当前使用现有独立优化容器/2、3卡18002、原8192/graph64/FG完整17项白名单、无blacklist、FGattention1。source8002/vLLM/共享源码/权重/tokenizer不改。离线micro需要精确停止本任务模型释放GPU队列，命令/SHA事前保存，完成后恢复原FG或合格候选；不是与模型并行探针。

micro通过后才实施私有guard、真实源码数值边界/fallback、双rankgraph/C8，再用完整指标声明的新契约比较Prefill/Decode/Mixed和回退。没有当前50000精度gate，正式四场景仍incomplete；本轮用户放行诊断优化，不能用micro宣称完成。命令/trace/源码patch/结果留在既定远端case，state.yml为索引。

新profile已完成：双rank各55graph launches，1Prefill/8Mixed/55Decode GPU范围；FA活动占Decode11.68%/11.86%、Prefill3.40%/3.49%、Mixed3.985%/4.000%。B64实际splitgrid16/64/2，merge384/2/1。实际路径与旧profile一致，捕获/分析SHA见state.yml，不能把活动占比当关键路径。开始隔离后的进程内M8可行性微测，源码尚未修改。

初次探针在0GPU/0编译/0矩阵时被pid_exists守护阻断：已退出212498仍为zombie。属于控制身份检查问题，未测试M8、无源码变化；失败结果SHA c29cbe55be14096795c252bd7159016cd424de3d64b7d282db01031038970211保留。恢复原实例231560/create1791941724.47后，仅修正检查允许精确旧进程已退出/zombie；新版仍检查当前正确模型PID出生和GPU隔离，不放宽算子/数值/性能契约。

终态：M8在首个B64/KV1K编译MACAMmaEncodingAttr shape_judge断言失败，0完整矩阵、无M8计时、未安装模型候选、未执行E2E。结果SHA537ef862c1fc4c989dbff592f444fa87d032128dc2629c9133b259d8e7845976；原FG/8192已恢复，op004-original-02 PID239394/create1791942156.85，graph/C8通过。候选rejected-compile/reverted；不修改编译器，不宣称性能收益。用户改选GDN升级与路由接入，其他FA方案暂缓。
