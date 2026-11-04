# diag-006 根脚本启动失败定位

结论：当前根脚本与此前验证命令的FV开关不同，导致普通sigmoid路由选择缺失原生算子的reference路径。属于启动配置/不支持native fallback问题，不是本轮新测的模型分数下降。

## 当前事实与原因

- PPU-07容器minimaxM3.1-opt-topk-sigmoid-20261021身份与原容器一致；Plugin完整tree03261630bd3b6ba6503a7f40395cef4395b723038fd1f13cebada126c8e7bb35与review-005完全相同。
- 用户当前`/mnt/nfs/users/jinghao/minimaxM3.1/start-model.sh`设置TP8物理0–7、8035/name MiniMax-M3.1-new2、Flash1019，未设置VLLM_FL_USE_FLAGGEMS_VLLM；docker默认环境中也没有该变量，Plugin默认值为0。此前bootstrap和回归控制通过docker exec -e显式设为1，未写入容器永久环境。
- service.log在15:00:39记录topk_sigmoid和scaled_int8_mm选择reference.torch。1797行首个根异常为`AttributeError: '_OpNamespace' '_moe_C' object has no attribute 'topk_sigmoid'`，栈来自ReferenceBackend→vLLM fused_topk_bias→原生C算子。随后dispatch记录该实现失败；All implementations failed、Engine初始化失败及NCCL abort均是后续结果。
- 独立进程、禁用可见GPU的只读最小复现确认默认选择reference.torch、native符号不存在，直接调用reference发生相同AttributeError；仅将现有FV开关改为1并重建manager后选择default.flagos。该选择复现只证明路径切换，不冒充模型完整启动成功。CPU能力stub与既有合同测试一致，不算PPU硬件验证。

## 恢复方式与验证缺口

在目标容器内，使用`VLLM_FL_USE_FLAGGEMS_VLLM=1 bash /mnt/nfs/users/jinghao/minimaxM3.1/start-model.sh`可修正当前算子选择配置；也可以由用户在启动环境设置原开关。此处没有新增环境变量，也没有改变默认值或绕过用户原有policy。不开FV且当前vLLM无native sigmoid算子的组合仍不支持。

本次未修改根脚本、Plugin、FV、FG、编译器或容器环境，没有启动/重启/停止服务或发模型请求；8035及旧8045均无法访问。用户此前要求不重启仍保持。没有声明修正开关后已完成readiness、模型graph或全量精度。原正式分数与gate保持历史归属；正式性能仍不允许。

前轮验证显式开启FV，但未同时验证根脚本缺开关的直接启动，是交付验证范围缺口；119 CPU/4设备测试仍保留其既有准确scope，不改写为根脚本全栈启动通过。若后续需要确认整服务恢复，应按用户授权启动准确服务，检查实际路由命中、graph/readiness与最小模型回归，不用本次selection结果替代。

## 证据

原始日志/脚本快照及capture.json保存在`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/diagnosis/diag006-startup-20261022-01`；capture SHA7b07544ae8350363cf41665a33b8e2829526d4c41f122d6d0fdfc52e427360fa，原log SHA a09c431d60b9e099b029ac9355196df12be0371fac25320203b13cc01c55b42a。快照取证脚本先归档R/commands/diag006-capture-20261022.py，SHA40ec788c67eca1772d523532e10ba6226f438de9ef9c31ba76abc854da88404b。未覆盖原日志或重试模型启动。
