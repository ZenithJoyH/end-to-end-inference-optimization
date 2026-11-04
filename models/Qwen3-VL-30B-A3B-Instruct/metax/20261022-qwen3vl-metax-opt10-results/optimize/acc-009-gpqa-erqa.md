# acc-009 GPQA 与 ERQA 完整精度评测

2026-10-22，用户指定 GPQA 阈值64分、ERQA阈值40分，取代之前暂缓精度的指令。本轮完成两项全量评测：GPQA **130/198=65.66分**（阈值64），ERQA **162/400=40.50分**（阈值40），两项均通过。

| 评测 | 正确/总题数 | 分数（满分100） | 阈值 | 判定 |
|---|---:|---:|---:|---|
| GPQA Diamond | 130/198 | 65.66 | 64 | passed |
| ERQA | 162/400 | 40.50 | 40 | passed |

## 服务与覆盖范围

mx-59 / MetaX C550 / TP2 / GPU6,7，容器 `qwen3vl-p64k-opt-20261015`，端口9999，served model `qwen3vl-opt10`。服务实例 `qwen3vl-p64k-opt-20261015:1592858:557237509`；用户本次启动开启prefix cache，评测保持其配置，不复用之前关闭cache的性能实例身份。gems-opt、内联GEMM1/GEMM2 MoE、通用FlagGems采样适配及局部histogram均保留。本次未修改源码、采样、启动参数，也未重启服务。

模式 formal-gate，覆盖 acc-009 及当前组合整体；组合通过不证明每个优化点可独立通过。原服务graph capture完成，两项评测使用同一实例；GPQA后及ERQA后重新核对服务、模型、tokenizer及四仓库源码，均保持一致。容器镜像继承及现有目录映射校验记录于外部container-gates.json。

## 方法与证据校验

GPQA使用规定的 `harbor.baai.ac.cn/flageval/flageval-llmeval:v1`、SHA校验原始runner和正式wrapper；任务 `gpqa_diamond_generative_cot` 完整198题，主指标 `exact_match,strict-match`。运行前两次provenance一致并冻结契约、通过preflight。temperature0.7/top_p0.8/top_k20，原生预算18000，并发32。seed42属于CLI/task设置，不将其冒称为逐请求API seed。全量样本/唯一题号和正式gate已验证。

ERQA使用 `flageval/mm-eval:v0.3.8` 中原生FlagEvalMM任务、API适配器及accuracy评分器；完整400唯一题号、630张图片，逐文件SHA复核，无筛题、try-run或响应cache复用。并发8、num_infers1、temperature0.7、max_tokens18000；原生payload不显式发送top_p/top_k，沿用服务默认0.8/20。native原始答案、evaluated及result三者覆盖/分数一致；数据、图片、评测源码的运行后校验通过。输出健康观察仅作诊断，不增加分数之外的门禁。

GPQA于09:47–10:06（北京时间）完成；ERQA于10:07启动，终态UTC `2026-10-22T03:12:33.944071+00:00`。GPQA wrapper/gate和ERQA runner、最终证据校验均成功。

## 原始产物

全部原始回答、日志、契约和配置留在 `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy`，本地只保存摘要与索引：

- 汇总：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/results.json`，SHA `e77875aff907b077bb7f7699c31ae72e4010e5224615a9af70ab926c7a69b3bd`。
- GPQA gate：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/gpqa/accuracy-gate.json`，SHA `27366079435553c581a85ad5e037f75e5954680cc043d7c56a711c7f4ffcad6b`；run record见state.yml。
- ERQA原生结果：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/erqa/native-output/erqa/erqa_result.json`，SHA `1d59c5745efa2f44f1d6f12ca621e4ff7fc032a8980ae9949d2a55e941ac85cb`；原始/evaluated答案SHA见state.yml。
- 服务manifest：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/manifests/service.json`，SHA `b0c74968e52e2bcc689bf9d582011cccbb5661dec1035c7d4fe883a1531f5451`。
- 初始实际模型/tokenizer/源码事实：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/manifests/source-facts.json`，SHA `b3a933a26a0b63a21cf979ecb78eea0448903a41bf36f42e2da47df66065570e`。权重绑定使用config/index及实际分片文件清单，不冒称已对全部权重字节hash。
- 前后身份校验：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/gpqa/post-source-check.json` 与 `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/erqa/post-source-check.json`；均passed。
- 方法bundle记录：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/manifests/accuracy-skill-bundle.json`，SHA `30b6c2105d1609bacc9c404659adca6465796c8665d0aea61e4b4b4fe2908d93`；采集在ERQA运行期间、GPQA完成后，时间见accuracy-method-journal.json，不冒称运行前采集。

监控 `qwen3-vl-gpqa-erqa`（30分钟、无变化安静）已暂停；没有重复启动评测。

本次用户精度请求已完成。最终四场景同契约性能anchor/candidate/revert仍未完成，此结果不等同于整个优化项目正式验收。重启服务须重新绑定gate；源码、配置或设备变化须按精度流程重新评测。

附加汇总读取问题已解决：首次finalize.py用str.splitlines拆分了GPQA答案中合法的Unicode分隔字符；原正式gate始终校验通过。finalize-v2.py改为按文件物理行读取，SHA `963b56eda34a6f7128dcaaff1ed7e92212f19a0802031bd3619dca5a4f51dcae`，成功回执`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-opt10-accuracy/finalize-v2-receipt.json`，SHA `a53cfcb2a411253a8c96728082769efb932cf43b6ef2588345c0b05f17cb9033`。首次错误日志及退出码保留，未重复模型推理、未改原生答案/指标/阈值。
