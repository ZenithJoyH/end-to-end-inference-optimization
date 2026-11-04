# audit-001 当前保留代码的性能优化点

- 状态：审计完成；只读，无新生产补丁、服务重启、GPU请求或性能测量。
- 对象：mx-103 / deepseekV4-flash，DeepSeek V4 Flash W8A8，TP8 MetaX C550，vLLM 0.24.0+empty。
- 分类：现有 framework、operator/replace、operator/improve 机制审计；不把此次梳理当作新的优化实验。
- 正确性：用户于2026-10-22明确认可170/198=85.86%为精度通过。使用同一批原始输出、去除Markdown加粗后提取；原strict153/198及回执保留。没有为这次确认重新生成答案。

## 范围与结论

当前有效工作区相对各自HEAD共58个变更文件，其中39个生产文件：Plugin23、FlagGems5、FlagGems-vllm11；另有19个配置/示例/文档/测试/benchmark。FlagTree源码安装但工作区干净，无本地性能补丁。vLLM使用0.24.0+empty；当前Plugin的model_runner与main一致，无保留差异。

主要性能机制集中在：Attention减少padding与寄存器压力，Indexer直接读取分页KV并分片query，MCTlass W8A8与原生MoE工作区复用，mHC融合与Split-K，以及局部mask/量化调用优化。注册、构造器、限幅、数值顺序、缓存隔离等必要适配不应重复统计成加速。

实际配置SHA为`e96726adc97507698369af82b6f35ea82f933fc8e09dcbbcbbaa7dbc3a7d57fe`。8个worker的35个启动dispatch绑定完全一致；mHC、稀疏Attention、Indexer和路由等绑定`default.flagos`，RMS绑定`reference.torch`。provider内部仍可能调用原生vLLM，因此不能仅凭flagos标签认定算子来自FlagGems。分支选择另有shape条件，下表的“开启”不等于每个分支都有实测命中次数。

## 优化内容与适用边界

| ID / 阶段 / 分类 | 保留的机制与作用 | 实际状态、条件与代价 |
|---|---|---|
| A1 / prefill+decode / operator/improve | **HQ64→HQ16**：本模型每rank8个真实query heads，把原生最少64head的padding降至16，减少无效head运算和中间空间 | decode_hq16=true；限定D512、NoPE448/RoPE64、FP8 KV、W8A8 O投影及local heads≤16。不是64→16倍数的端到端加速声明 |
| A2 / decode / operator/improve | **Split-TopK S4 +稳定归并**：SWA和压缩KV候选各分4段并行，提升小batch并行度；缓存partial max/sum/acc维持graph地址 | splits4/BK16/BH16/4warps/1stage，batch≤64；需要两套KV/indices/lens，压缩C4/C128层可用，SWA-only不走S4 |
| A3 / decode / operator/improve | **half-D、QK fold/blockdiag**：512维输出拆成256维，降低累加器压力；8真实head条件下用16lane组织两半V，减少重复QK路径 | 当前开启；受S4、HQ16、real_heads8、DQ=DV512等限制；其余回到双half-D或普通路径 |
| A4 / prefill / framework | **跨TP headpack**：相邻rank交换半段token的8个真实head，拼16有效head，每rank处理一半token，再交换输出复原 | 开启，SQ≥8，非compile/capture，偶数world；以额外P2P和等待换减少padding计算，净收益尚未消融 |
| A5 / prefill / operator/improve | **staged QK→PV**：QK一次产生BF16概率和softmax状态，两个256维PV program复用，降低寄存器压力；非headpack路径有half-D/blockdiag | staged开启，但目前只由headpack成功后的local路径进入；额外概率workspace、KV重读可能抵消收益，不等于全部prefill统一使用 |
| I1 / decode / operator/improve | **直接分页FP8 Indexer**：按block table读KV，融合反量化、QK、ReLU和head加权归约，省去全量gather/解量化tensor与逐batch Python循环 | paged_logits=true、next_n=1、H64/D128；生产调用match变体；其他情况保留gather fallback |
| I2 / decode / framework+operator/improve | **静态graph形状+GPU跳过无效context block**：固定slots便于replay，设备读取valid_len让无效块只写-inf或提前返回；tree top-k在图内逐级归并 | graphsafe=true、K512；仍有静态logits/candidate空间和tree初始化。精确top-k同时承担必要语义修复，不能把整个实现都算性能优化 |
| I3 / prefill / framework+operator/improve | **query行四路/两路分片**：四路各算完整行的1/4并本地top-k，只all_gather512个int32索引；KV加载提出head循环并跳因果无效块 | TP8/DP1/PP1、M≥2048/N≥4096触发四路；两路fallback要求M≥2048/N≥1024并通信FP32 logits；小shape回vendor deep_gemm。未证明当前GPQA各分支次数 |
| M1 / prefill+decode / operator/replace | **MCTlass W8A8 linear与MoE GEMM**：MetaX vendor执行per-token激活INT8/per-channel权重INT8，两段expert GEMM间保留原生激活及最终moe_sum | 当前use_mctlass=true、python_api=true。限定BF16 hidden、对称dynamic W8A8、SiLU、TP-only，无LoRA/EP/MegaMoE/zero-point等；chunk_size16384高于当前4096token上限，不能称chunking已降低本服务峰值 |
| M2 / prefill+decode / framework | **MoE原生workspace复用+kernel-M缓存**：用原生slice/resize替代私有scratch与output.copy_；按shape缓存vendor kernel-M选择，避免重复真实激活cast及大权重临时转换 | 当前专家实现保留；原生problem-size、workspace、activation和moe_sum复用。历史组件验证不等于103端到端收益 |
| M3 / prefill+decode / operator/replace | **E256 alignment特化**：小路由count+prefix/scatter两kernel；大路由融合初始化和计数，避免多次初始化launch | 连续ids、无expert_map/外部workspace、E256；topk6/C≤64最多384routes，满足≤512小路径。仍是allocating API，不能称alignment自身也复用workspace |
| H1 / prefill+decode / operator/replace | **mHC pre融合/Split-K与现有post/head算子**：小T拆K增加并行；T4096融合head epilogue和layer-input reduction，减少scratch往返和launch | residual[...,4,4096] BF16、fn[24,16384] FP32等才走特化；T≤128 split4，T≤2048 split2；8192+分支在当前MBT4096下通常不可达。原生NVIDIA也有TileLang融合，不能声称本实现“比原生更融合” |
| H2 / prefill为主 / operator/improve | **Embedding行mask**：每行只读一次广播mask，不需清零的行不读写，需清零的行直接写0 | 显式连续[T,4096] BF16/FP32、bool[T,1]、value0路径；其他fallback。不是全局masked_fill替换；小T不走行特化 |
| Q1 / prefill+decode / operator/improve | **linear动态INT8行分组、shape选warp与launch元数据缓存**：小K多行分组，减少CTA碎片；编译launch缓存减少重复host处理 | 动态对称BF16连续二维K≤16384，无外部scale/azp；主要同时承担vendor数值顺序兼容。MoE内部走原生量化，不能泛化为所有MoE量化；FULL replay不会逐token执行Python缓存查找 |
| R1 / prefill+decode / operator/replace | **复用融合routing和SiLU算子**：sqrt/softplus、偏置或Hash表、top-k、归一化/路由缩放交已有FlagGems入口；shared expert走tensor-limit SiLU×up+clamp | 原生GateLinear保留；shared expert和routed expert激活是两条路径。Hash核log1p/非有限索引修复、limit10传递属于正确性 |
| F1 / decode / framework | **原生FULL decode graph与启动dispatch预热**：capture后replay减少host调度/launch开销；CachedOp沿用main prewarm | 实际native breakable cudagraph，7档[1,2,4,8,16,32,64]；torch.compile pipeline none。不是全模型Inductor或prefill graph；单流为原生顺序helper，无多流overlap |
| F2 / 条件路径 / operator/improve | **Inductor RMS4096 scoped launch策略**：匹配数学体AST指纹后固定tile/stage和分rank warp，拒绝未知数学体 | 配置存在、hook保留；本轮启动审计没有RMS执行记录，当前compile pipeline none，不能算已确认命中的收益。FG mm/addmm launch policy也主要是shared-memory合法性限制，缺实际shape命中证据 |

## 原生复用、必要适配与未启用项

已复用vLLM0.24的模型加载/专家映射/logits、GateLinear、MoE工作区和激活/求和、Attention.forward_mqa、Indexer.forward、cache spec/metadata/workspace、compressor状态和kernel、global top-k索引转换、KV dequantize/gather，以及Plugin main ModelRunner生命周期。MetaX构造器和窄kernel调用点仍保留必要适配；已删除旧model_runner差异和全局多流runtime patch。

以下不列为当前生效加速：

- **FGV packed-page KV gather补丁**仍在库中，但当前Plugin provider直接alias原生vLLM gather，绕过该补丁。
- **prefill_native_topk=false**；ATen/native top-k包装文件当前未启用。非match paged Indexer变体也非生产调用点。
- **MoE tuned_configs**当前wrapper只读取SPLIT_K（现有entry为1或缺省1）；BLOCK/warp/stage等没有传入vendor tensor-only ABI，E32表也非本路径读取对象。
- **mHC≥8192**、FP8 O-projection、FP4/MegaMoE、MTP/投机解码均不计当前配置收益。
- **prefix caching、custom all-reduce、多流overlap关闭**。thinking是生成语义配置，不是性能优化；当前服务使用原生default-chat-template-kwargs启用，example serve.py的--thinking本身只改长度/并发配置。
- **SwiGLU limit10、INT8舍入顺序、hash log1p/非有限处理、top-k 16→8warp、tensor-limit ABI、compiler import隔离、FG/FGV独立缓存目录**主要是正确性、平台可运行性或隔离。
- **FlagTree源码安装与vLLM empty版本对齐、卸载vllm_metax**属于环境兼容，不能在没有对照的情况下归因成性能收益。

## 39个生产文件覆盖表

下列路径分别相对容器的Plugin `/opt/vllm-plugin-fl`、FG `/opt/dsv4-sources/FlagGems`、FGV `/opt/dsv4-sources/FlagGems-vllm`。对应源码与HEAD差异在远端快照，非本地工作区文件。机制ID对应上表；“接线”不重复计算收益。

| 仓库 | 相对路径 | 作用/当前归类 |
|---|---|---|
| Plugin | vllm_fl/__init__.py | MetaX/模型opt-in注册；兼容接线 |
| Plugin | vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py | H1/Q1/R1等provider，shape fallback与custom-op边界 |
| Plugin | vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4_attention.py | A1–A5接入、原生gather/global top-k alias |
| Plugin | vllm_fl/dispatch/backends/flaggems/register_ops.py | dispatch注册接线 |
| Plugin | vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/__init__.py | package接线 |
| Plugin | vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/indexer.py | I3小shape deep_gemm fallback、函数缓存 |
| Plugin | vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py | M1/M2 vendor GEMM、kernel-M缓存 |
| Plugin | vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py | 延后GDN注册、避免循环导入 |
| Plugin | vllm_fl/dsv4_config.py | typed冻结配置/TP8与single-stream支持门禁 |
| Plugin | vllm_fl/models/deepseek_v4.py | 原生模型复用、H1接入、INT8权重映射 |
| Plugin | vllm_fl/ops/deepseek_v4.py | H2/Q1/R1窄custom-op与fallback |
| Plugin | vllm_fl/ops/deepseek_v4_attention.py | A1–A5构造/调用边界、原生forward/cache复用 |
| Plugin | vllm_fl/ops/deepseek_v4_indexer_decode.py | I1/I2分页logits、静态tree top-k |
| Plugin | vllm_fl/ops/deepseek_v4_indexer_prefill.py | I3四路/两路query分片 |
| Plugin | vllm_fl/ops/deepseek_v4_metax/__init__.py | package接线 |
| Plugin | vllm_fl/ops/deepseek_v4_metax/decode.py | A2/A3 S4/half-D/QK fold、fallback |
| Plugin | vllm_fl/ops/deepseek_v4_metax/policy.py | A2–A5固定kernel policy |
| Plugin | vllm_fl/ops/deepseek_v4_metax/prefill.py | A4/A5 headpack、staged、half-D |
| Plugin | vllm_fl/ops/fused_moe/router.py | R1 DS opt-in融合routing |
| Plugin | vllm_fl/ops/prefill_topk_native_op.py | 未开启的native/ATen top-k可选路径 |
| Plugin | vllm_fl/ops/sparse_attn_indexer.py | I1–I3调度、short-row语义和graph处理 |
| Plugin | vllm_fl/patches/deepseek_v4_metax.py | F1/F2、hash审计、隔离门禁 |
| Plugin | vllm_fl/quantization/w8a8/deepseek_v4.py | M1/M2/M3、native workspace/activation、limit10修复 |
| FG | src/flag_gems/fused/topk_softplus_sqrt.py | R1数值修复：hash log1p及非有限索引 |
| FG | src/flag_gems/ops/dsv4_masked_fill.py | H2行mask和launch cache |
| FG | src/flag_gems/runtime/__init__.py | F2可选launch policy接线 |
| FG | src/flag_gems/runtime/backend/_metax/fused/top_k_per_row_prefill.py | warp64设备sort≤512线程的合法性修复 |
| FG | src/flag_gems/runtime/metax_launch_policy.py | mm/addmm shared-memory和stage限制 |
| FGV | src/flaggems_vllm/ops/deepseek_v4_attention_dequantize_and_gather_k_cache.py | page-stride免copy、tuner/grid修复；当前被native gather绕过 |
| FGV | src/flaggems_vllm/ops/dsv4_int8_quant.py | Q1动态INT8行分组、数值兼容 |
| FGV | src/flaggems_vllm/ops/dsv4_launch.py | Q1 compiled launch metadata cache/ABI兼容 |
| FGV | src/flaggems_vllm/runtime/backend/_metax/fused/gdn_chunk.py | 去掉导入即全局compiler patch，DSV4非GDN |
| FGV | src/flaggems_vllm/runtime/backend/_metax/ops/__init__.py | H1/M3/R1 vendor导出接线 |
| FGV | src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py | vendor alignment导入；主MoE走Plugin专家 |
| FGV | src/flaggems_vllm/runtime/backend/_metax/ops/mhc_pre.py | H1 MetaX融合与按T Split-K |
| FGV | src/flaggems_vllm/runtime/backend/_metax/ops/moe_align_block_size.py | M3 E256小路由及大路由初始化融合 |
| FGV | src/flaggems_vllm/runtime/backend/_metax/ops/silu_and_mul_with_clamp.py | shared expert tensor-limit graph ABI和tile限制 |
| FGV | src/flaggems_vllm/runtime/backend/_metax/tune_configs.yaml | scalar SiLU/linear配置；不能归给独立tensor-limit路径 |
| FGV | src/flaggems_vllm/utils/code_cache.py | 独立FLAGGEMS_VLLM_CACHE_DIR隔离 |

## 配套文件与证据边界

19个配套文件均已检查：Plugin11个示例/配置文件覆盖镜像构建、requirements/dependency lock、bootstrap、serve、实际profile原型、Hash表清单和两份MoE调参表，2个单元测试覆盖打包及层边界；FG1个integration说明；FGV2个测试、2个benchmark覆盖alignment和packed gather，另1个integration说明。它们不能另计为19项运行时优化。测试/benchmark文件存在不表示本revision已执行过；旧README性能表、旧revision/分支描述和mHC“27.93x”注释不代表本机当前版本结果。

当前已证明：源码/config身份与精度运行一致；8worker绑定相同；7档graph capture，C1 FULL replay14次、C8 FULL replay2次，10请求最小回归通过；完整GPQA198题用户确认85.86%通过。没有新增当前103同workload baseline/candidate/revert，也没有每个可选分支的shape计数或profile。总加速比、单点加速比及累计收益均为未测，不能相加或引用旧环境数字。

## 决定、风险与回退

保留当前生产状态，本轮不改代码、不重新压测。当前性能梳理完成；未进行PR整理或跨平台硬件验证，`pr_readiness=not_assessed`。精度认可不自动构成性能验收。

可见的后续测量候选仅记录，不实施：prefill provider未传入out导致临时输出再copy；top-k前3次/每512次读min/max仍有host同步；mHC每次FP32→BF16权重转换；静态tree workspace初始化；headpack/query分片通信等待。应先建立目标workload基线并确认热点再决定，不把静态可疑开销直接当作瓶颈。

此次无生产改动可回退。未来代码整理应以本次完整HEAD diff和有效源码快照为回退依据；不可因当前某路径未命中直接删除共享库实现。本地仅更新案例Markdown/YAML；没有提交、推送或创建PR。

## 外部证据

远端根：`/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/code-audit-001`。snapshot收集当前修改文件、对应HEAD及原生vLLM参考文件；大文件/权重/原始回答不进入本地案例。

- Plugin：HEAD `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`；branch `upgrade/20261020-main`；完整patch SHA `5ea09be19685b023b68ec43eed537793c366e7fa1c2fe6f5004361b2f948b4a9`。
- FlagGems：HEAD `8200f71f51d784d54a5a51019cb955acb74d64c1`；branch `upgrade/20261020-latest`；完整patch SHA `6be5befa86f2568f94de51bc12be73a74f24acb53beb690cc7f988b905930c21`。
- FlagGems-vllm：HEAD `fa78ddee4c3e78ce5047213ff0ef02acff34b2d5`；branch `upgrade/20261020-latest`；完整patch SHA `961849cb4f411f0bef0ad22c36f02361be8fe5babec603e30c73c5aad621e7ac`。
- FlagTree：HEAD `317a0249ec25c6756e0aee3a87e8e3c92f154335`；branch `main`；完整patch SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- `source-snapshot.json`：SHA `9ac04e72a68b3e673ad9e877d5f03f5e7737909c9816c6908751c9932d15006b`。
- `runtime-supplement.json`：SHA `1a739dd59402ba9af7aab9cf7cf461db59c05afbb892678d01f1626dc85428bb`。
- `startup-bindings.json`：SHA `f248db1fa438a56e6fa7296220ba899a3942a1d6eab01613e5cd0647e3aad5d8`。
- `user-accuracy-acceptance.json`：SHA `8d22349da1c15917918c51a7787bd3670beee153d69c08b8f56c316ddf6a7130`；保留原始198题及其归档，不改旧评测树。
- 采集命令：远端 `commands/collect-code-audit001.py`、`commands/audit-runtime-supplement.py`、`commands/collect-binding-audit.py`；先保存再执行，只读生产树。
