# MiniMax-M3 / PPU-13 指定 Plugin 分支验证

## 任务与边界

用户要求直接将新启动的 `minimaxM3` 容器 Plugin 换成 ZenithJoyH/vllm-plugin-FL/support-minimaxM3 并检查推理。该请求授权当前容器内安装切换；不是新一轮性能优化，不修改 vLLM、权重或共享源码，不复制旧 GPQA gate。

规则版本沿用当前仓库（版本号未单独冻结，policy_version/date 为 null）；acceptance_scope=diagnostic。目标 PPU-13 / 16×PPU-ZW810E / TP16 BF16。原 Plugin checkout 有本地改动，保留原路径；新 branch checkout 使用容器私有 `/workspace`，无需变更 /mnt、/data 挂载。

## 当前结论

最新[fw-020](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/fw-020-fp32-router-opt-in.md)已默认不注册GateLinearFL，保留原vLLM GateLinear；显式OOT白名单仍可选择新router。629项CPU/static/mock通过，单文件改动、安装路径/FGV/其他算子不变；8011同一API实例health200。无设备/模型验证或性能结论。

最新[env-004](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/env-004-single-final-checkout.md)已将下面候选统一安装为`/workspace/vllm-plugin-FL`与`/workspace/FlagGems-vllm`，各仅一份源码/安装记录，统一路径CPU600重跑通过。七份旧工作树已完整归档后移除；旧路径与rollback脚本不再直接有效，改用env-004恢复说明。整理未改变算子语义，8011前后同一API实例health200，未执行设备/模型验证。

以下为整理前候选形成过程及早期模型运行历史，不代表旧目录仍存在。

最新[fw-018](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/fw-018-fp32-router-gemm-dispatch.md)/[fw-019](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/fw-019-oai-experts-integration.md)在保留fw-017的独立候选上接入fp32_router_gemm和新版OAI experts：M>32保留原FP32 linear，不限制C64；alpha/beta/clamp照原参数透传，旧API/LoRA/quant等保持fallback。最终600项CPU/static/mock通过，候选`/workspace/vllm-plugin-FL.m3-router-oai-20261018`未安装；当前Plugin editable仍为refine001，原fw-017副本和两级回退保留。

用户要求不影响8011，复核原API/engine/16worker进程保留且health200；本轮无设备计算或GPU初始化，不做PPU/graph/模型验证、不宣称性能提升。未修改thead.yaml或新增Plugin test文件，未提交/推送。下列GPQA与模型服务状态均为历史组合，不代表本候选。

2026-10-18以[env-003](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/env-003-flaggems-vllm-update.md)为准：FlagGems-vllm已更新官方main46387d7/0.3.0.dev1并保留原packed SwiGLU，确认topk_sigmoid可导入；Plugin未变，未执行硬件计算。原8024服务在更新前已不在运行，本轮未启动。以下GPQA与服务运行状态均为此前历史证据，旧gate不能用于更新后的依赖组合。

正式GPQA：[accformal-006](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/accformal-006-ppu13-gpqa-c64-60k.md)于2026-10-17 19:27完成，当前无黑名单实例198题/C64/60K/阈值88%，strict-match 179/198=90.40%，gate签发及复验通过，服务/源码未漂移。API响应14条60K截断，空输出/超时0，截断不改变冻结分数判定；heartbeat已暂停。性能未测，不能据此声称端到端提速。

最新[fw-016](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/fw-016-unblacklisted-service-restart.md)对fw-015无新增测试/无thead.yaml差异的版本按原参数重启，C1/C8 10/10、16rank双模式capture及FULL180次执行通过，当前8024保留运行。冷启动约16分钟，现场采样证实视觉Conv3d候选扫描持续推进并最终自然完成；未恢复黑名单或修改算子，冻结日志与参数均已保留。下述fw-014仅为历史清理前配置证据。

指定提交 `620892ab8c083b137c24db6cfcdc32fe38cca963` 已安装并证实导入新路径。原样默认黑名单为空，TP0/1/15在视觉conv3d autotune同步中长时间未ready；恢复原配置conv3d/cudnn_convolution黑名单后env-002通过回归。当前fw-014在独立私有源码副本修正路由dtype/支持边界、调整worker patch时机；CPU72、真实PPU121项通过，16rank双模式capture及FULL180次执行通过，C1/C8共10请求最终答案10/10，health200。候选服务保留在8024。安装顺序/幂等有CPU/独立进程证据，不声称观察到运行中每rank安装事件。无性能或全量精度结论，证据等级 observation。

原始远程工作目录 `/mnt/nfs/users/jinghao/minimaxM3` 经 realpath 核验无变化，root:root/755、NFS 可用约7.4TiB。独立任务子目录：`/mnt/nfs/users/jinghao/minimaxM3/20261017-minimax-m3-ppu13-plugin-support`。完整命令、源码指纹、安装/启动日志和请求响应保存在该目录。

## 可恢复记录

- [模型状态与实验](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/README.md)
- 原 Plugin `/workspace/vllm-plugin-FL` 完整保留；安装回旧路径并重启本任务精确实例可回退。
- 文本推理检查范围：两次单请求、C8短/长上下文与中英混合提示、graph capture/replay。不覆盖图像推理、全平台兼容、GPQA或性能。
- 具体结果持续写回 [env-002](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/env-002-plugin-support-minimaxM3.md)。
- 当前候选与精确回退方式见 [fw-014](../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/fw-014-minimax-adaptation-contract-refinement.md)。上一健康checkout、baseline/candidate快照与完整补丁在远端refine-001目录；未提交或推送源码。
