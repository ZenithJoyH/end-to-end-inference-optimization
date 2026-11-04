# 点53：当前公共生产路径P1K稳态三阶段基线

状态（15:35，只读终态）：三阶段各8预热+3测量全部完成，33轮原生复验通过、所有约定测量指标波动≤5%，保留为`529cd814…`源码的入口基线，无ABR或收益结论。当前服务同实例health200/空闲，但Plugin磁盘内容已变为`4745048d…`，当前源码绑定incomplete，未自动覆盖、重启、回归或新实验；监控已删除。不改MBT32768、maxseq64、TP16/BF16、FULL_DECODE_ONLY、关闭前缀缓存及原启动脚本，不加临时MM/观测hook。

## 绑定修复与唯一启动

14:25:18准备全过、零生成请求：从原生run-record签发原始schema3 gate，再签发显式缓存更新schema5回执并用原生`check_gate`复验。分数仍为173/198，阈值86%，原始results/samples/契约/manifest未改；生产DB未清/复制/回退/手工改策略。新source gate SHA`bffa53cc…`、当前gate SHA`c2e08cef…`、当前manifest SHA`814b0ef0…`，完整SHA在state。旧14:07绑定incomplete是修复前历史，不再作为当前阻塞。

工具包SHA`da61f711…`，新accuracy bundle `804b60f9…`、performance bundle `872b65dd…`均经原生inspect/选择校验。控制器先保存至点51根`commands/point53-control-v1.py`（SHA`b712dbfb189e909247bf63ce66258653b9aec8e890f665ac8b2eec5408987f64`）；freeze SHA`a47a380c…`，三份原生dry-run均为8预热+3测量，CLI逐项核对后，14:28:17唯一派发PID2645381/start536630686。`glm-p1k`每30min只读跟进，不变安静、终态审计后删除，不重复派发或运行旧任务。

性能快照在原accuracy manifest基础上另存新增`cache_preparation`说明，未改原manifest，也不把新说明伪装成原精度字段；模型稳定身份已单独check相同。每阶段另做当前运行快照与缓存更新回执，计划与实际新快照命令均先dry-run；保留各阶段DB前后SHA，不把缓存热度差异藏成源码收益。

14:32:24只读确认：原生客户端版本/能力/源码探针已保存，Prefill第一预热轮的raw/output/validation已落盘，第二预热轮实际`vllm bench serve`进程在执行，health200，无终态failure。尚无测量轮/稳态聚合；不以首轮时间选择优化方向，也不把“已派发”当作测试已完成。额外11项精度provenance测试通过，本地GLM结构化绑定/唯一派发/冻约断言及diff whitespace检查通过。

## 方向与证据

点52已经验证实际默认flagos生产C64及完整最小模型回归，原生单次198题/C64为173/198＝87.3737%≥86%。当前唯一缺口是把可变调参DB SHA当作稳定代码身份。缓存表只读检查为1299张（686配置、613 benchmark），全部有num_warps/num_stages；实际写入实现为put_config/put_benchmark提交。原开始DB没有保存字节副本，不能补造逐行差分或全写入者证明。

绑定采用显式schema5 cache-update，保留原始198题/manifest/分数和DB前后SHA，只容许同实例、同DB URL/策略的内容更新；代码、模型、环境、设备、argv仍逐项核对。默认旧gate检查不放宽，不覆盖或篡改旧证据，不重跑GPQA。公共工具增加5项缓存绑定测试，原19项acceptance、31项性能比较、26项性能计划测试通过；后者单独运行需在测试进程增加同级模块搜索路径，不影响模型PYTHONPATH。

## 工作负载与停止条件

显式调用`inference-performance-evaluation: baseline`，当前正式目标`p1024-d1024-c64-n128`，本点建立scenario-entry而非未优化anchor。保留点52公共模型、SQL、H4和物理索引融合修复，历史版本收益不改绑。

| 阶段 | P/D/C/N | 含义 |
| --- | --- | --- |
| Prefill | 1024/1/64/64 | TTFT、输入近似总token吞吐代理；仍有调度、网络及首token成本 |
| Decode | 1024/1024/64/64 | TPOT/ITL及输出吞吐代理；仍有Prefill与批次填排成本 |
| Mixed | 1024/1024/64/128 | 原P1K目标workload，覆盖两波请求；本轮仅入口基线，不冒充ABR或最终验收 |

每阶段8预热+3测量，末3预热吞吐极差/中位数≤5%才准入。保留全部3测量轮，极差≤5%；慢首轮不删除。单轮1800s，规划总预算14400s，预算不足不启动下一个阶段。数值/模型/证据错误即停止；仅原生预热不稳定且服务健康空闲时，可保留incomplete并继续其余事先声明阶段。不盲重试、不改变阈值或清DB。生产服务不重启。

计划、比较阈值和dry-run在请求前保存。后续候选需同配置baseline/candidate/revert：吞吐至少+3%、各P99守护退化≤5%、测量波动≤5%、回退漂移≤3%，本轮本身不产生任何收益结论。P4K/P16K/P32K及长稳未测。

## 规划复盘planning53

MM06冷shape不一致不能归因收益；MM07固定shape确认冷搜索机制但C64仍索引转换OOM；点52只修内存且生产回归/原生分数达标。当前累计稳态收益未知。优先补三阶段入口基线，再对低开销指标无法解释的阶段采profiling，最后选择一个实际命中、净收益可证伪的主机/算子候选。不继续围绕MBT，也不直接重用旧点41/42调度器或冷MM限4策略。

终态按规划复盘技能更新：三阶段入口基线缺口已补齐，但客户端指标仍不能分离主机、设备和通信。先确认15:32外部源码编辑的归属及后续版本选择，再验证当前版本身份/正确性；不推定旧进程内存已经执行磁盘新代码。后续只列两个有条件方向，未启动：

1. 框架：取代表性Decode与父Mixed trace，先证伪逐token主机重复工作/graph launch空隙；当前约53ms的TPOT只是端到端代理，不是已证实的主机热点。若占比小则停止，不重用已无收益的合批器。必要时仅改Plugin扩展点，不改vLLM，保护worker生命周期与FULL replay。
2. 算子：只有当前trace确认Sparse MLA/索引转换或small-head链路确为关键路径后，再按真实shape/dtype/layout做现有实现替换或局部融合。先设备数值/动态graph与准确命中，再同配置Mixed A/B/R；不以索引内存下降或冷MM搜索收益代替稳态收益。

上述方向均需当前版本最小回归/适用精度触发、独立性能契约。未来Mixed吞吐≥3%、P99守护≤5%、spread≤5%、回退漂移≤3%不变；无实测净收益立即保留负结果并回退精确自有补丁。当前monitor只记录方向，不安装、profile或派发新测试。

## 当前效果与外部证据

15:28发现控制器已于15:14:14写入三阶段complete，原failure不存在。终态审计命令先保存为本点`commands/final-readonly-audit-v1.py`，SHA`2192412c9d960026525f8298e5269c1bedef760553bba600af97ecc77bd847c3`：只读重验全部33轮原生数据与当前稳定身份/health/空闲、唯一安装和镜像挂载，零生成、不调用控制器；结果另存`final-readonly-audit-v1.json`。未核验完成前不以completion代替当前身份审计。

v1在sources断言停止、尚未写出audit；原始文件和失败保留。只读细查发现：Plugin内容在入口与Mixed结束快照均为`529cd814…`，当前为`4745048d…`，不只是Git HEAD/index展示变化。三个近期文件mtime为15:32:02（晚于15:14终态）：`tests/unit_tests/glm5/test_mla.py`及vendor/thead的`register_ops.py`、`thead.py`。不推定改动者或仅凭mtime证明完整差分；不覆盖/回退外部编辑，不重启服务，不把旧gate绑定到新源码。证据恢复v2先保存`commands/final-readonly-audit-v2.py`、SHA`207d17915ad5f23cff2910ab094c6cf090d02061c136957275cbf4afec1d64c2`，只重验旧结果并明确记录当前身份漂移为incomplete，不放宽门槛或发送模型请求。15:35:19完成审计，`final-readonly-audit-v2.json` SHA`67e0ee304d988bf976a32da48fce0422048e7662a0a60a283bc07e50bd483df4`；状态`incomplete_current_source_drift`。其他源、argv/env、权重/tokenizer/thead、实例、镜像/挂载/网络、启动脚本未变，Plugin/FGV各一份editable安装，health200、running/waiting为0，控制器已退出；不把此变化误报成DB或原生分数失败。终态已如实审计并删除`glm-p1k`，不盲目恢复。

15:14:14控制器完成全部三阶段，15:35只读复验：维护版`check_run`核对全部33轮原始文件/命令/客户端/请求与输出/原生指标，未丢轮，无失败请求；9测量轮768个请求、含预热2816个请求均成功。末3预热吞吐与所有要求的测量指标均符合5%稳定性门槛。

| 阶段 | 主要吞吐三测量轮 token/s | 中位数 token/s | 吞吐极差/中位数 | 末3预热吞吐极差/中位数 |
| --- | --- | ---: | ---: | ---: |
| Prefill（总token近似输入吞吐） | 12331.812499 / 12199.211624 / 12339.034182 | 12331.812499 | 1.1338% | 0.0927% |
| Decode（输出吞吐） | 1172.118765 / 1152.625754 / 1155.959926 | 1155.959926 | 1.6863% | 1.5296% |
| Mixed（输出吞吐） | 1161.002109 / 1152.846368 / 1146.788598 | 1152.846368 | 1.2329% | 1.3743% |

Prefill各轮P99 TTFT的中位数5311.001ms、轮间极差1.1545%；Decode各轮P99 TTFT/TPOT/ITL的中位数分别5349.171/53.315/51.726ms，轮间极差0.8785%/1.8159%/1.9196%。这是三轮指标的中位数，不是合并所有请求后的P99，也不是纯设备阶段时间。仅入口基线，没有candidate/revert，不能证明端到端收益、回退漂移改善或长期稳定。

Mixed各轮P99 TTFT/TPOT/ITL的中位数分别5404.482/54.058/51.954ms，轮间极差2.0681%/1.6010%/0.8183%；P99 E2EL中位数57272.905ms、极差1.2880%。这证明本次已测轮满足稳定性准入，不证明跨实例漂移或正式三臂已通过，也不能与不同N的Decode直接计算优化收益。

原生run-record相对本点远端根分别为`performance/prefill-entry-01/run-record.json`（SHA`8aab4108…`）、`performance/decode-entry-01/run-record.json`（SHA`4e2f5a59…`）与`performance/mixed-entry-01/run-record.json`（SHA`d64366aa…`）。各轮完整数值、SHA及DB前后指纹写在state的`partial_results`，原生audit保存全部指标。DB正常写入605719d9…→6fa3eaef…→2ef62ddb…→bf1fc9d7…，终态与当前DB相同，未清理或回退。原评测源码精度仍173/198原生达标，当前磁盘新源码另待验证，不能复用原gate晋级。

远端唯一根：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261022-point53-steady-p1k`。原始GPQA仍在点52的`production-no-mm-02/formal-gpqa-01`，不复制或重写原样本。无提交推送、vLLM/权重变更或非PPU扩展。
