# maint-004：切换用户指定024plugin-opt分支

用户要求将当前优化容器Plugin切换为`https://github.com/ZenithJoyH/vllm-plugin-FL/tree/024plugin-opt`，并基于该代码继续调整。本轮属于代码基线维护，不新增性能收益声明。

目标仅为mx-59的`qwen3vl-p64k-opt-20261015`，私有源码路径`/workspace/vllm-plugin-FL`。先备份原HEAD、dirty/untracked内容、MoE JSON及当前8111服务启动配置，在`/workspace/vllm-plugin-FL-024plugin-opt-20261016`获取分支并检查指令和差异。旧源码完整保留，候选就绪后才重载当前空闲服务；不操作源8000或其他容器。

沿用原Plugin调度和backend边界，仅补齐新分支中缺少的现有行为：无LoRA MetaX完整MoE从FlagGems-vllm调用、Plugin持有原JSON、环境变量指定目录及package-data。不得恢复用户要求删除的test_moe_config.py，不把旧Plugin全量补丁盲目应用到新分支。vLLM、FlagGems-vllm、FlagGems、MoE JSON内容、sort、黑名单和memory0.91保持当前状态。

使用本地精度技能`minimal-regression`检查导入/路径、目标graph capture及至少两次replay、smoke/C8。正式GPQA按用户要求暂缓，没有完整E2E性能比较或正式gate。对新分支共享路径的影响在源码检查后明确，未测平台如实记录。

命令、原源码压缩快照及增量补丁保存于远端案例`commands/maint004-plugin-024plugin-opt-20261016/`，原生结果位于`results/maint004-*`及`manifests/maint004-*`，准确SHA更新同名state条目。

## 实际基线与适配

已获取分支`024plugin-opt`，精确HEAD为`08da21cb39601752040196232b60a152382c0f8f`（提交主题`fix(moe): align MetaX with the shared fused-experts path`）。该分支没有AGENTS.md。新分支已通过`VLLM_FL_USE_FLAGGEMS_VLLM`选择FlagGems-vllm，完整MoE共用NVIDIA/MetaX分支，并对SiLU、无clamp、无LoRA统一判断；当前模型满足这些条件。本轮不重新修改该判断。

最终适配仅为复制原57项JSON并添加对应package-data，Plugin Python运行代码相对指定HEAD不变。启动脚本仅新增`export VLLM_FL_USE_FLAGGEMS_VLLM=1`，原`FLAGGEMS_VLLM_MOE_CONFIG_DIR`与其余启动参数保持。该上游开关还作用于激活、位置编码等既有adapter的算子库选择；本次属于用户指定分支的整体基线替换，不是单变量性能实验，不将历史吞吐自动绑定到新版本。没有通过关闭FlagGems算子完成切换。

原目录来自容器镜像下层，首次rename返回EXDEV，原文件未改变。随后用shutil.move的copy/unlink流程保留完整原仓库于`/workspace/vllm-plugin-FL-before-024plugin-opt-20261016`，将候选放回`/workspace/vllm-plugin-FL`；没有使用符号链接或改变挂载。原源码压缩快照`plugin-before.tar.gz` SHA256为`a342f6f625691d68af43716f7622c6fc3bd8158529e8a94d197edd4f02956aea`，原身份/配置`before.json` SHA256为`b6ed2c28270fdbda0d5ab74d3275214af4ff1c0eda854185c4249b9e6f38459a`。

## 验证与交付

415个Python文件语法解析、package-data资源发现及git diff检查通过；指定分支现有CachedOp、config、policy、registry、types与MoE layer测试共67项通过。没有恢复`test_moe_config.py`，没有新增测试。首次stage命令误用不含tomllib的系统Python，在修改候选前失败；改用服务原有conda Python后通过。启动日志出现FlagTune可选xgboost缺失、AUTO退回默认调优配置提示，未安装依赖或更改调优策略；该提示不表示关闭FlagGems算子。

目标服务已就绪：`qwen3vl-opt4/8111/GPU0,1`，memory0.91、maxseq64、graph64、prefix cache关闭和其余argv与切换前相同。实际KV容量为562992 tokens，切换前为543712；不能把旧版本吞吐自动绑定到新源码身份和缓存预算，也不在没有测量时归因该变化。

| 范围 | 证据与结果 |
| --- | --- |
| 新代码身份及导入 | 两worker实际报告HEAD08da21cb39601752040196232b60a152382c0f8f，导入`/workspace/vllm-plugin-FL`；本地tracked diff只有pyproject，Python运行代码相对指定分支无改动。 |
| MoE执行 | 两worker实际调用FlagGems-vllm MetaX完整算子；未传config_dir参数，从原环境变量目录读取原JSON SHA，M64/GEMM2选择num_stages1、embedded=False。 |
| graph及健康 | FULL_AND_PIECEWISE capture完成；单请求smoke与16请求/C8通过，各worker完成16次原始graph replay，取证hook恢复。 |
| 原优化及隔离 | 原JSON、sort、黑名单保留；优化容器vLLM/FlagGems-vllm/FlagGems三仓库指纹不变；源容器四仓库指纹不变；旧Plugin完整回退副本指纹与切换前相同。 |
| 结论边界 | `minimal-regression=passed`；其他平台硬件、wheel及不可用的lint工具未测；正式GPQA按用户要求暂缓，完整端到端吞吐未测，`pr_readiness=experimental`。 |

当前服务manifest为`manifests/maint004-service.json`，SHA256 `5dcd17afc020c38bcba6d2b4e984926faf95ef49f61e3e91829af73d27f572db`；健康回执`results/maint004-health.json`，SHA256 `5eeec40e20f37baca3b8610825efd5af8c3b4536eefa84a340df83852a536455`。最终可应用增量补丁`commands/maint004-plugin-024plugin-opt-20261016/final-plugin-adaptation.patch`包含package-data与未跟踪JSON，SHA256 `3b730dffa14b2e12e63bc7b6d042a0e662d6f2b65032015c6741af408041b2fb`；它不包含上游分支本身的差异。原生测试日志、指纹核验及命令SHA见同名state条目和远端evidence-index。

回退仅针对当前空闲8111服务：核验当前服务和文件身份后停止其API，将当前私有Plugin另存到新目录，将完整旧副本恢复到原路径，恢复`start-model-before.sh`和原argv/env，再验证就绪。不得reset仓库、删除旧副本或操作源8000。未提交或推送任何代码。

## PR #595配置兼容性核验

2026-10-16用户询问能否直接使用[PR #595](https://github.com/flagos-ai/vllm-plugin-FL/pull/595/changes)。通过GitHub REST API读取当前PR元数据及唯一文件，并以HEAD `4c884f4c13174b33b69325ecd35909c21ff1c4d0`固定原始JSON：`vllm_fl/configs/moe/metax/E=128,N=384,device_name=metax.json`，SHA256 `ec38e926b545f76888b4d4a1775405df422b6d66ba5a4659203090c4a6073ffa`。该PR只增加原生vLLM调优表，没有增加FlagGems-vllm加载入口。

当前Plugin直接调用FlagGems-vllm MetaX完整MoE，其配置选择器不经过vLLM原生`get_moe_configs`，也不读取`VLLM_TUNED_CONFIG_FOLDER`。原生按`w2_shape[-1]=384`组织文件并取最近M；当前stage表对GEMM2使用N2048/K384、device_name=MetaX_C550、dtype=bf16、topk8及精确M。因此直接复制PR文件、改目录或仅export原生变量都不能使它替换当前生效配置。

配置数值也不是相同优化的另一种写法。当前实际M64/GEMM2为BM16/BN64/BK128/GROUP1/warps4/stages1；PR的M64为BM16/BN128/BK32/GROUP4/warps2/stages3。PR包含M8/32/64/1024/7393/8192，按最近M使M1也用M8、M128也用M64、M16384也用M8192；当前只精确覆盖M8..64/GEMM2的num_stages，保持embedded=False和原融合/归约路径。将PR映射为embedded配置还可能改变`use_half_gemm_fast_paths`及direct-sum选择，不能仅把JSON装入原表就视为等价。

结论：PR内容可以作为独立调参候选，目录组织也可以复用；直接替换当前保留配置不兼容。若接入，应单独适配格式/选择语义并验证完整算子数值、graph和同场景性能，不能为读取该表而关闭FlagGems或切回原生链路。本轮只读核验，没有修改容器源码、配置或服务，也未把PR历史性能归为当前收益；详细对照写入state的`pr595_compatibility_review`。
