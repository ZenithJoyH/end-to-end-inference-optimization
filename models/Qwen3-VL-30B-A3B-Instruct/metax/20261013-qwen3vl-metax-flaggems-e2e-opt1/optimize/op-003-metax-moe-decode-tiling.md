# op-003-metax-moe-decode-tiling

状态：preparation；operator/improve；父目标 P1024/D1024/C64/N128；Decode，Mixed/Prefill 为守护。依赖已保留 op002 的 JSON 配置。

## 优化方向与瓶颈依据
上一轮真实 trace 的 Decode GEMM1 约186us，GEMM2 stage1约110us；低M、128 experts、top8存在按BM16填充的计算。测试减小BM是否降低完整调用成本，同时检查增加分块/weight重读的反效果。新增用户CSV全部轮次保留，SUMMARY仅作原始记录，不能追认稳态准入。

## 优化内容与适用边界
先从用户当前容器有效状态以不暂停服务的快照创建新私有容器，同挂载并逐仓库核验身份；GPU0/1，用户8000与GPU4/5不变。初轮仅benchmark进程内配置覆盖，不修改产品代码/JSON。固定六组配置：原BM16，BM8、BM32（两GEMM和alignment一致），GEMM1 BN32、BK64、BN128/stage1。保留其他tile、warp、数学和FlagGems选择。

## 正确性与路径命中
M64、两种子、均匀/集中路由，原JSON实现及CPU FP64 oracle；atol.002/rtol.02/NRMSE≤.015，两次变化输入graph replay。候选复核M8/16/32/48/64。正式模型精度按用户指令暂缓。

## 性能效果
not_run。graph预热200次，3块×200重放；完整MoE≥5%改善，验证shape退化≤3%，B/R drift≤5%，spread≤10%才进入同配置无profiler targeted Mixed。900秒搜索预算，编译/数值失败保留记录；不切换native。

## 决定、风险与回退
pending；仅新容器可改。旧JSON和用户改动保留，未通过候选不写回。当前正式P1K及四场景验收仍incomplete。

## 外部证据
远端案例 `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1`；命令 `commands/prepare_op003_container.py`，准备回执 `results/op003-container-preparation.json`。

首轮完整搜索35.83秒，原文件未变。BM8在TritonMETAXGPUPipelineMACA编译失败；最佳BK64最低完整调用加速1.02997×，未达到冻结5%门槛，未晋级。后续tiling02在相同seed/route/M/graph/oracle/门槛下，预先冻结BK64 stage1/2/3、BK32 stage2及warps2/8资源组合；独立新产物，预算900秒，不重写或替换首轮。

第二轮39.34秒，最佳BK64/stage3最低加速1.02907×，仍未达到5%。两轮均未修改产品source/JSON，op003决定not-retained；原op002配置保留。编译失败仅BM8；可运行候选的数值/两次变化输入graph检查通过。后续转向真实M8192 Prefill热点，不继续扩大Decode搜索。
