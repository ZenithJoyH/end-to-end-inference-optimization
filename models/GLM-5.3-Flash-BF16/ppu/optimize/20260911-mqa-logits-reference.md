# 20260911-mqa-logits-reference MQA reference 路径对照

- 状态：`failed`
- 分类：`operator/replace`
- 目标场景：长 Prefill MQA
- 目标阶段：Prefill
- 依赖：reference MQA 实现

## 优化方向与瓶颈依据

用 reference 实现验证当前 MQA backend 是否存在可替换空间，并建立数值对照。

## 优化内容与适用边界

单变量切换到 reference MQA；该路径仅作为诊断候选，不是生产性能实现。

## 正确性与路径命中

长 Prefill 场景在形成有效性能结果前 OOM，因此没有可用于晋级的正确性或 graph
服务证据。

## 性能效果

没有有效吞吐数据；实验在性能测量前因 OOM 失败，不能将其与生产路径比较。

## 决定、风险与回退

决定拒绝。reference 路径显存风险高且不适合作为生产优化；服务恢复原 MQA backend。

## 外部证据

- `/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911/mqa-reference`

