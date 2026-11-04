# 20261015-hy4-preview-ppu13-clone / optimize

<!-- e2e:summary:start -->

- 案例：20261015-hy4-preview-ppu13-clone
- 当前状态：kept
- 当前候选：hy4-preview@PPU-13:20261016-ppu13-slim
- 下一步：accuracy-retest-completed-await-user-next-step-no-auto-performance-run

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-003 | passed | gpqa-diamond-full-c64 | [acc-003.md](acc-003.md) |
| acc-004 | completed | musr-team-allocation-full-c64 | [acc-004.md](acc-004.md) |
| env-002 | retained | image-slimming | [env-002.md](env-002.md) |
| env-001 | retained | environment-clone | [env-001.md](env-001.md) |
| acc-001 | passed | gpqa-diamond-full-c64 | [acc-001.md](acc-001.md) |
| acc-002 | completed | musr-team-allocation-full-c64 | [acc-002.md](acc-002.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa-diamond-full-c64 | acc-001-historical-service | exact_match,strict-match | 0.898989898989899 | ratio | full-accuracy-198-unique-samples |
| gpqa-diamond-full-c64 | acc-003-slim-current-service | exact_match,strict-match | 0.9191919191919192 | ratio | full-accuracy-198-unique-samples |
| musr-team-allocation-full-c64 | acc-004-slim-current-service | exact_match,custom-extract | 0.66 | ratio | full-accuracy-250-unique-samples-native-score |
| musr-team-allocation-full-c64 | acc-004-slim-format-diagnostic-only | exact_match,optional-left-parenthesis | 0.84 | ratio | same-250-outputs-diagnostic-not-native-score-or-gate |

<!-- e2e:summary:end -->

当前瘦身镜像复测：acc-003于2026-10-17 01:06 +08:00完成，GPQA strict-match 182/198（91.92% ≥ 87%），原生gate签发及完整依赖复验通过；198唯一题目、396行filter完整，评测前后及实时服务/源码身份一致。1个length结束、1个样本timeout标记仅作健康观察；未重启、未改配置。用户服务仍启用prefix cache，本轮不声明正式性能结论。

队列完成（2026-10-17 02:27 +08:00，02:52复验）：MuSR 250唯一题目完整，原生165/250＝66.00%，同批输出可选左括号诊断210/250＝84.00%，其中45题提取假阴性；剩余39题选项不同、1题最小诊断规则未解析，不把后者认定为推理错误。原生分数保持不变；与acc-002诊断84.4%的差异不能单凭单次随机采样归因镜像或推理优化。原生证据SHA、task/data及服务/源码前后与当前身份通过核验，MuSR error/abort/length/timeout均0。

两项均C64且串行，全部448题有响应，服务无运行/排队请求且保持启动，控制进程已退出。共享30分钟heartbeat `hy4-gpqa-musr-c64` 已由automation_update确认PAUSED。不重跑、不改变服务/源码/参数，不自动发起性能测量。

2026-10-16空间维护cleanup-001已完成：仅清理当前服务启动前、容器可写层`/tmp`中82132个可再生LLVM `.tix`中间文件，逻辑2.05GB，文件系统可用空间增加约2.29GB。服务未重启且health正常，模型/代码、当前编译缓存和全部评测证据保留，MuSR原始产物SHA复核未变。镜像底层未删，526.4GB镜像大小不变；大幅瘦身需另建干净镜像，不在本轮执行。详见[env-001.md](env-001.md)。

后续env-002已另建`hy4-preview-optimized:20261016-ppu13-slim`（1552f30d4387，34.23GB，单层）。源SDK/依赖、三库优化（含未提交改动）及调优配置指纹一致，运行Config与挂载核验通过，同无设备隔离条件Torch/Triton/vLLM导入通过。打包阶段未切换服务、未进行GPU精度评测；之后由用户自行启动新镜像服务并完成上述acc-003/acc-004。GPU性能仍未复测。临时验证容器已清理，未推送registry；旧镜像保留，所以旧镜像占用尚未回收。详情见[env-002.md](env-002.md)。
