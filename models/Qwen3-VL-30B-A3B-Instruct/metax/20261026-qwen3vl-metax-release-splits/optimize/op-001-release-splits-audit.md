# op-001：发布镜像 num_splits 问题核验

用户要求基于给定release镜像启动独立容器，检查此前发现的splits问题。本机mx-104匹配到唯一tag `202610191402`，固定镜像ID `sha256:07cf737e3e20e76b26fa2bc1264de98bc07f1977408416b61ab134d7acf51c3e`。本轮以用户发布镜像原始内容为新baseline，不复制旧容器的实验补丁，不修改模型适配，不动18977当前split1服务。

沿用本地inference-accuracy-diagnosis流程，先核验当前Plugin/native源码和实际导入/版本，再在空闲GPU7做有预算的最小算子复现。相同输入跨batch数值差异不自动判模型精度失败，更不能仅从num_splits默认0断言vendorbug；本镜像的正式GPQA/ERQA分数需要其自身评测，不沿用旧case。当前不启动新模型服务、不跑完整精度/性能。

挂载按现有source容器的/public-flash和/data逐项保持一致；不同image来自用户明确要求，单独记录镜像身份而非伪称继承旧容器writablelayer。新容器增加init以回收退出子进程，entrypoint为sleepinfinity；这是诊断容器生命周期设置，不改变镜像内推理代码。CPU检查隐藏GPU，后续组件仅在GPU7仍空闲时使用，不争抢当前GPU4/5或无关服务。

远端case：`/public-flash/jinghao/qwen3-VL/20261026-qwen3vl-metax-release-splits`，脚本/配置执行前归档，原始日志和张量留远端。当前待创建、待核验。

执行前归档：创建脚本SHA `7ec633f55e80e8d656132ca3ed5ff5da168c4a5175b36518d9ebe1fe93eff529`，静态核验脚本SHA `78d39ae94333efa3aaebf3c03457172372bdd3dda8bbc4501cb0caa2d442291e`；均位于本次remote case的commands目录。

## 静态取证

独立容器 `qwen3vl-release-splits-mx104-20261026` 已03:31:22 UTC创建，镜像ID与用户指定tag匹配，挂载parity通过，无模型服务。发布镜像Plugin实际HEAD08da21、FlagGems为gems-opt/c3c5，FlagTree0.7.0.post2；pip版本标签不能替代真实HEAD。

`/workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/impl/attention/flash_attn.py:830` 的decode调用不传num_splits（文件SHA f81fa552667b3ed98d1cf141d2dee33ba10476cda9a997744495bdbc36289ef2），native接口`:1540` 默认0（SHA a0ce682debda2e3b0457d3716e3c4bdc905d7d759238800494a5619f5a1d37c6）。native二进制 `flash_attn_2_cuda...so` SHA d51997a6e75f56908ae3d42bf150081eb14e4d36d5a735580745c7416a6799c6，也与当前source容器相同。因此镜像确实保留原始auto0路径，未包含后来固定1的缓解；尚不能仅据此判模型GPQA不达标。静态结果SHA 8abaae40ea3428a90a2f04664339cffbb3739241fde74746598e003093a6fc24。

## 执行前组件契约

仅GPU7、900秒预算，保持镜像USE_FLAGGEMS=1与原四项黑名单；重建既有真实TP-rank0/1 L0 QKV的页/stride/B1-B8数据，逻辑首序列完全相同，分别默认0/显式0/显式1；8个真实输入用例加16个BF16/FP16/KV1024/65536/Q1/B1-B8合成用例，原FP64容差、普通重复、graphcapture/3replays。固定1仅是API参数对照，不修改Plugin文件。原始张量留远端，无模型/完整精度/性能请求。

命令已归档：replay_release_native.py SHA d7a66964f9e9e67642e70c924e7be55dff5c2c346c0afdb019ef2fc043006bdc；run_release_component.py SHA 45c5397225c26440de8bc82df7ac6c9e1eeb38e491bd908b192eb49ab53d6761；均位于本case commands，依赖和输入SHA由configs/component-contract.json冻结。

## 组件结果与结论

2026-10-26 03:41:03 UTC（北京时间11:41）完成24项用例：8项真实TP-rank输入、16项BF16/FP16长短KV合成用例；原FP64参考容差全部通过，同batch普通重复精确，默认省略num_splits与显式0输出一致，16次graphcapture/48次回放全部通过。FlagGems保持开启、四项原黑名单不变，原生Python函数和绑定native二进制已实际核验。

| 同一逻辑首序列的B1/B8比较 | auto0最大绝对差 | auto0不同元素 | fixed1 |
|---|---:|---:|---|
| 真实TP-rank0输入，KV224+Q9 | 0.000244140625 | 2692 | 逐位一致 |
| 真实TP-rank1输入，KV224+Q9 | 0.00006103515625 | 2461 | 逐位一致 |

4个合成对照（BF16/FP16 × KV1024/65536，Q1，B1/B8异质邻居）也均出现auto0差异，而fixed1全精确一致；真实输入最大FP64绝对误差0.0001762685948508147，仍在原容差内。

**结论：该发布镜像保留此前同一auto0调用路径，且同输入跨batch数值差异能在其原始native实现中复现，镜像未包含后续固定split1的缓解。** 这是算子行为与原路径证据，不能仅据此判定kernel实现错误，也不能把旧镜像GPQA63.64/66.16等分数转给本镜像；本镜像完整模型GPQA/ERQA、模型级dispatch命中和端到端性能均未测。fixed1仅作为本次API参数对照，没有修改镜像Plugin。

结果 `results/native-component.json` SHA `912fe8e31e360d21b69289bf7cf24d06d07f65e1a78cb1679330bd400dc8b619`，原始输出及FP64参考张量位于本case captures；GPU7探针已退出，GPU7进程列表为空。新容器保持运行，仅docker-init/sleep。原18977服务PID/argv/配置/Attention源码前后SHA一致、HTTP200，保护回执 `results/source-preservation.json` SHA `55e4ece95c74262f70284fb8eeb77561436636745ec0a95f866941e0e4e8131d`。无新性能收益或精度gate，不提交推送。
