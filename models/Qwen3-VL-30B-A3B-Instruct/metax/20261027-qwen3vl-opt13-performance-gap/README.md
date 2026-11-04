# opt13 与历史 opt10 性能差距诊断

已完成现有数据只读核验；根因贡献仍待同机单变量验证，未改服务或发送新压测。

| 输入/输出，C64/N128 | opt10 总 tok/s | opt13 总 tok/s | 观测差额 |
|---|---:|---:|---:|
| 1K/1K | 3022.26 | 2316.93 | -23.34% |
| 4K/1K | 5410.82 | 5516.31 | +1.95% |
| 16K/1K | 6369.18 | 4804.64 | -24.56% |

[诊断、源码差异与规划复盘](optimize/diag-001-opt13-gap.md) · [结构化状态](optimize/state.yml)

1K仍有动态采样sort内核缓存写入，常见ITL更短而整轮尾部更慢；16K差距稳定且集中于Prefill/Mixed。当前与历史均split0/prefixOFF，采样补丁和gems-opt保留；PR638 Prefill路由、上游977后的MoE与跨Host环境是需隔离的差异。共享盘mtime与主机时钟存在约220秒偏差，不能按原始文件时间直接归属编译到某一轮。

P32/P64在取证时未完成，不外推。历史CSV无严格全轮绑定/逐请求原生JSON，当前opt13不能继承旧精度gate或签正式性能回退结论。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)

2026-10-27用户要求回退：[op-002 FLA回退](optimize/op-002-revert-pr638.md)已恢复当前分支原Prefill paged路径，保留默认split0及其他优化；唯一修改Attention文件。当前无模型进程，用户下次启动生效；未重测graph/精度/性能。上表opt13数字仍属于回退前PR638源码。
