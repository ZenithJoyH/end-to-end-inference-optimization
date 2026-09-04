# 性能评测工具

这些脚本来自“新模型适配”项目的公共 `test/perf_test/`，不依赖上游目录。

## 工具选择

| 文件 | 用途 | 状态 |
|---|---|---|
| `vllm_perf.py` | vLLM 多 workload、多轮 benchmark | 主要正式入口；模型、tokenizer 和服务地址由命令行显式传入 |
| `vllm_profile.py` | 调用 vLLM profile endpoint 并记录 trace | 参数化入口；只用于归因，不纳入正式性能汇总 |
| `sglang_perf.py` | SGLang benchmark | SGLang 后端按需使用 |
| `sglang_profile.py` | SGLang profiler | SGLang 后端按需使用 |
| `all_perf.py` | 较早的 vLLM 批量测试封装 | 保留参考；包含示例常量，不能直接作为新实验配置 |
| `trace_to_summary.py` | 汇总 PyTorch Chrome/Perfetto trace | 离线分析工具 |

## 正式 benchmark 要求

- 将脚本复制为案例专属 wrapper 或在案例目录保存对应补丁，不要悄悄修改公共 workload。
- 固定 model/tokenizer、endpoint、EOS、输入/输出长度、并发、请求数、轮数和随机数据策略。
- 至少一个 warmup 轮和多个稳态轮；不要只挑最快一轮。
- 任一正式轮请求失败、成功数不足或生成 token 不完整时，该轮不能进入汇总。
- baseline、candidate、revert 使用相同客户端、服务配置和 workload。
- ShareGPT 原始文件未迁入：上游文件约 673 MB。需要真实分布时在目标环境显式挂载，并记录路径、来源和 checksum。

vLLM 正式入口示例：

```bash
python3 evaluation/performance/vllm_perf.py \
  --model <served-model-name> \
  --tokenizer <tokenizer-path> \
  --host <service-host> \
  --port <service-port>
```

Profiler 入口使用同样的模型、tokenizer 和服务参数，并要求服务启动时显式启用 profiler。`all_perf.py` 和 SGLang 脚本保留了上游示例常量，使用前必须建立案例专属 wrapper；这些值不是本项目默认环境。
