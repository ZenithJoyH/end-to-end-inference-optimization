# interface-fix-003：Plugin收敛与算子接口兼容修复

2026-11-06，用户要求实施[接口审查](../../../../../docs/cases/20261105-bge-m3-mx59-serve-cleanup/plugin-interface-audit.md)，并明确要求直接应用到 BGE-M3 容器实际安装源码。目标为 mx-59 / BGE-M3 的三个私有 editable 仓库；沿用已验证独立容器 `bge-m3-1k-current-20261105-x4jxof0i` 先验证，再更新源容器文件。不重启在线服务，不提交或推送，不修改 vLLM、权重、编译器、调优配置或数值 kernel。

## 冻结契约与执行边界

| 项目真相 | 本轮约定 |
|---|---|
| Plugin | 删除单次转发函数，保留 call_once/dispatch/hooks/错误不重试；provider用q/k/v，既有位置调用仍有效 |
| FG | MetaX Linear补与原通用/NV同文案的K维度执行前RuntimeError；有效输入不改变计算 |
| FGV | public flash_attn_varlen_func与官方vLLM0.24.0的34参数顺序/默认值对齐；4个FA4参数默认None可用，非None在任何dispatch/copy/launch前NotImplementedError |
| 支持边界 | 不新增FA4、NV FP32或训练能力；既有dtype/shape/out/LSE/空序列/unsupported路径保留 |
| ABI | Python公开调用采用明确vLLM0.24契约；审计已有调用，内部vendor与C-extension仍按各自旧ABI映射。未知外部调用若使用旧第25项之后位置顺序，必须迁移为关键词，不猜测参数含义 |
| 数值/调优 | 原kernel、配置、精度oracle和容差冻结；无torch compute fallback，沿用既有tuner，无新autotune配置 |
| 验证 | Plugin全BGE+dispatch+Worker相关项；FG原测试与K错误/正例；FGV原FP32/swap测试、新34参数/零launch/ABI/None数值测试，优化解释器错误路径；实际pre-commit |
| 模型回归 | GPU3、FP16/FP32、native/C8及8种joint输出；两侧max_num_seqs1/maxlen128/MBT256，原atol1e-5/rtol1e-4；先新baseline再candidate，保留全部结果 |
| 性能/正式精度 | 本轮接口维护无性能结论；未调整kernel/调优，不用单测或有限模型请求代替正式验收 |
| 超时 | 单组pytest600s；临时服务readiness240s、每请求120s；错误即停止，保留失败回执 |

新增参数的unsupported检查位于公开函数最前；其余early/fast/general/vendor/C-extension路径保留原实现。FG新增校验只读metadata，在tuner、Parameter转换、contiguous与launch之前；Plugin删除冗余包装但保持执行入口。相关标准为Plugin A1/B1/B4/C1/D2/F1–F5、算子A1–A4/B1/B3/C1–C7/D1/E1–E3/F3–F6；本轮无数值或graph执行改动，不新增graph支持声明。

远端证据根计划为 `/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/interface-fix-003-20261106`，只新建且不覆盖。执行前保存commands、三库旧patch/指纹、逐文件原文/属性与回退方法；部署核验HEAD、完整旧patch及每个文件SHA，拒绝漂移。源码目录不在共享mount内，必须在当前inspect中再次核验。

最终状态：已发布到BGE-M3实际安装源码并完成验证。准备过程与首次失败保留如下；最终结果见文末。

预检已通过：三库源码/安装与前次交付一致，源/候选私有源码不在共享挂载内，挂载相同、来源镜像632f…正确；GPU3空闲、源health200。准备脚本保存于父案例commands/interface-fix-003-prepare.py，本轮commands/prepare.py保存执行副本，PREPARED.json保存门禁结果。

修改前功能回归执行入口：`docker exec bge-m3-1k-current-20261105-x4jxof0i /flagos/bin/python <evidence_root>/commands/functional.py baseline`。仅在GPU3启动本轮拥有的临时服务，脚本finally停止自身进程组；原服务不受影响。candidate复用同一脚本及契约，与本轮baseline逐项对照。

修改前FP16/FP32、C8、全部8种joint已完成，临时服务均退出。最终候选9个文件（Plugin4、FG2、FGV3）；FGV附带修正1处原benchmark参考调用的fa_version位置误绑为关键词，未跑性能测试。三库完整diff适用pre-commit通过（30/3/8文件），未自动改文件。

冻结payload SHA256 `033a809297960a43900f9a48c18c1b9d17850ddf0c8dcd83015aad96defff160`；控制包 `7bdd18f20fabad5f8402e6e983fd4ba7354cb3d93f004b6f58e9ba07ba65b612`。执行副本commands/deploy.py SHA `ae86cfc417f5dd62375934eb0276f0e6af513411ec278f55eeb1319601704914`，commands/validate.sh SHA `fade8aa6bfcd0cc8c393b59a93d950c0cbcc0d62c825d5ee02e8aab8a4ff3a4a`。先执行隔离容器 `python <evidence_root>/commands/deploy.py candidate candidate-001`，备份9项原文/权限/三库index并逐文件SHA核验后替换；随后同容器执行 `bash <evidence_root>/commands/validate.sh`。任何验证失败均保留原生回执，不能发布源容器。

源容器最终发布使用相同manifest，入口 `docker exec BGE-M3 /flagos/bin/python <evidence_root>/commands/deploy.py source source-001`。工具要求TEST_VALIDATION.json通过且绑定同一payload，在三库旧patch/HEAD/逐文件SHA仍一致时才写入；保留源在线进程，不改安装绑定。

执行前复核发现原pytest terminal hook在collect-only也会写accuracy_result.json，因此实际执行改为commands/validate-v2.sh（SHA 765429aa86c5944380eb8102c6e66e7f874a505c1c78b32815e1032453e8550c），仅补collect-only原生输出路径，避免测试产物污染源码树；原validate.sh未执行，保留备查。

候选部署完成：Plugin完整patch `dafb78f8e8f3f5d4c0c2822a82aa370a8632f53b391d20e79716c64b394aae08`（30/+1550/-3，运行时425行）；FG `4fac55ee15de2195dd42c3e331d55bf84cec7ff0ded2f22d7cb8de795418fb16`（3/+236/-1）；FGV `835eeb9a46101b40120a862fa521bdc25fde7c230c4496268937d6561ef258e4`（8/+769/-16）。Plugin总diff因补测试增加11行，运行时代码实际减少6行；不把测试增加隐去。

发布门禁工具commands/gate.py SHA `b7de31dadc4cd943a4ff8ae2eedbf7a81d7f6b53c8c80959cfe1d29a0f26ec32`，要求四组JUnit零fail/error/skip、确切测试数量、三库pre-commit通过、127060项功能对照通过，并绑定当前候选patch与payload后生成TEST_VALIDATION.json。回退工具commands/rollback.py SHA `4633d64ef30160d866705a2759e2c6c5be46cef0f3aa06456a48cedb405a355a` 已语法检查，未执行；仅在无后续源码/index漂移时恢复9项原文件，不重启服务。

首轮FGV验证149 passed/6 failed/432 deselected（58.31s），后续组按set-e未执行。6项失败均在测试import官方NV子模块：MetaX运行时将vllm.vllm_flash_attn替换为非package模块，非数值回归。保留全部断言，改为读取实际安装官方flash_attn_interface.py的AST构建参考Signature；生产代码不再改。首轮结果移入results/attempt1保留，候选二次部署仅更新这一测试文件并记录candidate-002；后续重跑完整已冻结验证集合，不删除失败项或放宽容差。

第二版payload SHA 8ee78d3943611e3e56d390476a1a2f5c8d2b23f50a578522fb7c8bc7244370f1，commands/manifest-v2.json与payload-v2.tar.gz冻结最终9项；commands/refine.py只调整候选FGV测试，三库pre-commit再次通过。发布与门禁/回退改用deploy-v2.py、gate-v2.py、rollback-v2.py，均核验v2 manifest，保留第一版材料。候选回退从candidate-001原文恢复，candidate-002仅记录测试修正及最终patch。

最终封存入口commands/finalize.py（SHA 8baa52a3c6b3378a401cae9a995cc8848c0fbd1767a08888331c1e3c05dd0908）在源发布后核对：源/候选三库完全一致、除manifest9项外源码不变、数值kernel AST不变、安装/模型配置/源服务身份不变、GPU3释放；仅写回报告、校验和、小型交付包。

## 最终结果

已直接应用到 `BGE-M3:/workspace/bge-m3/tune-src/` 三套实际安装源码，未重装、重启、提交或推送。源文件与测试候选逐项相同，除9项manifest文件外代码和数值kernel AST未变，安装/模型配置/源服务身份保持。GPU3已释放。

| 仓库 | 完整diff | 最终patch SHA256 |
|---|---|---|
| vllm-plugin-FL | 30 files changed, 1550 insertions(+), 3 deletions(-) | `dafb78f8e8f3f5d4c0c2822a82aa370a8632f53b391d20e79716c64b394aae08` |
| FlagGems | 3 files changed, 236 insertions(+), 1 deletion(-) | `4fac55ee15de2195dd42c3e331d55bf84cec7ff0ded2f22d7cb8de795418fb16` |
| FlagGems-vllm | 8 files changed, 807 insertions(+), 16 deletions(-) | `148c4b6c3ce46b55fe595b05524501fb20000849a5d79d7c52c23a2cdb1145ff` |

Plugin运行时新增行431→425；完整diff增加的测试保留。FGV公开34参数名称/顺序/默认值与官方vLLM0.24一致，4个新参数None通过原计算，非None执行前显式拒绝；内部ABI保持。旧外部尾部位置调用应迁移为关键词或新NV顺序，未承诺未知旧位置调用兼容。

最终验证：FGV155、优化解释器82、FG36（含原graph capture和两次新输入replay）、Plugin364，共637 passed，零fail/error/skip；三库完整diff的pre-commit通过。FP16/FP32、C8、8种joint共127060数值对照max_abs=0.0，阈值未变。首轮6项测试参考导入失败留在results/attempt1，未删除用例。NV/Hygon/THead转发测试为mock证据，不是硬件验证。

证据根：`/public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/interface-fix-003-20261106`。`FINAL_REPORT.json`、`TEST_VALIDATION.json`、`SHA256SUMS.json`及`delivery.tar.gz`已封存；原文件在source-001。必要回退入口为 `docker exec BGE-M3 /flagos/bin/python /public-flash/jinghao/BGEM3/test/perf_test/benchmark_results/bge-m3/20261105-bge-m3-mx59-base-1k.x4jxof0i/interface-fix-003-20261106/commands/rollback-v2.py source-001`，带当前patch/逐文件/index漂移检查，未执行。

本地交付包 `/tmp/bgem3-interface-20261106-delivery.tar.gz`，SHA256 `dc80a59f002c35de48095b349eb1a44b86538c82a64346688f274157e0fee9df`。非正式模型精度或性能验收，配套公开依赖未固定，PR仍experimental。

## 2026-11-09 FlagGems-vllm 完整 diff PR 复审

本次按用户要求只读 review，没有修改目标源码、重启服务或运行设备测试，先前停止的性能实验继续保持停止。审查对象为 mx-59 / BGE-M3，实际 editable 导入路径 `/workspace/bge-m3/tune-src/FlagGems-vllm/src/flaggems_vllm/__init__.py`，包版本 0.3.0.dev1，vLLM 0.24.0+empty。HEAD `7417158440a80753fb21dab3a124c1be388ab7eb`；完整 diff 8 files/+807/-16，patch SHA `148c4b6c3ce46b55fe595b05524501fb20000849a5d79d7c52c23a2cdb1145ff`，与 11 月 6 日交付相同。新增行约 561 行为测试、49 行为 benchmark，其余约 197 行为运行时代码；不把测试规模当作冗余实现。

结论：计算归属、既有 kernel 复用、MetaX 限域和 NVIDIA/vLLM0.24 公开签名对齐合理；完整补丁仍为 **needs_revision**，以下问题应在 PR 前修复。此前 637 项通过只对应记录中的具体验证集合，不等于下面这些未覆盖场景已通过。

### FGV-R1 / P2：FP32 执行前校验位于布局复制之后

位置：`src/flaggems_vllm/ops/flash_api.py:310`（新 FP32 限制检查），调用顺序见 `src/flaggems_vllm/ops/attention.py:1523`，复制实现见 `_metax/ops/flash_attention/common.py:309`。

触发：FP32 Q/K/V 最后一维非连续，同时传入 causal=True、ALiBi、softcap、非法 K/V dtype 或不支持的 head dimension。公开入口先调用 `ensure_last_dim_contiguous`，它实际分配并 launch copy kernel，然后才进入 `mha_varlan_fwd` 拒绝输入。因此这些输入不满足“任何 copy/launch 前检查能力”的要求；部分非法输入还可能先遇到布局处理错误。现有 unsupported 测试使用 dense 输入，invalid metadata 测试只拦截 attention launch，不能证明没有更早的 copy launch。

建议：将 FP32 能力/metadata 校验提到公开入口的布局准备之前，复用单一校验函数避免两层重复；增加 `last_stride + unsupported/invalid` 的组合测试，同时监控复制和 attention launch，并断言 out 不变。依据：算子 C1、D1、E2。属于执行次序问题，不据此宣称当前合法 BGE 输入结果错误。

### FGV-R2 / P2：通用接口测试无条件依赖已安装的 vLLM 源码

位置：`tests/test_flash_attn_varlen_func.py:779–829`，以及 :910 的 ABI 测试调用。

`_vllm_varlen_signature()` 直接 import vllm 并读取固定路径、AST 顶层常量和函数签名；`pyproject.toml` 的库依赖和 test extras 均未声明 vLLM。没有安装 vLLM 的算子测试环境会新增 ModuleNotFoundError；安装不同 vLLM 版本或源码布局变化时，原本固定为 0.24 的接口契约也会跟随本机安装漂移。本地提取并执行该原始 helper，在无 vLLM 环境已复现 ModuleNotFoundError。本容器恰有 0.24 只能证明这一环境适用。

建议：基础签名/ABI 单测使用注明来源版本的固定契约；对真实 vLLM 源码的比较另作为声明依赖与版本范围的集成检查。不要让缺少可选依赖跳过基础 ABI 检查。依据：算子 F3、E2。

### FGV-R3 / P2：测试污染全局随机数状态

位置：`tests/test_flash_attn_varlen_func.py:422–437`。

`_metax_fp32_inputs()` 每次 `torch.manual_seed(1234)` 会重置全局 CPU/设备 RNG；多数调用方未使用 fork_rng，conftest 也没有恢复。只有 invalid_metadata 一组有局部保护，不能保护其余 reference、long_encoder、half_regression、selected_context 等测试，导致后续用例的输入受测试顺序影响。

建议：使用设备匹配的局部 Generator 并传给 randn，或用覆盖相关 RNG 的 fixture/context 保存和恢复状态。依据：算子 E6。

### 其他交付缺口和收敛建议

- 算子 E3：:633 的 `test_metax_fp32_context_policy` 与 :700 的 `test_metax_fp32_long_preserves_other_native_profiles` 缺 `flash_attn_varlen_func` marker，按算子 marker 运行会漏掉共 13 个参数用例。应补 marker，无需删测试。
- 算子 F1/F2：现有 FP32 benchmark 只测三组长度、16 heads、D64，对比手写 torch reference；它能提供功能路径计时，但没有比较改动前 direct 配置，不能单独证明 128/1024 调参阈值、两阶段 long 配置及 D128/D256 资源限制的性能效果。PR 应绑定同条件原配置/新配置数据，覆盖阈值两侧、长上下文、代表性 batch/head 和未优化路径，披露回退；未补齐前不把配置选择描述为普适性能提升。
- 算子 E6：输入覆盖正负随机值和空序列，但缺少 NaN/Inf 数值边界；填充 NaN 输出哨兵不能替代 NaN/Inf 输入测试。应按实际支持契约补测或说明限制。
- 接口对齐修改了尾部位置参数顺序，已有内部 vendor/C-extension 映射保持，当前已审计调用无新增误绑证据；PR 仍应明确 vLLM0.24 支持版本和旧位置调用迁移要求。这是已知兼容性取舍，不重复列为新故障。
- 不建议删除 IEEE QK/PV、FP32 resource guard、forward-only/unsupported 检查、独立 FP64 oracle、out 哨兵或半精度回归。无新增公开算子/独立 kernel，注册 YAML 不变合理。两个主题可拆分 PR：MetaX FP32 支持/调优及测试；vLLM0.24 API 对齐及 ABI 测试（含 benchmark 参数误绑修复）。

### 本轮检查与证据边界

项目 inventory 与 mx-59 connectivity-check 通过；当前 git diff --check 通过；本地 Python AST 解析通过，两个 marker 缺失和 signature helper 缺依赖已核对。实际安装路径经 importlib metadata/find_spec 核对，未初始化模型/启动 GPU 测试。历史同 patch 的 pre-commit/设备测试保留原记录，本轮没有重跑，不声明新硬件验证。NV/Hygon/THead 仍只有既有静态/mock 证据。BGE 模型原支持 eager，本轮不新增 graph 支持声明或硬件结论。

本地只读审查快照 `/tmp/bgem3-fgv-review-20261109`；长期源码证据仍引用本节上方既有远端 FINAL_REPORT 和 delivery，完整 patch SHA 相同，不重复上传或创建远端实验。

2026-11-09审查问题已由[fgv-review-fix-005](fgv-review-fix-005.md)修复并应用实际安装源码；旧补丁及本节历史审查结论保留，当前版本与验证以该记录为准。

## 2026-11-09 FlagGems 完整 diff PR 审查

对象：mx-59 / BGE-M3 实际 editable 安装 `/workspace/bge-m3/tune-src/FlagGems`，HEAD `4897cc306cd83390c95b83b50df28f7edb1684c5`。完整 patch SHA `4fac55ee15de2195dd42c3e331d55bf84cec7ff0ded2f22d7cb8de795418fb16`，与历史交付相同：3 files/+236/-1。运行时 linear.py +58/-1，YAML +10，测试 +169。只读 review，未改容器代码、未启动设备测试或恢复已取消实验。

结论：修改归属与实现方向合理，没有确认的无关改动或新增数值错误；但按算子规范，完整补丁仍为 **needs_revision**，主要是验证材料不足。不能把“未覆盖”说成“已复现错误”。

### FG-R1 / P2：调参区域缺少绑定当前补丁的可审阅性能对照

位置：`src/flag_gems/runtime/backend/_metax/ops/linear.py:145–184`、`tune_configs.yaml:1973–1982`；对应算子 F1/F2/F3。

新分支为四种 (N,K) 特征对、0<M<=1024 的 contiguous FP32 输入增加独立候选池，注释称 measured region；但当前 diff 没有配套 benchmark 变化，现有 `benchmark/test_linear.py` 仅原生 torch 与当前 FG 比较，不能隔离“默认 linear tuner”与“默认+两组新候选”的增量收益。现有交付记录以正确性维护为范围，未提供绑定当前 patch 的该对照表。不能据此推断从未做过历史测量，但 PR 当前缺少可复核的证据。

建议：复用仓库 benchmark 框架，同设备、相同同步/warmup/测量、相同 cache 准备和 eager/graph 条件比较默认/扩展 tuner；覆盖四种特征对、M小值/中间值/1024与1025、bias、范围外守护，保留全部轮次、实际选中配置、默认耗时、候选耗时及回退。要区分首次调优成本与稳定缓存命中时间，不用模型总吞吐代替 Linear 证据。补证据前不根据候选池包含默认配置就断言热路径一定不回退。

### FG-R2 / P2：Parameter 处理和新增选择分支的测试范围不足

位置：`linear.py:163–184、223–233`，`tests/test_metax_linear.py:64–130`；对应算子 C1/E2。

`weight.as_subclass(torch.Tensor)` 位于选择器之外，对所有 MetaX Linear 的 Parameter 都生效，包括 FP16/BF16、范围外 shape 和非连续权重。新增测试只在一个 FP32/连续/冻结 Parameter 场景覆盖该转换，不能证明这些更宽路径的兼容性。输入 guard 还包含 requires_grad/grad_enabled、input contiguous、bias dtype/device、single_1d 等实质分支；矩阵统一用 inference_mode，且没有 eligible 特征对的一维输入和非连续输入选择反例，无法证明这些排除分支保持默认路径。

建议：先明确普通 Parameter 与框架 Parameter 子类的支持边界，补 FP16/BF16/FP32、范围内/外、非连续权重、真实 loader metadata 身份与内容保持检查；单独测试 grad enabled/no_grad/inference_mode 下的选择行为（不把它扩成新增 backward 支持），以及 eligible 1D、非连续输入、bias/device 不匹配时的预期选择或原异常。只有 A/B 证据表明确实冗余时再删除或收窄转换；当前不足以直接认定它不必要。继承的非连续 input.view、backward 或其他 ATen 变体限制不作为本次新增缺陷。

### FG-R3 / P2：新增调优路径的数值定义域边界覆盖不足

位置：`tests/test_metax_linear.py:88–125、152–169`；对应算子 C4/E2/E6。

新增精度用例主要为正负 randn，没有零输入/零权重、显式抵消、NaN/Inf 输入和非连续 bias 的数值用例；输出 NaN sentinel 只验证覆盖写入，不能代替 NaN/Inf 输入契约。新候选改变 tile/warp，虽然原 kernel AST 没改，仍应验证边界下累加、mask 和 bias 行为。补零参考用例时注意 relative_L2 的分母为0，需要单独按独立参考判断，不能照搬当前随机非零范数比值。

仓库原 `tests/test_linear.py` 已有 M=0 和多维常规用例，因此不是说整个仓库没有空输入测试；但历史36项是 `test_metax_linear.py` 专项，未把原标准 Linear 套件一并列入验证回执。建议补上述数值边界，并把适用标准 Linear 回归纳入最终验证；按实际合法契约选择，不为本补丁修复所有历史限制，也不放宽容差。

### 必要修改与不建议删除的内容

- `flag_gems.linear(input, weight, bias=None)` 与原 aten::linear 注册未变，没有新增融合/非 ATen API，不需要为了内部 tuning key 新增 operators.yaml 项。
- 复用原 linear_kernel，仅为限定形状建立独立 tuner；deepcopy 保护默认配置候选，厂商参数位于 MetaX YAML。`copy`、`lru_cache` 与两个候选都有直接用途，没有发现无关重命名、依赖升级或格式化。
- 当前实际 `LibTuner.kernel_hash` 包含 `configs_hash`，持久化表名据此区分；没有发现默认与扩展候选池因同一函数名而串用同一 best-config 表的证据。不得误报为缓存碰撞。当前 tuner/global knob 行为仍应按实际版本验证，不从静态历史资料猜测。
- 显式 K mismatch RuntimeError 与通用 Linear 同文案，并在 view/tuner/launch 前执行，属于必要契约护栏，不建议删除。它覆盖新增错误路径，不承诺修复所有旧非法输入。
- 显式 public API + 独立 CPU FP64 oracle、注册测试中的实际 tuner 命中、原 capture + 两次新输入/哨兵 replay、offset/非连续权重/半精度守护、默认配置不变断言都有价值。169行测试不等于169行冗余。
- 数值测试使用 fork_rng 隔离显式 manual_seed，未发现上轮 FGV 那种全局重新播种缺陷。ATen route 测试的 direct expected 用于路由一致性，数值正确性由前面的独立 FP64 用例承担，不把该 route 测试误报成全部 oracle 自引用。

### 验证边界与证据

本轮 inventory/connectivity、完整diff --check、AST解析通过；未执行设备单测、microbenchmark 或新的pre-commit。历史同 patch 的36项FG、graph及pre-commit通过记录仍保留；11月9日模型维护的配对结果不能当作此FG补丁相对默认tuner的增量性能证据。其他平台未新增修改，不要求无目的连接其他Host；本补丁不新增 out/backward 变体，无需扩大成整个线性算子族重构。

本地只读快照 `/tmp/bgem3-fg-review-20261109`。长期完整源码/patch/验证证据继续引用上方 interface-fix-003 既有远端 FINAL_REPORT、TEST_VALIDATION、delivery（FG patch SHA相同）。当前处理建议：保留实现，补性能、Parameter/选择分支和数值边界证据后再次审查；尚无依据要求大幅删减运行时代码。

2026-11-09 FlagGems审查问题已由[fg-review-fix-006](fg-review-fix-006.md)补齐验证并应用实际安装源码；生产实现保持不变，原审查作为历史保留，最新证据见该记录。
