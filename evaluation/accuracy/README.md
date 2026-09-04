# 精度评测脚本说明

本目录保存 GPQA Diamond 精度评测工具。新模型适配的正式精度验收固定使用：

- `llmrun.py`：基于 `lm-evaluation-harness`（命令为 `lm_eval`）的正式单服务评测入口。
- `llmrun_parallel.py`：保留用于明确指定的多服务、多 shard 场景，不能替代新模型适配的默认正式验收入口。

正式评测必须在目标机器上进入基于
`harbor.baai.ac.cn/flageval/flageval-llmeval:v1` 镜像的容器执行。默认评测完整的
198 道 `gpqa_diamond_generative_cot`。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `llmrun.py` | 单服务、单评测进程入口；支持服务等待、重试、本地响应缓存、结果校验和阶段计分。 |
| `llm_config.example.json` | `llmrun.py` 的配置模板；复制为案例专属配置后使用。 |
| `llmrun_parallel.py` | 多服务、多 shard 并行评测入口；各 shard 完成后合并正式结果。 |
| `llm_parallel_config.example.json` | `llmrun_parallel.py` 的配置模板。 |
| `score_progress.py` | GPQA 阶段计分辅助进程；由两个 runner 自动启动，不建议单独修改。 |

`score_progress.py` 必须和 `llmrun.py`、`llmrun_parallel.py` 放在同一目录，否则正式评测仍可运行，但不会输出中间得分。

## 运行环境

在目标机器上先找到并核对用于评测的容器：

```bash
docker ps --filter ancestor=harbor.baai.ac.cn/flageval/flageval-llmeval:v1 \
  --format '{{.ID}} {{.Names}} {{.Image}}'
docker inspect --format '{{.Config.Image}}' <container-name>
docker exec -it <container-name> bash
```

`docker inspect` 的镜像必须是
`harbor.baai.ac.cn/flageval/flageval-llmeval:v1`。进入容器后，正式 `lm_eval`
流程至少需要：

- `python3`
- `lm_eval`
- `datasets`
- 已缓存的 GPQA Diamond 数据集（当前配置为离线模式）
- 可访问的 OpenAI 兼容接口及 `/v1/models` 接口

进入脚本目录：

```bash
cd <容器内项目目录>/evaluation/accuracy
```

先做只读预检：

```bash
python3 llmrun.py <case-config.json> --preflight-only
```

预检会验证配置、离线数据集、模型服务和服务返回的模型 ID，但不会发起正式评测请求。

## 单服务评测

### 后台启动

```bash
nohup python3 llmrun.py <case-config.json> \
  > gpqa_full_c32_launcher.log 2>&1 &

echo $!
```

启动前应检查案例专属配置中的以下关键字段：

| 字段 | 含义 |
| --- | --- |
| `eval_model` | 本次评测的目录标签，不是发送给服务的模型名。建议把权重版本、graph/eager 和并发写进名称。 |
| `model_name` | 请求中的模型名，必须出现在 `/v1/models` 返回结果中。 |
| `base_url` | Chat Completions 完整地址，例如 `http://127.0.0.1:8010/v1/chat/completions`。 |
| `tasks` | 任务列表；阶段计分目前只支持 `gpqa_diamond_generative_cot`。 |
| `limit` | `0` 表示全量；正整数表示只跑前 N 道。 |
| `num_concurrent` | 单个 `lm_eval` 进程的请求并发数。 |
| `gen_kwargs` | 采样和最大生成长度，例如温度、`top_p`、`top_k`、`max_gen_toks`。 |
| `timeout` | 单次 API 请求超时，单位为秒。 |
| `api_max_retries` | API 客户端内部重试次数。 |
| `eval_max_retries` | 整个任务失败后的 runner 重试次数。重试时复用同一轮响应缓存。 |
| `allow_timeouts` | 是否允许最终样本中存在超时记录。 |
| `run_id` | `auto` 时每次生成新的时间戳；固定旧值时可尝试复用同一响应缓存。 |
| `progress_score_interval` | 每新增多少条缓存回复打印一次阶段得分；`0` 表示关闭。 |
| `progress_score_poll_seconds` | 阶段计分器扫描 SQLite 的周期，单位为秒。 |
| `service_poll_interval` | 服务未就绪时的再次探测间隔，单位为秒；当前 1800 即半小时。 |
| `service_wait_timeout` | 等待服务的总超时秒数；`0` 表示持续等待。 |

如果要启动 64 并发，至少同时修改：

```json
{
  "eval_model": "Qwen3.8-flash-gpqa-full-graph-c64",
  "num_concurrent": 64
}
```

其中真正控制并发的是 `num_concurrent`；`eval_model` 只是便于区分结果的标签。

### 查看运行日志和阶段得分

查看完整 launcher 日志：

```bash
tail -F gpqa_full_c32_launcher.log
```

只看阶段得分：

```bash
tail -F gpqa_full_c32_launcher.log \
  | grep --line-buffered '\[SCORE\]'
```

阶段得分也会单独写入：

```text
<output_root>/<eval_model>/<run_id>/<task>/progress_score.log
```

自动查找并查看最新计分日志：

```bash
SCORE_LOG=$(find outputs -name progress_score.log -type f -print0 \
  | xargs -0 ls -t | head -1)
echo "$SCORE_LOG"
tail -F "$SCORE_LOG"
```

典型输出：

```text
[SCORE] completed=30/198, matched=30, timeouts=0, strict=30/30 (100.00%), flexible=13/30 (43.33%)
```

- `completed`：SQLite 中已有的回复数。
- `matched`：成功映射到 GPQA 题目的回复数。正常情况下应等于 `completed`。
- `timeouts`：已缓存的超时回复数。
- `strict`：正式 GPQA 汇总采用的严格答案提取得分，重点观察这一项。
- `flexible`：任务附带的另一种提取结果，不是当前 group 的正式汇总指标。

并发运行时先完成的往往是生成较短的题，因此前 10、20、30 道的阶段得分不是严格随机抽样，只适合早期排障，不能代替全量结果。

## 输出、模型回复和缓存

单服务评测的持久化输出结构：

```text
<output_root>/<eval_model>/<run_id>/
├── effective_config.json
└── <task>/
    ├── lm_eval.log
    ├── progress_score.log
    ├── results_*.json
    └── samples_*.jsonl
```

- `effective_config.json`：补齐默认值并解析路径后的实际配置。
- `lm_eval.log`：该任务的完整 `lm_eval` 输出。
- `progress_score.log`：运行中的阶段得分。
- `results_*.json`：最终汇总指标，通常在任务完成时生成。
- `samples_*.jsonl`：每道题的输入、回复、过滤后的答案和得分，通常在任务完成时生成。

运行中的模型回复先保存在容器本地 SQLite：

```text
<cache_root>/<eval_model>/<run_id>/<task>/responses.sqlite_rank0.db
```

默认 `cache_root=/tmp/lm_eval_cache`。SQLite 内的值是序列化数据，不适合直接 `cat`；评测结束后优先查看 NFS 输出目录中的 `samples_*.jsonl`。

`/tmp` 缓存可能在容器删除或重建后丢失，而 NFS 下的结果会保留。

### run_id 和断点续跑

正常的新一轮评测使用：

```json
"run_id": "auto"
```

每次会生成形如 `20260825-153357` 的新目录，不会复用上一轮模型回复。Hugging Face 数据集缓存仍会复用，但它只包含题目，不包含模型答案。

查找最近一次单服务运行 ID：

```bash
ls -dt outputs/<eval_model>/*/ | head -1
```

如果任务意外中断，并且模型权重、推理参数和 prompt 均未变化，可以把 `run_id` 固定为旧值以尝试断点续跑：

```json
"run_id": "20260825-153357"
```

使用前必须确认对应 SQLite 仍存在。权重、服务配置、生成参数或任务模板变化后不要复用旧响应。

## 多服务 / 多 shard 并行评测

先做预检：

```bash
python3 llmrun_parallel.py <case-parallel-config.json> --preflight-only
```

后台启动：

```bash
nohup python3 llmrun_parallel.py <case-parallel-config.json> \
  > gpqa_parallel_launcher.log 2>&1 &
```

主要配置：

```json
{
  "api_list": "model-a:http://host-a:8010/v1/chat/completions,model-b:http://host-b:8010/v1/chat/completions",
  "data_parallel_size": 2,
  "shards": [0, 1],
  "num_concurrent": 32
}
```

- `api_list`：逗号分隔的 `模型名:URL`；顺序与本次启动的 shard 顺序对应。
- `data_parallel_size`：完整评测的总 shard 数。
- `shards`：本次实际执行的 shard ID。
- `num_concurrent`：每个 shard 的并发数；总请求并发约为运行中的 shard 数乘以该值。
- `merge_only`：不再发请求，只合并已经存在的 shard 结果。

只有全部 shard 都执行完成时，脚本才会自动调用 `lm_eval --merge_results` 并校验全量样本数；部分 shard 运行结束后需等其余 shard 完成，再用 `merge_only` 合并。

并行输出目录与单服务模式不同，不包含 `run_id` 层级：

```text
<output_root>/<eval_model>/<task>/
├── effective_config.json
├── lm_eval_shard-0.log
├── lm_eval_shard-1.log
├── shard-0/progress_score.log
├── shard-1/progress_score.log
├── merge.log
└── results_*.json
```

并行响应缓存仍按 `run_id` 隔离：

```text
<cache_root>/<eval_model>/<run_id>/shard-<N>/responses.sqlite_rank0.db
```

### 查看各 shard 的中间得分

```bash
watch -n 30 '
for f in outputs/*/gpqa_diamond_generative_cot/shard-*/progress_score.log; do
    echo "===== $f ====="
    tail -n 1 "$f"
done
'
```

当前版本输出的是每个 shard 的独立阶段得分，不会实时打印跨 shard 汇总分。全局阶段正确率应按样本数加权：

```text
全局阶段正确率 = 所有 shard 的 strict 正确数之和 / 所有 shard 的 matched 数之和
```

当 `data_parallel_size=1`、`shards=[0]` 时，单个 shard 的阶段得分就是当前全局阶段得分。

并行输出目录没有 `run_id` 层级。同一个 `eval_model` 和 task 重复运行时应先确认旧结果不会与新结果混淆，或者为新一轮使用新的 `eval_model` 标签。

## 服务等待、超时和重试

当前配置：

```json
{
  "wait_for_service": true,
  "service_poll_interval": 1800,
  "service_wait_timeout": 0,
  "timeout": 7200,
  "api_max_retries": 3,
  "eval_max_retries": 1,
  "allow_timeouts": true
}
```

含义：

- runner 启动后先访问 `/v1/models`。
- 服务未就绪时每 1800 秒（半小时）探测一次。
- `service_wait_timeout=0` 表示不设置总等待上限。
- 单个 API 请求允许等待 7200 秒。
- API 层最多重试 3 次。
- 整个任务失败后 runner 最多重试 1 次，并复用本轮已成功的 SQLite 缓存。
- 最终结果中允许存在超时样本，但日志会明确报告超时数量。

## 常用排查命令

查看评测进程：

```bash
ps -ef | grep -E '[l]lmrun|[l]m_eval|[s]core_progress'
```

查看最新阶段得分：

```bash
find outputs -name progress_score.log -type f -print0 \
  | xargs -0 ls -t | head
```

查看最终样本文件：

```bash
find outputs -name 'samples_*.jsonl' -type f
```

查看最终结果文件：

```bash
find outputs -name 'results_*.json' -type f
```

查看容器本地响应缓存：

```bash
find /tmp/lm_eval_cache -name 'responses.sqlite_rank0.db' -type f -ls
```

## 注意事项

1. 修改权重、服务启动参数、生成参数或任务模板后，应使用新的 `run_id`，不要混用旧响应。
2. `allow_timeouts=true` 只表示接受含超时的结果，不代表超时请求会被判为正确。
3. 阶段得分用于发现明显异常；最终报告以完整评测生成的 `results_*.json` 为准。
4. `score_progress.py` 当前只支持 `gpqa_diamond_generative_cot`。
5. 离线模式下，如果容器中没有 GPQA 数据集缓存，预检会直接失败。
6. 不建议把 SQLite 响应缓存放在 NFS 上；当前脚本有意将它保存在容器本地 `/tmp`，避免网络文件系统锁和性能问题。
