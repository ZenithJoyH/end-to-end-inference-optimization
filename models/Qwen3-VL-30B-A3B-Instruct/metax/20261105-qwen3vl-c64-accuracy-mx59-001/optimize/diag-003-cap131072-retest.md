# diag-003: 8条触顶题131072输出预算补测

用户2026-11-05要求提高生成上限并重测本次触顶题，明确选择**131072 token**。此授权取代上一步对这8条“不重跑”的限制，不扩大为全量GPQA/ERQA/性能或其他题。原126/198=63.64成绩、原始回答和诊断保留。

固定doc_id（从0起）：7,28,66,68,79,115,127,187，包含原判对7/68和原判错其余6条。原实际完成数证明全部8条各65536；只将它们的原实际上游body中max_completion_tokens65536->131072，其他键值逐项精确相同，无sampling/seed覆盖。当前model max_model_len262144已足够，不改服务参数。

模式inference-accuracy-evaluation/minimal-regression，限定request/output-health困难样本，非新完整正式精度或gate。不新增数学实现/observer/graph改动，无额外smoke，不把旧graph证据称为新观察；同服务已通过当前startup及normal smoke/C8且需CPU复核当前身份。

mx-59/qwen3vl用户opt17/8030/GPU0,1/TP2/BF16/prefixON/T.7P.8K20rep1保持。只创建已批准父case下新gpqa-cap131072目录，独立控制器保存请求、完整原始HTTP响应（含finish_reason/usage）、评分和源保留回执。客户端上限64，只有8个任务，实际最多8并发；每题一次、0retry/补位/额外GPU请求。启动前检查空闲，最多等待30min；每HTTP6h，预计控制器预算8h。新完整response只留远端，不放本地模型记录。

使用原官方CPU evaluator的RegexFilter/MultiChoiceRegexFilter/exact_match_fn，单列8题新旧结果、结束原因、token数及触顶情况；不拼接原198成绩、不签gate。重生成不是旧输出续写，现有warmcache、noseed及仅8题批轨迹不同，不能把变化全部归因为cap。任何评分工具问题仅CPU复核已保存响应，禁止重发模型。finally仅核验源保留，不停止/重启用户模型；source变化/请求异常保留证据并记incomplete。

远端：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072`。最新状态：8题补测、原规则评分及独立审计均完成，strict4/8，监控已删除。沿用用户每30min跟进偏好，补测终态及独立审计后删除新监控，不重启旧监控。

## 执行前归档
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/commands/controller.py` SHA256 `020400d7c2c0f4ca662b7a3a1dc53529137963aa85e10a38919b25492c0fad25`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/commands/start.py` SHA256 `c995dabbc97c259ed13cfad9386ce3c2d861bd34731647c9858dd6a54a82a793`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/commands/prepare.py` SHA256 `b9405d4ea7fcf73ea099b0a977f88de2ccf32e2389f74b6b76d7d714666ba188`
- `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/commands/score.py` SHA256 `f1ab906d3e95fc5caf0359d62e7f21e3af58587b8aa5d95091de331f8b3c9522`

本地上传脚本首轮发生临时UTF8解析报错（执行前、0模型请求/0远端变更）；原字节UTF8与compile重验通过后，用项目Python完成唯一上传。新监控qwen3vl-opt17-131k已创建，每30min；旧qwen3vl-opt17-c64监控仍删除。

22:20:31北京时间，唯一控制器417945/ticks682798781并发提交全部8条请求。22:21已有3份HTTP200，doc127/66/79分别生成553/953/1676 token，结束原因均为stop。服务指标5在运行、0等待。监控读取logs/events.jsonl和results/scored.json、completed.json、source-preserved.json，响应计数按唯一doc_id，避免将原始API文件和响应回执重复计算。

22:48定时只读检查：控制器417945/ticks682798781继续运行，8条均只发送一次、无请求错误。6份HTTP200已返回，全部finish_reason=stop，token数553/953/1676/5310/8943/12176。doc28与187仍生成，模型2running/0waiting、models200，尚无8题最终评分；继续等待既有请求。

23:06全部8题结束，strict4/8；doc28/187各131072且finish_reason=length，其余6条stop。控制器退出，源保留回执通过。执行前归档CPU独立审计commands/independent_audit.py SHA256 `3bb4a850f555007a2a4c46318e55f4ec5ab75363f5f957ee18e1b31680b0b2ab`，仅复核已有8份响应和当前服务，不重发模型。

## 最终逐题结果

2026-11-05 23:06全部8份HTTP200返回，23:22独立CPU复核完成。严格规则判对4/8，原相同8题为2/8；本次改为正确的是doc66和127。

| doc_id | 原65536严格判分 | 新严格提取 | 标准答案 | 新判分 | 新生成token数 | finish_reason |
|---|---|---|---|---|---:|---|
| 7 | 对 | A | (A) | 对 | 5310 | stop |
| 28 | 错 | [invalid] | (D) | 错 | 131072 | length |
| 66 | 错 | D | (D) | 对 | 953 | stop |
| 68 | 对 | D | (D) | 对 | 8943 | stop |
| 79 | 错 | A | (D) | 错 | 1676 | stop |
| 115 | 错 | C | (B) | 错 | 12176 | stop |
| 127 | 错 | A | (A) | 对 | 553 | stop |
| 187 | 错 | [invalid] | (A) | 错 | 131072 | length |

6条正常stop；doc28、187均为131072且length，严格提取均invalid。原判对7/68保持正确；79/115本轮正常stop但选项错误。所有原始HTTP字节、JSON响应和finish_reason/usage均在本子目录responses，未覆盖旧样本。

独立复核passed，8个原请求body唯一差异为max_completion_tokens65536->131072，恰好8个请求/8响应，无retry或补发。原RegexFilter/MultiChoiceRegexFilter/exact_match_fn重新核对同8回答，分数完全一致；原正式126/198=63.6363636364、ERQA175/400及旧回执SHA保持。未产生新正式gate或拼接198分数。

本次为仅8题、现有warmcache且无requestseed的重新生成，doc66/127本次不足1000token便stop，说明新旧生成轨迹发生变化；不能将2题改善全部归因于输出cap。该选样补测未提供全量198的新成绩，GPQA正式低分问题仍保留。

控制器417945/ticks682798781已退出，补测before/after/final及独立current的用户API346908/ticks681351047、源码、argv/env、模型/tokenizer/配置精确一致，models200。用户服务持续运行，0stop/restart/改码/改配置；独立审计0新模型请求。监控qwen3vl-opt17-131k已成功删除，无待跑任务。

## 证据
- scored：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/results/scored.json` SHA256 `f33cc54d2a8fed1bcc86b5f2dcb3b06ed3404d182cd09ab63f98f468bfc06d9e`
- completed：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/results/completed.json` SHA256 `de644969446cdee17739e0efcac67ee04bb2d8bdab32fc322c9b785566638502`
- source-preserved：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/results/source-preserved.json` SHA256 `2a7abba8ad1291c6dc2a82e73b7db773fba3dc8eddd8b2ffa6f55cf256fd5554`
- 独立审计：`/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/gpqa-cap131072/results/independent-audit.json` SHA256 `8865a4fc8b2a872b9496a78bd0eeb9ee005e2bed87fd3d941f412de79b6c0357`
