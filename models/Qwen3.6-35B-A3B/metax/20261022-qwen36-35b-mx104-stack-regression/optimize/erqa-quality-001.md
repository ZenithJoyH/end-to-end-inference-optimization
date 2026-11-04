# ERQA 47.5%结果诊断

用户要求分析本轮ERQA偏低原因。采用本地inference-accuracy-diagnosis，先离线原始400题/官方规则/健康/历史同题交集核验；不重跑模型、不改服务或评分，不以ERQA未冻结阈值阻塞已通过GPQA。当前无同配置NV ERQA基准，根因未确认。

新commands/user5-erqa-accuracy-analysis-001.py SHA708f00288db03f023b2fd4e0565c7319daa8bb99f8827eb3e23fd93703df69fe；输出CASE/accuracy-diagnosis/erqa-quality-001/analysis-001.json，0新增模型/admin请求。旧失败partial保留，历史共同成功题比较不能冒充全400或隔离归因。

初步analysis001已通过：362单选项190正确，38附带文字/截断，历史成功交集分数近似。进一步新commands/user5-erqa-accuracy-analysis-002.py SHA3e8738a9d290a157dd59a0c7b7a2aaf91d72bb293fe67414e79edb5c99d66841，离线验证历史同题所有图文请求/参数（仅model别名可不同），统计PNG尺寸和格式损失，读取当前模板/预处理与greedy源码并绑定原manifest；不调用模型或修改服务。

## 离线核验结论（2026-10-29）

正式结果保持190/400=47.50%，没有重新评分、生成、服务操作或源码修改。确认一种局部原因：回答格式不服从官方短答要求；其余错误的模型/执行机制根因尚未确认。

- 362题按官方归一化后为单选字母，其中190正确、172选错。另38题不是单字母，其中17题以正确字母开头但附加说明，例如doc7 `C. Quarter turn clockwise.`、doc24 `B. No.`。官方整段去句点、strip/lower后精确比较，附加说明仍判错。
- 仅离线提取明确的开头选项用于诊断为207/400=51.75%，比官方结果多17题/4.25个百分点。这不是官方新分数，也不能解释剩余差距。其余20题附加说明且开头选错，1题达到300token上限。
- 请求为temperature=0、max_tokens=300、enable_thinking=False。当前模板SHA与评测manifest一致，并确实为非思考分支注入空think块；回答completion tokens中位数2、无非空reasoning。非思考短答协议可能限制复杂空间/多视角推理，但尚无单变量证据量化影响。官方Qwen模型支持两种模式，不能将非思考本身称为错误。
- 400次HTTP全部200，无空输出/拒答，399stop+1length。截断即使全部挽救最多0.25个百分点；本轮不是OOM请求被计错，也没有证据表明数据漏图/图文顺序错误。全部630图及请求字节已核验；这不证明设备视觉数值等价。
- Multi-view11/37=29.73%，Trajectory29/66=43.94%，Spatial43/84=51.19%，State31/55=56.36%。错误集中情况只能用于下一步选取固定诊断样本，不能仅凭类别确认算子根因。

### 历史同题比较

仅比较旧失败轮已成功返回的同题，逐题问题/答案/图像hash/图文交错及请求参数完全一致（忽略model别名）。不将旧partial冒充完整400或隔离A/B实验。

| 旧轮 | 同题数 | 旧正确 | 当前同题正确 | 全文相同 |
|---|---:|---:|---:|---:|
| C64 20261028-001 |210|99|99|189|
| C64 20261028-002 |262|127|127|238|
| C64 20261029-001 |252|119|121|226|
| C32 20261029-002 |180|89|87|165|

这些结果不支持KV预算修复造成大幅新增降分；低分问题此前就存在。但不是隔离因果实验，不能排除已有视觉/MoE/GDN路径数值影响。当前没有同协议NV ERQA参考；用户此前NV77.53属于GPQA，不能用作ERQA对齐标准。

### 执行路径和后续顺序

原vLLM sampler源SHA b8c03e99ea099f710440a1390e1495772a563477a5eafaf3f6d75af194024f76与评测manifest匹配：all_greedy分支在top-k/top-p之前返回argmax。结合本轮temp0，暂无证据优先归因shortlist；这是源码分支判断，不是新的runtime trace。MoE/GDN仍参与logits生成，不能排除。

下一步优先预声明一组固定、有代表性的同题短程对照，隔离thinking开关和输出预算，不把两变量同时改变后的差异归因单一变量；每个回答仍保留官方严格分数，选项提取只作诊断。再获取相同图文输入/协议的NV或原生参考，区分模型能力/协议与优化栈数值差异。当前未启动任何新对照或全量评测，不修改官方metric，不按错题写特化代码。

### 证据

远端目录：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/accuracy-diagnosis/erqa-quality-001/`。

- analysis-001.json SHA fe8f80b9127271932775fa7fe08ac983ced8ba3de31da7f655be46d2b40d1ceb；command SHA5115aa6b061ed42b3d1e3724fd9f5d1fd554b748e79c97333339d518139ddd66，exit0。
- analysis-002.json SHA6d1a682c92a0b8959d2ef17c7c6b2a8c98f2d5a613f57627445b49104f1f74b0；command SHAa86525c404719ab5c00a2f28bdc1d71657a9faba62693bf9a2b224e0a71a431f，exit0。
- [官方ERQA冻结harness](https://github.com/embodiedreasoning/ERQA/blob/5bba488252c5b345a43335bfb9239b6bf12bd91c/eval_harness.py)：原始短答请求、图文编码和整段精确评分。
- [Qwen3.6-35B-A3B官方说明](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)：默认思考模式和可显式关闭思考，协议不等价；没有据此引入新的ERQA参考分数。
