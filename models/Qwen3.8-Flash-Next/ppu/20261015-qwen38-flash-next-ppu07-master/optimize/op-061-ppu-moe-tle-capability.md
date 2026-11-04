# op-061：PPU MoE alignment TLE能力门禁

## 范围与授权

用户2026-10-21“那你来调整下吧”，承接perf060已证实的PPU不支持`tle.distributed_barrier`却重复编译失败回退问题。仅改FlagGems的MoE alignment实现选择；不重启8010、不访问8035/物理0–7、不改vLLM/Plugin/数学/调优/采样，不启动新benchmark、GPU单测或GPQA，不提交推送。既有perf060 final恢复仍在执行，不能改其冻结源或冒充该旧实例已加载候选。

分类：`operator/improve`（去除该算子已知不支持路径的重复编译成本）。父场景`p1024-d1024-c64-n128`，性能尚未测量。精度流程`minimal-regression`，本轮只完成CPU dispatch/结构契约部分；GPU数值/边界/graph及模型回归待授权、资源门禁和加载候选后验证，状态不先记passed。

## 设计与证据

- 当前库`/opt/qwen38-flaggems-master-20261019-f0aa7f12`，HEAD`f0aa7f12180cea4776a2aba3f3889b8fb82a28b1`，包含原QSA/GDN/PLE适配及i64/randn修改，必须完整保留。原算子SHA`a2308bb7aaba53427ae7dcadf9002c1976fe160b33a1c00d0f3540f51f51386d`，该文件原本clean。完整其他仓库/引擎/模型指纹复用并重新核验perf060 `source-facts.json`、`container-boundary.json`与实际Git状态。
- 旧证据`perf-060.../attempt-003-warm8/diagnosis-existing-001/analysis.json` SHA`e7c68178...`；真实旧IR经CPU parse/PPU拒绝函数确认distributed_barrier不支持。18个source-only缓存目录、r8仍重写，无成功kernel cache。
- 复用FlagGems现有`runtime.device.vendor_name`，仅在alignment的TLE选择条件排除已知缺该能力的`thead` backend。保持`HAS_TLE`的版本/import含义，保留其他TLE使用及非PPU原路径，不新增用户开关、能力框架或模型名/机器名判断。不改四阶段kernel字节，不扩大异常捕获，不把未知错误缓存为永久不支持。
- 目标PPU不再先试cooperative/cluster；直接走原四阶段fallback。非目标vendor、HAS_TLE=False、非CUDA及expert边界仍遵循原逻辑。无新增设备查询、同步或全局运行状态。

## 隔离与执行计划（变更前冻结）

远端任务根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/operators/op-061-ppu-moe-tle-capability-20261021`。候选真实副本：`/opt/qwen38-op061-tle-capability-20261021/FlagGems`；不切安装/启动路径、不改旧源、不改原cache。先核镜像/mount_parity、私有目录不被挂载覆盖、旧源SHA/工作区及空间，再排他创建新目录并复制源（不复制.git和缓存）；只覆盖候选的算子及原`tests/test_moe_align_block_size.py`两份文件，差异需机器核验。回退只需不采用该候选；当前服务无需回退动作。

本地可编辑副本`/private/tmp/qwen38-op061.UfPh8t`，源文件由只读tar复制；使用apply_patch编辑。远端执行前保存候选、patch、命令和SHA于本任务`commands/`/`patches/`。测试复用原测试文件，CPU contract使用真实函数AST＋隔离依赖，模拟vendor/CUDA/TLE/专家上限和失败fallback；明确是mock dispatch，不当GPU数值。静态证明原四阶段kernel字节/AST和非目标分支不变，校验完整原依赖及安装Git未变。任何失败保留产物，不切服务绕过验证。

## 结果

本地候选已完成：仅`runtime.device`导入及TLE分支`vendor_name != "thead"`门禁，原文件其他AST完全一致，四阶段kernel与数值路径不改。原测试文件新增参数化CPU dispatch测试，不另建上游测试文件。

本地CPU真实函数AST＋依赖mock 7组通过（每组连续两次），覆盖PPU512/1024专家、非PPU原TLE成功/失败fallback、无TLE、非CUDA、1025专家边界；不是GPU数值或全平台通过。初版外部harness的mock属性清理错误已在本地修正并重验，未改模型或内核绕过。生产SHA`34f4acc92e4ea4c0bfffee7779802fd7f101bc864436352a79447e9b09858ba7`、测试SHA`f215709b597321464c6518b26b0d96ec42131bce2836228015bcc4c00a76c21b`。

远端变更命令在执行前保存于本地`/private/tmp/qwen38-op061.UfPh8t/deploy-isolated.py`，SHA`be9ba3bc66c32309b248864cedc67e197644d0b3688de93170511db93b214fba`；CPU contract SHA`6f925e8957a22596e570c31eceedcb72161e34c07d3a5b04492644a0fa70485a`，生产patch SHA`e00cad47f7c0751a273058eedd1693e9de5d7aaf1ab1bd1f0149e358012bc5b0`，测试patch SHA`a29a5f1db8b6ebfec6c36be401924b5c57c896ab5fa467bd012644bb570199ed`。先在核owner/空间/规范目录后排他创建上述远端根/commands，再tar `--keep-old-files`上传到commands（含候选、原baseline文件、patch与CPU脚本）；唯一执行`PYTHONDONTWRITEBYTECODE=1 python3 <root>/commands/deploy-isolated.py`。脚本核源SHA/旧perf060完整sourcefacts、镜像/挂载、候选路径为未挂载私有目录、原HEAD/工作区，复制完整原有效FlagGems（不复制.git/cache）到候选，只有算子及原测试两文件允许差异；CPU重验并保存排他receipt，最后重核活动源/安装Git不变。不安装、不切PYTHONPATH、不访问任何别的服务。已有候选/receipt则拒绝，不重复覆盖。

GPU数值/graph/模型最小回归：not_run，整体minimal-regression仍incomplete。无新性能测量或gate，`pr_readiness=experimental`。black/isort/flake8在本地和目标容器均不可用，本轮未联网安装，完整上游格式/CI未执行；语法/AST/whitespace检查单独记录。

## 容器隔离候选准备完成

`PREPARED.json` SHA`28e39602aa1f3844e63a1b7b02ab322f5a8f9e6877b4fcf06239a416241c69d9`。候选位于`/opt/qwen38-op061-tle-capability-20261021/FlagGems`，完整原有效仓库文件复制并机器核验只有上述算子/原测试文件两处差异；源、原工作区Git、安装绑定及其全部i64/randn/QSA/GDN/PLE适配均未变。容器镜像/挂载与原verified证据相符，候选路径为未挂载私有目录，远端任务父目录规范/owner UID0/mode0755，余空间约6539GiB。

`candidate-source-facts.json` SHA`e468eccbd801024dac839a8a89a1392b8f1b31d882c64ed4b9b22b99d2d98e7f`，保存源branch/HEAD/既有脏工作区和原/候选完整文件SHA。容器CPU再次执行同一7组dispatch contract通过，结果SHA`af6943c811d5975163711a33238fbd4e25d6e487afa64117657113fbde0d5663`；原四阶段及其他函数AST未变。0模型请求/0GPU测试/0服务动作，未提交推送。

当前8010是perf060原final FP32实例API979238/start528613221，健康且原10条smoke已自然完成；它使用旧Gems，**没有加载本候选**。原perf060终态CPU审计/暂停监控另记在perf060文档，不是本候选的模型验证。下一步若采用候选须先说明切换导入及8010重载范围，完成实际GPU数值/边界、capture与至少两次replay、模型C1/C8，再按同契约B/C/R测Prefill/Decode/Mixed；未获本轮重载/推理授权前不执行。当前决定：候选准备完成、运行晋级`incomplete`，不宣称性能问题已修复。

本地记录检查：YAML解析/唯一experiment_id、候选/测试语法及`git diff --check`通过；项目全局`check-project-records.py`因其他既有案例缺字段/链接及未迁移过程产物返回失败，本任务当前case无匹配错误。不修改无关案例或扩大清理范围，不把全局检查称通过。

## 用户继续授权：一次8010重载与最小回归（执行前冻结）

用户“请继续吧”承接前述候选加载/GPU与模型验证方案。仅对8010执行一次SIGTERM自然排空及一次候选启动，绝不访问8035及物理0–7，不安装或改动原共享源码，不提交推送。2026-10-21当前只读预检确认API979238/start528613221/argvSHA c146e2da，health200/running0/waiting0，原source与Git未变；connectivity-check仅PPU-07 passed。

新产物`<本实验远端根>/model-regression-001`排他创建。先完全排空8010所属树并检查8–15空闲，再物理8进行受控算子正确性：M=0/1/64/128/8065、E=10/250/512、block=16/64、int32 topk10、分散/集中两种输入，共60项；复用原测试CPU reference与专家内token multiset比较（专家内部顺序不属契约），核expert ID/count、索引哨兵和分配canary。M1/64/8065、E512/B16各capture一次和三次changed-input replay，9项核验。保存全部输入/actual/reference/canary PT及SHA；micro进程将两种TLE入口换为拒绝调用guard，仅用于证明实际GPU测试不先尝试不支持编译，不修改源文件或服务对象。第一次失败保存现场，停止后续阶段，不自动恢复或补跑。

GPU通过后只启动一次8010：原完整argv不变，沿用原pin047无模型埋点bootstrap、FP32/i64/randn/QSA M16/PLE051/normal_及index_select黑名单。仅PYTHONPATH追加私有Gems/src，使候选优先于原editable绑定；每阶段独立新cache，不清旧cache，原安装/Git不变。两类native capture各7/7后发送2C1 doc2（原sampling/seed/stop不变、max2048、返回完整token/prompt），两条完整token一致且原生FULL实际dispatch>=2才发8条doc2/C8。总10新请求、C<=8、0重试/隐藏预热；这与前轮perf060短doc2护栏相同，不是198题GPQA或困难题完整回归。不新增性能测量、正式gate或逐层logits/state采集。

执行入口先保存到`commands/model-control.py` SHA`39a05145b14b3b7b9662b6dc829974f3817d47a36825555e3a34496a99b27f39`、`commands/gpu-validation.py` SHA`9c38e9f010ad60e519f16bf28084c7e23472e72dc8d04b413754efec827e6b11`；只执行一次`python3 commands/model-control.py --mode prepare`（不动服务），核冻结回执后只执行一次`--mode launch`。原控制器自行stop→GPU→start→C1→graph→C8，已有DRIVER_LAUNCH则拒绝重复。异常不重复启动、不force kill；如GPU阶段失败，8010可能保持停止，需报告并等待方向。未获额外权限不自动恢复。终态原rawHTTP、完整token、算子PT、日志前缀与manifest保留，实际源/模型/tokenizer/服务身份前后核验；graph指标不是逐rank独立kernel trace，候选CPU/launch继承证据也不冒充worker函数对象采集。整体仍待执行，不提前记passed。

### 首失败：零token直接算子边界，已停止晋级

唯一driver3241114/start528972237，`GPU_FIRST_ERROR.json`原时刻1792573908.2283657（2026-10-21 17:11:48+08）。原8010所属树17:11:39自然排空。GPU矩阵第一项M0/E10/B16/topk10在stage1前端编译报`arange's end argument must be greater than the start argument`，实际为`tl.arange(0, tokens_per_thread)`且tokens_per_thread=0。0项GPU数值通过、0graph、0模型请求、0候选服务启动；没有非法访存证据，不是模型reasoning/精度异常。已及时通知用户，未改冻结契约/marker、未跳过M0续跑，也不自动恢复。

driver已退出，8010无listener，物理8–15均空闲；原安装/source/Git检查未变。完整首错trace、输入/未执行输出与canary保存`model-regression-001/GPU_FIRST_ERROR.json`、`gpu-first-error.pt`（4537bytes，SHA`1dcfc8932603f78a4073203f333475d7f0b102b814ff00eb9f3378e134a8185c`），终态manifest21项原件SHA全部核对通过（SHA`c391e9da062f298873d16194fe22b85c1ee70de892e0b4adbaa62ed34b97398a`）。SERVICE_START_ATTEMPT/RUN_STARTED均不存在，原10条请求未执行。

失败后仅CPU审计/复制编译产物，执行前保存`commands/failure-cpu-audit.py` SHA`40e061514eb6f07ba45d5db89dc10634ce8745626abe3c9044a6718f33bb4345`。计划核原/候选stage1与tokens_per_thread参数计算AST、当前Triton纯CPU next_power_of_2(0)、首PT可加载性，排他复制现有micro-cache/相关compiler文件至`failure-cpu-audit-001`。不重跑GPU、不发请求、不重启、不修改任何源；已有目录拒绝重复。此前临时只读shell内联检查的引号丢失导致CPU SyntaxError，未执行数值或变更；改用保存脚本避免转义，不当作模型错误。最小回归整体incomplete（空边界编译失败阻断），停止性能晋级，依据精度定位Skill区分继承边界与新候选回归，等待用户方向。

### CPU终态审计完成与结论边界

上述保存脚本唯一执行成功，未初始化CUDA。原/候选stage1 AST SHA均`fd455869962273d0eacf101f1c73e19f2f2cf0b9b60e7b07c8222b701fde12e4`，tokens_per_thread计算同为`next_power_of_2(ceil_div(numel,num_experts))`、无零输入guard；实际安装Triton纯CPU调用`next_power_of_2(0)==0`。结合首错误明确当前空输入前端拒绝机制，不是GPU非法访问。原版没有另行GPU重跑，生产caller是否允许/过滤空输入尚未确认，因此不能称新TLE门禁造成回归，也不擅自把空输入从冻结矩阵删除后声称通过。

CPU可读取完整首PT（input shape0×10/三个output及canary）；7份审计文件SHA全通过，已复制唯一失败编译`.source`、原/候选源码与3份实际compiler源。`failure-cpu-audit-001/summary.json` SHA`e0c953ea45a5c1d4a84a637f7acc5956d92d6768c0a55a092490cfd59053257f`、manifest SHA`5bbfeebf23a5f9f21097854e94f8989da3f76dbbb7243a06d6ad219be56e4ff1`、AUDIT_FINISHED SHA`5633ac16120a1f0e1acff17705cbd21dfc378ae32e3ee4154ba5b583662c1459`。没有wire回复/token是因为0模型请求，而非取证缺失；无GPU数值/graph/实际服务candidate路径或性能验证。仅补冻已有产物，没有改源/隐藏重试。

最终状态：`incomplete/blocked`，first-error已保全，8010停止且0次候选启动；原FP32/i64/QSA M16/PLE等源码仍保留，8035未访问。原30分钟monitor一直PAUSED，本轮短失败未重新启用，不会后台重试。下一步先核空输入ABI再选择修复边界或有证据地收紧调用契约，然后另行冻结受控续跑；未经用户方向不恢复8010、不重跑全量GPQA。精度Skill bundle SHA`6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`，operation=minimal-regression。知识差量refined：版本级HAS_TLE不等于PPU barrier能力；禁用无效TLE后原fallback仍须独立验证空输入，不能用CPU dispatch通过替代设备数值/graph通过。

## 用户授权补齐零边界后受控续跑（v2执行前冻结）

用户“请继续”明确承接上条补齐空输入后继续原验证的提议。只在新的真实私有副本`/opt/qwen38-op061-empty-fix-20261021/FlagGems`修正三处launch extent：`next_power_of_2(max(1, ceil_div(...)))`，分别对应topk输入、sorted输出与expert输出。无kernel函数改动、无额外设备同步/填充/分支；所有正extent参数逐值保持，0extent取1后由原mask屏蔽。原TLE门禁保留。生产算子SHA`a0ac9a7e1d7417fecc639765f2c74b08941b6497adbc8b2d41bcdd60293e0959`、测试SHA`16541193ca18ae1d73c5ff8a711b11a00711f2358767417d104709038670b030`。v1源码与整个model-regression-001原始失败不变，不覆盖旧facts/marker。

只读核验当前8010无listener、8–15空闲、原安装/source/Git未变。实际vLLM原生`moe_align_block_size.py:74–90`在topk.numel<E时把分配容量收紧为`min(numel*block, full_capacity)`，故M0的sorted/expert输出确实为零长度，不能只修tokens_per_thread。三处正几何clamp覆盖这一ABI；原vLLM不改。容器无可执行rg（只读退出126），改用精确目录Python源码读取，不当算子/模型故障。

本地真实函数AST与mock 7组dispatch（各两次）通过；去掉TLE guard与三处clamp后，整个生产模块AST与原始完全相同。24606组正/零几何CPU比较通过，当前next_power_of_2(0)语义已纠正到harness；不是GPU通过。上游测试复用原文件，原accuracy参数加入M0，另加4组compact零长度buffer测试，无新上游测试文件。

新运行目录`<本实验远端根>/model-regression-002`，不再发SIGTERM、不追旧PID：确认8010仍停止及旧driver退出后，先GPU原60项＋4项compact空buffer＋4项compact M1=68项，M0 compact B16/B64与M1compact/M64/M8065 B16共5次capture、各3次replay=15项。空graph每次先毒化post_pad=-777再replay，必须实际写回0；非空graph更换输入。CPU oracle复用原测试full reference，只比较调用者实际分配的expert前缀及有效token multiset，不因合法compact分配更改数学。保留全部PT/canary/SHA；首次异常停止，不改marker或扩范围重试。

GPU通过后只启动8010一次，保留完整原argv/FP32/i64/randn/QSA M16/PLE051/黑名单/pin047；Gems绑定仅为候选PYTHONPATH，旧安装和Git不改。模型仍严格10条短doc2、2C1＋8C8、max2048、原采样/seed/stop和完整HTTP/token，0重试/隐藏预热。两类capture7/7、两C1完整token相等及native FULL>=2后才C8。无全量GPQA/新性能/8035访问/提交推送。候选来源、模型/tokenizer/weights元数据/native wrapper及导入继承绑定与局限同v1；没有新增模型埋点或完整state/logits采集。

执行前保存于`commands/empty-v2/`：`prepare-v2.py` SHA`71f3f291b4da813ec999128e34f95dd9f64eda8f51659f2d7d68be6bbbbbcf67`（排他复制v1、只替换两文件、CPU重验并核v1/原源/首错未变），`cpu-contract-v2.py` SHA`c838b8345442c9f59b354e6f19e8c082a9e5fc05aae76690ad48d7bdd62f986d`，`gpu-validation-v2.py` SHA`543e5b1b077518562ca50fa2667b59114e8e0a68b08deb2040511485a41da66c`，`model-control-v2.py` SHA`6e114e6c658dd4cb2f461de1aee58d33466535f7472b41f30d4bc5fe823476ad`。唯一顺序：prepare-v2→model-control-v2 --mode prepare（不启动）→核PREPARED→--mode launch一次。新R/cache均排他，任何失败保留、不二次自动启动。该授权是修复后新验证，绝不改写第一次失败为通过。

### v2 GPU数值/边界与graph通过，唯一8010启动进行中

容器v2准备/CPU重验成功，source facts SHA`3ad8c862a8188bacfb9f9a0e58ea34efa041228e4b3b409330e479862dbabac9`，CPU结果SHA`ef3deb3d9684f6374ba9a7ea418cf48c65e5dc759e1da21a670d8486888bed51`。原v1完整源/首错/原安装和Git未变，v2仍只有算子与原测试文件两处差异；未改vLLM/其他依赖。

唯一driver3595907/start529059992/argvSHA`74a95fa79722da047ec4288e1558b3b87c8d2ef647e71a5fffb5ff08e48bb45c`。GPU于17:26:43+08自然完成68项direct＋15项replay（5capture各3次），全部通过原reference expert ID/count、有效token multiset与canary；83份原PT保存R下，包含第一次失败同M0/E10/B16及compact零长度输出，micro TLE入口guard无触发。没有改kernel或oracle绕过首错。17:26:44仅一次SERVICE_START_ATTEMPT与LAUNCHED，dockerexec3619546/start529063121；此后不得再调用controller任何mode。新API最终身份等待READY，不把docker PID当API。

当前模型加载/编译中，0模型HTTP，尚无READY、没有模型capture/replay通过结论。新requests SHA`1df622711549cc93b17aa702f004fb8c02189c124d6ccb28b047c886ffb56427`、launch SHA`af122beba013e00940b1b0c6de682edb3deafce44e5eac912908516705bcccad`已冻结。运行时只监控已有driver；原30分钟heartbeat已用产品工具更新到op061v2并确认ACTIVE，通知偏好仍仅完成/失败/明显停滞或需用户处理，正常进展安静；旧perf060终态/配置不重跑。

终态CPU-only审计脚本已执行前保存`commands/empty-v2/terminal-audit-v2.py` SHA`ea8a7f1e18a90fbfa3af4eedcbe9e8b36c28818f680f87330a3e210ff5b410f3`。只有原driver退出/僵尸、FINISHED passed与FINAL_SUMMARY/manifest齐全且无FIRST_ANOMALY/DRIVER_ERROR时，才可唯一执行`python3 <上述绝对命令路径>`；它拒绝已存在`R/cpu-audit-001`，仅CPU读取83PT/原raw/token及manifest、核10请求与两C1/graph/源/服务绑定、复制终态日志前缀和索引当前编译source，不发推理/GPU或服务动作。已有报告只读，失败不自动改模型或重试。若模型阶段异常，则只保全既有证据，不能硬套通过前提的审计。异步监控按本节SHA/身份和已有产物继续，不得追加请求。即使整体局部通过也无新formal gate/性能结论。

17:33:46+08交接只读核验：原driver3595907仍S态/精确start与argv未变；83份GPU PT SHA逐份核验全通过，GPU_FINISHED SHA`d019edfd22bf3f9c7ba486c02254bc0896859f15b29b7f03d62d6de8af130265`。当前8010尚无listener/READY/模型response，不能称恢复健康或精度通过。服务日志已17:32:13记录torch.compile完成224.85s（rank0），仍有启动后续工作；shm60秒提示不独自判停滞。新服务唯一启动已用，监控仅等原controller，不重复任何mode。后续由同一ACTIVE heartbeat继续读该R及终态审计；无明确进度依据不估ETA。YAML解析/唯一实验ID及git diff --check通过；无新公共评测代码修改，不声称全项目既有记录审计通过。

## v2终态：算子边界、graph与10请求最小回归通过

2026-10-21 18:00:17+08，原controller自然生成FINISHED并退出，未重试。READY于17:51:12签发，新8010 API3619570/start529063124/argvSHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`，原argv不变；PIECEWISE/FULL均7/7，两C1后native FULL=958（>=2），终态累计1652，native FULL8行证明本轮实际C8执行。此统计不是独立逐rank回调。10个seq全部HTTP200/非空final/finishstop/think-end248069/EOS248046，无真实HTTP失败、空final、max2048截断或日志非法访问/RPC错误；没有模型逐层NaN检查，不能由日志无NaN扩大结论。两C1完整token序列相同，各570、thinkend位置367；C8按seq2..9为514/518/518/441/441/441/441/441，均诊断答案B=gold B（10次同一doc2，不是10唯一题/正式分数）。所有prompt321 tokens一致，终态服务prompt计数3210/generation4895与原10份响应匹配；running0/waiting0/preemptions0，health200。

模型/source-before/after、原安装Git及v1首错未变。v2候选经本轮PYTHONPATH加载，不是覆盖全局editable安装；i64/randn、FP32、QSA M16、PLE i64+CTA、normal_/index_select与固定调优保持。未访问8035/物理0–7，未全量GPQA/性能/提交推送。原v1失败仍为失败，其marker/PT/source审计不改写；现在只将修复后的v2范围记`minimal-regression=passed`。没有新正式精度gate，原acc017 gate不绑定本次重启及Gems源码，更不能声称60K或原性能波动已修复。

唯一预存terminal-audit-v2.py执行成功，未初始化CUDA、未发GPU或模型请求；83份PT逐份SHA及CPU加载/canary、原raw请求响应SHA/prompt/完整token-usage、C1序列、5组各3次replay、source/8010身份通过。CPU审计11份冻结文件SHA全部核验。产物根`<本实验远端根>/model-regression-002`，重点为`FINAL_SUMMARY.json`、`FINISHED.json`、`manifest.json`、`cpu-audit-001/summary.json`及其manifest；服务持续运行，日志副本是明确终态前缀，不称永久实时完整日志。

关键SHA：R/READY `68bc93a6223ed7ddb76412404a29a303bff2f40f82f064719d750005fd29f1c5`；FINAL_SUMMARY `3cb58b089f09dba236b07658c72b6a641ba92150b35da8300de0b17dbac4c61f`；FINISHED `144293be16624b3b9107726a7dc6ba3032c86b63d4d0081f0fbe75f471ea253e`；原冻结manifest `c214197082b4ef879f2b0141d1b94e1f4242e420d0381e92df2e21adaba3ecef`；CPU报告 `6831ea2a5c02097314820700f1744903f1b286449461c2706ae71304d436c2b3`；CPU manifest `b12c8dede9a05eaf4abd4db4f30ea8b70b1e2f0c29f37aa02737f9f8500e6ce2`；AUDIT_FINISHED `7ee57c13a2b24fb53268d92343adc530a3abba702bb6d129e4afbd7862070510`。R/PREPARED `e0c3957e15e540db3baf07b45138f5794591796f8b816d21d7c94660c7d3d70d`，E/V2_PREPARED `bbda40a612d3a7162f7388cace09cf3b96b6a95f83f49d3ee94730922c53813a`。

原CPU审计的`compile-source-index.json`已索引3000份source SHA，但fallback分类误用Python `def`而实际为MLIR，故其fallback=0不作未命中证据，也不改原审计。额外只读按`tt.func public @moe_align_block_size_stage*`核验，实际为19份四阶段source（stage1/2/3/4分别8/1/4/6），均有v2私有源码路径loc，未见alignment TLE字串。它证明本模型cache编译来源，不是逐rank逐步kernel执行trace，且本轮有限短请求未覆盖性能case大M的时序或收益。为补冻这19个cache目录中的现有MLIR/metadata/binary，执行前保存`commands/empty-v2/compile-alignment-audit-v2.py` SHA`7f1f89dce88e0ccfb23a8d0cbbcec8c9ef78b01fb26f24afa8061809e3001e82`；仅CPU核原index SHA并复制既有文件至新`R/compile-alignment-audit-001`，上限256MiB/拒绝重复，不调用GPU/编译器/服务，不重跑原审计、不修改原产物。若补冻失败，只记缺失，不改模型或自动重试。

监控已用产品工具确认PAUSED，8010保留健康运行，等待用户下一范围。下一步如要判断重复不支持编译与波动是否消除，须另行冻结同契约Prefill/Decode/Mixed性能对照；本heartbeat不自行重测、扩请求或重新启动服务。`pr_readiness=experimental`（上游native pytest/格式CI及非PPU硬件未跑）。

MLIR补冻唯一执行成功：`compile-alignment-audit-001`保存19个当前alignment cache目录、152份原编译文件（864363bytes），加summary共153项manifest逐份SHA通过；原11文件CPU审计未改。补充summary SHA`2c11be28c9a41c6781b9e5a00e4c77f7204a2d37f09d84f638f22e1a28864148`、manifest SHA`27e4e61c56b59221821ce9d695d90965919ff45b39cbb377cedd4c840200f56c`、AUDIT_FINISHED SHA`700760ce4bd75c1b325b6009fe7a1e1bb4c8bc11e71dd1d9d748a8c1b22fab8b`；原3000份source索引SHA`60aae8b28222dffcb2a9361aefc4e64f9776f323bae9d427a8d6c2dc0f857e90`。仅复制既有MLIR/metadata/binary、0GPU/推理/服务动作。末次只读重核同API3619570/start529063124健康空闲、prompt3210/generation4895未增加、source-before完全相同。状态/YAML/唯一experiment_id与git diff --check通过；正式精度/性能not_run、未测项与首失败保留，当前候选只在已授权局部范围通过。
