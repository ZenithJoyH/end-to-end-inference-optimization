# 点47：正式PR视角审查与无调用ABI收敛

- 状态：已保留实际安装目录的收敛，CPU511通过/4跳过、模型/graph及最终只读审计通过；正式PR状态仍为needs_revision。分类framework/工程收敛，无新性能实验。范围仅PPU-13优化容器，基于PR454 `f7696963c44425fdf6603054248cc8256783b4c7`。当前源SHA `471a65fbb08b324da77876cb754d695b486360667121963b718b9b1966bacfd6`，差异50→48项，运行代码净减428行；未提交推送。

## 优化方向与瓶颈依据

用户要求从正式PR角度整体review并尽量收敛。重点是必要调用链、非目标行为、默认配置、依赖和测试，不以简单减少文件数把平台逻辑塞回公共模型。点46已完成独立GPQA175/198与模型graph，只证明其精确源身份；本点变更不能冒用该gate。

## 优化内容与适用边界

审查50路径，归类为共享模型/cache扩展、BF16模型配置/多模态兼容、dispatch/reference与vendor实现、平台策略和测试。当前发现：

1. 旧`bf16_indexer_cache_write/decode`在公共indexer复用后无模型调用，仍注册FlagGems/reference/vendor接口及YAML，扩大无用API与维护面。应删除完整旧接口及仅服务它们的实现，改用真实仍使用的BF16 top-k等接口测试，不删除有效错误传播/懒导入护栏。
2. 新增独立INT8 wrapper强制调用FGV，重复PR454现有量化入口并绕过其`VLLM_FL_USE_FLAGGEMS_VLLM`选择。当前目标为BF16且无该调用需求，收敛回公共注册/选择；不改量化算法。
3. sparse-indexer若干函数仅透传FGV，注册可直接引用已选择的同一公开函数；保留真正变换dtype/签名/layout的adapter。
4. 实验KDA shape日志和开关不应进入正式PR；保留模型作用域、幂等与metadata数值实现。

保留必要BF16缓存固定地址/物理槽位ABI、模型工厂与懒导入、worker生命周期修复，不将点46已证明必要的cache层删回危险旧路径。config/processor与PR454存在真实head_dim零值和视频采样/预算差异，未证明等价前不机械替换。非PPU、公共FP8与多模态真机未测。FGV迁移符号仍需配套上游变更，外部PPU native二进制依赖必须说明，不能宣称只合Plugin就可复现。

### 整体PR审查结论

| 范围 | 决定与理由 | 验证/剩余边界 |
|---|---|---|
| 旧独立BF16 indexer读写/Decode接口 | 删除两实现文件、三后端注册、vendor包装与YAML；只有注册/测试引用，无模型消费者 | 新护栏检查不再注册旧接口；保留真实top-k错误传播与导入检查 |
| 重复INT8特殊实现 | 删除一文件/强制注册/YAML，恢复PR454公共开关 | 同时保留0/1、缺失可选库测试，避免影响其他模型选择 |
| cache/MHC/KDA/MLA必要ABI | 保留dtype/layout/签名及worker初始化边界，去掉5个透传函数、直接引用相同FGV函数 | 保持use_flaggems_op旧alias与mutating-op单实现策略；本点模型graph已通过 |
| 公共模型与KV hook扩展 | 保留点46工厂/可覆写边界和owned patch，默认FP8工厂及原provider仍在 | 不按厂商切模型；非目标平台CPU/mock不是硬件通过 |
| config/processor/VLM | 暂保留。head_dim=0解释、Transformers层类型验证、视频采样/像素预算与公共实现并非简单别名 | 多模态真机未验，不为降低文件数静默改变训练侧语义；后续应独立收敛/验收 |
| 实验材料 | 移除KDA shape观测开关；点41/42调度器及实验控制脚本不在本Plugin提交差异中 | 无路径/题号/PID/机器身份选择kernel；过程证据留本案例远端 |
| 上游依赖与CI | 补充现有docs中的FGV扩展API和PPU外部二进制前提，新增测试按固定ruff清理 | FGV配套变更未形成可引用上游release/PR依赖，不能把仅Plugin描述为可独立复现；其他平台/FP8/多模态交给对应CI |

正式PR建议分清“BF16缓存兼容/公共复用”与“FGV算子实现/调优”的跨仓库依赖，不在Plugin复制数值kernel。当前审查基线固定为用户指定PR454，不擅自升级或声称已经验证未来main的可合并性。PPU平台级YAML还承载已验证的dispatch/ATen排除项，会作用同容器其他模型；在没有对应硬件回归前不进一步更改默认，不宣称这些配置已被所有模型证明。就正式PR而言，配套依赖落地、非目标CI及多模态配置边界仍是明确未完成项，因此保持needs_revision而非ready_for_review。

## 正确性与路径命中

最终模型/graph已通过：model01原实例对照后，仅对精确目标按原argv/环境启动新源码；C1/C8、16383/16384/16385边界原文/usage、11/11明确答案通过。FULL_DECODE_ONLY capture与多token回放覆盖通过，不宣称逐rank trace或长期稳定。当前实例`PPU-13:glm5.3-flash-opt-20260911:3777512:521192197`，`model01/completion.json` SHA `977fe175b2379865b0e27efd11be7a235512fe235df6c5fa40859a6fbd1d2015`。删除无调用接口及直接绑定相同数值provider属于本轮低风险整理，没有增加kernel/改变cache几何或算法；本轮只做minimal-regression，不重跑完整GPQA。旧175/198属于点46原源码，不能给当前471a65fb…改绑gate；正式性能/最终交付前仍须新源有效正式精度。

19:41:19 +08最终只读审计通过，`final-audit-v1.json` SHA `8815c8a07e04cbfc2aebab8b15d9aef8e81014ec6c55adc858d357114ef2ade7`：源文件/index/HEAD与CPU及模型回执一致；实际editable Plugin、FGV各只有1份安装，SCM48项可在VS Code暂存区查看，未创建commit/推送/PR。其余库、启动脚本/argv/环境、权重/tokenizer/主DB未变，health200且idle。3个删除文件可从`apply02/affected-before.tar.gz`恢复，SHA `8d93c45c32b2913b7f6eb90920e6531ed06413997995639581628615d670af88`；保留原index备份和全部既有dirty。未创建/启用新heartbeat，前台跟进至终态，旧monitor保持暂停。

apply02已实际通过完整515项：511通过、4跳过、0失败（XML117.785秒）。CPU诊断在原恢复源码独立进程复现setattr/undo污染，setenv对照无污染；同一完整范围通过后该测试隔离问题闭环。实际安装新源SHA `471a65fbb08b324da77876cb754d695b486360667121963b718b9b1966bacfd6`，index tree `33a26c916b92c6d196b93169b947c4fec7db6864`，相对纯PR454实际48项暂存差异。完整补丁`apply02/final-vs-PR454.patch` SHA `cd17e7a19651789d5e910aec637764afcea145506c7f9d19813e0bbd13beb0b9`。3文件删除有精确备份可恢复，其他dirty完整保留。model01唯一派发PID1802522/start_ticks521190410；以下“准备/待验证”是当时阶段记录，不覆盖最终结论。

apply01完整515项：508通过/3失败/4跳过（XML117.922秒），触发17路径/index精确回退，源恢复`4fd1f943…`，服务未重启/health200。失败全在随后运行的原公共环境开关测试：新增测试对模块动态`__getattr__`使用monkeypatch.setattr，undo时恢复False值为实体属性，遮蔽后续setenv('1')。属于测试隔离问题，不能当作模型精度下降；原日志/XML/回退不覆盖。调用accuracy-diagnosis，incident=`p47-CPU-dynamic-env-monkeypatch`，准备在已恢复原源码的独立CPU进程证明setattr/undo污染与setenv无污染对照，不发模型请求。

诊断命令`commands/diagnose-test-v1.py` SHA `f547e3f82b64f52e389b5938cc12eda7a44c2a537d58549d1e7ef6d9eb908f86`；v2仅把新测试两处setattr改为真实setenv，runtime补丁完全相同，不删除/放宽任何失败断言。`commands/apply-v2.py` SHA `8c2bb59864224542761fff8953018befd0c01f9b1098c988d20f73dbb3b5955c`，`pr-scope-v2.patch` SHA `dd8329610b71dd80217fc908bc884053195d8195cc58d6543b68852fe937c8cd`，manifest SHA `b2fea9c1e813b6c55de2165bd2abb485d112d317eabd1f47d89d5e31ff304830`。使用独立apply02保留原轮；模型命令v1未派发，v2仅依赖apply02通过回执，SHA `f4fef5d88926cf9a767549e2bd4bbbf44301f2b46f87dca4163b45230a5c8b5c`，同一model01尚未运行。

采用本地inference-accuracy-evaluation显式minimal-regression：修改前冻结源码/index/实际导入/实例与无用户负载，保存精确受影响路径备份；验证公共默认选择、未安装可选依赖、无旧ABI调用、异常传播、现有glm5全部CPU及新增回归。失败精确回退，不放宽断言。保留后需要目标模型graph启动/capture及至少两次replay、C1/C8和必要边界检查。若运行行为/数值路径发生实质变化，按高风险规则重新正式精度；不把175/198改绑到新源码。未测试前保持incomplete。

## 性能效果

not_run：本轮是PR scope整理，不改变MBT/调度/数值kernel，不以代码量或旧性能作为新版本端到端收益。

## 决定、风险与回退

决定retained，pr_readiness仍为needs_revision。已直接应用当前私有安装副本并完成CPU/模型/graph/最终审计；运行代码净减428行，差异50→48项（3文件删除、1已有依赖文档新增差异），其余dirty与VS Code暂存展示保持。配套FGV API尚需上游明确依赖，公共FP8/非PPU与多模态真机、最终新源完整gate/性能仍未验，不宣称正式PR可独立复现或直接合入。未提交、推送、创建PR或修改其他库/vLLM/权重/服务参数。当前点到此停止；后续收敛优先处理依赖和语义边界，不为了文件数再删除已证明必要的cache ABI。源码变化使旧完整gate仅保留为点46历史；本点验证单独记录。

## 外部证据

唯一远端根 `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261020-point47-pr-review`。命令/补丁先保存SHA再执行；原始diff、源码/index备份、测试日志及模型回归留远端，不建history或本项目script过程文件。

执行前冻结：`commands/apply-v1.py` SHA `a74caae5eeb80166aa6170837ebe8eced6a323b9e4e4ddaa2bba2a6f6150e3df`，`commands/pr-scope-v1.patch` SHA `bc0bbf4b565eb63c36ecacf1665795b657ae9b3055f09e3ea3b6a61a0897210e`，`patch-manifest.json` SHA `8dde46ec5b63c62ef6c1581cb4d9fd5a1ef7841867f58ff3213b7cb62a1056ee`。准备目录只在已批准任务父目录核对canonical/权限/空间后新建本点及commands（exist_ok=False），不覆盖旧目录。apply必须核验point46最终身份/源SHA与空闲、保存17路径/index和原完整diff；CPU失败精确恢复，不自动重启。3个删除文件均有受控备份可恢复。

本地项目CI固定ruff0.14.0安装仅在`/tmp/glm-p47-review-MZBvls/ruff`，未更改推理环境。5个本PR新增测试的ruff lint/format已通过，修复6个lint问题；运行源遵循目标仓库现有`vllm_fl/**`排除规则，没有无关全库格式化。当前delta17路径、含测试格式化614增/673删（净减59）；真正runtime删除量另统计，不将测试排版变化冒充结构收敛。

runtime真实delta13增/441删，净减428行；测试564增/213删主要为已有5测试文件CI排版和有效接口护栏替换，docs增加18行依赖说明。预期相对PR454为50→48项（删除3文件、增加1个已有文档差异），不是将代码藏到其他目录。

模型验证命令预存`commands/model-control-v1.py` SHA `e1fbfc00baad385e982b869a134153048147415659109acf608b19f27f1d41f2`：仅CPU通过且当前实例/源/index一致且空闲后，原参数重启精确目标；C1/C8、三个16K边界原文对照、11明确答案、FULL_DECODE_ONLY capture/至少两次多token回放。没有新cache/kernel算法，不重跑旧失败迭代或微基准。失败精确恢复本点17路径/index至已通过的点46源码，并恢复原参数服务和最小回归；不碰其余dirty。旧175/198不改绑，新正式性能前仍需当前源码有效gate。

终态只读审计预存`commands/final-audit-v1.py` SHA `5686e1cfc94182f2906b260187560c30a9a0bb8d46c567f759eae49c2b91b857`；只在model01原生passed后检查新实例/源码/index、其余库/参数/权重/tokenizer/DB不变、两库唯一editable安装、48项SCM、补丁/回退备份与CPU/graph证据。仅health/metrics等只读接口，无新生成请求，不重写旧gate。
