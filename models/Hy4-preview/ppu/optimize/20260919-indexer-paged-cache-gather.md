# 20260919-indexer-paged-cache-gather：分页 KV 直接 gather

- experiment-id：`20260919-indexer-paged-cache-gather`
- 分类：`operator/replace`
- 状态：`retained`

## 方向与改动

新增 T-Head vendor `hyv4_indexer.py`，按 paged-cache stride 和 block table
直接 gather 当前请求，避免对 `[424960,128]` 整个扁平 KV cache 执行
`index_select -> contiguous -> clone`。

## 效果与正确性

seq_len 2041/3987/4096 为 `2.70x/2.65x/2.66x`，每次减少约 `42–43 us`，
输出逐位一致；graph replay 和 Plugin `16/16` 通过。后续 trace 中大块
`index_select/contiguous/clone` 签名消失。

## 决策与边界

保留。服务级效果与同轮两项 Indexer 改动合并观察。

