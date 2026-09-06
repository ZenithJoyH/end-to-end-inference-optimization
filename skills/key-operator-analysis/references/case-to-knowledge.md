# 从实际案例演进关键算子知识

本文件定义如何把一次端到端优化中的算子证据转化为下一次可直接使用的知识。目标不是扩大文档，而是缩短后续任务从“发现热点”到“提出高质量首个实验”的时间，并让后续优化建立在已经验证过的机制、边界和反例上。

## 1. 三层知识结构

### 完整案例：事实系统

位置：`docs/cases/<case-id>/` 及对应 `models/<model>/<platform>/`。

保存环境、命令、源码 revision、patch、原始结果位置、正确性、失败过程、回退和最终验收。这里允许完整叙事，是任何性能数字的权威来源。

### Case index：算子证据账本

位置：`skills/key-operator-analysis/references/operators/<operator>/case-index.md`。

每个实际案例只保留一张结构化证据卡，用于快速判断当前场景是否与历史案例相似，并可反向链接到完整证据。成功、负优化、未命中、精度失败和未证实实验都应保留。

### Optimization map：可执行理解

位置：`skills/key-operator-analysis/references/operators/<operator>/optimization-map.md`。

把一个或多个证据卡提炼成未来决策：看到什么信号、先检查什么、什么条件下尝试哪类方案、何时停止、哪些解释已被反例否定。这里不是性能排行榜，也不保存完整实验流水账。

算子的 `README.md` 只保存相对稳定的语义、数据流、实现路径、性能模型和跨案例理解。只有案例改变这些内容时才修改。

## 2. 案例证据卡

使用以下字段；未知项写 `unknown`，不能补猜：

```yaml
case_id: ""
case_link: ""
status: kept | reverted | not-proven | blocked
evidence_level: observation | reproduced | transferred | invariant
environment:
  model: ""
  platform: ""
  hardware: ""
  engine_revision: ""
  plugin_revision: ""
  operator_library_revision: ""
  mode: eager | graph | both
operator_path:
  stage: prefill | decode | mixed
  impl_id: ""
  effective_shape: ""
  dtype: ""
  layout: ""
bottleneck_evidence: ""
change:
  classification: operator/replace | operator/improve
  primary_variable: ""
  applicability_guard: ""
results:
  operator: ""
  end_to_end: ""
  correctness: ""
  regressions: ""
knowledge_delta:
  prior_belief: ""
  outcome: confirmed | refined | contradicted | none
  revised_belief: ""
  future_first_check: ""
limits: ""
```

正文可以比 YAML 更易读，但这些语义必须齐备。性能数字只做索引摘要，并链接完整案例；不同 workload 的百分比不能放在同一列形成虚假可比性。

## 3. 提炼 optimization map

每条 map 项至少回答：

| 字段 | 问题 |
|---|---|
| 信号 | 哪个 profiler、shape、dispatch 或资源现象触发这条知识？ |
| 匹配键 | stage、每 rank shape、dtype、layout、backend、硬件和 graph/eager 哪些必须相符？ |
| 机制 | 哪部分无效工作、访存、计算、launch、同步或通信被改变？ |
| 首个实验 | 最小、可证伪、单变量的验证是什么？ |
| 通过证据 | 哪些运行时命中、数值、graph 和端到端证据才允许保留？ |
| 停止条件 | 哪种不命中、回退、额外开销或正确性问题应立即停止？ |
| 证据等级 | 当前是 observation、reproduced、transferred 还是 invariant？ |
| 来源 | 哪些案例卡支持或反驳？ |

`observation` 可以进入 map，但必须标为开放假设；`reproduced` 可以形成严格限域的已验证分支；达到 `transferred` 前不能删除关键平台和 shape 限制。

## 4. 强制写出知识差量

案例结束时不要只写“新增了某平台结果”。至少选择以下一种真实变化：

- `confirmed`：既有机制在相同适用边界内被复现，置信度提高。
- `refined`：发现更精确的决定变量、边界、首个检查或停止条件。
- `contradicted`：发现反例；保留原记录并缩小旧规则范围。
- `none`：案例没有改变算子理解，只增加了关联证据。

一个好差量应能改变下一次行动。例如，“MLA 更快”不是知识差量；“dispatch tile 应按 TP 后每 rank 的有效 head 数检查，先量化 head padding ratio，再决定是否做更小 tile A/B”才是可执行理解。

## 5. 更新和冲突规则

1. 先完成实际案例，再更新算子知识；不能用计划中的实验填写已验证结论。
2. 不把原始 trace、完整日志、大表格或 patch 复制进技能，使用链接和摘要。
3. 不按日期把案例段落连续追加到稳定 README；案例一律进入 case index。
4. 后续案例冲突时，分别记录环境和结果，标记 `disputed` 或收窄适用范围；不能挑选更好看的案例覆盖旧证据。
5. 优化后热点排序变化属于重要知识：记录新的瓶颈边界和下一步，但不把该排序外推到其他模型。
6. 案例的正式精度未完成时必须保留此限制；算子数值通过不能改写成模型精度通过。

## 6. 完成检查

- 完整案例仍是所有实验数字的唯一权威来源。
- case card 足以在一分钟内判断环境相似度和是否值得打开完整案例。
- optimization map 给出了首个验证实验和停止条件，而不只是总结结果。
- README 没有因单次案例膨胀成日志集合。
- 新知识明确说明比案例开始前多知道了什么，以及下一次因此少走哪一步。
