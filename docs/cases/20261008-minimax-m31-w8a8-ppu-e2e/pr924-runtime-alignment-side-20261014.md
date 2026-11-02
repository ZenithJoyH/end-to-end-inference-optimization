# PR #924 容器 MoE 环境对齐（侧对话）

用户于 2026-10-14 在侧对话明确要求基于当前 PR 对齐容器环境，随后自行运行端到端性能测试。本次仅部署该 PR 的 MoE 实现，不继续主任务评测、控制队列或自动化。

- Host：PPU-07，inventory/单机 connectivity-check 通过。
- 目标：minimaxM3.1-opt-20261008；镜像 sha256:78d8e42f2f21568667fd8727be790073b34f2683de2d9c2b734813aaf3b5a8fe。
- 挂载：唯一 `/mnt` bind；本次源码与 site-packages 均位于容器自身 overlay，未更改挂载。
- PR：https://github.com/flagos-ai/FlagGems-vllm/pull/924 ，已验证提交 fb70fd23462d411e3131c011ac8434073237e927。
- 原实际源码：`/workspace/FlagGems-vllm`，HEAD 1f9ac0e0caf3c32111f6be44c8e4d2fef2359546，有已适配与优化改动，完整保留未修改。
- 新私有源码：`/workspace/FlagGems-vllm-pr924-fb70fd2-20261014-side-01`。这是原有效源码副本叠加精确 PR MoE 文件，并非整个仓库 git HEAD 更新为该 PR。

## 部署范围

四个 PR 文件与公开提交/本侧硬件验证包 SHA 一致：vendor fused_moe.py、vendor ops/__init__.py、现有 tests/test_fused_moe.py、benchmark/test_fused_moe_int8.py。

同步 PR 基线的 generic ops/fused_moe.py，满足复用既有 INT32_DOWN 的依赖；generic alignment 本来就与 PR 基线相同。新副本排除整理前的两个独立 vendor MoE/alignment 文件及其旧测试，原目录中这些文件仍保留。全部其他 src 文件逐文件验证与原有效源码相同，包含 MiniMax QK/RoPE 接入与 SwiGLU workspace 非重叠兼容修复。Plugin、FlagGems、vLLM 与编译器未变更。

在回归通过后原子切换容器私有 `__editable__.flaggems_vllm-0.1.0.pth` 与 direct_url.json。未增加启动环境变量，未修改根启动脚本。新 Python 进程无需 PYTHONPATH override，包级三个 MoE API 已实测导向新副本的 `_thead/ops/fused_moe.py`；Plugin bridge 仍通过 FlagGems-vllm 解析入口。

## 验证与生效边界

PPU12 独占验证准入通过，部署副本运行完整 fused_moe 与现有 swigluoai_uninterleave 测试：167 passed，78.85s。MoE graph capture/replay 回归包含在测试中，实际导入和兼容导出核验通过，验证后 PPU12 无 compute process。

源码快照证明原三个仓库 revision/status/diff 与原 FlagGems-vllm src 内容在操作前后不变。当前 8035 TP8 模型服务未被重启，仍为更新前的常驻 Python 实例；用户须先停止旧模型服务，再在目标容器使用原 `/mnt/nfs/users/jinghao/minimaxM3.1/start-model.sh` 启动，之后进行压测。启动脚本保持用户现有端口 8035、served-model-name MiniMax-M3.1-opt3、TP8 配置。

本次不包含模型服务重新 capture、逐 worker 运行路径证明、smoke、正式 GPQA 或模型端到端性能验收；不能把部署回归当作这些验收，旧精度 gate 不自动绑定此新源码。

## 归档和回退

远端目录：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e/deployments/pr924-fb70fd2-20261014-side-01`。

控制命令：同 case 的 `commands/pr924-runtime-align-20261014-side-01.py`，SHA256 bc921649699fd5f19a181d11047dc71baee7e6d70055674cba388d536e245dba。

回退命令：同 case 的 `commands/pr924-runtime-rollback-20261014-side-01.py`，SHA256 87c52696bbc07decf2913a6226b0a50fd7047a59cbf5e47866e91bdb75d9b7cd。仅在 editable 路径仍属于本次部署时恢复归档的 `.pth` 和 direct_url.json，不删源码、不改变服务；下次重启恢复使用原副本。

原生回执：result.json 状态 aligned、functional passed、runtime_import verified_without_PYTHONPATH_override、service_restart_required=true。

| 证据 | SHA256 |
| --- | --- |
| result.json | 5823abe0c7059fa460d24781782036fc1bae10d6a7c89a7f22d1a64a643b2caf |
| before.json | 4e0bdea0217b67fca32ef2691dfbd9e3a35e0eab3200be0ef4adfd430576adad |
| after.json | addf7b7951fc2787a37d7d7e2e177ece6fad080d720cd2121ce6df95aad77b54 |
| functional.log | 0b8b91cc2c479615a667a13450b5a762f1e36f5085f87876273902ece45922df |
| runtime-verify.log | 4f7adb53bfcce6158687edebca575cd3bfe0c5f852d36a19a91dbd2772ed11db |

只创建本侧独立记录，未更改主任务 optimize/state.yml、评测门禁或排队流程。
