# env-059：补齐已安装Plugin的Git历史与审阅基线

- 用户2026-10-21明确授权补齐`/opt/vllm-plugin-FL`的Git历史，让VS Code显示未提交修改。仅元数据操作，不改变源码、editable绑定或服务，不提交推送、不访问8035，不推理/GPU测试。
- Host PPU-07，容器`qwen3.8-flash-opt-ppu07-20261015`，目标为容器私有真实目录。复用既有`/opt/qwen38-plugin-pr455-20261019/.git`只读历史，不获取远端新版本或复制原仓库配置/凭据/hooks。
- 真实基线：main `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`，PR455 `3cb373b11a81428c42ac5dd63348a00ee84f7863`；二者原合入树`d1a32bdb0540cf37e7ffb5ace6c0af8b51dc888e`仅是index树，并非合并提交。故HEAD保持main，PR455原合入暂存区，额外最终3文件保留2修改/1未跟踪；不伪造合并提交。
- 先在外部产物临时Git目录打包并核验历史、index、3文件/+242/-10预览，再仅发布`.git`。逐文件SHA和权限、editable origin/direct_url以及原仓库元数据前后核验不变。无checkout/reset/add/commit/push。
- 控制副本：`/private/tmp/qwen38-plugin-git-059.ARjGCF/{restore-git.py,restore-host.py}`。远端原始产物：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/env-059-plugin-git-metadata-20261021`，commands先保存再执行，目标8010精确身份及health前后只读核验。

## 结果

首次预览在发布`.git`前安全拒绝：除3文件外，发现已有`vllm_fl/configs/moe/E=256,N=512,device_name=nvidia.json`从原symlink变为普通文件。是历史快照的解引用表示差异，当前内容与原symlink目标逐字相等。没有改动或隐藏该差异，v2按2修改+1类型变化+1未跟踪校验，仍以原TREE作index，原PR内容与最终FP32差异如实分开。首次日志与临时Git目录保留，不当模型事故；服务身份/health不变，目标尚无`.git`。

修正后的元数据工具保存在同一commands下`restore-git-v2.py/restore-host-v2.py`，新`attempt-002`排他执行。仅工具允许显式已核的历史表示差异，不改源码或重跑模型验证。本次不是源码/数学改动，没有新模型、graph、精度gate或性能结论。

attempt002历史/fsck/index/真实差异/源码与安装不变预检全部通过；最终从/mnt到/opt原子rename因跨文件系统EXDEV拒绝，尚未发布`.git`，服务未动。随后保存`publish-git-v3.py/publish-host-v3.py`，于`attempt-003`仅复制已核元数据到私有`/opt/.vllm-plugin-FL-git-env059`，再次核验后在同一文件系统rename为目标`.git`，不重打包历史或改变任何源码。脚本SHA分别`e5fb77aeca04c3a18dffbc9f2497b58e43cd1ffa7ec145c605a5837a48933b73`及`daf3095d8f47ad8b7bf5bff6e032dc02e192c2d24c3259c27315f5863ca12bf6`；原失败产物完整保留。

## 终态：Git恢复完成，原件不变

- `/opt/vllm-plugin-FL/.git`为自包含真实目录，无alternates，不依赖原仓库存活。复用真实main/PR455历史，fsck通过；HEAD为main原commit，index为原合入TREE，未创建任何提交。
- VS Code暂存区显示原PR455合入：52文件/+9616/-255。Changes中为`test_operator_bindings.py`、`gpu/model.py`两处修改，新增未跟踪`gpu/tp_reduction.py`，共原FP32补丁3文件/+242/-10；另明确保留配置JSON的已有T类型差异，未隐藏/修复/伪装为新优化。
- 全部目标文件SHA及权限前后相同，editable origin/direct_url/版本相同，原来源仓库元数据预检不变；依赖修改0、新提交0、推送0、checkout0、推理/GPU/8035访问0。
- 8010 API2441711/start521315854/argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`前后不变、health200，重启0，仍原eng053已加载模块。monitor保持暂停。
- 最终证据`attempt-003/FINAL_REPORT.json` SHA`e7e0a44d174e58b3a81694322a40e30045ed5a9f245405f17fdebcccda6cc351`，`FINAL_MANIFEST.json` SHA`0b7fcd22047f176b8068a5d5da69755a513bd1fc587041e5414c84ac8e71c713`。文件列表、阶段diff、完整预检及工具失败记录保留同一外部根目录。
- 可恢复方式为移走本次新增`.git`保留备份，不触碰工作树；本轮未执行回退。没有新模型/graph/精度gate/性能结果。
