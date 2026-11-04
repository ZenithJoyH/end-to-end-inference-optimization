# 20261026-qwen3vl-metax-release-splits / optimize

<!-- e2e:summary:start -->

- 案例：20261026-qwen3vl-metax-release-splits
- 当前状态：completed-full-evaluation-GPQA-blocker-source-restored
- 当前候选：Original release image auto0 fully evaluated;not accuracy accepted;original source split1 restored
- 下一步：No scheduled work;GPQA inherited blocker remains unconfirmed. New diagnosis/fix/revalidation requires separately scoped work;no performance promotion

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| op-001-release-splits-audit | Image retains originalauto0path without later fixed1mitigation;same nativePython+binary and arithmetic behavior present;not evidence grosskernelerror or exactGPQAscore;leave imageunmodified | diagnostic-static-and-native-component | [op-001-release-splits-audit.md](op-001-release-splits-audit.md) |
| op-002-release-original-accuracy | No GPQA gate/no accuracy promotion;preserve original image and failed evidence;source split1 restored+verified;monitor deleted;no performance claim | full-gpqa198-erqa400 | [op-002-release-original-accuracy.md](op-002-release-original-accuracy.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->
