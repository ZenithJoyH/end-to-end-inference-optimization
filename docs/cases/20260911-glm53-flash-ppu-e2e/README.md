# 20260911-glm53-flash-ppu-e2e：GLM-5.3-Flash-BF16 / PPU 端到端优化

## 当前状态（2026-10-22，覆盖下文历史状态描述）

12:20：[点52生产路径](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261022-sparse-physical-index-fusion-52.md)原脚本/MBT不变，去除全部临时MM/vendor/观测hook，默认flagos的C64 64/64及完整最小模型/FULL回归通过，16worker无hook/TileLang，无OOM/RPC。相同新实例198题/C64/seed42/60K/86% GPQA已唯一启动，原生新UUID缓存命中0、开始实际请求；分数/gate未定，监控跟进，无新性能或提交推送。原生产DB合法调参写入已记录，未清/复制/回退；以下11:40/OFF/诊断策略为历史。

11:40：[点52索引融合修复](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261022-sparse-physical-index-fusion-52.md)已通过原C64 64/64与C1/C8、三16K边界、11/11答案、FULL捕获/多token回放；16worker实际`32768×2176`命中，未见OOM/RPC。保持MBT32768及原argv/脚本，以FGV通用融合算子消除多份全尺寸int64中间量；H4+融合源码保留，诊断服务OFF、完整及当前只读审计通过，monitor删除。首轮CPU fixture失败与精确回退保留。沿用MM07临时vendor/MM策略，仅验证该转换OOM在原C64短契约内修复，默认flagos/生产MM路径、新198题gate与稳态性能仍未验；无提交推送，不复用旧收益。

10:37：[点51 MM07终态](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-sparse-mla-small-head-dual-backend-51.md)固定shape/输入三臂数值与graph全过，原/候选/回退冷调用302.08/12.40/302.66s，仅确认冷搜索机制、不冒称稳态收益。模型通过C1/C8/16K/11答案/FULL捕获，但C64在公共物理索引转换remainder分配544MiB处OOM，16rank均报错；候选实际每worker22次限4命中，仍非充分修复。控制器恢复SQL-only/OFF且当前独立全树/index/身份/DB审计通过，候选不保留、无自动重试/GPQA/性能，终态监控删除；旧RPC唯一根因及当前峰值张量机制未完全归因。

09:40：[点51 MM06已闭环](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-sparse-mla-small-head-dual-backend-51.md)，原测试昨晚23:54结束，断网只是未取得回执。当前源码/index/唯一安装/镜像挂载及master DB审计SQL-only/OFF通过；原策略一轮C8通过、回退RPC失败，候选实际104→4命中并通过，但三臂冷shape无交集，不能报严格加速。下一07固定shape序列/输入SHA，再条件式原C64完整回归；尚无新gate/稳态性能，不保留临时策略。旧监控已暂停，下面运行/失联状态为历史。

23:36进行中：[点51 MM因果对照06](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-sparse-mla-small-head-dual-backend-51.md)真实PPU四候选×23shape的92项oracle和8次动态graph回放已通过，原P4096 C1/C8三臂唯一启动。MBT/FULL/kernel/key/生产DB不变，仅临时缩短候选搜索；同源SQL缓存、共享编译cache限制与实际shape对照在账本冻结。暂无模型修复/新gate/性能结论；已有只读monitor跟进，终态精确恢复SQL-only/OFF，不把23:04旧终态当当前试验结果。

23:04只读定位终态：[点51](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-sparse-mla-small-head-dual-backend-51.md)SQL修复保留，但C8仍约300s RPC失败。真实原生key/prune及前后只读DB差分进一步确认：不是缓存失效，19个winner/2040条候选标签正常写入；M20480已有11组、M20481/8198进入21504/9216冷bucket，每projection104候选（默认114经合法性裁剪），20个冷组中最后一组未完成。充分修复仍需同初始缓存单变量MM策略对照，另有独立do_bench协议tag风险未修复。本轮零模型/GPU请求、零库/生产DB变更，完整审计通过、服务OFF、H4未安装、monitor暂停。原C8失败/新gate/性能缺口保留，不将CPU预算推算当端到端收益；[可复用诊断卡](../../../skills/key-operator-analysis/references/operators/mm/case-index.md)。

17:11定位：[点50](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-pr454-public-path-50.md)公共Sparse MLA的H4→H64物化使SQ20172时Query/输出各1.23 GiB，有效输出仅78.8 MiB；切片仍持有大存储，源码与PR454方法一致。启动profile跳过真实attention，未覆盖额外物化，已用原生日志+源码AST/CPU-meta确认该机制；全峰值/碎片/缓存副本未完全归因，未修复/重启或重跑、无gate/性能。知识增量见MLA卡/map，不把历史BF16 vendor性能归属本公共路径。

16:53终态：[点50](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-pr454-public-path-50.md)完整最小回归虽通过，C64全量仍因TP14 Sparse MLA输出申请1.23 GiB时OOM失败，RPC超时是后续症状。原生0/198、198题全timeout，86%门槛未通过，不将服务故障解释成模型答题能力；无gate/性能晋级。当前服务已退出、8011拒绝连接，三库源码/index、唯一安装和静态身份只读审计未变；未自动重启/回退/重跑，证据冻结、monitor暂停，下一边界为公共Prefill峰值显存而非盲目叠加优化。以下16:37及此前是历史。

16:37最新：[点50公共路径修复](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-pr454-public-path-50.md)通过实际完整最小回归与独立审计。KPool稳定buffer和FG目标表缓存反射修复已在真实私有三库安装根生效，原FULL C1/C8/三16K-D8/11答案、16Worker无TileLang、唯一安装/身份/镜像挂载通过；Plugin12文件、FGV4、FG两个既有文件变动，无旧PPU模型路径/临时trace，原参数/脚本/vLLM不变。新身份198题/C64/strict>=86% GPQA已唯一派发，尚无gate/性能，不复用旧分数；旧失败、恢复及冷缓存因果限制保留。

[点50公共PR路径验证](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261021-pr454-public-path-50.md)13:56闭环：PPU仅用FlagGems/FlagGems-vllm，421相关CPU通过/4既有跳过、算子与三子图通过，实际16-rank完成11/11档decode FULL捕获、无降级；必要C8回归仍触发`_kpool_decode_update_batched_kernel`设备非法内存访问，因此公共候选未通过、不保留。旧TileLang导入、constructor与分组能力查询阻塞已有进展，不能继续把它们当当前首个故障；KPool输入/metadata/graph机制根因尚未确认。原point49两库源码/index及原FULL服务精确恢复，C1/C8、三16K边界、11答案和capture/多token回放通过，最终只读身份/唯一安装/镜像挂载及health200空闲审计通过；实际仍52项SCM、两库各1份安装。安全回退不是公共迁移完成；原参数/脚本未变，无新GPQA/gate/性能/提交推送，全部失败/恢复证据保留，监控暂停。

[点49职责边界复查](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-responsibility-preserving-dedup-49.md)已在容器实际安装Plugin完成并保留：仅共享FlagGems/reference同职责懒解析闭包，保留两端工厂/注册策略及vendor/MHC/cache/worker/processor边界，运行代码净减12行。首轮1项工厂契约失败后精确回退，修订后原失败测试及完整543 CPU通过/4既有跳过、模型C1/C8/16K三边界/11答案/FULL_DECODE_ONLY capture/多token回放、21:21最终审计通过。当前源1244047d…，原参数8011健康，两库各1份editable；未提交推送，无新完整GPQA/性能，不改绑点46旧175/198。PR既有配套依赖、非PPU/FP8/多模态硬件及当前新完整gate仍待补，本轮停止。下文为当时证据。

[点48 config/processor公共复用](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-config-processor-consolidation-48.md)已在实际安装Plugin完成：配置269→45行、处理器868→226行，运行代码净减825行，公共默认/短视频守护不变，无新增平台判断。188项新旧对照、536 CPU通过/4跳过、模型C1/C8/三档16K边界/11答案、FULL_DECODE_ONLY capture/多token回放及最终独立环境/身份审计通过，当前源1581bddf…，原参数服务健康。两库各1份安装，无新完整GPQA/性能/提交推送；175/198只属点46旧源，PR剩余配套FGV依赖及非PPU/FP8/多模态硬件/最终新gate缺口。本点结束，不自动派发新实验。

[点47正式PR审查与收敛](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-pr-review-consolidation-47.md)已直接收敛实际安装Plugin：移除无消费者旧indexer接口、重复INT8覆盖、5个透传和实验日志，runtime净减428行，SCM50→48；3文件删除可恢复。CPU511通过/4跳过、模型C1/C8/16K/11答案、FULL_DECODE_ONLY graph及最终身份审计通过，当前源471a65fb…；无新完整GPQA/性能/提交推送。正式PR仍needs_revision：FGV配套依赖、非PPU/公共FP8与多模态验证待补；下述点46的175/198不改绑到本点。

[点46共享模型/BF16缓存ABI](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-shared-model-cache-abi-46.md)已直接修改实际安装Plugin：复用PR454公共模型与cache生命周期，保留必要ABI及非等价config/processor，净减2252行。CPU498通过/4跳过，整模C1/C8、三个16K边界、11/11答案、FULL_DECODE_ONLY capture/多token回放及设备bitwise对照通过。新身份独立全量GPQA198题/C64 strict为175/198＝88.3838%≥86%，原生gate与最终身份/样本审计通过，监控暂停；8题timeout标记仅诊断、无补充替换。前五轮失败/恢复保留，无新性能测量/提交推送，非PPU/多模态硬件未验，下文为历史。

14:51最新：[点45审计与继续收敛](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-multiplatform-architecture-45.md)已直接在实际安装Plugin删除4个无语义转发文件，46→42项，净减183行；37运行/1配置/4测试，95 CPU/真实provider解析及最终只读核验通过。保留不同cache ABI的host实现和非等价config/processor，不称已最小化。服务未重启或发推理请求，参数/其他组件不变、健康，未提交推送；新磁盘版本模型/graph/gate待验证，删除可恢复。

13:41最新：[点45收敛补丁](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-multiplatform-architecture-45.md)已按用户明确要求直接应用容器实际editable Plugin，不再仅审查副本。实际目录95项CPU/新进程导入与注册通过，SCM46项，原有改动保留且删除文件可恢复。服务健康、进程/参数不变，未重装/重启/热重载/推送或发模型请求；磁盘源身份已更新，既有worker是否加载新逻辑未证明，旧模型graph/精度证据不能重新绑定。以下13:28“未安装”属此前历史。

13:28审查候选：[点45后续runtime contract收敛](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-multiplatform-architecture-45.md)消除通用注册入口T-Head特判，改用已有dispatch缓存ABI声明，移除无调用方bootstrap；95项CPU及真实元数据/重复注册检查通过。仅未安装副本，无模型构造/graph/full精度或性能验证；仍保留不同缓存ABI的host实现，其他平台真机启动和较早OpManager初始化时序未验证。实际容器、SCM45和服务未变，未提交推送。

11:18最新：按用户原生VS Code SCM审查要求，同一Plugin目录额外45项显示为“暂存的更改”；HEAD保留纯PR454，磁盘/index仍为已安装修复版，完整`a07f384`提交由快照分支保护。源码内容与服务不变、health200，无额外评测/重装/重启/推送。目录与注意事项见[点45](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-multiplatform-architecture-45.md)，以下11:11工作区干净状态为历史。

11:11后续：[点45](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-multiplatform-architecture-45.md)已按用户要求将实际安装Plugin提交为本地`a07f384`，工作分支`glm53-multiplatform-worker-fix-p45`，另保留纯PR454及冻结main基线分支，便于直接git diff。45文件差异包含累计适配/优化/测试；源码字节不变、工作区干净、运行服务不变且健康，未重装/重启或推送。FlagGems-vllm本次未提交，无新评测。

最新：[点45多平台结构修订、安装去重](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261020-multiplatform-architecture-45.md)已按用户后续授权完成。通用注册恢复公共默认实现，BF16 ABI独立算子键，真正平台特化保留vendor边界；Plugin v4与FlagGems-vllm v3各一份editable安装，13个旧私有源码目录已删除且有逐项校验的恢复归档。首轮worker进程初始化故障已最小复现、修复及实际模型回归闭环，失败/回退证据保留。116 CPU契约、10组PPU设备回归、9组graph各两回放、模型capture/C1/C8/16K边界和明确答案通过，最终独立审计通过、服务健康；不代表其他平台硬件验收。交付脚本/启动参数、vLLM/FlagGems/权重未改，无新全量GPQA gate或性能测量，未提交推送。

历史：[点44补丁收敛](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261019-minimal-patch-consolidation-44.md)曾部署并完成审计。Plugin新增内容净减702行（38→35个文件，含新增回归测试），FlagGems-vllm调参无关格式diff去除，数值kernel保持；75 CPU、41选路、graph及模型最小回归通过。现被点45替代，点43/44展开源码已归档删除，回退须恢复对应归档；点43补充171/198仍为历史，不伪造当前新分数或性能收益。

当前[点43上游迁移](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261019-upstream-migration-43.md)：官方Plugin main+PR454、官方FlagGems-vllm main及保留优化已安装到私有新副本，最小回归通过。用户授权14题统一补跑已完成并独立复验，全部14题替换、其余184题不变后171/198＝86.36%≥86%，补充口径达标；原单轮169/198失败保留、不签发新的单次全量gate。服务身份未变且健康、监控暂停，未自动继续性能优化或提交推送。保留PPU BF16兼容边界，不冒充纯净PR454 PPU验收；旧版173补充不混入新版。以下点42为此前已闭环历史。

用户要求固定MBT32768优化批次组织/晚到接纳。[点42有界Prefill合批](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261019-ready-prefill-coalescing-42.md)日志修复与真实“延后新Prefill、继续Decode”命中通过，但完整缩减三臂Mixed只+0.035879%且原生failed；Decode TTFT退化、基线/回退波动及回退漂移使guard保持incomplete。候选不保留，原服务/源码/参数恢复审计通过，monitor暂停，无新实验/完整gate/正式四场景结论。复盘将短探针命中与measured流量命中率未知分开，下一步先做frontend/IPC阶段归因，不据低spread宣称端到端成功。当前事实在模型state/总览维护，不在案例复制瞬时PID/health。

点41逐step诊断完成，16rank新trace确认前端接纳时序→异步成批/step边界接纳→含Prefill step碎片化的放大链；未证明单个算子随机失速。原参数服务已恢复健康，maxseq64/MBT32768/TP16/BF16/FULL_DECODE_ONLY/关闭前缀缓存保持，源码与交付脚本未改。此前缩减Mixed增量+5.3491%有效，Decode guard仍incomplete，正式四场景验收未完成；用户认可GPQA补充合并173/198与原生169/198分别保留，本次未签发新gate。细节与证据只维护在[点41记录](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/20261018-prefill-quantum-41.md)及[当前台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)，以下旧阶段状态为历史，不代表当前服务已停止。

## 摘要

- 执行规则：`0.18` / `2026-09-10`
- 验收范围：`diagnostic`
- 精度/性能状态：`passed` / `P1K targeted numeric gates passed; formal incomplete`
- 状态：`max_num_seqs=64 / exact-M64 Decode MoE candidate retained / P1K low-risk analysis converged / service stopped`；
  MQA 修复已提交并推送，本轮 M<=32 与 exact-M64 GEMM2 候选尚未提交或推送，
  最终四场景性能验收仍未完成。
- 目标：在 `PPU-13` 上建立可信基线，分层定位并优化 TTFT、TPOT 与吞吐，同时保持正确性、稳定性和资源边界。
- 模型/平台产物：[models/GLM-5.3-Flash-BF16/ppu](../../../models/GLM-5.3-Flash-BF16/ppu/)

## 已核验目标事实

- 模型：`/mnt/cpfs/models/GLM-5.3-Flash-BF16`，served name `glm5.3-flash`。
- 平台/Host：T-Head PPU，`PPU-13`，16×PPU-ZW810E。
- 源适配容器：`glm5.3-flash`，镜像
  `hy4-ppu07-snapshot:20260903@sha256:29a6712e24ca8e758ac8b33d3412892f0541bff108e2c057445fa671578237f6`。
- 当前运行配置：vLLM 0.24.0、BF16、TP16、max model len 80000、max seqs
  64、prefill eager、decode `FULL_DECODE_ONLY` graph。
- 初始 revision：vLLM `ee0da84a`、Plugin `db09b64a`、FlagGems `4a3cba02`、
  FlagGems-vllm `255ab560`。中间运行组合曾为 Plugin `96eb1bf`、FlagGems
  `fec9807`、FlagGems-vllm `255ab560`；该历史身份不再是最后验证实例。
- 当前已绑定交付 revision：Plugin `95b04f7`、FlagGems `9c9bff3`、
  FlagGems-vllm `f7443e7`。FlagGems clean；Plugin 和 FlagGems-vllm 保留本轮
  稳定性护栏与 M<=32/exact-M64 GEMM2 候选，为预期的未提交状态。
- exact-M64 后续 reprofile 与两个有界候选已完成；最后的 32768 token-budget
  探针已停止，8011 端口关闭且无遗留 vLLM 模型进程。

## 门禁与阻塞

- 独立优化容器：`glm5.3-flash-opt-20260911`；同镜像 ID、挂载一致性 passed，私有源码 revision 与实际 import 已验证。
- 用户已明确授权暂停源 vLLM 服务；源容器仍 running。服务退出后 16 张 PPU 均为 1 MiB、无运行进程。
- 适配项目未冻结正式性能 workload；当前先采用可复现的诊断矩阵，结果不能代表业务 SLO。
- 当前候选正式 GPQA 已完成 198 题，strict-match 为 172/198（86.87%）。用户确认门槛修正为 86% 并指示直接用该已完成结果判定，因此精度状态为 `passed`。原 wrapper 使用误写的 0.88 contract；此处记录为门槛修正后复判，不伪装为事前冻结。12 个 60K length-cap 响应作为非阻断输出健康风险保留。重复启动的 `formal-02` 已于 2026-09-11 14:55 +08:00 停止，部分产物不参与验收。

## 2026-09-18 服务中途退出

该事件是非阻断的输出健康问题，不改变 `172/198 >= 0.86` 的精度
gate。根因已确认：迁移后的 FlagGems-vllm MQA 算子仍从
`flag_gems.runtime` 取配置，使 FlagGems-vllm thead YAML 中的单个固定配置
没有生效，实际返回 144 个候选。新 shape
`M=2901,N=725,H=32,D=128` 在所有 TP rank 上同步在线 autotune，
在写入前 5 个 benchmark 结果后仍未完成，vLLM 的 300 秒 RPC 超时导致
EngineCore 和 API server 退出。同一 C8 热缓存复跑从首次约 133.87 秒降到
1.617 秒，复跑前后 DB SHA 不变，完成了单变量验证。详细证据与修复边界见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

修复将 MQA 算子的 runtime import 从 `flag_gems.runtime` 切换为
`flaggems_vllm.runtime`，并增加实际 tuner config 来源回归。完整模块测试为
`2 passed, 20 skipped`；直接算子覆盖非对齐 shape、原故障 shape、graph capture
与两次 replay，最大绝对误差不超过 `3.815e-6`。服务级用 32 请求构造总 prompt
token 精确为 2901 的批次，首次和立即复跑均 32/32 HTTP 200，复跑耗时
1.18455 秒，未再触发 MQA 多候选在线调优或 EngineCore 退出。修复证据位于远端
`diagnostics/accuracy-health-rpc-timeout-20260918-01/mqa-fix-validation-01/`；
两文件改动已提交为 `f7443e7` 并推送到
`ZenithJoyH/FlagGems-vllm: support-glm5.3-flash`，远端 HEAD 已核验；按用户要求
服务验证后保持停止。

## 初始候选原则

先核验框架中的明显浪费和工作点，再以 profiler 的真实生产 shape 决定算子替换或当前实现优化。
GLM-5.2 的 Indexer、Sparse MLA、MoE、采样与调度经验只作为候选机制，不继承其 TP16 MetaX 参数或性能数字。

## 已复现的算子慢路径

- 适配服务 FlagGems DB 的 906 张表中，892 张属于
  `_index_linearized_jit_function`；源码反查确认它对应 `aten.index.Tensor` 的
  FlagGems `index` 实现。
- 保留 thead 默认黑名单并追加 `index` 后，single 从约 131 秒降至 3.110 秒；
  C8 从两轮 8/8 在 240 秒超时恢复为 8/8 在 43.478–44.125 秒完成。
- single/C8 前后 `_index_linearized_jit_function` 表数量保持 892，运行命中记录不含
  `flag_gems.ops.index.index`，前缀缓存 query/hit 均为 0。
- 当前结论为 `reproduced`：FlagGems `index` 是该模型/平台/TP16 身份上的严重慢路径。
  正式 workload 的吞吐、TTFT、TPOT 尚未测量，不能把 sanity 改善写成最终性能收益。

完整结构化证据：[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 最新阶段状态

当前保留组合为 index 黑名单、native sparse MLA、
shape-gated native causal-conv、shape-gated vendor KDA 和
`max_num_batched_tokens=16384`，以及 shape-gated FlagGems MoE 分阶段配置。
MQA 固定配置已在运行时来源修复后生效，并通过原故障 shape 与服务级验证，
现计为生效的保留项。
`32768` 在长输出哨兵场景吞吐回退
1.523%，已拒绝并恢复 16384。最新证据排序和下一实验已合并到
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 源码提交交付

- `vllm-plugin-FL` `support-glm5.3-flash`：`85302a7` index 黑名单、
  `dbb0e67` sparse MLA、`062c06f` causal-conv、`ef19fd9` Chunk KDA、
  `96eb1bf` large-M MoE stage config。
- `FlagGems` 原 `4a3cba0` day-0 kernels 与 `fec9807` MQA 配置已完成迁移，
  当前 `master` 和 `support-glm5.3-flash` 均为最新上游 `9c9bff3`。
- 2026-09-15 已分别推送到 `ZenithJoyH/vllm-plugin-FL` 和
  `ZenithJoyH/FlagGems`；当时 `git ls-remote` 核验远端 HEAD 为 `96eb1bf` 和
  `fec9807`。Plugin 聚焦单测 7/7 通过，两个仓库 YAML 解析通过。
- 远端容器缺少 GitHub HTTPS 凭据，首次尝试未更新任何 ref；最终使用经过
  SHA-256 校验的 Git bundle 与本机 GitHub SSH 身份完成。命令证据位于远端
  `commands/push-source-branches-20260915/`。
- 2026-09-18 将 vLLM 专用 MQA 调优配置和本任务全部新增的非 ATen GLM
  serving 算子归入 `ZenithJoyH/FlagGems-vllm` 新分支
  `support-glm5.3-flash@f7443e7`。
  fork `main` 已先纯 fast-forward 到上游 `6e7ac61`，新分支领先最新主分支
  8 个提交。迁移范围包括 graph-safe BF16 MQA、BF16 cache gather、indexer
  pool、prefill tail、kpool、causal-conv/update、recurrent KDA、safe gate、
  Chunk KDA、fused-MoE launcher 和 sparse-MLA small-head 支持。Plugin 在
  `support-glm5.3-flash@95b04f7` 统一改从 `flaggems_vllm` 公共 API 延迟导入。
  最终隔离验证使用不含旧模型提交的 FlagGems `9c9bff3`；公共导出、Plugin
  import/dispatch 均通过，FlagGems-vllm 测试 23/23、Plugin 测试 11/11
  通过；20 个 MQA focused 用例仍因缺少 vLLM DeepGEMM/FP8 reference 跳过。
  最后验证实例使用与 `FlagGems-vllm@f7443e7` 内容一致的工作树；本次事件证明上述测试没有覆盖
  MQA 迁移后的 runtime tune-config 来源。
  迁移证据位于远端 `commands/migrate-flaggems-vllm-20260918/`。

MoE 候选先将 trace 分解为时间几乎各半的 GEMM1/GEMM2，再对
M=4096/12401/16384 分阶段调参。保留配置在两场景正式 A/B/R 中
使输出吞吐分别改善 2.609%/0.344%，P99 TTFT 分别降低
3.714%/4.163%，比较器判定 `passed`。结构化数值与远端证据路径见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

保留 MoE 后的 16-rank trace 显示稳定热点迁移到 sparse MLA，fused MoE
累计设备时间约下降 14.8%。native sparse MLA 来自不暴露 tile 参数的预编译
扩展；其外围索引转换使用 BN1024 后，三个主 shape 微基准虽提升
3.55x–4.54x，但两场景端到端吞吐分别为 -0.041%/-0.005%，正式比较器
判 `failed`。该实验补丁已回退，停止前实例继续使用上述 MoE 保留组合、16384
和关闭的前缀缓存。证据、反例与下一阶段排序均已并入
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

随后按 trace 前七个 shape 比较 general mm：thead 默认配置已经把 `mm`
列入 FlagGems 黑名单，停止前实例使用 native 路径。direct FlagGems 在六个
shape 上慢 17.6%–45.1%，仅 N=24 shape 持平，未达到 5% 门槛，因此未进入
服务 A/B，也没有新增代码改动。详细决策见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

## 2026-09-19 small-M Decode MoE 优化

P1K Decode trace 中 fused MoE 占设备时间 43.59%，且既有 large-M 配置
不覆盖 cached batch 32。本轮为 PPU aligned BF16、E=288、H=4096、
I=128、topk=8、1<=M<=32 的 GEMM2 增加有界配置。多 shape/多 seed
微基准中位加速 2.1424×，最低观测 1.3663×，数值和 graph
门禁均通过，落源后单测 18/18 通过。

P1024/D1024/C64/N128 targeted A/B/R 的输出吞吐中位数为
840.963 / 1004.382 / 847.618 tok/s；候选相对基线 +19.432%，
P99 TTFT 和 TPOT 分别降低 14.569% 与 16.262%，回退吞吐漂移
0.791%。三个有效角色均使用同一个冻结 FlagGems DB，SHA-256 为
`1917ccd26c170ca3d7c76197e662a862d3bfbdb1b6da064259bf2202eca38a83`，
测量期间未变且 WAL 为 0。

数值门槛已通过，但正式比较器因冻结契约要求 SLO attainment、
测量计划却未冻结 SLO 阈值而返回 `incomplete`。因此本轮只记为
P1K targeted 通过，不扩大为 formal/full 结论。获胜候选已保留在
FlagGems-vllm 工作树中，未提交、未推送；revert 服务已停止，
服务保持停止。

## 2026-09-19 后续候选、max64 分析与优化

small-M GEMM2 后的 16-rank reprofile 将 rank0 Decode 后续热点定位到
mHC pre、split-K reduction、MoE align 和 PCCL all-reduce。MoE align
source-path 虽快 3.635×，P1K 吞吐却下降 1.308%；mHC pre 虽在六个 shape
上中位快 5.528×，P1K 吞吐仍下降 0.587%，两者均已回退。精确
TP16 BF16 `[32,4096]` all-reduce 微基准也表明 PCCL 自动选择优于强制
Ring/Tree，后两者延迟分别增加 40.7%/236%。

三个连续负结果后测试 `max_num_seqs=32→64`。它使 P1K measured 吞吐中位数
从保守 max32 reference 的 1013.657 提升到 1277.797 tok/s（+26.058%），
但 P99 TPOT 从 31.281 增至 49.251 ms。用户明确将总输出吞吐设为主指标并接受
该延迟取舍，因此启动脚本已改为 max64。

max64 的 16-rank profile 解释了这个取舍：Decode step 近似设备时间从 max32 的
28.49 ms 增至 42.27 ms（+48.4%），但每步 token 数翻倍；同时 fused MoE 的
rank0 Decode device-activity 占比从 38.59% 增至 53.20%，成为首热点。针对真实
M64 baseline config 做 3-seed 扫描后，选取保持 BM32 padding 边界的 GEMM2
配置，算子中位加速 2.00306×，数值与 graph 门禁通过，聚焦测试 22/22 通过。

在同一 max64 P1K workload 上，候选 3 个 measured 轮的输出吞吐中位数为
1513.513 tok/s，相对前一版 max64 提升 18.447%，相对极差 2.687%；P99 TTFT
与 TPOT 分别改善 15.769% 与 15.561%，384/384 measured 请求成功。候选已保留、
未提交、未推送；服务已停止。

当时将 MoE align 与 mHC 视为“算子快但端到端慢”反例；该解释已被
2026-09-23 的候选 trace 纠正，具体见下文。本次 exact-M64 同时满足
live shape/config、首热点和无 profiler
服务复测，收益才得以兑现。完整数值、SHA 与远端路径见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。

保留候选的后续 16-rank reprofile 又证明 rank0 Decode marker span 相对优化前
下降 16.018%，fused-MoE 活动时长下降 30.617%，其占比从 53.20% 降到
44.12%。剩余 GEMM1 扫描的最佳中位加速仅 1.048522×，未过 1.05× 算子门槛，
没有改源码。随后基于 Mixed 的四次约 16-request admission 测试 32768 token
budget，但三轮 warmup 离散 17.771%、没有 measured 结果或 +3% 晋级信号，已拒绝，
启动脚本仍使用 16384。P1K 低风险方向因此已收敛；下一步是修正契约后的 P1K
checkpoint，再按顺序进入 P4K scenario-entry baseline/profile。

## 2026-09-23 P32K 算子筛选与 mHC/MoE align 归因

P32K Sparse MLA BH4 特化在精确 `Hq=4/Hkv=1/SKV=80000/topk=2048`
边界上未超过 vendor：主 `SQ=32768` 只有 `0.831×`，因此在服务前
回退。

mHC/MoE align 的“微基准快但端到端无收益”已完成 trace 级纠正。
mHC baseline 虽由 `reference.torch` 路由，编译服务图已执行 FlagGems
`mhc_pre_fused_kernel_hc_mult_4`，所以 isolated reference graph 不是服务的真实
分母。MoE align 的旧候选则因生产 `expert_map` 条件一次都未命中；
C32 trace 中新 kernel 为 0 次，老 stage2 仍为 2772 次。因此历史
`-1.308%` 只是 no-op 候选漂移，不是局部收益被 overlap 抵消。

本轮进一步将 MoE align 特化扩到 EP map 与 `M=64`；16 个 EP map、
4 个 shape 的有效输出精确一致，完整 align 调用加速 2.84×–3.12×。
但候选在 TP16 服务的首批 C64 请求上发生 worker 同步停滞，未通过
服务门禁，因此未进入 P32K A/B/R；两份源码曾按 SHA 恢复，8011 关闭。
2026-09-23 用户明确要求保留该修复并自行测试端到端性能，因此同一候选已按
已验证 SHA 重新装入优化容器。用户随后启动服务，P4K/P16K/P32K/P65536
三轮共 1536/1536 请求成功，服务现仍在运行。调用链复核发现本轮 align
dispatch 选中 `default.flagos`，直接调用 FlagGems 通用实现，绕开本次
FlagGems-vllm 候选入口；没有候选 kernel trace，也没有同配置 A/B/R，
因而不能将跨日期吞吐提升归因于本修复。长输入日志显示 Prefill 期间
Decode 速率急降，P65536 KV cache 曾达 99.9%，下一轮优先验证阶段调度与
KV 容量。详细数值、证据 SHA 和当前状态见
[优化事实与实验台账](../../../models/GLM-5.3-Flash-BF16/ppu/optimize/state.yml)。
