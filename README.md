# 端到端推理优化

本仓库用于对已经完成模型适配的推理服务做端到端性能分析和优化。

优化工作分为两个层面：`vllm-plugin-FL` 中的框架层优化，以及算子层优化。算子层进一步区分“接入更好的已有实现”和“优化当前实现”。分类边界、默认顺序和动态候选排名见 [优化 SOP](docs/performance-optimization-sop.md)。

当前工作区已包含一套独立的本地远端控制面：

- `inventory/`：目标机器的 SSH Host 别名和平台变量
- `playbooks/`：连接、健康状态和加速卡只读检查
- `scripts/`：本地 Ansible 环境及 Playbook 包装入口
- `docs/vllm-plugin-FL-analysis.md`：`vllm-plugin-FL` 架构与修改边界分析
- `docs/performance-optimization-sop.md`：随实际案例持续演进的端到端优化 SOP
- `docs/optimization-patterns.md`：从多个案例提炼的可迁移模式、边界和反例
- `docs/cases/`：成功、失败、回退与阻塞案例的索引和记录模板
- `models/<model>/<platform>/`：每个平台仅使用 `baseline/`、`optimize/`、`acceptance/` 三个产物目录
- `evaluation/`：独立的精度评测、性能 benchmark、profiling 工具和验收模板
- `test/Accuracy_test/`：正式 GPQA Diamond runner；在目标机器的 `flageval-llmeval:v1` 评测容器内使用 `llmrun.py`
- `test/perf_test/`：从适配流程纳入的原始性能测试与 profiling 工具
- `unit_tests/`：当前项目控制、评测和结果校验代码的本地单元测试；不用于模型精度或性能评测
- `skills/key-operator-analysis/`：关键算子分析技能及 MLA、mHC 知识库

SSH 用户、端口、堡垒机和密钥由本机 `~/.ssh/config` 管理，不写入仓库。

首次初始化：

```bash
./scripts/bootstrap-control-node
./scripts/inventory
./scripts/syntax-check
```

按需检查连接或硬件，不要无目标地探测所有机器：

```bash
./scripts/connectivity-check --limit <host-alias>
./scripts/health-check --limit <host-alias>
./scripts/accelerator-check --limit <host-alias>
```

具体工作方式、安全边界和实验规范见 `AGENTS.md`。
