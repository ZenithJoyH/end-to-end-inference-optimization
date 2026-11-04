# diag-016：opt7 stage1 后性能差距

2026-10-17，只读核验 mx-59 / qwen3vl-p64k-opt-20261015 / 8111。保持参考采样、gems-opt、sort int32、黑名单和现有 JSON；没有源码、服务配置、重启或生成/profile/benchmark 流量。用户 opt7 测试仍在运行，正式精度按用户要求暂缓。

## 数据结论与边界

原始 D1024/C64/N128 CSV，剔除另一份 N64/profile 数据；保留全部原始轮。下表沿用用户 CSV 的 SUMMARY（其原规则是第2/3轮），不是重新签发稳态准入或受控 B/C/R。

| 场景 | opt4 TPS | opt6 TPS | opt7 TPS |
|---|---:|---:|---:|
| P4096 | 985.46 | 900.65 | 867.38 |
| P16384 | 354.60 | 331.49 | 仅完成两轮332.40/332.07，尚无SUMMARY |
| P65536 | 76.29 | 70.21 | 截止快照暂无CSV |

P4K opt7比opt6低3.69%，比opt4低11.98%；平均TPOT 65.12→67.77ms（+4.07%），平均TTFT5879.55→5914.27ms（+0.59%）。opt7三轮822.77/861.04/873.73均保留，不能用首轮慢引导到冷启动优化，也不能把非交错手工套件差值认定为stage1的独立因果贡献。

## 运行身份与生效核查

用户在op015验证后自行重启了API942226（start_ticks517662127，served qwen3vl-opt7），当前不是op015的API932846。TP2/GPU0,1/BF16、memory0.91、maxseq64、batched8192、graph64、prefix cache关闭及KV562992一致，graph PIECEWISE/FULL双worker capture均完成。四仓库源码内容指纹及两份JSON哈希与op015验证后完全一致，参考采样未重新接入新算子，gems-opt/c3c5f5ab2和sort补丁保持；未发现更新丢失。

本轮没有注入worker观测hook，也没有生成请求；旧op015的实际stage选择和replay证明属于旧API，不能自动重绑定。当前日志包含FlagOS选择，但没有新的逐kernel参数证明。因此“源码/配置未漂移”不扩大成“本次每次dispatch已经重新观测”。

修正术语：FLAGGEMS_ENABLE_OPLIST_PATH指向的文件是debug调用记录输出，不是启用白名单；文件哈希稳定不能证明当前ATen注册集合或GPU热点不变。

## 首要假设：stage恢复不等于旧优化组合恢复

| M64 / GEMM2 | opt4 | opt6 | opt7 |
|---|---:|---:|---:|
| BLOCK_SIZE_M | 16 | 16 | 16 |
| BLOCK_SIZE_N | 64 | 128 | 128 |
| BLOCK_SIZE_K | 128 | 32 | 32 |
| GROUP_SIZE_M | 1 | 4 | 4 |
| num_warps | 4 | 2 | 2 |
| num_stages | 1 | 3 | 1 |

GEMM2的K=384，循环迭代数为旧3次/当前12次（不是launch次数）。N方向grid和occupancy也同时变化，不能只按K循环数换算性能；stage1在旧tile快，不表示在新tile也快。GEMM1的小M配置以及大M Prefill配置同样没有恢复。当前完整PR595配置令is_embedded=True，替代旧逐GEMM默认快配置选参，不能只比较一个num_stages。

op015 CPU全域验证证明实际新增变化只有M49..64/GEMM2 stage3→1。M8在opt6已经stage1，现仍BN128/BK64，与旧BN64/BK128不同。历史P64K Decode常见M8，故stage-only修改并不覆盖这部分差异；P16K常见batch也较小。shape适用性来自历史证据/容量分析，尚非本轮trace计数。

其他差异仍需控制：Plugin换分支后ModelRunner、graph等也改变，AST调用集差异多数属于Mamba/specdecode等条件分支，不能按diff行数认定Qwen热点回归。FlagGems两版已记录调用模块中，通用叶算子名仅sort存在git差异，而实际旧sort补丁与当前字节哈希相同；这缩小排查范围，但不排除注册/helper变化，也不支持回退用户指定gems-opt。两版5个MoE JIT kernel主体AST一致，direct_sum阈值都未启用，不是已证实根因。

## 已准备但未应用的单变量对照

外部commands/diag016-opt7-20261017保存：counterfactual-gemm2-stage3.json（同当前源码恢复opt6计算选参）；counterfactual-gemm2-opt4-decode.json（只在M8..64恢复完整旧GEMM2 tile/group/warp/stage，M0..7及M65以上保持）。不是恢复全套opt4，不改GEMM1或大M。CPU实际选择器重放M0..65536共262148项检查通过；小M旧配置在64/96/128KiB共享内存分支假设一致。未在设备上做新数值、graph或测速，不进入生效目录。

## 复盘与下一步

planning-opt7-stage1-20261017：stage-only集成正确性已通过，性能收益未成立。先比较同源码下当前stage1、stage3、完整旧GEMM2几何，M8/32/64完整MoE数值及graph至少两次replay后再做交错微测；晋级后以同配置P4K Mixed B/C/R验证，守护TTFT/TPOT及漂移。若不足以解释差距，再分别隔离GEMM1/Prefill配置，最后检查实际Plugin执行路径和ATen注册。保持参考采样、gems-opt、FlagOS算子，不能通过关算子取得收益。不得在用户测试期间争抢GPU、重启或叠加配置。

## 原始证据

远端任务根目录：`/public-flash/jinghao/qwen3-VL/20261015-qwen3vl-metax-p64k-opt3`。

- results/diag016-audit01.json：CSV初始快照、当前服务参数、源码/JSON；SHA cf26dc01e7e13fb131907b438580de5ad951a2eef1dc9dc60ebd8a8531aab24b。
- results/diag016-runtime01.json：四仓库指纹、capture/KV/FlagOS日志；SHA 077e73bc00ab83ba5fca4f0ec4bb98f01ffac5973a680629e6785630ace09cde。
- results/diag016-lineage01.json：实际sort与Plugin热方法差异；SHA d7cd9556e716161756d7deebda647e2cf1630aa5d20ef6143647fc566a2bc606。
- results/diag016-benchmark02.json：更新CSV快照，P16尚两轮；SHA 41e16907a1ae4b2980b2970fecf94da8736bfafb3ef171e66f8d00cadbd2804f。
- commands/diag016-opt7-20261017/：只读脚本、analysis/selector-inputs、候选JSON及CPU检查；具体SHA见state.yml。所有原始日志/源码材料保留在外部案例目录，不复制进Git。

结论边界：手工P4K恢复失败已确认，首要配置假设已收敛；独立性能贡献和完整根因未量化，无正式模型精度gate或最终端到端验收结论。
