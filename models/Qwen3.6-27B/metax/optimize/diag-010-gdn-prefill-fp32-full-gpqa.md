# GDN prefill FP32：完整GPQA修复前后对照

状态：completed，修复前162/198、修复后166/198，两侧均达到80%阈值。用户明确要求每侧完整198题一轮，并授权30分钟只读监控。

## 冻结契约

使用本地 inference-accuracy-evaluation Skill / formal-gate 及 SHA 核验的原始 llmrun.py，修正版科学方括号保留的原始198题，strict-match、阈值80%、max_gen_toks50000、temperature1/top_p0.95/top_k20、并发32、harness seed42/API seed1234。两侧独立UUID缓存，原生重试参数保持不变，不重跑整轮。完整21项FlagGems白名单含gdn_prefill与attention_backend、attention开关1、无blacklist，TP2 BF16/graph64/prefixoff/8192批预算相同。

唯一主要变量为私有MetaX gdn_chunk.py/gdn_wy.py。修复前源码f23993c2，修复后使用当前已通过原容差/graph的OP007源码6ea79405；它与PR925整理版逻辑相同但源码指纹不同，本次分数不得冒充PR925整理版直接精度证据。BF16已知算子数值失败路径仅作为用户要求的模型分数参考，不晋级或保留。

## 执行与验真

唯一有界控制器 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/diag010-controller.py`，SHA `f19e3052c7fd45da5be8b8d5ee2198b5be223d3965313159ab28cd64975c8266`。先验证当前526267/1791963121.41与四仓库源码、镜像/挂载，再两次采集每侧任务来源并冻结契约；仅停止本案例18002/2、3卡精确服务，依次启用修复前和修复后两文件。各侧新双rank graph/至少两replay、固定10题C8、22权重/tokenizer文件重验、preflight后完整198。模型源8002、其他GPU、共享代码、vLLM、权重/tokenizer不变；不跑性能。

评测进程回执 `manifests/diag010-{baseline,candidate}-gpqa-process.json`；原生日志 `logs/diag010-{baseline,candidate}-formal.log`；原始结果 `results/diag010-{baseline,candidate}-gpqa`。进度 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/diag010-progress.json`。分数低于阈值仍核验已有198题/396filter行、实际来源及精确当前源码实例，不把缺run-record当成没有分数，不签低分gate，不重试整轮。有效参考分数低于80不妨碍完成用户已授权的后侧对照。

终态 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/diag010-terminal-validation.json` 对照相同doc/gold/prompt/arguments，报告净正确题数/百分点、错变对/对变错及双方仍错，按输出SHA对齐HTTP完成原因和截断；80%判定独立保留。达到80才签发核验服务绑定gate，结束保留被评测的OP007 FP32实例。单轮T1/C32差值不能区分全部采样/批调度波动，不宣称稳定因果收益。

## 监控

用户明确授权后恢复 `qwen36-metax-flash-attention-op001` 每30分钟监控，远端只读，不发模型请求、不执行finalizer、不改服务或追加评测，仅有意义进展/完成/失败通知，终态暂停。

运行回执：控制器PID335474/create1791964996.89，`manifests/diag010-process.json` SHA `65edda431bd96c3cf6fe897df88eff21c9ae4be2f0f238e899cab4c529740b24`。四份provenance完全相等且与此前契约相同，SHA `d93ae2aa8437a7821073bea903319d81bb0d654e77ffc4ee949ea299bd75219f`；原生API接口源码默认seed1234已重新核对。监控ACTIVE仅远端只读。

修复前新实例 `qwen36-fa-opt:550742:1791965086.29`，service SHA `77bf7cf8d6768ed3f4110da9eba98b53caa15c7ab47f3c042f5736ce727c6ce9`；双rank各190graph launches、96旧WY/96prefill/2880packed/960FA split与merge，两次smoke通过。正式198题尚未启动，固定10题C8在运行且cached0。

正式第一轮已启动：评测容器PID9467/create1791965580.5，进程回执SHA `ba708fbb34ed7fdda32c1489ca140589f7b487cb1eb0662868a590baaf0f8d73`。C8已核验10题/20filter行，22权重/tokenizer文件全部重验通过；原生日志确认cached0/remaining198、C32及max_gen_toks50000，启动时实际Requesting API为0/198，不能当成完成。基线contract SHA `8cfc6ffd65115a1cce96618f947e2a790b859d244ef7d114eda2c561cf644a6a`，候选contract SHA `7c2d0759d5d5dcbb2f017039bbd0f807a0f47cff2874fb7fde0eff24c26c7c30`（仅各自provenance路径差异，provenance内容SHA相同）。第二轮FP32排队，尚无两侧新分数。

只读监控（2026-10-14T08:29:52.224132+00:00）：控制器335474/1791964996.89、正式评测9467/1791965580.5、模型550742/1791965086.29的精确身份仍相等，控制器/回执SHA及现役四仓库源码均匹配，完整21白名单/attention1/无blacklist保持。真实Requesting API完成74/198，同一日志解析到75条成功HTTP响应且全部stop；tqdm与响应事件计数存在一条更新时序差，不当作终态。cached0、首次原生attempt，未发现错误信号或响应解析失败。FP32第二轮尚未产生进程回执，仍由既定控制器排队；未启动额外评测、未发模型请求、未修改远端。无最终分数/gate；监控继续ACTIVE。

只读监控（2026-10-14T08:59:44.834190+00:00）：真实Requesting API完成146/198（上次74），成功HTTP事件147条且全部stop，无错误信号/响应解析失败，仍首次原生attempt、cached0。唯一控制器335474、评测9467和模型550742的精确出生时间/回执SHA均匹配，四仓库内容SHA未漂移，完整21项FlagGems/attention1/无blacklist保持。FP32第二轮尚未产生正式进程回执，终态证据未生成；尚无两側最终分数和配对结果。监控继续ACTIVE，没有模型请求、远端修改或新增评测。

只读监控（2026-10-14T09:28:59.559747+00:00）：真实Requesting API完成195/198（上次146），已观察196条成功HTTP响应，其中191stop、5length；5条length的completion_tokens均为50000，表明即使50k预算仍有输出截断，暂不能判断这些题的正确性或改动效果。无错误信号/响应解析失败，仍首次原生attempt、cached0。唯一控制器335474、评测9467及模型550742的出生时间/回执SHA仍匹配，现役四仓库内容SHA和全21项FlagGems/attention1/无blacklist均不变。第一轮尚未结束，FP32第二轮尚无正式进程回执，终态证据尚无；不使用部分分数推算最终精度。监控继续ACTIVE，不新增请求、远端变更、性能或重评。

只读监控（2026-10-14T09:58:56.049662+00:00）：修复前终态passed，native strict162/198=81.81818%，阈值80%。独立只读重验198唯一ID、396行/strict与flex各198、12处链接内容SHA和原生结果/样本正确数相等；未执行验收脚本。终态回执 `results/diag010-baseline-validation.json` SHA `e1a7d2bb4357d6a3b24064a98252c861247f22549f40375cc9f15c4089228a46`；native result SHA `1f2892ed7f55aae9595cefbd1bd3f94c563a0eea3887dcdec3cf3f34f4b83d26`，sample SHA `91963415ef9d437a75e84acf4fc7be4f4f53e92c0acebcb966ae921a150a7f2f`。HTTP198全部SHA对齐：193stop/5length，截断doc32/64/71/90/93各50000token且均错。控制器已签发核验基线gate（SHA `9d6461d85410ced2fa1efa593a6d8bb2f3362d2663e54bd5a45abdcd05346a72`），但550742已停止，该gate仅保留历史参考，不绑定FP32当前实例，也不推翻算子最终状态的原容差失败。

控制器正常进入已批准第二轮：FP32模型 `qwen36-fa-opt:583672:1791970287.66`，service SHA `fb57b514de6caf4af91fd6b4874c74cad98c86e5823e1038063f115b9c2bde1d`，runtime SHA `d37c58dcd7ba4b20b281edad4c4e8f653dcda3e6cc98b5efe5ef523cb6617783`，源码6ea79405重新匹配。双rank各190graph launches/96preciseWY/96prefill/2880packed/960FA splitmerge，原始OP007修复路径命中；新10doc/C8/20行通过、22权重/tokenizer重验匹配。正式进程eval PID10438/create1791970779.64，receipt SHA `6af9cb9ba2f0a7f213df47a42a43de8b0d1d009a406441f1d3a613a98f14e665`。真实Requesting API完成79/198，HTTP80响应均stop，无错误信号，首次attempt/cached0。全21项FG/attention1/无blacklist不变。尚无FP32最终分数或配对收益；监控ACTIVE，远端无附加请求/修改/重评/性能。

## 最终结果与只读验真（2026-10-14T12:31:14.923439+00:00）

| 版本 | strict正确题数 | 分数 | 阈值80% | 正常stop | 50000token截断 |
|---|---:|---:|---|---:|---:|
| 修复前BF16 / f23993c2 | 162/198 | 81.81818% | passed | 193 | 5 |
| 修复后OP007 FP32 / 6ea79405 | 166/198 | 83.83838% | passed | 195 | 3 |

观察到净增4题、+2.020202个百分点；155题双方正确，11题错变对、7题对变错，25题双方错误。错变对doc IDs：18、21、32、36、86、88、93、94、121、129、164；对变错：101、126、127、145、162、179、190；双方错误：8、12、13、17、30、64、71、75、76、79、81、85、90、97、102、106、113、130、138、147、157、160、167、168、185。

修复前截断32/64/71/90/93均错；修复后截断64/71/147均错，实际completion_tokens全部50000。原截断32、93本轮变正确；64、71仍截断且错；90改为stop仍错；147本轮新截断。输出健康只作观察，不增加精度门槛、不改变198分母。

监控只读重验22处链接内容SHA、两侧各198唯一ID/396filter行（strict与flex各198）、原生指标与strict样本重计162/166相等、gate schema3/run-record schema2链接及score/threshold/service SHA相等；两侧同198题/prompt/gold/arguments与实际provenance。配置差异只有输出标记/目录/UUID缓存/run ID，service差异仅源码指纹/运行证据/实例；两文件spec确认FP32等于进入本轮前保留的OP007，其他三仓库源码相等。实时SCORE正则解析155/186等为不完整观察，正式分数只取原生198题结果和样本。

终态 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/diag010-terminal-validation.json`，SHA `dd7d90e129c7c0fd113b58015e2523ec5b0253297e1b8bce9548b9e1e7d77d07`；候选验真SHA `786b8cda0392ef51968feba7afa3d6d676f692590a5291016fcce67ef4d4c8cd`；候选原生result SHA `81854c8cc755ae7221d9c8e16fb9db6e207fb6a70e37659025776ccb1f97c724`；candidate sample SHA `81ea83ec89e3ce20ea473910a221d366621667c1c1608198c60c6bce91553b45`；candidate health SHA `feb0b1e28a47c19dd5a961e39300f3ab6f8ee474f63afe497566bfdeb54fda0f`。路径均见state中的完整引用。

候选gate `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/diag010-candidate-accuracy-gate.json`，SHA `5c7520902fd0afb11d8e30e004d464b89c279058584669ebfa2a66795c2d2201`，由既定控制器issue/check后保存；本次监控只读核对，没有重新执行gate工具。当前模型 `qwen36-fa-opt:583672:1791970287.66`，service SHA `fb57b514de6caf4af91fd6b4874c74cad98c86e5823e1038063f115b9c2bde1d`、runtime SHA `d37c58dcd7ba4b20b281edad4c4e8f653dcda3e6cc98b5efe5ef523cb6617783`、四仓库源码指纹仍匹配，完整21项FG/attention1/无blacklist，graph与freshC8已验证，FP32实例保留运行。控制器和两轮客户端已退出。

本轮单次temperature1/C32固定seed的+4题是观察值，不能全部因果归于FP32或代表稳定提升；BF16 GPQA过80也不能否认此前算子最终状态超原容差。模型数值/批调度对逐题变化的具体贡献未分离。当前score只绑定OP0076ea，不是PR925整理版86cf的直接GPQA证据；旧native50000 158/198失败及所有旧任务/30000证据保持原样。四场景性能/E2E仍incomplete，不合并历史微基准增量或宣称性能验收。

监控 `qwen36-metax-flash-attention-op001` 已在终态验真后PAUSED（工具确认）。本次heartbeat无模型请求、无远端写入/重启/重评/finalizer/性能、源8002与其他GPU任务未操作；未更新GitHub或推送。
