# op-006：移除算子库对vLLM的反向依赖

后续[maint007](maint-007-remove-added-moe-tests.md)按用户要求删除本轮库侧新增`tests/test_moe_config_dir.py`，本页22项测试结果是删除前的历史验证，未重新创建该文件。独立加载器保留；当前服务和采样接入见[op008](op-008-plugin-topk-topp-integration.md)。

用户指出op005直接import vLLM加载函数破坏依赖方向。修正为库内独立JSON工具，generic和MetaX调用同一个工具，Plugin继续只提供PR595原文件及目录变量。计算、最近M选择、kernel及JSON数值不改；不调整vLLM、Plugin Worker/apply、用户gems-opt和sort。仍使用现有独立容器`qwen3vl-p64k-opt-20261015`，源容器8000受保护。

| 项目真相 | 编码前冻结 |
| --- | --- |
| 当前接口/改动 | `get_moe_configs`配置读取，无新增torch算子；generic/MetaX入口、库内公共JSON helper及配置测试。 |
| 只读/build | vLLM/Plugin/FlagGems只读；editable Python无需构建；保存原代码/补丁。 |
| 验证/超时 | 本地精度技能minimal-regression，JSON及无vLLM环境检查600秒，完整MoE每phase600秒，服务启动900秒；无正式GPQA。 |
| active set | BF16/FP16各M=0/1/7/8/32/36/37/64/65/128/1024/7393/8192/16384，E128/K2048/N384/topk8；smoke1+C8请求16。 |
| benchmark/profiler/autotune | 配置架构修正，不改变kernel和tile，无性能声明；benchmark/profiler/libtuner/deep_opt不适用。仓库workflow已读，其optimization.md不存在，本轮无kernel设计。 |

| 配置及数值契约 | 冻结规则 |
| --- | --- |
| JSON格式 | vLLM式E/N/device/dtype/block_shape文件名、整数M key、忽略triton_version；fp16/bf16无dtype后缀。 |
| 设备与依赖 | 仅库runtime元数据：硬件名及vendor别名，不调用vLLM/Plugin平台对象，不按安装位置探测框架文件。 |
| 目录/回退 | 继续VLLM_TUNED_CONFIG_FOLDER；未设置保持原embedded/default。设置后读外部文件，缺失使用库默认；不读取vLLM内置目录。目标MetaX缺文件原来也无内置匹配。 |
| 错误/缓存 | 无效JSON/非法M抛错，不宽泛捕获。配置在worker生命周期内缓存，更新文件后重启；batch invariant禁用调参。 |
| 输出语义 | tensor shape/dtype/layout/alias、routing及累加语义不变；28组完整MoE与当前原生委托版逐bit对照。测试侧数学参考仍BF16 atol.004/rtol.016、FP16 atol.0005/rtol.003。 |
| 未覆盖 | 其他vendor私有MoE副本不扩展；其他硬件不声称通过。正式GPQA按用户要求暂缓。 |

| 路径设计 | 方案/验证 |
| --- | --- |
| 外部表存在 | 公共helper仅解析JSON和元数据，返回表交给原selector；独立导入、原生对照、实际双GEMM命中。 |
| 外部表缺失或batch invariant | None进入库现有默认配置，无torch compute fallback；缺文件/错误/缓存测试。 |
| 未设置变量 | 原embedded路径；回归默认行为。 |
| 计算/graph | 原有完整FlagOS MoE；kernel AST不变，算子capture+两次replay及服务两worker各16次replay。 |

原始证据保存在远端案例`commands/op006-independent-loader-20261016/`、`results/op006-*`、`logs/op006-*`。在改动前保存当前委托版的完整MoE输出作可信参考。测试可以在外部验证脚本中导入原生vLLM作对照，但生产代码及库内新测试不依赖vLLM。

## 实现与已完成验证

generic与MetaX的两处`from vllm...get_moe_configs`已移除，改为调用库内`utils/moe_config.py::load_moe_configs`。公共helper仅使用functools/json/logging/os/typing，读取外部目录、格式化文件名、忽略triton_version、转换M key并缓存结果。硬件名称优先，其次vendor别名；H200名称归一、bf16/fp16无dtype后缀、block_shape和空字符串目录均有明确测试。缺文件返回None，经调用方原有default配置处理；不定位或读取vLLM包。变量未设置时原embedded/default入口保持。

新库侧测试不导入vLLM或加速卡运行时，22项通过。原生加载差分移至案例外部`test_native_interoperability.py`，11项通过，包含dtype/逻辑N/最近M/并列选择、block shape、缺文件、batch invariant、无效JSON及无目录原embedded行为。另在独立进程初始化torch后，清理vLLM模块并阻止后续任何vLLM及子模块导入：实际FlagGems-vllm导入、MetaX MoE函数解析、PR595 M64配置读取均通过，vLLM导入尝试为0。该结论只覆盖本轮MoE加载路径；审计发现indexer算子原有`_get_fp8_dtype`可选vllm.platforms导入，不属本轮新增，未改动该算子。

同一gems-opt身份下，修正前后BF16/FP16各14组完整MoE输出共28组逐bit一致；6组数学参考通过，8组graph capture各两次replay逐bit一致，配置选择逐次与原生selector一致。generic/MetaX全部Triton JIT AST与本轮before快照相同。Plugin PR JSON、vLLM及FlagGems指纹保持；已删除Plugin测试未恢复。目标环境未安装black/isort/flake8，已做语法和git diff检查；不声称完整lint通过。

## 服务回归与保留决定

TP2服务已以原argv启动，FULL_AND_PIECEWISE graph capture通过，两个worker各16次原始replay、smoke1+C8请求16全部成功。实际两个GEMM仍来自FlagGems-vllm MetaX实现，并命中PR595 M64的BM16/BN128/BK32/GROUP4/warps2/stages3。观测hook均已恢复；没有切到原生vLLM计算。服务运行于原独立容器`qwen3vl-p64k-opt-20261015`、GPU0,1、8111，memory0.91/graph64/maxseq64保持，实际KV562992。

候选验证期间四仓库指纹稳定；Plugin、vLLM及FlagGems从本轮开始到结束均未改，源8000/GPU4,5四仓库指纹保持。当前服务以`manifests/op006-service.json`为准，SHA256 `f5fe535c00e1587a20ed59c5c09e5372efb9a2f9c88fd3139f61d082b0f42cfb`；健康回执`results/op006-health.json` SHA256 `8f7cb3d36d886977e89b14a3d9d33211ee8db9119e5caf476887645299d0974f`。证据索引`commands/op006-independent-loader-20261016/evidence-index.json` SHA256 `f1eb69214ac3426dbc99992637c98b927d61811c4903daf8252bbde00555660a`，包括基线输出张量校验和；完整路径/命令SHA见state。

保留修正。`pr_readiness=experimental`：MoE生产路径和库内测试已去掉vLLM依赖，跨仓库只通过外部JSON文件及已有环境变量衔接；未进行其他平台硬件、完整lint、端到端性能和正式GPQA验证。没有新增性能收益声明。数值回归异常时可恢复本轮before.json中的三个旧文件并删除本轮新helper，再只重启8111；这是恢复旧委托版的应急路径，不作为推荐设计，不改用户gems-opt或Plugin JSON。
