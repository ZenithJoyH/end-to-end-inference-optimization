# eng-076 当前Plugin适配补丁PR收敛

**2026-11-02T12:23:42.984811+08:00 已将13文件候选发布到原[Plugin PR #573](https://github.com/flagos-ai/vllm-plugin-FL/pull/573)，head `0dc1d64e2860c1aa2a6841db97baf924ec18ea37`；与main无冲突，保留历史且未force-push。209 pytest CPU+8 CPU graph生命周期契约、13文件lint/format/pre-commit通过。算子依赖未合入，草稿跳过必需CI作业导致gate失败；仍非完整CI/设备/模型验收。未部署/重启，定时任务保持删除。以下11:47等为历史。**

**2026-11-02T11:47:44+08:00 依赖核对完成：复用既有算子PR，已更新现有Plugin草稿#573的合入依赖说明并精确读回；没有新建重复PR或提交/推送源码。当前13文件候选仍为未部署的format-v4，未推到旧#573 head。详见文末。**

本轮用户允许直接发布所需算子修复PR，并要求Plugin PR说明依赖其合入，同时指出可能已有PR。先通过GitHub原件核对已有#959/#982/#989、FlagGems #7582/#7270与当前2+6处保留差异，不重复发布已覆盖的修复；QSA #940与index_put #6892已合入另列。若覆盖完整，复用原PR并仅补现有Qwen草稿Plugin #573的依赖说明，保留其原代码/验证描述且明确当前eng076候选未推到该旧head；不推送Plugin代码、不改变任何部署或服务。依赖合入前仍保留merge blocker，不能用PR存在代替固定公共组合安装/验收。

v4设计（已完成，结果见文末）：从未加载v3派生candidate-format-v4，不改canonical源码。固定Ruff0.14.0/原pyproject格式化五大文件，不改配置或增加忽略。四文件含类型注释AST在忽略源码位置后完全一致；runner除两个既有I001导入分组整理外AST一致，保持首次模块导入顺序、导入绑定集合和全部注释。已核实涉及的原生导出为既有普通模块属性，重新运行155 CPU契约及原pre-commit，最终13文件显式lint/format通过。无模型/设备验证、部署、服务动作、8035或提交推送。以下v3结果保留为父候选证据。

本轮继续视频loader模型隔离，仅从candidate-tests-v2派生未加载candidate-video-v3。设计采用当前vLLM公开VideoLoaderRegistry和模型media_io_kwargs入口：专属子类复用原生采样/解码，复制本模型配置并选择专属backend，移除共享Qwen3类的全局FPS wrapper。共享原类、qwen3_vl注册和processor映射必须保持；显式其它backend及请求覆盖保留原优先级。兼容签名、注册冲突先检查，失败回滚专属注册；既有processor FPS/pruning校验保持。

验证先检查同进程初始化前后共享方法identity与非法FPS异常不变，再经真实MediaConnector同步/异步和VideoMediaIO验证路由、转发、metadata、失败无重试与配置隔离。适用Plugin A2/C1/C2/C3/D1/F1/F4/F7。无部署、模型请求、GPU、重启、8035或提交推送；CPU证据不替代codec、硬件/graph或模型验证。

**最新结果：2026-11-02T11:18:37.546830+08:00 五文件格式v4收敛完成，155 CPU、最终13文件显式lint/format及pre-commit通过；原5文件格式债已关闭。最新未加载候选 `/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate-format-v4`。11:19只读回读线上保持，pr_readiness仍needs_revision；最终diff、等价性和剩余问题见文末。以下v1/v2/v3为历史。**

- 结果：**完成一轮隔离候选代码收敛，未部署；pr_readiness=needs_revision。**
- 分类：framework / 工程整理；正式场景/性能不适用本轮，无新的模型精度结论。
- 用户授权：2026-11-02要求按最新Plugin PR要求收敛当前适配代码；不推断为重启、模型流量、GPU测试、机制埋点或提交推送授权。
- 父树：当前Plugin固定主线40f992dcae2a2e28bea83d9536b4347acb90bd18加原14路径适配修改；候选13路径。canonical `/opt/vllm-plugin-FL` 及其687源码成员保持原样。
- 候选：`/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate`；外部交付：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-076-plugin-pr-cleanup-20261102`。

## 优化方向与设计依据

本轮按本项目最新 `docs/plugin-change-review.md`、`docs/plugin-development-standard-v1.md` A1–G2审查剩余适配差异，没有升级主线或依赖。规范是用户工程要求，不冒称已经核实上游维护者的新PR意见。先复制当前真实源到独立未加载副本，保留原Git HEAD及修复；所有改变只发生在该候选。无模型、平台或算子新适配，无新数值kernel或平行dispatcher。

## 实际收敛内容

1. **去掉重复配置内容。** 原本将上游 `E=256,N=512,device_name=nvidia.json` 符号链接物化为146行普通文件；实核该文件和被链接目标SHA均97ccbad3a1933385e777d0817618edecbb80ff528b412e353c89c728d7d90193。候选恢复上游链接，字节/配置值不变，14个本地差异路径减为13。
2. **视觉选择先校验再改绑定。** PPU请求不支持后端时在安装全局OOT patch之前抛出错误；新增用例断言失败路径没有安装副作用。视觉绑定明确排除T-Head的NVIDIA分支，新增is_cuda=True的PPU反例，避免把CUDA形状API当NVIDIA能力。
3. **视频兼容补丁明确ABI与失败边界。** 安装前验证原生classmethod及可转发kwargs，接口不兼容时原对象不变；`functools.wraps`保留可审阅签名及wrapped原对象；重复安装不叠wrapper，执行期错误原样抛出且不重试。仍保留原FPS与pruning拒绝规则，未改有效视频的采样公式。
4. **工程一致性。** 新增/修改适配文件补齐版权/SPDX；Qwen3.8 patch改用目标项目init_logger。MoE测试不再将必需依赖ImportError静默转skip，增加provider执行出错只调用一次、无其它backend重试和无输出写入断言。
5. **修复与边界保留。** Mamba分组、RNG offset helper、runner以及模型主体四文件SHA与线上完全相同；没有改BF16/FP32状态dtype、既有MoE数学/选参、cache、graph或采样语义。

交付按主题拆成三个互不重叠patch：多模态6文件、PPU MoE接线及测试2文件、runner状态所有权5文件。组合源687成员；工程过程、PR正文、检查日志都在外部工程目录，没有塞入Plugin README/docs。临时CPU工具和reviewer工作树不在Plugin patch内。

## 正确性、路径与工程检查

| 检查 | 结果 | 边界 |
|---|---|---|
| 最终cpu-003 | **67 passed，0failed/errors/skipped** | 清洁PYTHONPATH，实际候选Plugin/当前canonical FlagGems与FlagGems-vllm；CUDA未初始化 |
| Mamba与RNG | 原CPU状态/offset生命周期用例保留 | 真实CPU tensor/native copy planning/reference；实际设备memcpy被CPU substitute，不能代表GPU kernel |
| MoE与多模态 | 真实业务方法/配置定义的路由、拒绝、ABI、幂等、异常无重试 | provider数值为mock，多模态部分为生产AST接线；不是模型输出或设备数值证据 |
| Python AST | 517文件通过 | 语法证据 |
| 目标仓库pre-commit | 8适用hook通过 | 固定原配置/版本不变；shellcheck与symlink hook对本次改动无适用文件 |
| supplemental Ruff | 新helpers与patch模块显式lint通过；改动测试format/lint通过 | 原仓库生产目录Ruff/typos排除规则未改。全文件format检查仍发现5个大文件既有格式债，不混入无关整文件重排 |
| 补丁应用 | 3主题按序apply和原在线源+incremental两种重建均逐项等于最终候选 | 独立新clone验证，没有commit/fetch或修改在线index |
| 在线保护 | 687源码成员保持，API原身份和原脚本SHA保持 | 2026-11-02T10:08:35.812761+08:00 generation5820486/prefixqueries322022/prefixhits32000未增；0推理/GPU/重启/提交推送 |
| 新候选硬件/graph/TP8/model/formal/performance | **not_run** | 当前没有加载候选或新增模型预算，不能继承旧源码的测试 |

首轮cpu-001因关闭Plugin发现而进入安装中不存在的stock CUDA扩展，在collection阶段失败；日志保留。cpu-00267项通过，但识别到容器遗留PYTHONPATH选中历史Gems，未把它作为最终依赖组合证据；cpu-003在env -u PYTHONPATH及显式origin断言下重跑67通过。没有修改测试断言掩盖这些执行环境问题。

## PR审查剩余项

- **C2作用域仍needs_revision：** 原FPS wrapper安装到共享Qwen3VLVideoBackend，虽然只在Qwen3.8多模态配置时安装、有效输入保持原函数路径，但其它Qwen3模型非法FPS的异常行为仍可能受影响。要完整符合模型隔离要求，需要真实模型级loader扩展点；本轮不通过删除FPS防护或未经验证的替代loader来掩盖该缺口。
- **D3固定依赖交付：** 没有新增跨仓库符号依赖；当前两算子库仍带已有修复，完整可公开复现组合及其release/pin仍需收口，不能把本机editable树当公开固定依赖。
- **F3/F4：** 最终候选未做真实硬件、graph capture/replay或模型回归；五大文件的基线格式债需单独处理/说明。pre-commit按原配置通过不等于所有生产文件完全格式化。

因此收敛候选可审阅，但不标ready_for_review，不创建PR或提交推送。正式GPQA174/198仍未达88%，本轮不是精度修复，也不恢复性能优化。

## 性能效果

not_run，无吞吐/延迟收益声明。

## 决定、风险与回退

决定：保留隔离工程候选供审阅，线上源不变。回退即不加载候选。任何后续部署/重启、硬件/模型复核、doc81取证仍须按新明确范围执行；本轮代码整理授权不自动解除先前限制。

## 外部证据

- 根目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-076-plugin-pr-cleanup-20261102`，commands保存已核SHA脚本、checks保存CPU回执；delivery保存补丁及完整源码清单。
- 候选源：`/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate`。
- `01-multimodal-contracts.patch` SHA31a7f1e3da9847743480646008ee47d05e9b762e635dd53811ccfbdddfe7ca20。
- `02-ppu-moe-routing.patch` SHA39084ddba1370623bb55ba8ff068fb968bbc3fd5b229fdfa69130c6183e3421c。
- `03-runner-state-ownership.patch` SHA30fe8333426db8fa3d609996cb396e3e0c853e4942c3963bc1f5d96ee8bc4e14。
- `combined-vs-40f992dc.patch` SHA67d2dcc7db66270d807c1c1f2290cd136f908a37e7fb9e1e4550b1d3c9743ee1。
- `cleanup-vs-online.patch` SHAbe143f091490d9d3fecec8638e296b3c0ddab169d0d74ad24619ebc686b0e786。
- `candidate-manifest.json` SHA61414f793720b9597a40492a3f5090fa780843f5d6f9c344c39c4967499160a9，687成员。
- FINAL_SUMMARY SHA26c5d40791d931126d1bfec406654b31592d7cc8406156d3c1b43e4139d30d3d；本地交付只读回读/private/tmp/qwen38-plugin-pr076-20261102/delivery-readback.json SHA7b98547a84f77c4a84fd48a0627844145002877537ab1dc0f1aeb30797207a54。
- 本地可审阅增量：/private/tmp/qwen38-plugin-pr076-20261102/delivery/cleanup-vs-online.patch；三主题及PR_DESCRIPTION同级。原始源完整备份留在远端，不导出完整Git历史或整个私有仓库。

最终32成员外部artifact-manifest SHA791661bd45eba7425d30293fa544f357fd6b27690e4f22afa289fda804ee738a，包含脚本、全部CPU首错/最终结果及pre-commit原始日志。

## 用户追加：测试文件再收敛（进行中）

仅在新candidate-tests-v2中改测试，原candidate及冻结交付不覆盖。将独立RNG测试并入已有test_model_runner.py，避免逐修复新增文件；将多模态测试改为pytest参数化/fixture并调整到patches职责目录；保留Mamba独立CPU数值reference与全部边界。运行源sampling_rng.py是此前已保留的offset生命周期修复，不是新采样算法或取证埋点，本轮生产文件一律不改。合并后确保旧runner依赖skip不吞掉RNG测试；CPU/工程检查完成后更新相同文档与state，无模型/服务/提交推送。

## 测试文件再收敛v2结果（2026-11-02，已完成）

仅测试变化，最新未加载候选为 `/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate-tests-v2`；原candidate和其冻结证据保持不变。对应外部目录为首轮工程根下 `test-convergence-002`。本轮0生产源码修改、0在线源码修改、0模型请求/GPU/重启/8035/提交推送。

- 删除独立 `tests/unit_tests/worker/test_sampling_rng.py`，原9组/14个参数实例全部移入已有 `worker/test_model_runner.py::TestSamplingRngOwnership`。将原runner整文件依赖skip收窄到原有函数/类；RNG测试独立运行，全部14个实际passed。原runner所有测试函数/类的body AST保持相同，不删原断言。采样block接线用真实NumPy数组代替手写Array/flatnonzero桩。
- 将原根目录 `test_thead_multimodal_contracts.py` 移到 `patches/test_qwen3_8_multimodal_contracts.py`，统一pytest fixtures/参数化与生产AST加载辅助；原407行收敛到367行。FPS/pruning矩阵、平台/能力反例、metadata转发、ABI、幂等及失败不重试覆盖保留。
- MoE测试去掉一条“PPU且禁用fused package却标执行错误”的重复参数：该分支在执行provider前已拒绝，原相同拒绝用例保留一次。Mamba417行独立CPU tensor/reference测试保持原样。
- 相对主线新增测试文件从3个减为2个；四个测试入口是既有MoE、既有runner、新Mamba、新多模态patch文件。不要为追求少文件将Mamba独立数值reference与RNG状态测试混写。

最终清洁PYTHONPATH/canonical两算子库组合 **136 passed，0failed/errors/skipped，CUDA未初始化**，包括14个RNG实例和原runner用例。136相对67的变化主要来自多模态矩阵成为独立pytest项，以及纳入原runner整套测试，不是新增模型验证或精度提升。原固定pre-commit8个适用hook通过；两种patch apply重建与最终候选精确相同。候选686源成员；352个生产源码/数据文件与v1逐字节一致。线上687成员仍相同、API及原脚本未变，generation5820486/prefixqueries322022/prefixhits32000不增。

### sampling_rng.py的作用与来源

该35行左右的worker helper属于此前已保留的RNG offset兼容修复，相对Plugin main尚未入库所以Git显示新增；不是本次测试收敛新增的采样算法，也不是doc81取证探针。它在runner实际`_sample`外保存discarded seeded请求generator的入口offset，finally只将这些请求恢复到入口值；有效token请求正常推进，global/unseeded RNG不动，异常恢复后继续上抛、不重试。使用实际入口值避免假设每次采样固定只消耗某个常数。

它不更改seed/temperature/top-p/top-k/stop/BF16或任何数学算子。独立小模块不依赖torch/vLLM设备初始化，便于隔离生命周期逻辑和CPU验证；本轮仅合并它的测试，生产文件SHA仍d0ea4e18f0e56618ac216efbcea463bf09b1a51d35f44a43b32173109f4547da。保留该兼容修复不意味着原C32 GPQA唯一因果已证实。

### v2交付及未验证项

外部 `test-convergence-002/delivery` 包含更新后的3主题patch、combined-vs-40f992dc.patch、tests-only-vs-v1.patch和candidate-manifest.json；PR_DESCRIPTION在同run根。首轮共享视频作用域、固定依赖交付、生产大文件格式债及硬件/graph/模型验证缺口仍保留，pr_readiness继续needs_revision。不得继承旧模型结果或擅自部署v2。

测试增量SHA37edbc7d6f3750d9a0ab76633153100e3792ab0c83c04c9529daaf7cb78cfd87；combined SHA2857f7a1adf332b248149a3cf91231ca9a1f5e6e9975f373c3d82e9bf0c60240；candidate-manifest SHA9b279792fe6c07cef602b4469150b6befa26e38809fd67a95c44da17658c47e0。17成员artifact-manifest SHA4b50346ee582ddc7f382ec07b04e8f5eae9dbdf475b804263320eb6c144fdd60。最终readback 2026-11-02T10:35:24.847544+08:00，本地/private/tmp/qwen38-plugin-pr076-tests-20261102/delivery-readback.json SHA4fa26794f38f785309cd95ac5722be76c13644ddbe61e9dccfd424c7a04c0abc；可审阅测试增量/private/tmp/qwen38-plugin-pr076-tests-20261102/delivery/tests-only-vs-v1.patch。

## 视频loader作用域v3：最终代码与验证

**已在未部署候选中解决共享loader影响。** 删除 `_patch_qwen3_video_fps_validation`，不再替换 `Qwen3VLVideoBackend.compute_frames_index_to_sample`。新增模型专属子类 `Qwen3_8FlashNextVideoBackend`，校验FPS后通过 `super()` 使用原生帧选择/解码；在既有 `VIDEO_LOADER_REGISTRY` 的独立 `qwen3_8_flash_next` key注册，不覆盖 `qwen3_vl` 或 `Qwen3VLVideoProcessor` 映射。Qwen3.8配置verifier通过既有 `media_io_kwargs.video.video_backend` 选择该实现，复制multimodal配置、外层字典和video字典，保护共享给其它模型的原配置。

显式 `qwen3_vl` 在本模型配置中选择等价采样的专属实现；显式其它backend、空值/None的环境回退、请求级覆盖保持vLLM原优先级，不强制接管用户指定的解码路径。目标模型processor中的FPS/pruning校验保持。ABI不符或专属注册名冲突先报错，注册/配置赋值失败回滚新注册；异常不上其它backend重试。text-only、language-model-only及不支持的speculative配置不会安装该loader。此行为通过当前vLLM原生扩展点完成，无vLLM源码改动、临时埋点或新开关。

最终 **155 passed，0failed/errors/skipped，CUDA未初始化**，包括全部14 RNG及原runner/Mamba/MoE用例。视频测试通过真实配置verifier、原生registry、Qwen3 loader采样、同步/异步MediaConnector、VideoMediaIO执行；外部下载与codec帧读取被替代。覆盖同进程初始化前后共享方法identity及非法FPS原异常保持、共享配置隔离、重复初始化、显式/请求覆盖、实际采样帧数、metadata/kwargs、ABI冲突、注册冲突、部分安装及赋值失败回滚、执行错误不重试。CPU证据不代表真实视频codec或模型/设备通过。

最终9个配置hook中，**7通过、2无适用文件**（symlink与shellcheck）；原pre-commit配置和固定版本保持。更正前两轮摘要中的“8适用hook”计数，原始日志一直是7通过/2不适用，没有遗漏或跳过新的适用检查。最终格式副本与候选两处import空行已对齐，AST不变，精确最终源码由cpu-003再次155通过；早先冻结guard拒绝不一致副本和错误计数的原记录保留，均非模型事故。

516个Python AST通过；三主题apply及v2组合patch加本轮增量apply，两种独立重建都与686成员最终候选精确一致。351个生产文件与v2相同，本轮生产仅patch模块变化；Mamba/RNG/runner/模型主体不变。2026-11-02T11:04:10.653160+08:00只读回读：线上687成员、原API与启动脚本保持，模型计数不增。0新模型请求、GPU测试、部署、重启、8035、提交或推送；定时任务保持已删除。

### 最终修改文件：相对40f992dc共13个（9生产、4测试）

候选根：`/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate-video-v3`。下列所有文件的本地review副本均逐项核对冻结候选SHA，位于 `/private/tmp/qwen38-plugin-pr076-video-20261102/review`；本轮只有标记“v3”的两项变化，未增加文件。

| 主题 | 文件 | 职责 |
|---|---|---|
| 多模态 | vllm_fl/patches/qwen3_8_flash_next.py **（v3）** | 模型注册、专属video backend及模型配置隔离 |
| 多模态 | vllm_fl/models/qwen3_8_flash_next/common/multimodal.py | 模型FPS/pruning输入契约 |
| 多模态 | vllm_fl/models/qwen3_8_flash_next/gpu/model.py | processor时间metadata与模型接线 |
| 多模态 | vllm_fl/platform.py | T-Head视觉能力/选择 |
| 多模态 | vllm_fl/attention/utils.py | OOT视觉attention的平台边界 |
| 多模态 | tests/unit_tests/patches/test_qwen3_8_multimodal_contracts.py **（v3）** | 原输入/路由用例及原生loader隔离回归 |
| MoE | vllm_fl/ops/fused_moe/fused_moe_utils.py | 保留PPU专用公开provider路由 |
| MoE | tests/unit_tests/ops/test_fused_moe_backend_routing.py | provider/失败无重试/选择边界 |
| runner状态 | vllm_fl/worker/model_runner.py | 异构Mamba及discarded RNG的实际接线 |
| runner状态 | vllm_fl/worker/mamba_buffers.py | 异构cache分组/布局/复制计划 |
| runner状态 | vllm_fl/worker/sampling_rng.py | discarded seeded请求入口offset恢复，非新采样算法 |
| runner状态 | tests/unit_tests/worker/test_mamba_buffers.py | 独立CPU状态/复制reference |
| runner状态 | tests/unit_tests/worker/test_model_runner.py | 既有runner测试及合并后的14 RNG用例 |

### 仍未闭环

1. **D3公开固定依赖交付。** 当前FlagGems/FlagGems-vllm组合仍含既有修复，需公开可获取的API、测试、固定release/commit及安装绑定；本轮未操作算子库。
2. **5个既有大文件的全文件格式债。** attention/utils.py、platform.py、gpu/model.py、fused_moe_utils.py、model_runner.py的显式format-check仍未通过；保持原pre-commit排除配置，如实保留结果，未混入无关整文件重排。
3. **真实视频/模型回归未运行。** 当前codec/下载为替代，不证明实际视频格式、图像/视频混输、模型输出或非目标平台硬件。
4. **最终设备和精度门禁未运行。** 当前候选未加载，无TP8数值、graph capture/两次replay、模型精度或性能新结果；正式GPQA174/198的未达标状态不变。本轮源码隔离修复不确认其原始精度因果。

共享video loader作用域不再列为待设计问题；已用当前原生扩展点和CPU契约收口，但以上交付/验证缺口使总体 `pr_readiness=needs_revision`。回退方式仍是不加载此独立候选。

### v3交付

外部目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-076-plugin-pr-cleanup-20261102/video-scope-003`。`delivery`含三主题、完整组合、本轮相对v2增量、候选manifest；PR_DESCRIPTION已围绕最终实现重写，不沿用旧共享wrapper描述。完整日志、失败guard、cpu-003、最终源码和回读证据保存。

- 多模态patch SHA25100fca27bc8242d72d6882da3b42d5fdc7e52f1d23ee4d05191d8daaba4524。
- 组合patch SHAc7b69306b7b9fb6cffd1be3b6d2e465aef8eaf5169fa33390f89cd0b83d23945。
- 本轮增量 SHA545388c16f28b9d8bc57d9182cc0f01cd7e3cce6076d65a99de70228e173c90a。
- 候选manifest SHA8b3c9294d553c8259dd870b5b4b4ee8733126348596569d645c4db3ee485a7cc；27成员artifact-manifest SHAb4e8a60ff8f50f08f7a591eb7f9335cc0431637f47bf9d592124488f53886820。
- 本地可审阅：`/private/tmp/qwen38-plugin-pr076-video-20261102/delivery/delivery/video-scope-vs-v2.patch`，完整组合同目录；最终13源文件在同工作目录review下。

## 五大文件格式v4：已完成

仅在新候选 `/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate-format-v4` 修改下列5个文件，v3和在线源保持。使用原Ruff0.14.0与原pyproject配置，显式指定文件，不修改规则、不增加ignore/noqa或isort跳过指令。本轮无新增/删除文件，最终组合仍为13文件（9生产、4测试）。

| 文件（均在候选vllm_fl下） | v3→v4行数 | 逻辑等价性 |
|---|---:|---|
| attention/utils.py | 154→153 | AST含类型注释在忽略源码位置后完全相同 |
| platform.py | 860→863 | 同上 |
| models/qwen3_8_flash_next/gpu/model.py | 1464→1469 | 同上 |
| ops/fused_moe/fused_moe_utils.py | 707→716 | 同上 |
| worker/model_runner.py | 8071→8101 | 除两处导入分组外AST相同，首次模块导入顺序与导入绑定集合一致 |

所有5文件的注释序列完全相同，表达式、控制流、数值/字符串常量、函数签名、默认值及函数内导入不变。`TypeIgnore.lineno`是AST中的位置字段，随换行自然移动；只在等价比较中规范化该行号，未修改或忽略type标签。runner原有两处I001涉及将同模块导入项排序、合并：GraphCaptureContext排序、PIN_MEMORY和is_residual_scattered_for_sp合并到原已有同模块from导入，不增加模块或改变首次模块初始化顺序。真实依赖的相关导出均是普通模块字典属性；workspace导入前后对象identity保持，PIN_MEMORY仍为bool。没有套用会改算式/分支的自动lint修复。

四个测试文件、Mamba/RNG helper、视频专属loader及其配置隔离代码均与v3字节一致。尤其sampling_rng.py未改、采样参数未改；现有BF16与Mamba/RNG修复保留，本轮不是新精度修复或新模型验证。

### 最终检查

- **155 CPU passed，0failed/errors/skipped，CUDA未初始化**，全部14 RNG用例与原runner/Mamba/MoE/视频契约实际运行；另完成真实模块导出identity检查。沿用干净PYTHONPATH与候选Plugin/canonical算子库origin断言。下载、codec读取及MoE数值替代边界与v3相同，不代表真实模型或设备。
- **全部13修改文件显式Ruff lint和format-check通过**，使用 `--no-force-exclude` 防止原生产目录排除规则让检查未运行；不是仅检查新增文件。
- 原pre-commit配置 **7通过、2无适用文件**，检查前后源SHA不变；无配置/依赖升级。初次显式lint发现3处既有I001，其中platform一处由formatter解决，runner两处按上述等价导入分组解决，原诊断保留。
- 516个Python AST解析通过；远端再次从v3和v4实际文件独立核对5份等价报告。最终13本地review文件SHA全部等于冻结候选。
- `main + 3个v3主题patch + 独立格式patch` 与 `v3完整patch + 格式patch` 两种重建均与686成员候选精确一致；未提交或推送。
- 2026-11-02T11:19:35.331611+08:00只读回读：线上687源码成员、原8010 API/脚本与模型计数保持，0新请求/GPU/部署/重启/8035/提交推送；定时任务未重建。

### 最终diff与剩余问题

将本轮整文件格式变动作为单独 `04-format-five-files.patch`，便于与业务适配差异分开审阅：**5文件，135新增/89删除**。最终相对main40f992dc的完整组合为 **13文件，1802新增/139删除**；这是包含此前适配与测试的总diff，不是本轮新增逻辑规模。

可审阅本地交付根 `/private/tmp/qwen38-plugin-pr076-format-20261102/delivery`：

- `delivery/04-format-five-files.patch`：本轮相对v3的完整增量，SHA9ce83cde0304de982cfcc4db9d98bd8f68a0ecb09bec6038aedd1e22147dac95。
- `delivery/combined-vs-40f992dc.patch`：最终完整组合，SHA9754375a951db30a5086d525f7996e096d6215ac5b2c95682dfd6a931dea825f。
- `delivery/DIFFSTAT.txt`：两个diff的逐文件统计；`LOGIC_EQUIVALENCE.json`和`checks/cpu-001/IMPORT_EXPORTS.json`：等价性及真实导出证据。
- `delivery/candidate-manifest.json`：686成员，SHAff5bc066c5e8a7f94a8ff5ebf1c2191f636a0491346b6e066dec54e6f082db6a。

权威远端目录为原eng-076工程根下 `format-004`，30成员artifact-manifest SHA6998d1d4e628bca2ddf27903db5d64dfee7980bd32bf47b49ad8d54bf28aadc4。源review在本地同工作根review下，完整源码留在远端候选；未导出Git历史。

**已关闭：五大文件格式债；共享video loader作用域在v3已关闭并保持。仍未闭环：**

1. FlagGems/FlagGems-vllm既有修复的公开固定API/测试、release或团队可获取commit及安装绑定（D3）。
2. 真实视频codec、多模态模型输出及其它平台硬件回归；当前CPU替代证据不能替代。
3. 最终候选真实TP8数值、graph capture/两次replay、正式模型精度与性能。GPQA174/198仍未达标，本轮未生成新分数/gate或确认原始因果。

因此仍标 `pr_readiness=needs_revision`。本轮授权的源码格式工作已完成，候选未加载；回退仍为不加载该独立候选。

## 已有算子PR复用与Plugin依赖说明（已完成）

用户明确允许直接提交缺失算子修复PR，并提醒可能已经提交。本次先读GitHub原件和当前canonical两库指定修复，未凭旧文档重复发布。最终所需修复已有公开PR覆盖，因此新增PR、源码commit/push均为0；只更新现有 [Plugin #573](https://github.com/flagos-ai/vllm-plugin-FL/pull/573) 的描述，补充“算子合入前不要合并”及公共组合验收条件。

| 必需算子PR（本次核实时均open、未合入） | 修复契约 | 公共review head |
|---|---|---|
| [FlagGems #5882](https://github.com/flagos-ai/FlagGems/pull/5882) | generic与adjacent/linearized index大地址扩宽 | 92db9ee5a011b9b297ffebc898bc9fd0e9ae9ee1 |
| [FlagGems #7270](https://github.com/flagos-ai/FlagGems/pull/7270) | randn输出乘法前i64扩宽 | 56e1065c350f49a238b10137afcf8a9eef667f3c |
| [FlagGems-vllm #959](https://github.com/flagos-ai/FlagGems-vllm/pull/959) | PLE state行索引i64及CTA写回同步 | 22194f0b2ee0cebb51f945a20a157b82c4e19c65 |
| [FlagGems-vllm #982](https://github.com/flagos-ai/FlagGems-vllm/pull/982) | 编译器TLE能力与MoE空输入非零launch extent | a15b9018d6ac930c6384c9e39a9096e13aed7a14 |
| [FlagGems-vllm #989](https://github.com/flagos-ai/FlagGems-vllm/pull/989) | thead MoE原始权重布局、移除隐式转置cache | 058056c33d56a129372e9978613d3b4921f55832 |

[FlagGems #7582](https://github.com/flagos-ai/FlagGems/pull/7582)已有generic/BF16 cache专项回归，但本身缺adjacent扩宽；继续追溯后确认更早#5882已经覆盖两条路径，因此不再扩展#7582制造重复。#7582作为重叠修复/专项回归关联，由维护者协调合并方式，不要求两套实现独立合入。QSA [FGVLLM #940](https://github.com/flagos-ai/FlagGems-vllm/pull/940)和index_put [FlagGems #6892](https://github.com/flagos-ai/FlagGems/pull/6892)已合入；旧#6413不再被错误列为当前index_put的必需未合入依赖。

### 覆盖证据与边界

- 仅CPU/文件读取当前两库已知2+6个修复文件。实际FlagGems另外存在__init__/clone/max_pool3d相关未提交改动，全部保留且不纳入本任务；首次严格差异集合断言拒绝后，先保存原错，再限定读取已知修复，不覆盖其它内容。
- #959 PLE、#989 vendor MoE、#7270 randn生产文件与公共head逐字节相同；将对应公开PR生产hunk应用到当前HEAD原件也精确重建当前文件。
- index当前私有树为无条件loaded-index i64扩宽，#5882为有保守边界的int32/int64双路径；#982的编译器能力查询也不同于当前私有树thead显式拦截。两者修复契约已公开，但**不是当前已验证组合的逐字节替代**；合入后须选包含完整修复的固定公共版本并重新核验，不能把某一个PR head当作整体安装pin。
- 为核对#7582的adjacent缺口曾在本地准备两文件增量并执行纯CPU生成器反向对照（旧generic通过/adjacent缺扩宽失败，拟补后2项通过），随后发现#5882覆盖，已明确放弃发布该重复增量。它没有提交、推送或部署；这些host检查也不冒充#5882 head的运行测试。新GPU/模型测试均0。

### GitHub实际变更

仅一次 `update_pull_request` 更新Plugin #573正文。公开说明列明上述5个依赖与review SHA、#7582重叠、#940/#6892已合入，以及合入后公共组合pin/安装/回归条件；没有创建新PR、发评论、改分支或触发手动CI重跑。

读回确认#573仍open/draft，head仍 `45b24bc7748720e0022a72e47a983398ddda36d3`，更新时刻2026-11-02T03:47:01Z；正文SHA c76e45a399c08cbe5dcf653948364284b19454bdf08c6bcc51c9fc9e9a187643，与发送payload精确一致。GitHub当前mergeable=false；已修正旧正文“无冲突”的过期表述。正文明确当前13文件v4候选未推到这个旧head，155 CPU结果不能冒充该旧分支的验收。

证据目录 `/private/tmp/qwen38-plugin-pr076-dependencies-20261102`：`github-existing.json`、`github-index-5882.json`、`operators-readonly-scoped.json`、`production-coverage.json`及Plugin正文发送前/后原件；`FINAL_SUMMARY.json`和manifest保存范围与SHA。运行容器、生产源码、BF16、修复、8010、权重/采样/环境未操作，0请求/GPU/服务动作/8035；定时任务保持删除。

当前缺口从“尚未定位公开算子交付”收窄为“已有PR待合入、最终公共组合固定和回归待做”；Plugin旧草稿冲突/代码同步，以及设备/graph/正式精度缺口仍保留。GPQA174/198未改，无新gate，不将本次PR描述更新称为精度修复完成。

## PR #573 同步与 main 冲突收敛（进行中）

用户明确授权将13文件format-v4候选更新到原#573、解决main冲突并更新说明，不新开PR、不部署或重启。当前main为087f9b6e89d94f54509fba85ed3d5a7afff96c0f，原head45b24bc7748720e0022a72e47a983398ddda36d3。使用独立公开仓库临时副本合并，保留两个父提交，不重写原历史。main已有#455模型包与HY4新接入，旧分支的单文件Qwen/HY4及旧派发/文档不再重复带入。最终树从main接入13文件候选，逐项保留main新增clamp、graph清理和KV物理布局逻辑；生产源不覆盖。准备重新验证实际合并树，既有算子PR合入依赖保持。

本次本地证据：`/private/tmp/qwen38-plugin-pr573-sync-evidence-20261102`；公开仓库工作副本：`/private/tmp/qwen38-plugin-pr573-sync-20261102`。

## PR #573 最终同步结果（2026-11-02T12:23:42.984811+08:00）

- 原PR：https://github.com/flagos-ai/vllm-plugin-FL/pull/573；新head `0dc1d64e2860c1aa2a6841db97baf924ec18ea37`，tree `1dc19881fd416e3c763f66f3caab1d891b4f5efe`。
- main：`087f9b6e89d94f54509fba85ed3d5a7afff96c0f`；父提交保留原head45b24bc和该main，非强推。GitHub回读mergeable=true、draft=true；13文件 **+1799/-135**。
- 当前main已有#455包式Qwen/HY4实现，清理旧PR单文件模型、旧派发/文档的重复差异；不重新带入过时实现。main增加的graph清理、pool生命周期、物理KV布局五个runner方法及五个平台方法AST保持，MoE保留clamp防护和runtime platform规则。
- 最终候选 `/opt/qwen38-eng076-plugin-pr-cleanup-20261102/candidate-pr573-v5`，仅CPU检查未加载。外部权威证据 `/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-076-plugin-pr-cleanup-20261102/pr573-sync-005`；完整补丁 `final-vs-main.patch`、源码清单 `source-manifest.json`、公开回读 `final-PR-readback.json`、说明 `PR_DESCRIPTION.md`、35成员manifest SHA `2bd10835dd9844963120710fe4885b60ab1232b197dc666847fa7a9fe977b924`，已逐成员size/SHA回读。

实际合并后验证：155原候选契约+54共享MoE/clamp/KV/Qwen/GLM回归共209 pytest CPU，0失败/错误/跳过；另直接调用既有CPU mock graph内存生命周期函数8组合通过，不能算真实capture/replay。14 RNG用例保持。全13显式Ruff0.14 lint/format、原precommit7通过/2无适用文件、570 Python AST及diff-check通过。远端候选740成员与最终tree逐字节同，线上canonical687冻结成员未变；无模型请求/GPU/服务动作。第一次CPU脚本因缺父checks目录在导入前失败，已保留原日志，v2只修正输出目录创建；不是模型事故。

最终修改文件：

- `tests/unit_tests/ops/test_fused_moe_backend_routing.py`
- `tests/unit_tests/patches/test_qwen3_8_multimodal_contracts.py`
- `tests/unit_tests/worker/test_mamba_buffers.py`
- `tests/unit_tests/worker/test_model_runner.py`
- `vllm_fl/attention/utils.py`
- `vllm_fl/models/qwen3_8_flash_next/common/multimodal.py`
- `vllm_fl/models/qwen3_8_flash_next/gpu/model.py`
- `vllm_fl/ops/fused_moe/fused_moe_utils.py`
- `vllm_fl/patches/qwen3_8_flash_next.py`
- `vllm_fl/platform.py`
- `vllm_fl/worker/mamba_buffers.py`
- `vllm_fl/worker/model_runner.py`
- `vllm_fl/worker/sampling_rng.py`

PR说明已围绕最终13文件重写，保留FG5882/7270、FGV959/982/989合入阻塞与公共组合安装回归要求；7582为重叠index专项、不单独覆盖adjacent；940/6892已合入。五个依赖在本次回读仍open/unmerged。

GitHub [CI run41387906170](https://github.com/flagos-ai/vllm-plugin-FL/actions/runs/41387906170)失败：draft条件跳过lint/build/discover和平台作业，未修改的ci-gate要求前三者success，因skipped拒绝；原job日志确认，无已执行代码测试失败。Code Scan跳过，CLA成功。PR继续草稿，不擅自改CI或触发设备测试。

剩余问题：1）依赖合入、选择公共固定组合并验证安装；2）非draft完整CI仍需执行；3）真实codec、多模态模型、TP8/device graph capture/replay和正式精度仍未测试。CPU通过不建立新GPQA gate，174/198历史未达88%及根因开放事实保持。此次只向既有分支增加一个merge commit并更新PR说明，未新建重复PR、未部署或重启；原BF16、线上修复与删除的定时任务保持。

## PR #573 非草稿 CI 跟进（进行中）

用户明确授权转为非草稿、跑完CI并处理失败项，保留算子依赖、不合并/部署/重启。已按原head0dc1d64转为ready，触发CI41388741752和Code Scan41388741646；PR说明保留do-not-merge依赖并移除继续draft的旧承诺。证据位于`/private/tmp/qwen38-plugin-pr573-ci-20261102`。只在既有分支修复实际失败，不放宽断言或绕过门禁。线上PPU07不执行模型/服务操作。


2026-11-02T12:38:29.044878+08:00 用户明确“暂时不用关注CI的情况”，停止轮询/补触发/失败跟进，不取消已经启动的CI队列，不创建定时任务。#573已非草稿，原head0dc1d64保持；最后实际观察：lint、build/wheel安装、discover、8平台Setup、CodeQL/依赖审查通过，8硬件functional等待runner，未完成整个CI/后续e2e。T-Head网页条件true且明确waiting for runner，未据此推断离线或宣称代码通过。无新增源码提交，无合并/部署/重启。算子PR合入阻塞保持。
