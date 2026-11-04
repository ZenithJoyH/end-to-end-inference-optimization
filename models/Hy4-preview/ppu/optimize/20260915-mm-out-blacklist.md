# 20260915-mm-out-blacklist：T-Head mm_out 路由回退

- experiment-id：`20260915-mm-out-blacklist`
- 分类：`operator/replace`
- 状态：`retained`
- 场景：P4K，TP16

## 方向与改动

将 `mm_out` 加入 T-Head `flagos_blacklist`，使该 ATen 路径不再进入
FlagGems general MM；`FLAGGEMS_ENABLE_OPLIST_PATH` 只记录 enabled-op，不覆盖
黑名单。

## 效果与正确性

策略解析确认 `use_flaggems_op("mm_out")=False`。组合重采样中
`mm_kernel_general` 从旧 profile 的 111,633 次降为 0，证明运行时命中。
服务 smoke/C8 与 graph 护栏随组合候选通过。

## 决策与边界

保留。收益包含在后续组合端到端结果中，未单独建立 profiler-off A/B，不能把
热点消失直接换算为独立端到端收益。

