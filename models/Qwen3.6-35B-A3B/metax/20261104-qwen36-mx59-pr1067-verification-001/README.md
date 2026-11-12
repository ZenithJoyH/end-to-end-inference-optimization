# Qwen3.6-35B-A3B / mx-59 / PR1067验证

使用用户指定镜像的私有独立验证容器，main与PR各11项GPU数值/变化输入Graph测试通过。配置性能相对当前主线退化，PR继续草稿；M64集中路由完整MoE慢9.70%，M8192非快路径GEMM1慢13.96%，另一个GEMM2漂移超限incomplete。未运行模型全量精度或端到端性能。

- [验证总览](optimize/README.md)
- [完整实验与边界](optimize/pr1067-hardware-001.md)
- [算子参考与模型baseline范围](baseline/README.md)
- [验收状态](acceptance/README.md)
- [PR #1067](https://github.com/flagos-ai/FlagGems-vllm/pull/1067)

59专用验证容器已停止，其他服务、104容器和用户镜像不变。原始数据位于/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-mx59-pr1067-verification-001。
