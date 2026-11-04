# op-001：PR #943 按模型拆分 TP2 MoE helpers

用户明确要求 PR #943 独立新增 `_is_qwenvl_tp2_moe_shape`，不再把E128 Qwen-VL混入已有 `_is_qwen_tp2_moe_shape`。本次仅更新该PR分支，源 head `a1570dfb367d186f9b07b7173e3b362c19dd5b8d`，base `bad340d67a35e583989fcebf56326f60edc85c9c`（含#977）。目标 fork `ZenithJoyH/FlagGems-vllm:main`，只改 `src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py`，现有test marker不变；不部署到运行容器。原文件SHA bbc2eddedc93a608a899653c5acca0b1cb4f5293436a5d6136a06401ce50e462，blob a3ea02b1828bb153e42a051b2c0a3818289f385f。

## 设计与边界

新增 `_is_qwenvl_tp2_moe_shape` 和 `_qwenvl_tp2_config`，保留完整E128/N/K/topk/dtype/C550/blockquant/int8/batch-invariant排除条件与原M分段配置。已有Qwen E256 shape/config helper恢复为上游原始函数。默认选择入口先检查独立Qwen-VL，再走原Qwen和其余原有路径，embedded配置优先级和sharedmem保护不变。只重构Python host选择层，不改Triton kernel/数学路径、public operator/API、Plugin/sampling/MoE调参值、依赖或JSON能力。按几何/能力匹配，不按模型路径/服务名匹配。

## 验证计划与发布

本地独立临时副本对旧PR与新候选执行全M配置、形状排除、E256/E512及generic fallback、embedded precedence/copy和nearest tie对照；AST证明旧Qwen helper与upstream完全一致、其他所有函数和五kernel不变，完成语法/格式/lint。原始脚本/快照/测试结果归档到 /public-flash/jinghao/qwen3-VL/20261027-flaggems-vllm-pr943-model-helpers，本地仅保存SHA与摘要。所有对照通过后向现有PR追加单文件提交并更新描述，再独立读取远端源码和diff。用户本次要求视为更新该PR授权，不新开PR或改draft状态，不改容器、不重启服务、不伪称新GPU/graph/模型分数。当前prepared，尚未发布。

## 已验证候选，待发布

新增两个Qwen-VL独立helper，原有Qwen TP2两个helper逐AST恢复到upstream bad340d。候选SHA `9de7b6eb0c366da625cb291b3be37d1fda01e8b9c346d10fb0924c12f0541746`。553360项对照全部通过：262160项E128全M配置、181440项形状/设备/量化/batch-invariant守护（含非法env的异常等价）、107520项默认配置与generic/E256/E512、2240项embedded优先级/nearest ties/返回copy。非guard对照要求两者都返回实际配置，不能用同样抛异常冒充通过。新两个shape helper互斥；E128配置body与旧分支AST完全一致，五kernel/public算子和其余函数AST不变。Black24.8.0/isort5.12.0/flake8 7.1.0按PR实际配置通过，语法/whitespace通过。未跑GPU/graph/模型精度或性能。

验证脚本SHA `ece8a407043179715520fef043ba50005766789b668de3abde595adaab645e0f`，重构脚本SHA `04373dbecf02a6f6571079ef78c6561fb6e7629203cde9cfc00a836c262adf99`，验证回执SHA `27351d6e1b9bc418a585888cb74c1380be86723ee84a617baa2a7481eeaa6f22`。归档包SHA `62c2b5cf030c738cf845bf797c16197f9a0548a8a817a83b69dd4eebfdb0cb31`，发布计划SHA `e456a439a23ba614fe86dd95e79f1bcb7e14836a15e4091a39b85ba86d074566`。发布动作仅对fork main单文件追加commit并改PR描述；先检查PR head仍为a1570dfb，并用当前content blob作写入保护。

## 发布完成与独立复核

已向fork main追加提交 `97da71f95d72941a29a5b9b256a35521115b8a2b`（parent a1570dfb），只改一个MoE文件（+62/-47），返回blob `02d02ae7d17f367a3b802a0ca64e624b40abc232`。读取远端提交的完整文件与本地候选逐字节一致；对base bad340d的PR总diff仍仅两个文件：MoE源文件和已有一行test marker。当前PR保持正式待评审（draftFalse），最终mergeableTrue。

原Qwen两helper AST与upstream相同；Qwen-VL独立shape/config函数隔离E128数据，其他函数/public算子/五kernel保持原PRAST，所有配置数值不变。553360项主机对照及仓库Black/isort/flake8/语法/whitespace检查通过。格式检查在仓库src布局并使用原.flake8配置完成；早先孤立文件运行造成的包导入分类/缺少CI配置提示已解决，没有为此改生产imports或扩大PR范围。GPU/graph/完整模型未重跑，不转移旧测量gate。没有修改或重启当前容器，因此当前容器源文件不会自动变为新PR版本。

首次PR描述更新被自动审批拒绝，理由是包含详细运行环境元数据；没有绕过。改为仅包含公开代码结构/通用验证范围、不含Host/容器/文件系统信息的描述后获准并成功更新，最终metadata重读确认。该审批事件已解决，无需用户额外授权。发布回执 /public-flash/jinghao/qwen3-VL/20261027-flaggems-vllm-pr943-model-helpers/results/publication.json SHA `3d17799e4915e073fadcafc13f78d280f5e28a76d4e26771caa0630d644453aa`。详细原始私有环境验证材料留远端，不再放入PR说明。
