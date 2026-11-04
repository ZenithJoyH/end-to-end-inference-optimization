# Hy4-preview / PPU 验收状态

Agent 结构化事实入口：[state.yml](state.yml)。

状态：`incomplete`。正式 GPQA gate 已通过；最终候选冻结与正式性能比较尚未完成。

当前状态（2026-09-21）：最新保留的 P16K cached-prefill sparse MLA hybrid
候选尚未提交、未推送，也没有与其源码身份匹配的精度 gate。下述 `92.93%` 是
历史冻结候选的有效证据，不能作为当前组合或最终验收的通过结论。

2026-09-19 的候选绑定评测完成 198/198、无 timeout，GPQA strict-match
`92.93% >= 87%`。签发的 gate SHA256 为
`503516c80851a17c27620bccfae7440792fa8d444f136023e830ca2fe47ee77a`，绑定
run-record SHA256
`55ecb5e6a69774a2c773bc010d50b875c1f8cfa5f3a20dcfb6afd2ff3d7065f4`；原始
证据位于远程案例的 `results/accuracy/formal-gate-20260918-f7d1aaa-a26a902-01/`。
该 gate 只适用于被冻结的服务身份。后续性能优化导致的代码变化或服务重启不能
复用它；最终组合仍需冻结并完成相应精度回归和正式性能比较。
