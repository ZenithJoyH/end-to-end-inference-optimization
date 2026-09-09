# 项目工具单元测试

本目录只保存当前项目控制、评测和结果校验代码的自动化单元测试，不保存模型精度评测或推理性能 workload。

- `test/`：在目标环境中实际运行的精度评测、性能 benchmark 和 profiling 工具。
- `unit_tests/`：验证本项目 Python 工具行为的本地单元测试。

运行全部单元测试：

```bash
PYTHONPYCACHEPREFIX=/tmp/e2e-eval-pycache \
  python3 -m unittest discover -s unit_tests -p 'test_*.py'
```

覆盖精度异常样本与非有限阈值、冻结契约和当前服务关联、正式 wrapper 编排、性能失败/缺轮拒绝汇总、明确 Host 限制和挂载差异。外部评测进程与 benchmark 以替身模拟；这些测试不构成模型精度或远端性能验收。

来源与格式负例分别位于 `test_accuracy_provenance.py` 和 `test_perf_result_schema.py`：验证错误服务/数据/样本计数、仅计数而无指标、旧版缺失失败字段及非有限指标等情况。原生格式夹具只代表已核对的结构，目标镜像及平台 fork 仍需集成验证。

配置执行、模型 wrapper 和三态比较分别见 `test_performance_plan.py`、`test_model_perf_wrapper.py`、`test_performance_comparison.py`，包括执行器产物直接进入比较器的联调。可选的 `test_lm_eval_source_interface.py` 通过指定固定官方 wheel 执行原始方法接口检查；未提供 wheel 时明确跳过，不自动下载依赖，使用方式见精度 README。

`test_accuracy_failures.py` 覆盖非法整数配置、验证失败不发布完成记录和原子产物发布；`test_profiling_and_reference_tools.py` 覆盖 profiling 失败/缺 trace、采集轮次分组、SGLang 原生计数/负载与 trace 分类。定向失败用例用于阻止误成功，不能替代后端集成测试。

`test_control_model_tools.py` 覆盖目标歧义、挂载选项、精确 sanity、历史汇总和启动 readiness；启动、进程及 HTTP 检查用替身模拟，不会启动模型服务。性能计划测试另外创建不安装 pip 的本地虚拟环境和合成包，验证客户端探针确实使用原虚拟环境入口及源码内容。

完整本地验证使用 `./scripts/validate-local`。原始 `test/` 资产的逐文件 SHA 由清单核验，禁止通过更新哈希掩盖意外修改。
