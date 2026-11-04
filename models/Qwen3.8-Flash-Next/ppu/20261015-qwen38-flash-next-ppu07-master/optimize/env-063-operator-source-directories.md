# env-063：算子库规范源码目录与Git审阅信息

后续环境更新：[env-064](env-064-remove-pythonpath-override.md)已让新root bash交互/登录shell去掉精确旧PYTHONPATH覆盖；Docker Config.Env仍未改，已有窗口需unset一次。以下安装时的覆盖说明保留为历史事实。

## 后续只读核对：库中保留文件不等于当前调用来源

2026-10-22用户质疑FlagGems中的PLE/QSA/GDN/MoE重复实现。限定PPU-07和原容器只读追踪，未导入生产包、未调用算子或修改代码/开关/服务，未访问8035。此前“保留修复”清单是源码保全清单，不应解读成这些旧模块都是当前实际kernel来源。

- PLE：Plugin `gpu/ple_layer.py:9`直接从`flaggems_vllm`导入`ple_short_conv_`，`gpu/ops/ple_fusion.py:6–11`导入FGVLLM的gate/prefill融合入口；真正PLE i64+CTA修复位于FGVLLM `ops/qwen4/ple_conv.py`，不是FlagGems旧`fused/ple_state.py`。
- QSA：Plugin `gpu/ops/qsa.py:8–15`直接从`flaggems_vllm`导入QSA操作，PPU M16实现仍在FGVLLM `_thead/fused/qsa_attention.py`。FlagGems旧`fused/qsa.py`不是该入口来源。
- GDN需分阶段：模型复用vLLM `QwenGatedDeltaNetAttention`；Plugin保留`patches/gdn_packed_decode.py`对vLLM packed kernel的能力/源码条件化FP32-beta兼容hook，另外FLA wrapper存在FlagGems/native选择，不能统称全从FGVLLM导入。未在当前Plugin找到旧FlagGems `fused/gdn_packed_decode.py`的显式调用点；这不等于本次证明了每个rank全部GDN实际执行分支，也不声称hook此次已重新触发。
- MoE不是按文件名推断：`dispatch/backends/flaggems/impl/fused_moe.py:23–26`按`VLLM_FL_USE_FLAGGEMS_VLLM`选择FGVLLM或FlagGems，`envs.py:17–18`默认0。原8010 API `/proc`中该开关未设置，bootstrap无该开关改写；冻结service.log八rank均记录`moe_align_block_size -> default.flagos`。结合未改的路由源码，此配置选FlagGems alignment，op061的TLE/空extent修复仍有意义，不能直接删除或移库。此处不是在线函数对象注入或每kernel新trace。

上述envs、MoE wrapper、GDN hook、PLE layer、QSA ops、model六份Plugin源与当前8010私有BF16副本逐字相同。FlagGems `common_slot_mapping/gdn_packed_decode/ple_state/qsa`四文件是继承旧兼容现场，且仍由`fused/__init__.py:95–98`包级导入导出；“没有当前显式调用点”不能写成“模块完全没有被import”。后续若收敛，应先审计并清理冗余模块及导出，再单独验证；若将MoE统一迁移FGVLLM，更是执行路径变更，不能冒充纯目录清理。本轮仅说明事实，未自动删除、迁移或切开关。

- 状态：completed，源码安装/Git及CPU工程检查通过；新模型minimal为incomplete（未重启/未发请求）。分类：framework / 工程环境整理，不新增算子优化。
- 授权：2026-10-22用户要求调整容器中FlagGems与FlagGems-vllm源码安装目录名，并可通过VS Code源代码管理查看修改项。
- 目标：PPU-07 / `qwen3.8-flash-opt-ppu07-20261015`；标准目录使用`/opt/FlagGems`与`/opt/FlagGems-vllm`，目前都不存在。不重启8010、不访问8035、不发GPU/推理、不提交推送。

## 设计和边界

复制**当前实际有效修复树**，不是旧默认安装树：Gems取`/opt/qwen38-op061-empty-fix-20261021/FlagGems`，FGVLLM取`/opt/qwen38-accdiag051-ple-cta-sync-20261020/fgvllm`。两者及目标均为容器overlay私有路径，不改挂载。旧目录原样保留给当前8010继续使用和回退；不做原地mv、不增加指向旧树的symlink、不修改冻结历史launch脚本。

Git以真实基线恢复修改可见性：Gems `f0aa7f12180cea4776a2aba3f3889b8fb82a28b1`，FGVLLM `b4d3382bb04da4e0ab444849697865b4d5fcd86e`。使用已有容器仓库对象，不fetch公网最新、不伪造commit、不git add。新目录独立Git基线/index让真实源码差异保持unstaged/untracked；不把当前修复文件当干净基线掩盖差异，历史symlink→普通文件差异如实显示。

实际安装当前仍是env041 Gems和旧FGVLLM目录editable；容器继承旧`PYTHONPATH`会遮蔽安装，8010又显式指定当前两棵私有修复树。三者分别记录。此次仅把新进程的安装绑定重定向规范目录，不改容器ENV或在线服务进程。干净新进程需清除旧PYTHONPATH才以editable为准。

## 安装与回退预案

先冻结当前服务身份、源码清单、site-packages中两包的精确metadata/pth/finder/专属CLI备份及其他依赖身份。新真实目录复制后逐文件验证，补齐真实Git基线，再以原版本离线构建editable wheel、`pip --no-deps --no-index`安装，不升级运行时依赖；Gems保留`5.5.0.dev0+gf0aa7f121.env041`、FGVLLM保留`0.3.0.dev1`。构建工具隔离到本任务私有目录，不使用不满足Gems pin的全局setuptools80/scm10；优先重用已有pip缓存。生成`_version.py`若被构建重写，恢复原字节再验；不改变实际算子源码。

外部根：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/environment/env-063-operator-source-directories-20261022`。私有控制/构建根：`/opt/qwen38-env063-source-directories-20261022`。commands先保存及校验SHA再执行，排他目录/阶段回执避免重复安装。失败保留首错，不自动重试或回退服务。恢复仅针对备份的两包安装绑定，不能覆盖整个site-packages；旧有效源码不删除。

## 验证

按本地`inference-accuracy-evaluation minimal-regression`执行CPU工程子集：源码/关键修复SHA、Python AST、Git差异/fsck与无alternates、editable/direct_url/干净CPU解析、其他依赖未变及当前8010身份/health不变。可运行不分配设备tensor的受保护包导入；禁止GPU初始化或为了完成导入而放开设备。未执行graph/C1/C8或新GPQA，不签新gate，不把源码安装等同于线上已切换。完整模型minimal结果incomplete，CPU工程另记。

## 结果

执行前脚本已在`/private/tmp/qwen38-env063-source-names.uV77da`保存并AST检查：`control.py` SHA`ba7a8acd8970cd58f010a6ac85ae1a2465cb08f629059c72e2d48c4c4b091d3f`、`install.py` SHA`1fae1e17ffa788dd86e3a8fbe1bc4c3ed97fc6b3c6008c07c7750978745f09f4`、`verify.py` SHA`f5d7f17e87e5f63b989c59a3267b2c7d1d50486298eeb8efad1abf76e6d79ff7`。排他传入外部根`commands/`，核SHA后只执行一次`PYTHONDONTWRITEBYTECODE=1 python3 <根>/commands/control.py`。构建依赖从旧pip缓存复制setuptools76.1.0/scm9.2.2/wheel0.46.2到私有build-deps；全局setuptools80.10.2/scm10.0.5/wheel0.45.1不改。一次pip同时重绑两包，`--no-index --no-deps --no-build-isolation --no-cache-dir -e /opt/FlagGems -e /opt/FlagGems-vllm`。

FGVLLM AGENTS.md已完整读取。本次不是算子开发，0数学/dispatch改动，不启动其workflow的GPU/benchmark流程。CPU验证仅做AST、关键SHA、spec/direct_url/版本，不执行包级生产导入或设备枚举；不把此范围称完整包导入或真实kernel命中。执行前仍待执行。监控保持PAUSED；Plugin BF16标准目录与FP32回退备份不改。

### 完成结果

两个标准目录已创建并以源码editable安装：

| 库 | 规范目录 | 版本（未升级） | 真实Git基线 |
|---|---|---|---|
| FlagGems | `/opt/FlagGems` | `5.5.0.dev0+gf0aa7f121.env041` | `f0aa7f12180cea4776a2aba3f3889b8fb82a28b1` |
| FlagGems-vllm | `/opt/FlagGems-vllm` | `0.3.0.dev1` | `b4d3382bb04da4e0ab444849697865b4d5fcd86e` |

Git为从已有仓库本地读取对象的自包含浅历史，分支`baseline`，无alternates，fsck通过；没有公网更新、伪造commit、git add/commit/push。VS Code在该容器中打开这两个目录，或把它们添加到同一工作区，源代码管理可直接显示：

- Gems：6处已跟踪修改（fused导出、MoE alignment、index、index_put、randn、MoE测试）；4个未跟踪兼容模块（common_slot_mapping/gdn_packed_decode/ple_state/qsa）。
- FGVLLM：PLE kernel修改、未跟踪`tests/test_ple_conv_large_state.py`；3个原有symlink→普通文件类型变化（`.github/copilot-instructions.md`、`CLAUDE.md`、`GEMINI.md`）明确保留，不冒充新算子修复。

Gems 6613项/FGVLLM 1063项有效payload与原正在使用的私有树逐份相等，原私有树和Plugin前后不变。构建重写的Gems `_version.py`已恢复原字节并再次核全树；i64/index_put/randn/MoE v2/PLE i64+CTA/QSA M16六项关键SHA全相同。4005个src Python文件AST通过；干净CPU新进程的spec和editable/direct_url分别指向两个新目录，版本保持。没有导入torch或生产算子包、没有GPU初始化/设备测试/模型请求，因此不是新模型或算子数值回归。

一次pip同时完成两包editable重绑；构建工具setuptools76.1.0/scm9.2.2/wheel0.46.2来自已有缓存，仅安装在`/opt/qwen38-env063-source-directories-20261022/build-deps`。原全局setuptools80.10.2/scm10.0.5/wheel0.45.1及Plugin/vLLM/Torch/FlagTree/packaging版本和来源不变；0运行时依赖升级/0联网下载。

安装前25份精确metadata/pth/finder/专属CLI已备份到`<外部根>/installation-before.tar.gz`，逐成员SHA复验，归档SHA`37a90eec6255542a56a770e4670282ae8c2465548aeeb451efd1d89acb797345`；清单SHA`662cd30a2d17b405f943403fcb2349796b85bbab0b8e31b0199808144fff25af`。旧有效源码目录及旧安装来源目录原样保留，不执行自动回退或清理。

8010 Host1924405/start531054985保持，health200/running0/waiting0、prompt82925/generated2446388前后相同。它的显式PYTHONPATH仍是acc018 BF16/051/op061私有路径；**没有重启或切换到这些规范目录**。容器继承的旧acc011 Gems PYTHONPATH也未修改，直接docker exec继承该变量仍会遮蔽新安装；核安装来源使用`env -u PYTHONPATH`。未来服务切换必须明确调整启动路径并授权验证，不通过全局hook伪装路径已生效。原acc018分数/gate不改写，不签新gate。

完整证据均在上述外部根：summary SHA`7483e0cff938149102e8537b87aa03a8738046de00356de2a416d724574fc521`、24文件manifest SHA`4c2744ad1e27bf617c2075c3c94fe6563a7009514f07b7740c0e85ad02b24809`、CPU_VERIFIED SHA`169d3ac42a691f0f039c4145f1d3608349e8a70e5c9e4ba258fe6b81499eab01`、Git-review-final SHA`ce27509a7d0680f410fbf845f55151bcda85712ba1388d98ec6e29d844a4f5eb`、FINISHED SHA`a52c87a5e90d79d6e2306507fdeefe9c9343851de4b0b5494a4c4223cf3a6b56`。保留新目录源码安装与审阅基线，monitor仍PAUSED，0服务动作/0次8035访问/0提交推送/0新GPU或推理。
