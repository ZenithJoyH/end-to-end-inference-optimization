# refactor-013：12个FGV PR同步上游并解决合入冲突

用户2026-11-12在侧聊要求优先解决#1136–#1147的合入冲突。只更新这些PR的原fork分支，不合并上游PR，不修改安装源码/整改容器/服务/模型/缓存，不运行GPU任务。主聊天已确认这些分支无待推送的op006/007/008数值候选；其活动实验保持独立。

## 冻结输入及策略

- 官方main固定为`3049b821d088f5566b825bdc564120249a26181d`。
- 新私有工作区：`/private/tmp/dsv4-pr-conflicts-20261112`，原review工作区保留。
- 原12个head/branch/body/draft快照：`pr-before.json`；计划：`conflicts-plan.json`。
- 保留原历史，两父merge（第一父为原PR head，第二父为固定main），非force、expected-head lease更新，不rebase或覆盖并发修改。
- 实际三方合并的文本冲突：#1136的common gather实现与测试，#1144的`conf/ci_test_aliases.yaml`；其余10个可自动合并。
- 保留#1143已验证的common测试组织及所有PR完整性能报告；旧数据仍绑定原测量SHA，不宣称merge head重新测得性能。
- 发布前检查冲突解决语义、生产函数AST差异、Python语法、原生CI/selector/registry和适用pre-commit hooks。当前禁止GPU任务，不能把CPU检查冒充新GPU验证。

## 冲突解决

#1136保留原64位scale地址生产实现（全文与原head相同），保留共享/重排物理页、空行、offset、17GiB寻址及两次新输入graph replay原测试函数体，同时吸收上游device-agnostic参考、真实top-level dispatch和新增generic batch31用例。原两个CUDA graph测试增加后端范围标记，避免在Ascend/MThreads错误调用CUDA graph；未放宽数值断言或删除边界形状。

#1144的alias保留`paged_mqa_logits: test_mqa_logits`，不恢复上游已删除的旧`gdn_w8a16_int8`映射（上游现使用统一GDN测试文件）。其余10个三方自动合并。#1143的`tests/test_mhc_pre.py`公共测试组织和旧Ascend覆盖均保留，不恢复后端后缀文件。

## 验证与发布结果

- 全12分支Python AST解析、git whitespace/未解决index检查、原生CI selector、casefold导出顺序、导出/注册、禁止torch compute fallback检查通过。
- 每个分支原生66项`test_ci_*.py`通过，CI依赖pins检查通过；增量operators.yaml/marker/ATen-name/benchmark-reference规则返回0，原有warning不当设备验证。
- 每个PR相对固定main的改动文件运行原生pre-commit，所有适用hooks通过；没有YAML改动时check-yaml正常不适用。未以本轮增量hooks代替上游全仓CI。
- 各PR目标算子生产源码与原head保持全文相同；合并导致的`__init__.py`变化属于上游新增导出组合，已有函数AST无变化。同步main本身含其他上游生产变更，不把它说成整个环境无变化；不能未经复测更新主聊天候选/安装目录。
- GitHub create-tree结果逐一等于本地已验证tree；12个merge提交均第一父为原head，第二父为`3049b821...`，非force且原head lease匹配才更新。
- 另一次公共git fetch独立核验12远端head、两个父节点、tree等于本地、固定main为祖先且merge-tree无冲突。
- API逐一回读12个PR均open、`mergeable=true`，base均为固定main；原body（含完整性能表）与Draft状态逐字/逐值未变。#1138/#1141/#1145仍Draft，不因冲突消除宣称性能问题解决。
- GitHub 12个`rule-check`均已success；最后回读`basic ci`仍queued或in_progress，未宣称新head GPU CI或性能重新通过。本轮没有GPU任务/服务/容器/安装源码变更，也没有合并上游PR。

| PR | 原head | 新merge head |
|---|---|---|
| [#1136](https://github.com/flagos-ai/FlagGems-vllm/pull/1136) | ca791350 | 4a505b46301ef61e1cbc6a18dcc4e5ee9c6276c7 |
| [#1137](https://github.com/flagos-ai/FlagGems-vllm/pull/1137) | 3d981a54 | 345294b0941d6116cd7e9b3ccbef058bfd13c3b8 |
| [#1138](https://github.com/flagos-ai/FlagGems-vllm/pull/1138) | 3a1e9864 | c124ebc965c9bfc447d6f2adfc5dcc0c36e16d0b |
| [#1139](https://github.com/flagos-ai/FlagGems-vllm/pull/1139) | fae391b0 | 15e1c83c4fb74812a1a4936c97f1924afb364302 |
| [#1140](https://github.com/flagos-ai/FlagGems-vllm/pull/1140) | a5a7d9cb | 8b43e534ee81bbb40874ce7eaed4c0a7d111dbc5 |
| [#1141](https://github.com/flagos-ai/FlagGems-vllm/pull/1141) | e57d59ff | 6c3284cbbe9ee25bb2b17f39742b53263d43ff87 |
| [#1142](https://github.com/flagos-ai/FlagGems-vllm/pull/1142) | 51ece3f6 | 32426add4b1c6d1bc45a4e3571aefcc001f91b7c |
| [#1143](https://github.com/flagos-ai/FlagGems-vllm/pull/1143) | 9b35f751 | 03d62ddb10e5a721f38da7e04231f48a5af6d139 |
| [#1144](https://github.com/flagos-ai/FlagGems-vllm/pull/1144) | 6d033e0b | 59db18ed0d520e301aa1ae7947ec22ccb49e9537 |
| [#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145) | f8d6d629 | 570da319cdd679aaa9157c7e7c9f647130b51e8b |
| [#1146](https://github.com/flagos-ai/FlagGems-vllm/pull/1146) | 929d9d85 | f7777fbd717162b40759dcea1e38fac41f01e8cf |
| [#1147](https://github.com/flagos-ai/FlagGems-vllm/pull/1147) | d6a4acee | 76bbe5b702126e11a633af7e371e35d33fb553d8 |

## 归档及并发保护

本次独立证据包`/private/tmp/dsv4-pr-conflicts-20261112/pr-conflicts-final13.tar.gz`，249369bytes，SHA256 `a89d7358b2ad35d038c2d92d86b4a48f0802966acd01bca10b00d67c4da7fe43`。含冻结输入、解决脚本/patch、12个CPU检查日志/AST绑定、发布回执和独立远端git审计。原PR正文中的数据仍绑定旧测量source，不改分、不重新跑GPU。主聊天通过独立`state-refactor013-entry.json`串行合并共享state/README，避免覆盖其活动记录。

状态：`complete_conflicts_resolved`。后续上游新提交可能再次产生合入差异；当前结论绑定上述main/head及回读时刻。
