# 性能工具

端到端优化任务由 [推理性能评测技能](../../skills/inference-performance-evaluation/SKILL.md) 选择 baseline、targeted、checkpoint 或 formal 无 profiler 测量，由 [推理 Profiling 技能](../../skills/inference-profiling/SKILL.md) 选择 capture、analyze 或 reprofile 诊断；本目录仍是实际命令、能力边界和工具语义的唯一维护位置。

| 工具 | 用途与范围 |
|---|---|
| `vllm_perf.py` | 参数化 vLLM 多轮诊断；提供绑定 gate 与当前身份后可用于正式候选测量 |
| `performance_plan.py` | 配置校验、命令生成、客户端能力预检及逐轮冻结证据，由 vllm_perf.py 调用 |
| `compare_performance.py` | 重验 baseline/candidate/revert 的原始证据，按预冻结阈值输出 passed/failed/incomplete |
| `vllm_profile.py` / `sglang_profile.py` | 共享诊断编排、逐轮原生结果检查及新增 trace 检查，仅用于归因 |
| `sglang_perf.py` | 参数化 SGLang 诊断，检查原生详细 JSONL；不自动签发正式验收 |
| `all_perf.py` | 历史矩阵与文本报告入口，显式指定目标，复用公共 vLLM 原生结果检查 |
| `trace_to_summary.py` | 分开统计主机、设备和未分类活动的累计时长 |

原始 `test/perf_test/` 保持导入基准；此目录的维护版修复了失败传播：非零退出、缺少成功计数、失败请求或不完整轮次不能成为成功汇总。预热失败也使整组失败；保留逐轮信息，缺轮不取剩余轮的均值，任何 case 失败整体非零退出。

## 性能服务启动门禁

所有新建 vLLM 性能基线以及对应 candidate/revert 服务，都在其余参数冻结后显式追加：

```bash
vllm serve <model> <其余冻结参数> \
  --no-enable-prefix-caching
```

该参数关闭 prefix caching；性能服务不要求增加 `--no-enable-log-requests`。执行前用目标版本 CLI 帮助确认 prefix cache 参数受支持，执行后保存完整进程参数及服务日志或等价 runtime 证据。service manifest 应填写 `launch_config.enable_prefix_caching=false`、`performance_context.prefix_cache_state=disabled`，并在 `cache_preparation` 说明验证方式；缺少实际状态证据时，比较保持 incomplete。

只有用户明确要求评估 prefix cache 时，才允许在单独契约中改变该状态，并把缓存准备、前缀复用比例和命中证据列为受控变量。不得把开启缓存的结果与默认关闭缓存的结果归因为其他代码或算子优化。历史产物维持原记录，不按本门禁改写。

执行计划在 dry-run/发送请求前检查默认关闭和配置一致性；比较器再次核验。
缓存实验需在冻结 comparison 中新增 `cache_experiment: {authorization, reuse_ratio, hit_evidence}`，
记录用户指令出处、0–1 前缀复用比例、命中证据路径，并在 `variable_paths` 显式声明实际变化的缓存状态、
准备方式和启动配置字段。缺失声明、启用状态与观测矛盾，均不产生有效比较。
服务身份必须记录 FlagGems-vllm 的实测安装状态与内容 SHA，规则见精度工具文档。

独立重复仍指不同服务实例；纯重启可以通过精度工具的显式 `rebind` 复用同一已评测候选的分数，
而不是复用旧实例的 gate。代码、配置、设备或环境变化不能走该分支。
比较器验证 schema4 rebind 时，要求 `run-record.input_artifacts.service` 的原始 manifest 仍可读取且 SHA 与测量快照一致，再用该原路径验证精确绑定；缺失或变更不能以相同内容副本绕过。测量快照、原始精度证据及 runtime/最小回归证据都继续做 SHA 校验。

## 配置执行与比较

新任务从 [plan.example.json](plan.example.json) 和 [comparison.example.json](comparison.example.json) 准备外部配置。`plan.example.json` 已包含当前 Agent 固定的四个正式目标场景：P1K/P4K/P16K/P32K、D1K、C64、N128，均为 finite batch；正式 full 计划不得删减。目标服务、tokenizer、预热、重复、超时、指标与阈值仍须按任务修改并冻结。若比较要求 SLO 达标率，必须在计划的 `measurement.slo` 填写对应的 `ttft/tpot/e2el` 毫秒阈值；空 SLO 不能产生 goodput 验收。

大模型不要求每轮执行同一份完整计划，也不要求先跑完所有场景基线。默认按 P1K→P4K→P16K→P32K 每次选取一个正式目标场景，完成该场景的 baseline、milestone、优化和 formal 后再切换下一项。milestone 可以使用更短输入/输出、更少请求/并发或更窄阶段；记录它映射的当前目标场景和 workload 差异，并使用自身同配置 baseline/candidate。milestone 达到预冻结的显著提升或出现热点迁移时，中间 formal 只运行当前目标场景，不运行其余三个。

当前目标场景在选择优化方向前分别维护 Prefill、Decode 和 Mixed 证据。计划中每个 case 可用可选 `stage` 标记诊断角色，缺省为 `mixed`；正式目标 case 必须为 `mixed`。单 token/短输出可作为 Prefill 侧探针，但不能要求 TPOT/ITL；长输出可突出 Decode，但仍要记录 Prefill 和调度残余成本。TTFT、TPOT、ITL 是客户端代理，不等于纯设备阶段时间。阶段专项必须有自己的同配置 baseline，并在保留候选前回到父目标 Mixed workload 检查另一阶段守护指标和端到端净收益。

如果 baseline 在实验前记录的诊断时间预算内仍未完成，可以停止该次客户端运行，将 run 及部分证据保留为 `incomplete/deferred-too-slow`。随后可以减少输入/输出长度、请求数或并发建立 milestone，并用本入口取得缩减 workload 的明确 baseline/candidate 数据；也可以选择静态分析或二者结合。缩减结果只支持该 milestone，候选达到晋级条件后仍须回到目标场景测量。没有完成的同配置 anchor 时，不输出精确加速比。

可以从场景目录分别生成 targeted、checkpoint 和 formal 计划：targeted 承载 milestone 和低成本哨兵，checkpoint 包含当前改动影响的场景，中间 formal 只包含当前一个正式目标场景，最终 formal 才包含固定四场景及额外业务场景。各计划使用稳定且可追溯的 case ID，保存配置和 SHA；任何缩减 workload 都建立自身同配置 baseline，不能复用其他计划汇总值。中间 formal 结果留在 `optimize/`，最终组合结果进入 `acceptance/`。

每次运行都提供当前 [service manifest](../accuracy/service-manifest.example.json)。自动比较额外核对其中的 `performance_context`：平台、设备身份、驱动/runtime、镜像与缓存准备。字段来自运行时取证，不靠把 unknown 改成字符串补造事实；scope 为诊断时执行器允许不完整身份，但比较器会将不足证据判为 incomplete。

先生成可审阅命令，不需要安装 vLLM，也不发送推理请求：

```bash
python3 evaluation/performance/vllm_perf.py \
  --config /external/plan.json \
  --comparison-contract /external/comparison.json \
  --service-manifest /external/baseline-service.json \
  --role baseline --run-id baseline-01 \
  --scope performance_only --output-dir /external/perf --dry-run
```

核对后去掉 `--dry-run` 执行。`performance_only` 仅用于已授权的纯性能研究；默认 scope 为 diagnostic。正式候选使用 `--role candidate --accuracy-gate /external/accuracy-gate.json`，不同时指定 performance_only；baseline/revert 分别保存身份，不能复用候选 gate。

执行器先验证客户端版本、所需 CLI 能力与可执行文件，再依次运行计划中的 case。每轮有超时预算；失败、缺失指标或预热不稳定立即停止并保存 failed 记录。输入与产物前后做 SHA 核验；新 run 目录已存在时拒绝覆盖。服务重启、源码切换与缓存清理仍按项目流程执行，本客户端不负责这些操作。

客户端身份还绑定实际 Python 入口/解释器、vLLM benchmark 和 CLI 的 Python 源文件，运行前后检查其内容，比较时重验保存的探针；同一版本号或 console script SHA 不足以证明 editable 安装未变化。当前支持直接 Python console script 和简单 `env python` shebang；shell wrapper 或不可读取源码的安装需先适配，不会跳过检查。虚拟环境入口保持原路径。此范围不等于全部第三方依赖的环境锁定；缺少这些证据的旧 run-record 不自动通过新比较。

客户端 capability 预检默认每项预算 30 秒。SDK/插件导入较慢时，计划入口可显式传入
`--client-probe-timeout 120`；预算记录在 client 证据中，仍执行解释器/源码绑定、版本和完整 CLI
能力检查。它只调整客户端启动预检，不改变 benchmark 轮次超时、服务配置或稳态准入。

`--output-dir/<run-id>/` 保留有效计划、服务/比较契约快照、客户端身份、原始结果和输出、逐轮 validation 及 `run-record.json`。原始大产物留在目标环境的外部路径，不加入项目。三个角色的每次独立进程运行都使用唯一 run-id。

收齐契约要求的运行后比较，例如每个角色各两个独立进程：

```bash
python3 evaluation/performance/compare_performance.py \
  --contract /external/comparison.json \
  --run-record /external/perf/baseline-01/run-record.json \
  --run-record /external/perf/baseline-02/run-record.json \
  --run-record /external/perf/candidate-01/run-record.json \
  --run-record /external/perf/candidate-02/run-record.json \
  --run-record /external/perf/revert-01/run-record.json \
  --run-record /external/perf/revert-02/run-record.json \
  --output /external/comparison-result.json
```

比较契约必须在测量时已通过 `--comparison-contract` 绑定；不能测完再改门槛。`variable_paths` 指向服务 manifest 中声明的主要变量，例如 `/flaggems_sha256` 或 `/launch_config/max_num_seqs`；缓存实验可显式声明 `/performance_context/prefix_cache_state` 及相应的 `/performance_context/cache_preparation`。设备、模型/权重、客户端、workload、生成与测量条件不能混入未声明变化；base_url 的地址变化仅允许作为服务定位差异，每次均与本次计划核对。

比较器重新核对原始 JSON、控制台输出、命令和 SHA，不只信 valid 标志或汇总表。重复引用同一轮产物、同一服务实例充当多个独立进程、缺轮、漂移超限和证据不足均为 incomplete。统计先取每进程的测量轮中位数，再取进程间中位数；保留所有轮和进程值，并检查两级波动以及 baseline/revert 漂移。这是预冻结的工程判断，不声称产生统计置信区间或总体请求 P99。

| 结果 / 退出码 | 含义 |
|---|---|
| `passed` / 0 | 所测 case 的主指标、守护指标及约定 SLO 通过，证据和重复完整 |
| `failed` / 1 | 可比较的完整证据表明收益或守护/SLO 门槛未通过 |
| `incomplete` / 2 | 缺少证据、配置/命令不匹配、重复不足、测量波动或回退漂移妨碍归因 |

`scope=formal` 还会重新消费每个候选实例的精度 gate，并要求显式预热稳定性检查。`performance_only` 的 passed 只表示性能研究契约通过，不代表正式精度、全业务或长期稳定性通过。JSON 输出不会覆盖已有文件。

## 计划支持的测量范围

- case 可分别指定输入/输出长度、请求数、并发、有限批次或有限请求的 open-loop 到达率与 burstiness，并用 `stage=prefill|decode|mixed` 保存分析角色；该字段是证据标签，不会让 runner 自动隔离设备阶段。多个 case 可构成有限速率扫描。
- 优化循环可以为不同场景使用独立计划。targeted/checkpoint/full 是实验契约中的结论层级，当前执行器通过实际计划中的 case 集合体现，不会自行判断遗漏场景；最终验收必须由执行者提供预冻结 full 计划并核对场景完整性。
- `warmup_rounds` 是固定预算。可选 `warmup_stability` 检查末尾窗口的 `(max-min)/median`；预算内未通过就停止。默认固定轮数不证明稳态，也不自动建立业务缓存冷热条件。
- 默认结论面向稳态：冷启动、服务首请求、首批次和预热轮不进入正式聚合，也不应主导优化方向。比较器会保留并检查所有正式测量轮的波动；不得在看到结果后删除较慢的首个测量轮。若首个测量轮仍显示过渡态，应将运行判为 `incomplete`，在新契约中增加预热或收紧稳态准入，并用同一规则重跑全部比较角色。只有显式的独立冷启动契约才能把这些启动成本作为主目标。
- `required_metrics` 明确本任务不可缺失的原生指标；支持 P50/P95/P99 等已列出的指标。单 token 输出不能要求 TPOT/ITL。`ignore_eos=false` 按每请求实际输出核对，不强行套固定输出总数。
- 非空 `measurement.slo` 原样传入原生 `--goodput`，采用同一请求同时满足全部 SLO 的结果，再核对 goodput 与时长/请求数。不会从 chunk ITL 猜测 TPOT/E2EL；口径依赖所记录的原生客户端版本。[vLLM 原生计算](https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/benchmarks/serve.py)
- 当前仅支持 random 长度受控 workload 与 `/v1/completions`。持续 closed-loop、业务 trace 重放、客户端待发队列计时、自动跨进程服务编排、cache 清理、资源监控与长稳尚不由此入口实现。open-loop 的并发上限可能降低实际发出速率；工具不会把有限扫描的 passed 宣称为持续容量达标。

## 历史入口与 wrapper 迁移

不提供 `--config` 时保留原维护版固定矩阵/三轮诊断入口：

```bash
python3 evaluation/performance/vllm_perf.py \
  --model MODEL --tokenizer /external/tokenizer \
  --host 127.0.0.1 --port 8000 --output-dir /external/perf
```

旧入口可继续使用精度 gate 做准入检查，但不生成新比较器要求的完整 run-record。需要自动比较时使用配置入口，不能把旧汇总表补字段冒充新证据。正式精度与服务取证流程见 [评测入口](../README.md)。

维护版 vLLM 使用固定随机长度（range ratio=0）、temperature=0、ignore_eos；`--seed` 默认 42，按 case/轮次派生不同种子，避免直接重复同一生成序列，但不证明前缀不重叠或缓存命中相同。每轮保存原生 JSON，并核验完整性与性能指标。该显式 workload 是 2026-09-06 的维护变更，旧默认结果不能直接混比，需重建同条件 baseline。

原生结果以两种明确结构校验：带显式 `failed` 的计数格式，以及 v0.11 的完整逐请求格式。后者必须以 `num_prompts/completed`、`errors/output_lens` 和控制台计数交叉验证，不把缺失 `failed` 当作零。必需的吞吐及 TTFT/TPOT/ITL mean/median/P99 从原生 JSON 读取，缺失、非有限或不完整轮次失败；诊断原因保存在逐轮 validation JSON。该多 token 矩阵不支持将单 token 输出的 TPOT/ITL 当成有效指标。新格式或平台 fork 仍需验证 CLI 和原生字段，当前本地 fixture 测试不等于全部客户端版本实测。

固定 workload、endpoint、EOS、采样、seed、轮数与缓存条件；候选、baseline、revert 使用同一客户端配置。每轮保留数据，报告稳态代表值和波动。profiling 与无 profiler 测量分开。完整 token 核验及业务代表性依然是正式验收要求，不能以脚本成功替代。

ShareGPT 原始文件没有迁入。需要真实数据时在目标环境显式配置，记录来源、revision 和 checksum。

XingChen 的历史模型 wrapper 已退出模型目录；其历史矩阵和结果语义保留在模型 `state.yml`、README 与案例文档中。新测试直接使用本目录公共计划入口并显式配置 workload、预热和重复，不能让历史 1 轮预热自动满足正式比较。性能研究和 dry-run 仍须提供 service manifest。

## Profiling 与 SGLang 诊断

两个 profiling 入口共用诊断流程，显式设置目标和 case；以下命令只预览配置，不发请求：

```bash
python3 evaluation/performance/vllm_profile.py \
  --model MODEL --tokenizer /external/tokenizer --host 127.0.0.1 --port 8000 \
  --case 1024,128,8,8 --runs 3 --warmup-rounds 1 \
  --profile-dir /external/server-traces --output-dir /external/profiling --dry-run

python3 evaluation/performance/sglang_perf.py \
  --model MODEL --tokenizer /external/tokenizer --host 127.0.0.1 --port 30000 \
  --output-dir /external/sglang --dry-run
```

SGLang profiling 将第一条命令的入口换为 `sglang_profile.py` 并设置实际端口。服务须事先配置 profiler；`--profile-dir` 指向执行客户端可见的实际 trace 目录，不推断远端映射。`--no-profile` 可省略此目录，只做诊断。`--case` 可重复，四个值依次为输入长度、输出长度、并发上限、请求数；`--profile-runs all|first|last` 只作用于非预热轮，`--timeout` 限制每轮客户端运行时间。

非零退出、超时、原生结果缺失或预热失败会保留失败证据并返回非零；profiling 与无 profiler 轮次分组汇总。请求采集但没有观察到新的或发生变化的非空有效 trace 时返回 `incomplete` / 2，不把旧文件或普通 benchmark JSON 当作采集成功。异步 trace 尚未导出时也保持 incomplete；新文件的时间窗口与 SHA 仅是采集证据，worker 覆盖、实际热点命中仍需检查 trace 内容。客户端超时后须检查目标服务的 profiler 状态，工具不会擅自重启服务。

vLLM profiling 默认 temperature=0；分析 temperature=1 的目标服务时显式传入
`--temperature 1`，避免诊断跳过实际采样路径。top-k/top-p 沿用目标服务的已核验默认值；
采样配置仍需写入诊断契约。

维护版 SGLang 使用固定随机长度、无限到达率和独立并发上限，分别保存每轮 JSONL、stdout/stderr 与 validation。原生 `request_rate=Infinity` 是该客户端的有限批次表示；决策指标仍须有限。接口按 [SGLang v0.5.11 源码](https://github.com/sgl-project/sglang/blob/v0.5.11/python/sglang/bench_serving.py)核对，区分 `--request-rate` 与 `--max-concurrency`，并使用其 `--output-details` 结果核验计数、长度和指标。此前 SGLang profiling 将并发作为到达率，旧性能脚本使用不同随机长度设置，不能与本次修复后的结果直接混比。当前未做 SGLang 真实服务集成验证。

`trace_to_summary.py` 按活动类别分组：CUDA runtime/driver 调用留在主机侧，不能因名称含 CUDA 或参数含 stream 就计入设备耗时。未知类别单列，需要时用 `--device-category` 显式补充经核实的平台类别。输出是可能重叠的活动时长之和，不是设备忙碌时间、关键路径时间或 CPU self time；缺失/非法 trace、空目录及目录中任一文件处理失败返回非零，已有摘要拒绝覆盖。

## 项目范围冻结与最终验收

原生比较器的 `passed` 只说明所绑定的比较契约通过。新项目验收另用 `final_acceptance.py`：
先在测量前冻结生命周期与基线身份，后对原生回执、阶段证据和目标目录一起重验。
旧记录不补写事后的范围 SHA，也不自动升级为最终通过。

先按任务修改比较模板的主指标、阈值、重复要求及变量；项目验收的主指标/守护项中必须
同时包含 TTFT 和 TPOT/ITL（例如 `p99_ttft_ms`、`p99_tpot_ms`）。然后准备契约：

```bash
.venv/bin/python evaluation/performance/final_acceptance.py prepare \
  --contract /external/comparison-draft.json \
  --baseline-service /external/anchor-service.json \
  --case-id case-001 --baseline-id anchor-001 \
  --lifecycle final-all-targets --baseline-kind anchor \
  --output /external/comparison-frozen.json
```

默认最终范围为 `p1024-d1024-c64-n128`、`p4096-d1024-c64-n128`、
`p16384-d1024-c64-n128`、`p32768-d1024-c64-n128`；允许显式追加业务场景，不能删减四项。
工具核验原始长度、并发、请求数和 finite-batch 模式；缩短后沿用原 ID 也不能通过。
中间验收改用 `--lifecycle intermediate-single-target --baseline-kind scenario-entry`
并指定一个 `--scenario-id`。所有测量通过 `--comparison-contract` 绑定准备好的新契约。
`prepare` 只准备文件，不判断基线来源真实与否；Agent 仍须核验该 manifest 来自未优化原路径
或相应场景入口，记录 baseline ID 的来源。工具随后保证 baseline/revert 与冻结身份一致。

收齐运行后，由 Agent（也可以人工）准备外部 `acceptance-manifest.json`，字段为：

- `schema_version: 1`。
- `contract`：测量前冻结的比较契约，格式 `{"path":"/绝对路径","sha256":"文件SHA256"}`。
- `run_records`：baseline/candidate/revert 所有独立运行的同格式引用列表。
- `phase_evidence`：以每个目标场景 ID 为键；每项包含 `prefill` 和 `decode`，例如以下单项。

```json
{
  "prefill": {
    "run_record": {"path": "/external/candidate-01/run-record.json", "sha256": "填写SHA256"},
    "case_id": "p1024-d1024-c64-n128",
    "method": "client-proxy",
    "residual_costs": "TTFT 含网络、排队和调度，不能解释为纯设备 Prefill 时间"
  },
  "decode": {
    "run_record": {"path": "/external/candidate-01/run-record.json", "sha256": "填写SHA256"},
    "case_id": "p1024-d1024-c64-n128",
    "method": "client-proxy",
    "residual_costs": "TPOT/ITL 含调度间隔及阶段干扰，不能解释为纯设备 Decode 时间"
  }
}
```

`client-proxy` 必须引用当前组合候选的同一 Mixed workload，并有相应 TTFT/TPOT/ITL 指标。
`isolated-probe` 可以引用同候选、同输入长度且 stage 对应的阶段探针，仍核验其全部原生
证据并说明残余成本；此引用只证明阶段观测有效，不独立证明阶段收益。阶段收益另需同配置
baseline/candidate 比较。最终净收益始终来自父目标 Mixed 的完整角色比较。

```bash
.venv/bin/python evaluation/performance/final_acceptance.py check \
  --manifest /external/acceptance-manifest.json \
  --output /external/project-acceptance.json
```

文件不覆盖；`passed` 返回 0，未通过返回 2，结果中的 `status` 区分 failed/incomplete。
只有 `status=passed` 且 `final_acceptance=true` 才表示最终四场景性能与绑定精度验收通过；
硬件不支持或缺轮时保留 incomplete。此结果不替代 PR readiness、交付/回退准备或长期稳定性验证。
人工发起的测量使用同一检查入口，不要求仅为更换操作者而重跑。

如果使用 agent journal，可在测量完成后建立只读验收步骤，`after` 使用
`{"kind":"acceptance","manifest":"/external/acceptance-manifest.json"}`；将已有 manifest
列入 `context_files`，scope 加入对应 `case_id`、`baseline_id`，保留正式精度前置检查。
验收 manifest 引用已存在的回执，不能在测量前伪造未来回执的 SHA。测量步骤本身仍冻结
原生 plan/contract/service 并使用 `performance` 后置检查。
