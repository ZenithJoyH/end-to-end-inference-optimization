# op-005：PR595 MoE JSON共用vLLM加载器

后续用户指出算子库不应反向依赖vLLM。[op006](op-006-independent-moe-json-loader.md)已移除本记录的原生函数委托，改为库内独立格式兼容加载器，PR595 JSON与FlagOS计算保留。本页记录当时实现和验证，当前服务以op006清单为准。

用户明确要求使用PR595原始JSON，FlagGems-vllm与vLLM共用同一配置格式/读取逻辑，计算仍走FlagOS。这覆盖此前“保持精确M/仅GEMM2范围”的要求；本轮配置数值和覆盖范围有意变化，不称等价迁移或已取得性能收益。

目标仍为mx-59现有独立容器`qwen3vl-p64k-opt-20261015`，Plugin基线为024plugin-opt/08da21cb3960。不新建性能任务，不修改源容器或无关服务；vLLM及FlagGems源码只读。库的generic与MetaX get_moe_configs在设置`VLLM_TUNED_CONFIG_FOLDER`时延迟导入并复用vLLM原生读取函数，把库内bf16/fp16标记映射为原生无dtype后缀；未设置该变量时保留原embedded/default逻辑。返回的表继续经既有最近M逻辑选择完整配置，两个GEMM使用同一表。移除此前精确M stage loader及其专用变量/JSON，Plugin仅保存PR原始文件和打包规则，不增加调用包装或测试文件。

| 实现前契约 | 范围 |
| --- | --- |
| 修改边界与build | FG-vllm generic/MetaX配置读取、原配置测试；Plugin资源/打包；用户启动脚本变量。editable源码无需构建，不改kernel、Worker、apply、权重或tokenizer。 |
| 加载语义 | 同一原生get_moe_configs，沿用文件名、设备名、block shape、triton_version处理、用户目录/内置目录优先级、batch invariant、缓存和异常语义。计算实现仍是FlagGems-vllm。 |
| 激活路径 | 文件表走现有tuned/embedded配置分支，包括既有融合路径选择；验证实际两个GEMM配置与数值，不为保持旧阶段路径而忽略JSON字段。 |
| 正确性 | 本地精度技能minimal-regression：配置对照、BF16/FP16完整MoE与数学参考，目标及边界M/空输入，graph至少两次replay，实际graph服务smoke/C8。固定BF16 rtol0.016/atol0.004、FP16 rtol0.003/atol0.0005，不按结果放宽。 |
| 非目标范围 | 不扩展其他vendor私有MoE副本；generic路径静态/契约检查不能代表其他平台硬件通过。未设置变量不引入vLLM运行时依赖。 |
| 算子协议 | 库AGENTS/workflow已读；本轮只做配置入口，不新增kernel或torch计算fallback，autotune/benchmark/deep_opt不适用。最小回归600秒/项、服务启动900秒，正式GPQA按用户要求暂缓。 |

PR固定HEAD为`4c884f4c13174b33b69325ecd35909c21ff1c4d0`，文件`vllm_fl/configs/moe/metax/E=128,N=384,device_name=metax.json`，SHA256 `ec38e926b545f76888b4d4a1775405df422b6d66ba5a4659203090c4a6073ffa`。命令、备份及证据保存在原远端案例下`commands/op005-pr595-shared-loader-20261016/`、`results/op005-*`，执行前记录命令SHA。

## 实现与算子回归

已将PR原始JSON按原路径保存在Plugin，替换原package-data规则；原`dispatch/backends/flaggems/configs/metax/moe`下的57行JSON已备份后移除。启动脚本改用`export VLLM_TUNED_CONFIG_FOLDER=/workspace/vllm-plugin-FL/vllm_fl/configs/moe/metax`，原专用`FLAGGEMS_VLLM_MOE_CONFIG_DIR`移除，`VLLM_FL_USE_FLAGGEMS_VLLM=1`保留。

库generic和MetaX各只在`get_moe_configs`增加显式原生目录变量存在时的延迟读取入口：调用vLLM现有`get_moe_configs`，并将bf16/fp16配置标签转成原生None，避免生成额外dtype后缀。不改原生代码，不复制其解析器，不调用原生MoE计算kernel；设置变量时，目录缺文件/空字符串/batch invariant/异常与缓存均由同一个原生函数处理，原生搜索不到表后进入FlagGems-vllm的默认配置。未设置变量时保留原库embedded表。旧stage loader、专用变量读取及精确M字段覆盖代码已移除，原共享内存默认配置修正保留。文件表经既有tuned分支选择完整tile配置，GEMM1/2共用该表，因而不保留旧的stage1覆盖或强行保持旧fast-path开关。

已通过11项库侧契约测试：真实原生读取函数与generic/MetaX接口对照，覆盖bf16/fp16/float32/FP8/INT8/INT4标签、逻辑N扩展、最近M及并列选择、triton_version元数据、block shape文件名、缺文件、batch invariant、无效JSON和未设置变量的原库回退。无新增Plugin测试，原`test_moe_config.py`保持删除。

## 验证期间的依赖版本变化

首轮实际服务检查完成smoke/C8与graph观测后，在最终源码身份断言处发现FlagGems已被外部更新：原`9beec73856969aec8268a7a22788a17a119211fb`变为`gems-opt/c3c5f5ab274f7d1a8a95e3d3ba7bbac28e4a9fd4`。按本地精度定位技能将`op005-concurrent-flaggems-update`归类为identity/configuration-drift，首轮回执无效；不是已观察到的数值失败。保留`logs/op005-health.log`和原请求/worker证据，不覆盖失败材料。

用户确认“已完成，保留 gems-opt 继续验证”。因此不回退其更新，冻结新源码指纹，重启仅本案例空闲8111服务，并以相同输入、容差与验证范围重跑。新版本下11项配置契约、28组完整MoE数值对照及算子graph两次replay再次通过；sort源码SHA仍为`06208cc0d074bd5a38a9ed84afa5870ccbea062fe3d244a1b438c2dc5df2e184`，int32直方图计数器优化保留。旧路径输出仅作可信数值参考，不作为新依赖组合的性能baseline。

重跑证据采用`op005r2-*`及`op005obs02-*`前缀；命令仍集中在同一个`commands/op005-pr595-shared-loader-20261016/`中。`rebind-before.json` SHA为`7066e4df3b6ab537d50f18e7d56594ef113404acad16fc36095840511c48cccb`。相同范围的重跑全部通过，该身份漂移事件已解决；不生成正式模型精度gate。

旧/新完整MoE共28组：BF16/FP16各M=0/1/7/8/32/36/37/64/65/128/1024/7393/8192/16384，均为有限输出，新结果与原可信路径在冻结容差内一致；不声称逐bit一致。M1/8/64各dtype共6组独立测试侧PyTorch数学参考通过。M8/64/1024/8192各dtype分别capture并两次replay，与同配置结果逐bit相同。新配置查表结果逐次与原生选择器一致。5个Triton JIT AST哈希与改动前相同，Python/bash语法、打包资源发现及两仓库diff检查通过。

## 最终服务验证与保留决定

用户确认的新FlagGems身份下，TP2/GPU0,1实际graph服务`qwen3vl-opt4:8111`启动、FULL_AND_PIECEWISE capture、smoke1+C8请求16全部通过。两个worker各完成16次原始graph replay，临时观测hook均已恢复。实际完整MoE函数和两个GEMM的dispatch均来自`FlagGems-vllm/runtime/backend/_metax/ops/fused_moe.py`，实际M64配置均为BM16/BN128/BK32/GROUP4/warps2/stages3，加载文件SHA与PR原文件一致。Plugin调用没有新增`config_dir`参数，Worker与apply源码未变。

当前memory0.91、maxseq64、graph64及原argv保持，实际KV562992。新一轮验证前后四仓库源码指纹稳定，vLLM源码未修改，源容器8000/GPU4,5四仓库指纹保持；用户更新的FlagGems不回退。`op005r2-health.json` SHA为`e9cb1fbb9f5fd28eb6718bfc934c13a007fcc59bc82133a00a2cacbbe38f7ac0`，最终服务清单`manifests/op005r2-service.json` SHA为`909b2614bb3f29a787b2f56299f99d518e8557fa3eba558e3dbfc69e0b45ea0d`。证据索引`commands/op005-pr595-shared-loader-20261016/evidence-index.json` SHA为`467cd07baff63f492403848059f4094e643301ea0e6b43fb4fe54c7a936ca428`；完整路径和其余SHA见同目录state。

保留此配置入口改动。未设置目录变量时仍走库原配置；设置后按原生文件名和最近M规则共用JSON，配置修改后需重启worker，与原生缓存生命周期一致。回退可恢复`before.json`中的源文件/旧JSON及原启动变量，然后只重启本案例8111；回退不覆盖用户的gems-opt更新。

`pr_readiness=experimental`：已整理本轮两仓库补丁，跨仓库依赖是Plugin提供JSON资源、FG-vllm提供条件原生读取入口，当前vLLM版本必须提供该读取接口。其他平台仅有generic契约覆盖、未作硬件验证；其他vendor私有MoE副本未扩展。未运行本身份完整端到端性能或正式GPQA，历史+10.92%不能当作本次配置改动收益。
