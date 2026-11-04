# diag-010 用户旧GPQA单样本与当前最新服务对照

完成时间：2026-10-23T15:47:31.827047+08:00。分类：单题/配置对比，没有复现该题的精度下降。用户文件实际只有doc_id0一个样本，不能据此核验198题总分或历史89.90%。本轮原生strict-match评分复核通过，但不是完整最小回归或全量精度gate；没有签gate、重启服务、改源码/配置/缓存或启动压测。

当前实际容器 `minimaxM3.1-opt-topk-sigmoid-20261021`，用户新启动的 `MiniMax-M3.1-new-new/8035`，Flash1019/TP8物理0–7/max_model_len100000/prefixcache开启。旧容器仍在但当前没有模型API进程。不能继续把旧C64评测实例当作当前服务。当前source/compiler/argv在单题前后核对不变，完整源码/导入与模型/tokenizer产物指纹见远端source证据；与acc-007归档源码内容一致，实例已重启，旧gate不自动绑定。

| 记录 | 样本范围 | 生成上限 | 输入tokens | 生成tokens | strict-match |
|---|---|---:|---:|---:|---:|
| 用户历史文件 | doc_id0，一题 | 95109 | 395 | 1028 | 1.0 |
| 旧容器最近C64全量记录中的同题 | 全量中的一题 | 18000 | 395 | 749 | 1.0 |
| 新容器acc-007全量记录中的同题 | 全量中的一题 | 18000 | 395 | 660 | 1.0 |
| 当前最新服务实测（修正封装-02） | 仅该题，一次请求 | 95109 | 395 | 1335 | 1.0 |

四者doc/prompt/target哈希对应同一道题；当前测试按文件原始messages列表发送，原生RegexFilter(strict-match，group_select=-1)与exact_match(ignore_case/ignore_punctuation)评分，提取答案与用户旧文件完全一致。当前HTTP200、finish_reason=stop，原始空/NUL均否。

关键配置差异是用户文件max_gen_toks95109，而近期两组全量GPQA均18000。温度1/top_p.95相同；do_sample=false是task记录字段，不能覆盖已验证的实际API温度1。旧文件未保存top_k和seed，本次保持缺省，不把它们补成-1/1234再声称旧配置完全一致。文件同样缺旧完整运行的并发、max_model_len、源码/权重与请求payload证据，95109不等于证明旧服务上下文长度95109。

这道题各次输出都少于18000，因此无法用更高上限解释该题结果，且没有发现答错。更高预算可能影响其他触顶题，但只有一条样本不能证实它是整套分差原因；不能将本轮1/1外推为当前GPQA100%，也不能拿先前167/198当当前重启实例的新完整分数。需要完整198题samples.jsonl以及原生results/config，才能核对历史高分、截断题与评分/预算差异。

## 请求封装修正及保留证据

首次准备因案例没有profiles父目录，在任何请求或产物写入前停止；仅补齐本案例父目录后继续。首个-01探针把arg_0[0]的序列化messages JSON当成用户文本再次包装，prompt_tokens428（不等于历史395）；该次虽native-score1、输出1807，也标为不可比并永久保留。发现后使用全新-02目录正确json.loads还原消息列表，修正后输入395与历史一致；未覆盖、删除或挑选旧结果。共2次诊断请求，仅-02的一次可比请求计入本次单题结论；没有全量重跑。

用户文件：GPQA Diamond-samples.json（历史路径当前不可用：`/Users/baai/Downloads/GPQA Diamond-samples.json`；须从原 revision 或远端证据恢复），SHA `d4e3fd9a8bc6c610729c0d0b666419500c01287067b5058b5fb5e3afb63111f9`。本地不复制题目、标准答案、推理响应或私有数据；远端唯一profile目录权限700，输入/响应权限600。

## 原生证据

- 修正后结果：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag010-user-gpqa-single-20261023-02/result.json`，SHA `132ecfddfdb0f45e9015e8fac5a6a0697f8015e69c8bb4ed58d31c56f14f7056`。
- 前置身份：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag010-user-gpqa-single-20261023-02/before-source.json`，SHA `1770ffc396cd84f82f4c857d35827ff4f5425c1bbfd7d0faf189ca10e3674106`。
- 结束身份：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag010-user-gpqa-single-20261023-02/after-source.json`，SHA `52252b1a640bc71c9b84f2d95f584f3530be4140d282198980f5660e9ce0f072`。
- 请求：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag010-user-gpqa-single-20261023-02/request.json`，SHA `1b287d29fc2b269d3428b3f2807669915bc41244ba82802f00a3af34ead1ac4e`。
- 原始响应：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag010-user-gpqa-single-20261023-02/response.json`，SHA `7ad1b73cdb0f2f06007d93404603bc71ccd3870f745317071421c4bff81029d3`。
- 原生评分：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/profiles/diag010-user-gpqa-single-20261023-02/native-score.json`，SHA `c35b4a830eba37307b8b2083c562874ef848f254ddb61d5d231308f42b67c36e`。
- 控制命令：`/mnt/nfs/users/jinghao/minimaxM3.1/optimize/20261021-minimax-m31-topk-sigmoid-tp8-accuracy/commands/diag010-single-request-control-20261023-02.py`，SHA `317559bf8f2db837087522bf91b28280e14dddd2dded1a556c543a93cdc41636`。

旧新完整评测样本的原生路径与SHA见[diag-008](diag-008.md)及[旧C64 diag-002](../../20261022-old-container-c64-accuracy/optimize/diag-002.md)。本轮没有新建监控，短单题请求已结束。

## 后续文件更新

用户后来将同一Downloads路径替换为完整198题/396记录，SHA0eb9cbdcd25f4ab3cff1e6dc0a4729cd3b987ae06801610fd6c8ddc432b85d0d，strict-match180/198=90.91%。本文件的“一题”只描述此前d4e3fd9a版本，完整对照见[diag-011](diag-011.md)。保留原单题结果与请求封装修正记录，不把历史覆盖成完整评测。
