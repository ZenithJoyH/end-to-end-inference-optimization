# delivery-001-retained-fp32-launch-script

用户要求更新指定启动脚本。仅交付当前保留的OP007 FP326ea/full21配置，不启动或重启服务，不采用未晋级OP010候选。

执行前核验四仓库源码一致、目标脚本为普通文件、old SHA 9af0fecf055f2b43c3c24148ab5be0dcc0c73008fc3a9d0971b4aec61346924d。原756537已是zombie，容器内未发现模型服务；历史gate只绑定已停止实例，后续启动需重新绑定。

状态：prepared。远端命令：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery001-20261015T045016Z-apply.py`，SHA `a359bb8a0056db4f9bba90116951ddd0c1b2cf87d2f4b2773c11616a932ec966`；载荷：`/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery001-20261015T045016Z-start-model-flagos.sh`，SHA `1908f67afd7d5acb63812e988b8a492c920932259b0f2339273b8ce862566625`。先执行CPU-only `--check`/bash语法，再备份原件、校验old SHA并原子替换，替换后仅重复check；日志唯一命名，原8002不重启。

首次替换在NFS复制备份扩展属性时EIO退出，目标未改，已有备份内容保留。V2只复制普通权限与时间并核验备份SHA，不复制扩展属性。恢复命令 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery001-20261015T045016Z-apply-v2.py` SHA `a4ce3c7b7227d1396b78939b5ddd01645a90bd0382d4923c2e7f3279d19c1574`，不重发模型请求。

## 交付结果

状态：completed/script-updated/not-started。原件备份 `/public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh.bak.20261015T045016Z`（SHA与旧脚本一致），新文件SHA `1908f67afd7d5acb63812e988b8a492c920932259b0f2339273b8ce862566625`；回执 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/delivery001-20261015T045016Z-receipt.json` SHA `f8ff48f3c546ac2ad3656260fa9de405069e45e74808c0e38f7951b92b29f049`。bash语法、容器内与宿主机入口--check均通过，未启动/重启服务、未请求模型、未运行性能。

默认进入独立优化容器 `qwen36-27b-fa-opt-20261012`，GPU2/3、18002、served name qwen36-fa-opt；TP2 BF16、8192、prefixoff、graph64、完整21项FG+attention1/no blacklist及原FP32源码均保留。启动前核验四repo SHA，端口占用拒绝启动，日志唯一文件。原8002服务不操作；旧源码/原容差不变。

在mx-59宿主机或优化容器内运行 `bash /public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh`；加 `--check` 仅检查不启动。不支持源容器私有代码路径，避免误用其环境。服务启动后需完成readiness和graph/C8/native gate rebind，旧166/198不是新实例已通过的声明。

## 用户要求简化

新修订prepared：去掉宿主机wrapper、源码hash/端口检查、--check模式及profiler配置，保留全21FG、私有FP32路径、独立cache和必要vLLM参数。在优化容器内执行，GPU2/3、18002不变。命令 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery001-20261015T045937Z-simplify.py` SHA `cc189438e9304c432853580208f253500eab53578aa34c10aac2d36e4478dd5f`；载荷 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/commands/delivery001-20261015T045937Z-simple.sh` SHA `33098fd25721471cce89a126ce33cfac527504d578bfb817736f5ff1bfeb740a`。仅语法验证，不执行启动。

简化版已替换，22行；bash -n通过，未启动或重启。新SHA `33098fd25721471cce89a126ce33cfac527504d578bfb817736f5ff1bfeb740a`，备份 `/public-flash/jinghao/qwen3.6-27B/start-model-flagos.sh.bak.20261015T045937Z`。回执 `/public-flash/jinghao/qwen3.6-27B/optimize/flash_attention/20261012-qwen36-27b-metax-flash-attention/results/delivery001-20261015T045937Z-simple-receipt.json` SHA `87ed3952b9206e235678dc798fa6243dac39934381c7c80822697cd179e3d29a`。现入口仅在优化容器内直接执行，不再支持旧版宿主机自动跳转与--check。日志追加到 `/public-flash/jinghao/qwen3.6-27B/service-qwen36-fa-opt.log`。
