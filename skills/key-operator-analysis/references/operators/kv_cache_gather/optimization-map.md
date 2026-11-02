# KV gather 排查地图

| 信号/匹配边界 | 机制和首个证伪实验 | 通过证据与停止条件 | 等级/来源 |
|---|---|---|---|
| 长输入才出现gather ATU/非法地址；FP8值+FP32 scale分页cache，外层页stride大 | 先反向追踪真实dispatch到函数；采集真实shape/stride、物理ID和cu。无访存算术探针比较int32/int64地址，再用同物理stride和高页ID做独立page reference | 位级值/scale一致、输出canary、graph replay；性能前删除CPU同步。元数据无效则先修上游映射，不mask错误。未捕获原故障ID不得伪造 | reproduced；[MetaX案例](case-index.md) |
| B31/B63首序列输出保留哨兵；upper_bound查找 | 对B+1项前缀测试首序列，和PyTorch按页oracle比较；核验迭代界限 | 正确复制且空padding不写；不能只看无崩溃 | reproduced；同上 |
| 内存错误消失但某轮吞吐/TPOT变慢 | 无profiler固定请求集/seed对照时间漂移；不能把成功预热或快轮替代慢测量。低开销证据不足再分阶段采trace | 保留所有已准入测量，按冻结spread判定；超阈值为incomplete，不能宣称稳态提升 | observation；同上 |
