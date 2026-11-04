# op007 Worker/MoE 清理与 FlagTree 激活

用户要求问题解决后恢复 Worker warmup，简化完整 MoE 分支，并询问旧 MCTLLASS 代码。当前源/独立容器默认仍 FlagTree 0.5.1+metax3.0/Triton3.1.0；op006 仅私有新版本 import 通过。因此先在独立容器升级默认安装，再验证无保护的正常 warmup，验证后回写源环境，源码及编译器备份和 SHA 防漂移回退同步准备。用户当前指令是该兼容性处理与清理的授权，不改基础镜像、vLLM、Torch/SDK、权重或其他服务。

设计：恢复既有 Worker kernel_warmup(self)，移除本任务 MetaX 跳过条件。完整 MoE 复用 TritonExpertsFL.apply；平台独自不能界定支持范围：MetaX 库 SiLU/FP16/BF16/FP32 限制、prepare 已乘输入权重、量化契约和 per-op vendor/reference/failed fallback 均需保护。只压缩等价条件，不新增 helper/dispatch/config。旧 vendor MCTLLASS 开关、形状集合、实例化和调用分支移除，vendor 原 mcoplib 路径保持；共享启动脚本只删对应 export，不执行。默认 FlagOS 完整库路径未命中该 vendor 特化；此前为了保留原有用户补丁未擅自删，当前用户指向此清理后删除。

冻结验证：image_lineage verified/mount_parity passed；FlagTree 新默认 0.7.0.post2+metax3.6/Triton3.6.0及真实路径；原 MiniMax import 通过；49 sampling、8 Plugin sampler 路由、实际 sampler graph、20等价 MoE 路由、BF16/FP16 MoE各2次变输入 graph replay；TP2 device0/1 FULL_AND_PIECEWISE capture + 每rank至少2replay，单请求2+两波C8共18请求。另验证删特化后无mctlassEx环境导入以及原mcoplib dispatch API。测试模式 minimal-regression，不能签发正式 GPQA gate 或宣称性能收益。源服务不重启。任何新编译器错误保存证据并定位，阻止回写。

远端沿用用户工作目录下既有唯一case，commands/op007 保存执行副本及 SHA，产物日志留远端。编译器替换前按旧 distribution RECORD 备份全量文件，回退脚本默认 dry-run；无关源码改动原样保留。其他平台硬件/LoRA真实执行/正式GPQA/端到端性能未测。

## 已完成结果

两个容器默认安装均升级 FlagTree 0.7.0.post2+metax3.6 / Triton3.6.0，真实导入为标准 site-packages；op006 overlay不参与默认启动。源与独立容器 image/mount 门禁 passed，原 vLLM tracked 工作区保持 clean，Torch/SDK/模型未改。源服务未启动、未重启；独立验证服务已精确停止，device0/1检查均859MiB、0%使用，无任务遗留服务。

Worker恢复无条件 kernel_warmup(self)，没有新 helper 或兼容条件。完整MoE分支只做等价排列/压缩，计算调用和分段fallback AST保持；仅添加平台不足以保持SiLU、dtype/量化、输入路由权重及显式per-op选择语义。删除 vendor MCTLLASS 的模块开关、固定行数白名单、FusedMoeGEMM实例化和GEMM2调用；mcoplib原调用AST相同。共享start-model.sh只删除一行对应export，未执行。此前为保留上游已有实验修改未擅自删除；本次用户要求审视该遗留实现后清理。

默认编译器回归：49采样用例/8Plugin路由、三类M64 logits各2次graph replay与参考逐位一致；20MoE路由mock保持、BF16 T64/FP16 T1 E128/H2048/I384/K8各2次变输入graph replay与旧路径通过。MiniMax原模块在新编译器导入成功。vendor在sys.modules[mctlassEx]=None条件可导入，旧特化shape现在调用mcoplib，属mock契约证据，不宣称vendor硬件算子验证。

TP2 BF16 device0/1 FULL_AND_PIECEWISE：19/19 mixed capture、11/11 decode capture完成，每rank有至少2次native replay与完整MetaX库日志；没有kernel_warmup import fallback日志。2单请求+2波C8共18返回非空，0客户端错误/超时，15个输出达到96token限制（观察，不作正式精度判断）。一次readiness探针发生在服务监听之前；稍后验证客户端已在readiness后完成全部请求，没有改测试或忽略请求失败。最小回归passed；未运行正式GPQA、vendor实际kernel、其他平台硬件或端到端性能，不签发正式gate，不计算收益。

源码SHA、版本、启动脚本SHA及备份身份见state。源编译器129个RECORD文件备份至 /workspace/op007-source-old-flagtree.tar；独立容器另有candidate备份。rollback.py默认dry-run已验证compiler备份与3源码/1启动脚本，mutated=false；--execute需再次满足空闲及SHA条件，恢复旧编译器和本轮源码，源服务不会自动重启。

Docker创建时固化的Config.Env仍有MCTLLASS=1（两个容器）；活动Plugin所有py/yaml/sh无引用、启动export已移除，因此不会实例化或调用该特化。移除Config.Env需重建容器；本轮没有停止/重建源容器，不把无效历史声明误报成已经从Docker配置删除。

结果 retained-code-and-runtime-only / pr_readiness=needs_revision。最小验证及postverify/rollback/最终审计路径均 /public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration/results/op007-*.json。最终72项产物的稳定hash见manifests/op007-artifacts-final.json；较早manifest是服务退出前快照。最终源码patch分别归档于patches/op007-final-qwen-vl-vllm-plugin-FL.patch及FlagGems-vllm.patch。未提交、推送或创建PR。
