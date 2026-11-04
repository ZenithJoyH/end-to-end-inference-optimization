# ERQA调优器参数引用：有界显存因果验证

用户“那请你来验证下吧”明确授权前述单变量有界验证。GPU4/5当前空闲、API984020已退出；不操作其他GPU/容器。沿用原B容器、TP2、端口8020、模型opt3、0.9、prefix-on、原图及现有MoE/GDN/shortlist。临时外部观察器不写生产源码；原run执行一次，release臂只清两个隐式benchmark参数属性，不清nargs或数值缓存、不改采样/分辨率。最终恢复无观察器原服务，不复用旧gate。

远端ROOT=/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-stack-regression/operator/erqa-tuner-retention-001。所有命令在CASE/commands唯一归档SHA后执行。历史证据/partial均不覆盖。

两新鲜服务retain/release从同一SQLite只读backup起点启动，私有DB不污染原库；原启动/profile/capture/16条资格均保留原引用，再启用单变量。两rank KV预算必须一致才继续。每臂启用边界后2xC8共16、text64、官方原请求doc178..325共148、sentinel1，上限245/臂；最终原服务资格16，总上限506。两臂请求完全相同、C64、SDK无重试，首错误锁定不提交后续；不是400题重跑或拼分。诊断输出不算正式精度/吞吐。

观察只保存shape/dtype/ptr/storage字节，无tensor值；weak registry不新增强引用。原始allocator snapshot只写出，分析默认仅JSON；不得不受限pickle.load。按两rank记录唯一存储、排除model/KV/encoder已知常驻后的存储、阶段边界释放前后allocated/reserved/free和OOM。storage union不是独占占用，真正allocation下降才是可释放贡献证据。

停止条件：身份/源码漂移、CPU观察器验证失败、KV预算不同、观察器异常阻后续；模型OOM保留partial后精确清理该臂，可以进入已冻结下一独立臂。任何未知进程不能宽泛停止。服务恢复失败单独记录并告知。子集不OOM不能证明完整400安全；没有失败重现不宣布唯一根因或修复完成。

准备中，尚未发新GPU模型请求。无源码提交/推送。

执行前命令归档（CASE/commands/）：
- `erqa-tuner-client-001.py` SHA `b5b13cc677e42f15522d9e9f0b3b7e3e8d8afa3a8f638a2332946f81f161effd`。
- `erqa-tuner-analyze-001.py` SHA `72ff6a3c61d6cab3080c2916a888b2a6b4ccbe51bcf3016efa96a98a87fa0514`。
- `erqa-tuner-controller-001.py` SHA `c207c9b108384aea62cd7b6d077bd1f8c900faeeedd89262b4fdeed64830cc99`。
- `erqa-tuner-sitecustomize.py` SHA `b371e23c71c78c986b6f93d8960811806471ad36f8c7944ef9300b7ad9699647`。
- `erqa-tuner-supervisor-001.py` SHA `23756234fef230f280b1020d51da3ea9acca18f0538fe8fb022c254d858c9075`。
- `erqa-tuner-starter-001.py` SHA `63779ed2d5d977c59ce64034c2a2d62e61fcd98f7128df04e84a58ec3fe8a80a`。
- `erqa-tuner-prepare-001.py` SHA `5f90001c824807af400ef50071793d81d25301f3c3cd99039e8193a07f1196a2`。
- `erqa-tuner-service-helper-001.py` SHA `475a01398ed5833d946deec877edb445449d5b2e05575d7495fc511771fd7413`。
- `erqa-tuner-cpu-test-001.py` SHA `06714f4410022133f82bbddebef1d6b7d7153b2aea7c69651d00fdf300e3e0b6`。
- `erqa-tuner-q35_tuner_observer.py` SHA `0de7d7b6746344beb8f10424edeb92b3e44ed39bf2ab2b2e066a407d698bca2e`。

已启动一次：Host controller2632503/start1150973669、supervisor2632502/start1150973661；retain API1086999/start1150973912。plan SHA2b4dc3a6e40cc37e4fc0e337e170dc400158dcf41f681f8f41b70f927972dcc8，CPU结果SHA2f15807c5ce38edc8a90f75cb744a99d97efcbc29ce02f9d7854985313da54c0（exit0）。当前加载原引用臂，尚无GPU显存结论。禁止重放starter/controller。
独立入口默认inactive，终态后唯一命令执行：CASE/commands/erqa-tuner-independent-001.py SHA397548c530bed09720f2ed69b47d8823afe406e8dbed7a446df3f26a7afd9f56。只读JSON/native证据+fresh身份/源码，不读取pickle，不发模型；仅预备，不当最终通过。

retain已16/16资格通过，两rank观察器实际命中；KV预算均22355859968B（约20.82GiB）。post-enable边界只观察不释放，每rankbenchmark context union2981486536B，其中排除已知model/KV/encoder共享后237199304B；这仍是upper bound而非独占泄漏，实际释放差值待release。无生产源码变化。

retain有限终态：前资格16，诊断边界后资格16+text64全部通过；图片64个send intent/57 HTTP200/7客户端ClientConnectionResetError(Cannot write to closing transport)，失败doc178..184，剩余84未提交。0 allocator OOM callbacks，服务保持存活。client144attempts137completed，不称144个模型实际准入，7个没有HTTP原生响应；已保留真实partial，不能作为148图完整通过/显存失败。先精确停止retain后进入release，未补跑任何题。release API1129120/start1151017653，正进行原引用启动资格。

传输错误提示存在keep-alive复用/连接关闭竞态，堆栈发生于aiohttp发送body阶段；本轮不在线更换client或重试，避免引入第二变量。后续若另做完整同输入运行，应事先预载payload并使用每阶段新连接池或force_close，保留此观察层失败。

工程范围：临时过程级LibTuner.run wrapper，不修改生产算子/Plugin/模型；A1/B4/C3/D1–D5/E1–E6/F3/F4作为适用审阅。CPU新wrapper生命周期（return/signature/exception/weakrefs/capture）通过；最小服务资格包含两个独立C8、completion_tokens>=2，FULL_DECODE_ONLY graph replay下界，不冒充directcounter。不是可合并生产补丁或正式精度晋级。

原controller退出2，原服务1140665/start1151040129恢复通过/16资格。release只完成16前资格，0释放边界/0正式诊断，未改任何引用。旧门禁预算差4096B（22355859968 vs22355864064），两臂两rank**实际KV均22351380480B，容量均2124908tokens**。原失败保留不追认。新followup-001只执行尚未执行的release部分，不重跑retain；门禁换成执行前冻结的实际分配字节/容量精确相等，观察器/请求/数值逻辑不改，复用同CPU证据与原缓存快照。接续最多245+恢复16，不补旧partial或score。
新命令执行前归档：
- CASE/commands/erqa-tuner-prepare-002.py SHA `0d76536d3cdd753ad3012a3fc102768d10387ca3aea551061c0236a32fdc4414`。
- CASE/commands/erqa-tuner-service-helper-002.py SHA `177585413db2a283941ae6d5316bf8c77bcf212cb572e08574c84855f5774ece`。
- CASE/commands/erqa-tuner-starter-002.py SHA `6b98edf1b6651acb7e920bfe86276d906459c8f7bf9f9a74fb34c2be51b6a3c7`。
- CASE/commands/erqa-tuner-supervisor-002.py SHA `410fb0a6cd4800ef3ffeb2c47bca54ef363246cb3a89956c1a65e52a055f31ae`。
- CASE/commands/erqa-tuner-controller-002.py SHA `4c494b1429faa73abb920c6b9c3ef9eb16ef71d3c4eb819b4f8a3e5c8639d3fd`。
- CASE/commands/erqa-tuner-client-002.py SHA `485d6e519ffc33e384ab977c1805e4a83555ddbd13d6764aec66231d6caa9711`。
- CASE/commands/erqa-tuner-analyze-002.py SHA `ddc0494bc87abbd6030a85d41cef11aeea23f9b5903a7752b78b36ef8d285900`。
- CASE/commands/erqa-tuner-independent-002.py SHA `48d0463942f4371cf7e03f8207e63edf3cae520f9dee37667be3c03398d652ec`。

followup-001已启动一次：Hostcontroller2707662/start1151083817、supervisor2707661/start1151083813，release API1150064/start1151086512。plan SHAe086134c51c2f5fcd33209c8713b8ee0aff9afad250c264db6c6affe9e194573。monitor qwen35-erqa-tuner-retention已更新为接续身份，旧脚本不得重放，当前独立002尚未执行。

实际释放边界初步结果（尚待完整独立核验）：followup release两rank1150685/1150686的post-enable-qualification同步边界allocated各下降244093440B=232.7856MiB；benchmark context唯一storage从约2.98GB归零，未调用empty_cache；实际KV22351380480B保持。随后2xC8共16通过。证明可释放的额外引用占用，不等于已证明完整ERQA的唯一OOM根因或正式修复。

待终态独立通过后才执行checkpoint（当前仅归档）：CASE/commands/erqa-tuner-terminal-checkpoint-001.py SHA ad486fef5265d0f1031d80dcc012bdac06cd5361d4f66eb1fafad95a0602856e。检查currentjob null/实际restored身份及report SHA，先备份CAS，不签gate。

## 终态独立结论：额外引用占用已证实，完整OOM唯一根因未证实

followup原生controller exit0、error/restore_error均null，普通原服务已恢复并16/16资格通过。独立入口002执行一次exit0，report `CASE/operator/erqa-tuner-retention-001/followup-001/independent-verification-001/verification.json` SHA `ca3a29d2711664e94302acfc08d74e905913d66b8091f06039aeb144fc6ac5f1`。109个共同算子/shape key的选中config集合差异0。新模型生成0，原请求bytes/SHA/raw/usage、真实partial、实际KV和前后源码均核验。

- retain两rank释放边界allocated下降0；release两rank各下降244093440B=232.7856MiB。清空仅_last_benchmark_args/meta，无empty_cache，实际KV每rank22351380480B完全一致。证明这两个强引用确实造成可回收GPU占用，不能把含共享KV/权重的约2.98GB union全部叫泄漏。
- 大项元数据为mul_generic_nd_kernel的231211008B storage集合：一个[2,65536,8,36] BF16视图保留150994944B底层storage，另75497472B输出和4718592B广播张量。单项集合含共享引用，未逐算子单独释放，不能精确把全部回收字节唯一分摊给它。另_index_jit_function保留2235138048B KV相关storage，与既有常驻KV共享，不是额外2GB泄漏。
- release完成148/148原图ERQA子集（doc178..325）、64/64文本、16/16边界后资格与sentinel1，诊断229/229；加前资格16为245。两rank allocator OOM0、observererror0，图文阶段context storage0，最低物理free分别808968192B（771.49MiB）与884469760B（843.50MiB）。这是有界运行结果，不是400题完整精度/稳定性验收。
- 原retain图片64send intents/57成功/7客户端closing-transport错误/84未提交，模型未OOM。因此两个arm的完整请求范围不相等，不能将图文峰值差、吞吐或148完成对比当成释放修复原OOM的严格AB因果证据。该连接错误全保留、无重试补分。
- 旧门禁4KiB预算误拒绝及其原服务恢复保留，不覆盖、不追认为通过。followup只执行之前未启用的release部分；没有重跑retain或完整评测。所有调用上限和实际次数分别记录；截至终态包括两个job资格/恢复，453个客户端attempt、446个HTTP成功、7个发送错误，不把attempt当模型实际接收。

当前普通服务：B容器API1192153/start1151143236，端口8020/qwen36-35b-opt3，GPU4/5、TP2、0.9、prefix-on，原argv/env、MoE/GDN/shortlist保持。无诊断PYTHONPATH/Q35 flags/私有DB override；生产6850源码字节匹配。临时引用释放没有作为生产修复保留；没有新formal gate或旧gate重绑。

终态checkpoint命令exit0，continuation SHA `ba2eaf884364937cf0d7495595345cc679c4198da994e4f0b165181d84369ab9`、phase erqa_tuner_retention_contribution_verified_original_restored、current_job=null。监控qwen35-erqa-tuner-retention已删除，停止空轮询。

判定：确认一个约233MiB/卡的可避免显存压力来源；不支持“单纯显存容量使所有C64图文必然无法运行”，也未证明仅修此项就能让原ERQA400稳定完成。完整OOM仍可能与视觉编码批次峰值、既有预算余量和额外调优workspace共同有关。若后续正式修复，应限于正常推理不持有隐式offline benchmark参数并保留显式benchmark接口，再按用户另行指示做相同0.9/C64完整回归；本轮不自动启动。
