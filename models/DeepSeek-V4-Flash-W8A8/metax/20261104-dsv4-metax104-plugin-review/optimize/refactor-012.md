# refactor-012：12个FGV PR的review处理与完整单算子性能报告

用户在2026-11-12侧聊明确要求处理全部#1136–#1147的comments，并为全部补充shape / vLLM latency / FlagGems latency / speedup。经用户直接授权向主聊天协调，使用物理GPU7短时窗口；主任务GPU0/TP8及其op-006/007/008保持独立，GPU7用完已归还，后续不再运行GPU。

## 已完成的review修正

发现#1143两项意见：合并按后端命名的测试，以及补完整性能表。代码提交 [9b35f751](https://github.com/ZenithJoyH/FlagGems-vllm/commit/9b35f7516cf6feecb04ade028536edff843ab66a) 已非force更新原PR分支，其余11个没有代码变更。

- 将Ascend及MetaX测试合并到tests/test_mhc_pre.py，删除两个后端后缀文件；只在各测试上声明后端要求。
- Ascend原7个helper/测试函数AST完全保持；CUDA RNG fixture在Ascend不执行。
- CI selector同时选择新common文件、原tests/test_mhc_ops.py和benchmark。
- Black24.8/isort5.12/flake8 7.1、AST保持、真实selector及git diff whitespace检查通过；仓库原生pre-commit hooks全部适用项通过，check-yaml因没有YAML改动正常不适用。hooks后1231文件SHA仍不变。
- 34 passed、29原Ascend-only skipped、0 failure/error；7 capture /14次新输入replay，实际MetaX/common JIT命中。1231文件SHA前后及独立CPU复验一致；未声称Ascend设备已验证。
- 远端Git tree d23922000506508ff98490add37f06b89fc22004与验证本地树完全相同，两个新增/修改文件的远端blob及全文逐一回读一致。
- 已[回复行内review](https://github.com/flagos-ai/FlagGems-vllm/pull/1143#discussion_r4545329823)并resolve；已[回复完整数据请求](https://github.com/flagos-ai/FlagGems-vllm/pull/1143#issuecomment-6812149751)。其余11PR当前没有行内/会话评论，不编造已处理意见。

## 性能报告：保留完整shape和每轮

12个PR正文均已新增报告并通过全文+head回读。10类算子共138个shape/变体行×3repeat=414个计时点；时长单位µs（原生JSON ms×1000），speedup逐点复算，所有慢点保留，不重跑模型、不拿E2E值当算子时长。

| PR | 算子/范围 | shape行 | 计时点 | 真实对照 |
|---|---|---:|---:|---|
| [#1136](https://github.com/flagos-ai/FlagGems-vllm/pull/1136) | gather地址修正：原benchmark版本guard，未计时 | 0 | 0 | 明确非SDK或not measured |
| [#1137](https://github.com/flagos-ai/FlagGems-vllm/pull/1137) | SiLU clamp：PyTorch composition | 10 | 30 | 明确非SDK或not measured |
| [#1138](https://github.com/flagos-ai/FlagGems-vllm/pull/1138) | 动态/静态INT8：vLLM native SDK | 60 | 180 | SDK |
| [#1139](https://github.com/flagos-ai/FlagGems-vllm/pull/1139) | Router TopK：vLLM native SDK | 8 | 24 | SDK |
| [#1140](https://github.com/flagos-ai/FlagGems-vllm/pull/1140) | QNorm/RoPE/cache：portable FGV+两侧同state resetcopy | 7 | 21 | 明确非SDK或not measured |
| [#1141](https://github.com/flagos-ai/FlagGems-vllm/pull/1141) | Prefill TopK：vLLM native SDK | 7 | 21 | SDK |
| [#1142](https://github.com/flagos-ai/FlagGems-vllm/pull/1142) | MoE align：portable allocating non-TLE API | 8 | 24 | 明确非SDK或not measured |
| [#1143](https://github.com/flagos-ai/FlagGems-vllm/pull/1143) | mHC pre：portable FGV public API | 10 | 30 | 明确非SDK或not measured |
| [#1144](https://github.com/flagos-ai/FlagGems-vllm/pull/1144) | MQA：独立shared/gathered/paged PyTorch参考 | 9 | 27 | 明确非SDK或not measured |
| [#1145](https://github.com/flagos-ai/FlagGems-vllm/pull/1145) | Decode TopK：vLLM native SDK | 11 | 33 | SDK |
| [#1146](https://github.com/flagos-ai/FlagGems-vllm/pull/1146) | sparse MLA：retained serial MetaX | 8 | 24 | 明确非SDK或not measured |
| [#1147](https://github.com/flagos-ai/FlagGems-vllm/pull/1147) | compiler/GDN隔离：没有单算子计时 | 0 | 0 | 明确非SDK或not measured |

真正SDK对照只有#1138/#1139/#1141/#1145。其他已有比较的vLLM latency/SDK speedup列标N/A，portable/reference/retained-serial时长与比值单列，不伪称SDK。#1136原生benchmark针对vLLM CUDA>=0.20.2且<0.21.0，当前MetaX vLLM-op0.24.0三次均在计时前skip；#1147只是编译器隔离/能力guard，64/128/64+128是正确性形状而非计时。两项明确测量缺口，不能冒充性能通过。三个性能阻塞PR#1138/#1141/#1145仍为Draft，原负优化/继承失败和阈值均保留。

原始证据包pr-validation-final15.tar.gz SHA b50f3cac68668067b3ef73530e1c05edb099ac07859276233a804942833799ec。计时所用旧source_commit、每轮原生JSON SHA、当前PR head均在各PR正文声明；当前部分PR已合并新main，因此不把旧测量冒称新head重新计时。CPU逐文件核验旧private workspace全SHA，相关算子/launch函数AST与所用benchmark callable均不变；变化为导出排序、绝对import或其他算子/CI。原SDK比对运行时HAS_VLLM/实际函数对象回执亦核对。完整CSV/各PR表格及源绑定审计保存在外部新review目录；当前项目只保留摘要和SHA。

## 隔离、失败与审计

新容器deepseekV4-flash-prreview-20261112，以已验证不可变snapshot镜像b371e510...创建，与原容器两个bind逐项相同（mount_parity passed）。只在新/opt/dsv4-pr-review-20261112/fgv03工作，不写原整改容器、主聊天regression容器、installed source、启动脚本、编译器、权重/缓存，不启动模型。

初次stage因仓库3个内部文档symlink的严格解包拒绝而失败，后续一个host回执名冲突也在启动Torch前被拒绝。均保留，0GPU请求，不当算子数值失败、不覆盖旧冻结命令。新版本仅允许解析后仍位于新副本内部的相对symlink，并添加唯一回执/阶段准入CPU检查；最终唯一实际GPU批次完整通过。300s测试预算，TERM180s后仅精确PID/ticks关联幸存者可KILL，进程已正常退出。

最终独立审计：D/pr-review12/final-review-audit.json SHA e1eb53d8d3f6b0da4756d72d20c3ef2a6675ca2e06405d00fa0fc8fe7c3a00f4；native XML SHA b9da7926ea01cc2f88d75eacd569be21c0567372c45df9a5d14c3c859ea0a60e，dispatch/graph SHA d9736d9127cc084fb090f0ebceae95c66f79af03d44b3464d7b93dd26707a67e。原容器ID/image一致，侧聊测试进程清空；GPU7释放时间已记录，主聊天随后收回所有GPU，未要求或宣称此刻全机空闲。

D=/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01。此文档为独立新文件；state/README小条目补丁交主聊天串行合并，未整文件覆盖其活动记录。没有合并上游PR、改变其他PR源码或更新汇总flaggems-vllm-opt；上游CI/maintainer最终review仍单独评估。

最终证据包：`/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review/refactor01/pr-review12/review-final12.tar.gz`，SHA256 `029c1c0ba72b76076f6215492607938d010ac8d1a106022c5d23f224b10b18dc`，88724bytes / 66files。含12PR最终全文、414计时点CSV、各原生结果SHA、源码绑定审计、修复patch、34/29skip原生回执及冻结命令。原16MB原生性能包独立保留不重复打包；首次0GPU编排失败原件仍保留在review根目录。
