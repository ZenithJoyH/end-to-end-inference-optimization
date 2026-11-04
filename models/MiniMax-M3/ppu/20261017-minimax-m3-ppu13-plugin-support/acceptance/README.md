# 验收边界

当前fw-020已默认关闭Plugin FP32 router替代，保留原GateLinear和显式OOT白名单可选接入。最终629项CPU/static/mock通过，只改custom_ops.py；8011同一API实例health200。PPU/graph/模型仍未验证，以下历史600项或旧精度结果不构成当前组合通过。

最新env-004已将fw017/018/019合并候选及FGV统一安装至`/workspace/vllm-plugin-FL`、`/workspace/FlagGems-vllm`，各只保留一份源码和安装记录。最终路径600项CPU/static/mock重跑通过，旧副本完整归档可恢复；源码语义未改，不是新设备或模型验证。

PPU数值、graph和模型推理仍未测。8011在本次整理前后同一API实例且health200，未争抢设备或启动MiniMax。因此不能签发新组合精度gate或称为推理验收通过；整体acceptance仍incomplete。旧dated回退路径改由[env-004](../optimize/env-004-single-final-checkout.md)的归档恢复入口替代。以下为历史阶段记录，不是当前服务状态。

2026-10-18当前状态：[env-003](../optimize/env-003-flaggems-vllm-update.md)已将FlagGems-vllm更新至官方main46387d7/0.3.0.dev1并保留原packed SwiGLU，安装/导入检查通过，未改Plugin或执行硬件计算。原8024服务在更新前已停止，本轮未启动。依赖已变化，下面90.40%及gate仅为旧组合历史证据，不用于新组合验收；当前完整精度、推理及性能仍未测，acceptance为incomplete。

当前文本正式精度通过：[accformal-006](../optimize/accformal-006-ppu13-gpqa-c64-60k.md)于2026-10-17 19:27完成（198/C64/60K/阈值88%），strict-match 179/198=90.40%，198唯一题目和双filter证据通过，gate签发及check通过。耗时90分14秒，服务/源码未漂移。API日志中14条达到60K，空输出/超时0；样本摘要的截断0仅反映顶层标记检测，不代表无截断。heartbeat已暂停，服务保留。四场景性能验收未运行，因此整体acceptance仍incomplete；不继承旧容器gate。

最新fw-016已对fw-015清理后的无黑名单版本按原参数重启，独立通过C1/C8最终答案10/10、16rank双模式capture及FULL180次执行。当前实例 `fad201d7b6ec:8024:30544:494374945` health200，保留运行。启动约16分钟，已保存视觉Conv3d冷调优过程；期间未修复或回退。随后同一实例通过上述完整GPQA，性能未验收。

历史：[fw-014小范围收敛](../optimize/fw-014-minimax-adaptation-contract-refinement.md) 基于620892ab + 原有两项卷积黑名单，CPU72、真实PPU121及C1/C8已通过，原证据保留。当前及历史均未覆盖PIECEWISE请求replay、真实多模态正确性、其他硬件和100K边界。当前gate路径为`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support/accuracy/accformal-006-gpqa-c64-60k-threshold88/accuracy/accuracy-gate.json`，同目录`final-result.json`保存终态；完整身份、SHA及native结果/样本路径见实验记录。
