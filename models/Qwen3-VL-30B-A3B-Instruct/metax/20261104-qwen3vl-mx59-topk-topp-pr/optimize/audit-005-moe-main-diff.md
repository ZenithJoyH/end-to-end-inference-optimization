# audit-005-moe-main-diff MoE与主线只读比较

2026-11-04用户询问当前mx-59/qwen3vl的fused_moe是否不同于主线。本轮仅只读取证，无源码/配置变更、无GPU或模型请求。

## 版本与来源

- 容器FlagGems-vllm HEAD仍为bad340d67a35e583989fcebf56326f60edc85c9c，已有未提交patch。
- 当前官方main固定到208ab5802fc9a3ea5458481f4a92b7bff330e283。
- [PR #943](https://github.com/flagos-ai/FlagGems-vllm/pull/943)已merged，head97da71f95d72941a29a5b9b256a35521115b8a2b，merge ddce1d66c98cfdbdcfff36364f3d10e3af9d499c。
- 三个MoE文件与deploy004之前的指纹完全一致，证明PR1069同步未改变MoE。

## MetaX专用文件

`src/flaggems_vllm/runtime/backend/_metax/ops/fused_moe.py`：当前main与PR943 head文件完全相同；容器仍用合并的 `_is_qwen_tp2_moe_shape` / `_qwen_tp2_config(..., E=128)` 承载Qwen-VL配置。主线已拆成 `_is_qwenvl_tp2_moe_shape` / `_qwenvl_tp2_config`。

AST比较：除上述两个合并函数及get_default_config外，其余共同函数（含计算kernel）完全一致；主线仅多两个Qwen-VL独立函数。仅抽取纯Python配置函数，M=0..16384、E128/E256、两GEMM/fast开关131080组配置精确相同；896组dtype/shape/block/int8/device/batch-invariant guards相同。该结论属于静态及CPU配置对照，不冒充GPU输出或完整模型一致证明。

容器SHA256：bbc2eddedc93a608a899653c5acca0b1cb4f5293436a5d6136a06401ce50e462。

## 通用文件与测试

`src/flaggems_vllm/ops/fused_moe.py`及`tests/test_fused_moe.py`与PR943 head完全相同，但与当前main不同。通用文件在容器未作相对HEAD的本地修改，差异来自主线后续演进，涉及分GEMM配置读取、按device缓存/查配置、INT8量化范围与路径、累加/边界保护等。不能将整份通用实现称为仅函数改名，也不能因此断言当前BF16模型有新数值问题。

容器通用文件SHA256：00fc24faaf69540c1aa0103b0ae5c3732e9c971a1316a5eaa0063295c61f3f05；测试SHA256：f7e4a6eb59d94e210ba74221a30c2920671c00b499aef5ecbb9c060788c5fcb0。

## 决定与证据

保持原代码。用户此次只问差异；之前要求PR1069同步时其余不变，不擅自更新MoE或追整个main。

只读产物和差异保存在本机临时目录 `/tmp/qwen3vl-topk-pr-20261104/moe005`：container-moe.json、upstream-files.json、各文件unified diff、compare_configs.py、comparison-result.json；没有复制到生产或提交完整源码/日志。
