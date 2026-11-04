# eng-055：复用PR原件，缩小FP32主补丁

- 授权：用户2026-10-21“那你俩收敛下吧，尽量可以复用原来PR中的内容，减少额外的代码增加”。沿用仅工程代码/CPU验证、不改8010、不访问8035、不推理/重启/提交/推送的边界；无需另起agent或新任务。
- 分类：framework / 工程范围收敛；不是新增性能优化。
- 输入：main a696859b＋PR455 head3cb373b1的冻结baseline，及已验证eng053三文件FP32修复。eng054公共HC dispatch/REFERENCE及GDN signature整理不进入本候选，原件与证据保留不删。
- 本地新副本：`/private/tmp/qwen38-plugin-slim-055.zd1K83/candidate`。
- 远端拟用独立目录：`/mnt/nfs/users/jinghao/qwen3.8-flash/20261015-qwen38-flash-next-ppu07-container/engineering/eng-055-plugin-minimal-fp32-20261021`；先核owner/解析/空间，排他创建，commands先保存再执行。

## 设计与执行门禁

1. 生产源全部逐字复用eng053，保留模型边界FP32、实例MoE shim及原PR中的HC/QSA/PLE调用，不复制算子/新增provider/fallback，也不改共享collective。保留外部env041 i64/randn、QSA M16及051 PLE依赖，不揉入Plugin补丁。
2. 测试补入PR455已有`tests/qwen3_8_flash_next/test_operator_bindings.py`，原delegate/Meta断言保留，依赖改为在各测试内加载以便CPU子集收集。合并toy/native重复guard/truncation测试，保留真实安装native方法、cast-before-reduce、取消误差、错误传播、dtype/stride/alias、幂等/实例隔离和不兼容runner检查。候选中不增加独立TP测试文件。
3. 使用inference-accuracy-evaluation `minimal-regression`的CPU契约子集；禁止GPU初始化/额外推理/服务加载。本轮没有新graph/C1/C8或formal结果；生产源若证实与eng053相同，只引用该原已测生产树的旧证据，不伪称新模型回归。
4. 保存完整/增量diff、原PR复用字节证明、脚本SHA/测试日志、实际服务前后身份/源/token计数。目标lint与apply-check通过才形成交付；父PR自身格式/CI问题仍单列，不通过新无关格式化扩大diff。

## 结果

已完成精简与CPU验证，作为后续主交付替代eng054；**3文件/+242/-10，生产2文件/+66/-3，新测试文件0**。原eng054的12文件/+878/-98整树及535 CPU证据保留，不作为本次主补丁继续叠加。新增行减少约72%，这只是补丁规模，不是性能数字。

### 原PR复用与实际改动

| 文件 | 相对main＋PR455的增量 | 必要性 |
|---|---|---|
| 原`gpu/model.py` | +4/-3 | 只导入helper、安装模型自身MoE实例adapter、两处显式FP32归约调用 |
| 新`gpu/tp_reduction.py` | +62/-0 | 原eng053已测helper逐字复用，保留BF16 cast-before-reduce/native guards和实例幂等，不为减行改成全局patch |
| 原`tests/qwen3_8_flash_next/test_operator_bindings.py` | +176/-7 | 在原文件合并CPU契约；原3个delegate/Meta测试断言AST完全相同，仅将依赖导入移到测试内部 |

**所有非测试文件与eng053逐字相同**。HC public/CachedOp、DEFAULT/REFERENCE、额外融合能力入口和GDN signature整理均未进入本候选；common→GPU原依赖问题留待独立重构，不宣称已解决。未复制FlagGems-vllm数学实现，未引入新backend/配置/框架。相对eng053仅测试两文件变动：原测试文件+176/-7、独立191行TP测试从**新副本**移除，合计+176/-198；原eng053文件与旧快照完整保留，可恢复，不删除用户/线上文件。

测试把toy/native的重复guard/truncation矩阵合并，以安装vLLM原方法作为单一reference，继续覆盖BF16乘前cast、其他dtype输入/返回身份、空行/非对齐/转置、TP/EP/SP/已归约判断、trunc/stride/alias、实例幂等、错误直传和BF16取消误差。没有通过删关键断言压缩行数；原PR的3个device依赖测试仍保留。

### CPU与工程验证

- `checks-001/pytest.log`：**410 passed、3 deselected，2.29秒**。24项cast/dtype/layout/identity、384项真实native方法比较、2组合安装/取消误差/错误测试。原3个device测试未执行，不能称全模块或硬件CI通过。
- torch2.10.0；安装vLLM MoERunner源SHA`d11a841e24f46a14884d36334b83387370cd8232679d8569a6a06eb3a6918eb2`。方法AST原样执行，collective用mock；不构造完整runner，不是TP8归约或GPU数值验证。外置harness只禁用GPU/子进程/网络，不替换Plugin包入口；本次测试直接加载独立helper，没有vendor包初始化。
- CUDA未初始化，blocked operations为空；Ruff check覆盖3改动文件通过，format覆盖测试/helper2文件通过。组合补丁对冻结base、增量补丁对eng053均apply-check通过。
- `accuracy-skill-bundle.json`冻结本地`e2e/accuracy` minimal-regression子集，bundle SHA`6e94a080dd3b64544c535e1fd4bda506f55516374d14d0f8ca6aa148bba2c7b2`。未发新模型请求，因此没有新的模型minimal/formal结果；旧eng053 graph/2C1/8C8仅作为相同生产字节的原历史证据引用，未重标成新测量。
- 首次connectivity在本地沙箱因Ansible RPC启动失败，获工具权限后同一只读Host检查通过；不是PPU或模型故障。inventory与探测范围仅PPU-07。

### 交付与当前绑定

远端工程根目录owner0，创建时可用约6.97TB，排他新目录未覆盖。产物：

- `candidate/`：645文件整树SHA`c505f298e69587fbf0d333dc5cb7b04308e2e814a121e6e97eaab1334b3b63f5`。
- `delivery/combined-fp32-minimal.patch` SHA`9312a08e5454d06a57e2143763072553d52efba70acb06ce8a8002abac6df12e`；`incremental-eng055-vs-eng053.patch` SHA`c0832c124a541e473feadabfbda102ba847fca92df2482cd15f517beaa2bae71`。
- `delivery/manifest.json` SHA`c4f85423765520bdc97b189714e3e7fa4b38448bf7be5f856c2513f3e8722ec7`，含PR原件复用、原3个测试断言保留、非测试字节相同及补丁指纹；`PR_DESCRIPTION.md`为新精简评审草稿。
- `final-audit-001/report.json` SHA`bd65d6cc9e7ffd8559fb3c893326893822360c013063960ebbf22ed88e110417`，645文件及实际在线eng053 `vllm_fl`包337文件逐字比对通过。完整脚本/CPU日志/junit/前后身份与metrics均在此根目录。
- 8010原API2441711/start521315854，argv SHA`c146e2da4762690185e9b3573c5f48796a5cb42aa2037de0d08d9ada40595010`、health200；测试前后身份、完整Python源与prompt/generation token计数相同。

本轮0模型请求、0GPU测试、0重启、无安装/导入路径切换/8035访问/提交推送；i64/randn、QSA M16、PLE、固定调优/黑名单保持。测试归并不需要重启在线服务。`pr_readiness=needs_revision`：原3个device测试/新上游CI未跑，父PR格式/临时CI绕过尚未处理，无新formal gate或性能结论。整体minimal记录仍incomplete（无新服务测量），不伪造新通过；monitor保持PAUSED，等待用户审阅后续方向。
