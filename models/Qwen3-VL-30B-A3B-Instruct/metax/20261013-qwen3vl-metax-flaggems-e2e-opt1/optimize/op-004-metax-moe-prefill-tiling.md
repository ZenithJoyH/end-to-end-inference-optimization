# op-004-metax-moe-prefill-tiling

状态preparation；operator/improve；当前父目标P1024/D1024/C64/N128；Prefill，守护Decode/Mixed。依赖op002 JSON，op003不进入组合。

## 优化方向与瓶颈依据
此前trace真实M8192 MoE G1约2.98ms/G2约1.41ms；资源guard使largeM快路径降低stage，pair gate/up因64KiB上限禁用。测试减少BM/BN/warp的寄存器压力与更好GROUP权重复用。最新manual长输入CSV趋势收益有限，仍不作为同配置精确因果。

## 优化内容与适用边界
同已验证新容器 qwen3vl-flaggems-op003-20261014，GPU0/1。初轮仅进程内配置覆盖，保留用户JSON/服务。M8192十组配置见state；两GEMM的BM与align一致，变更tile而不改数学/融合分支/算子选择。最佳候选先复核M4096/8192/16384，最终JSON拟只exactM8192，其余M原路径。

## 正确性与路径命中
M64原路径与CPUFP64oracle先确认；全M8192对原完整调用数值/graph、两次变化输入与路由replay，atol.002/rtol.02/NRMSE≤.015。精度评测仍按用户指令暂缓。

## 性能效果
not_run。每种子/路由前后baseline，200warmup/3块×50replay，1200秒有界搜索；全调用≥5%、B/R≤5%、spread≤10%、复核其他M退化≤3%才晋级。无profiler targeted必须以同配置Prefill/Decode/Mixed证明净收益，不能将micro提升当E2E。

## 决定、风险与回退
pending；任何最终JSON仅写新容器private仓库，原配置先归档。source用户8000/GPU4,5与qwen-vl不修改。正式四场景验收incomplete。

## 外部证据
远端案例 /public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1；后续op004-prefill01新命令/结果不覆盖op003证据。

完整十组搜索165.96秒，best group4最低speedup.982159×；未达到5%门槛，决定not-retained，源码与JSON未变。不将任何单路线改善冒充目标收益。复盘转向新确认的实际采样workload：userbench温度None继承模型.7，与此前own温度0不同。
