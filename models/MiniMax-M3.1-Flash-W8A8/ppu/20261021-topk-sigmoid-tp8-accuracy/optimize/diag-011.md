# diag-011 用户更新的完整旧GPQA文件与近期原生结果对照

状态：完整文件离线对照完成；生成预算差异已确认，整套分差原因尚未以单变量实验隔离。本轮0模型请求，不重启、不改服务/源码/配置/缓存、不签gate。原有GPQA≥81%通过状态和所有历史分数保留；用户文件没有服务身份，不能替当前实例签gate。

## 文件版本与分数

用户将同一路径的文件从diag-010当时的单题dict（13675bytes，SHA d4e3fd9a8bc6c610729c0d0b666419500c01287067b5058b5fb5e3afb63111f9）替换为完整list（15602812bytes，SHA 0eb9cbdcd25f4ab3cff1e6dc0a4729cd3b987ae06801610fd6c8ddc432b85d0d）。此前单题结论是对当时版本的记录，不删除或混写。

完整文件396条、198唯一doc_id0..197；每题strict-match和flexible-extract各一条，没有重复id/filter。两filter的原始输入/响应/usage完全相同，是同次生成的两个评分视图，不当作396题。原生RegexFilter及exact_match(ignore_case/ignore_punctuation)离线复核198题，提取与分数均198/198一致，无差异。strict-match180/198=90.9090909%；flexible-extract80/198=40.4040404%，仅另一个filter，不替换正式strict指标。这个文件对应90.91%，不是此前口头89.90%。

| 对照来源 | strict-match | 生成上限 | 并发/seed/top_k证据 |
|---|---:|---:|---|
| 用户历史完整样本文件 | 180/198，90.91% | 95109 | 文件未保存实际API并发/seed/top_k |
| 新容器new2 acc-007归档 | 167/198，84.34% | 18000 | C32，实际payload seed1234/top_k-1 |
| 旧容器最近C64归档 | 167/198，84.34% | 18000 | C64，实际payload seed1234/top_k-1 |

当前latest容器服务元数据仍为MiniMax-M3.1-new-new。表内new2是已完成acc-007的历史全量结果，不是对当前重启实例新测198题；当前实例仅diag-010单题正确。两组已有新/旧全量比较的源码/采样证据继续见diag-008和旧C64案例。

## 严格逐题匹配

与两组近期记录逐一核对，doc_hash、prompt_hash、target_hash各198/198一致；实际序列化messages prompt和实际target另算内容SHA也198/198一致。题目、提示词、选项顺序和目标答案未发生变化。

用户历史→new2：167题双方均对、18题双方均错、13题历史对/new2错、0题反向。即new2全部167正确题都包含在该历史文件180正确题中。差13题、6.565657个百分点。类别净差：物理82→81（−1），化学84→75（−9），生物14→11（−3）；只是失分分布，不是类别专属数值缺陷证据。

用户历史→近期旧C64：165题双方对、16题双方错、15题历史对/近期错、2题反向，仍净少13。近期旧C64和new2同为167，不支持“只要回旧容器就自动恢复180”的推断。

## 长输出与预算证据

完整用户记录max_gen_toks全部95109，T1/top_p.95。近期两组都是18000/T1/.95，另外显式top_k-1和实际payload seed1234。用户文件中的do_sample=false只是task字段，不能据此覆盖实际T1；它未保存旧APIpayload/服务上下文/权重源码/并发，不能补造成相同身份。

- 用户旧记录有19题生成超过18000 tokens，其中15题正确。整体生成token中位2829，均值8383.27，最大95109；4题达到95109，其中2正确、2错误，触顶本身不是失败门槛。
- new2少掉的13题中11题正好达到18000生成预算；10题在旧记录中用了超过18000 tokens后正确，范围30518–95109。
- 这13题中7题在new2缺少strict可提取答案；它们均属于触顶观察。其余2个未触顶失分题不能用长度上限解释。
- 用户与new2没有完全相同的raw response，近期输出也没有任何一题是用户旧输出的完整前缀；不能假定是同一生成轨迹延长后必然修复13题。温度/随机状态、执行batch和实现仍可能影响轨迹。

因此，预算差异是已确认的测量配置差异和优先验证因素，而不是已经确认的全部根因。要隔离它，应先在当前最新服务把GPQA上限对齐95109，按用户此前要求使用64并发并冻结其他条件，再看差距；本轮没有启动该全量任务，亦不能将用户历史样本分数绑定到当前服务。

## 证据及保存边界

本地用户文件：GPQA Diamond-samples.json（历史路径当前不可用：`/Users/baai/Downloads/GPQA Diamond-samples.json`；须从原 revision 或远端证据恢复）。原始题目、答案和响应不写入本地案例。完整文件传到PPU-07的可选归档操作被自动审批拒绝：用户仅授权参考/比较，未明确授权完整数据传输；该上传未执行、未绕过。原始文件保持本地，以SHA核对；远端仅保存不含题目/答案/响应的汇总和小脚本，不影响已完成的对照。

安全汇总：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag011-user-gpqa-full-20261023-01/comparison-v2.json`，SHA `70bd3e1cb2aa4e505aef3544f533f0a78d693e330d05484e133569648a674542`。第一版comparison.json SHA1aab1ff19a82f6d9856b5b5acc4946a26a955fd749eb09d503c01e45de1ee50d保留，但其中的raw-input目标只是未执行计划；v2纠正保存状态，不改统计。

- new2 stage_result：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01/gpqa/result.json`，SHA `6aa557e17da9d17a2edf247aa3219f9ecbf1528894dbc9c404d3cd89ba460f88`。
- new2 native_sample_ref：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/accuracy/new2-t1-suite-20261022-01/gpqa/outputs/new2-user-t1-gpqa-20261022-01/19e969f6300541fdb0b48b08b114a549/gpqa_diamond_generative_cot/MiniMax-M3.1-new2/samples_gpqa_diamond_generative_cot_2026-10-22T10-38-10.554619.jsonl`，SHA `da4bc93975775dbb9bdd1cb875026dcbb80aa038b48d12dcafe4d4f94d36510d`。
- old_c64 stage_result：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/gpqa/result.json`，SHA `86d346efe27571a1559360c2308d941dc80f80aca504828bce0c8216decc99f5`。
- old_c64 native_sample_ref：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261022-minimax-m31-old-container-c64-accuracy/accuracy/old-container-c64-t1-suite-20261022-01/gpqa/outputs/old-container-c64-user-t1-gpqa-20261022-01/efcec69ebb3e430a896fe73af10f0b5a/gpqa_diamond_generative_cot/MiniMax-M3.1-new2/samples_gpqa_diamond_generative_cot_2026-10-22T14-29-30.829474.jsonl`，SHA `c422ad94400d2d2f483be606b31e28434fd6de5191583b1369f4159d806e5d1d`。

完整逐题id/token/触顶统计及原生离线评分摘要见state的diag-011与安全汇总。原生离线helper SHA4fb0a3d4e4031189dcbc592b5f3ae1a62a12c95aba15ee5125acdc2b09e84114；首次仅汇总JSON的numpy整数序列化失败，修正类型后离线复核；没有模型请求或改变评分规则。
