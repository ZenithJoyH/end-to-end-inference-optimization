# 按参考脚本简化 BGE-M3 启动入口

> 本文保留24行版本的整理快照。按后续用户要求，当前改为23行并自动加载Plugin平台默认配置，详见[默认配置调整](serve-default.md)；本文中的BGE专用YAML及追加名单设置已移除。

2026-11-05。用户要求将 mx-59 的 `/public-flash/jinghao/BGEM3/serve.sh` 再简化，参考同机 `/public-flash/jinghao/qwen3.6-35B/start-model-flagos.sh`。仅修改这个启动脚本，不运行或重启模型服务，不修改参考脚本、容器、YAML或三库源码。

连接已通过本项目inventory与`connectivity-check --limit mx-59`。目标为非符号链接0755/root:root，旧SHA `4e3bd05a3ec7d2a63d59d7561d06ac9c5da5e37461d00b32627bbf844e65d993`；参考脚本SHA `97f1bea255f889c505b4183a5d43a2d94837ae2c5d5a4cf11d39ec73bf604689`。当前BGEM3目录仅剩serve.sh，原同级Plugin配置副本已不存在，旧配置路径已失效。容器真实Plugin根仍为 `/workspace/bge-m3/tune-src/vllm-plugin-FL`，实际服务YAML、dispatch YAML、`/flagos/bin/vllm`和模型config均存在可读。

## 简化方案与验证

候选 `/tmp/bgem3-serve-simple-20261105.sh` 共24行，SHA `0456211dc9f711eab99d7221f5c1ada65a8fdd00aae5dfb2dfc820ca46ab6f0e`。按参考脚本平铺必要环境变量和一条nohup命令；服务YAML中的全部启动参数展开为显式CLI，只保留真实安装目录内的dispatch配置引用。保留FP16 dense、TP1、eager、127.0.0.1:8000、原seed与资源/长度参数、原MetaX算子选择及GPU可见性继承，不照搬参考脚本的卡号或conda路径。

移除函数、帮助/dry-run、模型位置参数和多层环境路径覆盖；按用户要求直接编辑可读的启动命令，尾随`"$@"`仍允许追加vLLM参数。改为参考脚本同样的后台方式，日志为执行目录`./service.log`，建议先cd到BGEM3目录运行。

本地`bash -n`、ShellCheck通过；以nohup函数捕获命令和环境（没有调用vLLM），默认与`--port 8001`覆盖场景通过，确认JSON参数、whitelist清除、blacklist append继承与尾随参数正确。临时验证产物 `/tmp/bgem3-serve-simple-check-20261105.l2l_6qr3`。部署后在Host/容器复核SHA及bash语法，捕获的默认CLI会与真实安装的服务YAML逐项对照；不做模型服务或性能测试。

## 执行与回退计划

部署工具先保存为本地 `/tmp/bgem3-serve-simple-deploy-20261105.py`，上传到mx-59唯一 `/tmp/bgem3-serve-simple-deploy-20261105-9x6m4p.py` 后执行。只允许目标路径/旧SHA/参考脚本SHA一致时变更；保存控制工具和原文，保持owner/group/mode，不调用曾在NFS失败的copystat/xattr。对候选运行bash -n后，同目录原子替换；再次核验SHA和属性。

执行入口：`ssh mx-59 'python3 /tmp/bgem3-serve-simple-deploy-20261105-9x6m4p.py'`。独占临时证据目录和原文备份路径由工具生成并写入回执。回退仅在目标无后续编辑时恢复原文和属性，不触碰任何服务；不自动执行回退。

## 完成结果

- 已部署24行新脚本，SHA与候选一致：`0456211dc9f711eab99d7221f5c1ada65a8fdd00aae5dfb2dfc820ca46ab6f0e`；Host与BGE-M3容器内一致，owner/group/mode仍root:root/0755。
- 备份：`mx-59:/public-flash/jinghao/BGEM3/.serve.sh.simple-nog8hu60.original`，SHA等于旧脚本。Host独占执行记录 `/tmp/bgem3-serve-simple-20261105.p62bsd1g/{deploy.py,original.sh,candidate.sh,FINAL_REPORT.json}`。
- 本地ShellCheck、Host及容器bash语法通过；默认/尾随参数的nohup命令与环境捕获通过。容器内只读验证将15项原YAML服务选项逐项与捕获CLI比较，全部一致；host/port、实际dispatch配置、模型config与vLLM程序路径均核验。
- 未运行vLLM、未创建模型服务或实际service.log、未重启任何服务；未改参考脚本、三库、YAML或依赖。

用户可在BGE-M3容器内执行 `cd /public-flash/jinghao/BGEM3 && bash serve.sh`，日志在同目录`service.log`；也可追加`--port 8001`等vLLM选项。这里仅说明入口，没有代用户执行启动。
