# C64 模型默认采样全量 GPQA 与 MATH500

用户2026-10-27要求：评测其当前已启动服务，64并发，模型默认采样，全量GPQA/MATH500，每半小时通知。

目标mx-103，deepseekV4-flash，18001容器内loopback。当前API PID868640，thinking开启、prefix caching开启；本任务按用户当前服务原样评测，不修改源码/启动配置/重启服务。原service已停止记录不再作为当前事实。新服务image与现有相同，规范化三个挂载只读核实相同。

使用本地inference-accuracy-evaluation，显式mode=formal-gate；GPQA走官方规定镜像及SHA原始llmrun.py+formal_accuracy.py，全量198，沿用预冻结threshold0.8。MATH500为同一规定镜像原生math_500任务，全量500，通过SHA校验的原始runner执行；正式gate工具只支持GPQA，不扩展或冒充MATH500 gate，MATH500仅报告原生exact_match及完整性，不预设阈值。

模型generation_config.json temperature1/top_p1；评测框架默认temperature0、MATH任务0.6/top_p0.95，因此显式覆盖temperature1/top_p1/top_k-1/do_sampleTrue以匹配模型默认。两项max_gen_toks30000，保留各任务原生stop；API adapter自身默认seed1234未另设采样seed，lm-eval数据/fewshot seed42。两任务串行，各自num_concurrent64，不并行变成128。每次独立UUID响应缓存，不复用历史答案。GPQA/MATH500任务及数据在推理前冻结，不改变提取器或计分。

远程：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01`。commands/保存执行代码，manifests/保存当前服务及全量权重/tokenizer/engine/三仓源码新哈希；outputs/原生样本、results及run-record。原始大文件留远程。

Heartbeat `deepseek-v4-gpqa-math500` ACTIVE，每30分钟通知，包括无变化状态，终态停用。

执行前登记：
- `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01/commands/accuracy-tools.tar.gz` SHA `2bb835726485d2108d81c8ead67bf262a140e324eeed8d2f99bf6cc0a9297469`
- `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01/commands/coordinate.py` SHA `c2dd54e52a4dd21c16747b0c71edd76e3486ce106a9329c0f3a448e2a947445d`
- `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01/commands/identity.py` SHA `70878df28fc11f3a08b7ef44f610d0caf7063aab62e06780df742b368708e2e4`
- `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01/commands/prepare.py` SHA `fe10987fcb4a2daa19f341b6e529816d97019a3d4e0b433ef4c8613d3db132be`
- `/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01/commands/run-math.py` SHA `843090defa2eb2202552374c5a1f37e8a259bb777966361b0a4a7eba3994f5a7`
- 初始化及启动脚本 `/tmp/dsv4-accuracy-c64-20261027/stage.py` SHA `92fc60480e133141f58a5b8ceda7385e8f1d0ff2fb2cf860d7160cfde4d77b99`（逐文件哈希校验后先保存远端commands，再执行prepare/coordinate）。

补充取证/导出静态wrapper和清理本任务被网络阻塞的只读task-discovery探针，commands/supplement.py SHA `1f217a3a65a09d4fae0ed9601ddc0d757ad15f37c82b523b88c661a482ed0ea5`。仅精确匹配本任务创建的旧评测容器python3 -c，不触及用户服务或当前评测进程。

## 已启动

2026-10-27 14:20:52 Asia/Shanghai，GPQA正式评测启动，原生UUID `d655915da84e4576b79d3008ec745fe6`。截至本次只读观察，响应缓存54个唯一问题已完成；尚未最终计分，MATH500排队，不能将部分样本成绩冒充最终分数。

全62权重分片、tokenizer和engine及三仓当前源码身份新校验通过。当前service manifest SHA `529cacd667bee2b7610e424b924e74c1f622468a2abceeb505d02e966f2c5fb2`。GPQA配置SHA `070c75ce8c769552f29741e2dfd35cd036e72ec5c5557aa6480e6d369c467ed1`；MATH500配置SHA `0a2d811b8213a9b3dcb55966e5ee2d2535e76107f3f76e58bc79abfe522f8f80`。

## 跟进入口

读取远端progress.json、result.json/failure.json和coordinator-process.json，对照精确PID/startticks；不要重放启动脚本。logs/gpqa-full.log与math500-full.log为host侧流式日志，只读取尾部。原生cache/outputs位于新评测容器 `deepseekV4-flash-accuracy-c64-20261027` 中的相同R绝对路径，host侧outputs在阶段结束时导出。进度可从R/cache下单一当前task响应sqlite_rank0.db以read-only查询`SELECT COUNT(*) FROM unnamed`得到唯一缓存响应数，结合pbar/原生samples辨别错误、重试与最终完整性；不使用日志行数。API适配器源码实测seed默认1234并传给请求，lm-eval seed42只控制数据/fewshot。

MATH500没有预定pass阈值。原始runner、任务、数据和评分均保留；完整500唯一doc_id和样本exact_match总分对原生results交叉核验。不将MATH500签为仅支持GPQA的正式gate。

GPQA若低于80%可能没有run-record，但原生results/samples仍保留，coordinator继续运行用户要求的MATH500；这不授予继续叠加优化。任何failure.json必须检查真实原因及进程后处理，不重复整套测试。GPQA的strict-match和flexible-extract分开报告。终态需要最终结果、当前身份/源码不变检查、原生完整样本核验，更新本记录和state，停用heartbeat。若GPQA score<80%或证据无效，按本地accuracy-diagnosis技能解释并冻结证据，不擅改阈值/提取器重计。

旧评测容器的网络探针已经自行正常结束，supplement命令未向任何进程发送终止信号（匹配0）；正式评测和模型服务无影响。

本轮交接前末次观察：GPQA缓存85唯一响应，与服务success(stop)=85一致，驻留running=64，waiting=0，length/abort/error均0；coordinator精确PID/startticks仍存活，无failure.json。尚无最终成绩。MATH500仍等待自动接续。

## 14:45半小时进度（2026-10-27 Asia/Shanghai）

GPQA于14:45:27完成，耗时约24分35秒。原生strict-match **165/198=83.3333%**，flexible-extract **79/198=39.8990%**（独立filter，不相加）。198唯一doc_id完整，每filter198行共396行，原生results与样本逐题计分一致；正式schema3 gate签发且再次check通过，超过冻结80%阈值。gate SHA `81ca0f647cf15ee577f09387e64b19462970953bb6b2df722715e3c663d6eccc`；run-record SHA `be1b62529fe6c085fab67cacabe8e0ec0f8ab857a7017eb68d9fe49d001ddbba`。原生服务累计191自然结束、7达到30000输出上限，abort/error均0。这7题保留在198分母中，未排除或改分。

MATH500在14:45:32接续启动，原生API生成14:45:39开始，UUID `5cdf176c89594526a3426b3b8f8662b0`，C64；随后只读cache观察31/500完成，仍在运行。当前服务API进程/startticks/参数完全相同，4424个源码文件重新哈希一致。未启停服务或更改采样。Heartbeat保持ACTIVE。

审查工具读取samples时发现Unicode行分隔符会被Python str.splitlines误切，已使用标准文件迭代（仅换行\n分行）正确读取，正式acceptance工具本身也使用逐行迭代，gate有效。这是辅助读取问题，不是原生JSONL损坏。注意commands/run-math.py末尾的辅助完整性读取仍含read_text().splitlines，若MATH原生跑完后该处报同一JSONDecodeError，应改用原生sample_validation.iter_sample_records或文件逐行迭代核验既有结果，再补后处理/身份检查并导出；不要重新发500题、不改原生样本/计分，也不要把辅助解析失败说成模型失败。

最终核验前登记：commands/final-review.py SHA `0dbf74096a9582fccc2dd0dc5f77179a47c7b5ebd1e142fa1b493f5501da872c`。仅复核已有原生样本/计分/冻结数据与服务身份，写本任务final-review.json；不发新推理请求、不改变评分。

## 完成（2026-10-27）

全部评测于15:06:49 Asia/Shanghai完成，15:17现场独立核验。

|任务|完整样本|正确|原生得分|约耗时|
|---|---:|---:|---:|---|
|GPQA Diamond strict-match|198|165|83.3333%|24分35秒|
|MATH500 exact_match,none|500|479|95.80%|21分10秒|

本次C64，模型默认temperature1/top_p1/top_k-1/do_sampleTrue，API适配器原生seed1234，lm-eval/fewshot seed42，thinking开启，用户当前服务prefix cache开启。最大生成30000。GPQA满足冻结80%阈值且schema3 gate再次check通过；MATH500没有预设达标阈值，只报告实测成绩，不签GPQA格式gate。

两项698/698唯一题完整，GPQA每filter198行、两filter396行，MATH500单filter500行。逐题exact_match与原生results严格一致；MATH500所有doc内容哈希与推理前冻结500题逐项相同，任务数据/helper文件未变。GPQA flexible-extract79/198为另一提取器结果，不合并或替代strict-match。

服务累计690自然结束，8达到30000输出上限，其中GPQA7、MATH5001；所有题均计入分母，无排除/重计。原生results两项timeout均0，服务abort/error均0，当前日志未匹配OOM、illegal memory access或Traceback。当前API同PID/startticks/参数、4424源码文件哈希完全一致，health200，running/waiting均0；模型未停止或重启。

原生MATH500完整评分与辅助校验均正常完成；上一条记录中的splitlines潜在风险本次未触发，无需修改或重跑。

最终外部回执：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/accuracy-c64-default-20261027-01/final-review.json`，SHA `419f686546e1d56d39833f3a40d610dd585a9480138ada7625325383cffc78ca`。coordinator result SHA `9bd960dd0c699f8c2903675bbc6b0eddea7457e17059d04cf45653fa1fc1588f`；identity-after SHA `9fc60a3ce8cfd0c900c4768a67b3a373a9825cf0fc0dc578ca6eaa34bc3ccb2e`。

MATH500 results SHA `8d6eef3be06ac22163abaa5f92e99ea68e98ed57e2721a7e92a8f94b7e9c0233`；samples SHA `0336e3e4710e33fb642106db898197c29ef90891b3f8da28ca89468208c52582`。GPQA results SHA `4cffc65f6a6198a8fe0009b2e50ed08ce2f0e2e13b713b91298edd47b7859868`；samples SHA `291fe60886a3d095e02d8efce2cc7d76ae0c34e670ea423e1a7d1e2554f0a1bf`。完整绝对路径见final-review任务引用，原始样本/日志留远端，不提交本地。

半小时heartbeat `deepseek-v4-gpqa-math500` 已删除，原因为两项完整评测及最终核验均完成。官方评测容器保留作证据，不停止用户模型服务。此成绩属于本次当前C64/prefixON/APIseed1234配置；与此前C32/prefixOFF/APIseed42得分不作为单变量回退或加速对照，也不宣称完成四场景性能最终验收。
