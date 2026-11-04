# maint-007：删除本轮新增MoE测试

用户要求删除FlagGems-vllm库中本任务新增的全部MoE测试文件。目标仍为mx-59独立容器`qwen3vl-p64k-opt-20261015`，清单由实际git未跟踪文件与历史记录交叉核验，仅`tests/test_moe_config_dir.py`。仓库已有MoE测试及案例目录外部验证脚本保留。

文件内容已冻结在`commands/op008-sampler-integration-20261016/before.json`，删除前另存`removed-test_moe_config_dir.py`并校验SHA。清理命令`cleanup_moe_tests.py`只删除该清单文件，验证无新增MoE测试残留；不修改MoE配置加载器、JSON、kernel或Plugin MoE调用。

清理已执行成功。原始回执为远端案例`results/maint007-removed-moe-tests.json`，命令SHA及最终回执写入state。其运行源码没有变化，不单独重复MoE数值评测；随后op008统一验证服务graph与MoE配置保持。
