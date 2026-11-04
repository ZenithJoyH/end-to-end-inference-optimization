# 20261102-plugin-pr-review-61 当前Plugin适配补丁PR审查与整理

- 状态：已完成实际安装代码审查、最小等价整理与三主题PR材料；提交就绪状态为`needs_revision`。分类：维护与PR准备，不声明性能优化收益。
- 目标：PPU-13 / glm5.3-flash-opt-20260911 / 8011；仅当前私有Plugin及必要依赖边界，不提交、推送或创建PR。
- 用户授权：请你基于提交plugin PR的规范整理再梳理下你的plugin代码的适配修改。
- 基线：实际安装官方main@7094141e28a2680644fc41073aa9dfdfbf1f0044，当前Plugin内容SHA478ec9fa45c35b21d078cdfdc5aae90953f6543c8135188e9ba699021ba7bbf9。

## 方向与审查依据

按docs/plugin-change-review.md及docs/plugin-development-standard-v1.md逐项复核，不为了减少文件数迁移必要边界。当前5生产+3测试共8个Plugin文件：MLA dispatch/graph/小head能力接入、纯metadata映射、KPool固定地址、OOT设备构造及thead原生MM排除。先归档当前源码/Git/index并核对目标仓库实际贡献规范、公共扩展点与相关共享调用者，再决定有证据的必要整理。

必查A1–A4/B1–B4/C1–C4/D2–D5/E1–E4/F1–F5/F7；D1无新增开关、B5/F6无新平台/CI时记不适用；G1核对现有模型支持/example，G2不向Plugin README/docs写实验报告。D3跨库公共可获取固定版本及公开API必须明确，依赖仍是本地patch则如实needs_revision，不伪造PR就绪。

## 变更与验证计划

只收敛职责一致的重复、修复确实违反契约的差异；不升级基线、不改启动脚本/MBT/RPC/模型参数、不改权重/tokenizer/vLLM，不引入平台身份分支或新开关。读取实际HEAD/工作区/index/唯一安装/镜像挂载，保存精确补丁与回退材料。若生产逻辑有变，先冻结候选和回归范围，再按minimal-regression验证实际入口、独立参考、graph与模型受影响面；若只有审查资料，不为制造新证据重复模型评测。未知和未测项单独披露。

## 正确性与性能边界

现有点60：CPU465、真实PPU metadata145/变化输入graph6、完整模型最小/FULL/C64通过；原单次GPQA164/198，用户授权全部20题统一补充后174/198=87.88%>=86%。两口径保留，没有新单次完整C64 gate；当前无新性能测量，不把历史优化收益归属当前补丁或声称全平台/完整PR验收通过。

## 外部证据

用户工作根/mnt/nfs/users/jinghao/glm5.3-flash/optimize当前规范路径相同，owner root/mode0755、剩余1390GiB；新唯一目录/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/resume-20261102-point61-plugin-pr-review。源/优化镜像相同29a6712e…，目录挂载均/mnt:/mnt:rw:rprivate，实际Plugin私有未挂载。当前服务health200空闲。后续原始diff、源码快照、测试和PR草稿均在该目录集中保存；本地仅此记录/state及总览，不建history。

准备命令执行前冻结：`commands/prepare-v1.py` SHA `6a12f1eb1f7b2387d9f105337a272801ab2f2d2af4ff4d3ceeb0fdecfa0aba13`。先保存点60`commands/point61-prepare-v1.py`，执行时独占新建点61并核验保存同SHA副本；只保存当前私有Plugin源码/Git/index、原始补丁、小型审查包和身份，不修改库/服务，不发模型请求。


## 当前审查发现与最小整理

已通过GitHub只读比较确认Plugin main仍为7094141，与实际安装基线相同；没有拉取、合并或升级。FGV main比当前9f6a0ef多1笔FLA/GDN改动，不包含本地Sparse MLA改动，不以此更新安装环境。Plugin的pyproject glm5 extra、docs/安装/CI固定FGV80a8e971，但本次H4/graph capability/SQ0兼容仍依赖9f6a0ef上的本地未提交补丁，D3尚未满足。保留真实依赖阻塞，不随便填一个不能复现的公开SHA，也不在本任务擅自提交推送算子库。

实际PR检查发现tests/unit_tests/glm5/test_model.py一项I001 import排序错误，test_cache/test_model两文件未通过ruff0.14.0格式检查；已在审查副本纠正。两个测试文件仅格式及连续import分组顺序变化，AST归一化对比完全一致，测试函数/断言数量不变。thead.yaml继承的CUDA/NVIDIA标题与实际PPU配置矛盾，改为T-Head PPU/thead，仅两行注释，解析YAML逐值相同。4个生产Python文件一字未改，未压缩必要能力/缓存/metadata边界，也未新增模型分支、平台文件、开关或依赖。

全部8个实际改动文件已按目标.pre-commit-config.yaml执行pre-commit4.3.0（ruff hook0.14.0）：merge-conflict/private-key/end-of-file/trailing-whitespace/ruff-check/ruff-format/typos全部通过；symlink/shellcheck因没有相应文件类型而not_applicable，非意外跳过硬件测试。工具均在本机临时环境，模型容器依赖未更改；日志SHA `9327643aacac1a1efb45e90ea86843d6c5925e9170f813eb56e940333689bdd2`。

执行前冻结三路径整理包`commands/review-cleanup-v1.tgz` SHA `44b2aed624aae2908fadb2a33287b52859bc8ec71e744888e0532b483f8e4d01`，manifest SHA `89a0af6c570de20baa6b4e47da2fecbf9d0dc0ae58a91578a7d8fc5e2c3c34f1`；控制命令`commands/apply-review-v1.py` SHA `6e7b4c60517b7cc6a21133164b1ca2c36bc56b12e96117ed061bd427f79a850b`，输入归档SHA `1ee89d210d6b3cdab6e179f8b4b95394b1c597fc14e16268acbe1e08d49097bc`。应用前核对精确旧源/实例/空闲、每文件旧SHA/新SHA、AST/YAML等价；保留当前HEAD/index及全部无关文件。随后在实际安装容器仅运行非GPU的GLM5单元/dispatch config/whitelist契约，独立测试DB不写生产库；以原生JUnit逐项结果和已选测试全部通过为准，不使用预估数量下限。失败只按SHA反向恢复这三文件，不停止或重启模型，不改用户其他dirty。无新增模型生成请求。


## 实际整理与验证结果

09:39:13容器中的三路径整理已完成；原生465项CPU契约全部通过、failure/error/skip均0，JUnit SHA `4a84768bbade65546aef8f8e4da058b4baa06bc3e9e9713cf3f61f51de1a4e66`，日志SHA `6f5340c05422c923c7ecc8ace3ec763f27546560c5f8652ffdd8621b277586c7`。当前Plugin内容SHA `45c95631106d3c12d22a990af82fd28f0773b420e0e3472c4d3ee07677825837`；HEAD与index、其它文件/库不变。生产Python字节不变，thead解析值不变；原服务3917036/start622443729未重启、没有生成请求，MBT/RPC/所有启动参数不变，DB前后均eda5cc0b…。

最终PR材料按顺序拆为三个主题（不是三个已经提交的commit）：

| 主题 | 文件范围与必要职责 | 提交前状态 |
|---|---|---|
| 01 metadata内存修复 | framework-owned请求/页表/物理slot转换与稳定压缩，避免完整int64临时矩阵；测试独立整数oracle和动态graph | 已整理独立补丁；独立分支CI未跑，历史PPU证据仅按同生产代码说明 |
| 02 Sparse MLA graph/KPool/OOT | 公共capability/OperatorBinding、UniformType spec、H4能力转发、builder-owned稳定地址、CUDA OOT构造与失败恢复 | needs_revision：先公开交付/锁定FGV能力API和H4实现，之后同步安装/CI/docs并验证公开安装；不混入临时平台排除 |
| 03 PPU MM临时排除 | 单独保留当前部署mm/mm_out黑名单及退出条件，修正thead标题 | needs_revision：全PPU模型/MM shape都受影响，目前仅此GLM证据，不能直接宣称为全平台默认最佳；需修算子冷调参或验证并收窄作用域/补公共追踪 |

01/02含对应测试，03为平台配置例外；三份补丁依序git apply --check与每阶段逐字节比较通过，最终8文件与实际整理副本完全一致。没有Git提交或目标index操作。当前thead的vendor注册只有attention_backend，没有flash_mla_sparse_fwd；vendor选择能力测试是mock契约，不宣称实际PPU原生Sparse MLA链路已交付或硬件通过。实际16rank选择glm5.flaggems的证据沿用同生产代码的点60。

最终完整补丁SHA `8c805deebe758307f1b370ee92ae9de4f7a48b4fa999ca76abfabd3efa053df6`，series manifest SHA `e5939ea6a8f0ee094f627ab5512b636f61a2ba9afd1c72d8660520a1c9e636b9`。拟提交PR英文正文已按最终行为写好，明确测试日期/原生范围/历史硬件/补充计分和依赖阻塞；没有将过程日志写入Plugin README/docs。

发布材料/最终核验控制命令先保存：`commands/finalize-review-v1.py` SHA `90ed8accd79291f5cb7e31c333d04b8317f0503f739086cfe88f4d56359b630c`，输入归档SHA `bc2a35161cfacd2581d831ece0a9762b61312c44ad59f2ceb60931eaae8f0f8e`。只将补丁/PR草稿落入本点pr-series，核验8文件实际SHA与前后身份，导出既有FG/FGV前置patch供审查，不修改其它库、不发模型请求、不重启服务。


## 最终当前审计与规范核对

09:52:10最终只读核验完成，`review-completion.json` SHA `b96475b0ea964648548cd664e8b67f608b7c6a49de36501f0d4c2f08c2ad01c5`；`service-final.json` SHA `a85f2eba4dcae8a1431814f4573a9d3b01522d6397cfb06822c8d9a0f4f33c67`，`runtime-final.json` SHA `95aa1df09392bccd9d34eeefbdc0a11874efd63c4012b50368be538bf88de336`。同实例3917036/start622443729健康空闲；Plugin新SHA45c95631…与实际8文件一致，HEAD/index/其它库、argv/env、权重/tokenizer/thead库、唯一安装、镜像/挂载均保持。生产DB仍eda5cc0b…，启动脚本仍8fdae3f4…；没有新生成、服务重启或源码提交。

| 规范条款 | 本次核对与结果 |
|---|---|
| A1–A4 | 纯请求metadata在Plugin；数值算子在FG/FGV；复用公共模型/dispatch，无新增平台模型执行分支；必要缓存边界保留 |
| B1–B4 | 公共binding/capability在执行前选择；执行错误直接抛出；vendor测试不冒充实际硬件实现 |
| C1–C4 | 参数/返回/无效slot契约、限域构造与失败恢复测试保留；以能力而非版本号判断 |
| D1–D2 | 未引入新开关、未保留新的临时诊断路径 |
| D3 | **待修订**：公共固定FGV依赖缺少本地H4/graph能力，先交付算子API/测试再同步锁定安装/CI/docs |
| D4–D5 | **待修订**：MM排除沿既有平台配置且有退出条件，但覆盖全PPU，需单独评审、公共问题跟踪和影响范围验证/收窄 |
| E1–E4 | builder-owned固定地址与现有流依赖保留，metadata不读写实际KV数值；没有新增跨请求全局缓存 |
| F1–F4、F7 | 原生CPU465/0失败0跳过及适用pre-commit通过；本次生产Python字节不变、配置值相同。历史PPU/graph/整模证据明确标记；未重新跑硬件/模型/GPQA/性能，未验证新公共依赖的fresh install/wheel或非PPU硬件 |
| F5 | 三主题补丁顺序应用逐文件等价通过；不是已提交commit，独立主题分支CI尚未执行 |
| B5、F6 | 没有新厂商接入/CI改动，专用条款不适用，不声称全平台验收 |
| G1–G2 | 保留既有模型支持入口；PR英文说明与测试产物在外部实验目录，不把单次试验写进Plugin README/docs |

## 交付与后续顺序

最终材料位于外部根的`pr-series/`：三份主题patch、完整`plugin-final.patch`、`series-manifest.json`、三份英文`PR-*.md`正文及README。另只读导出`prerequisite-FlagGems.patch`、`prerequisite-FlagGems-vllm.patch`，两个算子库未改。源码快照`plugin-source-git-before.tgz`保留原Git/index，可按精确SHA仅反向恢复此次两测试文件及YAML注释；不可整体覆盖用户dirty。

本轮已完成用户要求的梳理和可审查材料，当前无需继续压缩必要适配边界。正式提交前仍需：先公开交付并锁定FGV必要能力；将平台级MM部署例外独立处理并验证适用范围；再针对最终公开依赖与各主题运行独立CI/安装和相应硬件回归。没有在本任务擅自提交/推送或更换依赖。点60的原生164/198与用户授权补充174/198全部保留为历史口径；本次仅测试/注释变化，不签发新的全量gate，不宣称性能收益。

本地记录验证：六文件`git diff --check`、YAML唯一key/身份/约束/历史分数/空gate和链接核验通过。全仓记录检查存在375项其它案例既有错误，本GLM/点61相关错误0；未修改无关案例。
