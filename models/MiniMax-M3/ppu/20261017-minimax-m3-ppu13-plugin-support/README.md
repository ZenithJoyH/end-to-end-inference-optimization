# MiniMax-M3 / PPU-13 指定 Plugin 分支验证

用户明确要求修改当前 `minimaxM3` 容器中的 Plugin，并验证推理。此任务不是性能实验，不新建优化容器，也不继承旧容器的 GPQA gate。

最新：[fw-020默认关闭router替代](optimize/fw-020-fp32-router-opt-in.md)已让默认模型继续使用原vLLM GateLinear类，只有显式OOT白名单选择gate_linear时才注册替代层。单文件默认策略及说明更新，629项CPU/static/mock通过；topk/OAI、FGV及其余源码不变，8011前后同一API实例health200。

[env-004版本收敛](optimize/env-004-single-final-checkout.md)保留的`/workspace/vllm-plugin-FL`与`/workspace/FlagGems-vllm`及editable安装不变，各一份。七份旧副本完整归档可恢复；本项另存单文件原件/完整delta，未新增源码副本或提交代码。

8011在整理前后保持同一API实例、health200，未运行PPU或模型验证；当前只完成源码整理和安装，不能据此宣称推理正常或加速。以下为早期阶段/组合的历史证据，不代表当前环境或有效gate。

2026-10-18：[env-003依赖更新](optimize/env-003-flaggems-vllm-update.md)已将FlagGems-vllm切至官方main46387d7/0.3.0.dev1，保留原packed SwiGLU及修正，确认topk_sigmoid导入和接口可用。Plugin未改，原目录可回退；原8024在更新前已不在运行，本轮不启动服务。新依赖组合未做模型/精度验证，下文90.40%只属于更新前历史组合。

正式精度：[accformal-006](optimize/accformal-006-ppu13-gpqa-c64-60k.md)已于2026-10-17 19:27完成，当前服务198题/C64/60K/阈值88%，strict-match 179/198=90.40%，gate签发及复验通过。无旧响应缓存命中，服务/源码未漂移；14条60K截断单独记录，空输出/超时0。heartbeat已暂停，服务保持运行。

最新交付：[fw-016](optimize/fw-016-unblacklisted-service-restart.md) 已按原参数重启并通过C1/C8 10/10及16rank graph回归；当前不含thead.yaml差异、无新增测试，仅保留3个源码文件修改。无黑名单冷启动约16分钟，视觉Conv3d autotune明显偏慢但最终自然完成，未修复或回退，完整现场已保留。

当前为620892ab的小范围收敛候选refine001：修正路由dtype/支持边界，将预处理patch移至worker加载阶段；后续按用户要求移出新增测试并撤销卷积黑名单。fw-014的CPU72/PPU121及服务回归作为历史证据保留，当前fw-016另有无黑名单新实例的10/10文本回归。PPU-13 `minimaxM3` 服务保留在127.0.0.1:8024；原健康checkout、快照和回退方式保留。当前组合正式GPQA通过，性能未测。

- [基线事实](baseline/README.md)
- [分支替换与推理验证](optimize/README.md)
- [验收边界](acceptance/README.md)
