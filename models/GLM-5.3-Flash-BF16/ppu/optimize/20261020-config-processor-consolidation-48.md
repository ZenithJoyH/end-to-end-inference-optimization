# 20261020-config-processor-consolidation-48 配置与处理器公共实现复用

- 状态：retained，已直接修改实际安装Plugin；188项旧新对照、536 CPU通过/4跳过、整模/graph及最终独立审计通过，服务按原参数健康运行。本点结束，无提交推送。
- 分类：framework / PR 可维护性收敛，不是新性能实验；影响 Prefill 输入解释、模型配置与启动预算，Decode/graph 作为守护。
- 目标：延续 GLM-5.3-Flash-BF16 / PPU-13 / TP16 当前案例，不改变正式四场景或阈值。

## 优化方向与瓶颈依据

用户明确要求继续收敛 config / processor，复用 PR454、只保留必要差异并回归。点46共享模型收敛及点47死接口清理已完成；点47源 `471a65fb…` 实际安装，CPU511通过/4跳过及模型graph通过，但无当前源码正式gate或性能测量。点46独立175/198只属于点46源码，不改绑。

规划复盘 planning48：当前无新身份累计性能证据，Prefill/Decode/Mixed热点不能按历史数字重建。优先级为配置继承→旧schema处理器适配→整模/graph；此轮不做MBT、调度或算子实验。首个证伪是旧/新固定输入逐字段、逐tensor及抽帧/预算/提示词对照，失败停止晋级并定位或精确回退。

## 优化内容与适用边界

当前候选实际内容：旧配置269→45行，继承PR454字段、属性、序列化及HF验证；仅保留BF16 head_dim=0→常规width、旧dense前缀默认、严格layer schema与显式嵌套构造委托。旧processor868→226行，共用配置加载、归一化、patchify、tokenization、调用流程及sampler；仅保留round式geometry/像素预算、旧HF提示词展开和reference_exact取帧适配。公共composite按既有sub_configs构造子对象，公共processor增加窄的预算/geometry/子处理器工厂/提示词hook，默认仍保持PR454原行为，不增加平台分支或新环境变量。

最终5路径含4运行文件和1新测试；运行代码净减825行，含测试总净减664行，新增运行文件为0。相对PR454的SCM文件数48→51来自两个既有公共文件的hook修改和一个回归测试，不把文件数增长说成减少，也不通过合并不同语义隐藏差异。其余原有48项改动保留。当前源SHA `1581bddf26923dc072cc5cc2eb02e2f9519a7f7130384d3be7eebfe719c042eb`，index tree `c98015f180fb25dbf93f597c4985d10429c12c61`。

设计归属为模型schema适配，不是平台选择。起始旧配置269行、旧processor868行；PR454公共配置288行、processor1299行。公共实现不完全等价：显式head_dim=0、像素预算/round式resize、动态抽帧和提示词展开职责不同，故通过小型模型语义hook保留差异；公共默认行为不变，不新增thead判断或可选vendor依赖。

精确修改目标为容器唯一editable Plugin `/workspace/e2e-opt/glm53-20260911/vllm-plugin-FL-review-20261020-p45-v4`，HEAD为PR454 `f7696963c44425fdf6603054248cc8256783b4c7`，48项既有暂存更改必须保留。起始源SHA `471a65fbb08b324da77876cb754d695b486360667121963b718b9b1966bacfd6`，index tree `33a26c916b92c6d196b93169b947c4fec7db6864`。vLLM/FG/FGV、权重/tokenizer、DB/thead、启动脚本和全部服务参数不变。

## 正确性与路径命中

apply03 CPU：188/188旧新对照、无失败；包含80配置、1真实checkpoint配置/roundtrip、18图像tensor/grid、10视频tensor/grid、72抽帧、1真实工厂/预算、2文本、2图像提示词和2视频/metadata提示词。各tensor比较使用相同输入、shape/dtype和torch.equal，不调整容差。新增25项契约与原515项一并运行，共536通过/0失败/4原有跳过（117.974s）；原有公共short-video非空、placeholder不展开、离线HF缓存/参数透传等守护均通过。新增测试ruff0.14.0 lint/format通过；runtime按目标pyproject排除，不假称已lint。

model01于20:12:59 +08唯一派发并已完成：原参数重载后C1/C8、16383/16384/16385-token原文边界、11/11固定明确答案、FULL_DECODE_ONLY capture及多token回放覆盖通过。证据为`model01/candidate/{minimal,semantic,final-audit}.json`和`model01/completion.json`（SHA `62ef3876ec6dafc11d2e558470cd4009297e86296216535c2aeee192b3ee596d`）。这不是逐rank replay trace或正式GPQA，不宣称多模态整模/其他平台硬件通过。

20:18:24 +08最终只读审计passed：当前实例`PPU-13:glm5.3-flash-opt-20260911:3799058:521421211`，源码与上述CPU/模型回归一致，health200/idle；Plugin/FGV各1份editable安装，原参数/环境/权重/tokenizer/DB/thead和其他库未变。冻结镜像与当前源/优化mount parity再次验证，源码真实私有；源适配容器只读。`final-audit-v1.json` SHA `4c740cc237c8daebd005510fc36bc342b175d4247c2aee1c210ceb8ae994473d`，环境回执`environment-final-readonly.json` SHA `bc88610e899d519bc218af42fc20f0b8841d256a8130b766fb3ae22d05c37849`。

使用本地 inference-accuracy-evaluation 的 minimal-regression：旧新配置构造、真实checkpoint配置、序列化/重载；图像/视频像素和grid、尺寸边界、抽帧、时间戳、混合提示词和文本输入；已有公共配置/processor/预算与dispatch CPU套件；整模C1/C8、16383/16384/16385、11项明确答案、FULL_DECODE_ONLY capture与至少两次多token回放。CPU/mock不能替代非PPU/多模态硬件验证。若输入或数值语义变化则触发完整GPQA，不以最小回归签发gate。

## 性能效果

未运行性能测试，不声称端到端收益；代码精简与行为回归不替代同配置A/B/R。

## 决定、风险与回退

保留已验证的apply03候选，本轮任务结束，不自动叠加优化或派发GPQA。前两轮失败及精确恢复全部保留，定位问题`p48-config-processor-parity`已在原188+540范围和整模/graph闭环。此轮为输入与配置行为对齐的低风险重构，未改变算子/数值与原服务参数；正式性能或最终交付前仍须为当前源重新做完整GPQA，不改绑点46的175/198，也不以最小回归签发gate。PR仍needs_revision：配套FGV依赖及非PPU/公共FP8/多模态整模硬件验证未补齐。

精确受影响路径恢复归档`apply03/affected-before.tar.gz` SHA `b4a1b982f93218b0c2b63b812149d2aaa3849a22e8e2fda673f006e6a7a0ffd9`，配合`index-before.bin`；只在当前内容匹配且无用户接管时恢复本次5路径，保留其他dirty。整库相对PR454最终补丁`apply03/final-vs-PR454.patch` SHA `62095726c48e28c231e682856c79b7cfb765b22e9f226a1f814dd80714caabe0`。未提交、推送、创建PR或修改启动脚本，仍可在同一容器目录用VS Code暂存区审查。

## 外部证据

远端唯一任务根（已核验并创建，准备回执`prepared.json`）：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261020-point48-config-processor`。下文为版本化执行与失败/修复记录，不再派发旧命令。

准备命令 `commands/prepare-v1.py`，SHA `04627c8a5a0e466093b9f2adc0c5b53e6ec5ae5709f24bc72df7eabcbd80732b`。首次引导副本放在父根 `prepare-point48-config-processor-v1.py`（不覆盖），命令只读核对点47原身份、空闲、health和路径权限/空间后创建唯一根，并将自身保存到上述commands；不改源码或服务。

已准备首版5路径补丁（4运行+1测试），306增加/998删除，尚未据此宣布回归通过。执行顺序为精确备份→直接修改安装源码→旧新CPU语义对照→原515项及新增契约测试，任一失败恢复本次路径/index且不重启服务。命令：`commands/apply-v1.py` SHA `73c7fa220e66b9e4a79a4e6d9f4c31f4e4f46456cd18468c5bc6d1e9fca7ef3a`；旧新对照 `commands/parity-v1.py` SHA `a51a056884dfcd3f1b705bc0af00290ca599e72eceafa2f94635303f5fd09968`；补丁 `commands/config-processor-v1.patch` SHA `cd07debf4ac5c4030750b75fca91722603c73fa4f5a563fdc31306d79509dc3e`；manifest SHA `6f1b149c245eaa6ffb11ef04ffea72938faa3982299239fffefd289117058f00`。旧源参考从安装前实际两文件保存到本点reference，只用于外部测试，不引入库依赖。

实际checkpoint的processor_config当前为token预算格式、patch_expand_factor=1，旧适配仍按其class像素默认解释，不能误以为文档中的旧size schema就是当前文件。新工厂保留该既有解释，并逐项对照当前真实checkpoint；不改变权重旁文件。

首版传输包 `commands-v1.tar.gz` SHA `89c273a9c5a46f9748c727da417f7f7ec11ad25f1d1497706240fa0e4ee27816`；只接受上列4个regular文件及SHA，不接受AppleDouble、符号链接、重复/绝对/父路径。提取到未存在的commands文件后执行已核验apply命令。

首轮apply01：旧新对照168通过/20项失败，未进入整模或完整CPU套件；源码/index已精确恢复为点47 `471a65fb…`，服务未重启且health200。失败分布：1个真实checkpoint嵌套配置roundtrip、9个抽帧边界、10个视频harness调用。触发精度定位`p48-config-processor-parity`，保留全部失败；不放宽比较或删掉慢/失败样本。

隔离诊断命令 `commands/diagnose-v1.py` SHA `6d8c774b42ac38538f4c5ab40bb673b6bc22e7a458869cb6f5c2ebd2939c0a10`，只在CPU进程内加载冻结旧/新配置，复现sampler与旧视频调用，输出`diagnosis-v1.json`；不改安装源码/模型参数、不发模型请求。

诊断已复现：未显式__init__的配置子类在当前Transformers中得到生成构造函数，真实text_config/vision_config仍是dict；显式super委托是必要兼容，不复制公共字段。旧抽帧extract_t允许0，且timestamp为index*(1/fps)，与公共legacy helper的min2及index/fps在24fps/30秒边界不同，样例第10帧41≠40；修复公共legacy helper对齐原reference，不复制sampler，公共fps_interval默认分支不改。10个视频失败在旧实现也因harness绕过标准化传list给缓存函数触发；改为标准tuple而非放宽tensor比较。

apply02保留原188个对照样例和全部515既有测试，加上新增契约及上述边界。5路径325增加/1002删除。新命令 `commands/apply-v2.py` SHA `a06a662d033764edec3584c9b6309b1413826cf5900a59f230432883affdb29f`，对照`parity-v2.py` SHA `818bbc2b9182ff3196e52a9fd37fdf63f5dc412032d385805b4558bd5bf8e14e`，补丁`config-processor-v2.patch` SHA `d5048cd4234f97bf3cd34333a651f96bd5f9a5e51460112310344c4673b22393`，manifest SHA `ec3cd8dc189e72d103c32ee00c001c0a699e990412aece6018275fd87a6c51cb`，包`commands-v2.tar.gz` SHA `04cf945a0d47e26dde44f6b079bdc032392f3928e928df2d958cab580d926c32`。

模型控制命令提前保存为`commands/model-control-v1.py` SHA `4b2336216dac870044ba70d7845b86717c1062f9af95d1e8374777e92ba67ef9`，CPU全部通过前不得派发；仅精确目标原参数重载，固定C1/C8/三个16K边界/11答案与graph审计。失败恢复apply02受影响路径/index和原参数实例并做回归，不更改交付脚本或其他dirty。

apply02：188/188旧新对照通过；完整540项CPU为531通过/5失败/4跳过（119.06s），已再次精确回退、服务未重启。三项失败是非法配置由HF StrictDataclass异常包装，需在委托前保留原ValueError校验；一项是公共duck-typed调用harness不提供新可选hook，应保留原公共行为；一项公共预采样短视频要求非空，本轮不能全局改变其legacy helper默认值。因此不修改已有测试或缩小范围，改为适配层显式选择reference_exact（0帧及乘倒数），公共legacy默认clamp/division与fps_interval均保留。配置用共享签名解析参数一次，前置旧schema校验，复用公共字段和序列化。

apply03仍为相同188对照+540项CPU。五路径344增加/1008删除。命令`commands/apply-v3.py` SHA `f79829495459b5e3ed211bcde410a95957e79c9b4ee81557eb49dcc34a079cba`，`parity-v3.py` SHA `c697f78c1309fc31f760c9bd90399acf706e71e1bb662ce06b5496a78e0d13d0`，`config-processor-v3.patch` SHA `43085d28868ee2e824a6923e926eb6479061ee787d78376a5b1d258475d58600`，manifest SHA `44bfc81d4ae595fab6622eb0356d7033db4e8d169a1ae95e73a5443f5edeb48f`，传输包SHA `f359157f52186a5343471661053bf0b3221bad51794d9bf5e869f09ed87ea909`。模型命令升级为`commands/model-control-v2.py` SHA `e453dd3639aa072de0443897a179b4020da2cf6983545ab63977b7429eeeb01e`，增加停止前精确PID/start_ticks接管检查，改绑apply03；旧v1不得派发。只读最终审计`commands/final-audit-v1.py` SHA `f9a15e149dc30bd8648d0eb64374aa96e374dc80088748fb11aff54f8306e3fb`。

精度Skill显式模式minimal-regression，bundle SHA `6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`；最初bundle检查漏传selection返回incomplete、随后显式模式重新冻结，不影响测试范围或阈值。

最终只读审计扩展命令`commands/final-audit-v2.py` SHA `5d15eac09cd335fcc4d5afac821a519e39c0e8847e0bf0bc0c54fdc67188fb72`，在model01完成后核对冻结image、当前源/优化容器规范化mount parity、两个editable根真实私有目录，再调用已保存v1进行源码/index/唯一安装/当前模型身份及CPU/188项回执复核；只新增证据，不发推理请求或改容器。
