# 20260920-native-decode-sparse-mla：pure Decode native MLA

- experiment-id：`20260920-native-decode-sparse-mla`
- 分类：`operator/replace`
- 状态：`rejected_and_reverted`
- 场景：`P4096/D128/C64/N64`

## 方向与改动

在 Plugin T-Head 边界 opt-in：仅 pure Decode 使用 PPU native sparse MLA，
Prefill 与其他形态保持原实现；Worker 命中日志用于排除 fallback。

## 效果与正确性

profiler-off A/B 中 output throughput `+0.196%`、duration `-0.196%`、mean
TPOT `-0.300%`。比较回执因历史 service manifest 缺唯一 `device_ids` 而为
`incomplete`，原始证据未改写。

## 决策

低于预冻结 `+2%` 门槛，使用保存补丁完整回退。该结果不否定 cached-prefill
长 SQ 的按语义 hybrid。

