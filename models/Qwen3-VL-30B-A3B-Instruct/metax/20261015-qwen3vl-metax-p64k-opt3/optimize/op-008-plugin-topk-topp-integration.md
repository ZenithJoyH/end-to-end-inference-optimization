# op-008：Plugin接入现有MetaX top-k/top-p库算子

用户要求完善对已新增FlagGems-vllm采样算子的Plugin调用。当前实际MetaX patch仍将vLLM `apply_top_k_top_p`固定指向PyTorch参考，库API未接入。本轮复用该vendor patch，仅增加库调用和既有策略判断，不新增Worker/模型特例、环境开关、runtime框架或vLLM源码改动。

| 编码前项目事实/范围 | 契约 |
| --- | --- |
| 容器与仓库 | 现有隔离容器qwen3vl-p64k-opt-20261015/GPU0,1；Plugin024plugin-opt/08da21cb3960，FG-vllm f6fdb9b，FlagGems gems-opt/c3c5f5ab2，vLLM ee0da84ab；本轮before.json重验。 |
| 可修改 | MetaX sampler patch和采样路由测试；MoE新增测试另按maint007删除。其余kernel/JSON/start脚本只读。 |
| 构建与验证 | editable Python，无需构建；既有库采样原测试、Plugin路由、实际hook数值与变化输入graph、TP2服务graph/smoke-C8；每项900秒、服务启动900秒。正式GPQA继续暂缓。 |
| 入口与策略 | 原MetaX入口；VLLM_FL_USE_FLAGGEMS_VLLM与use_flaggems_op("apply_top_k_top_p")共同选择库API，继承全局prefer、启停及黑白名单规则。 |
| 函数契约 | 同一logits对象，原地过滤；k/p无转换直接传入；双None立即identity；top-k阈值保留ties，top-p累计概率阈值及至少留一个token遵循当前reference。 |
| 支持范围 | 库负责rank2/FP32/cuda/contiguous/M<=64/1<=V<=262144及filter元数据判断，含BF16可表示值和任意FP32；不把模型名/路径/固定V作为路由条件。有效k/p取值由上游采样入口保证。 |
| 回退与错误 | 只捕获库在修改logits前抛出的NotImplementedError；metadata不支持时保留当前PyTorch路径。启用但缺依赖、编译/运行异常透出，不静默改回参考。 |
| 非目标 | patch仅由MetaX backend装载，不改其他平台。默认flag为0时维持原参考入口。该接入不证明其他平台硬件通过，不声称端到端收益。 |

最小回归选用本地精度技能minimal-regression：库原有49项测试先检验当前gems-opt；库测试参考和容差不改。实际Plugin hook覆盖k-only/p-only/k+p、边界/非连续/dtype fallback、变化值域graph两次replay，数值要求与启用FlagGems的实际原参考逐bit一致。服务smoke1+C8请求16，明确temperature.7/top_k20/top_p.8，观察实际库调用形状/来源；同时保留MoE JSON命中及两worker各16次原始graph replay证据。

新增Plugin测试仅针对采样，无新MoE测试。源码和证据位于远端案例`commands/op008-sampler-integration-20261016/`、`results/op008-*`、`logs/op008-*`；当前阶段不开展新性能测量或修改算子kernel。预期知识差量是证明已有算子可经当前Plugin生命周期接入，历史采样性能不可直接复用。

## 算子与接入回归

当前gems-opt下，库原测试49项通过，未修改测试或容差。新增Plugin采样路由测试17项通过：三种filter参数原样转发、无filter不导入库、已有启停/prefer/黑白名单策略、unsupported回退、依赖/运行错误透出以及重复执行patch不叠加包装。禁用策略仅用于路由正确性测试，不是本任务性能优化手段；服务继续保持FlagOS和原黑名单。

使用实际Plugin hook执行原库数值和graph用例47项通过，其中45组过滤对照、两组graph形状M2/V257与M64/V151936。graph分别切换BF16可表示值、任意FP32和正值ties，各两次replay，与当前启用FlagGems的原参考逐bit一致。另有9个实际边界探针：正常输入、M65、V262145、FP16、CPU、非连续logits、非连续k、FP64 p、空batch，库命中/回退及原地返回对象全部符合契约，数值逐bit一致。

源码指纹回放核验仅有：删除新增MoE测试，修改MetaX sampler patch并新增采样路由测试。FlagGems-vllm/FlagGems全部kernel、独立MoE JSON加载器、Plugin JSON、Worker与MoE apply均保持。语法和git diff检查通过；black/isort/flake8未安装，不声称完整lint通过。

## 服务验证与保留决定

服务以原argv恢复，FULL_AND_PIECEWISE capture通过，两个worker各16次原始graph replay及smoke1+C8请求16全部通过。HTTP请求固定temperature.7/top_k20/top_p.8/max_tokens64/ignore_eos，非正式精度或性能测量。两个worker均在启动预热中完成库API调用，实际logits为contiguous FP32 [64,151936]，k为int64 [64]、p为FP32 [64]，原地返回同一对象；函数来源为`FlagGems-vllm/runtime/backend/_metax/ops/top_k_top_p.py`，SHA256 `b17de0558d78acd5446877a8f44ffcc7dc5a6d5b2409f58c793b4872cff9817c`，与本轮before一致。采样命中观测发生在HTTP回归前的启动预热，不将其写成逐HTTP请求的采样计数；所有临时hook已恢复。

原MoE两个GEMM仍命中PR595 M64配置stages3，独立加载器/JSON、gems-opt与sort保持。当前8111/TP2/GPU0,1就绪，memory0.91/maxseq64/graph64保持，实际KV562992。候选前后四仓库指纹稳定，源8000/GPU4,5四仓库指纹保持，未回写或重启源容器。

保留此接入，`pr_readiness=experimental`。健康回执`results/op008-health.json` SHA256 `27792afe073cd758f2ad0f8a0d1b40ccee7324a0022057a94aee1f78dc2537e3`；服务清单`manifests/op008-service.json` SHA256 `3b084a6727c39ddc1e5bd4647af2e67bb416acad7541eff375d09b350001ab59`；索引`commands/op008-sampler-integration-20261016/evidence-index.json` SHA256 `fed29b5f301fc36c7a088a9774d73ec69fc27ae6e5c7c504443053e0b286e1c8`。完整路径和其余SHA见state。

回退仅需恢复before.json里的MetaX sampler文件，再只重启8111；按需移除本轮新增采样路由测试，不恢复用户要求删除的MoE测试，不覆盖gems-opt或配置。跨仓库依赖为FlagGems-vllm公共`apply_top_k_top_p`及其既有FlagGems实现；flag未启用时不导入此库。未测其他硬件、完整端到端性能或正式GPQA；没有新收益声明。知识差量仅确认当前版本可经Plugin生命周期接入并保留策略/metadata回退，无新增kernel或性能结论。
