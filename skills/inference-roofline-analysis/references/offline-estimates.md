# 离线容量与计算量估算

只在估算能改变下一步实验时使用。输入来自当前案例已核实的逐 rank 快照或实际 shape；服务身份、采集范围和对应 revision 仍按原流程记录。JSON 报告只绑定所读文件及其 SHA，不检查运行实例、不采计数器、不签发正式 gate。

## 显存与 KV 分页账本

当需要判断 graph/workspace 是否挤占 KV、不同 rank 显存是否失衡，或长输入准入为何受限时运行：

```bash
python3 evaluation/performance/capacity_analysis.py \
  --snapshot /external/case/capacity-snapshot.json \
  --output /external/case/capacity-report.json
```

快照按 `ranks[]` 分开提供事实；显存单位必须显式给出，测量值与估算值分开标记。只有声明互不重叠的 memory 科目才做 weights/KV/graph/workspace/other/free 与 total 对账。未解释残差保留为残差，不擅自归为 KV 或可用显存。

KV 输入示例（合成数值，仅演示字段；不代表任何模型结果）：

```json
{
  "schema_version": 1,
  "context": {"scenario_id": "synthetic", "candidate": "example"},
  "ranks": [{
    "rank": 0,
    "kv": {
      "layout": "hybrid",
      "groups_complete": true,
      "request_scope": "full_decode_lifecycle",
      "groups": [
        {"id": "full", "free_blocks": 100, "request_blocks": 9,
         "allocation_alignment_blocks": 4},
        {"id": "sliding", "free_blocks": 20, "request_blocks": 4}
      ]
    }
  }]
}
```

该例每请求第一组对齐到 12 块，两组上界为 8 和 5，当前 rank 的同构请求驻留上界为 5。
`groups_complete` 和 `full_decode_lifecycle` 是调用方需以真实分配路径证明的声明，工具不代其核验。
若需同时分账，在 rank 中增加 `memory_accounting: "disjoint"` 和 `memory` 对象；科目键为
`total/weights/kv/graph/workspace/other/free`，每项为
`{"value": 80, "unit": "GiB", "evidence": "measured", "source": "原始快照位置"}` 或 `null`。
该 quantity 结构中的 `value` 随科目填写，不把示例 total 复制到各科目。

KV 页容量取决于每组可用块、每请求所需块和分配对齐。普通 dense token→block 映射需明确声明；hybrid、MLA 等布局应直接提供各组 `request_blocks`。缺少每组分配需求、组覆盖或完整 Decode 生命周期范围时，只返回局部上界/未知。若布局名称为 unknown，但调用方已明确完整的每组块分配、对齐与生命周期需求，仍可计算这些声明下的驻留上界；未知布局不能用于推导 token→block。日志中的 `equivalent_tokens` 仅作观察，不自动除以请求长度。

明确的普通分页可用 `layout: "paged"`，每组给 `request_tokens`、`block_size_tokens` 和
`token_mapping: "dense_tokens"`，与 `request_blocks` 二选一。`request_blocks=0` 表示该组不约束新增请求；
所有组均不分配时没有有限 KV 上界。输出 `null` 表示未知，`0` 表示已知可用块不足，两者不能互换。

`--output` 必须是新文件；省略时输出到 stdout。退出 0 仅表示诊断报告生成成功，仍需读取 `status/gaps`；
非法输入或已有输出返回 2，不覆盖快照或旧报告。

逐组上界可以解释某一 rank 的驻留限制，但不能把 DP rank 上界相加或把 TP rank 任意取 min 后称为服务容量。完整结论还需要并行拓扑、调度规则、Running/Waiting、抢占/重算与目标负载实测。即使显存允许驻留，也不能推出满足 SLO 的并发或吞吐。

该边界对应已有 [hybrid KV 案例](../../../docs/cases/20261104-minimax-m3-metax-comm-kv-diagnosis/README.md)：等效 token 容量、组/块对齐与整输入准入共同影响实际行为。工具估算不能覆盖案例证据。

## Shape 与算法 FLOPs

需要可复算的算子计算量时，使用 `evaluation/performance/shape_flops.py` 对显式 shape 估算：

```bash
python3 evaluation/performance/shape_flops.py \
  --spec /external/case/operator-shapes.json \
  --output /external/case/algorithmic-flops.json
```

输入示例（合成 shape，不是模型结果）：

```json
{
  "schema_version": 1,
  "operations": [{
    "id": "projection",
    "kind": "gemm",
    "scope": {"phase": "decode", "rank": "0", "dtype": "bf16"},
    "calls": 2,
    "source": "已核验的实际per-rank shape记录",
    "shape_evidence": "measured",
    "shape": {"batch": 1, "m": 32, "n": 128, "k": 256}
  }]
}
```

`operations[]` 逐项给 `id/kind/scope/calls/source/shape_evidence/shape`；scope 的 phase 为
`prefill/decode/mixed/unknown`，rank 和 dtype 显式提供，可附 `scenario_id/service_id`。
GEMM 示例的算法量为 `2×1×32×128×256×2=4,194,304 FLOPs`；这里 measured 只修饰 shape 来源，
FLOPs 本身始终是估算。

其他支持形状：

- `kind: "attention"` 的 shape 给 `pattern: "dense"|"causal"`、`batch/query_tokens/key_tokens/query_heads/head_dim/value_head_dim`，可附 `kv_heads`；causal 还须给 `prefix_tokens` 且 `key_tokens=prefix_tokens+query_tokens`。sparse/MLA/hybrid pattern 保留未知，不回退成 dense。
- `kind: "moe_projections"` 的 shape 给 `tokens_per_expert` 真实各专家 token 数，以及 `projections: [{"name": "...", "in_features": ..., "out_features": ...}]`。明确列出 gate/up/down 等实际投影，不假设激活专家平均分布。
- 需要汇总时显式提供顶层 `aggregations: [{"id": "...", "operation_ids": ["..."]}]`；只能组合相同 scope 的操作，父子分解或重复调用不可重复计入。未声明聚合时不自动输出全模型总量。

优先输入已经核实的 per-rank shape 和调用次数，按 Prefill/Decode/Mixed 分组。未核实的模型配置不能代替实际 batch、padding、稀疏路由或执行 shape。

- GEMM 一次乘加按 2 FLOPs；batch 和调用次数各计一次。
- Attention 按显式 query/key 范围及 causal 规则计算 QK/AV 的算法工作量，遗漏的 softmax、RoPE、索引、拷贝等单列；不能把稀疏/MLA/hybrid 自动当 dense GQA。
- MoE 需要真实每专家 token 分布与投影结构，不能用总参数量或平均路由自动代替。
- 只汇总输入中声明的算子，缺失项保留；结果不是完整模型的硬件指令数。

结果作为 `F_algo` 的估算输入。`F_exec`、HBM 读写流量、kernel/range 计时、精度/执行单元对应的硬件屋顶均需独立证据。逻辑张量大小不能冒充 HBM 流量，算法计算量不能冒充实际执行量或 MFU。完整计算与净收益映射仍按 [roofline.md](roofline.md)执行。

## 写回与复用

原始快照/spec 和诊断 JSON 放在批准的外部产物目录。在已有优化点记录输入/输出路径与 SHA、phase/rank/shape、假设、缺口、有效范围及它改变了哪项候选判断。输入或关键绑定改变后重新分析；同输入有效报告直接复用。不新增模型阶段、强制 YAML 字段或评测模式。

分账与计算量工具的设计来源见[集成说明](../../../docs/analysis-tooling-integration.md)，实现由本项目独立维护。
