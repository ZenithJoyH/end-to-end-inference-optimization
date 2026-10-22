# Conv3d 诊断证据索引

## MiniMax-M3 / PPU-13：大规模视觉预热的冷调优最终完成

- case：20261017-minimax-m3-ppu13-plugin-support / fw-016；[事实主记录](../../../../../models/MiniMax-M3/ppu/20261017-minimax-m3-ppu13-plugin-support/optimize/fw-016-unblacklisted-service-restart.md)。状态：阶段性诊断，observation，不是算子优化或正式性能验收。
- 环境：MiniMax-M3 BF16 / TP16 / 16×PPU-ZW810E；vLLM0.24.0+empty实际安装源码manifest在案例；Plugin620892ab+三文件适配收敛；FlagGems3c6f7537、FlagGems-vllm1f9ac0e0含原有改动，精确指纹见案例。目标graph为FULL_AND_PIECEWISE，症状发生在capture前的启动多模态显存profile，不属于请求Prefill/Decode/Mixed。
- 路径：启动profile视频输入→vision_tower patch embedding `nn.Conv3d`→FlagGems通用Conv3d→Triton多候选autotune→device synchronize。TP0/1/15多轮非阻塞堆栈证明实际路径，非按文件名猜测。
- 有效shape：N399360、CO1280、原CI3补到16；BF16；D/H/W及kernel=(2,14,14)、stride同kernel、padding0、groups1、输出空间(1,1,1)。实际stride未从tensor对象内省，不能据此声称布局全部验证。
- 唯一变量：按用户要求撤销Plugin thead.yaml的conv3d/cudnn_convolution黑名单，保留其余源码/启动契约；无后续修复、清缓存、重启或回退。原有测试已移出Plugin源码但结果归档。
- 证据：do_bench采样在估算同步221和计时结束同步247之间变化，Config对象变化；内部estimate约4.54秒与9.88秒，warmup/repeat均1。THead配置静态11候选，某次live list可定位为第7项。内部估算不是正式microbenchmark，不计算模型吞吐收益。
- 结果：同一实例约16分钟后自行ready；原生profile/KV/warmup845.35秒（不能全归给Conv3d），16rank双模式capture，FULL180次，C1/C8最终答案10/10，health200。PIECEWISE请求replay、真实多模态输出、完整GPQA、其他shape/硬件、再次重启缓存效果均未测。
- 知识差量：refined。先前只观察到长时未ready，具体是否永久阻塞未定；本次候选推进并最终自然完成，确认了此实例的慢扫描边界。长时synchronize不能直接判永久死锁，应先取tuning key、候选对象/阶段变化与repeat；不证明所有Conv3d都适合该通用实现。
- 下一次首检/停止条件：同环境大patch-batch启动时先区分冷调优与无推进；冻结预算、保留现场，超预算记incomplete而非自动清缓存/回退。若要优化非重叠patch embedding→GEMM或固定配置，另建单变量实验并补数值、graph、端到端与正式精度证据；本卡不提供已验证配置或加速比。
