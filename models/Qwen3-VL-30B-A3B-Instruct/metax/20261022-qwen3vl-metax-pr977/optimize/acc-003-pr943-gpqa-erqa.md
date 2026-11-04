# acc-003 最新 PR943 的 GPQA 与 ERQA 全量精度

2026-10-22，两项全量评测及证据核验完成。**GPQA未达到64分阈值，ERQA达到40分阈值；当前组合精度验收失败。**

| 数据集 | 正确/题数 | 分数（满分100） | 阈值 | 结果 |
|---|---:|---:|---:|---|
| GPQA Diamond | 123/198 | 62.12 | 64 | failed |
| ERQA | 164/400 | 41.00 | 40 | passed |

## 本轮服务身份与范围

用户选择最新PR #943独立环境并要求开启prefix cache。mx-59，MetaX C550 GPU0/1，容器`qwen3vl-pr977-20261022`，TP2/BF16，端口18977，API模型名沿用`qwen3vl-pr977`；实例`qwen3vl-pr977-20261022:59760:559157267`。启动参数和运行日志均确认`enable_prefix_caching=True`；其余配置保留。结束时服务仍运行。9999原生产服务及其源码未修改，也未回写生产容器。

实际运行副本`/workspace/FlagGems-vllm-pr943-runtime`基于上游`bad340d`，包含最新PR943提交`316f036`的两文件变更及四个原采样兼容覆盖文件。实际MoE文件SHA为`749e81cfdbb4032aaa23648c53f32e3486d1e93c5aa03e41f2cb59d27f77b9e9`，与发布PR一致；运行树的git HEAD不是已提交316f036，不能仅以HEAD代表实际代码。gems-opt `c3c5f5ab`、Plugin `08da21cb`、vLLM `ee0da84a`与采样逻辑保留。版本、dirty内容、模型/tokenizer及实际源码指纹都已记录。

模式formal-gate，覆盖`pr-002-refresh943-upstream977`与本次组合，不把此前生产环境65.66/40.50分复用于新版本。独立容器镜像谱系与相同挂载重新核验通过。两worker实际FlagOS MoE路径、M64 GEMM1/GEMM2 stage3/1已核验；capture和每worker至少16次replay、11个HTTP请求（含C8）通过。

## 方法和有效性

GPQA使用规定镜像`harbor.baai.ac.cn/flageval/flageval-llmeval:v1`，SHA校验原始runner，完整任务`gpqa_diamond_generative_cot`、limit0、198题，主指标`exact_match,strict-match`。运行前两次provenance一致，冻结阈值0.64和题号后通过preflight。temperature0.7/top_p0.8/top_k20，原生18000生成预算，并发32，CLI/task seed42；后续diag-004核验原生API后端默认逐请求seed1234，已撤回早期未固定APIseed的假设。新UUID响应缓存不复用旧答案。原生逐题exact_match求和123，与聚合62.1212分一致；198唯一题号及全部filter、任务/配置/题目来源均已核验。empty/timeouts为0（诊断观察）。正式wrapper因低于冻结阈值退出1，未生成通过gate。

ERQA使用`flageval/mm-eval:v0.3.8`原生FlagEvalMM任务/API适配器/评分器，完整400题、630图片；并发8、num_infers1、temperature0.7、max_tokens18000，不使用try-run或响应缓存。原生payload不显式发送top_p/top_k，继承已验证服务默认0.8/20。400条原始答案、400条evaluated及最终accuracy41.00一致；唯一ID集合与冻结题集一致。数据、630图片和评测源码前后SHA检查通过，GPQA后及ERQA后的模型、tokenizer、源码和服务实例一致。健康观察未作为分数之外的门槛。

## GPQA失败诊断与结论边界

已调用本地精度诊断Skill，issue `diag-acc003-gpqa`。这是有效的冻结分数失败，根因尚未隔离，不是样本不完整或拿错指标。与上午生产环境全量结果只读对比：198个doc和原生请求arguments完全相同；109题两轮均对、21题由对变错、14题由错变对、54题两轮均错，原始回答相同6题。engine/Plugin/FlagGems源码指纹一致，FlagGems-vllm源码和GPU对不同；后续diag-004确认API默认seed1234，早期“未固定服务端逐请求seed”的假设已撤回。原比较缺少同卡重复受控A/B，不能将这7题净差异直接归因MoE。

不降低阈值、不换filter、不筛题、不重跑挑分，也未叠加性能优化。进一步晋级需要定位问题，实际修复后完成最小/graph回归并按原契约重新全量评测。本次请求的两数据集测量已完成，不代表当前组合正式精度通过。

## 控制过程保留

原流水线在GPQA无通过gate时停止，原失败回执保留；继续执行用户请求的ERQA仅补齐精度证据，不代表晋级。第一次只读证据审计漏设offline变量，导致联网等待；只停止精确匹配的本轮CPU审计PID，v2加入离线设置后核验通过。未重复GPQA模型推理，未改原生答案/指标/阈值。辅助progress parser的122题不是正式分数，主结果按原生strict-match123题记录。控制命令、SHA及修复回执均保存在本轮远端目录。

## 外部产物与监控

远端根目录`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy`。完整问答、图片、日志与原生结果留在远端；本地仅记录摘要、必要SHA及链接。

- `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/results.json`，SHA `3931fed67330d385c75ff66e3732fe3a2743bd6276222afa6c89d6d499d048c4`。
- `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/suite-completed.json`，SHA `2357451a608f113a8b0e93a84785ab055c65475f253dd94692829918ee896fbb`。
- `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/gpqa/failed-evaluation.json`，SHA `32fc07b8cdb4eb89e3f38047ab11e266c9f9ac494e6d1733010e33100befbb80`。
- `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/gpqa/comparison-old-current.json`，SHA `d97e596eb30fdc910d2897ce1501ffcfd0c4d35cab2da37f4b00d0d914911cbb`。
- `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/manifests/service.json`，SHA `252be23b96a999682a3c6a74094a95f396ea17a53a8f3fe45d08b8336d5f06b3`。
- `/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/graph/minimal-regression.json`，SHA `e595524fd6fd74c27323bcce2292406b308d05c95da3e27c1fefb446bef30aba`。
- 最终证据：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-pr943-accuracy/final-evidence.json`，SHA `468b50b1608837459c2122f3f2961a5eacc21873ec149843e2a31059121453dc`。

评测Skill bundle SHA `804b60f96089a5f37ee76d40c1ba11405ed8e61b45940786b52e52ed7b91edfb`，运行前归档；诊断bundle另见state。监控`qwen3-vl-gpqa-erqa`（30分钟、有意义变化才通知）在两项终态校验后已暂停，automation_update回执PAUSED。没有新端到端性能结果；正式性能不得借用本次失败GPQA签发的不存在gate。

后续[diag-004](diag-004-gpqa-controlled.md)纠正seed假设：原生API后端默认发送seed1234，因此此前“API未固定逐请求seed”的表述不准确；CLI42与API1234分属两层。原始123/198、164/400及其证据不变，不能再据此把下降直接解释为未设置seed。后续实测动态batch、同seed复现及同卡版本对照。

后续同卡受控对照已完成，详见[diag-004](diag-004-gpqa-controlled.md)：旧125/124、新128/125，新版均值高1.01个百分点，未复现稳定版本退化；同seed的版本内并发回答仍有变化。原123/198失败不变，根因具体算子尚未隔离，无新gate。

后续[diag-005固定前缀定位](diag-005-fixed-prefix-logits.md)已将独立运行副本同步PR943 a1570df，并在完整Q/K/V相同、同实例探针中性及忠实重放下定位首层MACA native kvcache自动路径的batch数值差异；组件固定split1消除差异，服务未应用该参数，其他配置及9999未动。原正式GPQA失败不覆盖，无新score/gate/E2E。
