# stats-004 GPQA补测合并统计

用户明确要求合并。用8题补测的全部结果替换对应原题，不逐题择优；原全量126分子减去这8题原2题正确，再加新4题正确，逐项核验198unique后计算。原native结果和样本保留，创建新的合并统计JSON，无模型请求。

执行前归档脚本SHA256 `15208ec6f3c549b238fa72769b44fe273f0e0f6b1426b9b0382e9fa225db30b2`。

## Completed merge

126 - 2 + 4 = 128 correct out of198. The user-requested merged GPQA score is **64.6464646465%**, meeting the64 threshold. All8 retest rows replace their original rows. Improvements are doc66 and127. ERQA remains175/400=43.75%.

This composite statistic retains the original complete126/198 run and the separate4/8 retest as source records. No new complete198 run, model requests, or formal gate were generated.

Artifact `/public-flash/jinghao/qwen3-VL/20261105-qwen3vl-c64-accuracy-mx59-001/results/gpqa-merged-cap131072.json` SHA256 `c26a4a4bc6be443cbdd21eb54eaa829370914cf1ca63f0be0500a437d9595228`. All198 rows record their original or retest source and both scores.
