# op-001-moe-public-api：完整 MoE 使用 Gems 公共入口

- 状态：superseded（后续共享调用整理已应用，详见op-002）；分类：operator/replace；场景：P4K/D1K/C64/N128；阶段：Prefill/Decode/Mixed。
- 本次范围是用户明确要求的代码整理，不启动端到端性能优化，不修改服务启动配置或重启服务。

## 优化方向与瓶颈依据

当前 Plugin 直接导入 FlagGems-vllm 的 `_metax` 私有模块，自行选择完整 MoE/workspace wrapper。公共 `flaggems_vllm.fused_experts_impl` 已绑定 MetaX 实现，且支持 out/workspace ABI；改成公共调用以保持平台分发与 shape 特化归属库侧。没有声称此整理会提高端到端吞吐。

## 优化内容与适用边界

保留既有无LoRA、MetaX、无expert_map、FP16/BF16同dtype、SiLU、非FP8/W8A16/W4A16边界；W8A8仍由上层专用路径处理。公共函数缺失时保留 staged fallback；公共workspace支持检查通过时复用output并交换两块modular workspace的角色；旧库没有workspace能力或buffer不支持时调用公共函数并copy结果。已选中实现执行失败直接抛出，不捕获后重试。

保持其他平台、LoRA、量化与非目标输入的原路径；当前MetaX特化实现和Gems源码不修改。功能测试的命中计数从私有wrapper迁到公共入口，并新增路由/兼容回归。

## 正确性与路径命中

执行前公共API探针确认 `vendor_name=metax`，函数module为MetaX fused_moe，signature含out/workspace13/workspace2；supports检查也公开。

实际结果：

| 验证 | 结果 | 结论边界 |
|---|---|---|
| Plugin公共入口路由测试+现有MoE adapter契约 | 26 passed | CPU/mock：output/workspace身份、参数传递、旧ABI、missing API、错误不重试、LoRA/量化/activation/dtype/expert-map/non-MetaX边界 |
| FlagGems-vllm现有modular workspace output alias测试 | 2 passed | 空闲C550设备4；BF16小形状，包含graph capture和两次replay、output与modular workspace别名 |
| Plugin现有functional MoE测试的hidden128子集 | 4 passed，8 deselected | 同一设备4；FP16完整公共入口与BF16 expert-map staged路径；各含非graph/graph两种，数值与实际命中检查 |
| 目标源码及功能测试git diff --check | passed | 保留全部既有工作区改动 |
| Ruff | unavailable | 目标环境和本地均未安装，未声称通过lint/format |

设备6/7上当前模型服务未重启、不承载本次测试；设备4预检为空闲且剩余显存充足。本次graph通过只属于算子测试，不等于完整TP2服务graph/模型精度通过。服务级最小回归及正式精度未运行，不签发gate。

## 性能效果

baseline/candidate/revert均not_run；没有可比性能数据或收益百分比。保留workspace路径避免因公共API整理而引入新的输出copy与中间buffer分配。

## 决定、风险与回退

当前目标源码位于容器私有/workspace，既有工作区修改全部保留。用户本轮明确授权修改源容器，作为本次代码整理的例外；不扩大到共享挂载、其他容器或服务重启。应用前校验SHA，回退只恢复本次三个目标文件的准确旧副本。

代码保留，所有已执行回归通过。运行服务继续使用其已加载函数，新代码在下次服务启动时加载；未自动重启或发送模型压测流量。`pr_readiness=needs_revision`，完整服务回归、Qwen目标全形状覆盖、多平台硬件与工程lint仍未测，不创建PR、不提交/推送。

## 外部证据

本地外部目录 `/private/tmp/qwen36-moe-public-api-20261013` 保存旧源码、候选、精确补丁、执行命令与测试输出。远端未指定新的产物工作目录，不创建共享任务根目录。Plugin原始文件SHA：`5bb687951274c01d69b41391898cfc3a9991d0afb1a2d643fff6545af1b56532`。

修改后源码SHA：`4466f9b6811a363951a2603a0629fbf3748f9201b9127c8db9a6f66e88cc3dda`。本次完整patch SHA：`9e609ea6a7e23705a3d0c99fc30fdd1058149f3f1b6c53522663baf29e716c46`。证据清单为外部目录 `evidence-manifest.json`，原始测试日志为 `unit.log`、`gpu_alias.log`、`gpu_small.log`。

回退入口为同目录 `rollback_remote.py`（未执行）。它先检查三个文件仍为本次应用后的SHA，再恢复两个既有文件的旧副本并删除本次新建的单元测试；后续文件有变化时拒绝覆盖。外部材料在本地临时目录，若需要长期交付应移入用户指定的持久外部产物目录。

后续用户要求统一NV/MetaX调用层，已由[op-002共享调用](op-002-moe-unified-call.md)接替。本文保留op-001当时的验证与源码身份，不将新结果追认到旧候选。
