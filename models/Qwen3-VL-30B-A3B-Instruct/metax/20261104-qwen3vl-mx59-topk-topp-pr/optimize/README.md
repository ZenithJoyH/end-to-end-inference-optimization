# Top-k/top-p PR 整理与单行优化

[PR #1069](https://github.com/flagos-ai/FlagGems-vllm/pull/1069) 最新为 b1287f17（signed-zero修复），Open待review/CI。源 mx-59/qwen3vl 保持039f03ed，本轮修复未部署到运行服务。

| ID | 范围 | 正确性 | 性能与决定 |
|---|---|---|---|
| [pr-001-topk-topp](pr-001-topk-topp.md) | 接口对齐与原始提交 | 68设备测试、6算子及3实际hook变化输入replay | 历史M1回退，原记录保留 |
| [op-002-single-batch-sort](op-002-single-batch-sort.md) | 仅M1排序特化 | 91设备测试/18graph replay、20组对原PR位级一致 | M1改善2.27–4.94x；全部8项超过0.9x参考，keep PR only |

[ci-003-export-order](ci-003-export-order.md)：仅修复MetaX导出列表casefold顺序，rule-check与basic ci均已通过（含两套MetaX环境），54项本地CI工具单测通过。

无模型/E2E累计收益；组件收益不能直接换算模型吞吐。原op002专用容器已停；本轮仅按用户授权将已验证代码同步到qwen3vl，不启动模型、不测性能。

[deploy-004-container-sync](deploy-004-container-sync.md)：已完成，目标容器91项组件测试/20组位级对照、18算子+18实际hook变化输入replay通过；原MoE、Plugin和运行配置保持。测试脚本导入路径incident已恢复并解决，未改算子或标准。

[audit-005-moe-main-diff](audit-005-moe-main-diff.md)：只读对比固定main208ab580；MetaX计算kernel相同、Qwen-VL helper拆分未同步，配置CPU对照一致；通用MoE文件仍旧版。未改MoE。

[sync-006-moe-main](sync-006-moe-main.md)：MetaX文件已精确同步main208ab580，25项现有MoE测试/8组位级对照/24次变化输入graph回放，以及PR1069的91项测试/18次实际Plugin回放通过。通用主线INT8大stride边界非法访问，通用文件与测试已回滚保留旧版。PR1069和其余配置保持；不是整体主线升级通过。

[fix-007-int8-large-stride](fix-007-int8-large-stride.md)：上述通用升级阻塞已修复，同步main208ab通用MoE加仅三个量化kernel的寻址归并补丁。私有及安装路径62项测试/42次变化输入replay、实际MetaX8组/24次replay、PR1069的91项测试/18次实际Plugin replay通过；测试报告被误分类为配置的审计问题保留记录并纠正，同一字节重装后15项/42次replay再验通过。111项真实配置与PR1069保持，独立最终审计通过；无模型或E2E结论。

- [op-008-threshold-prefix](op-008-threshold-prefix.md): 实测36形状/三方法均通过稳态及漂移检查；B64大词表完整接口约快4%–4.5%，小shape与部分B8普通调用回退，不能全量替换。91单测、42位级对照、额外18次graph回放通过；源服务未改，候选仅诊断，PR未更新。

- [op-009-shape-guard](op-009-shape-guard.md): guard integration and validation prepared; source unchanged, PR push only after validation.

[op-009-shape-guard](op-009-shape-guard.md) completed: PR039f03ed/Open/mergeable,134UT/48bitwise/24extra replay,44controlled rows. Smallpathswithin1.02%;B32/B64bigvocab normal~2.3–3.9%lower. Supplementary benchmark18/20>=0.9reference, two unchanged B64/V4096 inheritedgaps retained/disclosed. No source model changes.

- [deploy-010-pr1069-guard](deploy-010-pr1069-guard.md): completed; threefilesexact039f03ed, installed actualPlugin12capture/36replaypassed. Othercode/config/PID/source preserved. Disknew, existingservice not restarted/reloaded.

- [cleanup-011](cleanup-011-qwen3vl-containers.md): 已删除18个历史相关容器，qwen3vl/opt18/8030 原PID和配置保留、HTTP200；其他模型未被本任务操作，并发外部变化单独记录。

- [fix-012-signed-zero](fix-012-signed-zero.md): signed-zero过滤修复及124新增边界/graph测试已准备；待GPU验证和44行同机性能回归后更新PR。

- [fix-012-signed-zero](fix-012-signed-zero.md)：已发布b1287f17；旧错6组GPU复现，258单测（124新增）、34capture/102replay、48位级对照及44行双方法/5BCR回归通过。最大耗时增加0.547%，源服务未变，测试clone已删除；CI735/2225排队。

- [report-013-disabled-flaggems-operators](report-013-disabled-flaggems-operators.md)：已完成mx-104指定镜像调查，九条FlagGems Issue及12列模板Excel已核验；明确RNG/stride/NaN/stable-zero缺陷与默认fallback性能边界，原有服务保持、自有clone已删除。
