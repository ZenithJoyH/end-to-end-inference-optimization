# diag-001：TP8 首次张量分歧定位

accdiag-005 已在相同 NONE 模式、原 11 个 export、源码和请求下复现：TP8 C1 0/3；TP16 C1+C8 11/11。与图模式切换、新实例重启无关，具体算子和机制尚未确认。此实验只做正确性诊断，不产生性能收益或正式精度 gate。

实际使用 WorkerFL 的 `load_model` 扩展点，通过默认关闭的案例标记调用临时 `install_tensor_probe`。预检发现 PlatformFL 无条件覆盖 worker_cls，因此未执行初版显式子类方案。只在私有 Plugin 新增 observer 文件，并为原 load_model 增加案例标记 guard；Platform/vLLM/FlagGems/模型权重/根脚本均不修改。限当前 PPU 模型结构、CompilationMode.NONE/CUDAGraphMode.NONE；重复安装同一模型幂等，不支持的诊断配置明确拒绝。无新增环境变量。

服务就绪后，以 case trigger、准确 token IDs SHA 和 176-token 输入范围激活一次 Prefill 观察，记录输入、embedding、分片 QKV、O projection 输入、全局归约后的 norm、FFN 和最终 logits。张量仅保存外部案例目录；按实际分片映射比较，不把 TP 局部输出直接视为全局张量。采样复制不改变输入/输出。TP8/TP16 使用相同 observer 源码与请求；复现响应需分别与未加 observer 的记录一致。

外部案例 `/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261010-minimax-m31-w8a8-ppu-tp8-e2e`。源代码控制 `commands/diag001-tensor-probe-worker-source.py` SHA `00fc45ab012afa9e4f25fac0ec4427a958443933bb64112553bc1ac5fa623719`；安装控制 `commands/diag001-install-v2.py` SHA `499b4c33427bf4a27a7b6d25889262bc4dfaf29594973447ee82fe121cfb56c4`。执行前保存四套源码指纹与 Git 状态；新增文件必须处于未挂载的私有 Plugin 内，源容器指纹不变。

先恢复 TP8 并采集，再临时 TP16 对照，随后回到用户 TP8 graph 配置。每个实例保存命令、manifest、源码 SHA、实际 worker/设备与准确请求。正式精度监控在实际复现前启用、终态暂停。停止条件为 token 输入不一致、观测点/任一 rank 缺失、observer 改变响应或出现服务错误；失败保留证据，不推定根因。

`pr_readiness=experimental`：这是临时诊断文件，定位后停止诊断服务并删除精确新增文件，恢复原四套指纹后重新测量；不进入 PR 或性能验收。

安装第一版后尚未选择 ProbeWorker；实际采集将使用 v2：先将张量复制到 CPU，再在 CPU 上选行，避免观测结果依赖正在诊断的 GPU 索引/stack 算子。只更新本实验刚新增且旧 SHA 已验证的文件。source v2 SHA0665f8a4b3411b09b44b333d799045bfb6c4486b09c3ea0d569e1ad36648ddbf；升级控制 SHAe8684605864f20acb208f7bf6ebb6a2c6f8a70ef7417a7805b5691df9bdcd99a，存档于 commands/diag001-upgrade-v2.py，执行前记录。

实际 helper v4 SHA1758cf9c041e4f56e81dfa14d55f97862674f60caef71cd5b85da7927c3f6409，控制 `commands/diag001-worker-hook-install.py` SHAb4341a7732fd2b9d09b3b21733e2f1fb48d2a8f8ebb07c53733e95a2f1e633c0。修改前原 Worker 字节备份与 SHA 存于 profiles/diag001-source-03，回退时恢复精确备份、关闭标记并移除本实验新增文件；不丢弃任何继承适配补丁。初版 helper 已安装但未被实际服务选择。

TP8 8rank 与 TP16 16rank 各1323点采集完成，同176-tokenIDs。TP8完整响应复现原失败，TP16答案13、58tokens且内容SHA与未观察实例一致。TP8已检查的65个全局边界全部rank一致。CPU对照控制 `commands/diag001-cross-tp-prefill.py` SHA8df184b1ef8815afa61fd7860140bd5b9e4ce78a2c79b3b45b8b80e41904ce20，执行前记录；只比较全局边界及明确定义的共同QKV/head分片，不比较partial row-projection输出。

Cross-TP 393点对照结果SHAe8e6e2773a55c0dfaa5a8f6827daf20a5bd3994d909122de678fcb340f7517ff。进一步CPU检查所有8rank的layer0 QKV映射均exact_equal；TP16首token attention输出逐元素等于自身V，TP8在所有rank不满足，最早差异界定为前处理/attention内部。使用独立native Prefill小算例 heads4/8/16、query1/2/176、prefix128 检查causality，CPU FP32 oracle；控制commands/diag001-attn-micro.py SHA620b9335c115fed05fbe07d64786ae85af72879244eee1990dbf5fab2a46cde2，执行前记录。Kernel与模型性能尚未归因。

Micro v1在GPU调用前失败：宿主PID误在容器PIDnamespace核验，未执行kernel。v2移至宿主核验，容器继续检查idle指标；控制SHA d71585ea118b2c2ad07d17e853d0fb33cb90928aab7621b51119658161e1b82e，执行前记录。

独立native小算例复现：GQA8 qlen176 relativeL2=1.10394，GQA4/16约0.00194；GQA8 qlen2及prefix128同样失败。结果profiles/diag001-attn-micro-02.json SHA6d6e1f148554ba4dd6f3168e7bbec0e409f8a0675ec0c860da2b6a73f38f944d。下一控制v3 SHAdc2744abc800562119389af5f8b618a8955f1d43d5e6e15bc1f512114c22841a，在进程局部复制原launcher只补齐H16，执行前记录，不修改vLLM文件。

2026-10-12 机制已由 [diag-003](diag-003.md) 确认：PPU BF16 M8 的 A ldmatrix 载入地址漏 lane16 K位；原始→A-only IR修正→原始在独立矩阵乘和原native attention中控制错误。此前H16 padding作为绕行保留，未改安装编译器。
