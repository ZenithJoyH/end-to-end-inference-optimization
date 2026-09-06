# 项目工具单元测试

本目录只保存当前项目控制、评测和结果校验代码的自动化单元测试，不保存模型精度评测或推理性能 workload。

- `test/`：在目标环境中实际运行的精度评测、性能 benchmark 和 profiling 工具。
- `unit_tests/`：验证本项目 Python 工具行为的本地单元测试。

运行全部单元测试：

```bash
PYTHONPYCACHEPREFIX=/tmp/e2e-eval-pycache \
  python3 -m unittest discover -s unit_tests -p 'test_*.py'
```
