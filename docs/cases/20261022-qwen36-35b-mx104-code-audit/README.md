# Qwen3.6-35B / mx-104 verify 容器代码整理
**后续修复已完成：** [采样导入生命周期修复与真实TP2服务验证](../20261022-qwen36-35b-mx104-sampler-fix/README.md)已解决本次迁移记录中的采样导入顺序问题；6项导入、25项数值及实际优化采样器/shortlist/graph验证通过。下文保留当时代码审计与迁移范围，不以新的服务验证改写历史结果。

**当前状态：Plugin 已迁移到本轮最新 release/0.2（7cb559947），原 8 个局部修改保留，仍从 `/workspace/vllm-plugin-FL` editable 加载。** 101 个 CPU/mock 测试通过，安装后 89 个模块来源、50 个函数代码及 5 个关键算子选择核验通过，见 [Plugin 基线迁移记录](plugin-release02.md)。FlagGems-vllm 此前已切换至 `/opt/FlagGems-vllm/src/flaggems_vllm` editable 安装，276 文件保持原字节、156 个加载模块及 MoE/GDN 共 45 个函数一致性通过，见 [editable 安装记录](editable-installation.md)。[安装版 MoE 回收与 vLLM 复核](source-reconciliation.md)确认 vLLM 4,737 文件相对 HEAD 无差异，本轮未修改 vLLM。下文保留初次归档阶段的观察与产物身份，“旧 Plugin 基线”“安装专属”“非editable”等描述只对应该阶段。

2026-10-22，Asia/Shanghai。对象为 `mx-104` 的 `qwen3.6-35B-verify`，模型目录由用户明确指定为 `/data/Qwen3.6-35B-A3B-nomtp`。本次完成源码盘点、功能补丁分组和优化机制梳理；未开展新性能优化。本地历史及 mx-59 的结果均未用作本次优化内容或收益证据。

远程交付目录：`/public-flash/jinghao/qwen3.6-35B/20261022-qwen36-35b-mx104-code-audit`，下文以 `CASE` 表示。用户提供根目录规范路径与输入一致、非符号链接，owner UID/GID=0/0、权限0755；检查时空闲约3.24TB。仅在新case目录写入产物，不改原执行源码、安装、容器配置、模型或服务，不提交推送。

**完成结果：30份精确字节源码快照，5组按功能归类的规范化补丁，全部补丁在隔离副本应用成功，9个Python文件AST一致，原执行源码SHA未变化。** 这是代码归档与审阅包，尚不是新部署版本或精度/性能验收结论。

## 环境与证据边界

已通过 `scripts/inventory`、仅限 `mx-104` 的 `scripts/connectivity-check` 验证连接。容器检查时只有shell，没有模型服务，因此不能从该容器核验当前TP、设备组、服务端口、graph、启动参数或历史测量身份。本次不为代码整理启动模型、占用设备或创建新性能测试容器。

| 组件 | 当前身份 / 导入 | 本次核验结果 |
|---|---|---|
| 镜像引用 | `harbor.baai.ac.cn/flagos-inner-models-release/metax-qwen36-35b-a3b-release-1021:latest` | 实际ID：`sha256:955b7d73d6eb32c66904a77f4e393da966c2bfa8ff3c4c2b11d6305159c18535` |
| vLLM | 0.20.2+empty；`bc150f50299199599673614f80d12a196f377655`；editable `/workspace/vllm` | Git工作区干净；不把Plugin运行时patch计为vLLM落盘改动 |
| Plugin | 0.2.0+gd1653d9ff；main `d1653d9ff0450ce0366686bfcde5d8aecab44755`；editable `/workspace/vllm-plugin-FL` | 5个tracked文件修改，另有MoE配置及两份采样实现未跟踪 |
| FlagGems | metadata 5.0.2；editable `/workspace/FlagGems/src/flag_gems` | 目录无Git元数据，不能推断其revision或相对上游的改动；保存源码树内容指纹 |
| FlagGems-vllm | 0.1.0；源码 `/opt/FlagGems-vllm`，HEAD `e1a02b6b2e47abea9a6cfeaaf3431f50f7f476f8` | 非editable安装，实际导入 `/opt/conda/lib/python3.12/site-packages/flaggems_vllm` |
| PyTorch / FlagTree | 2.8.0+metax3.7.0.7 / 0.6.1+metax3.6 | 实际解释器 `/opt/conda/bin/python`，Python3.12；系统python3.10的无包结果不适用 |

挂载为 `/public-flash`→`/public-flash` RW/rprivate、`/data`→`/data` RW/rslave；`/workspace` 和 `/opt` 不在这些bind内。没有新容器的谱系/挂载门禁，本次也没有进行需要这些门禁的新性能实验。

模型配置实际为 `Qwen3_5MoeForConditionalGeneration` / `qwen3_5_moe`，BF16、hidden=2048、256专家、top8、moe_intermediate=512、40层（30 linear / 10 full attention）、vocab=248320。TP2形状推导为每rank专家中间维256、linear value heads16；这是分析形状，**不是已运行TP2的证明**。模型generation配置为temperature=0.6、top_k=20、top_p=0.95；服务或请求可覆盖，当前有效采样参数未知。

## 优化点清单

下列分类表示收益机制；“代码已接入”仅指源码/配置连接，不替代服务调用、graph和性能证据。

| ID | 分类 / 阶段 | 实质内容 | 连接状态与边界 |
|---|---|---|---|
| C01 | operator/replace；Prefill | 单请求把paged KV gather成连续KV，再调用FlashAttention varlen | Plugin分支已接入，容器开关为1；仅单prefill、seq_len≥2048、无KV量化；没有服务命中证据 |
| C02 | operator/improve；Prefill/Decode/Mixed | MoE按batch配置tile，GEMM2独立覆盖，含小M的SWAP_AB | Plugin staged路径和配置已接入；需匹配E/N/device配置文件和实际选中路径；另一快路径可能绕过该配置 |
| C03 | operator/replace；MoE激活 | TritonExpertsFL的SiLU改走call_op(silu_and_mul)，其他activation维持原调用 | 白名单包含silu_and_mul；改变中间buffer来源，正确性/分配/graph待服务验证 |
| C04 | operator/improve；采样/Decode | 词表248320的top64 shortlist，减少完整词表排序 | 模型结构/设备/dtype/batch受限；仍保留全词表softmax/cumsum和host同步，非全流程top64化 |
| C05 | framework配置；全阶段 | 开启FlagGems但按白名单选算子，路由topk_softmax强制MetaX vendor | 当前容器配置明确；不能将FlagGems-vllm中的全部kernel都视为已使用 |
| L01 | operator/improve；GDN Prefill | FlagGems-vllm H kernel从多配置autotune裁剪成目标shape固定配置 | 源码与安装版字节相同；当前Plugin FLA选择需按白名单核验，未证明此库路径在模型中命中 |
| L02 | operator/improve；MoE | FlagGems-vllm安装版额外增加TP2专家shape、分阶段tile与pipeline调参 | **仅安装副本有改动**，源仓库缺失；当前Plugin直接引用flag_gems，不可自动归因到此库 |
| P01 | framework/JIT控制；Mixed | full_kernel取消动态N专化/在线autotune的补丁文件 | **仅打包**；当前实际FlagGems MetaX full仍含full_kernel_scale autotune，不可算已应用 |

### C01：连续KV单请求Prefill

文件为Plugin `vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py` 和 `vllm_fl/envs.py`。新开关 `VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL` 默认0，当前容器设为1。

分支用block table的实际block IDs分别index_select K/V，再reshape、裁剪到seq_len，给FlashAttention传连续KV；其他情况保持paged KV，Decode分支未由此改动。2048阈值作用于包含prefix的KV总长，不能称为仅当前chunk query≥2048才启用。两次gather会引入临时KV和显存读写，长上下文反复chunk时是否划算要实测。

`/opt/dense27b_contiguous_prefill_patch_ly/` 是旧补丁包，README使用另一开关 `VLLM020_CONTIGUOUS_SINGLE_PREFILL`，并引用其他模型验证数字。当前实际代码使用 `VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL`；本次保留旧包为参考，不能据其README判断当前开关或性能。另一个 `/opt/qwen36-final-moe/patches/vllm_metax_contiguous_single_prefill_ly.diff` 也单独归档，不自动再安装。

### C02/C03：MoE分阶段配置与SiLU接入

Plugin `vllm_fl/ops/fused_moe/fused_moe.py` 在每chunk复制config，弹出 `GEMM2`，与base合并形成第二段config；`fused_moe_utils.py` 的staged路径采用相同规则。两段要求BLOCK_SIZE_M一致，避免专家排序/对齐与实际GEMM分块契约不一致。`.copy()` 避免修改缓存配置。

容器 `VLLM_TUNED_CONFIG_FOLDER` 指向 `/workspace/vllm-plugin-FL/vllm_fl/configs/moe/metax`。配置文件为 `E=256,N=256,device_name=metax.json`：M≤1024等配置使用BM16/BN128/BK64/W4/S2，并为GEMM2开启SWAP_AB；M2048/4096和≥8192另有tile，≥8192的GEMM2覆盖BK64/stages1/basic。参数按token batch/shape选择，不能直接把batch阈值解释为prompt长度。

当前FlagGems `fused/fused_moe.py` 的invoke入口会消费SWAP_AB、PAIR_GATE_UP_DOT；其完整fused_experts实现另有stage-aware配置、SiLU融合和直接归约能力。这些是当前库内存在的实现，因FlagGems没有Git baseline，不伪装为本次可量化的本地优化diff。

`TritonExpertsFL.apply` 还保留 `self._lora_context is None and current_platform.is_cuda()` 的完整 `flag_gems.fused_experts_impl(..., inplace=False)` 快路径并copy到输出，该路径在staged调参之前return。因此必须按实际platform/选中expert类核验是否经过C02/C03，不能把两条路径重复计收益。

SiLU分支把预分配workspace视图变量替换为dispatch返回张量。整理时未改其语义，后续维护应核对output alias、临时分配、LoRA和graph，而不是仅凭dispatch名认定减少了分配。

`/opt/qwen36-final-moe/configs/short_1k.json` 和 `long_context.json` 使用stage1/stage2 schema；当前Plugin配置使用base+GEMM2 schema。已检查Plugin和相关Gems源码引用，未发现这两份JSON的直接接线；不可把它们与当前VLLM_TUNED_CONFIG_FOLDER混为同一配置来源。

### C04：Qwen MoE shortlist采样

Plugin `dispatch/backends/vendor/metax/patches/topk_topp_sampler.py` 替换采样器构造符号，保留native随机数与logprobs处理。Qwen MoE分支要求qwen3_5_moe、BF16模型、E256/hidden2048/vocab248320和C550；tensor要求FP32 logits、连续布局、8≤batch≤64，k/p shape/dtype/device匹配。

`impl/qwen36_moe_shortlist.py` 先torch.topk取64个候选，用Triton准备按分数/索引排序的候选，安全条件含1≤k<64、64号候选严格低于top-k阈值和有限最大值；不满足回原PyTorch过滤。候选放在全词表末尾，仍在原词表维度进行softmax及cumsum，最后scatter筛选结果，避免宣称把所有算子都降成64维。

`bool(valid.all())` 会产生GPU到host判断，因此不能直接承诺该函数可放进capture区域；常规模型graph与采样执行边界也需分别确认。score tie、NaN/Inf、k边界、top_p边界、batch7/8/64/65、generator与logprobs均需要后续数值/行为回归；本次没有运行这些模型/设备测试。

同一个采样模块还保留Qwen3-VL counting分支和未跟踪文件 `qwen3_vl_counting.py`，其模型/shape条件与目标分开。本次补丁完整保留该依赖，未把非目标模型代码删掉。若后续拆PR，应明确其范围及依赖，避免只携带采样入口而丢失实现文件。

### C05、L01/L02、P01：接线与打包差异

容器为USE_FLAGGEMS=1、VLLM_USE_FLAGGEMS=1、FLAGGEMS_VENDOR=metax、USE_FLAGTUNE=0、FLAGGEMS_ATEN_SHAPE_AWARE=0、VLLM_FL_STRICT=0，且 `VLLM_FL_PER_OP=topk_softmax=vendor:metax`。白名单包含MoE invoke/align/sum、silu_and_mul及部分ATen算子，但**不包含** `chunk_gated_delta_rule_fwd`、`fused_recurrent_gated_delta_rule_fwd`。Plugin `ops/fla/chunk.py`、`fused_recurrent.py` 对这两个key做条件导入；白名单不启用时采用vLLM侧路径（MetaX自身patch另按加载处理），不能把FlagGems或FlagGems-vllm的GDN优化直接列为当前已启用。

登录shell实测函数对象：Plugin adapter所引用的 `flag_gems.invoke_fused_moe_triton_kernel` / `fused_experts_impl` 来自 `/workspace/FlagGems/src/flag_gems/fused/fused_moe.py`；`flag_gems.full` 来自MetaX `ops/full.py`。FlagGems-vllm公共 `fused_experts_impl` 则来自site-packages的MetaX实现，是另一套函数对象。库能导入只证明包可用，不能证明模型调用。

L01的prune条件为(H,K,V,BT)=(8或16,128,128,64)、varlen并存final state。H16选择BK64/BV64/W4/S3；H8且有initial state选择BV32/W2，否则BV64/W4。意图是减少新N/skew bucket触发24候选在线调优；这只能作为代码机制，注释中的“measured”不替代本次证据。

L02经整棵安装包与源码树的.py/.yaml/.json比较，唯一不同文件为MetaX `fused/fused_moe.py`；GDN修改在两处一致。安装版扩展了w1=(256,512,2048)、w2=(256,2048,256)、top8形状，增加GEMM1 BK32/GEMM2 BK64等配置与GEMM2 pipeline范围，并保留ablation日志。重装 `/opt/FlagGems-vllm` 会覆盖这份安装专属改动，因此已独立精确快照和拆出补丁，未自动迁回源仓库或重新安装。

P01补丁位于 `/opt/qwen36-moe-v725/patches/full_dynamic_shape_fix.diff`，意图给N加入do_not_specialize并改固定launch。当前实测 `flag_gems.full` 所属文件仍为原autotune版本。全局USE_FLAGTUNE=0也不能证明已关闭文件中直接使用的triton.autotune。

## 交付包、复现与校验

| CASE内相对路径 | 内容 / 使用边界 |
|---|---|
| `README.md` | 本报告的远程副本 |
| `manifests/source-inventory.json` | 版本、HEAD、工作区、实际模块spec、白名单容器环境和挂载 |
| `manifests/exact-source-inventory.json` | 30份原文件路径、字节SHA、大小、换行统计；对应下面精确快照 |
| `sources-exact-v2/` | 容器原文件精确字节快照，含安装专属MoE、GDN及主路径支持文件 |
| `review-v2/normalized/` | 保持AST的LF审阅副本，不是已部署代码 |
| `review-v2/patches/01-attention.patch` | Attention与开关，基于Plugin d1653d9ff |
| `review-v2/patches/02-moe.patch` | MoE两段参数/SiLU及必要未跟踪JSON，同上基线 |
| `review-v2/patches/03-sampling.patch` | 两模型采样入口及两份实现，同上基线；保留共享依赖 |
| `review-v2/patches/04-gdn-h-prune.patch` | GDN裁剪，基于FG-vllm e1a02b6 |
| `review-v2/patches/05-installed-only-moe.patch` | 安装专属MoE差异，以FG-vllm源码相对路径表示；不会自动更新安装 |
| `review-v2/checks/` | 已执行patch check/apply的隔离副本；不属于运行导入路径 |
| `patches/{plugin,fgv,vllm}.patch` | 最初完整Git补丁；vLLM为空。Plugin包含CRLF噪声，不建议直接作PR |
| `manifests/flaggems-tree-fingerprint.json` | 无Git的FlagGems源码内容清单及聚合指纹；不是上游revision |
| `manifests/cleanup-validation.json` | 5组check/apply通过、9份AST等价、原文件未变的回执 |
| `manifests/import-probe.json` | 登录shell导入、函数归属及白名单选择探针结果 |
| `commands/{capture,organize,organize-v2,probe}.py` | 每次远端操作前先保存的执行副本 |

需要复核补丁时，在匹配HEAD的独立checkout或本CASE的检查副本使用 `git apply --check <patch>`；先检查当前工作区，不能向已含优化的verify源码重复应用。Plugin三组补丁按01→02→03检查，FG-vllm的04/05以它自己的HEAD检查。FlagGems没有可靠Git基线，不提供虚假的“恢复上游”命令。

原执行源码没有变化，无需对原服务做回退。将来使用审阅包部署时，需要将新版本与当前精确快照区分，并在独立环境验证导入、命中、最小回归、graph capture及至少两次replay，另做精度/同配置性能验证；本次AST一致不能替代它们。

关键校验：

- `source-inventory.json` SHA256：`9f871f4512161a63193bdf3a0595bfb2766b72dec73fb174c4432ef300127505`。
- 完整Plugin patch SHA256：`983bc48df8a75027464bd56c7a4efaed6aa0446244347232dd90d13d093b91a8`。
- 完整FG-vllm patch SHA256：`f7dae365c02ba2231d952068cd115989039edf9bf61f43e5452c4d91ccb974da`。
- FlagGems源码树聚合SHA256：`cce96c703b67f3198127ce2d7709b1bffdd198650d74fe08f9f680630f3247c9`。
- `cleanup-validation.json` SHA256：`0e50914a37ad8adeb2a14e57f71dcf6ebd385d13ae20e18990c1b4e540d02057`；每个功能patch的SHA在该文件内。

## 验证状态与工程收尾

| 检查 | 结果 | 说明 |
|---|---|---|
| 功能patch语法 / check / 隔离副本应用 | executed_passed | 5组全部通过，新文件包含在补丁内 |
| Python解析与AST对等 | executed_passed | 9文件，保持原代码语义；不是算子数值测试 |
| 原执行源码未变化 | executed_passed | 快照清单30个文件结束时重算SHA一致 |
| 登录shell包导入 | executed_passed | MACA_PATH=/opt/maca；非登录shell缺失该变量曾报错，不判定模型失败 |
| 模型smoke / 数值 / graph / 正式精度 | not_run | 容器未运行模型；本次无部署或新算子修改 |
| 新性能 / A-B-revert / Prefill-Decode-Mixed分解 | not_run | 本次梳理代码机制，不声明端到端或单点加速比 |

Plugin原始diff的巨大行数主要来自CRLF：Attention1240行、采样入口103行、envs38行、fused_moe306行、MoE JSON233行。归一化只发生在审阅包，不改执行文件。当前 `pr_readiness=needs_revision`：缺模型路径命中和设备回归；安装专属MoE尚未纳入源仓库；采样包含非目标VL共享分支；需补采样边界和monkeypatch重复加载、workspace/LoRA及可选依赖验证。没有擅自升级、commit、push或创建PR。

容器还附带 `/opt/qwen36-moe-v725/reference_results/` 和 `/workspace/all_perf.py`。CSV包含1K/4K/16K/64K；脚本把请求数绑定并发数且默认N64，与本项目N128正式契约不同，也缺当前verify服务身份。因此不把其自报数字当作本次收益或正式四场景结果。

过程保留：首次生成器对新文件遗漏 `new file mode`，使02 patch在隔离副本check失败；v2补齐元数据后使用新目录重做全部5组并通过。旧 `review/`、`sources/` 及 `sources-exact/` 留为过程证据；`sources/` 是归一化文本分析副本，其字节不可代替精确快照。一次整包导出本地/tmp的请求被自动审批拒绝后未执行，后续改为远端就地归档，任务不再依赖该导出。

本次没有形成新的因果性能经验，不修订SOP或算子知识结论。后续优先统一源码/安装身份和共享入口范围，再在已授权的独立优化环境补命中及回归；保持当前verify可复现状态作为参照。

## 本地审计补记

远程报告正文SHA256为 `8d1c2b48712936254ab2b4e7fa714fd75b8072b83da0a256f4e6d69477f0e0ef`，已核对发布时本地与远端一致；本节为发布后的本地命令指纹补记。以下路径均相对远端 `CASE/commands/`，已在远端实际重算：

| 脚本 | SHA256 |
|---|---|
| capture.py | `15653f1024b4800e3a49681c30d5f335ba9561933468f72e8163d13a7490a9f3` |
| organize.py（首版失败保留） | `cfa772c0ecad62a3c8c72842cc9d48830f5ebed7b23dc7945f0f9a3cad548433` |
| organize-v2.py | `396b133a2799f825cacfc3a8f5dc92b162ba1ad84adbad63f8301aaa3eceb551` |
| probe.py | `87a31a773d5d0b55da9ea2f90a811d1bcc8ad97486d379f90e023b7e30701046` |
| publish-report.py | `0e52679fa3e41d083d3d66be22a58848e747ee5b6954af082bd72ce16a7f310b` |

本地文档与索引执行 `git diff --check` 通过；新报告另做no-index空白检查，无空白错误（退出码1仅表示与/dev/null存在新增内容）。
