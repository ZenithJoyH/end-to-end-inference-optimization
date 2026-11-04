# Plugin 分支替换

| 实验 | 方向 / 场景 | 变量 | 性能 | 正确性 | 决定 |
|---|---|---|---|---|---|
| [fw-020-fp32-router-opt-in](fw-020-fp32-router-opt-in.md) | 用户要求默认关闭router替代 | 默认不注册GateLinearFL，保留显式白名单和原类 | 未测 | 629项CPU/static/mock通过；设备/模型待测 | retained默认关闭；仅1文件，不影响8011 |
| [env-004-single-final-checkout](env-004-single-final-checkout.md) | 用户要求版本收敛 | 6份Plugin/3份FGV完整归档，统一安装各1份 | 不涉及 | 600项CPU重跑通过；源码hash/安装路径一致 | completed；七份旧目录移除、可归档恢复，8011未变 |
| [fw-018-fp32-router-gemm-dispatch](fw-018-fp32-router-gemm-dispatch.md) | FP32 router接入 | H6144/E128、M≤32分发、M>32原FP32 linear | 未测 | 专项69项通过；组合CPU600通过；PPU待测 | 私有候选未安装；CPU动态compile/真实vLLM回退通过，8011保留 |
| [fw-019-oai-experts-integration](fw-019-oai-experts-integration.md) | OAI整体experts接入 | 原alpha/beta/clamp透传，旧API/LoRA/quant回退 | 未测 | 专项115项通过；组合CPU600通过；PPU待测 | 关联fw-018；无硬件/模型结论，不影响8011 |
| [fw-017-topk-sigmoid-dispatch](fw-017-topk-sigmoid-dispatch.md) | 独立topk_sigmoid分发 | 替代router单组grouped_topk复用 | 未测 | 最终415项CPU/static/mock通过；PPU/graph/模型待测 | 用户要求保留8011；候选私有，不切换安装，可回退 |
| [env-003-flaggems-vllm-update](env-003-flaggems-vllm-update.md) | 用户要求依赖更新 | 官方main46387d7 + 保留原packed SwiGLU | 未测 | 0.3.0.dev1安装/导入通过，topk_sigmoid可用；未执行硬件计算 | 已切换私有副本，可回退；未改Plugin/启动服务；旧GPQA仅历史组合 |
| [accformal-006-ppu13-gpqa-c64-60k](accformal-006-ppu13-gpqa-c64-60k.md) | 当前服务全量正式GPQA | 198题/C64/60K/阈值88% | 不涉及 | strict-match 179/198=90.40%，gate复验通过 | passed；14条60K截断单独记录，heartbeat暂停 |
| [fw-016-unblacklisted-service-restart](fw-016-unblacklisted-service-restart.md) | 撤销yaml后重启验证 | 不恢复卷积黑名单；其余启动契约不变 | 未测；启动约16分钟 | C1/C8 10/10；16rank双模式capture、FULL180次 | passed最小回归；慢Conv3d调优证据保留 |
| [fw-015-plugin-delivery-cleanup](fw-015-plugin-delivery-cleanup.md) | 用户要求交付清理 | 移出2项新增测试、恢复HEAD的thead.yaml | 未测 | 静态检查通过；新磁盘配置未重启验证 | 已完成，可恢复备份 |
| [fw-014-minimax-adaptation-contract-refinement](fw-014-minimax-adaptation-contract-refinement.md) | 小范围契约/生命周期修正 | 路由dtype/边界，worker时机 | 未测 | CPU72+PPU121通过；C1/C8最终答案10/10；16rank capture、FULL180次 | retained，保留健康版回退 |
| [env-002-plugin-support-minimaxM3](env-002-plugin-support-minimaxM3.md) | 环境切换 / smoke+C8 | Plugin620892ab + 恢复既有卷积黑名单 | 未测 | 最终答案10/10；16rank双模式capture；FULL180次 | retained，非正式精度 |

保留原私有 Plugin checkout；不修改其他源码或共享启动脚本。

最新fw-020已按用户要求默认关闭FGV fp32_router_gemm的GateLinear替代：默认不注册GateLinearFL，模型使用原vLLM GateLinear类。现有OOT白名单显式包含gate_linear或调用方明确选择仍可接入，小M分发/大M回退保留；topk/OAI不改。629项CPU/static/mock通过（原600+新29），没有设备/模型验证。

env-004统一的`/workspace/vllm-plugin-FL`与`/workspace/FlagGems-vllm`及editable安装不变，各只有一份源码/安装记录。Plugin为43e0980+fw017/018/019/020（包版本仍0.0.0+g43e0980de.d20261018），FGV为46387d7/0.3.0.dev1+原packed SwiGLU。fw-020仅修改custom_ops.py的默认注册及说明，FGV和其他源码hash未变。无新增Plugin test文件或thead.yaml差异，未提交或推送。

七份旧工作副本已移除，完整9份原始目录归档在远端`consolidate-001-20261018/backup/source-before.tar.gz`，包含Git、dirty/untracked，可恢复。旧dated目录和旧回退脚本路径不再有效，使用env-004的RESTORE.md恢复说明，不直接运行历史rollback脚本。

fw-018/fw-019保留大batch FP32 linear回退，未限制服务max_num_seqs；原激活参数及SiLU/旧API/LoRA/quant回退不变。600项包含专项184+组合静态1+原topk415；本次仅变更目录/安装，未改变算子逻辑。

用户要求保留其他容器8011，因此未做PPU kernel/graph/模型验证，不宣称推理正常或加速。env-004前后8011原API实例相同且health200；没有GPU初始化、模型启动或停止/重启命令。当前是源码安装已切换，但模型运行验证仍待设备条件明确。

规划复盘`review-fw017-fw019-cpu-only-20261018`：结论incomplete，缺少新组合PPU正确性、正式精度与任何同配置性能数据。三阶段Prefill/Decode/Mixed收益和热点迁移均未知；下一步优先真实算子/分发验证，再graph+TP16模型回归与GPQA≥88%，最后才做同配置阶段/Mixed性能比较。当前用户代码/CPU范围已完成，不自动申请设备、启动评测或继续叠加优化。

当前依赖以2026-10-18 env-003为准：FlagGems-vllm已切换main46387d7的私有副本并保留原packed SwiGLU，旧源码未改。更新前8024服务已不在运行，本轮未启动。下文GPQA/服务health为2026-10-17原组合的历史证据，不绑定更新后依赖；新组合仍需模型与正式精度验证。

2026-10-18按用户要求将当前源码amend进原提交（非追加commit），`support-minimaxM3`现为[43e0980](https://github.com/ZenithJoyH/vllm-plugin-FL/commit/43e0980de214b75fd1a813e7e1f8cfcbb557edbc)，替换620892ab；原父节点、作者、说明及提交总数不变，force-with-lease推送及远端复核通过。无新增测试或thead.yaml差异；运行中容器HEAD/代码未改动，原gate不改写。备份及发布证据见[fw-014](fw-014-minimax-adaptation-contract-refinement.md)。

当前磁盘交付已按fw-015清理，仅剩3个源码文件diff，无新增测试、无thead.yaml修改。fw-016已按原启动契约重启并独立通过C1/C8和graph回归，当前health200，实例 `fad201d7b6ec:8024:30544:494374945`。无黑名单冷启动约16分钟，采样定位视觉Conv3d autotune；候选确有推进且最终自然完成，不是本轮已证实的永久死锁。全程未恢复黑名单或修改算子，慢启动现场与冻结日志保留。

历史：原样分支在视觉conv3d autotune同步处长时间未ready，恢复conv3d/cudnn_convolution黑名单后通过env-002回归。fw-014继承该配置通过，旧实例 `fad201d7b6ec:8024:23178:493728712` 已由fw-016精确重启，旧证据保留。PIECEWISE仅完成capture，未在请求中观察到replay。worker安装顺序/幂等由CPU和独立进程探针核验，默认INFO日志不可见，不宣称已观察16rank安装事件。当前组合全量GPQA已由accformal-006通过：179/198=90.40%≥88%，耗时90分14秒，服务/源码未漂移；14条API响应达到60K上限，空输出及超时0，不改变精度通过结论。gate签发及check通过，heartbeat已暂停；性能、真实多模态与100K输入边界未测，不继承旧gate。
