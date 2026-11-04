# accdiag-046：043与045同前缀跨实例logits差异离线定位

2026-10-19用户授权：只基于已保存输入/logits/编译产物区分缓存、编译和状态初始化。保留attention/MoE FP32、Gems i64修复和QSA M16，不访问8035，不全量GPQA；新增埋点或重启8010先报告等方向。本轮**0新推理/0GPU测试/0源码变更/0埋点/0重启/0服务信号**，只CPU/Host读取旧证据，新增分析结果排他保存，不覆盖043/044/045原件。按inference-accuracy-diagnosis执行，不调用模型评测或性能测量。

## 触发与冻结范围

045两条doc71/C1/343prompt/max1各HTTP200，all8rank raw/prob完全一致且无NaN，输入/位置/选行/seed/RNG/noise与043相同；但相对043每rank完整248320raw有244308项不同、max1.1875；过滤概率及token1596不变。043与045 Plugin483文件原字节相同/原FP32 helper相同，运行实例和fresh private caches不同，043曾完成19请求而045仅2。原044首NaN现场另保留，本轮主比较043q0/q1与045q0/q1，不拿旧layer38 doc81张量冒充doc71现场。

CASE=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/accuracy/acc-015-full-gpqa-ppu07-c64-current-i64-qsa-20261018。旧R43=`CASE/diagnostics/accdiag-043-doc81-layer-lmhead-20261019/runtime-001`，旧R45=`CASE/diagnostics/accdiag-045-rollback044-first-request-20261019/runtime-001`；新离线产物D=`CASE/diagnostics/accdiag-046-offline-cache-compile-state-20261019/analysis-001`，脚本先在CASE/commands保存/SHA冻结再执行。只读取这两次归档及其明确关联源码，不扫描其他任务或8035。

## 证伪顺序和证据边界

1. 核冻结manifest/SHA、实际device输入/位置/query/row/shape/stride与请求和原始采样分布；分别比较同实例重复、跨rank、跨实例差异。
2. 核source/probe/配置/CLI/环境和调优数据库；路径/opaque请求名差异明确归一化，不能把任意二进制差异直接归于数学实现。
3. 对比保存FX、生成代码、Triton IR/LLVM/metadata/最终二进制与缓存key，追踪模型实际shape对应的selected/autotune信息；区分路径重命名、编译hash、tile/算法/精度或归约变化。
4. 检查初始化/清零/KV/GDN读取前写入及首次两请求路径的现有日志/静态生成代码。未保存的设备状态不可离线补造；源码存在zero或初次异常消失不等于实际状态已证明。
5. 若缺逐层/初始状态或无法绑定实际kernel，结论用suspected/unknown；提出下一最小证伪设计并说明是否需要新埋点/重载，当前不执行。

本轮不签formal gate；旧164/198 failed/no gate和性能阻塞不变。分析完成写回同一记录/state/README；heartbeat保持PAUSED，不启动新控制器。

## 离线脚本冻结

`CASE/commands/accdiag046-cache-audit.py` SHA605e86bcd74bca7fea8ea6fb8cfc8a7730e18624f493967acd30909257c5561f：只用Host标准库顺序读取两份已冻结归档，核原archive/member SHA，排他创建D并保存文本/DB快照、逐rank FX路径归一化diff、共同cache key与autotune配置差异、原始runtime事实和报告；不导入模型/torch、不加载编译二进制、不用socket/信号。归档存在不冒充在线实际kernel命中。上传先拒绝目标已存在，再核传输SHA，执行一次。首次本地py_compile写系统缓存权限失败仅工具问题，改用/private/tmp专用pycache，不改变分析或服务。

第一阶段已完成：04314590成员与04512656成员及归档SHA核验通过；8rank FX仅去除已记录private路径后完全相同。存在472份共同best_config字节差异及IR调试路径差异，不能把它们直接当算法变化。第二阶段`CASE/commands/accdiag046-selection-audit.py` SHAcd0c2302e2441324f5d9a57ab48c9e35048e1af3e9d4839f523102271eb43b1c，仅CPU读取新snapshot，剥离调试metadata后比较IR，区分计时/hash与实际knob差异，打开已复制DB+WAL的只读连接，核selected参数；不打开live数据库/生成新kernel。排他产物D/selection-audit-001。SFTP上传因跳板路径不可用失败、前置sha未找到故未执行，改SSH排他字节传输+SHA后才唯一执行第一阶段；容器无rg改grep，均为工具限制无模型影响。

`CASE/commands/accdiag046-tensor-audit.py` SHA85574a90fd7ed97a5360c1aa869f159db7a5160b76e2df57ab4d7e92512d7462：容器CPU/OMP-MKL1/CUDA_VISIBLE_DEVICES空/PYTHONPATH空，仅torch.load已保存043/045输入采样64PT且核SHA，不导入模型或执行GPU；核同实例重复/跨rank全向量，计算raw差异是否仅平移、top-logit边际及think-end/EOS值。排他D/tensor-audit-001；不是模型重跑。

`CASE/commands/accdiag046-kernel-link-audit.py` SHAfe113d805a2c38e99bde3d7274e3c61c564be1c44fd92827e0a71d8321c7f5dc：标准库静态读取冻结归档中的ELF可执行section和AOT artifact/依赖；只pickletools解析opcode，不pickle.load/import/exec或加载二进制。核8rank AOT cache keys和归约参数对应源码；容器仅pathlib读取本任务GDN/QSA/PLE/shortconv源码保存当前SHA，不初始化torch/GPU。新D/kernel-link-audit-001，不覆盖前两阶段报告。

静态读取确认AOT实际为CRC32+大端uint64分帧的CacheCompiledArtifact，不是直接pickle；前一阶段的pickle opcode unknown仅格式识别限制，没有执行反序列化。按当前Torch两个序列化源码只读定义，冻结`CASE/commands/accdiag046-aot-bundle-audit.py` SHAab43d7f99edeb55fb05d9e934847f9dc76f2abea98a122fd2034a8547de8f02c，标准库手工解析外/内CRC和字段，只JSON读取autotune记录、核每rank每subgraph的AOT/torch keys，**不调用Torch load_cache_artifacts或pickle.load**。产物D/aot-bundle-audit-001，进一步区分终态cache中的候选与编译bundle里实际保存的调优配置。

## 离线终态：优先嫌疑为编译调优选择，初始化未排除

本轮所有分析脚本已自然退出；0新模型请求/0GPU测试/0服务信号/0重启/0埋点/0源码改动/0端点请求，不访问8035，也没有再次调用正式评测。只读容器源码和CPU torch.load保存张量；CUDA_initialized=false，FP32/i64/QSA M16没有改变。旧045 API绑定是3385225/start513345302，**本轮不以旧绑定冒充新的在线健康验证**。

### 输入与数值事实

- 重新核043/045共64份输入/采样PT的SHA/大小/可加载性。各自q0与q1的raw/prob逐位相等，且每轮的8rank raw全量也一致。跨轮全部8rank实际input_ids、positions、query_start_loc、logits_indices、seed、RNG-before与actual_noise相同，排除这些已保存边界的输入/随机性漂移；没有保存的其他模型kwargs不外推为已验证。
- 差异确是前向raw分布而不是常数平移：244308/248320项不同，max1.1875，mean_abs .1727825064，RMSE .2189179607；减掉均值后max仍1.1851419468。最大位置token18746，043=-2.6875、045=-3.875。
- 两轮top1均1596/logit27.375，top1-top2 margin分别9.125/8.875；实际top-k/top-p后**仅一个非零概率，1596=1**。所以prob/token相同是过滤掩盖前向差异，不是数值恢复。think-end248069 raw13.375→13.625，EOS248046为6.5625→6.46875、248044为5.0625→5.4375；本单tokendoc71不能用于判断原doc81/178的结束概率或60K因果。

### 三类假设的证据

| 假设 | 当前证据 | 判断边界 |
|---|---|---|
| 源码/输入/旧缓存污染或错版本 | 已保存installed source快照完全相同、Plugin483字节相同；CLI/采样/graph相同，只有private/cache/output路径及清除DIAG044不同。两轮均独立fresh cache并从相同017调优DB基线起步。04314590和04512656归档成员及archiveSHA全通过；043多出的运行shape与19vs2范围不同吻合 | 没有支持加载错误版本或文件损坏的证据；未把cache key/文件数不同直接当污染，也不声称排除所有不可见runtime缓存 |
| 同配置编译错误/编译不确定性 | 8rank完整FX只归一化private路径后逐字相同，400对子图AOT keys及Torch key相同；831共同source、825TTIR/TTGIR去debug位置后全相同。99份LLIR剩余文本差异样本为assert文件名/长度；825份共同ELF的可执行section对比无差异 | **未看到同配置产生不同计算代码的证据**。只约束共同key，不涵盖新选中不同配置或外部vendor库；ELF检查为静态代码段，不是在线launch trace |
| 编译autotune选择差异 | 664共同终态best_config中192字节同、382仅计时/hash变化、90实际knob变化（XBLOCK90、num_warps60、R0_BLOCK6）。进一步按CRC字段静态解析800份AOT bundle：400对子图中367对保存不同autotune参数，803差异实例/202独立key；其中R0_BLOCK变化17个rank/subgraph记录、9个key | 不是仅凭终态cache存在推测，**编译产物内保存的调优参数已证不同**；但仍不是每请求kernel实际launch，也没有该kernel输入/输出，不能据此确认1.1875根因或实现错误 |
| 状态初始化/复用 | 043和045前两请求均真实freshC1/computed0、graphNONE且同实例两次exact；当前GDN源码Prefill为gather initial_state→按prefill_has_initial_state置零→chunk→写回，i64源码保留 | 重复性削弱“每次随机坏状态”假设，但不排除固定每实例的初始状态、参数打包/allocator状态或未覆盖kwargs。没有实际has_initial_state/device初始GDN/KV/PLE状态、初始化后权重hash或doc71逐层hidden，不能凭源码zero语句宣布初始化正确 |

SQLite快照1559表核验：所比较mm/linear/gemv/split-K/index调优表参数与benchmark最优候选一致；差异集中4张mul表（043额外shape及少量参数差异），没有把SQL候选当实际kernel命中或忽略它们。原数据库不打开/不改；SQLite连接只针对新复制的DB+WAL工作快照。

### 具体优先证伪点：Attention前置Q/K RMSNorm归约

已将R0_BLOCK变化绑定到保存的Triton source/TTIR及Inductor代码：BF16输入行stride2048，256元素FP32平方和；一组从`1536 + r + 2048*x`加载，另一组从`r + 512*(x%3) + 2048*(x//3)`加载。实际AOT生成代码标注`split/view/chunk/rms_norm_default`，相邻生成query/key BF16[*,3,256]/[*,1,256]，当前QSA类声明`GemmaRMSNorm(head_dim)`。因此这是**Q/K归一化的前置归约候选，不是QSA sparse kernel的BLOCK_M=16本体，也不是TP allreduce被改回BF16**。

两种冻结配置：`XBLOCK16/R0_BLOCK32/warps4`与`XBLOCK64/R0_BLOCK64/warps16`。source明确不同FP32累加分组/树形归约，机制上可改变末位舍入并经BF16及深层前向放大；但本轮没有实际Q/K输入，未做设备或CPU反事实数值重放，不能确认该机制在doc71造成首差。示例bundle rank0/subgraph8的记录043为64/64/16、045为16/32/4，rank0/subgraph36和40相反；不能以终态同key的last-writer参数替代当时bundle，也不能简单按subgraph号当模型层号。

结论：分类为跨实例前向数值分歧；**compiler-autotune-selection为优先suspected，specific-kernel/root-cause仍unconfirmed，state-initialization unresolved**。已排除所保存输入/RNG边界漂移，未支持文件污染或同key随机误编译；不把合法舍入差异直接称bug，不将该结论外推为原GPQA低分/首NaN/60K循环根因。

## 证据与后续门禁

所有新报告/静态源码快照在D，原043/045 HTTP、PT、缓存归档、manifest未覆盖；原始脚本在CASE/commands。

| 报告 | SHA256 |
|---|---|
| `cache-report.json` | 1786277e2d746738e756f47f729c052e1ac8401af14c7a3b6a1aa46376816ef0 |
| `selection-audit-001/report.json` | 8a84e6cc7f888043c474cf5fb4cb1b2750ba3878e00b6cee7d04b6fcbfb178cc |
| `tensor-audit-001/report.json` | 8351151914b6d79c41d0ec1008d02f787728932f271dca2367db6bdb64140a29 |
| `kernel-link-audit-001/report.json` | 3d80b30b4b061bd43971a738e8ad771bab03e81fd4b7b4515824fabc5e87ed2c |
| `aot-bundle-audit-001/report.json` | 909a6322daee2926d165a87b364165ee640d987aaad5d9114601774d6ca600a8 |

`common-cache-paths.json`/`IR-after-debug-strip.json`保存全差异；`bundle-configurations.json`/`paired-AOT-autotune-changes.json`保存每rank/子图配置及CRC验证结果；`source-readback.json`保存GDN/QSA/PLE/shortconv当前源码SHA和完整字节，当前静态源码不冒充原请求实际设备state。两个只读查询的输出截断仅展示限制，完整分析JSON在D；一条kernel-link执行路径误拼未找到文件、修正路径后脚本只执行一次，没有模型或旧证据写入。

**当前离线范围完成，不再自动追加实验。** 最小下一证伪方案应先固定一份编译/调优选择，给doc71增加窄逐层末token及Q/K归约前后、实际选中config和GDN/PLE fresh-state mask/selected值取证，再以相同输入做冻结配置单变量对照。它需要新的埋点/8010重载或GPU算子验证，必须先向用户报告范围并获新方向；当前均未执行。不为补齐因果自行重跑全量GPQA。旧164/198 failed/no gate及性能阻塞保持，heartbeat仍PAUSED。
