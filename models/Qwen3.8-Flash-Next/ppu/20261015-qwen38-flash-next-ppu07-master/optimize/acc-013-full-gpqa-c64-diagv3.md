# acc-013：现有诊断v3服务的C64全量GPQA复测

后续状态：用户已另行授权[accdiag-017 i64修复与仅8010受控恢复](accdiag-017-index-i64-fix.md)，8010已恢复且两条C1正常，C8/C64局部回归运行中，未再启动全量GPQA。本篇原生0分/执行失败事实不改写，不当作新修复候选分数。

## 用户授权与结论边界

2026-10-16用户明确要求“先重跑一轮GPQA，看看问题是否还存在”，授权本次新的全198题运行；此前局部128请求上限及禁止formal只约束旧诊断，不沿用为本次198题限制。只使用8010现有实例，不重启/改源码，不影响0–7/8035，不复用旧响应缓存，不重复正式运行挑分。精度评测模式`formal-gate`，并结合`inference-accuracy-diagnosis`观察原reasoning-only及非法访问问题。

当前服务仍为`qwen3.8-flash-opt-ppu07-20261015`、PPU-07/8010、TP8物理8–15、API1325804/start483425629，加载`/opt/qwen38-accdiag016-20261016`私有取证v3。**本轮是带诊断同步/guard的服务复测**，不能代表无埋点生产候选已修复；未请求也未擅自移除埋点。原故障污染127/198及无有效gate不改写，accdiag016局部128正常且20972未覆盖的结论保留。即使本次得分通过，也只绑定实际带埋点源码、实例与环境。

## 冻结契约

- `gpqa_diamond_generative_cot`，limit0、198唯一doc、strict-match `exact_match,strict-match`阈值0.88。
- 单服务`http://127.0.0.1:8010/v1/chat/completions`、num_concurrent64，维持原native runner派发顺序，不以局部cohort顺序替代。
- temperature1/top_p0.95/top_k20/min_p0/presence_penalty0/repetition_penalty1/max_gen_toks60000；evaluator seed42、API原默认seed1234/stop不变，timeout7200、API retries3、eval retries0，与旧正式契约一致。
- 仅增加`return_token_ids=true,return_prompt_text=true`响应证据字段，不改模型采样/EOS/评分取值。已在规定镜像中CPU核验原生gen_kwargs布尔解析及payload透传，不发送额外smoke请求。
- 新CPU评测容器`qwen38-eval-ppu07-acc013-c64-20261016`，镜像`harbor.baai.ac.cn/flageval/flageval-llmeval:v1`，host网络、仅/mnt挂载，无加速卡；只复制GPQA原始数据缓存，不借用旧响应缓存/得分。
- 前后核验实际私有Plugin/Gems/FGVLLM/vLLM源码内容与权重清单/tokenizer、实例/argv/白名单环境；图capture/实际replay绑定当前实例原始证据，不伪造新warmup或性能结果。prefix cache必须有当前服务日志关闭证据。

## 执行前记录

远端唯一目录：

`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-013-full-gpqa-ppu07-c64-diagv3-20261016`

已完成目标Host inventory/connectivity-check、8010 health200/running0/waiting0/KV0及旧eval/诊断客户端退出核查。工作根规范路径、owner0/mode700、约8.1TB可用已确认，新case尚不存在。

| 执行副本 | SHA256 |
|---|---|
| commands/acc013.py | e3933fcc10369dc6fd4c6911ae00cdc51a8e90178c07cacaad8ead31ff13ee47 |
| commands/source_probe.py | 869b0bd2e37095dbe783641ed0e5a4ef3662bef5c942a8c9d674b81b1a9edb02 |
| commands/accuracy-bundle.tar | b96e8a7914f1760f94ad1fac23346c63cf6b06b478a227d405e37401a353ff45 |
| bundle/test/Accuracy_test/llmrun.py | 82cf6e8304cb6f9eb8ca48fe4055f6bbb2054a7b6a90d56de3d6b7a08e90c61e |

两个脚本AST通过；Skill bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。准备命令`python3 case/commands/acc013.py --mode prepare`：排他准备marker、全新eval容器、两次实际task/data provenance一致、当前source/服务绑定、`formal_accuracy.py --preflight-only`。准备成功后重新启用原monitor，再一次性执行`python3 case/commands/acc013.py --mode run`，由维护版wrapper调用SHA核验的原始runner。formal marker独占，拒绝重复。

现有观察器继续写accdiag016/runtime-002；新case的`evidence/observer-boundary.json`冻结每个rank与服务日志的原始offset/inode，**旧runtime-002/FINISHED不等于本轮结束**。本轮首次异常由原v3自动保全，监控只读取证、不自动恢复；运行结束控制器复制新增日志字节与既有首异常state文件到新case。完整原始采样前缀、真实generic/packed索引分开观察，20972未触达就记not-covered。不改写旧freeze或marker。

## 状态与监控

状态`preparing`，正式尚未启动、score/gate未知。复用原heartbeat `qwen3-8-ppu07-gpqa-c64`，待准备完成更新为本次运行、30分钟、实质进展/异常/完成通知，无变化安静。完成/失败后核验198唯一题、多filter、完整HTTP/token、服务前后身份及源码；仅工具有效完整且score>=0.88签发实际绑定gate。helper排除None后的高子集分数不能当正式精度，API content=None转TIMEOUT与真实网络超时必须分开。旧结果不替代本轮。

### 准备通过及唯一正式启动

14:15:40.607624+08:00 `PREPARED`写成，prepare exit0、两次provenance逐字相同，dataset_revision与旧正式相同，preflight明确“no evaluation was started”。当前实际私有4个入口SHA与accdiag016部署一致，vLLM/FGVLLM及模型/tokenizer指纹未变。服务manifest SHA `bb9e981a052cdc1f3777d9de44018f3b65869d6b70a1bea3f96bc90a5260379e`，contract SHA `3dfe8e95fa3c4277ee2c6a6e66ee299694f2d5d853a89c5c10f3278f89984a76`，source-before SHA `e8efa60579f58f2a39a1901de9565555bde830b15e3b14aaf279fbef653f7ee7`。当前服务日志有enable_prefix_caching=False原生证据，不为加CLI参数而重启。

原heartbeat已通过产品工具更新到本次acc013并ACTIVE、30分钟，仅实质变化通知。执行前新增`CLIENT_LAUNCH`排他记录后，将`python3 case/commands/acc013.py --mode run`以独立会话后台运行，stdout/stderr保存在新`client.log`，精确PID/start ticks写`CLIENT_PID.json`。控制器再核验实例、源码、空闲后独占写FORMAL_STARTED并调用原生wrapper；若任一前置检查失败，保留CLIENT_ERROR且不自动重试。该后台启动只属于本次唯一正式进程，不是第二套评测器。

### 本轮终态：实际23520索引触发执行前guard

正式于14:17:12.597828+08:00启动，控制器Host1590773/start484725752，UUID `5f9b92e8480844828f774e8970608ac2`。14:17:27.991384+08:00全局排他`FIRST_ANOMALY.json`由rank5写入：step75113、GDN `language_model.model.layers.4.linear_attn` prefill gather/IndexFunction实际int32索引23520，has_initial_state=false。这是本轮第一条实际模型Prefill，前一128局部已排空，scheduler现在分配复用的大block ID；不是另加请求的微测。

pool shape[87529,6,128,128]、stride[102400,16384,128,1]、FP32、storage_offset1920元素、storage35851878400字节。index23520本身在合法行范围内，i64行偏移2408448000、i32模拟偏移**−1886519296**，已跨20972边界；正确行字节区间[9633799680,9634192896)合法。**不是scheduler给出了超出pool行数的索引，而是32位乘法的地址偏移溢出条件被真实请求触发。**

现有v3执行前保护冻结operand/state后抛出`accdiag016 stopped BEFORE unsafe generic index; first operands frozen`，导致worker/engine/API退出。未允许危险gather kernel继续，所以**本轮不是一次已执行kernel的非法内存访问复现**；也不能用此guard异常当无埋点原版fault的完整因果证明。原nonzero同步点不是这里的执行边界，旧TLE unsupported候选编译提示仍不直接归为根因。首Prefill graph mode为NONE、291输入tokens、1个请求；没有本轮采样token前缀或正常最终API回复，不声称已复现reasoning-only。

8rank均保存36条layer state文件及operator-input-output.pt，manifest列出的大小均匹配、暂无capture_error。它们仍是selected rows和有界共享pool最后执行快照，不是完整pool或每层独立历史。全局FIRST_ANOMALY时间以排他marker为准；STOP_DISPATCH是另一个排他文件由rank3写入（.9916227），两者不因时间/rank不同判作证据冲突。

14:17:49.087202+08:00控制器自然写FINISHED，exit1、same_source=true、same_service=false、verdict=incomplete、gate=null。evaluator/helper/controller已退出，8010拒绝连接但容器保持running；没有人为停止/重启模型。原生396个filter对象覆盖198唯一doc，但全为故障后失败占位，原生0分不能代表有效模型精度。完整结果和sample相对case位于`results/Qwen3.8-Flash-Next-ppu07-acc013-c64-diagv3/5f9b92e8480844828f774e8970608ac2/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/`。`FINAL_SUMMARY.json` SHA `81de0e660d8ebf1ad4bb145d8e7ab6653af68273323b7e93c0116503a9d67af9`。

控制器已复制本轮新增rank/服务日志及state到`diagnostics/observer-delta/`、`observer-files/`，原manifest324条、SHA `4fc627a15c84518a096905ece9954fb36b9bc2db7d2dc7b62c1d2d182a3e27de`。追加纯CPU终态核验命令`python3 case/commands/freeze_incident.py`，脚本SHA `0be22ee34753956c0bdc5cdd58b40b905b64dd9ad95bbcf8ad247a8c6bfe97a7`、AST通过；仅校验已有324份副本、8rank state和native sample，再保存新`diagnostics/incident-freeze-001/`的manifest/report及完整服务日志前缀，不执行tensor反序列化/GPU框架/推理、不修改服务。

原heartbeat已通过产品工具确认PAUSED。下一步等证据最终SHA核验与用户方向，不自动恢复8010、不修改索引实现、不重跑；精度/性能仍无有效gate。现有危险输入/位宽条件已观测，旧非法访问和reasoning-only因果仍需受控i64修复/原路径对照验证。

### 终态证据校验完成

`diagnostics/incident-freeze-001/report.json` SHA `1253499bbbd24a9bc69fb6740945a0f0f93cd7c7f5f224c233cbfab4ca8ce017`；manifest SHA `58c0aa075dbcd1b3f3198ad0b1618f6894bd8d897192257a906b696b477ff29b`；rank-state-audit SHA `171f410497afaebee3fb529626bc0d8dc786b8974f8df16ead10505508beff03`。独立重算324份observer副本SHA全部通过；8rank×36份selected-layer state共288文件、8份operator-input-output及8份manifest齐全，列出的文件大小一致、capture_error0。总manifest绑定403个文件/357300447字节，并新增保存完整当前服务日志固定前缀；未采集独立host-wide driver/kernel日志，不冒称完整全机driver dump。

本轮rank0新增日志没有sampled-token-prefix（首prefill在采样前被拒绝），generic gather最大23520、scatter已执行记录最大16741、clear最大0；没有新packed decode设备观测，不能用旧18856冒充本轮值。native samples的198唯一doc均为`<TIMEOUT>`故障占位，是engine/API退出后的500/连接拒绝等失败，不是198次等满7200秒，也不是198个成功完成题。没有可保全的本轮正常最终回复/完整输出token，不能拿旧128回复补造；输入/索引/slot/request/graph/状态和HTTP失败日志均保留。

结论`incomplete-execution-failed`，正式score保持未知/不可用，原生0.0单列故障污染观察；无gate。本次推进是**实际大索引及偏移溢出条件已命中**，尚未证明未经guard的原kernel错误与旧乱码/reasoning-only因果；下一步建议针对索引先升64位再乘stride的最窄路径设计单变量修复与边界回归，需用户指示后执行，不在这次“重跑”授权中自动改码或恢复服务。
