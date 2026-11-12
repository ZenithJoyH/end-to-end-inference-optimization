# review-001：mx-104 Plugin规范审查及公共算子平台配置

当前交付以用户最新要求为准：公共策略位于框架默认 `/opt/vllm-plugin-fl/vllm_fl/dispatch/config/metax.yaml` 顶层；启动脚本无VLLM_FL_CONFIG，旧外部YAML已归档。44项CPU通过，当前服务未重启，下一次启动自动加载。下文早期外置方案为历史记录，已被delivery04替代。

用户明确指定mx-104当前优化容器，并确认远程根/public-flash/jinghao/deepseekV4。本次为代码审查/配置整理，不恢复mx-103已暂停OOM任务，不运行性能测试。当前唯一容器deepseekV4-flash，ID5da4d97f，镜像70c61a83，服务正在运行。

## 优化方向与瓶颈依据

按2026-11-04最新Plugin标准A1–H10审查整个现有补丁，重点公共rms_norm及ATen黑名单的外部控制、配置覆盖语义与模型量化适配。数值/资源修复若涉及运行行为则单独记录，不能凭静态整理宣称通过精度/性能。

## 优化内容与适用边界

先只读采集，源服务/源码未改；保留Git HEAD/index/dirty diff与source清单。执行前保存commands/capture.py SHA `d597eb37d444396302b1157a99b5923d429f630f6cb2746ed0e4769a7f04ccdc`，只向新远程案例目录写入审查和备份材料，源码仅只读。

## 正确性与路径命中

not_run，待核验实际读取点和CPU配置路由测试。

## 性能效果

not_run，不签发任何加速/完整验收结论。

## 决定、风险与回退

审查中；不提交/推送，不擅自升级依赖或重启用户服务。

## 外部证据

/public-flash/jinghao/deepseekV4/20261104-dsv4-metax104-plugin-review

执行前内嵌AST及NUL分隔符预检调整，capture.py最终SHA `d597eb37d444396302b1157a99b5923d429f630f6cb2746ed0e4769a7f04ccdc`，替代未执行草稿。

采集控制首次因python -c无__file__在创建空任务根/commands后失败，尚未读写目标源码；保留空目录，不重复创建或覆盖。续采集脚本commands/capture-resume.py SHA `49c7fda3658625c2ea2e08bf7670971ae9b33ad3b8ffbee02b0d696ccdd7f37a`，执行前验证目录仅含commands及自身文件，从真实保存的文件入口运行。

配置外置候选：metax.yaml移除整个模型级overlay，load_platform_config去掉对dsv4_config的反向依赖；model initialize移除set_global_policy，复用既有PolicyManager；FlagOS/OOT blacklist缺省读取get_effective_config，保留显式env覆盖和append。外部完整YAML与旧模型生效配置字典逐项相等，不放宽旧三项排除。仅候选副本修改；测试覆盖模型开启/未开启、外部完整/空配置、env冲突/append、真实模型initializer重复调用不覆盖选择及非目标平台。
执行前保存candidate-source.tar.gz SHA `6fdd5d833ca48c8dbf17df22fa2e0e75aa27f28d2c1bd5eca3ab00b81fb117ad`。
执行前保存candidate-manifest.json SHA `4a9785f77bcc2e4222ef415f2ec2f6ffdfe3c10e8c992c63dd64c1437a0e6f87`。
执行前保存config-externalization.patch SHA `055b323450189f3b7ed472e1fd49668b6b339e8b94cd842842ccb2866d1ce25d`。
执行前保存dispatch-metax.yaml SHA `a4d2513dfd3d17295bfb232b4b37e56481ae8f60e4f0834383dca9539e979ec2`。
执行前保存validate-candidate.py SHA `10bb0b5ab1a9c3a9766961f66ba6670645c5b770daa44a8ffd7ac0155b941fe8`。

候选01原生CPU pytest43passed/0fail/0skip，CUDA未初始化；Ruff/pre-commit容器未安装。按目标Ruff0.14.0在本地临时目录检查，新增测试修正loop lambda绑定并完成ruff check/format。最终候选02只改变测试格式及该闭包，生产三文件内容与候选01相同，另跑同43项验证，不拼接旧测试冒充最终代码结果。
执行前保存candidate02-source.tar.gz SHA `f8670ef9e4d5287d298ccece603390865328efe27dcccc217f5deb0a3bada682`。
执行前保存candidate02-manifest.json SHA `dae8037f27dcb621f2561b20b059c178055c329c4b2d0031714cb5b899a70b22`。
执行前保存config-externalization-final.patch SHA `ce53c3934d1b39cf055af2de2bb7d8cdcaf860414342012961220fa0657c4241`。
执行前保存validate-final.py SHA `6a041b83332865eb55f2814add2940cdd66a89d091c4fbd29895188f9f5eef10`。

配置文件交付前记录commands/install-config.py SHA `1432f8e616375102969279d3bed030a55f8dc350e74c069bff92002b0ea2fcb2`：最终候选43项CPU通过后，核验源631文件、Git HEAD/index及API精确身份/health未漂移，仅写声明的三生产+一测试文件；新建外部dispatch-metax.yaml并在原start-model.sh加单一VLLM_FL_CONFIG引用。保持原启动参数、env其它值和服务进程，不重启、不将其冒称已加载新源码。写前备份，失败精确回退本次文件。当前运行进程持有原模块/策略；本次新配置下次启动生效，GPU/graph/精度/性能未重新验收。
执行前NUL分隔符改用bytes([0])避免内嵌转义歧义，install-config.py最终SHA `3a96215a6a0cdde5bfddec973994a98d2a742bf91ab621f40ce4c64df071aa10`，替代未执行草稿。

首次delivery01在保存候选文件副本时，shutil.copy2复制扩展属性遇到共享文件系统EIO；发生在任何Plugin/外部配置/启动脚本写入前。保留delivery01和控制日志，不把它记为模型失败。新commands/install-config-v2.py SHA `93d4b603739298a5c1538befae96cfbd2df4962f9d42316f868b686be956eb69`仅将不必要的xattr复制改为字节保存，并使用全新delivery02；全部源SHA/API/index门禁再次检查，原部分产物不覆盖。

## 当前全部生产修改扫描结果

扫描基准HEAD `a696859b9aa528dfd5b21f5da3403fdc16bac4cd`（Sunrise graph mode #569），不是当前上游main的新revision；本次不升级依赖或同步代码。初始34个修改/新增文件，其中28个生产Python；AST语法全通过。测试/配置/调优JSON单列，不用文件数替代职责审查。

### CFG-01 / P1 / fixed_files_installed_next_launch

条款：D1, D2, D4, F1。

模型开启状态反向改变通用配置，且initializer强制set_global_policy覆盖外部dispatch选择。

整改：移除模型overlay及强制policy写入，复用PolicyManager及外部完整YAML。

涉及：`vllm_fl/dispatch/config/metax.yaml`, `vllm_fl/dispatch/config/utils.py`, `vllm_fl/configs/deepseek_v4_metax.py`。

### CFG-02 / P1 / fixed_files_installed_next_launch

条款：D4, F1。

FlagOS/OOT blacklist getter默认只读platform，VLLM_FL_CONFIG无法统一覆盖这些读取点。

整改：两getter默认使用get_effective_config；env替换、append、whitelist冲突语义保持且有实际测试。

涉及：`vllm_fl/dispatch/config/utils.py`。

### OWN-01 / P1 / needs_revision

条款：A1, A3, A4, D3。

四文件含14个Triton数值kernel（attention、MQA logits、score Top-k）；评分/排序不属于请求metadata。

整改：迁移到FlagGems-vllm vendor/metax公开API，保留Plugin中的请求/TP通信/workspace编排，逐项同步独立数值/graph测试；本次未搬运/改数学。

涉及：`vllm_fl/ops/deepseek_v4_metax/decode.py`, `vllm_fl/ops/deepseek_v4_metax/prefill.py`, `vllm_fl/ops/deepseek_v4_indexer_decode.py`, `vllm_fl/ops/deepseek_v4_indexer_prefill.py`。

### DISP-01 / P1 / needs_revision

条款：A1, B1, B3, D3。

embedding mask、dynamic INT8、silu clamp等路径直接引用算子私有模块或厂商函数；vLLM融合API仍调用FlagGems非ATen入口；通用后端实现直接绑定MetaX专属私有mHC函数。

整改：先在FG/FGV补齐所属公开API及vendor注册，再通过既有CachedOp/dispatch调用；黑名单仅控制其实际读取的ATen/OOT路径，不能宣称它能禁止这些显式私有调用。

涉及：`vllm_fl/ops/deepseek_v4.py`, `vllm_fl/quantization/w8a8/deepseek_v4.py`, `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py`, `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4_attention.py`。

### STATE-01 / P1 / needs_revision

条款：E2, E3, E4, F3。

_SPLIT_TOPK_BUF_CACHE为模块全局可变Tensor scratch，key缺少layer/request/stream所有者；_PAIR通信组懒建无统一销毁；KM缓存key只有shape/topk缺少设备与runtime身份。

整改：workspace由层/框架manager预算并在capture前准备，明确并发/stream归属；通信组按worker/TP生命周期初始化与释放；KM key按实际选参依赖补齐。仅静态风险，不是已证实OOM根因。

涉及：`vllm_fl/ops/deepseek_v4_metax/decode.py`, `vllm_fl/ops/deepseek_v4_indexer_prefill.py`, `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py`。

### INIT-01 / P1 / needs_revision

条款：C2, C3, E4, F1。

register_config连续写HF registry/MODELS_CONFIG_MAP/ModelRegistry，缺少完整预检和失败回退；initialize在后续导入/配置可能失败前已切换logger/library launch policy；厂商补丁入口有模块导入副作用。

整改：原子预检和安装，失败恢复已变更对象；增加第二/第三步失败测试。不要为了代码收敛删除必要的循环依赖规避入口。

涉及：`vllm_fl/configs/deepseek_v4_metax.py`, `vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py`。

### QUANT-01 / P1 / needs_revision

条款：B3, H2, H4, H5, H8, H9, H10。

quant_config通过__class__原地替换；kernel.can_implement主要验证bool字段和句柄存在，AZP/bias所需ScaledGEMM能力检查留到量化之后；缺少当前公开依赖下完整层选择/scale/TP/负例及graph支持矩阵。

整改：沿现有量化扩展点表达方法/能力，前置验证所需vendor API及契约。当前仅声明TP8/PP1/INT8/FP8 cache/无MTP范围；不能推断静态、非对称、EP、FP4或MTP已通过。

涉及：`vllm_fl/models/deepseek_v4.py`, `vllm_fl/quantization/w8a8/deepseek_v4.py`, `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py`。

### DELIVERY-01 / P1 / needs_revision

条款：D3, F4, F7, G1, G2。

本地editable FG/FGV私有扩展缺少对外固定依赖交付；部分从原生Triton私有fn拆tuner/launch；实际28生产文件显式Ruff扫描102条既有问题，规则中的vllm_fl exclude不能当作全生产代码lint通过。

整改：先公开算子API/测试及固定版本，再接Plugin；整理真实入口/依赖/CI及版权格式。当前新增测试Ruff0.14通过，未新增生产诊断；没有一键删除unused import以免破坏注册副作用。

涉及：`pyproject.toml`, `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py`, `vllm_fl/ops/deepseek_v4_metax/policy.py`。

## 逐文件去留与职责

| 生产文件 | 本轮决定及后续边界 |
|---|---|
| `vllm_fl/__init__.py` | 保留限MetaX的模型注册接线；原子注册/导入副作用按INIT-01补测 |
| `vllm_fl/configs/deepseek_v4_metax.py` | 删除模型强制dispatch策略；保留架构别名及严格TP8/PP1/graph输入校验，注册回滚待修 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4.py` | 改为公开API薄调用；去MetaX私有mHC直连与数值路由，CFG外置不是完整dispatch整改 |
| `vllm_fl/dispatch/backends/flaggems/impl/deepseek_v4_attention.py` | 融合FP8/KV读写从FG非ATen接口迁FGV；纯metadata helper可保留框架 |
| `vllm_fl/dispatch/backends/flaggems/register_ops.py` | 保留统一注册/去重；具体能力不能仅凭import/hasattr宣称数值和graph可用 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/__init__.py` | 薄vendor package可保留，不放数值kernel |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/indexer.py` | 保留真实deep_gemm vendor adapter；缓存目录环境写入改为现有初始化生命周期，不放调用热路径 |
| `vllm_fl/dispatch/backends/vendor/metax/impl/dsv4/mctlass_ops.py` | 真实vendor API适配可保留；移除模型绕分发直调、加强ScaledGEMM能力及KM缓存key/句柄释放 |
| `vllm_fl/dispatch/backends/vendor/metax/metax.py` | 保留真实MACA torch.mm BF16→FP32适配与fake schema；非目标输入能力/参数回归待补 |
| `vllm_fl/dispatch/backends/vendor/metax/patches/__init__.py` | 保留统一patch入口；清理全局import副作用及无条件has_triton_kernels=False，补能力/范围判断 |
| `vllm_fl/dispatch/backends/vendor/metax/patches/fix_standalone_compile.py` | 保留torch原生artifact capability判断的必要兼容层，按C2/C3补重复安装/失败测试 |
| `vllm_fl/dispatch/backends/vendor/metax/register_ops.py` | 保留vendor注册桥；补真实入口impl_id与异常不重试测试 |
| `vllm_fl/dispatch/config/utils.py` | 移除模型反向依赖，修正外部FlagOS/OOT配置读取，完整/空YAML及env优先级测试通过 |
| `vllm_fl/dsv4_config.py` | 保留框架模型能力/shape的不可变进程策略；不能再承载公共op黑名单或kernel默认选择 |
| `vllm_fl/models/deepseek_v4.py` | 保留原生模型/加载复用；量化__class__切换应按H2/H4整改；无MTP显式拒绝有边界 |
| `vllm_fl/ops/deepseek_v4.py` | 保留embedding编排；私有数值接线和自建选择链迁移到公开dispatch/API |
| `vllm_fl/ops/deepseek_v4_attention.py` | 保留原生attention/cache/metadata构造及graph边界；数值API依赖归属需整改，不能为少文件删除必要构造 |
| `vllm_fl/ops/deepseek_v4_indexer_decode.py` | MQA logits/score Top-k四kernel迁入FGV，Plugin只接公共入口 |
| `vllm_fl/ops/deepseek_v4_indexer_prefill.py` | 两个数值kernel迁FGV；query-row sharding通信及请求映射保留框架，补生命周期/退出 |
| `vllm_fl/ops/deepseek_v4_metax/__init__.py` | 随数字kernel迁移后评估删除空package，不独立保留平行算子库 |
| `vllm_fl/ops/deepseek_v4_metax/decode.py` | 四个attention/reduce数值kernel迁FGV；workspace ownership按STATE-01重构，非OOM归因 |
| `vllm_fl/ops/deepseek_v4_metax/policy.py` | kernel tile/warp/stage及私有tuner重建归算子库；框架只传已声明能力/执行参数 |
| `vllm_fl/ops/deepseek_v4_metax/prefill.py` | 四个数值kernel迁FGV；当前compute-stream TP P2P编排保留Plugin，不把launch当完成 |
| `vllm_fl/ops/fused_moe/router.py` | 保留input_ids/hash路由/缩放语义经CachedOp；通用调用方和非目标平台需实际回归 |
| `vllm_fl/ops/sparse_attn_indexer.py` | 保留metadata/KV-spec及native非MetaX/FP4边界；反量化和score Top-k计算迁FGV，不能一概称metadata |
| `vllm_fl/platform.py` | 保留平台能力入口configure_for_model调用；当前无新平台/CI功能，避免扩大全局默认 |
| `vllm_fl/quantization/w8a8/deepseek_v4.py` | 保留get_quant_method、native workspace/activation/reduction接线；MoE实际计算通过公开dispatch/vendor API，补H组支持矩阵 |
| `vllm_fl/worker/worker.py` | 保留spawn worker初始化顺序；只在目标模型启用，失败回滚/重复初始化补测 |

## 公开配置契约与验证边界

外部`VLLM_FL_CONFIG`完整替换内置配置文件；不隐式合并list。既有PolicyManager在显式YAML下整份选择；未指定外部文件时沿用平台默认及原env/op-config优先级。FlagOS显式env blacklist整体替换配置blacklist，APPEND顺序去重追加，whitelist与显式blacklist同时设置报错，whitelist单独设置覆盖排除；OOT显式env黑名单维持原优先级。旧模型生效配置与新外部完整YAML字典相等，rms_norm仍reference、router仍vendor:metax优先、topk/masked_fill/masked_fill_仍排除，控制责任已在部署方。

43项CPU实际配置/PolicyManager与模型initializer接线测试通过（数值库setup为mock），并非GPU数值或graph证据。28生产文件AST通过；显式Ruff扫描原/候选均102条既有问题、无新增诊断；新增测试Ruff0.14检查及format通过。生产目录被上游pyproject默认exclude，完整pre-commit未安装未执行，不能称整个现有diff符合F7。无新GPU/graph/GPQA/端到端性能数据，不继承mx-103分数为mx-104当前gate。

下一顺序：先处理FGV公开API/14数值kernel归属与固定依赖，再按入口拆dispatch和workspace所有权，最后原子初始化/量化矩阵与完整硬件回归。每一步单独候选、独立reference、更新输入至少两次graph replay；高风险改动须正式精度及目标E2E回归。当前不恢复OOM定位，不改数学实现或安装新依赖。全补丁`pr_readiness=needs_revision`。

## 配置整理交付结果

2026-11-04 12:06:46上海，delivery02/result.json确认files_installed_next_launch。实际容器Plugin只改三生产文件及对应测试，其他631清单内文件保持；Git HEAD/index未改。新增外部配置`/public-flash/jinghao/deepseekV4/dispatch-metax.yaml` SHA `a4d2513dfd3d17295bfb232b4b37e56481ae8f60e4f0834383dca9539e979ec2`；原`start-model.sh`仅增加单一VLLM_FL_CONFIG引用，SHA `4f0a396266f703bb52c0f4932ef36a1f20c3a9cdf22830f38f3decc5a15418bf`。当前API64785/ticks1202402350及argv仍相同、health200，未重启/未新绑定运行时；下次启动加载新配置，不把当前旧模块进程当新代码GPU验证。备份delivery02/backup保留四Plugin文件与原脚本，原源tar完整保留；未提交/推送。

正式完整现有diff仍needs_revision；本轮保留的是配置链路和部署外置，数值归属、统一dispatch、workspace/通信组生命周期、原子注册和量化支持矩阵尚未整改，不宣称已全部符合规范。
最终核验/审阅材料final-review.py SHA `43309eb7839a118b4135814bbec079609d283efd9b4fa448970ac63dde6d505e`。
最终核验/审阅材料review-findings.json SHA `fba05a174f00af0f8a120f3106f7598136a4245eb4aeff3a3f0b68c13639070a`。
最终核验/审阅材料ruff-source.json SHA `1cf03be6b913e101afdc5781f684cc9972ed335faf350ff6264e86973e4f488d`。
最终核验/审阅材料ruff-work.json SHA `aed7bb20c49238a603b6bed287c6350505482bfe97f63cf2c9c982406c3fa7d1`。

最终12:12:08上海核验：安装后的`/opt/vllm-plugin-fl`实际CPU配置路由返回rms_norm=reference、router=vendor:metax→flagos、FlagOS黑名单topk/masked_fill/masked_fill_及OOT原masked_fill两项；CUDA未初始化。全部源码与声明四文件新SHA一致、其他文件保持，Git HEAD/index不变，补丁reverse --check通过；当前API身份/argv相同且health200。`final-review-result.json`为passed_scoped_configuration_review，43测试0失败0跳过；整体diff仍needs_revision、服务未重启/未rebind。本地本案例记录校验0错误，全仓另有85项其他记录错误及257项历史过程产物警告，未修改无关记录。

## 用户补充：FlagGems-vllm现有修改核验（只读）

mx-104同容器`/opt/dsv4-sources/FlagGems-vllm`，HEAD `fa78ddee4c3e78ce5047213ff0ef02acff34b2d5`、branch upgrade/20261020-latest。相对HEAD共16个唯一变更文件，10生产Python+1调优YAML，另2测试+2benchmark+1集成文档；合计+1484/-18行。大头是新增MetaX mHC pre749行、alignment221行，以及量化78/launch38行。这些属于此前适配/优化，本次Plugin配置整理未新增FGV改动。

核心为mHC融合及Split-K、E256路由对齐、tensor-limit SiLU graph接线、动态INT8数值顺序兼容与JIT launch cache。生产改动放在算子库本身合理，不能为了压缩Plugin文件数就把库内必要kernel删除。后续需按公开API/vendor目录/独立数值测试/graph/固定依赖规范收敛，而不是恢复到未适配HEAD。

需分开评估的外围项：当前Plugin gather接线已复用vLLM原生，因此FGV gather改动不应算当前DSV4路径收益；GDN改动仅把导入即全局编译器补丁改成显式函数，非DeepSeek GDN计算；code_cache仅分离FLAGGEMS_VLLM_CACHE_DIR读取，公共基础设施主题应单独评审。测试/benchmark不是额外运行路径，不能只为文件数删掉。DSV4_INTEGRATION文档需按长期接口信息与过程记录拆分。

三个AM文件quant/launch/alignment各是同一个新增文件的两层差异，不是另三个文件。工作区相对index包含重要后续修正：quant适配Triton semantic extern、动态M及warp64的8warps限制；launch key不再按动态标量具体值特化而按整数类型；alignment N/CAP/ECAP转runtime。Git提交以暂存内容为准，若直接提交当前index会漏掉这些后续修正；源码加载与Git暂存区无关，当前进程是否已加载哪一版仍需运行证据，不能只看git status推定。本轮没有git add/reset/commit，也没有修改FGV或启动测试。

## 用户修正：使用框架默认YAML自动生效

用户明确要求撤销对部署外部YAML的依赖。沿Plugin既有自动平台入口把相同策略放到dispatch/config/metax.yaml顶层，删除start-model.sh的VLLM_FL_CONFIG export；不恢复deepseek_v4_int8模型分支，也不恢复模型set_global_policy。仅该容器MetaX平台默认改变：rms_norm=reference、router vendor:metax→flagos、FlagOS三项排除，OOT保持原两项；当前已验证模型选择结果与之前完整外部YAML相同。其他MetaX模型将共享平台默认，尚无其GPU性能结论；非MetaX文件不改。显式用户环境/YAML覆盖仍可选。

候选03修改默认配置与对应测试；增加模型initialize在外部文件未设置时也不覆盖平台默认的参数化回归，预期44项。原外部文件按精确SHA移入回退备份，启动脚本原参数保留，当前服务不重启，新启动不依赖外部路径。
执行前保存candidate03-source.tar.gz SHA `2fe81e5f45995eae3d70b317eec65d9ba0f54ccb3b8dd7165decb711fa83d63d`。
执行前保存candidate03-manifest.json SHA `a7c79cc02e165327391f0a4bee7d1e930f70fe863e336626dcf6c8dfa6e1935f`。
执行前保存platform-default.patch SHA `dacf4ac25a32cbdad788af35325f8287536ddba6343d847fffa22b113cd7551d`。
执行前保存validate-platform-default.py SHA `a5a3d6f2f99b7a7f8b49b5fde637cc227d363ef1e755aaf265ea52de7ac1aa3d`。
执行前保存commands/install-platform-default.py SHA `a7c2732c3afed45eecf0064b129df3d4f82cae948d0e54389ed3337c2ccadf0d`：44CPU通过后检查当前源与上一交付SHA、精确API/argv/health/HEAD/index，只改平台YAML与测试，移除启动export；旧外部YAML精确SHA归档到delivery03/backup。验证installed无VLLM_FL_CONFIG时从默认metax.yaml解析，CPU平台身份mock明确披露；其它库/源文件不动，不重启服务，异常只回退本次文件。

默认配置delivery03的源码/API/CPU路由检查均执行完成，但CPU首次平台发现日志写stdout，使控制器直接json.loads整段输出解析失败；失败路径已精确回退两Plugin文件、启动脚本和外部YAML，未重启服务。保留delivery03/failure.json与备份。新commands/install-platform-default-v2.py SHA `750e07d4b1a5498d62eba9c2baec12f7a7ad849414b0193646c99b4ca909eb39`使用全新delivery04，保存完整cpu-route.log并从带目标字段的JSON行解析，重新执行所有门禁，不覆盖旧回执。

12:21:32上海最终核验：delivery04/result.json为framework_default_installed_next_launch，平台默认YAML和对应测试已写入；start-model.sh恢复原3export及全部原参数，SHA `f0555064d6f6868154940753b511c859b08bdf9efdd84841d6c33d2d8a6ed142`。旧dispatch-metax.yaml已精确归档至delivery04/backup，原路径不再依赖。44项测试通过，安装后的真实配置函数在无VLLM_FL_CONFIG时解析到默认metax.yaml，返回相同rms/router/blacklist值；CPU平台身份为mock、未初始化CUDA。精确API/argv/health相同，当前进程未重启/未rebind，其它源文件/依赖不改。该策略为MetaX平台默认而非模型分支，其他MetaX模型尚无新增硬件回归结论。
