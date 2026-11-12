# 用户新容器的 GDN 导入对照

用户指出 mx-59/vllm0202-fl-release02-20261106 的未修复 Plugin 未复现循环导入。只读已确认 Plugin 为干净 release/0.2@6e11d0ab687247fdf4347a52788ec4f2baf57c79，与 PR699 基线一致；vLLM0.20.2+empty，服务正在运行。现有日志未见 Failed to import maca patches；不能把 FlashAttention 扩展缺失中的 partially initialized 文案混为 GDN 循环。

拟在该容器中执行有限 3 个新鲜解释器导入入口：原 vllm CLI --help（不启动服务）、layernorm、topk_topp_sampler。使用运行服务的解释器、环境与 cwd，仅加 -B/PYTHONDONTWRITEBYTECODE 防止 pyc 写入；观察器只记录 import，不替换 loader 或源码。检查 GDN 模块和 OOT registry、真实平台与警告，前后校验 API 身份和 Plugin/vLLM 完整 Python 源码。最多120秒/入口，无模型构造/请求、GPU kernel测试、重启或源码变更。

远端独立目录：/public-flash/jinghao/qwen3.6-35B/20261104-qwen36-main-config-compat-mx59-001/gdn-user-container-audit-20261106-001；commands/probe.py 执行前独立归档 SHA，输出 native-result.json。旧复现目录和源代码保持。

## 已完成：用户的正常启动观察成立，问题依赖导入顺序

三个入口均使用该容器当前实际 `/opt/conda/bin/python`、API 进程环境和 cwd，在新鲜独立进程中执行；没有加载历史源码快照，没有恢复旧代码，没有改写任何源码 loader。MetaPathFinder 仅记录被导入模块，始终返回 None，不提供替身或替换模块。

| 入口 | 原生退出码 | GDN 模块 / OOT registry | 结果 |
|---|---|---|---|
| 原 `vllm` CLI 初始化 + `--help` | 0 | 已加载；GatedDeltaNetAttention → MacaGatedDeltaNetAttention | 无 maca patches 循环警告 |
| 先 `import vllm.model_executor.layers.layernorm` | 0 | 未加载；GDN registry 为空 | 3条 `RMSNormGated` partially initialized 警告 |
| 先 `import vllm.v1.sample.ops.topk_topp_sampler` | 0 | 未加载；GDN registry 为空 | `rocm_aiter_ops` partially initialized 警告 |

全部解析得到实际平台 `vllm_fl.platform.PlatformFL`、vendor metax，实际 Plugin 文件来自 `/workspace/vllm-plugin-FL/vllm_fl`。注册结果只代表各导入入口返回时的新解释器状态；没有读取正在运行的服务进程内部 Python registry，也不推断后续其他导入永远无法恢复。

### 顺序差异

正常 CLI 首先经 general plugin 的 quant_linear / fp8 注册加载 `_custom_ops`，继而进入 MetaX patches。导入 GDN 时，layernorm 尚未进入初始化；GDN 可以正常导入 layernorm 并完成 OOT 注册。

直接导入 layernorm 则先进入 `layernorm → kernels → PlatformFL.import_kernels → MetaX patches → GDN → layernorm.RMSNormGated`。最后一步回读尚未定义的 RMSNormGated，异常被 PlatformFL 捕获并输出警告，因此解释器可以 exit0，但该入口结束时未完成 GDN 注册。先导入 sampler 的对应回路经过尚未完成的 `_aiter_ops.rocm_aiter_ops`。

用户正在运行的服务日志没有 `Failed to import maca patches`，有 Application startup complete；与 CLI 对照一致。日志中 FlashAttention `_vllm_fa2_C` 缺失带有 partially initialized 文案，是另一条路径，不能用作本 GDN 问题证据。

### 环境对照及结论修正

- 当前容器实际分支为 release/0.2，而非名为 0.20.0 的分支；commit 与 #699 基线一致，工作树干净。
- 新旧容器 vLLM0.20.2+empty、Torch2.8.0+metax3.7.0.7、mcoplib0.4.5+maca3.7.0.37.torch2.8 一致。`_custom_ops.py`、`_aiter_ops.py`、`layernorm.py`、`kernels/__init__.py` 的 SHA 相同。
- FlagGems revision 不同（新容器41be2075e、旧容器a456722a1），但同一新容器内已经同时得到正常/异常两种顺序，不需要把依赖差异作为解释，也未证明它有因果贡献。
- **#699 的准确定位是 import-order-dependent GDN registration failure，不能表述为该 release 正常 vllm serve 必然无法启动。用户当前正常服务是有效的成功路径证据。**
- 此 PR 可减少导入顺序耦合，但不能据此宣称当前正常服务需要它才能运行，或有精度/吞吐收益。本次没有更改公共 PR、容器源码或运行参数。

### 原始证据

- `commands/probe.py` SHA256 `062c4d64567a89ccb5ce106ea57dc2214b25b46dddd86bcdbe03066429b7c33d`。
- `result.json` SHA256 `d7f09bce38571ceea136b35e1d8fa729e3ccde3961cb196b2597564fd249a69c`。
- `native-result.json` exit0；三个子进程分别39.21/38.19/37.44秒、均自然退出。
- API 精确身份前后相同；Plugin/vLLM 共1933个 Python 文件前后 digest `2d852b228c199cb24da64662972b8d9c8b304da9d1558eec9e8913f4d76601fe` 相同。
- 最初只读探查使用系统 `/usr/bin/python3`，确认其没有推理依赖后改为服务实际 Conda 解释器；该初始探查不作为运行环境证据。另一次只读版本比较命令转义错误在 Host Python 解析阶段失败，随后用独立脚本完成比较，无服务操作。

## 按用户指令反馈到 PR

2026-11-06 已发布 [PR #699 复核评论](https://github.com/flagos-ai/vllm-plugin-FL/pull/699#issuecomment-6677716331)，列出正常 CLI 成功和两个直接导入入口失败的真实结果、退出码0/注册缺失、验证方式及边界。同时在 PR 描述开头加入 scope clarification 并链接该评论，明确不是正常服务必现启动故障，也无精度/性能收益证明。已读取评论确认正文发布成功；base、head、代码、服务均未改变。
