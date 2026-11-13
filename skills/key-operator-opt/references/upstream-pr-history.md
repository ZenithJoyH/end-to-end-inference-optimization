# 用上游 PR 缩短候选选择

当真实热点已经明确、准备新增融合/后端/模型快路，或现有实现与架构资料有差异时使用本入口。
先查本地案例的实际证据，再查影响当前方向的上游变更；不要求每个优化点联网重查全部模型。

## 离线查询

从项目根目录执行：

```bash
python3 scripts/upstream_pr_query.py --framework vllm --model DeepSeek --format json
python3 scripts/upstream_pr_query.py --operator indexer_topk --format json
python3 scripts/upstream_pr_query.py fusion --limit 5
```

默认索引是本目录的 [upstream-pr-index.json](upstream-pr-index.json)；可用 `--index /external/index.json` 显式选择另一份。
`--framework`、`--model`、`--operator`、`--review-level` 与关键词组合筛选，`--limit` 限制输出量。
查询只读索引，不解引用卡片中的路径、不联网、不自动同步。
JSON 输出包含索引路径与 SHA256、查询条件、匹配数及来源卡；无匹配是正常结果，不能据此认定上游没有实现。
非法输入返回非零，不用空结果掩盖解析错误。

## 读卡与决策

- `metadata_verified` 只说明在卡片日期核验了 PR 对象、状态和 revision；closed 与 merged 分别记录。
- `discovery` 是待审阅线索；`diff_reviewed` 需有准确 diff 范围和审阅证据；`target_reproduced` 还需目标环境的实际调用与原始验证产物。
- 卡片中的上游 head/merge revision 不等于当前服务 revision。旧本地结果不能自动绑定到后来更新过的 PR head。
- 默认种子是少量有来源的发现卡，不是完整模型优化史，也不证明任何国产平台命中或收益。

对匹配项读取原 PR 与当前调用方，回答：哪些字节、计算、launch、同步或调度行为改变；目标阶段、shape、dtype、graph、平台条件是否匹配；现有 Plugin/算子库扩展点能否接入；有哪些反例与回归风险。然后把它作为现有 `framework`、`operator/replace` 或 `operator/improve` 候选的一项来源，回到 SOP C2 排名和首个证伪实验。

在当前 `optimize/<experiment-id>.md` 中仅保留影响本轮决策的 PR URL、实际 revision、读过的文件/diff 范围、审阅/复现等级、采纳或暂缓理由与索引 SHA。原始材料留外部；不复制完整 PR 卡、不新建 `history/`，不将外部声称的加速比写成本项目收益。

## 维护与来源

索引更新由明确维护任务完成。修改时保留来源和日期，逐项核实 upstream 对象类型/状态，新增发现卡保持 `discovery`；后续审阅和复现须补相应证据。元数据刷新不会刷新旧 diff 审阅或性能数据的有效期。

查询与分级设计参考 [AI-Infra-Auto-Driven-SKILLS 固定版本的 PR history](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/5df356636bf9da3a1446653043942ff3487c1430/model-pr-optimization-history/SKILL.md)。本项目维护原创的精简索引和查询实现，不依赖该仓库目录或全局 Skill。
