# eng-074 Plugin主线更新并保留本地修复

2026-10-29后续用户重启的新主线组合已进入[acc023 C32 GPQA](acc-023-full-gpqa-c32-main.md)，首批在Plugin→vLLM MambaBuffers/get_mamba_groups规格一致性断言失败，服务自然退出；GPQA证据污染incomplete，ERQA未启动。故障已冻结，无新有效gate，不直接归因本更新或其他单一变化，未自动修复重启。

- 状态：retained，标准源码目录已更新，CPU及完整备份独立回读通过；工程源码交付，模型运行与性能not_run。
- 授权：2026-10-29用户要求更新当前容器Plugin主线。仅PPU-07容器qwen3.8-flash-opt-ppu07-20261015的/opt/vllm-plugin-FL；保留BF16及已有模型／多模态／MoE修复，不重启／推理／GPU／8035／提交推送，不升级另两库或vLLM。

## 方向与当前事实

连接检查限定PPU-07并通过ok3/changed0。当前Plugin main HEAD=a696859b9aa528dfd5b21f5da3403fdc16bac4cd，origin为官方flagos-ai/vllm-plugin-FL；ls-remote主线40f992dcae2a2e28bea83d9536b4347acb90bd18。容器running，只有/mnt目录bind，/opt私有真实目录，8010未监听。原工作区54个相对HEAD的跟踪修改及2个未跟踪文件包含Qwen3.8适配、BF16／MoE完整入口和多模态防护，禁止直接pull覆盖。两算子库HEAD分别f0aa7f12／b4d3382b，现有修改保留。

## 准备与执行前冻结

E=/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-074-plugin-main-update-20261029；仅新建、拒绝覆盖。容器私有W=/opt/qwen38-eng074-plugin-main-20261029。本地/private/tmp/qwen38-plugin-main-20261029.ICJ1Lj/prepare.py SHA1e3eb9e7019522d981b967dfdc0c072c227185e84a43bc73601e430908828ffb。白名单传输核SHA后执行`docker exec -e PYTHONDONTWRITEBYTECODE=1 -e CUDA_VISIBLE_DEVICES= qwen3.8-flash-opt-ppu07-20261015 python3 -B E/commands/prepare.py`。

先完整归档生产目录含.git／index／未跟踪／symlink并逐项核验，保存W/source-backup；只在新clone candidate中fetch固定主线SHA并应用原暂存和未暂存patch。原始patch及apply错误保留；冲突留在隔离候选处理，不修改生产目录。确认合并和CPU静态／契约检查通过后再记录部署脚本与SHA，保留旧标准目录完整回退副本，维持canonical /opt路径。准备脚本不导入torch、不操作服务、不执行GPU，另两库只读指纹。

## 验证、效果与回退

已按冻结deploy命令单次完成：canonical /opt/vllm-plugin-FL main HEAD=`40f992dcae2a2e28bea83d9536b4347acb90bd18`，原完整目录在`/opt/qwen38-eng074-plugin-main-20261029/original-canonical`、第二份source-backup和E/plugin-before.tar.gz均保留，原.git/index/暂存/未跟踪精确恢复能力保留。新目录相对主线9处本地变化：PPU MoE完整入口及测试、MoE配置普通文件、视觉Attention选择与forward绑定、视频fps/pruning防护及测试；大部分旧54路径适配已进入PR455，不重复作为本地变更。源码管理可查看这9处剩余差异，新HEAD是官方提交，无新commit／push。

独立核验canonical683成员／原备份660成员与冻结清单完全相同，25成员外部manifest全部回读通过。RESULT SHA`b0f89bd01f065acf504e64681eb2685c3bb5a64afd6af3b2aa041364fac84ecd`，manifest SHA`6a2690fe4c508794fe624ebee8885f67735a96c49b594eeecc5c69ada7151883`，archive SHA`6c61fc4f500c9787b01394a9fd8dfe9ffbc5da229e50132a14033e2a28023fb4`，CPU_VALIDATION SHA`517d428503ab2f363f3fbb5f37abbe0bc0786973d7b5da3bd9671d2b4a85b55f`。原BF16计算AST和现有修复保留、另两库／安装元数据／启动脚本／容器ID未变；当前8010仍未监听，未启动或重启服务、未推理/GPU/8035/encoder graph/提交推送。editable同路径直接使用新源码，无pip依赖升级；pip显示的Plugin版本仍为旧build label，应以Git HEAD及文件内容识别本轮更新。

决定仅retained源码交付，旧acc021/022和eng072结果为历史绑定，不给新主线继承gate或性能结论。上游涉及FP8 fallback／其他平台graph等行为，只有CPU静态／条件契约证据；运行中函数对象、模型数值、真实capture/replay、完整精度及性能未验证，不自动安排后续任务。回退可用上述完整原目录和归档恢复同一canonical路径，需按用户后续范围执行，绝不自动重启。以下是执行前冻结及中间错误记录。

v2完成：513 Python AST、7原多模态CPU测试、80真实MoE条件组合、4 BF16 adapter identity／完整模型AST防护／diff-check通过，683源码成员已冻结；三库clean origins均canonical /opt、真实torch未导入，另两库HEAD／status／内容与安装metadata不变。commands/deploy.py SHA`feef038e3f4ef31a800af13b9ee87d6d1d9e473e5c56cf609a9f7db4c1768af1`保存核SHA后单次Host执行：先核8010仍未监听、容器ID／私有/opt、生产完整manifest与备份精确相同、候选683成员和HEAD/status已绑定；原目录rename到W/original-canonical，candidate rename回/opt/vllm-plugin-FL。如第二次rename失败立即恢复原目录；不启动服务。后核完整源及原Git/index备份、另两库／dist-info／启动脚本／容器ID／8010不变并写RESULT/manifest，独立回读后收尾。无runtime依赖/entrypoint变更，原editable保持canonical路径，避免无必要pip重装；已安装Plugin版本metadata仍为旧build label，真实新源码以HEAD和内容指纹为准。

v1多模态／路由／BF16 CPU检查已通过，metadata断言因准备探针继承容器旧PYTHONPATH而读到历史Gems egg-info失败；非生产错误或实际依赖漂移。清洁env-u PYTHONPATH核三库均canonical /opt editable，Gems实际metadata为5.5.0.dev0+gf0aa7f121.env041，其他版本不变。原脚本和首轮日志保留，validate_v2.py SHA`69205b983f11bc6f7e8e1429da12145e31f95aa5e62fba79138f2450bb2aaca2`仅更正该比较来源、独立v2日志及增加当前dist-info文件SHA清单，CPU测试内容不变；执行前先保存核SHA。新主线FlagCX自动检测未发现已安装包，未增加通信安装或配置。

最小保留补丁已合入隔离候选，9路径；相对主线保留diff SHA`bff80f67bf128789c75f665713d86f82ffe4e24a88524c28bb6ae2d23b35cb96`。原模型AST除主线新增FP8接线外完全一致，保持BF16计算；上游新Ascend分支和固定依赖未回滚。CPU commands/validate.py SHA`9484d92a050ffcb245cbe83b307192733ac6e6f6648eba2cfd7d94abb2dbcbcc`：全Python AST／diff-check、原多模态unittest、真实MoE条件AST跨平台开关组合、新quant adapter普通BF16配置identity、三库版本和其他两库指纹；禁止导入真实torch／Plugin及GPU／模型请求。ruff/pre-commit工具未安装，不自动升级环境，仅如实记未跑。验证通过才保存候选文件清单供部署绑定。

准备脚本已完整保存原目录/Git/暂存/未跟踪备份，生产未改。主线新增13个提交/188文件，最新PR455已吸收旧暂存适配；整包旧patch因已删除路径而原子拒绝、candidate仍clean，原错误日志保留，不当生产故障。逐文件审查确认模型差异仅新FP8 fallback wiring及原多模态防护，原BF16计算已在主线。继续只应用原未暂存修复及两份未跟踪文件；MoE测试保留PPU覆盖前断言其余AST与主线一致，模型去掉仅新增FP8 wiring后须与原模型AST完全相等，保留主线新FP8/Ascend/CI固定依赖。commands/merge.py SHA`fabea04a8fff0ea51c9380e43f826a70d64fc517a559aee4f34fdb2f4299c421`先传核SHA后唯一CPU执行，不部署。原暂存语义和完整源码仍在备份，不创建任何commit。

完整私有备份跨环境导出被自动审批拒绝（更新授权未涵盖敏感源码跨环境复制）；未执行该复制，继续在远端隔离目录审查，不绕过限制。公开主线git archive可本地只读审阅。

适用Plugin规范A4/B3/C1/D3/F4/F6/F7，按真实上游差异追加对应接口审查。只做源码／依赖／CPU接线和语法验证；graph capture/replay、模型minimal、全量精度和性能均not_run，旧gate不自动继承。无收益声明，不签新gate或PR就绪。生产部署前保持incomplete；完整备份及Git状态为回退依据，回退不自动启动服务。
