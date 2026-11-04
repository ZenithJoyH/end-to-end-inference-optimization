# 20260921-p16k-sparse-mla-out-buffer-21：Sparse MLA 输出缓冲复用

## 方向与冻结范围

- 状态：完成，未晋级；`operator/improve`，只优化 thead vendor Sparse MLA 的完整调用，不改变 attention 数学、kernel、indices、topk、dtype 或布局。
- 父场景：`P16384/D1024/C64/N128`；TP16、BF16、max-seqs64、MBT32768、FULL_DECODE_ONLY、前缀缓存关闭。
- 入口证据：点20 rank0 trace 中 vendor Sparse MLA 占 Prefill/Mixed/Decode 设备活动汇总的27.9745%/29.2729%/6.1099%；活动汇总不是关键路径或端到端收益。
- 当前保留组合与交付脚本不变；不修改vLLM、权重或生产FlagGems数据库，不提交/推送。

## 实际调用链和假设

当前服务实际导入 Plugin `95b04f7` 的 `TheadMLASparseImpl`，其 `_bf16_flash_mla_kernel` 调用已安装 `flash_mla==1.0.0` 的预编译 `flash_mla_sparse_fwd`。实际kernel symbol为 `flash_sparse_prefill_fwd_kernel<...512,16,64,16...>`；P16K trace调用数为Prefill11、Mixed352、Decode942。

vendor Python API原生支持 `out: Optional[Tensor]`，但当前Plugin未传入，因此每次调用由vendor创建输出。vLLM父类已有workspace manager和q concat buffer，但没有BF16 attention output buffer。首个实验只比较同一vendor调用的默认分配与预分配 `out=`；预分配在计时外，模拟模型初始化期workspace。若有收益，再评估通过workspace manager增加与Q同时存活的输出buffer，而不是每层独立持有或在graph replay动态分配。

这是完整operator invocation的分配/数据流优化，不宣称vendor kernel本体改变。历史知识明确指出通用Triton替换在SQ16384/H4仅为vendor的0.828x，故不重复replacement；旧索引转换3.5–4.5x但端到端无收益，也不重复外围tile实验。

## 实验契约

- micro覆盖当前主bucket `SQ16384/H4/DQK512/DV512/topk2048`、相邻非对齐SQ和短SQ sentinel；BF16，indices/topk_length有效且包含非满topk行。
- baseline与candidate使用同一个vendor符号、相同输入；candidate仅传 `out=`。验证输出逐位/容差、返回对象data_ptr、非对齐/空有效行、3seed，以及graph capture和至少3次变更输入replay。
- 计时为3seed×3组交错A/B，包含vendor完整调用；baseline保留其内部输出分配，candidate输出buffer在计时外。中位加速至少1.05x且最低seed至少1.03x才允许改生产源码；任一shape数值/graph失败或重要sentinel退化超过5%立即停止。
- 若micro晋级，先以Skill `minimal-regression`验证源码后的目标/fallback/graph，再用Performance Skill `targeted`运行同配置P16K/D128/C64/N128 A/B/R，吞吐至少+3%且回退/阶段守护通过才测完整父场景。微基准不能作为模型性能收益。

## 当前结果

2026-09-21：PPU-13规定连通性检查通过；模型服务仍停止，实际FlagGems-vllm/FlagGems editable导入路径未漂移。尚未修改生产源码，不宣称新增收益。

首轮 `micro-01` 在性能计时前停止：60级别的小graph案例中，replay候选与随后同输入baseline的FP32辅助返回值有23/1028元素不逐位相同，最大绝对差 `9.5367431640625e-07`；exit-code=1。失败产物保留，不追认通过。issue `p16k_sparse_mla_out_aux_graph_21` 按精度定位Skill冻结为required minimal-regression blocker；下一步固定同一输入对比baseline自重复、candidate自重复和graph replay，分别统计模型消费的BF16 output及未消费的max-logits/LSE。定位前不运行性能、不修改源码、不放宽oracle。

最小诊断确认 `measurement-invalid`：baseline自重复的LSE也有24/1028元素变化，最大绝对差同为 `9.5367431640625e-07`；candidate自重复和graph对照幅度相同。BF16 output在全部同输入对照中逐位一致，max-logits也逐位一致；3次graph replay对变更输入均更新结果。诊断结果SHA256 `053d1dfe520e04ba7bd490cf9044ee2025751adf21bcacda57c4095f9606dfaa`。

不追认micro-01通过。另建micro-02并冻结修正oracle：模型消费的BF16 output和max-logits仍要求逐位一致；仅对未被Plugin返回给模型、且原vendor路径自身有归约波动的FP32 LSE使用 `rtol=atol=1e-6`。v2 benchmark SHA256 `118a286df1185c87126967810b4ab8bde33f558988a94e3d02bf345bf3d2fb20`；执行脚本SHA256 `f98352613405b595427cf71873c6b41756de7632cb51bf1b26841f96602c3ec7`。

micro-02 exit=0，3次变更输入graph replay通过；全部shape/seed的BF16 output和max-logits逐位一致，LSE最大绝对差保持 `9.5367431640625e-07`。完整调用结果：

| shape | baseline代表event延迟 | candidate代表event延迟 | 中位加速 | 最低seed加速 |
|---|---:|---:|---:|---:|
| SQ4096/SKV16384 | 5.63–5.69 ms | 5.62–5.68 ms | 1.000507× | 1.000328× |
| SQ15455/SKV65536 | 20.65–20.74 ms | 20.65–20.74 ms | 1.000078× | 0.999978× |
| SQ16384/SKV65536 | 22.46–22.73 ms | 22.46–22.73 ms | 1.000032× | 1.000001× |

结果SHA256 `d0859d6e932f74d339156c86f7af77ccdc2511ab274631c2df4b17c80bc71028`。所有shape均远低于1.05×/1.03×晋级门槛，非对齐shape最低seed还略慢。结论是vendor/PyTorch缓存分配相对主kernel成本可忽略；不为不可测收益新增约128 MiB长期输出workspace，不运行服务A/B/R，不修改Plugin或vendor源码。

知识差量：开始前认为vendor `out=` 可能消除逐层输出分配；实测将该假设收窄为反例。在PPU/BF16/H4/D512/topk2048、SQ4096–16384范围，下一次应先用完整调用micro判断分配占比，结果接近1.00×时立即停止，不进入workspace工程或服务测试。主kernel仍为预编译vendor黑盒；通用Triton替换旧证据只有0.828×，当前可修改边界内没有Sparse MLA候选。

## 外部产物与回退

- 远端案例：`/mnt/nfs/users/jinghao/glm5.3-flash/optimize/e2e-opt-20260911`。
- 命令将保存到 `commands/p16k-sparse-mla-out-buffer-21-20260921/`；结果保存到 `full-scenarios/p16384-d1024-c64-n128/candidates/sparse-mla-out-buffer-21/`。
- micro benchmark SHA256 `ece6f0686eb1b0709f1282150e3b1fbcd1b944d5ff17fc9c4e835efcacd1ed82`；执行脚本 SHA256 `ab8344da57899eb13f5a7e9615026c2b97c71eb6a3f7d5ce723f29f5fc740457`。
- 本地生成只使用 `/private/tmp`，不在项目 `scripts/` 或模型目录保存过程脚本。
- 没有生产源码变更，回退即不接入；服务保持停止，监控已停用。
