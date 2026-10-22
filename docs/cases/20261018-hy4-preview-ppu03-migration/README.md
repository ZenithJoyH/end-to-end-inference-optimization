# HY4 / PPU-03：024plugin-opt 与两个 gems-opt 的兼容迁移

2026-10-21终态：完整198题GPQA C64已完成，strict-match **183/198=92.4242%**，高于预冻结87%阈值。原参数、官方原runner、独立UUID和数据指纹未改变；396样本行对应198题×2filters，每题strict/ flexible各一次。前后服务、完整四包/仓源码、131权重文件身份清单、tokenizer和启动配置一致，acceptance issue/check通过，42文件/28141872字节原生证据已SHA备份。heartbeat hy4-ppu-03已PAUSED。 详见[acc006](../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/acc-006.md)。


最新：env030用一文件10行补齐BF16 indexer动态metadata的分段边界，修复FULL_AND_PIECEWISE短输入答非所问；service13启动、两类10capture、三阶段16rank各2step、9/C8、同题2次与13249token分页/实际hit13184通过。两个gems-opt保持不变，不开始评测。[修复diff与必要性](plugin-fix-env030/README.md)。

下述为历史。

最新env028服务验证：env027安装组合的service09启动/51capture、16rank各2replay、smoke/C8与分页通过；实际prefix-hit 13184.0 tokens。源码与两个Gems未改，GPQA仍hold。[验证说明](service-validation-env028/README.md)。

下述为历史记录。

当前env027已直接收敛容器安装Plugin的3项局部重复，614文件与CPU契约检查通过，两个gems-opt不变。服务未重启，不开始评测。[当前说明](plugin-cleanup-env027/README.md) · [完整diff](plugin-cleanup-env027/full-diff.md)。

历史服务验证（env021源码）：env022已重启当前env021/r15，新service08的51capture、16rank各2replay、smoke/C8和共享前缀分页均通过，实际prefix-hit 13184.0 tokens。两个Gems与源码未改，GPQA暂停。[验证说明](service-validation-env022/README.md)。下述为历史证据。

当前补充：env011已将非目标平台扩展收回、删除重复metadata类，部署到官方main@8b2033e4上的minimal-r06；182项CPU/mock/parser、分页/MLA设备套件及W8A8 graph/fullgraph通过，新service07完成51组capture、16rank两次replay、smoke/C8与共享前缀实际cache hit。两个gems-opt保持固定、源码不变；完整GPQA继续暂停，未签发当前精度gate。参考PR #611但未复制其FP8/Ray/Gems runtime patch。详见[env-011](../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/env-011.md)。下文为历史迁移事实。

当前结果见 [模型记录](../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/README.md) 和 [env-001](../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/env-001.md)。用户已追加完整精度验证；本任务未做性能优化。

## 环境与范围

用户明确指定已有 `PPU-03 / hy4-preview`。直接更新该容器私有 `/workspace/vllm-plugin-FL`；`/mnt` 共享挂载、模型、共享启动脚本保持只读。没有创建优化容器或运行性能实验。容器镜像身份 `sha256:dcfc456313fe0e9ae8444134bd37849c6bda7084eca3feef98a388db26f7bdbe`，目录挂载仍为 `/mnt:/mnt` RW/rprivate。

| 组件 | 分支与固定版本 | 本次变化 |
|---|---|---|
| Plugin | 024plugin-opt / 08da21cb39601752040196232b60a152382c0f8f | 补迁HY4模块、注册和兼容适配 |
| FlagGems-vllm | gems-opt / 46387d7f96050204c1b932f35680a3ea03896fa6 | 源码保持干净 |
| FlagGems | gems-opt / 3ba1d1d99010de56d12088992f8b0da3444d90ca | 源码保持干净 |
| vLLM | 0.24.0 / ee0da84ab9e04ac7610e28580af62c365e898389 | 只读 |

模型 `/mnt/cpfs/models/Hy4-preview-W8A8-linear-moe/`，78层、64heads、W8A8 linear/MoE、TP16，每rank4heads。模型config SHA `894bbe4e1dea2ac68993891795d3397f71bd2e4c92aae89ba443c10ebca462c2`。沿用原100K上下文、2048batched-token、FULL_DECODE_ONLY与8010端口。Torch2.10.0、FlagTree0.6.2a1+ppu3.6、SDK2.1.1-rbd225未更换。

## 迁移与兼容机制

保留新版共享模块，补HY4 config/model/loader/reasoning parser和惰性、幂等注册；复用registry/dispatch/backend增加BF16 Indexer与TopK。HY4构造处配置CUSTOM MLA prefill。公开sparse MLA要求64/128heads，adapter填充到支持head数后裁回4heads，保留sink语义。未回迁历史Gems vendor kernel。

当前SDK不支持两库默认选择的TLE sparse实现，使用已有 `FLAGGEMS_FLASHMLA_SPARSE_TLE=0` 开关。服务必须设置 `VLLM_FL_USE_FLAGGEMS_VLLM=1`：W8A8线性使用支持INT8的 `flaggems_vllm.triton_scaled_mm`，并迁回原opaque custom-op编译边界；当前FlagGems同名scaled_mm已改为FP8-only。原HY4 ATen blacklist显式传给当前服务，不覆盖新版平台默认。

## 证据与限制

59项迁移与W8A8回归通过；两个公开sparse provider均通过数值、capture和两次replay；实际Plugin W8A8四组shape覆盖BF16/FP32、bias、MLA identity吸收、零token、capture/两次replay和fullgraph inductor。TP16启动完成，51/51 FULL decode capture，9/9生成（1+8并发）与16rank各两次post-ready实际replay通过，最终health200；这是此前启动/C8验证结论；当前服务已在完整精度运行中退出。聊天模板使用no_think。最终绑定回执results/final-validation.json。

三个兼容失败均保留原日志与最小复现：TLE编译能力不符、MLA prefill注册缺失、scaled_mm INT8接口及Dynamo边界漂移。FlagGems AIU INT8接口在当前SDK触发非法地址；同进程随后结果无效，改为新进程隔离并验证FG-vllm公开Triton接口。不能把算子或小样本测试当作GPQA分数、长上下文验收或性能收益。其他平台、模型和env0当前新Gems路径未实测，PR准备状态needs_revision，无提交/推送。

## 外部产物与回退

容器内产物根 `/workspace/.hy4-preview-migration-20261018-01` 保存命令、逐轮manifest/补丁、原文件备份、日志与results。旧适配完整副本仍在 `/workspace/.hy4-preview-update-20261018-01/originals`，安装记录在相邻original-install。

R04完整28文件补丁 `plugin-hy4-migration-r04.patch` SHA `029f2335b49828182940e72919bfa9c1183f25d5cc97741496e464ae3488bb55`，逐文件清单 `plugin-source-r04.json` SHA `db82e2b526c1a04b88548977ea4986b1a50a96ba77952d9cc5d2e9ac83260ec0`；本地应用到原revision后逐项一致。回退前精确确认并停止本次服务，按manifest恢复before-plugin及各轮before目录，隔离新增文件；完整旧版本恢复使用原originals与original-install。不得覆盖有后续修改的文件或停止其他服务。

## 可复用认识

同名API不保证dtype兼容；升级后应先核验真实INT8/FP8契约。TLE导入成功不保证目标编译器支持。对量化与算子库Python包装器，必须以实际fullgraph编译证明兼容，eager/graph replay不能代替。以上结论限本次固定revision和PPU SDK；没有新的端到端性能证据，不修订性能SOP或算子性能知识。

2026-10-20：env031当前2048组合已按用户授权开始[acc006完整GPQA C64](../../../models/Hy4-preview/ppu/20261018-hy4-preview-ppu03-migration/optimize/acc-006.md)，阈值87%；新版FGV固定45e14232、FG3ba不变，8192无净吞吐收益未保留。运行中，尚无正式分数或gate。
