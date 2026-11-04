# 20261026-qwen3vl-opt12-c64-default-accuracy

已完成：opt12/9999/GPU0,1/TP2/prefixON服务完整GPQA198与ERQA400精度评测，各64并发、模型默认采样、依次各一次，均达到阈值。评测结束后用户模型仍原PID/源码/参数运行、modelsHTTP200，未重启。详情见[acc-001](optimize/acc-001-opt12-c64-default.md)。

默认采样实测temperature0.7/top_p0.8/top_k20/repetition_penalty1.0；独立loopback传输层去除官方客户端的采样和固定seed覆盖，保留任务stop及18000输出上限。原始runner/评分源码不改，实际native factory CPU验证通过，两次GPQA来源一致且198题与历史相同。本轮C64/无显式request seed/设备及实例不同，不作旧C32结果的单变量对照。

最终2026-10-27 02:11（Asia/Shanghai）复核结果：

| 数据集与口径 | 正确/分母 | 得分 | 阈值 | 结果 |
|---|---:|---:|---:|---|
| GPQA Diamond strict-match |129/198|65.1515|64|通过|
| ERQA 原生accuracy |168/398|42.21|40|通过|
| ERQA 全部400题、超时计错 |168/400|42.00|40|通过|

ERQA原生完整400条，其中2条SDK超时拒答由未修改的原生filter排除（ERQA_105/50）；398份正常结果和2条拒答均保留。400unique/source/630图/原评分源码、所有实际upstream无采样/seed覆盖和原模型前后身份均复核通过，403个原生产物逐文件SHA回收一致。

原生ERQA已01:59:42正常退出0；采集控制器等待重试残留HTTP drain超300秒而失败，旧failure完整保留。仅以CPU回收/复核已有原生结果恢复终态，无重跑或改分母/阈值；见collector-recovery.json。GPQA gate仅为当时实际测量实例和已关闭的19964传输绑定，不转作当前direct9999/未来实例新gate；未直接计数graph replay，无性能或PR638单变量收益结论。

原始产物 `/public-flash/jinghao/qwen3-VL/20261026-qwen3vl-opt12-c64-default-accuracy`；最终回执results/completed-recovered.json SHA5e337ce4156964f4956a969fa6b92be0a34de08fb38b6f31e7a44f98777a6504。监控`qwen3-vl-opt12-c64`已在两项终态、用户服务核验及记录归档后删除。

- [baseline](baseline/README.md)
- [optimize](optimize/README.md)
- [acceptance](acceptance/README.md)
