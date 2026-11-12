# operator-pr-007：按算子提交 PR

2026-11-09 用户明确授权将当前 FlagGems 与 FlagGems-vllm 修改按算子提交 PR。分为 Linear 与 flash_attn_varlen_func 两项；不提交 Plugin、不修改容器安装、不恢复已停止的 MBT 实验。

独立 checkout 合入最新上游 FG 319707ebbbd8427a6131a62e281f94dc81884878 / FGV bc46e67a6a2c97182fa4132605a661fe40cc792a，原容器补丁 SHA 为 cb47fb279da85372c09298b49f66b8a77dc083456c07a1d660fdd062e0809f8c / 34ebbd6c6b976f7ce2ce779b86c13f4c2e09752d670ca81158ef57dc648d4f2e。保留上游变更；算子计算主体与已验证安装版本 AST 相同。

本轮只读核验 GPU7 空闲，在既有隔离容器的 /workspace/bge-m3/pr-007 中解包独立完整源码，PYTHONPATH 指向该副本，未安装 wheel 或升级依赖。minimal-regression 只补测算子回归及 graph capture/replay；不替代模型正式精度或端到端性能。新原始结果放在 /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-operator-pr-007。远端脚本执行前保存并绑定 SHA。

本轮重新编译/调优开销较高；仅将之前006/005生成的内容寻址编译缓存以原子无覆盖方式复用到本轮独立cache，不修改已有文件或调优数据库，也不测冷启动或新增性能结果。执行脚本 /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-operator-pr-007/commands/seed-compile-cache.py SHA a3822d08b4f56a44110a045e16b2cd421eb34e726115bc7a9008dd02e42180bd，执行前本地冻结。

## 已提交 PR

- [flagos-ai/FlagGems #8591](https://github.com/flagos-ai/FlagGems/pull/8591)：codex/metax-linear-fp32-20261109-cb47fb2，commit `8c10ff9bfd714f68d3ce861ae3b73dfd514d4298`，4 文件，单提交，公开 blob SHA 已逐项与本地文件匹配。
- [flagos-ai/FlagGems-vllm #1124](https://github.com/flagos-ai/FlagGems-vllm/pull/1124)：codex/metax-varlen-fp32-20261109-34ebbd6，commit `646c835b774e729387b1d646b11c849d0be0e10b`，8 文件，单提交，公开 blob SHA 已逐项与本地文件匹配。

两项均 open、非 draft、未合并，GitHub mergeable=true（无文本冲突），CLA已通过。FGV code-style/rule-check/CI选择通过；其余 GPU CI 正在运行或排队。本轮 private checkout 硬件回归进行中，不把此前基线的测试结果冒称本轮最新上游结果。

结果归档与已安装源码无漂移核验脚本 /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-operator-pr-007/commands/archive.py SHA 47888f124a4d33ceec966983e915753b73a8a512ed5930156ecb92d717a49b38，执行前冻结。

最终交付归档脚本 /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-operator-pr-007/commands/final-delivery.py SHA fba2513bce3e84435651e7398505bd5d7d9baf8fae11f8c985d4241dc5ac26af，执行前冻结；仅保存 PR 元数据、描述和校验清单。

## 最终验证与状态

- 合入后的完整私有源码实际导入已核验。Linear **174 passed**（579.22s），varlen attention **166 passed**（45.559s）；两组零fail/error/skip，均保留真实graph capture与两次新输入replay。测试文件和生产修改文件逐项与公开PR blob校验相同。
- 两个纯Python wheel构建成功，无运行依赖安装或升级；FG适用改动文件pre-commit、FGV全库pre-commit、两库算子元数据/导出/marker/benchmark规则通过，FG API日志规则通过，FGV CI pin与66项CI helper单测通过。FG全文件clang-format本机架构限制已在PR如实披露，未混入C++修改。
- PR中明确区分本轮fresh rebase测试、此前FG006/FGV005的专项/模型功能证据、三轮算子policy benchmark；未将历史baseline数据当作最新版全库或模型性能。完整56/16shape表及所有观测回退已放入PR说明。
- 两个PR均为open、非draft、各1个提交，4/8文件，文本无冲突，CLA通过，未合并。FGV格式/规则/选择与多项容器smoke通过，其余GPU CI或FG格式/规则仍在运行/排队；FG旧style run因并发被取消，新run已排队，不冒称全部CI通过。
- BGE-M3实际安装的两库完整patch SHA分别仍为cb47fb279da85372c09298b49f66b8a77dc083456c07a1d660fdd062e0809f8c / 34ebbd6c6b976f7ce2ce779b86c13f4c2e09752d670ca81158ef57dc648d4f2e。本轮未更改安装源码或重启服务，GPU7无任务进程。MBT实验保持用户停止状态。

外部证据根：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261109-bge-m3-operator-pr-007`。SUMMARY.json SHA `2a1c45b91517f9e7b095baae00ea7eca0ea8afb306d29f832a401da4059d93c2`；DELIVERY.json SHA `a30faa8871000f326772cac3a0d9c04e3b6d6810377d22d437b5a6f5859fca42`；最终SHA256SUMS.json SHA `4043531af089780faf17edc889bd8d491c8cda174c4ccb3fc85e9e322a8bea3c`。原始JUnit、日志、两份完整源码包、执行脚本、PR最终说明与快照保留远端；本地临时构建/格式日志位于 `/tmp/bgem3-operator-pr-20261109`。
