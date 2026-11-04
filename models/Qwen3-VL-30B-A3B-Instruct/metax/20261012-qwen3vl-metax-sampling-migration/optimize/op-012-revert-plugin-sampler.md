# op-012 回退 Plugin 采样特化

用户要求将容器 Plugin 的 top-k/top-p 优化回退到原始 Plugin 代码。目标 qwen-vl，先在既有隔离容器 qwen-vl-sampling-opt-20261012 验证，随后回写源容器；不是全案例回退。当前 Plugin revision 4d4645b33627f0859e4b2d0be319bedc4562932d，原版 MetaX patch 直接调用 vLLM apply_top_k_top_p_pytorch。

回退范围：将 /workspace/vllm-plugin-FL/vllm_fl/dispatch/backends/vendor/metax/patches/topk_topp_sampler.py 从 SHA 9c236e5f181c83997c0137b652962ebd543244be431ad4b77ed259669c88b869 恢复到 HEAD SHA 30535591ccd3e909371d0f921bb71fe94774dd8a10f53fa8f745df21629a57f5；归档移除本案例新增、未跟踪的 tests/test_metax_topk_topp_sampler.py（SHA 74ba925fe09c3560e064e11afed6bd32f23f0656cef6e1def140ed6c11a35ade）。MoE/Worker/启动脚本/vLLM和库源码均不改；保留库独立算子，但Plugin不再调用。每次变更前校验镜像、目录挂载、HEAD、当前文件SHA、测试文件身份及活动进程，保存两文件原件；其他已修改源码逐项SHA守护。

用户授权的既有远程案例 /public-flash/jinghao/qwen3-VL/20261012-qwen3vl-metax-sampling-migration，新增commands/op012、backups/op012、results/op012-*。本次为指定回退，不晋级新性能候选、不启动源服务。按 e2e/accuracy minimal-regression 范围验证恢复后真实PyTorch fallback绑定、原支持组合与采样函数graph capture/两次replay；完整模型graph/C8与正式精度性能不作为本次源码回退结论，未运行时如实记录。

状态：completed / reverted-sampling-only。

## 完成结果

两个容器的 MetaX topk_topp_sampler.py 均与当前Plugin HEAD字节一致（SHA 30535591ccd3e909371d0f921bb71fe94774dd8a10f53fa8f745df21629a57f5），git diff仅该文件为空；新增测试已按原SHA备份并移除。新进程实际导入绑定为 _apply_top_k_top_p_no_triton，所有形状均调用原 apply_top_k_top_p_pytorch，无值排序特化、shape白名单、优化日志或库采样API调用。

独立卡0：M64/V151936 的BF16-grid、FP32、ties与M1/V1024四组输出与原reference逐位一致，各 capture并完成两次变化输入graph replay；k-only/p-only/neither通过，共10次实际fallback调用见证。结果仅覆盖采样函数与算子graph，未启动完整模型graph/C8，e2e/accuracy minimal服务回归记incomplete，无正式精度或性能gate；这是用户指定源码回退，不晋级新优化。

回写前检查qwen-vl无活动vLLM进程；优化容器残留worker均Z状态，不停止或清理历史进程。两容器挂载一致、镜像保持原身份；MoE两文件、Worker与FlagGems-vllm既有修改逐项SHA不变，vLLM/FlagGems工作区仍clean，Plugin当前只剩两项MoE修改。库中的采样算子/导出/测试保留；旧EXACT_TOPK_TOPP_M64开关未重新加入。未重启服务、未提交/推送。

回退前优化文件与测试分别保存在 backups/op012/qwen-vl/ 和 backups/op012/qwen-vl-sampling-opt-20261012/，若以后要恢复该优化，需以当前原版SHA和这些备份SHA重新做精确恢复，不使用旧op001/op005整包回退覆盖已保留MoE。原始结果results/op012-{check,candidate,validation,source,postverify}.json；全部产物SHA清单manifests/op012-artifacts.json。
