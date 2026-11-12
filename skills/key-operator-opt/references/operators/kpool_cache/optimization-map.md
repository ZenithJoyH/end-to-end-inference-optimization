# KPool / tail-cache graph 安全排查图

这里只覆盖[该限域证据卡](case-index.md)的诊断机制，不提供性能最优配置。

| 项目 | 首个检查或证伪 |
| --- | --- |
| 信号 | FULL capture通过，回放/批次变化后尾页kernel invalid page或跨请求写错；同步上报位置不一定首错 |
| 匹配键 | Decode KPool、外部metadata生成物理tail slots、FULL固定指针、真实dtype/stride/页容量及候选revision |
| 机制 | capture外每步clone出的新槽位张量不刷新旧graph指针；释放后allocator复用可能把普通数据解释为物理页号 |
| 首查 | 谁持有捕获输入、每step是否原地址更新、padding/空行是否复位；不要只查最终指针是64位或tail kernel mask |
| 最小实验 | 先全部合法块，固定同一kernel，比新metadata替换与同址copy的两次动态回放；再释放输入，用只复制原始槽位的graph验证复用，CPU计算地址范围，不执行危险kernel |
| 必要控制 | 独立eager算子使用新映射、CPU stash oracle、尾页padding/sibling canary；B1/B8及多次归属更换，不能因C1通过就排除生命周期 |
| 修复边界 | 公共metadata builder拥有稳定容量buffer并原地更新；保留-1、空行和请求重用语义，容量变化不得悄悄换掉被已有graph捕获的地址，不按厂商/机器新建模型路径 |
| 晋级证据 | buffer地址/内容和边界矩阵、capture及两次动态回放，随后原FULL模型C1/C8/长边界回归；高风险缓存/graph变化还需新正式精度，局部通过不能签gate |
| 停止条件 | 不用非法页clamp到0、黑名单同步上报的index或降级graph掩盖；缺原逐step输入时区分机制复现与原事故完全确认。任何非预期设备错误、服务漂移均停止 |
| 等级/来源 | reproduced，仅PPU/上述候选和shape；builder修复通过动态子图、真实C8及后续完整最小模型回归，新正式精度待测、无性能数据；中途P16385 RPC与后续主机SQL缓存问题另列，不混称KPool故障或按排除一项就认唯一根因，原PR支持的eager边界不受此结论否定 |
