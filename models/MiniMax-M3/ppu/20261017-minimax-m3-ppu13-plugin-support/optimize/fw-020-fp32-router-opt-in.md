# fw-020：FP32 router 默认关闭，保留显式接入

用户要求不要默认启用fp32_router_gemm，保留原GateLinear和可选接入，只做CPU回归、不影响8011。

## 设计与范围

对PPU-13/minimaxM3私有`/workspace/vllm-plugin-FL`做一个最小选择策略修改：`register_oot_ops`默认选择集合排除`gate_linear`。
不改变OOT_OPS可用算子集合，现有`VLLM_FL_OOT_WHITELIST`或调用方显式`whitelist=["gate_linear"]`仍可选择GateLinearFL；原白/黑名单及全局禁用优先级不变。
默认模型实例化直接保留vLLM GateLinear，不只是让替代层内部fallback；upstream自身native/linear选择行为不修改。
FGV adapter、registry/reference实现、M≤32新分发及M>32 FP32 linear回退继续保留，topk_sigmoid、OAI experts和原激活参数不改。
不新增配置项、thead.yaml修改、Plugin测试文件或第二份容器源码目录；不修改FGV/vLLM/权重，不提交/推送。

## 冻结CPU验证与回退

本地inference-accuracy-evaluation/minimal-regression，仅执行CPU/static/mock子集，完整最小回归仍因无PPU/graph/模型证据为incomplete。
先保存当前custom_ops原件、完整已有diff、版本/安装/8011原生进程与health；补丁只作用于一个已核验文件。
重跑原600项，加测默认注册排除、默认实例类身份/FP32 cast+linear、显式env/调用方白名单、优先级/禁用/重复注册及小/大batch。
CPU CUDA/HIP可见设备为空，逐项断言无GPU初始化；不争抢设备或启动/重启模型。
补丁/命令/外置测试/结果保存在远端router-optin-001-20261019；回退只恢复本项custom_ops原件或逆向单文件patch，保留env004完整归档。

## 状态与边界

首轮629项CPU/static/mock通过，失败/错误/跳过0；原600项完整重跑，加29项默认/显式选择专项。整理接口docstring后按最终文件再次运行同套回归，初轮原始回执保留为`*-first`文件。
无PPU性能证据，不能声称原路径或新算子更快；这里只按用户要求恢复保守默认。正式精度与性能均not_run，旧gate仍仅历史组合。

## 显式启用方式

使用现有`VLLM_FL_OOT_WHITELIST`，在所需OOT项列表中显式包含`gate_linear`；或调用`register_oot_ops(whitelist=["gate_linear"])`。
白名单是整体限制，不是增量追加：若还需要其他OOT替代层，必须同时列入其名称。不新增永久开关，不修改启动脚本替用户启用。
没有显式选择时，即使FGV/全局FlagOS已启用，也不注册GateLinearFL。原vLLM GateLinear自己的native/linear行为保持不变。
容器当前`VLLM_FL_OOT_WHITELIST`未设置，Worker正常入口为无参数`register_oot_ops()`；下次加载默认不会选替代层。

## 最终结果与外部证据

最终含接口注释的单文件版本，629项CPU/static/mock再次全部通过（15.58秒，失败/错误/跳过0）。执行真实Plugin注册逻辑、环境读取函数、vLLM GateLinear/PluggableLayer快照；ReplicatedLinear底层和FGV/device检测由CPU/mock隔离，不代表PPU验证。
默认模式检查类身份仍为upstream GateLinear，输入FP32/BF16、M0/1/32/33/64输出与原FP32 linear完全一致且不调用Plugin router custom op；显式env/调用方选择、优先级、禁用和重复注册仍成立；原有大小batch/graph fake及动态CPU compile、topk和OAI回归保留。
仅`vllm_fl/ops/custom_ops.py`发生变化，FGV及其他Plugin源码逐文件hash、editable路径和包元数据均不变。两仓仍各一份canonical源码，无新增Plugin测试/YAML修改。未提交/推送。
8011本次原生API实例PID/start_ticks前后相同，health200；无停止、重启、模型流量或GPU计算。最小回归整体仍incomplete（PPU/graph/模型not_run），正式精度和性能not_run，不复用旧gate。

以下相对远端router-optin-001-20261019目录：

- `checks/result.json`保存最终状态和检查范围；`checks/before.json`与`checks/service-after.json`保存精确安装/服务证据。
- `final-default-off.patch` SHA256 `6b4bd67535cf1bc6e701bf991ef4e4a8c85344dae4a280ac92e0e0302f280fac`，包含默认选择与docstring的完整可逆delta。
- `checks/plugin-final.patch` SHA256 `65434aa4a6c2d13cac8c003d29335e86f97a7a660ddac27b86e43f00dd799f45`，含原有未提交候选，不是单点贡献或新commit。
- `checks/source-after.json` SHA256 `150a2decb47f3a8e7e1c2aa1dbf75ba95f59166535b7954b68493a1d7534dd16`；目标文件最终SHA256 `f0bada37ea717be7d1706d1c87583c91f448edc9515be945e30f15ef8bc74f41`。
- `checks/cpu.xml` SHA256 `15386a8869862a33f5e40bf13284e31d4a98ff82c9ca77f2b53312ce21b7a8f9`；`logs/cpu.log` SHA256 `3eb48b008d313a368b8c4de0e1a8c8991ff239692346f0ec92997cbbec066ce4`。
- `commands/test_default_off_cpu.py` SHA256 `663d690e64baaa5dfdda83647ab2295abb115bb8d2a2608d599d2bdc7a745e0b`；原600项脚本仍引用旧外部证据路径，不在Plugin新增test。
- `backup/custom_ops.py` SHA256 `3f14127131b67ab83964eb5ae54e3400ca961c0b385d78184f401b3023c3dcab`，保留完整原件；`backup/plugin-before.patch`保留修改前组合diff。

回退可在核对本任务服务空闲、目标文件未被后续编辑后，逆向应用`final-default-off.patch`或恢复`backup/custom_ops.py`，不影响其他未提交改动；env-004完整归档仍保留。本轮未回退。
补充docstring的初稿patch曾因缺少尾部上下文在`git apply --check`失败，没有修改源码或CPU结果；修正后最终重跑。首轮629项及最终629项回执均保留，不将工具检查失败描述为数值或模型精度失败。
