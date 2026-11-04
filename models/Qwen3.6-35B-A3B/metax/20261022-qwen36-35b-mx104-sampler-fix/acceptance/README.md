# 20261022-qwen36-35b-mx104-sampler-fix / acceptance

<!-- e2e:summary:start -->

- 案例：20261022-qwen36-35b-mx104-sampler-fix
- 当前状态：completed
- 当前候选：sampler-import-001-v2
- 下一步：本轮指定容器修复与实际服务命中验证已完成；正式模型精度/性能仍not_run。

| 实验 | 状态/决定 | 场景 | 文档 |
|---|---|---|---|

| 场景 | 角色 | 指标 | 数值 | 单位 | 范围 |
|---|---|---|---|---|---|

<!-- e2e:summary:end -->

本轮指定容器修复与实际服务命中验证completed，代码retained。两个worker均使用优化采样器，504次成功shortlist、至少512次成功请求graph replay。正式模型精度与性能not_run，gate=null；其他模型/平台和自定义runner未测。临时服务已关闭，容器继续运行。
