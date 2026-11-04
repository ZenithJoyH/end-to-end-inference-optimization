# main-001 基于官方main直接维护

当前安装Plugin `0.0.0+ga696859b9.d20261020`，实际导入 `/workspace/vllm-plugin-fl/vllm_fl/__init__.py`。运行时只读核验官方main HEAD与当前HEAD均为 `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`；origin为官方仓库，当前为detached HEAD，暂存区与工作区混有本任务改动。

按用户要求，归档后切回同commit的main并跟踪origin/main，将改动统一保留为未暂存/未跟踪的普通文件。不得使用stash保存或恢复改动，不重置/覆盖源码，不提交或推送；若main基线漂移，不自动重放或覆盖，而保留状态继续核验。完成后核对3库逐文件内容、实际安装和原服务。

## 最终状态

- 已安装版本：`0.0.0+ga696859b9.d20261020`，路径 `/workspace/vllm-plugin-fl`。
- 基线：官方 `https://github.com/flagos-ai/vllm-plugin-FL.git` 的 `main`，HEAD `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，与本轮 `git ls-remote` 查询的官方main HEAD相同。
- 已从detached HEAD切为本地 `main`，跟踪 `origin/main`。已有适配/优化直接保留为普通工作区修改与新增文件，暂存区为空。
- 没有用stash保存、迁移或恢复改动；只读预检未发现已有stash，执行以ref检查确认仍不存在。没有重置源码、提交或推送。
- Plugin/FV/FG逐文件指纹与操作前一致；实际导入和Plugin注册通过。当前包版本不变，不需要重装。未改启动脚本，源8035健康；没有发模型请求或运行新的数值/精度/性能测试。

源码未变，Plugin tree仍为 `374b2b47b83dcf35504f716dd088430be14045b0329c3aacb7a669bf989152d9`。之后直接在该main工作区编辑；不要求生成新的自定义提交，也不以stash管理交付代码。

原生证据 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261020-minimax-m31-latest-stack-migration/profiles/main-001-20261020-01/result.json`、`git-before.json`、`git-after.json`、`source-before.json`、`source-after.json`、`runtime-verified.json`；完整改前源码和Git元数据归档为同目录 `plugin-before.tar.gz`，SHA256 `ecfa6f2159b86b6c3728f92bb248e350681774dfb496d2fbab2e95196b69a5b9`。精确证据SHA见 [state.yml](state.yml) 的main-001；归档仅在宿主机留存，不在容器中增加另一份安装源码。
