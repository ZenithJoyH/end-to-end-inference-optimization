# MM 调参诊断地图

## PPU Mixed新形状导致在线搜索

| 字段 | 限域决策 |
| --- | --- |
| 信号 | 请求中大量LibTuner/default_policy/_bench，RPC约300s超时；不能只凭sample_tokens超时报采样器故障 |
| 匹配键 | FlagGems当前PPU MM/BF16/NT、多投影M20481/8198，graph服务Prefill；版本必须重查，不套用其他平台 |
| 机制 | Config bucket冷缺失后，逐raw-key/config读取benchmark缓存；114候选经合法性裁剪仍104，缺少已验证的生产搜索预算 |
| 首个检查 | CPU执行真实get_key/get_benchmark_key和prune；只读前后DB行差分，验证是否新key、namespace不一致或实际丢失，三者不能混称缓存问题 |
| 首个实验 | 冻结同初始SQL缓存之外，还要冻结kernel shape序列和实际输入hash；先用固定shape Default/有界/Default确认搜索预算，保留完整key、合法性和Expanded，再做原范围模型回归 |
| 通过证据 | 实际策略命中，原C8及C64最小回归、数值边界、FULL捕获/至少两次回放；新正式gate后才有性能晋级，不把CPU减少候选当端到端加速 |
| 停止条件 | 数值/graph/服务失败即停；禁止延长RPC、降MBT、放宽key或重复暖缓存至通过来替代因果验证 |
| 证据等级 | reproduced机制，修复/充分因果待验证；不同warmup/rep的custom协议tag碰撞是独立风险，不能夹带归因 |
| 来源 | [GLM点51证据卡](case-index.md) |

反例边界：同HTTP P4096/C8和SQL快照，真实冷M仍可为12293、28673或20481+8198，三臂无共同冷shape。候选真实104→4命中并通过C8，不足以将237.6→58.9s认定为稳态收益；原策略一轮过、回退RPC失败时先比较冷shape组数，不盲重跑到稳定。
