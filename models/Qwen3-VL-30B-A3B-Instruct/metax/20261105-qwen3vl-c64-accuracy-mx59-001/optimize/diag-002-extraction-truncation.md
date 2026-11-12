# diag-002: GPQA提取和截断只读审计

用户2026-11-05明确要求只读审计本次GPQA是否实际答对但提取失败，或输出截断；不重跑、不改服务/配置。采用本地inference-accuracy-diagnosis，仅CPU复用现有原生198题、原RegexFilter/MultiChoiceRegexFilter/exact_match_fn；usage按已冻结实际上游payloadSHA逐题绑定。正式126/198成绩保留，不启监控、不发模型请求。

执行前脚本记录：`/tmp/qwen3vl-c64-accuracy-mx59-20261105/audit_extraction_readonly.py` SHA256 `35cdd15d461b43dd51f8aa10812df1d8a65ae7421a689b92151a48b1c528bd85`。脚本通过stdin在私有CPU评测器python -B执行，不写远端文件；输出只回收临时审计摘要。

当前完成初查：198个HTTP200的usage中8个completion_tokens=65536；原生样本/代理审计未存finish_reason，需区分“到达输出预算”与逐条length字段证据，继续检查最终答案和原提取结果。

## 最终结论

**未发现“最终明确选中标准正确选项、却被严格提取漏判”的条目。** 原始198条strict/flexible提取值和exact_match_fn判分均逐条重放一致；正式126/198=63.6363636364保持，不生成替代成绩或gate。

72条严格判错可分为：

| 类别 | 数量 | 证据 |
|---|---:|---|
| 明确最终选错，原提取正确 | 65 | 每条末尾最终选项与strict一致、与数据集标准选项不同 |
| 达65536且没有最终答案 | 6 | doc_id28/66/79/115/127/187，真实API usage逐题绑定；末尾仍在重复或未完推理 |
| 未到上限但长段重复、无最终答案 | 1 | doc_id48，61417tokens；末尾反复自我否定化学式，无最终选项 |

共8条达到输出预算65536：doc_id **7,28,66,68,79,115,127,187**（doc_id从0开始）。其中doc7、68原strict已判对，不能当成额外漏分；另6条strict invalid且无最终答案。

原生样本与代理日志没有保存finish_reason；触顶证据为API回报completion_tokens=65536，6条结束文本仍未完成，符合预算截断表现，不能伪称逐条已读取finish_reason=length。这里只读审计已有输出，未重新tokenize估算usage，也未为了补字段向模型发请求。

宽松提取“找回”的doc9/28/80/162均不是已确认的正确最终答案：doc9最终C而goldD；doc80最终B而goldC；doc162最终A而goldD；doc28一直分析DNA直到预算耗尽。宽松结果可能命中中间选项或题意引用，不应据此改分。doc48的宽松“Option A”候选仅在前段讨论选项，距结束很远，末尾长段重复且自我否定，也不是最终答对。

本审计按数据集gold和最终选项核对，不独立重判科学题标准答案。正式低分问题仍未定位到数值/采样实现根因；本结果不证明PR1069或native存在bug，也不自动追加完整GPQA、修复、优化或提高上限。

## 只读与保留状态

原始native samples SHA仍为`269b06dd2f99b2d39b0f8c247f9d8ba9f170af6c1c8374281ad5b08d1c0eaa80`；原GPQA/ERQA/原生审计回执SHA全部不变。新只读current采集与评测before在服务PID346908/ticks681351047、代码、权重/配置元数据、tokenizer、argv/env/git/版本精确一致。collect禁写pycache且GIT_OPTIONAL_LOCKS=0；仅CPU审计，0新增模型HTTP请求，0服务stop/restart/源码或配置修改。监控维持已删除，不创建新监控。

完整原回答仍在原远端case；本地临时输出只有审计元数据和有限结束片段，不把整份原始数据复制进模型记录。

审计摘要：`/tmp/qwen3vl-c64-accuracy-mx59-20261105/extraction-final-summary.json` SHA256 `7a7eaf0388292e2b925c918c3011301646a1e8774f7772dc35626addc4b198ee`。
