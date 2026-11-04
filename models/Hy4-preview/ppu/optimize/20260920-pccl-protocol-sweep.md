# 20260920-pccl-protocol-sweep：TP16 PCCl 协议扫描

- experiment-id：`20260920-pccl-protocol-sweep`
- 分类：`framework`
- 状态：`rejected_keep_default`

## 方向与结果

`NCCL_PROTO=Simple` 对约 25 MB all-reduce 提升 `8%–10%`，但 8 MB 退化约
`47%`、4 MB 退化 `12%–13%`；`Tree` 全面慢于默认，`Simple,LL` 与
`LL,Simple` 也不能按消息大小自动选择。

## 决策

不修改启动脚本，保持默认协议。若继续，需要厂商层 size threshold 或平台边界
融合，并重新走高风险精度 gate。

