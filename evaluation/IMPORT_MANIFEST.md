# 评测资产导入清单

- 导入日期：2026-09-03
- 来源项目：`新模型适配`
- 来源范围：公共 `test/Accuracy_test/` 与 `test/perf_test/`
- 集成方式：复制为当前仓库独立副本；运行时不读取或调用来源目录

## 精度资产

| 当前文件 | 来源文件 | 来源 SHA-256 | 本地修改 |
|---|---|---|---|
| `accuracy/llmrun.py` | `test/Accuracy_test/llmrun.py` | `82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e` | 2026-09-06：复用严格样本检查；原始正式副本在 test/ 保持不变 |
| `accuracy/llmrun_parallel.py` | `test/Accuracy_test/llmrun_parallel.py` | `68732e02d6809fa9ec60f05e26b7b8bbc610e639957cdfd235520e243882e215` | 无 |
| `accuracy/score_progress.py` | `test/Accuracy_test/score_progress.py` | `645380282dbf164868ca0d4f01da1a7d8c260a4638983f4731e9bdb3148fe97d` | 无 |
| `accuracy/README.md` | `test/Accuracy_test/README.md` | 未固定 | 路径和配置名本地化 |
| `accuracy/*.example.json` | 上游公共示例配置 | 未固定 | 移除模型/NFS 路径；默认拒绝超时 |
| `accuracy/verify_accuracy.py` | 当前项目新增 | — | 绝对阈值与相对基线门禁 |

## 性能资产

| 当前文件 | 来源 SHA-256 | 本地修改 |
|---|---|---|
| `performance/all_perf.py` | `02ea877553735000195e65ceaf2abeb5b7d371eae962a45399a19c58564622d1` | 显式指定目标；历史矩阵复用公共原生结果校验 |
| `performance/vllm_perf.py` | `c3dc6d8f9405a62fc51081086e7347d828fb63917ce956f04c8d21cc4001bfab` | model/tokenizer/服务地址参数化 |
| `performance/sglang_perf.py` | `a7c8bde7bc9ac590b7adaccfcce41eb3081249f2a8325f345a21b6f288aed1c4` | 目标参数化；固定长度/到达率与并发分离；详细 JSONL 和失败证据 |
| `performance/vllm_profile.py` | `7e67bb5b8022d6763349128b1fa09dd03fd4f166504f64d274bc56c6987c6e46` | 共享诊断编排；复用原生校验、分组汇总与新增 trace 验证 |
| `performance/sglang_profile.py` | `a1a190232e2051c8f52c6b4a46688c6a335df1152a6a1c442599325da6a17205` | 委托共享 profiling 流程 |
| `performance/trace_to_summary.py` | `ebbab01e75297e4d5cb3acdf3f144f9c3691ad659f5435e9b1d01f2faf3536e4` | 主机/设备/未知类别分开；校验时长、拒绝覆盖、传播目录失败 |

## 未导入

- `ShareGPT_V3_unfiltered_cleaned_split.json`：来源文件约 673 MB，属于大体积数据集，不纳入仓库。使用时在目标环境挂载并记录来源、路径和 checksum。
- 模型实例目录中的 Host、容器、NFS 路径、运行结果和一次性 wrapper：与具体适配环境绑定，不作为公共评测基线迁入。
- `.DS_Store`、response cache、输出、日志和 profiler trace：均为生成或本地状态。

## 2026-09-06 维护变更

新增 `formal_accuracy.py`、`sample_validation.py`、`acceptance.py` 及契约/身份模板；维护版性能工具修复非零退出和不完整轮次汇总；vLLM 固定长度/采样/逐轮 seed，保存原生 JSON 并检查 token 总数，旧 workload 需重建基线。分数工具拒绝 NaN/Inf 阈值，分数 PASS 明确不代表正式验收。实际正式 runner 仍为 test/Accuracy_test/llmrun.py，外层增加显式 seed 和校验。原始 test/ 中 11 个 runner/配置/性能文件的 SHA 均不因此改变。维护文件不再声称与导入来源字节相等。

本轮复审继续增加正式 task/数据 provenance、原生结果身份/样本内容交叉校验，精度 contract/run-record/gate 升为 schema 2；公共 vLLM 性能解析支持有失败计数和旧版完整逐请求两种结果结构，必需指标缺失/非法时失败。目标镜像和硬件集成仍需后续任务验证，历史记录不自动通过新门禁。

## 2026-09-07 修复更新

增加 schema 1 性能计划执行与预冻结比较契约，统一模型 wrapper 到公共执行器，校验原始指标与计数/时长一致性并提供三态比较。精度采集同步原生 TaskManager metadata，正式样本检查按冻结 filter 集合验证 198 唯一题目及跨 filter 一致性。原始 test/ 的导入字节基准继续保持；新工具、固定源码接口检查与实际目标镜像/硬件验证分别报告。
