# pr-039：randn地址i64修复的上游Issue与PR

状态published-open-CI-checkout-network-failure-not-code-regression。用户2026-10-19明确授权直接向`flagos-ai/FlagGems`提交randn修复Issue和PR并关联。本轮仅发布已验证038补丁，**不修改/重启运行容器或8010，不访问8035，不做新GPU/推理/GPQA**。038健康服务和旧正式164/198 failed/no gate保持；当前仓库无关dirty文件不提交。

## 上游核验与发布范围

- GitHub身份ZenithJoyH；上游只读，已有fork `ZenithJoyH/FlagGems`可写。新feature分支`fix/randn-output-offset-int64`，base `flagos-ai/FlagGems:master`冻结80d30e43158d8790112e15602a4c64590c703d9c / tree69bfe02f06cf158c23d177a4d60974af4607854c，不更新fork master/support分支、不带旧模型扩展。
- 新克隆独立临时目录`/tmp/flaggems-randn-pr-UtPk0i/FlagGems`；无AGENTS.md。已读上游CONTRIBUTING、贡献测试规范、Bug/PR模板与CI约束。GitHub/Firecrawl只读核查当前源码及已有Issue/PR；generic randn旧文件与038原始文件完整SHA一致f0c89b53。
- 仅2文件：`src/flag_gems/ops/randn.py`的输出pid在乘法前扩i64（新文件SHA48d700e32c7c7a57e8414ba944d04cf56bb5c299677233716163504c89d11bd4，字节等于已设备验证版本）及`tests/test_randn.py`（SHAb7df6c0cb1c54a80150be4883892c5e6d16f05a12bee2a50da7c19ad5887f957）。AST证明RNG/其它源码字节未变。测试只调用public `flag_gems.randn`，24个小/空/尾/3dtype seed状态用例；2个BF16大N用例显式`FLAGGEMS_TEST_LARGE_RANDN=1`且>=32GiB空闲，不默认巨量分配、不建议在未修复checkout启用。
- 已有#7179是早期normal_/randn启动native stack调查，未确因，不能自动用本修复关闭该历史问题。新Issue聚焦已确认大N地址缺陷，公开shape/环境版本/安全CPU复现/038真实验证及限制，引用#7179；PR正文使用`Fixes #新Issue`，再在Issue评论链接PR。不声称原事故完美A/B或模型精度修复。
- 未上传模型权重、数据集、完整日志/cache/PT、私有部署目录、UUID/密钥；公开信息仅必要模型名、硬件类型/容量、版本、形状、代码和验证摘要（用户已允许公开模型/硬件/环境）。

## 验证与发布门禁

静态passed：AST、源码唯一表达式diff/原RNG字节相同、git diff --check、isort5.12、flake8 7.3、上游check_kernelgen_tests（无use_gems）和check_operator_markers。black26.5.1不可从当前索引获取，补充black25.1检查2文件不需格式修改；精确pinned pre-commit待CI，不掩盖工具缺失。新pytest未在当前占用设备执行，不能引用038独立算子81/18432/完整大N/graph回归作为新pytest命令通过；旧硬件证据与该待测项在PR中分别说明。

发布前读取当前branch是否冲突；在fork以冻结上游commit作parent创建只含2文件的新commit/tree/ref，不强推、不合并。创建Issue/PR各一次，未知结果先只读查重，不盲重试。PR创建成功后立即attach到当前聊天，核base/head/2changedfiles/代码SHA和`Fixes`引用，Issue评论反向引用，并读回确认。PR readiness=ready_for_review-with-explicit-hardware-CI-gaps，不代表已合并或全平台通过。

公开payload与最终回执计划保存在外部`CASE/publications/pr-039-randn-i64-upstream-20261019/`（CASE沿用038正式目录），当前记录保留URL/commit/SHA/检查结论，不存完整原始payload副本。只在该唯一新子目录排他创建，不覆盖任何旧数据。

## CI失败只读定位（2026-10-19 16:24+08）

PR head仍为56e1065c350f49a238b10137afcf8a9eef667f3c，未修改提交。用户反馈红灯后只读核查GitHub check-runs、job steps和原始日志：

- [rule-check-required失败日志](https://github.com/flagos-ai/FlagGems/actions/runs/39220760468/job/117955244058)：robust-checkout第一轮HTTP传输curl28（速度低于20480 bytes/sec持续20秒），随后连接超时，30轮后报`robust-checkout: all links failed after 30 rounds`退出1。失败发生在checkout，后续规则步骤均skipped；不是randn测试、编译或规则断言失败。SSH无key被跳过不能据此判断凭证错误。
- code-style已success；[python-op测试日志](https://github.com/flagos-ai/FlagGems/actions/runs/39220760439/job/117955527868)确认本次merge测试commit64dcfc1193e2a2484548fb37c4ae103969afbd73，常规`tests/test_randn.py`为27 passed/2 skipped，quick-cpu模式为25 passed/2 skipped。两项大张量测试按opt-in设计跳过；不能据此声称CI已验证大N，038的PPU证据仍单列。
- unittest-required在该快照仍queued，不能宣称全部CI通过。当前失败无须据此修改randn实现；仅失败检查的重跑待用户指令。本轮未重跑CI、未发评论、未改PR、未访问目标服务或8035，未启动任何推理/GPU测试。

## 结果

- Issue：[FlagGems #7269](https://github.com/flagos-ai/FlagGems/issues/7269)，2026-10-19 16:08:28+08创建，open。
- PR：[FlagGems #7270](https://github.com/flagos-ai/FlagGems/pull/7270)，16:09:22+08创建，open/non-draft/未合并，已attach当前聊天；target master，head ZenithJoyH:fix/randn-output-offset-int64。
- Commit `56e1065c350f49a238b10137afcf8a9eef667f3c` / treea5c726488f388ba05b805c6b1ea28327ef89c35a，parent为冻结80d30e43。分支更新使用expected旧SHA且force=false；fork master/support分支未动。上游master同期自然前进至d06fae7d，PR读回仍mergeable、1commit/2files（58add/1del），未夹带fork历史差异。
- PR正文精确`Fixes #7269`，GitHub CLI读回`closingIssuesReferences`已明确包含7269；Issue[反向评论6262679223](https://github.com/flagos-ai/FlagGems/issues/7269#issuecomment-6262679223)已读回，PR合并后自动关闭7269；旧7179仅related、不自动关闭。
- 线上2文件内容逐字节等于本地检查版本；代码SHA48d700e3、tests b7df6c0c，完整SHA见范围段。public Issue body SHAe45805492ed2595bca83e3da28f1642a4f457e6669544b968e971c7263812bb5，最终PR body SHA5078a40fb6bff0f6f5e3379eba8f82e4c15713e3b277e59e8abbff14da7205dc。无额外GitHub提交/合并/强推。
- 初始CI只读快照：triage/preprocess success，python-op in_progress，code-style/rule-check-required queued，其余按标签skipped；不是CI已通过或硬件新pytest已执行的结论。不为本次提交创建持续监控/触发额外测试指令，既有模型heartbeat仍PAUSED。
- 公开payload/commit/读回与检查回执按上述唯一publications目录保存；只做标准库版本metadata和历史证据读取（Triton独立distribution不存在，FlagTree提供3.6.0模块，未当作未安装）。运行服务、权重、Plugin/FGVLLM/Gems安装均未修改，模型HTTP请求0、新GPU测试0、8035访问0。原先038硬件验证与本轮新pytest待测项明确分开。
- 外部归档已排他创建并核传输SHA：`issue.md` e4580549、`pr.md` 5078a40f、`fix.patch` cf49738da9d69b959686edc0ba2d9fd9848c1a798a0a94377b7d65b7c46b950d、`receipt.json` 01d01ba1995925e313a4e498669e9a097a6d74fe9819af6b3cec527896f677f2、`manifest.json` 26f17ae1e8fc0fccfc82b4cb169ba8278e95e8828e0fd3c3312adea9d5b78965。本地关联记录/YAML/文档映射及git diff whitespace复核通过，不等于全仓历史记录审计或模型验收通过。
