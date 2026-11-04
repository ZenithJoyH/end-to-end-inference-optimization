# op-001：原生 vllm_metax Attention 调用与 splits 核验

用户指定原生镜像 `cr.metax-tech.com/public-ai-release/maca/vllm-metax:0.24.0-maca.ai3.8.2.5-torch2.10-py312-ubuntu22.04-amd64`，问题是是否仍有auto0跨batch数值差异，以及vllm_metax如何调用。仅mx-104，读取本机该tag固定不可变manifest `d080f0f3aa7108b7e9d9cc23eec704bdb7828ec6bb731dab6129a77200238d1e`，与10月13记录的镜像身份一致。当前registry独立重验返回token授权失败，不推断远端tag未移动；核验结论绑定本机immutable digest。现有metax-for-plugin0240容器虽然引用同镜像，但不检查/改动其writablelayer，避免误当原始镜像。

CPU临时容器无挂载/GPU/network、read-only rootfs，仅标准库AST和metadata读取原始文件、entrypoints、platform/backend映射、native调用参数和二进制指纹；finally删除本次临时容器。不改现有优化容器/源码或服务。CPU执行脚本 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-native024-splits-audit/commands/audit_image.py，SHA `92064efdf6566b9ee0df91dda20ea868681670b359a79359a4940ae0e9dc2296`。执行前归档结果路径和SHA，之后根据实际native内容设计最窄同输入复现。

参照本地inference-accuracy-diagnosis最小复现：不把默认0本身称bug，不把batch位级差异作为模型正式失败条件，不直接继承旧GPQA/ERQA成绩。原始source/原生结果/trace/张量留/public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-native024-splits-audit，本地只保存摘要。GPU复现另冻有限组件合同，先核对空闲卡，不停无关服务；不启动完整模型或测性能。当前状态prepared。

## 静态调用与组件冻结

已读取镜像原始vllm_metax0.24.0+g436274/MACA3.8.2.5/Torch2.10。无FlagOSPlugin/FlagGems/FGV。平台entry point `metax -> vllm_metax:register`，返回MacaPlatform，非MLA优先FLASH_ATTN，经registry选择MetaX FlashAttentionBackend。fa_utils直接导入flash_attn包，FA版本辅助器返回2。普通prefill走varlen（1185），decode走kvcache（1217）；querylength bucketing decode也走kvcache（991），均省略num_splits。`VLLM_METAX_ENABLE_FA_SPLIT_FORWARD`运行时默认lambda1，与native分片num_splits是不同配置。native接口默认0、SHA4b2d5b...和soSHAf251391...与刚测试的基础镜像相同。静态原始回执SHA `04a4c87bfe4dc4895cba62e46b33fa07b2cad0a251aee9346fb44db7d771ec2c`。

本轮原生镜像仍独立验证一次：只用启动前确认空闲GPU7，24项旧真实rank/合成输入B1/B8、split0/1、原FP64容差和graph3回放，900秒、无retry。临时组件容器同原容器两项bind挂载，镜像原始代码不改；仅直调nativeAPI，新增运行时证明`vllm_metax.fa_utils.flash_attn_with_kvcache is 被测fn`、实际平台OOT与split_forward默认True。此证明不替代完整模型forward/backend命中或TP2模型测试。finally删除本次临时容器，不启动或停止现有服务。控制器 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-native024-splits-audit/commands/run_component.py，SHA `61f55ba547c00832c52d44bd337030728f735dd747b6c063d3c3a2461db666be`，实际probe及所有依赖/输入在启动前另存合同。

## 实际结果与调用链

原始官方镜像中独立重放完成，24项FP64参考原容差/普通重复全部通过；省略num_splits与显式0完全一致。16次graph capture/48次replay通过。实际runtime当前平台为 `vllm_metax.platform.MxsmlMacaPlatform`，`fa_utils.flash_attn_with_kvcache` 与被测函数是同一个对象，split_forward默认True，native默认num_splits0。

| 同一逻辑首序列B1/B8 | split0最大绝对差 | 不同元素 | split1 |
|---|---:|---:|---|
| 真实rank0，KV224/Q9 | 0.000244140625 |2692|exact|
| 真实rank1，KV224/Q9 | 0.00006103515625 |2463|exact|
| 合成BF16，KV1024/Q1 | 0.0009765625 |566|exact|
| 合成BF16，KV65536/Q1 | 0.0001220703125 |857|exact|
| 合成FP16，KV1024/Q1 | 0.0001220703125 |507|exact|
| 合成FP16，KV65536/Q1 | 0.0000152587890625 |829|exact|

这是同输入原生单GPU组件重放（包括先前TP-rank数据），不是完整TP2模型forward或GPQA/ERQA。新版官方镜像仍有auto0跨batch差异，但全部参考容差通过，不能只据此称kernel算错/模型精度不达标。没有强制设置split1或修改原始镜像文件。

调用链源文件均位于 `/opt/conda/lib/python3.12/site-packages/`：

1. `vllm_metax/__init__.py:14` 的register返回MacaPlatform，平台插件entry point为metax。运行时对象MxsmlMacaPlatform。
2. `vllm_metax/platform.py:123` 注册FLASH_ATTN到 `vllm_metax.v1.attention.backends.flash_attn.MacaFlashAttentionBackend`；普通非MLA候选优先FLASH_ATTN，仍做能力/用户选择校验。backend的get_impl_cls位于Attention文件148行，返回FlashAttentionImpl。
3. `vllm_metax/v1/attention/backends/flash_attn.py:1010` forward读取paged KV、canonicalize stride。non-cascade/DCP1常规路径下 `envs.py:76` 的 `VLLM_METAX_ENABLE_FA_SPLIT_FORWARD` 默认True。该开关只控制Prefill/Decode分路，与KV内部分片num_splits不同。
4. Prefill调用1185行varlen，直接用paged K/V与prefill_block_table，没有FlagOS PR638的contiguous gather。Decode在1217行调用kvcache，q reshape为[B,Q,H,D]，转发block_table、cache_seqlens、scale/causal/window/alibi/softcap/sinks；querylength分桶时991行按桶调用同API，两处都不传num_splits。关闭split_forward的1235后分支走统一varlen，不能把kvcache组件结果扩展为它的全部行为。
5. `vllm_metax/v1/attention/backends/fa_utils.py:12` 直接从flash_attn导入函数，get_flash_attn_version返回2；既不走FlagOS Plugin，也不走FlagGems。
6. `flash_attn/flash_attn_interface.py:1896` 的API默认num_splits0，2039行调用 `flash_attn_cuda.fwd_kvcache`，2059行按位置向编译扩展透传num_splits，底层so为 `flash_attn_2_cuda.cpython-312-x86_64-linux-gnu.so`。0是启发式自动分片，1不拆分KV，>1指定分片数；并非0表示无切分。

原生结果 /public-flash/jinghao/qwen3-VL/20261027-qwen3vl-metax-native024-splits-audit/results/native-component.json SHA `758a065b88365b2d9a900d752e9f80e33edb16decc6783620a46c3ec717feb1a`，组件总回执SHA `f4823eec05178bdce03097b057f3107c21adbba6c83849db50f8db5d82608ab3`。实际probeSHA `4624d937eeb58ac2f6501adb8b4c0da9a7973e2bc73cf00bda5f38c44da861eb`，合同SHA `6f141d4ac00e87355f0440eb6a27e7dea2dc87dd998b06f999f493068368870c`。

两临时容器均已删除，GPU7已无进程，受保护容器前后身份/挂载/Attention源码一致；本次未启动或停止现有模型服务，未改现有metax-for-plugin0240容器。cleanup回执SHA `8c9b5f41211dd3c26be871da6338e146f0d8df0f00a91ed5c2ea8ac05af2a8ee`。无新gate/性能结论或待跑任务。
