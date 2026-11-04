# maint-011：FlagGems-vllm完整补丁收敛

用户要求完整检查并收敛库改动。范围为当前隔离容器`qwen3vl-p64k-opt-20261015`实际导入的`/workspace/FlagGems-vllm`，相对HEAD f6fdb9b逐文件核验tracked diff和全部untracked内容；不回写独立的public-flash副本，不修改Plugin、vLLM、FlagGems、JSON或启动策略，不重新加入用户已删除的测试/perf。

## 编码前审查和契约

| 保留部分 | 当前必要性与本轮处理 |
| --- | --- |
| 两处ops导出+generic采样API | 根目录已恢复HEAD，通过ops导入/运行时vendor替换提供公共显式API。generic仅identity/unsupported，MetaX保存实现，保留平台边界。不新增ATen注册，因其是Plugin直接调用的专用API。 |
| MoE generic/MetaX入口 | 继续变量存在时读取外部配置，否则走原embedded/default。将重复设备名/别名提取集中到共同工具，入口仅保留目录分支与调用。 |
| JSON工具 | 仅库自身runtime元数据和标准库，无vLLM/Plugin导入或框架路径探测；硬件名优先/vendor别名、dtype/block/H200规则与异常行为保持。文件缓存以完整路径区分目录/shape/dtype/设备，修改内容仍需重启/清缓存。 |
| MetaX共享内存修正 | 真实device上限、stage可减至1、paired保护和FP32字节数是已验证的兼容修复，不能为了减少行数撤销。原tile与全部kernel计算体保持。 |
| MetaX采样 | BF16精确检测/FP32 radix两路径及mask均保留，仅去除两个未用kernel参数；计算体AST保持。历史来源保存在案例，不把临时文件历史当运行逻辑。 |

| 项目真相/验证 | 实现前冻结 |
| --- | --- |
| 可编辑 | 上述7个源码文件；无新增文件种类，不改库HEAD或提交/push。 |
| build/autotune/benchmark | editable Python+已有Triton；本轮不调tile/算法，无新autotune和性能目标，benchmark/deep_opt不适用。 |
| baseline | gems-opt/c3c5f5ab2及原PR595 JSON；MoE使用既有op006可信输出张量及SHA作逐bit参考，采样使用原参考函数，验证脚本均在案例外部。 |
| 数值与shape | MoE BF16/FP16各M0/1/7/8/32/36/37/64/65/128/1024/7393/8192/16384，E128/K2048/N384/topk8；同输入逐bit，独立数学参考沿用BF16 atol.004/rtol.016、FP16 atol.0005/rtol.003。 |
| 路径 | 外部/默认配置、目录与设备缓存隔离、元数据错误、禁止vLLM导入；采样原49项+实际hook47项+9边界+Plugin路由17项，不改容差。 |
| graph/服务 | MoE8组各2replay、采样两shape三种值域各2replay；原8111服务TP2 capture/各16replay、smoke1+C8请求16，temperature.7/k20/p.8。只重启本案例空闲服务，源8000保护。 |
| 通过/停止 | 外部契约及最小回归全部通过、最终源码/导入命中一致；失败先诊断/修正或回退，不叠加性能调优。单项900秒、启动900秒；GPQA按用户指令暂缓。 |

本轮使用本地精度技能minimal-regression，不生成正式gate，也不以历史+10.92%或早期采样microbenchmark声称最终组合收益。最终应只保留7个功能源码文件的差异，列出完整combined diff（含新文件），备份前后补丁和回退条件。

原始证据在`commands/maint011-convergence-20261016/`、`results/maint011-*`、`logs/maint011-*`。before.json SHA256为`80af3dc5e04f184db8a534abf166be24014fac270005f9d09756d7bbfb3e507a`。所有检查测试保存在外部案例，用户删除的库test/perf不恢复。

## 验证入口修正

事件`maint011-validation-path`归类`measurement-invalid`，不属于数值失败：`sampling_tests.py`在49项采样通过后引用已不存在的Plugin测试路径，pytest以4退出且未采集测试。当前任务before快照已表明Plugin没有该测试；其删除是本轮之前事实。保留原`maint011-sampling_tests.log`、`maint011-plugin-routing.log`及原脚本，不覆盖失败证据。

修复仅将op008归档的17项路由测试放入案例外部，测试体完全相同，仅将基于`__file__`的定位改为实际Plugin绝对路径；不向Plugin或算子库恢复文件。`sampling_resume.py`复用本轮已完成49项结果并继续17/47/9项。没有数值容差、生产代码或性能参数变更；后续必须全部通过才恢复服务验收。

## 共享副本状态变化

`validate_sources.py`已通过私有4仓库指纹、7文件范围、根init和kernel AST检查，随后在共享副本校验处报FileNotFoundError。复核发现`/public-flash/jinghao/qwen3-VL/FlagGems-vllm`整目录在Host和两个容器中均不存在；任务前before.json保存的该副本文件SHA仍在。本次apply脚本仅向`/workspace/FlagGems-vllm`六个精确路径write_text，无删除、重命名或共享路径写入；此变化不能伪报为“共享副本未变”。已异步向用户核实其是否主动清理，不恢复或创建该目录。

后续`validate_sources_v2.py`保持私有源码所有断言不变，将缺失整目录作为明确的shared_copy_state记录。若目录存在但文件内容变动，仍必须匹配原SHA，否则检查失败。服务实际导入私有路径，故此项无需阻止其独立验证/恢复；源容器私有4仓库保护另行严格校验。原失败日志保留。

## 最终源码审查

已检查tracked diff及全部untracked文件。相对HEAD `f6fdb9b120787e12892ac67e54979cbf829c7d64`只保留以下7个源码文件（4 tracked、3新增）；本轮只写其中6个文件，generic采样stub未改。根目录`src/flaggems_vllm/__init__.py`与HEAD逐字节一致。完整补丁包含新增文件，避免仅使用git diff遗漏它们。

| 文件（根目录`/workspace/FlagGems-vllm`） | 必要职责及最终处理 |
| --- | --- |
| `src/flaggems_vllm/ops/__init__.py` | 通用API的import/ops导出，移动到现有import组；根init沿用既有从ops绑定机制，不重复加root __all__。 |
| `src/flaggems_vllm/ops/top_k_top_p.py` | 通用无过滤identity与不支持输入NotImplementedError契约；非MetaX导入不要求MetaX kernel。 |
| `src/flaggems_vllm/runtime/backend/_metax/ops/__init__.py` | vendor替换通用API，沿用backend ops导出，不新建dispatch。 |
| `src/flaggems_vllm/runtime/backend/_metax/ops/top_k_top_p.py` | 保留采样实现、元数据边界和device guard；删除_hist_prefix.M、_mask_sorted_top_k.top_k两个未用参数及实参；14个JIT计算体AST完全相同。 |
| `src/flaggems_vllm/utils/moe_config.py` | 唯一外部JSON读取器，集中设备名/别名解析；按文件路径缓存，保留硬件名优先、native格式、dtype/block/H200与错误行为，无vLLM/Plugin依赖。 |
| `src/flaggems_vllm/ops/fused_moe.py` | 外部目录配置分支仅一次load调用，未设置变量时原embedded/default逻辑保持；9个JIT完整AST不变。 |
| `src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py` | 同上入口简化；保留真实共享内存上限、stage可减至1、paired容量保护和FP32元素字节数修复，5个JIT完整AST不变。 |

既有MetaX容量保护处理已复现的编译资源超限，不能为了减少行数移除。generic API与vendor ops入口分别负责非目标导入/显式API/vendor绑定，均有必要。没有模型路径、名称、Host或PID选择分支。

原仓库`ops/indexer_k_quant_and_cache.py`仍有继承的可选`vllm.platforms`导入，本次未改该文件；无vLLM依赖的结论仅针对新增MoE/采样生产路径。JSON加载不探测vLLM/Plugin安装路径，库中不放模型JSON；Plugin内原文件与目录变量不变。

## 已完成的算子验证

- 外部pytest：配置契约20、原采样49、路由17、实际Plugin hook47均通过；hook另有2项不属于该调用面而预先deselect。
- MoE BF16/FP16共28形状点与op006保存输出逐bit一致，最大差值0；独立数学参考6点沿用原容差，8组graph各2replay通过。
- 禁止vLLM导入的独立进程成功读取原M64配置，零次尝试导入vLLM。非目标设备名/缓存用mock元数据验证，不代表NVIDIA硬件通过。
- 9项边界的实际Plugin/API/reference调用计数、原地同对象与逐bit输出通过；2个采样shape在BF16可表示/FP32/正值ties三个域各2replay通过。
- 四仓库指纹重建确认仅6处私有库内容变化，Plugin、vLLM、FlagGems及JSON保持任务前状态；已删除的库MoE测试和采样test/perf未恢复，Plugin已不存在的路由测试也未恢复。
- syntax、git diff --check通过。black/isort/flake8在目标环境不可用，未声明完整lint通过。本轮无调参、benchmark、端到端收益或正式精度结论。

完整补丁：远端命令目录中的`final-flaggems-vllm.patch`，SHA256 `95b996201eda82154c5bc4c85ee6c87bb7bad1a4b568a6209b5d61c827e69107`，相对HEAD +531/-9（包含既有新增采样实现）。本轮收敛差异另见`convergence-only.patch`。

回退：先停止本案例8111服务，再运行已保存但本轮未执行的`rollback.py`；它要求6文件仍匹配candidate后才恢复before快照，不使用git reset，不恢复已删除测试，不动其他仓库或共享目录。恢复原argv/env后需补最小回归。

运行版本：torch 2.8.0+metax3.7.0.7，FlagTree 0.7.0.post2+metax3.6；editable实际导入身份以四仓库git SHA为准，distribution metadata不代替源码revision。

## 服务回归与结论

8111服务API PID326427，以任务前相同argv/env语义恢复，TP2/GPU0,1、memory0.91/maxseq64/graph64不变。FULL_AND_PIECEWISE capture通过，2个worker各16次原始graph replay通过；smoke1及C8请求16共17次均有非空响应，结束后running/waiting均为0。两个worker在启动预热实际调用MetaX库采样（同对象原地返回）、FlagGems-vllm完整fused_experts_impl及两段GEMM，原M64JSON配置/stage3和SHA不变，有限观测hook均恢复。采样命中证据来自启动预热，不能误记为HTTP阶段重新安装观测。

最小回归`executed_passed`，源8000容器私有4仓库与op003保护快照完全一致，本次未重启或写回源容器。当前实际导入的私有Plugin/vLLM/FlagGems与任务前完全相同，库仅上述6处预期变化。2026-10-16用户明确确认已主动清理共享public-flash副本，此项归类为预期的用户清理，已关闭待确认状态，无需恢复。保留原始核验过程及封存回执，实际使用私有/workspace副本。

决定：保留收敛补丁。`pr_readiness=experimental`：未做非MetaX硬件、完整lint、正式GPQA及新端到端性能，删除测试是用户要求，外部复现脚本和可信原始证据保留。当前清单`manifests/maint011-service.json`，最终源码回执`results/maint011-validated-sources.json`，服务回执`results/maint011-health.json`。不以历史性能数字为本轮代码的收益证明，不修改acceptance gate。

| 验证范围 | 证据类型及结果 | 未测边界 |
| --- | --- | --- |
| MetaX BF16/FP16 MoE与FP32采样，支持shape及边界 | hardware：executed_passed，数值、原地语义、fallback及graph | 不宣称所有量化格式或其他模型设备运行通过 |
| native JSON格式/设备名称/目录与device缓存隔离 | actual native对照及mock元数据：executed_passed | NVIDIA及其他平台硬件not_run |
| TP2 graph/worker/服务生命周期 | hardware：executed_passed，capture/2worker各16replay/17请求；有限hook恢复 | 正式GPQA及无profiler吞吐not_run |

最终证据索引`commands/maint011-convergence-20261016/evidence-index-v2.json`，SHA256 `6b3663e08224fd600f8dfe08a0196d946b37dc9d8538dcf50dc829543e54309e`。使用关闭的服务日志快照，排除仍运行的服务日志及封存命令自身日志；旧索引保留但被v2替代。服务清单SHA `b9619fe6d7afca137d1c85544ce344dec2f9edefa626dda9bb29a6dbb6ad1ccf`，服务回执SHA `56f8d2d218aa661af2fc48ef3f03586b82b0e615bf86cedc7e60e6072b184c73`。完整命令/补丁/回执路径和SHA已写入state.yml。
