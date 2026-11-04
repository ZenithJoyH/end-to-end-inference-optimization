# accdiag-023：acc-015异常输出与首Prefill执行边界离线定位

2026-10-18用户要求继续查精度异常原因。按inference-accuracy-diagnosis，仅分析已有198题正式回复/token/冻结observer及当前只读源码；不新增模型请求，不改采样/源码/埋点，不重启8010，不操作8035，不重跑全量GPQA，原heartbeat保持PAUSED。若需要受控复现、GPU测试或服务变更，先说明范围并等待方向。

## 问题与冻结事实

acc-015正式164/198=82.83%<.88、有效failed-score/no gate。34错误分为11个提前EOS/11个60K无final/12个有正文错答。已有终态审计report5ba94de8/manifest2e6e31d0，source/服务/198题数据/配置/两个filter完整性核验通过；22异常API tokens匹配rank0真实采样前缀，无真实HTTP超时。017 i64修复保留、generic32884/storage合法、packed32775，现有索引/state/nonfinite检查无新错误；缺新C64逐层hidden/logits/首次GPU state，不能从finite推导数学正确。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。计划派生证据目录CASE/diagnostics/accdiag-023-output-causality-20261018，保留全部原件，不覆盖已有快照。

## 本轮离线检查

1. 对198题生成结果重新分类，区分推理不终止、起始即无关、答案格式及语义错误；不把None占位当网络超时。
2. 将每题原始prompt/API IDs与8rank首Prefill、slot、computed/scheduled及混合负载绑定，比较正常/异常及早晚准入、旧slot前任；相关性不当因果。
3. 检查异常采样是否与同时在途peer的token行重合，以及首轮设备输入/最终logits是否真的有保存；没有则明确缺口，不借旧C8 focus补造新C64现场。
4. 只读核对当前runner的input IDs/positions/logits行选择、PLE ngram上下文、QSA token-to-request/cache与GDN状态路径，找可证伪的窄边界。

离线结果已完成；root-cause confidence=首Prefill执行边界已缩窄、具体数值根因not-isolated。正式阈值失败继续阻止叠加性能优化。新的CPU派生脚本及路径/SHA在执行前记录于此。

预存CPU/stdlib-only脚本`/tmp/accdiag023-offline.py`→`CASE/commands/accdiag023-offline.py`，SHA `9e6a71cdf83afdb4d483c28303873c7bc011eb8adddec723e9d225f0854f5c23`。核验后只执行一次`python3 CASE/commands/accdiag023-offline.py`，排他创建上列新派生目录。读取acc015已有native日志/samples/83份observer冻结manifest和旧acc014回复，按原prompt精确配对；输出198题分类/8rank首Prefill及首个真实发出token的负载绑定、slot前任、异常前32采样与同时peer行比较、60K重复指标、旧新prompt-token一致性及得分翻转。post-sampler EOS之后的额外token不参与异常前缀行比较。旧新源码/运行状态不同，所有配对只作症状证据，不算单变量A/B；不导入torch，不发推理/信号/改服务。

第一份离线报告已执行，report SHA `61c1379b2350ee77c639fc25dabb7a9c62ee70b881f20cf42d991fe81eee737f`、manifest `929ce9c7b6cc39edaf82605b66851069914b08d77a016dc1587cabb7b7abd3ff`。注意其中positive_decode_peers仅computed>0，不足以判断真实Decode；first_emit仅rank0按原observer设计有记录，198题first_prefill均8rank覆盖。报告保留不改写。

为修正派生分类（不是模型代码），预存第二份CPU脚本`/tmp/accdiag023-refine.py`→`CASE/commands/accdiag023-refine.py`，SHA `54b0650359e564906cfa290b9148fb24abd9099f68f04c7c3409ca8022f6687c`。仅重读rank0冻结日志/已保存报告，以scheduled=1且computed>=原prompt长度验证peer是真Decode，追踪跨63行间隙的最近slot前任，附首Prefill的GDN gather/scatter索引/边界，排他新写`diagnostics/accdiag-023-output-causality-20261018/refinement-001.json`。slot前任不等于物理cache/state页前任，多Prefill步的算子索引仅为batch级，不能虚称逐请求因果。

## 结果与因果边界

第二份报告已执行且独立重算SHA通过：`refinement-001.json` SHA `4f49ae2fff662673ce367eaaf0522743c956ca4b619ce1b4d6adf76669f4206f`；第一份report/manifest重算均与上述一致。新建派生文件不覆盖原正式结果或observer现场。

### 1. 共12题从首token开始异常，不是只有提前EOS

11提前EOS为76/77/78/86/92/98/101/102/109/110/178，首token均非1596，起始即空白、`|`、聊天模板或与题目无关文本。另发现doc85属于同一异常簇：首token91、reasoning为`| C-41`及聊天特殊标记，574个completion tokens的后续正文在讨论“prompt injection/乱码/多边形方程”，没有回答原题，strict过滤结果`[invalid]`。因此此前12个有content错误需细分为**1个异常内容/格式失败(doc85)+11个明确答案与gold不同**，不能把doc85算成正常语义推理错答。

全部198题旧acc014与当前acc015的API prompt文本、prompt token IDs逐题完全相同，排除已保存API请求侧的题目/模板/tokenization漂移，但不能证明当前首Prefill实际device input IDs正确。22无final API tokens与实际rank0采样前缀的既有终态核验不变：EOS确实由模型采出，不是评测器漏取最终答案或真实网络超时。未发现异常前缀长段复制同时peer采样流的证据（doc102仅2个连续采样调用相同，不构成串行污染证明）。

### 2. 首Prefill边界：实际Mixed C64持续更替，而非直接FULL replay

doc64–197共134个后续请求，均证实首Prefill为63个真实Decode peer（scheduled=1且computed>=各自prompt长度）+1个computed0、一次完整prompt的新请求，slot/request-row63、graphNONE。该组104正确/9有content错误/11提前EOS/10length。初始doc0–63共64题为60正确/3错答/1length、无提前EOS，首token均1596。12个起始异常全部在前一组，且首token采样与首Prefill同step。doc178精确step97433、455prompt+63Decode=518tokens，首token91，最终11tokens提前EOS。

这是负载形态的相关性，不是Mixed本身的因果证明：大量正常请求走同一路径。slot63在前一步可能为空（batch63）并由新请求重新占用；报告补齐其上一次占用者，但**行号复用不等于同物理state/KV页复用**。坏首token产生于graphNONE步，不能把该步直接归为FULL graph replay；前序graph对共享状态的影响仍未被排除。

### 3. 大索引与状态证据不支持直接重判为旧i32故障

现有generic gather/scatter记录在正常与异常步都包含20972以上索引，已知i64实现/地址/storage核验正常；异常首Prefill的has_initial_state均False。全部198题首Prefill的batch级36层算子记录均有大索引，不能用“跨界即坏”解释结果。已有invalid/nonfinite/mismatch为0只说明这些守卫未触发，**不证明逐层数值语义正确**。部分stage包含置零索引0，不把所有stage合并range当作某一请求的单个state ID。

### 4. 60K与其余错答分别处理

11个length输出均有题目相关的长推理，60K token后仍未发出think-end或final。16token非重叠片段唯一率98.19%–99.97%，末4096token片段唯一率至少99.61%，未显示简单的短token循环；部分reasoning中出现答案字母，但也可能继续反驳，不能离线补作final或重算分数。这里可确认的直接失败机制是**耗尽60000生成预算**，是否因适配数值偏差而推理变长仍未隔离。

doc85之外11个有final错答的明确答案与strict解析一致、但与gold不同，不是统一抽取规则错误；不能仅凭最终文本证明哪个算子导致语义推理偏差。旧新配对18题由对变错、6题由错变对、净少12题；旧新运行实例/源码/负载历史不同，禁止把176→164当单变量收益或退化归因。

## 当前源码核对与下一项最小证伪

只读检查实际private021 runner与模型、安装vLLM GDN：非spec logits选择`query_start_loc[1:]-1`；输入来自CPU token行按computed/req_indices抽取；ngram上下文对computed0行先填EOS；QSA token-to-request/cache映射依赖CommonAttentionMetadata；GDN Mixed的prefill状态gather→按False mask置零→chunk→scatter写回，conv1d已显式将实际cache index转i64后乘stride。静态代码未给出可直接宣称修复的错误，尤其不能以源代码“看起来正确”替代设备现场。

最窄剩余边界是**请求更替后的首Prefill输入/元数据→PLE/GDN/QSA逐层计算→logits行选择→采样**。当前保存了API输入与实际采样token，缺新C64首步的device input_ids/positions/query_start_loc/ngram_context/logits_indices及逐层hidden/logits；旧C8 focus PT不能填这个缺口。建议下一次仅8010定点捕获该链路，并与CPU重建的本次预期输入/行索引比对：输入已错则定位runner/复用；输入相同则逐层找到首个数值分歧，再区分PLE/GDN/QSA及采样。保持i64、固定原sampling、首次异常保存证据、正常/异常步配对；有限/无越界不替代reference数值比较。

**尚未执行此新复现。需要新增埋点/重载8010或新请求时先等用户方向；本轮模型请求0、服务变更0，未影响8035，未重跑GPQA。** 最后只读检查8010 API2623908/start494912777、8035 API4161238/start487889425及原argv SHA不变，双health200。原heartbeat保持PAUSED。正式164/198 failed-score无gate不改写。
