# 已验证源码的远端提交核对（2026-10-13）

用户要求将当前已经验证的修改提交到此前指定的远端仓库。核对 PPU-01 优化容器 `qwen3.8-flash-opt-candidate-20260919` 的源码差异、实验记录和 GitHub 当前分支后，确认可交付修改已经由现有提交覆盖。本次没有创建重复提交、推送新分支或改动运行服务。

| 仓库与目标分支 | 已核验远端 HEAD | 覆盖结果 |
|---|---|---|
| `ZenithJoyH/vllm-plugin-FL` / `support-qwen3.8-flash` | `45b24bc7748720e0022a72e47a983398ddda36d3` | 已包含 T-Head common-slot graph 完成同步、三处 async-ready event 的平台限定 factory 及对应测试。当前在线源码仍从旧 HEAD 加 dirty patch 导入；远端源码已有后续 metadata 生命周期整理，不能直接用旧工作树文件覆盖。 |
| `ZenithJoyH/FlagGems` / `support-qwen3.8-flash` | `5e17bf1c29acba33463c7e98329ce3cba72f6e92` | 已包含 SQLite 有界等待、锁专用 retry 和测试；远端 `sql.py` blob 与私有运行源码完全一致。 |
| `ZenithJoyH/FlagGems-vllm` | 当前运行 HEAD `5865ed53b183e6d3aff69ad1823622a11679d257` | 运行工作树无修改，没有需要提交的补丁，因此无需创建用户指定的条件性分支。 |

FlagGems `src/flag_gems/utils/models/sql.py` 的本地与远端 Git blob SHA 均为 `b4e3a32d74a2c34126f9dc9ec8098b6127c8fad3`。对应已验证证据是八进程 first-use SQLite 压力复现及 acc-011 全量 GPQA；见本案例 `accfix-001`。旧 GPQA 回执仍受服务绑定限制，本次源码提交核对不签发新精度 gate。

Plugin 当前 dirty 内容中的 QSA 静态 score cap 与 runtime tightening、FlagGems `qsa.py` cap 接口属于已回退或待验证实验，不纳入交付。远端 Qwen 模型文件在相关段落没有该静态 cap 配置；其 blob 为 `7e4a74ef6bf69f9cfb4009b2353b46a80a5271d2`。native `mm_out` 的最小回归失败候选没有被提升为默认配置。`.orig` 文件未提交。

核对方式：限定 PPU-01 的连接验证与 Git 状态读取；`git ls-remote` 精确检查两个目标分支；GitHub connector 读取固定 commit/ref 的源码与提交。只有只读核对，无新的代码变更，未重新运行模型精度或性能测试。

远端链接：[Plugin 分支](https://github.com/ZenithJoyH/vllm-plugin-FL/tree/support-qwen3.8-flash)、[FlagGems 修复提交](https://github.com/ZenithJoyH/FlagGems/commit/5e17bf1c29acba33463c7e98329ce3cba72f6e92)。
