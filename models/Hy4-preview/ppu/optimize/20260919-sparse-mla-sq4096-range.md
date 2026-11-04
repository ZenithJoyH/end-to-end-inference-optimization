# 20260919-sparse-mla-sq4096-range：full-prefix 扩展到 SQ4096

- experiment-id：`20260919-sparse-mla-sq4096-range`
- 分类：`operator/improve`
- 状态：`retained_but_inactive_at_mbt2048`

## 方向与改动

将 full-prefix HQ4 分组路径从 SQ2048 扩展到 SQ4096。

## 效果与正确性

SQ2560/3072/4096 prefix-then-capped 为 `1.656x/1.387x/1.161x`，random 输入
不回退；精确性、graph replay 和聚焦测试 `29/29` 通过。

## 决策与边界

保留源码，但当前 `max-num-batched-tokens=2048` 下不会激活；不计入现有 E2E
收益。

