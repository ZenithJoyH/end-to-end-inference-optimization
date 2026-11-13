# 已有 trace 的分层导航与候选表

用于 `analyze` 中需要 forward/layer 结构、跨 stream 活动区间或融合候选的情况。输入 trace 的采集有效性、服务身份、graph/backend 命中和 rank 覆盖仍按 Profiling Skill 核验；离线工具只绑定读取的文件，不签发采集或性能通过回执。

## 命令

从项目根目录执行：

```bash
python3 evaluation/performance/trace_analysis.py \
  --trace /external/case/rank0.trace.json.gz \
  --annotations /external/case/verified-boundaries.json \
  --output /external/case/trace-analysis.json \
  --perfetto-output /external/case/range-navigation.trace.json
```

输入支持 Chrome trace JSON 或 gzip，分析正时长的 complete (`ph: "X"`) 活动；不自动配对 `B/E` 事件。`--annotations` 和 `--perfetto-output` 可省略；无边界时仍按 pid/device 分组统计，但 phase/forward/layer 保持 unknown。厂商 trace 的额外设备活动类别须先核验，再用可重复的 `--device-category` 显式声明，不能因事件带 stream 或名字包含 CUDA 就当作设备 kernel。

输出使用新文件，不覆盖输入或已有报告。分析报告和导航文件放在批准的外部 case 目录；本地模型记录仅保留摘要、路径和必要 SHA。
Perfetto 输出是独立的范围导航 trace，不包含或重写原 kernel trace；用报告中的原始事件下标和时间范围关联原文件。
导航使用稳定数值 pid/tid 与可读名称 metadata；当前经过本地 JSON 序列化和回归检查，尚未做实际 Perfetto UI/trace_processor 导入验证。
退出 0 仅说明有效诊断已生成，仍须检查顶层 `gaps`；`status: "incomplete"` 表示归属/身份等信息存在缺口，
任何状态都不是模型或性能验收通过。格式/绑定错误返回非零并拒绝生成结果。

## 经核验的范围与锚点

annotations 的 `trace_sha256` 必须是输入文件原始字节的 SHA256（gzip 输入也取压缩文件本身），不能使用另一轮 trace 的边界。时间单位为微秒，直接使用 trace 原坐标；`event_index` 是原 `traceEvents` 数组下标，包含 metadata，不能用过滤 kernel 后的序号。

以下为字段示例，时间和下标均为合成值，需替换为真实边界：

```json
{
  "schema_version": 1,
  "trace_sha256": "替换为输入文件的64位SHA256",
  "rank_bindings": [
    {"pid": 10, "device": 0, "rank": 0, "evidence": "worker manifest与trace metadata对应"}
  ],
  "ranges": [
    {"id": "p0", "kind": "phase", "label": "decode", "pid": 10, "device": 0,
     "start_us": 100, "end_us": 150, "evidence": "已核验step边界"},
    {"id": "f0", "kind": "forward", "label": "target-0", "parent_id": "p0",
     "pid": 10, "device": 0, "start_us": 100, "end_us": 150,
     "evidence": "已核验完整target forward，含末尾边界"}
  ],
  "anchors": [
    {"id": "a0", "parent_id": "f0", "verified": true,
     "event_indices": [0, 3], "labels": ["L0", "L1"],
     "evidence": "当前源码和trace证明每层一次，最后一层由f0末尾封闭"}
  ],
  "source_map": [
    {"event_index": 0, "source": "实际调用方文件:行号或impl_id", "evidence": "已核验launch-site映射"}
  ]
}
```

`ranges` 也可直接声明 `kind: "layer"`、`parent_id` 指向对应 forward，省去 anchors。父子窗口必须在同一 pid/device/rank，且包含关系和同级非歧义性可验证；不将多个 rank 均分成层。范围须位于对应分组已观察活动的首尾内。同一 pid/device 对应多个 rank 时，范围需显式提供 `rank`；`rank_bindings` 的 rank 是显式映射，pid 本身不自动当 rank。

锚点须先由当前实现及时间线证明其频率和含义，再提供准确原事件下标与层标签。未知层数、target/draft 混入、不同 graph 路径或不完整末尾不能靠 kernel 名匹配或计数整除修复。验证条件不满足时保留父窗口与未知层归属；重新核验边界后再分析，不为工具额外采集。

## 如何解释结果

- `sum_duration_us` 是活动时长之和，重叠活动可重复累计。
- `busy_union_us` 是该 pid/device 和窗口内活动区间的并集；不包含未采集活动，也不是硬件利用率计数器。
- `wall_us` 使用最早开始和最大结束，保留跨 stream 长尾；范围本身的窗口长度与其中活动跨度分别解释。
- `cross_stream_overlap_us` 是不同 stream 同时活动的时间，不证明依赖可解除、开销被隐藏或对应时间可以移除。
- `exclusive_us` 是当前统计集合内没有其他 stream 活动的时间，也不自动等于依赖关键路径。

缺少 stream 时，精确 overlap/exclusive 为 `null`，仅保留已知 stream 的交叠下界 `known_stream_overlap_lower_bound_us`；不能把未知 stream 当独立流或零交叠。

跨范围的 kernel 在范围内按相交区间统计，保留原事件和 crossing 标记；完整事件的阶段/层归属不能被静默指派到一个窗口。父子层级是同一活动的不同视图，不可相加。范围部分缺失时也不能把剩余未归属活动丢掉后称为完整阶段统计。

报告提供 kernel/source、overlap 和 fusion 候选视图及原事件导航。源码归因是显式映射或 trace 中已有 launch-site 线索；无法确认则 unknown。相邻、同 stream 或不同 Python scope 均不证明真实数据依赖。检查依赖、状态/graph、数据转换和完整调用新增成本后，才将候选交给 SOP C2 排名与首个证伪实验。

只将本轮决策依赖的阶段/rank/层、候选与反例、未知项和原始范围写入当前优化点。端到端收益继续用无 profiler 的同契约 baseline/candidate/revert 验证，不能用两个 trace 的比例代替。

本入口参考外部项目的分层导航和候选表机制，来源与本地取舍见[集成说明](../../../docs/analysis-tooling-integration.md)。
