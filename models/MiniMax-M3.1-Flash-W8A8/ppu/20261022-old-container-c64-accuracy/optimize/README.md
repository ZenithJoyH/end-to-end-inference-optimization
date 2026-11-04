# 20261022-old-container-c64-accuracy / optimize

三项旧容器C64全量精度已完成并核验：GPQA167/198=84.34%（81%门槛及原生gate通过）、Math500469/500=93.80%、ERQA252/400=63.00%（后两项score-only）。105+2最小回归及graph前置通过；实际脚本max_model_len100000、prefixcache开启，采样1/.95/-1，生成18k/28k/30k。未改为历史32768配置，不混用历史最高分。整套controller终态，minimax-c64已删除；模型服务保留，无性能任务。

[与new2逐题比较](diag-002.md)：旧C64相对new2的GPQA持平，Math500高1.00个百分点（+5题），ERQA低1.75个百分点（−7题）。ERQA双方221题均对、110题均错，旧对新错31、反向38；空/NUL均0，触顶旧6/new2 8。客户端并发与源码/compiler均不同，不能归因单个改动。

<!-- e2e:summary:start -->

- 案例：20261022-old-container-c64-accuracy
- 当前状态：old-container-c64-all-three-complete-verified
- 当前候选：user-old-container-start-script-20261022
- 下一步：No active evaluation or monitor. Existing model service retained; no performance or further inference requested.

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|
| acc-001 | all_three_complete_verified | — | [acc-001.md](acc-001.md) |
| diag-002 | all_three_native_offline_comparison_complete | — | [diag-002.md](diag-002.md) |

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa | old-container-c64 | native_accuracy | 84.34343434343434 | percent | acc-001 full 198 samples; C64; GPQA threshold81%, other tasks score-only |
| math500 | old-container-c64 | native_accuracy | 93.8 | percent | acc-001 full 500 samples; C64; GPQA threshold81%, other tasks score-only |
| erqa | old-container-c64 | native_accuracy | 63.0 | percent | acc-001 full 400 samples; C64; GPQA threshold81%, other tasks score-only |

<!-- e2e:summary:end -->
