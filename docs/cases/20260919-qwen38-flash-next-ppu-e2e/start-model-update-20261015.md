# 启动脚本更新（2026-10-15）

后续用户要求进一步简化；下述 87 行版本已被同日的 34 行简版取代。简版来源为 `commands/start-model-simple-20261015.sh`，部署命令为 `commands/deploy-start-model-simple-20261015.yml`。固定 8010 / 卡 0–7，删除参数解析、多端口、dry-run、路径/端口检查、动态日志及状态输出；保留必要 SDK、通信、卷积 fallback、私有 SQLite 修复与模型参数。删除 IB 已禁用时不生效的 HCA/GID 设置、NCCL 日志级别、字节码设置及默认值 pipeline-parallel-size=1。日志改为追加 `/mnt/nfs/users/jinghao/qwen3.8-flash/service2.log`，不覆盖旧日志。该脚本不再支持 `PORT=8000` 或 `--dry-run`。

简版 SHA-256：`c039af5b8782ba45ec67bc243ce8f45f849122a526310de460a71d1a4b7341b7`。复杂版备份位于远端案例目录 `start-model-simplify-20261015-01/start-model.sh.previous`，原始用户脚本备份仍保留在第一次更新目录中。简化操作不启动服务，不构成新的精度验证。已完成部署：`--check --diff` 预检和实际执行均通过，Ansible `failed=0`，容器内 `bash -n` 及新脚本 SHA-256 核验通过。

用户明确要求修改 PPU-01 的 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`。范围仅启动脚本，不拉取或修改推理源码，不启动、停止或重启服务，不执行精度/性能评测。

## 配置依据

原脚本默认 8010 / 卡 0–7 / TP8 / BF16 / 80K 上下文 / max-num-seqs 64，未显式设置 max-num-batched-tokens 或私有缓存修复。依据 acc-011 的 `services/services-runtime.json`，新脚本使用 max-num-seqs 32、max-num-batched-tokens 4096、FULL_AND_PIECEWISE graph、NCCL_IB_DISABLE=1、私有 FlagGems `/opt/qwen38-acc011-cachefix-20260924/FlagGems/src` 和每端口独立的 `port8000.db` / `port8010.db`。私有 sql.py 的实际 SHA-256 仍为 `f20c01b48ba749ff42fe3935466c3e658ea9c89c6dbf5bd9d9155b326dc4de4f`。

默认启动 8010 / 卡 0–7；`PORT=8000` 则启动 8000 / 卡 8–15，每次只启动一个副本。追加 blacklist 保持 `_conv_depthwise2d,index,normal_`，不追加 `mm_out`；清除调用 shell 中的 `VLLM_FL_QSA_STATIC_SCORE_COLUMNS` 和 `VLLM_TUNED_CONFIG_FOLDER`，不恢复被拒绝或回退的实验。日志采用唯一文件名，端口占用则拒绝启动，不自动终止现有服务。脚本预期在优化容器内执行，`--dry-run` 不调用 vLLM。

核对时 Plugin 仍为 `939600b323c02c21916f1f76bfb4cd8c2b02578d` 加已有 dirty patches；此次不将远端较新的提交自动部署到容器。采用历史通过配置不等于当前源码/服务已获得新精度 gate；旧 acc-011 的 175/198 不能自动绑定未来启动实例。

## 变更与备份

- 原脚本 SHA-256：`5ca860e63c9a58a14020901c73575598f6ff212a0e160684a603d65caa784812`。
- 新脚本 SHA-256：`73b84baaf7020e4c55051e40ab3390daba94b789ea1a5931cbe7382780b675ca`。
- 唯一远端归档目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/start-model-update-20261015-01`。
- 原脚本备份：该目录 `start-model.sh.original`；新脚本与部署 playbook：该目录 `commands/`。
- 执行副本保存在上述远端归档的 `commands/`；本地 `commands/start-model-20261015.sh` 和 `commands/deploy-start-model-20261015.yml` 是未纳入仓库的一次性命令副本。

部署前已通过本地 bash 语法检查和 Ansible `--check --diff`，无远端写入；实际部署使用原始 SHA 冲突检查、原文件备份与原子替换。部署完成：Ansible `failed=0`，原脚本备份和新脚本 SHA 校验通过；优化容器内 bash 语法检查、宿主机/容器脚本 SHA 一致性检查、8010 与 8000 两路 `--dry-run` 均通过。未调用模型服务启动分支，未运行精度/性能测试，不签发新 gate。
