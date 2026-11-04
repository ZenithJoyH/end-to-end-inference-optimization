# accdiag-003：GPQA 30K 截断实例改用 60K 重跑

## 目的与边界

- 仅重跑 `accdist-001` 三轮中 `usage.completion_tokens == 30000` 的原生 strict-match 实例，判断 30K 输出上限对错误与无效答案的贡献。
- 共 64 个 `(request_seed, doc_id)` 实例、31 道不同题；保留每轮原始 prompt、选项排列、request seed 和 sampling 参数。
- 唯一请求变量为 `max_tokens: 30000 -> 60000`。按用户要求核验服务端长度：131072 启动尝试在多模态 dummy profile 的 FlagGems `conv3d` 中触发 PPU illegal memory access，未进入 ready；随后恢复已验证的 `--max-model-len=65536`，它覆盖本轮最大总长度 62637 并留有 2899 tokens 余量。其余服务参数和 `fw-006` 候选不变。
- 本轮是输出截断根因诊断，不是 198 题正式 gate；服务身份与配置变化后，旧 gate 不再绑定。

## 预检

- 模型 `text_config.max_position_embeddings=1048576`。
- 64 个实例的 prompt 为 358–2637 tokens，最大 `prompt + 60000 = 62637`；服务端 65536 有 2899 tokens 余量。
- 131072 服务尝试未通过 readiness，未发送评测请求；失败日志保留为诊断证据。
- 来源三轮截断数分别为 20/20/24，31 道题并集、12 道题三轮交集。

## 请求契约

- endpoint：`http://127.0.0.1:8023/v1/chat/completions`
- `temperature=1, top_p=0.95, top_k=20, stop=["</s>"]`
- 并发上限 64；服务 `max_num_seqs=32`，由服务调度排队。
- 请求超时 14400 秒；每个实例独立保存完整响应、usage、finish reason、答案提取、hash 和错误。

## 证据

- 远程根：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/accuracy/accdiag-003-gpqa-truncated-60k`
- 131K 失败切换：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/accdiag003-maxlen131k`
- 131K 失败日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/accdiag003-131k-server.log`
- 65K 恢复切换：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/accdiag003-maxlen65536-fallback`
- 65K 服务日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/accdiag003-65536-server.log`

## 状态

- 首次 65K run 按用户要求在 1/64 完成后停止，已有响应保留；随后切换到 131K + T-Head YAML blacklist，从头建立 `accdiag-003b-gpqa-truncated-60k-131k-blacklist`。本文件保留为首次尝试记录。
