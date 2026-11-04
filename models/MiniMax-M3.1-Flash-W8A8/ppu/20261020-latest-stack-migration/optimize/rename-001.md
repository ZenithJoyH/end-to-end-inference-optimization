# rename-001 最终安装路径规范

当前策略更新：[policy-001](policy-001.md) 已撤回新增provider/平台白名单，恢复上游环境开关；新容器当前独立启动脚本显式设置既有开关=1。此前实验中的策略/启动SHA为历史记录。

按用户指令，将最新容器中的最终 Plugin/FV 真实目录分别更名为 `/workspace/vllm-plugin-fl` 与 `/workspace/flaggems-vllm`，同步 editable 安装，不保留旧目录或别名。保留官方发行版与 Python import 名称、源码内容和已有优化，不升级依赖。预检目标路径均不存在，容器无模型进程；独立启动脚本不含旧源码路径，预计无需改动。原容器、共享挂载与全局脚本不改。执行前归档控制命令及当前安装元数据；结论与证据将在完成后写回。

## 完成结果

两库已真实更名并按新路径无依赖、无网络索引重新 editable 安装；没有保留旧目录或软链接别名，没有复制第二版本。

| 项目 | 当前实际路径 / 版本 |
|---|---|
| Plugin源码 | `/workspace/vllm-plugin-fl` |
| Plugin实际导入 | `/workspace/vllm-plugin-fl/vllm_fl/__init__.py` |
| Plugin发行版 | `vllm-plugin-fl`，`0.0.0+ga696859b9.d20261020` |
| FV源码 | `/workspace/flaggems-vllm` |
| FV实际导入 | `/workspace/flaggems-vllm/src/flaggems_vllm/__init__.py` |
| FV发行版 | 官方metadata名称 `flaggems_vllm`（pip规范化名称 `flaggems-vllm`），`0.3.0.dev1` |

Python import 名称仍为 `vllm_fl`、`flaggems_vllm`，不修改官方工程/发行版定义。各库发行版仅一份，direct_url均指向上述新目录；Plugin注册、MoE/INT8公共接口实现来源核验通过。扫描安装目录未见旧路径引用，`/workspace`仅保留对应两份最终源码。

三库源码逐文件与更名前一致：Plugin tree `374b2b47b83dcf35504f716dd088430be14045b0329c3aacb7a669bf989152d9`；FV tree `2f62194e14f5f49eb579532aacbafd20716db372f260a2396b32fe4e1fe13f26`；FG tree `1798d770ab7e7247d9b91c45870297776a3f041055d5da8ec854cdd34178c8be`。当前优化与未提交改动完整保留。

新容器独立启动脚本仍为 `/workspace/minimax-m31-latest-stack-20261020/start-model.sh`，它通过已安装解释器加载两库、不含旧源码路径，内容与host归档版本均无需修改。原容器8035健康，全局启动脚本保持原样；未启动/重启模型，也未发模型请求。没有新增精度或性能结果，既有refactor最小回归保持为历史代码内容验证；没有正式gate复用或签发。

原生证据：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/rename-001-20261020-01/result.json`、`installation-after.json`、`source-before.json`、`source-after.json`；安装命令/日志与旧editable元数据归档均在同目录。路径与SHA见 [state.yml](state.yml) 的rename-001。历史env-001/refactor-001/cleanup-001中的路径反映当时状态，当前路径以本记录及state.current为准。

回退仅限目标容器无模型实例时，将两库真实目录按映射更名回原路径并用同参数重新editable安装；原元数据归档为 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/rename-001-20261020-01/editable-metadata-before.tar.gz`。不恢复历史源码副本，不影响共享挂载或源容器。
