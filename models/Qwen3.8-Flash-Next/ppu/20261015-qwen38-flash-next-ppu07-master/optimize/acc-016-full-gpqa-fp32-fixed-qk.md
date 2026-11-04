# acc-016：当前FP32/i64/QSA M16/固定QK调优服务全量GPQA

## 当前终态：服务非法访问，incomplete / 无gate

后续只读定位见[accdiag048](accdiag-048-ple-state-invalid-page.md)：实际FlagGems-vllm PLE state kernel遗漏乘前i64扩位，真实stride204800导致首个危险row10486；3份驱动寄存器/相对PC与缓存机器码反推唯一合法row11242，地址偏差-8GiB。源码/编译缺陷确认，事故机制高置信度；原始完整设备indices缺失、未做GPU重现或修复验证，正式incomplete结论不变，不外推旧60K因果。以下为最初终态核验记录。

2026-10-20本轮11:20:40启动、11:33:52控制器自然终态，总计约792秒（13分12秒）。11:52起只读核验：原8010 API/控制器/原生wrapper/evaluator/helper均已退出，8010连接拒绝；eval容器仅剩保活进程。未重启、未重跑、未访问8035。同一heartbeat已由产品确认PAUSED。

原生strict-match为38/198（0.1919191919191919），但本轮受到服务故障污染，不能解释为有效模型精度下降至19.19%，结论为`incomplete`，不是有效完整精度失败或通过，无gate。samples有198唯一题、两filter各198行，同doc的原始内容/arguments/resps/usage/hash一致；其中仅39题正常返回，38题正确，159题是`Cannot connect to host 127.0.0.1:8010`导致的真实连接失败后`<TIMEOUT>`占位，不是159次7200秒网络等待超时，也不是159条reasoning-only回复。39条解析API对象与samples按完整content+usage逐份唯一绑定，token长度与usage均一致，全部finish=stop、含248069、末248046，330–3353 tokens；无空final、无60K length截断。39题子集38正确不能替代全量分数或宣称精度通过。

首次设备故障现场：service新窗口先出现驱动`Exception invalid page`，`Exception at function: _ple_conv_state_kernel`，首个PC `0xcf7409d8`；其后11:33:22.267 rank5、11:33:22.276 rank4、11:33:22.357 rank1的ProcessGroup watchdog报告illegal memory access，11:33:25 executor因worker死亡退出。NCCL watchdog是后续异步同步上报点，不是已确认的根因。当前支持的边界是PLE状态kernel非法页访问；实际输入索引/有效地址/首个错误写入、编译或状态复用是否致因尚未隔离，不把它等同旧index/index_put缺陷。没有本轮GPU首次异常state或完整逐层QK/logits现场，不能用旧047e两条PT冒充。

本轮8rank新增日志各有3415条batch-binding及34条实际graph replay记录，最后显式count=3328，证明当前实例确实执行过graph replay，但不能以此证明PLE状态地址正确。新窗口未见generic gather/scatter实际索引/stride/storage或packed设备indices事件，20972边界为`not-covered-by-retained-evidence`，不从scheduler推算。无FIRST_ANOMALY marker并不否定驱动非法访问，因为formal请求未配置窄张量采集。

控制器自然冻结`CASE/diagnostics/observer-delta/service-diag.log`及`runtime/rank0..7/events.ndjson`，9文件的长度、SHA、原源文件终态尾部均独立核验一致。完整服务日志仍在上文runtime006/service-diag.log；其原始寄存器/反汇编、watchdog栈、scheduler dump均保留。formal-run.log保留39条完整解析API对象及tokens（不是HTTP wire bytes）；159个未返回请求无最终API token，不补造。source-before/source-after完全相同SHA `f112c291af01410d8baa907ef3e926313699c429059468c179162a5e1f009a8e`，但原服务已死亡，不能签同实例成功绑定。

原生结果与样本位于CASE/results/Qwen3.8-Flash-Next-ppu07-acc016-c64-fp32-fixed-qk/10d1630a159642bb9bf995c62ac56278/gpqa_diamond_generative_cot/Qwen3.8-Flash-Next/：`results_2026-10-20T03-33-42.961808.json` SHA `e6d0725ef5098fcaaa8150bb64f1b0f36c6eee351e3b7e81c32922774ae98809`；`samples_gpqa_diamond_generative_cot_2026-10-20T03-33-42.961808.jsonl` SHA `f9155b9391d8c28d21ae5939bddc1d9b465055e3a408593e7eb812dff95d8010`。

失败/不完整回执`CASE/FINAL_SUMMARY.json` SHA `ec864bcdc53228f45d014e03718db04b9a47dc224d9506188dc8d2a4f04b8ac7`；`FINISHED` SHA `cbf29da72d4b6bc97f64ef029e611b41c5a06636b82868055a5f3c92c156d634`；observer-manifest SHA `28eaace84cb6c9f43ba73dd7b8e67ac97c532e42d96c1d2c17f01f116bd10f4a`；本轮service delta SHA `d848405cd56d0485a03dd553f2663ea03b8a59d0140fc096df8edd9765e0a6f1`；formal-run.log SHA `e99ce07e0e75ee1002b57e284d9832a95aeadfd07ad56722fc3632782745ef75`。原生wrapper exit1，summary same_source=true/same_service=false、verdict=incomplete。无新精度gate，性能优化仍阻塞；旧acc015有效164/198失败不改写。下一步等待用户指定仅离线定位或批准受控复现；不自动修复、恢复或全量重跑。

## 授权与冻结范围

用户2026-10-20明确要求启动服务跑全量GPQA，覆盖之前局部“不跑全量”的限制，但不授权重复启动、自动重跑、改源码或额外重启。本轮模式为inference-accuracy-evaluation formal-gate，独立198唯一题/单服务C64/limit0，task=gpqa_diamond_generative_cot、metric=exact_match,strict-match、threshold=0.88；temperature1/top_p0.95/top_k20/min_p0/presence0/repetition1/max_gen_toks60000，evaluator seed42、API默认seed1234/原stop、API retries3/eval retries0/timeout7200，返回完整tokenIDs/prompt取证。

Host PPU-07，容器qwen3.8-flash-opt-ppu07-20261015，8010/TP8物理8–15。只读核查当前API3644676/start518122313仍health200且running/waiting0、prompt686/generated2，故复用该已恢复实例，不再重启。不访问8035或操作其他服务。保留attention/MoE FP32、env041 Gems i64/randn修复、QSA M16、normal_/index_select黑名单、047固定调优和去重观察器；不因新正式评测改数学或埋点。

原局部runtime006的相同前缀logits与005逐位相同，但与旧043 max1.5仍在，不宣称修复已成功。本轮完整正式结果单独判断；旧acc015 164/198 failed/no gate和旧局部结果不代替新分数。

## 原始目录与执行计划

新CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-016-full-gpqa-ppu07-c64-fp32-fixed-qk-20261020。
新评测容器qwen38-eval-ppu07-acc016-c64-20261020，规定flageval-llmeval:v1镜像、全新UUID/容器本地SQLite响应缓存，不复用旧答案。命令先排他保存CASE/commands；部署同SHA维护formal_accuracy/acceptance/sample_validation与原始test/Accuracy_test/llmrun.py，只用单服务原生runner，不新增评测实现。

执行顺序：核验当前服务/source/镜像挂载/空闲资源和无本任务旧客户端→保存当前manifest与observer边界→创建新eval容器及复制原数据缓存→两次无推理provenance一致→冻结schema3契约→维护wrapper --preflight-only→复用原30分钟heartbeat并唯一launch。运行中不得重新prepare/launch/run、重启/修改服务；无可靠数据不估ETA，进度按唯一doc证据，不把多filter行数或排除None的helper分数当正式进度/分数。

## 证据限制与终态规则

当前实际观察器和完整服务日志位于旧acc015/diagnostics/accdiag-047-fixed-tune-qk-state-20261020/runtime-006，CASE冻结现有journal byte/inode与非journal文件边界，只分析新窗口；两条旧047e目标的PT/状态不充当本轮formal请求现场。窄QK/logits完整采集只对旧两条opaque ID配置，不能宣称新198题也有完整逐层张量或logits；保留正式native解析API响应与完整token，但不冒充HTTP wire bytes。运行时已有通用索引/状态日志覆盖按实际字段核验，缺失如实记录，不为精度结果新增埋点或重启。

正式评测继续收集错答、空content和length，不因单题错误自动停/重跑。API content None→TIMEOUT占位不等于真实网络超时。服务异常只保全已有证据，不自动恢复；新索引/状态/NaN/非法访问与首次输出健康异常应及时通知，已有旧marker不能当新故障。

## 准备回执与唯一启动命令

prepare成功，未发送推理：当前8010原实例/源码/镜像挂载通过；新eval容器已建，两次无推理provenance完全相同，SHA `c39228d57fd391a9f723496f54fa2fb3f0d7aeb17810a2edf63559152dc63523`、数据revision与旧198题相同；维护wrapper preflight明确通过且无评测启动。新响应缓存与UUID只会在正式启动生成，不用旧响应。

controller CASE/commands/acc016.py SHA `ead12824e45223769e9238a2e339c74d3383ca412754691ef691602503e0f3d5`；source_probe.py SHA `0d85786571b2e2b8fc95299fe24c47da247a8e80fbf7cc6a3bcaff802c52449f`。执行层复用SHA核验后的旧正式wrapper执行/原生结果绑定/单次launch函数，仅更换本轮CASE/EVAL/当前source-runtime边界，并将8035保护函数改为不访问；prepare重新核当前身份，未把旧manifest换PID复用。

PREPARED SHA `90dc149d4f2cba09f609651ac729c54114c0ff2b08324ae3c56caeb65e8bc285`；config `f82abe4b869779bfb9c0367be2b54674a4d9914f039d001d16e3fd4e2d5f0404`；contract `3a0c4a020ea5153bae9b01cb72cdd999cf82c948d0fc3de9306ac853e78c04af`；service manifest `14f1a0bbd57d554c6a26ab5ba42330227172eef0a2bcd0fa9d875e9f26ea12bb`；当前source-before `f112c291af01410d8baa907ef3e926313699c429059468c179162a5e1f009a8e`；observer边界 `603eeeae21695f938b0fae2427e82f4329d80f3fc3b8c2f8af2020e5f243264b`。

Skill完整bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`、模式formal-gate已核，原30分钟heartbeat同ID已产品确认ACTIVE、目标会话不变，新name为Qwen3.8 PPU07 acc016 GPQA C64，只读/实质变化通知、不重复启动。执行前冻结命令：`python3 CASE/commands/acc016.py --mode launch`仅一次，唯一子进程`--mode run`调用维护formal_accuracy.py包装原始llmrun。保留prepare/预检与native完整日志；不会再prepare/重启或自动重跑。

## 已实际启动

唯一launch成功，controller Host4011383/start518226570；FORMAL_STARTED 2026-10-20 11:20:40+08，原生API请求于11:20:55开始。native wrapper Host4011766、lm-eval4014412及helper4014413均属于本轮eval容器/进程链，不是多次正式尝试。UUID `10d1630a159642bb9bf995c62ac56278`，原生明确`Cached requests:0, Requests remaining:198`，C64/timeout7200、API retries3/eval0和所有原采样/max60000参数已从实际config与native启动日志核验。HF offline cached-dataset提示只说明数据来自已核验缓存，provenance和198题内容指纹不变。

11:22初始只读：8010 health200、running64/waiting0/preemptions0、prompt17545/generated70推进，controller/evaluator/helper健康，CLIENT_ERROR/FINAL_SUMMARY/FINISHED均无；这不是完成题数，不按在途/派发数计进度。分数/gate pending，无可靠ETA不估。结果根CASE/results/Qwen3.8-Flash-Next-ppu07-acc016-c64-fp32-fixed-qk/10d1630a159642bb9bf995c62ac56278/。原8010未额外重启、源码/配置未改，不访问8035；30分钟同一heartbeat ACTIVE，继续只读监控，等待原生评测自然结束。

原生task日志含`do_sample=False`兼容元数据警告；已只读核本轮实际`lm_eval/models/openai_completions.py` SHA `83cb3d92d08feaf919b91562a3aeab5055b52873eed729845f37c33a2370e38e`，chat `_create_payload`先pop该不支持字段，再从gen_kwargs取明确temperature1，并保留其他参数，不把该警告解释为本轮greedy，也不为消除警告而修改采样或重跑。API基础模块SHA493c6671属于该版本来源核查，不是新增补丁。

终态核验198唯一题及每filter完整、native结果/来源/当前服务与源码前后一致、进程退出；score>=0.88且证据有效才报告维护工具签发的gate。低分failed-score，故障污染或缺证incomplete，不签假gate。不复用旧分数、C1结果或历史replay证明当前formal身份；启动前runtime graph_replays按实际未证实记录，后续正式请求中的实际replay另核。完整结果、samples、日志、token、gate或失败证据留远端，写回本记录/state/README后暂停同一heartbeat，等待用户方向。
