# 20261020-env011-gpqa-metax59 / acceptance

全量 GPQA Diamond 已完成：**101/198，exact_match,strict-match = 51.01%，未达到 80% 阈值**。没有签发精度通过 gate。198 题均返回，超时、空输出、截断均为 0。

当前组合为 env-011 加 MetaX top-k 启动兼容修复，TP8 graph。正式并发 C32、temperature=1、top_p=1、top_k=-1、max_gen_toks=30000、seed=42；数据、原生过滤器、输出和阈值保持冻结值。服务与源码前后核验一致。

61 题因答案字母加粗而未被原生 strict 正则识别，另 36 题提取成功但答案不符；根因部分定位，不能据此认定某个适配改动造成数值回退。详见 [acc-002 诊断](../optimize/acc-002.md)；首次 top-k 执行失败及修复见 [acc-001](../optimize/acc-001.md)。本次没有性能测量或性能通过结论。

原始证据在 mx-59 的评测容器和 deepseekV4-flash 容器中均保留：`/opt/dsv4-accuracy/20261020-env011-gpqa-02/`。其中 `manifests/final-review.json` 包含完整性、元数据、正式计分与文件 SHA 核验。首次失败证据也一并保留，跨容器归档 119 个文件、14,664,179 字节，逐文件 SHA 校验一致，校验回执为 `/opt/dsv4-upgrades/20261020-formal-accuracy-02/manifests/archive-parity.json`。前台进度监控已随评测终态结束。

<!-- e2e:summary:start -->

- 案例：20261020-env011-gpqa-metax59
- 当前状态：accuracy_failed
- 当前候选：env011+acc001-topk-fix:fc653169d482b61133db1783f22921a5432b7f7b4bf4e7a3eb67022f8c649223
- 下一步：Accuracy diagnosis acc-002; no gate and no performance promotion

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|
| gpqa-diamond-198 | candidate | exact_match,strict-match | 0.51010101010101 | fraction | full |

<!-- e2e:summary:end -->
