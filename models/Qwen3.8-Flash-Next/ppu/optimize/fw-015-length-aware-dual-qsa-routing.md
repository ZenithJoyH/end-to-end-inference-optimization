# fw-015：长度感知的双 TP8 QSA 安全路由

## 动机

固定 `VLLM_FL_QSA_STATIC_SCORE_COLUMNS=8448` 对四个正式性能场景的最大总长度
P32768/D1024（33792 token）是精确上界，但把它全局用于 GPQA 的最长 60K 输出会截断
QSA 可见候选，`acc-008` 已证明这种全局部署不可接受。完全无边界配置恢复了 11 个
60K cap，并把正式分数从 167/198 提高到 174/198；与此同时，`perf-015` 的前两轮
P16K Prefill warmup 已显示无边界路径约 5803 tok/s，明显慢于历史有边界 `perf-014`
约 7699 tok/s。warmup 不是正式加速比，但足以提出一个新的可证伪机制。

本实验不重新全局启用固定边界，而是保留两个不同语义的 TP8 replica：

- bounded replica：`8448` 个 compressed columns，只接收可证明整个生成周期都不超过
  `8448 * 4 = 33792` token 的请求；
- unbounded replica：不设置 QSA 静态边界，承接所有长请求、异常请求和无法证明安全的请求。

## 冻结安全规则

1. 使用 vLLM 自身 `/tokenize` 的 `count`，确保 chat template、special token 与真实服务一致。
2. 仅当请求显式给出非负整数 `max_tokens`，且 `prompt_count + max_tokens <= 33792` 时选择 bounded。
3. 缺少 `max_tokens`、批量/令牌 ID prompt、multimodal、tokenize 错误、schema 不识别、上游超时或任何歧义都 fail closed 到 unbounded。
4. 路由器不得修改 sampling、prompt、messages、tools、stop、seed 或输出；流式和非流式响应都透明转发。
5. bounded 服务身份必须同时证明 `compress_ratio=4`、`static_score_columns=8448` 和当前 Plugin/FlagGems SHA；unbounded 服务必须证明环境中不存在该变量。
6. 边界测试覆盖 33791、33792、33793，并以实际 tokenizer count 而不是字符数判定。

## 分阶段门禁

- 协议单测：安全规则、错误回退、chat/completion tokenization payload、stream passthrough 全部通过。
- 路由 smoke：短请求只能到 bounded，超界与无法识别请求只能到 unbounded；记录后端命中证据。
- 数值/graph：bounded 上的 P16K/P32K 边界请求必须通过 selection、graph capture 和至少两次 replay；unbounded 路径保持当前语义。
- 性能：先完成 `perf-015` 当前无边界三阶段基线，再做同设备顺序 A/B/R。P16K Mixed 输出吞吐至少 +1%，A/R 漂移不超过 1%，延迟守护项不劣化超过 5%，代理额外开销不超过 1%。
- 精度边界：本实验不能签发正式 gate；`acc-009` 仍为 174/198。任何长请求命中 bounded 都立即否决机制。

## 当前状态

`planned_protocol_only`。2026-09-24 只读核验 `perf-015` 三阶段原生回执已经完成；这只解除原先“等待其完成”的前置条件，不证明有边界/无边界之间的因果性能收益，更不授权改变当前 8000/8010。当前 acc-011 是 maxseq32、无 M64 tuned folder、FlagGems `mm_out`，而 `perf-014/015` 使用不同身份；须先在当前身份做同卡顺序 A/B/R，并通过 fail-closed 路由协议、边界、graph 与完整精度门禁。长请求或无法证明安全的请求始终只能走 unbounded。
