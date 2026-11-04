# 20261026-qwen3vl-opt12-c64-default-accuracy / acceptance

用户指定的本轮精度任务已完成，两项均达到原阈值，各完整一次：GPQA129/198=65.1515分（阈值64）；ERQA原生168/398=42.21分（阈值40），2条SDK超时拒答保留，全部400计错168/400=42.00分也通过。两项均C64、模型默认采样、prefixON；原native提示/stop/18000输出cap保留。

ERQA原生完成后控制器等待残留HTTP drain而退出；原失败保留，仅CPU回收403个原生文件并逐文件SHA验证、重用原filter与评分逻辑恢复，0新增模型请求、未重跑。400unique/630图/源码/全部实际采样参数审计及原用户模型PID/source/models200均通过。最终证据见远端results/completed-recovered.json，SHA5e337ce4156964f4956a969fa6b92be0a34de08fb38b6f31e7a44f98777a6504；详细过程见[acc-001](../optimize/acc-001-opt12-c64-default.md)。

这只是本轮指定实例的精度结论，无四场景性能验收或PR638单变量收益结论。直接graph replay计数未观测；当时GPQA gate绑定的19964评测适配器已关闭，不复用给direct9999或未来重启。用户模型保持原PID运行、未改源码/参数或清cache。

<!-- e2e:summary:start -->

- 案例：20261026-qwen3vl-opt12-c64-default-accuracy
- 当前状态：completed-user-requested-accuracy-only
- 当前候选：opt12/GPU0,1/TP2/9999/prefixON/PR638+decode1/gemsopt/MoE;C64 server model defaults
- 下一步：No pending evaluation. User model retained;no performance acceptance or automatic rerun. Old gate binds measured adapter19964,not future direct endpoint or restart.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa198-c64-model-defaults | candidate | strict_match_accuracy | 65.15151515151516 | percent | 129/198;threshold64;full |
| erqa400-c64-model-defaults | candidate | native_accuracy | 42.21 | percent | 168/398;2native timeout rejects preserved;threshold40;400raw/evaluated IDs verified |
| erqa400-c64-model-defaults | candidate | all400_accuracy_timeout_incorrect | 42.0 | percent | 168/400;conservative supplementary denominator |

<!-- e2e:summary:end -->
