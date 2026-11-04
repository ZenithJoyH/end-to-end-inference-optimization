# op006 FlagTree升级可行性与隔离预检

用户询问能否升级FlagTree修复MiniMax _index_block_score_kernel导入错误，并提供仅用于网络访问的代理。当前source/clone的FlagTree均0.5.1+metax3.0，实际Triton3.1.0、jit缺少do_not_specialize_on_alignment；Python3.12.11、Torch2.8.0+metax3.7.0.7、vLLM0.24.0、Ubuntu22.04/glibc2.35。原运行与源码保持op005 r2。

官方MetaX手册2026-10-08指定0.7.0.post2+metax3.6，基于Triton3.6/C550；其推荐镜像是Python3.12/Torch2.8.0+metax3.7.0.7/vLLM0.24。通用手册较早仅列0.7.0+metax3.6，选择较新平台专页post2。main JIT源码已显式支持该参数；不以源码推断wheel或整个栈通过。

本项是framework运行时兼容性诊断，不宣称性能优化或验收。只在既有独立容器私有/workspace/op006-flagtree-runtime创建side-by-side包，用新进程PYTHONPATH隔离导入；不更改任何容器全局安装、Worker源码或其他依赖。官方wheel及SHA保留于用户根目录下既有case/wheels/op006；镜像/挂载门禁在预检前复核。控制文件commands/op006-flagtree-review，凭据临时stdin传递，日志脱敏，不保存代理凭据/环境。

预冻结判据：精确wheel版本/CPython312/MetaX3.6，实际triton/jit来源必须新overlay、keyword受支持、vLLM triton_utils一致、原MiniMax warmup模块能正常导入，且全局FlagTree版本前后不变。此预检不执行MiniMax kernel、不启动模型、不验证算子性能或graph；源Worker兼容条件仍保留。若考虑正式替换，需要随后恢复正常kernel_warmup并对采样/MoE、目标graph模式、smoke/C8及正式精度/性能按范围回归后决定。

来源：[MetaX官方手册](https://github.com/flagos-ai/FlagTree/wiki/User-manual-for-metax)、[JIT源码](https://github.com/flagos-ai/FlagTree/blob/main/python/triton/runtime/jit.py)、[通用手册](https://github.com/flagos-ai/FlagTree/wiki/User-Manual)。状态：completed / diagnosis-only。


## 实际结果与结论边界

直连官方FlagOS索引获取精确版本 wheel：flagtree-0.7.0.post2+metax3.6-cp312-cp312-linux_x86_64.whl，425411075 bytes，SHA256=4e113cc9e94e5788400ccc11bbd3d8d29739255a517c801784115dff6bc4dda1，与索引链接公布hash一致，路径为上述case/wheels/op006-v2（首次代理尝试目录op006保留）。

独立容器私有overlay实际Triton3.6.0、FlagTree0.7.0.post2+metax3.6，triton/jit来源均/workspace/op006-flagtree-runtime。原生jit与vLLM triton_utils接口均包含do_not_specialize_on_alignment。正常空闲device0能力查询条件下，原minimax_m3_msa_warmup模块完整导入passed，此前_index_block_score_kernel decorator TypeError消失。此项实证说明升级可以修复当前API/导入错误，不等于MiniMax算子在MetaX执行或精度通过。

初次网络通过用户提供的临时代理访问FlagOS索引遇CONNECT500，改直连成功；凭据不保存。第一次probe屏蔽GPU，vLLM在更早的oink_ops导入中查询设备能力导致No CUDA GPUs available；这属于预检环境限制，与新jit参数无关。保存两次原件后在正常设备条件复检通过，没有更改源码绕过导入错误。

source/clone全局编译器后检查均仍FlagTree0.5.1+metax3.0 / Triton3.1.0。没有替换global安装、Torch、SDK、Plugin、vLLM或模型启动配置；Worker保护仍保留；没有启动模型服务或执行GPU kernel。私有overlay仅通过独立新进程PYTHONPATH激活，平常运行不生效，无需回退既有安装。26项外部产物数量见state及manifests/op006-artifacts.json，不以预检签发模型精度gate。

下一步若正式升级，先在隔离环境用新编译器的独立JIT cache，恢复正常kernel_warmup路径，回归现有采样（含任意FP32 values-only sort）、完整MoE及fallback边界，验证目标TP2 FULL_AND_PIECEWISE capture/至少两rank replay与smoke/C8，再按变更范围做正式精度/性能与源版本回退准备。通过后才能删除源Worker临时保护并替换源编译器。不可从GitHub main签名或成功import直接推断整个运行栈通过。

证据：results/op006-flagtree-preflight-v2.json、results/op006-device-import-probe.json、results/op006-global-install-postcheck.json；logs/op006-overlay-probe-v2.log、logs/op006-device-import-probe.log；manifests/op006-artifacts.json列全部控制/日志/结果/wheel SHA。没有提交、推送或PR。

## 当前后续状态（op007）

2026-10-13：[op007](op-007-worker-moe-cleanup.md)已验证并回写默认FlagTree3.6链路，恢复正常Worker warmup、删除旧vendor MCTLLASS代码与启动export。本文上述版本/保护状态为当时实验事实，当前运行以op007/state为准；原采样与完整MoE算法保持。
