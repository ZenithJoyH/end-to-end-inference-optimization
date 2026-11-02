# #7075 当前容器复现与实际日志补充

用户于 2026-10-13 明确允许公开模型、硬件、运行环境、实际输入 shape、版本和完整错误日志，并要求补充到 FlagGems #7075。该授权适用于此 issue；不涉及凭据、密钥或其他任务数据。

本轮在 PPU-01 的 `qwen3.8-flash-opt-candidate-20260919` 做独立进程诊断，使用只读核验为空闲的物理 PPU0。先跑 native，再跑直接 FlagGems generic conv1d；每个进程只允许 8% 的 96-GiB 显存，使用实际 BF16 `[7,10240,3644]`、weight `[10240,1,4]`、groups10240、dilation3。该预算模拟原服务的剩余显存；不能据此断言空闲整卡、无预算时也会 OOM。不会启动或重启模型服务，不修改运行源码，也不执行历史非法访问 kernel 的另一次复现。

远端新目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/conv7075-current-env-repro-20261013`。父目录 canonical、owner UID0、0775、空余约8.28TB；新目录不存在。脚本在执行前保存于本案例 `commands/conv7075-current-env-{repro,host}.py` 并复制到远端 `commands/`，结果与完整进程日志写入远端 `results/`。autotune DB 和 Triton cache 指定到该目录；FlagGems 生成的 Python pad wrapper 仍从其运行时 `/root/.flaggems/code_cache` 路径加载，不能将其误写为所有缓存均已隔离。

远端控制命令：`python3 /mnt/nfs/users/jinghao/qwen3.8-flash/20260919-qwen38-flash-next-ppu-e2e/conv7075-current-env-repro-20261013/commands/conv7075-current-env-host.py`。host 脚本在两个模式前后检查 PPU0 的显存占用不超过64MiB且util为0，不满足时拒绝启动。

历史证据来自适配容器 `/bug/flaggems-depthwise-conv-padding-20260904/`，完整日志和 SHA 已重新只读读取：

- `eager-v2.log`: `030a0b2226aea606154abdcdfcb4e5780371bd6271e3d87f50db6af0eeeea92a`。
- `graph-v2.log`: `acdcc84cd1a023415d38c0939fff1fc1a940d327abd74fe0c503f73a19c28cc8`。
- `nested-conv.log`: `ffa16b7a49c22ddb4d729cf78ef1dd6110205559a3d21ffed94ef4bd116f3f5c`。

状态：completed_reproduced_allocator_oom。host 控制命令正常退出，两次独立诊断前后 PPU0 空闲检查通过。

当前运行版本：FlagGems 实际源码 HEAD `2b1e5cfdbd22d453933b2c6589a29daf31315ccd`、导入 `/workspace/FlagGems/src/flag_gems/__init__.py`，distribution metadata 为 `5.3.5+g38653f94c`，实际 source HEAD 优先于 editable 安装元数据。PyTorch `2.10.0`、Python `3.12.3`；Triton 模块 `3.6.0`，由 FlagTree `0.6.2a1+ppu3.6` 提供；PPU-ZW810E 96GiB、PPU-SMI1.28、driver2.1.1-rbd225。`conv2d.py` SHA-256 `290a77432d169331d594a59696d61e6b020ed65ce0e1d1a18ece3b669ff391e7`。源码仅有不相关的既有 `qsa.py` dirty，卷积源码未改变。

| 独立进程 | 结果 | 内存与证据 |
|---|---|---|
| native | success，输出 `[7,10240,3635]` | 额外峰值 `521113600` bytes；`native.json` SHA `3fd8d34a498fac9f7ba504e8c3d010c48589fbe8ccb8e8f8bce6c32d5e72d9d4`；`native.log` SHA `4b1a7902991b97a709feba076ae264731a555ead10c4e58608bf3281c63d00f0`。 |
| direct generic FlagGems | expected OOM | 请求7.79GiB、进程预算7.68GiB；`conv2d.py:407 -> F.pad -> constant_pad_rank_5.py:28 torch.empty`，卷积 kernel launch 前失败；`gems.json` SHA `9d469f22af2835be92466672617230eb6ce7a7d4bf02abe66ac51eddcb8267aa`；`gems.log` SHA `8c3206a2946e43a161fa331c38ec98d1e7eb6060e643ea9c09b1c691c325127a`。 |

脚本 SHA：repro `7866d1f3724a05d67a7b7740870045af9ebc60af05fb835fb2fe6ba9af7fae54`；host `91fe6583576e4db159b9cda0e52cad50e5ca98375ce0c67b164840f618dc9ac6`，远端与本地一致。

已公开补充到 [#7075 comment 6141950812](https://github.com/flagos-ai/FlagGems/issues/7075#issuecomment-6141950812)：实际 shape、历史/当前版本、当前原生/FlagGems 对照、actual-shape case、两份当前完整进程日志和三份历史完整日志。只有当前日志中带用户名的复现目录前缀规范化为 `/path/to/repro`；所有错误信息和栈帧保留，SHA 对应规范化前原文件。issue 主文增加摘要与该补充链接，并 read-back 确认发布成功。

结论边界：本轮复现的是当前 generic path 在明确预算下的临时分配 OOM。空闲96GiB整卡取消预算后未重测，不能断言必然OOM；也没有声称新的 upstream T-Head 专用 kernel 失败。原先公开的CPU示例只证明16倍存储放大，不能将它当成GPU算子OOM复现。
