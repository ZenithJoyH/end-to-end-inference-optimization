# diag-002 旧容器C64与new2精度比较

状态：三项原生终态及逐题离线对照全部完成。旧容器控制于 2026-10-22T23:40:26.729359+08:00 完成，终态独立复核于 2026-10-23T00:07:06.527036+08:00；监控 minimax-c64 已删除，原模型服务保留。

| 数据集 | 旧容器C64 | new2（acc-007） | 旧容器减new2 |
|---|---:|---:|---:|
| GPQA | 167/198，84.34% | 167/198，84.34% | 0题，0个百分点 |
| Math500 | 469/500，93.80% | 464/500，92.80% | +5题，+1.00个百分点 |
| ERQA | 252/400，63.00% | 259/400，64.75% | −7题，−1.75个百分点 |

## 逐题变化

GPQA两边160题均对、24题均错；旧容器对而new2错7题、反向7题，总分相同但不是同一组题全相同。两轮物理81/86、化学75/93、生物11/19正确数也相同。旧C64触顶22题（19错），new2触顶20题（17错）；各11题严格答案提取缺失且均触顶。旧对/new2错的7题中new2有5触顶、3缺严格答案；这只是对应关系，不证明延长预算必然答对。

Math500两边457题均对、24题均错；旧对而new2错12题，反向7题，净少5题。new2相对旧容器几何41→37（净少4题）、预备微积分48→46、数论61→60；预备代数78→79、计数概率37→38各补回1题；代数及中级代数正确总数相同。旧C64没有触顶，new2只有1题触顶且错，12个旧对/new2错中只有这一题触顶，长度不能解释其余11题。两任务原始空/NUL-only/timeout均0；没有重评分或调整过滤器。

## 可比项与差异变量

198/500题的doc_hash、prompt_hash、target_hash全部相同；任务配置去metadata后相同；实际payload均T1/top_p.95/top_k-1/seed1234，生成预算18000/28000。权重产物指纹、tokenizer、vLLM源码树和所有已核对启动参数相同：TP8物理0–7、BF16、max_model_len100000、prefixcache开启、8192 batched tokens、maxseq64及graph模式/capture sizes。

变化：旧客户端64/64/64，new2客户端32/32/16；旧Plugin08da21c/FV46387d7/FG3b76f81与new2 Plugina696859/FV0dfb5cd/FG8200f71含各自工作区修改；FlagTree旧0.6.2a1+ppu3.6，新0.7.1.dev1+ppu3.6，Triton均3.6.0，adjust文件及Python树指纹不同。当前旧服务源树/compiler/argv与冻结证据仍一致。

这不是纯代码单变量A/B。温度1下两轮响应不同且batch/实现同时变化，不能把Math净5题直接归因某个算子、topk-sigmoid或编译器。几何差4题仅是基准失分分布，不是几何专属算子回归证据。用户此前GPQA89.90%最高分未在本轮旧容器复现；该最高分轮次的32768上下文契约尚无原生产物，不能混入本表。

ERQA两轮均已核对实际400个唯一ID、evaluated400及正确数与原生accuracy一致。若后续需要隔离版本影响，new2也应在同C64契约下测量；当前没有启动任何额外评测、改源码、重启或压测。

## ERQA完整逐题对照

两轮221题均对、110题均错；旧容器对而new2错31题，旧容器错而new2对38题，new2净多7题。冻结400ID集合、原始数据集SHA、图片清单及原生评分源码均相同。原始item.answer的真正空响应和NUL-only两轮均0；30000生成预算触顶旧6题、new2 8题。旧容器触顶更少但分数更低，不能用空响应、NUL或触顶数量解释全部差异；没有重评分。

| 原生类别 | 旧C64正确率 | new2正确率 | new2减旧C64（百分点） |
|---|---:|---:|---:|
| Trajectory Reasoning | 62.12% | 72.73% | +10.61 |
| Pointing | 85.29% | 73.53% | -11.76 |
| Task Reasoning | 65.79% | 78.95% | +13.16 |
| Multi-view Reasoning | 37.84% | 43.24% | +5.40 |
| State Estimation | 65.45% | 61.82% | -3.63 |
| Action Reasoning | 68.06% | 65.28% | -2.78 |
| Other | 35.71% | 57.14% | +21.43 |
| Spatial Reasoning | 63.10% | 60.71% | -2.39 |

这些是原生类别汇总，不能据此确认某一类别或算子的系统性回归。new2在轨迹、任务、多视角推理等类别较高；旧容器在指向、状态估计、动作、空间推理较高。平均生成token旧6823.4675、new2 7018.3；没有把输出长短作为正确性的替代指标。

## 证据

旧run：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01`。new2 run：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01`。

离线报告：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/diag002-new2-native-comparison-20261022-01.json`，SHA `c29810ea0ba80ff695f33717cddd61f49440e7c1a6e9886a7c1171bde402339e`。脚本、每阶段result/samples及身份SHA见state的diag-002；原始题目答案响应仅留远端，未写入本地文档。

终态ERQA证据（只读聚合，无新增远端报告文件）：

- 旧原生result：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/erqa/native-output/erqa/erqa_result.json`，SHA `9b02c678f831bd5f66ab65676becd7c7b43e7e38799c77f116eb71dfa3fb24b6`。
- 旧evaluated：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/erqa/native-output/erqa/erqa_evaluated.json`，SHA `bce68c98594819b9001e508969cdcceb625404b73d528f90299da6368fd83288`。
- 旧audit：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/erqa/native-audit.json`，SHA `6777492b9079f47ca690f53b914172b9cceb73172bf9bb8c90c847a34d148efa`。
- new2原生result：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01/erqa/native-output/erqa/erqa_result.json`，SHA `9196ad1a234fba5fff80e0fd43d77f47653dd2af7d94120abdddf5e35a74171f`。
- new2 evaluated：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01/erqa/native-output/erqa/erqa_evaluated.json`，SHA `1ed567ffc3dfe77449010ac6e63d02b7eb20a720faac546268900e8857326aa9`。
- 整套result：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/result.json`，SHA `b3610b28c5ca07c225987749442060c1ce14fae60c05baf53f8668c93ba740fc`。
- controller终态：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/control-result.json`，SHA `9c84552a907b002b652d76e65e0d726d5329309661a6e43df851a17e3d97bbd7`。
