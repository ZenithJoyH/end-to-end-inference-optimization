# diag-006-common-wrong-truncation-config

状态：离线28题审计完成；两道预算配对复现已被用户50000全量重测取代，保留partial。技能：inference-accuracy-diagnosis、minimal-regression。触发：用户2026-10-13要求分析两backend都错的28题，尤其输出截断与评测配置。已有正式159/198和160/198达到80%；本轮健康诊断不作gate阻塞，不改分、不改变原正式契约。

## 当前结论与证据边界

最清楚的可操作问题是**输出上限30000会切断尚未完成的思考**。两轮完整各14题finish_reason=length，均精确生成30000token；FlagGems13题错、1题strict正确，原生14题全错。28共同错题中8两边触顶、3一边触顶、17双方正常结束且最终选项错误。输入188–2891token，触顶时输入加输出最多32891，远小于服务262144上下文；8192是每批调度token预算，不是输出上限。

所有396个样本的原响应与对应HTTP日志内容SHA准确关联，避免按异步响应顺序错配题号。正式gold与原始Correct Answer的shuffle映射逐题核验相等。正常结束的17共同错题未发现正确final答案被strict误提取；12题两边选同一个错误答案，5题选不同错误答案。剩余错误集中于专业推理/知识、题目歧义和可能的共享推理栈问题，不能仅凭两backend同错就断定模型自身能力，更不能断定FlashAttention数值问题。

预算影响的上界：若所有触顶错题都能救回，FlagGems最高172/198＝86.87%、原生174/198＝87.88%。这只是13/14题全恢复的算术上限，不是预测，不是新分数。长思考反复验证或持续枚举已经可见，加预算不一定结束，更不一定答对。

## 28题审计

下表“与gold不同”是对现有样本和数据集解释的比较，除明确的数据/映射检查外，并非独立科学正确性认证。

| doc_id | 输出状态 | 机制/观察 |
|---:|---|---|
| 8 | 正常结束但错 | 分子点群：把两个稠环分子的C3h/D3h判断与gold相反 |
| 13 | 正常结束但错 | ChIP伪峰：选择重复区域，gold关注开放染色质及标准NGS处理 |
| 17 | 正常结束但错 | 丰度标注强疑点：两边按相对丰度得3.98，gold12.6；原专家反馈也指出概念问题 |
| 27 | 一边触顶 | 反应序列/动力学烯醇盐和甲基位置：一边正常但位置判断与gold不同 |
| 30 | 一边触顶 | 多步反应产物：一边把终产物识别为硝基苯亚甲基丙酮，gold为靛蓝 |
| 32 | 两边触顶 | EXO/meso构型反复验证，均未结束思考 |
| 36 | 两边触顶 | 多步反应和13C等效碳重复检查，均未结束思考；进入预算代表诊断 |
| 71 | 两边触顶 | 笼状产物及氢信号数的结构猜测循环 |
| 75 | 正常结束但错 | 嵌合胚胎：一边否定凋亡，一边推定红绿共定位，均与gold细胞质定位不同 |
| 76 | 两边触顶 | Cope/Claisen及反应连接方式反复讨论 |
| 81 | 正常结束但错 | 立体描述符：两边直接将相邻相同R/S当作cis，选择A而goldD |
| 85 | 正常结束但错 | 化学选择性及CIP优先级：两边按保留构型选A，gold同一S底物对应两产物 |
| 90 | 两边触顶 | aldol/DAST产物立体构型反复检查，均截断 |
| 102 | 正常结束但错 | 芳香取代序列：两边选D，与goldC不同；完整中间体路径判断未独立实证 |
| 106 | 正常结束但错 | 题目客观性疑点：两边选异构体预处理而gold先体外验证；expert2也质疑选项唯一性 |
| 113 | 正常结束但错 | 氰醇步骤：两边采用酸性HCN路径，gold指定亚硫酸氢盐中间体 |
| 115 | 正常结束但错 | Diels–Alder/CIP相对与绝对构型判断与gold不同 |
| 121 | 两边触顶 | 多步合成及质子等效数反复检查 |
| 126 | 一边触顶 | 原始两个错误选项重复A/D；goldB唯一，一边截断、一边正常错，未发生gold映射错位 |
| 130 | 两边触顶 | NOE/endo-exo及桥氢空间关系反复验证 |
| 138 | 正常结束但错 | 反应类型：两边按氧化/二醇解释，gold为烯醇亚硝化水解 |
| 147 | 两边触顶 | 持续枚举非银元素/高阶氟化物，均触顶；gold锁定AgF127，进入预算代表诊断 |
| 157 | 正常结束但错 | dominant-negative后果：两边推定降解，gold聚集；不是提取失败 |
| 160 | 正常结束但错 | 平均自由程：两边假设相同碰撞截面后比较热运动因素；与gold不同，题意/物理假设未独立核验 |
| 164 | 正常结束但错 | 双催化乙烯体系：链行走/活化条件与gold选择性铬催化不同 |
| 167 | 正常结束但错 | “难以察觉”范围：两边包含更多数据格式问题，gold仅3/4 |
| 168 | 正常结束但错 | 衰变终点：两边把相空间变化解释为终点降低，gold为移除有质量粒子后提高 |
| 185 | 正常结束但错 | aza-Cope键迁移/产物命名均与gold不同 |

8项双触顶：32、36、71、76、90、121、130、147，均未关闭thinking、没有完整final。3项单触顶：27、30为原生触顶；126为FlagGems触顶，另一轮正常结束仍错。领域计数：化学20（有机18）、生物5、物理3。

## 评测配置核验

| 项目 | 实际值与判断 |
|---|---|
| 集合/任务 | gpqa_diamond_generative_cot、原始198唯一题、修复科学方括号后的固定provenance；zero-shot、repeats1 |
| 指标 | exact_match,strict-match；固定80%；两filter396行按doc/filter唯一，分母仍198 |
| 输入 | 单user消息包含题目/选项和步骤及final格式要求；没有将gold/Explanation作为提示 |
| 采样 | temperature1、top_p.95、top_k20；实际API构造方法移除do_sampleFalse，仍采样 |
| 随机种子 | harness42／实际API1234，两个backend一致；不能将CLI42误报为HTTP42 |
| 输出预算 | max_gen_toks30000被映射成HTTP max_tokens30000；任务默认18000被显式覆盖，HTTP usage确认30000 |
| Thinking | template默认注入assistant `<think>\n`；没有enable_thinkingFalse；未设置独立thinking token预算 |
| Prefix / graph / 并行 | prefix关闭，graph FULL_AND_PIECEWISE、TP2 BF16；服务启动参数未因本诊断改变 |
| 调度 | 正式C32；max_num_batched_tokens8192只控制chunked prefill/批调度；两道复现另行C4，不能冒充C32重评 |
| 终止 | EOS按weights配置，另stop `</s>`；触顶finish_reason=length，完整final通常stop。无输入/超时截断证据 |
| 答案提取 | case-sensitive `answer is\s*[\(\[]?([ABCDEFGHIJ])[\)\]]?`，取最后匹配；标签metric忽略大小写/标点 |

strict扫描整个输出（含thinking），没有专门分离final，故可能从中间思考提取字母。FlagGems触顶doc61曾匹配正确字母但未完成final：本契约仍计正确，不自行删题或改gate。未发现共同正常错题的final被误判；当前数据不支持通过换regex救回这17题。flexible分数低于strict不能替代冻结指标。

官方[模型卡](https://huggingface.co/Qwen/Qwen3.6-27B/blob/main/README.md#best-practices)的Thinking参数与本轮一致；多数查询建议32768输出token，复杂benchmark建议81920，并给出不同的MCQ输出格式。卡上GPQA87.8，但其具体GPQA prompt/seed/repeats/预算协议未核验。当前30000/custom COT/单轮结果不能直接视为复现了官方条件。不能为了对齐宣传分数擅自换prompt、指标、gold、温度或正式预算。

## 数据集质量问题与保留规则

- doc17：按标准相对丰度，`[Si/H]1=0.3`、`[Si/H]2=-0.3`，同H归一化的比为`10^0.6≈3.98`；gold为12.6。原dataset专家反馈直接指出作者将相对太阳丰度定义用错，[Epoch一手分析](https://epoch.ai/gradient-updates/gpqa-diamond-whats-left)也质疑同一题。作为强标注/题意疑点记录，未修改gold或重新计分。
- doc106：原expert2质疑问题客观性及选项唯一性，两个backend都倾向不同于gold的前期异构体步骤；需独立专业判断，未证实gold必错。
- doc126和89：原始数据的两个错误选项重复，正确选项唯一，expert反馈可核对；不是科学方括号修复遗漏，也不是gold映射偏移。不能用重复干扰项证明模型选择A正确。

## 两道最小预算复现（已取代）

冻结doc36（有限但重复的核磁/结构验证）及doc147（持续枚举候选）两类截断机制；原生black03同实例，C4同时发每题30000/81920两条件，总共4请求，无重试；温度/top_p/top_k/APIseed/原prompt/stop保持，两条件都加return_token_ids作为观测。45分钟HTTP timeout；无服务重启、无源码变更、无性能测量。

只有短条件确实length30000、两条件prompt和前30000token完全相等、长条件正常结束且答对，才确认该题由预算救回。若前缀分叉，则不能归因上限；若81920仍截断或仍错，则证伪“只要增加预算就能解决”。本2题诊断不签发gate、不产生新的198分数。若后续切换正式81920或官方prompt，需要单独冻结及批准的新正式契约，旧结果全部保留。

评测容器qwen36-fa-gpqa-fixed-20261012/PID1556/create1791856237.54，绑定服务qwen36-fa-opt:82515:1791815908.86（同source内容指纹再次验过），仍只用独立2/3卡18002，源8002不操作。复用监控qwen36-metax-flash-attention-op001，ACTIVE/30分钟，只通知有意义变化及终态，结束后暂停。

## 外部证据

根目录：/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention

| 产物 | SHA256 |
|---|---|
| commands/diag006-audit-common-wrong.py | 4c548f94391e3b895bfd75f25674ac64ce0e772857998e2eb7561823a3f9e3e5 |
| results/diag006-common28-audit.json | 3b7357037084805d6f0da5b3ed57350114bd0e64455d6aab00463e88f14b7910 |
| results/diag006-common28-summary.json | d25ff0cd46ab8fc3e829fbdb935e059db552432b2eb392f10580196ce0c2296c |
| commands/diag006-config-audit.py | e2a2219f2a0dff0ee9314d6dc0e5367c696dd4b0c6c0e7449eaeda495912bad9 |
| results/diag006-config-audit.json | 9817f8c57c69bbcb8fb63e959c2069cfd1bca4f26ab0bf4a3f0ab56df5cc8ac0 |
| commands/diag006-budget-plan.json | 583653a98dd61d9671319fb5d7bd764f4453da0cf8b72953a974baa6524b85ca |
| commands/diag006-budget-worker.py | 3b44dc9353c494c565a7f69ffa469861519b9248b19429911be734b8e3eb238e |

所有原题、长响应、请求、HTTP日志和gold专家讨论保留远端；本地仅归纳与索引。API来源代码SHA和两轮输入sample/log SHA在审计JSON中。`results/diag006-budget-probe/terminal.json`与`manifests/diag006-budget-process.json`为下一检查入口。已通过正式两gate未作任何修改。

预算复现启动回执SHA `0ec3df7f75cd7e8b35998a9d7c36fbbbc4c41372e14b1bc28d2b5fade6464d54`；最后只读检查精确PID/create相等，4请求运行中、排队0、完成0，当前尚不能判断救回情况。

用户随后明确选择正式50000输出预算完整198题。已精确停止本诊断客户端，保留两条30000/length/invalid响应；两个81920响应未完成，不形成预算救回结论。取消回执manifests/diag006-superseded-by-cap50000.json SHA8c2cc46f21848f68ef31319c7491dc97e2a94fd8ac8e014e4405aa54acccce06。既有监控已转绑定[diag007正式重测](diag-007-native-cap50000-full-gpqa.md)，不再监控或重复本诊断。

后续用户批准50000完整结果已验真，见[diag007](diag-007-native-cap50000-full-gpqa.md)：length14→5，158/198低于80；原14截断题5本轮正确，但前缀已分叉，不能给出严格budget-only救回结论。旧两题81920未完成的边界保持，本轮不追加任何重测。
