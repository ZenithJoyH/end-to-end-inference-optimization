# PPU-07 FlagGems master 更新

后续已按用户要求 [去掉启动脚本 PYTHONPATH 并清理旧 editable 映射](remove-pythonpath-20261015.md)，无 PYTHONPATH 的导入与全部 130 项模型单元测试通过。下文启动脚本 SHA 和默认环境检查属于本次升级当时的证据。

状态：`updated_operator_regression_passed`。已切换生效并完成 editable 安装；用户明确选择“master + 必要 QSA 适配”，不是纯 master。没有启动模型，也没有新增正式精度/性能 gate。

范围固定为 PPU-07 的 `qwen3.8-flash-opt-ppu07-20261015`（容器 ID `378fb2429d4cb36221ab5156d7417e18747c25544954c097c65195aafac21ddc`）。不修改 PPU-01，不启动/重启模型服务，不进行正式 GPQA。原 `/workspace/FlagGems` 非默认导入副本不变。

上游 `flagos-ai/FlagGems` master 于本轮开始核验为 `85cc5efb195edefea284e8ac460840601ca4c02f`，GitHub branch API 与容器 git 远端互证。当前默认导入旧私有目录 `/opt/qwen38-acc011-cachefix-20260924/FlagGems/src`，旧 HEAD `2b1e5cfdbd22d453933b2c6589a29daf31315ccd`，包含既有 QSA 与 SQLite 未提交补丁。该目录和 site-packages 均为容器私有 writable layer，不在唯一 `/mnt:/mnt` bind 中。

方案：先在 `/opt/qwen38-flaggems-master-20261015-85cc5ef/FlagGems` checkout 固定 master，保留现有四个上游尚未包含的模型扩展 `qsa.py`、`ple_state.py`、`gdn_packed_decode.py`、`common_slot_mapping.py`，仅补充 fused 包的 10 个导出。其他通用算子和 SQLite 实现采用 master；不整树覆盖旧代码，不升级 Torch/FlagTree/vLLM，不更改模型权重、Plugin、挂载或启动脚本。先隔离导入和模型单元测试（包括 GPU 算子/graph），再测试新 SQLite 的 8 进程首次建表。全部通过后才将旧私有源码和调优 DB 目录整体移至 `/opt/qwen38-flaggems-backup-20261015-85cc5ef/`，新源码移动到原稳定导入位置并重新 editable 安装。无删除；切换失败自动恢复旧目录、缓存和 editable 安装。

实际 Torch `2.10.0`、vLLM `0.24.0+empty`、FlagTree `0.6.2a1+ppu3.6` 不变。master 的可选 thead 依赖建议 FlagTree `0.6.2a2+ppu3.6`；本轮不静默升级编译器，兼容性结论仅限实际执行的测试。build 使用已安装工具和 `--no-build-isolation --no-deps`，不强制变更 master 的 build-tool 建议版本。

执行与原始证据根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/flaggems-master-update-20261015-01/`。命令副本均在 `commands/`。原补丁仅一行上下文，`git apply --check` 拒绝；没有变更 active 安装。修正版本 `flaggems-master-model-exports-v2.patch` SHA-256 `558e827d46021f6b24f71d872eaf25a11a748c1d7370fd424df0f0beaf92e48a`；staging runner `flaggems-master-prepare-v2.sh` SHA-256 `e46640717364bfb3b1703788891ea14adee5a346b1c58d39fa5c0802675bad9e`；activation runner `flaggems-master-activate-v2.sh` SHA-256 `d632a4c746b628573b8f12ffba6faf41871cbb24c36d7ee37584b320b67e31a5`。本地同目录 `commands/` 保存可复用控制命令。

用户已修改共享 `start-model.sh` 的 graph capture sizes，并移除先前 max-num-seqs/max-num-batched-tokens 限制。实测 SHA-256 `ba3a4d241bd392d69f12adb2cc5cc6d615238e17c86a24654563fd30dc9aeecb`，本轮保留；不以旧脚本覆盖。容器内 `/opt/start-model-ppu07.sh` 原 SHA `183add493a8aeb5bffdebaf4c2af3e2f5deaff530cbbd5df60372f0f77afafd9` 也保留。

测试不能等同模型正式精度、TP8 graph capture/replay 或稳态端到端性能验收；旧精度 gate 不因容器复制或依赖更新而有效。新代码的正式模型验证仍待后续独立执行。

## 完成结果

默认 Docker exec 环境实际导入 `/opt/qwen38-acc011-cachefix-20260924/FlagGems/src/flag_gems/__init__.py`，HEAD 为上述 master，pip 包版本 `5.5.0.dev0+g85cc5efb1.d20261015`。模块自身 `__version__` 多拼接一次 git 后缀，实测为 `5.5.0.dev0+g85cc5efb1.d20261015+g85cc5efb1`；以 git HEAD、pip metadata 和文件内容作为版本证据，未为显示问题引入额外补丁。

- staging 全部模型测试：`130 passed in 27.55s`，覆盖 QSA、PLE、GDN、slot mapping、dispatch、缓存布局及对应单算子 graph capture/replay；设备为物理 PPU8，未使用有其他工作负载的 PPU0–7。
- master 原生 SQLite 实现：8 个独立进程同时首次建表/写入，8 表、全部 exit 0、integrity `ok`。未移植旧 SQL retry 补丁；这只证明本次测试，不能外推完整 GPQA 并发。
- 激活 runner 使用默认 PYTHONPATH 复查了 10 个扩展导出，并再次执行 QSA/dispatch：`21 passed in 13.99s`，最终 `ACTIVATION_PASSED`；完整 playbook `failed=0`。最终容器仅有原来的两个 bash，测试客户端已退出；master `sql.py` 与 HEAD 无 diff，源码 diff 仅为 fused 导出和四个必要扩展。
- Torch `2.10.0`、vLLM `0.24.0+empty`、FlagTree `0.6.2a1+ppu3.6` 保持原值，Plugin 不变。两个启动脚本前后 SHA 均一致，用户的 graph capture 参数保留。
- 旧源码及所有既有修改保留于 `/opt/qwen38-flaggems-backup-20261015-85cc5ef/FlagGems`，原缓存保留于同目录 `caches/`；原稳定路径的 caches 为新版本重新建立，避免旧实现调优记录混用。无材料删除。回退仅能在重新确认目标容器无模型进程后恢复这两个目录，并对原稳定路径重新 editable 安装；激活脚本含失败自动回退，不应重复执行。

原生证据位于上述远端根：

- `runtime-receipt.json` SHA-256 `6defc63a56ba5279a2990af904d9f051b2577cee136915e93b2eaab1b06d8569`。
- `prepare-v2.log` SHA-256 `dd30927ba0f5491876c4c9c00157891178929f6c6c67a9c2a8292c2938a89005`。
- `sqlite-stress.log` SHA-256 `92dfec70d4f7723ea994df29c8689a6fe3ec36e6facc029eb85c3cab7666a3d8`。
- `activation.log` SHA-256 `d66002ea101f95eccbc04ec36582dd1344b70a860d4c25c43a7d82754aeece81`；`legacy-flaggems.patch`、`legacy-status.log`、`master-model-exports.diff` 和 `launch-scripts-before.sha256` 保留切换及回退证据。

`activate-flaggems-master.yml` SHA-256 `b983f88d5855d80bf9666fa6494c1213c263b14f6cdbf238ccc778ee9af0aed4`，执行前经过 `--check --diff`；首轮 check 因只读 inspect 在 check 模式被跳过而失败，修正为显式 `check_mode: false` 后预检及实际执行均成功，失败预检未变更容器。

结论边界：新 master + 4 个必要扩展已生效，算子回归通过；新 master 在该旧 FlagTree 编译器组合上的全模型/TP8 graph/GPQA 与四场景性能仍 `not_run`。原镜像 lineage/mount 交付证明仍为历史事实，但升级后的 FlagGems 已与 PPU-01 分叉，不再声称源码与源容器相同。`pr_readiness=experimental`，本轮不提交或推送代码。
