# cleanup-007：去掉最后三项非必要启动环境变量

状态：**completed_retained**（2026-10-28 12:42 Asia/Shanghai独立核验通过）。用户2026-10-28明确要求从start-model.sh去掉VLLM_MULTI_STREAM_GEMM_TOKEN_THRESHOLD、VLLM_TUNED_CONFIG_FOLDER、VLLM_NO_USAGE_STATS，并验证启动/推理，prefixOFF。目标mx-103/deepseekV4-flash（当前73eedc5bc92c）；远端根/public-flash/jinghao/deepseekV4/20261022-thinking-gpqa-metax103/launch-minimal-20261028-01。

这是部署脚本整理，不是新的性能优化或Plugin改动。不新建性能容器，不改Plugin/FlagGems/FGV/vLLM、权重、tokenizer、挂载或缓存。保留GEMS_VENDOR、VLLM_PLUGINS、TF32三个export以及完整原argv/nohup/service.log行为。原生默认阈值1024和无外部调参路径不影响当前已覆写attention及包内MoE配置路径；移除NO_USAGE_STATS恢复原生遥测策略，不另加其他禁用开关。

e2e/accuracy模式minimal-regression：保持现有20条C1/C8两轮/两条>10K非对齐长输入fixture，新增1条未传chat_template_kwargs的简单加法默认thinking请求（2+3，temperature0/seed0/max_tokens1024，要求最终content含独立整数5且finish_reason=stop）。共21条。检查真实graph capture和至少两次FULL replay、health200、8workers、三变量不在API原始启动环境、三个剩余export同值、argv不变、prefixOFF及无OOM/非法访存/MCCL错误。不是新的GPQA、精度gate重绑或性能等价结论。

开始前保存新任务目录/脚本原SHA和备份、inspect/设备挂载、三仓revision/工作区及源码指纹。确认空闲并精确停止当前API及已记录子进程，容器保持运行；内存保留旧API完整env/cwd/argv用于失败恢复，不写入完整环境。部署失败仅停止本控制器新API、恢复原script/log和原API（按当前原始参数/环境），不盲目重启、不清共享缓存。所有变更命令执行前存到任务commands并记录SHA。不提交/推送。

执行前命令：prepare.py SHA `83ebed8f15fb0f30c34581951e2448047524ae5abd3d69122985ff54f9c26146`；只新建任务根、备份script、生成严格三行删除候选、冻结4仓源码/配置指纹及当前精确API，暂不停止服务或安装候选。Skill bundle e2e/accuracy minimal-regression SHA `1ed06a57f1f6e1ef39fb7fd872f579122b098a18f0255ade0a1160d6432c2b66`。

commands/deploy.py SHA `064ecfa895d52037bc3700c8cdcd3505d46839bac0c89fa8025c7f5d0016c46c`。执行前保存；在容器内保留旧env于内存、核验API/argv/startticks及空闲状态后，仅TERM该API并等待原8workers退出。安装候选、以真实script启动，argv逐项相等；21请求/FULL/health/三变量缺失通过才保留。失败保存证据、停止本次新API、恢复script/日志/原API；不修改代码、设备、挂载和缓存。部署前已做脚本语法核验，复制最小回归执行副本SHA保存在manifest-before.json。

初次prepare在copy2复制扩展属性时被远端文件系统返回EIO；文件字节已复制但未修改原script/服务。prepare02改为按字节写备份并校验SHA，不复制不支持的xattrs；只续用本轮尚未完成manifest的新任务目录。此为备份元数据操作兼容问题，不是模型服务异常。

prepare02 SHA `3b22a31b99aedfe6f5bfe0741785c2db7c154c0226b53bbd8c2473eeb576d789`已完成；当前精确API48735/ticks1157896807。候选script SHA `270c89058f6edf5f496af3ecaaae7c0307745222bb7648a74284ac2db178b522`，仅剩GEMS_VENDOR/VLLM_PLUGINS/TF32。启动控制器前先核验deploy.py固定SHA并保存唯一driver-process.json；控制器是宿主docker exec，只替换本任务API，不重启容器。

新API已按三export脚本启动，PID394611/startticks1158259741（仅本轮运行绑定），argv与原API完全一致，prefixOFF。等待加载/capture后由控制器执行21请求。独立verify.py在result通过后复核script仅三行删除、四仓源码/配置指纹不变、镜像和挂载不变、当前API身份/argv/环境、默认thinking请求、21结果及FULLreplay，生成final-verification及SHA；不重复模型测试。

commands/verify.py SHA `062ff54b6620fc8cedcf2547248cca4f42425382bdf58c59a830f2e043ee0619`，执行前保存。Skill冻结回执保存在commands/accuracy-bundle.json。

21条回归/FULLreplay/health已通过。初次独立verify在原始Docker Mounts列表直接按序比较处失败；随后只读确认容器ID/镜像相同，三项mount所有Source/Destination/RW/Propagation/volume身份字段一致，Config.Env也没有已删除三变量。Docker列表顺序不能作挂载变化判断；verify02对完整mount字典做规范化排序比较（不忽略任何字段），并比较版本元数据。保留初次取证失败，不重启/修改服务、不重跑模型回归，也不更改任何测试期望。


## 最终交付

`/public-flash/jinghao/deepseekV4/start-model.sh` 已仅删除指定三行，SHA `270c89058f6edf5f496af3ecaaae7c0307745222bb7648a74284ac2db178b522`。现在只保留GEMS_VENDOR=metax、VLLM_PLUGINS=fl、TORCH_ALLOW_TF32_CUBLAS_OVERRIDE=1；未注入替代环境变量，vLLM遥测回到原生默认策略。其他脚本内容逐字节一致，完整argv与重启前一致，`--no-enable-prefix-caching`持续保留；用户nohup及service.log重定向行为不变。

源精确API及关联worker已空闲停止；未停止/重启/删除容器。新API/8workers正常运行，health200。旧日志在本轮service.before.log，原script在backup/start-model.sh，失败自动恢复机制未触发。源码和版本独立复核：Plugin、vLLM、FlagGems、FGV四个源码/配置指纹集合完全不变，发行包版本相同；同一容器/镜像/规范化挂载未变；未清理共享缓存或改权重/tokenizer。

21/21请求通过：原20条（C1两题、两轮C8、两条>10K非对齐长输入）+一条未传chat_template_kwargs的默认thinking请求。默认thinking请求2+3最终返回5、finish_reason=stop、completion_tokens46；未配置reasoning_parser，因此返回原始带思考结束标记的content，未改写响应/评分。真实FULL_DECODE_ONLY捕获完成；原生FULL C1 count10、C8 count2，padding到8 count6，满足重复replay。无OOM、非法访存、MCCL错误或Traceback。原有xgboost缺失的AUTO默认回退日志未在本轮安装/修复，不构成新的软件依赖变更或性能结论。

本项仅e2e/accuracy minimal-regression：证明当前配置可启动和推理，不是新GPQA分数/历史gate重绑，也不是正式性能等价或全长度稳定性验收。不因为历史52项配置单测曾通过就宣称本轮重新跑了它们；本轮只改三行script，使用bash语法、字节diff、实际API环境及21条真实请求核验。未提交/推送。

原始证据位于远端任务根：
- result.json SHA `edc933a98f7660c13d55a17a717d1bdc6bcff09570a344ead8b5ae6d1fb10812`
- final-verification.json SHA `a858209fb983d6656f1bd9be7cf5600b777a6772f92eebdf6198be2c77ffc31b`
- minimal-regression/result.json SHA `b9329def7bae6aaa09e6be228e06400a64b63fb2adce9cc403f4fd1d2bc68a30`
- thinking-result.json SHA `8262c833bdf4c9f3c42fda22c90bf9ce27eaf1a8530dbf883ce649389e58dfd0`
- runtime-environment.json SHA `4402f064de1cfadf69b0ad1b4f18161f3a586213ded14d0c4d662d64683dee23`
- source-fingerprints.json SHA `b73651e7fab0af2535637c958c5a0ccda1c5b258a8787e55537102e1bd8634ef`
- fingerprints-after.json SHA `f11c68cb2d1d90b053f2d68a20b826fae99279ef9b73914ba8f56026a27d619e`
- manifest-before.json SHA `b94b6b09dfc92294baa102883baaecfb44cb2c1188410c15247e4529a691ce71`
- commands/verify02.py SHA `ef2be90b5a08f3b0f2341871b2e8309e08dc2656ad6527d679a0e788b0cdfa32`

回退：恢复backup/start-model.sh，必要时仅按当时精确API/startticks和子进程停止当前任务服务，再用恢复后的脚本启动；本轮没有生产源码改动，无需Git reset、容器回滚或缓存清空。原源环境完整env只在控制器执行期内存中用于异常恢复，未保存到日志。


## TF32 变量只读说明（用户后续询问）

未修改脚本/现有API或GPU测试。当前MetaX PyTorch头文件ATen/Context.h:477读取TORCH_ALLOW_TF32_CUBLAS_OVERRIDE，初始化Float32MatmulPrecision HIGH/HIGHEST。两个独立仅导入torch的进程实测：未设置时get_float32_matmul_precision=highest、cuda.matmul.allow_tf32=False；设1时high、True。说明它在该vendor build中确实改变PyTorch精度策略，不是仅凭NVIDIA变量名称推测无效。

语义是允许受PyTorch BLAS控制的FP32矩阵乘使用较低内部精度以换取可能的性能收益，输出dtype仍FP32；不直接把INT8/BF16专用MCTlass路径改成TF32，也不统一控制Triton dot精度。此设置本身不是启动硬性依赖，但尚未测量当前MetaX硬件实际TF32指令命中、删除后的数值或端到端性能影响，不能由两个策略值就宣称实测性能收益或移除安全。原启动脚本仍保留=1，cleanup-007结果和SHA不变。

官方语义来源：[PyTorch2.10 CUDA环境变量](https://docs.pytorch.org/docs/2.10/cuda_environment_variables.html)、[FP32 matmul精度](https://docs.pytorch.org/docs/2.10/generated/torch.set_float32_matmul_precision.html)。容器当前实现与独立进程输出优先于通用文档对实际MetaX运行事实的推断。
