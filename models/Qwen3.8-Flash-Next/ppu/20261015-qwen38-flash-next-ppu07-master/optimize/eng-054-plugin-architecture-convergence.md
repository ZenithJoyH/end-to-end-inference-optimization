# eng-054：Plugin复用边界与真实MoE契约收敛

- 授权：用户2026-10-21“那你进行调整吧”，落实eng053整体review；不提交推送，不更改/重启在线8010，不访问8035，不发推理或GPU测试。
- 分类：framework / 工程边界整理；不是新性能优化或已验证模型候选。
- 父候选：eng053独立三文件FP32树，main a696859b＋PR455 3cb373b1；已完成10请求最小回归的运行树保持不动。
- 本地新副本：`/private/tmp/qwen38-plugin-converge-054.i7JDrL/candidate`。远端新工程目录计划`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-054-plugin-architecture-convergence-20261021`，先检查/排他创建，commands与测试原件外置。

## 设计归属与冻结范围

1. FP32 helper和模型归约调用数学不变，保留实例级shim，避免为runner_cls注入复制上游构造器或改全局collective。增加以已安装vLLM真实native方法为reference、mock collective的CPU契约，不再只用toy Runner互相印证。
2. 将HC的无状态纯数值接口接入现有CachedOp/registry、FlagGems-vllm DEFAULT及PyTorch REFERENCE，实现延迟公共符号查找。复用已有能力工具，不造新策略/缓存框架；model custom-op fake/opaque ABI不变，common不再反向导入gpu leaf。
3. QSA/PLE cache、索引、request映射和状态更新事务继续留模型/原算子库，本轮不拆成可失败后重放的独立fallback调用。i64/randn/QSA M16/PLE修复依赖及非目标模型/全局collective默认行为不改。
4. GDN构造局部复用同一次signature检测，更新独立PR说明的部署/回退/验证信息；不得沿用eng053模型回归充当新树通过。

## 验证契约

按inference-accuracy-evaluation minimal-regression，仅执行CPU合同子集：真实native MoE各guard/dtype/truncation/stride/alias，HC reference与现有库数值、registry/policy/可选依赖隔离/metadata fake/构造依赖方向；目标仓库lint/format/patch检查。使用新独立路径与CUDA_VISIBLE_DEVICES空，保留脚本SHA/日志/结果，任何GPU初始化或线上源漂移立即停止。

本轮不授权新服务加载，故新树模型graph capture/2replay/C1/C8与formal GPQA均not_run，整体minimal结果保持incomplete；CPU通过只证明工程/CPU覆盖。性能not_run，无speedup/gate。原eng053运行源/实例及已测结果保留，监控仍暂停。

## 结果

已完成独立源码调整与CPU验证，**535 passed / 0 failed，2.80秒**；新候选未加载，`pr_readiness=needs_revision`。

### 实际代码与设计边界

- `vllm_fl/ops/hyperconnection.py`保留四个原opaque custom-op ABI/fake，委托现有CachedOp；原`gpu/ops/hyperconnection.py`仅兼容导出，`common`不再导入GPU目录。
- DEFAULT实现位于`dispatch/backends/flaggems/impl/hyperconnection.py`，四个数值符号延迟查找公共FlagGems-vllm导出；仅融合能力检查仍使用原库的support predicate。PyTorch REFERENCE位于相邻reference backend。复用已有allow/blacklist、policy epoch、strict/fallback；禁用融合数值入口也禁用其DEFAULT能力入口，不增加全局开关/设备探测/缓存框架。
- REFERENCE保留FP32分组归约、ordered gate accumulation及combine先回到residual dtype再norm的边界；融合能力返回false，common继续原分离调度。仅这些不写输入/状态的HC调用允许既有fallback；不搬动QSA/PLE事务。
- FP32 helper字节与eng053完全相同，实例级MoE shim未改；模型内只去重一次GDN signature检测。不为替换实例shim而复制未透传runner_cls的上游构造器，不改全局collective。
- 相对eng053增量11文件/+622/-96（含测试和代码移动）；相对main＋PR455组合12文件/+878/-98。行数不是性能收益，未改kernel或调参。

### 验证结果与局限

| 范围 | 实际结果 | 证据性质/边界 |
|---|---|---|
| 原FP32合约 | 53 passed | CPU tensor＋mock collective |
| 安装vLLM真实MoERunner方法 | 384 passed | 原方法AST原样执行；SP/TP/EP/reduced/dtype/trunc/stride/alias，不构造完整runner，不证明多卡归约 |
| HC数值/dispatch/strict/fallback/Meta/common导入 | 65 passed | CPU真实torch和dispatch，vendor provider合约用mock，不代表硬件命中 |
| 复用已有CachedOp/registry/types | 33 passed | 原测试未改；不另造测试框架 |
| 工程检查 | 11增量文件Ruff check通过，6新格式文件format通过；两补丁apply-check通过 | 既有父PR格式/临时CI绕过不在本次修正范围 |
| 新候选包启动、accelerator数值/命中、graph/两次replay/C1/C8、formal、性能 | not_run | 新候选总体minimal=incomplete，不能继承eng053模型通过或旧acc017 gate |

外置CPU harness跳过有硬件初始化副作用的package入口/平台发现，并以空配置、CPU dispatch key替代；**真实dispatch core、HC provider/public/common及安装vLLM的custom-op注册方法AST均执行**。torch2.10.0，CUDA未初始化，无被拒绝的GPU/子进程/网络尝试。不是生产package可导入性或实际8rank函数命中的证明。原完整operator-bindings模块含设备依赖未跑，HC Meta由新CPU合约覆盖。

初轮`checks-001`497 passed/5 failed为隔离平台缺vendor字段；002为policy设置返回旧值时仍读取环境及错误使用primary选择当fallback执行证据；003剩fallback断言。均为测试工具/断言问题，旧证据保留；未改dispatch实现绕过失败。004原502全通过，005复用33项旧测试后535全通过。仅CPU复测，无模型事故/推理重试。

### 交付、绑定与回退

远端工程根目录按原计划创建，实际owner0、可用空间约6.97TB；无覆盖旧证据。最终独立源`candidate-v004/`，旧candidate/v002/v003保留。

- `delivery/incremental-eng054.patch`、`delivery/combined-fp32-hc.patch`、`delivery/manifest.json`及`PR_DESCRIPTION.md`；前者应用eng053，后者应用main a696859b＋PR455 3cb373b1，均未提交/推送。
- 源树650文件指纹`5ded64a8565dd28c7a6cdf49efab41a6431900fdae8c3f252c8f61ae69a9b72d`，远端逐份核对与本地交付一致。
- `checks-005/pytest.log`、`junit.xml`、`cpu-summary.json`（SHA`8a855707db4c6b144687179aae256b2a51b7145c07b4ec8412bcf76b979f4a0b`）；脚本保存在`commands/`，不进入Plugin补丁。
- `final-audit-001/report.json` SHA`6142089ec2c92187462dc4897e9a1841930aa9783284a42957c14bf828f79622`；manifest保留测试/脚本/交付指纹。初次mac tar的AppleDouble/xattr元数据告警不属源码，清单明确排除`._*`；后续传输禁用该元数据，未删除旧文件。
- 只读绑定8010 API2441711/start521315854，argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`、health200；各轮前后线上eng053完整Python源、身份和prompt/generation token计数不变。

本轮0模型请求、0GPU测试、0重启、0次8035访问、无安装/PYTHONPATH切换。保留FP32、env041 i64/randn、QSA M16、051 PLE及固定调优/黑名单。当前回退即不部署此候选；线上eng053及旧回执不变。下一步需用户另行授权新候选加载，验证实际backend/graph/2C1/8C8；未获授权前不重启、不扩大、不自动全量评测。

## 后续代码量复审：建议缩小主补丁，不继续堆叠抽象

用户2026-10-21询问是否仍能收敛。本段只读比较本地冻结源码和补丁，未修改任何Plugin候选、未连接远端或执行测试，也未提交/推送。

结论：可以明显缩小。eng054把精度修复的PR扩大为HC分层和fallback建设，虽然沿用了既有dispatch，但当前目标没有必须同时引入新HC REFERENCE数学实现和可选依赖fallback的证据。对主补丁而言，这扩大了审查面及需要重验的行为，不是FP32修复的必要依赖。

- 当前组合：12文件/+878/-98；生产9文件/+378/-96，另3个测试文件。
- 推荐主补丁：恢复eng053的model.py与62行TP helper，仅保留eng054增强后的真实native契约测试。**只读虚拟diff为3文件/+335/-3，生产2文件/+66/-3**；该数字保留现有269行测试、不假设后续压缩，尚未形成或验证新的候选。
- HC公共入口、DEFAULT/REFERENCE实现、能力选择、GPU兼容导出及相关HC测试从主补丁整体移出，原eng054证据保留，不删除旧材料；如确有多backend调用需求，再作为独立重构评审和验证。common→GPU依赖问题仍记录为待独立处理，不能因拆出而宣称已解决。
- GDN signature去重与FP32修复无关，从本次主补丁去掉，避免顺带整理。
- 测试仍可将旧toy Runner的guard/truncation矩阵（当前80–118行）与真实native方法契约（195–269行）合并，避免重复维护；保留cast-before-reduce、取消误差反例、异常直传、实例隔离/幂等、dtype/stride/alias及截断语义。不以减少参数组合数或535计数为代码量目标；进一步行数需实现后实算。
- 62行实例级MoE shim不为减少行数改成全局collective/class monkey patch，也不复制完整上游构造器。i64/QSA M16/PLE仍为外部已保留依赖，不揉进Plugin补丁。

上述是范围收敛建议，不是已完成的新改动；535 CPU结果仍只绑定原eng054树，不能沿用来认证尚未生成的精简树。当前线上eng053不动，后续实现及新验证等待用户方向。
