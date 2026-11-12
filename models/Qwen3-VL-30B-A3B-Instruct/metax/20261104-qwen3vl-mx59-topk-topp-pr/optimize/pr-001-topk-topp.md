# pr-001-topk-topp MetaX top-k/top-p 上游 PR

- 状态：用户请求已完成；算子PR保持Draft/needs_revision（单行性能回退）。
- 分类：operator/replace；仅交付既有算子与接入，不执行新E2E优化。
- PR：[FlagGems-vllm #1069](https://github.com/flagos-ai/FlagGems-vllm/pull/1069)，公开提交675b36e9b39397e097ce5b7cf0289769bd97bd02，当前无合并冲突。

## 优化方向与瓶颈依据

用户2026-11-04要求从mx-59的qwen3vl容器提交既有top-k/top-p算子。生产源FGV bad340d、Plugin08da21c，镜像标签202610291523。已有MoE改动不纳入PR。上游基线5877f5c，创建PR时main449cd35仅变更无关benchmark，与本补丁不冲突。

## 优化内容与适用边界

按用户后续指令，公共接口统一为 `top_k_top_p(logits, p=None, k=None)`，与Ascend对齐参数顺序及非原地返回；不保留旧库 `apply_top_k_top_p` 名称或兼容层。MetaX支持连续FP32二维logits、M<=64及1<=V<=262144；k为int32/int64、p为FP32同设备连续行参数，值域由vLLM调用方保证。Ascend专属override在MetaX显式拒绝，无隐式忽略。普通generic入口不提供Torch compute fallback。接口从ops、包级与MetaX backend公开导出，统一metadata且排除ATen注册。

算法保留既有BF16精确值计数排序、FP32 radix、FlagGems softmax/cumsum和Triton阈值；只调整接口/必要输出clone，不改RNG。现有MetaX固定schedule不新增NVIDIA/autotune。依赖实测FlagGems5.5dev/c3c5f5ab2、Torch2.8.0+metax3.7.0.7、Triton/FlagTree3.6.0。

mx-59/qwen3vl调用方已同步：两个Plugin sampler文件改为新API与p/k关键字参数，使用返回张量，开关键对应top_k_top_p。不支持metadata在执行前选择原生路径；执行错误上抛，不捕获后跨backend重试。vLLM原生调用点仍沿用框架自身名称，不是旧库兼容入口。容器只定向更新6个库文件及2个Plugin文件，未整体升级仓库，MoE源码逐文件SHA一致。

## 正确性与路径命中

独立latest-main checkout在空闲GPU0验证：68项设备测试通过；2次capture/6次变化输入replay通过；公开MetaX真实入口、旧导出不存在、输入保持、metadata拒绝、空batch、非零storage offset、ties/NaN/Inf/signed zero均覆盖。真实容器vLLM sampler hook另验证一次/幂等安装、参数转发、前置fallback、执行错误不重试、RNG状态不变及3次变化输入replay。

初次严格FP32参考掩码比较65通过/2失败保留：大词表仅top-p各差1token，排序全exact，争议CDF差4.470348e-8；两个位置候选均更接近CPU FP64。最终测试对仅top-p用独立FP64 CDF及仓库既定FP32 RESOLUTION=1.3e-6检查：区间外掩码正确、区间内必须保持稳定后缀、保留值精确；不宣称另一归约实现的掩码逐位相同。核心算法未为此改变。

全部相关pre-commit通过。接口对齐前v2的67通过为历史；带兼容层v3草案未执行，已由无兼容v4取代。容器首次回写预检docker top缺PID列，在0源码写入前失败；修正pid,comm后联动更新通过，原文件及回滚脚本已归档。工具进程导入出现vendor patch循环导入告警，完整模型启动、正式精度和E2E未测，不冒充模型验收。

## 性能效果

仅算子计时，FP32/k20/p0.8，双方都包含一次clone；参考为独立稳定升序Torch的vLLM过滤语义。时间单位ms。

| 输入分布 | M×V | Reference | MetaX | 比值 |
|---|---:|---:|---:|---:|
| bf16-grid | 1×4096 | 0.133376 | 0.561920 | 0.237× |
| bf16-grid | 1×151936 | 0.298240 | 0.613120 | 0.486× |
| bf16-grid | 8×151936 | 1.957120 | 0.613248 | 3.191× |
| bf16-grid | 64×151936 | 9.519872 | 1.775104 | 5.363× |
| arbitrary-fp32 | 1×4096 | 0.135168 | 0.565376 | 0.239× |
| arbitrary-fp32 | 1×151936 | 0.296448 | 0.573696 | 0.517× |
| arbitrary-fp32 | 8×151936 | 1.975936 | 1.196672 | 1.651× |
| arbitrary-fp32 | 64×151936 | 9.597184 | 6.539008 | 1.468× |

M1低于0.9x要求，已在Draft PR完整披露；未追加调参或声称全场景收益。这不是E2E吞吐或模型精度结论。

## 决定、风险与回退

API整理与用户指定调用方同步已完成；PR等待维护者审查及小batch性能后续，不签发新模型gate。生产8文件变更采用旧SHA检查、完整备份、验证失败自动恢复。当前验证通过，已保留新接口。Plugin变更不混入FGV PR，也没有自动另提Plugin PR。

## 外部证据

远端 `/public-flash/jinghao/qwen3-VL/20261104-qwen3vl-mx59-topk-topp-pr/`：commands包含最终patch-v4、更新/验证/回退逻辑；results/final-audit.json为终审；results/completed-v4.json、benchmark-v4.json、container-updated.json及logs/container-integration.log保存原始回执。SHA及8文件指纹见state.yml。原始数据留远端，源码唯一提交以公开PR为准。
