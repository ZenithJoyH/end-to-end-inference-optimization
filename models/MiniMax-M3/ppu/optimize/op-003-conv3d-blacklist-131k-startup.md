# op-003：FlagGems conv3d 黑名单与 131K 服务启动

## 假设与证据

- 未加黑名单的 `max_model_len=131072` 服务在 `determine_available_memory -> profile_run -> MiniMax-M3 video tower -> F.conv3d` 路径进入 `/workspace/FlagGems/src/flag_gems/ops/conv3d.py`，随后在 Triton autotune/event timing 中触发 PPU illegal memory access，服务未 ready。
- 用户指定在 Plugin 的 T-Head 平台配置 `vllm_fl/dispatch/config/thead.yaml` 中加入该算子；配置将由 `get_flag_gems_whitelist_blacklist()` 解析并传给 `flag_gems.enable(unused=...)`。

## 单变量改动

- 服务基线：`fw-006`、TP16、BF16、AABS0、prefix cache off、graph sizes 1/2/4/8/16/32、`max_model_len=131072`。
- 完整失败栈证明 `F.conv3d` 在 T-Head 上的真实注册入口是 `cudnn_convolution`，该 wrapper 再调用通用 `conv3d`。因此候选只在 `vllm_fl/dispatch/config/thead.yaml` 的 `flagos_blacklist` 增加 `conv3d` 和 `cudnn_convolution`，分别覆盖直接入口与实际 wrapper 入口。
- 服务显式设置 `VLLM_FL_CONFIG` 指向同一 `thead.yaml`，确保 API 与 spawned worker 的早期配置读取一致；不使用算子黑名单环境变量。
- 预期行为：FlagGems 不注册 `conv3d`，PyTorch/平台原生路径接管；不修改 FlagGems kernel 源码，不影响其他算子 dispatch。

## 验证门禁

1. 启动日志明确记录 `[FlagGems] Disable ... conv3d`。
2. 原先失败的多模态 dummy profile 完成，不再进入 FlagGems `conv3d.py` 错误栈。
3. 6/6 graph capture、health 和北京 smoke 通过。
4. 之后从头运行 `accdiag-003` 的 64 个 60K 请求；该精度诊断同时作为目标服务的长上下文正确性观察，但不构成正式 gate。

## 回退

- 使用已验证的 `minimax-m3-accdiag003-65536-service.sh` 恢复 65K 服务；黑名单仅存在于候选服务进程环境中。

## 证据路径

- 原始 131K 失败日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/accdiag003-131k-server.log`
- 候选日志：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/logs/op003-conv3d-blacklist-131k-server.log`
- 切换证据：`/mnt/nfs/users/jinghao/minimaxM3/20260921-minimax-m3-ppu-e2e/transitions/op003-conv3d-blacklist-maxlen131k`

## 结果

- 仅加入 `conv3d` 的首次 YAML 尝试仍命中 `runtime/backend/_thead/ops/cudnn_convolution.py -> flag_gems.ops.conv3d`，由此确认实际 wrapper 注册名。
- `thead.yaml` 最终 blacklist 为 `[conv3d, cudnn_convolution]`；配置解析验证二者均不允许，`linear` 仍允许。
- 131K 服务成功越过原多模态 dummy profile 失败点，服务日志中 `illegal memory`、`Engine core initialization failed`、`cudnn_convolution.py` 和 `flag_gems/ops/conv3d.py` 命中均为 0。
- 6/6 graph capture、health 和北京 smoke 通过；服务实例 `bd37abcbf719:8023:895010:279945667`。
- 决定：为 `accdiag-003b` 保留；当前证据证明启动问题修复，不代表该 blacklist 已完成正式性能或全模型精度验收。
