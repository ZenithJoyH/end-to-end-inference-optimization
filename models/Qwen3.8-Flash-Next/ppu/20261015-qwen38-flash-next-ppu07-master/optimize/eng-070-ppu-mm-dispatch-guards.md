# eng-070 平头哥视觉 Attention 分发与视频输入防护

- 状态：源码已写入、CPU契约与保护性审计通过；设备／推理／graph未跑，未重启加载。2026-10-24用户授权源码修改，不重启服务、不跑推理／GPU、不启用encoder graph、不访问8035、不提交／推送。
- 范围：PPU-07既有独立优化容器 `qwen3.8-flash-opt-ppu07-20261015`，仅其私有 `/opt/vllm-plugin-FL`；`/opt`不在挂载中，三库已有修改保留。前置分析为[eng069](eng-069-multimodal-source-audit.md)。

## 优化方向与瓶颈依据

不是性能测量：修复视觉后端选择／执行不一致，以及视频非法配置／fps进入除法的输入契约。没有已测视觉热点、性能主指标或速度结论。Prefill视觉接入受影响，文本Decode／Mixed性能未测。

## 优化内容与适用边界

1. 在已有 PlatformFL视觉后端选择与MMEncoderAttention OOT hook中为thead显式选择／绑定现有TorchSDPA，拒绝不支持的显式视觉backend，不查询NVIDIA能力或假称FA命中。非thead保持原行为。暂不新增未经设备验证的Attention kernel，也不处理encoder graph。
2. 在Qwen3.8模型配置边界拒绝非零／非法video_pruning_rate；在直接模型／processor入口按需复用同一校验，避免绕过配置核验后占位token与embedding错位。None／0保持原行为。
3. 复用Plugin模型shim和幂等兼容hook：Qwen3视频loader在采帧除法前检查source／target fps，Qwen3.8 ProcessingInfo在timestamp除法前检查元数据／显式采样fps。检查finite positive numeric，不修改合法值、抽帧算法／timestamps／采样参数。不修改vLLM安装源；共享Qwen3 loader仅改变非法fps的报错。

实现前核对当前三repo HEAD、branch与未提交状态；基线源码保存本地 `/private/tmp/qwen38-eng070.qcz4mU/source-before.tgz`，远端部署前另存原件、原Git diff／index清单与受保护源SHA。已有BF16、PLE、QSA、GDN、MoE及index/index_put/randn修复不动。

## 正确性与路径命中

只做CPU mock契约／静态编译／格式检查，覆盖thead默认／显式选择、非目标平台、重复hook、非法pruning和fps、合法值透传。未执行模型导入／tensor计算／服务请求；mock不代表硬件命中或数值通过。

服务当前模块不通过reload替换，本轮磁盘修改不宣称正在运行的服务已经加载。旧文本gate留作历史绑定，不给新磁盘候选继承多模态或正式gate。

## 性能效果

not_run；无baseline／candidate／revert，无新精度、graph或吞吐结论。

## 决定、风险与回退

先形成最窄源码候选、回退备份与CPU证据；`pr_readiness=experimental`。任何源漂移／共享路径／前置SHA不匹配都停止部署，不覆盖用户改动；不自动重启验证。回退仅恢复本轮文件的部署前原件，其他源码与Git index不动，实际回退操作也须记录并不触发服务动作。

## 外部证据

- 本地候选／命令：`/private/tmp/qwen38-eng070.qcz4mU`。
- 计划远端：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-070-ppu-mm-dispatch-guards-20261024`，使用前检查父目录权限／容量与规范路径；新建拒绝覆盖。
- 目标Git HEAD：Plugin a696859b9aa528dfd5b21f5da3403fdc16bac4cd（main）；FGVLLM b4d3382bb04da4e0ab444849697865b4d5fcd86e（baseline）；Gems f0aa7f12180cea4776a2aba3f3889b8fb82a28b1（baseline）。已有dirty／staged修改保留，不reset／stage。

### 执行前冻结的源码候选与命令

本地7项CPU unittest契约、六文件语法编译及Ruff check通过；4文件Ruff format check通过，platform／model已有无关格式差异不混入补丁。完整model AST去除本轮明确MM输入防护后与原件一致，BF16／MoE／PLE／QSA／状态与权重加载计算不变。测试仅标准库＋vLLM stand-in，不导入torch／模型。

- 六个文件（5生产＋1 CPU测试），无FGVLLM／Gems／vLLM修改。
- 部署包 `/private/tmp/qwen38-eng070.qcz4mU/deployment-bundle.tgz` SHA `f4e8141c9835a152b21ddcfe314f5ca9226cd3f431eab8b6a1846cc1ebd02885`。
- 远端执行本E的 `commands/deploy.py --mode check`，仅核验；再唯一一次 `--mode apply`：脚本SHA `70ce8976e11a2da995c92aa3c18e4acff70f51ed444ec02c3c2ffe5f592906f9`。先存before／原Git diff与文件备份，再对精确六文件原SHA核验、原子写入、后核三库源／HEAD／index及8010 listener进程身份。不请求health，不执行新import／服务或测试。
- 源补丁 `source-change.patch` SHA `250c572d4575b7087e807a485cebf22b43dd674dbee7c880deb8ce2b5c45ec13`。
- 传输仅新建上述E目录（父目录规范路径检查、新E拒绝覆盖），将本包普通文件解包到E；不修改挂载或安装绑定。部署脚本发现已APPLY_STARTED即拒绝重发。
- FPS loader hook最终仅由Qwen3.8的非language-only配置校验安装；不在通用模型注册时无条件改变其他模型。直接metadata／timestamp入口由ProcessingInfo校验，合法值仍交原实现。

## 实施终态：六文件落盘，未重启／未验证设备

执行回执 `APPLIED.json`（epoch1792808751.28641，SHA `ca676553e37d626024793af05ff78cc8471b430861f4166b27b7bdc450a3a28d`）确认本轮仅修改六文件：

| 文件（相对 `/opt/vllm-plugin-FL`） | 改动 |
|---|---|
| `vllm_fl/platform.py` | thead视觉支持列表仅SDPA；默认／显式SDPA不探测NVIDIA能力，不支持的显式backend抛ValueError；其他平台旧分支不动。 |
| `vllm_fl/attention/utils.py` | thead MMEncoderAttention.forward_oot显式绑定forward_native，与SDPA选择一致；无新kernel／FA导入。 |
| `vllm_fl/patches/qwen3_8_flash_next.py` | 配置拒绝未实现pruning；仅非language-only配置安装幂等Qwen3 loader fps检查，保留原采帧算法。 |
| `vllm_fl/models/qwen3_8_flash_next/common/multimodal.py` | 新增共享纯CPU输入契约：pruning仅None或数值0；fps须有限正数，拒绝0／负数／NaN／Inf／None／bool等。 |
| `vllm_fl/models/qwen3_8_flash_next/gpu/model.py` | processor与直接构造入口拒绝pruning；timestamp入口验证原fps／显式采样fps，`sampled_fps=None`仍允许，保留num_frames路径与原metadata对象。 |
| `tests/unit_tests/test_thead_multimodal_contracts.py` | 一份可直接用标准库unittest运行的CPU源码契约测试；vLLM stand-in／AST选取定义，不导入torch或模型，不做任何tensor推理。 |

最终7项unittest通过：fps边界、pruning边界、PPU选择／非目标显式backend、OOT重复hook／非目标绑定、loader重复hook／异常先于原调用、processor／timestamp、配置安装范围。六文件syntax compile及Ruff0.14.0 check通过；4文件format check通过。platform／model原有无关格式保留，没有借格式化改动计算部分。首次lint发现测试风格问题已修正；容器无Ruff，检查工具仅装在本机隔离tmp，不修改容器依赖。

保存并比较部署前599项Plugin／794项FGVLLM／6115项Gems源、配置／symlink指纹：Plugin变化精确等于六文件，其他Plugin文件不变，FGVLLM与Gems全部原件相等，三库HEAD／branch／index不变。四个被替换文件的原件在E的`source-before/`，两个新增文件事前不存在；完整本轮补丁和三库原index／worktree diff均保留。实际源路径每级均为真实目录／文件，无指向共享挂载的符号链接。安装版vLLM六个相关边界文件与eng069分析快照逐字相等。

`SOURCE_BEFORE.json` SHA `125f401d887220be137ab81f36f3d2b2df66190fec58338046901932a2e682e9`，`SOURCE_AFTER.json` SHA `7a6b1bfe166f4e0f859aa1ac7616e86b9a4ee92e134d0d2f3be0d6f3f43f61df`；回读16项传输原件、六个最终SHA／语法和四个回退原件通过。closing-audit-002.json SHA `274596bbfe5c27e2f2c5f047c302cd4067f5777e5ece1ff7d7c3fda93999e4fc`，本机与E分别保存。

8010端口精确listener进程的start／argv SHA前后一致（namespace PID1598786、start546089295、argv c146e2da…595010），容器身份／StartedAt不变；没有health／metrics／模型请求或新GPU操作。monitor未更改，容器保持此前已由外部解除暂停的状态，本轮pause／unpause均0。

**仅源文件落盘，不宣称服务已加载这些新函数。** 没有设备数值、视觉capture／replay、图片／视频精度或性能结果，未启用encoder graph。旧acc020 gate仍属于原op068绑定，不能给eng070新磁盘源码签发／继承gate；当前不自动继续正式性能或重启验证。

回退方法（未执行）：先核六个当前SHA仍等于`payload-manifest.json`中的after；按`source-before/`恢复四个原文件并保留原权限，将两个新增文件移入新建的回退留存目录而不是直接删除；不改其他源／Git index／安装绑定，不触发任何服务动作。若有其他人后续修改，停止覆盖并人工合并。

最终决定：按用户要求保留源码候选，`pr_readiness=experimental`；等待独立的加载／设备／推理验证方向，不把CPU mock与源码存在当作实际PPU命中证明。

## 后续eng071单次重载覆盖（2026-10-24）

用户随后授权单次8010重启并去掉language-model-only，执行与首错完整记录于[eng071](eng-071-ppu-image-video-minimal.md)。本候选与原BF16／所有算子修复已随新实例加载，三库／engine／HEAD／index及模型metadata前后当前相等；两类语言capture均7/7，encoder graph关闭，8010健康空闲。原生日志记录MMEncoderAttention选择TORCH_SDPA，但controller过严的另一条固定Plugin日志断言先失败，**尚未发图片／视频请求**。因此eng070实际视觉函数来源、媒体语义与fps／pruning设备边界验证仍`incomplete`，无两次请求replay或新gate，不宣称多模态已通过。保留原失败与当前服务，monitor已暂停，未自动修补／续跑／二次重启。

用户再次明确授权修正工具校验后，eng071同实例`continuation-001`已完成：12HTTP200（6图片红色、6视频先红后蓝）、两组C1完整token分别66／127一致、实际混合C8和语言FULL replay通过；图片／视频各8rank真实BF16 Tensor进入native MMEncoderAttention SDPA→Torch SDPA→FlagGems Attention函数，完整源码SHA与16份调用记录绑定。124项新manifest及12raw／token、19＋6冻结输入、60原manifest与8父级引用均经CPU审计通过。当前源／Git／API完全保留，健康空闲、KV／抢占0，本次续行0重启／0信号／0重试；首错原件不覆盖。结论更新为固定合成媒体`passed-minimal-scoped`，不是通用多模态／长视频、无效fps／pruning设备拒绝矩阵、encoder graph、GPQA或性能通过；这些边界仍仅已有CPU契约或not_run。
