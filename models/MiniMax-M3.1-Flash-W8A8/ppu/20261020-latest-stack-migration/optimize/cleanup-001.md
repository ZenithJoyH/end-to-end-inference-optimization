# cleanup-001 仅保留最终安装的 Plugin 与 FlagGems-vllm

当前路径更新：两库已按用户要求更名为 `/workspace/vllm-plugin-fl`、`/workspace/flaggems-vllm`，见 [rename-001](rename-001.md)；下文原路径为本实验执行时的历史记录。

用户明确要求清理最新容器中的旧版本。预检确认实际 editable 安装仅各一份，分别指向 `/workspace/minimax-m31-latest-stack-20261020/plugin` 和 `/workspace/minimax-m31-latest-stack-20261020/fv`。10 个旧私有源码目录未被安装引用、进程工作目录或最终源码符号链接依赖；执行前再次检查进程文件引用与完整源码身份。

保留所有最终源码和依赖，先将旧目录（包括未提交改动）归档到宿主机案例目录，逐文件 SHA 验证后才移除明确列表内目录。共享 `/mnt`、旧容器、FlagGems、vLLM 和全局启动脚本不改。本轮不启动模型、精度或性能测试。执行结果与原生归档证据将在完成后写回。

## 完成结果

已清理10个旧私有源码目录：原 `/workspace/FlagGems-vllm`、`FlagGems-vllm-gems-opt-20261016-01`、`FlagGems-vllm-pr924-fb70fd2-20261014-side-01`，原 `/workspace/vllm-plugin-FL`、`vllm-plugin-FL-024plugin-opt-20261016-01`，以及 `/workspace/pr-validation/` 下5个历史PR验证源码目录（空父目录一并移除）。历史未提交/未跟踪文件均先归档，未丢弃。

容器私有目录中仅保留最终版本，editable 安装来源各唯一：

| 库 | 最终安装源码 | 安装版本 |
|---|---|---|
| Plugin | `/workspace/minimax-m31-latest-stack-20261020/plugin` | `0.0.0+ga696859b9.d20261020` + refactor-001最终源码 |
| FlagGems-vllm | `/workspace/minimax-m31-latest-stack-20261020/fv` | `0.3.0.dev1` + 已保留优化 |

对3库重新计算完整源码指纹，与清理前/上一轮最终候选一致；两库实际导入、唯一发行版/direct_url、Plugin注册、scaled INT8/MoE公开实现来源均通过。扫描 `/workspace` 仅余上述两个相应源码包根。FlagGems、vLLM、共享 `/mnt` 和全局启动脚本未变；源容器保留、8035健康200。本轮没有停止/启动模型服务，没有发模型请求，也没有重装或升级依赖；不新增数值、精度或性能结论。

归档在容器外的宿主机案例目录，使用前后源码清单一致，13,875个文件/链接条目逐项校验通过：

- `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/cleanup-001-20261020-01/historical-plugin-fv-sources.tar.gz`
- SHA256 `0328ee911244f7fcefb5cf453bc13b4aabe5727322adcc386e9598ac16321ffa`
- 清单 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/cleanup-001-20261020-01/historical-sources-manifest.json`；原生校验回执 `archive-verified.json`、安装回执 `final-installation-verified.json`、终态 `result.json` 同目录，精确SHA见 [state.yml](state.yml)。

只在需要恢复历史材料时，从已校验宿主归档恢复明确目录至目标容器私有 `/workspace`；不用恢复旧副本来改变当前安装。归档不放回容器。源容器和共享挂载中的历史代码不属于本轮清理范围。
