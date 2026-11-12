# randn 地址类型诊断地图

## 大N输出偏移先溢出后扩位

- 信号：startup/Inductor benchmark生成大合成随机张量，服务在设备同步或driver formatted-output处理处退出；先确认实际派发至哪个randn实现，不直接归因printf或模型Attention。
- 匹配键：当前证据为Gems f0c89b53基线/PPU/BF16连续N6400030720、BLOCK512/UNROLL4；请求P/D/M阶段未覆盖。不同revision、布局、dtype、平台须重核，不能迁移性能结论。
- 机制：`pid*BLOCK*UNROLL+lane`先算i32会在2^31元素处变负，即使N和最终指针GEP为i64，负值仍可能通过`off<N`。修复必须在乘法前扩位，四条输出store均检查。RNG counter数值域另算，禁止顺手改变随机算法/状态推进。
- 首个实验：离线核真实shape/grid/TTIR/LLVM；在用户许可与独占资源门禁内，用小scratch写出边界位模式与CPU比对，不启动原版巨大危险store。保留原IR，避免为复现破坏设备上下文。
- 通过证据：固定版小shape/seed-offset输出和RNG状态与安全原路径一致；原大shape NaN预填后全覆盖、canary、关键block独立参考、目标graph capture+2replay通过；生产编译IR证明乘法前i64。若优化对象是startup，还要单独验证原契约服务启动，算子结果不能替代模型精度与请求性能。
- 停止条件：仍有i32输出乘加、随机序列/状态改变、canary写坏/未覆盖、graph错误或新native异常，均停止晋级并保留首个证据；不自行重置设备/重启/全量GPQA。仅修复版startup通过也不能解除原正式精度阻塞。
- 证据等级：reproduced于上述固定版子集；旧地址算术为invariant；与driver SIGSEGV关系仍supported-not-perfect-causal-AB。
- 来源：[037→038证据卡](case-index.md)。无无profiler性能测量，不提供加速比。
