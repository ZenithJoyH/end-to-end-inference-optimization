# env-018：容器内FlagGems-vllm升级至官方main

## 交付结果

2026-10-16 16:45+08:00已完成安装，版本`0.3.0.dev1`、官方main `65680392edfdd566a8c8e3cd99cba18e4dc3c26b`，新Python进程实际导入`/opt/qwen38-fgvllm-main-20261016-6568039/src/flaggems_vllm/__init__.py`，editable安装，无须增加PYTHONPATH。全包AST、真实thead后端import、20个HC/PLE/QSA/状态IO符号及旧Plugin直接依赖scaled_int8_quant导入通过；完整签名/模块/SHA在verification-v3.json。该import仅物理8设备能力查询触发上下文，CUDA tensor分配0字节，未执行算子或模型请求。

最终核验旧FlagGems-vllm源码241个Python文件逐SHA未变，FlagGems private017的index/index_put64位修复未变。8010 API2235393/start484916288与8035保护身份1948536/start484833646均保持，health均200。依赖升级0、服务重启0、新推理请求0、GPU算子测试0；Plugin/Gems/vLLM/权重/启动脚本未改，原诊断heartbeat保持PAUSED。

本次仅保留容器安装更新，**没有把新增算子自动接入当前模型调用链，也没有验证其PPU数值/graph/性能或模型精度**。上游相关实现位于ops/qwen4；这里只确认接口可导入，不将H100特化或上游测试结果当作PPU验证。后续接入需单独按适用shape/状态与graph契约验证；不得因已安装就签发gate或重启服务。

原始回执`environment/env-018-flaggems-vllm-main-20261016/FINAL_SUMMARY.json` SHA `b77223060703dc51cbe0145662f3389b0150624f90aed1a76844b67c7bf7b5b1`，包含安装/验证文件SHA清单。旧源码和安装元数据保留，回退仅将editable绑定恢复旧/workspace目录，不清理证据或自动重启。

## 范围与执行前事实

用户2026-10-16明确要求更新当前容器FlagGems-vllm，来源为官方仓库 https://github.com/flagos-ai/FlagGems-vllm 。按当前上下文仅PPU-07容器`qwen3.8-flash-opt-ppu07-20261015`；不重启/热切换8010、不改变Plugin/Gems/vLLM/权重/采样、不启动或重跑GPQA，不恢复先前暂停的监控。新算子接入和GPU/模型回归不在此次安装操作中宣称通过。

当前包`flaggems_vllm==0.1.0`以editable安装于`/workspace/FlagGems-vllm`，main HEAD `5865ed53b183e6d3aff69ad1823622a11679d257`、工作区干净。官方HEAD只读解析为main `65680392edfdd566a8c8e3cd99cba18e4dc3c26b`，作为本轮固定目标。容器仅挂载`/mnt`→`/mnt`，`/workspace`、`/opt`、site-packages均不在共享挂载内。现有服务API2235393/start484916288和8worker仍在，旧源路径必须保持不变，避免运行中惰性导入混用新旧源码。

## 实施计划、验证及回退

prepare及install已成功，固定main提交的版本为`0.3.0-dev1`（pip规范化为`0.3.0.dev1`）。已完整读取新AGENTS/pyproject/包与ops导出。当前Plugin的直接依赖为`flaggems_vllm.ops.scaled_int8_quant`，新增Qwen家族在上游目录命名为`ops/qwen4`，包含HC、PLE、QSA，不能仅因文件命名就断言当前服务已采用。

安装后验证脚本`commands/env018-verify-fgvllm.py` SHA `115c216d48e6e042548c1472997e2b4322e2f94670e64c919fa109487a14a6a2`，执行`python3 <script>`保存verification.json/import.log；新进程仅物理卡8可见，禁止CUDA lazy initialization、不创建tensor或运行kernel，核验新安装路径/20个新增接口/直接依赖导入及全包AST。若禁止初始化导致导入失败，须明确验证限制，不能作为设备算子失败或直接切换服务。

首次验证在读取`importlib.metadata.version('triton')`时失败，实际平台以FlagTree提供triton模块而非同名distribution；尚未导入新包，不是算子报错。保留原失败日志，修正版入口`commands/env018-verify-fgvllm-v2.py` SHA `46932d45d229cc49da031026213c8d7334d7629947f4e647aed6c58aa65e4af8`，改为读取实际triton模块版本/路径，产物独立verification-v2.json/log，不重复安装或覆盖第一次证据。

v2已验证新路径/版本及全包AST，但上游FLA/gdn2_native/chunk_intra在import时查询`torch.cuda.get_device_capability`，被验证脚本主动禁止lazy-init拒绝，非设备kernel失败。16:43只读ppu-smi确认物理8仍为本任务worker、空闲13418MiB，0–7为其他服务且不操作。v3入口`commands/env018-verify-fgvllm-v3.py` SHA `b12b7b4b1764b624237c14fd748f51fde28a5039bc25d8191145490b9f138c86`，仅CUDA_VISIBLE_DEVICES=8的新进程允许设备能力查询所需上下文，仍不构造张量/调用算子/发模型请求，退出前核验CUDA tensor allocation为0，产物另存verification-v3.json/log。这个必要导入检查不是GPU数值回归或服务重载。

v3已成功导入，vendor=thead，20个目标符号及scaled_int8_quant直接依赖均通过，CUDA初始化后张量分配0字节。最终只读复核入口`commands/env018-finalize-fgvllm.py` SHA `b76da3c579513efb08d609fa04f033372a9e5a0e72c813ab7c76379ac45c4b97`，执行`python3 <script>`保存FINAL_SUMMARY.json，核验旧包所有Python文件SHA、017的index/index_put修复、当前新包路径/HEAD/工作区、8010/8035身份与health，并哈希绑定本轮原始安装/验证证据；不写源码或改运行进程。

先保存安装元数据、旧源码SHA/工作区、挂载与进程快照；在远端唯一环境目录clone固定上游，复制到容器未挂载私有`/opt/qwen38-fgvllm-main-20261016-6568039`。完整读取新仓库AGENTS、pyproject及新增Qwen算子导出和实际调用签名后，执行`pip install --no-deps --no-build-isolation -e <private>`，不升级Torch/Triton/Gems等依赖，不设置额外PYTHONPATH。保留旧editable源码供回退。

安装仅对新Python进程生效，已有worker保持旧模块/搜索路径；不以包存在宣称服务命中新算子。验证新进程实际导入路径/源码SHA/版本与新增导出、旧Plugin依赖符号兼容；仅CPU静态和无张量分配import，任何GPU/graph/模型正确性和性能均not_run。若导入/依赖失败，不静默升级依赖或修改适配代码，报告并回退安装绑定。回退入口为在同容器`python3 -m pip install --no-deps --no-build-isolation -e /workspace/FlagGems-vllm`，同样不得自行重启服务。

远端目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/environment/env-018-flaggems-vllm-main-20261016`。控制脚本：父case的`commands/env018-update-fgvllm.py --mode prepare|install`，SHA `680f0d4c663651ea796782843d8fa47d8145bc132f0cdecd6aaf0d8b6562e4a9`；AST通过（本地py_compile仅因系统pycache不可写失败，未执行脚本或触及远端）。执行前保存/核验脚本SHA，先`python3 <script> --mode prepare`只建立新副本和证据，读取新AGENTS/依赖/导出后才执行install。以上为执行前计划，现已完成，最终结果见本文交付结果与远端FINAL_SUMMARY；无精度gate/性能收益声明。
