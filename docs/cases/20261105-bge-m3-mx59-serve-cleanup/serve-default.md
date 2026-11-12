# 启动器改用Plugin平台默认配置

2026-11-05，用户要求调整serve.sh中的blacklist append及BGE专用YAML设置，生效YAML使用vllm-plugin-FL默认文件。范围仍为mx-59的`/public-flash/jinghao/BGEM3/serve.sh`，不改Plugin源码或默认YAML、不启动/重启服务。

已通过inventory及`connectivity-check --limit mx-59`。实际脚本旧SHA为`0456211dc9f711eab99d7221f5c1ada65a8fdd00aae5dfb2dfc820ca46ab6f0e`。当前Plugin没有default.yaml；`dispatch/config/utils.py`通过平台检测加载`metax.yaml`，设置`VLLM_FL_CONFIG`会走自定义配置覆盖路径。平台默认metax.yaml已经声明`attention_backend: [vendor:metax]`，默认FlagOS/OOT黑名单均含masked_fill、masked_fill_。

## 最小调整

移除BGE专用YAML路径和额外attention_backend排除，合并为：

```bash
# Use the plugin's platform defaults (metax.yaml on this machine).
unset VLLM_FL_CONFIG VLLM_FL_FLAGOS_WHITELIST VLLM_FL_FLAGOS_BLACKLIST VLLM_FL_FLAGOS_BLACKLIST_APPEND
```

清理环境覆盖是为了避免从旧shell继承自定义路径或白/黑名单而使默认配置失效；不把attention_backend塞入共享metax.yaml，也不使用BLACKLIST整体替换丢失平台默认屏蔽。其余服务CLI、必要环境、日志与后台启动方式不变，脚本23行。

候选`/tmp/bgem3-serve-default-20261105.sh`，SHA `2485353193d727df00e2bd78fde1af03c6b925568aa12d352c0625468d4efae5`。本地bash语法与ShellCheck通过。验证将以nohup替身截获命令，分别覆盖普通环境和故意继承旧YAML/白名单/黑名单/追加名单的环境；在真实容器中用实际配置加载器、policy和OpManager验证自动命中metax.yaml、默认黑名单保留、attention解析到vendor.metax，只解析不调用算子或vLLM服务。追加CLI参数仍须正常透传。

## 执行计划

部署工具`/tmp/bgem3-serve-default-deploy-20261105.py`先上传唯一Host文件`/tmp/bgem3-serve-default-deploy-20261105-k4m8p2.py`后执行。核对目标旧SHA与普通文件路径，独占备份原文，保留root:root/0755；bash语法通过后同目录原子替换，不复制NFS扩展属性，不触碰其他文件/服务。工具和回执放Host独占/tmp目录；备份在目标同目录隐藏唯一文件。回退需先核对无后续编辑，再从该备份恢复；不自动执行。

执行入口：`ssh mx-59 'python3 /tmp/bgem3-serve-default-deploy-20261105-k4m8p2.py'`。验证和部署结果在完成后补充。

本地命令捕获验证通过：默认与故意继承四个旧覆盖的场景均清除了这些变量，尾随`--port 8001`保留，默认vLLM argv与上一版完全相同。产物`/tmp/bgem3-serve-default-check-20261105.6jb4ifjo`。

首轮容器配置探针位于`/tmp/bgem3-serve-default-probe-20261105.m7j6_a9t`，真实加载metax.yaml且平台黑名单正确，但探针错误地要求impl_id必须为vendor.metax而失败；实际通用`vendor:metax`按既有优先级选择vendor.metax.bge_m3。已核对其源码：FP32 BGE能力分支以外委托原MacaBackend，不能把适配入口名称当成最终Attention类。未修改生产代码或默认YAML去迎合该断言，保留失败回执。

修订探针保存为`/tmp/bgem3-serve-default-probe-v2-20261105.py`并上传容器唯一文件：仍用真实配置加载器/OpManager，不替换provider；只注入BGE FP16的model metadata，以实际后端选择函数返回值与原MacaBackend及FLASH_ATTN注册类路径对照。该metadata测试不代表模型数值验证，不调用数值算子或启动服务。两种环境均通过后才部署脚本。

两种容器场景均通过，证据根`/tmp/bgem3-serve-default-probe-v2-20261105.09pl192v`。生效配置为真实安装的`dispatch/config/metax.yaml`（SHA `c76fbcc4cca4ae81bf7a8311af7106de801e1d7495c8502803f9074fa540c0b0`），blacklist恰为masked_fill、masked_fill_；默认strict=false，attention顺序vendor:metax。解析到既有vendor.metax.bge_m3适配器后，FP16 metadata实际返回`vllm_fl.dispatch.backends.vendor.metax.impl.attention.flash_attn.MacaFlashAttentionBackend`，与原生选择器/FLASH_ATTN注册路径一致。普通环境与故意注入旧覆盖的环境结果相同，均未启动服务/执行数值算子。

## 完成结果

- 已部署23行脚本，Host与BGE-M3容器内SHA均为`2485353193d727df00e2bd78fde1af03c6b925568aa12d352c0625468d4efae5`，root:root/0755保持不变。
- 备份`mx-59:/public-flash/jinghao/BGEM3/.serve.sh.default-saxe7xj6.original`，对应旧24行脚本、SHA `0456211d…`；Host部署记录`/tmp/bgem3-serve-default-20261105.utt9csx1/{deploy.py,original.sh,candidate.sh,FINAL_REPORT.json}`。
- bash语法、ShellCheck、普通/旧覆盖环境的命令捕获、真实默认配置/黑名单加载、FP16元数据后端类解析均通过。容器内实际脚本与探针验证的候选逐字节一致，默认metax.yaml SHA未变。
- 默认CLI与上一版逐项完全一致，追加参数仍透传；本轮只调整脚本的配置环境覆盖。没有修改任何YAML/Plugin/算子库，没有启动、停止或重启服务，没有模型数值/性能新验收。
