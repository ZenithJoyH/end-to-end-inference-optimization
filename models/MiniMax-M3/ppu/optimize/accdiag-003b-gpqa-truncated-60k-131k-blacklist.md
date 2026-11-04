# accdiag-003b：131K + T-Head YAML 黑名单下重跑 GPQA 截断实例

## 目的与边界

- 从头重跑 `accdist-001` 三轮中的 64 个 30K 截断 `(request_seed, doc_id)` 实例，共 31 道不同题。
- 客户端 `max_tokens=60000`、并发上限 64；服务端 `--max-model-len=131072`，覆盖已观测的最大 `prompt + generation = 62637`。
- 该轮是截断根因诊断，不是 198 题正式 gate；不合并首次 65K 运行已完成的 1 个响应。

## 服务变更

- 仅修改独立优化容器内的 `/workspace/vllm-plugin-FL/vllm_fl/dispatch/config/thead.yaml`。
- `flagos_blacklist` 增加 `conv3d` 和 `cudnn_convolution`：前者覆盖直接入口，后者是本次 T-Head 实际命中的 wrapper 注册名。
- 131K 服务已通过原失败点、6/6 graph capture、health 和北京 smoke；服务实例为 `bd37abcbf719:8023:895010:279945667`。

## 证据

- 评测根：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accdiag-003b-gpqa-truncated-60k-131k-blacklist`
- 服务日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op003-thead-yaml-entrypoint-131k-server.log`
- 启动门禁：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/results/op003-conv3d-blacklist`
- 切换证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/op003-thead-yaml-entrypoint-maxlen131k`

## 状态

- 评测完成：64/64 成功，0 error，0 空输出；33 个 `stop`，31 个在 60000 tokens 处再次 `length`截断。
- 截断子集正确数由 20 增加到 39；23 个由错误翻为正确，4 个由正确翻为错误，净增 19。
- 这是定向诊断而非 formal gate；后续使用同一 131K/60K 配置进行 `accformal-004` 全量 198 题正式评测。
