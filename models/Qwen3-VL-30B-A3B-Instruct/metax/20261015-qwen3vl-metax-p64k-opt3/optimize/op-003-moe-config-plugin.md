# op-003：MoE 优化配置迁入 Plugin

现有57项GEMM2调优JSON由独立容器中的Plugin维护，内容不变。2026-10-16按用户要求改用`FLAGGEMS_VLLM_MOE_CONFIG_DIR`指定目录，移除Plugin传`config_dir`的包装函数，库保留通用加载逻辑。目标服务为`qwen3vl-p64k-opt-20261015`、GPU0/1、8111、模型名`qwen3vl-opt4`，保留用户当前memory0.91。源容器`qwen3vl-flaggems-e2e-20261013`的8000/GPU4,5未回写、停止或重启。这是既有优化环境中的配置整理，没有另建性能优化任务。

## 配置归属与调用

新目录：`/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/flaggems/configs/metax/moe/`。文件名保持`E=128,N=2048,K=384,topk=8,device_name=MetaX_C550,dtype=bf16,gemm_stage=gemm2.json`，SHA256保持`ad5bf196af20be5f9bb2916527a9fd061172e7fbbc93ed329a3e925758654261`，精确M=8..64的`num_stages=1`不变。

最终调用为Plugin `TritonExpertsFL.apply` → FlagGems-vllm `fused_experts_impl`，不传目录参数。启动脚本`/public-flash/jinghao/qwen3-VL/start-model.sh`增加`export FLAGGEMS_VLLM_MOE_CONFIG_DIR=/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/flaggems/configs/metax/moe`。MetaX配置选择器读取该变量，将目录作为私有加载器缓存key的一部分；库不反向导入Plugin，不含Plugin路径常量，也不保存此次JSON。变量未设置/为空时保留库默认目录行为，修改同路径文件后需重启worker以刷新缓存。初版adapter/config_dir接口只作为下文历史迁移记录保留。

`apply`仅替换import，不增加平台判断；环境变量入口位于库的MetaX配置边界，其他平台不新增读取行为。未修改Worker、kernel、dtype、LoRA分步路径或FlagGems选择，不增加产品全局monkeypatch。缺文件、未命中shape/M、量化block shape及embedded优先级保持原行为。JSON覆写仍保持`is_embedded=False`，避免改变融合、对齐路径。此前共享内存默认配置修正继续保留，与目录选择接口分开看待。

Plugin的package-data已包含新JSON，FlagGems-vllm恢复仅打包原YAML。当前使用私有源码导入，无需重装。

### 2026-10-16：库侧残留修改说明

用户询问为何FlagGems-vllm仍有diff。再次核对当前源码SHA仍为`575e94b132f2e62faa36c06ed5c11519161142a80f13bde156041d9ac5911716`。上次对话中“仅保留通用config_dir接口”的表达不够完整：本轮只新增通用目录传递，但整个库还保留此前的共享内存修正和JSON加载器，并未恢复成上游零diff。

相对当前HEAD，新增函数为`_get_shared_memory_limit`、`_get_moe_stage_configs`，变更函数为`try_get_optimal_moe_config`、`_generic_get_default_config`、`fused_experts_impl`。其中共享内存修正读取真实per-block上限，核算paired GEMM1双权重tile，允许stage降至1，并按容量限制paired路径；这些是此前已有的默认配置修正，不是此次搬JSON新增的kernel或另一份JSON。

最终选择顺序是：先查原embedded配置；没有embedded配置时，生成库默认配置（包含上述共享内存修正），再在block_shape=None时读取Plugin指定目录的精确M条目并覆盖对应字段。目标M8..64/GEMM2的`num_stages=1`由Plugin JSON提供，算子加载合并与执行仍发生在FlagGems-vllm，`is_embedded=False`不变。因此当前仍是两个仓库配套生效，不能只移植Plugin而撤掉全部库侧补丁。

若绕过Plugin adapter直接调用库算子，`config_dir=None`只查已清空的库默认JSON目录，不会自动得到Plugin的57项调优；库的默认/共享内存逻辑仍会执行。当前只读文件核验与此前两worker graph取证一致，未向用户在途worker注入代码，也未修改源码或服务。

### 2026-10-16：外部调优目录环境变量可行性

在`qwen3vl-p64k-opt-20261015`只读检查当前源码，未修改源码、环境、服务或在途benchmark。vLLM的`model_executor/layers/fused_moe/fused_moe.py:1043`确实读取`envs.VLLM_TUNED_CONFIG_FOLDER`，但FlagGems-vllm源码中没有该变量的读取点；实际MetaX完整MoE调用自己的配置选择器，不经过vLLM的该加载器。当前Plugin adapter在`dispatch/backends/flaggems/impl/fused_moe.py:24`显式传入Plugin资源目录，库侧`runtime/backend/_metax/ops/fused_moe.py:624`负责加载，`:734`负责合并。因此仅export现有`VLLM_TUNED_CONFIG_FOLDER`不会让这份配置作用于当前FlagGems MoE。

两者格式与选择语义也不同：vLLM原生文件名以E/N/device/dtype及可选block shape组织，命中后按最近M选择完整配置；当前文件还区分K/topk/GEMM阶段，精确命中M后只合并指定字段，保持默认融合路径及`is_embedded=False`。不能仅改目录或文件名就视为等价接入，尤其不能把GEMM2的stage覆盖推广到GEMM1或未覆盖M。

可以设计类似环境变量的通用外部目录入口，使库直接读取目录、Plugin不再逐次传`config_dir`；但仍需库侧支持目录读取与上述覆盖语义，属于替代参数传递方式，不能消除加载器依赖。是否复用vLLM变量名需要明确两个后端的格式与作用范围；独立FlagGems目录变量或保留显式接口都比假定vLLM变量自动透传更明确。共享内存默认配置修正与JSON目录入口是不同改动，环境变量方案不会自动替代前者。本轮仅解释可行性，没有实施新接口，也没有重新测量或扩大此前验证结论。

### 2026-10-16：环境变量入口改造（完成）

按用户新指令，采用`FLAGGEMS_VLLM_MOE_CONFIG_DIR`指定Plugin现有JSON目录。删除Plugin目录包装函数，`apply`恢复直接导入`flaggems_vllm.fused_experts_impl`；库侧删除完整算子和选择器的`config_dir`透传，只在配置选择时读取环境变量，把解析后的目录传入私有缓存加载器，保证不同目录不会复用错误缓存。环境变量未设置或为空时保持库默认目录；现有embedded优先级、block_shape限制、精确M/shape/dtype/device/GEMM阶段匹配及`is_embedded=False`不变。JSON内容、共享内存修正和kernel均不变，其他平台不新增读取入口。

复用现有独立容器及已通过的镜像/挂载门禁。只重载目标8111服务，保留用户当前0.91及其余启动参数，不操作源服务。正式GPQA按用户要求暂缓；本地精度技能显式选择`minimal-regression`，配置等价、数值与graph、服务健康和实际路径取证不是正式精度/吞吐验收。

| 项目真相/实现前契约 | 本轮范围 |
| --- | --- |
| 修改及只读边界 | 仅目标私有Plugin的adapter/apply/测试、FG-vllm MetaX配置读取/测试及当前启动脚本的目录export；vLLM、FlagGems、JSON和模型权重只读；备份旧路径作为参考。 |
| Build/验证/时限 | editable源码无需构建；CPU配置对照与pytest、相同seed完整MoE对拍、目标服务capture及至少两次replay、smoke/C8；单项600秒、服务就绪900秒。 |
| 数值契约 | 所有输入/输出dtype、shape、layout、alias、路由/激活、空输入和错误语义不变；不新增kernel或torch计算fallback。对照原函数与原配置，覆盖目标和边界M及非目标dtype/device/shape、量化block与embedded。 |
| 路径与autotune | 仅修改目录来源；命中走既有精确M覆盖，其余保持原默认/embedded路径。无新性能参数或NVIDIA路径改动，autotune/算子benchmark/deep_opt不适用，不声明性能收益。库workflow中的conv1d任务与本轮用户任务无关，optimization.md在当前仓库缺失；本轮不进入kernel设计。 |
| 操作记录 | 本地`/private/tmp/qwen3vl-moe-env-20261016/`，远端`commands/op003-env-config-20261016/`保存执行前脚本、备份及SHA；执行前检查8111空闲及无benchmark客户端。 |

最终改动及验证已完成。启动脚本只增加目录export，用户已自行调为0.91的内存参数及完整argv保持一致。Plugin移除目录包装函数与Path导入，apply直接导入库完整算子。库删除完整算子及选择器的公开`config_dir`参数与透传，环境目录只进入私有缓存加载器。JSON SHA256保持`ad5bf196af20be5f9bb2916527a9fd061172e7fbbc93ed329a3e925758654261`。

| 当前环境变量版本的验证 | 结果及边界 |
| --- | --- |
| 配置等价 | 155232组原目录参数入口与新环境入口的最终配置相同；硬件信息mock，不代表其他平台实测。5个Triton JIT AST不变。 |
| 完整MoE及graph | 同seed的12项M=0/1/7/8/9/16/32/48/64/65/128/8192逐bit相等；M8/64/65/8192分别完成两次replay并相等。 |
| 契约测试 | 库侧11项通过，覆盖未设置/空值、目录缓存切换、精确M、stage/dtype/shape、缺文件、embedded优先级、无效JSON及不读取vLLM变量；Plugin直接入口及原JSON范围两项通过。 |
| 工程检查 | Python语法、bash语法、两个源码仓库diff检查通过。目标formatter仍不可用，未安装依赖或构建wheel。首次数值命令误用无torch的系统python，在测试执行前失败；保留日志，改用原服务的`/opt/conda/bin/python`后通过。 |
| 当前服务 | 原8111空闲后仅重启该服务；保持GPU0/1、memory0.91、maxseq64、graph64、prefix cache关闭及其余argv。KV543712 tokens。单请求smoke及16请求/C8通过。 |
| 实际命中 | 两worker均从环境变量获得Plugin目录；完整算子调用未带`config_dir`关键字，实际GEMM2 M64选择stage1、embedded=False。完成capture及各16次原始graph replay；worker取证hook已恢复。 |
| 源保护 | 原容器四源码指纹不变；优化容器vLLM及FlagGems（含sort）指纹不变，原FlagGems选择和黑名单保持。 |

环境变量版本的命令、六文件原内容、增量补丁和SHA索引均在`commands/op003-env-config-20261016/`，其中`before.json`为本次回退起点，`candidate_v2.json`为最终写入内容，`*-final-env.patch`为最终增量补丁。回执为`results/op003env-config-equivalence.json`、`op003env-candidate-numerics.json`、`op003env-checks.json`、`op003env-health.json`。新服务manifest为`manifests/op003env-service.json`，SHA256 `0f495ee333fcef47611edf1a9ab1d5c4342175ed8169380cf8ae31d9bdd6b855`；健康回执SHA256 `1e7298fb7574175d1080ce31cf9e0992ee017d42a6758730c7ac039fbd505dc5`。详细路径/SHA写入state的`env_entry_revision`。

本次没有重测完整端到端吞吐，也没有进行正式GPQA；`minimal-regression=passed`，不签发正式精度gate。`pr_readiness=experimental`：通用环境变量加载能力仍是库侧依赖，原有共享内存修正继续保留，其他平台硬件和wheel/style仍未完整验证。回退只针对当前8111服务，核对实际进程/空闲状态与候选哈希后恢复本次六文件备份和原启动方式；不reset仓库，不操作源服务。下列初版迁移回执与18431回退描述均为历史记录，不用于当前服务操作。

### 按用户要求删除Plugin测试文件

2026-10-16已从当前优化容器`qwen3vl-p64k-opt-20261015`删除`/workspace/vllm-plugin-FL/tests/unit_tests/flaggems/test_moe_config.py`。删除前源码备份在`commands/op003-env-config-20261016/removed-plugin-test_moe_config.py`，SHA256 `370a2e20b23b23933f0877c50e1969da647f5239af77966d130c260dece84456`。文件不存在及Plugin diff检查通过；生产源码与MoE JSON哈希不变，FlagGems-vllm配置测试保留，没有重启服务或新增评测。原13项测试结果及完整源码manifest保留为删除前的历史证据，不重新标记身份。回执`results/op003env-plugin-test-removal-20261016.json`，SHA256 `33708ff23f5074d442db380074fc9f7f26d4c0bc73de62f5d84525c5fdcfca2f`。

## 首次目录迁移验证（历史）

| 范围 | 结果与边界 |
|---|---|
| 原/新最终配置 | 155,232组CPU/static对照一致；覆盖目标及边界M、设备名称、shape/dtype、量化block、两个GEMM stage、fast-path和embedded优先级。硬件信息为mock，不代表其他平台实测。 |
| 完整MoE数值 | MetaX GPU0同seed的12项M=0/1/7/8/9/16/32/48/64/65/128/8192，与迁移前逐bit一致，输出有限。 |
| 算子graph | M=8/64/65/8192各两次replay与输出一致；五个Triton JIT函数AST SHA完全不变。 |
| 单元测试 | 库侧4项配置目录、缓存隔离、回退及优先级测试通过；Plugin 4项平台路由测试通过，非目标平台使用mock。 |
| 工程检查 | 语法及两个仓库diff检查通过；package-data能发现资源。未构建wheel；目标未安装Ruff/Black/isort/flake8，未擅自安装。 |
| 实际服务 | 16请求/C8健康检查通过；两个worker实际传入Plugin目录，M64/GEMM2最终stage=1、embedded=False；完成capture，各16次原始graph replay，所有取证hook恢复。 |
| 保留配置 | memory0.91、maxseq64、graph64、KV543712 tokens；MoE调优值、sort int32及原黑名单保持。 |
| 源保护 | 原容器四源码树、JSON及sort哈希与初始状态相同。 |

这是配置归属整理，未声明新性能提升。此前P64K +10.92%属于迁移前源码身份，迁移后未重测完整端到端吞吐。正式模型精度按用户要求暂缓，没有签发精度或四场景验收gate。

## 产物、依赖与回退

远端根目录：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。命令、六个原文件备份、候选内容及两仓库增量补丁在`commands/op003-plugin-moe-config/`；命令与原生回执SHA统一记录在`state.yml`同名实验条目。

关键回执位于上述根目录的`results/`：`op003-config-equivalence.json`、`op003-baseline-numerics.json`、`op003-candidate-numerics.json`、`op003-engineering-checks.json`、`op003-plugin-config-health.json`、`op003-plugin-service-ready.json`、`op003-source-protection-recheck.json`。新服务manifest为`manifests/op003-plugin-config-service.json`，SHA256 `6e85eada73a1fdb705adf62f90a4dbbf80b68efa5ea173f81b2b820b39a8fd64`。

跨仓库依赖为库侧通用`config_dir`参数，不能只移植Plugin调用而遗漏接口。`pr_readiness=experimental`：这是相对既有私有改动的配对增量补丁，不代表继承的MetaX实现和新接口已完成上游评审。其他平台硬件、wheel及新身份完整性能检查仍为未测项。

回退仅操作本独立服务：停止18431服务，核对当前文件哈希后，从`before.json`或`before/`恢复六个原文件，再移除本实验新增的Plugin JSON、两个测试文件，使用原保留启动配置重启。不得reset仓库或操作源服务。备份不放回算子仓库；原有未提交改动继续保留。
