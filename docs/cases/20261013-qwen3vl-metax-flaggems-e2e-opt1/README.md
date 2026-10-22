# Qwen3-VL / MetaX / FlagGems端到端优化

当前基于用户MoE JSON和qwen3vl-opt2-retry，在mx-59新独立容器GPU0/1验证。实际temperature0.7/top_k20/top_p0.8的随机采样trace定位FlagGems radix sort直方图热点；将有界计数器int64改为int32，Plugin/vLLM和MoE JSON均不改，未关闭FlagGems算子。完整排序数值、特殊值和graph变化输入重放通过，服务两worker命中证据完整。

2026-10-15原始P1024/D1024/C64/N128 performance_only B/C/R，各3warm+3measure：吞吐1133.59→1357.26→1130.62 token/s，候选+19.73%，P99TPOT56.09→46.82ms；延迟/稳定性守护全部passed、所有9测量轮保留、每轮128请求全部成功。D256 milestone+15.33%另存，不与原始场景相加。私有新容器qwen3vl-flaggems-op003-20261014保留候选，own18430停/GPU0,1释放；用户容器源码hash未变、8000仍正常，未回写/重启。

op003两轮小M MoE、op004大M MoE扫描均未满足完整算子晋级标准，未保留。旧greedy op002 +8.30%观察因原基线尾延迟波动超限仍incomplete；copy_/cumsum合并黑名单降低吞吐10.05%，已恢复。用户opt2手测CSV与自有不同设备/采样/场景结果分开解释，不混算精确收益。

正式精度按用户要求暂缓，无模型精度gate；新组合P4K/P16K/P32K未完成，最终四场景验收incomplete。下一轮先建立P4K采样匹配的三阶段checkpoint再选热点，不继续无新证据的MoE扫参。

[模型记录](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/README.md)、[op005证据](../../../models/Qwen3-VL-30B-A3B-Instruct/metax/20261013-qwen3vl-metax-flaggems-e2e-opt1/optimize/op-005-flaggems-sort-sampling.md)。远端案例 `/public-flash/jinghao/qwen3-VL/20261013-qwen3vl-metax-flaggems-e2e-opt1`；NFS满后的native对照和最终源码回执位于新容器私有 `/workspace/e2e-artifacts/20261013-qwen3vl-metax-flaggems-e2e-opt1/hist32-full03`（docker exec读取）。

2026-10-15后续用户授权：已将已验证sort单行优化回写至qwen3vl-flaggems-e2e-20261013，MoE JSON和其余仓库修改前后hash一致，原文件已备份；未重启服务或代跑测试，进入用户手动E2E交接状态。部署回执、SHA及回退路径见op005实验记录。
