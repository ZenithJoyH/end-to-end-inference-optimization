# 测试资产完整性清单

本目录中的 runner、配置和性能工具已纳入当前项目，不与原模型适配工作区建立运行时联系。本清单记录当前副本的 SHA-256，用于把正式评测时进入容器的文件与项目基准进行核对。

说明文档会随当前项目的 SOP 持续维护，因此不将 README 的哈希作为上游字节等价证明。正式 GPQA Diamond runner 的基准是 `Accuracy_test/llmrun.py`。

## Accuracy_test

| 文件 | SHA-256 | 角色 |
|---|---|---|
| `Accuracy_test/llmrun.py` | `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e` | 默认正式 GPQA Diamond runner |
| `Accuracy_test/llmrun_parallel.py` | `68732e02d6809fa9ec60f05e26b7b8bbc610e639957cdfd235520e243882e215` | 多服务/多 shard 入口；仅显式指定时使用 |
| `Accuracy_test/score_progress.py` | `645380282dbf164868ca0d4f01da1a7d8c260a4638983f4731e9bdb3148fe97d` | 阶段计分辅助进程 |
| `Accuracy_test/llm_config.json` | `9c5cbbf6cdbaf7021190ae1fe83d83e7ebabeffe0f8f722d5aebf8f6a4a62c74` | 原始单服务配置；正式任务使用案例专属副本 |
| `Accuracy_test/llm_parallel_config.json` | `56f5a922e39e33807fb61ddc8c62ea4b8b2e1b0f980adc4427b461f197067099` | 原始分片配置；非默认正式路径 |

## perf_test

| 文件 | SHA-256 |
|---|---|
| `perf_test/all_perf.py` | `02ea877553735000195e65ceaf2abeb5b7d371eae962a45399a19c58564622d1` |
| `perf_test/sglang_perf.py` | `a7c8bde7bc9ac590b7adaccfcce41eb3081249f2a8325f345a21b6f288aed1c4` |
| `perf_test/sglang_profile.py` | `a1a190232e2051c8f52c6b4a46688c6a335df1152a6a1c442599325da6a17205` |
| `perf_test/trace_to_summary.py` | `ebbab01e75297e4d5cb3acdf3f144f9c3691ad659f5435e9b1d01f2faf3536e4` |
| `perf_test/vllm_perf.py` | `c3dc6d8f9405a62fc51081086e7347d828fb63917ce956f04c8d21cc4001bfab` |
| `perf_test/vllm_profile.py` | `7e67bb5b8022d6763349128b1fa09dd03fd4f166504f64d274bc56c6987c6e46` |

正式评测前在本地和目标评测容器内分别计算 runner 哈希；不一致时停止评测并确认部署来源，不以文件名相同代替内容一致。
