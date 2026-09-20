# FP8/FP4 MQA logits 案例驱动优化地图

## 已验证规则

### 跨仓库迁移后先证明 tuner 使用目标包的 runtime 配置

- 证据等级：`reproduced`。
- 触发信号：算子和 vendor tune YAML 已迁入新包，但冷 shape 仍出现大量候选
  benchmark、长时间同步在线调优或 worker RPC timeout。
- 匹配范围：带 `libtuner`/等价装饰器的 MQA logits 实现；必须按实际 vendor、
  graph 模式、dtype、每 rank shape 和运行函数对象重新匹配。
- 机制：装饰器在定义 kernel 时消费显式 runtime 返回的 config 集合。源码残留旧包
  runtime import 会绕过新包 YAML；减少 YAML 内容或预热单个 shape 都不能修复来源错误。
- 第一检查：同时打印目标包 `runtime.get_tuned_config(operator)` 和实际
  `kernel.fn.configs` 的完整 config 签名，并反查 runtime 对象的模块来源。
- 首个实验：只切换 runtime 来源，保持 kernel 和配置不变；新增测试断言两者 config
  集合完全相等，并在目标 vendor 上断言期望的有界候选数或唯一配置。
- 通过证据：配置来源测试、非对齐 shape 数值、原故障 shape 数值、graph capture
  与至少两次 replay、冷服务复现均通过；服务不再因该 MQA 表进入多候选在线调优。
- 数据库判读：整库 hash 变化只能说明某个 tuner 写库，不能归因到 MQA。必须按
  operator/config key 检查对应 benchmark/config 表；随后同 workload 复跑应稳定。
- 停止条件：实际 kernel 仍持有旧 config；目标 vendor YAML 未被解析；数值、graph
  或服务健康回归；候选数虽下降但原故障 shape 仍触发长时在线 benchmark。
- 来源：[GLM-5.3-Flash/PPU case card](case-index.md#case20260911-glm53-flash-ppu-e2e)。

## 尚未证明的边界

- 单配置消除了本案例的超时路径，但尚无正式端到端 A/B 证明它在所有 shape 上都是
  最快配置。
- 不能把既有 `172/198` 模型分数当成本次源码修复后的新精度结果；需要新分数时应
  重新运行正式精度评测。
- 其他平台可能需要多配置集合；不得把 thead 的唯一配置无条件推广。
