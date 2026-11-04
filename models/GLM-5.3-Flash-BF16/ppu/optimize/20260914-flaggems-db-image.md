# 20260914-flaggems-db-image FlagGems 调优库固化

- 状态：`retained`
- 分类：`deployment`
- 目标场景：所有后续性能与 graph 服务
- 目标阶段：Prefill / Decode / Mixed
- 依赖：`FLAGGEMS_DB_URL`

## 优化方向与瓶颈依据

在线 autotune 会引入不可重复的冷启动、长尾和 DB 写入，影响性能比较与服务稳定性。

## 优化内容与适用边界

把预热后的 FlagGems SQLite 调优库放入容器内稳定目录，通过
`FLAGGEMS_DB_URL` 绑定，并在实验前后校验 SHA 和 WAL。

## 正确性与路径命中

后续有效 A/B/R 使用同一 DB；exact-M64 测量期间数据库 SHA 保持
`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`，WAL 为 0。

## 性能效果

该点改善的是可复现性和冷 shape 稳定性，不声明独立稳态吞吐增益。它使后续单变量
性能比较不被在线调优写库混淆。

## 决定、风险与回退

决定保留。新增未知 shape 仍可能触发缺失配置；回退为更换 DB URL，但会失去当前
冻结证据的一致性。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/flaggems-db-image-20260914`

