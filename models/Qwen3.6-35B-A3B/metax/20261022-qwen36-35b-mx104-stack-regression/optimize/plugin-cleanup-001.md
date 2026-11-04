# 清理当前服务不再需要的 Plugin 修改

用户明确要求回退当前容器中当前服务已不需要的修改。当前B私有/workspace/vllm-plugin-FL release/0.2@1bc0c77；FGV私有/opt/FlagGems-vllm。只针对本案例原修改，不影响其他容器/共享源码，不提交推送。

只读预检：容器ID2e3dbfa，挂载仅/data和/public-flash；未发现模型API/EngineCore进程，18135/health、/v1/models、/server_info均connection refused。历史continuation实例是旧观察，不能据此启动/停止服务。本次不自动重启或发模型请求。

设计/范围：清理已切换到FGV完整MoE前遗留的Plugin配置实现。未被消费的VLLM_FL_METAX_CONTIGUOUS_SINGLE_PREFILL（仅envs定义）；旧Plugin fused_moe.py的GEMM2覆盖；utils里FGV早返回后的LoRA/其他平台fallback GEMM2和silu覆盖；旧E256N256配置表。还原相应upstream字节，utils只保留用户要求的FGV NVIDIA/MetaX完整接口分支和原日志，AST证明当前非LoRA整个分支不变。不会回退正在承担当前模型路径的采样器生命周期/shortlist、GDN、PR638或FGV c4673a GEMM调参。无理由为清理影响其他平台增加新设计。

|验证范围|方法/边界|
|---|---|
|目标nonLoRA MoE|前后整个分支AST一致；FGV源码字节保护|
|清理后的fallback|恢复上游代码；不声称LoRA/其他平台硬件通过|
|语法/import|全部源码compile、实际Conda+MACA新进程import；不请求模型|
|graph/精度/性能|not_run；本次不重启服务，新完整GPQA/实际kernel命中与gate尚无|

执行前归档commands/plugin-cleanup-prepare-001.py SHA fa3cd72174e71434df72d6376aec88d34edb783d16fabc0fc482912a122c0501；输出environment/plugin-cleanup-001，先完整tar及四包源码指纹，再生成候选，不写生产。移除内容归档留存，禁止直接git clean/reset --hard。

候选已审阅：envs/fused_moe.py回归HEAD，utils只保留原完整FGV nonLoRA分支（含原日志），删除失效_silu/GEMM2 fallback覆盖。snapshotSHA1a0ff75913603df6b9c32e86a9735cd277dacc34f387b6d6b888bf637903899b，backupSHAee4033e7881d78b7ef3b1300386de370b19ef33c1ddd3f0d0d6a29b0f43f9bdc。prepSHA62cfba1a364d1482335c03de8891eae2b4f0658c15c0fdb1169afe7e9a8bcffc，5877受保护源配置。

执行前归档commands/plugin-cleanup-apply-002.py SHA 3b8a70c4d2f9f46a73c063baa880e86f649ffc487eb689d909d5689476f9c98c，核验完整保护清单无漂移后原子写3文件，旧JSON先在removed-and-before-files-002备份后移出算子配置目录，所有原文件保留在外部归档。实际Conda+MACA新进程导入Plugin/MoE utils，全部Python语法与nonLoRA AST检查；若失败仅在源仍是本次新SHA时精确恢复原字节，不覆盖并发改动。0模型/服务操作，旧GPU/CPU诊断不重放。

执行前最终脚本SHA 483c462cc96b34d8317cac968f973f7af2c789a405f138d2f218743d26dcfc9c（以上3b8a预稿未归档/未执行；snapshot使用既有共享产物文件路径传入，避免把5877源码清单塞入单个argv）。此最终SHA为唯一执行版本。

条件式收尾commands/plugin-cleanup-closeout-003.py SHA e31ef4a6da766a31c856cd150299617811eab7ac63665eb4cebd17260b2c0bde：只在verification002 passed/nonLoRA AST一致时执行，GET /health只读刷新状态，CAS追加continuation.plugin_cleanup_001并保存前后副本，无服务控制/模型请求/新gate。

apply002检查失败并按保护逻辑全部还原：独立MoE import需要deep_ep→libmpi.so.40，而该docker exec检查进程没有服务启动时的LD_LIBRARY_PATH；错误保留apply-result-002.json和removed-and-before-files-002。0服务/GPU/模型请求。未执行closeout003。新唯一commands/plugin-cleanup-apply-004.py SHA 821d123bcdea1a768a12fb3a5c5b52415414bb48e67887a4d3e7f8106745cf0b，相同源码候选，仅为Conda导入检查子进程加/opt/maca/ompi/lib:/opt/maca/lib，不修改全局/服务env。执行前再次要求5877完整源SHA等于原snapshot，证明原文件已还原，无补跑模型或数值实验。

最终条件式收尾commands/plugin-cleanup-closeout-005.py SHA c805cc667981723cbf857d50c63f9376e43bd9ba914b75e8d8e719a699711a22引用verification004；早期003仅本地预稿未归档/执行。只有新004通过才CAS追加，保持全部失败证据。

## 已完成

apply004执行exit0，verification-004.json SHA4ddd6c7d3675f91797c452a21b7ef6036e6d7994a1a0c2ae67130499e2cb8c56。5877份原受保护文件仅预声明3改1移出，其余全部SHA不变。旧配置表和三个原文件在removed-and-before-files-004留存，全Plugin（含.git）tar备份SHAee4033e7881d78b7ef3b1300386de370b19ef33c1ddd3f0d0d6a29b0f43f9bdc。

保留整个nonLoRA分支AST与原完全相等；FGV GEMM c4673a、FGV gdn_chunk、Plugin PR638、sampler生命周期/shortlist/其余源码保持。envs和Plugin fused_moe.py已与HEAD逐字一致；utils仅保留NVIDIA/MetaX FGV完整接口分支（新SHAa35ecf98d2c884a4a8f91a6a62d8746480e6b462e6811ac5500563bcc06061cb）。最终Plugin剩4个tracked修改（patches __init__/topk_topp_sampler/worker model_runner/FGV接口utils）和3个untracked（现有sampler测试/shortlist/VL counting），未删除仍有调用关系的采样模块或其回归。

399个Python源码compile，实际/opt/conda/bin/python新进程Plugin及MoE utils import通过；需要MACA和MPI路径仅传给检查子进程。首002观察失败原样保留且自动恢复，004重新确认原snapshot无漂移后完成；不是模型失败/补跑。graph/模型精度/性能not_run，不重签旧gate，不宣称新版本精度。

收尾continuationSHA68f4f6837f205c5db220981f18883bc3ff2763b0baec9353e358d70c3a80cdaa，current_job null；/health:18135仍connection refused，未启动/重启服务。历史current_service是旧记录，不能当作当前运行事实。启动脚本/模型/vLLM/Gems/FGV/source容器/A/GPU任务均未更改。
