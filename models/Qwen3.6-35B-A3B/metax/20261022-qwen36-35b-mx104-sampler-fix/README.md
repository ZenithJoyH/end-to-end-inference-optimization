# 20261022-qwen36-35b-mx104-sampler-fix

已完成 `mx-104` / `qwen3.6-35B-verify` 的 Plugin 采样导入顺序修复，并保留代码。模型为 `/data/Qwen3.6-35B-A3B-nomtp`；Plugin 基于 `release/0.2@7cb559947`。本轮只修改 3 个生产文件的生命周期并新增 1 个集成测试，原采样 guards/数值方法与 kernel 保持不变。

**6 项新鲜导入测试、25 项独立数值/边界回归通过；实际 TP2（GPU0、1）服务的两个 worker 都构造优化采样器，17 个 C1/C8 请求成功，观察到 504 次成功 shortlist 与至少 512 次请求阶段 graph replay。** 首版 4 失败/2 通过及 GDN eager import 循环诊断保留；第二版修复后完成上述验证。

临时验证服务已停止、端口关闭、GPU 无残留进程，容器继续运行。vLLM、FlagGems-vllm、FlagGems 包文件不变，四包仍从各自 editable 源码目录加载。正式模型精度与性能 `not_run`，未签 gate；其他模型/平台与绕开 ModelRunnerFL 的自定义 runner 未测。

- [修复前基线与失败证据](baseline/README.md)
- [修复、数值和服务验证](optimize/README.md)
- [交付与验收边界](acceptance/README.md)
- [可复用案例摘要](../../../../docs/cases/20261022-qwen36-35b-mx104-sampler-fix/README.md)

远端原始材料：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-sampler-fix`。本地仅保存 Markdown/YAML 摘要，精确启动进程身份见远端 `service-001/launch.json`。
