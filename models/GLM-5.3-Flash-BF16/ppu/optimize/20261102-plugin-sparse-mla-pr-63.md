# 点63 Plugin Sparse MLA正式PR提交

用户明确授权：把Plugin代码也提交一个PR，并写清依赖当前FGV PR合入。状态：准备独立审查分支/验证；不修改生产源码、用户dirty/index或服务，不改MBT/参数，不发模型请求。

目标PPU-13/glm5.3-flash-opt-20260911/8011；原实例3917036/start622443729，Plugin45c95631…/FGVd6cbf04f…保持。独立PR副本基于官方main7094141e28a2680644fc41073aa9dfdfbf1f0044，复用点61顺序校验的metadata、graph/KPool/OOT两份补丁，排除平台级MM临时部署例外。8个安装差异中7个源码/测试进入核心主题，额外只更新必要的现有依赖文档。

## 依赖与提交边界

依赖[FlagGems-vllm #1044](https://github.com/flagos-ai/FlagGems-vllm/pull/1044)，当前公开head7dac5f76e085e2b6a860f7a80bb413d92ce39ff5仍Draft未合入、两项算子形状性能未过0.9，不能伪造完成。只读compare确认Plugin当前共享pin80a8e971与该head分叉（ahead20/behind14），不能直接换共享pin而撤掉既有多平台能力。保留现有pyproject/CI/安装/docs pin，PR明确禁止在1044合入且得到同时包含现有portability修复和新能力的公共固定版本、同步更新所有pin并回归前合并。仅以Draft交付审查，不添加私有/浮动分支或伪造merge SHA。

## 验证计划与规范

按Plugin A1–G2及plugin-change-review审查；metadata归框架，数值算子仍在FGV，既有公共dispatch/provider能力接入，KPool稳定workspace，原OOT构造限域恢复。新增注释/日志英文、版权与实际pre-commit。最终候选7文件与点61实际生产适配逐字节匹配，MM配置不进入PR，不凭mock冒称真实vendor MLA。先独立副本运行原生CPU GLM/dispatch/whitelist和PPU145 metadata/变化输入sentinel graph，再构建wheel核对内容及固定版本formatter。验证使用未安装的Plugin副本及点62已验证FGV1044文件副本；保留SQL/MNNVL runtime上下文，不能冒充fresh公共安装或新模型gate。当前服务持续原参数健康空闲，无新GPQA/E2E收益。

全部执行命令、补丁、测试和发布回执保存批准远端新唯一目录resume-20261102-point63-plugin-pr，本地仅单一md/state/README。依赖与未测项写入PR，不上传私有路径/模型样本/原始日志，不关闭旧PR572或修改其它用户分支。

执行前冻结`commands/validate-v1.py` SHA `dee2687fd62dad1f25b46feb8a6ff2465222931179f22147dd0a857591147011`，bundle SHA `9f8a31a14432c58896dc3a9282fe20a14e3838b1f363803ebbfb541041a7921a`：首次创建未安装Plugin副本，覆盖PR8文件与上游未修改thead配置（确认排除MM变更），依赖点62精确1044源码副本。CPU+安装器契约按原生实际数量检查，GPU仅metadata145和6次新输入graph，不运行模型；每阶段健康空闲、单PPU0和独立测试DB，构建wheel不安装。失败保留并停止，不自动重跑或改源。

正式[Draft Plugin PR #669](https://github.com/flagos-ai/vllm-plugin-FL/pull/669)已提交，head5a9f55936a1745231416b78624fcc9209c1c2e78，8文件/1提交；正文与现有集成文档均明确依赖1044合入及公共组合pin收敛。CPU477、PPU153（145映射+8既有真实indexer）全部通过/0skip，3capture/6变化输入回放、wheel内容核验通过。Hosted CI41381030133因Draft跳过lint/build/discover而ci-gate failure，不是数值用例执行失败，也不伪造绿色；CLA success；保留Draft/不改CI。最终只读/归档命令`commands/finalize-v1.py` SHA `0e56f8788e4c6e6d8af8ee3e3271739e47fe3fbfca0703b52b3bfee3af6f8211`，submission-artifacts SHA `9d9fadbd6eaea29abee75116819feb2f562ed3f8dfa5afa266aa1c1651fda34e`，无新模型请求或部署。

## 已发布的最终补丁与依赖

正式[Plugin Draft PR #669](https://github.com/flagos-ai/vllm-plugin-FL/pull/669)，分支`ZenithJoyH:glm53-sparse-mla-graph-20261102`，head`5a9f55936a1745231416b78624fcc9209c1c2e78`、base`7094141e28a2680644fc41073aa9dfdfbf1f0044`，1提交/8文件/+821−81。tree`97e542cd2e337a510f175227e807754a953e20aa`，patch SHA`5bfa23d7fb143d404f105c87329eb968f7cab196dca2fe6ca21558f072c52682`；上传的每个Git blob与检查副本一致。

4生产文件负责：①框架纯metadata固定1024扫描/物理slot稳定压缩；②公共Sparse MLA provider binding、head/graph capability与UniformType中自身未压缩cache spec；③KPool builder-owned有界稳定slot mapping；④既有临时构造patch对CUDA设备OOT生效、保留reference排除与原子回滚。3个既有测试文件补完整契约，1个既有集成文档说明依赖。没有另建PPU模型执行路径、复制Attention数值kernel或新增平台文件/开关。临时平台MM排除未提交；生产容器仍保留原部署配置。

PR及文档明确：先合入FGV1044、处理其已披露性能限制，再选择同时保留原portability能力和新API的公共固定commit，同步pyproject extra、公共CI安装器与安装文档并验证。现有80a8e971与1044分支分叉，未用后者直接替换全平台pin；也未伪造合入SHA/使用浮动或私有分支。#572旧广泛适配PR及其它分支没有修改/关闭。

## 原生验证

| 检查 | 结果及边界 |
|---|---|
| CPU | 477passed、0failure/error/skip，含原GLM单元契约、dispatch config/whitelist及12项安装器契约；JUnit SHA`e969530686514997f7ae7c98747037ffe1adacc4b709caf4a0618f5fe5c639c4` |
| PPU | 153passed、0failure/error/skip；145metadata边界（108基本组合+32混合dtype/page size+空页面/3graph/非法契约）及8项既有真实indexer decode/pool容量用例，PPU本轮选中BF16，不声称FP8所有分支通过；JUnit SHA`ac22c526c5cc9f2dc863718e55d5dd828d97d6788c0aa27590ac04801ae659bf` |
| graph | 3capture/6次变化输入回放；更新页表/index、两个输出先填sentinel，再与独立CPU整数oracle逐位比较；不是全模型graph验收 |
| 工程 | 适用pre-commit、额外4生产文件Ruff check/format、AST/whitespace通过；wheel构建成功，4生产源码逐字节匹配、thead.yaml仍上游原始SHAa60a6ae8…，未安装；wheel SHA`eca93d3aa0ebf0a0049fc24aa9f8fb9cea48f920a1d2905d9ca651f81d486077` |
| 运行组合 | 未安装Plugin副本+点62精确1044算子文件；原runtime SQL/MNNVL/ATen补丁仍在测试上下文，不能说fresh完整公共安装通过 |
| Hosted CI | [run41381030133](https://github.com/flagos-ai/vllm-plugin-FL/actions/runs/41381030133)为failure；Draft使lint/build/discover及平台job skipped，汇总ci-gate要求success而报错。已读job125071680481原始日志确认，不是数值用例运行失败；CLA success，CodeScan skipped。未改CI或为变绿解除依赖阻塞Draft |
| 未运行 | 不发模型endpoint请求、不重启服务、不跑新整模/GPQA/E2E或非PPU硬件；历史整模/分数不当成本PR gate |

设备用例数量由实际JUnit核验，不以预估145为通过门槛或丢弃额外用例。原始CPU/设备日志、XML、构建、源码manifest、补丁、PR正文/回执均保存在点63外部根；本项目仅本md/state/README，不建history。运行中DB/源/参数/实例前后相同，未覆盖用户dirty/index。

## 规范复核

A1–A4：request/page/slot metadata在框架，KV数值与Attention在FGV；公共模型复用。B1–B4/C1–C4：统一binding/policy、执行前capability、cache写后错误不重试、限域构造失败回滚。D1–D5：无新开关/平台默认值；跨仓依赖仍为D3合并前阻塞，Draft明示，MM例外独立。E1–E4：builder-owned固定容量buffer、地址生命周期及current stream，无全局跨请求缓冲。F1–F4/F7：CPU真实契约、独立PPU整数oracle与新输入sentinel graph、格式/构建与英文声明；未测如实披露。F5：只交付当前核心集成，不继承旧分支广泛改动。B5/F6无新厂商或CI代码变动，Draft汇总失败不改门禁。G1/G2：既有模型入口不重复注册，只更新必要依赖长期文档，试验数据只在PR和当前项目。

提交完成并不代表可合并；`pr_readiness=Draft_dependency_pin_and_public_install_pending`。未自动安装候选、切换依赖或继续性能优化；生产与点60历史精度口径保持。

## 最终当前只读审计

11:10:07审计闭环：原实例`PPU-13:glm5.3-flash-opt-20260911:3917036:622443729`健康空闲，原三库/engine源码、用户index、argv/env、权重/tokenizer/thead/安装及DB保持；MBT32768/TP16/BF16/FULL/RPC300和原脚本保持，无源码部署/重启/模型请求。生产Plugin仍45c95631…、FGV仍d6cbf04f…，本PR未部署。DB仍eda5cc0b…；未给新PR绑定历史164或补充174/198分数。

终态`completion.json` SHA `764079c557a272f40a0786daf9945437db48f48214dca51b67046ac23ee41ce7`；原生验证回执SHA `de214fdfbb4c7c5870f0ca0fc808ae7cf8e39e975a0e1fb8be71a4330232cc35`；wheel校验SHA `3a5441cecc919598976ed64b3838edcf22630fe4d80065e05b2264751d6f03f0`。最终service manifest SHA `78379306d3be84893dbb488cbd779056a928feb3e7db53f812953a69bde60621`，runtime SHA `6044eeb1514910cd7cf9292212e0331aa5ce51159d2559a0b13bc71bf2c78163`。本地YAML唯一key/当前身份、PR链接/依赖、原生数量、Draft CI真实状态、历史分数/空gate、文档空白与索引检查通过。
