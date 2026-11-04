# diag-004 GPQA受控对照诊断

本轮完成四次全量GPQA对照，**未复现最新FlagGems-vllm稳定退化；确认同版本、同请求seed下并发推理仍存在回答波动。** 具体导致不同回答的底层算子尚未隔离。原acc-003的123/198失败保留，不以重跑较高分替换，不签发新的通过gate。

Issue：`diag-acc003-gpqa`。诊断任务已完成；根因分类`suspected`，版本退化`not-reproduced`，不是`measurement-invalid`。GPQA64分门槛仍阻止当前组合正式晋级和继续叠加性能优化。

## 受控设计与结果

mx-59的独立容器`qwen3vl-pr977-20261022`，同一GPU0/1、TP2/BF16、18977。预声明顺序B1新→A1旧→A2旧→B2新，仅切换FlagGems-vllm实际导入树。gems-opt、Plugin、采样接入、黑名单、权重/tokenizer、启动参数、MoE调优选择均保持；prefix cache全程开启。原9999生产服务未改动。

每轮重新启动，双worker实际FlagOS MoE命中、graph capture及每worker至少16次replay、smoke/C8均通过。随后同序doc0..197做C1/生成1token的prompt cache准备；正式测量仍为198题、C32、18000生成预算、temperature0.7/top_p0.8/top_k20、API seed1234和CLI/task seed42。使用相同原始runner、任务来源、题目和请求arguments，独立UUID响应缓存。所有轮均保留，没有看到分数后挑选或丢轮。

| 顺序 | FlagGems-vllm | 正确/题数 | 分数 | 64分阈值 |
|---|---|---:|---:|---|
| B1 | 最新PR943运行树 | 128/198 | 64.65 | 达到 |
| A1 | 原内联MoE运行树 | 125/198 | 63.13 | 未达到 |
| A2 | 原内联MoE运行树 | 124/198 | 62.63 | 未达到 |
| B2 | 最新PR943运行树 | 125/198 | 63.13 | 未达到 |

旧版平均62.8788，新版平均63.8889，新减旧为**+1.0101个百分点**。按题配对bootstrap（10000次、固定重采样seed20261022）95%区间为**[-0.2525,+2.5253]个百分点**，包含0。这是以四轮观测为条件的题目重采样区间；每版本只有两轮且只有一个API seed，不能当作完整跨运行/seed置信界或证明版本影响严格为零。

旧版重复两轮169/198原始回答相同、3题正误变化，净差1题；新版177/198回答相同、5题正误变化，净差3题。跨版本B1/A1有7题正误不同，B2/A2仅1题。旧版两轮本身也低于64，故低于阈值不是新版独有；当前证据不支持把此前生产130对新123的7题净差直接归因最新MoE。原比较还跨GPU对及缓存/运行状态，本次不能证明那7题只由一种因素造成。

## seed审计和版本内复现

需要纠正早期解释：规定镜像中的`TemplateAPI.__init__(seed=1234)`将seed传给原生OpenAIChatCompletion payload；模型创建additional_config没有覆盖它。CLI42属于另一层，**API请求本身已经固定为1234**。vLLM按请求创建独立torch.Generator，FlagGems MetaX exponential_也向Philox helper传入该generator。因此不能用“没有固定请求seed”解释下降。

短探针仅比较回答前128token，不做精度打分：C1下seed1234、5678分别重复两次均一致，两seed之间不同，省略seed也不同。C8固定1234重复仅4/8一致。统一priming后三轮C8相邻比较仍只有4/8、5/8一致，C1重复仍相同。因此冷/热缓存准备不是唯一原因；同seed并不保证当前并发全模型调用逐token复现。动态batch造成数值差异再被采样放大是待隔离假设，尚不能指定为某个算子错误。

## 固定输入MoE与源码证据

旧/新实际MoE在GPU2使用同一BF16 hidden/weights/router，E128/H2048/I384/topk8，M=1/7/8/32/64/65/256/512/1024/4096/8192，**全部逐元素相同、最大差0**；各版本内部重复也相同。M1/64/4096每版本capture一次、replay两次，共6次capture、12次replay，均与未capture结果一致。真实GEMM1/2配置、FUSE_SILU/direct_sum选择也一致。该证据反对这些固定输入/shape下的MoE数值退化，不替代全模型证明。

旧树`/workspace/FlagGems-vllm/src`，MoE SHA `faeeead6990fb078e4ab625dba092eec47e1680a16f869659bd7743c0803ca3d`；新树`/workspace/FlagGems-vllm-pr943-runtime/src`，MoE SHA `749e81cfdbb4032aaa23648c53f32e3486d1e93c5aa03e41f2cb59d27f77b9e9`。新树基于上游bad340d，MoE与发布PR943 head316f036一致，同时保留四个原采样兼容覆盖文件。实际源码指纹而非git HEAD单独决定代码身份。

新旧MoE kernel函数AST一致；host/profile/workspace组织有变化，但本模型已测路径选择一致。现有BF16 Attention函数AST相同，新增MetaX Attention主要为INT8；MetaX调优YAML未变。库中其他模型的变更不等于本模型命中，需要按实际路径解释。

## 固定logits采样器补充对照

在主四轮全部结束后，GPU2单独测试当前真实Plugin通用FlagGems-vllm topk/topp过滤、native采样和FlagGems exponential_组合；同一FP32 logits、词表151936、请求seed1234、同黑名单。M1/7/8/32/64，两种布局（连续、行末padding17）各重复两次，共20组。每次独立clone输入并验证相同输入SHA，避免原地过滤污染后续测试。

20组全部满足：输入相同、首行概率逐位相同、全部行/不同batch/布局/重复间的随机噪声相同、输出token相同；generator offset均37984。该限定测试未复现固定输入采样器的batch相关随机性。结合C1稳定/C8全模型不稳定，后续应优先捕获模型生成的首次分歧logits；仍不能仅凭合成logits证明所有真实输入和完整长序列采样都不存在问题。

初版探针M1的`.contiguous()`与原row共享存储，过滤原地改变了后续输入，已明确标为`measurement-invalid`，保留原始结果与无效回执；不能把其输出差异当作算子bug。修正版使用`.clone()`并逐次验证输入SHA。此控制问题只涉及补充探针，不影响此前四轮原生GPQA对照。

有效结果：`results/sampler-fixed-logits-v2-summary.json`，SHA `2dd8f1fb00e691e651af0123a3aeb87c5cae97a35723fe76c71ecc1b02c8ec00`；无效初版说明`results/sampler-probe-v1-invalid.json`。

## 证据有效性、终态与剩余问题

四轮均核验198唯一题号、全部filter、原生逐题/聚合一致、冻结task/config/provenance、原始runner SHA、原生样本及results SHA。每轮前后模型/tokenizer、四仓库源码及服务身份一致；跨轮模型、vLLM、Plugin、FlagGems、启动配置相同。低于阈值的wrapper退出1是预期测量结果，不掩盖失败。辅助原始acc003的progress122不替代原生strict-match123。

结束时已保持最新运行树：实例`qwen3vl-pr977-20261022:446914:560444786`，18977 ready，GPU0/1，prefix cache开启；9999仍为`qwen3vl-opt10`。没有修改三个仓库源码，没有回写生产，没有新端到端性能结论。

后续如要进一步定位，应固定token前缀捕获首次分歧logits，对照单请求/动态batch，再隔离具体算子或归约边界。当前没有修复补丁，不关闭原精度问题；真实修复后须按原始全量契约取得新的通过gate，而非挑一次重跑分数。

## 远端产物与控制过程

远端根目录：`/public-flash/jinghao/qwen3-VL/20261022-qwen3vl-gpqa-controlled-diagnosis`。每轮的原始问答、task和log保存在`trials/{B1,A1,A2,B2}/`；本地只存摘要与校验引用。

- 最终主证据`results/final-evidence.json`，SHA `b16bd2ea462c84154230093b91900d745fa27b2b1a106a83e0670e55dde3bab5`。
- 四轮汇总`results/full-control-summary.json`，SHA `ba88a754bb67de7ac972a4af3bed49c4ee2a4e7d8b26c66c641890520b01abe7`。
- 完成回执`results/controller-completed.json`，SHA `2d5e6505f69ff474a7dad7fcd93177cb95fb8c4b69e591355539914a05a9d322`。
- 短探针`results/seed-probe-summary.json`、`results/warm-probe-summary.json`。
- 算子与graph `results/operator-replay-summary.json`。
- 契约`manifests/full-control-plan.json`、源码`manifests/source-comparison.json`、payload `manifests/payload-audit.json`。
- 可复现命令和SHA见state；执行控制器`commands/full_controller_v2.py`、验证工具`tools-v2`。

控制过程均保留：离线请求构造最初误用max_tokens，发模型请求前已纠正为原生max_completion_tokens；CPU旧评测器不挂载新R，v3改为只读输出传回host；工具copy2在NFS保留元数据时报EIO，旧内容保留并按字节校验，改用tools-v2。缓存reset route404，未开启dev参数，改用相同重启/priming。以上不影响四轮主测量有效性。

全诊断完成回执：`results/diagnosis-completed.json`，SHA `9cef671c4c1c645df84b578d54f31f4f46311196f5bec891472afc740cead45c`，关联四轮主证据、有效采样补充和无效探针说明，最后再次核验18977最新运行树/prefix cache及9999模型身份。自动监控`qwen3-vl-gpqa-erqa`已暂停（automation_update回执PAUSED）。没有自动启动下一轮评测。

后续[diag-005固定前缀定位](diag-005-fixed-prefix-logits.md)已将独立运行副本同步PR943 a1570df，并在完整Q/K/V相同、同实例探针中性及忠实重放下定位首层MACA native kvcache自动路径的batch数值差异；组件固定split1消除差异，服务未应用该参数，其他配置及9999未动。原正式GPQA失败不覆盖，无新score/gate/E2E。
