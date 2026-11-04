# op008 未量化入口重复判断清理

用户要求检查上游保证，删除重复判断，只保留必要逻辑，独立容器验证后回写qwen-vl。上游真实revision见commands/op008/upstream.json，既有FlagTree0.7.0.post2+metax3.6/Triton3.6.0保持。仅改fused_moe_utils.py，vLLM、其他Plugin文件及FlagGems/FlagGems-vllm不改。

静态调用链：Plugin select_unquantized_moe_backend_oot仅由Plugin UnquantizedFusedMoEMethodFL和patched upstream UnquantizedFusedMoEMethod调用；仓库扫描无量化方法引用TritonExpertsFL。FL类继承get_fused_moe_quant_config；上游该函数仅调用FusedMoEQuantConfig.make(gemm1_* params)或biased_moe_quant_config，同样非量化；三配置属性均None。随后make_unquantized_moe_kernel传原quant_config给experts_cls，prepare使用同一配置。删除三项None热路径判断，不为移除防护新增helper或配置。

保留：无LoRA（OOT选择在is_lora_enabled检查之前）；MetaX平台；SiLU（上游Triton支持更多激活）；dtype范围（ModelConfig常规字符串CLI映射只有三种，但接受任意torch.dtype的Python入口无相同硬限制，prepare也不作三dtype校验，旧staged路径还可接FP8）；not apply_router_weight_on_input（上游透传且prepare在true时已乘权重）；四op default.flagos（上游use_flaggems不是per-op策略保证）。支持条件仅删已证实重复项，不扩大到直接人工注入量化config的TritonExpertsFL对象。

冻结最小回归：真实继承get_fused_moe_quant_config的偏置/非偏置构造及模块prepare调用，20左右合法路由/负例保持，人工注入量化config的旧mock用例记为入口契约外，不以其作为新支持配置；BF16/FP16完整MoE代表shape各2次变输入graph replay，新增小shape FP32独立数学参考；TP2 FULL_AND_PIECEWISE启动、capture/两rank各至少2replay，2单+2C8共18请求。验证observer仅在远端case记录真实worker第一次TritonExpertsFL.apply的quant_config三值；不进入生产源码。失败保存证据、阻止回写。先复核image lineage及mount parity，source不启停；脚本及补丁保存commands/op008并SHA防漂移/回退。

范围为代码整理，非正式精度或性能验收。正式GPQA/性能和其他平台硬件未测；不声称累计收益。

## 上游保证与保留条件

| 条件 | 上游证据 | 决定 |
|---|---|---|
| quant_dtype / weight_quant_dtype / block_shape为None | `UnquantizedFusedMoEMethod.get_fused_moe_quant_config`（目标源码272行）；FL继承同一函数（layer.py20行）；make_unquantized_moe_kernel直接传该配置（oracle294行） | 删除三个重复判断 |
| LoRA为空 | OOT分支在is_lora_enabled判断前返回TritonExpertsFL | 保留 |
| activation为SiLU | 上游支持GELU等激活，未限定SiLU | 保留 |
| 三种浮点输入dtype | CLI字符串映射限三种，但ModelConfig接受torch.dtype对象且prepare不作三类型限制，原staged路径也允许FP8 | 保留，不能把常规CLI映射当公共调用硬保证 |
| 输入路由权重标志为False | modular_kernel1266行透传；NoDPEP.prepare在True时已乘权重 | 保留 |
| 四op均default.flagos | use_flaggems入口不保证per-op选择，policy可以覆盖 | 保留 |

独立算子检查已通过：4个真实继承配置构造（偏置/非偏置及clamp字段组合，最小fixture，只证明配置构造）；6个真实prepare组合；19个合法路由/边界比较；BF16 T64/FP16 T1 E128 H2048 I384 K8与原路径一致，FP32 T3 E4 H64 I32 K2另与CPU float64独立数学参考比较。三dtype各2次变输入graph replay通过。新的validate-v2.py将global_num_experts取真实w1.shape[0]，初始脚本未执行；没有设备测试失败后改成功标准。人工构造量化config直接注入此未量化专家类的旧mock检查不再作为该入口支持承诺，原20项路由矩阵中合法19项保持。

## 模型验证、回写与结论

TP2 BF16 FULL_AND_PIECEWISE服务完成19项mixed和11项decode capture，两个实际worker各记录首次apply的quant_dtype/weight_quant_dtype/block_shape均None，实际源SHA为93188655b4445f6dfb020e8779abe5d621884a0aafb6028b131c883586a5cf98。验证observer仅在远端case的PYTHONPATH生效，Python profile在首次目标apply后停用；生产源码没有任何观察代码。两rank native graph replay各至少2次、完整MetaX库命中；2单请求+2波C8共18返回非空、0客户端错误，15达到96token上限，属输出观察，不是正式精度判断。

通过后仅回写qwen-vl的一文件，以原315707...SHA保护并备份；源/clone postverify确认精确删除三行，完整调用及fallback AST不变、vLLM工作区clean、默认FlagTree保持op007版本。源服务不启动/重启。独立验证服务18408精确停止；0/1设备检查均860MiB/0%使用。

一文件rollback.py默认dry-run通过，mutated=false，--execute需当前SHA和源空闲，恢复本文件至op007，不改编译器或其他仓库。使用更早op007回退先恢复op008，避免旧SHA校验失败。最终51项控制/补丁/日志/结果SHA见 /public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration/manifests/op008-artifacts.json；文件差异为commands/op008/entry_cleanup.patch，整仓最终patch位于patches/op008-final-qwen-vl-plugin.patch。

结论 retained-code-only；独立最小回归passed，其他平台硬件/实际LoRA/正式GPQA/端到端性能未测，pr_readiness=needs_revision。没有新增性能优化结论、提交、推送或PR。
