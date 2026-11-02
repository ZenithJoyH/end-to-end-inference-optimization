# FlagGems-vllm 切换源码 editable 安装

2026-10-22；`mx-104` / `qwen3.6-35B-verify`。用户明确要求将该容器中的 FlagGems-vllm 改为 `/opt/FlagGems-vllm` 的 editable 安装，保持优化逻辑并核验实际加载路径。本轮沿用既有案例，远端新增产物目录 `editable-001/`。

## 执行前记录

- 已重新通过 inventory 与仅限 `mx-104` 的 connectivity-check。
- 源仓库 HEAD：`e1a02b6b2e47abea9a6cfeaaf3431f50f7f476f8`；已有 MoE、GDN 两个 dirty 文件保留。
- 当前旧分发版本：`0.1.0`，普通安装至 `/opt/conda/lib/python3.12/site-packages/flaggems_vllm`，`direct_url.dir_info` 为空。
- 构建入口为 `setuptools.build_meta`，src layout；版本固定 `0.1.0`，无 setup.py、安装 entry point 或仓库外脚本记录。
- 实际解释器 `/opt/conda/bin/python`，pip 24.3.1、setuptools 80.10.2、wheel 0.45.1；当前无模型服务/worker。
- 源码与安装版共 276 个运行源码/配置文件一致；MoE SHA256 `c575c8a798232cd86e18e1239d2a314cd0e3afe21faf5951c45798c84f706679`，GDN SHA256 `109a6f92b0a7bb728acc6029d471bdb302d097c9ef04ded48bf8ccc7b6c0e04d`。

安装命令限定为 `/opt/conda/bin/python -B -m pip --isolated --disable-pip-version-check install --no-index --no-deps --no-build-isolation --no-cache-dir -e /opt/FlagGems-vllm`。不升级依赖，不改代码、Plugin backend、模型或容器配置。

执行前将旧包完整目录与 dist-info 在远端打包备份，保存源码树哈希、Git 差异、分发版本与依赖清单。命令先保存为远端 `commands/install-editable-001.py` 再执行。安装后从仓库外工作目录启动新解释器，检查 editable 元数据、旧副本是否遮蔽、全部已加载本包模块来源，以及 MoE/GDN 原始函数 code object 和源码的对应关系。

远端案例根目录：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit`。备份和一次性执行脚本仅保存在该案例目录；本地保存本摘要和必要 SHA。

安装脚本执行前 SHA256：`24fb6849e20c429518075cfe64a3d4bf4d9cf19feb7f5e11be68e1258af40371`；已对宿主机入口与容器内 payload 做语法检查。

## 执行结果

**已完成，当前 FlagGems-vllm 为 editable 安装，直接加载源码仓库。** 安装完成时间为 2026-10-22 18:27，导入核验时间为 18:28（Asia/Shanghai）。

| 核验项 | 结果 |
|---|---|
| 版本 | 保持 `0.1.0` |
| `direct_url.json` | `url=file:///opt/FlagGems-vllm`，`dir_info.editable=true` |
| editable 入口 | site-packages 的 `__editable__.flaggems_vllm-0.1.0.pth`，内容仅 `/opt/FlagGems-vllm/src` |
| 实际包入口 | `/opt/FlagGems-vllm/src/flaggems_vllm/__init__.py` |
| MetaX MoE / GDN | 实际文件均位于源码 `runtime/backend/_metax/fused/` |
| 已加载模块 | 156 个本包模块的 `__file__` 和 spec origin 全部位于该源码树 |
| 函数代码 | MoE 31 个、GDN 14 个顶层函数（含装饰器内部原函数）与源码编译结果全部一致 |
| 与旧安装对比 | 31 个 MoE 函数 code object 指纹与上一轮安装副本核验一致；整包 276 个源码/配置文件 SHA 无变化 |
| 工作目录/环境遮蔽 | 从 `/tmp` 启动正常新解释器通过；另以 `python -I` 排除 cwd/PYTHONPATH 干扰，仍解析到源码 |
| 配置资源 | `importlib.resources.files('flaggems_vllm.runtime')` 解析到源码 `runtime/` |
| 旧安装副本 | `/opt/conda/lib/python3.12/site-packages/flaggems_vllm` 已不存在 |
| 依赖与其他组件 | 所有分发的版本和 requires 清单无变化；Plugin、vLLM 的 HEAD/status/diff 及 FlagGems 源码指纹无变化 |
| 源仓库状态 | HEAD 和原 MoE/GDN dirty 状态不变；安装未改推理源码 |

`importlib.metadata` 同时可枚举到 site-packages 的有效 dist-info 与源码下构建生成的 `flaggems_vllm.egg-info`，两者版本均为 `0.1.0`。有效 `distribution('flaggems-vllm')` 返回 site-packages dist-info，含正确 editable direct_url；egg-info 是同一源码构建元数据，不是第二套执行代码。

安装成功后，普通 Python 源码修改由后续新解释器直接加载，无需再手动同步 site-packages；已运行的 Python 进程仍须重启加载变更。修改依赖或打包元数据时仍需重新安装。本次没有改变 Plugin backend；Plugin 原先直接使用 FlagGems 的 MoE 调用链不因本次安装方式变化而切到 FlagGems-vllm。

## 备份、证据与回退

以下均相对远端案例根目录，实际内容保留在指定 Host：

| 路径 | 内容 |
|---|---|
| `editable-001/previous-installation.tar.gz` | 原 site-packages 包完整目录与 dist-info，逐文件校验备份内容通过 |
| `editable-001/before.json` | 原源码/安装哈希清单、Git 状态、版本/依赖及其他组件指纹 |
| `editable-001/source-before.patch` | 保留的 MoE/GDN 源码修改 |
| `editable-001/pip-install.log` | 离线 editable 构建、旧包卸载及安装日志 |
| `editable-001/installation.json` | 安装结果、无漂移检查及 editable RECORD 文件哈希 |
| `editable-001/verification.json` | 156 个模块来源、45 个函数校验及 isolated resolver 证据 |
| `editable-001/README.md` | 本记录远端副本 |
| `editable-001/publication.json` | 发布文件与命令的 SHA 清单 |
| `commands/install-editable-001.py` | 实际安装命令与前后保护检查 |
| `commands/verify-editable-001.py` | 实际导入、函数和配置路径核验 |
| `commands/rollback-editable-001.py` | 已准备、未执行的安装回退脚本 |

关键 SHA256：

- 旧安装备份：`9d05e2a0a837d783125ab2ff58be0578d3f06b680e7c70cc502a26e86edd917d`。
- 安装脚本：`24fb6849e20c429518075cfe64a3d4bf4d9cf19feb7f5e11be68e1258af40371`。
- 核验脚本：`fae79ce055d33afbf1985e1814a9e316fbedb5e770d6bee1606e5b6c57568711`。
- 回退脚本：`f4cba3b4cd7feea0601c644e01abd0370dc2424d6c285977f9d63f4586899af8`。

需回退时，在 `mx-104` 运行 `python3 /public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit/commands/rollback-editable-001.py`。脚本先检查源码未产生后续变化、editable 元数据哈希、备份 SHA 和无 worker，再卸载本轮 editable 入口并恢复原安装副本，不改源码。检查失败即停止，避免覆盖后续工作。不要使用上一轮 `rollback-moe-001.py` 作为本轮安装回退；其范围只是历史源码同步。

本轮未启动模型、执行设备 kernel、graph、精度或性能测试；结果属于安装方式切换与新解释器代码一致性核验。未修改模型、容器配置、算法或优化参数，未 commit、push 或创建 PR。
