# eng-071 单次8010重启／图片与视频最小回归

- 2026-10-24用户授权：仅8010重启一次，去掉language-model-only，图片／视频最小回归和实际视觉Attention来源，保存完整证据；保留BF16及现有修复，不启用encoder graph、不访问8035、不跑全量GPQA、不提交／推送。
- 模式：本地 `inference-accuracy-evaluation`，`e2e/accuracy: minimal-regression`，bundle SHA `1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`；覆盖eng069／eng070。
- 状态：原固定日志断言首错保留；经用户授权修正校验条件后，同实例完成12请求、16份真实视觉来源和独立CPU审计，`passed-minimal-scoped`。本次续行0重启／0信号，服务健康空闲。工程层验证，无性能收益或formal gate；以下执行前及首错内容保留为历史。

## 优化方向与瓶颈依据

eng070源码已经落盘但未加载；当前文本8010健康空闲，image／video真实路径尚未验证。本轮验证注册／权重／processor／视觉SDPA／MRoPE与语言模型接入，不叠加新优化。沿用同一独立优化容器 `qwen3.8-flash-opt-ppu07-20261015`，PPU-07 TP8物理8–15。

## 优化内容与适用边界

仅单次精确SIGTERM旧8010 API，自然排空其owned tree，再单次启动；旧身份Host PID2114316/start546089295/argvSHA c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010。不kill其他PID，不强杀，排空180秒失败即停，不第二次尝试或恢复。

去掉`--language-model-only`；显式保持`cudagraph_mm_encoder=false,compile_mm_encoder=false`，原语言FULL_AND_PIECEWISE及capture sizes1/2/4/8/16/32/64不变。为最小视觉启动限定每请求image/video各至多1，`size.shortest_edge=4096,longest_edge=262144,max_frames=8,fps=2`。其他模型／采样／TP／BF16／黑名单／pin047不变。私有新cache `/opt/qwen38-eng071-mm-20261024/cache`，bootstrap只包含既有pin策略及本轮来源审计，无库覆盖；不清旧cache。

素材在停止旧服务前CPU生成并解码核验：320×192非方图（左红方形、右蓝圆）；320×240 MP4、8帧、2fps（前4帧红底、后4帧蓝底）。没有从其他业务取图／视频，也无网络素材。图片与视频各2条C1，后续4图片＋4视频请求C8，共最多12次POST、0重试、无隐藏推理。原温度1/top_p.95/top_k20/min_p0/presence0/repetition1/seed1234/stop，max2048、每请求600秒。

## 正确性与路径命中

先要求新服务READY、两类语言capture各7/7、8rank三canonical源码及开关1；再发C1。保存完整请求JSON（含base64素材）、HTTP头与响应原始body、prompt／token IDs、usage、thinkend／EOS／finish、最终文字。图片应识别左侧红色，视频应红色先于蓝色；相同媒体两C1完整token序列须一致。之后核语言native FULL实际dispatch至少2，再发固定8条C8。

审计仅在每rank首次image-C1／video-C1视觉forward内部短暂启用Python profiler，捕获实际MMEncoderAttention native／SDPA、SDPA wrapper、Torch builtin及可观察到的FlagGems下层函数来源／源码SHA／调用栈／tensor元数据；原视觉forward仅执行一次，finally恢复profiler。无tensor数值读取、无数学函数实现替换／额外模型执行，encoder graph关闭。临时bootstrap不写生产源码。来源证据不是独立逐rank设备kernel trace；编译时FakeTensor等元数据如实记录，不把CPU/mock或构造日志当实际kernel命中。

审计自身CPU mechanics测试通过：返回对象identity不变、每调用原函数恰一次、重复安装幂等、profile恢复。该测试不代表设备或模型通过。

首HTTP／输出／语义／执行／源漂移停止新增阶段并冻结，在途自然收齐；不重试、不追加到通过、不修源码重启、不自动恢复文本服务。启动readiness40分钟，普通持续编译不凭shm60秒提示判死锁。失败使用精度定位Skill冻结并报告。

## 性能效果

not_run；本轮有临时Python来源观察开销，不用于任何性能结论。范围仅两种合成素材，不声称通用图片／视频精度、长视频、正式四场景或GPQA通过，不继承旧acc020 gate。

## 决定、风险与回退

唯一controller的prepare只生成素材／冻结配置／CPU取证；launch最多单次后台run。source前后、三库HEAD/index／模型元数据与权重stat绑定，终态保存原错误／manifest，留当前8010等待方向。本轮无授权二次恢复服务；失败不扩大操作。

## 外部证据与执行前命令

- E：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-071-ppu-image-video-minimal-20261024`；新建拒绝覆盖，使用既有/mnt挂载。
- 本地命令 `/private/tmp/qwen38-eng071.SWQSk2`，远端E/commands原件。
- `control.py --mode prepare` → `control.py --mode launch`（唯一启动后台run），controller SHA `ee51297177268db1fa186c6930ffa910bdfa95df9e2160e4f840b6d6f266337f`；部署包SHA `c614c7875f395c1c739c5cd62a5cc3e317b1c1781c135a6db2e9ddefb06bcb3a`。即时信号前仅比较稳定PID/start/argv身份，不将瞬时R/S进程状态误作身份漂移。
- vision_audit SHA `efcd4493317a9ff494b7bd31de73e213505b6be54d27eca49f31a3cb61f724a2`；source_probe `84c6173eef2b914bb4407d4589151312056e822eaa71ab108395069a28e106b2`；其余SHA见同一state。
- 只读preflight确认当前health200／running0／waiting0／KV0、eng070六文件原SHA一致，原始argv／白名单env和启动脚本保存在E/preflight.json；没有复制凭据或完整环境变量。

准备已成功、尚未发推理：PREPARED SHA `5d4b9241723e6d47bf79e5a70354f7e56e7a9f3271f229e03c39d4057f1e5d80`；frozen-inputs `3d55fa2ff5fee91da3cc1cbea23e41f62f6acf3fb1811141b63842d033c6cb73`；launch `9e77391bd5f45f76600ed335caaec7ec88b0468f3316d2bafeb4a4a8e2044edd`；requests `b6886efd7317fbeb93455d8b65f5d9351471271a471ae3304ddc538cc9b606b7`；source-before `7a0ace9c0c9f74f8bd80f909fbd9dcb35695a3615592ce37eef77f9c849dd335`。MP4八帧2fps解码角点RGB验证前红后蓝，素材SHA见state／assets-manifest。下一步只执行一次已冻结launch。

## 单次重启已交付：新多模态实例初始化中

唯一driver Host3894218/start552602086/argvSHA `1fee36f33f60f5b7008d1bdcdc2081eae60d89638ec90e3b2c1820408b5b082e`。旧API精确SIGTERM于epoch1792810195.7681854，owned tree于1792810197.8643386自然排空；唯一新服务启动1792810197.9170334。初期新日志确认Qwen4ExpForConditionalGeneration／BF16／TP8及无language-model-only、encoder graph与compile false／媒体界限；尚无READY或新HTTP推理，未拿旧health当新实例。只读观察原controller，不重复prepare／launch／run或追加停止重启。

长加载／编译按Skill创建30分钟只读保底heartbeat `qwen3-8-ppu07-mm-eng071`（ACTIVE），仅实质结果／首失败／明显停滞／完成／需处理通知；旧op068 monitor不变且保持暂停。新monitor不执行prepare／run／请求或恢复动作，终态停用。初次工具参数缺少destination返回invalid、未创建；补destination=thread后唯一创建成功。

## 终态：校验脚本日志断言失败，媒体回归未执行

2026-10-24 11:15:31+08（epoch1792811731.2356966），原driver在`control.py:140`断言固定字符串`Using TORCH_SDPA for T-Head vision attention`失败，退出并冻结`DRIVER_ERROR.json`、`terminal-evidence-001/`和`manifest.json`。这属于验证工具的日志前置条件／证据缺口，不是已证实的模型输出或视觉算子错误。按`inference-accuracy-diagnosis`分类为`measurement-invalid`，整体`incomplete`，不修补原controller、不重发请求或二次重启。

独立只读核验发现同一本轮原生日志10:51:34已记录`Using AttentionBackendEnum.TORCH_SDPA for MMEncoderAttention.`，因此“缺少另一条Plugin INFO”不能推导为选择了错误backend。固定措辞作为硬门禁过严是本次中止的直接原因；为何Plugin日志未输出没有运行中logger状态现场，只能列为待核，不能虚称视觉路径已失败或已实际命中。两类语言capture均7/7；无新HTTP模型请求，native FULL请求dispatch为0，**没有两次请求replay，也没有图片／视频8rank实际调用证据**。

11:17:10+08的独立检查：新API Host3895409/start552602448/argvSHA `e58dee3a67ecd27a839617e5010c2d3e37eab4d994401fec9cc406b69b4a38b2`，namespace2643933；8010 listener、完整argv与冻结expected相等，物理8–15／BF16／开关1、无language-model-only、encoder graph和compile false。health200，running0／waiting0、prompt／generated计数均0；本轮停止／启动各1次，0强杀／恢复／重试。三库、engine、metadata／tokenizer／权重stat与source-before结构完全一致，现有修复保留；模型权重非全字节重读。

CPU审计核验19冻结输入和60个原生terminal manifest成员，SHA／长度无错；driver已退出。无READY／RUN_STARTED／FINAL_SUMMARY／FINISHED，这是失败路径实际缺项，不伪造成功标记；无raw HTTP／token及视觉来源产物，因为根本未派发。CPU审计的`failed-native-execution`仅指controller异常退出，模型回归结论仍是`incomplete`，不是`failed-score`。

补充取证命令仅CPU读取既有证据、当前源码及精确8010的GET health/metrics：`terminal_audit.py`、`terminal_diagnostic.py`，输出`terminal-audit-001.json`、`terminal-diagnostic-001.json`。这四件已保存到新建且拒绝覆盖的`E/diagnostics/terminal-cpu-001/`，逐字SHA回读通过，补充manifest SHA `b6e15e1061a8044c4b335dfb848304ab4e740b65cc48ae45f3a39baad5d9ad6b`。audit脚本／报告SHA `5ed9b19a…7866`／`3d3a2561…5ceb`；diagnostic脚本／报告SHA `e51f5bad…d3f2`／`67c62bb1…bc00`，完整值见state。不改原controller／冻结输入／manifest／生产源码。日志尾部与首次错误原件保持在原terminal目录。当前服务保留健康空闲，不自动恢复文本配置。

归档工具限制已如实保留：最初远端`-c`引用被shell拒绝，未创建目录；SCP返回0但回读不存在文件，不能当传输成功。随后用保存的stdin脚本独占建目录，SSH stdin传限定四文件、`xb`拒绝覆盖并回读SHA，才判定归档完成。此过程没有模型请求或服务动作，也没有覆盖首次错误。

本轮monitor已由产品工具确认`PAUSED`。后续若获准修正验证条件，只应使用当前同一8010、保留原失败及原预算、先核绑定后继续未执行媒体请求，不需要再次重启；本轮未自动执行此续行。不能签formal gate、外推通用多模态精度／长视频或性能。

## 用户授权同实例续行：continuation-001（执行前冻结）

用户明确允许修正校验条件、沿用当前8010完成原定图片／视频回归。只更正前置证据条件：接受本轮原生`MMEncoderAttention TORCH_SDPA`选择日志，加上精确argv／源码／8rank启动来源绑定；实际媒体调用仍必须在两类C1中证明8rank真实Tensor进入native SDPA和wrapper，并核源码SHA，不用选择日志代替调用。原`control.py`、`DRIVER_ERROR.json`、60项terminal manifest和19冻结输入不改写。

续行目录为同一E下新建且拒绝覆盖的`continuation-001/`，仍属eng071，不新建模型实验。原12请求JSON逐字复制（SHA `b6886efd…06b7`），最多2图C1＋2视频C1后4图4视频C8、0重试／0隐藏请求；采样／素材／600秒预算与原契约完全不变。此前0请求，故没有重跑已完成样本。既有被动worker observer只读取原mutable phase文件并在首次媒体forward记录来源，bootstrap与生产源不修改。

初次只读取证遇堡垒机超时；重新限定PPU-07的connectivity检查ok3/changed0，`continuation-preflight-002.json`（epoch1792813312.3265688，SHA `fb41e1ee563f60e1c922cbb230be3642cb4f6a9e30296bef637d21846599dd2e`）确认同一API3895409/start552602448/argv e58dee3a…38b2、health200、running/waiting/prompt/generated均0、源完全相等及19／60项原SHA通过。首个空取证文件保留，不伪装成功或新模型错误。

执行前命令均保存在本地`/private/tmp/qwen38-eng071.SWQSk2/`：`initialize_continuation.py`仅独占建证据目录并CPU复制原request；SHA `c76f4158b4c2058e2bfcc1f97889fc938c6d2835b05caf026af7a05ee703a7c7`。通过SSH stdin限定成员、`xb`拒绝覆盖部署包；不使用SCP退出码证明成功。远端`D/commands/continue_media.py --mode prepare`仅取证冻结，`--mode launch`只启动唯一HTTP回归controller，绝不调用服务启动／停止／恢复分支。controller SHA `01b7cbb36acc4a2e670233dbed1ac3dcfeab538f9c72c4c7faa257be060d7ee6`。复用原`invoke()`函数原件，不编辑请求实现。

三项CPU契约测试已通过：无信号／重启调用且Popen仅本controller、复用原invoke与原分片、8rank来源校验拒绝FakeTensor和缺rank；不是模型或设备通过。续行运行前再次核health/源码/计数与首错，任何异常停后续阶段且不重试；终态单独冻结D原件／服务日志增量／manifest，保留当前8010。原失败目录继续保持原样，旧monitor保持暂停；短回归前台跟进，不新增长期任务。

最终部署包SHA `8e0e7603714357d64a0bbb2fb3ea2deaf9244ecccd31f2cd3558b4dd3278b720`；四件上传文件逐字SHA回读且远端3项CPU测试通过，零推理prepare成功。唯一续行driver Host1425208/start552940387/argvSHA `77c0147b2f8301d6092137406331ed1cef84d6a648d0484365e91931dfc7dc8d`，epoch1792813577.3340414交付；1792813578.8679903首次发图片seq0。当前仅监控这一个controller，不重复launch／发请求。原第一错误SHA `03d4536a5bfa16d6338da8ad44058b544142176d53d0bfe8d367196ef0607f88` 与原manifest `e55e4b4d83b4b87be3eb2134a7bed0d95d92ad178386897c93bbf487401b33f3`仍原样保留。

## 续行终态：12请求最小回归通过，实际视觉来源已确认

2026-10-24 11:54:37+08，continuation唯一controller自然退出、原生FINISHED为passed；summary SHA `123c1a8b6a45c020a0001e710880be84d4848816d574cc70d64638be3887ffae`，124项terminal manifest SHA `944491f75e54370151b803977bd563efa79bc0892985f301b3e3cbbefd517006`。第一阶段首错仍原样保留，本次更正工具证据条件后的新回执不回写旧失败。

| 范围 | 实际结果 |
|---|---|
| 图片C1两次 | 均HTTP200，最终“红色”；完整66token逐位相同 |
| 视频C1两次 | 均HTTP200，最终“先红，后蓝”；完整127token逐位相同 |
| 混合C8 | 4图＋4视频均HTTP200且语义正确；实际scheduler Running8、unpadded8/FULL累计59次 |
| 总计 | 12次HTTP尝试／12完整响应，6图＋6视频；无重试／隐藏推理／空final／2048截断／异常EOS |
| token／服务 | prompt1944／generated1140与所有原始响应usage相符；最终health200、running0／waiting0／KV0／preemptions0 |
| graph | 原语言PIECEWISE与FULL capture各7/7；C8前native FULL316，原生summary快照FULL450，晚于summary的日志另有输出，不把快照当完整终生计数；encoder graph／compile均false |
| 服务操作 | 续行0信号／0新启动／0重启；eng071总计仍仅原来1次重启 |

两种媒体各8rank（共16份）均记录真实`Tensor`、BF16、每rank2头／head_size72；首次图片query `[1,240,2,72]`，首次视频query `[1,384,2,72]`。实际Python调用链为：

`Qwen3_VisionTransformer.forward → MMEncoderAttention.forward_native → _forward_sdpa → vllm.v1.attention.ops.vit_attn_wrappers.torch_sdpa_wrapper → torch._C._nn.scaled_dot_product_attention → flag_gems.ops._scaled_dot_product_flash_attention → flag_gems.ops.attention.flash_attention_forward`。

native MMEncoderAttention SHA `eed118ad411fd3a51d151b919c7f4dabed6043715ffb30fcfe1377838a665010`，wrapper `26109136c6a3781f964b79b2de45b4c876784f2ecfb56696d4535a2cad58ecb3`；下层实际来自`/opt/FlagGems/src/flag_gems/ops/_scaled_dot_product_flash_attention.py`（`c2d06e156b9c06761bfb94a2f2718fe6cc95439d74edc09f222d12b286912e46`）及`ops/attention.py`（`d6b180e640e0e57965ef6780dc36ab2c266135d9e1cd0d8629f5860579d87a75`）。因此此处视觉入口是SDPA，下层是FlagGems通用Attention函数，不是由名字猜测FGVLLM算子或外部NVIDIA FlashAttention命中。所有来源与冻结源码SHA绑定；observer已恢复，0tensor值读取／0额外模型执行。不是逐设备kernel trace。

独立CPU审计`audit_continuation.py`（SHA `4c395131f962dc83cf52a297a731967e459b1b1081c46009faedac88db44a8bb`）已返回`passed-minimal-scoped`、errors=[]：19原冻结输入＋6续行冻结输入、60原manifest＋124续行manifest、8父级引用及12份raw／headers／完整prompt和token、16份来源全部核验。当前源／三库HEAD-index／engine／模型metadata及权重stat前后相等，BF16／全部既有修复保留。新增窗口无ERROR／Traceback／NaN／illegal memory行。CPU审计报告SHA `0742153d4db80a25cdfdda3be1b95f966d7ffb896d579e8c2c6330a058f6d111`；最终只读运行绑定报告（epoch1792814318.665123，SHA `dd089e8ef41c087523f20a51afe1148ac53097bd8f5340e4b314060ba3827dfe`）再次确认同API、health200／空闲／KV0／抢占0、完整当前源码及首错一致，晚一份native FULL快照为514。两脚本和两报告已另存D/diagnostics/terminal-cpu-001，拒绝覆盖并回读归档；不修改原native manifest。

结论仅覆盖两种固定合成媒体、C1重复与混合C8、现有语言graph和实际视觉函数来源。没有通用多模态精度／长视频／encoder graph／正式GPQA／性能结果；首图片请求有新shape编译，不计稳态性能。未访问8035、未提交或推送，monitor保持PAUSED，保留当前同一BF168010等待方向。

补充审计四件已完成远端SHA回读，D/diagnostics/terminal-cpu-001/manifest.json SHA `a7a2f76e46a6c0f0aba7c6e80c2c8a4fbb47c3f24236c78a60bc75fecf4862cd`。本地state唯一键／ID与文档链接检查、`git diff --check`通过；未运行无关全仓历史检查或任何额外设备负载。
