# eng-073：最新已验证模型启动配置同步到用户入口

2026-10-29用户修改为prefix cache enabled后自行重启，最新三库组合C32精度见[acc023](acc-023-full-gpqa-c32-main.md)：首批执行Mamba规格断言导致服务退出，GPQA无有效分数、ERQA未启动。未确认与环境收敛或prefix cache的因果关系，原历史结果不继承，无自动修复／重启。

## 后续授权：env-trim-002继续收敛环境（已完成）

2026-10-26用户明确要求继续收敛非必要变量。仅修改同一start-model.sh，删除VLLM_FL_QWEN38_FGVLLM_OPS、DNN_VENDOR、PYTHONPATH及DIAG047_CONFIG显式export，并unset以免继承；保留SDK初始化、平台通信、设备8–15、FGVLLM开关1、黑名单防护及全部模型argv／nohup日志接口。不修改三个库源码或修复，不删除cache／日志，不启动／重启／推理／GPU／8035／提交推送。移除实验bootstrap也移除pin047固定generated-Inductor选参，未来使用默认选参；旧精度gate不自动绑定，运行回归not_run。

CPU只用find_spec、禁设备且无torch导入，三个库分别解析到/opt/vllm-plugin-FL、/opt/FlagGems、/opt/FlagGems-vllm。静态确认前两项export无当前代码读取点，SDK提供PPU_SDK自动识别thead。8010未监听，当前目标SHA8703b9356c88bec4d123779ea67aff4d8c547e1a4af4926f7e58b487553c5429。

新产物目录E3=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-073-start-model-script-sync-20261026/env-trim-002`，拒绝覆盖。本地`/private/tmp/qwen38-envconverge-20261026.P9DajW`；commands/start-model.sh SHA`a62499ceeabb013516079bc0b4b603916784f251829e9e879299dcc080293340`，commands/install.py SHA`083885db91d03405d712e29062c1d07a12b85e283229743a237f3db8b09e87bd`。仅白名单传这两文件并核SHA后，唯一执行`python3 -B E3/commands/install.py`。安装器核旧SHA／完整argv／环境差异／symlink／同挂载及8010未监听，bash -n不执行；独占备份`/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh.bak-eng073-envtrim2-20261026`，保留原0755和owner原子替换。后核host/container SHA／语法／五份生产源码与容器ID不变，保存RESULT和manifest，再独立回读。原备份、源码、实验bootstrap及日志均保留。

已按冻结命令单次安装，目标SHA`a62499ceeabb013516079bc0b4b603916784f251829e9e879299dcc080293340`；新备份SHA`8703b9356c88bec4d123779ea67aff4d8c547e1a4af4926f7e58b487553c5429`精确等于旧目标，历史两份备份保留。主机／容器文件SHA及bash -n、完整argv、owner／0755、五份关键生产源码及容器ID前后不变均通过，8010仍未监听。三个库无实验PYTHONPATH仍解析canonical /opt源码目录，检查未导入torch。独立回读五个manifest成员、实际目标及备份通过；E3/RESULT.json SHA`59692336aa3f8a2793b955ec9002b582f8031c590b094502f7aae8c0c6a2f1b8`，manifest SHA`314f6e5e3c0c047f21ef48222cb3f6fbf0e6005ebaec40f683ba2fbe58f553b0`。状态env-converged-script-only-CPU-verified-not-executed／independent-readback-passed；0启动／重启／新推理／GPU／8035／源码修改／cache删除／提交推送。保留BF16、16图、现有修复和encoder graph关闭；下一次启动将不加载实验bootstrap／pin047，默认选参的模型精度和性能尚未运行验证，不继承旧gate。以下env-trim001保留pin047的说明为历史。

## 后续授权：env-trim-001精简非必要环境配置（已完成）

用户要求去掉部分非必要环境变量，包括cache保存配置。本轮只改同一start-model.sh，不执行启动、不删除任何cache／日志、不改源码／采样／算子修复／模型参数，不访问8035或提交推送。新核目标仍SHA`d71854f0f9e4e263ad1e7ccea9d165f099d534d5fae3dcf993adff3e4f306dad`，8010未监听。

删除四项自定义cache/DB路径export：FLAGGEMS_DB_URL、FLAGGEMS_CACHE_DIR、TRITON_CACHE_DIR、VLLM_CACHE_ROOT，并以一行unset避免继承旧实验路径；恢复库默认存储行为，不是禁用cache、不清理文件。目标Gems／FGVLLM静态源码确认cache目录与DB变量均支持省略。移除PYTHONDONTWRITEBYTECODE的显式export、六个已不用的DIAG旧变量unset；模型argv、nohup／service.log接口、平台通信、FGVLLM switch／QSA选择、黑名单清理与normal_/index_select保持不变。

保留PYTHONPATH及DIAG047_CONFIG：实际bootstrap/pin047.py通过前者安装固定generated-Inductor选参，后者提供pin策略配置／journal根；不是可直接删除的cache目录。sitecustomize同时有既有来源日志hook，本次不重构或改动它们，避免把“精简变量”扩大为选参／执行路径修改。不删除旧bootstrap/config，也不新增模型observer。恢复默认cache会改变未来cache身份／热身状态，不将旧gate或性能自动外推为新启动验证。

续行产物E2=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-073-start-model-script-sync-20261026/env-trim-001`，拒绝覆盖；本地`/private/tmp/qwen38-envtrim-20261026.Kwcn0y`。候选commands/start-model.sh SHA`8703b9356c88bec4d123779ea67aff4d8c547e1a4af4926f7e58b487553c5429`，受控安装器commands/install.py SHA`3edc1cf45be2c3696a20ddfb0403713f396cdad0178a6f5edd08e81da028d595`。只传这两文件、核白名单SHA后唯一执行`python3 -B E2/commands/install.py`；先断言目标旧SHA／非symlink／未被并发修改、完整argv等于原eng072、环境差异仅上述删除，bash -n不执行脚本。独占备份同目录`start-model.sh.bak-eng073-envtrim-20261026`及E2/start-model.sh.before，保留原uid/gid/mode原子替换；后核目标／备份／host-container SHA、语法、五份关键源码／容器ID和8010监听状态不变。原eng073备份及原回执不覆盖。

已按上述SHA脚本单次执行完成，目标新SHA`8703b9356c88bec4d123779ea67aff4d8c547e1a4af4926f7e58b487553c5429`。独占新备份SHA`d71854f0f9e4e263ad1e7ccea9d165f099d534d5fae3dcf993adff3e4f306dad`与本次修改前文件精确相同，旧eng073备份保留。vLLM完整argv／nohup日志接口不变，环境差异仅预声明项；主机／容器内目标SHA及bash-n、原uid/gid／0755、五份关键源码SHA、容器ID与8010前后未监听均通过。

独立回读5个manifest成员／实际目标／备份核验通过；E2/RESULT.json SHA`5c21c084a585df3e051e8d085566391cbf39c723dc53223a8348a076e1a0dbb5`，E2/manifest.json SHA`f327ae690df071e57a32b9193da67dfd87458495e1acefdd014a8f3a93919236`，状态`env-trim-script-only-CPU-verified-not-executed`和`independent-readback-passed`。决定retained脚本交付；固定pin047／BF16／多模态16图／算子修复不变，0缓存删除／日志覆盖／启动／重启／新推理／GPU测试／8035／提交推送。默认cache不等于关闭cache，未来首启／缓存状态和模型新绑定未经实测，不签新gate或性能结论。以下是上一阶段交付历史，其target SHA不再是当前目标。

状态：已完成指定启动脚本更新，完整argv／环境策略和独立CPU回读核验通过；仅工程交付，不是新性能／精度实验。2026-10-26用户明确要求将最新启动参数更新到PPU-07 `/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh`。本次0启动／停止／重启服务，0推理或GPU请求，不访问8035，不提交推送。

## 方向、依据与主要变量

现有文件为旧纯文本配置（`--language-model-only`、旧通信／黑名单设置），SHA`58d1b0655ed2a13d0ecaddba2e5004e0e8cd0e2458aca68d84e7cfa8cb70845c`，uid/gid0、mode0755、普通文件非symlink，父路径规范解析一致。目标容器`qwen3.8-flash-opt-ppu07-20261015`running，真实`/mnt`→`/mnt` RW bind，因此宿主机／容器为同一目标文件。2026-10-26新核8010未监听，旧健康空闲记录是历史状态，本Agent未操作服务。

参考唯一实际验证配置为eng072 `model-regression-001/launch-service.sh`，SHA`599757578c9a355a3c5bd0d7b89ae809ebf3182e88d8047774dd14098da11e59`。该配置曾通过14请求minimal及acc021 GPQA175/198新gate、acc022 ERQA251/400原生score；旧结果不冒充本次重启或新绑定验证。

## 内容与适用边界

保留用户入口原`nohup`后台运行及`./service.log`截断输出接口；将vLLM实际argv和export/unset/source/cd/set策略同步参考配置。保留BF16、TP8物理8–15、8010、上下文80000、显存.85、prefix cache关闭；去掉language-model-only，image16/video1、像素4096–262144、video8帧/fps2；语言FULL_AND_PIECEWISE、encoder graph/compile false；三canonical `/opt`源码editable及FGVLLM开关1、normal_/index_select、原eng072隔离cache和固定pin047/bootstrap路径不变。没有更改任何三库源码或算子修复。

仍依赖既有eng072 bootstrap／fixed-tuning-config，不擅自去除以改变已验证路径；本次不创建冷cache或改选参。调用时必须在指定模型容器中。未来执行该入口会按用户原接口覆盖工作目录service.log；本次不执行，也不触碰旧实验service.log。

## 执行前命令与回退计划

E=`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-073-start-model-script-sync-20261026`，只新建且拒绝已有E。本地`/private/tmp/qwen38-start-model-20261026.F7zCU1`。候选`commands/start-model.sh` SHA`d71854f0f9e4e263ad1e7ccea9d165f099d534d5fae3dcf993adff3e4f306dad`，受控安装器`commands/install.py` SHA`edd45eb11ec8880db57f0fd9399f5293a361ba7855abc36437dd32338e56da99`。

仅传这两个白名单SHA文件到E/commands后，唯一执行`python3 -B E/commands/install.py`。安装器先核旧目标／参考SHA及非symlink、目标容器／挂载和8010未监听；仅`bash -n`语法检查不执行脚本，独立比较完整argv与全部环境策略精确等于参考。独占备份`/mnt/nfs/users/jinghao/qwen3.8-flash/start-model.sh.bak-eng073-20261026`及E/start-model.sh.before，不覆盖原备份；核旧文件未并发改变后以原uid/gid/mode原子替换。前后只读核容器、8010、五份关键源码SHA不变，主机／容器实际目标SHA及语法通过后保存RESULT／manifest。失败保留原错和备份，不启动服务或自动回滚运行状态。

回退仅恢复指定脚本的备份字节，需再次明确操作；不通过重启、恢复模型或执行旧controller进行回退。

## 正确性、性能与决定

本地bash -n、参数JSON、模型argv／单nohup解析、安装器AST通过；远端完整argv与eng072 expected-argv逐字相等、全部export/unset/source/cd/set策略精确相等，主机及容器中bash -n与实际目标SHA均通过。目标uid/gid0、mode0755保留，原脚本备份SHA与旧目标精确相同，5份关键BF16／MoE原布局／index/index_put/randn源SHA及容器ID前后不变。8010前后均无监听，未执行任何模型启动脚本，旧eng072日志保持不变。

独立回读核5个manifest成员、当前目标及相同挂载容器文件、原备份全部SHA通过：RESULT SHA`f307fb3f2b71cfd3d721f3d377743371ab8dcdf41ce5044d0f7159ba6d849f75`，manifest SHA`4f8cad718026cbb82126f98a99714649552f2441ae3364c20e5110b77cc66098`，目标新SHA`d71854f0f9e4e263ad1e7ccea9d165f099d534d5fae3dcf993adff3e4f306dad`。回执状态`updated-script-only-CPU-verified-not-executed`及`independent-readback-passed`，原件在E/RESULT.json、E/BEFORE.json、E/start-model.sh.before、E/manifest.json和E/commands下。

决定：retained配置交付。新模型minimal／formal／性能均not_run，用户只要求配置更新，不签新gate、性能或当前运行通过结论。原服务未监听状态保持；新配置仅未来手动启动时加载。无新monitor，无服务恢复动作。
