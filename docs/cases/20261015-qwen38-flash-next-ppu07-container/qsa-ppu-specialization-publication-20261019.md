# QSA PPU 特化代码发布（2026-10-19，侧对话）

## 范围与结果

用户在本侧对话明确要求在 `ZenithJoyH/FlagGems-vllm` 新建 fix 分支，提交现有 QSA 平头哥后端特化。
仅发布现有四文件补丁，不继续主任务的实验或更改模型运行环境。

- 分支：[fix/ppu-QSA](https://github.com/ZenithJoyH/FlagGems-vllm/tree/fix/ppu-QSA)
- 提交：[1936bdda5eccea99bb74890adb853e5f9c23cb4a](https://github.com/ZenithJoyH/FlagGems-vllm/commit/1936bdda5eccea99bb74890adb853e5f9c23cb4a)
- 父提交：`65680392edfdd566a8c8e3cd99cba18e4dc3c26b`，即现有已验证安装的上游基线。
- fork 的 main 尚无这批 QSA 算子，故不从旧 main 重建实现，也不更新 main。
  发布后复验 main 仍为 `46a81d39732af0e1b0ef6c474e500591dfb2d124`。
- GitHub compare 复验：相对父提交仅 ahead 1 commit、四个预期文件。
- 没有创建 PR；没有修改容器、服务、Plugin、FlagGems、i64 修复或当前主任务记录。
  未访问 8035，也未发模型/算子请求。

## 发布内容

公共 helper 接收私有 `min_block_m` 参数，generic 默认仍为 8；PPU `_thead` wrapper
传入 16，覆盖 single/split 两条路径，较大 group 仍取 next power of two。
原有三个 Triton kernel body 和公共接口不变，无 Torch compute fallback。
新增 metadata-only 路由/ABI/CPU unsupported 测试；不包含诊断埋点或其他优化。

源为 PPU-07 容器 `qwen3.8-flash-opt-ppu07-20261015` 中现有安装
`/opt/qwen38-fgvllm-main-20261016-6568039`。只读核验该仓库 HEAD 和 dirty 集合，
四文件哈希与 op-019 历史验证记录逐一相同；通过只读文件传输取回本地独立暂存目录。
未切换远端分支或写入远端源码。

| 文件 | SHA256 |
| --- | --- |
| `src/flaggems_vllm/ops/qwen4/qsa_attention.py` | `89c0bb3e47fedfb7ef73512ceff6fe4d464863a296e874eadb411a54342efb42` |
| `src/flaggems_vllm/runtime/backend/_thead/fused/__init__.py` | `3a39c83ff755767fd0a0cc200853c6d3e9ead5030153387e3232a2272a43c87a` |
| `src/flaggems_vllm/runtime/backend/_thead/fused/qsa_attention.py` | `3bb3d08342ac47415c62c5c11b2d88b85aa8fe9701d48890b5a8751b88db895a` |
| `tests/test_qsa_thead_attention.py` | `4b66d865be871bcd8e153b4e92ad54f37e1bdd0d80451835e4e623950ea00ba4` |

## 验证与限制

- 本次 CPU-only 静态检查通过：四 SHA、Python parse/compile、空白、三个 JIT kernel AST
  与父提交相同、公共接口相同、generic M8/PPU M16 与 split 参数透传。
- `git diff --no-index --check` 无空白诊断（no-index 因存在正常差异返回 1）。
- 发布后通过 GitHub 按新分支重新读取四文件，内容与取回文件逐字相同。
- 沿用同一源码历史验证：14 项 CPU 路由检查及 12 次有界 PPU QSA API 事务，
  其中 10 份实际数值输出零超容差，最大绝对误差 0.0078125，包含 capture 和两次改变输入/索引 replay。
  详细范围见同模型 `optimize/op-019-fgvllm-integration.md`，不冒充本次重跑结果。
- 本次不运行 GPU、模型、GPQA 或性能测试。本机无 torch/triton/pytest 和格式工具，未安装依赖。
  不宣称新增精度 gate、性能收益、非 PPU 硬件验证或完整 PR readiness；历史未测项仍保留。

连接仅限 PPU-07；首次沙箱内 connectivity-check 的本地 Ansible RPC 启动失败，
经针对同 Host 的权限审查后重试成功（ok3/changed0/failed0），未将失败当连接通过。
本地暂存和审计脚本：`/private/tmp/ppu-qsa-publication.ucdDrx/`，不纳入远端提交。

## 同日按用户要求调整提交并对齐官方 main

用户明确要求调整该笔提交，并将修复分支对齐 `flagos-ai/FlagGems-vllm` 的 main。
新提交为 [7d0c41f1cf9f130a29d52d8c835651771241183f](https://github.com/ZenithJoyH/FlagGems-vllm/commit/7d0c41f1cf9f130a29d52d8c835651771241183f)，
直接父提交是本次查询且发布前复验未变的官方 main
`46387d7f96050204c1b932f35680a3ea03896fa6`。
以 `expected_sha=1936bdda5eccea99bb74890adb853e5f9c23cb4a` 的 force-with-lease
更新同一 `fix/ppu-QSA` 分支，发布后复验该 ref 与四文件内容均匹配。
旧提交保留作历史记录，不再是分支头；没有更新 fork/main 或创建 PR。

- 移除独立的 `tests/test_qsa_thead_attention.py`（新树确认不存在），将路由/ABI/CPU unsupported
  用例并入已有 `tests/test_qsa_attention.py`。
- 原数值/graph 测试改用包级公共导出，实际遵循 vendor replacement；generic 模块仅用于元数据对照。
- 元数据组大小增加 17，验证向上取 32 而非固定 16；PPU 专用用例在非 thead 后端跳过，
  非 PPU 不导入 thead 后端模块。
- 官方 main 的公共 QSA 与 thead 导出文件和旧基线相同，无实现冲突；生产三文件仍与前次发布逐字相同。
- 使用原版 `tools/select_tests.py` 的实际函数，核验 common 和 thead QSA 源码均能选择
  `tests/test_qsa_attention.py`，无需另改 CI 映射或 capability allowlist。
- 相对官方 main 恰为一笔提交、四个预期文件，ahead1/behind0，未夹带上游之外的其他补丁。

本次检查：Python syntax、空白、ABI、三个 kernel AST 保持、CI 选测通过。
另以实际 wrapper/test AST 配合纯 CPU 张量元数据桩进行模拟：thead 18 passed/0 skipped，
非 PPU 10 passed/8 skipped。该模拟不加载真实 torch/pytest/Triton，不生成数值结果，
不能当作硬件测试或完整 pytest 通过；本次未重新进行设备数值、graph、模型、性能验证。
本地暂存/审计：`/private/tmp/ppu-qsa-align.WzGY9O/`。
本轮没有任何远端机器连接或运行环境变更，未访问 8010/8035。

## 同日按用户明确要求向官方提交 PR

已创建正式非 draft PR：[flagos-ai/FlagGems-vllm#940](https://github.com/flagos-ai/FlagGems-vllm/pull/940)，
标题 `fix(thead): enforce a 16-row minimum tile for sparse QSA`。
目标 `flagos-ai/FlagGems-vllm:main`（创建时 `46387d7...`），
来源 `ZenithJoyH/FlagGems-vllm:fix/ppu-QSA`（`7d0c41f...`），
核验为 1 commit / 4 changed files，状态 open，未合并。

初次含本地验证明细的正文被发布风控拒绝；未绕过工具或上传原始证据。
缩减为仅引用已公开提交及 diff 的说明，同一创建接口成功，未出现重复 PR。
正文明确不宣称新硬件/模型/性能验证，CI 和 review 尚待完成；没有新增标签、评审人或合并动作。
App 的 PR 附件登记尝试返回本侧对话 `thread not found`，不影响 GitHub 上 PR 已成功创建。
未为此操作访问服务或改动模型环境。

## PR #940 首轮 CI 与纯格式修复

用户报告 CI 失败后只读核查：`basic ci` run `39189320473` 的 `code style`
job `117858409057` 仅 Black 失败，要求将新增元数据测试的一处 `function(...)`
调用展开为多行。Flake8/isort 均通过；`multi-backend summary` 连带失败，
选测及硬件任务 skipped，不能称作设备数值测试失败。rule-check/CLA 通过。

用户随后明确要求直接修正并推送当前 PR。追加纯格式提交
[a964fb0762eb6bea34e8b9e40c83ae9fb3671c0e](https://github.com/ZenithJoyH/FlagGems-vllm/commit/a964fb0762eb6bea34e8b9e40c83ae9fb3671c0e)，
父提交为 `7d0c41f...`，仅 `tests/test_qsa_attention.py` 加8行/删1行；
完整模块 AST 前后相同。修复 blob `d5249fe79c0a703f767956f568785e94e433d489`
与 CI Black diff 给出的结果前缀一致。

在独立临时 venv 安装 CI 固定版本后，真实执行并通过 Black24.8.0、isort5.12.0、
flake8 7.1.0 检查。临时目录不含完整包布局，初次 isort 把 first-party 包识别为 third-party；
指定实际已取回的 `src` 路径后通过，未因此更改原导入顺序。
未修改共享 Python 或容器；无 GPU/模型测试。
沙箱内初次 pip 因 DNS 不可达失败，经本次操作权限审核后只向该临时 venv 安装成功。

通过 expected head=`7d0c41f...`、force=false 快进同一分支，未重写历史；
随后 GitHub API 确认 PR #940 head 为 `a964fb0...`。新 CI 结果单独核查，
本地格式通过不冒充全套 CI 通过。暂存/检查脚本位于
`/private/tmp/ppu-qsa-blackfix.3OUsAH/`，不进入 PR。
