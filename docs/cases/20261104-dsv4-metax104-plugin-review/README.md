# DeepSeek-V4-Flash / mx-104 Plugin规范审查

2026-11-06 23:09BJT最新源码交付：[refactor-010](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/refactor-010.md)完成整改容器Plugin/FGV/FG全适配审查与27路径收敛，删除3过渡模块、保留不等价的BF16/INT8/packed/workspace契约。前后162CPU、8,444普通源码+4链接/HEAD/index独立审计通过；暂存区统一，无commit/push或服务动作。当前18001仍无服务，GPU数值/真实dispatch/graph/model待验证。ref008/ref009与更早运行证据只作历史，不能绑定这版。


2026-11-06最新配置：[refactor-009](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/refactor-009.md)仅MetaX DeepSeek-V4 INT8且未显式splitting_ops时复用原生默认边界并加入FL；启动脚本3字段JSON，16CPU与配置投影等效检查、642文件/HEAD/index审计通过。已更新安装源码和脚本，不重启、不提交推送；既有离线状态保持。无新GPU/graph/精度性能结论。

2026-11-06最新交付：[refactor-008](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/refactor-008.md)已按用户明确要求直接应用实际FGV/Plugin18路径，完整SHA及安装源码52CPU通过；GPU/真实dispatch/graph待验证。本轮应用前18001已无API/不可达，保持该状态，不自动启动。旧ref007/隔离阶段记录保留为历史。

2026-11-06最新候选：[refactor-008](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/refactor-008.md)继续统一MQA/MLA公开契约，4临时名→1新语义族+2已有API，52CPU与源码不变审计通过；未安装，GPU/真实dispatch/graph待验证，同运行服务不变。下段ref007仍为当前已交付版本。

2026-11-06 18:33BJT最新：[refactor-007接口收敛交付](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/refactor-007.md)复用主线公开接口，新增公开ID从8收敛到4，MetaX核保留后端。123项原生算子/真实dispatch/graph（0失败/跳过）、prefixON22minimal及原prefixOFF22runtime、两实例7FULLcapture通过；18路径限定更新、完整文件指纹/实例独立复核，恢复opt2/18001/OFF/.85原argv/env，启动脚本不变。无新GPQA/性能、无提交推送，旧分数/gate不代表本候选。此前op004完整精度属于以下历史版本。

2026-11-06当前：[op-004修复与完整精度](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/op-004.md)在main025复用候选上修复packed gather scale乘法int32溢出及31/63边界搜索。旧5/15失败→新18/18GPU数值graph+5CachedOp通过；用户重启后22minimal/7FULL及C64 prefixON GPQA160/198=80.8081%、MATH500477/500=95.4%全部完整原生/身份复核。GPQA达80%但低于用户85.35参考，不声称精度提升；本次698题无OOM/非法访存。整改容器18001保留服务，未提交推送、无新E2E收益。

可复用机制：packed跨层KV stride不能沿用小contiguous测试的32位地址假设；应在乘法前拓宽block ID，并覆盖高物理块ID与batch=2^k-1。以合法guard-storage复现旧地址回绕、FP8bytes/FP32scale exact reference、变化输入graph验证，避免故意再次非法访问。实际planner复算不冒充故障时tensor采样，prefix命中不是该缺陷必要条件。机制证据限本候选/MetaX；暂不据此扩大通用SOP阈值或宣称其他平台正确性。

2026-11-05更新：[op-003整改与验证](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/op-003.md)已将真实MoE clamped SiLU经Plugin dispatch接入FGV公开融合out，修复必要的负零/共享workspace契约；CPU12、GPU115+9、16capture/32新输入replay及模型7FULLcapture+22minimal通过。整改容器已更新并在18001按原参数恢复，prefixOFF/.85；原服务容器未改。没有新GPQA或性能收益结论，旧C20测试不代表新源码验收。以下为初始审查历史。

2026-11-04；按用户要求检查当前已优化容器，主要结论为公共算子策略应由框架平台配置控制，模型初始化不得按模型名覆盖公共dispatch。用户最新要求已切换到默认metax.yaml自动加载，当前模型服务未重启，新配置下次启动加载。

[逐文件报告与整改清单](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/review-001.md) · [结构化状态](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/state.yml)

源容器deepseekV4-flash，Plugin HEAD a696859b，vLLM0.24.0+empty，MetaX TP8。用户远程目录/public-flash/jinghao/deepseekV4，证据根其下20261104-dsv4-metax104-plugin-review。初始34修改/新增文件、28生产Python逐职责审查；14个数值Triton kernel仍应迁算子库。统一dispatch/公开API、workspace归属、注册回滚及量化支持矩阵存在待整改项。

本次三生产配置文件和一测试文件整理；最新公共策略置于Plugin默认dispatch/config/metax.yaml顶层，启动脚本VLLM_FL_CONFIG已移除，旧外部YAML归档至delivery04/backup。此前43项CPU测试通过；默认加载新候选44passed/0skip、未初始化CUDA，新增测试Ruff0.14通过。全部现有28生产文件Ruff显式扫描102既有问题、无新增诊断，完整pre-commit未执行。服务前后精确同实例/argv/health200，其他源码及Git HEAD/index未变。无新GPU、graph、GPQA或E2E数据，不签发新gate；现有完整补丁仍needs_revision。

可复用边界：配置返回值测试不足以证明实际读取者生效；应验证真实PolicyManager、FlagOS/OOT getter及模型initialize之后的策略身份。blacklist也不能被声称可拦截绕过dispatch的显式私有算子调用。本案例为code/config review，不恢复mx-103暂停的OOM任务。

2026-11-12 单算子SDK追平探索继续于 op006/007/008。独立私有测试副本；原服务/安装源未动。快速TLE原型通过集合数值/graph和微基准，却被仓库重复输入稳定顺序测试拦截，完整保留并冻结模型；正复用原canonical数学以共享scratch修复，不把旧原型微基准称可交付或E2E收益。详见[op-006](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/op-006.md)、[op-008](../../../models/DeepSeek-V4-Flash-W8A8/metax/20261104-dsv4-metax104-plugin-review/optimize/op-008.md)。
